"use client";

import * as React from "react";
import { formatDistanceToNowStrict } from "date-fns";
import {
  MessageSquarePlus,
  MoreHorizontal,
  Pencil,
  Pin,
  PinOff,
  Search,
  Trash2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import type { ChatSession } from "@/types/api";

interface SessionSidebarProps {
  sessions: ChatSession[] | undefined;
  isLoading: boolean;
  activeSessionId: number | null;
  onSelect: (sessionId: number) => void;
  onNewChat: () => void;
  onCreateDisabled?: boolean;
  onRename: (session: ChatSession) => void;
  onDelete: (session: ChatSession) => void;
  onTogglePin: (session: ChatSession) => void;
}

function SessionRow({
  session,
  active,
  onSelect,
  onRename,
  onDelete,
  onTogglePin,
}: {
  session: ChatSession;
  active: boolean;
  onSelect: () => void;
  onRename: () => void;
  onDelete: () => void;
  onTogglePin: () => void;
}) {
  return (
    <div
      className={active ? "group relative rounded-md bg-sidebar-active" : "group relative rounded-md hover:bg-sidebar-accent"}
    >
      <button
        type="button"
        onClick={onSelect}
        className="flex w-full items-center gap-2 px-2.5 py-2 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        aria-current={active ? "true" : undefined}
      >
        <span className="min-w-0 flex-1">
          <span
            className={
              "block truncate text-sm font-medium " +
              (active ? "text-white" : "text-sidebar-foreground")
            }
          >
            {session.title?.trim() || "New conversation"}
          </span>
          <span className="mt-0.5 block truncate text-xs text-sidebar-muted">
            Active {formatDistanceToNowStrict(new Date(session.last_active), { addSuffix: true })}
          </span>
        </span>
        {session.is_pinned ? <Pin className="size-3.5 shrink-0 text-indigo-400" /> : null}
      </button>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon-sm"
            className={cn(
              "absolute right-1 top-1/2 -translate-y-1/2 opacity-0 transition-opacity group-hover:opacity-100 data-[state=open]:opacity-100",
              "text-sidebar-muted hover:bg-black/30 hover:text-white",
            )}
            aria-label={`Actions for ${session.title ?? "conversation"}`}
          >
            <MoreHorizontal className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" side="right">
          <DropdownMenuItem onSelect={onRename}>
            <Pencil />
            Rename
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={onTogglePin}>
            {session.is_pinned ? (
              <>
                <PinOff />
                Unpin
              </>
            ) : (
              <>
                <Pin />
                Pin
              </>
            )}
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem destructive onSelect={onDelete}>
            <Trash2 />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}

export function SessionSidebar({
  sessions,
  isLoading,
  activeSessionId,
  onSelect,
  onNewChat,
  onCreateDisabled,
  onRename,
  onDelete,
  onTogglePin,
}: SessionSidebarProps) {
  const [query, setQuery] = React.useState("");

  const normalizedQuery = query.trim().toLowerCase();
  const { pinned, recent } = React.useMemo(() => {
    if (!sessions) return { pinned: [] as ChatSession[], recent: [] as ChatSession[] };
    const list = normalizedQuery
      ? sessions.filter((s) => (s.title ?? "").toLowerCase().includes(normalizedQuery))
      : sessions;
    return {
      pinned: list.filter((s) => s.is_pinned),
      recent: list.filter((s) => !s.is_pinned),
    };
  }, [sessions, normalizedQuery]);

  function renderRows(rows: ChatSession[]) {
    return rows.map((session) => (
      <SessionRow
        key={session.session_id}
        session={session}
        active={session.session_id === activeSessionId}
        onSelect={() => onSelect(session.session_id)}
        onRename={() => onRename(session)}
        onDelete={() => onDelete(session)}
        onTogglePin={() => onTogglePin(session)}
      />
    ));
  }

  const hasAny = pinned.length > 0 || recent.length > 0;

  return (
    <div className="flex h-full flex-col border-r border-sidebar-border bg-sidebar">
      <div className="space-y-2.5 p-3">
        <Button
          onClick={onNewChat}
          disabled={onCreateDisabled}
          className="w-full justify-start gap-2"
        >
          <MessageSquarePlus />
          New chat
        </Button>
        <div className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-sidebar-muted" />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search chats…"
            className="h-8 border-sidebar-border bg-sidebar-accent pl-8 text-sidebar-foreground placeholder:text-sidebar-muted focus-visible:ring-ring"
          />
        </div>
      </div>

      <div className="min-h-0 flex-1 space-y-1 overflow-y-auto px-3 pb-4">
        {isLoading ? (
          <div className="space-y-2 pt-1">
            {Array.from({ length: 6 }).map((_, index) => (
              <Skeleton key={index} className="h-12 bg-sidebar-accent" />
            ))}
          </div>
        ) : !hasAny ? (
          <p className="px-2 py-6 text-center text-xs text-sidebar-muted">
            {normalizedQuery ? "No chats match your search." : "No conversations yet."}
          </p>
        ) : (
          <>
            {pinned.length > 0 ? (
              <div className="space-y-1">
                <p className="px-2 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-wider text-sidebar-muted">
                  Pinned
                </p>
                {renderRows(pinned)}
              </div>
            ) : null}
            {recent.length > 0 ? (
              <div className="space-y-1">
                <p className="px-2 pb-1 pt-3 text-[11px] font-semibold uppercase tracking-wider text-sidebar-muted">
                  Recent
                </p>
                {renderRows(recent)}
              </div>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}
