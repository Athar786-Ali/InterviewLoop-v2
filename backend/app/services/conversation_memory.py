import json
from typing import Protocol

from redis import Redis

from app.core.config import settings
from app.schemas.interview import InterviewSessionState


class InterviewMemory(Protocol):
    def save(self, state: InterviewSessionState) -> InterviewSessionState:
        ...

    def get(self, session_id: str) -> InterviewSessionState | None:
        ...

    def append_turn(self, session_id: str, role: str, content: str) -> InterviewSessionState:
        ...


class ConversationMemory:
    def __init__(self, window_size: int | None = None) -> None:
        self.window_size = window_size or settings.interview_memory_window
        self.sessions: dict[str, InterviewSessionState] = {}

    def save(self, state: InterviewSessionState) -> InterviewSessionState:
        state.turns = state.turns[-self.window_size :]
        self.sessions[state.session_id] = state
        return state

    def get(self, session_id: str) -> InterviewSessionState | None:
        return self.sessions.get(session_id)

    def append_turn(self, session_id: str, role: str, content: str) -> InterviewSessionState:
        state = self.sessions[session_id]
        state.turns.append({"role": role, "content": content})
        state.turns = state.turns[-self.window_size :]
        return self.save(state)


class RedisConversationMemory:
    def __init__(self, redis_client: Redis, window_size: int | None = None) -> None:
        self.redis_client = redis_client
        self.window_size = window_size or settings.interview_memory_window

    def save(self, state: InterviewSessionState) -> InterviewSessionState:
        state.turns = state.turns[-self.window_size :]
        self.redis_client.set(self._key(state.session_id), state.model_dump_json())
        return state

    def get(self, session_id: str) -> InterviewSessionState | None:
        raw_state = self.redis_client.get(self._key(session_id))
        if not raw_state:
            return None
        if isinstance(raw_state, bytes):
            raw_state = raw_state.decode("utf-8")
        return InterviewSessionState.model_validate(json.loads(raw_state))

    def append_turn(self, session_id: str, role: str, content: str) -> InterviewSessionState:
        state = self.get(session_id)
        if not state:
            raise KeyError(session_id)
        state.turns.append({"role": role, "content": content})
        return self.save(state)

    def _key(self, session_id: str) -> str:
        return f"interview:memory:{session_id}"
