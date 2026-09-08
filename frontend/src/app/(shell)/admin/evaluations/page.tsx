/**
 * DocAssistIQ — Evaluation Harness Dashboard (Phase 18).
 *
 * Runs strictly against the fixed held-out baseline_eval_set.jsonl
 * to verify model performance on clinical extraction, diagnosis, safety.
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import {
  listEvaluations,
  triggerEvaluation,
  getEvaluationDetails,
  executeEvaluationPipeline,
  listDatasets,
  type EvaluationRunResponse,
  type EvaluationRunDetailResponse,
  type DatasetResponse,
} from "@/lib/api";

export default function EvaluationsPage() {
  const { toast } = useToast();
  const [runs, setRuns] = useState<EvaluationRunResponse[]>([]);
  const [datasets, setDatasets] = useState<DatasetResponse[]>([]);
  const [loading, setLoading] = useState(true);

  // Detail modal state
  const [selectedRun, setSelectedRun] = useState<EvaluationRunDetailResponse | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    const [evalRes, dataRes] = await Promise.all([
      listEvaluations(),
      listDatasets()
    ]);
    
    setLoading(false);
    
    if (evalRes.ok) setRuns(evalRes.data);
    if (dataRes.ok) setDatasets(dataRes.data);
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  async function handleTriggerEval() {
    // Pick the first approved dataset
    const approvedDataset = datasets.find(d => d.approval_status === "approved");
    if (!approvedDataset) {
      toast.error("No approved datasets available. Go to Dataset Registry first.");
      return;
    }
    
    const r = await triggerEvaluation({
      dataset_id: approvedDataset.id,
      model_version: "baseline-v1-local",
    });
    
    if (!r.ok) {
      toast.error(r.error.message || "Failed to trigger evaluation");
      return;
    }
    
    toast.success("Evaluation run triggered.");
    fetchData();
  }

  async function handleExecuteRun(runId: string) {
    toast.success("Starting evaluation pipeline...");
    const r = await executeEvaluationPipeline(runId);
    if (!r.ok) {
      toast.error(r.error.message || "Pipeline execution failed");
    } else {
      toast.success("Pipeline completed!");
    }
    fetchData();
    if (selectedRun && selectedRun.id === runId) {
      viewDetails(runId);
    }
  }

  async function viewDetails(runId: string) {
    setLoadingDetails(true);
    const r = await getEvaluationDetails(runId);
    setLoadingDetails(false);
    if (!r.ok) {
      toast.error(r.error.message || "Failed to load details");
      return;
    }
    setSelectedRun(r.data);
  }

  return (
    <div className="admin-eval-page" style={{ maxWidth: "1200px" }}>
      <header className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <h2 className="page-title">Model Evaluation Harness</h2>
          <p className="page-subtitle">
            Execute repeatable evaluations on fixed hold-out datasets. 
          </p>
        </div>
        <button className="btn-primary" onClick={handleTriggerEval}>
          ▶ Run Baseline Evaluation
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
                  <th>Model Version</th>
                  <th>Dataset ID</th>
                  <th>Status</th>
                  <th>Accuracy</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {runs.map(run => {
                  const acc = run.metrics?.accuracy;
                  return (
                    <tr key={run.id}>
                      <td><strong>{run.model_version}</strong></td>
                      <td style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                        {run.dataset_id.split("-")[0]}...
                      </td>
                      <td>
                        <span className={`status-badge status-${run.status.toLowerCase()}`}>
                          {run.status.toUpperCase()}
                        </span>
                      </td>
                      <td>
                        {run.status === "completed" && acc !== undefined ? (
                          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                            <div style={{ width: "60px", height: "6px", background: "var(--border-subtle)", borderRadius: "3px" }}>
                              <div style={{ width: `${acc * 100}%`, height: "100%", background: acc > 0.8 ? "var(--success)" : "var(--primary)", borderRadius: "3px" }} />
                            </div>
                            <span>{(acc * 100).toFixed(1)}%</span>
                          </div>
                        ) : (
                          <span style={{ color: "var(--text-secondary)" }}>--</span>
                        )}
                      </td>
                      <td>
                        {run.status === "pending" ? (
                          <button className="btn-secondary btn-sm" onClick={() => handleExecuteRun(run.id)}>
                            Execute
                          </button>
                        ) : (
                          <button className="btn-secondary btn-sm" onClick={() => viewDetails(run.id)}>
                            View Results
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {runs.length === 0 && (
                  <tr>
                    <td colSpan={5} style={{ textAlign: "center", padding: "3rem", color: "var(--text-secondary)" }}>
                      No evaluation runs yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Details Modal */}
      {selectedRun && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: "800px", width: "90%", maxHeight: "90vh", overflowY: "auto" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.5rem" }}>
              <div>
                <h3 style={{ margin: "0 0 0.5rem" }}>Evaluation Results</h3>
                <code style={{ fontSize: "0.875rem" }}>{selectedRun.model_version} on Dataset {selectedRun.dataset_id.split("-")[0]}</code>
              </div>
              <button 
                onClick={() => setSelectedRun(null)} 
                style={{ background: "none", border: "none", fontSize: "1.5rem", cursor: "pointer", color: "var(--text-secondary)" }}
              >
                &times;
              </button>
            </div>

            <div style={{ display: "flex", gap: "2rem", marginBottom: "2rem" }}>
              <div style={{ flex: 1, padding: "1.5rem", background: "var(--surface-base)", borderRadius: "8px", textAlign: "center" }}>
                <div style={{ fontSize: "2rem", fontWeight: "600", color: "var(--primary)" }}>
                  {selectedRun.metrics?.accuracy !== undefined ? `${(selectedRun.metrics.accuracy * 100).toFixed(1)}%` : "--"}
                </div>
                <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>Overall Accuracy</div>
              </div>
              <div style={{ flex: 1, padding: "1.5rem", background: "var(--surface-base)", borderRadius: "8px", textAlign: "center" }}>
                <div style={{ fontSize: "2rem", fontWeight: "600" }}>
                  {selectedRun.metrics?.correct_records ?? 0} / {selectedRun.metrics?.total_records ?? 0}
                </div>
                <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>Correct Records</div>
              </div>
            </div>

            <h4 style={{ margin: "0 0 1rem" }}>Record Breakdown</h4>
            <div className="data-table-container">
              <table className="data-table" style={{ fontSize: "0.875rem" }}>
                <thead>
                  <tr>
                    <th>Task</th>
                    <th>Record ID</th>
                    <th>Correct</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedRun.results.map(res => (
                    <tr key={res.id}>
                      <td><span className="badge" style={{ background: "var(--surface-base)" }}>{res.task_type}</span></td>
                      <td><code>{res.record_identifier.substring(0,8)}</code></td>
                      <td>
                        {res.is_correct ? (
                          <span style={{ color: "var(--success)", fontWeight: "600" }}>✓ Yes</span>
                        ) : (
                          <span style={{ color: "var(--error)", fontWeight: "600" }}>✗ No</span>
                        )}
                      </td>
                      <td>
                        <details>
                          <summary style={{ cursor: "pointer", color: "var(--primary)" }}>View Data</summary>
                          <div style={{ padding: "0.5rem", background: "var(--surface-base)", marginTop: "0.5rem", borderRadius: "4px" }}>
                            <strong>Ground Truth:</strong>
                            <pre style={{ margin: "0.25rem 0 1rem", fontSize: "0.75rem", whiteSpace: "pre-wrap" }}>
                              {JSON.stringify(res.ground_truth, null, 2)}
                            </pre>
                            <strong>Model Output:</strong>
                            <pre style={{ margin: "0.25rem 0 0", fontSize: "0.75rem", whiteSpace: "pre-wrap" }}>
                              {JSON.stringify(res.model_output, null, 2)}
                            </pre>
                          </div>
                        </details>
                      </td>
                    </tr>
                  ))}
                  {selectedRun.results.length === 0 && (
                    <tr>
                      <td colSpan={4} style={{ textAlign: "center", padding: "2rem", color: "var(--text-secondary)" }}>
                        No record results available.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "1.5rem" }}>
              <button className="btn-secondary" onClick={() => setSelectedRun(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
