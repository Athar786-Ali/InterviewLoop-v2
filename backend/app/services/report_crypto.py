import base64

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import normalize_pem


class ReportSignatureService:
    def __init__(self, private_key_pem: str | None = None, public_key_pem: str | None = None) -> None:
        raw_private = private_key_pem if private_key_pem is not None else settings.report_signature_private_key
        raw_public = public_key_pem if public_key_pem is not None else settings.report_signature_public_key
        self.private_key_pem = normalize_pem(raw_private)
        self.public_key_pem = normalize_pem(raw_public)

    def sign(self, content: bytes) -> str:
        if not self.private_key_pem:
            raise AppError("REPORT_SIGNATURE_CONFIGURATION_ERROR", "Report private signing key is not configured.", 500)
        private_key = serialization.load_pem_private_key(self.private_key_pem.encode("utf-8"), password=None)
        signature = private_key.sign(
            content,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode("ascii")

    def verify(self, content: bytes, signature: str) -> bool:
        if not self.public_key_pem:
            raise AppError("REPORT_SIGNATURE_CONFIGURATION_ERROR", "Report public signing key is not configured.", 500)
        public_key = serialization.load_pem_public_key(self.public_key_pem.encode("utf-8"))
        try:
            public_key.verify(
                base64.b64decode(signature),
                content,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256(),
            )
            return True
        except InvalidSignature:
            return False
