import { apiClient } from "../api/client";

type ApiEnvelope<T> = {
  data: T;
};

export type InterviewMode = "topic" | "resume" | "mixed";
export type Difficulty = "easy" | "medium" | "hard";

export type StartInterviewPayload = {
  mode: InterviewMode;
  topic?: string;
  resume_text?: string;
  difficulty?: Difficulty;
};

export type InterviewQuestion = {
  session_id: string;
  question_id?: string;
  question: string;
  difficulty: Difficulty;
  topic?: string;
};

export type AnswerResult = {
  score?: number;
  feedback?: string;
  next_question?: InterviewQuestion;
  completed?: boolean;
};

export async function startInterview(payload: StartInterviewPayload) {
  const response = await apiClient.post<ApiEnvelope<InterviewQuestion>>("/interviews/start", payload);
  return response.data.data;
}

export async function submitInterviewAnswer(session_id: string, answer: string) {
  const response = await apiClient.post<ApiEnvelope<AnswerResult>>("/interviews/answer", { session_id, answer });
  return response.data.data;
}
