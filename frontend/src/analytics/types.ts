export type ScoreSummary = {
  average_score: number;
  completed_interviews: number;
  total_questions: number;
  interview_streak: number;
};

export type RadarTopicScore = {
  topic: string;
  score: number;
};

export type TopicInsight = {
  topic: string;
  score: number;
  delta: number;
};

export type TopicTrendPoint = {
  date: string;
  topic: string;
  score: number;
};

export type RecentInterview = {
  session_id: string;
  interview_type: string;
  status: string;
  average_score: number;
  started_at: string | null;
  completed_at: string | null;
};

export type AnalyticsDashboard = {
  summary: ScoreSummary;
  radar: RadarTopicScore[];
  weak_topics: TopicInsight[];
  improved_topics: TopicInsight[];
  topic_trends: TopicTrendPoint[];
  recent_interviews: RecentInterview[];
};

export type ApiResponse<T> = {
  success: boolean;
  data: T;
  message: string;
};
