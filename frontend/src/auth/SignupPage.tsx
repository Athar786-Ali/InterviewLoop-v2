import { Mail, ShieldCheck, UserPlus } from "lucide-react";
import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { signup, verifyEmail } from "./api";
import styles from "./AuthPages.module.css";

export function SignupPage() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [isOtpReady, setOtpReady] = useState(false);
  const [isSubmitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSignup(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await signup({ full_name: fullName, email, password });
      setOtpReady(true);
    } catch {
      setError("Could not create account. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleVerify() {
    setSubmitting(true);
    setError("");
    try {
      await verifyEmail(email, otp);
      navigate("/login", { replace: true });
    } catch {
      setError("Invalid OTP. Check your email and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className={styles.page}>
      <section className={`${styles.card} ${styles.split}`}>
        {/* ── Brand hero ── */}
        <aside className={styles.intro}>
          <span className={styles.introKicker}>Join InterviewLoop</span>
          <h1>Start your interview prep journey.</h1>
          <p>
            Create a free account and get instant access to AI-powered mock interviews with
            adaptive difficulty, Socratic hints, and coaching-grade feedback.
          </p>
          <div className={styles.featurePills}>
            {[
              { emoji: "🧠", label: "AI personas: FAANG, Service Co., Startup" },
              { emoji: "📄", label: "Resume-aware questions from your experience" },
              { emoji: "📊", label: "Performance analytics with topic radar" },
              { emoji: "🔒", label: "Signed, verifiable interview reports" },
            ].map(({ emoji, label }) => (
              <div className={styles.featurePill} key={label}>
                <span className={styles.featurePillIcon}>{emoji}</span>
                <span className={styles.featurePillText}>{label}</span>
              </div>
            ))}
          </div>
        </aside>

        {/* ── Signup form ── */}
        <form className={styles.form} onSubmit={handleSignup}>
          <div>
            <h2 className={styles.formTitle}>Create account</h2>
            <p className={styles.formSubtitle}>Free forever. No credit card required.</p>
          </div>

          <label className={styles.field}>
            <span className={styles.fieldLabel}>Full name</span>
            <input
              autoComplete="name"
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Jane Smith"
              required
              value={fullName}
            />
          </label>

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
              autoComplete="new-password"
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              type="password"
              value={password}
            />
          </label>

          {!isOtpReady ? (
            <button className={styles.primary} disabled={isSubmitting} id="signup-submit" type="submit">
              <UserPlus aria-hidden="true" size={16} />
              {isSubmitting ? "Creating account…" : "Create account"}
            </button>
          ) : (
            <>
              <p className={styles.status}>
                <Mail size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "middle" }} />
                Check your inbox — we sent a 6-digit verification code.
              </p>
              <label className={styles.field}>
                <span className={styles.fieldLabel}>Verification code</span>
                <input
                  autoComplete="one-time-code"
                  inputMode="numeric"
                  maxLength={6}
                  onChange={(e) => setOtp(e.target.value)}
                  placeholder="123456"
                  value={otp}
                />
              </label>
              <button
                className={styles.primary}
                disabled={isSubmitting || otp.length < 6}
                id="verify-email"
                onClick={handleVerify}
                type="button"
              >
                <ShieldCheck aria-hidden="true" size={16} />
                {isSubmitting ? "Verifying…" : "Verify email"}
              </button>
            </>
          )}

          <Link className={styles.link} to="/login">Already have an account? Sign in →</Link>

          {error && <p className={styles.error}>{error}</p>}
        </form>
      </section>
    </main>
  );
}
