import { useCallback, useEffect, useRef, useState } from "react";

import type { ClientInterviewEvent, InterviewEvent, WebSocketStatus } from "./websocketTypes";

type Options = {
  sessionId: string | null;
  enabled?: boolean;
  maxReconnectAttempts?: number;
};

function wsBaseUrl() {
  const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
  return apiBase.replace(/^http/, "ws").replace(/\/api\/v1\/?$/, "/api/v1");
}

export function useInterviewEvents({ sessionId, enabled = true, maxReconnectAttempts = 5 }: Options) {
  const [events, setEvents] = useState<InterviewEvent[]>([]);
  const [status, setStatus] = useState<WebSocketStatus>("idle");
  const socketRef = useRef<WebSocket | null>(null);
  const lastSequenceRef = useRef(0);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<number | null>(null);

  const sendEvent = useCallback((event: ClientInterviewEvent) => {
    const socket = socketRef.current;
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ ...event, last_sequence: lastSequenceRef.current }));
      return true;
    }
    return false;
  }, []);

  useEffect(() => {
    if (!sessionId || !enabled) {
      return;
    }

    let closedByEffect = false;

    function connect() {
      setStatus(reconnectAttemptsRef.current > 0 ? "reconnecting" : "connecting");
      const url = `${wsBaseUrl()}/interviews/${sessionId}/events?last_sequence=${lastSequenceRef.current}`;
      const socket = new WebSocket(url);
      socketRef.current = socket;

      socket.onopen = () => {
        reconnectAttemptsRef.current = 0;
        setStatus("connected");
      };

      socket.onmessage = (message) => {
        const event = JSON.parse(message.data) as InterviewEvent;
        lastSequenceRef.current = Math.max(lastSequenceRef.current, event.sequence);
        setEvents((current) => [...current.slice(-99), event]);
        if (event.type === "heartbeat") {
          socket.send(JSON.stringify({ type: "ping", last_sequence: lastSequenceRef.current }));
        }
      };

      socket.onerror = () => {
        setStatus("error");
      };

      socket.onclose = () => {
        if (closedByEffect) {
          setStatus("closed");
          return;
        }
        if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setStatus("error");
          return;
        }
        reconnectAttemptsRef.current += 1;
        const delay = Math.min(1000 * reconnectAttemptsRef.current, 5000);
        reconnectTimerRef.current = window.setTimeout(connect, delay);
      };
    }

    connect();

    return () => {
      closedByEffect = true;
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current);
      }
      socketRef.current?.close(1000);
      socketRef.current = null;
    };
  }, [enabled, maxReconnectAttempts, sessionId]);

  const clearEvents = useCallback(() => setEvents([]), []);

  return {
    clearEvents,
    events,
    sendEvent,
    status,
  };
}
