"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  EllipsisVertical,
  Eye,
  FileText,
  Lock,
  Search,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { EmptyState, ErrorState, LoadingBlock } from "@/components/shared/states";
import { PageHeader } from "@/components/layout/page-header";
import { deleteDocument, listDocuments, uploadDocument } from "@/lib/api/documents";
import { formatDate, formatDateTime } from "@/lib/utils";
import type {
  DocumentResponse,
  DocumentType,
  DocumentVisibility,
  PrincipalType,
} from "@/types/api";

const TYPE_OPTIONS: { value: DocumentType; label: string }[] = [
  { value: "HR_POLICY", label: "HR Policy" },
  { value: "SOP", label: "Standard Operating Procedure" },
  { value: "TECHNICAL", label: "Technical" },
  { value: "MEETING_NOTE", label: "Meeting Note" },
  { value: "REPORT", label: "Report" },
];

const PRINCIPAL_OPTIONS: { value: PrincipalType; label: string; needsId: boolean }[] = [
  { value: "USER", label: "User", needsId: true },
  { value: "TEAM", label: "Team", needsId: true },
  { value: "DEPARTMENT", label: "Department", needsId: true },
  { value: "ORG_ADMIN", label: "All Org Admins", needsId: false },
];

const ACCEPTED_EXTENSIONS = [".pdf", ".txt", ".docx", ".md"];
const MAX_FILE_BYTES = 50 * 1024 * 1024;

interface PermissionRow {
  key: number;
  principal_type: PrincipalType;
  /** Stored as a raw digit-string while editing; converted to a number on submit. */
  principalIdText: string;
}

interface UploadFormState {
  title: string;
  description: string;
  documentType: DocumentType | "";
  visibility: DocumentVisibility | "";
  file: File | null;
}

const EMPTY_UPLOAD: UploadFormState = {
  title: "",
  description: "",
  documentType: "",
  visibility: "",
  file: null,
};

