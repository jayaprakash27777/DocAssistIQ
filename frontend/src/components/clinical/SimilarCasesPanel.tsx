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
      <div className="bg-slate-900/50 rounded-xl p-6 border border-slate-700">
        <div className="flex items-center gap-2 mb-4 text-slate-400">
          <Activity className="w-5 h-5 animate-pulse" />
          <h3 className="font-semibold">Retrieving Historical Cases...</h3>
        </div>
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="animate-pulse flex space-x-4">
              <div className="flex-1 space-y-3 py-1">
                <div className="h-4 bg-slate-700 rounded w-3/4"></div>
                <div className="space-y-2">
                  <div className="h-3 bg-slate-700 rounded"></div>
                  <div className="h-3 bg-slate-700 rounded w-5/6"></div>
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
      <div className="bg-red-900/20 rounded-xl p-4 border border-red-900/50">
        <div className="flex items-center gap-2 text-red-400 mb-2">
          <AlertTriangle className="w-5 h-5" />
          <h3 className="font-semibold text-sm">Failed to load historical cases</h3>
        </div>
        <p className="text-xs text-red-300/80">{error}</p>
      </div>
    );
  }

  if (cases.length === 0) {
    return (
      <div className="bg-slate-900/50 rounded-xl p-6 border border-slate-800 text-center">
        <Users className="w-8 h-8 text-slate-600 mx-auto mb-3" />
        <h3 className="text-sm font-medium text-slate-300">No similar cases found</h3>
        <p className="text-xs text-slate-500 mt-1">
          We couldn't find any historical cases matching this clinical presentation.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/80 rounded-xl border border-slate-700 overflow-hidden">
      <div className="p-4 border-b border-slate-800 bg-slate-800/30 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-indigo-400" />
          <h3 className="font-semibold text-slate-200">Similar Historical Cases</h3>
        </div>
        <span className="text-xs font-medium px-2 py-1 bg-indigo-500/20 text-indigo-300 rounded-full">
          {cases.length} Match{cases.length !== 1 ? 'es' : ''}
        </span>
      </div>

      <div className="p-4 space-y-4">
        <AnimatePresence>
          {cases.map((c, index) => (
            <motion.div
              key={c.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50 hover:border-indigo-500/30 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex flex-wrap gap-2">
                  {c.age_group && (
                    <span className="px-2 py-0.5 bg-slate-700 rounded text-xs text-slate-300">
                      Age: {c.age_group}
                    </span>
                  )}
                  {c.biological_sex && (
                    <span className="px-2 py-0.5 bg-slate-700 rounded text-xs text-slate-300 capitalize">
                      Sex: {c.biological_sex}
                    </span>
                  )}
                  <span className="px-2 py-0.5 bg-slate-700/50 border border-slate-600 rounded text-xs text-slate-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {c.created_at ? new Date(c.created_at).toLocaleDateString() : 'Unknown Date'}
                  </span>
                </div>
              </div>

              <div className="mb-3">
                <h4 className="text-xs font-semibold text-slate-400 mb-1 uppercase tracking-wider">Clinical Presentation</h4>
                <p className="text-sm text-slate-300 leading-relaxed line-clamp-3">
                  {c.clinical_presentation_summary}
                </p>
              </div>

              {c.baseline_conditions && Object.keys(c.baseline_conditions).length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-700/50">
                  <h4 className="text-xs font-semibold text-slate-400 mb-1">Baseline Conditions:</h4>
                  <div className="flex flex-wrap gap-1">
                    {Object.keys(c.baseline_conditions).map(condition => (
                      <span key={condition} className="px-1.5 py-0.5 bg-rose-500/10 text-rose-300 rounded text-[10px] uppercase">
                        {condition.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="mt-3 pt-3 border-t border-slate-700/80 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                <p className="text-[10px] text-amber-400/80 leading-tight">
                  {c.warning}
                </p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
