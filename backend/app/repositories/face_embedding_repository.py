from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models.face_embedding import FaceEmbedding


class FaceEmbeddingRepository:
    def __init__(self, db: DbSession) -> None:
        self.db = db

    def create(self, user_id: UUID, model_name: str, embeddings: list[list[float]]) -> FaceEmbedding:
        enrollment = FaceEmbedding(
            user_id=user_id,
            model_name=model_name,
            embeddings=embeddings,
            embedding_metadata={"image_count": len(embeddings)},
            is_active=True,
        )
        self.db.add(enrollment)
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment

    def get_active_by_user(self, user_id: UUID) -> FaceEmbedding | None:
        statement = (
            select(FaceEmbedding)
            .where(
                FaceEmbedding.user_id == user_id,
                FaceEmbedding.is_active.is_(True),
                FaceEmbedding.deleted_at.is_(None),
            )
            .order_by(FaceEmbedding.created_at.desc())
        )
        return self.db.scalar(statement)

    def deactivate_active_by_user(self, user_id: UUID) -> None:
        active = self.get_active_by_user(user_id)
        if active:
            active.is_active = False
            self.db.add(active)
            self.db.commit()
