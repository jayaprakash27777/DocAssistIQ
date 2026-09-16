"use client";

import { useCallback, useEffect, useState, useRef } from "react";
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
import { Server, Activity, CheckCircle2, XCircle, Loader2, X, ShieldAlert } from "lucide-react";
import { motion } from "framer-motion";

export default function IngestionAdminPage() {
  const { toast } = useToast();
  const [jobs, setJobs] = useState<IngestionJobResponse[]>([]);
  const [sources, setSources] = useState<SourceResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const [showModal, setShowModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedSource, setSelectedSource] = useState("");
  const [sourceVersion, setSourceVersion] = useState("");
  const isFetchingRef = useRef(false);

  const fetchJobs = useCallback(async (isInitial = false) => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;
    if (isInitial) setLoading(true);

    const r = await listIngestionJobs(1, 100);
    
    if (isInitial) setLoading(false);
    isFetchingRef.current = false;

    if (!r.ok) {
      if (isInitial) toast.error(r.error.message || "Failed to load jobs");
      return;
    }
    setJobs(r.data.items);
    setTotal(r.data.total);
    setLastUpdated(new Date());
  }, [toast]);

  const fetchSources = useCallback(async () => {
    const r = await listSources(1, 100);
    if (r.ok) {
      setSources(r.data.items.filter(s => s.is_production_suitable));
    }
  }, []);

  useEffect(() => {
    fetchJobs(true);
    fetchSources();
    
    const interval = setInterval(() => fetchJobs(false), 3000);
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
    fetchJobs(false);
  }

  async function handleReview(jobId: string, status: "approved" | "rejected") {
    const r = await reviewIngestionJob(jobId, status);
    if (!r.ok) {
      toast.error(r.error.message || `Failed to mark job as ${status}`);
      return;
    }
    toast.success(`Job marked as ${status}.`);
    fetchJobs(false);
  }

  const getStatusColor = (status: string) => {
    switch(status.toLowerCase()) {
      case 'completed': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 'failed': return 'bg-red-100 text-red-700 border-red-200';
      case 'running': return 'bg-blue-100 text-blue-700 border-blue-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getReviewColor = (status: string) => {
    switch(status.toLowerCase()) {
      case 'approved': return 'bg-emerald-50 text-emerald-600 border-emerald-200';
      case 'rejected': return 'bg-red-50 text-red-600 border-red-200';
      default: return 'bg-slate-50 text-slate-500 border-slate-200';
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 relative overflow-hidden p-8 pt-10">
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-300/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '8s' }}></div>
      <div className="absolute inset-0 z-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>

      <div className="max-w-7xl mx-auto space-y-8 relative z-10">
        
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <div className="relative p-2.5 bg-purple-500/10 rounded-xl border border-purple-500/20 shadow-sm overflow-hidden">
                <div className="absolute inset-0 bg-purple-400/20 animate-pulse"></div>
                <Server size={28} className="text-purple-600 relative z-10" />
              </div>
              <h1 className="text-4xl font-bold text-slate-900 tracking-tight font-heading">
                Knowledge Ingestion
              </h1>
            </div>
            <p className="text-slate-500 text-lg max-w-2xl font-medium">
              Monitor background workers and review parsed medical knowledge ({total} jobs).
            </p>
          </div>
          
          <div className="flex flex-col items-end gap-3">
            <div className="flex items-center gap-2 text-sm font-medium text-purple-700 bg-purple-50 px-4 py-2 rounded-full border border-purple-200 shadow-sm backdrop-blur-md">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-purple-500"></span>
              </span>
              Live Data Feed
              <span className="text-purple-600/60 ml-2 text-xs font-mono">
                Updated: {lastUpdated.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' })}
              </span>
            </div>
            <button
              onClick={() => setShowModal(true)}
              className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl font-medium shadow-lg shadow-slate-900/20 transition-all flex items-center gap-2"
            >
              + Run Ingestion
            </button>
          </div>
        </header>

        <section className="bg-white/60 backdrop-blur-xl border border-white rounded-3xl p-6 shadow-xl shadow-slate-200/50">
          {loading && jobs.length === 0 ? (
            <div className="space-y-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex gap-4 p-4 border border-slate-100 rounded-2xl bg-slate-50/50">
                  <Skeleton height="2rem" width="15%" />
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
                    <th className="px-6 py-4">Job Info</th>
                    <th className="px-6 py-4">Source</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4">Validation</th>
                    <th className="px-6 py-4">Review</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {jobs.map((job, i) => (
                    <motion.tr 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      key={job.id} 
                      className="hover:bg-slate-50/50 transition-colors group"
                    >
                      <td className="px-6 py-4">
                        <div className="font-mono text-xs font-bold text-slate-700">{job.id.substring(0, 8)}...</div>
                        <div className="text-xs text-slate-500 mt-1">{new Date(job.created_at).toLocaleString()}</div>
                        {job.content_hash && (
                          <div className="text-[10px] text-slate-400 mt-1 truncate max-w-[120px]" title={job.content_hash}>
                            Hash: {job.content_hash.substring(0, 12)}...
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-mono text-xs text-slate-600 bg-slate-100 px-2 py-1 rounded inline-block">{job.source_id.substring(0, 8)}...</div>
                        {job.source_version && <div className="text-[10px] uppercase font-bold text-slate-400 mt-1">v. {job.source_version}</div>}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider border ${getStatusColor(job.status)}`}>
                          {job.status === 'running' && <Loader2 size={12} className="animate-spin" />}
                          {job.status}
                        </span>
                        {job.error_message && (
                          <div className="text-[10px] text-red-500 mt-1 max-w-[150px] truncate" title={job.error_message}>
                            {job.error_message}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {job.validation_result ? (
                          <div className="space-y-1">
                            <span className="text-xs font-medium text-slate-500 flex items-center gap-1"><CheckCircle2 size={12} className="text-emerald-500"/> Has Result</span>
                            {job.validation_result.deduplication && (
                              <span className="text-[10px] text-slate-400 italic block">{job.validation_result.deduplication}</span>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-300">—</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase border ${getReviewColor(job.review_status)}`}>
                          {job.review_status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        {job.status === "completed" && job.review_status === "unreviewed" && (
                          <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => handleReview(job.id, "approved")}
                              className="px-3 py-1.5 bg-emerald-50 text-emerald-600 hover:bg-emerald-500 hover:text-white border border-emerald-200 hover:border-emerald-500 rounded-lg text-xs font-bold uppercase tracking-wider transition-all"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleReview(job.id, "rejected")}
                              className="px-3 py-1.5 bg-red-50 text-red-600 hover:bg-red-500 hover:text-white border border-red-200 hover:border-red-500 rounded-lg text-xs font-bold uppercase tracking-wider transition-all"
                            >
                              Reject
                            </button>
                          </div>
                        )}
                      </td>
                    </motion.tr>
                  ))}
                  {jobs.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-6 py-16 text-center">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 mb-4">
                          <Activity size={32} className="text-slate-400" />
                        </div>
                        <h3 className="text-lg font-bold text-slate-800 mb-1">No ingestion jobs found</h3>
                        <p className="text-slate-500">Start an ingestion pipeline to parse knowledge sources.</p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl border border-slate-100 relative"
          >
            <button onClick={() => setShowModal(false)} className="absolute top-6 right-6 text-slate-400 hover:text-slate-600 transition-colors">
              <X size={24} />
            </button>

            <div className="w-12 h-12 rounded-2xl bg-purple-100 text-purple-600 flex items-center justify-center mb-5">
              <Server size={24} />
            </div>
            
            <h3 className="text-2xl font-bold text-slate-800 mb-6 font-heading">
              Start Ingestion Pipeline
            </h3>

            <form onSubmit={handleStartJob} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Verified Source *</label>
                <select 
                  value={selectedSource} 
                  onChange={e => setSelectedSource(e.target.value)}
                  required
                  className="w-full rounded-xl border-slate-200 bg-slate-50 p-3 text-sm focus:ring-purple-500 focus:border-purple-500 transition-shadow outline-none border appearance-none cursor-pointer"
                >
                  <option value="">-- Select Source --</option>
                  {sources.map(s => (
                    <option key={s.id} value={s.id}>{s.name} ({s.code})</option>
                  ))}
                </select>
                {sources.length === 0 && (
                  <p className="text-xs text-amber-600 mt-2 flex items-center gap-1">
                    <ShieldAlert size={12}/> No verified sources available. Verify a source first.
                  </p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Source Version (Optional)</label>
                <input 
                  value={sourceVersion} 
                  onChange={e => setSourceVersion(e.target.value)}
                  placeholder="e.g. 2026AA" 
                  className="w-full rounded-xl border-slate-200 bg-slate-50 p-3 text-sm focus:ring-purple-500 focus:border-purple-500 transition-shadow outline-none border"
                />
              </div>

              <div className="flex gap-3 justify-end pt-4 border-t border-slate-100 mt-6">
                <button type="button" onClick={() => setShowModal(false)} disabled={isSubmitting} className="px-5 py-2.5 rounded-xl font-medium text-slate-600 hover:bg-slate-100 transition-colors">Cancel</button>
                <button type="submit" disabled={isSubmitting || sources.length === 0} className="px-5 py-2.5 rounded-xl font-medium text-white bg-slate-900 hover:bg-slate-800 shadow-lg shadow-slate-900/20 transition-all disabled:opacity-50">
                  {isSubmitting ? "Starting..." : "Start Job"}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}
