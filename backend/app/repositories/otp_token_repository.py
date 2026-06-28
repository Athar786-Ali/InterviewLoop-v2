from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models.otp_token import OtpToken


class OtpTokenRepository:
    def __init__(self, db: DbSession) -> None:
        self.db = db

    def create(self, email: str, token_hash: str, purpose: str, expires_at: datetime, user_id: object | None) -> OtpToken:
        token = OtpToken(
            email=email,
            token_hash=token_hash,
            purpose=purpose,
            expires_at=expires_at,
            user_id=user_id,
        )
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def get_latest_active(self, email: str, purpose: str) -> OtpToken | None:
        statement = (
            select(OtpToken)
            .where(
                OtpToken.email == email,
                OtpToken.purpose == purpose,
                OtpToken.consumed_at.is_(None),
                OtpToken.deleted_at.is_(None),
            )
            .order_by(OtpToken.created_at.desc())
        )
        return self.db.scalar(statement)

    def save(self, token: OtpToken) -> OtpToken:
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token
