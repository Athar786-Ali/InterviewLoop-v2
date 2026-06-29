from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import AppError
from app.schemas.auth import LoginRequest, SignupRequest
from app.services.auth_service import AuthService, EMAIL_VERIFICATION_PURPOSE


class FakeUsers:
    def __init__(self):
        self.by_email = {}

    def get_by_email(self, email):
        return self.by_email.get(email)

    def create(self, email, password_hash, full_name):
        user = SimpleNamespace(
            id=uuid4(),
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            is_active=True,
            is_email_verified=False,
        )
        self.by_email[email] = user
        return user

    def save(self, user):
        self.by_email[user.email] = user
        return user


class FakeOtpTokens:
    def __init__(self):
        self.tokens = []

    def create(self, email, token_hash, purpose, expires_at, user_id):
        token = SimpleNamespace(
            email=email,
            token_hash=token_hash,
            purpose=purpose,
            expires_at=expires_at,
            user_id=user_id,
            consumed_at=None,
        )
        self.tokens.append(token)
        return token

    def get_latest_active(self, email, purpose):
        matches = [token for token in self.tokens if token.email == email and token.purpose == purpose and not token.consumed_at]
        return matches[-1] if matches else None

    def save(self, token):
        return token


class FakeSessions:
    def __init__(self):
        self.sessions = []

    def create(self, user_id, session_id, started_at):
        session = SimpleNamespace(
            id=uuid4(),
            user_id=user_id,
            session_id=session_id,
            status="active",
            started_at=started_at,
            completed_at=None,
            created_at=started_at,
        )
        self.sessions.append(session)
        return session

    def list_active_by_user(self, user_id):
        return [session for session in self.sessions if session.user_id == user_id and session.status == "active"]


class FakeRefreshTokens:
    def __init__(self):
        self.tokens = []

    def create(self, user_id, session_id, token_hash, family_id, expires_at):
        token = SimpleNamespace(
            id=uuid4(),
            user_id=user_id,
            session_id=session_id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,
            revoked_at=None,
        )
        self.tokens.append(token)
        return token

    def list_active_by_user(self, user_id):
        return [token for token in self.tokens if token.user_id == user_id and not token.revoked_at]


class FakePasswordHasher:
    def hash(self, value):
        return f"hashed:{value}"

    def verify(self, value, value_hash):
        return value_hash == f"hashed:{value}"


class FakeTokenHasher(FakePasswordHasher):
    pass


class FakeJwtService:
    def create_access_token(self, user_id, session_id):
        return f"access:{user_id}:{session_id}", 900


class FakeOtpGenerator:
    def create(self):
        return "123456"


class FakeRefreshGenerator:
    def create(self):
        return "refresh-secret"


class FakeEmailService:
    def __init__(self):
        self.sent = []

    def send_otp(self, email, otp, purpose):
        self.sent.append((email, otp, purpose))


class FakeRateLimiter:
    def check(self, key):
        return None


@pytest.fixture
def auth_context():
    email_service = FakeEmailService()
    service = AuthService(
        users=FakeUsers(),
        otp_tokens=FakeOtpTokens(),
        sessions=FakeSessions(),
        refresh_tokens=FakeRefreshTokens(),
        passwords=FakePasswordHasher(),
        token_hasher=FakeTokenHasher(),
        jwt_service=FakeJwtService(),
        otp_generator=FakeOtpGenerator(),
        refresh_generator=FakeRefreshGenerator(),
        email_service=email_service,
        rate_limiter=FakeRateLimiter(),
    )
    return service, email_service


def test_signup_creates_user_and_sends_email_verification_otp(auth_context):
    service, email = auth_context

    user = service.signup(
        SignupRequest(email="Candidate@Example.com", password="very-secure-password", full_name="Candidate")
    )

    assert user.email == "candidate@example.com"
    assert user.password_hash == "hashed:very-secure-password"
    assert email.sent == [("candidate@example.com", "123456", EMAIL_VERIFICATION_PURPOSE)]


def test_verify_email_consumes_otp_and_marks_user_verified(auth_context):
    service, _ = auth_context
    user = service.signup(SignupRequest(email="candidate@example.com", password="very-secure-password"))

    verified = service.verify_email("candidate@example.com", "123456")

    assert verified.id == user.id
    assert verified.is_email_verified is True


def test_login_rejects_unverified_email(auth_context):
    service, _ = auth_context
    service.signup(SignupRequest(email="candidate@example.com", password="very-secure-password"))

    with pytest.raises(AppError) as error:
        service.login(LoginRequest(email="candidate@example.com", password="very-secure-password"))

    assert error.value.code == "EMAIL_NOT_VERIFIED"


def test_login_issues_access_and_refresh_tokens_for_verified_user(auth_context):
    service, _ = auth_context
    service.signup(SignupRequest(email="candidate@example.com", password="very-secure-password"))
    service.verify_email("candidate@example.com", "123456")

    tokens = service.login(LoginRequest(email="candidate@example.com", password="very-secure-password"))

    assert tokens.access_token.startswith("access:")
    assert tokens.refresh_token.endswith(".refresh-secret")
    assert tokens.expires_in == 900


def test_login_rejects_wrong_password(auth_context):
    service, _ = auth_context
    service.signup(SignupRequest(email="candidate@example.com", password="very-secure-password"))
    service.verify_email("candidate@example.com", "123456")

    with pytest.raises(AppError) as error:
        service.login(LoginRequest(email="candidate@example.com", password="wrong-password"))

    assert error.value.code == "INVALID_CREDENTIALS"
