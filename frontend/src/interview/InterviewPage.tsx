import { Send } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { LiveInterviewEvents } from "./LiveInterviewEvents";
import { submitInterviewAnswer, type AnswerResult, type InterviewQuestion } from "./api";
import styles from "./InterviewPages.module.css";

export function InterviewPage() {
  const { sessionId = "" } = useParams();
  const [question, setQuestion] = useState<InterviewQuestion | null>(null);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [isSubmitting, setSubmitting] = useState(false);

  useEffect(() => {
    const cached = sessionStorage.getItem(`interview:${sessionId}:question`);
    if (cached) {
      setQuestion(JSON.parse(cached) as InterviewQuestion);
    } else {
      setQuestion({
        session_id: sessionId,
        question: "Start from the setup page to receive the generated interview question for this session.",
        difficulty: "medium",
      });
    }
  }, [sessionId]);

  async function submitAnswer(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    try {
      const next = await submitInterviewAnswer(sessionId, answer);
      setResult(next);
      setAnswer("");
      if (next.next_question) {
        setQuestion(next.next_question);
        sessionStorage.setItem(`interview:${sessionId}:question`, JSON.stringify(next.next_question));
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <span className={styles.kicker}>Live interview</span>
          <h1>Session {sessionId.slice(0, 8) || "draft"}</h1>
        </div>
      </header>
      <section className={styles.grid}>
        <form className={styles.panel} onSubmit={submitAnswer}>
          <div className={styles.question}>
            <div className={styles.meta}>
              <span>{question?.difficulty ?? "medium"}</span>
              {question?.topic && <span>{question.topic}</span>}
            </div>
            <p>{question?.question ?? "Loading question..."}</p>
          </div>
          <label className={styles.field}>
            <span>Answer</span>
            <textarea onChange={(event) => setAnswer(event.target.value)} placeholder="Type your answer or use the speech system when connected." required value={answer} />
          </label>
          <button className={styles.primary} disabled={isSubmitting} type="submit">
            <Send aria-hidden="true" size={18} />
            {isSubmitting ? "Evaluating..." : "Submit answer"}
          </button>
          {result?.feedback && <div className={styles.feedback}>Score {result.score ?? "-"}: {result.feedback}</div>}
        </form>
        <LiveInterviewEvents initialSessionId={sessionId} locked />
      </section>
    </main>
  );
}
