import { useState } from "react";

import { useInterviewEvents } from "./useInterviewEvents";
import styles from "./LiveInterviewEvents.module.css";

export function LiveInterviewEvents({ initialSessionId = "demo-session", locked = false }: { initialSessionId?: string; locked?: boolean }) {
  const [sessionId, setSessionId] = useState(initialSessionId);
  const { events, sendEvent, status, clearEvents } = useInterviewEvents({ sessionId });

  return (
    <section className={styles.panel}>
      <div className={styles.header}>
        <div>
          <span>Live Events</span>
          <h2>Interview websocket stream</h2>
        </div>
        <b data-state={status}>{status}</b>
      </div>

      <div className={styles.controls}>
        <input disabled={locked} onChange={(event) => setSessionId(event.target.value)} value={sessionId} />
        <button onClick={() => sendEvent({ type: "question_started", payload: { source: "client" } })} type="button">
          Send event
        </button>
        <button onClick={clearEvents} type="button">Clear</button>
      </div>

      <div className={styles.events}>
        {events.map((event) => (
          <article key={`${event.sequence}-${event.type}`}>
            <strong>#{event.sequence} {event.type}</strong>
            <pre>{JSON.stringify(event.payload, null, 2)}</pre>
          </article>
        ))}
        {!events.length && <p>No events yet.</p>}
      </div>
    </section>
  );
}
