from app.core.config import settings
from app.services.email_service import EmailService
from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    name="email.send",
    autoretry_for=(Exception,),
    retry_backoff=settings.celery_task_retry_backoff_seconds,
    retry_kwargs={"max_retries": settings.celery_task_max_retries},
)
def send_email_task(self, to_email: str, subject: str, body: str) -> dict:
    EmailService().send_email(to_email=to_email, subject=subject, body=body)
    return {"status": "sent", "to_email": to_email}


@celery_app.task(
    bind=True,
    name="email.send_otp",
    autoretry_for=(Exception,),
    retry_backoff=settings.celery_task_retry_backoff_seconds,
    retry_kwargs={"max_retries": settings.celery_task_max_retries},
)
def send_otp_email_task(self, email: str, otp: str, purpose: str) -> dict:
    EmailService().send_otp(email=email, otp=otp, purpose=purpose)
    return {"status": "sent", "email": email, "purpose": purpose}
