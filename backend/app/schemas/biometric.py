from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.auth import TokenPair
from app.schemas.common import ORMModel


class BiometricEnrollmentRequest(BaseModel):
    images: list[str] = Field(min_length=5, max_length=5)


class BiometricEnrollmentRead(ORMModel):
    id: UUID
    model_name: str
    is_active: bool


class BiometricLoginRequest(BaseModel):
    email: EmailStr
    face_image: str
    liveness_frames: list[str] = Field(min_length=3, max_length=30)


class BiometricLoginResponse(TokenPair):
    pass
