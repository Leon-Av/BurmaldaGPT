"""Контроль запросов: per-user rate limiting + гибридная очередь.

Rate limiting (token bucket на пользователя):
  - 12 запросов/мин (или из config queue.user_rate_limit_per_minute)
  - 200 запросов/час (или queue.user_rate_limit_per_hour)
  Хранится in-memory (для проде — Redis, см. TODO). Достаточно для 1 backend-инстанса.

Гибридная очередь:
  - Глобальный лимит одновременных запросов к LLM = llm.max_concurrent
  - Первые queue.max_waiting запросов ждут в очереди с показом позиции
  - Остальные получают мгновенный 429 «сервис занят»
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from fastapi import HTTPException

from app.config import settings


# ============================================================
#  Rate limiting (per-user)
# ============================================================

@dataclass
class _Bucket:
    """Скользящее окно: список timestamp'ов запросов."""
    minute: List[float] = field(default_factory=list)
    hour: List[float] = field(default_factory=list)


class RateLimiter:
    """Per-user rate limiter (скользящее окно). Потокобезопасный."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._buckets: Dict[str, _Bucket] = {}
        self._per_minute = settings.queue.user_rate_limit_per_minute
        self._per_hour = settings.queue.user_rate_limit_per_hour

    async def check(self, user_id: str) -> None:
        """Проверяет лимит. Raise HTTPException 429 если превышен."""
        async with self._lock:
            now = time.time()
            b = self._buckets.setdefault(user_id, _Bucket())

            # Чистим устаревшие timestamp'ы.
            b.minute = [t for t in b.minute if now - t < 60]
            b.hour = [t for t in b.hour if now - t < 3600]

            if len(b.minute) >= self._per_minute:
                retry = 60 - int(now - b.minute[0]) + 1
                raise HTTPException(
                    status_code=429,
                    detail=f"Слишком много запросов. Попробуйте через {retry} сек.",
                    headers={"Retry-After": str(retry)},
                )
            if len(b.hour) >= self._per_hour:
                retry = 3600 - int(now - b.hour[0]) + 1
                raise HTTPException(
                    status_code=429,
                    detail=f"Превышен часовой лимит запросов. Попробуйте через {retry // 60} мин.",
                    headers={"Retry-After": str(retry)},
                )

            b.minute.append(now)
            b.hour.append(now)

    def reset(self, user_id: str) -> None:
        self._buckets.pop(user_id, None)


# ============================================================
#  Гибридная очередь (глобальная, для LLM-запросов)
# ============================================================

class QueueFullError(HTTPException):
    """Очередь переполнена → мгновенный 429."""

    def __init__(self, active: int, waiting: int) -> None:
        super().__init__(
            status_code=429,
            detail=(
                "Сервис сейчас перегружен. "
                f"Активных запросов: {active}, в очереди: {waiting}. "
                "Попробуйте через минуту."
            ),
            headers={"Retry-After": "60"},
        )


class RequestQueue:
    """Глобальная гибридная очередь LLM-запросов.

    - max_concurrent: одновременно выполняемых запросов (llm.max_concurrent)
    - max_waiting: сколько могут ждать в очереди с позицией
    - остальные → мгновенный QueueFullError (429)

    acquire() возвращает контекст-менеджер: ждёт своей очереди, потом
    выполняется. Optional[QueuePosition] передаётся в callback для индикации.
    """

    def __init__(self) -> None:
        self._sem = asyncio.Semaphore(settings.llm.max_concurrent)
        self._max_waiting = settings.queue.max_waiting
        self._wait_timeout = settings.queue.wait_timeout_seconds
        self._lock = asyncio.Lock()
        self._waiting = 0  # кол-во ждущих в очереди прямо сейчас
        self._active = 0   # кол-во активных запросов

    async def acquire(self) -> None:
        """Ждёт слот. Raise QueueFullError если очередь переполнена/таймаут."""
        async with self._lock:
            # Быстрая проверка: если уже ждут слишком много — сразу 429.
            if self._waiting >= self._max_waiting:
                raise QueueFullError(self._active, self._waiting)
            self._waiting += 1

        try:
            try:
                await asyncio.wait_for(self._sem.acquire(), timeout=self._wait_timeout)
            except asyncio.TimeoutError:
                raise QueueFullError(self._active, self._waiting)
        finally:
            async with self._lock:
                self._waiting -= 1
                self._active += 1

    def release(self) -> None:
        self._sem.release()
        async def _dec():
            async with self._lock:
                self._active -= 1
        # release может вызываться не из async-контекста — планируем задачу.
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(_dec())
        except RuntimeError:
            pass

    def stats(self) -> dict:
        return {
            "active": self._active,
            "waiting": self._waiting,
            "max_concurrent": settings.llm.max_concurrent,
            "max_waiting": self._max_waiting,
        }


# Синглтоны.
rate_limiter = RateLimiter()
request_queue = RequestQueue()
