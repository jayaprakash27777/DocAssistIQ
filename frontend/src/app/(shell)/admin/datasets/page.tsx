"use client";

import { useCallback, useEffect, useState, useRef } from "react";
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
import { Database, ShieldAlert, CheckCircle2, ShieldCheck, Activity, X, AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";

export default function DatasetsPage() {
  const { toast } = useToast();
  const [datasets, setDatasets] = useState<DatasetResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const [validatingDataset, setValidatingDataset] = useState<DatasetResponse | null>(null);
  const [validationResult, setValidationResult] = useState<DatasetValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  
  const isFetchingRef = useRef(false);

  const fetchDatasets = useCallback(async (isInitial = false) => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;
    if (isInitial) setLoading(true);

    const r = await listDatasets();
    
    if (isInitial) setLoading(false);
    isFetchingRef.current = false;

    if (!r.ok) {
      if (isInitial) toast.error(r.error.message || "Failed to load datasets");
      return;
    }
    setDatasets(r.data);
    setLastUpdated(new Date());
  }, [toast]);

  useEffect(() => {
    fetchDatasets(true);
    const interval = setInterval(() => fetchDatasets(false), 3000);
    return () => clearInterval(interval);
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
    fetchDatasets(false);
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
    fetchDatasets(false);
  }

  async function handleApprove(datasetId: string) {
    const r = await approveDataset(datasetId);
    if (!r.ok) {
      toast.error(r.error.message || "Failed to approve dataset");
      return;
    }
    toast.success("Dataset approved for ML pipelines.");
    setValidatingDataset(null);
    fetchDatasets(false);
  }

  const getStatusColor = (status: string) => {
    switch(status.toLowerCase()) {
      case 'approved': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 'rejected': return 'bg-red-100 text-red-700 border-red-200';
      case 'pending': return 'bg-amber-100 text-amber-700 border-amber-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 relative overflow-hidden p-8 pt-10">
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-300/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '8s' }}></div>
      <div className="absolute inset-0 z-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>

      <div className="max-w-7xl mx-auto space-y-8 relative z-10">
        
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <div className="relative p-2.5 bg-indigo-500/10 rounded-xl border border-indigo-500/20 shadow-sm overflow-hidden">
                <div className="absolute inset-0 bg-indigo-400/20 animate-pulse"></div>
                <Database size={28} className="text-indigo-600 relative z-10" />
              </div>
              <h1 className="text-4xl font-bold text-slate-900 tracking-tight font-heading">
                Dataset Registry & Governance
              </h1>
            </div>
            <p className="text-slate-500 text-lg max-w-2xl font-medium">
              Manage ML datasets. De-identification and strict validation are mandatory.
            </p>
          </div>
          
          <div className="flex flex-col items-end gap-3">
            <div className="flex items-center gap-2 text-sm font-medium text-indigo-700 bg-indigo-50 px-4 py-2 rounded-full border border-indigo-200 shadow-sm backdrop-blur-md">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-indigo-500"></span>
              </span>
              Live Data Feed
              <span className="text-indigo-600/60 ml-2 text-xs font-mono">
                Updated: {lastUpdated.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' })}
              </span>
            </div>
            <button
              onClick={handleCreateMockDataset}
              className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl font-medium shadow-lg shadow-slate-900/20 transition-all flex items-center gap-2"
            >
              + Register Dataset
            </button>
          </div>
        </header>

        <section className="bg-white/60 backdrop-blur-xl border border-white rounded-3xl p-6 shadow-xl shadow-slate-200/50">
          {loading && datasets.length === 0 ? (
            <div className="space-y-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex gap-4 p-4 border border-slate-100 rounded-2xl bg-slate-50/50">
                  <Skeleton height="2rem" width="30%" />
                  <Skeleton height="2rem" width="20%" />
                  <Skeleton height="2rem" width="10%" />
                  <Skeleton height="2rem" width="15%" />
                </div>
              ))}
            </div>
          ) : (
            <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50/80 border-b border-slate-100 text-slate-500 font-medium uppercase tracking-wider text-xs">
                  <tr>
                    <th className="px-6 py-4">Dataset Name</th>
                    <th className="px-6 py-4">Version</th>
                    <th className="px-6 py-4">Source</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4">Safety/PII</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {datasets.map((ds, i) => (
                    <motion.tr 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      key={ds.id} 
                      className="hover:bg-slate-50/50 transition-colors group"
                    >
                      <td className="px-6 py-4">
                        <div className="font-bold text-slate-800 font-mono text-sm">{ds.name}</div>
                        <div className="text-xs text-slate-500 mt-1">{ds.record_count > 0 ? `${ds.record_count.toLocaleString()} records` : "Unvalidated"}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="px-2 py-1 bg-slate-100 text-slate-600 rounded font-mono text-xs font-bold border border-slate-200">v{ds.version}</span>
                      </td>
                      <td className="px-6 py-4 text-slate-600 font-medium">{ds.source}</td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider border ${getStatusColor(ds.approval_status)}`}>
                          {ds.approval_status}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {ds.is_deidentified ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-md text-[10px] font-bold uppercase tracking-wider">
                            <ShieldCheck size={14} /> De-identified
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-red-50 text-red-700 border border-red-200 rounded-md text-[10px] font-bold uppercase tracking-wider">
                            <ShieldAlert size={14} /> Not Cleared
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        {(ds.approval_status === "pending" || ds.approval_status === "rejected") ? (
                          <div className="flex items-center justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => handleValidate(ds)}
                              className="px-3 py-1.5 bg-indigo-50 text-indigo-600 hover:bg-indigo-500 hover:text-white border border-indigo-200 hover:border-indigo-500 rounded-lg text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-1.5"
                            >
                              <Activity size={14} />
                              Run Validation
                            </button>
                          </div>
                        ) : (
                          <span className="text-xs font-bold text-slate-400 uppercase">Approved</span>
                        )}
                      </td>
                    </motion.tr>
                  ))}
                  {datasets.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-6 py-16 text-center">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 mb-4">
                          <Database size={32} className="text-slate-400" />
                        </div>
                        <h3 className="text-lg font-bold text-slate-800 mb-1">No datasets registered</h3>
                        <p className="text-slate-500">Register and validate your ML datasets here.</p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>

      {validatingDataset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-3xl p-8 max-w-3xl w-full shadow-2xl border border-slate-100 relative max-h-[90vh] flex flex-col"
          >
            <button onClick={() => setValidatingDataset(null)} className="absolute top-6 right-6 text-slate-400 hover:text-slate-600 transition-colors">
              <X size={24} />
            </button>
            
            <div className="mb-6">
              <h3 className="text-2xl font-bold text-slate-800 mb-2 font-heading">
                Dataset Validation Report
              </h3>
              <div className="flex gap-2 items-center">
                <span className="px-2 py-1 bg-slate-100 text-slate-600 border border-slate-200 rounded font-mono text-xs font-bold">{validatingDataset.name}</span>
                <span className="text-sm font-medium text-slate-500 font-mono">v{validatingDataset.version}</span>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto min-h-0">
              {isValidating ? (
                <div className="flex flex-col items-center justify-center py-20 text-indigo-600">
                  <div className="w-16 h-16 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mb-6"></div>
                  <h4 className="text-xl font-bold text-slate-800 mb-2">Executing Validation Pipeline</h4>
                  <p className="text-slate-500">Running PII detection, schema enforcement, and leakage checks...</p>
                </div>
              ) : validationResult ? (
                <div className="space-y-6">
                  <div className={`p-5 rounded-2xl border ${validationResult.is_valid && !validationResult.pii_detected ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'} flex items-center gap-4`}>
                    <div className={`p-3 rounded-xl ${validationResult.is_valid && !validationResult.pii_detected ? 'bg-emerald-100 text-emerald-600' : 'bg-red-100 text-red-600'}`}>
                      {validationResult.is_valid && !validationResult.pii_detected ? <CheckCircle2 size={32} /> : <AlertTriangle size={32} />}
                    </div>
                    <div>
                      <h4 className={`text-lg font-bold mb-1 ${validationResult.is_valid && !validationResult.pii_detected ? 'text-emerald-800' : 'text-red-800'}`}>
                        {validationResult.is_valid && !validationResult.pii_detected ? "Validation Passed" : "Validation Failed"}
                      </h4>
                      <p className={`text-sm ${validationResult.is_valid && !validationResult.pii_detected ? 'text-emerald-600' : 'text-red-600'}`}>
                        Processed {validationResult.record_count.toLocaleString()} records.
                      </p>
                    </div>
                  </div>

                  <div className="bg-slate-50 rounded-2xl border border-slate-100 p-6">
                    <h5 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">Inspection Metrics</h5>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex justify-between items-center">
                        <span className="text-slate-600 font-medium">Missing Values</span>
                        <span className={`font-bold ${validationResult.missing_values > 0 ? 'text-red-500' : 'text-slate-800'}`}>{validationResult.missing_values}</span>
                      </div>
                      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex justify-between items-center">
                        <span className="text-slate-600 font-medium">Malformed Records</span>
                        <span className={`font-bold ${validationResult.malformed > 0 ? 'text-red-500' : 'text-slate-800'}`}>{validationResult.malformed}</span>
                      </div>
                      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex justify-between items-center">
                        <span className="text-slate-600 font-medium">Exact Duplicates</span>
                        <span className={`font-bold ${validationResult.duplicates > 0 ? 'text-red-500' : 'text-slate-800'}`}>{validationResult.duplicates}</span>
                      </div>
                      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex justify-between items-center">
                        <span className="text-slate-600 font-medium">Label Conflicts</span>
                        <span className={`font-bold ${validationResult.label_conflicts > 0 ? 'text-red-500' : 'text-slate-800'}`}>{validationResult.label_conflicts}</span>
                      </div>
                      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex justify-between items-center">
                        <span className="text-slate-600 font-medium">Data Leakage</span>
                        <span className={`font-bold uppercase text-[10px] px-2 py-1 rounded ${validationResult.leakage_detected ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-600'}`}>{validationResult.leakage_detected ? "DETECTED" : "None"}</span>
                      </div>
                      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex justify-between items-center">
                        <span className="text-slate-600 font-medium">PII Detection</span>
                        <span className={`font-bold uppercase text-[10px] px-2 py-1 rounded ${validationResult.pii_detected ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'}`}>{validationResult.pii_detected ? "FAILED CLOSED (PII)" : "CLEARED"}</span>
                      </div>
                    </div>
                  </div>

                  {validationResult.errors.length > 0 && (
                    <div className="bg-red-50 rounded-2xl border border-red-100 p-6">
                      <h5 className="text-sm font-bold text-red-800 uppercase tracking-wider mb-3">Error Logs</h5>
                      <ul className="space-y-2">
                        {validationResult.errors.map((err, i) => (
                          <li key={i} className="text-sm text-red-600 font-mono bg-white/50 p-2 rounded-lg border border-red-100">
                            {err}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : null}
            </div>

            <div className="flex justify-end gap-3 pt-6 mt-2 border-t border-slate-100">
              <button 
                onClick={() => setValidatingDataset(null)}
                className="px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-medium transition-colors"
              >
                Close
              </button>
              
              {validationResult && validationResult.is_valid && !validationResult.pii_detected && (
                <button 
                  onClick={() => handleApprove(validatingDataset.id)}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-medium shadow-lg shadow-indigo-600/20 transition-all flex items-center gap-2"
                >
                  Approve Dataset for ML
                </button>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
