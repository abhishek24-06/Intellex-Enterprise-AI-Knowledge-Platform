"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { FileText, RefreshCcw, Search, Upload } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { EmptyState, ErrorState, LoadingBlock } from "@/components/shared/states";
import { PageHeader } from "@/components/layout/page-header";
import { listMyDocuments } from "@/lib/api/documents";
import { formatDate } from "@/lib/utils";
import type { DocumentResponse, DocumentStatus, DocumentType, DocumentVisibility } from "@/types/api";

export const STATUS_BADGE: Record<DocumentStatus, { label: string; variant: "success" | "warning" | "destructive" | "secondary" }> = {
  READY: { label: "Ready", variant: "success" },
  PROCESSING: { label: "Processing", variant: "warning" },
  UPLOADING: { label: "Uploading", variant: "warning" },
  FAILED: { label: "Failed", variant: "destructive" },
  ARCHIVED: { label: "Archived", variant: "secondary" },
};

export const TYPE_LABELS: Record<DocumentType, string> = {
  HR_POLICY: "HR Policy",
  SOP: "SOP",
  TECHNICAL: "Technical",
  MEETING_NOTE: "Meeting Note",
  REPORT: "Report",
};

export function VisibilityBadge({ visibility }: { visibility: DocumentVisibility }) {
  return visibility === "ORGANIZATION" ? (
    <Badge variant="info">Organization</Badge>
  ) : (
    <Badge variant="warning">Restricted</Badge>
  );
}

/**
 * Documents the authenticated user can access.
 * The backend resolves ACL permissions server-side — the frontend only
 * renders what the API returns for the current user.
 */
export function MyDocumentsView({ headerAction }: { headerAction?: React.ReactNode }) {
  const [query, setQuery] = React.useState("");
  const [selected, setSelected] = React.useState<DocumentResponse | null>(null);

  const documentsQuery = useQuery({
    queryKey: ["my-documents"],
    queryFn: listMyDocuments,
  });

  const documents = React.useMemo(
    () => documentsQuery.data ?? [],
    [documentsQuery.data],
  );
  const normalized = query.trim().toLowerCase();

  const filtered = React.useMemo(() => {
    if (!normalized) return documents;
    return documents.filter(
      (doc) =>
        doc.title.toLowerCase().includes(normalized) ||
        doc.original_filename.toLowerCase().includes(normalized),
    );
  }, [documents, normalized]);

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6 lg:p-8">
      <PageHeader
        title="My Documents"
        description="Documents you are authorized to access. Permissions are enforced by the platform."
        actions={
          <>
            {headerAction}
            <Button
              variant="outline"
              size="sm"
              onClick={() => documentsQuery.refetch()}
              disabled={documentsQuery.isFetching}
            >
              <RefreshCcw className={documentsQuery.isFetching ? "animate-spin" : undefined} />
              Refresh
            </Button>
          </>
        }
      />

      {documentsQuery.isLoading ? (
        <LoadingBlock label="Loading your documents…" />
      ) : documentsQuery.isError ? (
        <ErrorState
          title="Could not load documents"
          message={
            documentsQuery.error instanceof Error ? documentsQuery.error.message : undefined
          }
          onRetry={() => documentsQuery.refetch()}
        />
      ) : documents.length === 0 ? (
        <EmptyState
          icon={Upload}
          title="No accessible documents yet"
          description="Documents shared with you or your organization will appear here once uploaded by an administrator."
        />
      ) : (
        <>
          <div className="relative max-w-sm">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by title or filename…"
              className="pl-8"
              aria-label="Search documents"
            />
          </div>

          {filtered.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="No matches"
              description={`No documents match “${query}”.`}
            />
          ) : (
            <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {filtered.map((doc) => (
                <li key={doc.document_id}>
                  <button
                    type="button"
                    onClick={() => setSelected(doc)}
                    className="group flex h-full w-full flex-col rounded-lg border bg-card p-4 text-left shadow-sm transition-all hover:border-indigo-300 hover:shadow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-indigo-50 text-indigo-600">
                      <FileText className="size-4.5" />
                    </span>
                    <p className="mt-3 line-clamp-2 text-sm font-medium leading-snug group-hover:text-primary">
                      {doc.title}
                    </p>
                    <p className="mt-0.5 truncate text-xs text-muted-foreground">
                      {doc.original_filename}
                    </p>
                    <div className="mt-auto pt-3">
                      <Badge variant="secondary">{TYPE_LABELS[doc.document_type]}</Badge>
                    </div>
                    <p className="mt-2 text-[11px] text-muted-foreground">
                      Uploaded {formatDate(doc.uploaded_at)}
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </>
      )}

      {/* Document details */}
      <Dialog open={selected !== null} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent>
          {selected ? (
            <>
              <DialogHeader>
                <DialogTitle>{selected.title}</DialogTitle>
                <DialogDescription>
                  Document #{selected.document_id} · {selected.original_filename}
                </DialogDescription>
              </DialogHeader>
              {selected.description ? (
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {selected.description}
                </p>
              ) : null}
              <dl className="grid grid-cols-2 gap-x-4 gap-y-3 rounded-lg border bg-muted/40 p-4 text-sm">
                <Detail label="Type" value={TYPE_LABELS[selected.document_type]} />
                {/* <Detail label="Status" value={STATUS_BADGE[selected.status].label} /> */}
                {/* <Detail label="Visibility" value={<VisibilityBadge visibility={selected.visibility} />} /> */}
                <Detail label="Uploaded" value={formatDate(selected.uploaded_at)} />
                {/* <Detail label="Uploader ID" value={`#${selected.uploaded_by}`} /> */}
                {/* <Detail label="Organization" value={`#${selected.organization_id}`} /> */}
              </dl>
            </>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function Detail({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </dt>
      <dd className="mt-0.5">{value}</dd>
    </div>
  );
}
