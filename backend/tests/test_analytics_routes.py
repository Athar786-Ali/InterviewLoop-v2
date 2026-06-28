from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_analytics_service, get_current_user
from app.main import create_app
from app.schemas.analytics import AnalyticsDashboard, ScoreSummary


class FakeAnalyticsService:
    def get_dashboard(self, user_id):
        return AnalyticsDashboard(
            summary=ScoreSummary(
                average_score=7.5,
                completed_interviews=4,
                total_questions=20,
                interview_streak=3,
            )
        )


def test_analytics_dashboard_route_returns_structured_response():
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4())
    app.dependency_overrides[get_analytics_service] = lambda: FakeAnalyticsService()
    client = TestClient(app)

    response = client.get("/api/v1/analytics/dashboard")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["summary"]["average_score"] == 7.5
