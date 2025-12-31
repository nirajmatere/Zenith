from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import jwt
from passlib.context import CryptContext

from zenith_api.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return cast(str, pwd_context.hash(password))


def verify_password(password: str, hashed_password: str) -> bool:
    return cast(bool, pwd_context.verify(password, hashed_password))

def hash_token(token: str) -> str:
    # Store only a hash in DB for security.
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def create_access_token(*, user_id: str, expires_minutes: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "type": "access",
        "jti": uuid.uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_refresh_token(*, user_id: str, expires_days: int) -> tuple[str, datetime]:
    now = datetime.now(UTC)
    expires_at = now + timedelta(days=expires_days)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "jti": uuid.uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token, expires_at

def decode_token(token: str) -> dict[str, Any]:
    decoded = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    return cast(dict[str, Any], decoded)