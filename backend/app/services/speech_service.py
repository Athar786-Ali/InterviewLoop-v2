from app.schemas.speech import TranscriptEvent, TranscriptEventType, TypedAnswerResponse


class TypedFallbackService:
    def submit(self, session_id: str, answer: str) -> TypedAnswerResponse:
        return TypedAnswerResponse(session_id=session_id, transcript=answer)

    def event(self, session_id: str, answer: str) -> TranscriptEvent:
        return TranscriptEvent(
            type=TranscriptEventType.FALLBACK_TYPED,
            text=answer,
            is_final=True,
            message=f"Typed fallback accepted for session {session_id}.",
        )
