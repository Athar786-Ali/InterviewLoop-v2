"""Interview engine service.

Orchestrates the full interview lifecycle:
  1. start()  — creates DB Session row, generates warm-up question (unscored).
  2. answer() — scores answer via LLM, persists QuestionLog + TopicPerformance,
                advances adaptive difficulty, returns next question.
  3. end()    — marks Session completed, aggregates InterviewSummary.

Architecture: route -> service (this file) -> repository -> SQLAlchemy model.
In-memory ConversationMemory holds LLM context between turns; the DB holds the
durable record.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from app.core.exceptions import AppError
from app.db.base import utc_now
from app.models.user import User
from app.repositories.question_log_repository import QuestionLogRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.topic_performance_repository import TopicPerformanceRepository
from app.schemas.interview import (
    Difficulty,
    InterviewEvaluation,
    InterviewQuestion,
    InterviewSessionState,
    InterviewStartRequest,
    InterviewStartResponse,
    InterviewSummary,
    InterviewTurnResponse,
    TopicBreakdown,
)
from app.services.adaptive_difficulty import AdaptiveDifficultyService
from app.services.conversation_memory import InterviewMemory
from app.services.llm_service import OllamaLLMService
from app.services.prompt_templates import render_evaluation_prompt, render_question_prompt
from app.services.speech_analytics import SpeechAnalyticsService

# Fixed warm-up question — not scored, not stored as a QuestionLog
_WARMUP_QUESTION = InterviewQuestion(
    question=(
        "Before we dive in, tell me a bit about yourself and "
        "what you're hoping to get out of this practice session."
    ),
    topic="warmup",
    difficulty=Difficulty.EASY,
    expected_signals=[],
)

_ENCOURAGING_MESSAGES = [
    "Great session! Keep up the momentum.",
    "Every practice session makes you sharper. Well done!",
    "You're building interview confidence with every attempt.",
    "Solid effort! Review the weak areas and you'll be ready.",
]


def _encouraging_message(avg: float, delta: float | None) -> str:
    if delta is not None and delta > 0:
        return f"You improved {delta:.1f} points compared to your last session. Keep it up!"
    if avg >= 7:
        return "Excellent performance! You're well-prepared."
    if avg >= 5:
        return "Good effort! Focus on your weak areas and you'll be interview-ready."
    return "Keep practising — every session makes you stronger. Review the feedback above."


class InterviewEngineService:
    def __init__(
        self,
        llm_service: OllamaLLMService,
        memory: InterviewMemory,
        difficulty_service: AdaptiveDifficultyService,
        session_repo: SessionRepository,
        question_log_repo: QuestionLogRepository,
        topic_perf_repo: TopicPerformanceRepository,
    ) -> None:
        self.llm_service = llm_service
        self.memory = memory
        self.difficulty_service = difficulty_service
        self.session_repo = session_repo
        self.question_log_repo = question_log_repo
        self.topic_perf_repo = topic_perf_repo

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, payload: InterviewStartRequest, user: User) -> InterviewStartResponse:
        """Create a DB session, seed in-memory state, return warm-up question."""
        session_id = uuid4().hex

        # Persist interview session to DB
        db_session = self.session_repo.create_interview_session(
            user_id=user.id,
            session_id=session_id,
            interview_type=payload.mode.value,
            started_at=utc_now(),
        )

        state = InterviewSessionState(
            session_id=session_id,
            mode=payload.mode,
            topic=payload.topic,
            resume_text=payload.resume_text,
            jd_text=payload.jd_text,
            current_difficulty=payload.initial_difficulty,
            persona=payload.persona,
            pressure_mode=payload.pressure_mode,
            db_session_id=str(db_session.id),
            question_count=0,
        )
        state.turns.append({"role": "interviewer", "content": _WARMUP_QUESTION.question})
        self.memory.save(state)

        return InterviewStartResponse(
            session_id=session_id,
            question=_WARMUP_QUESTION,
            persona=state.persona,
            pressure_mode=state.pressure_mode,
            is_warmup=True,
        )

    def answer(
        self,
        session_id: str,
        answer: str,
        user: User,
        elapsed_seconds: float | None = None,
    ) -> InterviewTurnResponse:
        """Score candidate answer, persist to DB, return next question."""
        state = self.memory.get(session_id)
        if not state:
            raise AppError("INTERVIEW_SESSION_NOT_FOUND", "Interview session was not found.", 404)

        # Score answer via LLM
        evaluation: InterviewEvaluation = self.llm_service.generate_structured(
            render_evaluation_prompt(state, answer),
            InterviewEvaluation,
        )

        # Phase 2.6 — speech analytics (pure heuristics, no LLM)
        speech = SpeechAnalyticsService.analyse(answer, elapsed_seconds)
        evaluation.filler_count = speech.filler_count
        evaluation.words_per_minute = speech.words_per_minute

        # Advance adaptive difficulty
        state.scores.append(evaluation.score)
        state.turns.append({"role": "candidate", "content": answer})
        state.current_difficulty = self.difficulty_service.next_difficulty(
            state.current_difficulty, state.scores
        )

        # Generate next (now scored) question
        next_question = self._generate_question(state)
        state.turns.append({"role": "interviewer", "content": next_question.question})

        # Increment question count (first answer = question 1 answered)
        state.question_count = (state.question_count or 0) + 1
        self.memory.save(state)

        # Determine which question was just answered (the current warm-up was Q0)
        sequence_number = state.question_count

        # Persist QuestionLog and TopicPerformance if we have a DB session
        if state.db_session_id:
            db_session_uuid = UUID(state.db_session_id)
            # Find the question text for the answered question from turns
            # turns[-3] = interviewer question, turns[-2] = candidate answer
            answered_question_text = ""
            for i in range(len(state.turns) - 2, -1, -1):
                if state.turns[i].get("role") == "interviewer":
                    answered_question_text = state.turns[i]["content"]
                    break

            topic = next_question.topic or state.topic or "general"

            self.question_log_repo.create(
                session_id=db_session_uuid,
                sequence_number=sequence_number,
                topic=topic,
                difficulty=state.current_difficulty.value,
                question_text=answered_question_text,
                answer_text=answer,
                score=evaluation.score,
                feedback=evaluation.feedback,
            )
            self.topic_perf_repo.upsert_score(
                user_id=user.id,
                session_id=db_session_uuid,
                topic=topic,
                new_score=evaluation.score,
            )

        return InterviewTurnResponse(
            evaluation=evaluation,
            next_question=next_question,
            next_difficulty=state.current_difficulty,
        )

    def end(self, session_id: str, user: User) -> InterviewSummary:
        """Mark interview complete, aggregate and return summary."""
        # Mark DB session completed
        db_session = self.session_repo.get_by_session_id(session_id)
        if not db_session or db_session.user_id != user.id:
            raise AppError("INTERVIEW_SESSION_NOT_FOUND", "Interview session was not found.", 404)

        db_session.status = "completed"
        db_session.completed_at = utc_now()
        self.session_repo.save(db_session)

        # Aggregate question logs
        logs = self.question_log_repo.list_for_session(db_session.id)
        scored = [log for log in logs if log.score is not None]

        overall_avg = round(sum(log.score for log in scored) / len(scored), 2) if scored else 0.0

        # Per-topic breakdown from TopicPerformance rows
        topic_perfs = self.topic_perf_repo.list_for_user(user.id)
        session_perfs = [tp for tp in topic_perfs if tp.session_id == db_session.id]
        topics = [
            TopicBreakdown(
                topic=tp.topic,
                average_score=tp.average_score or 0.0,
                questions_attempted=tp.questions_attempted,
                weak_area_count=tp.weak_area_count,
            )
            for tp in session_perfs
        ]

        # Simple strength/weakness extraction from evaluations
        strengths: list[str] = []
        weaknesses: list[str] = []
        for log in scored:
            if log.score and log.score >= 7 and log.topic not in strengths:
                strengths.append(log.topic)
            elif log.score and log.score < 4 and log.topic not in weaknesses:
                weaknesses.append(log.topic)

        # Score delta vs last completed session (if any)
        delta: float | None = None
        all_sessions = self.session_repo.list_active_by_user(user.id)
        prev_completed = [
            s for s in all_sessions
            if s.status == "completed" and str(s.id) != str(db_session.id)
        ]
        if prev_completed:
            prev = prev_completed[0]
            prev_logs = self.question_log_repo.list_for_session(prev.id)
            prev_scored = [log for log in prev_logs if log.score is not None]
            if prev_scored:
                prev_avg = sum(log.score for log in prev_scored) / len(prev_scored)
                delta = round(overall_avg - prev_avg, 2)

        # Clean up in-memory state
        if hasattr(self.memory, "sessions"):
            self.memory.sessions.pop(session_id, None)  # type: ignore[attr-defined]

        return InterviewSummary(
            session_id=session_id,
            overall_average_score=overall_avg,
            total_questions=len(scored),
            topics=topics,
            top_strengths=strengths[:3],
            top_weaknesses=weaknesses[:3],
            encouraging_message=_encouraging_message(overall_avg, delta),
            score_delta=delta,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generate_question(self, state: InterviewSessionState) -> InterviewQuestion:
        return self.llm_service.generate_structured(
            render_question_prompt(state, state.current_difficulty),
            InterviewQuestion,
        )
