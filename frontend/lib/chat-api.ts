import { fetchApi, getApiBaseUrl } from "./api";

export interface SourceReference {
  document_id: string;
  chunk_text: string;
  score: number;
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  role: string;
  content: string;
  tokens_used: number;
  sources: SourceReference[];
  model_used: string | null;
}

export async function sendMessage(
  assistantId: string,
  conversationId: string | null,
  message: string
): Promise<ChatResponse> {
  return fetchApi("/chat", {
    method: "POST",
    body: JSON.stringify({
      assistant_id: assistantId,
      conversation_id: conversationId,
      message,
    }),
  });
}

export function createWebSocket(
  assistantId: string,
  tenantId: string,
  token: string
): WebSocket {
  const apiBase = getApiBaseUrl();
  const wsBase = apiBase.replace(/^http/, "ws");
  const url = `${wsBase}/ws/chat?token=${encodeURIComponent(token)}&tenant_id=${encodeURIComponent(tenantId)}&assistant_id=${encodeURIComponent(assistantId)}`;
  return new WebSocket(url);
}
