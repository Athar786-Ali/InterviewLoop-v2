from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_current_user, get_totp_service
from app.core.exceptions import AppError
from app.main import create_app
from app.schemas.totp import TotpSetupResponse, TotpStatusResponse


class FakeTotpService:
    def setup(self, user, label):
        return TotpSetupResponse(
            credential_id=uuid4(),
            provisioning_uri="otpauth://totp/InterviewLoop-v2:candidate@example.com",
            qr_code_data_url="data:image/png;base64,abc",
            recovery_codes=["one", "two"],
        )

    def verify(self, user, code):
        if code == "000000":
            raise AppError("INVALID_MFA_CODE", "Invalid MFA code.", 401)
        return TotpStatusResponse(is_enabled=True, recovery_codes_remaining=2)


def current_user():
    return SimpleNamespace(id=uuid4(), email="candidate@example.com", is_active=True)


def test_totp_setup_route_returns_structured_response():
    app = create_app()
    app.dependency_overrides[get_current_user] = current_user
    app.dependency_overrides[get_totp_service] = lambda: FakeTotpService()
    client = TestClient(app)

    response = client.post("/api/v1/auth/mfa/totp/setup", json={"label": "Candidate"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["qr_code_data_url"].startswith("data:image/png;base64,")
    assert body["data"]["recovery_codes"] == ["one", "two"]


def test_totp_verify_route_returns_structured_error_response():
    app = create_app()
    app.dependency_overrides[get_current_user] = current_user
    app.dependency_overrides[get_totp_service] = lambda: FakeTotpService()
    client = TestClient(app)

    response = client.post("/api/v1/auth/mfa/totp/verify", json={"code": "000000"})

    assert response.status_code == 401
    assert response.json() == {
        "success": False,
        "error": {"code": "INVALID_MFA_CODE", "message": "Invalid MFA code."},
    }
