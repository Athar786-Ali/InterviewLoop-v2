from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: DbSession) -> None:
        self.db = db

    def create(self, user_id: UUID | None, session_id: UUID | None, action: str, metadata_json: dict) -> AuditLog:
        log = AuditLog(user_id=user_id, session_id=session_id, action=action, metadata_json=metadata_json)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def list_for_user(self, user_id: UUID) -> list[AuditLog]:
        statement = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id, AuditLog.deleted_at.is_(None))
            .order_by(AuditLog.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_latest_for_user(self, user_id: UUID) -> AuditLog | None:
        statement = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id, AuditLog.deleted_at.is_(None))
            .order_by(AuditLog.created_at.desc())
        )
        return self.db.scalar(statement)
