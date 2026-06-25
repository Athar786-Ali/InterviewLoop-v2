from uuid import UUID

from sqlalchemy import Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseModel


class TopicPerformance(BaseModel, Base):
    __tablename__ = "topic_performance"
    __table_args__ = (
        UniqueConstraint("user_id", "session_id", "topic", name="uq_topic_performance_user_session_topic"),
        Index("ix_topic_performance_user_id", "user_id"),
        Index("ix_topic_performance_session_id", "session_id"),
        Index("ix_topic_performance_topic", "topic"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    topic: Mapped[str] = mapped_column(String(120), nullable=False)
    average_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    questions_attempted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    weak_area_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped["User"] = relationship(back_populates="topic_performances")
    session: Mapped["Session"] = relationship(back_populates="topic_performances")
