"""Pydantic-схемы (API-контракты)."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    display_name: Optional[str] = Field(default=None, max_length=64)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: str
    username: str
    display_name: str
    theme: str

    model_config = {"from_attributes": True}


# ---------- Chats ----------
class ChatCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)


class ChatUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class ChatOut(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Messages ----------
class MessageImageOut(BaseModel):
    id: str
    mime_type: str
    order_index: int

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime
    images: List[MessageImageOut] = []

    model_config = {"from_attributes": True}


class SendMessageResponse(BaseModel):
    """Финальный SSE-эвент: id сохранённого сообщения ассистента."""
    message_id: str
    role: str = "assistant"
    content: str


TokenResponse.model_rebuild()
