"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { formatDistanceToNowStrict } from "date-fns";
import {
  ArrowRight,
  FileText,
  MessagesSquare,
  Pin,
  Search,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/shared/states";
import { PageHeader } from "@/components/layout/page-header";
import { listMyDocuments } from "@/lib/api/documents";
import { listSessions } from "@/lib/api/chat";
import { useAuth } from "@/providers/auth-provider";

function StatCard({
  label,
  value,
  icon: Icon,
  href,
  linkLabel,
}: {
  label: string;
  value: number | string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
  linkLabel: string;
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <span className="flex size-9 items-center justify-center rounded-md bg-indigo-50 text-indigo-600">
            <Icon className="size-4.5" />
          </span>
          <span className="text-2xl font-semibold tabular-nums">{value}</span>
        </div>
        <p className="mt-3 text-sm font-medium">{label}</p>
        <Link
          href={href}
          className="mt-1 inline-flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-primary"
        >
          {linkLabel}
          <ArrowRight className="size-3" />
        </Link>
      </CardContent>
    </Card>
  );
}

export function EmployeeDashboard() {
  const { user } = useAuth();

  const documentsQuery = useQuery({
    queryKey: ["my-documents"],
    queryFn: listMyDocuments,
  });

  const sessionsQuery = useQuery({
    queryKey: ["chat", "sessions"],
    queryFn: listSessions,
  });

  const sessions = sessionsQuery.data?.sessions ?? [];
  const recentSessions = sessions.slice(0, 5);

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6 lg:p-8">
      <PageHeader
        title={`Welcome back, ${user?.name.split(" ")[0] ?? "there"}`}
        description="Your personal Intellex workspace."
      />

      <section aria-label="Overview">
        {documentsQuery.isError || sessionsQuery.isError ? (
          <ErrorState
            title="Some workspace data could not be loaded"
            onRetry={() => {
              void documentsQuery.refetch();
              void sessionsQuery.refetch();
            }}
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {documentsQuery.isLoading ? (
              <Skeleton className="h-[132px]" />
            ) : (
              <StatCard
                label="Accessible documents"
                value={documentsQuery.data?.length ?? 0}
                icon={FileText}
                href="/employee/documents"
                linkLabel="Browse documents"
              />
            )}
            {sessionsQuery.isLoading ? (
              <Skeleton className="h-[132px]" />
            ) : (
              <StatCard
                label="Conversations"
                value={sessions.length}
                icon={MessagesSquare}
                href="/chat"
                linkLabel="Open chat"
              />
            )}
            {/* <StatCard
              label="Retrieval testing"
              value="Run"
              icon={Search}
              href="/employee/retrieval"
              linkLabel="Open playground"
            /> */}
          </div>
        )}
      </section>

      <section className="grid gap-4 lg:grid-cols-2" aria-label="Recent activity">
        <Card>
          <CardHeader className="flex-row items-start justify-between space-y-0">
            <div>
              <CardTitle className="text-base">Recent conversations</CardTitle>
              <CardDescription>Continue where you left off.</CardDescription>
            </div>
            <Button asChild variant="outline" size="sm">
              <Link href="/chat">
                New chat
                <ArrowRight className="size-3.5" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {sessionsQuery.isLoading ? (
              <div className="space-y-2">
                {[0, 1, 2].map((i) => (
                  <Skeleton key={i} className="h-11" />
                ))}
              </div>
            ) : recentSessions.length === 0 ? (
              <p className="rounded-lg border border-dashed px-4 py-8 text-center text-sm text-muted-foreground">
                No conversations yet. Start your first chat.
              </p>
            ) : (
              <ul className="divide-y">
                {recentSessions.map((session) => (
                  <li key={session.session_id}>
                    <Link
                      href="/chat"
                      className="flex items-center gap-3 py-2.5 transition-colors hover:text-primary"
                    >
                      <span className="min-w-0 flex-1 truncate text-sm font-medium">
                        {session.title?.trim() || "New conversation"}
                      </span>
                      {session.is_pinned ? (
                        <Pin className="size-3.5 shrink-0 text-muted-foreground" />
                      ) : null}
                      <span className="shrink-0 text-xs text-muted-foreground">
                        {formatDistanceToNowStrict(new Date(session.last_active), {
                          addSuffix: true,
                        })}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Quick start</CardTitle>
            <CardDescription>Jump straight into a task.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-2.5">
            <Button asChild variant="secondary" className="justify-start">
              <Link href="/chat">
                <MessagesSquare />
                Ask Intellex a question
              </Link>
            </Button>
            <Button asChild variant="secondary" className="justify-start">
              <Link href="/employee/documents">
                <FileText />
                Find a document
              </Link>
            </Button>
            {/* <Button asChild variant="secondary" className="justify-start">
              <Link href="/employee/retrieval">
                <Search />
                Inspect retrieval quality
              </Link>
            </Button> */}
            <div className="mt-2 rounded-lg border bg-muted/40 p-3 text-xs leading-relaxed text-muted-foreground">
              Your access is managed by your organization administrator.
              Documents outside your permissions never appear in results or answers.
            </div>
          </CardContent>
        </Card>
      </section>

      <p className="text-center text-xs text-muted-foreground">
        Signed in as{" "}
        <Badge variant="secondary" className="mx-0.5">
          Employee
        </Badge>{" "}
        workspace · Intellex enforces all permissions server-side.
      </p>
    </div>
  );
}
