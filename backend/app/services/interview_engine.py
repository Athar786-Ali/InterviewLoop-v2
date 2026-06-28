from uuid import uuid4

from app.core.exceptions import AppError
from app.schemas.interview import (
    InterviewEvaluation,
    InterviewQuestion,
    InterviewSessionState,
    InterviewStartRequest,
    InterviewStartResponse,
    InterviewTurnResponse,
)
from app.services.adaptive_difficulty import AdaptiveDifficultyService
from app.services.conversation_memory import InterviewMemory
from app.services.llm_service import OllamaLLMService
from app.services.prompt_templates import render_evaluation_prompt, render_question_prompt


class InterviewEngineService:
    def __init__(
        self,
        llm_service: OllamaLLMService,
        memory: InterviewMemory,
        difficulty_service: AdaptiveDifficultyService,
    ) -> None:
        self.llm_service = llm_service
        self.memory = memory
        self.difficulty_service = difficulty_service

    def start(self, payload: InterviewStartRequest) -> InterviewStartResponse:
        state = InterviewSessionState(
            session_id=uuid4().hex,
            mode=payload.mode,
            topic=payload.topic,
            resume_text=payload.resume_text,
            current_difficulty=payload.initial_difficulty,
        )
        question = self._generate_question(state)
        state.turns.append({"role": "interviewer", "content": question.question})
        self.memory.save(state)
        return InterviewStartResponse(session_id=state.session_id, question=question)

    def answer(self, session_id: str, answer: str) -> InterviewTurnResponse:
        state = self.memory.get(session_id)
        if not state:
            raise AppError("INTERVIEW_SESSION_NOT_FOUND", "Interview session was not found.", 404)

        evaluation = self.llm_service.generate_structured(
            render_evaluation_prompt(state, answer),
            InterviewEvaluation,
        )
        state.scores.append(evaluation.score)
        state.turns.append({"role": "candidate", "content": answer})
        state.current_difficulty = self.difficulty_service.next_difficulty(state.current_difficulty, state.scores)
        next_question = self._generate_question(state)
        state.turns.append({"role": "interviewer", "content": next_question.question})
        self.memory.save(state)

        return InterviewTurnResponse(
            evaluation=evaluation,
            next_question=next_question,
            next_difficulty=state.current_difficulty,
        )

    def _generate_question(self, state: InterviewSessionState) -> InterviewQuestion:
        return self.llm_service.generate_structured(
            render_question_prompt(state, state.current_difficulty),
            InterviewQuestion,
        )
