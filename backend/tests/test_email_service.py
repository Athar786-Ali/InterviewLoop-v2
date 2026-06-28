import logging
import smtplib

import pytest

from app.core.exceptions import AppError
from app.services.email_service import EmailService


class FakeSMTP:
    def __init__(self):
        self.started_tls = False
        self.login_calls = []
        self.messages = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return None

    def starttls(self):
        self.started_tls = True

    def login(self, username, password):
        self.login_calls.append((username, password))

    def send_message(self, message):
        self.messages.append(message)


class RecordingSMTP(FakeSMTP):
    instances = []

    def __init__(self, host, port, timeout):
        super().__init__()
        self.host = host
        self.port = port
        self.timeout = timeout
        self.instances.append(self)


def configure_smtp(monkeypatch):
    monkeypatch.setattr("app.services.email_service.settings.smtp_host", "smtp.example.com", raising=False)
    monkeypatch.setattr("app.services.email_service.settings.smtp_port", 587, raising=False)
    monkeypatch.setattr("app.services.email_service.settings.smtp_username", "mailer@example.com", raising=False)
    monkeypatch.setattr("app.services.email_service.settings.smtp_password", "smtp-secret", raising=False)
    monkeypatch.setattr("app.services.email_service.settings.smtp_from_email", "noreply@example.com", raising=False)
    monkeypatch.setattr("app.services.email_service.settings.smtp_from_name", "InterviewLoop", raising=False)
    monkeypatch.setattr("app.services.email_service.settings.smtp_use_tls", True, raising=False)


def test_send_email_sends_html_and_plain_text_message(monkeypatch):
    configure_smtp(monkeypatch)
    RecordingSMTP.instances = []
    monkeypatch.setattr("app.services.email_service.smtplib.SMTP", RecordingSMTP)

    EmailService().send_email(
        to_email="candidate@example.com",
        subject="Report ready",
        body="<strong>Your report is ready.</strong>",
    )

    smtp = RecordingSMTP.instances[0]
    assert smtp.host == "smtp.example.com"
    assert smtp.port == 587
    assert smtp.timeout == 10
    assert smtp.started_tls is True
    assert smtp.login_calls == [("mailer@example.com", "smtp-secret")]
    assert len(smtp.messages) == 1
    message = smtp.messages[0]
    assert message["To"] == "candidate@example.com"
    assert message["Subject"] == "Report ready"
    assert message["From"] == "InterviewLoop <noreply@example.com>"
    assert "Your report is ready." in message.get_body(("plain",)).get_content()
    assert "<strong>Your report is ready.</strong>" in message.get_body(("html",)).get_content()


def test_send_otp_composes_purpose_specific_email(monkeypatch):
    configure_smtp(monkeypatch)
    smtp = FakeSMTP()

    EmailService(smtp_factory=lambda host, port: smtp).send_otp(
        email="candidate@example.com",
        otp="123456",
        purpose="password_reset",
    )

    message = smtp.messages[0]
    assert message["Subject"] == "Password reset code for InterviewLoop"
    assert "123456" in message.get_body(("plain",)).get_content()
    assert "Password reset" in message.get_body(("html",)).get_content()


def test_email_service_warns_and_skips_when_smtp_not_configured(monkeypatch, caplog):
    monkeypatch.setattr("app.services.email_service.settings.smtp_host", None, raising=False)
    monkeypatch.setattr("app.services.email_service.settings.smtp_username", None, raising=False)
    smtp = FakeSMTP()

    with caplog.at_level(logging.WARNING):
        EmailService(smtp_factory=lambda host, port: smtp).send_email(
            to_email="candidate@example.com",
            subject="Ignored",
            body="This should not send.",
        )

    assert smtp.messages == []
    assert "smtp_email_skipped" in caplog.text


def test_email_service_retries_transient_smtp_failure(monkeypatch):
    configure_smtp(monkeypatch)
    smtp = FakeSMTP()
    calls = []

    def smtp_factory(host, port):
        calls.append((host, port))
        if len(calls) == 1:
            raise smtplib.SMTPServerDisconnected("temporary disconnect")
        return smtp

    EmailService(smtp_factory=smtp_factory, retry_attempts=2, retry_backoff_seconds=0).send_email(
        to_email="candidate@example.com",
        subject="Retry",
        body="Retry succeeds.",
    )

    assert len(calls) == 2
    assert len(smtp.messages) == 1


def test_email_service_raises_app_error_after_retry_exhaustion(monkeypatch):
    configure_smtp(monkeypatch)

    def smtp_factory(host, port):
        raise smtplib.SMTPConnectError(421, "temporarily unavailable")

    with pytest.raises(AppError) as error:
        EmailService(smtp_factory=smtp_factory, retry_attempts=2, retry_backoff_seconds=0).send_email(
            to_email="candidate@example.com",
            subject="Failure",
            body="This will fail.",
        )

    assert error.value.code == "SMTP_DELIVERY_FAILED"
