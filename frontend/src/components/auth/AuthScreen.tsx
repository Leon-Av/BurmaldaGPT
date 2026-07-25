/** Экран входа / регистрации. */
import { motion } from "framer-motion";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { useState } from "react";

import { ApiError } from "@/api/client";
import { useAuthStore } from "@/store/auth";
import { useThemeStore } from "@/store/theme";

import { Logo } from "@/components/ui/Logo";
import { Sun, Moon, Monitor } from "lucide-react";
import type { Theme } from "@/types";

type Mode = "login" | "register";

export function AuthScreen() {
  const [mode, setMode] = useState<Mode>("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const { login, register, loading } = useAuthStore();
  const { theme, setTheme } = useThemeStore();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    try {
      if (mode === "login") {
        await login(username.trim(), password);
      } else {
        await register(username.trim(), password, displayName.trim() || undefined);
      }
    } catch (err) {
      setLocalError(err instanceof ApiError ? err.message : "Что-то пошло не так");
    }
  };

  const switchMode = (m: Mode) => {
    setMode(m);
    setLocalError(null);
  };

  const themeIcon = { light: <Sun size={16} />, dark: <Moon size={16} />, system: <Monitor size={16} /> };
  const cycleTheme = () => {
    const order: Theme[] = ["light", "dark", "system"];
    const i = order.indexOf(theme);
    setTheme(order[(i + 1) % order.length]);
  };

  return (
    <div className="min-h-screen flex flex-col bg-app relative overflow-hidden">
      {/* Декоративный фон — перекрывающиеся круги как на логотипе */}
      <div className="pointer-events-none absolute inset-0 opacity-[0.5]">
        <div className="absolute -top-32 -right-32 w-[480px] h-[480px] rounded-full bg-brand-400/15 blur-3xl" />
        <div className="absolute -bottom-40 -left-32 w-[420px] h-[420px] rounded-full bg-brand-300/10 blur-3xl" />
      </div>

      {/* Переключатель темы в углу */}
      <button
        onClick={cycleTheme}
        className="absolute top-5 right-5 z-10 h-10 w-10 rounded-xl border border-app bg-elevated/80 backdrop-blur flex items-center justify-center text-muted hover:text-main transition-colors shadow-soft"
        title={`Тема: ${theme}`}
      >
        {themeIcon[theme]}
      </button>

      <div className="flex-1 flex items-center justify-center p-6 relative z-[1]">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          className="w-full max-w-[400px]"
        >
          <div className="flex flex-col items-center mb-8">
            <Logo size={56} animated showText={false} />
            <h1 className="mt-5 text-2xl font-bold text-main tracking-tight">
              <span className="font-extrabold">Бурмалда</span>
              <span className="font-semibold text-muted">GPT</span>
            </h1>
            <p className="mt-2 text-sm text-muted text-center">
              Чат-ассистент, говорящий на бурмалде
            </p>
          </div>

          <div className="bg-elevated rounded-2xl border border-app shadow-float p-6">
            {/* Переключатель режима */}
            <div className="grid grid-cols-2 gap-1 p-1 bg-soft rounded-xl mb-6">
              {(["login", "register"] as Mode[]).map((m) => (
                <button
                  key={m}
                  onClick={() => switchMode(m)}
                  className={`relative h-9 text-sm font-medium rounded-lg transition-colors ${
                    mode === m ? "text-main" : "text-muted hover:text-main"
                  }`}
                >
                  {mode === m && (
                    <motion.div
                      layoutId="auth-pill"
                      className="absolute inset-0 bg-elevated rounded-lg shadow-soft"
                      transition={{ type: "spring", stiffness: 400, damping: 30 }}
                    />
                  )}
                  <span className="relative z-[1]">
                    {m === "login" ? "Вход" : "Регистрация"}
                  </span>
                </button>
              ))}
            </div>

            <form onSubmit={submit} className="space-y-4">
              {mode === "register" && (
                <Field
                  label="Отображаемое имя (необязательно)"
                  value={displayName}
                  onChange={setDisplayName}
                  placeholder="Как вас называть"
                  autoComplete="name"
                />
              )}
              <Field
                label="Логин"
                value={username}
                onChange={setUsername}
                placeholder="username"
                autoComplete="username"
                required
                minLength={3}
              />
              <div>
                <label className="block text-sm font-medium text-main mb-1.5">Пароль</label>
                <div className="relative">
                  <input
                    type={showPwd ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    autoComplete={mode === "login" ? "current-password" : "new-password"}
                    required
                    minLength={6}
                    className="w-full h-11 px-3.5 pr-11 rounded-xl bg-soft border border-app text-main placeholder:text-faint focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-500/20 transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPwd((v) => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-main transition-colors"
                    tabIndex={-1}
                  >
                    {showPwd ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {localError && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="text-sm text-red-500 bg-red-500/10 rounded-lg px-3 py-2"
                >
                  {localError}
                </motion.div>
              )}

              <button
                type="submit"
                disabled={loading || !username || !password}
                className="w-full h-11 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-medium shadow-soft transition-all active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Подождите…
                  </>
                ) : mode === "login" ? (
                  "Войти"
                ) : (
                  "Создать аккаунт"
                )}
              </button>
            </form>
          </div>

          <p className="mt-6 text-center text-xs text-faint">
            Войдите, чтобы сохранялась история чатов
          </p>
        </motion.div>
      </div>
    </div>
  );
}

interface FieldProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  autoComplete?: string;
  required?: boolean;
  minLength?: number;
}

function Field({ label, value, onChange, ...rest }: FieldProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-main mb-1.5">{label}</label>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full h-11 px-3.5 rounded-xl bg-soft border border-app text-main placeholder:text-faint focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-500/20 transition-all"
        {...rest}
      />
    </div>
  );
}
