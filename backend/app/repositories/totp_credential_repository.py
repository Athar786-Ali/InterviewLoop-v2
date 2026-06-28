from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models.totp_credential import TotpCredential


class TotpCredentialRepository:
    def __init__(self, db: DbSession) -> None:
        self.db = db

    def create(
        self,
        user_id: UUID,
        encrypted_secret: bytes,
        recovery_code_hashes: list[str],
        label: str | None,
    ) -> TotpCredential:
        credential = TotpCredential(
            user_id=user_id,
            encrypted_secret=encrypted_secret,
            recovery_code_hashes=recovery_code_hashes,
            recovery_code_metadata={"remaining": len(recovery_code_hashes)},
            is_enabled=False,
            label=label,
        )
        self.db.add(credential)
        self.db.commit()
        self.db.refresh(credential)
        return credential

    def get_latest_by_user(self, user_id: UUID) -> TotpCredential | None:
        statement = (
            select(TotpCredential)
            .where(TotpCredential.user_id == user_id, TotpCredential.deleted_at.is_(None))
            .order_by(TotpCredential.created_at.desc())
        )
        return self.db.scalar(statement)

    def get_enabled_by_user(self, user_id: UUID) -> TotpCredential | None:
        statement = (
            select(TotpCredential)
            .where(
                TotpCredential.user_id == user_id,
                TotpCredential.is_enabled.is_(True),
                TotpCredential.deleted_at.is_(None),
            )
            .order_by(TotpCredential.created_at.desc())
        )
        return self.db.scalar(statement)

    def save(self, credential: TotpCredential) -> TotpCredential:
        self.db.add(credential)
        self.db.commit()
        self.db.refresh(credential)
        return credential
