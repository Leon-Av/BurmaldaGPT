/** Селектор модели (если сервер разрешает выбор) — дропдаун в шапке чата. */
import { AnimatePresence, motion } from "framer-motion";
import { Check, ChevronDown, Cloud, Cpu } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { useChatsStore } from "@/store/chats";
import type { ModelOption } from "@/types";

interface ModelSelectorProps {
  models: ModelOption[];
}

export function ModelSelector({ models }: ModelSelectorProps) {
  const { selectedModel, setSelectedModel } = useChatsStore();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  // Опция «Авто» (балансировка) + список моделей.
  const current = models.find((m) => m.name === selectedModel);
  const label = current ? current.name : "Авто";

  const pick = (name: string | null) => {
    setSelectedModel(name);
    setOpen(false);
  };

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center gap-1.5 h-9 px-3 rounded-xl border border-app bg-elevated text-main text-sm font-medium hover:bg-soft transition-colors max-w-[200px] sm:max-w-none"
        title="Выбрать модель"
      >
        <span className="truncate">{label}</span>
        <ChevronDown size={15} className={`shrink-0 text-muted transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: -4 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -4 }}
            transition={{ duration: 0.12 }}
            className="absolute right-0 top-full mt-1 w-64 bg-elevated border border-app rounded-xl shadow-float py-1.5 z-30"
          >
            <button
              onClick={() => pick(null)}
              className="w-full px-3 py-2.5 text-left hover:bg-soft flex items-center gap-2.5 transition-colors"
            >
              <Cpu size={15} className="text-brand-500 shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-sm text-main font-medium">Авто</div>
                <div className="text-xs text-faint">Балансировка между серверами</div>
              </div>
              {!selectedModel && <Check size={15} className="text-brand-500" />}
            </button>

            {models.length > 0 && (
              <div className="px-3 py-1.5 text-[10px] uppercase tracking-wider text-faint font-semibold">
                Модели
              </div>
            )}

            {models.map((m) => (
              <button
                key={m.name}
                onClick={() => pick(m.name)}
                className="w-full px-3 py-2.5 text-left hover:bg-soft flex items-center gap-2.5 transition-colors"
              >
                {m.kind === "cloud" ? (
                  <Cloud size={15} className="text-brand-400 shrink-0" />
                ) : (
                  <Cpu size={15} className="text-brand-500 shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-main font-medium truncate">{m.name}</div>
                  <div className="text-xs text-faint truncate font-mono">{m.model || "—"}</div>
                </div>
                {selectedModel === m.name && <Check size={15} className="text-brand-500" />}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
