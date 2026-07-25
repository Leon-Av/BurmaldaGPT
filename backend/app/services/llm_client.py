"""Клиент к LLM-серверу (OpenAI-compatible /v1/chat/completions) со стримингом.

Асинхронный стриминг chunk'ов по токенам. Поддержка мультимодальных сообщений
(изображения в формате base64 data URL).
"""
from __future__ import annotations

import asyncio
import base64
import json
from typing import AsyncIterator, List, Optional

import httpx

from app.config import settings

# Семафор ограничивает параллельные запросы к LLM (см. возможности сервера).
_semaphore: Optional[asyncio.Semaphore] = None


def get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(settings.llm.max_concurrent)
    return _semaphore


class LLMOverloaded(Exception):
    """Превышен лимит параллельных запросов к модели."""


class LLMError(Exception):
    """Ошибка общения с LLM-сервером."""


class ChatMessage:
    """Унифицированное представление сообщения для LLM.

    Поддерживает plain-текст и мультимодал (текст + список (data_url, mime)).
    """

    def __init__(
        self,
        role: str,
        content: str,
        images: Optional[List[tuple[bytes, str]]] = None,
    ) -> None:
        self.role = role
        self.content = content
        self.images = images or []

    def to_payload(self) -> dict:
        if not self.images:
            return {"role": self.role, "content": self.content}

        # Мультимодальный формат OpenAI: content — массив частей.
        parts: list[dict] = []
        for data, mime in self.images:
            b64 = base64.b64encode(data).decode("ascii")
            parts.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64}"},
                }
            )
        parts.append({"type": "text", "text": self.content})
        return {"role": self.role, "content": parts}


async def stream_chat_completion(
    messages: List[ChatMessage],
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> AsyncIterator[str]:
    """Стримит delta-токены из чат-комплишена.

    Raises LLMOverloaded при превышении лимита одновременных запросов,
    LLMError при прочих ошибках.
    """
    sem = get_semaphore()
    if sem.locked() and sem._value <= 0:  # быстрая проверка без блокировки
        raise LLMOverloaded("Сервер модели занят. Попробуйте через секунду.")

    payload = {
        "model": settings.llm.model,
        "messages": [m.to_payload() for m in messages],
        "stream": True,
        "temperature": temperature if temperature is not None else settings.llm.temperature,
        "max_tokens": max_tokens if max_tokens is not None else settings.llm.max_tokens,
    }
    headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
    if settings.llm.api_key:
        headers["Authorization"] = f"Bearer {settings.llm.api_key}"

    url = f"{settings.llm.base_url}/v1/chat/completions"

    async with sem:
        timeout = httpx.Timeout(settings.llm.timeout_seconds, connect=15.0)
        got_any = False
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as resp:
                    if resp.status_code != 200:
                        body = await resp.aread()
                        raise LLMError(
                            f"LLM вернул {resp.status_code}: {body[:500].decode('utf-8', 'ignore')}"
                        )
                    try:
                        async for line in resp.aiter_lines():
                            token = _parse_sse_line(line)
                            if token:
                                got_any = True
                                yield token
                    except (httpx.RemoteProtocolError, httpx.ReadError):
                        # Сервер закрыл соединение без [DONE] (часто у vLLM/llama.cpp).
                        # Если мы уже получили контент — это нормальное завершение стрима.
                        if not got_any:
                            raise LLMError("LLM закрыл соединение, не отдав ни одного токена")
                        # иначе — просто завершаем генератор (return не нужен, выпадаем из цикла)
        except (httpx.RemoteProtocolError, httpx.ReadError) as e:
            if not got_any:
                raise LLMError(f"Сетевая ошибка при обращении к LLM: {e}") from e
        except httpx.HTTPError as e:
            raise LLMError(f"Сетевая ошибка при обращении к LLM: {e}") from e


def _parse_sse_line(line: str) -> str:
    """Парсит одну строку SSE-ответа OpenAI. Возвращает текст delta или ''."""
    if not line or not line.startswith("data:"):
        return ""
    data = line[len("data:"):].strip()
    if not data or data == "[DONE]":
        return ""
    try:
        obj = json.loads(data)
    except json.JSONDecodeError:
        return ""
    choices = obj.get("choices") or []
    if not choices:
        return ""
    delta = choices[0].get("delta") or {}
    return delta.get("content") or ""
