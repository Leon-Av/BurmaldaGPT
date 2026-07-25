/** Стор аутентификации. */
import { create } from "zustand";

import * as authApi from "@/api/auth";
import { clearAuth, getStoredUser, setAuth } from "@/api/client";
import type { Theme, User } from "@/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
  init: () => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, displayName?: string) => Promise<void>;
  logout: () => void;
  patchUser: (patch: Partial<User>) => void;
  setTheme: (theme: Theme) => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: getStoredUser(),
  loading: false,
  error: null,

  init: async () => {
    // Восстанавливаем пользователя по токену.
    const stored = getStoredUser();
    if (!stored) return;
    set({ loading: true });
    try {
      const me = await authApi.fetchMe();
      set({ user: me, loading: false });
    } catch {
      clearAuth();
      set({ user: null, loading: false });
    }
  },

  login: async (username, password) => {
    set({ loading: true, error: null });
    try {
      const { access_token, user } = await authApi.login(username, password);
      setAuth(access_token, user);
      set({ user, loading: false });
    } catch (e) {
      set({ loading: false, error: (e as Error).message });
      throw e;
    }
  },

  register: async (username, password, displayName) => {
    set({ loading: true, error: null });
    try {
      const { access_token, user } = await authApi.register(username, password, displayName);
      setAuth(access_token, user);
      set({ user, loading: false });
    } catch (e) {
      set({ loading: false, error: (e as Error).message });
      throw e;
    }
  },

  logout: () => {
    clearAuth();
    set({ user: null });
  },

  patchUser: (patch) => {
    const current = get().user;
    if (!current) return;
    const updated = { ...current, ...patch };
    setAuth(getTokenSafe(), updated);
    set({ user: updated });
  },

  setTheme: async (theme) => {
    get().patchUser({ theme });
    try {
      await authApi.updateMe({ theme });
    } catch {
      /* некритично */
    }
  },
}));

function getTokenSafe(): string {
  return localStorage.getItem("burmalda-token") || "";
}
