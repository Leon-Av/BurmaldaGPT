/** Главный layout чата после входа.

Ключевая идея: контейнер сообщений и поле ввода — стабильная структура,
которая НЕ пересоздаётся при появлении первого ответа (раньше welcome↔chat
переключение ломало скролл посреди стрима). Когда сообщений нет — поверх
показывается центрированный welcome-оверлей; когда есть — обычный список.
*/
import { motion } from "framer-motion";
import { Menu, Sun, Moon, Monitor, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { useChatsStore } from "@/store/chats";
import { useThemeStore } from "@/store/theme";

import type { Theme } from "@/types";
import { Logo } from "@/components/ui/Logo";
import { Message } from "./Message";
import { MessageInput } from "./MessageInput";
import { SettingsModal } from "@/components/settings/SettingsModal";
import { Sidebar } from "./Sidebar";

const SUGGESTIONS = [
  { icon: "💡", title: "Объясни простыми словами", prompt: "Объясни, что такое квантовая запутанность, простыми словами" },
  { icon: "✍️", title: "Помоги с текстом", prompt: "Напиши короткое дружелюбное письмо коллеге" },
  { icon: "🧮", title: "Реши задачу", prompt: "У Маши 12 яблок, она отдала треть. Сколько осталось?" },
  { icon: "🌍", title: "Расскажи факт", prompt: "Расскажи интересный факт о космосе" },
];

export function ChatLayout() {
  const {
    activeChatId,
    chats,
    messagesByChat,
    streaming,
    streamingChatId,
    loadChats,
    sendMessage,
    stopStreaming,
  } = useChatsStore();
  const { theme, setTheme } = useThemeStore();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const messages = activeChatId ? messagesByChat[activeChatId] || [] : [];
  const showWelcome = messages.length === 0;

  const scrollRef = useRef<HTMLDivElement>(null);
  // Приклеен ли пользователь к низу — управляем авто-скроллом.
  const [stick, setStick] = useState(true);

  useEffect(() => {
    loadChats();
  }, [loadChats]);

  // Сброс «приклеенности» при смене чата — новый чат всегда приклеен.
  useEffect(() => {
    setStick(true);
  }, [activeChatId]);

  // Авто-скролл: только если пользователь около низа. Без scrollIntoView —
  // оно «тянет» за собой родительские контейнеры и ломает страницу.
  useEffect(() => {
    if (!stick) return;
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, stick]);

  const onScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    setStick(distanceFromBottom < 120);
  };

  const themeIcon = { light: <Sun size={18} />, dark: <Moon size={18} />, system: <Monitor size={18} /> };
  const cycleTheme = () => {
    const order: Theme[] = ["light", "dark", "system"];
    const i = order.indexOf(theme);
    setTheme(order[(i + 1) % order.length]);
  };

  const activeChatTitle =
    chats.find((c) => c.id === activeChatId)?.title || "Новый чат";

  // Последний assistant для кнопки «копировать».
  let lastAssistantId: string | null = null;
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].role === "assistant") {
      lastAssistantId = messages[i].id;
      break;
    }
  }

  const handleSubmit = (content: string, images?: File[]) => {
    setStick(true);
    sendMessage(content, images);
  };

  return (
    <div className="h-screen flex overflow-hidden bg-app">
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      {/* Правая часть: шапка + область сообщений + поле ввода.
          Стабильная структура — не пересоздаётся при первом ответе. */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 px-3 md:px-5 flex items-center justify-between shrink-0 border-b border-app">
          <div className="flex items-center gap-2 min-w-0">
            <button
              onClick={() => setSidebarOpen(true)}
              className="md:hidden h-10 w-10 rounded-xl text-muted hover:text-main hover:bg-soft flex items-center justify-center shrink-0"
              aria-label="Открыть панель"
            >
              <Menu size={20} />
            </button>
            <h2 className="font-semibold text-main truncate">{activeChatTitle}</h2>
            {streaming && streamingChatId === activeChatId && (
              <span className="hidden sm:inline-flex items-center gap-1.5 text-xs text-faint ml-2">
                <span className="h-1.5 w-1.5 rounded-full bg-brand-500 animate-pulse-soft" />
                печатает
              </span>
            )}
          </div>
          <button
            onClick={cycleTheme}
            className="h-10 w-10 rounded-xl text-muted hover:text-main hover:bg-soft flex items-center justify-center transition-colors shrink-0"
            title={`Тема: ${theme}`}
          >
            {themeIcon[theme]}
          </button>
        </header>

        {/* Контейнер сообщений — единый overflow-y-auto, не пересоздаётся. */}
        <div
          ref={scrollRef}
          onScroll={onScroll}
          className="flex-1 overflow-y-auto overflow-x-hidden"
        >
          {showWelcome ? (
            <WelcomeOverlay onSubmit={handleSubmit} />
          ) : (
            <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
              {messages.map((m) => (
                <Message
                  key={m.id}
                  message={m}
                  chatId={activeChatId || ""}
                  streaming={
                    streaming && streamingChatId === activeChatId && m.role === "assistant"
                  }
                  isLastAssistant={m.id === lastAssistantId}
                />
              ))}
              <div className="h-4" />
            </div>
          )}
        </div>

        {/* Поле ввода — внизу. Скрыто на welcome (там центрированный input
            в overlay), чтобы не дублировать поле ввода. */}
        {!showWelcome && (
          <div className="shrink-0 px-4 pb-4 pt-2 bg-app">
            <div className="max-w-3xl mx-auto">
              {streaming && (
                <div className="mb-2 flex justify-center">
                  <button
                    onClick={stopStreaming}
                    className="inline-flex items-center gap-2 h-8 px-3 rounded-full border border-app bg-elevated text-muted hover:text-main text-xs font-medium transition-colors"
                  >
                    <Square size={12} className="fill-current" />
                    Остановить
                  </button>
                </div>
              )}
              <MessageInput onSubmit={handleSubmit} streaming={streaming} />
            </div>
          </div>
        )}
      </div>

      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}

/** Центрированный welcome-оверлей внутри скроллируемого контейнера. */
function WelcomeOverlay({
  onSubmit,
}: {
  onSubmit: (content: string, images?: File[]) => void;
}) {
  return (
    <div className="min-h-full flex flex-col items-center justify-center px-4 py-10">
      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="flex flex-col items-center mb-8"
      >
        <div className="animate-float">
          <Logo size={72} animated showText={false} />
        </div>
        <h1 className="mt-6 text-3xl font-extrabold tracking-tight text-main">
          Бурмалда
          <span className="font-semibold text-muted">GPT</span>
        </h1>
        <p className="mt-2 text-muted text-center max-w-md">
          Чат-ассистент, который отвечает на «бурмалде». Спросите что угодно.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-2xl"
      >
        <MessageInput onSubmit={onSubmit} streaming={false} autoFocus />

        <div className="mt-6 grid grid-cols-2 gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s.title}
              onClick={() => onSubmit(s.prompt)}
              className="group flex items-center gap-3 p-3 rounded-xl border border-app bg-elevated hover:bg-soft text-left transition-all active:scale-[0.98] shadow-soft"
            >
              <span className="text-xl shrink-0">{s.icon}</span>
              <div className="min-w-0">
                <div className="text-sm font-medium text-main truncate">{s.title}</div>
                <div className="text-xs text-faint truncate">{s.prompt}</div>
              </div>
            </button>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
