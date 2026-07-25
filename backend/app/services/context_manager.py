"""Управление контекстом: token-based sliding window.

Главная оптимизация для масштабирования: НЕ передаём модели всю историю
(200k токенов), а только последние сообщения, влезающие в лимит context_max_tokens.
Это уменьшает prefill в 10x и кардинально поднимает throughput.

Использует tiktoken (BPE-токенайзер, как у GPT). Для других моделей (granite/gemma)
оценка приблизительная, но достаточно точная для отсечения длинной истории.
"""
from __future__ import annotations

from typing import List, Optional

import tiktoken

from app.config import settings
from app.models import Message

# Кэш энкодера. cl100k_base — универсальный BPE, близок к granite/llama.
_ENCODER: Optional[tiktoken.Encoding] = None


def _get_encoder() -> tiktoken.Encoding:
    global _ENCODER
    if _ENCODER is None:
        try:
            _ENCODER = tiktoken.get_encoding("cl100k_base")
        except Exception:
            # Фоллбэк: грубая оценка (1 токен ≈ 4 символа для русского).
            _ENCODER = None
    return _ENCODER  # type: ignore[return-value]


def count_tokens(text: str) -> int:
    """Подсчёт числа токенов в тексте."""
    enc = _get_encoder()
    if enc is not None:
        return len(enc.encode(text))
    # грубая оценка для русского (~2 символа на токен, кириллица менее экономна)
    return max(1, len(text) // 2)


def count_message_tokens(role: str, content: str) -> int:
    """Токены сообщения с учётом оверхеда ролей (как в OpenAI: ~4 токена на сообщение)."""
    return count_tokens(content) + 4  # +4 токена на структуру role/content


def build_context(
    history: List[Message],
    new_user_content: str,
    system_prompt: str,
    *,
    max_tokens: Optional[int] = None,
    max_messages: Optional[int] = None,
) -> tuple[List[Message], int]:
    """Собирает контекст для LLM по sliding window.

    Возвращает (отобранные_сообщения_истории, total_tokens_estimate).
    Всегда включает system_prompt (отдельно) + последние сообщения, влезающие в лимит.
    """
    limit_tokens = max_tokens or settings.llm.context_max_tokens
    limit_messages = max_messages or settings.llm.context_messages

    # Токены system prompt + нового user-сообщения — это «фиксированные» затраты,
    # остаток лимита идёт на историю.
    system_tokens = count_message_tokens("system", system_prompt)
    new_tokens = count_message_tokens("user", new_user_content)
    budget = limit_tokens - system_tokens - new_tokens

    if budget <= 0:
        # Контекст настолько мал, что не влезает даже system+new — отдаём минимум.
        return [], system_tokens + new_tokens

    selected: List[Message] = []
    used = 0
    # Идём с конца (самые свежие), добавляем пока влезаем.
    for msg in reversed(history):
        if len(selected) >= limit_messages:
            break
        m_tokens = count_message_tokens(msg.role, msg.content)
        if used + m_tokens > budget:
            break
        selected.append(msg)
        used += m_tokens

    selected.reverse()
    return selected, system_tokens + used + new_tokens
