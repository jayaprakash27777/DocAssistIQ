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

// ── Platform types (mirror backend app/api/platform.py) ────

/**
 * Standard paginated response envelope returned by all list endpoints.
 *
 * Backend shape:
 *   { items: T[], total: number, page: number, page_size: number, pages: number }
 */
export interface PagedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

/** Pagination query parameters for list endpoints. */
export interface PaginationQuery {
  page?: number;
  page_size?: number;
}

/** Sorting query parameters for list endpoints. */
export interface SortQuery {
  sort_by?: string;
  sort_dir?: "asc" | "desc";
}

/**
 * Build a URL query string from pagination, sort, and arbitrary filter params.
 *
 * Omits keys whose value is undefined or null.
 *
 * Example:
 *   buildQueryString({ page: 2, page_size: 10, sort_by: "email", role: "doctor" })
 *   // => "page=2&page_size=10&sort_by=email&role=doctor"
 */
export function buildQueryString(
  params: PaginationQuery & SortQuery & Record<string, string | number | boolean | undefined | null>,
): string {
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== null,
  ) as [string, string | number | boolean][];
  if (entries.length === 0) return "";
  return entries.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join("&");
}


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

// ── Auth types ─────────────────────────────────────────────

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

// ── Token storage ──────────────────────────────────────────

const TOKEN_KEY = "docassistiq_access_token";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function storeToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function clearStoredToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
  }
}

// ── Auth API wrappers ──────────────────────────────────────

function authHeaders(): Record<string, string> {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function authedFetch<T>(
  url: string,
  options: RequestInit = {},
): Promise<ApiResult<T>> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
  const requestId = generateRequestId();

  const headers: Record<string, string> = {
    Accept: "application/json",
    "Content-Type": "application/json",
    "X-Request-ID": requestId,
    ...authHeaders(),
    ...(options.headers as Record<string, string>),
  };

  try {
    const res = await fetch(url, { ...options, signal: controller.signal, headers });
    clearTimeout(timer);

    const responseRequestId = res.headers.get("x-request-id") ?? requestId;

    if (res.status === 204) {
      return { ok: true, data: undefined as unknown as T, statusCode: 204, requestId: responseRequestId };
    }

    let rawBody: unknown;
    try { rawBody = await res.json(); } catch { rawBody = null; }

    if (res.ok) {
      return { ok: true, data: rawBody as T, statusCode: res.status, requestId: responseRequestId };
    }

    if (res.status === 401) {
      clearStoredToken();
    }

    return {
      ok: false,
      error: parseApiError(rawBody, res.status),
      statusCode: res.status,
      requestId: responseRequestId,
    };
  } catch (err: unknown) {
    clearTimeout(timer);
    const isTimeout = err instanceof Error && err.name === "AbortError";
    return {
      ok: false,
      error: { code: isTimeout ? "TIMEOUT" : "NETWORK_ERROR", message: isTimeout ? "Request timed out" : "Network error", statusCode: 0 },
      statusCode: 0,
      requestId: null,
    };
  }
}

