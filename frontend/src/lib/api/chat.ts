import { apiFetch } from "./client";
import type {
  ChatHistoryListResponse,
  ChatQueryResponse,
  ChatSession,
  ChatSessionListResponse,
  ChatSessionUpdateRequest,
} from "@/types/api";

// ---------------------------------------------------------------------------
// Sessions
// ---------------------------------------------------------------------------

export interface CreateChatSessionRequest {
  title?: string | null;
}

export function createSession(payload: CreateChatSessionRequest = {}): Promise<ChatSession> {
  return apiFetch<ChatSession>("/chat/sessions", { method: "POST", body: payload });
}

export function listSessions(): Promise<ChatSessionListResponse> {
  return apiFetch<ChatSessionListResponse>("/chat/sessions");
}

export function getSession(sessionId: number): Promise<ChatSession> {
  return apiFetch<ChatSession>(`/chat/sessions/${sessionId}`);
}

export function updateSession(
  sessionId: number,
  payload: ChatSessionUpdateRequest,
): Promise<ChatSession> {
  return apiFetch<ChatSession>(`/chat/sessions/${sessionId}`, {
    method: "PATCH",
    body: payload,
  });
}

export async function deleteSession(sessionId: number): Promise<void> {
  await apiFetch<void>(`/chat/sessions/${sessionId}`, { method: "DELETE" });
}

// ---------------------------------------------------------------------------
// Messages (Agentic RAG)
// ---------------------------------------------------------------------------

export interface SendMessageRequest {
  query: string;
}

export function sendMessage(sessionId: number, query: string): Promise<ChatQueryResponse> {
  return apiFetch<ChatQueryResponse>(`/chat/sessions/${sessionId}/messages`, {
    method: "POST",
    body: { query },
  });
}

export function getMessages(sessionId: number): Promise<ChatHistoryListResponse> {
  return apiFetch<ChatHistoryListResponse>(`/chat/sessions/${sessionId}/messages`);
}
