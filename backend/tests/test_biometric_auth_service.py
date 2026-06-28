from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import AppError
from app.services.biometric_auth_service import BiometricAuthService
from app.services.biometric_clients import ARC_FACE_MODEL_NAME, get_arcface_client, get_liveness_detector


class FakeUsers:
    def __init__(self, user):
        self.user = user

    def get_by_email(self, email):
        return self.user if self.user.email == email else None


class FakeFaceEmbeddings:
    def __init__(self):
        self.active = None
        self.created = []
        self.deactivated = False

    def create(self, user_id, model_name, embeddings):
        enrollment = SimpleNamespace(
            id=uuid4(),
            user_id=user_id,
            model_name=model_name,
            embeddings=embeddings,
            is_active=True,
        )
        self.active = enrollment
        self.created.append(enrollment)
        return enrollment

    def get_active_by_user(self, user_id):
        if self.active and self.active.user_id == user_id and self.active.is_active:
            return self.active
        return None

    def deactivate_active_by_user(self, user_id):
        if self.active and self.active.user_id == user_id:
            self.active.is_active = False
            self.deactivated = True


class FakeSessions:
    def create(self, user_id, session_id, started_at):
        return SimpleNamespace(id=uuid4(), user_id=user_id, session_id=session_id, started_at=started_at, status="active")


class FakeRefreshTokens:
    def create(self, user_id, session_id, token_hash, family_id, expires_at):
        return SimpleNamespace(id=uuid4(), user_id=user_id, session_id=session_id, token_hash=token_hash)


class FakeArcFace:
    def __init__(self, match=True):
        self.match = match
        self.calls = []

    def embedding_from_base64(self, image):
        self.calls.append(image)
        return [1.0, 0.0, 0.0]

    def is_match(self, candidate, enrolled_embeddings):
        return self.match


class FakeLiveness:
    def __init__(self, live=True):
        self.live = live

    def verify(self, frames):
        return self.live


class FakeJwt:
    def create_access_token(self, user_id, session_id):
        return f"access:{user_id}:{session_id}", 900


class FakeTokenHasher:
    def hash(self, value):
        return f"hashed:{value}"


class FakeRefreshGenerator:
    def create(self):
        return "refresh-secret"


class FakeRateLimiter:
    def check(self, key):
        return None


@pytest.fixture
def verified_user():
    return SimpleNamespace(
        id=uuid4(),
        email="candidate@example.com",
        is_active=True,
        is_email_verified=True,
    )


def build_service(user, face_repo, arcface=None, liveness=None):
    return BiometricAuthService(
        users=FakeUsers(user),
        face_embeddings=face_repo,
        sessions=FakeSessions(),
        refresh_tokens=FakeRefreshTokens(),
        arcface_client=arcface or FakeArcFace(),
        liveness_detector=liveness or FakeLiveness(),
        jwt_service=FakeJwt(),
        token_hasher=FakeTokenHasher(),
        refresh_generator=FakeRefreshGenerator(),
        rate_limiter=FakeRateLimiter(),
    )


def test_biometric_enrollment_requires_five_images_and_stores_arcface_embeddings(verified_user):
    face_repo = FakeFaceEmbeddings()
    service = build_service(verified_user, face_repo)

    enrollment = service.enroll(verified_user, ["a", "b", "c", "d", "e"])

    assert enrollment.model_name == ARC_FACE_MODEL_NAME
    assert len(enrollment.embeddings) == 5
    assert face_repo.created == [enrollment]


def test_biometric_enrollment_rejects_wrong_image_count(verified_user):
    service = build_service(verified_user, FakeFaceEmbeddings())

    with pytest.raises(AppError) as error:
        service.enroll(verified_user, ["a", "b"])

    assert error.value.code == "INVALID_ENROLLMENT_IMAGE_COUNT"


def test_biometric_login_verifies_face_liveness_and_issues_tokens(verified_user):
    face_repo = FakeFaceEmbeddings()
    face_repo.create(verified_user.id, ARC_FACE_MODEL_NAME, [[1.0, 0.0, 0.0]])
    service = build_service(verified_user, face_repo)

    tokens = service.login("candidate@example.com", "face-image", ["open", "closed", "open"])

    assert tokens.access_token.startswith("access:")
    assert tokens.refresh_token.endswith(".refresh-secret")
    assert tokens.expires_in == 900


def test_biometric_login_rejects_face_mismatch(verified_user):
    face_repo = FakeFaceEmbeddings()
    face_repo.create(verified_user.id, ARC_FACE_MODEL_NAME, [[1.0, 0.0, 0.0]])
    service = build_service(verified_user, face_repo, arcface=FakeArcFace(match=False))

    with pytest.raises(AppError) as error:
        service.login("candidate@example.com", "face-image", ["open", "closed", "open"])

    assert error.value.code == "FACE_VERIFICATION_FAILED"


def test_biometric_login_rejects_failed_liveness(verified_user):
    face_repo = FakeFaceEmbeddings()
    face_repo.create(verified_user.id, ARC_FACE_MODEL_NAME, [[1.0, 0.0, 0.0]])
    service = build_service(verified_user, face_repo, liveness=FakeLiveness(live=False))

    with pytest.raises(AppError) as error:
        service.login("candidate@example.com", "face-image", ["open", "closed", "open"])

    assert error.value.code == "LIVENESS_CHECK_FAILED"


def test_biometric_singletons_reuse_instances():
    assert get_arcface_client() is get_arcface_client()
    assert get_liveness_detector() is get_liveness_detector()
