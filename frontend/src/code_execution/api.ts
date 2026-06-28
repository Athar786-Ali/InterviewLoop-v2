import { apiClient } from "../api/client";
import type { ApiResponse, CodeExecutionResult, CodeLanguage, RuntimeSpec } from "./types";

export async function fetchRuntimes(): Promise<RuntimeSpec[]> {
  const response = await apiClient.get<ApiResponse<RuntimeSpec[]>>("/code-execution/runtimes");
  return response.data.data;
}

export async function runCode(language: CodeLanguage, sourceCode: string, stdin: string): Promise<CodeExecutionResult> {
  const response = await apiClient.post<ApiResponse<CodeExecutionResult>>("/code-execution/run", {
    language,
    source_code: sourceCode,
    stdin,
  });
  return response.data.data;
}
