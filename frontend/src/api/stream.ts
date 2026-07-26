/** Стриминг ответа ассистента через fetch + ReadableStream.

Парсит SSE-события (data: {...}) от эндпоинта /api/chats/{id}/messages.
Возвращает AsyncIterable StreamEvent + контроллер для отмены.
*/
import type { StreamEvent } from "@/types";
import { ApiError, getToken } from "./client";

export interface StreamHandle {
  events: AsyncIterable<StreamEvent>;
  abort: () => void;
}

export function streamMessage(
  chatId: string,
  content: string,
  images: File[] = [],
  model?: string
): StreamHandle {
  const controller = new AbortController();

  const form = new FormData();
  form.append("content", content);
  if (model) form.append("model", model);
  for (const img of images) form.append("images", img);

  const iterator = async function* (): AsyncIterable<StreamEvent> {
    const token = getToken();
    const resp = await fetch(`/api/chats/${chatId}/messages`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
      signal: controller.signal,
    });

    if (!resp.ok || !resp.body) {
      let message = `Ошибка ${resp.status}`;
      try {
        const data = await resp.json();
        message = data.detail || message;
      } catch {
        /* ignore */
      }
      throw new ApiError(resp.status, message);
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // SSE-сообщения разделяются двойным переводом строки.
        let sep: number;
        while ((sep = buffer.indexOf("\n\n")) >= 0) {
          const rawEvent = buffer.slice(0, sep);
          buffer = buffer.slice(sep + 2);
          const event = parseSSE(rawEvent);
          if (event) yield event;
        }
      }
    } finally {
      reader.releaseLock();
    }
  };

  return {
    events: iterator(),
    abort: () => controller.abort(),
  };
}

function parseSSE(raw: string): StreamEvent | null {
  const lines = raw.split("\n");
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed.startsWith("data:")) continue;
    const payload = trimmed.slice(5).trim();
    if (!payload) continue;
    try {
      return JSON.parse(payload) as StreamEvent;
    } catch {
      /* битый JSON — пропускаем */
    }
  }
  return null;
}
