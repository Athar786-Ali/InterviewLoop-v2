from app.api.v1.dependencies import get_interview_engine
from app.main import create_app
from app.schemas.interview import Difficulty, InterviewEvaluation, InterviewQuestion, InterviewStartResponse, InterviewTurnResponse
from fastapi.testclient import TestClient


class FakeInterviewEngine:
    def start(self, payload):
        return InterviewStartResponse(
            session_id="session-1",
            question=InterviewQuestion(
                question="What is dependency injection?",
                topic=payload.topic or "architecture",
                difficulty=payload.initial_difficulty,
                expected_signals=["testability"],
            ),
        )

    def answer(self, session_id, answer):
        return InterviewTurnResponse(
            evaluation=InterviewEvaluation(score=8, feedback="Good", strengths=["clear"], weaknesses=[]),
            next_question=InterviewQuestion(
                question="How would you test it?",
                topic="architecture",
                difficulty=Difficulty.HARD,
                expected_signals=["mocks"],
            ),
            next_difficulty=Difficulty.HARD,
        )


def test_start_interview_route_returns_structured_question():
    app = create_app()
    app.dependency_overrides[get_interview_engine] = lambda: FakeInterviewEngine()
    client = TestClient(app)

    response = client.post("/api/v1/interviews/start", json={"mode": "topic", "topic": "Python"})

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["session_id"] == "session-1"


def test_answer_interview_route_returns_evaluation_and_next_question():
    app = create_app()
    app.dependency_overrides[get_interview_engine] = lambda: FakeInterviewEngine()
    client = TestClient(app)

    response = client.post("/api/v1/interviews/answer", json={"session_id": "session-1", "answer": "Use services."})

    assert response.status_code == 200
    assert response.json()["data"]["evaluation"]["score"] == 8
    assert response.json()["data"]["next_difficulty"] == "hard"
