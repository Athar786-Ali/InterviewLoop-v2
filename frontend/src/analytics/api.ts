import { apiClient } from "../api/client";
import type { AnalyticsDashboard, ApiResponse } from "./types";

export async function fetchAnalyticsDashboard(): Promise<AnalyticsDashboard> {
  const response = await apiClient.get<ApiResponse<AnalyticsDashboard>>("/analytics/dashboard");
  return response.data.data;
}
