/** Стор чатов и сообщений. */
import { create } from "zustand";

import * as chatsApi from "@/api/chats";
import { streamMessage, type StreamHandle } from "@/api/stream";
import type { Chat, Message } from "@/types";

interface ChatsState {
  chats: Chat[];
  activeChatId: string | null;
  messagesByChat: Record<string, Message[]>;
  loadingChats: boolean;
  loadingMessages: boolean;
  streaming: boolean;
  streamingChatId: string | null;
  /** Источник (сервер/модель), обрабатывающий текущий стрим — для индикатора в UI. */
  currentSource: string | null;
  /** Текст ошибки последнего запроса (для дружелюбного UI). Сбрасывается при новом запросе. */
  lastError: string | null;
  /** Выбранная пользователем модель (имя источника) или null = авто. */
  selectedModel: string | null;
  currentStream: StreamHandle | null;

  loadChats: () => Promise<void>;
  createChat: () => Promise<string>;
  selectChat: (chatId: string) => Promise<void>;
  renameChat: (chatId: string, title: string) => Promise<void>;
  removeChat: (chatId: string) => Promise<void>;
  sendMessage: (content: string, images?: File[]) => Promise<void>;
  stopStreaming: () => void;
  ensureActiveChat: () => Promise<string>;
  setSelectedModel: (name: string | null) => void;
  dismissError: () => void;
}

export const useChatsStore = create<ChatsState>((set, get) => ({
  chats: [],
  activeChatId: null,
  messagesByChat: {},
  loadingChats: false,
  loadingMessages: false,
  streaming: false,
  streamingChatId: null,
  currentSource: null,
  lastError: null,
  selectedModel: null,
  currentStream: null,

  loadChats: async () => {
    set({ loadingChats: true });
    try {
      const chats = await chatsApi.listChats();
      set({ chats, loadingChats: false });
    } catch {
      set({ loadingChats: false });
    }
  },

  createChat: async () => {
    const chat = await chatsApi.createChat();
    set((s) => ({
      chats: [chat, ...s.chats.filter((c) => c.id !== chat.id)],
      activeChatId: chat.id,
      messagesByChat: { ...s.messagesByChat, [chat.id]: [] },
    }));
    return chat.id;
  },

  selectChat: async (chatId) => {
    set({ activeChatId: chatId, loadingMessages: true });
    try {
      const messages = await chatsApi.listMessages(chatId);
      set((s) => ({
        messagesByChat: { ...s.messagesByChat, [chatId]: messages },
        loadingMessages: false,
      }));
    } catch {
      set({ loadingMessages: false });
    }
  },

  renameChat: async (chatId, title) => {
    set((s) => ({
      chats: s.chats.map((c) => (c.id === chatId ? { ...c, title } : c)),
    }));
    try {
      await chatsApi.updateChat(chatId, title);
    } catch {
      await get().loadChats();
    }
  },

  removeChat: async (chatId) => {
    const prev = get().chats;
    set((s) => {
      const rest = s.chats.filter((c) => c.id !== chatId);
      const next = { ...s.messagesByChat };
      delete next[chatId];
      return {
        chats: rest,
        messagesByChat: next,
        activeChatId: s.activeChatId === chatId ? null : s.activeChatId,
      };
    });
    try {
      await chatsApi.deleteChat(chatId);
    } catch {
      set({ chats: prev });
    }
  },

  ensureActiveChat: async () => {
    const { activeChatId } = get();
    if (activeChatId) return activeChatId;
    return get().createChat();
  },

  setSelectedModel: (name) => set({ selectedModel: name }),
  dismissError: () => set({ lastError: null }),

  sendMessage: async (content, images = []) => {
    const chatId = await get().ensureActiveChat();
    const { selectedModel } = get();

    // Добавляем сообщение пользователя сразу (оптимистично).
    const userMsg: Message = {
      id: `pending-${Date.now()}`,
      role: "user",
      content,
      created_at: new Date().toISOString(),
      images: images.map((file, i) => ({
        id: `pending-img-${i}`,
        mime_type: file.type,
        order_index: i,
      })),
    };
    const assistantPlaceholderId = `pending-assistant-${Date.now()}`;
    const assistantMsg: Message = {
      id: assistantPlaceholderId,
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
      images: [],
    };

    set((s) => ({
      messagesByChat: {
        ...s.messagesByChat,
        [chatId]: [...(s.messagesByChat[chatId] || []), userMsg, assistantMsg],
      },
      streaming: true,
      streamingChatId: chatId,
      currentSource: null,
      lastError: null,
    }));

    const handle = streamMessage(chatId, content, images, selectedModel ?? undefined);
    set({ currentStream: handle });

    try {
      for await (const ev of handle.events) {
        if (ev.type === "source") {
          set({ currentSource: ev.source });
        } else if (ev.type === "token") {
          set((s) => {
            const list = s.messagesByChat[chatId] || [];
            return {
              messagesByChat: {
                ...s.messagesByChat,
                [chatId]: list.map((m) =>
                  m.id === assistantPlaceholderId
                    ? { ...m, content: m.content + ev.delta }
                    : m
                ),
              },
            };
          });
        } else if (ev.type === "title") {
          set((s) => ({
            chats: s.chats.map((c) =>
              c.id === chatId ? { ...c, title: ev.title } : c
            ),
          }));
        } else if (ev.type === "message") {
          set((s) => {
            const list = s.messagesByChat[chatId] || [];
            return {
              messagesByChat: {
                ...s.messagesByChat,
                [chatId]: list.map((m) =>
                  m.id === assistantPlaceholderId ? { ...m, id: ev.id } : m
                ),
              },
            };
          });
        } else if (ev.type === "error") {
          // Дружелюбное сообщение для 429 (перегрузка/rate limit).
          const isOverload = ev.status === 429;
          const friendly = isOverload
            ? "Сервис сейчас перегружен. Пожалуйста, подождите минуту и попробуйте снова."
            : ev.message;
          set({ lastError: friendly });

          // Если ответа ещё нет — убираем пустой placeholder, чтобы не было пустого сообщения.
          set((s) => {
            const list = s.messagesByChat[chatId] || [];
            const assistant = list.find((m) => m.id === assistantPlaceholderId);
            if (assistant && !assistant.content) {
              return {
                messagesByChat: {
                  ...s.messagesByChat,
                  [chatId]: list.filter((m) => m.id !== assistantPlaceholderId),
                },
              };
            }
            return s;
          });
        } else if (ev.type === "done") {
          break;
        }
      }
    } catch (e) {
      if ((e as Error).name !== "AbortError") {
        set({ lastError: (e as Error).message });
        set((s) => {
          const list = s.messagesByChat[chatId] || [];
          const assistant = list.find((m) => m.id === assistantPlaceholderId);
          if (assistant && !assistant.content) {
            return {
              messagesByChat: {
                ...s.messagesByChat,
                [chatId]: list.filter((m) => m.id !== assistantPlaceholderId),
              },
            };
          }
          return s;
        });
      }
    } finally {
      set({
        streaming: false,
        streamingChatId: null,
        currentStream: null,
        currentSource: null,
      });
      void get().loadChats();
    }
  },

  stopStreaming: () => {
    const { currentStream } = get();
    if (currentStream) currentStream.abort();
    set({ streaming: false, streamingChatId: null, currentStream: null, currentSource: null });
  },
}));
