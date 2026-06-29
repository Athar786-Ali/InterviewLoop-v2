from pydantic import BaseModel as _BaseModel

from app.core.exceptions import AppError
from app.schemas.interview import HintResponse, InterviewSessionState
from app.services.conversation_memory import InterviewMemory
from app.services.llm_service import OllamaLLMService
from app.services.prompt_templates import render_hint_prompt


class _HintLLMResponse:
    """Internal Pydantic model for the LLM structured output."""
    from pydantic import BaseModel

    class _Schema(BaseModel):
        hint: str


class _HintSchema(_BaseModel):
    hint: str


class HintEngineService:
    """Generates Socratic hints for struggling candidates.

    In Simulated pressure mode, hints are blocked at the route layer.
    This service only handles the LLM interaction itself.
    """

    def __init__(self, llm_service: OllamaLLMService, memory: InterviewMemory) -> None:
        self.llm_service = llm_service
        self.memory = memory

    def generate(self, session_id: str, current_question: str) -> HintResponse:
        """Generate a Socratic hint for the current interview question.

        Args:
            session_id: The active interview session ID.
            current_question: The question the candidate is stuck on.

        Returns:
            A HintResponse containing a guiding nudge.

        Raises:
            AppError: If the session is not found.
        """
        state: InterviewSessionState | None = self.memory.get(session_id)
        if not state:
            raise AppError("INTERVIEW_SESSION_NOT_FOUND", "Interview session was not found.", 404)

        result = self.llm_service.generate_structured(
            render_hint_prompt(state, current_question),
            _HintSchema,
        )
        return HintResponse(session_id=session_id, hint=result.hint)
