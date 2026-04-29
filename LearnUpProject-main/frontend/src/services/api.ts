import axios, { AxiosError } from "axios";

/**
 * Base URL for FastAPI:
 * - Development (recommended): set VITE_API_URL=/api in .env and run Vite dev server (proxy forwards to port 8000)
 * - Direct: VITE_API_URL=http://127.0.0.1:8000
 */
export const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

/** Must match AuthContext localStorage key for JWT */
export const LEARNUP_TOKEN_KEY = "learnup_token";

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(LEARNUP_TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function getApiErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const ax = err as AxiosError<{
      detail?: string | { message?: string } | Array<{ msg?: string; loc?: unknown }>;
    }>;
    const d = ax.response?.data?.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d))
      return d.map((x) => (typeof x === "object" && x && "msg" in x ? String(x.msg) : JSON.stringify(x))).join("; ");
    if (d && typeof d === "object" && "message" in d && typeof d.message === "string")
      return d.message;
    return ax.message || "Request failed";
  }
  return "Something went wrong";
}
