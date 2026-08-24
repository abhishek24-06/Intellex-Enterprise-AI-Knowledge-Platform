export interface ChatSession {
  session_id: number;
  title: string | null;
  created_at: string;
  last_active: string;
  is_pinned: boolean;
}

export interface ChatSource {
  document_id: number;
  original_filename: string;
}

export interface ChatMessage {
  chat_id: number;
  session_id: number;
  question: string;
  answer: string;
  created_at: string;
  feedback: string | null;
  sources: ChatSource[];
}

/**
 * GET /chat/sessions/{session_id}/messages
 */
export interface ChatHistoryResponse {
  messages: ChatMessage[];
}

/**
 * POST /chat/sessions/{session_id}/messages
 *
 * Backend returns:
 * {
 *   query,
 *   answer,
 *   sources
 * }
 */
export interface ChatMessageResponse {
  query: string;
  answer: string;
  sources: ChatSource[];
}