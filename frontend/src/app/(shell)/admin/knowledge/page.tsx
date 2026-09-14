/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/**
 * DocAssistIQ — Knowledge Review Dashboard (Phase 14).
 *
 * Admin view to review, approve, reject, or supersede ingested knowledge entities.
 * Includes provenance inspection before approval.
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import {
  listPendingKnowledge,
  reviewKnowledge,
  inspectProvenance,
  syncEmbedding,
  type KnowledgeEntityResponse,
  type ProvenanceItemResponse,
} from "@/lib/api";

type EntityType = "disease" | "symptom" | "investigation" | "medicine";

export default function KnowledgeReviewPage() {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<EntityType>("disease");
  const [entities, setEntities] = useState<KnowledgeEntityResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  // Provenance inspection modal
  const [inspectingEntity, setInspectingEntity] = useState<KnowledgeEntityResponse | null>(null);
  const [provenanceData, setProvenanceData] = useState<ProvenanceItemResponse[]>([]);
  const [provenanceLoading, setProvenanceLoading] = useState(false);

  const fetchEntities = useCallback(async () => {
    setLoading(true);
    const r = await listPendingKnowledge(activeTab, 1, 50);
    setLoading(false);
    if (!r.ok) {
      toast.error(r.error.message || `Failed to load pending ${activeTab}s`);
      return;
    }
    setEntities(r.data.items);
    setTotal(r.data.total);
  }, [activeTab, toast]);

  useEffect(() => {
    fetchEntities();
  }, [fetchEntities]);

  async function handleInspect(entity: KnowledgeEntityResponse) {
    setInspectingEntity(entity);
    setProvenanceLoading(true);
    const r = await inspectProvenance(activeTab, entity.id);
    setProvenanceLoading(false);
    
    if (r.ok) {
      setProvenanceData(r.data);
    } else {
      toast.error(r.error.message || "Failed to load provenance");
      setProvenanceData([]);
    }
  }

  async function handleReview(status: "APPROVED" | "REJECTED" | "SUPERSEDED") {
    if (!inspectingEntity) return;
    
    const r = await reviewKnowledge(activeTab, inspectingEntity.id, status);
    if (!r.ok) {
      toast.error(r.error.message || `Failed to mark as ${status}`);
      return;
    }
    
    toast.success(`${inspectingEntity.name} marked as ${status}`);
    setInspectingEntity(null);
    fetchEntities();
  }

  async function handleSyncEmbedding() {
    if (!inspectingEntity) return;
    
    toast.success(`Syncing embedding for ${inspectingEntity.name}...`);
    const r = await syncEmbedding(activeTab, inspectingEntity.id);
    
    if (r.ok) {
      toast.success(`Embedding generated (${r.data.dimensions}d, model: ${r.data.model})`);
    } else {
      toast.error(r.error.message || "Failed to generate embedding");
    }
  }

  return (
    <div className="admin-knowledge-page" style={{ maxWidth: "1200px" }}>
      <header className="page-header">
        <div>
          <h2 className="page-title">Clinical Knowledge Review</h2>
          <p className="page-subtitle">
            Safely review and publish parsed knowledge to the active clinical system.
          </p>
        </div>
      </header>

      <div className="tabs">
        {(["disease", "symptom", "investigation", "medicine"] as const).map(tab => (
          <button
            key={tab}
            className={`tab ${activeTab === tab ? "active" : ""}`}
            onClick={() => setActiveTab(tab)}
            style={{ textTransform: "capitalize", padding: "0.5rem 1rem", border: "none", borderBottom: activeTab === tab ? "2px solid var(--primary)" : "2px solid transparent", background: "none", fontWeight: activeTab === tab ? "600" : "400", cursor: "pointer", color: activeTab === tab ? "var(--primary)" : "var(--text-secondary)" }}
          >
            {tab}s
          </button>
        ))}
      </div>

      <div style={{ marginTop: "1rem" }}>
        {loading ? (
          <div className="data-table">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} style={{ padding: "1rem", borderBottom: "1px solid var(--border-subtle)" }}>
                <Skeleton height="1.5rem" width="40%" />
              </div>
            ))}
          </div>
        ) : (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Name</th>
                  <th>Status</th>
                  <th>AI Generated</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {entities.map(entity => (
                  <tr key={entity.id}>
                    <td><code>{entity.code}</code></td>
                    <td><strong>{entity.name}</strong></td>
                    <td><span className="status-badge status-pending">{entity.status}</span></td>
                    <td>
                      {entity.is_ai_generated ? (
                        <span className="badge" style={{ background: "hsl(30 100% 95%)", color: "hsl(30 100% 30%)" }}>AI Extracted</span>
                      ) : (
                        <span className="badge" style={{ background: "hsl(220 20% 95%)", color: "hsl(220 20% 40%)" }}>Manual</span>
                      )}
                    </td>
                    <td>
                      <button
                        className="btn-secondary btn-sm"
                        onClick={() => handleInspect(entity)}
                      >
                        Inspect & Review
                      </button>
                    </td>
                  </tr>
                ))}
                {entities.length === 0 && (
                  <tr>
                    <td colSpan={5} style={{ textAlign: "center", padding: "3rem", color: "var(--text-secondary)" }}>
                      No pending {activeTab}s awaiting review.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Review Modal */}
      {inspectingEntity && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: "800px", width: "90%" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.5rem" }}>
              <div>
                <h3 style={{ margin: "0 0 0.5rem", fontSize: "1.25rem" }}>Review: {inspectingEntity.name}</h3>
                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                  <code style={{ background: "var(--surface-base)", padding: "2px 6px", borderRadius: "4px" }}>{inspectingEntity.code}</code>
                  <span style={{ textTransform: "capitalize", fontSize: "0.875rem", color: "var(--text-secondary)" }}>{activeTab}</span>
                </div>
              </div>
              <button 
                onClick={() => setInspectingEntity(null)} 
                style={{ background: "none", border: "none", fontSize: "1.5rem", cursor: "pointer", color: "var(--text-secondary)" }}
              >
                &times;
              </button>
            </div>

            <div style={{ background: "hsl(220 20% 97%)", padding: "1rem", borderRadius: "8px", marginBottom: "1.5rem" }}>
              <h4 style={{ margin: "0 0 0.75rem", fontSize: "0.875rem", textTransform: "uppercase", color: "var(--text-secondary)" }}>Source Provenance</h4>
              
              {provenanceLoading ? (
                <Skeleton height="3rem" width="100%" />
              ) : provenanceData.length > 0 ? (
                <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "1rem" }}>
                  {provenanceData.map((prov) => (
                    <li key={prov.id} style={{ background: "white", padding: "1rem", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                        <strong>{prov.source_name} <code>({prov.source_code})</code></strong>
                        <div style={{ display: "flex", gap: "0.5rem" }}>
                          {prov.evidence_grade && <span className="badge" style={{ background: "hsl(220 100% 95%)", color: "var(--primary)" }}>Level {prov.evidence_grade}</span>}
                          {prov.is_ai_extracted && <span className="badge" style={{ background: "hsl(30 100% 95%)", color: "hsl(30 100% 30%)" }}>AI Extracted</span>}
                        </div>
                      </div>
                      <p style={{ margin: 0, fontSize: "0.9375rem", color: "var(--text-primary)" }}>{prov.claim}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ margin: 0, fontStyle: "italic", color: "var(--text-secondary)" }}>No specific evidence claims attached to this entity.</p>
              )}
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid var(--border-subtle)", paddingTop: "1.5rem" }}>
              <button 
                className="btn-secondary" 
                onClick={handleSyncEmbedding}
                style={{ fontSize: "0.875rem" }}
              >
                ⟳ Generate Embedding
              </button>
              
              <div style={{ display: "flex", gap: "1rem" }}>
                <button className="btn-secondary" onClick={() => handleReview("REJECTED")}>
                  Reject (Do Not Publish)
                </button>
                <button className="btn-secondary" onClick={() => handleReview("SUPERSEDED")}>
                  Mark as Superseded
                </button>
                <button className="btn-primary" onClick={() => handleReview("APPROVED")}>
                  Approve for Production
                </button>
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
