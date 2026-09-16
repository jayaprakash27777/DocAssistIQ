"use client";

import { useCallback, useEffect, useState, useRef } from "react";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import {
  listSources,
  createSource,
  verifySource,
  type SourceResponse,
  type SourceCreate,
} from "@/lib/api";
import { BookOpen, CheckCircle2, ShieldAlert, X } from "lucide-react";
import { motion } from "framer-motion";

export default function SourcesAdminPage() {
  const { toast } = useToast();
  const [sources, setSources] = useState<SourceResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const [showModal, setShowModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const isFetchingRef = useRef(false);

  const fetchSources = useCallback(async (isInitial = false) => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;
    if (isInitial) setLoading(true);
    
    const r = await listSources(1, 100);
    
    if (isInitial) setLoading(false);
    isFetchingRef.current = false;
    
    if (!r.ok) {
      if (isInitial) toast.error(r.error.message || "Failed to load sources");
      return;
    }
    setSources(r.data.items);
    setTotal(r.data.total);
    setLastUpdated(new Date());
  }, [toast]);

  useEffect(() => {
    fetchSources(true);
    const intervalId = setInterval(() => fetchSources(false), 3000);
    return () => clearInterval(intervalId);
  }, [fetchSources]);

  async function handleVerify(sourceId: string) {
    const r = await verifySource(sourceId);
    if (!r.ok) {
      toast.error(r.error.message || "Failed to verify source");
      return;
    }
    toast.success("Source verified for production.");
    fetchSources(false);
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
    fetchSources(false);
  }

  return (
    <div className="min-h-screen bg-slate-50 relative overflow-hidden p-8 pt-10">
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-300/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '8s' }}></div>
      <div className="absolute inset-0 z-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>

      <div className="max-w-7xl mx-auto space-y-8 relative z-10">
        
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <div className="relative p-2.5 bg-emerald-500/10 rounded-xl border border-emerald-500/20 shadow-sm overflow-hidden">
                <div className="absolute inset-0 bg-emerald-400/20 animate-pulse"></div>
                <BookOpen size={28} className="text-emerald-600 relative z-10" />
              </div>
              <h1 className="text-4xl font-bold text-slate-900 tracking-tight font-heading">
                Medical Source Registry
              </h1>
            </div>
            <p className="text-slate-500 text-lg max-w-2xl font-medium">
              Manage and verify clinical knowledge sources ({total} total).
            </p>
          </div>
          
          <div className="flex flex-col items-end gap-3">
            <div className="flex items-center gap-2 text-sm font-medium text-emerald-700 bg-emerald-50 px-4 py-2 rounded-full border border-emerald-200 shadow-sm backdrop-blur-md">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </span>
              Live Data Feed
              <span className="text-emerald-600/60 ml-2 text-xs font-mono">
                Updated: {lastUpdated.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' })}
              </span>
            </div>
            <button
              onClick={() => setShowModal(true)}
              className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl font-medium shadow-lg shadow-slate-900/20 transition-all flex items-center gap-2"
            >
              + Register Source
            </button>
          </div>
        </header>

        <section className="bg-white/60 backdrop-blur-xl border border-white rounded-3xl p-6 shadow-xl shadow-slate-200/50">
          {loading ? (
            <div className="space-y-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex gap-4 p-4 border border-slate-100 rounded-2xl bg-slate-50/50">
                  <Skeleton height="2rem" width="20%" />
                  <Skeleton height="2rem" width="40%" />
                  <Skeleton height="2rem" width="40%" />
                </div>
              ))}
            </div>
          ) : (
            <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50/80 border-b border-slate-100 text-slate-500 font-medium uppercase tracking-wider text-xs">
                  <tr>
                    <th className="px-6 py-4">Code</th>
                    <th className="px-6 py-4">Name / Org</th>
                    <th className="px-6 py-4">Data Type</th>
                    <th className="px-6 py-4">Access</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {sources.map((s, i) => (
                    <motion.tr 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      key={s.id} 
                      className="hover:bg-slate-50/50 transition-colors group"
                    >
                      <td className="px-6 py-4 font-mono text-xs font-bold text-slate-700">{s.code}</td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-slate-800">{s.name}</div>
                        <div className="text-xs text-slate-500 mt-0.5">{s.organisation}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="px-2.5 py-1 bg-slate-100 text-slate-600 rounded-md text-xs font-medium">{s.data_type}</span>
                      </td>
                      <td className="px-6 py-4">{s.access_mechanism}</td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider ${
                          s.is_production_suitable ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'
                        }`}>
                          {s.is_production_suitable ? <CheckCircle2 size={14} /> : <ShieldAlert size={14} />}
                          {s.status}
                        </span>
                        {s.is_production_suitable && (
                          <div className="text-[10px] text-emerald-600 font-bold uppercase mt-1">Verified</div>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        {!s.is_production_suitable && (
                          <div className="flex items-center justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => handleVerify(s.id)}
                              className="px-3 py-1.5 bg-emerald-50 text-emerald-600 hover:bg-emerald-500 hover:text-white border border-emerald-200 hover:border-emerald-500 rounded-lg text-xs font-bold uppercase tracking-wider transition-all"
                            >
                              Verify
                            </button>
                          </div>
                        )}
                      </td>
                    </motion.tr>
                  ))}
                  {sources.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-6 py-16 text-center">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 mb-4">
                          <BookOpen size={32} className="text-slate-400" />
                        </div>
                        <h3 className="text-lg font-bold text-slate-800 mb-1">No sources registered</h3>
                        <p className="text-slate-500">Register clinical sources to begin knowledge ingestion.</p>
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
            className="bg-white rounded-3xl p-8 max-w-lg w-full shadow-2xl border border-slate-100 relative max-h-[90vh] overflow-y-auto"
          >
            <button onClick={() => setShowModal(false)} className="absolute top-6 right-6 text-slate-400 hover:text-slate-600 transition-colors">
              <X size={24} />
            </button>

            <div className="w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-600 flex items-center justify-center mb-5">
              <BookOpen size={24} />
            </div>
            
            <h3 className="text-2xl font-bold text-slate-800 mb-6 font-heading">
              Register New Source
            </h3>

            <form onSubmit={handleCreateSource} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Source Code *</label>
                <input name="code" required pattern="^[a-z0-9_]+$" title="Lowercase, numbers, underscores only" placeholder="e.g. pubmed_central" className="w-full rounded-xl border-slate-200 bg-slate-50 p-3 text-sm focus:ring-emerald-500 focus:border-emerald-500 transition-shadow outline-none border" />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Organisation *</label>
                <input name="organisation" required placeholder="e.g. NIH / NLM" className="w-full rounded-xl border-slate-200 bg-slate-50 p-3 text-sm focus:ring-emerald-500 focus:border-emerald-500 transition-shadow outline-none border" />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Name *</label>
                <input name="name" required placeholder="e.g. PubMed Central" className="w-full rounded-xl border-slate-200 bg-slate-50 p-3 text-sm focus:ring-emerald-500 focus:border-emerald-500 transition-shadow outline-none border" />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Base URL</label>
                <input type="url" name="base_url" placeholder="Optional URL" className="w-full rounded-xl border-slate-200 bg-slate-50 p-3 text-sm focus:ring-emerald-500 focus:border-emerald-500 transition-shadow outline-none border" />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">Data Type *</label>
                  <select name="data_type" required className="w-full rounded-xl border-slate-200 bg-slate-50 p-3 text-sm focus:ring-emerald-500 focus:border-emerald-500 transition-shadow outline-none border appearance-none cursor-pointer">
                    <option value="literature">Literature</option>
                    <option value="clinical_guidelines">Clinical Guidelines</option>
                    <option value="drug_database">Drug Database</option>
                    <option value="coding_system">Coding System</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">Access Mechanism *</label>
                  <select name="access_mechanism" required className="w-full rounded-xl border-slate-200 bg-slate-50 p-3 text-sm focus:ring-emerald-500 focus:border-emerald-500 transition-shadow outline-none border appearance-none cursor-pointer">
                    <option value="api">API</option>
                    <option value="bulk_download">Bulk Download</option>
                    <option value="licensed_feed">Licensed Feed</option>
                    <option value="manual">Manual</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">License / Access Terms</label>
                <textarea name="license_info" placeholder="Provide licensing details required for verification..." rows={3} className="w-full rounded-xl border-slate-200 bg-slate-50 p-3 text-sm focus:ring-emerald-500 focus:border-emerald-500 transition-shadow outline-none border"></textarea>
              </div>

              <div className="flex gap-3 justify-end pt-4 border-t border-slate-100">
                <button type="button" onClick={() => setShowModal(false)} disabled={isSubmitting} className="px-5 py-2.5 rounded-xl font-medium text-slate-600 hover:bg-slate-100 transition-colors">Cancel</button>
                <button type="submit" disabled={isSubmitting} className="px-5 py-2.5 rounded-xl font-medium text-white bg-slate-900 hover:bg-slate-800 shadow-lg shadow-slate-900/20 transition-all disabled:opacity-50">
                  {isSubmitting ? "Registering..." : "Register Source"}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}
