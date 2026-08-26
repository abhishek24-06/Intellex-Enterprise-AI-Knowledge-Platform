import { apiFetch } from "./client";
import type { ChatExecutionTrace, ObservabilitySummary } from "@/types/api";

// Protected by require_observability_admin (ORG_ADMIN | SUPER_ADMIN).

export function getObservabilitySummary(windowHours: number): Promise<ObservabilitySummary> {
  return apiFetch<ObservabilitySummary>(
    `/admin/observability/summary?window_hours=${encodeURIComponent(String(windowHours))}`,
  );
}

export function getChatTrace(chatId: number): Promise<ChatExecutionTrace> {
  return apiFetch<ChatExecutionTrace>(`/admin/observability/chat/${chatId}`);
}
