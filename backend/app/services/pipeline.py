"""Конвейер: LLM (стрим) → буфер по предложениям → перевод → стрим клиенту.

Стратегия «по предложениям»:
1. Получаем токены от LLM.
2. Накапливаем в буфере до границы предложения (. ! ? … или \\n) при достаточной длине.
3. Переводим накопленное предложение через /translate.
4. Отдаём переведённое предложение как SSE-delta клиенту.
5. В конце переводим остаток буфера.

Так пользователь видит «живой» поток переведённого текста, а перевод
остаётся связным на уровне предложения.
"""
from __future__ import annotations

import asyncio
import re
from typing import AsyncIterator, List

from app.services.llm_client import ChatMessage, LLMError, LLMOverloaded, stream_chat_completion
from app.services.translator import translate_text

# Граница предложения: . ! ? … (с опц. закрывающей кавычкой/скобкой) или перевод строки.
_SENTENCE_END = re.compile(r"([.!?…]+[\"')\]]?\s+)|(\n+)")

# Минимальная длина накопленного буфера перед отправкой на перевод —
# избегаем переводить осколки вроде «1.» в списках.
_MIN_FLUSH_LEN = 12


def _split_at_sentence_boundary(buffer: str) -> tuple[str, str]:
    """Делит буфер на (готовая_к_переводу_часть, остаток).

    Возвращает ("", buffer) если граница ещё не найдена или буфер слишком короткий.
    Берём ПОСЛЕДНЮЮ границу предложения в буфере, чтобы короткие фразы
    вроде «Привет! » не уходили на перевод по отдельности от следующего
    предложения — они склеиваются и переводятся вместе, сохраняя согласования.
    """
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
    messages: List[ChatMessage],
    flush_interval: float = 1.5,
) -> AsyncIterator[dict]:
    """Запускает конвейер чата. Yield'ит SSE-события-словари.

    Типы событий (поля "type"):
      - {"type": "token", "delta": "..."} — кусок переведённого ответа
      - {"type": "error", "message": "...", "status": int} — ошибка
      - {"type": "done", "content": str} — завершение (content — полный текст)

    Стратегия флеша:
      1. По границе предложения (берём последнюю границу в буфере).
      2. По таймеру: если буфер копится дольше flush_interval без новой
         границы предложения — флешим накопленное целиком (живость стрима).
    """
    full_translated: list[str] = []

    try:
        buffer = ""
        last_flush = asyncio.get_event_loop().time()

        async for token in stream_chat_completion(messages):
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
                # Нет границы предложения, но буфер копится — флешим целиком.
                translated = await translate_text(buffer)
                if translated:
                    full_translated.append(translated)
                    yield {"type": "token", "delta": translated}
                buffer = ""
                last_flush = now

        # Остаток буфера.
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
    except Exception as e:  # noqa: BLE001 — не роняем стрим, докладываем клиенту
        yield {"type": "error", "status": 500, "message": f"Внутренняя ошибка: {e}", "content": "".join(full_translated)}
