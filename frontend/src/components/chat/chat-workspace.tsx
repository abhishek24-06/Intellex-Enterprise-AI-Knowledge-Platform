"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  BrainCircuit,
  FileText,
  Loader2,
  MessagesSquare,
  PanelLeft,
  Pin,
  RefreshCcw,
  SendHorizonal,
  X,
} from "lucide-react";
import { toast } from "sonner";

import { SessionSidebar } from "@/components/chat/session-sidebar";
import { MarkdownContent } from "@/components/chat/markdown-content";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { EmptyState, ErrorState } from "@/components/shared/states";
import {
  createSession,
  deleteSession,
  getMessages,
  listSessions,
  sendMessage,
  updateSession,
} from "@/lib/api/chat";
import type { ChatHistoryMessage, ChatSource, ChatSession } from "@/types/api";

const SUGGESTIONS = [
  "Summarize our expense reimbursement policy.",
  "Who is in the Engineering department?",
  "What is the escalation procedure for incidents?",
];

interface PendingQuestion {
  question: string;
}

interface SendFailure {
  question: string;
  message: string;
}

export function ChatWorkspace() {
  const queryClient = useQueryClient();

  const [activeIdState, setActiveId] = React.useState<number | null>(null);
  const [draft, setDraft] = React.useState("");
  const [pendingQuestion, setPendingQuestion] = React.useState<PendingQuestion | null>(null);
  const [sendFailure, setSendFailure] = React.useState<SendFailure | null>(null);
  const [mobileListOpen, setMobileListOpen] = React.useState(false);
  const [renaming, setRenaming] = React.useState<ChatSession | null>(null);
  const [deleting, setDeleting] = React.useState<ChatSession | null>(null);
  const [renameValue, setRenameValue] = React.useState("");

  const sessionsQuery = useQuery({
    queryKey: ["chat", "sessions"],
    queryFn: listSessions,
  });

  const sessions = React.useMemo(
    () => sessionsQuery.data?.sessions ?? [],
    [sessionsQuery.data],
  );

  // `null` means "auto-select the most recent session" once data arrives.
  const activeId =
    activeIdState ?? (sessions.length > 0 ? sessions[0].session_id : null);

  const activeSession = React.useMemo(
    () => sessions.find((s) => s.session_id === activeId) ?? null,
    [sessions, activeId],
  );

  const messagesQuery = useQuery({
    queryKey: ["chat", "messages", activeId],
    queryFn: () => getMessages(activeId as number),
    enabled: activeId !== null,
  });

  const createSessionMutation = useMutation({
    mutationFn: () => createSession({}),
    onSuccess: async (session) => {
      await queryClient.invalidateQueries({ queryKey: ["chat", "sessions"] });
      setActiveId(session.session_id);
      setMobileListOpen(false);
    },
    onError: (error) => toast.error(error.message),
  });

  const sendMutation = useMutation({
    mutationFn: ({ sessionId, query }: { sessionId: number; query: string }) =>
      sendMessage(sessionId, query),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["chat", "messages", activeId],
      });
      void queryClient.invalidateQueries({ queryKey: ["chat", "sessions"] });
      setPendingQuestion(null);
    },
    onError: (error, variables) => {
      setPendingQuestion(null);
      setSendFailure({ question: variables.query, message: error.message });
    },
  });

  const updateSessionMutation = useMutation({
    mutationFn: ({
      sessionId,
      title,
      isPinned,
    }: {
      sessionId: number;
      title?: string | null;
      isPinned?: boolean | null;
    }) => updateSession(sessionId, { title, is_pinned: isPinned }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["chat", "sessions"] });
      setRenaming(null);
    },
    onError: (error) => toast.error(error.message),
  });

  const deleteSessionMutation = useMutation({
    mutationFn: (sessionId: number) => deleteSession(sessionId),
    onSuccess: async (_data, sessionId) => {
      await queryClient.invalidateQueries({ queryKey: ["chat", "sessions"] });
      if (activeId === sessionId) setActiveId(null);
      setDeleting(null);
      toast.success("Conversation deleted");
    },
    onError: (error) => toast.error(error.message),
  });

  // Auto-scroll to bottom when messages change.
  const scrollRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const element = scrollRef.current;
    if (element) element.scrollTop = element.scrollHeight;
  }, [messagesQuery.data, pendingQuestion]);

  function handleSend() {
    const trimmed = draft.trim();
    if (!trimmed || activeId === null || sendMutation.isPending) return;

    setSendFailure(null);
    setPendingQuestion({ question: trimmed });
    setDraft("");
    sendMutation.mutate({ sessionId: activeId, query: trimmed });
  }

  function handleNewChat() {
    createSessionMutation.mutate();
  }

  const messages = messagesQuery.data?.messages ?? [];

  return (
    <div className="flex h-[calc(100vh-3.5rem)] min-h-0">
      {/* Sessions sidebar — desktop */}
      <div className="hidden w-72 shrink-0 md:block">
        <SessionSidebar
          sessions={sessionsQuery.data?.sessions}
          isLoading={sessionsQuery.isLoading}
          activeSessionId={activeId}
          onSelect={setActiveId}
          onNewChat={handleNewChat}
          onCreateDisabled={createSessionMutation.isPending}
          onRename={(session) => {
            setRenaming(session);
            setRenameValue(session.title ?? "");
          }}
          onDelete={setDeleting}
          onTogglePin={(session) =>
            updateSessionMutation.mutate({
              sessionId: session.session_id,
              isPinned: !session.is_pinned,
            })
          }
        />
      </div>

      {/* Sessions drawer — mobile */}
      {mobileListOpen ? (
        <div className="fixed inset-0 z-50 flex md:hidden" role="dialog" aria-modal="true">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setMobileListOpen(false)}
            aria-hidden
          />
          <div className="relative w-72 max-w-[80vw]">
            <button
              type="button"
              className="absolute right-2 top-2 rounded-md p-1 text-sidebar-muted hover:text-white"
              onClick={() => setMobileListOpen(false)}
              aria-label="Close conversations"
            >
              <X className="size-5" />
            </button>
            <SessionSidebar
              sessions={sessionsQuery.data?.sessions}
              isLoading={sessionsQuery.isLoading}
              activeSessionId={activeId}
              onSelect={(id) => {
                setActiveId(id);
                setMobileListOpen(false);
              }}
              onNewChat={handleNewChat}
              onCreateDisabled={createSessionMutation.isPending}
              onRename={(session) => {
                setRenaming(session);
                setRenameValue(session.title ?? "");
                setMobileListOpen(false);
              }}
              onDelete={(session) => {
                setDeleting(session);
                setMobileListOpen(false);
              }}
              onTogglePin={(session) => {
                updateSessionMutation.mutate({
                  sessionId: session.session_id,
                  isPinned: !session.is_pinned,
                });
              }}
            />
          </div>
        </div>
      ) : null}

      {/* Conversation column */}
      <div className="flex min-w-0 flex-1 flex-col bg-background">
        <header className="flex h-12 shrink-0 items-center justify-between gap-3 border-b px-4">
          <div className="flex min-w-0 items-center gap-2">
            <Button
              variant="ghost"
              size="icon-sm"
              className="md:hidden"
              onClick={() => setMobileListOpen(true)}
              aria-label="Show conversations"
            >
              <PanelLeft className="size-4" />
            </Button>
            <h2 className="truncate text-sm font-medium">
              {activeSession ? activeSession.title?.trim() || "New conversation" : "Intellex Assistant"}
            </h2>
            {activeSession?.is_pinned ? (
              <Pin className="size-3.5 shrink-0 text-muted-foreground" aria-label="Pinned" />
            ) : null}
          </div>
          {sendMutation.isPending ? (
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Loader2 className="size-3.5 animate-spin" />
              Thinking…
            </span>
          ) : null}
        </header>

        <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto">
          {activeId === null ? (
            <WelcomePane onPickSuggestion={setDraft} creating={createSessionMutation.isPending} />
          ) : messagesQuery.isLoading ? (
            <div className="mx-auto max-w-3xl space-y-6 p-6">
              {[0, 1].map((i) => (
                <div key={i} className="space-y-3">
                  <Skeleton className="ml-auto h-10 w-2/5 rounded-xl" />
                  <Skeleton className="h-24 w-full rounded-xl" />
                </div>
              ))}
            </div>
          ) : messagesQuery.isError ? (
            <div className="p-6">
              <ErrorState
                title="Could not load conversation"
                message={
                  messagesQuery.error instanceof Error ? messagesQuery.error.message : undefined
                }
                onRetry={() => messagesQuery.refetch()}
              />
            </div>
          ) : messages.length === 0 && !pendingQuestion ? (
            <div className="p-6">
              <EmptyState
                icon={MessagesSquare}
                title="Start the conversation"
                description="Ask about your organization's knowledge, documents, people, or teams."
              />
            </div>
          ) : (
            <div className="mx-auto max-w-3xl space-y-7 px-4 py-6 sm:px-6">
              {messages.map((message) => (
                <HistoryExchange key={message.chat_id} message={message} />
              ))}

              {pendingQuestion ? (
                <>
                  <UserBubble text={pendingQuestion.question} />
                  <AssistantThinking />
                </>
              ) : null}

              {sendFailure ? (
                <div
                  role="alert"
                  className="flex flex-col gap-2 rounded-lg border border-red-200 bg-red-50/70 p-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="flex items-start gap-2 text-sm text-red-800">
                    <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                    <span>{sendFailure.message}</span>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={sendMutation.isPending}
                    onClick={() =>
                      activeId !== null &&
                      sendMutation.mutate({
                        sessionId: activeId,
                        query: sendFailure.question,
                      })
                    }
                  >
                    <RefreshCcw className="size-3.5" />
                    Retry
                  </Button>
                </div>
              ) : null}
            </div>
          )}
        </div>

        {/* Composer */}
        <div className="shrink-0 border-t bg-card px-4 py-3 sm:px-6">
          <form
            className="mx-auto flex max-w-3xl items-end gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              handleSend();
            }}
          >
            <Textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  handleSend();
                }
              }}
              placeholder={
                activeId === null
                  ? "Create a chat to start asking questions…"
                  : "Ask Intellex anything… (Enter to send, Shift+Enter for a new line)"
              }
              rows={1}
              disabled={activeId === null || sendMutation.isPending}
              className="max-h-40 min-h-[42px] resize-none"
            />
            <Button
              type="submit"
              size="icon"
              disabled={activeId === null || !draft.trim() || sendMutation.isPending}
              aria-label="Send message"
            >
              {sendMutation.isPending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <SendHorizonal className="size-4" />
              )}
            </Button>
          </form>
          <p className="mx-auto mt-2 max-w-3xl text-center text-[11px] text-muted-foreground">
            Intellex answers are grounded in documents you can access and your
            organization&apos;s directory. Verify critical information independently.
          </p>
        </div>
      </div>

      {/* Rename dialog */}
      <Dialog open={renaming !== null} onOpenChange={(open) => !open && setRenaming(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Rename conversation</DialogTitle>
            <DialogDescription>Choose a clear name so you can find it later.</DialogDescription>
          </DialogHeader>
          <input
            value={renameValue}
            onChange={(event) => setRenameValue(event.target.value)}
            placeholder="e.g. Q3 policy review"
            maxLength={255}
            className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Conversation name"
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setRenaming(null)}>
              Cancel
            </Button>
            <Button
              disabled={updateSessionMutation.isPending}
              onClick={() => {
                if (!renaming) return;
                updateSessionMutation.mutate({
                  sessionId: renaming.session_id,
                  title: renameValue.trim(),
                });
              }}
            >
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation */}
      <Dialog open={deleting !== null} onOpenChange={(open) => !open && setDeleting(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Delete conversation?</DialogTitle>
            <DialogDescription>
              This permanently removes “{deleting?.title?.trim() || "New conversation"}” and its
              full history. This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleting(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={deleteSessionMutation.isPending}
              onClick={() => deleting && deleteSessionMutation.mutate(deleting.session_id)}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function UserBubble({ text }: { text: string }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[85%] whitespace-pre-wrap break-words rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-sm leading-relaxed text-white shadow-sm">
        {text}
      </div>
    </div>
  );
}

function AssistantThinking() {
  return (
    <div className="flex items-start gap-3">
      <AssistantAvatar />
      <div className="rounded-2xl rounded-tl-md border bg-card px-4 py-3 shadow-sm" aria-busy>
        <span className="flex items-center gap-1.5">
          {[0, 1, 2].map((dot) => (
            <span
              key={dot}
              className="size-1.5 animate-bounce rounded-full bg-muted-foreground/60"
              style={{ animationDelay: `${dot * 120}ms` }}
            />
          ))}
        </span>
      </div>
    </div>
  );
}

function AssistantAvatar() {
  return (
    <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-indigo-600 shadow-sm">
      <BrainCircuit className="size-4.5 text-white" />
    </span>
  );
}

function SourcesRow({ sources }: { sources: ChatSource[] }) {
  if (sources.length === 0) return null;

  return (
    <div className="mt-3 border-t pt-2.5">
      <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Sources
      </p>
      <ul className="flex flex-wrap gap-1.5">
        {sources.map((source) => (
          <li key={`${source.document_id}-${source.original_filename}`}>
            <Badge variant="outline" className="gap-1.5 bg-muted/50 font-normal">
              <FileText className="size-3 text-muted-foreground" />
              {source.original_filename}
              <span className="text-[10px] text-muted-foreground">#{source.document_id}</span>
            </Badge>
          </li>
        ))}
      </ul>
    </div>
  );
}

function HistoryExchange({ message }: { message: ChatHistoryMessage }) {
  return (
    <>
      <UserBubble text={message.question} />
      <div className="flex items-start gap-3">
        <AssistantAvatar />
        <div className="min-w-0 max-w-[92%] flex-1 rounded-2xl rounded-tl-md border bg-card px-4 py-3 shadow-sm">
          <MarkdownContent content={message.answer} />
          <SourcesRow sources={message.sources} />
          {message.feedback ? (
            <div className="mt-3 border-t pt-2.5">
              <Badge
                variant={
                  message.feedback === "Bad"
                    ? "destructive"
                    : message.feedback === "Good"
                      ? "success"
                      : "secondary"
                }
              >
                Feedback: {message.feedback}
              </Badge>
            </div>
          ) : null}
        </div>
      </div>
    </>
  );
}

function WelcomePane({
  onPickSuggestion,
  creating,
}: {
  onPickSuggestion: (value: string) => void;
  creating: boolean;
}) {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <div className="w-full max-w-xl text-center">
        <span className="mx-auto mb-5 flex size-12 items-center justify-center rounded-xl bg-indigo-600 shadow-md">
          <BrainCircuit className="size-6 text-white" />
        </span>
        <h2 className="text-xl font-semibold tracking-tight">Meet the Intellex Assistant</h2>
        <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
          Ask questions across your accessible documents, your organizational
          directory, or both at once. Answers cite their sources.
        </p>

        <div className="mt-7 grid gap-2 text-left sm:grid-cols-3">
          {SUGGESTIONS.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => onPickSuggestion(suggestion)}
              disabled={creating}
              className="rounded-lg border bg-card p-3 text-xs leading-relaxed text-muted-foreground shadow-sm transition-colors hover:border-indigo-300 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {suggestion}
            </button>
          ))}
        </div>

        {creating ? (
          <p className="mt-5 inline-flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="size-3.5 animate-spin" />
            Creating a new chat…
          </p>
        ) : (
          <p className="mt-5 text-xs text-muted-foreground">
            Select a conversation on the left, or press{" "}
            <kbd className="rounded border bg-muted px-1 py-0.5 font-mono text-[10px]">
              New chat
            </kbd>{" "}
            to begin.
          </p>
        )}
      </div>
    </div>
  );
}
