/**
 * DocAssistIQ — Typed API client.
 *
 * All requests:
 *   - Include a client-generated X-Request-ID for correlation
 *   - Have a configurable timeout (default 5 s)
 *   - Return a discriminated ApiResult — never throw
 *   - Parse the standard error envelope on non-2xx responses
 *
 * Base URL is set via NEXT_PUBLIC_API_URL environment variable.
 */

import { parseApiError, type FrontendError } from "./errors";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/api\/v1$/, "") ??
  "http://localhost:8000";

// ── Types ──────────────────────────────────────────────────

/** Shape of a single dependency in /ready response. */
export interface DependencyStatus {
  status: "healthy" | "unhealthy";
  error?: string;
}

/** Shape of the /ready response body. */
export interface ReadinessResponse {
  status: "healthy" | "degraded";
  request_id: string;
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
  request_id: string;
}

/** Shape of the /api/v1/ping response body. */
export interface PingResponse {
  version: string;
  api_version: string;
  env: string;
  request_id: string;
}

/** Successful API result. */
export interface ApiSuccess<T> {
  ok: true;
  data: T;
  statusCode: number;
  requestId: string | null;
}

/** Failed API result (network error, timeout, or HTTP error). */
export interface ApiFailure {
  ok: false;
  error: FrontendError;
  statusCode: number;
  requestId: string | null;
}

export type ApiResult<T> = ApiSuccess<T> | ApiFailure;

// ── Client-side request ID ─────────────────────────────────

function generateRequestId(): string {
  // Use crypto.randomUUID() when available (browsers + Node 16+).
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  // Fallback for environments without crypto.randomUUID
  return `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
}

// ── Core fetch wrapper ─────────────────────────────────────

/**
 * Fetch with timeout, X-Request-ID injection, and error envelope parsing.
 * Never throws — all errors are captured in the ApiResult.
 *
 * For endpoints that return 503 with a valid JSON body (e.g. /ready),
 * pass acceptedErrorCodes to treat those status codes as successful parses.
 */
async function fetchWithTimeout<T>(
  url: string,
  {
    timeoutMs = 5000,
    acceptedErrorCodes = [] as number[],
  }: { timeoutMs?: number; acceptedErrorCodes?: number[] } = {}
): Promise<ApiResult<T>> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const requestId = generateRequestId();

  try {
    const res = await fetch(url, {
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        "X-Request-ID": requestId,
      },
      cache: "no-store",
    });

    clearTimeout(timer);

    const responseRequestId =
      res.headers.get("x-request-id") ??
      res.headers.get("X-Request-ID") ??
      requestId;

    // Treat accepted error codes as parseable responses
    if (res.ok || acceptedErrorCodes.includes(res.status)) {
      const data = (await res.json()) as T;
      return {
        ok: true,
        data,
        statusCode: res.status,
        requestId: responseRequestId,
      };
    }

    // Parse the error envelope
    let rawBody: unknown;
    try {
      rawBody = await res.json();
    } catch {
      rawBody = null;
    }

    return {
      ok: false,
      error: parseApiError(rawBody, res.status),
      statusCode: res.status,
      requestId: responseRequestId,
    };
  } catch (err: unknown) {
    clearTimeout(timer);

    const isTimeout =
      err instanceof Error && err.name === "AbortError";

    const frontendError: FrontendError = {
      code: isTimeout ? "TIMEOUT" : "NETWORK_ERROR",
      message: isTimeout
        ? "Request timed out"
        : err instanceof Error
        ? err.message
        : "Network error",
      statusCode: 0,
    };

    return {
      ok: false,
      error: frontendError,
      statusCode: 0,
      requestId: null,
    };
  }
}

// ── Public API ─────────────────────────────────────────────

/** Fetch the liveness status from /health. */
export async function getHealth(): Promise<ApiResult<HealthResponse>> {
  return fetchWithTimeout<HealthResponse>(`${BASE_URL}/health`);
}

/**
 * Fetch the readiness status from /ready.
 * /ready can return 503 even when the body is valid JSON,
 * so we accept 503 as a parseable response.
 */
export async function getReady(): Promise<ApiResult<ReadinessResponse>> {
  return fetchWithTimeout<ReadinessResponse>(`${BASE_URL}/ready`, {
    acceptedErrorCodes: [503],
  });
}

/** Fetch the versioned API ping from /api/v1/ping. */
export async function getPing(): Promise<ApiResult<PingResponse>> {
  return fetchWithTimeout<PingResponse>(`${BASE_URL}/api/v1/ping`);
}
