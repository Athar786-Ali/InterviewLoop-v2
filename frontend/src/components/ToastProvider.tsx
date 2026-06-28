import { CheckCircle2, X } from "lucide-react";
import { createContext, type ReactNode, useCallback, useEffect, useMemo, useState } from "react";

import styles from "./ToastProvider.module.css";

type ToastTone = "success" | "error" | "info";

type Toast = {
  id: string;
  message: string;
  tone: ToastTone;
};

type ToastContextValue = {
  pushToast: (message: string, tone?: ToastTone) => void;
};

export const ToastContext = createContext<ToastContextValue>({ pushToast: () => undefined });

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const pushToast = useCallback((message: string, tone: ToastTone = "info") => {
    const id = crypto.randomUUID();
    setToasts((current) => [...current.slice(-2), { id, message, tone }]);
    window.setTimeout(() => dismiss(id), 4200);
  }, [dismiss]);

  useEffect(() => {
    function handleToast(event: Event) {
      const detail = (event as CustomEvent<{ message: string; tone?: ToastTone }>).detail;
      if (detail?.message) {
        pushToast(detail.message, detail.tone ?? "info");
      }
    }

    window.addEventListener("interviewloop:toast", handleToast);
    return () => window.removeEventListener("interviewloop:toast", handleToast);
  }, [pushToast]);

  const value = useMemo(() => ({ pushToast }), [pushToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div aria-live="polite" className={styles.stack}>
        {toasts.map((toast) => (
          <article className={styles.toast} data-tone={toast.tone} key={toast.id}>
            <CheckCircle2 aria-hidden="true" size={18} />
            <span>{toast.message}</span>
            <button aria-label="Dismiss notification" onClick={() => dismiss(toast.id)} type="button">
              <X aria-hidden="true" size={16} />
            </button>
          </article>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
