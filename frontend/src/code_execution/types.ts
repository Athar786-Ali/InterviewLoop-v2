export type CodeLanguage = "python" | "cpp" | "java" | "javascript";

export type RuntimeSpec = {
  language: CodeLanguage;
  label: string;
  monaco_language: string;
  template: string;
};

export type BanditIssue = {
  test_id: string;
  severity: string;
  confidence: string;
  text: string;
  line_number: number | null;
};

export type CodeExecutionResult = {
  language: CodeLanguage;
  status: string;
  stdout: string;
  stderr: string;
  exit_code: number | null;
  timed_out: boolean;
  bandit_issues: BanditIssue[];
};

export type ApiResponse<T> = {
  success: boolean;
  data: T;
  message: string;
};
