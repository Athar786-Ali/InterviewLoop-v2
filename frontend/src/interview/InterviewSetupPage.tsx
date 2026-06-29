import { BrainCircuit, Building2, CheckCircle2, FileUp, PlayCircle, Rocket, Upload } from "lucide-react";
import { type ChangeEvent, type FormEvent, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { type Difficulty, type InterviewMode, type Persona, type PressureMode, startInterview, uploadResume } from "./api";
import styles from "./InterviewPages.module.css";

const PERSONAS: { value: Persona; emoji: string; name: string; desc: string }[] = [
  { value: "product", emoji: "🏢", name: "FAANG / Product", desc: "System design, depth, edge cases" },
  { value: "service", emoji: "🏗️", name: "Service Co.", desc: "Breadth, SDLC, teamwork" },
  { value: "startup", emoji: "🚀", name: "Startup", desc: "Pragmatic, ship-it, full-stack" },
];

const MODES: { value: InterviewMode; label: string; emoji: string; sub: string }[] = [
  { value: "topic", label: "Topic", emoji: "🎯", sub: "Choose a focus area" },
  { value: "resume", label: "Resume", emoji: "📄", sub: "From your experience" },
  { value: "mixed", label: "Mixed", emoji: "🔀", sub: "Topic + Resume blend" },
  { value: "behavioral", label: "Behavioral", emoji: "🤝", sub: "STAR method & soft skills" },
  { value: "job_description", label: "Role Match", emoji: "💼", sub: "Paste a job posting" },
];

const DIFFICULTIES: { value: Difficulty; label: string }[] = [
  { value: "easy", label: "Easy" },
  { value: "medium", label: "Medium" },
  { value: "hard", label: "Hard" },
];

const TOPIC_TRACKS = [
  {
    label: "DSA", emoji: "📊",
    topics: ["Arrays", "Strings", "Linked Lists", "Trees", "Graphs", "Dynamic Programming", "Sorting & Searching", "Stacks & Queues", "Heaps", "Recursion & Backtracking", "Hashing", "Bit Manipulation"],
  },
  {
    label: "System Design", emoji: "🏗️",
    topics: ["Load Balancing", "Caching", "Database Design", "Microservices", "CAP Theorem", "Rate Limiting", "Message Queues", "API Design", "Scalability", "Distributed Systems"],
  },
  {
    label: "OS", emoji: "💻",
    topics: ["Processes & Threads", "Deadlocks", "Memory Management", "CPU Scheduling", "File Systems", "IPC", "Virtual Memory", "Semaphores"],
  },
  {
    label: "DBMS", emoji: "🗄️",
    topics: ["SQL Joins", "Normalization", "Transactions (ACID)", "Indexing", "NoSQL vs SQL", "Query Optimization", "ER Diagrams", "Stored Procedures"],
  },
  {
    label: "Computer Networks", emoji: "🌐",
    topics: ["OSI Model", "TCP/IP", "HTTP/HTTPS", "DNS", "Sockets", "IP Addressing", "Firewalls", "CDN"],
  },
  {
    label: "OOP / LLD", emoji: "🧱",
    topics: ["SOLID Principles", "Design Patterns", "Class Design", "Abstraction", "Polymorphism", "OOPS Concepts"],
  },
  {
    label: "Behavioral / HR", emoji: "🤝",
    topics: ["STAR Method", "Leadership", "Conflict Resolution", "Strengths & Weaknesses", "Teamwork", "Problem Solving"],
  },
  {
    label: "Languages", emoji: "⚡",
    topics: ["Python", "Java", "JavaScript", "C++", "Go", "TypeScript", "SQL"],
  },
];

export function InterviewSetupPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [mode, setMode] = useState<InterviewMode>("topic");
  const [difficulty, setDifficulty] = useState<Difficulty>("medium");
  const [topic, setTopic] = useState("Arrays");
  const [resumeText, setResumeText] = useState("");
  const [jdText, setJdText] = useState("");
  const [persona, setPersona] = useState<Persona>("product");
  const [pressureMode, setPressureMode] = useState<PressureMode>("practice");
  const [isStarting, setStarting] = useState(false);
  const [isUploading, setUploading] = useState(false);
  const [resumeFileName, setResumeFileName] = useState("");
  const [activeTrack, setActiveTrack] = useState(0);
  const [error, setError] = useState("");

  async function handleResumeUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      const result = await uploadResume(file);
      setResumeText(result.resume_text);
      setResumeFileName(file.name);
    } catch {
      setError("Could not parse the PDF. Try a text-based PDF or paste your resume text below.");
    } finally {
      setUploading(false);
    }
  }

  async function handleStart(event: FormEvent) {
    event.preventDefault();
    setStarting(true);
    setError("");
    try {
      const result = await startInterview({
        mode,
        initial_difficulty: difficulty,
        topic: (mode !== "resume" && mode !== "behavioral" && mode !== "job_description") ? topic : undefined,
        resume_text: (mode === "resume" || mode === "mixed") ? resumeText : undefined,
        jd_text: mode === "job_description" ? jdText : undefined,
        persona,
        pressure_mode: pressureMode,
      });
      sessionStorage.setItem(`interview:${result.session_id}:state`, JSON.stringify(result));
      navigate(`/interview/${result.session_id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "";
      if (msg.includes("401") || msg.includes("403") || msg.includes("NOT_AUTHENTICATED")) {
        setError("Session expired. Please log out and log back in.");
      } else {
        setError("Could not start the interview. Make sure Ollama is running and the model is pulled.");
      }
    } finally {
      setStarting(false);
    }
  }

  const needsResume = mode === "resume" || mode === "mixed";
  const needsTopic = mode !== "resume" && mode !== "behavioral" && mode !== "job_description";
  const needsJd = mode === "job_description";

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <span className={styles.kicker}>Interview Setup</span>
          <h1>Launch your mock interview</h1>
        </div>
      </header>

      <form className={styles.layout} onSubmit={handleStart}>
        {/* ── Left: config ── */}
        <div className={styles.panel}>
          {/* Mode */}
          <div className={styles.section}>
            <span className={styles.sectionLabel}>Interview Mode</span>
            <div className={styles.segments}>
              {MODES.map((m) => (
                <button
                  aria-pressed={mode === m.value}
                  className={styles.segmentBtn}
                  key={m.value}
                  onClick={() => setMode(m.value)}
                  type="button"
                >
                  <span className={styles.segmentIcon}>{m.emoji}</span>
                  {m.label}
                  <span className={styles.segmentSub}>{m.sub}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Persona */}
          <div className={styles.section}>
            <span className={styles.sectionLabel}>AI Interviewer Persona</span>
            <div className={styles.personaGrid}>
              {PERSONAS.map((p) => (
                <button
                  aria-pressed={persona === p.value}
                  className={styles.personaCard}
                  key={p.value}
                  onClick={() => setPersona(p.value)}
                  type="button"
                >
                  <span className={styles.personaEmoji}>{p.emoji}</span>
                  <span className={styles.personaName}>{p.name}</span>
                  <span className={styles.personaDesc}>{p.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Pressure Mode */}
          <div className={styles.section}>
            <span className={styles.sectionLabel}>Pressure Mode</span>
            <div className={styles.pressureToggle}>
              <button
                aria-pressed={pressureMode === "practice"}
                className={styles.pressureCard}
                data-mode="practice"
                onClick={() => setPressureMode("practice")}
                type="button"
              >
                <span className={styles.pressureLabel}>🌱 Practice</span>
                <span className={styles.pressureDesc}>Hints enabled. Coaching tone. Great for learning.</span>
              </button>
              <button
                aria-pressed={pressureMode === "simulated"}
                className={styles.pressureCard}
                data-mode="simulated"
                onClick={() => setPressureMode("simulated")}
                type="button"
              >
                <span className={styles.pressureLabel}>⚡ Simulated</span>
                <span className={styles.pressureDesc}>No hints. Strict scoring. Real interview atmosphere.</span>
              </button>
            </div>
          </div>

          {/* Topic Picker */}
          {needsTopic && (
            <div className={styles.section}>
              <span className={styles.sectionLabel}>Topic Focus</span>
              {/* Track tabs */}
              <div className={styles.topicTabs}>
                {TOPIC_TRACKS.map((track, i) => (
                  <button
                    className={activeTrack === i ? styles.topicTabActive : styles.topicTab}
                    key={track.label}
                    onClick={() => setActiveTrack(i)}
                    type="button"
                  >
                    {track.emoji} {track.label}
                  </button>
                ))}
              </div>
              {/* Topic chips */}
              <div className={styles.topicChips}>
                {TOPIC_TRACKS[activeTrack].topics.map((t) => (
                  <button
                    className={topic === t ? styles.topicChipActive : styles.topicChip}
                    key={t}
                    onClick={() => setTopic(t)}
                    type="button"
                  >
                    {t}
                  </button>
                ))}
              </div>
              {/* Free-text override */}
              <input
                className={styles.topicInput}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Or type a custom topic…"
                value={topic}
              />
            </div>
          )}

          {/* Difficulty */}
          <div className={styles.section}>
            <span className={styles.sectionLabel}>Starting Difficulty</span>
            <div className={styles.segments}>
              {DIFFICULTIES.map((d) => (
                <button
                  aria-pressed={difficulty === d.value}
                  className={styles.segmentBtn}
                  key={d.value}
                  onClick={() => setDifficulty(d.value)}
                  type="button"
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          {/* Resume */}
          {needsResume && (
            <div className={styles.section}>
              <span className={styles.sectionLabel}>Resume</span>

              <input
                accept=".pdf"
                hidden
                id="resume-file"
                onChange={handleResumeUpload}
                ref={fileInputRef}
                type="file"
              />

              {resumeFileName ? (
                <div className={styles.uploadSuccess}>
                  <CheckCircle2 size={16} />
                  {resumeFileName} — parsed successfully
                </div>
              ) : (
                <div
                  className={`${styles.uploadArea} ${isUploading ? styles.uploading : ""}`}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <FileUp className={styles.uploadIcon} size={24} />
                  <span className={styles.uploadText}>
                    {isUploading ? "Parsing PDF…" : "Click to upload resume PDF"}
                  </span>
                  <span className={styles.uploadSub}>PDF only · max 2 MB</span>
                </div>
              )}

              <label className={styles.field} style={{ marginTop: 10 }}>
                <span className={styles.fieldLabel}>Or paste resume text</span>
                <textarea
                  onChange={(e) => setResumeText(e.target.value)}
                  placeholder="Paste your resume content here…"
                  value={resumeText}
                />
              </label>
            </div>
          )}

          {/* Job Description */}
          {needsJd && (
            <div className={styles.section}>
              <span className={styles.sectionLabel}>Job Description</span>
              <label className={styles.field}>
                <span className={styles.fieldLabel}>Paste the job requirements</span>
                <textarea
                  onChange={(e) => setJdText(e.target.value)}
                  placeholder="Paste the job description or role requirements here..."
                  value={jdText}
                  style={{ minHeight: "150px" }}
                />
              </label>
            </div>
          )}

          {error && (
            <div className={styles.errorBanner}>
              <span>⚠️</span> {error}
            </div>
          )}

          <button className={styles.primary} disabled={isStarting} id="start-interview" type="submit">
            <PlayCircle aria-hidden="true" size={18} />
            {isStarting ? "Starting interview…" : "Launch interview"}
          </button>

        </div>

        {/* ── Right: info sidebar ── */}
        <aside className={styles.infoPanel}>
          <div className={styles.infoCard}>
            <p className={styles.infoTitle}>🧠 Adaptive Engine</p>
            <ul className={styles.infoList}>
              <li>Difficulty adjusts after each answer using a sliding-window score average</li>
              <li>Session memory prevents repeat questions in the same session</li>
              <li>Structured JSON output ensures consistent, parseable responses</li>
            </ul>
          </div>

          <div className={styles.infoCard}>
            <p className={styles.infoTitle}>💡 Hint Engine</p>
            <ul className={styles.infoList}>
              <li>Available in Practice mode only</li>
              <li>Socratic nudges — guides thinking without revealing the answer</li>
              <li>Persona-aware: FAANG hints dig deeper, Startup hints are pragmatic</li>
            </ul>
          </div>

          <div className={styles.infoCard}>
            <p className={styles.infoTitle}>⚙️ Powered by</p>
            <div className={styles.techStack}>
              {["Ollama", "Qwen2.5:3b", "FastAPI", "pypdf", "Structured Output"].map((t) => (
                <span className={styles.techPill} key={t}>{t}</span>
              ))}
            </div>
          </div>
        </aside>
      </form>
    </main>
  );
}
