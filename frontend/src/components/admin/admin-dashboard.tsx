"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  FileText,
  FolderKanban,
  Gauge,
  MessagesSquare,
  Network,
  Search,
  UserPlus,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/shared/states";
import { PageHeader } from "@/components/layout/page-header";
import { listDocuments } from "@/lib/api/documents";
import { listUsers } from "@/lib/api/users";

function StatTile({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: number | string;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-5">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-md bg-indigo-50 text-indigo-600">
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

const QUICK_ACTIONS = [
  {
    label: "Create employee",
    description: "Provision an account in a department and team.",
    href: "/admin/users",
    icon: UserPlus,
  },
  {
    label: "Upload document",
    description: "Publish organization-wide or restricted knowledge.",
    href: "/admin/documents",
    icon: FileText,
  },
  {
    label: "Create department",
    description: "Structure your organization.",
    href: "/admin/departments",
    icon: FolderKanban,
  },
  {
    label: "Inspect observability",
    description: "Agent executions, latency, retries, routes.",
    href: "/admin/observability",
    icon: Gauge,
  },
];

export function AdminDashboard() {
  const usersQuery = useQuery({ queryKey: ["users"], queryFn: listUsers });
  const documentsQuery = useQuery({ queryKey: ["documents"], queryFn: listDocuments });

  const anyError = usersQuery.isError || documentsQuery.isError;

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6 lg:p-8">
      <PageHeader
        title="Organization Overview"
        description="Manage your organization's people, structure, knowledge, and AI operations."
        actions={
          <Button asChild size="sm">
            <Link href="/chat">
              <MessagesSquare className="size-4" />
              Open Chat
            </Link>
          </Button>
        }
      />

      {anyError ? (
        <ErrorState
          title="Some organization data could not be loaded"
          message={
            usersQuery.isError && usersQuery.error instanceof Error
              ? usersQuery.error.message
              : undefined
          }
          onRetry={() => {
            void usersQuery.refetch();
            void documentsQuery.refetch();
          }}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {usersQuery.isLoading ? (
            <Skeleton className="h-[86px]" />
          ) : (
            <StatTile
              label={`Active ${usersQuery.data?.length === 1 ? "user" : "users"} in your organization`}
              value={usersQuery.data?.length ?? 0}
              icon={Users}
            />
          )}
          {documentsQuery.isLoading ? (
            <Skeleton className="h-[86px]" />
          ) : (
            <StatTile
              label="Organization documents"
              value={documentsQuery.data?.length ?? 0}
              icon={FileText}
            />
          )}
          <StatTile label="Teams & structure" value="Manage" icon={Network} />
          <StatTile label="AI operations" value="Monitor" icon={Gauge} />
        </div>
      )}

      <section aria-label="Quick actions">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Quick actions
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {QUICK_ACTIONS.map((action) => (
            <Link key={action.href} href={action.href}>
              <Card className="h-full transition-all hover:border-indigo-300 hover:shadow">
                <CardContent className="p-5">
                  <span className="flex size-9 items-center justify-center rounded-md bg-indigo-50 text-indigo-600">
                    <action.icon className="size-4.5" />
                  </span>
                  <p className="mt-3 flex items-center gap-1 text-sm font-medium">
                    {action.label}
                    <ArrowRight className="size-3.5 opacity-0 transition-opacity group-hover:opacity-100" />
                  </p>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                    {action.description}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Knowledge base</CardTitle>
            <CardDescription>
              Organization documents are available to every employee; restricted
              documents honor their access-control entries only.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline" size="sm">
              <Link href="/admin/documents">
                Manage documents
                <ArrowRight className="size-3.5" />
              </Link>
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Retrieval diagnostics</CardTitle>
            <CardDescription>
              Verify what the pipeline retrieves for specific queries before your
              employees ever see an answer.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline" size="sm">
              <Link href="/admin/retrieval">
                <Search className="size-3.5" />
                Open playground
              </Link>
            </Button>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
