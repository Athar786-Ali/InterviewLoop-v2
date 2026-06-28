import Editor from "@monaco-editor/react";
import { useEffect, useMemo, useState } from "react";

import { fetchRuntimes, runCode } from "./api";
import styles from "./CodingRoundPage.module.css";
import type { CodeExecutionResult, CodeLanguage, RuntimeSpec } from "./types";

const fallbackRuntimes: RuntimeSpec[] = [
  { language: "python", label: "Python", monaco_language: "python", template: 'print("Hello from Python")\n' },
  { language: "cpp", label: "C++", monaco_language: "cpp", template: '#include <iostream>\nint main() { std::cout << "Hello"; }\n' },
  { language: "java", label: "Java", monaco_language: "java", template: 'public class Main { public static void main(String[] args) { System.out.println("Hello"); } }\n' },
  { language: "javascript", label: "JavaScript", monaco_language: "javascript", template: 'console.log("Hello from JavaScript");\n' },
];

export function CodingRoundPage() {
  const [runtimes, setRuntimes] = useState<RuntimeSpec[]>(fallbackRuntimes);
  const [language, setLanguage] = useState<CodeLanguage>("python");
  const [sourceCode, setSourceCode] = useState(fallbackRuntimes[0].template);
  const [stdin, setStdin] = useState("");
  const [result, setResult] = useState<CodeExecutionResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [status, setStatus] = useState<"ready" | "offline">("ready");

  useEffect(() => {
    fetchRuntimes()
      .then((items) => {
        setRuntimes(items);
        setSourceCode(items[0]?.template ?? fallbackRuntimes[0].template);
      })
      .catch(() => setStatus("offline"));
  }, []);

  const activeRuntime = useMemo(
    () => runtimes.find((runtime) => runtime.language === language) ?? fallbackRuntimes[0],
    [language, runtimes],
  );

  function selectLanguage(nextLanguage: CodeLanguage) {
    const runtime = runtimes.find((item) => item.language === nextLanguage) ?? fallbackRuntimes[0];
    setLanguage(nextLanguage);
    setSourceCode(runtime.template);
    setResult(null);
  }

  async function execute() {
    setIsRunning(true);
    setResult(null);
    try {
      setResult(await runCode(language, sourceCode, stdin));
    } catch {
      setResult({
        language,
        status: "client_error",
        stdout: "",
        stderr: "Unable to reach the code execution API.",
        exit_code: null,
        timed_out: false,
        bandit_issues: [],
      });
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <span className={styles.kicker}>Coding Round</span>
          <h1>Sandboxed code editor</h1>
        </div>
        <a className={styles.dashboardLink} href="/">Dashboard</a>
      </header>

      <section className={styles.toolbar}>
        <div className={styles.languageTabs} role="tablist" aria-label="Languages">
          {runtimes.map((runtime) => (
            <button
              aria-selected={runtime.language === language}
              key={runtime.language}
              onClick={() => selectLanguage(runtime.language)}
              type="button"
            >
              {runtime.label}
            </button>
          ))}
        </div>
        <div className={styles.runtimeMeta}>
          <span>{status === "ready" ? "API runtime" : "Preview runtime"}</span>
          <b>Network off</b>
          <b>CPU capped</b>
          <b>128 MB</b>
        </div>
      </section>

      <section className={styles.workspace}>
        <div className={styles.editorPane}>
          <Editor
            height="560px"
            language={activeRuntime.monaco_language}
            onChange={(value) => setSourceCode(value ?? "")}
            options={{
              fontSize: 14,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              padding: { top: 16 },
              wordWrap: "on",
            }}
            theme="vs-dark"
            value={sourceCode}
          />
        </div>

        <aside className={styles.sidePane}>
          <label className={styles.inputBlock}>
            <span>stdin</span>
            <textarea onChange={(event) => setStdin(event.target.value)} value={stdin} />
          </label>
          <button className={styles.runButton} disabled={isRunning} onClick={execute} type="button">
            {isRunning ? "Running..." : "Run in sandbox"}
          </button>
          <section className={styles.output}>
            <div className={styles.outputHeader}>
              <span>Result</span>
              <b data-status={result?.status ?? "idle"}>{result?.status ?? "idle"}</b>
            </div>
            <pre>{result?.stdout || result?.stderr || "Execution output will appear here."}</pre>
          </section>
          {!!result?.bandit_issues.length && (
            <section className={styles.issues}>
              <h2>Bandit findings</h2>
              {result.bandit_issues.map((issue) => (
                <article key={`${issue.test_id}-${issue.line_number}`}>
                  <strong>{issue.test_id}</strong>
                  <span>{issue.severity}</span>
                  <p>{issue.text}</p>
                </article>
              ))}
            </section>
          )}
        </aside>
      </section>
    </main>
  );
}
