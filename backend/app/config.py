"""Загрузка конфигурации из config.yaml с перекрытием переменными окружения."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

import yaml
from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


def _env(key: str, default: str | None = None) -> str | None:
    val = os.getenv(key)
    return val if val not in (None, "") else default


class LLMConfig:
    base_url: str
    model: str
    api_key: str
    max_concurrent: int
    timeout_seconds: float
    context_messages: int
    temperature: float
    max_tokens: int
    vision_enabled: bool
    max_images_per_message: int

    def __init__(self, raw: dict) -> None:
        self.base_url = _env("LLM_BASE_URL", raw["base_url"]).rstrip("/")
        self.model = _env("LLM_MODEL", raw["model"])
        self.api_key = _env("LLM_API_KEY", raw.get("api_key", "")) or ""
        self.max_concurrent = int(raw.get("max_concurrent", 6))
        self.timeout_seconds = float(raw.get("timeout_seconds", 120))
        self.context_messages = int(raw.get("context_messages", 20))
        self.temperature = float(raw.get("temperature", 0.7))
        self.max_tokens = int(raw.get("max_tokens", 2048))
        self.vision_enabled = bool(raw.get("vision_enabled", True))
        self.max_images_per_message = int(raw.get("max_images_per_message", 5))


class TranslatorConfig:
    base_url: str
    hard_mode: bool
    timeout_seconds: float

    def __init__(self, raw: dict) -> None:
        self.base_url = _env("TRANSLATOR_BASE_URL", raw["base_url"]).rstrip("/")
        self.hard_mode = bool(raw.get("hard_mode", True))
        self.timeout_seconds = float(raw.get("timeout_seconds", 30))


class AuthConfig:
    secret_key_env: str
    token_ttl_minutes: int
    secret_key: str

    def __init__(self, raw: dict) -> None:
        self.secret_key_env = raw.get("secret_key_env", "SECRET_KEY")
        self.token_ttl_minutes = int(raw.get("token_ttl_minutes", 10080))
        self.secret_key = os.getenv(self.secret_key_env, "")
        if not self.secret_key:
            # Fallback для локальной разработки — НЕ использовать в проде.
            self.secret_key = "dev-insecure-secret-change-me"


class DatabaseConfig:
    url: str

    def __init__(self, raw: dict) -> None:
        self.url = _env("DATABASE_URL", raw.get("url", "sqlite:///./burmalda.db"))


class ServerConfig:
    host: str
    port: int
    cors_origins: List[str]

    def __init__(self, raw: dict) -> None:
        self.host = raw.get("host", "0.0.0.0")
        self.port = int(raw.get("port", 8001))
        self.cors_origins = list(raw.get("cors_origins", ["*"]))


class Settings:
    llm: LLMConfig
    translator: TranslatorConfig
    auth: AuthConfig
    database: DatabaseConfig
    server: ServerConfig

    def __init__(self) -> None:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        self.llm = LLMConfig(raw.get("llm", {}))
        self.translator = TranslatorConfig(raw.get("translator", {}))
        self.auth = AuthConfig(raw.get("auth", {}))
        self.database = DatabaseConfig(raw.get("database", {}))
        self.server = ServerConfig(raw.get("server", {}))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
