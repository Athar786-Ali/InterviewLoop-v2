from types import SimpleNamespace
from uuid import uuid4

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
