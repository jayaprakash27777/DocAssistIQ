/**
 * DocAssistIQ — Consultations List (Phase 20).
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import {
  listConsultations,
  createConsultation,
  type ConsultationResponse,
  type ConsultationSummary,
} from "@/lib/api";

export default function ConsultationsListPage() {
  const { toast } = useToast();
  const router = useRouter();
  const [consultations, setConsultations] = useState<ConsultationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const fetchConsultations = useCallback(async () => {
    setLoading(true);
    const r = await listConsultations();
    setLoading(false);
    if (r.ok) {
      setConsultations(r.data.items);
    } else {
      toast.error(r.error.message || "Failed to load consultations");
    }
  }, [toast]);

  useEffect(() => {
    fetchConsultations();
  }, [fetchConsultations]);

  const handleCreate = async () => {
    setCreating(true);
    const r = await createConsultation();
    setCreating(false);
    if (r.ok) {
      toast.success("New consultation created");
      router.push(`/consultations/${r.data.id}`);
    } else {
      toast.error(r.error.message || "Failed to create consultation");
    }
  };

  return (
    <div className="consultations-page" style={{ maxWidth: "1000px" }}>
      <header className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <h2 className="page-title">My Consultations</h2>
          <p className="page-subtitle">View and manage clinical sessions.</p>
        </div>
        <button className="btn-primary" onClick={handleCreate} disabled={creating}>
          {creating ? "Creating..." : "+ New Consultation"}
        </button>
      </header>

      <div style={{ marginTop: "2rem" }}>
        {loading ? (
          <div className="data-table">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} style={{ padding: "1rem", borderBottom: "1px solid var(--border-subtle)" }}>
                <Skeleton height="1.5rem" width="100%" />
              </div>
            ))}
          </div>
        ) : (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID / Time</th>
                  <th>Patient Session</th>
                  <th>Status</th>
                  <th>Notes Length</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {consultations.map(c => (
                  <tr key={c.id}>
                    <td>
                      <div><strong>{c.id.substring(0, 8)}</strong></div>
                      <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                        {new Date(c.created_at).toLocaleString()}
                      </div>
                    </td>
                    <td>
                      <code style={{ fontSize: "0.8125rem" }}>
                        --
                      </code>
                    </td>
                    <td>
                      <span className={`status-badge status-${c.status.toLowerCase()}`}>
                        {c.status.toUpperCase()}
                      </span>
                    </td>
                    <td>{c.input_preview?.length || 0} chars</td>
                    <td>
                      <Link href={`/consultations/${c.id}`} className="btn-secondary btn-sm">
                        Open Room
                      </Link>
                    </td>
                  </tr>
                ))}
                {consultations.length === 0 && (
                  <tr>
                    <td colSpan={5} style={{ textAlign: "center", padding: "3rem", color: "var(--text-secondary)" }}>
                      <div style={{ fontSize: "2rem", marginBottom: "1rem" }}>🩺</div>
                      <div style={{ fontWeight: 600 }}>No consultations yet</div>
                      <div style={{ fontSize: "0.875rem", marginTop: "0.5rem" }}>
                        Start a new consultation to begin analyzing clinical notes.
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
