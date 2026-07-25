"""Клиент к LLM-серверу (OpenAI-compatible /v1/chat/completions) со стримингом.

Теперь принимает конкретный LLMSource (выбранный роутером), а не глобальный конфиг.
Поддерживает локальные сервера (LM Studio/llama-server) и облачные провайдеры
(OpenAI/Anthropic-via-compat/Groq) — все через единый OpenAI-compat API.
"""
from __future__ import annotations

import base64
import json
from typing import AsyncIterator, List, Optional

import httpx

from app.config import LLMSource, settings


class LLMOverloaded(Exception):
    """Превышен лимит параллельных запросов."""


class LLMError(Exception):
    """Ошибка общения с LLM-сервером."""


class ChatMessage:
    """Унифицированное представление сообщения для LLM.

    Поддерживает plain-текст и мультимодал (текст + список (data, mime)).
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
    source: LLMSource,
    messages: List[ChatMessage],
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> AsyncIterator[str]:
    """Стримит delta-токены из чат-комплишена к указанному источнику.

    Raises LLMError при сетевых/серверных ошибках.
    """
    payload: dict = {
        "messages": [m.to_payload() for m in messages],
        "stream": True,
        "temperature": temperature if temperature is not None else settings.llm.temperature,
        "max_tokens": max_tokens if max_tokens is not None else settings.llm.max_output_tokens,
    }
    # Для cloud-провайдеров model обязательна; для local LM Studio — нет (берёт загруженную),
    # но передаём если задана.
    if source.model:
        payload["model"] = source.model

    headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
    if source.api_key:
        headers["Authorization"] = f"Bearer {source.api_key}"

    url = f"{source.base_url}/v1/chat/completions"
    timeout = httpx.Timeout(settings.llm.timeout_seconds, connect=15.0)
    got_any = False

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise LLMError(
                        f"{source.name} вернул {resp.status_code}: "
                        f"{body[:500].decode('utf-8', 'ignore')}"
                    )
                try:
                    async for line in resp.aiter_lines():
                        token = _parse_sse_line(line)
                        if token:
                            got_any = True
                            yield token
                except (httpx.RemoteProtocolError, httpx.ReadError):
                    # Сервер закрыл соединение без [DONE] (часто у LM Studio/llama-server).
                    # Если уже получили контент — это нормальное завершение стрима.
                    if not got_any:
                        raise LLMError(f"{source.name} закрыл соединение, не отдав ни одного токена")
    except (httpx.RemoteProtocolError, httpx.ReadError) as e:
        if not got_any:
            raise LLMError(f"Сетевая ошибка при обращении к {source.name}: {e}") from e
    except httpx.HTTPError as e:
        raise LLMError(f"Сетевая ошибка при обращении к {source.name}: {e}") from e


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
