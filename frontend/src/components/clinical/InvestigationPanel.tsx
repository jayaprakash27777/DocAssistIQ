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

const PRIORITY_STYLES: Record<string, { bg: string; text: string; border: string; dot: string }> = {
  "HIGH PRIORITY": { bg: "bg-red-50",    text: "text-red-700",    border: "border-red-200",    dot: "bg-red-500" },
  "CONDITIONAL":   { bg: "bg-amber-50",  text: "text-amber-700",  border: "border-amber-200",  dot: "bg-amber-500" },
  "IF INDICATED":  { bg: "bg-blue-50",   text: "text-blue-700",   border: "border-blue-200",   dot: "bg-blue-400" },
};

const Section = ({ title, items, color, icon: Icon, consultationId, disease }: { title: string, items: any[], color: string, icon: any, consultationId: string, disease: string }) => {
  if (items.length === 0) return null;
  return (
    <div className="mb-8 last:mb-0">
      <h6 className={`text-sm font-bold uppercase tracking-widest mb-4 flex items-center gap-2 ${color}`}>
        <Icon className="w-4 h-4" /> {title}
        <span className="ml-auto text-[10px] font-black text-slate-400 normal-case tracking-normal">
          {items.length} test{items.length !== 1 ? "s" : ""} · Drag any to Clinical Note
        </span>
      </h6>
      <div className="space-y-3">
        {items.map((item: any, idx: number) => {
          const pStyle = PRIORITY_STYLES[item.priority] || PRIORITY_STYLES["IF INDICATED"];
          // Rich drag payload for clinical note
          const dragText = [
            `${item.priority}: ${item.name || item.investigation_name}`,
            item.rationale ? `  Rationale: ${item.rationale}` : "",
            item.evidence  ? `  Evidence: ${item.evidence}` : "",
            item.safety_flags?.length ? `  ⚠️ Safety: ${item.safety_flags.join("; ")}` : "",
          ].filter(Boolean).join("\n");

          return (
            <motion.div
              key={`${item.investigation_name}-${idx}`}
              draggable={true}
              onDragStart={(e) => {
                const de = (e as unknown as DragEvent);
                if (de.dataTransfer) {
                  de.dataTransfer.setData("text/plain", dragText);
                  de.dataTransfer.effectAllowed = "copy";
                }
              }}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.06 }}
              className={`group relative px-5 py-4 rounded-2xl border ${pStyle.border} ${pStyle.bg} hover:shadow-md hover:border-slate-300/80 transition-all duration-200 cursor-grab active:cursor-grabbing active:scale-[0.99] active:opacity-80 backdrop-blur-md`}
            >
              {/* Drag tooltip */}
              <div className="absolute -top-7 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20">
                <div className="bg-slate-800 text-white text-[10px] font-bold px-2.5 py-1 rounded-lg shadow-lg whitespace-nowrap">
                  ⠿ Drag to Clinical Note
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className={`mt-0.5 w-2 h-2 rounded-full flex-shrink-0 ${pStyle.dot}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-3">
                    <span className={`font-bold text-sm ${pStyle.text} leading-tight`}>
                      {item.name || item.investigation_name}
                    </span>
                    <span className={`flex-shrink-0 text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full border ${pStyle.border} ${pStyle.text} ${pStyle.bg}`}>
                      {item.priority}
                    </span>
                  </div>
                  {item.rationale && (
                    <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">{item.rationale}</p>
                  )}
                  {item.evidence && (
                    <p className="text-[10px] text-slate-400 mt-1 font-medium italic">📚 {item.evidence}</p>
                  )}
                  {item.safety_flags?.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {item.safety_flags.map((flag: string, fi: number) => (
                        <span key={fi} className="text-[9px] font-bold text-red-700 bg-red-50 border border-red-200 px-2 py-0.5 rounded-full">
                          ⚠️ {flag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                <FeedbackButtons
                  suggestionId={`inv-${consultationId}-${disease}-${item.name || item.investigation_name}`}
                  suggestionType="investigation"
                  suggestionContext={item}
                />
              </div>
            </motion.div>
          );
        })}
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
      className="mt-6 p-7 overflow-hidden rounded-3xl shadow-[0_12px_44px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.95)] border border-slate-200/80 bg-white/90 backdrop-blur-3xl relative"
    >
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-cyan-400 opacity-80" />
      
      <div className="flex items-start justify-between mb-8 pb-5 border-b border-slate-200/60">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-white rounded-2xl shadow-sm border border-blue-100 flex items-center justify-center ring-2 ring-blue-50">
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
