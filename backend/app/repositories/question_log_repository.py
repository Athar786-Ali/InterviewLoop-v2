from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models.question_log import QuestionLog


class QuestionLogRepository:
    def __init__(self, db: DbSession) -> None:
        self.db = db

    def create(
        self,
        *,
        session_id: UUID,
        sequence_number: int,
        topic: str,
        difficulty: str,
        question_text: str,
        answer_text: str | None = None,
        score: float | None = None,
        feedback: str | None = None,
    ) -> QuestionLog:
        log = QuestionLog(
            session_id=session_id,
            sequence_number=sequence_number,
            topic=topic,
            difficulty=difficulty,
            question_text=question_text,
            answer_text=answer_text,
            score=score,
            feedback=feedback,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def list_for_session(self, session_id: UUID) -> list[QuestionLog]:
        statement = (
            select(QuestionLog)
            .where(QuestionLog.session_id == session_id, QuestionLog.deleted_at.is_(None))
            .order_by(QuestionLog.sequence_number)
        )
        return list(self.db.scalars(statement).all())

    def save(self, log: QuestionLog) -> QuestionLog:
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
