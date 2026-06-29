"""Tests for InterviewEngineService with DB persistence.

Uses Fake* repositories following the established pattern in the test suite.
"""

from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.schemas.interview import (
    Difficulty,
    InterviewEvaluation,
    InterviewMode,
    InterviewQuestion,
    InterviewStartRequest,
    InterviewStartResponse,
    InterviewTurnResponse,
)
from app.services.interview_engine import InterviewEngineService, _WARMUP_QUESTION


# ---------------------------------------------------------------------------
# Fake infrastructure
# ---------------------------------------------------------------------------

class FakeUser:
    def __init__(self):
        self.id = uuid4()


class FakeLLMService:
    """Returns deterministic responses for unit tests."""

    def generate_structured(self, prompt: str, schema):
        if schema.__name__ == "InterviewQuestion":
            return InterviewQuestion(
                question="Explain binary search.",
                topic="algorithms",
                difficulty=Difficulty.MEDIUM,
            )
        if schema.__name__ == "InterviewEvaluation":
            return InterviewEvaluation(
                score=8.0,
                feedback="Good answer.",
                strengths=["clear"],
                weaknesses=[],
                what_went_well=["Logical structure"],
                next_time_try="Add complexity analysis",
            )
        raise ValueError(f"Unknown schema: {schema}")


class FakeMemory:
    def __init__(self):
        self.sessions = {}

    def save(self, state):
        state.turns = state.turns[-8:]
        self.sessions[state.session_id] = state
        return state

    def get(self, session_id):
        return self.sessions.get(session_id)

    def append_turn(self, session_id, role, content):
        state = self.sessions[session_id]
        state.turns.append({"role": role, "content": content})
        return self.save(state)


class FakeDifficultyService:
    def next_difficulty(self, current, scores):
        return current


class FakeSessionRow:
    def __init__(self, user_id, session_id, interview_type):
        self.id = uuid4()
        self.user_id = user_id
        self.session_id = session_id
        self.interview_type = interview_type
        self.status = "active"
        self.started_at = None
        self.completed_at = None


class FakeSessionRepo:
    def __init__(self, user_id):
        self._user_id = user_id
        self._sessions: dict[str, FakeSessionRow] = {}

    def create_interview_session(self, user_id, session_id, interview_type, started_at):
        row = FakeSessionRow(user_id, session_id, interview_type)
        self._sessions[session_id] = row
        return row

    def get_by_session_id(self, session_id):
        return self._sessions.get(session_id)

    def save(self, session):
        return session

    def list_active_by_user(self, user_id):
        return list(self._sessions.values())


class FakeQuestionLogRepo:
    def __init__(self):
        self.logs = []

    def create(self, **kwargs):
        row = SimpleNamespace(**kwargs, id=uuid4())
        self.logs.append(row)
        return row

    def list_for_session(self, session_id):
        return [log for log in self.logs if log.session_id == session_id]


class FakeTopicPerfRepo:
    def __init__(self):
        self.records = []
        self.upserted = []

    def upsert_score(self, user_id, session_id, topic, new_score):
        self.upserted.append({"topic": topic, "score": new_score})
        row = SimpleNamespace(
            user_id=user_id,
            session_id=session_id,
            topic=topic,
            average_score=new_score,
            questions_attempted=1,
            weak_area_count=1 if new_score < 4 else 0,
        )
        self.records.append(row)
        return row

    def list_for_user(self, user_id):
        return self.records


def _make_engine(user=None):
    user = user or FakeUser()
    session_repo = FakeSessionRepo(user.id)
    question_log_repo = FakeQuestionLogRepo()
    topic_perf_repo = FakeTopicPerfRepo()
    engine = InterviewEngineService(
        llm_service=FakeLLMService(),
        memory=FakeMemory(),
        difficulty_service=FakeDifficultyService(),
        session_repo=session_repo,
        question_log_repo=question_log_repo,
        topic_perf_repo=topic_perf_repo,
    )
    return engine, user, session_repo, question_log_repo, topic_perf_repo


# ---------------------------------------------------------------------------
# start() tests
# ---------------------------------------------------------------------------

def test_start_returns_warmup_question():
    engine, user, *_ = _make_engine()
    payload = InterviewStartRequest(mode=InterviewMode.TOPIC, topic="Python")
    result = engine.start(payload, user)

    assert isinstance(result, InterviewStartResponse)
    assert result.is_warmup is True
    assert result.question.question == _WARMUP_QUESTION.question


def test_start_creates_db_session_row():
    engine, user, session_repo, *_ = _make_engine()
    payload = InterviewStartRequest(mode=InterviewMode.TOPIC, topic="Arrays")
    result = engine.start(payload, user)

    assert result.session_id in session_repo._sessions
    row = session_repo._sessions[result.session_id]
    assert row.interview_type == "topic"
    assert row.status == "active"


