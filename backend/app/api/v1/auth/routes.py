from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.v1.dependencies import get_auth_service, get_current_user
from app.models.user import User
from app.schemas.auth import (
    AuthUserRead,
    EmailVerificationRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    ResetPasswordRequest,
    SessionRead,
    SignupRequest,
    TokenPair,
)
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=ApiResponse[AuthUserRead], status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse[AuthUserRead]:
    user = auth_service.signup(payload)
    return ApiResponse(
        data=AuthUserRead.model_validate(user),
        message="Signup successful. Check your email for the verification OTP.",
    )


@router.post("/verify-email", response_model=ApiResponse[AuthUserRead])
def verify_email(
    payload: EmailVerificationRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse[AuthUserRead]:
    user = auth_service.verify_email(email=payload.email, otp=payload.otp)
    return ApiResponse(data=AuthUserRead.model_validate(user), message="Email verified successfully.")


@router.post("/login", response_model=ApiResponse[TokenPair])
def login(
    payload: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse[TokenPair]:
    return ApiResponse(data=auth_service.login(payload), message="Login successful.")


@router.post("/refresh", response_model=ApiResponse[TokenPair])
def refresh(
    payload: RefreshRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse[TokenPair]:
    return ApiResponse(data=auth_service.refresh(payload.refresh_token), message="Token refreshed.")


@router.post("/logout", response_model=ApiResponse[None])
def logout(
    payload: LogoutRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[None]:
    auth_service.logout(current_user, raw_refresh_token=payload.refresh_token, session_id=payload.session_id)
    return ApiResponse(message="Logout successful.")


@router.post("/forgot-password", response_model=ApiResponse[None])
def forgot_password(
    payload: ForgotPasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse[None]:
    auth_service.forgot_password(payload.email)
    return ApiResponse(message="If the account exists, a password reset OTP has been sent.")


@router.post("/reset-password", response_model=ApiResponse[None])
def reset_password(
    payload: ResetPasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse[None]:
    auth_service.reset_password(payload)
    return ApiResponse(message="Password reset successful.")


@router.get("/sessions", response_model=ApiResponse[list[SessionRead]])
def list_sessions(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[list[SessionRead]]:
    sessions = [SessionRead.model_validate(session) for session in auth_service.list_sessions(current_user)]
    return ApiResponse(data=sessions)


@router.delete("/sessions/{session_id}", response_model=ApiResponse[None])
def revoke_session(
    session_id: UUID,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[None]:
    auth_service.revoke_session(current_user, session_id)
    return ApiResponse(message="Session revoked.")
