import { apiClient } from "../api/client";
import type { TokenPair } from "./authStore";

type ApiEnvelope<T> = {
  data: T;
  message?: string;
};

export type SignupPayload = {
  email: string;
  full_name: string;
  password: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export async function signup(payload: SignupPayload) {
  const response = await apiClient.post<ApiEnvelope<{ user_id: string; email: string }>>("/auth/signup", payload);
  return response.data.data;
}

export async function verifyEmail(email: string, otp: string) {
  const response = await apiClient.post<ApiEnvelope<{ verified: boolean }>>("/auth/verify-email", { email, otp });
  return response.data.data;
}

export async function login(payload: LoginPayload) {
  const response = await apiClient.post<ApiEnvelope<TokenPair>>("/auth/login", payload);
  return response.data.data;
}

export async function logout() {
  await apiClient.post("/auth/logout");
}

export async function requestPasswordReset(email: string) {
  const response = await apiClient.post<ApiEnvelope<{ sent: boolean }>>("/auth/forgot-password", { email });
  return response.data.data;
}

export async function resetPassword(email: string, otp: string, new_password: string) {
  const response = await apiClient.post<ApiEnvelope<{ reset: boolean }>>("/auth/reset-password", {
    email,
    otp,
    new_password,
  });
  return response.data.data;
}
