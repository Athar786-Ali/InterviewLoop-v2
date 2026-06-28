from datetime import timedelta

from app.core.config import settings
from app.core.security import utc_now
from app.models.audit_log import AuditLog
from app.models.otp_token import OtpToken
from app.models.refresh_token import RefreshToken
from app.workers.celery_app import celery_app
from app.workers.tasks.base import with_db_session


@celery_app.task(
    bind=True,
    name="cleanup.soft_deleted_records",
    autoretry_for=(Exception,),
    retry_backoff=settings.celery_task_retry_backoff_seconds,
    retry_kwargs={"max_retries": settings.celery_task_max_retries},
)
@with_db_session
def cleanup_soft_deleted_records_task(db, self) -> dict:
    cutoff = utc_now() - timedelta(days=settings.cleanup_soft_deleted_days)
    deleted = 0
    for model in (OtpToken, RefreshToken, AuditLog):
        rows = db.query(model).filter(model.deleted_at.is_not(None), model.deleted_at < cutoff).all()
        for row in rows:
            db.delete(row)
            deleted += 1
    db.commit()
    return {"status": "cleaned", "deleted": deleted}
