import { apiClient } from "../api/client";

type ApiEnvelope<T> = {
  data: T;
};

export type ReportSummary = {
  report_id: string;
  session_id: string;
  status?: string;
  score?: number;
  created_at?: string;
  signature_valid?: boolean;
};

export type ReportVerification = {
  report_id: string;
  signature_valid: boolean;
  hash_chain_valid: boolean;
};

export async function listReports() {
  const response = await apiClient.get<ApiEnvelope<ReportSummary[]>>("/reports");
  return response.data.data;
}

export async function generateReport(session_id: string) {
  const response = await apiClient.post<ApiEnvelope<ReportSummary>>("/reports", { session_id });
  return response.data.data;
}

export async function verifyReport(report_id: string) {
  const response = await apiClient.get<ApiEnvelope<ReportVerification>>(`/reports/${report_id}/verify`);
  return response.data.data;
}

export async function downloadReport(report_id: string, fileType: "json" | "pdf") {
  const response = await apiClient.get(`/reports/${report_id}/download/${fileType}`, { responseType: "blob" });
  const blob = new Blob([response.data]);
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `interview-report-${report_id}.${fileType}`;
  anchor.click();
  URL.revokeObjectURL(url);
}
