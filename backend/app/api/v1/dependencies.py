from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session as DbSession

from app.core.exceptions import AppError
from app.core.security import JwtService, OtpGenerator, PasswordHasher, RefreshTokenGenerator, TokenHasher
from app.db.session import get_db
from app.models.user import User
from app.repositories.otp_token_repository import OtpTokenRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.analytics_service import AnalyticsService
from app.services.email_service import EmailService
from app.services.adaptive_difficulty import AdaptiveDifficultyService
from app.services.conversation_memory import ConversationMemory
from app.services.code_execution_service import CodeExecutionService, DockerSandboxRunner
from app.services.interview_engine import InterviewEngineService
from app.services.llm_service import OllamaLLMService
from app.services.rate_limiter import RateLimiter
from app.services.hint_engine import HintEngineService
from app.services.report_crypto import ReportSignatureService
from app.services.report_pdf import ReportPdfRenderer
from app.services.report_service import ReportService
from app.services.resume_parser import ResumeParserService
from app.services.deepgram_service import DeepgramStreamingService
from app.services.speech_service import TypedFallbackService

Db = Annotated[DbSession, Depends(get_db)]
bearer_scheme = HTTPBearer(auto_error=False)

# Module-level singletons for stateful in-memory services.
# These are intentionally process-scoped so session memory and rate limit
# counters persist across requests within the same worker process.
_rate_limiter = RateLimiter()
_conversation_memory = ConversationMemory()


def get_auth_service(db: Db) -> AuthService:
    return AuthService(
        users=UserRepository(db),
        otp_tokens=OtpTokenRepository(db),
        sessions=SessionRepository(db),
        refresh_tokens=RefreshTokenRepository(db),
        passwords=PasswordHasher(),
        token_hasher=TokenHasher(),
        jwt_service=JwtService(),
        otp_generator=OtpGenerator(),
        refresh_generator=RefreshTokenGenerator(),
        email_service=EmailService(),
        rate_limiter=_rate_limiter,
    )


def get_interview_engine() -> InterviewEngineService:
    return InterviewEngineService(
        llm_service=OllamaLLMService(),
        memory=_conversation_memory,
        difficulty_service=AdaptiveDifficultyService(),
    )


def get_hint_engine() -> HintEngineService:
    return HintEngineService(
        llm_service=OllamaLLMService(),
        memory=_conversation_memory,
    )


def get_resume_parser() -> ResumeParserService:
    return ResumeParserService()


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
