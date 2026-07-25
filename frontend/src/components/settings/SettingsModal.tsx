/** Модалка настроек: тема, имя, выход. */
import { LogOut, Monitor, Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

import { updateMe } from "@/api/auth";
import { useAuthStore } from "@/store/auth";
import { useThemeStore } from "@/store/theme";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { useCapabilities } from "@/hooks/useCapabilities";
import type { Theme } from "@/types";

interface SettingsModalProps {
  open: boolean;
  onClose: () => void;
}

export function SettingsModal({ open, onClose }: SettingsModalProps) {
  const { user, logout, patchUser } = useAuthStore();
  const { theme, setTheme } = useThemeStore();
  const caps = useCapabilities(true);
  const [name, setName] = useState(user?.display_name || "");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setName(user?.display_name || "");
  }, [user, open]);

  const saveName = async () => {
    if (!name.trim()) return;
    setSaving(true);
    try {
      const updated = await updateMe({ display_name: name.trim() });
      patchUser({ display_name: updated.display_name });
    } finally {
      setSaving(false);
    }
  };

  const themeOptions: { value: Theme; label: string; icon: React.ReactNode }[] = [
    { value: "light", label: "Светлая", icon: <Sun size={16} /> },
    { value: "dark", label: "Тёмная", icon: <Moon size={16} /> },
    { value: "system", label: "Системная", icon: <Monitor size={16} /> },
  ];

  return (
    <Modal open={open} onClose={onClose} title="Настройки">
      <div className="space-y-5">
        {/* Профиль */}
        <section>
          <div className="text-sm font-semibold text-main mb-2">Профиль</div>
          <div className="flex items-center gap-3 mb-3">
            <div className="h-12 w-12 rounded-full bg-brand-500 text-white flex items-center justify-center font-semibold text-lg">
              {(user?.display_name || user?.username || "?").charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0">
              <div className="font-medium text-main truncate">{user?.display_name}</div>
              <div className="text-sm text-faint truncate">@{user?.username}</div>
            </div>
          </div>
          <label className="block text-xs font-medium text-muted mb-1.5">Отображаемое имя</label>
          <div className="flex gap-2">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="flex-1 h-10 px-3 rounded-xl bg-soft border border-app text-main text-sm focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-500/20 transition-all"
            />
            <Button onClick={saveName} disabled={saving || !name.trim()} variant="primary" size="md">
              {saving ? "…" : "Сохранить"}
            </Button>
          </div>
        </section>

        {/* Тема */}
        <section>
          <div className="text-sm font-semibold text-main mb-2">Тема оформления</div>
          <div className="grid grid-cols-3 gap-2">
            {themeOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setTheme(opt.value)}
                className={`h-16 rounded-xl border flex flex-col items-center justify-center gap-1.5 text-xs font-medium transition-all ${
                  theme === opt.value
                    ? "border-brand-500 bg-brand-50 dark:bg-brand-900/20 text-brand-600 dark:text-brand-300"
                    : "border-app bg-soft text-muted hover:text-main"
                }`}
              >
                {opt.icon}
                {opt.label}
              </button>
            ))}
          </div>
        </section>

        {/* О сервере */}
        {caps.model && (
          <section>
            <div className="text-sm font-semibold text-main mb-2">Сервер</div>
            <div className="rounded-xl bg-soft border border-app p-3 space-y-1.5 text-sm">
              <div className="flex justify-between">
                <span className="text-muted">Модель</span>
                <span className="text-main font-mono text-xs">{caps.model}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Изображения</span>
                <span className={caps.vision_enabled ? "text-green-500" : "text-faint"}>
                  {caps.vision_enabled ? `до ${caps.max_images_per_message} шт.` : "отключены"}
                </span>
              </div>
            </div>
          </section>
        )}

        {/* Выход */}
        <section className="pt-2 border-t border-app">
          <button
            onClick={() => {
              onClose();
              logout();
            }}
            className="w-full h-10 rounded-xl border border-app bg-soft hover:bg-red-500/10 text-red-500 font-medium text-sm flex items-center justify-center gap-2 transition-all"
          >
            <LogOut size={16} />
            Выйти из аккаунта
          </button>
        </section>
      </div>
    </Modal>
  );
}
