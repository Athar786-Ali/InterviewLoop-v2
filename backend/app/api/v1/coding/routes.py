"""Coding judge API routes."""

import random
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.dependencies import get_code_execution_service
from app.data.coding_problems import ALL_PROBLEMS, PROBLEMS_BY_ID
from app.schemas.coding import CodingProblem, CodingSubmitRequest, CodingSubmitResponse
from app.schemas.common import ApiResponse
from app.services.code_execution_service import CodeExecutionService
from app.services.coding_judge import CodingJudgeService

router = APIRouter(prefix="/coding", tags=["coding"])


def get_judge(
    execution_service: Annotated[CodeExecutionService, Depends(get_code_execution_service)],
) -> CodingJudgeService:
    return CodingJudgeService(execution_service)


@router.get("/problems", response_model=ApiResponse[list[CodingProblem]])
def list_problems(
    difficulty: str | None = Query(default=None, description="easy | medium | hard"),
    category: str | None = Query(default=None, description="arrays | strings | trees | …"),
    tag: str | None = Query(default=None, description="Filter by a single tag"),
) -> ApiResponse[list[CodingProblem]]:
    """Return the full problem list, optionally filtered."""
    problems = ALL_PROBLEMS
    if difficulty:
        problems = [p for p in problems if p.difficulty == difficulty]
    if category:
        problems = [p for p in problems if p.category == category]
    if tag:
        problems = [p for p in problems if tag in p.tags]
    return ApiResponse(data=problems)


@router.get("/question", response_model=ApiResponse[CodingProblem])
def random_question(
    difficulty: str | None = Query(default=None),
    category: str | None = Query(default=None),
) -> ApiResponse[CodingProblem]:
    """Return a random problem matching the filters."""
    pool = ALL_PROBLEMS
    if difficulty:
        pool = [p for p in pool if p.difficulty == difficulty]
    if category:
        pool = [p for p in pool if p.category == category]
    if not pool:
        pool = ALL_PROBLEMS
    return ApiResponse(data=random.choice(pool))


@router.get("/question/{problem_id}", response_model=ApiResponse[CodingProblem])
def get_problem(problem_id: str) -> ApiResponse[CodingProblem]:
    """Return a specific problem by ID."""
    problem = PROBLEMS_BY_ID.get(problem_id)
    if not problem:
        from app.core.exceptions import AppError
        raise AppError("PROBLEM_NOT_FOUND", f"Problem '{problem_id}' not found.", 404)
    return ApiResponse(data=problem)


@router.post("/submit", response_model=ApiResponse[CodingSubmitResponse])
def submit_solution(
    payload: CodingSubmitRequest,
    judge: Annotated[CodingJudgeService, Depends(get_judge)],
) -> ApiResponse[CodingSubmitResponse]:
    """Judge a submitted solution against all test cases."""
    result = judge.judge(payload)
    msg = f"Passed {result.passed}/{result.total} test cases."
    return ApiResponse(data=result, message=msg)
