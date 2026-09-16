"use client";

import { useCallback, useEffect, useState, useRef } from "react";
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
import { TestTube2, CheckCircle2, Play, Activity, AlertCircle, X, ExternalLink } from "lucide-react";
import { motion } from "framer-motion";

export default function EvaluationsPage() {
  const { toast } = useToast();
  const [runs, setRuns] = useState<EvaluationRunResponse[]>([]);
  const [datasets, setDatasets] = useState<DatasetResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const [selectedRun, setSelectedRun] = useState<EvaluationRunDetailResponse | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  
  const isFetchingRef = useRef(false);

  const fetchData = useCallback(async (isInitial = false) => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;
    if (isInitial) setLoading(true);

    const [evalRes, dataRes] = await Promise.all([
      listEvaluations(),
      listDatasets()
    ]);
    
    if (isInitial) setLoading(false);
    isFetchingRef.current = false;
    
    if (evalRes.ok) setRuns(evalRes.data);
    if (dataRes.ok) setDatasets(dataRes.data);
    setLastUpdated(new Date());
  }, []);

  useEffect(() => {
    fetchData(true);
    const interval = setInterval(() => fetchData(false), 3000);
    return () => clearInterval(interval);
  }, [fetchData]);

  async function handleTriggerEval() {
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
    fetchData(false);
  }

  async function handleExecuteRun(runId: string) {
    toast.success("Starting evaluation pipeline...");
    const r = await executeEvaluationPipeline(runId);
    if (!r.ok) {
      toast.error(r.error.message || "Pipeline execution failed");
    } else {
      toast.success("Pipeline completed!");
    }
    fetchData(false);
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

  const getStatusColor = (status: string) => {
    switch(status.toLowerCase()) {
      case 'completed': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 'failed': return 'bg-red-100 text-red-700 border-red-200';
      case 'running': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'pending': return 'bg-amber-100 text-amber-700 border-amber-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 relative overflow-hidden p-8 pt-10">
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-pink-300/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '8s' }}></div>
      <div className="absolute inset-0 z-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>

      <div className="max-w-7xl mx-auto space-y-8 relative z-10">
        
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <div className="relative p-2.5 bg-pink-500/10 rounded-xl border border-pink-500/20 shadow-sm overflow-hidden">
                <div className="absolute inset-0 bg-pink-400/20 animate-pulse"></div>
                <TestTube2 size={28} className="text-pink-600 relative z-10" />
              </div>
              <h1 className="text-4xl font-bold text-slate-900 tracking-tight font-heading">
                Model Evaluation Harness
              </h1>
            </div>
            <p className="text-slate-500 text-lg max-w-2xl font-medium">
              Execute repeatable evaluations on fixed hold-out datasets.
            </p>
          </div>
          
          <div className="flex flex-col items-end gap-3">
            <div className="flex items-center gap-2 text-sm font-medium text-pink-700 bg-pink-50 px-4 py-2 rounded-full border border-pink-200 shadow-sm backdrop-blur-md">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-pink-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-pink-500"></span>
              </span>
              Live Data Feed
              <span className="text-pink-600/60 ml-2 text-xs font-mono">
                Updated: {lastUpdated.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' })}
              </span>
            </div>
            <button
              onClick={handleTriggerEval}
              className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl font-medium shadow-lg shadow-slate-900/20 transition-all flex items-center gap-2"
            >
              <Play size={16} className="fill-white" />
              Run Baseline Evaluation
            </button>
          </div>
        </header>

        <section className="bg-white/60 backdrop-blur-xl border border-white rounded-3xl p-6 shadow-xl shadow-slate-200/50">
          {loading && runs.length === 0 ? (
            <div className="space-y-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex gap-4 p-4 border border-slate-100 rounded-2xl bg-slate-50/50">
                  <Skeleton height="2rem" width="20%" />
                  <Skeleton height="2rem" width="20%" />
                  <Skeleton height="2rem" width="10%" />
                  <Skeleton height="2rem" width="20%" />
                </div>
              ))}
            </div>
          ) : (
            <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50/80 border-b border-slate-100 text-slate-500 font-medium uppercase tracking-wider text-xs">
                  <tr>
                    <th className="px-6 py-4">Model Version</th>
                    <th className="px-6 py-4">Dataset ID</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4">Accuracy</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {runs.map((run, i) => {
                    const acc = run.metrics?.accuracy;
                    return (
                      <motion.tr 
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.05 }}
                        key={run.id} 
                        className="hover:bg-slate-50/50 transition-colors group"
                      >
                        <td className="px-6 py-4">
                          <div className="font-bold text-slate-800">{run.model_version}</div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="px-2 py-1 bg-slate-100 text-slate-600 rounded font-mono text-xs font-bold border border-slate-200">
                            {run.dataset_id.split("-")[0]}...
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider border ${getStatusColor(run.status)}`}>
                            {run.status === 'completed' && <CheckCircle2 size={12} />}
                            {run.status === 'failed' && <AlertCircle size={12} />}
                            {run.status}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          {run.status === "completed" && acc !== undefined ? (
                            <div className="flex items-center gap-3">
                              <div className="w-24 h-2 bg-slate-100 rounded-full overflow-hidden">
                                <motion.div 
                                  initial={{ width: 0 }}
                                  animate={{ width: `${acc * 100}%` }}
                                  transition={{ duration: 1, delay: 0.2 }}
                                  className={`h-full ${acc > 0.8 ? "bg-emerald-500" : "bg-pink-500"} rounded-full`}
                                />
                              </div>
                              <span className={`font-bold ${acc > 0.8 ? "text-emerald-700" : "text-pink-700"}`}>
                                {(acc * 100).toFixed(1)}%
                              </span>
                            </div>
                          ) : (
                            <span className="text-slate-300 font-medium">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-right">
                          {run.status === "pending" ? (
                            <div className="flex items-center justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={() => handleExecuteRun(run.id)}
                                className="px-3 py-1.5 bg-blue-50 text-blue-600 hover:bg-blue-500 hover:text-white border border-blue-200 hover:border-blue-500 rounded-lg text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-1.5"
                              >
                                <Play size={12} className="fill-current" /> Execute
                              </button>
                            </div>
                          ) : (
                            <div className="flex items-center justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={() => viewDetails(run.id)}
                                className="px-3 py-1.5 bg-slate-50 text-slate-600 hover:bg-slate-200 border border-slate-200 hover:border-slate-300 rounded-lg text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-1.5"
                              >
                                <Activity size={14} /> View Results
                              </button>
                            </div>
                          )}
                        </td>
                      </motion.tr>
                    );
                  })}
                  {runs.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-6 py-16 text-center">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 mb-4">
                          <TestTube2 size={32} className="text-slate-400" />
                        </div>
                        <h3 className="text-lg font-bold text-slate-800 mb-1">No evaluation runs yet</h3>
                        <p className="text-slate-500">Trigger a baseline evaluation to measure model accuracy.</p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>

      {selectedRun && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-3xl p-8 max-w-4xl w-full shadow-2xl border border-slate-100 relative max-h-[90vh] flex flex-col"
          >
            <button onClick={() => setSelectedRun(null)} className="absolute top-6 right-6 text-slate-400 hover:text-slate-600 transition-colors">
              <X size={24} />
            </button>
            
            <div className="mb-6">
              <h3 className="text-2xl font-bold text-slate-800 mb-2 font-heading">
                Evaluation Results
              </h3>
              <div className="flex gap-2 items-center">
                <span className="px-2 py-1 bg-slate-100 text-slate-600 border border-slate-200 rounded font-mono text-xs font-bold">{selectedRun.model_version}</span>
                <span className="text-sm font-medium text-slate-500">on Dataset <code className="font-mono text-xs font-bold">{selectedRun.dataset_id.split("-")[0]}</code></span>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto min-h-0 space-y-6">
              
              <div className="grid grid-cols-2 gap-6">
                <div className="bg-gradient-to-br from-pink-50 to-pink-100/50 border border-pink-200 rounded-2xl p-6 text-center shadow-sm">
                  <div className="text-4xl font-black text-pink-700 tracking-tight mb-1">
                    {selectedRun.metrics?.accuracy !== undefined ? `${(selectedRun.metrics.accuracy * 100).toFixed(1)}%` : "—"}
                  </div>
                  <div className="text-sm font-bold text-pink-600/70 uppercase tracking-wider">Overall Accuracy</div>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-2xl p-6 text-center shadow-sm">
                  <div className="text-4xl font-black text-slate-700 tracking-tight mb-1">
                    {selectedRun.metrics?.correct_records ?? 0} <span className="text-2xl text-slate-400">/ {selectedRun.metrics?.total_records ?? 0}</span>
                  </div>
                  <div className="text-sm font-bold text-slate-500 uppercase tracking-wider">Correct Records</div>
                </div>
              </div>

              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="px-6 py-4 bg-slate-50 border-b border-slate-200">
                  <h4 className="font-bold text-slate-700">Record Breakdown</h4>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm text-slate-600">
                    <thead className="bg-white border-b border-slate-100 text-slate-400 font-medium text-xs">
                      <tr>
                        <th className="px-6 py-3">Task</th>
                        <th className="px-6 py-3">Record ID</th>
                        <th className="px-6 py-3">Correct</th>
                        <th className="px-6 py-3">Details</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {selectedRun.results.map(res => (
                        <tr key={res.id} className="hover:bg-slate-50/50">
                          <td className="px-6 py-3">
                            <span className="px-2 py-1 bg-slate-100 text-slate-600 rounded text-[10px] font-bold uppercase tracking-wider">{res.task_type}</span>
                          </td>
                          <td className="px-6 py-3 font-mono text-xs text-slate-500">{res.record_identifier.substring(0,8)}</td>
                          <td className="px-6 py-3">
                            {res.is_correct ? (
                              <span className="inline-flex items-center gap-1.5 text-emerald-600 font-bold text-xs"><CheckCircle2 size={14}/> Yes</span>
                            ) : (
                              <span className="inline-flex items-center gap-1.5 text-red-600 font-bold text-xs"><AlertCircle size={14}/> No</span>
                            )}
                          </td>
                          <td className="px-6 py-3">
                            <details className="group cursor-pointer text-slate-500 [&_summary::-webkit-details-marker]:hidden">
                              <summary className="flex items-center gap-1 font-medium text-blue-600 hover:text-blue-700 transition-colors">
                                View Data <ExternalLink size={12}/>
                              </summary>
                              <div className="mt-3 p-4 bg-slate-50 rounded-xl border border-slate-200 cursor-text">
                                <div className="mb-4">
                                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1 block">Ground Truth</span>
                                  <pre className="text-xs text-slate-700 bg-white p-3 rounded-lg border border-slate-100 overflow-x-auto">
                                    {JSON.stringify(res.ground_truth, null, 2)}
                                  </pre>
                                </div>
                                <div>
                                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1 block">Model Output</span>
                                  <pre className="text-xs text-slate-700 bg-white p-3 rounded-lg border border-slate-100 overflow-x-auto">
                                    {JSON.stringify(res.model_output, null, 2)}
                                  </pre>
                                </div>
                              </div>
                            </details>
                          </td>
                        </tr>
                      ))}
                      {selectedRun.results.length === 0 && (
                        <tr>
                          <td colSpan={4} className="text-center py-10 text-slate-400 font-medium">
                            No record results available.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>

            <div className="flex justify-end pt-6 mt-2 border-t border-slate-100">
              <button 
                onClick={() => setSelectedRun(null)}
                className="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl font-medium shadow-lg shadow-slate-900/20 transition-all"
              >
                Close Report
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
