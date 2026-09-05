/**
 * DocAssistIQ — Typed API client.
 *
 * Minimal fetch wrapper used by client components.
 * All requests include a configurable timeout and typed error handling.
 * Base URL is set via NEXT_PUBLIC_API_URL environment variable.
 */

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/api\/v1$/, "") ??
  "http://localhost:8000";

/** Shape of a single dependency in /ready response. */
export interface DependencyStatus {
  status: "healthy" | "unhealthy";
  error?: string;
}

/** Shape of the /ready response body. */
export interface ReadinessResponse {
  status: "healthy" | "degraded";
  dependencies: {
    database: DependencyStatus;
    redis: DependencyStatus;
    storage: DependencyStatus;
  };
}

/** Shape of the /health response body. */
export interface HealthResponse {
  status: "healthy";
  service: string;
}

/** Result of any API call — either data or an error. */
export type ApiResult<T> =
  | { ok: true; data: T; statusCode: number }
  | { ok: false; error: string; statusCode: number };

/**
 * Fetch with a timeout. Resolves with a typed ApiResult.
 * Never throws — all errors are captured in the result.
 */
async function fetchWithTimeout<T>(
  url: string,
  timeoutMs = 5000
): Promise<ApiResult<T>> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    clearTimeout(timer);
    if (!res.ok && res.status !== 503) {
      return { ok: false, error: `HTTP ${res.status}`, statusCode: res.status };
    }
    const data = (await res.json()) as T;
    return { ok: true, data, statusCode: res.status };
  } catch (err: unknown) {
    clearTimeout(timer);
    const message =
      err instanceof Error
        ? err.name === "AbortError"
          ? "Request timed out"
          : err.message
        : "Network error";
    return { ok: false, error: message, statusCode: 0 };
  }
}

/** Fetch the liveness status from /health. */
export async function getHealth(): Promise<ApiResult<HealthResponse>> {
  return fetchWithTimeout<HealthResponse>(`${BASE_URL}/health`);
}

/** Fetch the readiness status from /ready. */
export async function getReady(): Promise<ApiResult<ReadinessResponse>> {
  // /ready can return 503 even when the body is valid JSON
  return fetchWithTimeout<ReadinessResponse>(`${BASE_URL}/ready`);
}
