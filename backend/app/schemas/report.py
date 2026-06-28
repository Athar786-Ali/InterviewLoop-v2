from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ORMModel


class ReportGenerateRequest(BaseModel):
    session_id: UUID
    report_type: str = "interview"


class ReportRead(ORMModel):
    id: UUID
    session_id: UUID
    report_type: str
    storage_path: str | None
    content_hash: str | None
    signature: str | None
    generated_at: datetime | None


class ReportVerificationResponse(BaseModel):
    report_id: UUID
    is_valid: bool
    content_hash: str
    signature_valid: bool
    hash_matches: bool


class AuditLogRead(ORMModel):
    id: UUID
    action: str
    metadata_json: dict | None
    created_at: datetime
