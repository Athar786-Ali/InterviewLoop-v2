import base64
import io
import logging
from secrets import token_urlsafe
from uuid import UUID

import pyotp
import qrcode

from app.core.config import settings
from app.core.encryption import SecretCipher
from app.core.exceptions import AppError
from app.core.security import TokenHasher
from app.models.totp_credential import TotpCredential
from app.models.user import User
from app.repositories.totp_credential_repository import TotpCredentialRepository
from app.schemas.totp import TotpSetupResponse, TotpStatusResponse
from app.services.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class TotpService:
    def __init__(
        self,
        credentials: TotpCredentialRepository,
        cipher: SecretCipher,
        token_hasher: TokenHasher,
        rate_limiter: RateLimiter,
    ) -> None:
        self.credentials = credentials
        self.cipher = cipher
        self.token_hasher = token_hasher
        self.rate_limiter = rate_limiter

    def setup(self, user: User, label: str | None) -> TotpSetupResponse:
        self.rate_limiter.check(f"mfa:setup:{user.id}")
        secret = pyotp.random_base32()
        recovery_codes = self._generate_recovery_codes()
        credential = self.credentials.create(
            user_id=user.id,
            encrypted_secret=self.cipher.encrypt(secret),
            recovery_code_hashes=[self.token_hasher.hash(code) for code in recovery_codes],
            label=label,
        )
        account_name = label or user.email
        provisioning_uri = pyotp.TOTP(secret).provisioning_uri(
            name=account_name,
            issuer_name=settings.totp_issuer_name,
        )
        logger.info("totp_setup_created", extra={"user_id": str(user.id), "credential_id": str(credential.id)})
        return TotpSetupResponse(
            credential_id=credential.id,
            provisioning_uri=provisioning_uri,
            qr_code_data_url=self._qr_data_url(provisioning_uri),
            recovery_codes=recovery_codes,
        )

    def enable(self, user: User, code: str) -> TotpStatusResponse:
        self.rate_limiter.check(f"mfa:enable:{user.id}")
        credential = self._get_latest_credential(user.id)
        if not self._verify_totp_code(credential, code):
            raise AppError("INVALID_TOTP_CODE", "Invalid TOTP code.", 401)
        credential.is_enabled = True
        self.credentials.save(credential)
        logger.info("totp_enabled", extra={"user_id": str(user.id), "credential_id": str(credential.id)})
        return self._status_from_credential(credential)

    def disable(self, user: User, code: str) -> TotpStatusResponse:
        self.rate_limiter.check(f"mfa:disable:{user.id}")
        credential = self._get_enabled_credential(user.id)
        if not self._verify_code_or_recovery(credential, code):
            raise AppError("INVALID_MFA_CODE", "Invalid MFA code.", 401)
        credential.is_enabled = False
        self.credentials.save(credential)
        logger.info("totp_disabled", extra={"user_id": str(user.id), "credential_id": str(credential.id)})
        return self._status_from_credential(credential)

    def verify(self, user: User, code: str) -> TotpStatusResponse:
        self.rate_limiter.check(f"mfa:verify:{user.id}")
        credential = self._get_enabled_credential(user.id)
        if not self.verify_credential_code(credential, code):
            raise AppError("INVALID_MFA_CODE", "Invalid MFA code.", 401)
        logger.info("totp_verified", extra={"user_id": str(user.id), "credential_id": str(credential.id)})
        return self._status_from_credential(credential)

    def verify_credential_code(self, credential: TotpCredential, code: str) -> bool:
        return self._verify_code_or_recovery(credential, code)

    def status(self, user: User) -> TotpStatusResponse:
        credential = self.credentials.get_enabled_by_user(user.id)
        if not credential:
            return TotpStatusResponse(is_enabled=False, recovery_codes_remaining=0)
        return self._status_from_credential(credential)

    def _verify_code_or_recovery(self, credential: TotpCredential, code: str) -> bool:
        if self._verify_totp_code(credential, code):
            return True
        return self._consume_recovery_code(credential, code)

    def _verify_totp_code(self, credential: TotpCredential, code: str) -> bool:
        secret = self.cipher.decrypt(credential.encrypted_secret)
        return pyotp.TOTP(secret).verify(code, valid_window=settings.totp_valid_window)

    def _consume_recovery_code(self, credential: TotpCredential, code: str) -> bool:
        remaining_hashes = []
        matched = False
        for code_hash in credential.recovery_code_hashes:
            if not matched and self.token_hasher.verify(code, code_hash):
                matched = True
                continue
            remaining_hashes.append(code_hash)
        if matched:
            credential.recovery_code_hashes = remaining_hashes
            credential.recovery_code_metadata = {"remaining": len(remaining_hashes)}
            self.credentials.save(credential)
        return matched

    def _get_latest_credential(self, user_id: UUID) -> TotpCredential:
        credential = self.credentials.get_latest_by_user(user_id)
        if not credential:
            raise AppError("TOTP_NOT_CONFIGURED", "TOTP setup has not been started.", 404)
        return credential

    def _get_enabled_credential(self, user_id: UUID) -> TotpCredential:
        credential = self.credentials.get_enabled_by_user(user_id)
        if not credential:
            raise AppError("TOTP_NOT_ENABLED", "TOTP is not enabled for this account.", 404)
        return credential

    def _generate_recovery_codes(self) -> list[str]:
        return [token_urlsafe(settings.totp_recovery_code_bytes) for _ in range(settings.totp_recovery_code_count)]

    def _qr_data_url(self, provisioning_uri: str) -> str:
        image = qrcode.make(provisioning_uri)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    def _status_from_credential(self, credential: TotpCredential) -> TotpStatusResponse:
        return TotpStatusResponse(
            is_enabled=credential.is_enabled,
            recovery_codes_remaining=len(credential.recovery_code_hashes),
        )