export async function authRegister(payload: RegisterPayload): Promise<ApiResult<MeResponse>> {
  return authedFetch<MeResponse>(`${BASE_URL}/api/v1/auth/register`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function authLogin(payload: LoginPayload): Promise<ApiResult<TokenResponse>> {
  return authedFetch<TokenResponse>(`${BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function authLogout(): Promise<ApiResult<undefined>> {
  const result = await authedFetch<undefined>(`${BASE_URL}/api/v1/auth/logout`, {
    method: "POST",
  });
  clearStoredToken();
  return result;
}

export async function authGetMe(): Promise<ApiResult<MeResponse>> {
  return authedFetch<MeResponse>(`${BASE_URL}/api/v1/auth/me`);
}

// ── Consultation types ──────────────────────────────────────

/** Mandatory safety label — matches backend PLACEHOLDER_LABEL */
export const PLACEHOLDER_LABEL = "PLACEHOLDER DEVELOPMENT RESPONSE — NOT CLINICAL";

export interface ConsultationResponse {
  id: string;
  doctor_id: string;
  patient_session_id: string | null;
  status: string;
  input_text: string;
  created_at: string;
  updated_at: string;
  findings: ClinicalFindingResponse[];
}

export interface ConsultationCreateRequest {
  patient_session_id?: string | null;
  input_text?: string;
}

export interface ConsultationTransitionRequest {
  new_status: string;
  input_text?: string | null;
}

export interface ConsultationSummary {
  id: string;
  status: string;
  is_placeholder: boolean;
  input_preview: string;
  created_at: string;
}

// ── Consultation API functions ──────────────────────────────

export async function createConsultation(
  payload: ConsultationCreateRequest = {},
): Promise<ApiResult<ConsultationResponse>> {
  return authedFetch<ConsultationResponse>(
    `${BASE_URL}/api/v1/consultations/`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
}

export async function getConsultation(
  id: string,
): Promise<ApiResult<ConsultationResponse>> {
  return authedFetch<ConsultationResponse>(
    `${BASE_URL}/api/v1/consultations/${id}`,
  );
}

export async function transitionConsultationStatus(
  consultationId: string,
  payload: ConsultationTransitionRequest,
): Promise<ApiResult<ConsultationResponse>> {
  return authedFetch<ConsultationResponse>(
    `${BASE_URL}/api/v1/consultations/${consultationId}/status`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
  );
}

export async function listConsultations(
  page = 1,
  page_size = 20,
): Promise<ApiResult<PagedResponse<ConsultationSummary>>> {
  return authedFetch<PagedResponse<ConsultationSummary>>(
    `${BASE_URL}/api/v1/consultations/?page=${page}&page_size=${page_size}`,
  );
}

// -- Doctor types (Phase 10) ---------------------------------

export interface DoctorResponse {
  id: string;
  user_id: string;
  tenant_id: string | null;
  specialty: string | null;
  credential_reference: string | null;
  credential_body: string | null;
  bio: string | null;
  verification_status: 'pending' | 'verified' | 'rejected';
  rejection_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface DoctorCreate {
  specialty?: string;
  credential_reference?: string;
  credential_body?: string;
  bio?: string;
}

export interface DoctorUpdate {
  specialty?: string;
  credential_reference?: string;
  credential_body?: string;
  bio?: string;
}

export interface VerifyDoctorRequest {
  action: 'verify' | 'reject';
  rejection_reason?: string;
}

// ── Doctor API functions ────────────────────────────────────

export async function getMyDoctorProfile(): Promise<ApiResult<DoctorResponse>> {
  return authedFetch<DoctorResponse>(`${BASE_URL}/api/v1/doctors/me`);
}

export async function createMyDoctorProfile(
  payload: DoctorCreate,
): Promise<ApiResult<DoctorResponse>> {
  return authedFetch<DoctorResponse>(`${BASE_URL}/api/v1/doctors/me`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function updateMyDoctorProfile(
  payload: DoctorUpdate,
): Promise<ApiResult<DoctorResponse>> {
  return authedFetch<DoctorResponse>(`${BASE_URL}/api/v1/doctors/me`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function listPendingDoctors(
  page = 1,
  page_size = 20,
): Promise<ApiResult<PagedResponse<DoctorResponse>>> {
  return authedFetch<PagedResponse<DoctorResponse>>(
    `${BASE_URL}/api/v1/doctors/pending?page=${page}&page_size=${page_size}`,
  );
}

export async function verifyDoctor(
  doctor_id: string,
  payload: VerifyDoctorRequest,
): Promise<ApiResult<DoctorResponse>> {
  return authedFetch<DoctorResponse>(
    `${BASE_URL}/api/v1/doctors/${doctor_id}/verify`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
  );
}


// -- File Storage (Phase 11) ---------------------------------

export interface FileObjectResponse {
  id: string;
  owner_id: string;
  tenant_id: string | null;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  checksum_sha256: string | null;
  status: string;
  scan_status: string;
  linked_entity_type: string | null;
  linked_entity_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface FileDownloadUrlResponse {
  file_id: string;
  download_url: string;
  expires_in_seconds: number;
}

export interface FileUploadResponse {
  file: FileObjectResponse;
  message: string;
}

export async function uploadFile(
  formData: FormData,
): Promise<ApiResult<FileUploadResponse>> {
  return authedFetch<FileUploadResponse>(`${BASE_URL}/api/v1/files/upload`, {
    method: 'POST',
    body: formData, // Do not set Content-Type header, let browser set it with boundary
  });
}

export async function listFiles(
  page = 1,
  page_size = 20,
): Promise<ApiResult<PagedResponse<FileObjectResponse>>> {
  return authedFetch<PagedResponse<FileObjectResponse>>(
    `${BASE_URL}/api/v1/files/?page=${page}&page_size=${page_size}`,
  );
}

export async function getFileDownloadUrl(
  fileId: string,
): Promise<ApiResult<FileDownloadUrlResponse>> {
  return authedFetch<FileDownloadUrlResponse>(
    `${BASE_URL}/api/v1/files/${fileId}/download`,
  );
}

export async function deleteFile(fileId: string): Promise<ApiResult<void>> {
  return authedFetch<void>(`${BASE_URL}/api/v1/files/${fileId}`, {
    method: 'DELETE',
  });
}

// -- Medical Sources (Phase 12) ------------------------------

export interface SourceResponse {
  id: string;
  code: string;
  organisation: string;
  name: string;
  base_url: string | null;
  access_mechanism: string;
  data_type: string;
  license_info: string | null;
  is_production_suitable: boolean;
  last_verified_at: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface SourceCreate {
  code: string;
  organisation: string;
  name: string;
  base_url?: string;
  access_mechanism: string;
  data_type: string;
  license_info?: string;
}

export interface SourceUpdate {
  organisation?: string;
  name?: string;
  base_url?: string;
  access_mechanism?: string;
  data_type?: string;
  license_info?: string;
}

export async function listSources(
  page = 1,
  page_size = 20,
): Promise<ApiResult<PagedResponse<SourceResponse>>> {
  return authedFetch<PagedResponse<SourceResponse>>(
    `/api/v1/sources/?page=&page_size=`,
  );
}

export async function getSource(id: string): Promise<ApiResult<SourceResponse>> {
  return authedFetch<SourceResponse>(`${BASE_URL}/api/v1/sources/`);
}

export async function createSource(
  payload: SourceCreate,
): Promise<ApiResult<SourceResponse>> {
  return authedFetch<SourceResponse>(`${BASE_URL}/api/v1/sources/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function updateSource(
  id: string,
  payload: SourceUpdate,
): Promise<ApiResult<SourceResponse>> {
  return authedFetch<SourceResponse>(`${BASE_URL}/api/v1/sources/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function verifySource(
  id: string,
): Promise<ApiResult<SourceResponse>> {
  return authedFetch<SourceResponse>(
    `${BASE_URL}/api/v1/sources/${id}/verify`,
    {
      method: 'POST',
    },
  );
}

// -- Knowledge Ingestion (Phase 13) -------------------------

export interface IngestionJobResponse {
  id: string;
  source_id: string;
  source_version: string | null;
  status: string;
  content_hash: string | null;
  raw_artifact_url: string | null;
  validation_result: Record<string, any> | null;
  error_message: string | null;
  review_status: string;
  created_at: string;
  updated_at: string;
}

export interface IngestionJobCreate {
  source_id: string;
  source_version?: string;
}

export async function listIngestionJobs(
  page = 1,
  page_size = 20,
): Promise<ApiResult<PagedResponse<IngestionJobResponse>>> {
  return authedFetch<PagedResponse<IngestionJobResponse>>(
    `/api/v1/ingestion/jobs?page=&page_size=`,
  );
}

export async function startIngestionJob(
  payload: IngestionJobCreate,
): Promise<ApiResult<IngestionJobResponse>> {
  return authedFetch<IngestionJobResponse>(`${BASE_URL}/api/v1/ingestion/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function reviewIngestionJob(
  id: string,
  status: 'approved' | 'rejected',
): Promise<ApiResult<IngestionJobResponse>> {
  return authedFetch<IngestionJobResponse>(
    `${BASE_URL}/api/v1/ingestion/jobs/${id}/review`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ review_status: status }),
    },
  );
}

// -- Knowledge Review (Phase 14) ----------------------------

export interface KnowledgeEntityResponse {
  id: string;
  code: string;
  name: string;
  status: string;
  is_ai_generated: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProvenanceItemResponse {
  id: string;
  claim: string;
  evidence_grade: string | null;
  recommendation_grade: string | null;
  is_ai_extracted: boolean;
  source_name: string;
  source_code: string;
}

export async function listPendingKnowledge(
  entityType: string,
  page = 1,
  pageSize = 20,
): Promise<ApiResult<PagedResponse<KnowledgeEntityResponse>>> {
  return authedFetch<PagedResponse<KnowledgeEntityResponse>>(
    `/api/v1/knowledge//pending?page=&page_size=`,
  );
}

export async function reviewKnowledge(
  entityType: string,
  id: string,
  newStatus: 'APPROVED' | 'REJECTED' | 'SUPERSEDED' | 'OUTDATED',
): Promise<ApiResult<KnowledgeEntityResponse>> {
  return authedFetch<KnowledgeEntityResponse>(
    `${BASE_URL}/api/v1/knowledge/${entityType}/${id}/review`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_status: newStatus }),
    },
  );
}

export async function inspectProvenance(
  entityType: string,
  id: string,
): Promise<ApiResult<ProvenanceItemResponse[]>> {
  return authedFetch<ProvenanceItemResponse[]>(
    `${BASE_URL}/api/v1/knowledge/${entityType}/${id}/provenance`,
  );
}

export interface EmbeddingSyncResponse {
  id: string;
  model: string;
  dimensions: number;
  generated_at: string;
}

export async function syncEmbedding(
  entityType: string,
  id: string,
): Promise<ApiResult<EmbeddingSyncResponse>> {
  return authedFetch<EmbeddingSyncResponse>(
    `${BASE_URL}/api/v1/knowledge/${entityType}/${id}/embeddings/sync`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    },
  );
}

