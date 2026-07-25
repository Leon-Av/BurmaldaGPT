/** Chats API. */
import type { Chat, Message } from "@/types";
import { request } from "./client";

export async function listChats(): Promise<Chat[]> {
  return request<Chat[]>("/chats");
}

export async function createChat(title?: string): Promise<Chat> {
  return request<Chat>("/chats", {
    method: "POST",
    body: JSON.stringify({ title: title || null }),
  });
}

export async function updateChat(chatId: string, title: string): Promise<Chat> {
  return request<Chat>(`/chats/${chatId}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });
}

export async function deleteChat(chatId: string): Promise<void> {
  await request<void>(`/chats/${chatId}`, { method: "DELETE" });
}

export async function listMessages(chatId: string): Promise<Message[]> {
  return request<Message[]>(`/chats/${chatId}/messages`);
}

export function imageUrl(chatId: string, messageId: string, imageId: string): string {
  return `/api/chats/${chatId}/messages/${messageId}/image/${imageId}`;
}
