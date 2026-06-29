import { BrainCircuit, KeyRound, LogIn, Mail, Mic, Sparkles, Zap } from "lucide-react";
import { type FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { login, requestPasswordReset, resetPassword } from "./api";
import { setTokens } from "./authStore";
import styles from "./AuthPages.module.css";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [resetCode, setResetCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setSubmitting] = useState(false);
  const [showReset, setShowReset] = useState(false);
  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? "/";

  async function handleLogin(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const tokens = await login({ email, password });
      setTokens(tokens);
      navigate(from, { replace: true });
    } catch {
      setError("Invalid email or password. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  async function sendReset() {
    setError("");
    try {
      await requestPasswordReset(email);
      setStatus("If that account exists, a reset OTP has been sent.");
      setShowReset(true);
    } catch {
      setError("Could not send reset email. Try again shortly.");
    }
  }

  async function completeReset() {
    setError("");
    try {
      await resetPassword(email, resetCode, newPassword);
      setStatus("Password reset complete. Sign in with your new password.");
      setShowReset(false);
    } catch {
      setError("Reset failed. Check your OTP and try again.");
    }
  }

  return (
    <main className={styles.page}>
      <section className={`${styles.card} ${styles.split}`}>
        {/* ── Brand hero ── */}
        <aside className={styles.intro}>
          <span className={styles.introKicker}>InterviewLoop</span>
          <h1>Practice loop,<br />score loop,<br />improve loop.</h1>
          <p>AI-powered mock interviews with adaptive difficulty, Socratic hints, and coaching feedback — built for serious students.</p>

          <div className={styles.featurePills}>
            {[
              { icon: BrainCircuit, label: "3 AI Personas: FAANG, Service, Startup" },
              { icon: Sparkles, label: "Socratic hints that guide, not spoil" },
              { icon: Zap, label: "Adaptive difficulty using sliding window" },
              { icon: Mic, label: "Voice-first with typed fallback" },
            ].map(({ icon: Icon, label }) => (
              <div className={styles.featurePill} key={label}>
                <span className={styles.featurePillIcon}>
                  <Icon size={14} />
                </span>
                <span className={styles.featurePillText}>{label}</span>
              </div>
            ))}
          </div>
        </aside>

        {/* ── Login form ── */}
        <form className={styles.form} onSubmit={handleLogin}>
          <div>
            <h2 className={styles.formTitle}>Sign in</h2>
            <p className={styles.formSubtitle}>Welcome back — let's continue your loop.</p>
          </div>

          <label className={styles.field}>
            <span className={styles.fieldLabel}>Email address</span>
            <input
              autoComplete="email"
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              type="email"
              value={email}
            />
          </label>

          <label className={styles.field}>
            <span className={styles.fieldLabel}>Password</span>
            <input
              autoComplete="current-password"
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              type="password"
              value={password}
            />
          </label>

          <button className={styles.primary} disabled={isSubmitting} id="login-submit" type="submit">
            <LogIn aria-hidden="true" size={16} />
            {isSubmitting ? "Signing in…" : "Sign in"}
          </button>

          <div className={styles.row}>
            <button className={styles.secondary} id="send-reset" onClick={sendReset} type="button">
              <Mail aria-hidden="true" size={15} />
              Forgot password
            </button>
            <Link className={styles.link} to="/signup">Create account →</Link>
          </div>

          {showReset && (
            <div className={styles.field}>
              <span className={styles.fieldLabel}>Reset OTP</span>
              <input
                aria-label="Reset OTP"
                onChange={(e) => setResetCode(e.target.value)}
                placeholder="6-digit OTP from email"
                value={resetCode}
              />
              <input
                aria-label="New password"
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="New password"
                type="password"
                value={newPassword}
              />
              <button className={styles.secondary} onClick={completeReset} type="button">
                <KeyRound aria-hidden="true" size={15} />
                Reset password
              </button>
            </div>
          )}

          {status && <p className={styles.status}>{status}</p>}
          {error && <p className={styles.error}>{error}</p>}
        </form>
      </section>
    </main>
  );
}
