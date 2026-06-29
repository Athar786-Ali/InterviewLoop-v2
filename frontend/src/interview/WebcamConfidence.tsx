import { Camera, CameraOff, ChevronDown, ChevronUp, Loader2, Maximize2, Minimize2, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import styles from "./WebcamConfidence.module.css";

type ExpressionKey = "neutral" | "happy" | "sad" | "angry" | "fearful" | "disgusted" | "surprised";

const EXPRESSION_TO_CONFIDENCE: Record<ExpressionKey, number> = {
  happy:      90,
  neutral:    75,
  surprised:  60,
  fearful:    35,
  disgusted:  30,
  sad:        25,
  angry:      20,
};

const EXPRESSION_LABEL: Record<ExpressionKey, string> = {
  happy:      "😊 Confident",
  neutral:    "😐 Composed",
  surprised:  "😮 Alert",
  fearful:    "😰 Nervous",
  disgusted:  "😒 Unsure",
  sad:        "😟 Stressed",
  angry:      "😠 Tense",
};

type ConfidencePoint = { time: number; score: number };

declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    faceapi: any;
  }
}

function loadFaceApi(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (window.faceapi) { resolve(); return; }
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js";
    script.onload = () => resolve();
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

export function WebcamConfidence() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<number>(0);

  const [state, setState] = useState<"idle" | "loading" | "running" | "error">("idle");
  const [consent, setConsent] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const [confidence, setConfidence] = useState<number | null>(null);
  const [expression, setExpression] = useState<ExpressionKey | null>(null);
  const [history, setHistory] = useState<ConfidencePoint[]>([]);
  const [avgConfidence, setAvgConfidence] = useState<number | null>(null);
  const [modelLoaded, setModelLoaded] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearInterval(intervalRef.current);
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  const startWebcam = useCallback(async () => {
    setState("loading");
    try {
      // Load face-api.js from CDN
      await loadFaceApi();
      const faceapi = window.faceapi;

      // Load models from CDN
      if (!modelLoaded) {
        const MODEL_URL = "https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/weights";
        await Promise.all([
          faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
          faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL),
        ]);
        setModelLoaded(true);
      }

      // Get webcam
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240 } });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      setState("running");

      // Detect every 2 seconds
      intervalRef.current = window.setInterval(async () => {
        if (!videoRef.current || !window.faceapi) return;
        try {
          const detection = await faceapi
            .detectSingleFace(videoRef.current, new faceapi.TinyFaceDetectorOptions())
            .withFaceExpressions();

          if (detection?.expressions) {
            const exprs = detection.expressions as Record<string, number>;
            const topExpr = Object.entries(exprs).sort((a, b) => b[1] - a[1])[0];
            const key = topExpr[0] as ExpressionKey;
            const score = EXPRESSION_TO_CONFIDENCE[key] ?? 50;
            setExpression(key);
            setConfidence(score);
            setHistory((prev) => {
              const next = [...prev, { time: Date.now(), score }].slice(-20);
              const avg = Math.round(next.reduce((a, b) => a + b.score, 0) / next.length);
              setAvgConfidence(avg);
              return next;
            });
          }
        } catch { /* detection failed for this frame, skip */ }
      }, 2000);

    } catch (err) {
      console.error("Webcam error:", err);
      setState("error");
    }
  }, [modelLoaded]);

  const stopWebcam = useCallback(() => {
    clearInterval(intervalRef.current);
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setState("idle");
    setConfidence(null);
    setExpression(null);
  }, []);

  if (dismissed) return null;

  return (
    <div className={`${styles.pip} ${minimized ? styles.pipMinimized : ""}`}>
      {/* ── Header ── */}
      <div className={styles.header}>
        <span className={styles.headerTitle}>
          <Camera size={12} /> Confidence Monitor
        </span>
        <div className={styles.headerActions}>
          <button
            className={styles.iconBtn}
            onClick={() => setMinimized((m) => !m)}
            title={minimized ? "Expand" : "Minimize"}
            type="button"
          >
            {minimized ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
          <button className={styles.iconBtn} onClick={() => { stopWebcam(); setDismissed(true); }} title="Close" type="button">
            <X size={12} />
          </button>
        </div>
      </div>

      {!minimized && (
        <>
          {/* ── Consent gate ── */}
          {!consent && state === "idle" && (
            <div className={styles.consent}>
              <Camera className={styles.consentIcon} size={28} />
              <p className={styles.consentText}>
                Enable webcam to monitor your confidence level during the interview.
              </p>
              <p className={styles.consentNote}>
                🔒 All processing is 100% local in your browser. No video data is sent to any server.
              </p>
              <button
                className={styles.enableBtn}
                onClick={() => { setConsent(true); startWebcam(); }}
                type="button"
              >
                Enable Camera
              </button>
            </div>
          )}

          {/* ── Loading state ── */}
          {state === "loading" && (
            <div className={styles.loadingState}>
              <Loader2 className={styles.spin} size={22} />
              <span>Loading face detection model…</span>
            </div>
          )}

          {/* ── Error state ── */}
          {state === "error" && (
            <div className={styles.errorState}>
              <CameraOff size={22} />
              <span>Camera access denied or unavailable.</span>
              <button className={styles.retryBtn} onClick={startWebcam} type="button">Retry</button>
            </div>
          )}

          {/* ── Running: video + confidence ── */}
          {state === "running" && (
            <div className={styles.videoWrap}>
              <video
                autoPlay
                className={styles.video}
                muted
                playsInline
                ref={videoRef}
              />
              <canvas className={styles.overlay} ref={canvasRef} />

              {/* Score overlay */}
              {confidence !== null && expression !== null && (
                <div className={styles.scoreOverlay}>
                  <div
                    className={styles.scoreCircle}
                    style={{
                      background: `conic-gradient(${
                        confidence > 65 ? "var(--accent-green)" :
                        confidence > 40 ? "var(--accent-amber)" : "var(--accent-red)"
                      } ${confidence}%, var(--bg-elevated) 0%)`,
                    }}
                  >
                    <span className={styles.scoreNumber}>{confidence}%</span>
                  </div>
                  <span className={styles.expressionLabel}>{EXPRESSION_LABEL[expression]}</span>
                </div>
              )}
            </div>
          )}

          {/* ── Mini confidence chart ── */}
          {history.length > 1 && state === "running" && (
            <div className={styles.chartWrap}>
              <div className={styles.chartLabel}>
                Session avg: <strong>{avgConfidence}%</strong>
              </div>
              <div className={styles.miniChart}>
                {history.map((point, i) => (
                  <div
                    className={styles.bar}
                    key={i}
                    style={{
                      height: `${point.score}%`,
                      background: point.score > 65
                        ? "var(--accent-green)"
                        : point.score > 40
                        ? "var(--accent-amber)"
                        : "var(--accent-red)",
                    }}
                    title={`${point.score}%`}
                  />
                ))}
              </div>
            </div>
          )}

          {/* ── Stop button ── */}
          {state === "running" && (
            <button className={styles.stopBtn} onClick={stopWebcam} type="button">
              <CameraOff size={12} /> Stop camera
            </button>
          )}
        </>
      )}
    </div>
  );
}
