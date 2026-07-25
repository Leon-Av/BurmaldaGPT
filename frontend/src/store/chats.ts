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
  currentStream: StreamHandle | null;

  loadChats: () => Promise<void>;
  createChat: () => Promise<string>;
  selectChat: (chatId: string) => Promise<void>;
  renameChat: (chatId: string, title: string) => Promise<void>;
  removeChat: (chatId: string) => Promise<void>;
  sendMessage: (content: string, images?: File[]) => Promise<void>;
  stopStreaming: () => void;
  ensureActiveChat: () => Promise<string>;
}

export const useChatsStore = create<ChatsState>((set, get) => ({
  chats: [],
  activeChatId: null,
  messagesByChat: {},
  loadingChats: false,
  loadingMessages: false,
  streaming: false,
  streamingChatId: null,
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
    // Оптимистичное обновление.
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

  sendMessage: async (content, images = []) => {
    const chatId = await get().ensureActiveChat();

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
    }));

    const handle = streamMessage(chatId, content, images);
    set({ currentStream: handle });

    try {
      for await (const ev of handle.events) {
        if (ev.type === "token") {
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
          // Заменяем placeholder на сохранённый id.
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
          set((s) => {
            const list = s.messagesByChat[chatId] || [];
            return {
              messagesByChat: {
                ...s.messagesByChat,
                [chatId]: list.map((m) =>
                  m.id === assistantPlaceholderId
                    ? {
                        ...m,
                        content:
                          m.content ||
                          `_Ошибка: ${ev.message}_`,
                      }
                    : m
                ),
              },
            };
          });
        } else if (ev.type === "done") {
          break;
        }
      }
    } catch (e) {
      // Прерывание (abort) — это не ошибка.
      if ((e as Error).name !== "AbortError") {
        set((s) => {
          const list = s.messagesByChat[chatId] || [];
          return {
            messagesByChat: {
              ...s.messagesByChat,
              [chatId]: list.map((m) =>
                m.id === assistantPlaceholderId
                  ? { ...m, content: m.content || `_Ошибка: ${(e as Error).message}_` }
                  : m
              ),
            },
          };
        });
      }
    } finally {
      set({ streaming: false, streamingChatId: null, currentStream: null });
      // Обновляем порядок/заголовок чата.
      void get().loadChats();
    }
  },

  stopStreaming: () => {
    const { currentStream } = get();
    if (currentStream) currentStream.abort();
    set({ streaming: false, streamingChatId: null, currentStream: null });
  },
}));
