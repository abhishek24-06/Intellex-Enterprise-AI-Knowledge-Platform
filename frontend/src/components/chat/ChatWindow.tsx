"use client";

import {
  FormEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import { apiFetch } from "@/src/lib/api";

import MessageBubble from "./MessageBubble";

import {
  ChatHistoryResponse,
  ChatMessage,
  ChatMessageResponse,
} from "@/src/types/chat";

interface Props {
  sessionId: number | null;
}

export default function ChatWindow({
  sessionId,
}: Props) {
  const [messages, setMessages] =
    useState<ChatMessage[]>([]);

  const [query, setQuery] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const messagesContainerRef =
    useRef<HTMLDivElement>(null);
  // ------------------------------------------------------------
  // Load existing conversation
  // ------------------------------------------------------------

  useEffect(() => {
    if (!sessionId) {
      setMessages([]);
      return;
    }

    async function loadHistory() {
      try {
        setError("");

        const data =
          await apiFetch<ChatHistoryResponse>(
            `/chat/sessions/${sessionId}/messages`,
          );

        setMessages(data.messages);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load conversation.",
        );
      }
    }

    void loadHistory();
  }, [sessionId]);

  // ------------------------------------------------------------
  // Auto-scroll
  // ------------------------------------------------------------

  useEffect(() => {
  const container =
    messagesContainerRef.current;

  if (!container) {
    return;
  }

  container.scrollTo({
    top: container.scrollHeight,
    behavior: "smooth",
  });
}, [messages]);
  // ------------------------------------------------------------
  // Send message
  // ------------------------------------------------------------

  async function sendMessage(
    event: FormEvent,
  ) {
    event.preventDefault();

    if (
      !sessionId ||
      !query.trim() ||
      loading
    ) {
      return;
    }

    const currentQuery =
      query.trim();

    setQuery("");
    setError("");
    setLoading(true);

    try {
      const response =
        await apiFetch<ChatMessageResponse>(
          `/chat/sessions/${sessionId}/messages`,
          {
            method: "POST",
            body: JSON.stringify({
              query: currentQuery,
            }),
          },
        );

      /*
       * POST response only contains:
       *
       * query
       * answer
       * sources
       *
       * It does NOT contain chat_id/session_id/created_at.
       *
       * Therefore we build the frontend message using:
       * - current session ID
       * - current query
       * - temporary unique ID
       * - current timestamp
       */

      const message: ChatMessage = {
        chat_id: -Date.now(),
        session_id: sessionId,
        question: response.query,
        answer: response.answer,
        created_at:
          new Date().toISOString(),
        feedback: null,
        sources: response.sources,
      };

      setMessages(
        (previous) => [
          ...previous,
          message,
        ],
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Message failed.",
      );

      setQuery(currentQuery);
    } finally {
      setLoading(false);
    }
  }

  // ------------------------------------------------------------
  // Empty state
  // ------------------------------------------------------------

  if (!sessionId) {
    return (
      <div className="flex flex-1 items-center justify-center bg-zinc-950">
        <div className="text-center">
          <div className="mb-2 text-2xl font-semibold text-white">
            Welcome to Intellex
          </div>

          <div className="text-sm text-zinc-500">
            Start a new conversation to
            query your enterprise
            knowledge base.
          </div>
        </div>
      </div>
    );
  }

  // ------------------------------------------------------------
  // Chat UI
  // ------------------------------------------------------------

  return (
    <section className="flex min-h-0 min-w-0 flex-1 flex-col bg-zinc-950">

      <div
  ref={messagesContainerRef}
  className="min-h-0 flex-1 overflow-y-auto px-6 py-8"
>
        <div className="mx-auto max-w-4xl space-y-8">

          {messages.map(
            (message) => (
              <MessageBubble
                key={
                  `${message.chat_id}-${message.created_at}`
                }
                message={message}
              />
            ),
          )}

          {loading && (
            <div className="max-w-fit rounded-2xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-sm text-zinc-500">
              Intellex is thinking...
            </div>
          )}

          {error && (
            <div className="rounded-xl border border-red-900 bg-red-950/30 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}

        </div>
      </div>

      <div className="border-t border-zinc-800 p-4">

        <form
          onSubmit={sendMessage}
          className="mx-auto flex max-w-4xl items-end gap-3 rounded-2xl border border-zinc-700 bg-zinc-900 p-2"
        >

          <textarea
            value={query}
            onChange={(event) =>
              setQuery(
                event.target.value,
              )
            }
            onKeyDown={(event) => {
              if (
                event.key ===
                  "Enter" &&
                !event.shiftKey
              ) {
                event.preventDefault();

                void sendMessage(
                  event as unknown as FormEvent,
                );
              }
            }}
            rows={1}
            placeholder="Ask Intellex anything..."
            className="max-h-40 min-h-12 flex-1 resize-none bg-transparent px-3 py-3 text-sm text-white outline-none placeholder:text-zinc-600"
          />

          <button
            type="submit"
            disabled={
              loading ||
              !query.trim()
            }
            className="rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {loading
              ? "Thinking..."
              : "Send"}
          </button>

        </form>
      </div>

    </section>
  );
}