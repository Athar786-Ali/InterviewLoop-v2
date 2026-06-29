import { apiClient } from "../api/client";

type ApiEnvelope<T> = { data: T; message?: string };

export type CodeLanguage = "python" | "javascript" | "java" | "cpp";

export type TestCase = {
  input: string;
  expected_output: string;
  label: string;
};

export type CodingProblem = {
  id: string;
  title: string;
  difficulty: "easy" | "medium" | "hard";
  category: string;
  tags: string[];
  problem_statement: string;
  constraints: string[];
  examples: { input: string; output: string; explanation?: string }[];
  starter_code: Record<string, string>;
  test_cases: TestCase[];
};

export type TestCaseResult = {
  label: string;
  input: string;
  expected: string;
  actual: string;
  passed: boolean;
  runtime_ms: number | null;
};

export type SubmitResponse = {
  problem_id: string;
  language: string;
  passed: number;
  total: number;
  all_passed: boolean;
  results: TestCaseResult[];
  stderr: string;
  timed_out: boolean;
};

export async function fetchCodingProblems(filters?: {
  difficulty?: string;
  category?: string;
}): Promise<CodingProblem[]> {
  const params = new URLSearchParams();
  if (filters?.difficulty) params.set("difficulty", filters.difficulty);
  if (filters?.category) params.set("category", filters.category);
  const response = await apiClient.get<ApiEnvelope<CodingProblem[]>>(
    `/coding/problems?${params.toString()}`,
  );
  return response.data.data;
}

export async function fetchRandomProblem(filters?: {
  difficulty?: string;
  category?: string;
}): Promise<CodingProblem> {
  const params = new URLSearchParams();
  if (filters?.difficulty) params.set("difficulty", filters.difficulty);
  if (filters?.category) params.set("category", filters.category);
  const response = await apiClient.get<ApiEnvelope<CodingProblem>>(
    `/coding/question?${params.toString()}`,
  );
  return response.data.data;
}

export async function submitSolution(
  problem_id: string,
  language: CodeLanguage,
  source_code: string,
): Promise<SubmitResponse> {
  const response = await apiClient.post<ApiEnvelope<SubmitResponse>>("/coding/submit", {
    problem_id,
    language,
    source_code,
  });
  return response.data.data;
}
