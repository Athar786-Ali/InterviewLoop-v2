import { ShieldCheck, UserPlus } from "lucide-react";
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

  async function handleSignup(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    try {
      await signup({ full_name: fullName, email, password });
      setOtpReady(true);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleVerify() {
    setSubmitting(true);
    try {
      await verifyEmail(email, otp);
      navigate("/login", { replace: true });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className={styles.page}>
      <section className={`${styles.card} ${styles.split}`}>
        <aside className={styles.intro}>
          <span>Secure onboarding</span>
          <h1>Start with email verification.</h1>
          <p>Signup keeps identity, sessions, refresh tokens, and MFA ready for the interview workflow.</p>
        </aside>
        <form className={styles.form} onSubmit={handleSignup}>
          <h2>Create account</h2>
          <label className={styles.field}>
            <span>Full name</span>
            <input autoComplete="name" onChange={(event) => setFullName(event.target.value)} required value={fullName} />
          </label>
          <label className={styles.field}>
            <span>Email</span>
            <input autoComplete="email" onChange={(event) => setEmail(event.target.value)} required type="email" value={email} />
          </label>
          <label className={styles.field}>
            <span>Password</span>
            <input autoComplete="new-password" onChange={(event) => setPassword(event.target.value)} required type="password" value={password} />
          </label>
          <button className={styles.primary} disabled={isSubmitting} type="submit">
            <UserPlus aria-hidden="true" size={18} />
            {isSubmitting ? "Creating..." : "Create account"}
          </button>
          {isOtpReady && (
            <>
              <label className={styles.field}>
                <span>Email OTP</span>
                <input inputMode="numeric" onChange={(event) => setOtp(event.target.value)} value={otp} />
              </label>
              <button className={styles.secondary} disabled={isSubmitting} onClick={handleVerify} type="button">
                <ShieldCheck aria-hidden="true" size={18} />
                Verify email
              </button>
            </>
          )}
          <Link className={styles.link} to="/login">Already have an account?</Link>
        </form>
      </section>
    </main>
  );
}