// -- Dataset Registry (Phase 17) ----------------------------

export interface DatasetRegisterRequest {
  name: string;
  source: string;
  license: string;
  version: string;
  hash: string;
  schema_def: any;
  intended_use: string;
  limitations: string;
  storage_path: string;
}

export interface DatasetResponse {
  id: string;
  name: string;
  source: string;
  version: string;
  hash: string;
  record_count: number;
  is_deidentified: boolean;
  approval_status: string;
  storage_path: string;
}

export interface DatasetValidationResult {
  is_valid: boolean;
  record_count: number;
  malformed: number;
  missing_values: number;
  duplicates: number;
  pii_detected: boolean;
  label_conflicts: number;
  leakage_detected: boolean;
  errors: string[];
}

export async function listDatasets(): Promise<ApiResult<DatasetResponse[]>> {
  return authedFetch<DatasetResponse[]>(`/api/v1/datasets`);
}

export async function registerDataset(
  payload: DatasetRegisterRequest,
): Promise<ApiResult<DatasetResponse>> {
  return authedFetch<DatasetResponse>(`/api/v1/datasets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function validateDataset(
  id: string,
): Promise<ApiResult<DatasetValidationResult>> {
  return authedFetch<DatasetValidationResult>(
    `/api/v1/datasets//validate`,
    { method: 'POST' }
  );
}

