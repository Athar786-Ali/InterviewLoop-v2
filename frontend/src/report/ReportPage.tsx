import { Download, FileSignature, RefreshCw, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";

import { downloadReport, generateReport, listReports, verifyReport, type ReportSummary, type ReportVerification } from "./api";
import styles from "./ReportPage.module.css";

const fallbackReports: ReportSummary[] = [
  { report_id: "preview-report", session_id: "demo-session", status: "signed", score: 8.1, signature_valid: true },
];

export function ReportPage() {
  const [reports, setReports] = useState<ReportSummary[]>(fallbackReports);
  const [sessionId, setSessionId] = useState("");
  const [verification, setVerification] = useState<ReportVerification | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "offline">("loading");

  async function refresh() {
    setStatus("loading");
    try {
      setReports(await listReports());
      setStatus("ready");
    } catch {
      setStatus("offline");
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function createReport() {
    const report = await generateReport(sessionId);
    setReports((current) => [report, ...current]);
    setSessionId("");
  }

  async function verify(reportId: string) {
    setVerification(await verifyReport(reportId));
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <span className={styles.kicker}>Reports</span>
          <h1>Signed interview evidence</h1>
        </div>
        <button className={styles.secondary} onClick={refresh} type="button">
          <RefreshCw aria-hidden="true" size={18} />
          {status === "loading" ? "Syncing..." : status === "ready" ? "Refresh" : "Preview data"}
        </button>
      </header>
      <section className={styles.panel}>
        <div className={styles.generate}>
          <input onChange={(event) => setSessionId(event.target.value)} placeholder="Session UUID" value={sessionId} />
          <button className={styles.primary} disabled={!sessionId} onClick={createReport} type="button">
            <FileSignature aria-hidden="true" size={18} />
            Generate report
          </button>
        </div>
        {verification && (
          <div className={styles.verify}>
            Signature: {verification.signature_valid ? "valid" : "invalid"} · Hash chain: {verification.hash_chain_valid ? "valid" : "invalid"}
          </div>
        )}
        <div className={styles.list}>
          {reports.map((report) => (
            <article className={styles.item} key={report.report_id}>
              <div>
                <strong>{report.report_id}</strong>
                <span>Session {report.session_id} · {report.status ?? "generated"} · score {report.score ?? "-"}</span>
              </div>
              <div className={styles.actions}>
                <button className={styles.secondary} onClick={() => verify(report.report_id)} type="button">
                  <ShieldCheck aria-hidden="true" size={18} />
                  Verify
                </button>
                <button className={styles.secondary} onClick={() => downloadReport(report.report_id, "json")} type="button">
                  <Download aria-hidden="true" size={18} />
                  JSON
                </button>
                <button className={styles.primary} onClick={() => downloadReport(report.report_id, "pdf")} type="button">
                  <Download aria-hidden="true" size={18} />
                  PDF
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
