"""Роутер отправки сообщения: принимает текст + изображения, стримит ответ (SSE).

Полный конвейер:
  1. rate limit (per-user)
  2. очередь (гибридная)
  3. выбор источника LLM (роутер: round_robin/least_load или по выбору пользователя)
  4. сборка контекста (token-based sliding window)
  5. стриминг LLM → перевод по предложениям → SSE клиенту
  6. сохранение ответа + авто-заголовок
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.database import SessionLocal, get_db
from app.models import Chat, Message, MessageImage, User
from app.routers.chats import _get_owned_chat
from app.services.context_manager import build_context, count_tokens
from app.services.llm_client import ChatMessage
from app.services.llm_router import NoAvailableSourceError, router as llm_router
from app.services.pipeline import run_chat_pipeline
from app.services.request_control import QueueFullError, rate_limiter, request_queue
from app.services.title import make_title

router = APIRouter(prefix="/api/chats", tags=["messages"])

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8 МБ на картинку

SYSTEM_PROMPT = (
    "Ты — дружелюбный русскоязычный ассистент БурмалдаGPT. "
    "Отвечай всегда на русском языке, ясно, по делу и дружелюбно. "
    "Перевод твоих ответов на «бурмалду» выполняется отдельно — "
    "пиши обычным русским языком, не пытайся имитировать бурмалду сам."
)


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/{chat_id}/messages")
async def send_message(
    chat_id: str,
    content: str = Form(...),
    model: Optional[str] = Form(default=None),  # выбор модели пользователем (если разрешено)
    images: List[UploadFile] = File(default=[]),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Принимает сообщение пользователя (multipart: текст + до N картинок + опц. model),
    сохраняет его и стримит ответ ассистента как SSE.
    """
    # 1) Rate limit (per-user).
    await rate_limiter.check(user.id)

    chat = _get_owned_chat(chat_id, user, db)

    # 2) Валидация выбора модели.
    preferred = None
    if model and settings.llm.allow_user_model_selection:
        # Проверяем, что запрошенная модель активна.
        active_names = {s.name for s in settings.llm.active_sources}
        if model in active_names:
            preferred = model

    # 3) Валидация изображений.
    vision_enabled = settings.llm.vision_enabled
    max_images = settings.llm.max_images_per_message
    image_blobs: list[tuple[bytes, str]] = []

    if images:
        if not vision_enabled:
            raise HTTPException(status_code=400, detail="Загрузка изображений отключена в конфигурации сервера.")
        if len(images) > max_images:
            raise HTTPException(status_code=400, detail=f"Можно прикрепить не более {max_images} изображений.")
        for img in images:
            if img.content_type not in ALLOWED_IMAGE_TYPES:
                raise HTTPException(status_code=400, detail=f"Неподдерживаемый тип файла: {img.content_type}")
            data = await img.read()
            if len(data) > MAX_IMAGE_BYTES:
                raise HTTPException(status_code=400, detail="Изображение слишком большое (макс. 8 МБ).")
            image_blobs.append((data, img.content_type))

    # 4) Сохраняем сообщение пользователя.
    user_msg = Message(chat_id=chat.id, role="user", content=content)
    db.add(user_msg)
    for idx, (data, mime) in enumerate(image_blobs):
        db.add(MessageImage(message=user_msg, order_index=idx, mime_type=mime, data=data))

    needs_title = chat.title == "Новый чат" and not chat.messages
    if needs_title:
        chat.title = make_title(content)
    db.commit()
    db.refresh(user_msg)
    db.refresh(chat)

    return StreamingResponse(
        _stream(chat.id, content, image_blobs, preferred, needs_title),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def _history_message_to_llm(m: Message) -> ChatMessage:
    images: list[tuple[bytes, str]] = []
    if settings.llm.vision_enabled and m.images:
        images = [(img.data, img.mime_type) for img in m.images]
    return ChatMessage(role=m.role, content=m.content, images=images)


async def _stream(
    chat_id: str,
    new_content: str,
    image_blobs: list[tuple[bytes, str]],
    preferred_model: Optional[str],
    send_title: bool,
):
    """Генератор SSE-событий: очередь → выбор источника → конвейер → сохранение."""
    full_content: list[str] = []
    persisted = False
    source_name: Optional[str] = None

    # --- 0) Очередь (гибридная): ждём слот или 429 ---
    try:
        await request_queue.acquire()
    except QueueFullError as e:
        yield _sse({"type": "error", "status": 429, "message": e.detail})
        yield _sse({"type": "done"})
        return

    try:
        # --- 1) Выбор источника LLM ---
        try:
            source = await llm_router.select(preferred_name=preferred_model)
        except NoAvailableSourceError as e:
            yield _sse({"type": "error", "status": 503, "message": str(e)})
            yield _sse({"type": "done"})
            return
        source_name = source.name
        await llm_router.acquire(source)
        # Сообщаем клиенту, какой источник/модель используется (для UI).
        yield _sse({"type": "source", "source": source.name, "kind": source.kind})

        # --- 2) Сборка контекста (sliding window) ---
        with SessionLocal() as db:
            history_all = list(
                reversed(
                    db.scalars(
                        __import__("sqlalchemy").select(Message)
                        .where(Message.chat_id == chat_id)
                        .order_by(Message.created_at.desc())
                        .limit(settings.llm.context_messages + 1)
                    ).all()
                )
            )
        # history_all включает только что сохранённое user_msg последним —
        # передаём историю БЕЗ него, оно пойдёт отдельно с картинками.
        history = history_all[:-1] if history_all else []
        selected_history, used_tokens = build_context(
            history, new_content, SYSTEM_PROMPT
        )

        llm_messages: list[ChatMessage] = [ChatMessage(role="system", content=SYSTEM_PROMPT)]
        for m in selected_history:
            llm_messages.append(_history_message_to_llm(m))
        user_images = image_blobs if settings.llm.vision_enabled else []
        llm_messages.append(ChatMessage(role="user", content=new_content, images=user_images))

        # --- 3) Конвейер: LLM → перевод по предложениям → стрим ---
        success = True
        async for event in run_chat_pipeline(source, llm_messages):
            etype = event.get("type")
            if etype == "token":
                full_content.append(event["delta"])
                yield _sse(event)
            elif etype == "done":
                content_str = event.get("content") or "".join(full_content)
                msg_id = _persist_assistant_message(chat_id, content_str)
                persisted = True
                yield _sse({"type": "message", "id": msg_id})
                if send_title:
                    with SessionLocal() as db:
                        chat = db.get(Chat, chat_id)
                        if chat:
                            yield _sse({"type": "title", "title": chat.title})
                yield _sse({"type": "done"})
                return
            elif etype == "error":
                success = False
                error_content = event.get("content") or "".join(full_content)
                if error_content:
                    msg_id = _persist_assistant_message(chat_id, error_content)
                    persisted = True
                    yield _sse({"type": "message", "id": msg_id})
                    if send_title:
                        with SessionLocal() as db:
                            chat = db.get(Chat, chat_id)
                            if chat:
                                yield _sse({"type": "title", "title": chat.title})
                yield _sse(event)
                yield _sse({"type": "done"})
                return

        # --- 4) Обрыв без done/error — сохраняем накопленное ---
        if not persisted and full_content:
            msg_id = _persist_assistant_message(chat_id, "".join(full_content))
            yield _sse({"type": "message", "id": msg_id})
            yield _sse({"type": "done"})

    finally:
        request_queue.release()
        if source_name:
            # Находим source по имени для release метрики.
            for s in settings.llm.active_sources:
                if s.name == source_name:
                    await llm_router.release(s, success=success if 'success' in dir() else True)
                    break


def _persist_assistant_message(chat_id: str, content: str) -> str:
    """Сохраняет ответ ассистента в отдельной короткой сессии."""
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        msg = Message(chat_id=chat_id, role="assistant", content=content, created_at=now)
        db.add(msg)
        chat = db.get(Chat, chat_id)
        if chat:
            chat.updated_at = now
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(chat, "updated_at")
        db.commit()
        db.refresh(msg)
        return msg.id
