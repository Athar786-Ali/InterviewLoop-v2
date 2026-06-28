import axios from "axios";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1",
  timeout: 15000,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("interviewloop.access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.error?.message ??
      error.response?.data?.message ??
      error.message ??
      "Something went wrong.";

    window.dispatchEvent(new CustomEvent("interviewloop:toast", { detail: { message, tone: "error" } }));

    if (error.response?.status === 401) {
      localStorage.removeItem("interviewloop.access_token");
      localStorage.removeItem("interviewloop.refresh_token");
      window.dispatchEvent(new Event("interviewloop:auth-change"));
    }

    return Promise.reject(error);
  },
);
