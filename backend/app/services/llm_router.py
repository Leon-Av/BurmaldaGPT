"""Маршрутизатор LLM: балансировка между несколькими источниками.

Поддерживает:
  - round_robin: по очереди между активными источниками (с учётом weight)
  - least_load: наименее загруженный (по числу активных запросов в роутере)
  - явный выбор источника (когда пользователь выбирает модель в UI)

Возвращает LLMSource, который llm_client использует для запроса.
"""
from __future__ import annotations

import asyncio
import itertools
from typing import Dict, List, Optional

from app.config import LLMSource, settings


class LLMRouterError(Exception):
    """Нет доступных источников LLM."""


class NoAvailableSourceError(LLMRouterError):
    """Все источники заняты/недоступны."""


class LLMRouter:
    """Балансировщик нагрузки между источниками LLM.

    Потокобезопасный (через asyncio.Lock). Хранит счётчики активных запросов
    по каждому источнику для least_load и для метрик.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        # round-robin курсор с разворачиванием по весам
        self._rr_cycle: itertools.cycle = self._build_weighted_cycle()
        # счётчики активных запросов по source.name
        self._active: Dict[str, int] = {}
        # счётчики за всё время (для метрик)
        self._total: Dict[str, int] = {}
        self._errors: Dict[str, int] = {}
        self._last_failed: Dict[str, float] = {}

    def _build_weighted_cycle(self) -> itertools.cycle:
        """Создаёт цикл с учётом весов (мощный сервер встречается чаще)."""
        items: List[str] = []
        for s in settings.llm.active_sources:
            items.extend([s.name] * max(1, s.weight))
        if not items:
            items = ["__none__"]
        return itertools.cycle(items)

    def reload(self) -> None:
        """Перестраивает цикл после изменения конфига (тесты/горячая перезагрузка)."""
        self._rr_cycle = self._build_weighted_cycle()

    async def select(
        self,
        preferred_name: Optional[str] = None,
    ) -> LLMSource:
        """Выбирает источник LLM.

        preferred_name: если задан (выбор модели в UI) — возвращает его,
                        если он активен. Иначе — обычная балансировка.
        """
        async with self._lock:
            sources = settings.llm.active_sources
            if not sources:
                raise NoAvailableSourceError(
                    "Нет активных источников LLM. Проверьте config.yaml (local_servers/cloud_providers)."
                )

            # --- Явный выбор пользователем ---
            if preferred_name:
                for s in sources:
                    if s.name == preferred_name:
                        return s
                # Если preferred не найден — игнорируем, идём в балансировку.

            # --- least_load: наименее активных запросов ---
            if settings.llm.load_balancing == "least_load":
                # Выбираем источник с минимальным self._active[name].
                best = min(sources, key=lambda s: self._active.get(s.name, 0))
                return best

            # --- round_robin с учётом весов ---
            # Пропускаем отключённые/несуществующие имена в цикле.
            active_names = {s.name for s in sources}
            for _ in range(100):  # защита от бесконечного цикла
                name = next(self._rr_cycle)
                if name in active_names:
                    return next(s for s in sources if s.name == name)
            # fallback: первый активный
            return sources[0]

    async def acquire(self, source: LLMSource) -> None:
        """Отметить начало запроса к источнику (для least_load и метрик)."""
        async with self._lock:
            self._active[source.name] = self._active.get(source.name, 0) + 1
            self._total[source.name] = self._total.get(source.name, 0) + 1

    async def release(self, source: LLMSource, success: bool = True) -> None:
        """Отметить завершение запроса."""
        async with self._lock:
            cur = self._active.get(source.name, 0)
            if cur > 0:
                self._active[source.name] = cur - 1
            if not success:
                import time

                self._errors[source.name] = self._errors.get(source.name, 0) + 1
                self._last_failed[source.name] = time.time()

    def metrics(self) -> dict:
        """Снимок метрик для мониторинга / UI."""
        return {
            "active": dict(self._active),
            "total": dict(self._total),
            "errors": dict(self._errors),
            "sources": [
                {"name": s.name, "kind": s.kind, "model": s.model, "enabled": s.enabled}
                for s in settings.llm.sources
            ],
        }


# Синглтон роутера.
router = LLMRouter()
