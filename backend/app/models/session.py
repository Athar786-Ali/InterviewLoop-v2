from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseModel


class Session(BaseModel, Base):
    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_session_id", "session_id", unique=True),
        Index("ix_sessions_user_id", "user_id"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[str] = mapped_column(String(96), nullable=False)
    interview_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(48), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")
    interview_logs: Mapped[list["InterviewLog"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    question_logs: Mapped[list["QuestionLog"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    topic_performances: Mapped[list["TopicPerformance"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="session")
    code_executions: Mapped[list["CodeExecution"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="session", cascade="all, delete-orphan")
