"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  listPendingDoctors,
  verifyDoctor,
  type DoctorResponse,
} from "@/lib/api";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import { ShieldAlert, CheckCircle2, XCircle } from "lucide-react";
import { motion } from "framer-motion";

interface ActionState {
  doctor: DoctorResponse;
  action: "verify" | "reject";
  rejectionReason: string;
  saving: boolean;
}

export default function AdminDoctorsPage() {
  const { toast } = useToast();
  const [doctors, setDoctors] = useState<DoctorResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [action, setAction] = useState<ActionState | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const PAGE_SIZE = 20;

  useEffect(() => {
    let cancelled = false;
    let initialLoad = true;

    async function fetchData() {
      if (initialLoad) setLoading(true);
      const r = await listPendingDoctors(page, PAGE_SIZE);
      if (cancelled) return;
      if (initialLoad) {
        setLoading(false);
        initialLoad = false;
      }
      if (!r.ok) {
        setError(r.error.message ?? "Failed to load pending doctors.");
        return;
      }
      setDoctors(r.data.items);
      setTotal(r.data.total);
      setPages(r.data.pages);
      setLastUpdated(new Date());
    }

    fetchData();
    const intervalId = setInterval(fetchData, 3000);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [page]);

  async function handleAction(e: FormEvent) {
    e.preventDefault();
    if (!action) return;

    if (action.action === "reject" && !action.rejectionReason.trim()) {
      toast.error("A rejection reason is required.");
      return;
    }

    setAction((a) => a ? { ...a, saving: true } : a);

    const r = await verifyDoctor(action.doctor.id, {
      action: action.action,
      rejection_reason: action.action === "reject" ? action.rejectionReason : undefined,
    });

    if (!r.ok) {
      setAction((a) => a ? { ...a, saving: false } : a);
      toast.error(r.error.message ?? "Action failed.");
      return;
    }

    setAction(null);
    toast.success(
      action.action === "verify"
        ? `Dr. ${action.doctor.credential_reference ?? action.doctor.id} verified.`
        : `Dr. ${action.doctor.credential_reference ?? action.doctor.id} rejected.`,
    );
    setDoctors((prev) => prev.filter((d) => d.id !== action.doctor.id));
    setTotal((t) => t - 1);
  }

  return (
    <div className="min-h-screen bg-slate-50 relative overflow-hidden p-8 pt-10">
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-300/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '8s' }}></div>
      <div className="absolute inset-0 z-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>

      <div className="max-w-7xl mx-auto space-y-8 relative z-10">
        
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <div className="relative p-2.5 bg-sky-500/10 rounded-xl border border-sky-500/20 shadow-sm overflow-hidden">
                <div className="absolute inset-0 bg-sky-400/20 animate-pulse"></div>
                <ShieldAlert size={28} className="text-sky-600 relative z-10" />
              </div>
              <h1 className="text-4xl font-bold text-slate-900 tracking-tight font-heading">
                Doctor Verifications
              </h1>
            </div>
            <p className="text-slate-500 text-lg max-w-2xl font-medium">
              Review and approve or reject pending doctor credential submissions.
            </p>
          </div>
          
          <div className="flex items-center gap-2 text-sm font-medium text-sky-700 bg-sky-50 px-4 py-2 rounded-full border border-sky-200 shadow-sm backdrop-blur-md">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-sky-500"></span>
            </span>
            Live Data Feed
            <span className="text-sky-600/60 ml-2 text-xs font-mono">
              Updated: {lastUpdated.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' })}
            </span>
          </div>
        </header>

        <section className="bg-white/60 backdrop-blur-xl border border-white rounded-3xl p-6 shadow-xl shadow-slate-200/50">
          <div className="mb-6 flex justify-between items-center">
            <h2 className="text-xl font-bold text-slate-800 font-heading">
              Pending Reviews ({total})
            </h2>
          </div>

          {loading ? (
            <div className="space-y-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex gap-4 p-4 border border-slate-100 rounded-2xl bg-slate-50/50">
                  <Skeleton height="2rem" width="10%" />
                  <Skeleton height="2rem" width="30%" />
                  <Skeleton height="2rem" width="60%" />
                </div>
              ))}
            </div>
          ) : error ? (
            <div className="bg-red-50 text-red-600 p-4 rounded-xl border border-red-100 flex items-center justify-between">
              <p>{error}</p>
              <button onClick={() => { setError(null); setPage(1); }} className="px-4 py-1.5 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors font-medium text-sm">Retry</button>
            </div>
          ) : total === 0 ? (
            <div className="text-center py-16 bg-white/40 rounded-2xl border border-slate-100 border-dashed">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-100 mb-4">
                <CheckCircle2 size={32} className="text-emerald-500" />
              </div>
              <h3 className="text-lg font-bold text-slate-800 mb-1">No pending verifications</h3>
              <p className="text-slate-500">All doctor profiles have been reviewed.</p>
            </div>
          ) : (
            <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50/80 border-b border-slate-100 text-slate-500 font-medium uppercase tracking-wider text-xs">
                  <tr>
                    <th className="px-6 py-4">Doctor ID</th>
                    <th className="px-6 py-4">Specialty</th>
                    <th className="px-6 py-4">Credential</th>
                    <th className="px-6 py-4">Submitted</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {doctors.map((d, i) => (
                    <motion.tr 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      key={d.id} 
                      className="hover:bg-slate-50/50 transition-colors group"
                    >
                      <td className="px-6 py-4 font-mono text-xs text-slate-500">{d.user_id.slice(0, 8)}…</td>
                      <td className="px-6 py-4 font-medium text-slate-700">{d.specialty || <span className="text-slate-300">—</span>}</td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-slate-700">{d.credential_reference || <span className="text-slate-300">—</span>}</div>
                        <div className="text-xs text-slate-400 mt-1 truncate max-w-[200px]">{d.credential_body}</div>
                      </td>
                      <td className="px-6 py-4 text-slate-500">{new Date(d.created_at).toLocaleDateString()}</td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={() => setAction({ doctor: d, action: "verify", rejectionReason: "", saving: false })}
                            className="px-3 py-1.5 bg-emerald-50 text-emerald-600 hover:bg-emerald-500 hover:text-white border border-emerald-200 hover:border-emerald-500 rounded-lg text-xs font-bold uppercase tracking-wider transition-all"
                          >
                            Verify
                          </button>
                          <button
                            onClick={() => setAction({ doctor: d, action: "reject", rejectionReason: "", saving: false })}
                            className="px-3 py-1.5 bg-red-50 text-red-600 hover:bg-red-500 hover:text-white border border-red-200 hover:border-red-500 rounded-lg text-xs font-bold uppercase tracking-wider transition-all"
                          >
                            Reject
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
              
              {pages > 1 && (
                <div className="flex items-center justify-between px-6 py-4 bg-slate-50/50 border-t border-slate-100">
                  <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1} className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-slate-600 text-sm font-medium hover:bg-slate-50 disabled:opacity-50 disabled:hover:bg-white transition-colors">Previous</button>
                  <span className="text-sm text-slate-500">Page <span className="font-medium text-slate-700">{page}</span> of {pages}</span>
                  <button onClick={() => setPage(p => Math.min(pages, p + 1))} disabled={page >= pages} className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-slate-600 text-sm font-medium hover:bg-slate-50 disabled:opacity-50 disabled:hover:bg-white transition-colors">Next</button>
                </div>
              )}
            </div>
          )}
        </section>
      </div>

      {action && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl border border-slate-100"
          >
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-5 ${action.action === 'verify' ? 'bg-emerald-100 text-emerald-600' : 'bg-red-100 text-red-600'}`}>
              {action.action === 'verify' ? <CheckCircle2 size={24} /> : <XCircle size={24} />}
            </div>
            
            <h3 className="text-2xl font-bold text-slate-800 mb-2 font-heading">
              {action.action === "verify" ? "Verify Doctor" : "Reject Application"}
            </h3>
            
            <p className="text-slate-500 mb-6 leading-relaxed">
              {action.action === "verify"
                ? `You are about to verify Dr. ${action.doctor.user_id.slice(0, 8)}. This will grant them access to clinical features.`
                : "This application will be rejected. Please provide a clear reason for the rejection."}
            </p>

            <form onSubmit={handleAction}>
              {action.action === "reject" && (
                <div className="mb-6">
                  <label className="block text-sm font-medium text-slate-700 mb-2">Rejection Reason *</label>
                  <textarea
                    rows={3}
                    value={action.rejectionReason}
                    onChange={(e) => setAction(a => a ? { ...a, rejectionReason: e.target.value } : a)}
                    required
                    placeholder="E.g., Credential document is illegible..."
                    disabled={action.saving}
                    className="w-full rounded-xl border-slate-200 bg-slate-50 p-3 text-sm focus:ring-red-500 focus:border-red-500 transition-shadow outline-none border"
                  />
                </div>
              )}

              <div className="flex gap-3 justify-end">
                <button type="button" onClick={() => setAction(null)} disabled={action.saving} className="px-5 py-2.5 rounded-xl font-medium text-slate-600 hover:bg-slate-100 transition-colors">Cancel</button>
                <button type="submit" disabled={action.saving} className={`px-5 py-2.5 rounded-xl font-medium text-white transition-all shadow-lg ${action.action === 'verify' ? 'bg-emerald-500 hover:bg-emerald-600 shadow-emerald-500/20' : 'bg-red-500 hover:bg-red-600 shadow-red-500/20'}`}>
                  {action.saving ? "Processing..." : action.action === "verify" ? "Confirm Verification" : "Reject Application"}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}
