"""SQLAlchemy engine/session."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


# check_same_thread=False — для SQLite + FastAPI (sync sessions, короткие).
connect_args = (
    {"check_same_thread": False}
    if settings.database.url.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.database.url,
    connect_args=connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Создаёт таблицы. Импорт моделей обязателен до create_all."""
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