export function DocumentsAdminView() {
  const queryClient = useQueryClient();

  const [query, setQuery] = React.useState("");
  const [viewing, setViewing] = React.useState<DocumentResponse | null>(null);
  const [deleting, setDeleting] = React.useState<DocumentResponse | null>(null);
  const [uploadOpen, setUploadOpen] = React.useState(false);
  const [form, setForm] = React.useState<UploadFormState>(EMPTY_UPLOAD);
  const [permissions, setPermissions] = React.useState<PermissionRow[]>([]);
  const [uploadError, setUploadError] = React.useState<string | null>(null);
  const nextKey = React.useRef(1);

  const documentsQuery = useQuery({ queryKey: ["documents"], queryFn: listDocuments });

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!form.documentType || !form.visibility || !form.file) {
        throw new Error("Complete all required fields before uploading.");
      }
      return uploadDocument(
        {
          title: form.title.trim(),
          description: form.description.trim() || null,
          document_type: form.documentType,
          visibility: form.visibility,
          permissions:
            form.visibility === "RESTRICTED"
              ? permissions.map((row) => ({
                  principal_type: row.principal_type,
                  principal_id:
                    row.principal_type === "ORG_ADMIN" || row.principalIdText === ""
                      ? null
                      : Number(row.principalIdText),
                }))
              : [],
        },
        form.file,
      );
    },
    onSuccess: (document) => {
      void queryClient.invalidateQueries({ queryKey: ["documents"] });
      void queryClient.invalidateQueries({ queryKey: ["my-documents"] });
      toast.success(`“${document.title}” uploaded and queued for processing.`);
      closeUpload();
    },
    onError: (error) => setUploadError(error.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (documentId: number) => deleteDocument(documentId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["documents"] });
      await queryClient.invalidateQueries({ queryKey: ["my-documents"] });
      setDeleting(null);
      toast.success("Document deleted");
    },
    onError: (error) => toast.error(error.message),
  });

  function openUpload() {
    setForm(EMPTY_UPLOAD);
    setPermissions([]);
    setUploadError(null);
    setUploadOpen(true);
  }

  function closeUpload() {
    setUploadOpen(false);
    setForm(EMPTY_UPLOAD);
    setPermissions([]);
    setUploadError(null);
  }

  function addPermissionRow() {
    setPermissions((rows) => [
      ...rows,
      { key: nextKey.current++, principal_type: "USER", principalIdText: "" },
    ]);
  }

  function validateUpload(): string | null {
    if (!form.title.trim()) return "Title is required.";
    if (!form.documentType) return "Select a document type.";
    if (!form.visibility) return "Select a visibility level.";
    if (!form.file) return "Choose a file to upload.";

    const extension = `.${form.file.name.split(".").pop()?.toLowerCase() ?? ""}`;
    if (!ACCEPTED_EXTENSIONS.includes(extension)) {
      return `Unsupported file type. Accepted: ${ACCEPTED_EXTENSIONS.join(", ")}`;
    }
    if (form.file.size > MAX_FILE_BYTES) {
      return "File exceeds the 50 MB limit.";
    }
    if (form.visibility === "RESTRICTED") {
      for (const row of permissions) {
        if (row.principal_type !== "ORG_ADMIN" && row.principalIdText === "") {
          return `Enter an ID for the ${row.principal_type.toLowerCase()} access entry.`;
        }
      }
    }
    return null;
  }

  const documents = documentsQuery.data ?? [];
  const normalized = query.trim().toLowerCase();
  const filtered = normalized
    ? documents.filter(
        (doc) =>
          doc.title.toLowerCase().includes(normalized) ||
          doc.original_filename.toLowerCase().includes(normalized),
      )
    : documents;

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6 lg:p-8">
      <PageHeader
        title="Organization Documents"
        description="Manage the organization's knowledge base and access-control entries."
        actions={
          <Button size="sm" onClick={openUpload}>
            <Upload />
            Upload document
          </Button>
        }
      />

      {documentsQuery.isLoading ? (
        <div className="space-y-2">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-12" />
          ))}
        </div>
      ) : documentsQuery.isError ? (
        <ErrorState
          title="Could not load documents"
          message={
            documentsQuery.error instanceof Error ? documentsQuery.error.message : undefined
          }
          onRetry={() => documentsQuery.refetch()}
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
              title={documents.length === 0 ? "No documents yet" : "No matches"}
              description={
                documents.length === 0
                  ? "Upload your first document to make it available to the AI assistant."
                  : "No documents match your search."
              }
              action={
                documents.length === 0 ? (
                  <Button size="sm" onClick={openUpload}>
                    <Upload />
                    Upload document
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <div className="rounded-lg border bg-card shadow-sm">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Document</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Visibility</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Uploader</TableHead>
                    <TableHead>Uploaded</TableHead>
                    <TableHead>ID</TableHead>
                    <TableHead className="w-12"><span className="sr-only">Actions</span></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map((doc) => (
                    <TableRow key={doc.document_id}>
                      <TableCell>
                        <p className="max-w-[220px] truncate font-medium">{doc.title}</p>
                        <p className="max-w-[220px] truncate text-xs text-muted-foreground">
                          {doc.original_filename}
                        </p>
                      </TableCell>
                      <TableCell className="text-sm">{TYPE_LABEL(doc.document_type)}</TableCell>
                      <TableCell>
                        {doc.visibility === "ORGANIZATION" ? (
                          <Badge variant="info">Organization</Badge>
                        ) : (
                          <Badge variant="warning">
                            <Lock className="size-3" />
                            Restricted
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={doc.status} />
                      </TableCell>
                      <TableCell className="font-mono text-sm text-muted-foreground">
                        #{doc.uploaded_by}
                      </TableCell>
                      <TableCell className="whitespace-nowrap text-sm text-muted-foreground">
                        {formatDate(doc.uploaded_at)}
                      </TableCell>
                      <TableCell className="font-mono text-sm text-muted-foreground">
                        #{doc.document_id}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon-sm" aria-label={`Actions for ${doc.title}`}>
                              <EllipsisVertical className="size-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onSelect={() => setViewing(doc)}>
                              <Eye />
                              View details
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem destructive onSelect={() => setDeleting(doc)}>
                              <Trash2 />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </>
      )}

      {/* ---------------- Upload dialog ---------------- */}
      <Dialog open={uploadOpen} onOpenChange={(open) => !open && closeUpload()}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Upload document</DialogTitle>
            <DialogDescription>
              Accepted formats: PDF, TXT, DOCX, MD · up to 50 MB. Processing starts immediately.
            </DialogDescription>
          </DialogHeader>

          {uploadError ? (
            <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
              {uploadError}
            </p>
          ) : null}

          <div className="space-y-4">
            <label className="block space-y-1.5">
              <Label>Title *</Label>
              <Input
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                placeholder="e.g. Remote Work Policy v3"
              />
            </label>

            <label className="block space-y-1.5">
              <Label>Description</Label>
              <Textarea
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                placeholder="Optional summary of the document's contents."
                rows={2}
              />
            </label>

            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block space-y-1.5">
                <Label>Document type *</Label>
                <Select
                  value={form.documentType}
                  onValueChange={(value) => setForm((f) => ({ ...f, documentType: value as DocumentType }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select type…" />
                  </SelectTrigger>
                  <SelectContent>
                    {TYPE_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </label>

              <label className="block space-y-1.5">
                <Label>Visibility *</Label>
                <Select
                  value={form.visibility}
                  onValueChange={(value) =>
                    setForm((f) => ({
                      ...f,
                      visibility: value as DocumentVisibility,
                    }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select visibility…" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ORGANIZATION">Organization-wide</SelectItem>
                    <SelectItem value="RESTRICTED">Restricted (ACL)</SelectItem>
                  </SelectContent>
                </Select>
              </label>
            </div>

            {form.visibility === "RESTRICTED" ? (
              <fieldset className="space-y-2.5 rounded-lg border bg-muted/40 p-3.5">
                <legend className="px-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Access control entries
                </legend>

                {permissions.map((row, index) => {
                  const needsId = row.principal_type !== "ORG_ADMIN";
                  return (
                    <div key={row.key} className="flex items-center gap-2">
                      <Select
                        value={row.principal_type}
                        onValueChange={(value) =>
                          setPermissions((rows) =>
                            rows.map((r, i) =>
                              i === index
                                ? {
                                    ...r,
                                    principal_type: value as PrincipalType,
                                    principalIdText: value === "ORG_ADMIN" ? "" : r.principalIdText,
                                  }
                                : r,
                            ),
                          )
                        }
                      >
                        <SelectTrigger className="w-44 shrink-0" aria-label="Permission principal type">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {PRINCIPAL_OPTIONS.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>

                      {needsId ? (
                        <Input
                          inputMode="numeric"
                          value={row.principalIdText}
                          onChange={(e) =>
                            setPermissions((rows) =>
                              rows.map((r, i) =>
                                i === index
                                  ? { ...r, principalIdText: e.target.value.replace(/\D/g, "") }
                                  : r,
                              ),
                            )
                          }
                          placeholder={`${row.principal_type.charAt(0)}${row.principal_type.slice(1).toLowerCase()} ID`}
                          aria-label={`${row.principal_type} ID`}
                          className="flex-1"
                        />
                      ) : (
                        <Input disabled value="All organization admins" className="flex-1" />
                      )}

                      <Button
                        type="button"
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => setPermissions((rows) => rows.filter((_, i) => i !== index))}
                        aria-label="Remove permission"
                      >
                        <X className="size-4" />
                      </Button>
                    </div>
                  );
                })}

                <Button type="button" variant="outline" size="sm" onClick={addPermissionRow}>
                  + Add access entry
                </Button>
                <p className="text-xs leading-relaxed text-muted-foreground">
                  Restricted documents are only visible to users matching at least one entry.
                </p>
              </fieldset>
            ) : form.visibility === "ORGANIZATION" ? (
              <p className="rounded-md border bg-muted/40 px-3 py-2 text-xs leading-relaxed text-muted-foreground">
                Organization-wide documents do not use access entries — every member
                of your organization can retrieve this document.
              </p>
            ) : null}

            <label className="block space-y-1.5">
              <Label>File *</Label>
              <Input
                type="file"
                accept=".pdf,.txt,.docx,.md,application/pdf,text/plain,text/markdown"
                onChange={(e) => setForm((f) => ({ ...f, file: e.target.files?.[0] ?? null }))}
                className="file:mr-3 file:rounded-md file:border-0 file:bg-secondary file:px-3 file:py-1 file:text-xs file:font-medium hover:file:bg-accent"
              />
              {form.file ? (
                <p className="text-xs text-muted-foreground">
                  {form.file.name} · {(form.file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              ) : null}
            </label>

            {uploadMutation.isPending ? (
              <LoadingBlock label="Uploading & processing document… This can take a moment." />
            ) : null}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={closeUpload} disabled={uploadMutation.isPending}>
              Cancel
            </Button>
            <Button
              disabled={uploadMutation.isPending}
              onClick={() => {
                const error = validateUpload();
                if (error) {
                  setUploadError(error);
                  return;
                }
                setUploadError(null);
                uploadMutation.mutate();
              }}
            >
              {uploadMutation.isPending ? "Uploading…" : "Upload"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ---------------- View details ---------------- */}
      <Dialog open={viewing !== null} onOpenChange={(open) => !open && setViewing(null)}>
        <DialogContent>
          {viewing ? (
            <>
              <DialogHeader>
                <DialogTitle>{viewing.title}</DialogTitle>
                <DialogDescription>
                  Document #{viewing.document_id} · {viewing.original_filename}
                </DialogDescription>
              </DialogHeader>
              {viewing.description ? (
                <p className="text-sm leading-relaxed text-muted-foreground">{viewing.description}</p>
              ) : null}
              <dl className="grid grid-cols-2 gap-x-4 gap-y-3 rounded-lg border bg-muted/40 p-4 text-sm">
                <DetailRow label="Type" value={TYPE_LABEL(viewing.document_type)} />
                <DetailRow label="Status" value={viewing.status} />
                <DetailRow label="Visibility" value={viewing.visibility === "ORGANIZATION" ? "Organization-wide" : "Restricted"} />
                <DetailRow label="Uploaded" value={formatDateTime(viewing.uploaded_at)} />
                <DetailRow label="Uploader ID" value={`#${viewing.uploaded_by}`} />
                <DetailRow label="Organization ID" value={`#${viewing.organization_id}`} />
              </dl>
            </>
          ) : null}
        </DialogContent>
      </Dialog>

      {/* ---------------- Delete confirm ---------------- */}
      <Dialog open={deleting !== null} onOpenChange={(open) => !open && setDeleting(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Delete document?</DialogTitle>
            <DialogDescription>
              “{deleting?.title}” will be removed from the knowledge base. Existing chat
              history may still reference it. This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleting(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={deleteMutation.isPending}
              onClick={() => deleting && deleteMutation.mutate(deleting.document_id)}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function TYPE_LABEL(type: DocumentType): string {
  const found = TYPE_OPTIONS.find((o) => o.value === type);
  return found?.label ?? type;
}

function StatusBadge({ status }: { status: DocumentResponse["status"] }) {
  switch (status) {
    case "READY":
      return <Badge variant="success">Ready</Badge>;
    case "PROCESSING":
      return <Badge variant="warning">Processing</Badge>;
    case "UPLOADING":
      return <Badge variant="warning">Uploading</Badge>;
    case "FAILED":
      return <Badge variant="destructive">Failed</Badge>;
    default:
      return <Badge variant="secondary">{status}</Badge>;
  }
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</dt>
      <dd className="mt-0.5">{value}</dd>
    </div>
  );
}
