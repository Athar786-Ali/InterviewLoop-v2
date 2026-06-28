import logging

from app.db.base import Base
from app.db.session import get_engine
from app import models  # noqa: F401

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Create SQLAlchemy tables for local Docker/dev environments."""
    Base.metadata.create_all(bind=get_engine())
    logger.info("database_tables_ready")
