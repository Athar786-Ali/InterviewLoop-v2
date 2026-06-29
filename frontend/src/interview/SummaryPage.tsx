import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { ArrowLeft, ArrowUpRight, ArrowDownRight, Target, BrainCircuit, AlertCircle } from "lucide-react";

import { endInterview, type InterviewSummary } from "./api";
import styles from "./SummaryPage.module.css";

const SCORE_COLORS = {
  high: "var(--accent-green)",
  medium: "var(--accent-amber)",
  low: "var(--accent-red)",
};

function getScoreColor(score: number) {
  if (score >= 7) return SCORE_COLORS.high;
  if (score >= 4) return SCORE_COLORS.medium;
  return SCORE_COLORS.low;
}

export function SummaryPage() {
  const { sessionId = "" } = useParams();
  const navigate = useNavigate();
  
  const [summary, setSummary] = useState<InterviewSummary | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function finish() {
      try {
        const data = await endInterview(sessionId);
        setSummary(data);
      } catch (err: any) {
        setError(err.message || "Failed to finalize the interview session.");
      } finally {
        setIsLoading(false);
      }
    }
    finish();
  }, [sessionId]);

  if (isLoading) {
    return (
      <main className={styles.loadingState}>
        <div className={styles.spinner} />
        <p>Analysing your performance...</p>
      </main>
    );
  }

  if (error || !summary) {
    return (
      <main className={styles.errorState}>
        <AlertCircle size={48} className={styles.errorIcon} />
        <h2>Session Error</h2>
        <p>{error}</p>
        <button className={styles.btn} onClick={() => navigate("/interview/setup")}>
          Return to Setup
        </button>
      </main>
    );
  }

  const chartData = summary.topics.map(t => ({
    name: t.topic,
    score: t.average_score
  }));

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <span className={styles.kicker}>Session Complete</span>
          <h1>Interview Summary</h1>
        </div>
        <button className={styles.btnOutline} onClick={() => navigate("/interview/setup")}>
          <ArrowLeft size={16} /> New Interview
        </button>
      </header>

      <div className={styles.content}>
        {/* Top metrics */}
        <section className={styles.metricsGrid}>
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Overall Score</span>
            <div className={styles.metricValueWrapper}>
              <span className={styles.metricValue} style={{ color: getScoreColor(summary.overall_average_score) }}>
                {summary.overall_average_score.toFixed(1)}
              </span>
              <span className={styles.metricMax}>/ 10</span>
            </div>
            {summary.score_delta !== null && (
              <div className={`${styles.delta} ${summary.score_delta > 0 ? styles.deltaPositive : summary.score_delta < 0 ? styles.deltaNegative : ""}`}>
                {summary.score_delta > 0 ? <ArrowUpRight size={14} /> : summary.score_delta < 0 ? <ArrowDownRight size={14} /> : null}
                {Math.abs(summary.score_delta).toFixed(1)} points vs last
              </div>
            )}
          </div>

          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Questions Answered</span>
            <div className={styles.metricValueWrapper}>
              <span className={styles.metricValue}>{summary.total_questions}</span>
            </div>
          </div>

          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Feedback</span>
            <p className={styles.message}>{summary.encouraging_message}</p>
          </div>
        </section>

        {/* Strengths and Weaknesses */}
        <section className={styles.feedbackGrid}>
          <div className={styles.feedbackCard}>
            <h3 className={styles.feedbackTitle}><Target size={18} className={styles.iconGreen} /> Top Strengths</h3>
            {summary.top_strengths.length > 0 ? (
              <ul className={styles.feedbackList}>
                {summary.top_strengths.map(s => <li key={s}>{s}</li>)}
              </ul>
            ) : (
              <p className={styles.empty}>Not enough data yet.</p>
            )}
          </div>

          <div className={styles.feedbackCard}>
            <h3 className={styles.feedbackTitle}><BrainCircuit size={18} className={styles.iconAmber} /> Areas for Improvement</h3>
            {summary.top_weaknesses.length > 0 ? (
              <ul className={styles.feedbackList}>
                {summary.top_weaknesses.map(w => <li key={w}>{w}</li>)}
              </ul>
            ) : (
              <p className={styles.empty}>No clear weak areas detected.</p>
            )}
          </div>
        </section>

        {/* Chart */}
        {chartData.length > 0 && (
          <section className={styles.chartSection}>
            <h3>Score Breakdown by Topic</h3>
            <div className={styles.chartWrapper}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                  <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis domain={[0, 10]} stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip 
                    cursor={{ fill: "var(--bg-elevated)" }}
                    contentStyle={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: "8px" }}
                  />
                  <Bar dataKey="score" radius={[4, 4, 0, 0]} maxBarSize={60}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getScoreColor(entry.score)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
