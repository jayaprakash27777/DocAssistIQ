/**
 * DocAssistIQ — Standard API Error Utilities
 *
 * The backend always returns errors in this shape:
 * {
 *   "error": {
 *     "code":       "NOT_FOUND",
 *     "message":    "Resource not found",
 *     "request_id": "550e8400-e29b-41d4-a716-446655440000"
 *   }
 * }
 *
 * This module provides typed interfaces and helper functions
 * so UI components handle errors consistently.
 */

/** Machine-readable error codes returned by the API. */
export type ErrorCode =
  | "NOT_FOUND"
  | "VALIDATION_ERROR"
  | "UNAUTHORIZED"
  | "FORBIDDEN"
  | "CONFLICT"
  | "SERVICE_UNAVAILABLE"
  | "RATE_LIMITED"
  | "INTERNAL_ERROR"
  | "BAD_REQUEST"
  | "METHOD_NOT_ALLOWED"
  | "HTTP_ERROR"
  | "NETWORK_ERROR"
  | "TIMEOUT"
  | string; // allow forward-compatible unknown codes

/** The error detail block inside an API error response. */
export interface ApiErrorDetail {
  code: ErrorCode;
  message: string;
  request_id?: string;
}

/** The top-level API error response envelope. */
export interface ApiErrorEnvelope {
  error: ApiErrorDetail;
}

/**
 * A normalized error object used inside the frontend.
 * Produced by parseApiError() regardless of whether the
 * error came from the API envelope, a network timeout, or fetch failure.
 */
export interface FrontendError {
  code: ErrorCode;
  message: string;
  requestId?: string;
  /** HTTP status code, 0 for network errors. */
  statusCode: number;
}

/** Type guard: checks whether a value looks like an ApiErrorEnvelope. */
export function isApiErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as ApiErrorEnvelope).error === "object" &&
    typeof (value as ApiErrorEnvelope).error?.code === "string" &&
    typeof (value as ApiErrorEnvelope).error?.message === "string"
  );
}

/**
 * Parse an API error envelope into a FrontendError.
 * Falls back to a generic message if the shape is unexpected.
 */
export function parseApiError(
  raw: unknown,
  statusCode: number
): FrontendError {
  if (isApiErrorEnvelope(raw)) {
    return {
      code: raw.error.code,
      message: raw.error.message,
      requestId: raw.error.request_id,
      statusCode,
    };
  }
  return {
    code: "INTERNAL_ERROR",
    message: "An unexpected error occurred.",
    statusCode,
  };
}

/** Return a user-friendly message for common error codes. */
export function friendlyErrorMessage(error: FrontendError): string {
  switch (error.code) {
    case "NOT_FOUND":
      return "The requested resource could not be found.";
    case "UNAUTHORIZED":
      return "Please sign in to continue.";
    case "FORBIDDEN":
      return "You do not have permission to perform this action.";
    case "VALIDATION_ERROR":
      return error.message; // field-level detail is safe to show
    case "CONFLICT":
      return "This action conflicts with existing data. Please refresh and try again.";
    case "SERVICE_UNAVAILABLE":
      return "A required service is temporarily unavailable. Please try again shortly.";
    case "RATE_LIMITED":
      return "Too many requests. Please wait a moment and try again.";
    case "NETWORK_ERROR":
    case "TIMEOUT":
      return "Unable to reach the server. Please check your connection.";
    case "INTERNAL_ERROR":
    default:
      return "An unexpected error occurred. Please try again later.";
  }
}
