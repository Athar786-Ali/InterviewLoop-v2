from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class TotpSetupRequest(BaseModel):
    label: str | None = Field(default=None, max_length=160)


class TotpSetupResponse(BaseModel):
    credential_id: UUID
    provisioning_uri: str
    qr_code_data_url: str
    recovery_codes: list[str]


class TotpEnableRequest(BaseModel):
    code: str = Field(min_length=6, max_length=32)


class TotpVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=32)


class TotpDisableRequest(BaseModel):
    code: str = Field(min_length=6, max_length=32)


class TotpStatusResponse(ORMModel):
    is_enabled: bool
    recovery_codes_remaining: int
