/** Дружелюбный баннер ошибки (429/перегрузка) с кнопкой закрытия. */
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, X } from "lucide-react";

import { useChatsStore } from "@/store/chats";

export function ErrorBanner() {
  const { lastError, dismissError } = useChatsStore();

  return (
    <AnimatePresence>
      {lastError && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
          transition={{ duration: 0.2 }}
          className="fixed bottom-24 left-1/2 -translate-x-1/2 z-40 max-w-md w-[calc(100%-2rem)]"
        >
          <div className="flex items-start gap-3 p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 shadow-float">
            <AlertTriangle size={18} className="text-amber-500 shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <div className="text-sm text-amber-900 dark:text-amber-100 font-medium">
                {lastError}
              </div>
            </div>
            <button
              onClick={dismissError}
              className="text-amber-500 hover:text-amber-700 dark:hover:text-amber-300 p-0.5 rounded-md transition-colors shrink-0"
              aria-label="Закрыть"
            >
              <X size={16} />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
