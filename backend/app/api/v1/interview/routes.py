from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.api.v1.dependencies import get_current_user, get_hint_engine, get_interview_engine, get_resume_parser
from app.core.exceptions import AppError
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.interview import (
    HintRequest,
    HintResponse,
    InterviewStartRequest,
    InterviewStartResponse,
    InterviewSummary,
    InterviewTurnRequest,
    InterviewTurnResponse,
    PressureMode,
)
from app.services.hint_engine import HintEngineService
from app.services.interview_engine import InterviewEngineService
from app.services.resume_parser import ResumeParserService

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("/start", response_model=ApiResponse[InterviewStartResponse])
def start_interview(
    payload: InterviewStartRequest,
    engine: Annotated[InterviewEngineService, Depends(get_interview_engine)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[InterviewStartResponse]:
    return ApiResponse(data=engine.start(payload, current_user), message="Interview started.")


@router.post("/answer", response_model=ApiResponse[InterviewTurnResponse])
def submit_answer(
    payload: InterviewTurnRequest,
    engine: Annotated[InterviewEngineService, Depends(get_interview_engine)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[InterviewTurnResponse]:
    return ApiResponse(
        data=engine.answer(
            payload.session_id,
            payload.answer,
            current_user,
            payload.elapsed_seconds,
        ),
        message="Answer evaluated.",
    )


@router.post("/{session_id}/end", response_model=ApiResponse[InterviewSummary])
def end_interview(
    session_id: str,
    engine: Annotated[InterviewEngineService, Depends(get_interview_engine)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[InterviewSummary]:
    """Mark the interview complete and return a full performance summary."""
    return ApiResponse(data=engine.end(session_id, current_user), message="Interview complete.")


@router.post("/hint", response_model=ApiResponse[HintResponse])
def request_hint(
    payload: HintRequest,
    engine: Annotated[InterviewEngineService, Depends(get_interview_engine)],
    hint_engine: Annotated[HintEngineService, Depends(get_hint_engine)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[HintResponse]:
    """Return a Socratic hint for the current question.

    Blocked when the session is in Simulated pressure mode — real interviews
    don't come with hints.
    """
    state = engine.memory.get(payload.session_id)
    if not state:
        raise AppError("INTERVIEW_SESSION_NOT_FOUND", "Interview session was not found.", 404)
    if state.pressure_mode == PressureMode.SIMULATED:
        raise AppError(
            "HINTS_DISABLED",
            "Hints are not available in Simulated interview mode. Stay in the zone.",
            status.HTTP_403_FORBIDDEN,
        )
    hint = hint_engine.generate(payload.session_id, payload.current_question)
    return ApiResponse(data=hint, message="Here is a hint to guide your thinking.")


@router.post("/upload-resume", response_model=ApiResponse[dict])
def upload_resume(
    resume_parser: Annotated[ResumeParserService, Depends(get_resume_parser)],
    file: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
) -> ApiResponse[dict]:
    """Extract text from a resume PDF or plain-text upload.

    Accepts either:
    - A PDF file via multipart `file` field, OR
    - Raw text via form `text` field.

    Returns the extracted/cleaned text so the frontend can pass it to
    `InterviewStartRequest.resume_text`.
    """
    if file is not None:
        file_bytes = file.file.read()
        extracted = resume_parser.parse_pdf(file_bytes)
    elif text is not None:
        extracted = resume_parser.parse_text(text)
    else:
        raise AppError("RESUME_MISSING", "Provide either a PDF file or resume text.", 422)

    return ApiResponse(
        data={"resume_text": extracted, "char_count": len(extracted)},
        message="Resume parsed successfully.",
    )
