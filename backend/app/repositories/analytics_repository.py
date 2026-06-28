from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import selectinload

from app.models.session import Session


class AnalyticsRepository:
    def __init__(self, db: DbSession) -> None:
        self.db = db

    def list_user_sessions(self, user_id: UUID) -> list[Session]:
        statement = (
            select(Session)
            .where(Session.user_id == user_id, Session.deleted_at.is_(None))
            .options(selectinload(Session.question_logs), selectinload(Session.topic_performances))
            .order_by(Session.started_at.desc().nullslast(), Session.created_at.desc())
        )
        return list(self.db.scalars(statement).all())
