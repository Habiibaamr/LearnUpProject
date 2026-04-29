import { api } from "./api";
import type { LoginResponse, UserMe } from "../types";

export async function login(email: string, password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>("/auth/login", { email, password });
  if (!data?.access_token) {
    throw new Error("Login succeeded but no token was returned.");
  }
  return data;
}

/** Pass accessToken right after login so /me does not rely on timing with localStorage + useEffect. */
export async function fetchMe(accessToken?: string): Promise<UserMe> {
  const config =
    accessToken != null && accessToken !== ""
      ? { headers: { Authorization: `Bearer ${accessToken}` } as const }
      : {};
  const { data } = await api.get<UserMe>("/auth/me", config);
  return data;
}
