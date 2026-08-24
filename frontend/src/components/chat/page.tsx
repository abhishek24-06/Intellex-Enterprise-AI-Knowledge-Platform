"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import ChatSidebar from "./ChatSidebar";
import ChatWindow from "./ChatWindow";
import { apiFetch } from "@/src/lib/api";
import { ChatSession } from "@/src/types/chat";

export default function ChatPage() {
  const router = useRouter();

  const [sessions, setSessions] =
    useState<ChatSession[]>([]);

  const [
    activeSessionId,
    setActiveSessionId,
  ] = useState<number | null>(
    null,
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  useEffect(() => {
    const token =
      sessionStorage.getItem(
        "intellex_token",
      );

    if (!token) {
      router.replace("/login");
      return;
    }

    async function loadSessions() {
      try {
        const response =
          await apiFetch<{
            sessions: ChatSession[];
          }>(
            "/chat/sessions",
          );

        setSessions(
          response.sessions,
        );

        if (
          response.sessions.length >
          0
        ) {
          setActiveSessionId(
            response.sessions[0]
              .session_id,
          );
        }
      } catch {
        sessionStorage.removeItem(
          "intellex_token",
        );

        router.replace("/login");
      } finally {
        setLoading(false);
      }
    }

    loadSessions();
  }, [router]);

  async function createSession() {
    const session =
      await apiFetch<ChatSession>(
        "/chat/sessions",
        {
          method: "POST",
          body: JSON.stringify({
            title: null,
          }),
        },
      );

    setSessions(
      (previous) => [
        session,
        ...previous,
      ],
    );

    setActiveSessionId(
      session.session_id,
    );
  }

  async function deleteSession(
    sessionId: number,
  ) {
    await apiFetch<void>(
      `/chat/sessions/${sessionId}`,
      {
        method: "DELETE",
      },
    );

    setSessions(
      (previous) =>
        previous.filter(
          (session) =>
            session.session_id !==
            sessionId,
        ),
    );

    if (
      activeSessionId ===
      sessionId
    ) {
      setActiveSessionId(null);
    }
  }

  function logout() {
    sessionStorage.removeItem(
      "intellex_token",
    );

    router.replace("/login");
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-950 text-sm text-zinc-500">
        Loading Intellex...
      </div>
    );
  }

  return (
    <main className="flex h-screen bg-zinc-950">
      <ChatSidebar
        sessions={sessions}
        activeSessionId={
          activeSessionId
        }
        onSelect={
          setActiveSessionId
        }
        onNewChat={
          createSession
        }
        onDelete={
          deleteSession
        }
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-zinc-800 px-6">
          <div className="text-sm text-zinc-400">
            Enterprise Knowledge
            Intelligence
          </div>

          <button
            onClick={logout}
            className="text-sm text-zinc-500 hover:text-white"
          >
            Sign out
          </button>
        </header>

        <ChatWindow
          sessionId={
            activeSessionId
          }
        />
      </div>
    </main>
  );
}