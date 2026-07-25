/** Общие типы приложения. */

export type Theme = "light" | "dark" | "system";

export interface User {
  id: string;
  username: string;
  display_name: string;
  theme: Theme;
}

export interface Chat {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface MessageImage {
  id: string;
  mime_type: string;
  order_index: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  images?: MessageImage[];
}

export interface Capabilities {
  vision_enabled: boolean;
  max_images_per_message: number;
  model: string;
}

/** SSE-события стрима ответа ассистента. */
export type StreamEvent =
  | { type: "token"; delta: string }
  | { type: "title"; title: string }
  | { type: "message"; id: string }
  | { type: "error"; status?: number; message: string }
  | { type: "done" };
