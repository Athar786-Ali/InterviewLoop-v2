from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.services.analytics_service import AnalyticsService


def question(topic, score, days_ago):
    return SimpleNamespace(
        topic=topic,
        score=score,
        deleted_at=None,
        created_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
    )


def session(session_id, days_ago, questions, status="completed"):
    when = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return SimpleNamespace(
        session_id=session_id,
        interview_type="topic",
        status=status,
        started_at=when,
        completed_at=when,
        created_at=when,
        question_logs=questions,
    )


class FakeAnalyticsRepository:
    def __init__(self, sessions):
        self.sessions = sessions

    def list_user_sessions(self, user_id):
        return self.sessions


def test_dashboard_computes_summary_topics_trends_and_recent_interviews():
    sessions = [
        session("s1", 0, [question("Python", 9, 0), question("SQL", 4, 0)]),
        session("s2", 1, [question("Python", 7, 1), question("SQL", 5, 1)]),
        session("s3", 2, [question("Python", 3, 2), question("SQL", 6, 2)]),
        session("draft", 5, [question("System Design", 8, 5)], status="active"),
    ]
    service = AnalyticsService(FakeAnalyticsRepository(sessions))

    dashboard = service.get_dashboard(uuid4())

    assert dashboard.summary.average_score == 6
    assert dashboard.summary.completed_interviews == 3
    assert dashboard.summary.total_questions == 7
    assert dashboard.summary.interview_streak == 3
    assert dashboard.radar[0].topic == "Python"
    assert dashboard.weak_topics[0].topic == "SQL"
    assert dashboard.improved_topics[0].topic == "Python"
    assert dashboard.improved_topics[0].delta > 0
    assert dashboard.topic_trends
    assert dashboard.recent_interviews[0].session_id == "s1"
