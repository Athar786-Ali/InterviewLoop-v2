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
  mfa_code?: string;
};

export type TotpSetup = {
  secret?: string;
  qr_code_uri?: string;
  qr_code_png_base64?: string;
  recovery_codes?: string[];
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

export async function setupTotp() {
  const response = await apiClient.post<ApiEnvelope<TotpSetup>>("/auth/mfa/totp/setup");
  return response.data.data;
}

export async function enableTotp(code: string) {
  const response = await apiClient.post<ApiEnvelope<{ enabled: boolean; recovery_codes?: string[] }>>("/auth/mfa/totp/enable", {
    code,
  });
  return response.data.data;
}

export async function disableTotp(code: string) {
  const response = await apiClient.post<ApiEnvelope<{ disabled: boolean }>>("/auth/mfa/totp/disable", { code });
  return response.data.data;
}

export async function enrollBiometric(images: string[]) {
  const response = await apiClient.post<ApiEnvelope<{ enrolled: boolean }>>("/auth/biometric/enroll", { images });
  return response.data.data;
}
