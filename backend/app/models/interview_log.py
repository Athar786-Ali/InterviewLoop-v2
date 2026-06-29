from uuid import UUID
from typing import Any

from sqlalchemy import ForeignKey, Index, String, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseModel


class InterviewLog(BaseModel, Base):
    __tablename__ = "interview_logs"
    __table_args__ = (
        Index("ix_interview_logs_session_id", "session_id"),
        Index("ix_interview_logs_event_type", "event_type"),
    )

    session_id: Mapped[UUID] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    session: Mapped["Session"] = relationship(back_populates="interview_logs")
