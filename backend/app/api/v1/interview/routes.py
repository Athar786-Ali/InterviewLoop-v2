from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_interview_engine
from app.schemas.common import ApiResponse
from app.schemas.interview import InterviewStartRequest, InterviewStartResponse, InterviewTurnRequest, InterviewTurnResponse
from app.services.interview_engine import InterviewEngineService

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("/start", response_model=ApiResponse[InterviewStartResponse])
def start_interview(
    payload: InterviewStartRequest,
    engine: Annotated[InterviewEngineService, Depends(get_interview_engine)],
) -> ApiResponse[InterviewStartResponse]:
    return ApiResponse(data=engine.start(payload), message="Interview started.")


@router.post("/answer", response_model=ApiResponse[InterviewTurnResponse])
def submit_answer(
    payload: InterviewTurnRequest,
    engine: Annotated[InterviewEngineService, Depends(get_interview_engine)],
) -> ApiResponse[InterviewTurnResponse]:
    return ApiResponse(data=engine.answer(payload.session_id, payload.answer), message="Answer evaluated.")
