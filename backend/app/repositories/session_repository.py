from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models.session import Session


class SessionRepository:
    def __init__(self, db: DbSession) -> None:
        self.db = db

    def create(self, user_id: UUID, session_id: str, started_at: datetime) -> Session:
        session = Session(
            user_id=user_id,
            session_id=session_id,
            interview_type="auth",
            status="active",
            started_at=started_at,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def list_active_by_user(self, user_id: UUID) -> list[Session]:
        statement = select(Session).where(
            Session.user_id == user_id,
            Session.status == "active",
            Session.deleted_at.is_(None),
        )
        return list(self.db.scalars(statement).all())

    def get_active_for_user(self, session_id: UUID, user_id: UUID) -> Session | None:
        statement = select(Session).where(
            Session.id == session_id,
            Session.user_id == user_id,
            Session.status == "active",
            Session.deleted_at.is_(None),
        )
        return self.db.scalar(statement)

    def get_for_user(self, session_id: UUID, user_id: UUID) -> Session | None:
        statement = select(Session).where(
            Session.id == session_id,
            Session.user_id == user_id,
            Session.deleted_at.is_(None),
        )
        return self.db.scalar(statement)

    def save(self, session: Session) -> Session:
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
