"""Мета-эндпоинты: статус/возможности сервера (для фронтенда)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.config import settings
from app.models import User
from app.services.llm_router import router as llm_router
from app.services.request_control import request_queue

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/capabilities")
def capabilities(user: User = Depends(get_current_user)) -> dict:
    """Возвращает возможности сервера для фронтенда.

    models: список доступных моделей (имя + kind) — только если allow_user_model_selection.
    Иначе — пусто (пользователь не выбирает, авто-балансировка).
    """
    models = []
    if settings.llm.allow_user_model_selection:
        for s in settings.llm.active_sources:
            models.append({"name": s.name, "kind": s.kind, "model": s.model})

    # Имя модели по умолчанию (для отображения) — первая локальная.
    default_name = ""
    local = settings.llm.local_sources
    if local:
        default_name = local[0].model or local[0].name

    return {
        "vision_enabled": settings.llm.vision_enabled,
        "max_images_per_message": settings.llm.max_images_per_message,
        "model": default_name,
        "allow_model_selection": settings.llm.allow_user_model_selection,
        "models": models,
    }


@router.get("/stats")
def stats(user: User = Depends(get_current_user)) -> dict:
    """Текущая загрузка сервера (для админ-панели / мониторинга)."""
    return {
        "queue": request_queue.stats(),
        "llm": llm_router.metrics(),
    }
