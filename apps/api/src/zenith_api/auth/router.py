from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from zenith_api.auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from zenith_api.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from zenith_api.config import settings
from zenith_api.db.models import RefreshToken, User
from zenith_api.db.session import get_db

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Email already registered"
        )

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    access = create_access_token(user_id=str(user.id), expires_minutes=settings.jwt_access_minutes)
    refresh, refresh_exp = create_refresh_token(
        user_id=str(user.id),
        expires_days=settings.jwt_refresh_days,
    )

    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh),
            expires_at=refresh_exp,
        )
    )
    db.commit()

    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials"
        )

    access = create_access_token(user_id=str(user.id), expires_minutes=settings.jwt_access_minutes)
    refresh, refresh_exp = create_refresh_token(
        user_id=str(user.id),
        expires_days=settings.jwt_refresh_days,
    )

    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh),
            expires_at=refresh_exp,
        )
    )
    db.commit()

    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    # Validate JWT shape
    try:
        decoded = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from None

    if decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token type"
        )

    sub = decoded.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token payload"
        )

    try:
        user_id = uuid.UUID(sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        ) from None


    # Check stored token hash (revokable refresh)
    token_hash = hash_token(payload.refresh_token)
    rt = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    if rt is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Refresh token not found"
        )

    if rt.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Refresh token revoked"
        )

    now = datetime.now(UTC)
    if rt.expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Refresh token expired"
        )

    access = create_access_token(user_id=str(user_id), expires_minutes=settings.jwt_access_minutes)

    # Return same refresh token (simple). Later: rotate refresh token.
    return TokenResponse(access_token=access, refresh_token=payload.refresh_token)
