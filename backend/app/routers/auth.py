"""Роутер аутентификации: регистрация, вход, текущий пользователь."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.scalar(select(User).where(User.username == body.username))
    if existing:
        raise HTTPException(status_code=409, detail="Имя пользователя уже занято")

    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        display_name=body.display_name or body.username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.username == body.username))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)) -> User:
    return current


@router.put("/me", response_model=UserOut)
def update_me(
    payload: dict,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Обновление профиля (theme, display_name)."""
    if "theme" in payload and payload["theme"] in ("light", "dark", "system"):
        current.theme = payload["theme"]
    if "display_name" in payload and payload["display_name"]:
        current.display_name = str(payload["display_name"])[:64]
    db.commit()
    db.refresh(current)
    return current
