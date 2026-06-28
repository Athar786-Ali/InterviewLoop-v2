from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.core.exceptions import AppError


class SecretCipher:
    def __init__(self, key: str | None = None) -> None:
        encryption_key = key or settings.totp_secret_encryption_key
        if not encryption_key:
            raise AppError("MFA_CONFIGURATION_ERROR", "TOTP secret encryption key is not configured.", 500)
        self.fernet = Fernet(encryption_key.encode("utf-8"))

    def encrypt(self, value: str) -> bytes:
        return self.fernet.encrypt(value.encode("utf-8"))

    def decrypt(self, value: bytes) -> str:
        try:
            return self.fernet.decrypt(value).decode("utf-8")
        except InvalidToken as exc:
            raise AppError("MFA_SECRET_DECRYPTION_FAILED", "Unable to decrypt TOTP secret.", 500) from exc
