from typing import Protocol

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
    """In-memory sliding-window conversation store.

    Stores interview session state in a process-level dict with a rolling
    window to cap context size. Sufficient for a single-instance deployment.
    """

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
