from types import SimpleNamespace
from uuid import uuid4

import pyotp
import pytest

from app.core.exceptions import AppError
from app.services.totp_service import TotpService


class FakeCredentialRepo:
    def __init__(self):
        self.credential = None

    def create(self, user_id, encrypted_secret, recovery_code_hashes, label):
        self.credential = SimpleNamespace(
            id=uuid4(),
            user_id=user_id,
            encrypted_secret=encrypted_secret,
            recovery_code_hashes=list(recovery_code_hashes),
            recovery_code_metadata={"remaining": len(recovery_code_hashes)},
            is_enabled=False,
            label=label,
        )
        return self.credential

    def get_latest_by_user(self, user_id):
        return self.credential if self.credential and self.credential.user_id == user_id else None

    def get_enabled_by_user(self, user_id):
        if self.credential and self.credential.user_id == user_id and self.credential.is_enabled:
            return self.credential
        return None

    def save(self, credential):
        self.credential = credential
        return credential


class FakeCipher:
    def encrypt(self, value):
        return f"encrypted:{value}".encode()

    def decrypt(self, value):
        return value.decode().removeprefix("encrypted:")


class FakeHasher:
    def hash(self, value):
        return f"hashed:{value}"

    def verify(self, value, value_hash):
        return value_hash == f"hashed:{value}"


class FakeRateLimiter:
    def check(self, key):
        return None


@pytest.fixture
def user():
    return SimpleNamespace(id=uuid4(), email="candidate@example.com")


@pytest.fixture
def service_context(monkeypatch):
    repo = FakeCredentialRepo()
    monkeypatch.setattr("app.services.totp_service.pyotp.random_base32", lambda: "JBSWY3DPEHPK3PXP")
    monkeypatch.setattr(
        "app.services.totp_service.TotpService._generate_recovery_codes",
        lambda self: ["RCODE-1", "RCODE-2"],
    )
    service = TotpService(repo, FakeCipher(), FakeHasher(), FakeRateLimiter())
    return service, repo


def test_totp_setup_returns_google_authenticator_uri_qr_and_recovery_codes(service_context, user):
    service, repo = service_context

    setup = service.setup(user, label="Candidate")

    assert setup.credential_id == repo.credential.id
    assert "otpauth://totp/" in setup.provisioning_uri
    assert "issuer=InterviewLoop-v2" in setup.provisioning_uri
    assert setup.qr_code_data_url.startswith("data:image/png;base64,")
    assert setup.recovery_codes == ["RCODE-1", "RCODE-2"]
    assert repo.credential.encrypted_secret != b"JBSWY3DPEHPK3PXP"


def test_totp_enable_verifies_code_and_marks_enabled(service_context, user):
    service, repo = service_context
    service.setup(user, label=None)
    code = pyotp.TOTP("JBSWY3DPEHPK3PXP").now()

    status = service.enable(user, code)

    assert status.is_enabled is True
    assert repo.credential.is_enabled is True
    assert status.recovery_codes_remaining == 2


def test_totp_verify_accepts_and_consumes_recovery_code(service_context, user):
    service, repo = service_context
    service.setup(user, label=None)
    service.enable(user, pyotp.TOTP("JBSWY3DPEHPK3PXP").now())

    status = service.verify(user, "RCODE-1")

    assert status.is_enabled is True
    assert status.recovery_codes_remaining == 1
    assert repo.credential.recovery_code_hashes == ["hashed:RCODE-2"]


def test_totp_recovery_code_cannot_be_reused(service_context, user):
    service, _ = service_context
    service.setup(user, label=None)
    service.enable(user, pyotp.TOTP("JBSWY3DPEHPK3PXP").now())
    service.verify(user, "RCODE-1")

    with pytest.raises(AppError) as error:
        service.verify(user, "RCODE-1")

    assert error.value.code == "INVALID_MFA_CODE"


def test_totp_disable_requires_valid_code(service_context, user):
    service, repo = service_context
    service.setup(user, label=None)
    service.enable(user, pyotp.TOTP("JBSWY3DPEHPK3PXP").now())

    status = service.disable(user, pyotp.TOTP("JBSWY3DPEHPK3PXP").now())

    assert status.is_enabled is False
    assert repo.credential.is_enabled is False
