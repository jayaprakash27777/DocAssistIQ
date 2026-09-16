/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React, { useState, useEffect } from "react";
import { getInvestigationsForDisease, InvestigationResponse } from "@/lib/api";
import FeedbackButtons from "./FeedbackButtons";
import { motion, AnimatePresence } from "framer-motion";
import ClinicalLoader from "./ClinicalLoader";
import { AlertTriangle, AlertCircle, FileText, CheckCircle2 } from "lucide-react";

const Section = ({ title, items, color, icon: Icon, consultationId, disease }: { title: string, items: any[], color: string, icon: any, consultationId: string, disease: string }) => {
  if (items.length === 0) return null;
  return (
    <div className="mb-8 last:mb-0">
      <h6 className={`text-sm font-bold uppercase tracking-widest mb-6 flex items-center gap-3 ${color}`}>
        <Icon className="w-5 h-5" /> {title}
      </h6>
      <div className="space-y-4">
        {items.map((item: any, idx: number) => (
          <motion.div 
            key={`${item.investigation_name}-${idx}`}
            draggable={true}
            onDragStart={(e) => {
              e.dataTransfer.setData("text/plain", `Plan: Order ${item.name || item.investigation_name} - ${item.rationale || item.reason}`);
            }}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="group px-6 py-5 bg-white/70 rounded-2xl border border-white hover:border-blue-300 transition-all duration-300 shadow-[0_2px_10px_rgb(0,0,0,0.02)] hover:shadow-[0_8px_30px_rgb(59,130,246,0.1)] relative overflow-hidden backdrop-blur-xl cursor-grab active:cursor-grabbing"
          >
            <div className="flex justify-between items-start gap-6 relative z-10">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <div className="text-slate-300 hover:text-slate-500 cursor-grab px-1 -ml-2" title="Drag to Clinical Note">
                    <span className="text-xl leading-none">⠿</span>
                  </div>
                  <span className="font-bold text-lg text-slate-800 group-hover:text-blue-600 transition-colors">
                    {item.name || item.investigation_name}
                  </span>
                  {item.is_fasting_required && (
                    <span className="px-2.5 py-1 text-xs font-bold uppercase tracking-widest bg-[var(--color-warning-50)] text-[var(--color-warning-700)] rounded-full">
                      Fasting
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-600 leading-relaxed font-medium">
                  {item.rationale || item.reason}
                </p>
              </div>
              <div className="opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                <FeedbackButtons 
                  suggestionId={`inv-${consultationId}-${disease}-${item.name || item.investigation_name}`} 
                  suggestionType="investigation" 
                  suggestionContext={item} 
                />
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default function InvestigationPanel({ consultationId, disease, competing = [] }: { consultationId: string, disease: string, competing?: string[] }) {
  const [data, setData] = useState<InvestigationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const res = await getInvestigationsForDisease(consultationId, disease, competing);
      if (res.ok) {
        setData(res.data);
      } else {
        if (res.error.message !== "Not Found") {
          setError(res.error.message || "Failed to load investigations");
        }
      }
      setLoading(false);
    }
    load();
  }, [consultationId, disease]);

  if (loading) {
    return <ClinicalLoader label={`Evaluating workup for ${disease}...`} messages={["Reviewing clinical presentation", "Analyzing standard of care guidelines", "Synthesizing investigation panel", "Finalizing recommendations"]} />;
  }

  if (error) {
    return <div className="mt-4 p-4 text-xs text-[var(--color-danger-700)] bg-[var(--color-danger-50)]/80 rounded-2xl border border-[var(--color-danger-200)] flex items-center gap-2"><AlertCircle className="w-4 h-4"/> {error}</div>;
  }

  if (!data || data.suggestions.length === 0) {
    return (
      <div className="mt-4 p-4 text-xs text-[var(--text-secondary)] bg-[var(--surface-sunken)] rounded-2xl border border-[var(--border-default)] italic">
        No reference investigations available for {disease}.
      </div>
    );
  }

  const highPriority = data.suggestions.filter(s => s.priority === "HIGH PRIORITY");
  const conditional = data.suggestions.filter(s => s.priority === "CONDITIONAL");
  const ifIndicated = data.suggestions.filter(s => s.priority === "IF INDICATED");


  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-6 p-6 overflow-hidden rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-white/60 bg-white/40 backdrop-blur-2xl relative"
    >
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-300 to-cyan-300 opacity-70"></div>
      
      <div className="flex items-start justify-between mb-8 pb-5 border-b border-white/50">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-white/80 rounded-2xl shadow-sm border border-blue-100/50 flex items-center justify-center backdrop-blur-md">
            <FileText className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h5 className="font-black text-slate-800 text-lg tracking-tight">Expected Investigations</h5>
            <p className="text-[10px] text-slate-500 font-bold tracking-widest uppercase mt-1">Context-aware algorithmic recommendations</p>
          </div>
        </div>
        <div className="shrink-0">
          <FeedbackButtons 
            suggestionId={`inv-${consultationId}-${disease}`} 
            suggestionType="investigation" 
            suggestionContext={data} 
          />
        </div>
      </div>

      <div className="space-y-6">
        <Section title="High Priority / Immediate" items={highPriority} color="text-[var(--color-danger-600)] [var(--color-danger-400)]" icon={AlertCircle} consultationId={consultationId} disease={disease} />
        <Section title="Conditional / Monitor" items={conditional} color="text-[var(--color-warning-600)] [var(--color-warning-400)]" icon={AlertTriangle} consultationId={consultationId} disease={disease} />
        <Section title="If Indicated" items={ifIndicated} color="text-[var(--color-primary-600)] [var(--color-primary-400)]" icon={CheckCircle2} consultationId={consultationId} disease={disease} />
      </div>
    </motion.div>
  );
}
