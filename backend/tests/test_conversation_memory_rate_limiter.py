import time

import pytest

from app.core.exceptions import AppError
from app.schemas.interview import Difficulty, InterviewMode, InterviewSessionState
from app.services.conversation_memory import ConversationMemory
from app.services.rate_limiter import RateLimiter


def make_state(session_id="session-1"):
    return InterviewSessionState(
        session_id=session_id,
        mode=InterviewMode.TOPIC,
        topic="Python",
        current_difficulty=Difficulty.MEDIUM,
        turns=[],
    )


def test_in_memory_conversation_memory_trims_sliding_window():
    memory = ConversationMemory(window_size=2)
    memory.save(make_state())

    memory.append_turn("session-1", "assistant", "question")
    state = memory.append_turn("session-1", "user", "answer")
    state = memory.append_turn("session-1", "assistant", "next")

    assert [turn["content"] for turn in state.turns] == ["answer", "next"]
    assert memory.get("session-1") is state


def test_in_memory_conversation_memory_get_returns_none_for_unknown_session():
    memory = ConversationMemory()
    assert memory.get("unknown-session") is None


def test_in_memory_conversation_memory_save_and_retrieve():
    memory = ConversationMemory(window_size=4)
    state = make_state("session-abc")
    saved = memory.save(state)
    retrieved = memory.get("session-abc")

    assert saved is retrieved
    assert retrieved.session_id == "session-abc"


def test_rate_limiter_allows_requests_within_limit(monkeypatch):
    monkeypatch.setattr("app.services.rate_limiter.settings.auth_rate_limit_attempts", 3, raising=False)
    monkeypatch.setattr("app.services.rate_limiter.settings.auth_rate_limit_window_seconds", 60, raising=False)
    limiter = RateLimiter()

    # These should not raise
    limiter.check("auth:login:user@example.com")
    limiter.check("auth:login:user@example.com")
    limiter.check("auth:login:user@example.com")


def test_rate_limiter_blocks_after_limit_exceeded(monkeypatch):
    monkeypatch.setattr("app.services.rate_limiter.settings.auth_rate_limit_attempts", 2, raising=False)
    monkeypatch.setattr("app.services.rate_limiter.settings.auth_rate_limit_window_seconds", 60, raising=False)
    limiter = RateLimiter()

    limiter.check("auth:login:blocked@example.com")
    limiter.check("auth:login:blocked@example.com")

    with pytest.raises(AppError) as error:
        limiter.check("auth:login:blocked@example.com")

    assert error.value.code == "RATE_LIMITED"


def test_rate_limiter_uses_separate_counters_per_key(monkeypatch):
    monkeypatch.setattr("app.services.rate_limiter.settings.auth_rate_limit_attempts", 1, raising=False)
    monkeypatch.setattr("app.services.rate_limiter.settings.auth_rate_limit_window_seconds", 60, raising=False)
    limiter = RateLimiter()

    limiter.check("key:a")  # first call on key:a — passes

    with pytest.raises(AppError):
        limiter.check("key:a")  # second call on key:a — blocked

    limiter.check("key:b")  # first call on key:b — passes (separate counter)


def test_rate_limiter_resets_after_window_expires(monkeypatch):
    monkeypatch.setattr("app.services.rate_limiter.settings.auth_rate_limit_attempts", 1, raising=False)
    monkeypatch.setattr("app.services.rate_limiter.settings.auth_rate_limit_window_seconds", 0, raising=False)
    limiter = RateLimiter()

    limiter.check("expiry:key")  # passes
    time.sleep(0.01)  # window of 0 seconds expires immediately

    # Window has expired — counter resets, this should pass again
    limiter.check("expiry:key")
