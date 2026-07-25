"""Клиент к burmalda_api (POST /translate).

Переводит русский текст в «бурмалду». Используется конвейером pipeline.
"""
from __future__ import annotations

import httpx

from app.config import settings


class TranslatorError(Exception):
    pass


# Переиспользуем клиент между вызовами (живёт в event loop).
_client: httpx.AsyncClient | None = None


async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=settings.translator.timeout_seconds)
    return _client


async def translate_text(text: str) -> str:
    """Переводит текст. При ошибке возвращает оригинал (чтобы не рвать стрим)."""
    if not text.strip():
        return text
    payload = {"text": text, "hard_mode": settings.translator.hard_mode}
    try:
        client = await _get_client()
        resp = await client.post(
            f"{settings.translator.base_url}/translate",
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("translated", text)
    except (httpx.HTTPError, KeyError, ValueError) as e:
        # Деградация: показать оригинал, лог без раскрытия деталей клиенту.
        TranslatorError.detail = str(e)
        return text
