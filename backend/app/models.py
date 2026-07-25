"""ORM-модели."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    theme: Mapped[str] = mapped_column(String(16), nullable=False, default="system")  # light|dark|system
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    chats: Mapped[list["Chat"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", order_by="Chat.updated_at.desc()"
    )


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="Новый чат")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="chats")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan", order_by="Message.created_at"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    chat_id: Mapped[str] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    chat: Mapped["Chat"] = relationship(back_populates="messages")
    images: Mapped[list["MessageImage"]] = relationship(
        back_populates="message", cascade="all, delete-orphan", order_by="MessageImage.order_index"
    )


class MessageImage(Base):
    """Прикреплённые изображения (для мультимодальных моделей)."""
    __tablename__ = "message_images"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), index=True, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False, default="image/png")
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    message: Mapped["Message"] = relationship(back_populates="images")
