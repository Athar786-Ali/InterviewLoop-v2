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


class Persona(StrEnum):
    """AI interviewer personality that shapes tone and question style."""

    SERVICE = "service"   # Service company (TCS/Infosys): breadth-focused, process-heavy
    PRODUCT = "product"   # Product/FAANG (Google/Amazon): depth, system design, edge cases
    STARTUP = "startup"   # Startup: pragmatic, ship-it mindset, full-stack generalism


class PressureMode(StrEnum):
    """Controls hint availability and scoring strictness."""

    PRACTICE = "practice"       # Hints allowed; forgiving, coaching tone
    SIMULATED = "simulated"     # Hints blocked; strict, real-interview atmosphere


class InterviewStartRequest(BaseModel):
    mode: InterviewMode
    topic: str | None = Field(default=None, max_length=160)
    resume_text: str | None = Field(default=None, max_length=12000)
    initial_difficulty: Difficulty = Difficulty.MEDIUM
    persona: Persona = Persona.PRODUCT
    pressure_mode: PressureMode = PressureMode.PRACTICE


class InterviewTurnRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=96)
    answer: str = Field(min_length=1, max_length=8000)


class HintRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=96)
    current_question: str = Field(min_length=1, max_length=2000)


class HintResponse(BaseModel):
    session_id: str
    hint: str


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
    # v1-style coaching fields: richer, human-readable feedback
    what_went_well: list[str] = Field(default_factory=list)
    next_time_try: str = ""


class InterviewSessionState(BaseModel):
    session_id: str
    mode: InterviewMode
    topic: str | None = None
    resume_text: str | None = None
    current_difficulty: Difficulty = Difficulty.MEDIUM
    persona: Persona = Persona.PRODUCT
    pressure_mode: PressureMode = PressureMode.PRACTICE
    scores: list[float] = Field(default_factory=list)
    turns: list[dict[str, str]] = Field(default_factory=list)


class InterviewStartResponse(BaseModel):
    session_id: str
    question: InterviewQuestion
    persona: Persona
    pressure_mode: PressureMode


class InterviewTurnResponse(BaseModel):
    evaluation: InterviewEvaluation
    next_question: InterviewQuestion
    next_difficulty: Difficulty
