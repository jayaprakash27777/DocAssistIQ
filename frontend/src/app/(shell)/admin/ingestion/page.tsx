/**
 * DocAssistIQ — Knowledge Ingestion Dashboard (Phase 13).
 *
 * Admin view to monitor Celery ingestion jobs and review parsed knowledge.
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import {
  listIngestionJobs,
  startIngestionJob,
  reviewIngestionJob,
  listSources,
  type IngestionJobResponse,
  type SourceResponse,
} from "@/lib/api";

export default function IngestionAdminPage() {
  const { toast } = useToast();
  const [jobs, setJobs] = useState<IngestionJobResponse[]>([]);
  const [sources, setSources] = useState<SourceResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  // Modal
  const [showModal, setShowModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedSource, setSelectedSource] = useState("");
  const [sourceVersion, setSourceVersion] = useState("");

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    const r = await listIngestionJobs(1, 100);
    setLoading(false);
    if (!r.ok) {
      toast.error(r.error.message || "Failed to load jobs");
      return;
    }
    setJobs(r.data.items);
    setTotal(r.data.total);
  }, [toast]);

  const fetchSources = useCallback(async () => {
    const r = await listSources(1, 100);
    if (r.ok) {
      setSources(r.data.items.filter(s => s.is_production_suitable));
    }
  }, []);

  useEffect(() => {
    fetchJobs();
    fetchSources();
    
    // Simple polling for jobs since they run in background
    const interval = setInterval(fetchJobs, 10000);
    return () => clearInterval(interval);
  }, [fetchJobs, fetchSources]);

  async function handleStartJob(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedSource) {
      toast.error("Please select a verified source.");
      return;
    }

    setIsSubmitting(true);
    const r = await startIngestionJob({
      source_id: selectedSource,
      source_version: sourceVersion || undefined,
    });
    setIsSubmitting(false);

    if (!r.ok) {
      toast.error(r.error.message || "Failed to start ingestion job");
      return;
    }
    
    toast.success("Ingestion job started in background.");
    setShowModal(false);
    fetchJobs();
  }

  async function handleReview(jobId: string, status: "approved" | "rejected") {
    const r = await reviewIngestionJob(jobId, status);
    if (!r.ok) {
      toast.error(r.error.message || `Failed to mark job as ${status}`);
      return;
    }
    toast.success(`Job marked as ${status}.`);
    fetchJobs();
  }

  return (
    <div className="admin-ingestion-page" style={{ maxWidth: "1200px" }}>
      <header className="page-header">
        <div>
          <h2 className="page-title">Knowledge Ingestion Queue</h2>
          <p className="page-subtitle">
            Monitor background workers and review parsed medical knowledge ({total} jobs).
          </p>
        </div>
        <button
          className="btn-primary"
          onClick={() => setShowModal(true)}
        >
          Run Ingestion
        </button>
      </header>

      {loading && jobs.length === 0 ? (
        <div className="data-table">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} style={{ padding: "1rem", borderBottom: "1px solid var(--border-subtle)" }}>
              <Skeleton height="1.5rem" width="30%" />
            </div>
          ))}
        </div>
      ) : (
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Job ID</th>
                <th>Source ID</th>
                <th>Version</th>
                <th>Status</th>
                <th>Validation</th>
                <th>Review</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id}>
                  <td>
                    <span style={{ fontFamily: "monospace", fontSize: "0.8rem" }}>
                      {job.id.substring(0, 8)}...
                    </span>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                      {new Date(job.created_at).toLocaleString()}
                    </div>
                  </td>
                  <td>
                    <span style={{ fontFamily: "monospace", fontSize: "0.8rem" }}>
                      {job.source_id.substring(0, 8)}...
                    </span>
                  </td>
                  <td>{job.source_version || "—"}</td>
                  <td>
                    <span className={`status-badge status-${job.status}`}>
                      {job.status}
                    </span>
                    {job.error_message && (
                      <div style={{ fontSize: "0.75rem", color: "var(--error)", marginTop: "4px", maxWidth: "200px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }} title={job.error_message}>
                        {job.error_message}
                      </div>
                    )}
                  </td>
                  <td>
                    {job.validation_result ? (
                       <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Has Result</span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>
                    <span className={`status-badge status-${job.review_status}`}>
                      {job.review_status}
                    </span>
                  </td>
                  <td>
                    {job.status === "completed" && job.review_status === "unreviewed" && (
                      <div style={{ display: "flex", gap: "0.5rem" }}>
                        <button
                          className="btn-primary btn-sm"
                          onClick={() => handleReview(job.id, "approved")}
                        >
                          Approve
                        </button>
                        <button
                          className="btn-secondary btn-sm"
                          onClick={() => handleReview(job.id, "rejected")}
                        >
                          Reject
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
              {jobs.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ textAlign: "center", padding: "2rem" }}>
                    No ingestion jobs found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Run Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: "400px" }}>
            <h3>Start Ingestion Pipeline</h3>
            <form onSubmit={handleStartJob} className="source-form">
              <div className="form-group">
                <label>Verified Source</label>
                <select 
                  value={selectedSource} 
                  onChange={e => setSelectedSource(e.target.value)}
                  required
                >
                  <option value="">-- Select Source --</option>
                  {sources.map(s => (
                    <option key={s.id} value={s.id}>{s.name} ({s.code})</option>
                  ))}
                </select>
                {sources.length === 0 && (
                  <p style={{ fontSize: "0.8rem", color: "var(--warning)", marginTop: "4px" }}>
                    No verified sources available. Verify a source first.
                  </p>
                )}
              </div>
              <div className="form-group">
                <label>Source Version (Optional)</label>
                <input 
                  value={sourceVersion} 
                  onChange={e => setSourceVersion(e.target.value)}
                  placeholder="e.g. 2026AA" 
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)} disabled={isSubmitting}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={isSubmitting || sources.length === 0}>
                  {isSubmitting ? "Starting..." : "Start Job"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
