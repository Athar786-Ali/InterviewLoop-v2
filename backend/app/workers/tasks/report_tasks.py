from uuid import UUID

from app.core.config import settings
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.services.report_crypto import ReportSignatureService
from app.services.report_pdf import ReportPdfRenderer
from app.services.report_service import ReportService
from app.workers.celery_app import celery_app
from app.workers.tasks.base import with_db_session


@celery_app.task(
    bind=True,
    name="reports.generate_pdf",
    autoretry_for=(Exception,),
    retry_backoff=settings.celery_task_retry_backoff_seconds,
    retry_kwargs={"max_retries": settings.celery_task_max_retries},
)
@with_db_session
def generate_pdf_report_task(db, self, user_id: str, session_id: str, report_type: str = "interview") -> dict:
    user = UserRepository(db).get_by_id(UUID(user_id))
    if not user:
        raise ValueError("User not found")
    service = ReportService(
        reports=ReportRepository(db),
        audit_logs=AuditLogRepository(db),
        sessions=SessionRepository(db),
        signer=ReportSignatureService(),
        pdf_renderer=ReportPdfRenderer(),
    )
    report = service.generate(user=user, session_id=UUID(session_id), report_type=report_type)
    return {"status": "generated", "report_id": str(report.id)}
