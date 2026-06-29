import { apiClient } from "../api/client";

type ApiEnvelope<T> = { data: T };

export type InterviewMode = "topic" | "resume" | "mixed" | "behavioral" | "job_description";
export type Difficulty    = "easy" | "medium" | "hard";
export type Persona       = "service" | "product" | "startup";
export type PressureMode  = "practice" | "simulated";

export type StartInterviewPayload = {
  mode: InterviewMode;
  topic?: string;
  resume_text?: string;
  jd_text?: string;
  initial_difficulty?: Difficulty;
  persona?: Persona;
  pressure_mode?: PressureMode;
};

export type InterviewQuestion = {
  question: string;
  difficulty: Difficulty;
  topic?: string;
  expected_signals?: string[];
};

export type InterviewEvaluation = {
  score: number;
  feedback: string;
  strengths: string[];
  weaknesses: string[];
  what_went_well: string[];
  next_time_try: string;
  filler_count?: number;
  words_per_minute?: number | null;
};

export type StartInterviewResponse = {
  session_id: string;
  question: InterviewQuestion;
  persona: Persona;
  pressure_mode: PressureMode;
  is_warmup: boolean;
};

export type AnswerResult = {
  evaluation: InterviewEvaluation;
  next_question: InterviewQuestion;
  next_difficulty: Difficulty;
};

export type HintResult = {
  session_id: string;
  hint: string;
};

export type TopicBreakdown = {
  topic: string;
  average_score: number;
  questions_attempted: number;
  weak_area_count: number;
};

export type InterviewSummary = {
  session_id: string;
  overall_average_score: number;
  total_questions: number;
  topics: TopicBreakdown[];
  top_strengths: string[];
  top_weaknesses: string[];
  encouraging_message: string;
  score_delta: number | null;
};

export async function startInterview(payload: StartInterviewPayload): Promise<StartInterviewResponse> {
  const response = await apiClient.post<ApiEnvelope<StartInterviewResponse>>("/interviews/start", payload);
  return response.data.data;
}

export async function submitInterviewAnswer(session_id: string, answer: string, elapsed_seconds?: number): Promise<AnswerResult> {
  const response = await apiClient.post<ApiEnvelope<AnswerResult>>("/interviews/answer", { 
    session_id, 
    answer,
    elapsed_seconds
  });
  return response.data.data;
}

export async function endInterview(session_id: string): Promise<InterviewSummary> {
  const response = await apiClient.post<ApiEnvelope<InterviewSummary>>(`/interviews/${session_id}/end`);
  return response.data.data;
}

export async function requestHint(session_id: string, current_question: string): Promise<HintResult> {
  const response = await apiClient.post<ApiEnvelope<HintResult>>("/interviews/hint", {
    session_id,
    current_question,
  });
  return response.data.data;
}

export async function uploadResume(file: File): Promise<{ resume_text: string; char_count: number }> {
  const form = new FormData();
  form.append("file", file);
  const response = await apiClient.post<ApiEnvelope<{ resume_text: string; char_count: number }>>(
    "/interviews/upload-resume",
    form,
    // Do NOT set Content-Type manually — axios sets multipart/form-data with correct boundary
  );
  return response.data.data;
}
