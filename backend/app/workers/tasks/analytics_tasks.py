from uuid import UUID

from app.core.config import settings
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.user_repository import UserRepository
from app.services.analytics_service import AnalyticsService
from app.workers.celery_app import celery_app
from app.workers.tasks.base import with_db_session


@celery_app.task(
    bind=True,
    name="analytics.update_user",
    autoretry_for=(Exception,),
    retry_backoff=settings.celery_task_retry_backoff_seconds,
    retry_kwargs={"max_retries": settings.celery_task_max_retries},
)
@with_db_session
def update_user_analytics_task(db, self, user_id: str) -> dict:
    dashboard = AnalyticsService(AnalyticsRepository(db)).get_dashboard(UUID(user_id))
    return {
        "status": "updated",
        "user_id": user_id,
        "average_score": dashboard.summary.average_score,
        "completed_interviews": dashboard.summary.completed_interviews,
    }


@celery_app.task(
    bind=True,
    name="analytics.refresh_all_users",
    autoretry_for=(Exception,),
    retry_backoff=settings.celery_task_retry_backoff_seconds,
    retry_kwargs={"max_retries": settings.celery_task_max_retries},
)
@with_db_session
def refresh_all_users_analytics_task(db, self) -> dict:
    user_ids = UserRepository(db).list_active_ids()
    for user_id in user_ids:
        update_user_analytics_task.delay(str(user_id))
    return {"status": "queued", "user_count": len(user_ids)}
