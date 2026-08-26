import { apiFetch } from "./client";
import type {
  CreateDocumentRequest,
  DocumentResponse,
} from "@/types/api";

// ---------------------------------------------------------------------------
// Org-admin document management (require_org_admin)
// ---------------------------------------------------------------------------

export function listDocuments(): Promise<DocumentResponse[]> {
  return apiFetch<DocumentResponse[]>("/documents/");
}

export function getDocument(documentId: number): Promise<DocumentResponse> {
  return apiFetch<DocumentResponse>(`/documents/${documentId}`);
}

export function deleteDocument(documentId: number): Promise<DocumentResponse> {
  return apiFetch<DocumentResponse>(`/documents/${documentId}`, { method: "DELETE" });
}

/**
 * Uploads a document.
 *
 * Mirrors the backend contract:
 *   metadata = JSON string of CreateDocumentRequest
 *   file     = multipart file upload
 */
export function uploadDocument(metadata: CreateDocumentRequest, file: File): Promise<DocumentResponse> {
  const formData = new FormData();
  formData.append("metadata", JSON.stringify(metadata));
  formData.append("file", file);

  return apiFetch<DocumentResponse>("/documents/upload", {
    method: "POST",
    formData,
  });
}

// ---------------------------------------------------------------------------
// My Documents (authenticated user, ACL resolved server-side)
// ---------------------------------------------------------------------------

export function listMyDocuments(): Promise<DocumentResponse[]> {
  return apiFetch<DocumentResponse[]>("/my_documents/");
}

export function getMyDocument(documentId: number): Promise<DocumentResponse> {
  // NOTE: the backend returns this document without an explicit response_model;
  // prefer data already available from listMyDocuments() when rendering details.
  return apiFetch<DocumentResponse>(`/my_documents/${documentId}`);
}
