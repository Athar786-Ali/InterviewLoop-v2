from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, LargeBinary, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseModel


class TotpCredential(BaseModel, Base):
    __tablename__ = "totp_credentials"
    __table_args__ = (
        Index("ix_totp_credentials_user_id", "user_id"),
        Index("ix_totp_credentials_is_enabled", "is_enabled"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    encrypted_secret: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    recovery_code_hashes: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    recovery_code_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    label: Mapped[str | None] = mapped_column(String(160), nullable=True)

    user: Mapped["User"] = relationship(back_populates="totp_credentials")
