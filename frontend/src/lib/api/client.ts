import { API_BASE_URL } from "@/lib/config";

const TOKEN_STORAGE_KEY = "intellex.access_token";

export const UNAUTHORIZED_EVENT = "intellex:unauthorized";

export interface ApiErrorField {
  field: string;
  message: string;
}

export class ApiError extends Error {
  readonly status: number;
  readonly detail?: string;
  readonly fields?: ApiErrorField[];

  constructor(status: number, message: string, fields?: ApiErrorField[]) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = message;
    this.fields = fields;
  }
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function storeToken(token: string): void {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearStoredToken(): void {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  formData?: FormData;
  signal?: AbortSignal;
}

interface ParsedDetail {
  message: string;
  fields?: ApiErrorField[];
}

function parseFastApiDetail(detail: unknown, fallback: string): ParsedDetail {
  if (typeof detail === "string") {
    return { message: detail.trim().length > 0 ? detail : fallback };
  }

  if (Array.isArray(detail)) {
    const parts: string[] = [];
    const fields: ApiErrorField[] = [];
    for (const item of detail) {
      if (item && typeof item === "object" && "msg" in item && typeof item.msg === "string") {
        const loc =
          "loc" in item && Array.isArray(item.loc)
            ? item.loc
                .filter((p: unknown) => typeof p === "string" || typeof p === "number")
                .join(".")
            : "";
        parts.push(loc ? `${loc}: ${item.msg}` : item.msg);
        fields.push({ field: loc, message: item.msg });
      }
    }
    if (parts.length > 0) {
      return { message: parts.join("; "), fields };
    }
  }

  return { message: fallback };
}

async function parseError(response: Response): Promise<ParsedDetail> {
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    // Non-JSON body; fall through to generic message.
  }

  if (body && typeof body === "object" && "detail" in body) {
    return parseFastApiDetail(
      (body as { detail: unknown }).detail,
      `Request failed (${response.status})`,
    );
  }

  return { message: `Request failed (${response.status})` };
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, formData, signal } = options;

  const headers = new Headers();

  const token = getStoredToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let requestBody: BodyInit | undefined;
  if (formData) {
    requestBody = formData;
  } else if (body !== undefined) {
    headers.set("Content-Type", "application/json");
    requestBody = JSON.stringify(body);
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: requestBody,
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(0, "Cannot reach the Intellex server. Check your connection.");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  if (!response.ok) {
    const parsed = await parseError(response);

    switch (response.status) {
      case 400:
        throw new ApiError(400, parsed.message);
      case 401: {
        // Only treat as session expiry when an auth token was attached.
        // The login endpoint itself returns 401 for invalid credentials.
        if (token && typeof window !== "undefined") {
          clearStoredToken();
          window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
        }
        throw new ApiError(
          401,
          parsed.message || "Your session has expired. Please sign in again.",
        );
      }
      case 403:
        throw new ApiError(403, parsed.message || "You do not have permission to perform this action.");
      case 404:
        throw new ApiError(404, parsed.message || "The requested resource was not found.");
      case 422:
        throw new ApiError(422, parsed.message || "The submitted data is invalid.", parsed.fields);
      case 429:
        throw new ApiError(429, "Too many requests. Please slow down and try again.");
      default:
        throw new ApiError(response.status, parsed.message || "An unexpected server error occurred.");
    }
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError(response.status, "The server returned an invalid response.");
  }
}
