import { Loader2 } from "lucide-react";
import { Link } from "react-router-dom";

import styles from "./RouteFallback.module.css";

export function RouteLoader() {
  return (
    <main className={styles.page}>
      <section className={styles.panel}>
        <Loader2 aria-hidden="true" className={styles.spin} size={24} />
        <span>Loading workspace</span>
      </section>
    </main>
  );
}

export function NotFoundPage() {
  return (
    <main className={styles.page}>
      <section className={styles.panel}>
        <strong>404</strong>
        <h1>Page not found</h1>
        <p>The route does not exist in this workspace.</p>
        <Link to="/">Return to dashboard</Link>
      </section>
    </main>
  );
}
