import json

import pytest

from app.core.exceptions import AppError
from app.schemas.interview import Difficulty, InterviewMode, InterviewSessionState
from app.services.conversation_memory import ConversationMemory, RedisConversationMemory
from app.services.rate_limiter import RateLimiter


class FakeRedis:
    def __init__(self, values=None):
        self.values = values or {}
        self.expired_keys = []
        self.counts = {}

    def set(self, key, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    def incr(self, key):
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    def expire(self, key, ttl):
        self.expired_keys.append((key, ttl))


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


def test_redis_conversation_memory_serializes_and_restores_state():
    redis = FakeRedis()
    memory = RedisConversationMemory(redis, window_size=2)
    state = make_state("redis-session")
    state.turns = [{"role": "user", "content": "old"}, {"role": "assistant", "content": "new"}]

    memory.save(state)
    restored = memory.get("redis-session")

    assert restored is not None
    assert restored.session_id == "redis-session"
    assert restored.turns[-1]["content"] == "new"
    assert json.loads(redis.values["interview:memory:redis-session"])["session_id"] == "redis-session"


def test_redis_conversation_memory_raises_for_missing_append():
    memory = RedisConversationMemory(FakeRedis(), window_size=2)

    with pytest.raises(KeyError):
        memory.append_turn("missing", "user", "answer")


def test_rate_limiter_sets_expiry_and_blocks_after_limit(monkeypatch):
    redis = FakeRedis()
    monkeypatch.setattr("app.services.rate_limiter.settings.auth_rate_limit_attempts", 2, raising=False)
    monkeypatch.setattr("app.services.rate_limiter.settings.auth_rate_limit_window_seconds", 30, raising=False)
    limiter = RateLimiter(redis)

    limiter.check("auth:login")
    limiter.check("auth:login")

    assert redis.expired_keys == [("auth:login", 30)]

    with pytest.raises(AppError) as error:
        limiter.check("auth:login")

    assert error.value.code == "RATE_LIMITED"
