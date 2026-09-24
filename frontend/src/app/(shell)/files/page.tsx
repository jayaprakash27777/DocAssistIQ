/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable react/no-unescaped-entities */
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
import { motion, AnimatePresence, Variants } from "framer-motion";
import { FileStack, UploadCloud, Download, Trash2, AlertCircle, CheckCircle2, XCircle, FileIcon, Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

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

  function validateFile(file: File): string | null {
    if (file.size === 0) return "File is empty.";
    if (file.size > MAX_SIZE_BYTES) return `File exceeds 50 MB limit (${formatBytes(file.size)}).`;
    const ext = getExt(file.name);
    if (!ALLOWED_EXTS.has(ext)) {
      return `Extension '${ext || "(none)"}' is not allowed.`;
    }
    return null;
  }

  async function handleUpload(file: File) {
    const err = validateFile(file);
    if (err) {
      setUploadState({ status: "error", message: err, name: file.name });
      return;
    }

    setUploadState({ status: "uploading", progress: 0, name: file.name });

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

  async function handleDownload(fileId: string, filename: string) {
    const r = await getFileDownloadUrl(fileId);
    if (!r.ok) {
      toast.error(r.error.message ?? "Failed to get download link.");
      return;
    }
    window.open(r.data.download_url, "_blank", "noopener,noreferrer");
  }

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

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <motion.div 
      className="max-w-5xl mx-auto px-4 py-8"
      variants={containerVariants}
      initial="hidden"
      animate="show"
    >
      <header className="mb-10">
        <motion.h1 variants={itemVariants} className="text-4xl font-extrabold font-heading text-[var(--text-primary)] tracking-tight mb-2">
          File Vault
        </motion.h1>
        <motion.p variants={itemVariants} className="text-lg text-[var(--text-secondary)] font-medium">
          Securely upload and manage clinical documents.
        </motion.p>
      </header>

      {storageError && (
        <motion.div variants={itemVariants} className="bg-red-50 border border-red-200 rounded-xl p-4 mb-8 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <div>
              <strong className="text-sm font-bold text-red-900 block">Storage unavailable</strong>
              <p className="text-xs text-red-700 font-medium mt-0.5">{storageError}</p>
            </div>
          </div>
          <Button variant="outline" onClick={() => loadFiles(page)} className="border-red-200 text-red-700 hover:bg-red-100 h-9">
            <RefreshCw className="w-4 h-4 mr-2" /> Retry
          </Button>
        </motion.div>
      )}

      {/* Dropzone */}
      <motion.div variants={itemVariants} className="mb-10">
        <div
          className={`relative border-2 border-dashed rounded-3xl p-10 transition-all duration-300 flex flex-col items-center justify-center text-center ${
            isDragging 
              ? "border-[var(--color-primary-500)] bg-[var(--color-primary-50)] scale-[1.02]" 
              : uploading 
                ? "border-[var(--color-primary-300)] bg-white/60 backdrop-blur-md shadow-sm" 
                : "border-[var(--border-strong)] bg-white/40 backdrop-blur-md hover:bg-white/80 hover:border-[var(--color-primary-400)] hover:shadow-md"
          }`}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          role="region"
          aria-disabled={uploading}
        >
          {uploadState.status === "idle" && (
            <>
              <div className={`w-20 h-20 rounded-full flex items-center justify-center mb-6 shadow-inner transition-colors duration-300 ${isDragging ? "bg-[var(--color-primary-100)] text-[var(--color-primary-600)]" : "bg-[var(--surface-sunken)] text-[var(--text-tertiary)]"}`}>
                <UploadCloud className="w-10 h-10" />
              </div>
              <h3 className="text-xl font-bold text-[var(--text-primary)] mb-2 font-heading">Upload Document</h3>
              <p className="text-[var(--text-secondary)] font-medium mb-6">
                Drag and drop a file here, or{" "}
                <button
                  className="text-[var(--color-primary-600)] font-bold hover:underline outline-none"
                  onClick={() => fileInputRef.current?.click()}
                  type="button"
                >
                  browse your computer
                </button>
              </p>
              <div className="flex flex-wrap gap-2 justify-center">
                {['PDF', 'Images', 'CSV', 'DICOM'].map(ext => (
                  <span key={ext} className="px-3 py-1 bg-white border border-[var(--border-default)] rounded-md text-[10px] font-bold text-[var(--text-tertiary)] uppercase shadow-sm">
                    {ext}
                  </span>
                ))}
                <span className="px-3 py-1 bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-md text-[10px] font-bold text-[var(--text-tertiary)] uppercase shadow-sm">
                  Max 50 MB
                </span>
              </div>
            </>
          )}

          {uploadState.status === "uploading" && (
            <div className="w-full max-w-md mx-auto py-4">
              <div className="flex justify-between items-end mb-3">
                <span className="font-bold text-[var(--color-primary-700)] text-sm truncate pr-4">{uploadState.name}</span>
                <span className="font-mono text-xs font-bold text-[var(--color-primary-600)]">{uploadState.progress}%</span>
              </div>
              <div className="w-full h-3 bg-[var(--color-primary-100)] rounded-full overflow-hidden shadow-inner">
                <motion.div
                  className="h-full bg-gradient-to-r from-[var(--color-primary-400)] to-[var(--color-primary-600)]"
                  initial={{ width: 0 }}
                  animate={{ width: `${uploadState.progress}%` }}
                  transition={{ duration: 0.2 }}
                />
              </div>
              <p className="text-xs text-[var(--text-tertiary)] font-bold mt-4 flex items-center justify-center gap-2 uppercase tracking-widest">
                <Loader2 className="w-4 h-4 animate-spin text-[var(--color-primary-500)]" /> Uploading to vault...
              </p>
            </div>
          )}

          {uploadState.status === "success" && (
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="flex flex-col items-center">
              <div className="w-16 h-16 bg-[var(--color-success-100)] rounded-full flex items-center justify-center mb-4 text-[var(--color-success-600)] shadow-sm">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <p className="text-lg font-bold text-[var(--text-primary)]">Upload Complete</p>
              <p className="text-sm text-[var(--text-secondary)] mt-1 truncate max-w-xs">{uploadState.name}</p>
            </motion.div>
          )}

          {uploadState.status === "error" && (
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="flex flex-col items-center">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4 text-red-600 shadow-sm">
                <XCircle className="w-8 h-8" />
              </div>
              <p className="text-lg font-bold text-red-700">Upload Failed</p>
              <p className="text-sm text-red-600/80 font-medium mt-1 mb-6 max-w-sm text-center leading-relaxed">{uploadState.message}</p>
              <Button variant="outline" onClick={() => setUploadState({ status: "idle" })} className="h-9 px-6 rounded-full border-red-200 text-red-700 hover:bg-red-50">
                Dismiss
              </Button>
            </motion.div>
          )}

          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={onFileInput}
            accept={[...ALLOWED_EXTS].join(",")}
            disabled={uploading}
          />
        </div>
      </motion.div>

      {/* File List */}
      <motion.div variants={itemVariants}>
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold font-heading text-[var(--text-primary)] flex items-center gap-3">
            Stored Documents
            {total > 0 && (
              <span className="px-2.5 py-0.5 bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-full text-xs text-[var(--text-secondary)] shadow-inner">
                {total}
              </span>
            )}
          </h3>
        </div>

        <div className="glass-panel-4k gpu-accelerated rounded-3xl border border-slate-200/90 bg-white/85 backdrop-blur-2xl shadow-[0_12px_36px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.9)] overflow-hidden relative z-10 ring-1 ring-black/5">
          {listLoading ? (
            <div className="p-6 space-y-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex items-center gap-4">
                  <Skeleton className="h-12 w-12 rounded-xl" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-1/3" />
                    <Skeleton className="h-3 w-1/4" />
                  </div>
                  <Skeleton className="h-8 w-8 rounded-md" />
                </div>
              ))}
            </div>
          ) : total === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-center bg-white/40">
              <div className="w-20 h-20 bg-[var(--surface-sunken)] rounded-2xl flex items-center justify-center mb-6 shadow-inner border-2 border-white/50 rotate-3">
                <FileStack className="w-10 h-10 text-[var(--text-tertiary)] -rotate-3" />
              </div>
              <h4 className="text-lg font-bold font-heading text-[var(--text-primary)] mb-2">Vault is Empty</h4>
              <p className="text-sm text-[var(--text-secondary)] font-medium max-w-sm">
                No documents found in your clinical storage.
              </p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-[var(--color-neutral-50)]/50 border-b border-[var(--border-default)]">
                      <th className="px-6 py-4 text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-wider">File</th>
                      <th className="px-6 py-4 text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-wider hidden sm:table-cell">Size</th>
                      <th className="px-6 py-4 text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-wider hidden md:table-cell">Status</th>
                      <th className="px-6 py-4 text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-wider hidden lg:table-cell">Date</th>
                      <th className="px-6 py-4 text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-wider text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-subtle)] bg-white/60">
                    {files.map((f) => (
                      <tr key={f.id} className="hover:bg-white transition-colors group">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-xl bg-[var(--surface-sunken)] border border-[var(--border-default)] flex items-center justify-center text-[var(--color-primary-500)] shrink-0 shadow-sm group-hover:scale-105 transition-transform">
                              <FileIcon className="w-5 h-5" />
                            </div>
                            <div className="min-w-0">
                              <p className="text-sm font-bold text-[var(--text-primary)] truncate max-w-[200px] sm:max-w-xs md:max-w-sm" title={f.original_filename}>
                                {f.original_filename}
                              </p>
                              <p className="text-xs text-[var(--text-tertiary)] font-medium mt-0.5 uppercase tracking-wider">
                                {f.mime_type.split("/")[1]?.substring(0,6) ?? 'FILE'}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-[var(--text-secondary)] font-medium hidden sm:table-cell">
                          {formatBytes(f.size_bytes)}
                        </td>
                        <td className="px-6 py-4 hidden md:table-cell">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-widest shadow-sm border ${
                            f.scan_status === 'CLEAN' ? 'bg-[var(--color-success-50)] text-[var(--color-success-700)] border-[var(--color-success-200)]' :
                            f.scan_status === 'INFECTED' ? 'bg-red-50 text-red-700 border-red-200' :
                            'bg-amber-50 text-amber-700 border-amber-200'
                          }`}>
                            {f.scan_status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-xs text-[var(--text-secondary)] font-medium hidden lg:table-cell">
                          {new Date(f.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex items-center justify-end gap-2 opacity-100 sm:opacity-50 sm:group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => handleDownload(f.id, f.original_filename)}
                              className="p-2 text-[var(--color-primary-600)] hover:bg-[var(--color-primary-50)] rounded-lg transition-colors border border-transparent hover:border-[var(--color-primary-200)]"
                              title="Download"
                            >
                              <Download className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => setConfirmDeleteId(f.id)}
                              disabled={deletingId === f.id}
                              className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-transparent hover:border-red-200 disabled:opacity-50"
                              title="Delete"
                            >
                              {deletingId === f.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {pages > 1 && (
                <div className="px-6 py-4 border-t border-[var(--border-default)] flex items-center justify-between bg-[var(--color-neutral-50)]/50">
                  <Button
                    variant="outline"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="h-8 text-xs font-bold"
                  >
                    Previous
                  </Button>
                  <span className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-widest">
                    Page {page} of {pages}
                  </span>
                  <Button
                    variant="outline"
                    onClick={() => setPage((p) => Math.min(pages, p + 1))}
                    disabled={page >= pages}
                    className="h-8 text-xs font-bold"
                  >
                    Next
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </motion.div>

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {confirmDeleteId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
              onClick={() => setConfirmDeleteId(null)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="dashboard-card !block w-full max-w-md p-6 relative z-10 shadow-2xl"
            >
              <div className="w-12 h-12 rounded-full bg-red-100 text-red-600 flex items-center justify-center mb-4 relative z-10 border border-red-200 shadow-sm">
                <AlertCircle className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-[var(--text-primary)] mb-2 font-heading relative z-10">Delete File?</h3>
              <p className="text-[var(--text-secondary)] text-sm mb-8 relative z-10 font-medium">
                Are you sure you want to permanently delete this document? This action cannot be undone and will remove it from the clinical vault.
              </p>
              <div className="flex gap-3 justify-end relative z-10 border-t border-[var(--border-default)] pt-5">
                <Button
                  variant="outline"
                  onClick={() => setConfirmDeleteId(null)}
                  disabled={deletingId === confirmDeleteId}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  onClick={() => handleDelete(confirmDeleteId)}
                  disabled={deletingId === confirmDeleteId}
                  className="bg-red-600 hover:bg-red-700 text-white border-transparent shadow-md gap-2"
                >
                  {deletingId === confirmDeleteId ? (
                    <><Loader2 className="w-4 h-4 animate-spin"/> Deleting...</>
                  ) : (
                    <><Trash2 className="w-4 h-4"/> Delete Permanently</>
                  )}
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
