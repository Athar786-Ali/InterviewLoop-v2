from datetime import datetime, timedelta, timezone
from secrets import randbelow, token_urlsafe
from uuid import UUID

import bcrypt
import jwt

from app.core.config import settings
from app.core.exceptions import AppError


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PasswordHasher:
    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


class TokenHasher:
    def hash(self, value: str) -> str:
        return bcrypt.hashpw(value.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify(self, value: str, value_hash: str) -> bool:
        return bcrypt.checkpw(value.encode("utf-8"), value_hash.encode("utf-8"))


class JwtService:
    def create_access_token(self, user_id: UUID, session_id: UUID) -> tuple[str, int]:
        if not settings.jwt_private_key:
            raise AppError("AUTH_CONFIGURATION_ERROR", "JWT private key is not configured.", 500)

        expires_delta = timedelta(minutes=settings.access_token_minutes)
        expires_at = utc_now() + expires_delta
        payload = {
            "sub": str(user_id),
            "sid": str(session_id),
            "type": "access",
            "exp": expires_at,
            "iat": utc_now(),
        }
        token = jwt.encode(payload, settings.jwt_private_key, algorithm=settings.jwt_algorithm)
        return token, int(expires_delta.total_seconds())

    def decode_access_token(self, token: str) -> dict[str, str]:
        if not settings.jwt_public_key:
            raise AppError("AUTH_CONFIGURATION_ERROR", "JWT public key is not configured.", 500)

        try:
            payload = jwt.decode(token, settings.jwt_public_key, algorithms=[settings.jwt_algorithm])
        except jwt.PyJWTError as exc:
            raise AppError("INVALID_ACCESS_TOKEN", "Invalid or expired access token.", 401) from exc

        if payload.get("type") != "access":
            raise AppError("INVALID_ACCESS_TOKEN", "Invalid access token.", 401)
        return payload


class OtpGenerator:
    def create(self) -> str:
        return f"{randbelow(1_000_000):06d}"


class RefreshTokenGenerator:
    def create(self) -> str:
        return token_urlsafe(48)
