import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.services.email_service import EmailService
from app.services.llm_service import OllamaLLMService

# 1. Setup SQLite DB for the test
import os
DB_FILE = "test_integration.db"
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_FILE}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# 2. Mock Email Service (to grab OTP)
class FakeEmailService(EmailService):
    def __init__(self):
        self.sent_otps = {}

    def send_otp(self, email: str, otp: str, purpose: str):
        self.sent_otps[email] = otp


# 3. Mock LLM Service (for the interview engine)
class FakeLLMService(OllamaLLMService):
    def __init__(self, *args, **kwargs):
        self.retry_attempts = 3
        pass

    def generate_structured(self, prompt: str, schema_class: type, max_retries: int = 3, timeout: int = 120):
        # We can just check the schema_class name to know what to return
        name = schema_class.__name__
        if name == "InterviewStartResponse":
            from app.schemas.interview import InterviewStartResponse, InterviewQuestion, Difficulty
            return InterviewStartResponse(
                session_id="test-session",
                question=InterviewQuestion(
                    question="What is polymorphism?",
                    topic="OOP",
                    difficulty=Difficulty.MEDIUM,
                    expected_signals=["oop"]
                ),
                persona="product",
                pressure_mode="practice"
            )
        elif name == "InterviewTurnResponse":
            from app.schemas.interview import InterviewTurnResponse, InterviewEvaluation, InterviewQuestion, Difficulty
            return InterviewTurnResponse(
                evaluation=InterviewEvaluation(
                    score=9,
                    feedback="Great answer.",
                    strengths=["clear"],
                    weaknesses=[],
                    what_went_well=["good example"],
                    next_time_try="nothing"
                ),
                next_question=InterviewQuestion(
                    question="Next question?",
                    topic="OOP",
                    difficulty=Difficulty.HARD,
                    expected_signals=[]
                ),
                next_difficulty=Difficulty.HARD
            )
        elif name == "InterviewEvaluation":
            from app.schemas.interview import InterviewEvaluation
            return InterviewEvaluation(
                score=9,
                feedback="Great answer.",
                strengths=["clear"],
                weaknesses=[],
                what_went_well=["good example"],
                next_time_try="nothing"
            )
        elif name == "InterviewQuestion":
            from app.schemas.interview import InterviewQuestion, Difficulty
            return InterviewQuestion(
                question="What is polymorphism?",
                topic="OOP",
                difficulty=Difficulty.MEDIUM,
                expected_signals=["oop"]
            )
        elif name == "InterviewSummary":
            from app.schemas.interview import InterviewSummary
            return InterviewSummary(
                session_id="test-session",
                overall_average_score=9.0,
                total_questions=1,
                encouraging_message="Good job."
            )
        # Default fallback
        return schema_class()


# 4. Create App and apply overrides
fastapi_app = create_app()
fastapi_app.dependency_overrides[get_db] = override_get_db

fake_email_service = FakeEmailService()

# Monkey patch EmailService inside dependencies.py
import app.api.v1.dependencies
app.api.v1.dependencies.EmailService = lambda: fake_email_service

# Monkey patch OllamaLLMService inside dependencies.py
app.api.v1.dependencies.OllamaLLMService = FakeLLMService

# Monkey patch utc_now to be naive for SQLite tests
from datetime import datetime, timezone
def naive_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

import app.services.auth_service
app.services.auth_service.utc_now = naive_utc_now
import app.db.base
app.db.base.utc_now = naive_utc_now


@pytest.fixture
def client():
    # Fresh DB for each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(fastapi_app) as c:
        yield c


def test_full_interview_flow(client):
    # Step 1: Signup
    email = "integration@example.com"
    signup_res = client.post("/api/v1/auth/signup", json={
        "email": email,
        "password": "StrongPassword123!",
        "full_name": "Integration Tester"
    })
    assert signup_res.status_code == 201, signup_res.json()

    # Step 2: Verify Email
    otp = fake_email_service.sent_otps[email]
    verify_res = client.post("/api/v1/auth/verify-email", json={
        "email": email,
        "otp": otp
    })
    assert verify_res.status_code == 200

    # Step 3: Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "StrongPassword123!"
    })
    assert login_res.status_code == 200
    access_token = login_res.json()["data"]["access_token"]
    
    headers = {"Authorization": f"Bearer {access_token}"}

    # Step 4: Start Interview
    start_res = client.post("/api/v1/interviews/start", json={
        "mode": "topic",
        "topic": "OOP",
        "initial_difficulty": "medium",
        "persona": "product",
        "pressure_mode": "practice"
    }, headers=headers)
    assert start_res.status_code == 200
    start_data = start_res.json()["data"]
    session_id = start_data["session_id"]
    # Expect warmup question
    assert "tell me a bit about yourself" in start_data["question"]["question"].lower()

    # Step 5: Answer Warmup Question
    warmup_res = client.post("/api/v1/interviews/answer", json={
        "session_id": session_id,
        "answer": "I am an engineer looking to practice."
    }, headers=headers)
    assert warmup_res.status_code == 200
    warmup_data = warmup_res.json()["data"]
    # The next question should now be from the FakeLLMService
    assert warmup_data["next_question"]["question"] == "What is polymorphism?"

    # Step 6: Answer Technical Question
    answer_res = client.post("/api/v1/interviews/answer", json={
        "session_id": session_id,
        "answer": "Polymorphism is when subclasses override parent methods."
    }, headers=headers)
    assert answer_res.status_code == 200
    eval_data = answer_res.json()["data"]["evaluation"]
    assert eval_data["score"] == 9

    # Step 7: End Interview
    end_res = client.post(f"/api/v1/interviews/{session_id}/end", headers=headers)
    assert end_res.status_code == 200
    summary_data = end_res.json()["data"]
    assert summary_data["overall_average_score"] == 9
    assert summary_data["total_questions"] >= 1
    assert len(summary_data["topics"]) == 1
    assert summary_data["topics"][0]["topic"] == "OOP"
