/**
 * DocAssistIQ — Source Management Dashboard (Phase 12).
 *
 * Admin view to list, register, and verify medical knowledge sources.
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import {
  listSources,
  createSource,
  verifySource,
  type SourceResponse,
  type SourceCreate,
} from "@/lib/api";

export default function SourcesAdminPage() {
  const { toast } = useToast();
  const [sources, setSources] = useState<SourceResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  // New source modal state
  const [showModal, setShowModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchSources = useCallback(async () => {
    setLoading(true);
    const r = await listSources(1, 100); // Admin lists all for now
    setLoading(false);
    if (!r.ok) {
      toast.error(r.error.message || "Failed to load sources");
      return;
    }
    setSources(r.data.items);
    setTotal(r.data.total);
  }, [toast]);

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  async function handleVerify(sourceId: string) {
    const r = await verifySource(sourceId);
    if (!r.ok) {
      toast.error(r.error.message || "Failed to verify source");
      return;
    }
    toast.success("Source verified for production.");
    fetchSources();
  }

  async function handleCreateSource(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const payload: SourceCreate = {
      code: fd.get("code") as string,
      organisation: fd.get("organisation") as string,
      name: fd.get("name") as string,
      base_url: (fd.get("base_url") as string) || undefined,
      access_mechanism: fd.get("access_mechanism") as string,
      data_type: fd.get("data_type") as string,
      license_info: (fd.get("license_info") as string) || undefined,
    };

    setIsSubmitting(true);
    const r = await createSource(payload);
    setIsSubmitting(false);

    if (!r.ok) {
      toast.error(r.error.message || "Failed to create source");
      return;
    }
    toast.success("Source registered successfully.");
    setShowModal(false);
    fetchSources();
  }

  return (
    <div className="admin-sources-page">
      <header className="page-header">
        <div>
          <h2 className="page-title">Medical Source Registry</h2>
          <p className="page-subtitle">
            Manage and verify clinical knowledge sources ({total} total).
          </p>
        </div>
        <button
          className="btn-primary"
          onClick={() => setShowModal(true)}
        >
          + Register Source
        </button>
      </header>

      {loading ? (
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
                <th>Code</th>
                <th>Name / Org</th>
                <th>Data Type</th>
                <th>Access</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((s) => (
                <tr key={s.id}>
                  <td><strong>{s.code}</strong></td>
                  <td>
                    {s.name}
                    <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                      {s.organisation}
                    </div>
                  </td>
                  <td><span className="badge">{s.data_type}</span></td>
                  <td>{s.access_mechanism}</td>
                  <td>
                    <span className={`status-badge status-${s.status}`}>
                      {s.status}
                    </span>
                    {s.is_production_suitable && (
                      <div style={{ fontSize: "0.75rem", color: "var(--primary)", marginTop: "4px" }}>
                        Verified
                      </div>
                    )}
                  </td>
                  <td>
                    {!s.is_production_suitable && (
                      <button
                        className="btn-secondary btn-sm"
                        onClick={() => handleVerify(s.id)}
                      >
                        Verify
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {sources.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ textAlign: "center", padding: "2rem" }}>
                    No sources registered.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Registration Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: "500px" }}>
            <h3>Register New Source</h3>
            <form onSubmit={handleCreateSource} className="source-form">
              <div className="form-group">
                <label>Source Code</label>
                <input name="code" required pattern="^[a-z0-9_]+$" title="Lowercase, numbers, underscores only" placeholder="e.g. pubmed_central" />
              </div>
              <div className="form-group">
                <label>Organisation</label>
                <input name="organisation" required placeholder="e.g. NIH / NLM" />
              </div>
              <div className="form-group">
                <label>Name</label>
                <input name="name" required placeholder="e.g. PubMed Central" />
              </div>
              <div className="form-group">
                <label>Base URL</label>
                <input type="url" name="base_url" placeholder="Optional URL" />
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Data Type</label>
                  <select name="data_type" required>
                    <option value="literature">Literature</option>
                    <option value="clinical_guidelines">Clinical Guidelines</option>
                    <option value="drug_database">Drug Database</option>
                    <option value="coding_system">Coding System</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Access Mechanism</label>
                  <select name="access_mechanism" required>
                    <option value="api">API</option>
                    <option value="bulk_download">Bulk Download</option>
                    <option value="licensed_feed">Licensed Feed</option>
                    <option value="manual">Manual</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>License / Access Terms</label>
                <textarea name="license_info" placeholder="Provide licensing details required for verification..." rows={3}></textarea>
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)} disabled={isSubmitting}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={isSubmitting}>
                  {isSubmitting ? "Registering..." : "Register Source"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
