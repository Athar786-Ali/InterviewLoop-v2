import { BrainCircuit, ChevronRight, Lightbulb, Loader2, Send, ShieldAlert, Sparkles, Target } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { type AnswerResult, type InterviewQuestion, type Persona, type PressureMode, requestHint, submitInterviewAnswer } from "./api";
import styles from "./InterviewWorkspace.module.css";
import { WebcamConfidence } from "./WebcamConfidence";


type SessionState = {
  session_id: string;
  question: InterviewQuestion;
  persona: Persona;
  pressure_mode: PressureMode;
};

const PERSONA_LABELS: Record<Persona, string> = {
  product: "🏢 FAANG / Product",
  service: "🏗️ Service Co.",
  startup: "🚀 Startup",
};

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: "var(--accent-green)",
  medium: "var(--accent-amber)",
  hard: "var(--accent-red)",
};

export function InterviewPage() {
  const { sessionId = "" } = useParams();
  const [sessionState, setSessionState] = useState<SessionState | null>(null);
  const [question, setQuestion] = useState<InterviewQuestion | null>(null);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [hint, setHint] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [isSubmitting, setSubmitting] = useState(false);
  const [isHinting, setHinting] = useState(false);
  const [questionCount, setQuestionCount] = useState(1);

  useEffect(() => {
    const cached = sessionStorage.getItem(`interview:${sessionId}:state`);
    if (cached) {
      const parsed = JSON.parse(cached) as SessionState;
      setSessionState(parsed);
      setQuestion(parsed.question);
    } else {
      setQuestion({
        question: "Navigate to Setup to start a configured interview session.",
        difficulty: "medium",
      });
    }
  }, [sessionId]);

  async function submitAnswer(event: FormEvent) {
    event.preventDefault();
    if (!answer.trim()) return;
    setSubmitting(true);
    setHint("");
    setSubmitError("");
    try {
      const next = await submitInterviewAnswer(sessionId, answer);
      setResult(next);
      setAnswer("");
      setQuestionCount((c) => c + 1);
      if (next.next_question) {
        setQuestion(next.next_question);
        const updatedState = sessionState
          ? { ...sessionState, question: next.next_question }
          : null;
        if (updatedState) {
          sessionStorage.setItem(`interview:${sessionId}:state`, JSON.stringify(updatedState));
        }
      }
    } catch {
      setSubmitError("Could not evaluate your answer. Check that the Ollama model is running.");
    } finally {
      setSubmitting(false);
    }
  }

  async function getHint() {
    if (!question?.question) return;
    setHinting(true);
    try {
      const res = await requestHint(sessionId, question.question);
      setHint(res.hint);
    } catch (err: any) {
      if (err?.response?.status === 403) {
        setHint("Hints are disabled in Simulated mode. Stay in the zone! 💪");
      } else {
        setHint("Could not fetch a hint right now. Try again.");
      }
    } finally {
      setHinting(false);
    }
  }

  const isSimulated = sessionState?.pressure_mode === "simulated";
  const diffColor = question ? DIFFICULTY_COLORS[question.difficulty] ?? "var(--text-secondary)" : "var(--text-secondary)";

  return (
    <main className={styles.page}>
      {/* ── Header bar ── */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.kicker}>Live Session</span>
          <div className={styles.sessionId}>
            Session <code>{sessionId.slice(0, 10)}…</code>
          </div>
        </div>
        <div className={styles.headerBadges}>
          {sessionState && (
            <span className={styles.badge}>{PERSONA_LABELS[sessionState.persona]}</span>
          )}
          {isSimulated ? (
            <span className={`${styles.badge} ${styles.badgeAmber}`}>
              <ShieldAlert size={12} /> Simulated
            </span>
          ) : (
            <span className={`${styles.badge} ${styles.badgeGreen}`}>
              <Sparkles size={12} /> Practice
            </span>
          )}
          <span className={styles.badge} style={{ borderColor: diffColor, color: diffColor }}>
            {question?.difficulty ?? "medium"}
          </span>
        </div>
      </header>

      {/* ── Workspace grid ── */}
      <div className={styles.workspace}>
        {/* ── Left: Question + Hint ── */}
        <aside className={styles.questionPanel}>
          <div className={styles.questionBadge}>
            <Target size={14} />
            Q{questionCount}
          </div>
          {question?.topic && (
            <span className={styles.questionTopic}>{question.topic}</span>
          )}
          <p className={styles.questionText}>
            {question?.question ?? "Loading question…"}
          </p>

          {question?.expected_signals && question.expected_signals.length > 0 && (
            <div className={styles.signals}>
              <span className={styles.signalsLabel}>Expected signals</span>
              {question.expected_signals.map((s) => (
                <span className={styles.signalPill} key={s}>{s}</span>
              ))}
            </div>
          )}

          {/* Hint area */}
          <div className={styles.hintSection}>
            <button
              className={`${styles.hintBtn} ${isSimulated ? styles.hintBtnDisabled : ""}`}
              disabled={isHinting || isSimulated}
              id="request-hint"
              onClick={getHint}
              title={isSimulated ? "Hints are disabled in Simulated mode" : "Get a Socratic hint"}
              type="button"
            >
              {isHinting ? <Loader2 className={styles.spin} size={14} /> : <Lightbulb size={14} />}
              {isSimulated ? "No hints (Simulated)" : "Get a hint"}
            </button>
            {hint && (
              <div className={styles.hintCard}>
                <BrainCircuit className={styles.hintIcon} size={14} />
                <p>{hint}</p>
              </div>
            )}
          </div>
        </aside>

        {/* ── Right: Answer form + Feedback ── */}
        <section className={styles.answerPanel}>
          <form onSubmit={submitAnswer}>
            <label className={styles.answerLabel}>Your answer</label>
            <textarea
              className={styles.answerTextarea}
              id="answer-input"
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Type your answer clearly and concisely. Explain your reasoning."
              required
              value={answer}
            />
            <button className={styles.submitBtn} disabled={isSubmitting || !answer.trim()} type="submit">
              {isSubmitting
                ? <><Loader2 className={styles.spin} size={16} /> Evaluating…</>
                : <><Send size={16} /> Submit answer</>
              }
            </button>
            {submitError && (
              <div className={styles.submitError}>⚠️ {submitError}</div>
            )}
          </form>

          {/* ── Evaluation result ── */}
          {result && (
            <div className={styles.evaluation} key={questionCount}>
              <div className={styles.evalHeader}>
                <div className={styles.scoreRing} style={{ "--score-pct": `${(result.evaluation.score / 10) * 100}%` } as React.CSSProperties}>
                  <span className={styles.scoreValue}>{result.evaluation.score.toFixed(1)}</span>
                  <span className={styles.scoreLabel}>/ 10</span>
                </div>
                <div>
                  <div className={styles.evalTitle}>Evaluation</div>
                  <p className={styles.evalFeedback}>{result.evaluation.feedback}</p>
                </div>
              </div>

              {result.evaluation.what_went_well.length > 0 && (
                <div className={styles.evalSection}>
                  <span className={styles.evalSectionLabel}>✅ What went well</span>
                  <ul className={styles.evalList}>
                    {result.evaluation.what_went_well.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {result.evaluation.next_time_try && (
                <div className={`${styles.evalSection} ${styles.evalTip}`}>
                  <span className={styles.evalSectionLabel}>💡 Next time, try</span>
                  <p className={styles.evalTipText}>{result.evaluation.next_time_try}</p>
                </div>
              )}

              <div className={styles.nextDifficulty}>
                <ChevronRight size={14} />
                Next difficulty: <strong>{result.next_difficulty}</strong>
              </div>
            </div>
          )}
        </section>
      </div>

      {/* ── Webcam confidence PiP overlay ── */}
      <WebcamConfidence />
    </main>
  );
}
