import { PlayCircle } from "lucide-react";
import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { startInterview, type Difficulty, type InterviewMode } from "./api";
import styles from "./InterviewPages.module.css";

export function InterviewSetupPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<InterviewMode>("topic");
  const [difficulty, setDifficulty] = useState<Difficulty>("medium");
  const [topic, setTopic] = useState("Python backend engineering");
  const [resumeText, setResumeText] = useState("");
  const [isStarting, setStarting] = useState(false);

  async function handleStart(event: FormEvent) {
    event.preventDefault();
    setStarting(true);
    try {
      const question = await startInterview({ mode, difficulty, topic, resume_text: resumeText });
      sessionStorage.setItem(`interview:${question.session_id}:question`, JSON.stringify(question));
      navigate(`/interview/${question.session_id}`);
    } finally {
      setStarting(false);
    }
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <span className={styles.kicker}>Interview setup</span>
          <h1>Launch an adaptive mock interview</h1>
        </div>
      </header>
      <form className={styles.grid} onSubmit={handleStart}>
        <section className={styles.panel}>
          <span className={styles.label}>Mode</span>
          <div className={styles.segments}>
            {(["topic", "resume", "mixed"] as InterviewMode[]).map((item) => (
              <button aria-pressed={mode === item} key={item} onClick={() => setMode(item)} type="button">
                {item}
              </button>
            ))}
          </div>
          <label className={styles.field}>
            <span>Difficulty</span>
            <select onChange={(event) => setDifficulty(event.target.value as Difficulty)} value={difficulty}>
              <option value="easy">easy</option>
              <option value="medium">medium</option>
              <option value="hard">hard</option>
            </select>
          </label>
          <label className={styles.field}>
            <span>Topic focus</span>
            <input onChange={(event) => setTopic(event.target.value)} value={topic} />
          </label>
          <label className={styles.field}>
            <span>Resume context</span>
            <textarea onChange={(event) => setResumeText(event.target.value)} placeholder="Paste resume summary for resume or mixed mode" value={resumeText} />
          </label>
          <button className={styles.primary} disabled={isStarting} type="submit">
            <PlayCircle aria-hidden="true" size={18} />
            {isStarting ? "Starting..." : "Start interview"}
          </button>
        </section>
        <aside className={styles.panel}>
          <h2>Adaptive engine</h2>
          <p>Difficulty is adjusted by the backend using sliding-window scoring and session memory. The frontend keeps setup intent clean and observable.</p>
          <div className={styles.meta}>
            <span>Ollama</span>
            <span>Qwen2.5:7b</span>
            <span>Structured output</span>
          </div>
        </aside>
      </form>
    </main>
  );
}
