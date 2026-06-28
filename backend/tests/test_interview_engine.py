from app.core.exceptions import AppError
from app.schemas.interview import (
    Difficulty,
    InterviewEvaluation,
    InterviewMode,
    InterviewQuestion,
    InterviewStartRequest,
)
from app.services.adaptive_difficulty import AdaptiveDifficultyService
from app.services.conversation_memory import ConversationMemory
from app.services.interview_engine import InterviewEngineService
from app.services.prompt_templates import render_question_prompt


class FakeLLM:
    def __init__(self):
        self.question_count = 0

    def generate_structured(self, prompt, schema):
        if schema is InterviewEvaluation:
            return InterviewEvaluation(score=9, feedback="Strong answer", strengths=["clear"], weaknesses=[])
        self.question_count += 1
        return InterviewQuestion(
            question=f"Question {self.question_count}?",
            topic="Python",
            difficulty=Difficulty.MEDIUM if self.question_count == 1 else Difficulty.HARD,
            expected_signals=["specificity"],
        )


def test_adaptive_difficulty_sliding_window_increases_and_decreases():
    service = AdaptiveDifficultyService()

    assert service.next_difficulty(Difficulty.MEDIUM, [8, 9, 9]) == Difficulty.HARD
    assert service.next_difficulty(Difficulty.MEDIUM, [2, 4, 3]) == Difficulty.EASY
    assert service.next_difficulty(Difficulty.MEDIUM, [5, 6, 7]) == Difficulty.MEDIUM


def test_question_prompt_contains_mode_difficulty_and_structured_output_instruction():
    request = InterviewStartRequest(mode=InterviewMode.MIXED, topic="Python", resume_text="Built APIs")
    memory = ConversationMemory()
    engine = InterviewEngineService(FakeLLM(), memory, AdaptiveDifficultyService())
    started = engine.start(request)
    state = memory.get(started.session_id)

    prompt = render_question_prompt(state, Difficulty.HARD)

    assert "Mode: mixed" in prompt
    assert "Difficulty: hard" in prompt
    assert "Return only valid JSON" in prompt
    assert "Built APIs" in prompt


def test_interview_engine_starts_session_and_generates_question():
    memory = ConversationMemory()
    engine = InterviewEngineService(FakeLLM(), memory, AdaptiveDifficultyService())

    response = engine.start(InterviewStartRequest(mode=InterviewMode.TOPIC, topic="Python"))

    assert response.session_id
    assert response.question.question == "Question 1?"
    assert memory.get(response.session_id).turns[-1]["role"] == "interviewer"


def test_interview_engine_evaluates_answer_and_adapts_next_difficulty():
    memory = ConversationMemory()
    engine = InterviewEngineService(FakeLLM(), memory, AdaptiveDifficultyService())
    started = engine.start(InterviewStartRequest(mode=InterviewMode.TOPIC, topic="Python"))

    response = engine.answer(started.session_id, "I would use dependency injection.")

    assert response.evaluation.score == 9
    assert response.next_difficulty == Difficulty.HARD
    assert response.next_question.question == "Question 2?"
    assert len(memory.get(started.session_id).turns) == 3


def test_interview_engine_rejects_missing_session():
    engine = InterviewEngineService(FakeLLM(), ConversationMemory(), AdaptiveDifficultyService())

    try:
        engine.answer("missing", "answer")
    except AppError as exc:
        assert exc.code == "INTERVIEW_SESSION_NOT_FOUND"
    else:
        raise AssertionError("Expected AppError")
