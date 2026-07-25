"""Роутер отправки сообщения: принимает текст + изображения, стримит ответ (SSE)."""
from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.database import SessionLocal, get_db
from app.models import Chat, Message, MessageImage, User
from app.routers.chats import _get_owned_chat
from app.services.llm_client import ChatMessage
from app.services.pipeline import run_chat_pipeline
from app.services.title import make_title

router = APIRouter(prefix="/api/chats", tags=["messages"])

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8 МБ на картинку


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/{chat_id}/messages")
async def send_message(
    chat_id: str,
    content: str = Form(...),
    images: List[UploadFile] = File(default=[]),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Принимает сообщение пользователя (multipart: текст + до N картинок),
    сохраняет его и стримит ответ ассистента как SSE.

    SSE-события (JSON в data):
      {"type":"token","delta":"..."} — кусок переведённого ответа
      {"type":"title","title":"..."} — обновлённое название чата
      {"type":"message","id":"..."} — id сохранённого сообщения ассистента
      {"type":"error","status":...,"message":"..."}
      {"type":"done"}
    """
    chat = _get_owned_chat(chat_id, user, db)

    # --- Валидация изображений ---
    vision_enabled = settings.llm.vision_enabled
    max_images = settings.llm.max_images_per_message
    image_blobs: list[tuple[bytes, str]] = []

    if images:
        if not vision_enabled:
            raise HTTPException(
                status_code=400,
                detail="Загрузка изображений отключена в конфигурации сервера.",
            )
        if len(images) > max_images:
            raise HTTPException(
                status_code=400,
                detail=f"Можно прикрепить не более {max_images} изображений.",
            )
        for img in images:
            if img.content_type not in ALLOWED_IMAGE_TYPES:
                raise HTTPException(status_code=400, detail=f"Неподдерживаемый тип файла: {img.content_type}")
            data = await img.read()
            if len(data) > MAX_IMAGE_BYTES:
                raise HTTPException(status_code=400, detail="Изображение слишком большое (макс. 8 МБ).")
            image_blobs.append((data, img.content_type))

    # --- Сохраняем сообщение пользователя ---
    user_msg = Message(chat_id=chat.id, role="user", content=content)
    db.add(user_msg)
    for idx, (data, mime) in enumerate(image_blobs):
        db.add(
            MessageImage(
                message=user_msg,
                order_index=idx,
                mime_type=mime,
                data=data,
            )
        )

    # --- Авто-заголовок для нового чата ---
    needs_title = chat.title == "Новый чат" and not chat.messages
    if needs_title:
        chat.title = make_title(content)
    db.commit()
    db.refresh(user_msg)
    db.refresh(chat)

    # --- Готовим контекст для LLM ---
    history = db.scalars(
        select(Message)
        .where(Message.chat_id == chat.id)
        .order_by(Message.created_at.desc())
        .limit(settings.llm.context_messages + 1)  # +1 — текущее user_msg
    ).all()
    history = list(reversed(history))

    llm_messages: list[ChatMessage] = [_system_message()]
    # Пропускаем только что сохранённое сообщение — оно последним пойдёт с картинками.
    for m in history[:-1]:
        llm_messages.append(_history_message_to_llm(m))
    # Текущее сообщение — с изображениями.
    user_images = image_blobs if vision_enabled else []
    llm_messages.append(ChatMessage(role="user", content=content, images=user_images))

    return StreamingResponse(
        _stream(chat.id, llm_messages, needs_title),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # nginx не буферизует
            "Connection": "keep-alive",
        },
    )


def _system_message() -> ChatMessage:
    return ChatMessage(
        role="system",
        content=(
            "Ты — дружелюбный русскоязычный ассистент БурмалдаGPT. "
            "Отвечай всегда на русском языке, ясно, по делу и дружелюбно. "
            "Перевод твоих ответов на «бурмалду» выполняется отдельно — "
            "пиши обычным русским языком, не пытайся имитировать бурмалду сам."
        ),
    )


def _history_message_to_llm(m: Message) -> ChatMessage:
    images: list[tuple[bytes, str]] = []
    if settings.llm.vision_enabled and m.images:
        images = [(img.data, img.mime_type) for img in m.images]
    return ChatMessage(role=m.role, content=m.content, images=images)


async def _stream(chat_id: str, llm_messages: list[ChatMessage], send_title: bool):
    """Генератор SSE-событий конвейера + гарантированное сохранение ответа в БД."""
    full_content: list[str] = []
    persisted = False

    async for event in run_chat_pipeline(llm_messages):
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
                # Заголовок уже выставлен при сохранении user_msg; шлём его клиенту.
                with SessionLocal() as db:
                    chat = db.get(Chat, chat_id)
                    if chat:
                        yield _sse({"type": "title", "title": chat.title})
            yield _sse({"type": "done"})
            return
        elif etype == "error":
            # Сохраняем то, что успело прийти, и шлём клиенту id + done.
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

    # Если стрим оборвался БЕЗ done/error (обрыв соединения LLM) —
    # гарантированно сохраняем накопленное, чтобы не потерять ответ.
    if not persisted and full_content:
        msg_id = _persist_assistant_message(chat_id, "".join(full_content))
        yield _sse({"type": "message", "id": msg_id})
        yield _sse({"type": "done"})


def _persist_assistant_message(chat_id: str, content: str) -> str:
    """Сохраняет ответ ассистента в отдельной короткой сессии (потокобезопасно)."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        msg = Message(chat_id=chat_id, role="assistant", content=content, created_at=now)
        db.add(msg)
        chat = db.get(Chat, chat_id)
        if chat:
            # Обновляем updated_at — помечаем dirty для гарантии flush.
            chat.updated_at = now
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(chat, "updated_at")
        db.commit()
        db.refresh(msg)
        return msg.id
