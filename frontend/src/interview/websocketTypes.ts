export type InterviewEventType =
  | "connected"
  | "reconnected"
  | "heartbeat"
  | "pong"
  | "question_started"
  | "transcript_partial"
  | "transcript_final"
  | "answer_submitted"
  | "evaluation_ready"
  | "error"
  | "session_cleanup";

export type InterviewEvent = {
  type: InterviewEventType;
  session_id: string;
  sequence: number;
  payload: Record<string, unknown>;
  timestamp: string;
};

export type ClientInterviewEvent = {
  type: string;
  payload?: Record<string, unknown>;
  last_sequence?: number;
};

export type WebSocketStatus = "idle" | "connecting" | "connected" | "reconnecting" | "closed" | "error";
