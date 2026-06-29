from types import SimpleNamespace
from uuid import uuid4

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.services.report_crypto import ReportSignatureService
from app.services.report_pdf import ReportPdfRenderer
from app.services.report_service import ReportService


def key_pair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


class FakeReports:
    def __init__(self):
        self.report = None

    def create(self, **kwargs):
        self.report = SimpleNamespace(id=uuid4(), deleted_at=None, **kwargs)
        return self.report

    def get_for_user(self, report_id, user_id):
        if self.report and self.report.id == report_id and self.report.user_id == user_id:
            return self.report
        return None

    def list_for_user(self, user_id):
        return [self.report] if self.report else []


class FakeAuditLogs:
    def __init__(self):
        self.logs = []

    def get_latest_for_user(self, user_id):
        return self.logs[-1] if self.logs else None

    def create(self, user_id, session_id, action, metadata_json):
        log = SimpleNamespace(id=uuid4(), user_id=user_id, session_id=session_id, action=action, metadata_json=metadata_json)
        self.logs.append(log)
        return log


class FakeSessions:
    def __init__(self, session):
        self.session = session

    def get_for_user(self, session_id, user_id):
        if self.session.id == session_id and self.session.user_id == user_id:
            return self.session
        return None


def test_report_service_generates_json_pdf_signature_and_hash_chain(tmp_path):
    private_pem, public_pem = key_pair()
    user_id = uuid4()
    session = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        session_id="external-session",
        interview_type="topic",
        status="completed",
        question_logs=[
            SimpleNamespace(score=8, deleted_at=None),
            SimpleNamespace(score=6, deleted_at=None),
        ],
    )
    user = SimpleNamespace(id=user_id, email="candidate@example.com")
    reports = FakeReports()
    audit_logs = FakeAuditLogs()
    service = ReportService(
        reports=reports,
        audit_logs=audit_logs,
        sessions=FakeSessions(session),
        signer=ReportSignatureService(private_pem, public_pem),
        pdf_renderer=ReportPdfRenderer(),
        storage_dir=str(tmp_path),
    )

    report = service.generate(user, session.id, "interview")
    verification = service.verify(user, report.id)

    assert (tmp_path / str(user.id) / str(session.id) / "report.json").exists()
    assert (tmp_path / str(user.id) / str(session.id) / "report.pdf").exists()
    assert report.content_hash
    assert report.signature
    assert verification.is_valid is True
    assert audit_logs.logs[0].metadata_json["hash_chain"]
    assert audit_logs.logs[1].metadata_json["previous_hash"] == audit_logs.logs[0].metadata_json["hash_chain"]


def test_report_pdf_renderer_outputs_pdf_bytes():
    pdf = ReportPdfRenderer().render({"average_score": 7.5, "status": "completed"})

    assert pdf.startswith(b"%PDF")


def test_report_signature_service_normalizes_escaped_newline_pem_values():
    private_pem, public_pem = key_pair()
    # Simulate keys stored with literal "\n" sequences (as in docker-compose .env files)
    escaped_private = private_pem.replace("\n", "\\n")
    escaped_public = public_pem.replace("\n", "\\n")

    signer = ReportSignatureService(escaped_private, escaped_public)
    content = b"test report content"
    signature = signer.sign(content)

    assert signer.verify(content, signature) is True
    assert not signer.verify(b"tampered content", signature)

