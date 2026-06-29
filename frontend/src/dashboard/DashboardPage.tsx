import { PlayCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Link } from "react-router-dom";

import { fetchAnalyticsDashboard } from "../analytics/api";
import type { AnalyticsDashboard, TopicTrendPoint } from "../analytics/types";
import styles from "./DashboardPage.module.css";

const fallbackDashboard: AnalyticsDashboard = {
  summary: {
    average_score: 7.8,
    completed_interviews: 12,
    total_questions: 86,
    interview_streak: 5,
  },
  radar: [
    { topic: "Python", score: 8.4 },
    { topic: "SQL", score: 6.2 },
    { topic: "System Design", score: 7.1 },
    { topic: "Behavioral", score: 8.8 },
    { topic: "Algorithms", score: 6.9 },
  ],
  weak_topics: [
    { topic: "SQL joins", score: 5.4, delta: -0.6 },
    { topic: "Distributed locks", score: 5.9, delta: -0.2 },
    { topic: "Graph traversal", score: 6.1, delta: 0 },
  ],
  improved_topics: [
    { topic: "API design", score: 8.6, delta: 1.8 },
    { topic: "Python internals", score: 8.2, delta: 1.4 },
    { topic: "Behavioral structure", score: 8.9, delta: 1.1 },
  ],
  topic_trends: [
    { date: "Jun 21", topic: "Python", score: 6.8 },
    { date: "Jun 22", topic: "Python", score: 7.2 },
    { date: "Jun 23", topic: "Python", score: 7.9 },
    { date: "Jun 24", topic: "Python", score: 8.4 },
    { date: "Jun 21", topic: "SQL", score: 5.6 },
    { date: "Jun 22", topic: "SQL", score: 5.9 },
    { date: "Jun 23", topic: "SQL", score: 6.1 },
    { date: "Jun 24", topic: "SQL", score: 6.7 },
  ],
  recent_interviews: [
    { session_id: "topic-python", interview_type: "topic", status: "completed", average_score: 8.4, started_at: null, completed_at: null },
    { session_id: "resume-backend", interview_type: "resume", status: "completed", average_score: 7.6, started_at: null, completed_at: null },
    { session_id: "mixed-systems", interview_type: "mixed", status: "completed", average_score: 7.2, started_at: null, completed_at: null },
  ],
};

export function DashboardPage() {
  const [dashboard, setDashboard] = useState<AnalyticsDashboard>(fallbackDashboard);
  const [status, setStatus] = useState<"loading" | "ready" | "offline">("loading");

  useEffect(() => {
    let active = true;
    fetchAnalyticsDashboard()
      .then((data) => {
        if (active) {
          setDashboard(data);
          setStatus("ready");
        }
      })
      .catch(() => {
        if (active) {
          setStatus("offline");
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const trendData = useMemo(() => normalizeTrendData(dashboard.topic_trends), [dashboard.topic_trends]);

  return (
    <main className={styles.page}>
      <section className={styles.header}>
        <div>
          <span className={styles.kicker}>Analytics Dashboard</span>
          <h1>Interview performance cockpit</h1>
        </div>
        <div className={styles.headerActions}>
          <Link className={styles.ctaButton} to="/interview/setup">
            <PlayCircle size={14} />
            New Interview
          </Link>
          <div className={styles.syncBadge} data-state={status}>
            {status === "loading" ? "Syncing…" : status === "ready" ? "Live data" : "Preview data"}
          </div>
        </div>
      </section>

      <section className={styles.metrics}>
        <Metric label="Average score" value={dashboard.summary.average_score.toFixed(1)} helper="Across scored answers" />
        <Metric label="Completed" value={dashboard.summary.completed_interviews.toString()} helper="Mock interviews" />
        <Metric label="Questions" value={dashboard.summary.total_questions.toString()} helper="Evaluated responses" />
        <Metric label="Streak" value={`${dashboard.summary.interview_streak}d`} helper="Consecutive practice days" />
      </section>

      <section className={styles.grid}>
        <article className={styles.panel}>
          <div className={styles.panelTitle}>
            <h2>Topic radar</h2>
            <span>Score balance</span>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={dashboard.radar}>
              <PolarGrid stroke="rgba(255,255,255,0.06)" />
              <PolarAngleAxis dataKey="topic" tick={{ fill: "#8b9eb8", fontSize: 11 }} />
              <Radar dataKey="score" stroke="#19d4d4" fill="#19d4d4" fillOpacity={0.18} />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 8, color: "#f0f6fc" }} />
            </RadarChart>
          </ResponsiveContainer>
        </article>

        <article className={styles.panel}>
          <div className={styles.panelTitle}>
            <h2>Topic trends</h2>
            <span>Recent movement</span>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={trendData}>
              <defs>
                <linearGradient id="trendFill" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="5%" stopColor="#7c6ff7" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#7c6ff7" stopOpacity={0.01} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
              <XAxis dataKey="date" tick={{ fill: "#4a5568", fontSize: 11 }} />
              <YAxis domain={[0, 10]} tick={{ fill: "#4a5568", fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 8, color: "#f0f6fc" }} />
              <Area type="monotone" dataKey="score" stroke="#7c6ff7" strokeWidth={2.5} fill="url(#trendFill)" />
            </AreaChart>
          </ResponsiveContainer>
        </article>
      </section>

      <section className={styles.columns}>
        <TopicList title="Weak topics" tone="risk" topics={dashboard.weak_topics} />
        <TopicList title="Improved topics" tone="good" topics={dashboard.improved_topics} />
        <article className={styles.panel}>
          <div className={styles.panelTitle}>
            <h2>Recent interviews</h2>
            <span>Latest sessions</span>
          </div>
          <div className={styles.recentList}>
            {dashboard.recent_interviews.map((item) => (
              <div className={styles.recentItem} key={item.session_id}>
                <div>
                  <strong>{item.interview_type}</strong>
                  <span>{item.status}</span>
                </div>
                <b>{item.average_score.toFixed(1)}</b>
              </div>
            ))}
          </div>
        </article>
      </section>
    </main>
  );
}

function Metric({ label, value, helper }: { label: string; value: string; helper: string }) {
  return (
    <article className={styles.metric}>
      <span className={styles.metricLabel}>{label}</span>
      <strong className={styles.metricValue}>{value}</strong>
      <small className={styles.metricHelper}>{helper}</small>
    </article>
  );
}

function TopicList({ title, tone, topics }: { title: string; tone: "risk" | "good"; topics: { topic: string; score: number; delta: number }[] }) {
  return (
    <article className={styles.panel}>
      <div className={styles.panelTitle}>
        <h2>{title}</h2>
        <span>{tone === "risk" ? "Needs attention" : "Momentum"}</span>
      </div>
      <div className={styles.topicList}>
        {topics.map((topic) => (
          <div className={styles.topicItem} key={topic.topic}>
            <div>
              <strong>{topic.topic}</strong>
              <span>{topic.score.toFixed(1)} avg</span>
            </div>
            <b data-tone={tone}>{topic.delta > 0 ? `+${topic.delta.toFixed(1)}` : topic.delta.toFixed(1)}</b>
          </div>
        ))}
      </div>
    </article>
  );
}

function normalizeTrendData(points: TopicTrendPoint[]) {
  if (!points.length) {
    return [];
  }
  return points.map((point) => ({
    date: point.date.slice(5) || point.date,
    topic: point.topic,
    score: point.score,
  }));
}
