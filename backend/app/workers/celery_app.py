from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "interviewloop_v2",
    broker=str(settings.redis_url),
    backend=str(settings.redis_url),
)
