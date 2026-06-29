from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models.topic_performance import TopicPerformance


class TopicPerformanceRepository:
    def __init__(self, db: DbSession) -> None:
        self.db = db

    def get_or_create(self, *, user_id: UUID, session_id: UUID, topic: str) -> TopicPerformance:
        """Return an existing row or create a new one (not yet committed)."""
        statement = select(TopicPerformance).where(
            TopicPerformance.user_id == user_id,
            TopicPerformance.session_id == session_id,
            TopicPerformance.topic == topic,
            TopicPerformance.deleted_at.is_(None),
        )
        existing = self.db.scalar(statement)
        if existing:
            return existing
        record = TopicPerformance(
            user_id=user_id,
            session_id=session_id,
            topic=topic,
            questions_attempted=0,
            weak_area_count=0,
        )
        self.db.add(record)
        return record

    def upsert_score(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        topic: str,
        new_score: float,
    ) -> TopicPerformance:
        """Increment attempted count, recompute average, flag weak areas (score < 4)."""
        record = self.get_or_create(user_id=user_id, session_id=session_id, topic=topic)
        prev_avg = record.average_score or 0.0
        prev_count = record.questions_attempted
        record.questions_attempted = prev_count + 1
        record.average_score = round(
            (prev_avg * prev_count + new_score) / record.questions_attempted, 2
        )
        if new_score < 4:
            record.weak_area_count += 1
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def save(self, record: TopicPerformance) -> TopicPerformance:
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_for_user(self, user_id: UUID) -> list[TopicPerformance]:
        statement = select(TopicPerformance).where(
            TopicPerformance.user_id == user_id,
            TopicPerformance.deleted_at.is_(None),
        )
        return list(self.db.scalars(statement).all())
