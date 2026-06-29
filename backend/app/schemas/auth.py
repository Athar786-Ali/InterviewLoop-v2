from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    full_name: str | None = Field(default=None, max_length=160)


class EmailVerificationRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=12)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32)


class LogoutRequest(BaseModel):
    refresh_token: str | None = Field(default=None, min_length=32)
    session_id: UUID | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=12)
    new_password: str = Field(min_length=12, max_length=128)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class SessionRead(ORMModel):
    id: UUID
    session_id: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class AuthUserRead(ORMModel):
    id: UUID
    email: EmailStr
    full_name: str | None
    is_email_verified: bool
    is_active: bool
