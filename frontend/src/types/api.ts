/**
 * TypeScript contract mirroring the Intellex FastAPI backend exactly.
 * Source of truth: app/schemas/*, app/dto/*, app/enums/enums.py.
 * Do not rename fields or enum values.
 */

export type UserRole = "SUPER_ADMIN" | "ORG_ADMIN" | "EMPLOYEE";

export type DocumentStatus =
  | "UPLOADING"
  | "PROCESSING"
  | "READY"
  | "FAILED"
  | "ARCHIVED";

export type DocumentType =
  | "HR_POLICY"
  | "SOP"
  | "TECHNICAL"
  | "MEETING_NOTE"
  | "REPORT";

export type FeedbackType = "Good" | "Satisfactory" | "Bad";

export type PrincipalType = "USER" | "TEAM" | "DEPARTMENT" | "ORG_ADMIN";

export type PermissionType = "READ";

export type DocumentVisibility = "ORGANIZATION" | "RESTRICTED";

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

/** GET /auth/me */
export interface CurrentUser {
  user_id: number;
  name: string;
  email: string;
  role: UserRole;
  organization_id: number | null;
  department_id: number | null;
  team_id: number | null;
}

/** POST /auth/login */
export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// ---------------------------------------------------------------------------
// Users (org-admin management)
// ---------------------------------------------------------------------------

export interface User {
  user_id: number;
  name: string;
  email: string;
  role: UserRole;
  organization_id: number | null;
  department_id: number | null;
  team_id: number | null;
  is_active: boolean;
}

export interface CreateEmployeeRequest {
  name: string;
  email: string;
  password: string;
  department_id?: number | null;
  team_id?: number | null;
}

export interface CreateOrgAdminRequest {
  name: string;
  email: string;
  password: string;
}

export interface UpdateUserRequest {
  name?: string | null;
  email?: string | null;
  department_id?: number | null;
  team_id?: number | null;
}

export interface ChangeUserRoleRequest {
  role: UserRole;
}

// ---------------------------------------------------------------------------
// Departments / Teams / Organizations
// ---------------------------------------------------------------------------

export interface Department {
  department_id: number;
  organization_id: number;
  name: string;
  description: string;
  created_at: string;
}

export interface CreateDepartmentRequest {
  name: string;
  description?: string | null;
}

export interface Team {
  team_id: number;
  department_id: number;
  organization_id: number;
  name: string;
  description: string;
  created_at: string;
  is_active: boolean;
}

export interface CreateTeamRequest {
  department_id: number;
  name: string;
  description?: string | null;
}

export interface Organization {
  organization_id: number;
  name: string;
  industry: string;
  is_active: boolean;
}

export interface CreateOrganizationRequest {
  organization_name: string;
  industry_name: string;
  admin_name: string;
  admin_email: string;
  admin_password: string;
}

export interface OrganizationOnboardingResponse {
  organization: Organization;
  admin_email: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Documents
// ---------------------------------------------------------------------------

export interface DocumentACLRequest {
  principal_type: PrincipalType;
  principal_id?: number | null;
}

export interface CreateDocumentRequest {
  title: string;
  description?: string | null;
  document_type: DocumentType;
  visibility: DocumentVisibility;
  permissions: DocumentACLRequest[];
}

export interface DocumentResponse {
  document_id: number;
  title: string;
  description: string | null;
  original_filename: string;
  document_type: DocumentType;
  visibility: DocumentVisibility;
  status: DocumentStatus;
  organization_id: number;
  uploaded_by: number;
  uploaded_at: string;
}

// ---------------------------------------------------------------------------
// Retrieval
// ---------------------------------------------------------------------------

export interface RetrievedChunkResponse {
  document_id: number;
  chunk_id: number;
  chunk_index: number;
  chunk_text: string;
  token_count: number;
  metadata: Record<string, unknown>;
  vector_score: number;
  rerank_score: number | null;
}

export interface RetrievalResponse {
  query: string;
  results: RetrievedChunkResponse[];
}

// ---------------------------------------------------------------------------
// Chat sessions / messages / history
// ---------------------------------------------------------------------------

export interface ChatSession {
  session_id: number;
  title: string | null;
  created_at: string;
  last_active: string;
  is_pinned: boolean;
}

export interface ChatSessionListResponse {
  sessions: ChatSession[];
}

export interface ChatSource {
  document_id: number;
  original_filename: string;
}

export interface ChatQueryResponse {
  query: string;
  answer: string;
  sources: ChatSource[];
}

export type ChatFeedback = FeedbackType;

export interface ChatHistoryMessage {
  chat_id: number;
  session_id: number;
  question: string;
  answer: string;
  created_at: string;
  feedback: ChatFeedback | null;
  sources: ChatSource[];
}

export interface ChatHistoryListResponse {
  messages: ChatHistoryMessage[];
}

export interface ChatSessionUpdateRequest {
  title?: string | null;
  is_pinned?: boolean | null;
}

// ---------------------------------------------------------------------------
// Observability (require_observability_admin)
// ---------------------------------------------------------------------------

export interface AgentExecution {
  execution_id: number;
  chat_id: number;
  session_id: number;
  user_id: number;
  organization_id: number;
  request_id: string;
  agent_name: string;
  route: string | null;
  attempt: number;
  status: string;
  latency_ms: number;
  details: Record<string, unknown>;
  created_at: string;
}

export interface AgentLatencySummary {
  agent_name: string;
  execution_count: number;
  average_latency_ms: number;
  min_latency_ms: number;
  max_latency_ms: number;
}

export interface RouteSummary {
  route: string;
  execution_count: number;
}

export interface ObservabilitySummary {
  window_hours: number;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  average_latency_ms: number;
  retry_count: number;
  retry_rate: number;
  critic_accept_count: number;
  critic_retry_count: number;
  critic_acceptance_rate: number;
  agent_latency: AgentLatencySummary[];
  routes: RouteSummary[];
}

export interface ChatExecutionTrace {
  chat_id: number;
  execution_count: number;
  executions: AgentExecution[];
}
