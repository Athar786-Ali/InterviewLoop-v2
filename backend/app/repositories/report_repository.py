from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models.report import Report


class ReportRepository:
    def __init__(self, db: DbSession) -> None:
        self.db = db

    def create(
        self,
        user_id: UUID,
        session_id: UUID,
        report_type: str,
        storage_path: str,
        content_hash: str,
        signature: str,
        generated_at,
    ) -> Report:
        report = Report(
            user_id=user_id,
            session_id=session_id,
            report_type=report_type,
            storage_path=storage_path,
            content_hash=content_hash,
            signature=signature,
            generated_at=generated_at,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_for_user(self, report_id: UUID, user_id: UUID) -> Report | None:
        statement = select(Report).where(
            Report.id == report_id,
            Report.user_id == user_id,
            Report.deleted_at.is_(None),
        )
        return self.db.scalar(statement)

    def list_for_user(self, user_id: UUID) -> list[Report]:
        statement = (
            select(Report)
            .where(Report.user_id == user_id, Report.deleted_at.is_(None))
            .order_by(Report.created_at.desc())
        )
        return list(self.db.scalars(statement).all())
