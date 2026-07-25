/** Meta API — возможности сервера. */
import type { Capabilities } from "@/types";
import { request } from "./client";

export async function fetchCapabilities(): Promise<Capabilities> {
  return request<Capabilities>("/capabilities");
}
