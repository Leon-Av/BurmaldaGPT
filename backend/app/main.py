"""Точка входа сервера БурмалдаGPT (FastAPI)."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import auth, chats, messages, meta


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="БурмалдаGPT API",
    version="1.0.0",
    description="Многопользовательский чат с LLM и переводом ответов на «бурмалду».",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth.router)
app.include_router(meta.router)
app.include_router(chats.router)
app.include_router(messages.router)


@app.get("/")
def root() -> dict:
    return {"service": "БурмалдаGPT API", "status": "running", "version": "1.0.0"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=False,
    )
