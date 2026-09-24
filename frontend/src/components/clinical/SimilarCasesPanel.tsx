/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable react/no-unescaped-entities */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useEffect, useState } from "react";
import { getSimilarCases, SimilarCaseResponse } from "@/lib/api";
import { Activity, AlertTriangle, Clock, Users } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface SimilarCasesPanelProps {
  consultationId: string;
}

export function SimilarCasesPanel({ consultationId }: SimilarCasesPanelProps) {
  const [cases, setCases] = useState<SimilarCaseResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadCases() {
      setLoading(true);
      try {
        const response = await getSimilarCases(consultationId);
        if (response.ok && response.data) {
          setCases(response.data.cases);
        } else {
          setError(!response.ok ? response.error.message : "Failed to load similar cases");
        }
      } catch (err: any) {
        setError(err.message || "An unexpected error occurred");
      } finally {
        setLoading(false);
      }
    }

    loadCases();
  }, [consultationId]);

  if (loading) {
    return (
      <div className="dashboard-card !block p-6 animate-pulse">
        <div className="flex items-center gap-2 mb-4 text-[var(--color-primary-600)] relative z-10">
          <Activity className="w-5 h-5 animate-spin" />
          <h3 className="font-semibold">Retrieving Historical Cases...</h3>
        </div>
        <div className="space-y-4 relative z-10">
          {[1, 2].map((i) => (
            <div key={i} className="flex space-x-4">
              <div className="flex-1 space-y-3 py-1">
                <div className="h-4 bg-[var(--color-neutral-200)] rounded w-3/4"></div>
                <div className="space-y-2">
                  <div className="h-3 bg-[var(--color-neutral-100)] rounded"></div>
                  <div className="h-3 bg-[var(--color-neutral-100)] rounded w-5/6"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 rounded-xl p-4 border border-red-200 shadow-sm">
        <div className="flex items-center gap-2 text-red-600 mb-2">
          <AlertTriangle className="w-5 h-5" />
          <h3 className="font-bold text-sm">Failed to load historical cases</h3>
        </div>
        <p className="text-xs text-red-500 font-medium">{error}</p>
      </div>
    );
  }

  if (cases.length === 0) {
    return (
      <div className="dashboard-card flex-col items-center justify-center p-8 text-center !block">
        <div className="w-16 h-16 bg-[var(--color-neutral-100)] rounded-full flex items-center justify-center mx-auto mb-4 relative z-10">
          <Users className="w-8 h-8 text-[var(--text-tertiary)]" />
        </div>
        <h3 className="text-base font-bold text-[var(--text-primary)] relative z-10">No similar cases found</h3>
        <p className="text-sm text-[var(--text-secondary)] mt-1 relative z-10">
          We couldn't find any historical cases matching this clinical presentation.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-panel-4k gpu-accelerated rounded-3xl overflow-hidden shadow-[0_20px_50px_rgba(0,0,0,0.08),inset_0_1px_0_rgba(255,255,255,0.9)] border border-slate-200/90 bg-white/80 backdrop-blur-2xl">
      <div className="px-6 py-4 border-b border-slate-200/80 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white flex items-center justify-between relative overflow-hidden shadow-md">
        <div className="absolute inset-0 bg-gradient-to-r from-teal-500/10 via-indigo-500/10 to-purple-500/10 pointer-events-none" />
        <div className="flex items-center gap-3 relative z-10">
          <div className="w-9 h-9 bg-gradient-to-br from-teal-400 to-indigo-500 rounded-xl flex items-center justify-center text-white shadow-md shadow-teal-500/30 ring-1 ring-white/30">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-white text-base tracking-tight m-0">Similar Historical Cases</h3>
            <p className="text-xs text-slate-300 m-0">Vector matched against historical case repository</p>
          </div>
        </div>
        <span className="relative z-10 text-xs font-bold px-3 py-1 bg-teal-500/20 text-teal-300 rounded-full border border-teal-400/40 shadow-sm backdrop-blur-md">
          {cases.length} Match{cases.length !== 1 ? 'es' : ''} Found
        </span>
      </div>

      <div className="p-5 space-y-4 relative z-10 bg-slate-50/50">
        <AnimatePresence>
          {cases.map((c, index) => (
            <motion.div
              key={c.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              whileHover={{ y: -2 }}
              transition={{ delay: index * 0.08 }}
              className="bg-white/95 rounded-2xl p-5 border border-slate-200/80 hover:border-indigo-300 transition-all shadow-sm hover:shadow-lg ring-1 ring-black/5"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex flex-wrap gap-2">
                  {c.age_group && (
                    <span className="px-2.5 py-1 bg-slate-100 border border-slate-200 rounded-lg text-xs font-bold text-slate-700 shadow-sm">
                      Age: {c.age_group}
                    </span>
                  )}
                  {c.biological_sex && (
                    <span className="px-2.5 py-1 bg-slate-100 border border-slate-200 rounded-lg text-xs font-bold text-slate-700 capitalize shadow-sm">
                      Sex: {c.biological_sex}
                    </span>
                  )}
                  <span className="px-2.5 py-1 bg-slate-100 border border-slate-200 rounded-lg text-xs font-semibold text-slate-500 flex items-center gap-1.5 shadow-sm">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    {c.created_at ? new Date(c.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : 'Unknown Date'}
                  </span>
                </div>
              </div>

              <div className="mb-3">
                <h4 className="text-[10px] font-black text-indigo-700 mb-1.5 uppercase tracking-wider">Clinical Presentation</h4>
                <p className="text-sm text-slate-700 font-normal leading-relaxed line-clamp-3">
                  {c.clinical_presentation_summary}
                </p>
              </div>

              {c.baseline_conditions && Object.keys(c.baseline_conditions).length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-100">
                  <h4 className="text-[10px] font-bold text-slate-500 mb-2 uppercase tracking-wider">Baseline Conditions:</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.keys(c.baseline_conditions).map(condition => (
                      <span key={condition} className="px-2.5 py-0.5 bg-rose-50 text-rose-700 border border-rose-200 rounded-lg text-[11px] font-bold uppercase shadow-sm">
                        {condition.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {c.warning && (
                <div className="mt-3 pt-3 border-t border-slate-100 flex items-start gap-2.5 bg-amber-50/80 p-3 rounded-xl border border-amber-200/80 shadow-sm">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <p className="text-xs font-bold text-amber-900 leading-snug m-0">
                    {c.warning}
                  </p>
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
