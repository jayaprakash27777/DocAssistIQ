"use client";

import { useCallback, useEffect, useState, useRef } from "react";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import {
  listExperiments,
  getExperiment,
  registerExperiment,
  type ExperimentResponse,
  type ExperimentRegisterRequest,
} from "@/lib/api";
import { FlaskConical, Activity, TerminalSquare, AlertCircle, CheckCircle2, Clock, Hash, Cpu, Target, ExternalLink, X, Plus, Loader2 } from "lucide-react";
import { motion } from "framer-motion";

export default function ExperimentsPage() {
  const { toast } = useToast();
  const [experiments, setExperiments] = useState<ExperimentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const [selectedExp, setSelectedExp] = useState<ExperimentResponse | null>(null);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [registering, setRegistering] = useState(false);
  const [form, setForm] = useState({
    name: "",
    model_name: "emilyalsentzer/Bio_ClinicalBERT",
    dataset_version: "1.0.0",
    dataset_hash: "sha256-a1b2c3d4e5f6",
    code_commit: "a1b2c3d4e5f67890123456789abcdef012345678",
    random_seed: 42,
    hardware_gpu: "1x NVIDIA A100-SXM4-80GB",
    learning_rate: "0.00002",
    batch_size: "16",
    epochs: "3",
  });

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) {
      toast.error("Please enter an experiment name");
      return;
    }
    setRegistering(true);
    const payload: ExperimentRegisterRequest = {
      name: form.name.trim(),
      model_name: form.model_name.trim(),
      dataset_version: form.dataset_version.trim(),
      dataset_hash: form.dataset_hash.trim(),
      code_commit: form.code_commit.trim(),
      random_seed: Number(form.random_seed) || 42,
      hardware: { gpu: form.hardware_gpu },
      configuration: {
        learning_rate: parseFloat(form.learning_rate) || 0.00002,
        batch_size: parseInt(form.batch_size) || 16,
        epochs: parseInt(form.epochs) || 3,
      },
    };

    const r = await registerExperiment(payload);
    setRegistering(false);
    if (!r.ok) {
      toast.error(r.error.message || "Failed to register experiment");
      return;
    }
    toast.success(`Experiment "${r.data.name}" registered successfully!`);
    setShowRegisterModal(false);
    setForm({
      name: "",
      model_name: "emilyalsentzer/Bio_ClinicalBERT",
      dataset_version: "1.0.0",
      dataset_hash: "sha256-a1b2c3d4e5f6",
      code_commit: "a1b2c3d4e5f67890123456789abcdef012345678",
      random_seed: 42,
      hardware_gpu: "1x NVIDIA A100-SXM4-80GB",
      learning_rate: "0.00002",
      batch_size: "16",
      epochs: "3",
    });
    fetchExperiments(false);
  }
  
  const isFetchingRef = useRef(false);

  const fetchExperiments = useCallback(async (isInitial = false) => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;
    if (isInitial) setLoading(true);

    const r = await listExperiments();
    
    if (isInitial) setLoading(false);
    isFetchingRef.current = false;
    
    if (!r.ok) {
      if (isInitial) toast.error(r.error.message || "Failed to load experiments");
      return;
    }
    setExperiments(r.data);
    setLastUpdated(new Date());
  }, [toast]);

  useEffect(() => {
    fetchExperiments(true);
    const interval = setInterval(() => fetchExperiments(false), 3000);
    return () => clearInterval(interval);
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
    if (seconds === null) return "—";
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs.toFixed(0)}s`;
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
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-rose-300/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '8s' }}></div>
      <div className="absolute inset-0 z-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>

      <div className="max-w-7xl mx-auto space-y-8 relative z-10">
        
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <div className="relative p-2.5 bg-rose-500/10 rounded-xl border border-rose-500/20 shadow-sm overflow-hidden">
                <div className="absolute inset-0 bg-rose-400/20 animate-pulse"></div>
                <FlaskConical size={28} className="text-rose-600 relative z-10" />
              </div>
              <h1 className="text-4xl font-bold text-slate-900 tracking-tight font-heading">
                ML Experiment Tracking
              </h1>
            </div>
            <p className="text-slate-500 text-lg max-w-2xl font-medium">
              Reproducible metadata, code commits, and artifacts from CLI pipeline executions.
            </p>
          </div>
          
          <div className="flex flex-col items-end gap-3">
            <div className="flex items-center gap-2 text-sm font-medium text-rose-700 bg-rose-50 px-4 py-2 rounded-full border border-rose-200 shadow-sm backdrop-blur-md">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-500"></span>
              </span>
              Live Data Feed
              <span className="text-rose-600/60 ml-2 text-xs font-mono">
                Updated: {lastUpdated.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' })}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowRegisterModal(true)}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white font-semibold rounded-xl text-xs flex items-center gap-2 shadow-lg shadow-rose-600/20 transition-all cursor-pointer"
              >
                <Plus size={14} /> Register Experiment
              </button>
              <div className="flex items-center gap-2 bg-slate-900 text-slate-300 px-4 py-2 rounded-xl text-xs font-mono shadow-lg shadow-slate-900/20 border border-slate-800">
                <TerminalSquare size={14} className="text-rose-400" />
                python cli/ml_experiment.py --help
              </div>
            </div>
          </div>
        </header>

        <section className="bg-white/60 backdrop-blur-xl border border-white rounded-3xl p-6 shadow-xl shadow-slate-200/50">
          {loading && experiments.length === 0 ? (
            <div className="space-y-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex gap-4 p-4 border border-slate-100 rounded-2xl bg-slate-50/50">
                  <Skeleton height="2rem" width="25%" />
                  <Skeleton height="2rem" width="20%" />
                  <Skeleton height="2rem" width="15%" />
                  <Skeleton height="2rem" width="10%" />
                </div>
              ))}
            </div>
          ) : (
            <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50/80 border-b border-slate-100 text-slate-500 font-medium uppercase tracking-wider text-xs">
                  <tr>
                    <th className="px-6 py-4">Experiment Name</th>
                    <th className="px-6 py-4">Model & Dataset</th>
                    <th className="px-6 py-4">Commit Hash</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4">Duration</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {experiments.map((exp, i) => (
                    <motion.tr 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      key={exp.id} 
                      className="hover:bg-slate-50/50 transition-colors group"
                    >
                      <td className="px-6 py-4">
                        <div className="font-bold text-slate-800 text-sm">{exp.name}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-slate-700">{exp.model_name}</div>
                        <div className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                          <Database size={10} /> v{exp.dataset_version}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="px-2 py-1 bg-slate-100 text-slate-500 rounded font-mono text-xs font-bold border border-slate-200 flex items-center gap-1 w-fit">
                          <Hash size={12} />
                          {exp.code_commit.substring(0, 7)}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider border ${getStatusColor(exp.status)}`}>
                          {exp.status === 'completed' && <CheckCircle2 size={12} />}
                          {exp.status === 'failed' && <AlertCircle size={12} />}
                          {exp.status}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1.5 text-slate-500">
                          <Clock size={14} />
                          {formatDuration(exp.execution_duration_sec)}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={() => viewDetails(exp.id)}
                            className="px-3 py-1.5 bg-rose-50 text-rose-600 hover:bg-rose-500 hover:text-white border border-rose-200 hover:border-rose-500 rounded-lg text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-1.5"
                          >
                            <Activity size={14} /> Details
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                  {experiments.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-6 py-16 text-center">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 mb-4">
                          <FlaskConical size={32} className="text-slate-400" />
                        </div>
                        <h3 className="text-lg font-bold text-slate-800 mb-1">No experiments found</h3>
                        <p className="text-slate-500 mb-4">Run the CLI tool to track your first experiment:</p>
                        <div className="inline-block bg-slate-900 text-slate-300 px-4 py-3 rounded-xl text-xs font-mono border border-slate-800 text-left">
                          <span className="text-rose-400">python</span> cli/ml_experiment.py \<br/>
                          <span className="pl-4">--name</span> my-first-run \<br/>
                          <span className="pl-4">--dataset-version</span> v1.0 \<br/>
                          <span className="pl-4">--model-name</span> bert
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>

      {selectedExp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-3xl p-8 max-w-4xl w-full shadow-2xl border border-slate-100 relative max-h-[90vh] flex flex-col"
          >
            <button onClick={() => setSelectedExp(null)} className="absolute top-6 right-6 text-slate-400 hover:text-slate-600 transition-colors">
              <X size={24} />
            </button>
            
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="text-2xl font-bold text-slate-800 font-heading">
                  Experiment: {selectedExp.name}
                </h3>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${getStatusColor(selectedExp.status)}`}>
                  {selectedExp.status}
                </span>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto min-h-0 space-y-6 pr-2">
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-slate-50 rounded-2xl border border-slate-100 p-6">
                  <h4 className="flex items-center gap-2 text-sm font-bold text-slate-500 uppercase tracking-wider mb-5">
                    <Target size={16} /> Reproducibility
                  </h4>
                  <div className="space-y-4 text-sm">
                    <div className="flex justify-between items-center pb-3 border-b border-slate-200">
                      <span className="text-slate-500">Commit</span>
                      <span className="font-mono font-bold text-slate-700 bg-slate-200 px-2 py-0.5 rounded text-xs">{selectedExp.code_commit}</span>
                    </div>
                    <div className="flex justify-between items-center pb-3 border-b border-slate-200">
                      <span className="text-slate-500">Dataset Version</span>
                      <span className="font-bold text-slate-700">v{selectedExp.dataset_version}</span>
                    </div>
                    <div className="flex justify-between items-center pb-3 border-b border-slate-200">
                      <span className="text-slate-500">Dataset Hash</span>
                      <span className="font-mono text-slate-500 text-xs truncate max-w-[150px]" title={selectedExp.dataset_hash}>{selectedExp.dataset_hash}</span>
                    </div>
                    <div className="flex justify-between items-center pb-3 border-b border-slate-200">
                      <span className="text-slate-500">Preprocessing Version</span>
                      <span className="font-bold text-slate-700">{selectedExp.preprocessing_version}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Random Seed</span>
                      <span className="font-mono font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded text-xs">{selectedExp.random_seed}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-50 rounded-2xl border border-slate-100 p-6">
                  <h4 className="flex items-center gap-2 text-sm font-bold text-slate-500 uppercase tracking-wider mb-5">
                    <Cpu size={16} /> Execution
                  </h4>
                  <div className="space-y-4 text-sm">
                    <div className="flex justify-between items-center pb-3 border-b border-slate-200">
                      <span className="text-slate-500">Model Name</span>
                      <span className="font-bold text-slate-700">{selectedExp.model_name}</span>
                    </div>
                    <div className="flex justify-between items-center pb-3 border-b border-slate-200">
                      <span className="text-slate-500">Duration</span>
                      <span className="font-bold text-slate-700">{formatDuration(selectedExp.execution_duration_sec)}</span>
                    </div>
                    <div className="pb-3 border-b border-slate-200">
                      <span className="text-slate-500 block mb-2">Hardware Specs</span>
                      <pre className="text-[10px] bg-white p-2 rounded border border-slate-200 text-slate-600 font-mono overflow-x-auto">
                        {JSON.stringify(selectedExp.hardware, null, 2)}
                      </pre>
                    </div>
                    <div>
                      <span className="text-slate-500 block mb-2">Artifacts Location</span>
                      {selectedExp.artifact_location ? (
                        <div className="flex items-center gap-2 text-xs font-mono text-rose-600 bg-rose-50 p-2 rounded border border-rose-100 break-all">
                          <ExternalLink size={14} className="shrink-0" />
                          {selectedExp.artifact_location}
                        </div>
                      ) : (
                        <span className="text-slate-400 italic">No artifacts recorded</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-3">Hyperparameters</h4>
                <div className="bg-slate-900 rounded-2xl p-5 border border-slate-800 shadow-inner">
                  <pre className="text-xs font-mono text-emerald-400 overflow-x-auto whitespace-pre-wrap">
                    {Object.keys(selectedExp.configuration).length > 0 
                      ? JSON.stringify(selectedExp.configuration, null, 2) 
                      : "// No configuration recorded"}
                  </pre>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-3">Final Metrics</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.keys(selectedExp.metrics).length > 0 ? (
                    Object.entries(selectedExp.metrics).map(([key, val]) => (
                      <div key={key} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 break-words">{key.replace(/_/g, " ")}</span>
                        <span className="text-2xl font-black text-rose-600">
                          {typeof val === 'number' && val % 1 !== 0 ? val.toFixed(4) : String(val)}
                        </span>
                      </div>
                    ))
                  ) : (
                    <div className="col-span-full bg-slate-50 border border-slate-100 border-dashed rounded-xl p-8 text-center text-slate-400">
                      No metrics recorded.
                    </div>
                  )}
                </div>
              </div>

            </div>

            <div className="flex justify-end pt-6 mt-2 border-t border-slate-100">
              <button 
                onClick={() => setSelectedExp(null)}
                className="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl font-medium shadow-lg shadow-slate-900/20 transition-all"
              >
                Close Details
              </button>
            </div>
          </motion.div>
        </div>
      )}

      {showRegisterModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-3xl p-8 max-w-2xl w-full shadow-2xl border border-slate-100 relative max-h-[90vh] flex flex-col"
          >
            <button 
              onClick={() => setShowRegisterModal(false)} 
              className="absolute top-6 right-6 text-slate-400 hover:text-slate-600 transition-colors"
            >
              <X size={24} />
            </button>
            
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-rose-50 rounded-xl border border-rose-200 text-rose-600">
                  <FlaskConical size={22} />
                </div>
                <h3 className="text-2xl font-bold text-slate-800 font-heading">
                  Register ML Experiment
                </h3>
              </div>
              <p className="text-slate-500 text-sm">
                Record new reproducible model training run metadata, hyperparameters, and git provenance.
              </p>
            </div>

            <form onSubmit={handleRegister} className="flex-1 overflow-y-auto space-y-5 pr-2">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                    Experiment Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. bio-clinicalbert-v2"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                    Model Architecture *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Bio_ClinicalBERT"
                    value={form.model_name}
                    onChange={(e) => setForm({ ...form, model_name: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                    Dataset Version *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="1.0.0"
                    value={form.dataset_version}
                    onChange={(e) => setForm({ ...form, dataset_version: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                    Dataset Hash *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="sha256-..."
                    value={form.dataset_hash}
                    onChange={(e) => setForm({ ...form, dataset_hash: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm font-mono text-xs focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                  Code Commit Hash (Git SHA) *
                </label>
                <input
                  type="text"
                  required
                  placeholder="40-character hex commit SHA"
                  value={form.code_commit}
                  onChange={(e) => setForm({ ...form, code_commit: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm font-mono text-xs focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                    Hardware Environment
                  </label>
                  <input
                    type="text"
                    value={form.hardware_gpu}
                    onChange={(e) => setForm({ ...form, hardware_gpu: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">
                    Random Seed
                  </label>
                  <input
                    type="number"
                    value={form.random_seed}
                    onChange={(e) => setForm({ ...form, random_seed: Number(e.target.value) })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500"
                  />
                </div>
              </div>

              <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
                  Hyperparameters Configuration
                </h4>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[11px] font-medium text-slate-500 mb-1">Learning Rate</label>
                    <input
                      type="text"
                      value={form.learning_rate}
                      onChange={(e) => setForm({ ...form, learning_rate: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-rose-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-slate-500 mb-1">Batch Size</label>
                    <input
                      type="number"
                      value={form.batch_size}
                      onChange={(e) => setForm({ ...form, batch_size: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-rose-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-slate-500 mb-1">Epochs</label>
                    <input
                      type="number"
                      value={form.epochs}
                      onChange={(e) => setForm({ ...form, epochs: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-rose-500"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowRegisterModal(false)}
                  className="px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-xl font-medium text-sm transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={registering}
                  className="px-6 py-2.5 bg-rose-600 hover:bg-rose-700 text-white rounded-xl font-semibold text-sm shadow-lg shadow-rose-600/20 transition-all flex items-center gap-2 disabled:opacity-50 cursor-pointer"
                >
                  {registering ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
                  {registering ? "Registering..." : "Register Run"}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}
// Add a quick mock Database icon since it's not imported directly in lucide-react if using the old set
function Database({ size = 24, className = "" }: { size?: number, className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
    </svg>
  );
}
