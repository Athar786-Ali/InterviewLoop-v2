from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.api.v1.dependencies import get_current_user, get_report_service
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.report import ReportGenerateRequest, ReportRead, ReportVerificationResponse
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ApiResponse[ReportRead])
def generate_report(
    payload: ReportGenerateRequest,
    report_service: Annotated[ReportService, Depends(get_report_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ReportRead]:
    report = report_service.generate(current_user, payload.session_id, payload.report_type)
    return ApiResponse(data=ReportRead.model_validate(report), message="Report generated.")


@router.get("", response_model=ApiResponse[list[ReportRead]])
def list_reports(
    report_service: Annotated[ReportService, Depends(get_report_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[list[ReportRead]]:
    return ApiResponse(data=[ReportRead.model_validate(report) for report in report_service.list_reports(current_user)])


@router.get("/{report_id}/verify", response_model=ApiResponse[ReportVerificationResponse])
def verify_report(
    report_id: UUID,
    report_service: Annotated[ReportService, Depends(get_report_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ReportVerificationResponse]:
    return ApiResponse(data=report_service.verify(current_user, report_id))


@router.get("/{report_id}/download/{file_type}")
def download_report(
    report_id: UUID,
    file_type: str,
    report_service: Annotated[ReportService, Depends(get_report_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> FileResponse:
    path = report_service.download_path(current_user, report_id, file_type)
    media_type = "application/pdf" if file_type == "pdf" else "application/json"
    return FileResponse(path, media_type=media_type, filename=path.name)
