from datetime import timedelta
from uuid import UUID, uuid4

from fastapi import status

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import JwtService, OtpGenerator, PasswordHasher, RefreshTokenGenerator, TokenHasher, utc_now
from app.models.refresh_token import RefreshToken
from app.models.session import Session
from app.models.user import User
from app.repositories.otp_token_repository import OtpTokenRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, ResetPasswordRequest, SignupRequest, TokenPair
from app.services.email_service import EmailService
from app.services.rate_limiter import RateLimiter

EMAIL_VERIFICATION_PURPOSE = "email_verification"
PASSWORD_RESET_PURPOSE = "password_reset"


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        otp_tokens: OtpTokenRepository,
        sessions: SessionRepository,
        refresh_tokens: RefreshTokenRepository,
        passwords: PasswordHasher,
        token_hasher: TokenHasher,
        jwt_service: JwtService,
        otp_generator: OtpGenerator,
        refresh_generator: RefreshTokenGenerator,
        email_service: EmailService,
        rate_limiter: RateLimiter,
    ) -> None:
        self.users = users
        self.otp_tokens = otp_tokens
        self.sessions = sessions
        self.refresh_tokens = refresh_tokens
        self.passwords = passwords
        self.token_hasher = token_hasher
        self.jwt_service = jwt_service
        self.otp_generator = otp_generator
        self.refresh_generator = refresh_generator
        self.email_service = email_service
        self.rate_limiter = rate_limiter

    def signup(self, payload: SignupRequest) -> User:
        email = payload.email.lower()
        self.rate_limiter.check(f"auth:signup:{email}")

        if self.users.get_by_email(email):
            raise AppError("EMAIL_ALREADY_REGISTERED", "An account already exists for this email.", status.HTTP_409_CONFLICT)

        user = self.users.create(
            email=email,
            password_hash=self.passwords.hash(payload.password),
            full_name=payload.full_name,
        )
        self._issue_otp(email=email, purpose=EMAIL_VERIFICATION_PURPOSE, user=user)
        return user

    def verify_email(self, email: str, otp: str) -> User:
        normalized_email = email.lower()
        self.rate_limiter.check(f"auth:verify-email:{normalized_email}")
        user = self._get_user_by_email(normalized_email)
        self._consume_otp(normalized_email, otp, EMAIL_VERIFICATION_PURPOSE)
        user.is_email_verified = True
        return self.users.save(user)

    def login(self, payload: LoginRequest) -> TokenPair:
        email = payload.email.lower()
        self.rate_limiter.check(f"auth:login:{email}")
        user = self._get_user_by_email(email)

        if not self.passwords.verify(payload.password, user.password_hash):
            raise AppError("INVALID_CREDENTIALS", "Invalid email or password.", status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            raise AppError("USER_INACTIVE", "This account is inactive.", status.HTTP_403_FORBIDDEN)
        if not user.is_email_verified:
            raise AppError("EMAIL_NOT_VERIFIED", "Verify your email before logging in.", status.HTTP_403_FORBIDDEN)

        session = self.sessions.create(user_id=user.id, session_id=uuid4().hex, started_at=utc_now())
        return self._issue_token_pair(user, session)

    def refresh(self, raw_refresh_token: str) -> TokenPair:
        token = self._get_refresh_token(raw_refresh_token)
        secret = self._parse_refresh_token(raw_refresh_token)[1]

        if token.revoked_at or token.expires_at <= utc_now() or not self.token_hasher.verify(secret, token.token_hash):
            raise AppError("INVALID_REFRESH_TOKEN", "Invalid or expired refresh token.", status.HTTP_401_UNAUTHORIZED)

        user = token.user
        session = token.session
        if not user.is_active or session.status != "active":
            raise AppError("INVALID_SESSION", "Session is no longer active.", status.HTTP_401_UNAUTHORIZED)

        token.revoked_at = utc_now()
        new_secret = self.refresh_generator.create()
        new_token = self.refresh_tokens.create(
            user_id=user.id,
            session_id=session.id,
            token_hash=self.token_hasher.hash(new_secret),
            family_id=token.family_id,
            expires_at=utc_now() + timedelta(days=settings.refresh_token_days),
        )
        token.replaced_by_token_hash = new_token.token_hash
        self.refresh_tokens.save(token)

        access_token, expires_in = self.jwt_service.create_access_token(user.id, session.id)
        return TokenPair(
            access_token=access_token,
            refresh_token=f"{new_token.id}.{new_secret}",
            expires_in=expires_in,
        )

    def logout(self, user: User, raw_refresh_token: str | None, session_id: UUID | None) -> None:
        if raw_refresh_token:
            token = self._get_refresh_token(raw_refresh_token)
            if token.user_id != user.id:
                raise AppError("INVALID_REFRESH_TOKEN", "Invalid refresh token.", status.HTTP_401_UNAUTHORIZED)
            token.revoked_at = utc_now()
            self.refresh_tokens.save(token)

        if session_id:
            session = self.sessions.get_active_for_user(session_id=session_id, user_id=user.id)
            if not session:
                raise AppError("SESSION_NOT_FOUND", "Session was not found.", status.HTTP_404_NOT_FOUND)
            self._revoke_session(session)

    def forgot_password(self, email: str) -> None:
        normalized_email = email.lower()
        self.rate_limiter.check(f"auth:forgot-password:{normalized_email}")
        user = self.users.get_by_email(normalized_email)
        if user:
            self._issue_otp(email=normalized_email, purpose=PASSWORD_RESET_PURPOSE, user=user)

    def reset_password(self, payload: ResetPasswordRequest) -> None:
        email = payload.email.lower()
        self.rate_limiter.check(f"auth:reset-password:{email}")
        user = self._get_user_by_email(email)
        self._consume_otp(email, payload.otp, PASSWORD_RESET_PURPOSE)
        user.password_hash = self.passwords.hash(payload.new_password)
        self.users.save(user)
        self._revoke_all_user_sessions(user.id)

    def list_sessions(self, user: User) -> list[Session]:
        return self.sessions.list_active_by_user(user.id)

    def revoke_session(self, user: User, session_id: UUID) -> None:
        session = self.sessions.get_active_for_user(session_id=session_id, user_id=user.id)
        if not session:
            raise AppError("SESSION_NOT_FOUND", "Session was not found.", status.HTTP_404_NOT_FOUND)
        self._revoke_session(session)

    def _issue_otp(self, email: str, purpose: str, user: User) -> None:
        otp = self.otp_generator.create()
        self.otp_tokens.create(
            email=email,
            token_hash=self.token_hasher.hash(otp),
            purpose=purpose,
            expires_at=utc_now() + timedelta(minutes=settings.otp_ttl_minutes),
            user_id=user.id,
        )
        self.email_service.send_otp(email=email, otp=otp, purpose=purpose)

    def _consume_otp(self, email: str, otp: str, purpose: str) -> None:
        token = self.otp_tokens.get_latest_active(email=email, purpose=purpose)
        if not token or token.expires_at <= utc_now() or not self.token_hasher.verify(otp, token.token_hash):
            raise AppError("INVALID_OTP", "Invalid or expired OTP.", status.HTTP_400_BAD_REQUEST)
        token.consumed_at = utc_now()
        self.otp_tokens.save(token)

    def _issue_token_pair(self, user: User, session: Session) -> TokenPair:
        access_token, expires_in = self.jwt_service.create_access_token(user.id, session.id)
        refresh_secret = self.refresh_generator.create()
        refresh_token = self.refresh_tokens.create(
            user_id=user.id,
            session_id=session.id,
            token_hash=self.token_hasher.hash(refresh_secret),
            family_id=uuid4().hex,
            expires_at=utc_now() + timedelta(days=settings.refresh_token_days),
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=f"{refresh_token.id}.{refresh_secret}",
            expires_in=expires_in,
        )

    def _get_refresh_token(self, raw_refresh_token: str) -> RefreshToken:
        token_id, _ = self._parse_refresh_token(raw_refresh_token)
        token = self.refresh_tokens.get_by_id(token_id)
        if not token:
            raise AppError("INVALID_REFRESH_TOKEN", "Invalid refresh token.", status.HTTP_401_UNAUTHORIZED)
        return token

    def _parse_refresh_token(self, raw_refresh_token: str) -> tuple[UUID, str]:
        try:
            token_id, secret = raw_refresh_token.split(".", 1)
            return UUID(token_id), secret
        except ValueError as exc:
            raise AppError("INVALID_REFRESH_TOKEN", "Invalid refresh token.", status.HTTP_401_UNAUTHORIZED) from exc

    def _get_user_by_email(self, email: str) -> User:
        user = self.users.get_by_email(email)
        if not user:
            raise AppError("USER_NOT_FOUND", "User was not found.", status.HTTP_404_NOT_FOUND)
        return user

    def _revoke_session(self, session: Session) -> None:
        session.status = "revoked"
        session.completed_at = utc_now()
        self.sessions.save(session)

    def _revoke_all_user_sessions(self, user_id: UUID) -> None:
        for session in self.sessions.list_active_by_user(user_id):
            self._revoke_session(session)
        for token in self.refresh_tokens.list_active_by_user(user_id):
            token.revoked_at = utc_now()
            self.refresh_tokens.save(token)
