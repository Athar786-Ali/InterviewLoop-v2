from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from sqlalchemy.orm import Session as DbSession

from app.core.config import settings
from app.core.encryption import SecretCipher
from app.core.exceptions import AppError
from app.core.security import JwtService, OtpGenerator, PasswordHasher, RefreshTokenGenerator, TokenHasher
from app.db.session import get_db
from app.models.user import User
from app.repositories.otp_token_repository import OtpTokenRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.face_embedding_repository import FaceEmbeddingRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.totp_credential_repository import TotpCredentialRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.analytics_service import AnalyticsService
from app.services.biometric_auth_service import BiometricAuthService
from app.services.biometric_clients import get_arcface_client, get_liveness_detector
from app.services.email_service import EmailService
from app.services.adaptive_difficulty import AdaptiveDifficultyService
from app.services.conversation_memory import RedisConversationMemory
from app.services.code_execution_service import CodeExecutionService, DockerSandboxRunner
from app.services.interview_engine import InterviewEngineService
from app.services.llm_service import OllamaLLMService
from app.services.rate_limiter import RateLimiter
from app.services.report_crypto import ReportSignatureService
from app.services.report_pdf import ReportPdfRenderer
from app.services.report_service import ReportService
from app.services.totp_service import TotpService
from app.services.deepgram_service import DeepgramStreamingService
from app.services.speech_service import TypedFallbackService

Db = Annotated[DbSession, Depends(get_db)]
bearer_scheme = HTTPBearer(auto_error=False)


def get_redis() -> Redis:
    return Redis.from_url(str(settings.redis_url), decode_responses=True)


def get_auth_service(db: Db, redis_client: Annotated[Redis, Depends(get_redis)]) -> AuthService:
    token_hasher = TokenHasher()
    totp_repository = TotpCredentialRepository(db)
    rate_limiter = RateLimiter(redis_client)
    totp_service = TotpService(
        credentials=totp_repository,
        cipher=SecretCipher(),
        token_hasher=token_hasher,
        rate_limiter=rate_limiter,
    )
    return AuthService(
        users=UserRepository(db),
        otp_tokens=OtpTokenRepository(db),
        sessions=SessionRepository(db),
        refresh_tokens=RefreshTokenRepository(db),
        passwords=PasswordHasher(),
        token_hasher=token_hasher,
        jwt_service=JwtService(),
        otp_generator=OtpGenerator(),
        refresh_generator=RefreshTokenGenerator(),
        email_service=EmailService(),
        rate_limiter=rate_limiter,
        totp_credentials=totp_repository,
        totp_service=totp_service,
    )


def get_biometric_auth_service(db: Db, redis_client: Annotated[Redis, Depends(get_redis)]) -> BiometricAuthService:
    return BiometricAuthService(
        users=UserRepository(db),
        face_embeddings=FaceEmbeddingRepository(db),
        sessions=SessionRepository(db),
        refresh_tokens=RefreshTokenRepository(db),
        arcface_client=get_arcface_client(),
        liveness_detector=get_liveness_detector(),
        jwt_service=JwtService(),
        token_hasher=TokenHasher(),
        refresh_generator=RefreshTokenGenerator(),
        rate_limiter=RateLimiter(redis_client),
    )


def get_totp_service(db: Db, redis_client: Annotated[Redis, Depends(get_redis)]) -> TotpService:
    return TotpService(
        credentials=TotpCredentialRepository(db),
        cipher=SecretCipher(),
        token_hasher=TokenHasher(),
        rate_limiter=RateLimiter(redis_client),
    )


def get_interview_engine(redis_client: Annotated[Redis, Depends(get_redis)]) -> InterviewEngineService:
    return InterviewEngineService(
        llm_service=OllamaLLMService(),
        memory=RedisConversationMemory(redis_client),
        difficulty_service=AdaptiveDifficultyService(),
    )


def get_deepgram_service() -> DeepgramStreamingService:
    return DeepgramStreamingService()


def get_typed_fallback_service() -> TypedFallbackService:
    return TypedFallbackService()


def get_analytics_service(db: Db) -> AnalyticsService:
    return AnalyticsService(AnalyticsRepository(db))


def get_code_execution_service() -> CodeExecutionService:
    return CodeExecutionService(DockerSandboxRunner())


def get_report_service(db: Db) -> ReportService:
    return ReportService(
        reports=ReportRepository(db),
        audit_logs=AuditLogRepository(db),
        sessions=SessionRepository(db),
        signer=ReportSignatureService(),
        pdf_renderer=ReportPdfRenderer(),
    )


def get_current_user(
    db: Db,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if not credentials:
        raise AppError("NOT_AUTHENTICATED", "Authentication is required.", 401)

    payload = JwtService().decode_access_token(credentials.credentials)
    try:
        user_id = UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise AppError("INVALID_ACCESS_TOKEN", "Invalid access token.", 401) from exc

    user = UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise AppError("NOT_AUTHENTICATED", "Authentication is required.", 401)
    return user
