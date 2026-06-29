import Editor from "@monaco-editor/react";
import {
  BookOpen, CheckCircle2, ChevronDown, ChevronRight,
  Code2, Loader2, Play, RefreshCw, XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import styles from "./CodingRound.module.css";
import type { CodeLanguage, CodingProblem, SubmitResponse } from "./codingApi";
import { fetchCodingProblems, fetchRandomProblem, submitSolution } from "./codingApi";

const DIFFICULTY_COLOR = {
  easy:   "var(--accent-green)",
  medium: "var(--accent-amber)",
  hard:   "var(--accent-red)",
};

const CATEGORIES = [
  "arrays", "strings", "linked-lists", "trees", "dynamic-programming",
  "sorting-searching", "graphs", "stacks-queues", "math-bits", "recursion",
];

const LANGUAGES: { value: CodeLanguage; label: string; monacoLang: string }[] = [
  { value: "python",     label: "Python",     monacoLang: "python" },
  { value: "javascript", label: "JavaScript", monacoLang: "javascript" },
  { value: "java",       label: "Java",       monacoLang: "java" },
  { value: "cpp",        label: "C++",        monacoLang: "cpp" },
];

export function CodingRoundPage() {
  const [problems, setProblems] = useState<CodingProblem[]>([]);
  const [problem, setProblem] = useState<CodingProblem | null>(null);
  const [language, setLanguage] = useState<CodeLanguage>("python");
  const [code, setCode] = useState("");
  const [result, setResult] = useState<SubmitResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setSubmitting] = useState(false);
  const [filterDiff, setFilterDiff] = useState("");
  const [filterCat, setFilterCat] = useState("");
  const [showProblems, setShowProblems] = useState(false);
  const [elapsedSec, setElapsedSec] = useState(0);
  const [timerActive, setTimerActive] = useState(false);

  useEffect(() => {
    fetchCodingProblems()
      .then((data) => {
        setProblems(data);
        if (data.length) loadProblem(data[0]);
      })
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  // Timer
  useEffect(() => {
    if (!timerActive) return;
    const id = setInterval(() => setElapsedSec((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [timerActive]);

  function loadProblem(p: CodingProblem) {
    setProblem(p);
    setCode(p.starter_code[language] ?? p.starter_code["python"] ?? "");
    setResult(null);
    setElapsedSec(0);
    setTimerActive(true);
    setShowProblems(false);
  }

  async function pickRandom() {
    setIsLoading(true);
    try {
      const p = await fetchRandomProblem({
        difficulty: filterDiff || undefined,
        category: filterCat || undefined,
      });
      loadProblem(p);
    } catch { /* use local fallback */ } finally {
      setIsLoading(false);
    }
  }

  async function handleSubmit() {
    if (!problem) return;
    setSubmitting(true);
    setResult(null);
    try {
      const res = await submitSolution(problem.id, language, code);
      setResult(res);
      setTimerActive(false);
    } catch {
      setResult({
        problem_id: problem.id, language, passed: 0,
        total: problem.test_cases.length, all_passed: false,
        results: problem.test_cases.map((tc) => ({
          label: tc.label, input: tc.input, expected: tc.expected_output,
          actual: "Error: could not reach backend", passed: false, runtime_ms: null,
        })),
        stderr: "Backend unreachable", timed_out: false,
      });
    } finally {
      setSubmitting(false);
    }
  }

  function onLanguageChange(lang: CodeLanguage) {
    setLanguage(lang);
    if (problem) {
      setCode(problem.starter_code[lang] ?? problem.starter_code["python"] ?? code);
    }
    setResult(null);
  }

  const filteredProblems = useMemo(() => problems.filter((p) => {
    if (filterDiff && p.difficulty !== filterDiff) return false;
    if (filterCat && p.category !== filterCat) return false;
    return true;
  }), [problems, filterDiff, filterCat]);

  const timerLabel = `${String(Math.floor(elapsedSec / 60)).padStart(2, "0")}:${String(elapsedSec % 60).padStart(2, "0")}`;

  return (
    <main className={styles.page}>
      {/* ── Top toolbar ── */}
      <header className={styles.topbar}>
        <div className={styles.topbarLeft}>
          <span className={styles.logo}><Code2 size={16} /> Coding Round</span>
          <button className={styles.problemPicker} onClick={() => setShowProblems(!showProblems)} type="button">
            {problem ? problem.title : "Pick a problem"}
            <ChevronDown size={14} />
          </button>
        </div>
        <div className={styles.topbarRight}>
          {/* Difficulty filter */}
          <select className={styles.filter} onChange={(e) => setFilterDiff(e.target.value)} value={filterDiff}>
            <option value="">All Difficulty</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
          {/* Category filter */}
          <select className={styles.filter} onChange={(e) => setFilterCat(e.target.value)} value={filterCat}>
            <option value="">All Topics</option>
            {CATEGORIES.map((c) => <option key={c} value={c}>{c.replace(/-/g, " ")}</option>)}
          </select>
          <button className={styles.randomBtn} onClick={pickRandom} type="button">
            <RefreshCw size={13} /> Random
          </button>
          {/* Language selector */}
          <div className={styles.langTabs}>
            {LANGUAGES.map((l) => (
              <button
                className={language === l.value ? styles.langActive : styles.langTab}
                key={l.value}
                onClick={() => onLanguageChange(l.value)}
                type="button"
              >{l.label}</button>
            ))}
          </div>
          <span className={styles.timer}>{timerLabel}</span>
        </div>
      </header>

      {/* ── Problem dropdown list ── */}
      {showProblems && (
        <div className={styles.problemDropdown}>
          {filteredProblems.map((p) => (
            <button
              className={`${styles.problemRow} ${problem?.id === p.id ? styles.problemRowActive : ""}`}
              key={p.id}
              onClick={() => loadProblem(p)}
              type="button"
            >
              <span
                className={styles.diffDot}
                style={{ background: DIFFICULTY_COLOR[p.difficulty] }}
              />
              <span className={styles.problemTitle}>{p.title}</span>
              <span className={styles.problemCat}>{p.category}</span>
            </button>
          ))}
          {filteredProblems.length === 0 && (
            <div className={styles.noProblem}>No problems match the filter.</div>
          )}
        </div>
      )}

      {/* ── Main workspace ── */}
      <div className={styles.workspace}>
        {/* ── Problem panel ── */}
        <aside className={styles.problemPanel}>
          {isLoading && (
            <div className={styles.loading}>
              <Loader2 className={styles.spin} size={24} />
              <span>Loading problem…</span>
            </div>
          )}
          {problem && !isLoading && (
            <>
              <div className={styles.problemHeader}>
                <div>
                  <h1 className={styles.problemTitleLarge}>{problem.title}</h1>
                  <div className={styles.problemMeta}>
                    <span
                      className={styles.diffBadge}
                      style={{ color: DIFFICULTY_COLOR[problem.difficulty], borderColor: DIFFICULTY_COLOR[problem.difficulty] }}
                    >{problem.difficulty}</span>
                    <span className={styles.catBadge}>{problem.category.replace(/-/g, " ")}</span>
                    {problem.tags.slice(0, 3).map((t) => (
                      <span className={styles.tagBadge} key={t}>{t}</span>
                    ))}
                  </div>
                </div>
              </div>

              <div className={styles.problemBody}>
                <p className={styles.problemText}>{problem.problem_statement}</p>

                {problem.constraints.length > 0 && (
                  <div className={styles.section}>
                    <span className={styles.sectionLabel}>Constraints</span>
                    <ul className={styles.constraintList}>
                      {problem.constraints.map((c) => <li key={c}>{c}</li>)}
                    </ul>
                  </div>
                )}

                {problem.examples.length > 0 && (
                  <div className={styles.section}>
                    <span className={styles.sectionLabel}>Examples</span>
                    {problem.examples.map((ex, i) => (
                      <div className={styles.example} key={i}>
                        <div className={styles.exampleRow}><b>Input:</b> <code>{ex.input}</code></div>
                        <div className={styles.exampleRow}><b>Output:</b> <code>{ex.output}</code></div>
                        {ex.explanation && <div className={styles.exampleNote}>{ex.explanation}</div>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </aside>

        {/* ── Editor + Results ── */}
        <div className={styles.editorColumn}>
          {/* Monaco editor */}
          <div className={styles.editorWrap}>
            <Editor
              height="100%"
              language={LANGUAGES.find((l) => l.value === language)?.monacoLang ?? "python"}
              onChange={(v) => setCode(v ?? "")}
              options={{
                fontSize: 14,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                padding: { top: 16, bottom: 16 },
                wordWrap: "on",
                lineNumbers: "on",
                renderLineHighlight: "line",
                cursorBlinking: "smooth",
              }}
              theme="vs-dark"
              value={code}
            />
          </div>

          {/* Submit bar */}
          <div className={styles.submitBar}>
            {result && (
              <span className={result.all_passed ? styles.passLabel : styles.failLabel}>
                {result.all_passed
                  ? <><CheckCircle2 size={14} /> All {result.total} tests passed!</>
                  : <><XCircle size={14} /> {result.passed}/{result.total} tests passed</>
                }
              </span>
            )}
            <button
              className={styles.submitBtn}
              disabled={isSubmitting || !problem}
              onClick={handleSubmit}
              type="button"
            >
              {isSubmitting
                ? <><Loader2 className={styles.spin} size={15} /> Running tests…</>
                : <><Play size={15} /> Run Tests</>
              }
            </button>
          </div>

          {/* Test case results */}
          {result && (
            <div className={styles.resultsPanel}>
              <div className={styles.resultsHeader}>
                <BookOpen size={14} />
                <span>Test Results</span>
                <span className={styles.resultsSummary}>
                  {result.passed}/{result.total} passed
                  {result.timed_out && " · Time Limit Exceeded"}
                </span>
              </div>
              {result.results.map((r, i) => (
                <div
                  className={`${styles.testCase} ${r.passed ? styles.testPass : styles.testFail}`}
                  key={i}
                >
                  <div className={styles.testHeader}>
                    {r.passed
                      ? <CheckCircle2 className={styles.passIcon} size={14} />
                      : <XCircle className={styles.failIcon} size={14} />
                    }
                    <span className={styles.testLabel}>
                      {r.label || `Test ${i + 1}`}
                    </span>
                    {r.runtime_ms != null && (
                      <span className={styles.runtime}>{r.runtime_ms}ms</span>
                    )}
                    <ChevronRight size={12} className={styles.testArrow} />
                  </div>
                  {!r.passed && (
                    <div className={styles.testDetails}>
                      <div className={styles.testRow}>
                        <span>Input</span><code>{r.input}</code>
                      </div>
                      <div className={styles.testRow}>
                        <span>Expected</span><code className={styles.expected}>{r.expected}</code>
                      </div>
                      <div className={styles.testRow}>
                        <span>Got</span><code className={styles.actual}>{r.actual || "(empty)"}</code>
                      </div>
                    </div>
                  )}
                </div>
              ))}
              {result.stderr && (
                <div className={styles.stderrBox}>
                  <span>Error output</span>
                  <pre>{result.stderr}</pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
