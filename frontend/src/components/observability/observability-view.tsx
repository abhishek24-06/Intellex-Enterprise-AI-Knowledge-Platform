"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  GitBranch,
  RefreshCcw,
  Search,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { PageHeader } from "@/components/layout/page-header";
import { getChatTrace, getObservabilitySummary } from "@/lib/api/observability";
import { formatDateTime, formatLatency } from "@/lib/utils";
import type { AgentExecution } from "@/types/api";

const WINDOWS = [
  { label: "Last 24h", hours: 24 },
  { label: "Last 3 days", hours: 72 },
  { label: "Last 7 days", hours: 168 },
  { label: "Last 30 days", hours: 720 },
];

const ROUTE_BAR_COLORS = [
  "bg-indigo-500",
  "bg-cyan-600",
  "bg-emerald-600",
  "bg-amber-600",
  "bg-red-500",
];

function SummaryCard({
  label,
  value,
  icon: Icon,
  tone = "default",
}: {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  tone?: "default" | "success" | "warning" | "destructive";
}) {
  const tones = {
    default: "bg-indigo-50 text-indigo-600",
    success: "bg-emerald-50 text-emerald-700",
    warning: "bg-amber-50 text-amber-700",
    destructive: "bg-red-50 text-red-600",
  } as const;

  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-5">
        <span className={`flex size-10 shrink-0 items-center justify-center rounded-md ${tones[tone]}`}>
          <Icon className="size-5" />
        </span>
        <div className="min-w-0">
          <p className="text-xl font-semibold tabular-nums leading-none">{value}</p>
          <p className="mt-1 truncate text-xs text-muted-foreground">{label}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function ExecutionRow({ execution }: { execution: AgentExecution }) {
  const detailEntries = Object.entries(execution.details ?? {});

  return (
    <TableRow>
      <TableCell className="whitespace-nowrap">
        <span className="font-mono font-medium">{execution.agent_name}</span>
      </TableCell>
      <TableCell>
        {execution.route ? (
          <Badge variant="info">{execution.route}</Badge>
        ) : (
          <span className="text-xs text-muted-foreground">—</span>
        )}
      </TableCell>
      <TableCell className="font-mono text-sm">#{execution.attempt}</TableCell>
      <TableCell>
        {execution.status.toLowerCase() === "success" || execution.status.toLowerCase() === "succeeded" ? (
          <Badge variant="success">{execution.status}</Badge>
        ) : (
          <Badge variant={execution.status.toLowerCase() === "failed" ? "destructive" : "secondary"}>
            {execution.status}
          </Badge>
        )}
      </TableCell>
      <TableCell className="font-mono text-sm tabular-nums">
        {formatLatency(execution.latency_ms)}
      </TableCell>
      <TableCell className="hidden font-mono text-xs text-muted-foreground lg:table-cell">
        {execution.request_id.slice(0, 8)}…
      </TableCell>
      <TableCell className="hidden whitespace-nowrap text-xs text-muted-foreground xl:table-cell">
        {formatDateTime(execution.created_at)}
      </TableCell>
      <TableCell>
        {detailEntries.length > 0 ? (
          <details className="group">
            <summary className="cursor-pointer list-none text-xs font-medium text-primary hover:underline focus-visible:outline-none">
              Metadata ({detailEntries.length})
            </summary>
            <div className="mt-1 flex flex-wrap gap-1">
              {detailEntries.map(([key, value]) => (
                <code
                  key={key}
                  className="rounded border bg-muted px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground"
                >
                  {key}: {typeof value === "object" ? JSON.stringify(value) : String(value)}
                </code>
              ))}
            </div>
          </details>
        ) : (
          <span className="text-xs text-muted-foreground">—</span>
        )}
      </TableCell>
    </TableRow>
  );
}

export function ObservabilityView() {
  const [windowHours, setWindowHours] = React.useState(24);
  const [traceChatIdInput, setTraceChatIdInput] = React.useState("");
  const [traceChatId, setTraceChatId] = React.useState<number | null>(null);

  const summaryQuery = useQuery({
    queryKey: ["observability", "summary", windowHours],
    queryFn: () => getObservabilitySummary(windowHours),
  });

  const traceQuery = useQuery({
    queryKey: ["observability", "trace", traceChatId],
    queryFn: () => getChatTrace(traceChatId as number),
    enabled: traceChatId !== null,
  });

  function onSubmitTrace(event: React.FormEvent) {
    event.preventDefault();
    const parsed = Number(traceChatIdInput.replace(/\D/g, ""));
    if (Number.isFinite(parsed) && parsed > 0) setTraceChatId(parsed);
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6 lg:p-8">
      <PageHeader
        title="AI Observability"
        description="Operational metrics for the agentic RAG pipeline — safe execution metadata only."
        actions={
          <Tabs value={String(windowHours)} onValueChange={(value) => setWindowHours(Number(value))}>
            <TabsList>
              {WINDOWS.map((w) => (
                <TabsTrigger key={w.hours} value={String(w.hours)}>
                  {w.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        }
      />

      {/* Summary */}
      {summaryQuery.isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-[86px]" />
          ))}
        </div>
      ) : summaryQuery.isError ? (
        <ErrorState
          title="Could not load observability summary"
          message={
            summaryQuery.error instanceof Error
              ? summaryQuery.error.message
              : "This area requires organization administrator privileges."
          }
          onRetry={() => summaryQuery.refetch()}
        />
      ) : summaryQuery.data ? (
        (() => {
          const s = summaryQuery.data;
          return (
            <>
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <SummaryCard label="Total executions" value={s.total_executions.toLocaleString()} icon={Activity} />
                <SummaryCard
                  label="Successful"
                  value={s.successful_executions.toLocaleString()}
                  icon={CheckCircle2}
                  tone="success"
                />
                <SummaryCard
                  label="Failed"
                  value={s.failed_executions.toLocaleString()}
                  icon={AlertTriangle}
                  tone="destructive"
                />
                <SummaryCard
                  label="Average latency"
                  value={formatLatency(s.average_latency_ms)}
                  icon={Clock}
                />
                <SummaryCard label="Retries" value={`${s.retry_count.toLocaleString()} (${(s.retry_rate * 100).toFixed(1)}%)`} icon={RefreshCcw} />
                <SummaryCard
                  label="Critic accepted"
                  value={s.critic_accept_count.toLocaleString()}
                  icon={CheckCircle2}
                />
                <SummaryCard
                  label="Critic retries requested"
                  value={s.critic_retry_count.toLocaleString()}
                  icon={RefreshCcw}
                />
                <SummaryCard
                  label="Critic acceptance rate"
                  value={`${(s.critic_acceptance_rate * 100).toFixed(1)}%`}
                  icon={GitBranch}
                />
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Agent latency</CardTitle>
                    <CardDescription>Average, minimum and maximum per agent.</CardDescription>
                  </CardHeader>
                  <CardContent className="px-0 pb-0 [&_table]:border-t">
                    {s.agent_latency.length === 0 ? (
                      <EmptyState
                        className="m-5 border-0 py-8"
                        title="No agent activity recorded in this window"
                      />
                    ) : (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Agent</TableHead>
                            <TableHead>Executions</TableHead>
                            <TableHead>Avg</TableHead>
                            <TableHead>Min</TableHead>
                            <TableHead>Max</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {s.agent_latency.map((row) => (
                            <TableRow key={row.agent_name}>
                              <TableCell className="font-mono text-sm font-medium">{row.agent_name}</TableCell>
                              <TableCell className="tabular-nums">{row.execution_count}</TableCell>
                              <TableCell className="tabular-nums">{formatLatency(row.average_latency_ms)}</TableCell>
                              <TableCell className="tabular-nums text-muted-foreground">
                                {formatLatency(row.min_latency_ms)}
                              </TableCell>
                              <TableCell className="tabular-nums text-muted-foreground">
                                {formatLatency(row.max_latency_ms)}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Routes taken</CardTitle>
                    <CardDescription>Distribution of orchestrator routing decisions.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3.5">
                    {s.routes.length === 0 ? (
                      <EmptyState
                        className="border-0 py-8"
                        title="No routed requests in this window"
                      />
                    ) : (
                      (() => {
                        const maxCount = Math.max(...s.routes.map((r) => r.execution_count));
                        return s.routes.map((route, index) => (
                          <div key={route.route}>
                            <div className="mb-1 flex items-center justify-between text-sm">
                              <span className="font-medium">{route.route}</span>
                              <span className="tabular-nums text-muted-foreground">
                                {route.execution_count.toLocaleString()}
                              </span>
                            </div>
                            <div className="h-2 overflow-hidden rounded-full bg-muted" role="presentation">
                              <div
                                className={`h-full rounded-full ${ROUTE_BAR_COLORS[index % ROUTE_BAR_COLORS.length]}`}
                                style={{
                                  width: `${Math.max((route.execution_count / maxCount) * 100, 2)}%`,
                                }}
                              />
                            </div>
                          </div>
                        ));
                      })()
                    )}
                  </CardContent>
                </Card>
              </div>
            </>
          );
        })()
      ) : null}

      {/* Chat trace */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Chat execution trace</CardTitle>
          <CardDescription>
            Inspect every agent execution recorded for a specific chat message ID.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={onSubmitTrace} className="flex max-w-md items-center gap-2">
            <Input
              inputMode="numeric"
              value={traceChatIdInput}
              onChange={(event) => setTraceChatIdInput(event.target.value.replace(/\D/g, ""))}
              placeholder="Enter chat ID (e.g. 42)"
              aria-label="Chat ID"
            />
            <Button type="submit" disabled={!traceChatIdInput.trim()}>
              <Search />
              Trace
            </Button>
          </form>

          {traceChatId === null ? (
            <p className="rounded-lg border border-dashed px-4 py-8 text-center text-sm text-muted-foreground">
              Enter a chat ID to load its execution timeline.
            </p>
          ) : traceQuery.isLoading ? (
            <LoadingBlock label="Loading trace…" />
          ) : traceQuery.isError ? (
            <ErrorState
              title={`No trace found for chat #${traceChatId}`}
              message={
                traceQuery.error instanceof Error ? traceQuery.error.message : undefined
              }
            />
          ) : traceQuery.data && traceQuery.data.executions.length === 0 ? (
            <EmptyState title="No executions recorded for this chat" description="The chat may predate observability instrumentation." />
          ) : traceQuery.data ? (
            <div className="rounded-lg border bg-card">
              <div className="flex items-center justify-between border-b px-4 py-2.5">
                <p className="text-sm font-medium">Chat #{traceQuery.data.chat_id}</p>
                <Badge variant="secondary">
                  {traceQuery.data.execution_count} execution{traceQuery.data.execution_count === 1 ? "" : "s"}
                </Badge>
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Agent</TableHead>
                    <TableHead>Route</TableHead>
                    <TableHead>Attempt</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Latency</TableHead>
                    <TableHead className="hidden lg:table-cell">Request</TableHead>
                    <TableHead className="hidden xl:table-cell">Recorded</TableHead>
                    <TableHead>Metadata</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {traceQuery.data.executions.map((execution) => (
                    <ExecutionRow key={execution.execution_id} execution={execution} />
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}

function LoadingBlock({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-12" aria-busy>
      <span className="size-5 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
      <p className="text-sm text-muted-foreground">{label}</p>
    </div>
  );
}
