from enum import StrEnum

from pydantic import BaseModel, Field


class InterviewMode(StrEnum):
    TOPIC = "topic"
    RESUME = "resume"
    MIXED = "mixed"
    BEHAVIORAL = "behavioral"      # Phase 2.2
    JOB_DESCRIPTION = "job_description"  # Phase 2.3


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
    jd_text: str | None = Field(default=None, max_length=12000)  # Phase 2.3: job description
    initial_difficulty: Difficulty = Difficulty.MEDIUM
    persona: Persona = Persona.PRODUCT
    pressure_mode: PressureMode = PressureMode.PRACTICE


class InterviewTurnRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=96)
    answer: str = Field(min_length=1, max_length=8000)
    elapsed_seconds: float | None = None  # Phase 2.6: for WPM calculation


class HintRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=96)
    current_question: str = Field(min_length=1, max_length=2000)


class HintResponse(BaseModel):
    session_id: str
    hint: str


class InterviewQuestion(BaseModel):
    question: str
    topic: str = ""          # optional — model may omit it
    difficulty: Difficulty = Difficulty.MEDIUM
    expected_signals: list[str] = Field(default_factory=list)


class InterviewEvaluation(BaseModel):
    score: float = Field(default=5.0, ge=0, le=10)
    feedback: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    what_went_well: list[str] = Field(default_factory=list)
    next_time_try: str = ""
    # Phase 2.6: speech analytics (computed server-side, not from LLM)
    filler_count: int = 0
    words_per_minute: float | None = None


class InterviewSessionState(BaseModel):
    session_id: str
    mode: InterviewMode
    topic: str | None = None
    resume_text: str | None = None
    jd_text: str | None = None
    current_difficulty: Difficulty = Difficulty.MEDIUM
    persona: Persona = Persona.PRODUCT
    pressure_mode: PressureMode = PressureMode.PRACTICE
    scores: list[float] = Field(default_factory=list)
    turns: list[dict[str, str]] = Field(default_factory=list)
    # DB pk of the Session row (UUID as str); populated by interview engine on start()
    db_session_id: str | None = None
    question_count: int = 0  # number of scored questions asked so far


class InterviewStartResponse(BaseModel):
    session_id: str
    question: InterviewQuestion
    persona: Persona
    pressure_mode: PressureMode
    is_warmup: bool = False   # True for the icebreaker (Phase 2.1)


class InterviewTurnResponse(BaseModel):
    evaluation: InterviewEvaluation
    next_question: InterviewQuestion
    next_difficulty: Difficulty


# ---------------------------------------------------------------------------
# End-of-interview summary (Phase 1.1 / Phase 2.4)
# ---------------------------------------------------------------------------

class TopicBreakdown(BaseModel):
    topic: str
    average_score: float
    questions_attempted: int
    weak_area_count: int


class InterviewSummary(BaseModel):
    session_id: str
    overall_average_score: float
    total_questions: int
    topics: list[TopicBreakdown] = Field(default_factory=list)
    top_strengths: list[str] = Field(default_factory=list)
    top_weaknesses: list[str] = Field(default_factory=list)
    encouraging_message: str = ""
    score_delta: float | None = None   # vs previous session; None on first session
