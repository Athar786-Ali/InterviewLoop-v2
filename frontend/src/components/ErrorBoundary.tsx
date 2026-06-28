import { AlertTriangle, RotateCcw } from "lucide-react";
import { Component, type ErrorInfo, type ReactNode } from "react";

import styles from "./ErrorBoundary.module.css";

type State = {
  hasError: boolean;
};

export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Frontend boundary captured an error", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className={styles.page}>
          <section className={styles.panel}>
            <AlertTriangle aria-hidden="true" size={34} />
            <h1>Something interrupted the workspace</h1>
            <p>The app state can be recovered with a refresh. Your server data is not changed by this screen.</p>
            <button onClick={() => window.location.reload()} type="button">
              <RotateCcw aria-hidden="true" size={18} />
              Reload app
            </button>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}
