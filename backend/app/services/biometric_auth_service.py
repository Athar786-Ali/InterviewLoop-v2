import logging
from datetime import timedelta
from uuid import uuid4

from fastapi import status

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import JwtService, RefreshTokenGenerator, TokenHasher, utc_now
from app.models.face_embedding import FaceEmbedding
from app.models.user import User
from app.repositories.face_embedding_repository import FaceEmbeddingRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenPair
from app.services.biometric_clients import ARC_FACE_MODEL_NAME, BlinkLivenessDetector, DeepFaceArcFaceClient
from app.services.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class BiometricAuthService:
    def __init__(
        self,
        users: UserRepository,
        face_embeddings: FaceEmbeddingRepository,
        sessions: SessionRepository,
        refresh_tokens: RefreshTokenRepository,
        arcface_client: DeepFaceArcFaceClient,
        liveness_detector: BlinkLivenessDetector,
        jwt_service: JwtService,
        token_hasher: TokenHasher,
        refresh_generator: RefreshTokenGenerator,
        rate_limiter: RateLimiter,
    ) -> None:
        self.users = users
        self.face_embeddings = face_embeddings
        self.sessions = sessions
        self.refresh_tokens = refresh_tokens
        self.arcface_client = arcface_client
        self.liveness_detector = liveness_detector
        self.jwt_service = jwt_service
        self.token_hasher = token_hasher
        self.refresh_generator = refresh_generator
        self.rate_limiter = rate_limiter

    def enroll(self, user: User, images: list[str]) -> FaceEmbedding:
        self.rate_limiter.check(f"biometric:enroll:{user.id}")
        if len(images) != 5:
            raise AppError("INVALID_ENROLLMENT_IMAGE_COUNT", "Biometric enrollment requires exactly 5 images.", 422)
        embeddings = [self.arcface_client.embedding_from_base64(image) for image in images]
        self.face_embeddings.deactivate_active_by_user(user.id)
        enrollment = self.face_embeddings.create(
            user_id=user.id,
            model_name=ARC_FACE_MODEL_NAME,
            embeddings=embeddings,
        )
        logger.info(
            "biometric_enrollment_completed",
            extra={"user_id": str(user.id), "model_name": ARC_FACE_MODEL_NAME, "image_count": len(images)},
        )
        return enrollment

    def login(self, email: str, face_image: str, liveness_frames: list[str]) -> TokenPair:
        normalized_email = email.lower()
        self.rate_limiter.check(f"biometric:login:{normalized_email}")
        user = self._get_login_user(normalized_email)
        enrollment = self.face_embeddings.get_active_by_user(user.id)
        if not enrollment:
            raise AppError("BIOMETRIC_NOT_ENROLLED", "No biometric enrollment exists for this account.", 404)

        candidate_embedding = self.arcface_client.embedding_from_base64(face_image)
        if not self.arcface_client.is_match(candidate_embedding, enrollment.embeddings):
            logger.info("biometric_face_verification_failed", extra={"user_id": str(user.id)})
            raise AppError("FACE_VERIFICATION_FAILED", "Face verification failed.", status.HTTP_401_UNAUTHORIZED)

        if not self.liveness_detector.verify(liveness_frames):
            logger.info("biometric_liveness_failed", extra={"user_id": str(user.id)})
            raise AppError("LIVENESS_CHECK_FAILED", "Blink liveness detection failed.", status.HTTP_401_UNAUTHORIZED)

        session = self.sessions.create(user_id=user.id, session_id=uuid4().hex, started_at=utc_now())
        logger.info("biometric_login_success", extra={"user_id": str(user.id), "session_id": str(session.id)})
        return self._issue_token_pair(user, session.id)

    def _get_login_user(self, email: str) -> User:
        user = self.users.get_by_email(email)
        if not user:
            raise AppError("USER_NOT_FOUND", "User was not found.", 404)
        if not user.is_active:
            raise AppError("USER_INACTIVE", "This account is inactive.", 403)
        if not user.is_email_verified:
            raise AppError("EMAIL_NOT_VERIFIED", "Verify your email before logging in.", 403)
        return user

    def _issue_token_pair(self, user: User, session_id) -> TokenPair:
        access_token, expires_in = self.jwt_service.create_access_token(user.id, session_id)
        refresh_secret = self.refresh_generator.create()
        refresh_token = self.refresh_tokens.create(
            user_id=user.id,
            session_id=session_id,
            token_hash=self.token_hasher.hash(refresh_secret),
            family_id=uuid4().hex,
            expires_at=utc_now() + timedelta(days=settings.refresh_token_days),
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=f"{refresh_token.id}.{refresh_secret}",
            expires_in=expires_in,
        )
