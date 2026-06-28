from collections.abc import Callable
from functools import wraps

from sqlalchemy.orm import Session

from app.db.session import get_session_factory


def with_db_session(fn: Callable):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        db: Session = get_session_factory()()
        try:
            return fn(db, *args, **kwargs)
        finally:
            db.close()

    return wrapper
