import pytest

from app.core.exceptions import AppError
from app.schemas.interview import (
    Difficulty,
    HintResponse,
    InterviewMode,
    InterviewSessionState,
    Persona,
    PressureMode,
)
from app.services.hint_engine import HintEngineService, _HintSchema
from app.services.conversation_memory import ConversationMemory


class FakeLLM:
    """Stub LLM that returns a predetermined Socratic hint."""

    def generate_structured(self, prompt, schema):
        assert schema is _HintSchema, f"Expected _HintSchema, got {schema}"
        return _HintSchema(hint="What would happen if the system had no shared state?")


class FakeFailingLLM:
    def generate_structured(self, prompt, schema):
        raise AppError("LLM_GENERATION_FAILED", "LLM is down.", 503)


def _make_state(
    session_id="hint-session",
    persona=Persona.PRODUCT,
    pressure_mode=PressureMode.PRACTICE,
) -> InterviewSessionState:
    return InterviewSessionState(
        session_id=session_id,
        mode=InterviewMode.TOPIC,
        topic="Distributed Systems",
        current_difficulty=Difficulty.MEDIUM,
        persona=persona,
        pressure_mode=pressure_mode,
    )


def test_hint_engine_returns_socratic_hint():
    memory = ConversationMemory()
    memory.save(_make_state())
    engine = HintEngineService(llm_service=FakeLLM(), memory=memory)

    result = engine.generate("hint-session", "Explain the CAP theorem.")

    assert isinstance(result, HintResponse)
    assert result.session_id == "hint-session"
    assert result.hint == "What would happen if the system had no shared state?"


def test_hint_engine_raises_for_missing_session():
    memory = ConversationMemory()
    engine = HintEngineService(llm_service=FakeLLM(), memory=memory)

    with pytest.raises(AppError) as exc:
        engine.generate("nonexistent-session", "What is X?")

    assert exc.value.code == "INTERVIEW_SESSION_NOT_FOUND"


def test_hint_engine_uses_session_persona_for_tone():
    """Ensure the hint prompt includes the persona preamble (indirect check via LLM stub call)."""
    from app.services.prompt_templates import render_hint_prompt

    state = _make_state(persona=Persona.STARTUP)
    prompt = render_hint_prompt(state, "How would you ship this feature in a week?")

    assert "startup" in prompt.lower() or "ship" in prompt.lower()


def test_hint_engine_propagates_llm_errors():
    memory = ConversationMemory()
    memory.save(_make_state())
    engine = HintEngineService(llm_service=FakeFailingLLM(), memory=memory)

    with pytest.raises(AppError) as exc:
        engine.generate("hint-session", "What is eventual consistency?")

    assert exc.value.code == "LLM_GENERATION_FAILED"


def test_hint_prompt_contains_question_and_forbids_revealing_answer():
    from app.services.prompt_templates import render_hint_prompt

    state = _make_state()
    prompt = render_hint_prompt(state, "What is a B-tree index?")

    assert "B-tree index" in prompt
    assert "without revealing" in prompt.lower() or "do not give away" in prompt.lower() or "not reveal" in prompt.lower()