export async function approveDataset(
  id: string,
): Promise<ApiResult<DatasetResponse>> {
  return authedFetch<DatasetResponse>(
    `/api/v1/datasets//approve`,
    { method: 'POST' }
  );
}

// -- Evaluation Harness (Phase 18) --------------------------

export interface EvaluationResultResponse {
  id: string;
  record_identifier: string;
  task_type: string;
  ground_truth: any;
  model_output: any;
  is_correct: boolean | null;
  score: number | null;
  failure_reason: string | null;
}

export interface EvaluationRunResponse {
  id: string;
  dataset_id: string;
  model_version: string;
  status: string;
  metrics: any;
}

export interface EvaluationRunDetailResponse extends EvaluationRunResponse {
  results: EvaluationResultResponse[];
}

export interface TriggerEvaluationRequest {
  dataset_id: string;
  model_version: string;
}

export async function listEvaluations(): Promise<ApiResult<EvaluationRunResponse[]>> {
  return authedFetch<EvaluationRunResponse[]>(`/api/v1/evaluations`);
}

export async function getEvaluationDetails(
  id: string,
): Promise<ApiResult<EvaluationRunDetailResponse>> {
  return authedFetch<EvaluationRunDetailResponse>(`/api/v1/evaluations/`);
}

export async function triggerEvaluation(
  payload: TriggerEvaluationRequest,
): Promise<ApiResult<EvaluationRunResponse>> {
  return authedFetch<EvaluationRunResponse>(`/api/v1/evaluations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function executeEvaluationPipeline(
  id: string,
): Promise<ApiResult<{ status: string }>> {
  return authedFetch<{ status: string }>(
    `/api/v1/evaluations//execute`,
    { method: 'POST' }
  );
}

// -- ML Experiments (Phase 19) -----------------------------

