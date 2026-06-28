from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: DbSession) -> None:
        self.db = db

    def create(
        self,
        user_id: UUID,
        session_id: UUID,
        token_hash: str,
        family_id: str,
        expires_at: datetime,
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            session_id=session_id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,
        )
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def list_active_by_user(self, user_id: UUID) -> list[RefreshToken]:
        statement = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.deleted_at.is_(None),
        )
        return list(self.db.scalars(statement).all())

    def get_by_id(self, token_id: UUID) -> RefreshToken | None:
        statement = select(RefreshToken).where(RefreshToken.id == token_id, RefreshToken.deleted_at.is_(None))
        return self.db.scalar(statement)

    def save(self, token: RefreshToken) -> RefreshToken:
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token
