from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_analytics_service, get_current_user
from app.models.user import User
from app.schemas.analytics import AnalyticsDashboard, RecentInterview, TopicTrendPoint
from app.schemas.common import ApiResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=ApiResponse[AnalyticsDashboard])
def dashboard(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[AnalyticsDashboard]:
    return ApiResponse(data=analytics_service.get_dashboard(current_user.id))


@router.get("/topic-trends", response_model=ApiResponse[list[TopicTrendPoint]])
def topic_trends(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[list[TopicTrendPoint]]:
    return ApiResponse(data=analytics_service.get_dashboard(current_user.id).topic_trends)


@router.get("/recent-interviews", response_model=ApiResponse[list[RecentInterview]])
def recent_interviews(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[list[RecentInterview]]:
    return ApiResponse(data=analytics_service.get_dashboard(current_user.id).recent_interviews)
