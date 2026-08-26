import { apiFetch } from "./client";
import type { CurrentUser, TokenResponse } from "@/types/api";

export function login(email: string, password: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: { email, password },
  });
}

export function getMe(signal?: AbortSignal): Promise<CurrentUser> {
  return apiFetch<CurrentUser>("/auth/me", { signal });
}
