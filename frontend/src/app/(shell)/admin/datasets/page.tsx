/**
 * DocAssistIQ — Dataset Registry Dashboard (Phase 17).
 *
 * Enforces dataset metadata, validation checks (PII, malformed, leakage),
 * and approval states before a dataset can be consumed by ML pipelines.
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import {
  listDatasets,
  registerDataset,
  validateDataset,
  approveDataset,
  type DatasetResponse,
  type DatasetValidationResult,
} from "@/lib/api";

export default function DatasetsPage() {
  const { toast } = useToast();
  const [datasets, setDatasets] = useState<DatasetResponse[]>([]);
  const [loading, setLoading] = useState(true);

  // Validation modal state
  const [validatingDataset, setValidatingDataset] = useState<DatasetResponse | null>(null);
  const [validationResult, setValidationResult] = useState<DatasetValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  const fetchDatasets = useCallback(async () => {
    setLoading(true);
    const r = await listDatasets();
    setLoading(false);
    if (!r.ok) {
      toast.error(r.error.message || "Failed to load datasets");
      return;
    }
    setDatasets(r.data);
  }, [toast]);

  useEffect(() => {
    fetchDatasets();
  }, [fetchDatasets]);

  async function handleCreateMockDataset() {
    const r = await registerDataset({
      name: "mimic-iv-notes-filtered",
      source: "MIMIC-IV v2.2",
      license: "PhysioNet Credentialed",
      version: "1.0.0",
      hash: "sha256-pending",
      schema_def: { required: ["text", "label"] },
      intended_use: "Training symptom NER model",
      limitations: "Contains ICU patients only. Biased towards severe conditions.",
      storage_path: "data/raw/sample.jsonl",
    });
    
    if (!r.ok) {
      toast.error(r.error.message || "Failed to register dataset");
      return;
    }
    toast.success("Dataset registered successfully");
    fetchDatasets();
  }

  async function handleValidate(dataset: DatasetResponse) {
    setValidatingDataset(dataset);
    setValidationResult(null);
    setIsValidating(true);
    
    const r = await validateDataset(dataset.id);
    setIsValidating(false);
    
    if (!r.ok) {
      toast.error(r.error.message || "Validation pipeline failed");
      return;
    }
    
    setValidationResult(r.data);
    
    // Refresh to show updated approval status
    fetchDatasets();
  }

  async function handleApprove(datasetId: string) {
    const r = await approveDataset(datasetId);
    if (!r.ok) {
      toast.error(r.error.message || "Failed to approve dataset");
      return;
    }
    toast.success("Dataset approved for ML pipelines.");
    setValidatingDataset(null);
    fetchDatasets();
  }

  return (
    <div className="admin-datasets-page" style={{ maxWidth: "1200px" }}>
      <header className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <h2 className="page-title">Dataset Registry & Governance</h2>
          <p className="page-subtitle">
            Manage ML datasets. De-identification and strict validation are mandatory.
          </p>
        </div>
        <button className="btn-primary" onClick={handleCreateMockDataset}>
          + Register Dataset
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
                  <th>Dataset Name</th>
                  <th>Version</th>
                  <th>Source</th>
                  <th>Status</th>
                  <th>Safety/PII</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map(ds => (
                  <tr key={ds.id}>
                    <td>
                      <strong>{ds.name}</strong>
                      <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
                        {ds.record_count > 0 ? `${ds.record_count.toLocaleString()} records` : "Unvalidated"}
                      </div>
                    </td>
                    <td><code>v{ds.version}</code></td>
                    <td>{ds.source}</td>
                    <td>
                      <span className={`status-badge status-${ds.approval_status.toLowerCase()}`}>
                        {ds.approval_status}
                      </span>
                    </td>
                    <td>
                      {ds.is_deidentified ? (
                        <span className="badge" style={{ background: "hsl(140 100% 95%)", color: "hsl(140 100% 30%)" }}>✓ De-identified</span>
                      ) : (
                        <span className="badge" style={{ background: "hsl(0 100% 95%)", color: "hsl(0 100% 40%)" }}>⚠ Not Cleared</span>
                      )}
                    </td>
                    <td>
                      {ds.approval_status === "pending" || ds.approval_status === "rejected" ? (
                        <button className="btn-secondary btn-sm" onClick={() => handleValidate(ds)}>
                          Run Validation
                        </button>
                      ) : (
                        <button className="btn-secondary btn-sm" disabled>
                          Approved
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {datasets.length === 0 && (
                  <tr>
                    <td colSpan={6} style={{ textAlign: "center", padding: "3rem", color: "var(--text-secondary)" }}>
                      No datasets registered.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Validation Modal */}
      {validatingDataset && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: "700px", width: "90%" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.5rem" }}>
              <div>
                <h3 style={{ margin: "0 0 0.5rem" }}>Dataset Validation Report</h3>
                <code style={{ fontSize: "0.875rem" }}>{validatingDataset.name} v{validatingDataset.version}</code>
              </div>
              <button 
                onClick={() => setValidatingDataset(null)} 
                style={{ background: "none", border: "none", fontSize: "1.5rem", cursor: "pointer", color: "var(--text-secondary)" }}
              >
                &times;
              </button>
            </div>

            {isValidating ? (
              <div style={{ textAlign: "center", padding: "3rem 0" }}>
                <div className="spinner" style={{ margin: "0 auto 1rem" }}></div>
                <p>Executing validation pipeline (PII, schema, leakage)...</p>
              </div>
            ) : validationResult ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                <div style={{ 
                  padding: "1rem", 
                  borderRadius: "8px", 
                  background: validationResult.is_valid && !validationResult.pii_detected ? "hsl(140 100% 97%)" : "hsl(0 100% 97%)",
                  border: `1px solid ${validationResult.is_valid && !validationResult.pii_detected ? "hsl(140 100% 80%)" : "hsl(0 100% 80%)"}`
                }}>
                  <h4 style={{ margin: "0 0 0.5rem", color: validationResult.is_valid && !validationResult.pii_detected ? "hsl(140 100% 30%)" : "hsl(0 100% 40%)" }}>
                    {validationResult.is_valid && !validationResult.pii_detected ? "Validation Passed" : "Validation Failed"}
                  </h4>
                  <p style={{ margin: 0, fontSize: "0.9375rem" }}>
                    Processed {validationResult.record_count.toLocaleString()} records.
                  </p>
                </div>

                <div className="data-table-container">
                  <table className="data-table" style={{ fontSize: "0.875rem" }}>
                    <tbody>
                      <tr>
                        <td><strong>Missing Values</strong></td>
                        <td style={{ color: validationResult.missing_values > 0 ? "var(--error)" : "inherit" }}>{validationResult.missing_values}</td>
                      </tr>
                      <tr>
                        <td><strong>Malformed Records</strong></td>
                        <td style={{ color: validationResult.malformed > 0 ? "var(--error)" : "inherit" }}>{validationResult.malformed}</td>
                      </tr>
                      <tr>
                        <td><strong>Exact Duplicates</strong></td>
                        <td style={{ color: validationResult.duplicates > 0 ? "var(--error)" : "inherit" }}>{validationResult.duplicates}</td>
                      </tr>
                      <tr>
                        <td><strong>Label Conflicts</strong></td>
                        <td style={{ color: validationResult.label_conflicts > 0 ? "var(--error)" : "inherit" }}>{validationResult.label_conflicts}</td>
                      </tr>
                      <tr>
                        <td><strong>Data Leakage</strong></td>
                        <td style={{ color: validationResult.leakage_detected ? "var(--error)" : "inherit" }}>
                          {validationResult.leakage_detected ? "DETECTED" : "None"}
                        </td>
                      </tr>
                      <tr>
                        <td><strong>PII Detection</strong></td>
                        <td style={{ color: validationResult.pii_detected ? "var(--error)" : "var(--success)", fontWeight: "600" }}>
                          {validationResult.pii_detected ? "FAILED CLOSED (PII DETECTED)" : "CLEARED"}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {validationResult.errors.length > 0 && (
                  <div style={{ background: "var(--surface-base)", padding: "1rem", borderRadius: "6px" }}>
                    <h5 style={{ margin: "0 0 0.5rem" }}>Error Logs</h5>
                    <ul style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.875rem", color: "var(--error)" }}>
                      {validationResult.errors.map((err, i) => (
                        <li key={i}>{err}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div style={{ display: "flex", justifyContent: "flex-end", gap: "1rem", marginTop: "1rem" }}>
                  <button className="btn-secondary" onClick={() => setValidatingDataset(null)}>
                    Close
                  </button>
                  {validationResult.is_valid && !validationResult.pii_detected && (
                    <button className="btn-primary" onClick={() => handleApprove(validatingDataset.id)}>
                      Approve Dataset for ML
                    </button>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
