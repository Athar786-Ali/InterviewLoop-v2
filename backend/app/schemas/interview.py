from enum import StrEnum

from pydantic import BaseModel, Field


class InterviewMode(StrEnum):
    TOPIC = "topic"
    RESUME = "resume"
    MIXED = "mixed"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class InterviewStartRequest(BaseModel):
    mode: InterviewMode
    topic: str | None = Field(default=None, max_length=160)
    resume_text: str | None = Field(default=None, max_length=12000)
    initial_difficulty: Difficulty = Difficulty.MEDIUM


class InterviewTurnRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=96)
    answer: str = Field(min_length=1, max_length=8000)


class InterviewQuestion(BaseModel):
    question: str
    topic: str
    difficulty: Difficulty
    expected_signals: list[str] = Field(default_factory=list)


class InterviewEvaluation(BaseModel):
    score: float = Field(ge=0, le=10)
    feedback: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)


class InterviewSessionState(BaseModel):
    session_id: str
    mode: InterviewMode
    topic: str | None = None
    resume_text: str | None = None
    current_difficulty: Difficulty = Difficulty.MEDIUM
    scores: list[float] = Field(default_factory=list)
    turns: list[dict[str, str]] = Field(default_factory=list)


class InterviewStartResponse(BaseModel):
    session_id: str
    question: InterviewQuestion


class InterviewTurnResponse(BaseModel):
    evaluation: InterviewEvaluation
    next_question: InterviewQuestion
    next_difficulty: Difficulty
