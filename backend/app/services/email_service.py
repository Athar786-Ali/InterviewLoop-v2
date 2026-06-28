import html
import logging
import re
import smtplib
import time
from collections.abc import Callable
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import settings
from app.core.exceptions import AppError

logger = logging.getLogger(__name__)

SMTPFactory = Callable[[str, int], smtplib.SMTP]
TRANSIENT_SMTP_ERRORS = (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, TimeoutError, OSError)


class EmailService:
    def __init__(
        self,
        smtp_factory: SMTPFactory | None = None,
        retry_attempts: int = 2,
        retry_backoff_seconds: float = 0.2,
    ) -> None:
        self.smtp_factory = smtp_factory or self._create_smtp_client
        self.retry_attempts = retry_attempts
        self.retry_backoff_seconds = retry_backoff_seconds

    def send_otp(self, email: str, otp: str, purpose: str) -> None:
        label = self._purpose_label(purpose)
        subject = f"{label} code for InterviewLoop"
        plain_text = (
            f"Your InterviewLoop {label.lower()} code is {otp}.\n\n"
            "This code expires shortly. If you did not request this, you can safely ignore this email."
        )
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #102033; line-height: 1.6;">
            <h2 style="margin: 0 0 12px;">{html.escape(label)}</h2>
            <p>Your InterviewLoop code is:</p>
            <p style="font-size: 28px; font-weight: 700; letter-spacing: 6px; margin: 18px 0;">{html.escape(otp)}</p>
            <p>This code expires shortly. If you did not request this, you can safely ignore this email.</p>
          </body>
        </html>
        """
        self._send_message(email, subject, plain_text, html_body, purpose=purpose)

    def send_email(self, to_email: str, subject: str, body: str) -> None:
        plain_text = self._to_plain_text(body)
        html_body = self._to_html_body(body)
        self._send_message(to_email, subject, plain_text, html_body)

    def _send_message(
        self,
        to_email: str,
        subject: str,
        plain_text: str,
        html_body: str,
        purpose: str | None = None,
    ) -> None:
        if not settings.smtp_host or not settings.smtp_username:
            logger.warning(
                "smtp_email_skipped",
                extra={"recipient": to_email, "purpose": purpose, "reason": "smtp_not_configured"},
            )
            return

        message = self._build_message(to_email, subject, plain_text, html_body)
        last_error: Exception | None = None

        for attempt in range(1, self.retry_attempts + 1):
            try:
                with self.smtp_factory(settings.smtp_host, settings.smtp_port) as smtp:
                    if settings.smtp_use_tls:
                        smtp.starttls()
                    if settings.smtp_password:
                        smtp.login(settings.smtp_username, settings.smtp_password)
                    smtp.send_message(message)
                logger.info("smtp_email_sent", extra={"recipient": to_email, "purpose": purpose})
                return
            except TRANSIENT_SMTP_ERRORS as exc:
                last_error = exc
                logger.warning(
                    "smtp_transient_failure",
                    extra={"recipient": to_email, "purpose": purpose, "attempt": attempt, "error": str(exc)},
                )
                if attempt < self.retry_attempts:
                    time.sleep(self.retry_backoff_seconds * attempt)
                    continue
                break
            except smtplib.SMTPException as exc:
                logger.exception("smtp_delivery_failed", extra={"recipient": to_email, "purpose": purpose})
                raise AppError("SMTP_DELIVERY_FAILED", "Unable to send email.", 503) from exc

        logger.exception("smtp_delivery_failed_after_retries", exc_info=last_error, extra={"recipient": to_email, "purpose": purpose})
        raise AppError("SMTP_DELIVERY_FAILED", "Unable to send email after retrying SMTP delivery.", 503) from last_error

    def _build_message(self, to_email: str, subject: str, plain_text: str, html_body: str) -> EmailMessage:
        from_email = settings.smtp_from_email or settings.smtp_username
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = formataddr((settings.smtp_from_name, from_email))
        message["To"] = to_email
        message.set_content(plain_text)
        message.add_alternative(html_body, subtype="html")
        return message

    @staticmethod
    def _purpose_label(purpose: str) -> str:
        labels = {
            "email_verification": "Email verification",
            "password_reset": "Password reset",
        }
        return labels.get(purpose, purpose.replace("_", " ").title())

    @staticmethod
    def _to_plain_text(body: str) -> str:
        without_tags = re.sub(r"<[^>]+>", "", body)
        return html.unescape(without_tags).strip() or body

    @staticmethod
    def _to_html_body(body: str) -> str:
        if re.search(r"<[a-zA-Z][^>]*>", body):
            return body
        escaped = html.escape(body).replace("\n", "<br>")
        return f"<html><body><p>{escaped}</p></body></html>"

    @staticmethod
    def _create_smtp_client(host: str, port: int) -> smtplib.SMTP:
        return smtplib.SMTP(host=host, port=port, timeout=10)
