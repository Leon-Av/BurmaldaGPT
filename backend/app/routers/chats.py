"""Роутер чатов: CRUD + история сообщений + изображения."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Chat, Message, MessageImage, User
from app.schemas import ChatCreate, ChatOut, ChatUpdate, MessageOut

router = APIRouter(prefix="/api/chats", tags=["chats"])


def _get_owned_chat(chat_id: str, user: User, db: Session) -> Chat:
    chat = db.get(Chat, chat_id)
    if not chat or chat.user_id != user.id:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return chat


@router.get("", response_model=list[ChatOut])
def list_chats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chats = db.scalars(
        select(Chat).where(Chat.user_id == user.id).order_by(Chat.updated_at.desc())
    ).all()
    return chats


@router.post("", response_model=ChatOut, status_code=status.HTTP_201_CREATED)
def create_chat(
    body: ChatCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Chat:
    chat = Chat(user_id=user.id, title=(body.title or "Новый чат"))
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.patch("/{chat_id}", response_model=ChatOut)
def update_chat(
    chat_id: str,
    body: ChatUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Chat:
    chat = _get_owned_chat(chat_id, user, db)
    chat.title = body.title
    db.commit()
    db.refresh(chat)
    return chat


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(
    chat_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    chat = _get_owned_chat(chat_id, user, db)
    db.delete(chat)
    db.commit()


@router.get("/{chat_id}/messages", response_model=list[MessageOut])
def list_messages(
    chat_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = _get_owned_chat(chat_id, user, db)
    return list(chat.messages)


@router.get("/{chat_id}/messages/{message_id}/image/{image_id}")
def get_message_image(
    chat_id: str,
    message_id: str,
    image_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Отдаёт байты изображения (для предпросмотра в UI)."""
    from fastapi.responses import Response

    _get_owned_chat(chat_id, user, db)  # проверка владения
    img = db.get(MessageImage, image_id)
    if not img or img.message_id != message_id:
        raise HTTPException(status_code=404, detail="Изображение не найдено")
    return Response(content=img.data, media_type=img.mime_type)
