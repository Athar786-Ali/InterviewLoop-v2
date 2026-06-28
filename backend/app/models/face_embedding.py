from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseModel


class FaceEmbedding(BaseModel, Base):
    __tablename__ = "face_embeddings"
    __table_args__ = (
        Index("ix_face_embeddings_user_id", "user_id"),
        Index("ix_face_embeddings_model_name", "model_name"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(80), nullable=False)
    embeddings: Mapped[list[list[float]]] = mapped_column(JSONB, nullable=False)
    embedding_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship(back_populates="face_embeddings")