export interface ExperimentResponse {
  id: string;
  name: string;
  status: string;
  code_commit: string;
  dataset_version: string;
  dataset_hash: string;
  preprocessing_version: string;
  model_name: string;
  configuration: any;
  random_seed: number;
  hardware: any;
  execution_duration_sec: number | null;
  metrics: any;
  artifact_location: string | null;
}

export async function listExperiments(): Promise<ApiResult<ExperimentResponse[]>> {
  return authedFetch<ExperimentResponse[]>(`/api/v1/experiments`);
}

export async function getExperiment(
  id: string,
): Promise<ApiResult<ExperimentResponse>> {
  return authedFetch<ExperimentResponse>(`/api/v1/experiments/`);
}

// -- Consultation Lifecycle (Phase 20) --------------------------

export interface ClinicalFindingResponse {
  id: string;
  finding_type: string;
  finding_text: string;
  concept: string | null;
  value: string | null;
  certainty: string | null;
  negated: boolean;
  temporality: string | null;
  source_context: string | null;
  canonical_concept: string | null;
  mapping_source: string | null;
  mapping_confidence: number | null;
  is_ai_suggested: boolean;
  is_clinician_confirmed: boolean;
  status: string;
  confidence_score: number | null;
}




export async function reviewClinicalFinding(
  consultationId: string,
  findingId: string,
  action: 'confirm' | 'reject',
): Promise<ApiResult<ClinicalFindingResponse>> {
  return authedFetch<ClinicalFindingResponse>(`${BASE_URL}/api/v1/consultations/${consultationId}/findings/${findingId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action }),
  });
}

// -- Consent (Phase 21) -----------------------------------------

export interface ConsentRecordResponse {
  id: string;
  consultation_id: string;
  actor_name: string;
  actor_relationship: string;
  consent_text_version: string;
  purpose: string;
  status: string;
  recording_permitted: boolean;
  recorded_by_id: string;
  created_at: string;
}

export interface ConsentRecordCreate {
  consultation_id: string;
  actor_name: string;
  actor_relationship: string;
  purpose: string;
  recording_permitted: boolean;
}

export async function createConsent(
  payload: ConsentRecordCreate,
): Promise<ApiResult<ConsentRecordResponse>> {
  return authedFetch<ConsentRecordResponse>(`/api/v1/consent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function getActiveConsent(
  consultationId: string,
): Promise<ApiResult<ConsentRecordResponse>> {
  return authedFetch<ConsentRecordResponse>(`/api/v1/consent/`);
}

export async function revokeConsent(
  consultationId: string,
): Promise<ApiResult<ConsentRecordResponse>> {
  return authedFetch<ConsentRecordResponse>(`/api/v1/consent//revoke`, {
    method: 'POST',
  });
}

// -- Manual Intake (Phase 22) --------------------------

export interface ManualIntakeResponse {
  id: string;
  consultation_id: string;
  doctor_id: string;
  status: string;
  chief_complaint: string | null;
  symptoms: string | null;
  duration: string | null;
  severity: string | null;
  onset: string | null;
  location: string | null;
  associated_symptoms: string | null;
  aggravating_factors: string | null;
  relieving_factors: string | null;
  negations: string | null;
  past_medical_history: string | null;
  medications: string | null;
  allergies: string | null;
  family_social_history: string | null;
  vitals: string | null;
  previous_investigations: string | null;
  updated_at: string;
}

export type ManualIntakeUpdate = Partial<Omit<ManualIntakeResponse, "id" | "consultation_id" | "doctor_id" | "status" | "updated_at">>;

export async function getIntake(
  consultationId: string,
): Promise<ApiResult<ManualIntakeResponse>> {
  return authedFetch<ManualIntakeResponse>(`/api/v1/consultations/${consultationId}/intake`);
}

export async function updateIntake(
  consultationId: string,
  payload: ManualIntakeUpdate,
): Promise<ApiResult<ManualIntakeResponse>> {
  return authedFetch<ManualIntakeResponse>(`/api/v1/consultations/${consultationId}/intake`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function finalizeIntake(
  consultationId: string,
): Promise<ApiResult<ManualIntakeResponse>> {
  return authedFetch<ManualIntakeResponse>(`/api/v1/consultations/${consultationId}/intake/finalize`, {
    method: 'POST',
  });
}

// ── Transcripts (Phase 27) ────────────────────────────────────────────────────────

export interface TranscriptSegmentResponse {
  id: string;
  start_time: number;
  end_time: number;
  speaker_label: string | null;
  speaker_confidence: number | null;
  speaker_source: string | null;
  raw_text: string;
  processed_text: string;
  clinician_corrected_text: string | null;
  is_corrected: boolean;
}

export interface TranscriptResponse {
  id: string;
  consultation_id: string;
  status: string;
  segments: TranscriptSegmentResponse[];
}

export async function getTranscript(
  consultationId: string,
): Promise<ApiResult<TranscriptResponse>> {
  return authedFetch<TranscriptResponse>(`/api/v1/consultations/${consultationId}/transcript`);
}

export async function saveTranscript(
  consultationId: string,
  payload: { status: string; segments: any[] },
): Promise<ApiResult<TranscriptResponse>> {
  return authedFetch<TranscriptResponse>(`/api/v1/consultations/${consultationId}/transcript`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function correctTranscriptSegment(
  consultationId: string,
  segmentId: string,
  text: string,
): Promise<ApiResult<TranscriptSegmentResponse>> {
  return authedFetch<TranscriptSegmentResponse>(
    `/api/v1/consultations/${consultationId}/transcript/segments/${segmentId}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clinician_corrected_text: text }),
    },
  );
}

// ── Clinical Note types ─────────────────────────────────────

export interface NoteSection {
  text: string;
  original_ai_text: string | null;
  status: "draft" | "accepted";
}

export interface ClinicalNoteResponse {
  id: string;
  consultation_id: string;
  author_id: string;
  note_type: string;
  body: Record<string, NoteSection>;
  status: string;
  version: number;
  last_edited_by_id: string | null;
  is_ai_generated: boolean;
  created_at: string;
  updated_at: string;
}

export interface ClinicalNoteUpdate {
  body: Record<string, NoteSection>;
  version: number;
}

export async function getClinicalNote(
  consultation_id: string,
): Promise<ApiResult<ClinicalNoteResponse>> {
  return authedFetch<ClinicalNoteResponse>(
    `${BASE_URL}/api/v1/consultations/${consultation_id}/note`,
  );
}

export async function updateClinicalNote(
  consultation_id: string,
  payload: ClinicalNoteUpdate,
): Promise<ApiResult<ClinicalNoteResponse>> {
  return authedFetch<ClinicalNoteResponse>(
    `${BASE_URL}/api/v1/consultations/${consultation_id}/note`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
}

// ── Clinical Representation types ───────────────────────────

export interface Provenance {
  source_type: string;
  source_id: string;
  timestamp: string;
  author_id: string | null;
}

export interface RepresentationItem {
  value: string;
  concept: string | null;
  status: string | null;
  provenances: Provenance[];
}

export interface PatientContext {
  demographics: string | null;
  provenances: Provenance[];
}

export interface ClinicalRepresentationResponse {
  consultation_id: string;
  schema_version: string;
  generated_at: string;
  patient_context: PatientContext;
  symptoms: RepresentationItem[];
  negations: RepresentationItem[];
  duration: RepresentationItem[];
  severity: RepresentationItem[];
  history: RepresentationItem[];
  medications: RepresentationItem[];
  allergies: RepresentationItem[];
  vitals: RepresentationItem[];
  investigations: RepresentationItem[];
  report_findings: RepresentationItem[];
}

export async function getClinicalRepresentation(
  consultation_id: string,
): Promise<ApiResult<ClinicalRepresentationResponse>> {
  return authedFetch<ClinicalRepresentationResponse>(
    `${BASE_URL}/api/v1/consultations/${consultation_id}/representation`,
  );
}

// ── Differential Diagnosis types ────────────────────────────

export interface DifferentialDiagnosisItem {
  disease: string;
  score: number;
  supporting_findings: string[];
  missing_expected_findings: string[];
  contradicting_information: string[];
  uncertainty: string;
  explanation_reference: string;
}

export interface DifferentialDiagnosisResponse {
  consultation_id: string;
  provider_metadata: Record<string, any>;
  top_candidates: DifferentialDiagnosisItem[];
}

export async function getDifferentialDiagnosis(
  consultation_id: string,
): Promise<ApiResult<DifferentialDiagnosisResponse>> {
  return authedFetch<DifferentialDiagnosisResponse>(
    `${BASE_URL}/api/v1/consultations/${consultation_id}/differential`,
  );
}
