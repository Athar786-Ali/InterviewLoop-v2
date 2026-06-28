from enum import StrEnum

from pydantic import BaseModel, Field


class TranscriptEventType(StrEnum):
    PARTIAL = "partial_transcript"
    FINAL = "final_transcript"
    ERROR = "error"
    RECONNECTED = "reconnected"
    FALLBACK_TYPED = "fallback_typed"
    CLOSED = "closed"


class TranscriptEvent(BaseModel):
    type: TranscriptEventType
    text: str = ""
    is_final: bool = False
    confidence: float | None = None
    error_code: str | None = None
    message: str = ""


class TypedAnswerRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=96)
    answer: str = Field(min_length=1, max_length=8000)


class TypedAnswerResponse(BaseModel):
    session_id: str
    transcript: str
    source: str = "typed"
