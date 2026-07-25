"""Мета-эндпоинты: статус/возможности сервера (для фронтенда)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.config import settings
from app.models import User

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/capabilities")
def capabilities(user: User = Depends(get_current_user)) -> dict:
    """Возвращает публичные (для залогиненного) возможности сервера.

    Фронтенд использует, чтобы показать/скрыть UI загрузки изображений и т.п.
    """
    return {
        "vision_enabled": settings.llm.vision_enabled,
        "max_images_per_message": settings.llm.max_images_per_message,
        "model": settings.llm.model,
    }
