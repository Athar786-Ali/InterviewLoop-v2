from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models.user import User


class UserRepository:
    def __init__(self, db: DbSession) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email, User.deleted_at.is_(None))
        return self.db.scalar(statement)

    def get_by_id(self, user_id: UUID) -> User | None:
        statement = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        return self.db.scalar(statement)

    def create(self, email: str, password_hash: str, full_name: str | None) -> User:
        user = User(email=email, password_hash=password_hash, full_name=full_name)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def save(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_active_ids(self) -> list:
        statement = select(User.id).where(User.is_active.is_(True), User.deleted_at.is_(None))
        return list(self.db.scalars(statement).all())
