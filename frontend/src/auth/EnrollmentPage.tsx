import { Fingerprint, KeyRound, QrCode } from "lucide-react";
import { useState } from "react";

import { disableTotp, enableTotp, enrollBiometric, setupTotp, type TotpSetup } from "./api";
import styles from "./AuthPages.module.css";

export function EnrollmentPage() {
  const [samples, setSamples] = useState(["", "", "", "", ""]);
  const [totp, setTotp] = useState<TotpSetup | null>(null);
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("");

  async function submitBiometric() {
    await enrollBiometric(samples.filter(Boolean));
    setMessage("Biometric enrollment submitted.");
  }

  async function startTotp() {
    setTotp(await setupTotp());
  }

  async function submitEnable() {
    const result = await enableTotp(code);
    setMessage(result.recovery_codes?.length ? "TOTP enabled. Save your recovery codes." : "TOTP enabled.");
    setTotp((current) => ({ ...current, recovery_codes: result.recovery_codes ?? current?.recovery_codes }));
  }

  async function submitDisable() {
    await disableTotp(code);
    setMessage("TOTP disabled.");
  }

  return (
    <main className={styles.page}>
      <section className={styles.card}>
        <div className={styles.form}>
          <h2>Security enrollment</h2>
          <p className={styles.status}>Enroll face embeddings and Google Authenticator compatible TOTP before high-trust interview sessions.</p>
          <div className={styles.samples}>
            {samples.map((sample, index) => (
              <label className={styles.field} key={index}>
                <span>Face sample {index + 1}</span>
                <textarea onChange={(event) => setSamples((current) => current.map((item, itemIndex) => (itemIndex === index ? event.target.value : item)))} placeholder="Paste base64 captured image payload" value={sample} />
              </label>
            ))}
          </div>
          <div className={styles.row}>
            <button className={styles.primary} onClick={submitBiometric} type="button">
              <Fingerprint aria-hidden="true" size={18} />
              Enroll face
            </button>
            <button className={styles.secondary} onClick={startTotp} type="button">
              <QrCode aria-hidden="true" size={18} />
              Setup TOTP
            </button>
          </div>
          {totp?.qr_code_png_base64 && <img alt="TOTP QR code" className={styles.qr} src={`data:image/png;base64,${totp.qr_code_png_base64}`} />}
          {totp?.qr_code_uri && <p className={styles.status}>{totp.qr_code_uri}</p>}
          <label className={styles.field}>
            <span>Authenticator code</span>
            <input inputMode="numeric" onChange={(event) => setCode(event.target.value)} value={code} />
          </label>
          <div className={styles.row}>
            <button className={styles.primary} onClick={submitEnable} type="button">
              <KeyRound aria-hidden="true" size={18} />
              Enable TOTP
            </button>
            <button className={styles.secondary} onClick={submitDisable} type="button">Disable TOTP</button>
          </div>
          {!!totp?.recovery_codes?.length && (
            <div className={styles.codes}>
              {totp.recovery_codes.map((item) => <code key={item}>{item}</code>)}
            </div>
          )}
          {message && <p className={styles.status}>{message}</p>}
        </div>
      </section>
    </main>
  );
}
