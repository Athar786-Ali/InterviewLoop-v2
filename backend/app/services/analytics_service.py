from collections import defaultdict
from datetime import timedelta

from app.models.session import Session
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import (
    AnalyticsDashboard,
    RadarTopicScore,
    RecentInterview,
    ScoreSummary,
    TopicInsight,
    TopicTrendPoint,
)


class AnalyticsService:
    def __init__(self, analytics: AnalyticsRepository) -> None:
        self.analytics = analytics

    def get_dashboard(self, user_id) -> AnalyticsDashboard:
        sessions = self.analytics.list_user_sessions(user_id)
        questions = [
            question
            for session in sessions
            for question in session.question_logs
            if question.deleted_at is None and question.score is not None
        ]
        completed_sessions = [session for session in sessions if session.status == "completed"]

        return AnalyticsDashboard(
            summary=ScoreSummary(
                average_score=self._average([question.score for question in questions]),
                completed_interviews=len(completed_sessions),
                total_questions=len(questions),
                interview_streak=self._streak(completed_sessions),
            ),
            radar=self._radar(questions),
            weak_topics=self._weak_topics(questions),
            improved_topics=self._improved_topics(questions),
            topic_trends=self._topic_trends(questions),
            recent_interviews=self._recent_interviews(sessions),
        )

    def _radar(self, questions) -> list[RadarTopicScore]:
        by_topic = self._scores_by_topic(questions)
        return [
            RadarTopicScore(topic=topic, score=self._average(scores))
            for topic, scores in sorted(by_topic.items(), key=lambda item: item[0].lower())
        ]

    def _weak_topics(self, questions) -> list[TopicInsight]:
        by_topic = self._scores_by_topic(questions)
        insights = [TopicInsight(topic=topic, score=self._average(scores)) for topic, scores in by_topic.items()]
        return sorted(insights, key=lambda insight: insight.score)[:5]

    def _improved_topics(self, questions) -> list[TopicInsight]:
        grouped = defaultdict(list)
        for question in sorted(questions, key=lambda item: item.created_at):
            grouped[question.topic].append(question.score)

        insights = []
        for topic, scores in grouped.items():
            if len(scores) < 2:
                continue
            midpoint = max(1, len(scores) // 2)
            baseline = self._average(scores[:midpoint])
            recent = self._average(scores[midpoint:])
            delta = round(recent - baseline, 2)
            if delta > 0:
                insights.append(TopicInsight(topic=topic, score=recent, delta=delta))
        return sorted(insights, key=lambda insight: insight.delta, reverse=True)[:5]

    def _topic_trends(self, questions) -> list[TopicTrendPoint]:
        grouped = defaultdict(list)
        for question in questions:
            day = question.created_at.date().isoformat()
            grouped[(day, question.topic)].append(question.score)
        return [
            TopicTrendPoint(date=day, topic=topic, score=self._average(scores))
            for (day, topic), scores in sorted(grouped.items())
        ]

    def _recent_interviews(self, sessions: list[Session]) -> list[RecentInterview]:
        recent = []
        for session in sessions[:8]:
            scores = [
                question.score
                for question in session.question_logs
                if question.deleted_at is None and question.score is not None
            ]
            recent.append(
                RecentInterview(
                    session_id=session.session_id,
                    interview_type=session.interview_type,
                    status=session.status,
                    average_score=self._average(scores),
                    started_at=session.started_at,
                    completed_at=session.completed_at,
                )
            )
        return recent

    def _streak(self, completed_sessions: list[Session]) -> int:
        completed_days = {
            (session.completed_at or session.started_at or session.created_at).date()
            for session in completed_sessions
        }
        if not completed_days:
            return 0

        current_day = max(completed_days)
        streak = 0
        while current_day in completed_days:
            streak += 1
            current_day = current_day - timedelta(days=1)
        return streak

    def _scores_by_topic(self, questions) -> dict[str, list[float]]:
        by_topic = defaultdict(list)
        for question in questions:
            by_topic[question.topic].append(question.score)
        return by_topic

    def _average(self, values: list[float]) -> float:
        clean_values = [value for value in values if value is not None]
        if not clean_values:
            return 0
        return round(sum(clean_values) / len(clean_values), 2)
