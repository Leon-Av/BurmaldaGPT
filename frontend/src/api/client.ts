/** Базовый HTTP-клиент с JWT. */
import type { User } from "@/types";

const TOKEN_KEY = "burmalda-token";
const USER_KEY = "burmalda-user";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuth(token: string, user: User): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getStoredUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const resp = await fetch(`/api${path}`, { ...options, headers });

  if (resp.status === 401) {
    clearAuth();
  }

  if (!resp.ok) {
    let message = `Ошибка ${resp.status}`;
    try {
      const data = await resp.json();
      message = data.detail || data.message || message;
    } catch {
      /* не JSON */
    }
    throw new ApiError(resp.status, message);
  }

  if (resp.status === 204) return undefined as T;
  return resp.json() as Promise<T>;
}

export { request };
