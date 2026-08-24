const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

type ApiOptions = RequestInit & {
  auth?: boolean;
};

export async function apiFetch<T>(
  path: string,
  options: ApiOptions = {},
): Promise<T> {
  const token =
    typeof window !== "undefined"
      ? sessionStorage.getItem("intellex_token")
      : null;

  const headers = new Headers(
    options.headers,
  );

  headers.set(
    "Content-Type",
    "application/json",
  );

  if (
    options.auth !== false &&
    token
  ) {
    headers.set(
      "Authorization",
      `Bearer ${token}`,
    );
  }

  const response = await fetch(
    `${API_URL}${path}`,
    {
      ...options,
      headers,
    },
  );

  if (!response.ok) {
    let message =
      "Request failed.";

    try {
      const data = await response.json();

      message =
        data.detail ??
        data.message ??
        message;
    } catch {
      // Ignore JSON parsing failure.
    }

    throw new Error(message);
  }

  if (
    response.status === 204
  ) {
    return undefined as T;
  }

  return response.json();
}