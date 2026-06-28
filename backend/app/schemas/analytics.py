from datetime import datetime

from pydantic import BaseModel, Field


class ScoreSummary(BaseModel):
    average_score: float = 0
    completed_interviews: int = 0
    total_questions: int = 0
    interview_streak: int = 0


class RadarTopicScore(BaseModel):
    topic: str
    score: float


class TopicInsight(BaseModel):
    topic: str
    score: float
    delta: float = 0


class TopicTrendPoint(BaseModel):
    date: str
    topic: str
    score: float


class RecentInterview(BaseModel):
    session_id: str
    interview_type: str
    status: str
    average_score: float
    started_at: datetime | None = None
    completed_at: datetime | None = None


class AnalyticsDashboard(BaseModel):
    summary: ScoreSummary
    radar: list[RadarTopicScore] = Field(default_factory=list)
    weak_topics: list[TopicInsight] = Field(default_factory=list)
    improved_topics: list[TopicInsight] = Field(default_factory=list)
    topic_trends: list[TopicTrendPoint] = Field(default_factory=list)
    recent_interviews: list[RecentInterview] = Field(default_factory=list)
