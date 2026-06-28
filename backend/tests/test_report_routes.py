from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_current_user, get_report_service
from app.main import create_app
from app.schemas.report import ReportVerificationResponse


class FakeReportService:
    def __init__(self):
        self.report = SimpleNamespace(
            id=uuid4(),
            session_id=uuid4(),
            report_type="interview",
            storage_path="/tmp/report",
            content_hash="abc",
            signature="sig",
            generated_at=datetime.now(timezone.utc),
        )

    def generate(self, user, session_id, report_type):
        self.report.session_id = session_id
        self.report.report_type = report_type
        return self.report

    def list_reports(self, user):
        return [self.report]

    def verify(self, user, report_id):
        return ReportVerificationResponse(
            report_id=report_id,
            is_valid=True,
            content_hash="abc",
            signature_valid=True,
            hash_matches=True,
        )


def test_generate_report_route_returns_report_envelope():
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4())
    app.dependency_overrides[get_report_service] = lambda: FakeReportService()
    client = TestClient(app)
    session_id = str(uuid4())

    response = client.post("/api/v1/reports", json={"session_id": session_id, "report_type": "interview"})

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["session_id"] == session_id


def test_verify_report_route_returns_signature_status():
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4())
    app.dependency_overrides[get_report_service] = lambda: FakeReportService()
    client = TestClient(app)

    response = client.get(f"/api/v1/reports/{uuid4()}/verify")

    assert response.status_code == 200
    assert response.json()["data"]["signature_valid"] is True
