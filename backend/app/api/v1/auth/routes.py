from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.v1.dependencies import get_auth_service, get_biometric_auth_service, get_current_user, get_totp_service
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
from app.schemas.biometric import (
    BiometricEnrollmentRead,
    BiometricEnrollmentRequest,
    BiometricLoginRequest,
    BiometricLoginResponse,
)
from app.schemas.common import ApiResponse
from app.schemas.totp import (
    TotpDisableRequest,
    TotpEnableRequest,
    TotpSetupRequest,
    TotpSetupResponse,
    TotpStatusResponse,
    TotpVerifyRequest,
)
from app.services.auth_service import AuthService
from app.services.biometric_auth_service import BiometricAuthService
from app.services.totp_service import TotpService

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


@router.post("/biometric/enroll", response_model=ApiResponse[BiometricEnrollmentRead])
def enroll_biometric(
    payload: BiometricEnrollmentRequest,
    biometric_service: Annotated[BiometricAuthService, Depends(get_biometric_auth_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[BiometricEnrollmentRead]:
    enrollment = biometric_service.enroll(current_user, payload.images)
    return ApiResponse(data=BiometricEnrollmentRead.model_validate(enrollment), message="Biometric enrollment complete.")


@router.post("/biometric/login", response_model=ApiResponse[BiometricLoginResponse])
def biometric_login(
    payload: BiometricLoginRequest,
    biometric_service: Annotated[BiometricAuthService, Depends(get_biometric_auth_service)],
) -> ApiResponse[BiometricLoginResponse]:
    tokens = biometric_service.login(
        email=payload.email,
        face_image=payload.face_image,
        liveness_frames=payload.liveness_frames,
    )
    return ApiResponse(data=BiometricLoginResponse.model_validate(tokens), message="Biometric login successful.")


@router.post("/mfa/totp/setup", response_model=ApiResponse[TotpSetupResponse])
def setup_totp(
    payload: TotpSetupRequest,
    totp_service: Annotated[TotpService, Depends(get_totp_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[TotpSetupResponse]:
    return ApiResponse(data=totp_service.setup(current_user, payload.label), message="TOTP setup created.")


@router.post("/mfa/totp/enable", response_model=ApiResponse[TotpStatusResponse])
def enable_totp(
    payload: TotpEnableRequest,
    totp_service: Annotated[TotpService, Depends(get_totp_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[TotpStatusResponse]:
    return ApiResponse(data=totp_service.enable(current_user, payload.code), message="TOTP enabled.")


@router.post("/mfa/totp/verify", response_model=ApiResponse[TotpStatusResponse])
def verify_totp(
    payload: TotpVerifyRequest,
    totp_service: Annotated[TotpService, Depends(get_totp_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[TotpStatusResponse]:
    return ApiResponse(data=totp_service.verify(current_user, payload.code), message="TOTP verified.")


@router.post("/mfa/totp/disable", response_model=ApiResponse[TotpStatusResponse])
def disable_totp(
    payload: TotpDisableRequest,
    totp_service: Annotated[TotpService, Depends(get_totp_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[TotpStatusResponse]:
    return ApiResponse(data=totp_service.disable(current_user, payload.code), message="TOTP disabled.")


@router.get("/mfa/totp/status", response_model=ApiResponse[TotpStatusResponse])
def totp_status(
    totp_service: Annotated[TotpService, Depends(get_totp_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[TotpStatusResponse]:
    return ApiResponse(data=totp_service.status(current_user))
