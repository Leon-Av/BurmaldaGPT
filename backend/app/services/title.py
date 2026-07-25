"""Автоматическое название чата.

Первая итерация: короткий заголовок из первого сообщения пользователя.
Опционально можно генерировать через LLM (короткий запрос), но для скорости
и без лишних запросов к модели используем локальную эвристику.
"""
from __future__ import annotations

import re

_WS = re.compile(r"\s+")


def make_title(first_user_message: str, max_words: int = 6, max_len: int = 60) -> str:
    text = _WS.sub(" ", first_user_message).strip()
    if not text:
        return "Новый чат"
    words = text.split()
    title = " ".join(words[:max_words])
    if len(words) > max_words:
        title += "…"
    if len(title) > max_len:
        title = title[: max_len - 1].rstrip() + "…"
    return title
