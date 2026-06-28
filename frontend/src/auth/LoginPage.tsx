import { KeyRound, LogIn, Mail } from "lucide-react";
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
  const [mfaCode, setMfaCode] = useState("");
  const [resetCode, setResetCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [status, setStatus] = useState("");
  const [isSubmitting, setSubmitting] = useState(false);
  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? "/";

  async function handleLogin(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    try {
      const tokens = await login({ email, password, mfa_code: mfaCode || undefined });
      setTokens(tokens);
      navigate(from, { replace: true });
    } finally {
      setSubmitting(false);
    }
  }

  async function sendReset() {
    await requestPasswordReset(email);
    setStatus("Password reset OTP sent when the account is eligible.");
  }

  async function completeReset() {
    await resetPassword(email, resetCode, newPassword);
    setStatus("Password reset complete. Sign in with the new password.");
  }

  return (
    <main className={styles.page}>
      <section className={`${styles.card} ${styles.split}`}>
        <aside className={styles.intro}>
          <span>InterviewLoop-v2</span>
          <h1>Practice loop, score loop, improve loop.</h1>
          <p>Secure interview sessions with MFA, live events, analytics, reports, and coding rounds in one production workspace.</p>
        </aside>
        <form className={styles.form} onSubmit={handleLogin}>
          <h2>Sign in</h2>
          <label className={styles.field}>
            <span>Email</span>
            <input autoComplete="email" onChange={(event) => setEmail(event.target.value)} required type="email" value={email} />
          </label>
          <label className={styles.field}>
            <span>Password</span>
            <input autoComplete="current-password" onChange={(event) => setPassword(event.target.value)} required type="password" value={password} />
          </label>
          <label className={styles.field}>
            <span>MFA code</span>
            <input inputMode="numeric" onChange={(event) => setMfaCode(event.target.value)} placeholder="Optional unless enabled" value={mfaCode} />
          </label>
          <button className={styles.primary} disabled={isSubmitting} type="submit">
            <LogIn aria-hidden="true" size={18} />
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
          <div className={styles.row}>
            <button className={styles.secondary} onClick={sendReset} type="button">
              <Mail aria-hidden="true" size={18} />
              Send reset OTP
            </button>
            <Link className={styles.link} to="/signup">Create account</Link>
          </div>
          <div className={styles.row}>
            <input aria-label="Reset OTP" onChange={(event) => setResetCode(event.target.value)} placeholder="Reset OTP" value={resetCode} />
            <input aria-label="New password" onChange={(event) => setNewPassword(event.target.value)} placeholder="New password" type="password" value={newPassword} />
            <button className={styles.secondary} onClick={completeReset} type="button">
              <KeyRound aria-hidden="true" size={18} />
              Reset
            </button>
          </div>
          {status && <p className={styles.status}>{status}</p>}
        </form>
      </section>
    </main>
  );
}
