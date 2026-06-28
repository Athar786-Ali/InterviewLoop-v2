from app.schemas.speech import TranscriptEventType
from app.services.speech_service import TypedFallbackService


def test_typed_fallback_service_returns_final_typed_event():
    service = TypedFallbackService()

    event = service.event("session-1", "typed answer")

    assert event.type == TranscriptEventType.FALLBACK_TYPED
    assert event.text == "typed answer"
    assert event.is_final is True
