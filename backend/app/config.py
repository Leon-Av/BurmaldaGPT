"""Загрузка конфигурации из config.yaml с перекрытием переменными окружения.

Поддерживает несколько источников LLM:
  - 1-6 локальных серверов (LM Studio / llama-server / любой OpenAI-compat)
  - 0+ облачных провайдеров (OpenAI, Anthropic, Groq, ...)
Ключи облака читаются из переменных окружения (см. provider.env_key).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import List, Literal

import yaml
from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


def _env(key: str, default: str | None = None) -> str | None:
    val = os.getenv(key)
    return val if val not in (None, "") else default


@dataclass
class LLMSource:
    """Унифицированный источник LLM — локальный сервер или облако.

    kind:        "local" | "cloud"
    name:        отображаемое имя (для UI)
    base_url:    OpenAI-compat endpoint
    model:       имя модели (для local может быть пустым — сервер сам выбирает)
    api_key:     ключ (для local обычно ""; для cloud — из ENV)
    weight:      вес в round_robin (мощный сервер = больше)
    enabled:     активен ли (local всегда True; cloud — по флагу в конфиге)
    """

    kind: Literal["local", "cloud"]
    name: str
    base_url: str
    model: str
    api_key: str
    weight: int = 1
    enabled: bool = True


@dataclass
class LLMConfig:
    allow_user_model_selection: bool
    load_balancing: Literal["round_robin", "least_load"]
    sources: List[LLMSource]
    context_max_tokens: int
    max_output_tokens: int
    temperature: float
    timeout_seconds: float
    context_messages: int
    max_concurrent: int
    vision_enabled: bool
    max_images_per_message: int

    @property
    def active_sources(self) -> List[LLMSource]:
        """Только активные источники (local всегда активны, cloud — по флагу)."""
        return [s for s in self.sources if s.enabled]

    @property
    def local_sources(self) -> List[LLMSource]:
        return [s for s in self.active_sources if s.kind == "local"]

    @property
    def cloud_sources(self) -> List[LLMSource]:
        return [s for s in self.active_sources if s.kind == "cloud"]


@dataclass
class QueueConfig:
    max_waiting: int
    wait_timeout_seconds: float
    user_rate_limit_per_minute: int
    user_rate_limit_per_hour: int


@dataclass
class TranslatorConfig:
    base_url: str
    hard_mode: bool
    timeout_seconds: float


@dataclass
class AuthConfig:
    secret_key: str
    token_ttl_minutes: int


@dataclass
class DatabaseConfig:
    url: str


@dataclass
class ServerConfig:
    host: str
    port: int
    cors_origins: List[str]


@dataclass
class Settings:
    llm: LLMConfig
    queue: QueueConfig
    translator: TranslatorConfig
    auth: AuthConfig
    database: DatabaseConfig
    server: ServerConfig


def _build_sources(raw_llm: dict) -> List[LLMSource]:
    """Собирает унифицированный список источников из local_servers + cloud_providers."""
    sources: List[LLMSource] = []

    # --- Локальные сервера ---
    for srv in raw_llm.get("local_servers", []) or []:
        base = (srv.get("base_url") or "").rstrip("/")
        if not base:
            continue
        sources.append(
            LLMSource(
                kind="local",
                name=srv.get("name", "Локальный сервер"),
                base_url=base,
                # LM Studio не требует model в запросе (берёт загруженную),
                # но если указана — передаём.
                model=srv.get("model", ""),
                api_key=srv.get("api_key", "") or "",
                weight=int(srv.get("weight", 1)),
                enabled=True,  # локальные всегда активны
            )
        )

    # --- Облачные провайдеры ---
    for prov in raw_llm.get("cloud_providers", []) or []:
        base = (prov.get("base_url") or "").rstrip("/")
        model = prov.get("model", "")
        env_key = prov.get("env_key", "")
        api_key = os.getenv(env_key, "") if env_key else ""
        sources.append(
            LLMSource(
                kind="cloud",
                name=prov.get("name", "Cloud"),
                base_url=base,
                model=model,
                api_key=api_key,
                weight=1,
                enabled=bool(prov.get("enabled", False)) and bool(api_key) and bool(model),
            )
        )

    return sources


def _build_settings_from(raw: dict) -> Settings:
    raw_llm = raw.get("llm", {}) or {}
    raw_queue = raw.get("queue", {}) or {}
    raw_tr = raw.get("translator", {}) or {}
    raw_auth = raw.get("auth", {}) or {}
    raw_db = raw.get("database", {}) or {}
    raw_srv = raw.get("server", {}) or {}

    sources = _build_sources(raw_llm)
    if not any(s.kind == "local" and s.enabled for s in sources) and not any(
        s.kind == "cloud" and s.enabled for s in sources
    ):
        # Нет ни одного активного источника — критическая ошибка конфигурации.
        # Не падаем здесь (дадим приложению стартовать с понятным сообщением).
        pass

    llm = LLMConfig(
        allow_user_model_selection=bool(raw_llm.get("allow_user_model_selection", False)),
        load_balancing=raw_llm.get("load_balancing", "round_robin"),
        sources=sources,
        context_max_tokens=int(raw_llm.get("context_max_tokens", 4096)),
        max_output_tokens=int(raw_llm.get("max_output_tokens", 1024)),
        temperature=float(raw_llm.get("temperature", 0.7)),
        timeout_seconds=float(raw_llm.get("timeout_seconds", 120)),
        context_messages=int(raw_llm.get("context_messages", 20)),
        max_concurrent=int(raw_llm.get("max_concurrent", 64)),
        vision_enabled=bool(raw_llm.get("vision_enabled", True)),
        max_images_per_message=int(raw_llm.get("max_images_per_message", 5)),
    )

    queue = QueueConfig(
        max_waiting=int(raw_queue.get("max_waiting", 30)),
        wait_timeout_seconds=float(raw_queue.get("wait_timeout_seconds", 60)),
        user_rate_limit_per_minute=int(raw_queue.get("user_rate_limit_per_minute", 12)),
        user_rate_limit_per_hour=int(raw_queue.get("user_rate_limit_per_hour", 200)),
    )

    translator = TranslatorConfig(
        base_url=_env("TRANSLATOR_BASE_URL", raw_tr.get("base_url", "http://localhost:8000")).rstrip("/"),
        hard_mode=bool(raw_tr.get("hard_mode", True)),
        timeout_seconds=float(raw_tr.get("timeout_seconds", 30)),
    )

    secret = os.getenv(raw_auth.get("secret_key_env", "SECRET_KEY"), "")
    if not secret:
        secret = "dev-insecure-secret-change-me"
    auth = AuthConfig(
        secret_key=secret,
        token_ttl_minutes=int(raw_auth.get("token_ttl_minutes", 10080)),
    )

    database = DatabaseConfig(
        url=_env("DATABASE_URL", raw_db.get("url", "sqlite:///./burmalda.db")),
    )

    server = ServerConfig(
        host=raw_srv.get("host", "0.0.0.0"),
        port=int(raw_srv.get("port", 8001)),
        cors_origins=list(raw_srv.get("cors_origins", ["*"])),
    )

    return Settings(llm=llm, queue=queue, translator=translator, auth=auth, database=database, server=server)


@lru_cache
def get_settings() -> Settings:
    if not CONFIG_PATH.exists():
        raise RuntimeError(f"config.yaml не найден: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return _build_settings_from(raw)


def reload_settings() -> Settings:
    """Перечитывает конфиг (для тестов/горячей перезагрузки)."""
    get_settings.cache_clear()
    return get_settings()


settings = get_settings()
