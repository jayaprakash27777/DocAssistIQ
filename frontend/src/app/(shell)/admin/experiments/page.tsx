/**
 * DocAssistIQ — ML Experiments Dashboard (Phase 19).
 *
 * Provides a UI to view fully reproducible experiment metadata,
 * including commit hashes, dataset versions, and hyperparameters.
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import {
  listExperiments,
  getExperiment,
  type ExperimentResponse,
} from "@/lib/api";

export default function ExperimentsPage() {
  const { toast } = useToast();
  const [experiments, setExperiments] = useState<ExperimentResponse[]>([]);
  const [loading, setLoading] = useState(true);

  // Detail modal state
  const [selectedExp, setSelectedExp] = useState<ExperimentResponse | null>(null);

  const fetchExperiments = useCallback(async () => {
    setLoading(true);
    const r = await listExperiments();
    setLoading(false);
    
    if (!r.ok) {
      toast.error(r.error.message || "Failed to load experiments");
      return;
    }
    setExperiments(r.data);
  }, [toast]);

  useEffect(() => {
    fetchExperiments();
  }, [fetchExperiments]);

  async function viewDetails(expId: string) {
    const r = await getExperiment(expId);
    if (!r.ok) {
      toast.error(r.error.message || "Failed to load details");
      return;
    }
    setSelectedExp(r.data);
  }

  function formatDuration(seconds: number | null) {
    if (seconds === null) return "--";
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs.toFixed(0)}s`;
  }

  return (
    <div className="admin-exp-page" style={{ maxWidth: "1200px" }}>
      <header className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <h2 className="page-title">ML Experiment Tracking</h2>
          <p className="page-subtitle">
            Reproducible metadata, code commits, and artifacts from CLI pipeline executions.
          </p>
        </div>
        <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)", background: "var(--surface-base)", padding: "0.5rem 1rem", borderRadius: "6px" }}>
          <code>python cli/ml_experiment.py --help</code>
        </div>
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
                  <th>Experiment Name</th>
                  <th>Model / Dataset</th>
                  <th>Commit Hash</th>
                  <th>Status</th>
                  <th>Duration</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {experiments.map(exp => (
                  <tr key={exp.id}>
                    <td><strong>{exp.name}</strong></td>
                    <td>
                      <div>{exp.model_name}</div>
                      <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                        Dataset: {exp.dataset_version}
                      </div>
                    </td>
                    <td><code style={{ fontSize: "0.8125rem" }}>{exp.code_commit.substring(0, 7)}</code></td>
                    <td>
                      <span className={`status-badge status-${exp.status.toLowerCase()}`}>
                        {exp.status.toUpperCase()}
                      </span>
                    </td>
                    <td>{formatDuration(exp.execution_duration_sec)}</td>
                    <td>
                      <button className="btn-secondary btn-sm" onClick={() => viewDetails(exp.id)}>
                        Details
                      </button>
                    </td>
                  </tr>
                ))}
                {experiments.length === 0 && (
                  <tr>
                    <td colSpan={6} style={{ textAlign: "center", padding: "4rem 2rem", color: "var(--text-secondary)" }}>
                      <div style={{ fontSize: "2rem", marginBottom: "1rem" }}>🧪</div>
                      <div style={{ fontWeight: 600 }}>No experiments found</div>
                      <div style={{ fontSize: "0.875rem", marginTop: "0.5rem" }}>
                        Run the CLI tool to track your first experiment:<br />
                        <code style={{ background: "var(--surface-base)", padding: "0.25rem 0.5rem", borderRadius: "4px", display: "inline-block", marginTop: "0.5rem" }}>
                          python cli/ml_experiment.py --name my-first-run --dataset-version v1.0 --model-name bert
                        </code>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Details Modal */}
      {selectedExp && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: "800px", width: "90%", maxHeight: "90vh", overflowY: "auto" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.5rem" }}>
              <div>
                <h3 style={{ margin: "0 0 0.5rem" }}>Experiment: {selectedExp.name}</h3>
                <span className={`status-badge status-${selectedExp.status.toLowerCase()}`}>
                  {selectedExp.status.toUpperCase()}
                </span>
              </div>
              <button 
                onClick={() => setSelectedExp(null)} 
                style={{ background: "none", border: "none", fontSize: "1.5rem", cursor: "pointer", color: "var(--text-secondary)" }}
              >
                &times;
              </button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginBottom: "2rem" }}>
              {/* Left Column: Reproducibility */}
              <div style={{ background: "var(--surface-base)", padding: "1rem", borderRadius: "8px" }}>
                <h4 style={{ margin: "0 0 1rem", fontSize: "0.875rem", textTransform: "uppercase", color: "var(--text-secondary)" }}>
                  Reproducibility
                </h4>
                <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: "0.75rem", fontSize: "0.875rem" }}>
                  <span style={{ color: "var(--text-secondary)" }}>Commit:</span>
                  <code>{selectedExp.code_commit}</code>
                  
                  <span style={{ color: "var(--text-secondary)" }}>Dataset Ver:</span>
                  <span>{selectedExp.dataset_version}</span>
                  
                  <span style={{ color: "var(--text-secondary)" }}>Dataset Hash:</span>
                  <code>{selectedExp.dataset_hash.substring(0, 16)}...</code>
                  
                  <span style={{ color: "var(--text-secondary)" }}>Preproc Ver:</span>
                  <span>{selectedExp.preprocessing_version}</span>
                  
                  <span style={{ color: "var(--text-secondary)" }}>Random Seed:</span>
                  <span>{selectedExp.random_seed}</span>
                </div>
              </div>

              {/* Right Column: Execution */}
              <div style={{ background: "var(--surface-base)", padding: "1rem", borderRadius: "8px" }}>
                <h4 style={{ margin: "0 0 1rem", fontSize: "0.875rem", textTransform: "uppercase", color: "var(--text-secondary)" }}>
                  Execution
                </h4>
                <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: "0.75rem", fontSize: "0.875rem" }}>
                  <span style={{ color: "var(--text-secondary)" }}>Model:</span>
                  <span>{selectedExp.model_name}</span>
                  
                  <span style={{ color: "var(--text-secondary)" }}>Hardware:</span>
                  <span>{JSON.stringify(selectedExp.hardware)}</span>
                  
                  <span style={{ color: "var(--text-secondary)" }}>Duration:</span>
                  <span>{formatDuration(selectedExp.execution_duration_sec)}</span>
                  
                  <span style={{ color: "var(--text-secondary)" }}>Artifacts:</span>
                  <span style={{ wordBreak: "break-all" }}>
                    {selectedExp.artifact_location ? (
                      <a href="#" style={{ color: "var(--primary)" }}>{selectedExp.artifact_location}</a>
                    ) : "--"}
                  </span>
                </div>
              </div>
            </div>

            <h4 style={{ margin: "0 0 1rem" }}>Hyperparameters</h4>
            <pre style={{ background: "var(--surface-base)", padding: "1rem", borderRadius: "8px", fontSize: "0.8125rem", overflowX: "auto" }}>
              {Object.keys(selectedExp.configuration).length > 0 
                ? JSON.stringify(selectedExp.configuration, null, 2) 
                : "No configuration recorded."}
            </pre>

            <h4 style={{ margin: "1.5rem 0 1rem" }}>Final Metrics</h4>
            <div className="data-table-container">
              <table className="data-table" style={{ fontSize: "0.875rem" }}>
                <thead>
                  <tr>
                    <th>Metric</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(selectedExp.metrics).map(([key, val]) => (
                    <tr key={key}>
                      <td style={{ textTransform: "capitalize" }}><strong>{key.replace("_", " ")}</strong></td>
                      <td>
                        {typeof val === 'number' && val % 1 !== 0 ? val.toFixed(4) : String(val)}
                      </td>
                    </tr>
                  ))}
                  {Object.keys(selectedExp.metrics).length === 0 && (
                    <tr>
                      <td colSpan={2} style={{ textAlign: "center", padding: "1rem", color: "var(--text-secondary)" }}>
                        No metrics recorded.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "1.5rem" }}>
              <button className="btn-secondary" onClick={() => setSelectedExp(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
