"""Конвейер: LLM (стрим) → буфер по предложениям → перевод → стрим клиенту.

Теперь принимает конкретный LLMSource (выбранный роутером), а не использует
глобальный конфиг. Остальная логика (буфер по предложениям + перевод) без изменений.
"""
from __future__ import annotations

import asyncio
import re
from typing import AsyncIterator, List

from app.config import LLMSource
from app.services.llm_client import ChatMessage, LLMError, LLMOverloaded, stream_chat_completion
from app.services.translator import translate_text

# Граница предложения: . ! ? … (с опц. закрывающей кавычкой/скобкой) или перевод строки.
_SENTENCE_END = re.compile(r"([.!?…]+[\"')\]]?\s+)|(\n+)")

# Минимальная длина накопленного буфера перед отправкой на перевод.
_MIN_FLUSH_LEN = 12


def _split_at_sentence_boundary(buffer: str) -> tuple[str, str]:
    """Берём ПОСЛЕДНЮЮ границу предложения в буфере (связность перевода)."""
    if len(buffer) < _MIN_FLUSH_LEN:
        return "", buffer
    last = None
    for match in _SENTENCE_END.finditer(buffer):
        last = match
    if not last:
        return "", buffer
    cut = last.end()
    return buffer[:cut], buffer[cut:]


async def run_chat_pipeline(
    source: LLMSource,
    messages: List[ChatMessage],
    flush_interval: float = 1.5,
) -> AsyncIterator[dict]:
    """Запускает конвейер чата для указанного источника. Yield'ит SSE-события.

    Типы событий (поля "type"):
      - {"type": "token", "delta": "..."} — кусок переведённого ответа
      - {"type": "error", "message": "...", "status": int, "content": str}
      - {"type": "done", "content": str} — завершение (content — полный текст)
    """
    full_translated: list[str] = []

    try:
        buffer = ""
        last_flush = asyncio.get_event_loop().time()

        async for token in stream_chat_completion(source, messages):
            buffer += token
            now = asyncio.get_event_loop().time()

            ready, rest = _split_at_sentence_boundary(buffer)
            if ready:
                translated = await translate_text(ready)
                if translated:
                    full_translated.append(translated)
                    yield {"type": "token", "delta": translated}
                buffer = rest
                last_flush = now
            elif buffer and (now - last_flush) > flush_interval:
                translated = await translate_text(buffer)
                if translated:
                    full_translated.append(translated)
                    yield {"type": "token", "delta": translated}
                buffer = ""
                last_flush = now

        if buffer.strip():
            translated = await translate_text(buffer)
            if translated:
                full_translated.append(translated)
                yield {"type": "token", "delta": translated}

        yield {"type": "done", "content": "".join(full_translated)}

    except LLMOverloaded as e:
        yield {"type": "error", "status": 503, "message": str(e), "content": "".join(full_translated)}
    except LLMError as e:
        yield {"type": "error", "status": 502, "message": f"Ошибка модели: {e}", "content": "".join(full_translated)}
    except Exception as e:  # noqa: BLE001
        yield {"type": "error", "status": 500, "message": f"Внутренняя ошибка: {e}", "content": "".join(full_translated)}
