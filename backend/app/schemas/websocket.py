from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class InterviewEventType(StrEnum):
    CONNECTED = "connected"
    RECONNECTED = "reconnected"
    HEARTBEAT = "heartbeat"
    PONG = "pong"
    QUESTION_STARTED = "question_started"
    TRANSCRIPT_PARTIAL = "transcript_partial"
    TRANSCRIPT_FINAL = "transcript_final"
    ANSWER_SUBMITTED = "answer_submitted"
    EVALUATION_READY = "evaluation_ready"
    ERROR = "error"
    SESSION_CLEANUP = "session_cleanup"


class InterviewEvent(BaseModel):
    type: InterviewEventType
    session_id: str
    sequence: int = 0
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClientInterviewEvent(BaseModel):
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    last_sequence: int | None = None
