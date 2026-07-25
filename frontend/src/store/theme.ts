/** Стор темы (тёмная/светлая/системная) с применением к <html>. */
import { create } from "zustand";

import type { Theme } from "@/types";

const STORAGE_KEY = "burmalda-theme";

interface ThemeState {
  theme: Theme;
  resolvedDark: boolean;
  setTheme: (t: Theme) => void;
  apply: () => void;
}

function systemDark(): boolean {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function resolveDark(theme: Theme): boolean {
  return theme === "dark" || (theme === "system" && systemDark());
}

function applyToDom(dark: boolean): void {
  const root = document.documentElement;
  root.classList.toggle("dark", dark);
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute("content", dark ? "#0f1115" : "#ffffff");
}

function initialTheme(): Theme {
  return (localStorage.getItem(STORAGE_KEY) as Theme) || "system";
}

const initial = initialTheme();

export const useThemeStore = create<ThemeState>((set, get) => ({
  theme: initial,
  resolvedDark: resolveDark(initial),
  setTheme: (t) => {
    localStorage.setItem(STORAGE_KEY, t);
    const dark = resolveDark(t);
    applyToDom(dark);
    set({ theme: t, resolvedDark: dark });
  },
  apply: () => {
    applyToDom(get().resolvedDark);
  },
}));

// Реакция на смену системной темы.
if (typeof window !== "undefined") {
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    const { theme, setTheme } = useThemeStore.getState();
    if (theme === "system") setTheme("system");
  });
}
