from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_code_execution_service
from app.schemas.code_execution import CodeExecutionRequest, CodeExecutionResult, RuntimeSpec
from app.schemas.common import ApiResponse
from app.services.code_execution_service import CodeExecutionService

router = APIRouter(prefix="/code-execution", tags=["code-execution"])


@router.get("/runtimes", response_model=ApiResponse[list[RuntimeSpec]])
def runtimes(
    service: Annotated[CodeExecutionService, Depends(get_code_execution_service)],
) -> ApiResponse[list[RuntimeSpec]]:
    return ApiResponse(data=service.runtimes())


@router.post("/run", response_model=ApiResponse[CodeExecutionResult])
def run_code(
    payload: CodeExecutionRequest,
    service: Annotated[CodeExecutionService, Depends(get_code_execution_service)],
) -> ApiResponse[CodeExecutionResult]:
    return ApiResponse(data=service.execute(payload), message="Execution complete.")
