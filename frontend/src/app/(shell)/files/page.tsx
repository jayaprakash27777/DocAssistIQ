/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable react/no-unescaped-entities */
/**
 * DocAssistIQ — File Manager Page (/files).
 *
 * Secure file management interface with:
 *   - Drag-and-drop + browse file uploader
 *   - Upload progress simulation (real XHR progress in future)
 *   - File type/size validation on the client before sending
 *   - Upload success / error / retry states
 *   - Paginated list of own files
 *   - Download via presigned URL (opens in new tab)
 *   - Delete with confirmation
 *   - Degraded storage failure state (API error banner)
 *
 * Client-side validation mirrors server constraints:
 *   Max 50 MB, allowed extensions: .pdf .jpg .jpeg .png .tiff .tif .webp .txt .csv .xlsx .dcm
 */

"use client";

import { DragEvent, FormEvent, useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import {
  listFiles,
  uploadFile,
  getFileDownloadUrl,
  deleteFile,
  type FileObjectResponse,
} from "@/lib/api";
import { motion } from "framer-motion";
import { FileStack } from "lucide-react";

const MAX_SIZE_BYTES = 50 * 1024 * 1024;
const ALLOWED_EXTS = new Set([
  ".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp",
  ".txt", ".csv", ".xlsx", ".dcm",
]);

function getExt(name: string): string {
  const dot = name.lastIndexOf(".");
  return dot >= 0 ? name.slice(dot).toLowerCase() : "";
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
}

type UploadState =
  | { status: "idle" }
  | { status: "validating" }
  | { status: "uploading"; progress: number; name: string }
  | { status: "success"; name: string }
  | { status: "error"; message: string; name: string };

export default function FilesPage() {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadState, setUploadState] = useState<UploadState>({ status: "idle" });

  const [files, setFiles] = useState<FileObjectResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [listLoading, setListLoading] = useState(true);
  const [storageError, setStorageError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const PAGE_SIZE = 20;

  const loadFiles = useCallback(async (p: number) => {
    setListLoading(true);
    const r = await listFiles(p, PAGE_SIZE);
    setListLoading(false);
    if (!r.ok) {
      setStorageError(r.error.message ?? "Failed to load files.");
      return;
    }
    setFiles(r.data.items);
    setTotal(r.data.total);
    setPages(r.data.pages);
    setStorageError(null);
  }, []);

  useEffect(() => { loadFiles(page); }, [page, loadFiles]);

  // ── Validation ─────────────────────────────────────────────

  function validateFile(file: File): string | null {
    if (file.size === 0) return "File is empty.";
    if (file.size > MAX_SIZE_BYTES) return `File exceeds 50 MB limit (${formatBytes(file.size)}).`;
    const ext = getExt(file.name);
    if (!ALLOWED_EXTS.has(ext)) {
      return `Extension '${ext || "(none)"}' is not allowed. Allowed: ${[...ALLOWED_EXTS].join(", ")}`;
    }
    return null;
  }

  // ── Upload ────────────────────────────────────────────────

  async function handleUpload(file: File) {
    const err = validateFile(file);
    if (err) {
      setUploadState({ status: "error", message: err, name: file.name });
      return;
    }

    setUploadState({ status: "uploading", progress: 0, name: file.name });

    // Simulate progress (real progress needs XHR — fetch API doesn't expose it)
    const interval = setInterval(() => {
      setUploadState((s) =>
        s.status === "uploading" && s.progress < 85
          ? { ...s, progress: s.progress + 12 }
          : s,
      );
    }, 150);

    const formData = new FormData();
    formData.append("file", file);

    const r = await uploadFile(formData);
    clearInterval(interval);

    if (!r.ok) {
      setUploadState({
        status: "error",
        message: r.error.message ?? "Upload failed.",
        name: file.name,
      });
      return;
    }

    setUploadState({ status: "success", name: file.name });
    toast.success(`'${file.name}' uploaded successfully.`);
    setTimeout(() => setUploadState({ status: "idle" }), 2500);
    loadFiles(1);
    setPage(1);
  }

  function onFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleUpload(file);
    e.target.value = "";
  }

  // ── Drag & Drop ─────────────────────────────────────────

  function onDragOver(e: DragEvent) {
    e.preventDefault();
    setIsDragging(true);
  }

  function onDragLeave() {
    setIsDragging(false);
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  }

  // ── Download ──────────────────────────────────────────────

  async function handleDownload(fileId: string, filename: string) {
    const r = await getFileDownloadUrl(fileId);
    if (!r.ok) {
      toast.error(r.error.message ?? "Failed to get download link.");
      return;
    }
    window.open(r.data.download_url, "_blank", "noopener,noreferrer");
  }

  // ── Delete ────────────────────────────────────────────────

  async function handleDelete(fileId: string) {
    setDeletingId(fileId);
    const r = await deleteFile(fileId);
    setDeletingId(null);
    setConfirmDeleteId(null);
    if (!r.ok) {
      toast.error(r.error.message ?? "Failed to delete file.");
      return;
    }
    toast.success("File deleted.");
    setFiles((f) => f.filter((x) => x.id !== fileId));
    setTotal((t) => t - 1);
  }

  const uploading = uploadState.status === "uploading";

  return (
    <div className="files-page">
      <header className="files-header">
        <div>
          <h2 className="files-title">Files</h2>
          <p className="files-subtitle">
            Securely upload and manage clinical documents.
          </p>
        </div>
      </header>

      {/* Storage degraded error */}
      {storageError && (
        <div className="files-storage-error" role="alert">
          <strong>Storage unavailable</strong>
          <p>{storageError}</p>
          <button onClick={() => loadFiles(page)}>Retry</button>
        </div>
      )}

      {/* Drop zone */}
      <div
        id="files-dropzone"
        className={`files-dropzone ${isDragging ? "files-dropzone--over" : ""} ${uploading ? "files-dropzone--uploading" : ""}`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        role="region"
        aria-label="File upload drop zone"
        aria-disabled={uploading}
      >
        {uploadState.status === "idle" && (
          <>
            <div className="files-drop-icon" aria-hidden="true">📁</div>
            <p className="files-drop-text">
              Drag &amp; drop a file here, or{" "}
              <button
                id="files-browse-btn"
                className="files-browse-link"
                onClick={() => fileInputRef.current?.click()}
                type="button"
              >
                browse
              </button>
            </p>
            <p className="files-drop-hint">
              Max 50 MB · PDF, Images, CSV, XLSX, TXT, DICOM
            </p>
          </>
        )}

        {uploadState.status === "uploading" && (
          <div className="files-upload-progress" aria-live="polite">
            <p className="files-upload-name">{uploadState.name}</p>
            <div
              className="files-progress-bar-track"
              role="progressbar"
              aria-valuenow={uploadState.progress}
              aria-valuemin={0}
              aria-valuemax={100}
            >
              <div
                className="files-progress-bar-fill"
                style={{ width: `${uploadState.progress}%` }}
              />
            </div>
            <p className="files-upload-pct">{uploadState.progress}%</p>
          </div>
        )}

        {uploadState.status === "success" && (
          <div className="files-upload-success" aria-live="polite">
            <span className="files-upload-check" aria-hidden="true">✅</span>
            <p>'{uploadState.name}' uploaded</p>
          </div>
        )}

        {uploadState.status === "error" && (
          <div className="files-upload-error" role="alert" aria-live="assertive">
            <span aria-hidden="true">❌</span>
            <div>
              <strong>Upload failed</strong>
              <p>{uploadState.message}</p>
            </div>
            <button
              className="files-retry-btn"
              onClick={() => setUploadState({ status: "idle" })}
            >
              Dismiss
            </button>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          id="files-input"
          className="files-input-hidden"
          onChange={onFileInput}
          accept={[...ALLOWED_EXTS].join(",")}
          aria-label="File input"
          disabled={uploading}
        />
      </div>

      {/* File list */}
      <div className="files-list-section">
        <h3 className="files-list-heading">
          Your files {total > 0 && <span className="files-count">({total})</span>}
        </h3>

        {listLoading && (
          <div aria-busy="true">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="files-skeleton-row">
                <Skeleton height="1rem" width="40%" />
                <Skeleton height="0.875rem" width="20%" />
              </div>
            ))}
          </div>
        )}

        {!listLoading && total === 0 && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center py-20 text-center"
          >
            <motion.div 
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="w-20 h-20 bg-gradient-to-tr from-[var(--color-primary-100)] to-[var(--color-info-50)] rounded-full flex items-center justify-center mb-6 shadow-sm border-2 border-[var(--surface-secondary)]"
            >
              <FileStack className="w-10 h-10 text-[var(--color-primary-600)]" />
            </motion.div>
            <motion.h4 
              initial={{ y: 5, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="text-xl font-bold font-heading text-[var(--text-primary)] mb-2"
            >
              No Files Uploaded
            </motion.h4>
            <motion.p 
              initial={{ y: 5, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="text-[var(--text-secondary)] font-medium max-w-sm"
            >
              Your storage is empty. Drag and drop documents above to securely upload them to the clinical vault.
            </motion.p>
          </motion.div>
        )}

        {!listLoading && files.length > 0 && (
          <>
            <div className="files-table-wrap">
              <table className="files-table" aria-label="Uploaded files">
                <thead>
                  <tr>
                    <th scope="col">Filename</th>
                    <th scope="col">Type</th>
                    <th scope="col">Size</th>
                    <th scope="col">Status</th>
                    <th scope="col">Uploaded</th>
                    <th scope="col">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {files.map((f) => (
                    <tr key={f.id}>
                      <td className="files-filename" title={f.original_filename}>
                        {f.original_filename.length > 40
                          ? f.original_filename.slice(0, 38) + "…"
                          : f.original_filename}
                      </td>
                      <td className="files-mime">{f.mime_type.split("/")[1] ?? f.mime_type}</td>
                      <td>{formatBytes(f.size_bytes)}</td>
                      <td>
                        <span className={`files-status files-status--${f.scan_status}`}>
                          {f.scan_status}
                        </span>
                      </td>
                      <td>
                        <time dateTime={f.created_at}>
                          {new Date(f.created_at).toLocaleDateString()}
                        </time>
                      </td>
                      <td className="files-actions-cell">
                        <button
                          id={`download-btn-${f.id}`}
                          className="files-download-btn"
                          onClick={() => handleDownload(f.id, f.original_filename)}
                          title="Download"
                          aria-label={`Download ${f.original_filename}`}
                        >
                          ↓
                        </button>
                        <button
                          id={`delete-btn-${f.id}`}
                          className="files-delete-btn"
                          onClick={() => setConfirmDeleteId(f.id)}
                          title="Delete"
                          aria-label={`Delete ${f.original_filename}`}
                          disabled={deletingId === f.id}
                        >
                          🗑
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {pages > 1 && (
              <nav className="files-pagination" aria-label="Pages">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="files-page-btn"
                >
                  ← Previous
                </button>
                <span className="files-page-info">Page {page} of {pages}</span>
                <button
                  onClick={() => setPage((p) => Math.min(pages, p + 1))}
                  disabled={page >= pages}
                  className="files-page-btn"
                >
                  Next →
                </button>
              </nav>
            )}
          </>
        )}
      </div>

      {/* Delete confirmation dialog */}
      {confirmDeleteId && (
        <div
          className="files-confirm-overlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-dialog-title"
        >
          <div className="files-confirm-dialog">
            <h3 id="delete-dialog-title">Delete file?</h3>
            <p>This action is permanent and cannot be undone.</p>
            <div className="files-confirm-actions">
              <button
                onClick={() => setConfirmDeleteId(null)}
                className="files-confirm-cancel"
                disabled={deletingId === confirmDeleteId}
              >
                Cancel
              </button>
              <button
                id="confirm-delete-btn"
                onClick={() => handleDelete(confirmDeleteId)}
                className="files-confirm-delete"
                disabled={deletingId === confirmDeleteId}
                aria-busy={deletingId === confirmDeleteId}
              >
                {deletingId === confirmDeleteId ? "Deleting…" : "Delete permanently"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
