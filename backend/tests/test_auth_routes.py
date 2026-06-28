from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_auth_service
from app.core.exceptions import AppError
from app.main import create_app


class SignupService:
    def signup(self, payload):
        return SimpleNamespace(
            id=uuid4(),
            email=payload.email,
            full_name=payload.full_name,
            is_email_verified=False,
            is_active=True,
        )


class FailingSignupService:
    def signup(self, payload):
        raise AppError("EMAIL_ALREADY_REGISTERED", "An account already exists for this email.", 409)


class VerifyEmailService:
    def __init__(self):
        self.calls = []

    def verify_email(self, email, otp):
        self.calls.append((email, otp))
        return SimpleNamespace(
            id=uuid4(),
            email=email,
            full_name=None,
            is_email_verified=True,
            is_active=True,
        )


def test_signup_route_returns_structured_success_response():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: SignupService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "candidate@example.com", "password": "very-secure-password", "full_name": "Candidate"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "candidate@example.com"
    assert body["data"]["is_email_verified"] is False


def test_signup_route_returns_structured_error_response():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: FailingSignupService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "candidate@example.com", "password": "very-secure-password"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "success": False,
        "error": {
            "code": "EMAIL_ALREADY_REGISTERED",
            "message": "An account already exists for this email.",
        },
    }


def test_verify_email_route_accepts_otp_field():
    service = VerifyEmailService()
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: service
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/verify-email",
        json={"email": "candidate@example.com", "otp": "123456"},
    )

    assert response.status_code == 200
    assert service.calls == [("candidate@example.com", "123456")]
    assert response.json()["data"]["is_email_verified"] is True


@pytest.mark.parametrize("payload", [{"email": "candidate@example.com", "otp_code": "123456"}])
def test_verify_email_route_rejects_old_otp_code_field(payload):
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: VerifyEmailService()
    client = TestClient(app)

    response = client.post("/api/v1/auth/verify-email", json=payload)

    assert response.status_code == 422
