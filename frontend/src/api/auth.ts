/** Auth API. */
import type { User } from "@/types";
import { request } from "./client";

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export async function register(
  username: string,
  password: string,
  displayName?: string
): Promise<AuthResponse> {
  return request<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({
      username,
      password,
      display_name: displayName || undefined,
    }),
  });
}

export async function login(
  username: string,
  password: string
): Promise<AuthResponse> {
  return request<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function fetchMe(): Promise<User> {
  return request<User>("/auth/me");
}

export async function updateMe(payload: Partial<Pick<User, "theme" | "display_name">>): Promise<User> {
  return request<User>("/auth/me", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}
