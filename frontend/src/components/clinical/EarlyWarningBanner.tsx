"use client";

import React, { useState, useEffect } from "react";
import { getEarlyWarning, EarlyWarningResponse } from "@/lib/api";
import { AlertOctagon, Activity, ChevronDown, ChevronUp } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function EarlyWarningBanner({ consultationId, trigger }: { consultationId: string, trigger?: any }) {
  const [data, setData] = useState<EarlyWarningResponse | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    async function load() {
      const res = await getEarlyWarning(consultationId);
      if (res.ok && res.data.probability_percentage > 0) {
        setData(res.data);
      }
    }
    load();
  }, [consultationId, trigger]);

  if (!data || data.probability_percentage < 30) return null; // Only show if there's significant risk

  const isCritical = data.probability_percentage >= 70;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`mb-6 rounded-3xl border overflow-hidden glass-panel-4k gpu-accelerated ${
        isCritical 
          ? "bg-gradient-to-r from-red-50/90 via-rose-50/95 to-red-50/90 border-red-300 shadow-[0_16px_40px_rgba(239,68,68,0.12),inset_0_1px_0_rgba(255,255,255,0.9)]" 
          : "bg-gradient-to-r from-amber-50/90 via-orange-50/95 to-amber-50/90 border-amber-300 shadow-[0_16px_40px_rgba(245,158,11,0.12),inset_0_1px_0_rgba(255,255,255,0.9)]"
      }`}
    >
      <div 
        className={`px-6 py-4 flex items-center justify-between cursor-pointer transition-colors ${
          isCritical ? "hover:bg-red-100/50" : "hover:bg-amber-100/50"
        }`}
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-2xl text-white shadow-md ring-1 ring-white/30 ${
            isCritical ? "bg-gradient-to-br from-red-500 to-rose-700 shadow-red-500/30" : "bg-gradient-to-br from-amber-500 to-orange-600 shadow-amber-500/30"
          }`}>
            {isCritical ? (
              <AlertOctagon className="w-6 h-6 animate-pulse" />
            ) : (
              <Activity className="w-6 h-6" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h3 className={`font-black uppercase tracking-widest text-xs m-0 ${isCritical ? "text-red-700" : "text-amber-800"}`}>
                Early Warning System Alert
              </h3>
              <span className={`px-2.5 py-0.5 text-[10px] font-black rounded-full uppercase tracking-wider shadow-sm ${
                isCritical ? "bg-red-600 text-white" : "bg-amber-600 text-white"
              }`}>
                {data.probability_percentage}% PROBABILITY
              </span>
            </div>
            <p className={`text-base sm:text-lg font-bold m-0 tracking-tight ${isCritical ? "text-red-950" : "text-amber-950"}`}>
              {data.primary_warning_flag}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded-xl flex items-center justify-center border shadow-sm ${
            isCritical ? "border-red-200 bg-white/70 text-red-700" : "border-amber-200 bg-white/70 text-amber-700"
          }`}>
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </div>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className={`border-t px-6 py-6 bg-white/70 backdrop-blur-xl ${isCritical ? "border-red-200" : "border-amber-200"}`}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <h4 className={`text-xs font-black uppercase tracking-widest mb-3.5 ${isCritical ? "text-red-800" : "text-amber-900"}`}>
                  Contributing Clinical Factors
                </h4>
                <ul className="space-y-2.5 list-none p-0 m-0">
                  {data.contributing_factors.map((factor, i) => (
                    <li key={i} className={`flex items-start gap-2.5 text-sm font-medium p-2.5 rounded-xl border ${
                      isCritical 
                        ? "bg-red-50/80 border-red-100 text-red-950" 
                        : "bg-amber-50/80 border-amber-100 text-amber-950"
                    }`}>
                      <span className="w-1.5 h-1.5 rounded-full bg-red-500 mt-2 shrink-0" />
                      <span>{factor}</span>
                    </li>
                  ))}
                </ul>
              </div>
              
              <div>
                <h4 className="text-xs font-black uppercase tracking-wider mb-3 text-slate-700">Deterministic Clinical Scores</h4>
                <div className="grid grid-cols-4 gap-2.5 mb-5">
                  <div className="bg-slate-900 text-white p-3 rounded-2xl text-center shadow-md">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">NEWS2</span>
                    <span className={`text-2xl font-black ${data.news2_score >= 5 ? "text-rose-400" : "text-teal-300"}`}>{data.news2_score}</span>
                  </div>
                  <div className="bg-slate-900 text-white p-3 rounded-2xl text-center shadow-md">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">SIRS</span>
                    <span className={`text-2xl font-black ${data.sirs_score >= 2 ? "text-rose-400" : "text-teal-300"}`}>{data.sirs_score}/4</span>
                  </div>
                  <div className="bg-slate-900 text-white p-3 rounded-2xl text-center shadow-md">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">MEWS</span>
                    <span className={`text-2xl font-black ${data.mews_score >= 4 ? "text-rose-400" : "text-teal-300"}`}>{data.mews_score}</span>
                  </div>
                  <div className="bg-slate-900 text-white p-3 rounded-2xl text-center shadow-md">
                    <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">qSOFA</span>
                    <span className={`text-2xl font-black ${data.qsofa_score >= 2 ? "text-rose-400" : "text-teal-300"}`}>{data.qsofa_score}</span>
                  </div>
                </div>
                
                <h4 className="text-xs font-black uppercase tracking-wider mb-2.5 text-slate-700">Immediate Recommended Actions</h4>
                <ul className="space-y-2 list-none p-0 m-0">
                  {data.recommended_immediate_actions.map((action, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm font-medium p-2.5 rounded-xl bg-white border border-slate-200/80 shadow-sm text-slate-800">
                      <div className="w-2 h-2 rounded-full bg-teal-500 mt-1.5 flex-shrink-0" />
                      <span>{action}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
