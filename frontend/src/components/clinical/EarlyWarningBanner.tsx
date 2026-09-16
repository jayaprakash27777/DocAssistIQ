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
      className={`mb-6 rounded-2xl border shadow-lg overflow-hidden ${
        isCritical 
          ? "bg-red-50/90 border-red-200   shadow-red-500/10" 
          : "bg-orange-50/90 border-orange-200   shadow-orange-500/10"
      }`}
    >
      <div 
        className={`px-5 py-4 flex items-center justify-between cursor-pointer ${
          isCritical ? "hover:bg-red-100/50 :bg-red-900/30" : "hover:bg-orange-100/50 :bg-orange-900/30"
        } transition-colors`}
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-4">
          <div className={`p-2.5 rounded-full ${isCritical ? "bg-red-100 text-red-600  " : "bg-orange-100 text-orange-600  "}`}>
            {isCritical ? (
              <AlertOctagon className={`w-6 h-6 ${isCritical ? 'animate-pulse' : ''}`} />
            ) : (
              <Activity className="w-6 h-6" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h3 className={`font-black uppercase tracking-widest text-sm ${isCritical ? "text-red-700 " : "text-orange-700 "}`}>
                Early Warning System Alert
              </h3>
              <span className={`px-2 py-0.5 text-[10px] font-bold rounded-full ${isCritical ? "bg-red-600 text-white" : "bg-orange-500 text-white"}`}>
                {data.probability_percentage}% PROBABILITY
              </span>
            </div>
            <p className={`text-lg font-bold ${isCritical ? "text-red-950 " : "text-orange-950 "}`}>
              {data.primary_warning_flag}
            </p>
          </div>
        </div>
        <div className={`p-2 rounded-full ${isCritical ? "text-red-400" : "text-orange-400"}`}>
          {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </div>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className={`border-t px-6 py-5 ${isCritical ? "border-red-200 " : "border-orange-200 "}`}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <h4 className={`text-xs font-bold uppercase tracking-widest mb-3 ${isCritical ? "text-red-800 " : "text-orange-800 "}`}>
                  Contributing Clinical Factors
                </h4>
                <ul className="space-y-2">
                  {data.contributing_factors.map((factor, i) => (
                    <li key={i} className={`flex items-start gap-2 text-sm font-medium ${isCritical ? "text-red-900 " : "text-orange-900 "}`}>
                      <span className="mt-1 font-bold">•</span> {factor}
                    </li>
                  ))}
                </ul>
              </div>
              
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider mb-2 opacity-80">Deterministic Clinical Scores</h4>
                <div className="grid grid-cols-2 gap-2 mb-4">
                  <div className="bg-black/10  p-2 rounded-lg text-center">
                    <span className="block text-[10px] font-bold opacity-75">NEWS2</span>
                    <span className={`text-xl font-black ${data.news2_score >= 5 ? "text-red-300" : ""}`}>{data.news2_score}</span>
                  </div>
                  <div className="bg-black/10  p-2 rounded-lg text-center">
                    <span className="block text-[10px] font-bold opacity-75">SIRS</span>
                    <span className={`text-xl font-black ${data.sirs_score >= 2 ? "text-red-300" : ""}`}>{data.sirs_score}/4</span>
                  </div>
                  <div className="bg-black/10  p-2 rounded-lg text-center">
                    <span className="block text-[10px] font-bold opacity-75">MEWS</span>
                    <span className={`text-xl font-black ${data.mews_score >= 4 ? "text-red-300" : ""}`}>{data.mews_score}</span>
                  </div>
                  <div className="bg-black/10  p-2 rounded-lg text-center">
                    <span className="block text-[10px] font-bold opacity-75">qSOFA</span>
                    <span className={`text-xl font-black ${data.qsofa_score >= 2 ? "text-red-300" : ""}`}>{data.qsofa_score}</span>
                  </div>
                </div>
                
                <h4 className="text-xs font-bold uppercase tracking-wider mb-2 opacity-80">Immediate Recommended Actions</h4>
                <ul className="space-y-2">
                  {data.recommended_immediate_actions.map((action, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm font-medium">
                      <div className="w-1.5 h-1.5 rounded-full bg-current mt-1.5 flex-shrink-0" />
                      {action}
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
