"use client";

import { ChatSession } from "@/src/types/chat";

interface Props {
  sessions: ChatSession[];
  activeSessionId: number | null;
  onSelect: (sessionId: number) => void;
  onNewChat: () => void;
  onDelete: (sessionId: number) => void;
}

export default function ChatSidebar({
  sessions,
  activeSessionId,
  onSelect,
  onNewChat,
  onDelete,
}: Props) {
  return (
    <aside className="flex w-72 flex-col border-r border-zinc-800 bg-zinc-950">
      <div className="flex items-center justify-between border-b border-zinc-800 p-4">
        <div>
          <div className="font-semibold text-white">
            Intellex
          </div>

          <div className="text-xs text-zinc-500">
            Knowledge Intelligence
          </div>
        </div>
      </div>

      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full rounded-xl border border-zinc-700 px-4 py-3 text-left text-sm text-white transition hover:bg-zinc-900"
        >
          + New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-4">
        <div className="mb-2 px-2 text-xs uppercase tracking-wider text-zinc-600">
          Conversations
        </div>

        <div className="space-y-1">
          {sessions.map(
            (session) => (
              <div
                key={
                  session.session_id
                }
                className={`group flex items-center rounded-xl ${
                  activeSessionId ===
                  session.session_id
                    ? "bg-zinc-800"
                    : "hover:bg-zinc-900"
                }`}
              >
                <button
                  onClick={() =>
                    onSelect(
                      session.session_id,
                    )
                  }
                  className="min-w-0 flex-1 px-3 py-3 text-left"
                >
                  <div className="truncate text-sm text-zinc-200">
                    {session.title ??
                      "New conversation"}
                  </div>
                </button>

                <button
                  onClick={() =>
                    onDelete(
                      session.session_id,
                    )
                  }
                  className="mr-2 hidden rounded-lg px-2 py-1 text-xs text-zinc-500 hover:bg-zinc-800 hover:text-red-400 group-hover:block"
                  aria-label="Delete chat"
                >
                  ×
                </button>
              </div>
            ),
          )}
        </div>
      </div>
    </aside>
  );
}