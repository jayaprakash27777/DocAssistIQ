"use client";

import React, { useState, useEffect } from "react";
import { getEpiRadar, EpiRadarResponse } from "@/lib/api";
import { Radar, Users, MapPin, AlertTriangle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function EpiRadarAlert({ consultationId, trigger }: { consultationId: string, trigger?: any }) {
  const [data, setData] = useState<EpiRadarResponse | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    async function load() {
      const res = await getEpiRadar(consultationId);
      if (res.ok && res.data.cluster_detected) {
        setData(res.data);
      }
    }
    load();
  }, [consultationId, trigger]);

  if (!data || !data.cluster_detected || dismissed) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="dashboard-card mb-8 !block !p-0 overflow-hidden bg-purple-50/30 hover:bg-purple-50/50 border-purple-200"
    >
      <div className="bg-gradient-to-r from-purple-100/80 to-transparent px-5 py-3 border-b border-purple-200 flex justify-between items-center relative z-10">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white text-purple-600 rounded-xl shadow-sm border border-purple-100">
            <Radar className="w-5 h-5 animate-[spin_4s_linear_infinite]" />
          </div>
          <div>
            <h3 className="font-bold uppercase tracking-widest text-[10px] text-purple-800">
              Syndromic Surveillance Alert
            </h3>
            <p className="text-sm font-bold text-purple-950 flex items-center gap-2">
              <MapPin className="w-3 h-3" /> Local Geographic Cluster Detected
            </p>
          </div>
        </div>
        <button 
          onClick={() => setDismissed(true)}
          className="text-purple-500 hover:text-purple-700 text-xs font-bold bg-white/50 px-3 py-1.5 rounded-full transition-colors border border-purple-200 shadow-sm"
        >
          Dismiss
        </button>
      </div>

      <div className="p-5 relative z-10">
        <div className="flex flex-col md:flex-row gap-6">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-purple-600" />
              <h4 className="font-bold text-lg text-purple-900">{data.cluster_name}</h4>
            </div>
            <p className="text-sm text-purple-800 mb-4 font-medium leading-relaxed">
              {data.warning_message}
            </p>
            
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[10px] font-bold text-purple-700 uppercase tracking-widest">Matched Symptoms:</span>
              {data.matched_symptoms.map((sym, i) => (
                <span key={i} className="px-2.5 py-1 bg-white text-purple-900 border border-purple-200 shadow-sm rounded-md text-xs font-bold">
                  {sym}
                </span>
              ))}
            </div>
          </div>
          
          <div className="w-px bg-purple-200 hidden md:block"></div>
          
          <div className="md:w-1/3 flex flex-col justify-center items-center p-4 bg-white/60 rounded-2xl border border-purple-100 shadow-sm">
            <Users className="w-8 h-8 text-purple-500 mb-2" />
            <span className="text-3xl font-black text-purple-900 font-heading">{data.local_cases_last_48h}</span>
            <span className="text-[10px] font-bold text-purple-700 uppercase tracking-widest text-center mt-1">Similar Cases<br/>Last 48 Hours</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