def test_start_stores_session_id_in_memory():
    engine, user, *_ = _make_engine()
    payload = InterviewStartRequest(mode=InterviewMode.RESUME, resume_text="My resume")
    result = engine.start(payload, user)

    state = engine.memory.get(result.session_id)
    assert state is not None
    assert state.db_session_id is not None


def test_start_behavioral_mode_sets_correct_interview_type():
    engine, user, session_repo, *_ = _make_engine()
    payload = InterviewStartRequest(mode=InterviewMode.BEHAVIORAL)
    result = engine.start(payload, user)

    row = session_repo._sessions[result.session_id]
    assert row.interview_type == "behavioral"


# ---------------------------------------------------------------------------
# answer() tests
# ---------------------------------------------------------------------------

def test_answer_returns_evaluation_and_next_question():
    engine, user, *_ = _make_engine()
    payload = InterviewStartRequest(mode=InterviewMode.TOPIC, topic="Trees")
    start_result = engine.start(payload, user)

    turn = engine.answer(start_result.session_id, "Binary tree is...", user)

    assert isinstance(turn, InterviewTurnResponse)
    assert turn.evaluation.score == 8.0
    assert turn.next_question.question == "Explain binary search."


def test_answer_persists_question_log():
    engine, user, session_repo, question_log_repo, _ = _make_engine()
    payload = InterviewStartRequest(mode=InterviewMode.TOPIC, topic="Graphs")
    start = engine.start(payload, user)

    engine.answer(start.session_id, "DFS traversal...", user)

    assert len(question_log_repo.logs) == 1
    log = question_log_repo.logs[0]
    assert log.answer_text == "DFS traversal..."
    assert log.score == 8.0


def test_answer_upserts_topic_performance():
    engine, user, session_repo, _, topic_perf_repo = _make_engine()
    payload = InterviewStartRequest(mode=InterviewMode.TOPIC, topic="DP")
    start = engine.start(payload, user)

    engine.answer(start.session_id, "Memoization...", user)

    assert len(topic_perf_repo.upserted) == 1
    assert topic_perf_repo.upserted[0]["score"] == 8.0


def test_answer_adds_speech_analytics():
    engine, user, *_ = _make_engine()
    payload = InterviewStartRequest(mode=InterviewMode.TOPIC, topic="OS")
    start = engine.start(payload, user)

    # Answer with filler words
    turn = engine.answer(start.session_id, "Um, like, basically it's a process", user)

    assert turn.evaluation.filler_count >= 2


def test_answer_raises_404_for_unknown_session():
    engine, user, *_ = _make_engine()
    from app.core.exceptions import AppError
    with pytest.raises(AppError) as exc_info:
        engine.answer("no-such-session", "answer", user)
    assert exc_info.value.code == "INTERVIEW_SESSION_NOT_FOUND"


# ---------------------------------------------------------------------------
# end() tests
# ---------------------------------------------------------------------------

def test_end_marks_session_completed():
    engine, user, session_repo, *_ = _make_engine()
    payload = InterviewStartRequest(mode=InterviewMode.TOPIC, topic="DBMS")
    start = engine.start(payload, user)

    engine.end(start.session_id, user)

    row = session_repo._sessions[start.session_id]
    assert row.status == "completed"
    assert row.completed_at is not None


def test_end_returns_interview_summary():
    engine, user, session_repo, question_log_repo, _ = _make_engine()
    payload = InterviewStartRequest(mode=InterviewMode.TOPIC, topic="CN")
    start = engine.start(payload, user)

    # Answer one question to populate question log
    db_session_id = UUID(engine.memory.get(start.session_id).db_session_id)
    question_log_repo.create(
        session_id=db_session_id,
        sequence_number=1,
        topic="CN",
        difficulty="medium",
        question_text="What is TCP?",
        answer_text="TCP is reliable",
        score=7.5,
        feedback="Good",
    )
    summary = engine.end(start.session_id, user)

    assert summary.session_id == start.session_id
    assert summary.overall_average_score == 7.5
    assert summary.total_questions == 1
    assert len(summary.encouraging_message) > 0


def test_end_raises_404_for_wrong_user():
    engine, user, *_ = _make_engine()
    other_user = FakeUser()
    payload = InterviewStartRequest(mode=InterviewMode.TOPIC, topic="OOP")
    start = engine.start(payload, user)

    from app.core.exceptions import AppError
    with pytest.raises(AppError) as exc_info:
        engine.end(start.session_id, other_user)
    assert exc_info.value.status_code == 404


def test_end_clears_in_memory_state():
    engine, user, *_ = _make_engine()
    payload = InterviewStartRequest(mode=InterviewMode.TOPIC, topic="Python")
    start = engine.start(payload, user)

    engine.end(start.session_id, user)

    assert engine.memory.get(start.session_id) is None
