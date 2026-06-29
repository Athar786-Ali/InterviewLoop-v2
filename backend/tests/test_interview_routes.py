import io

from app.api.v1.dependencies import get_hint_engine, get_interview_engine, get_resume_parser
from app.core.exceptions import AppError
from app.main import create_app
from app.schemas.interview import (
    Difficulty,
    HintResponse,
    InterviewEvaluation,
    InterviewQuestion,
    InterviewStartResponse,
    InterviewTurnResponse,
    Persona,
    PressureMode,
)
from fastapi.testclient import TestClient


class FakeInterviewEngine:
    def __init__(self, pressure_mode=PressureMode.PRACTICE):
        from app.schemas.interview import InterviewSessionState, InterviewMode
        self._state = InterviewSessionState(
            session_id="session-1",
            mode=InterviewMode.TOPIC,
            topic="Python",
            pressure_mode=pressure_mode,
            persona=Persona.PRODUCT,
        )
        self.memory = _FakeMemory(self._state)

    def start(self, payload):
        return InterviewStartResponse(
            session_id="session-1",
            question=InterviewQuestion(
                question="What is dependency injection?",
                topic=payload.topic or "architecture",
                difficulty=payload.initial_difficulty,
                expected_signals=["testability"],
            ),
            persona=payload.persona,
            pressure_mode=payload.pressure_mode,
        )

    def answer(self, session_id, answer):
        return InterviewTurnResponse(
            evaluation=InterviewEvaluation(
                score=8,
                feedback="Good",
                strengths=["clear"],
                weaknesses=[],
                what_went_well=["Clear explanation", "Good structure"],
                next_time_try="Add a concrete example next time",
            ),
            next_question=InterviewQuestion(
                question="How would you test it?",
                topic="architecture",
                difficulty=Difficulty.HARD,
                expected_signals=["mocks"],
            ),
            next_difficulty=Difficulty.HARD,
        )


class _FakeMemory:
    def __init__(self, state):
        self._state = state

    def get(self, session_id):
        if session_id == self._state.session_id:
            return self._state
        return None


class FakeHintEngine:
    def generate(self, session_id, current_question):
        return HintResponse(session_id=session_id, hint="Think about what changes most frequently.")


class FakeResumeParser:
    def parse_pdf(self, file_bytes):
        return "John Doe — Software Engineer\n5 years Python experience"

    def parse_text(self, text):
        return text.strip()


def test_start_interview_route_returns_structured_question():
    app = create_app()
    app.dependency_overrides[get_interview_engine] = lambda: FakeInterviewEngine()
    client = TestClient(app)

    response = client.post("/api/v1/interviews/start", json={"mode": "topic", "topic": "Python"})

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["session_id"] == "session-1"


def test_start_interview_route_returns_persona_and_pressure_mode():
    app = create_app()
    app.dependency_overrides[get_interview_engine] = lambda: FakeInterviewEngine()
    client = TestClient(app)

    response = client.post(
        "/api/v1/interviews/start",
        json={"mode": "topic", "topic": "Python", "persona": "startup", "pressure_mode": "simulated"},
    )

    data = response.json()["data"]
    assert data["persona"] == "startup"
    assert data["pressure_mode"] == "simulated"


def test_answer_interview_route_returns_evaluation_and_next_question():
    app = create_app()
    app.dependency_overrides[get_interview_engine] = lambda: FakeInterviewEngine()
    client = TestClient(app)

    response = client.post("/api/v1/interviews/answer", json={"session_id": "session-1", "answer": "Use services."})

    assert response.status_code == 200
    assert response.json()["data"]["evaluation"]["score"] == 8
    assert response.json()["data"]["next_difficulty"] == "hard"


def test_answer_route_returns_coaching_fields():
    app = create_app()
    app.dependency_overrides[get_interview_engine] = lambda: FakeInterviewEngine()
    client = TestClient(app)

    response = client.post("/api/v1/interviews/answer", json={"session_id": "session-1", "answer": "DI is great."})
    eval_data = response.json()["data"]["evaluation"]

    assert eval_data["what_went_well"] == ["Clear explanation", "Good structure"]
    assert eval_data["next_time_try"] == "Add a concrete example next time"


def test_hint_route_returns_hint_in_practice_mode():
    app = create_app()
    engine = FakeInterviewEngine(pressure_mode=PressureMode.PRACTICE)
    app.dependency_overrides[get_interview_engine] = lambda: engine
    app.dependency_overrides[get_hint_engine] = lambda: FakeHintEngine()
    client = TestClient(app)

    response = client.post(
        "/api/v1/interviews/hint",
        json={"session_id": "session-1", "current_question": "Explain SOLID principles."},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["hint"] == "Think about what changes most frequently."
    assert data["session_id"] == "session-1"


def test_hint_route_blocked_in_simulated_mode():
    app = create_app()
    engine = FakeInterviewEngine(pressure_mode=PressureMode.SIMULATED)
    app.dependency_overrides[get_interview_engine] = lambda: engine
    app.dependency_overrides[get_hint_engine] = lambda: FakeHintEngine()
    client = TestClient(app)

    response = client.post(
        "/api/v1/interviews/hint",
        json={"session_id": "session-1", "current_question": "Explain SOLID principles."},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "HINTS_DISABLED"


def test_hint_route_returns_404_for_unknown_session():
    app = create_app()
    engine = FakeInterviewEngine(pressure_mode=PressureMode.PRACTICE)
    app.dependency_overrides[get_interview_engine] = lambda: engine
    app.dependency_overrides[get_hint_engine] = lambda: FakeHintEngine()
    client = TestClient(app)

    response = client.post(
        "/api/v1/interviews/hint",
        json={"session_id": "no-such-session", "current_question": "What is X?"},
    )

    assert response.status_code == 404


def test_upload_resume_route_returns_extracted_text_from_pdf():
    app = create_app()
    app.dependency_overrides[get_resume_parser] = lambda: FakeResumeParser()
    client = TestClient(app)

    fake_pdf = io.BytesIO(b"%PDF-1.4 fake content")
    response = client.post(
        "/api/v1/interviews/upload-resume",
        files={"file": ("resume.pdf", fake_pdf, "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert "John Doe" in data["resume_text"]
    assert data["char_count"] > 0


def test_upload_resume_route_accepts_plain_text():
    app = create_app()
    app.dependency_overrides[get_resume_parser] = lambda: FakeResumeParser()
    client = TestClient(app)

    response = client.post(
        "/api/v1/interviews/upload-resume",
        data={"text": "  Jane Smith — Backend Engineer  "},
    )

    assert response.status_code == 200
    assert response.json()["data"]["resume_text"] == "Jane Smith — Backend Engineer"


def test_upload_resume_route_returns_422_when_nothing_provided():
    app = create_app()
    app.dependency_overrides[get_resume_parser] = lambda: FakeResumeParser()
    client = TestClient(app)

    response = client.post("/api/v1/interviews/upload-resume")

    assert response.status_code == 422
