"use client";

import React, { useState, useEffect } from "react";
import { getDifferentialDiagnosis, DifferentialDiagnosisResponse } from "@/lib/api";
import { toast } from "react-hot-toast";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, ChevronDown, ChevronUp, AlertTriangle, ShieldAlert } from "lucide-react";
import InvestigationPanel from "./InvestigationPanel";
import MedicationPanel from "./MedicationPanel";

export default function DifferentialDiagnosis({ consultationId }: { consultationId: string }) {
  const [data, setData] = useState<DifferentialDiagnosisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [showInvestigationsFor, setShowInvestigationsFor] = useState<string | null>(null);
  const [showMedicationsFor, setShowMedicationsFor] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const res = await getDifferentialDiagnosis(consultationId);
      if (res.ok) {
        setData(res.data);
      } else {
        // Suppress 404s or empty state logs for differential if it's not ready
        if (res.error.message !== "Not Found") {
          toast.error(res.error.message || "Failed to load differential diagnosis");
        }
      }
      setLoading(false);
    }
    load();
  }, [consultationId]);

  if (loading) {
    return (
      <div className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm mb-6">
        <div className="animate-pulse flex space-x-4">
          <div className="flex-1 space-y-4 py-1">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  if (data.status === "INSUFFICIENT_INFO") {
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel overflow-hidden mb-6 rounded-2xl"
      >
        <div className="bg-[var(--surface-overlay)] px-4 py-3 border-b border-[var(--glass-border)] flex items-center gap-2">
          <Bot className="w-5 h-5 text-gray-500" />
          <h3 className="font-semibold text-gray-700 text-sm tracking-wide">AI DIFFERENTIAL SUGGESTION</h3>
        </div>
        <div className="p-8 flex flex-col items-center justify-center text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4 shadow-inner">
            🤷
          </div>
          <h4 className="text-lg font-bold text-gray-800 mb-2">Insufficient Information</h4>
          <p className="text-sm text-gray-600 max-w-sm mb-6">
            {data.message || "Not enough clinical information provided to generate a safe differential diagnosis."}
          </p>
          {data.missing_critical_info.length > 0 && (
            <div className="text-left bg-yellow-50/80 text-yellow-800 p-4 rounded-xl border border-yellow-200/50 text-xs w-full max-w-sm shadow-sm">
              <strong className="block mb-2 flex items-center gap-1"><AlertTriangle className="w-3 h-3"/> Missing Requirements:</strong>
              <ul className="list-disc pl-4 space-y-1">
                {data.missing_critical_info.map((info, i) => (
                  <li key={i}>{info}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </motion.div>
  }

  if (data.top_candidates.length === 0) {
    return null;
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel mb-8 overflow-hidden rounded-2xl shadow-xl shadow-[var(--glass-shadow)] border border-[var(--glass-border)]"
    >
      <div className="bg-gradient-to-r from-[var(--color-primary-50)] to-transparent px-5 py-4 border-b border-[var(--glass-border)] flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white rounded-xl shadow-sm border border-[var(--glass-border)]">
            <Bot className="w-5 h-5 text-[var(--color-primary-600)]" />
          </div>
          <h3 className="font-bold text-[var(--color-primary-950)] tracking-wide">AI DIFFERENTIAL SUGGESTION</h3>
        </div>
        <span className="text-xs text-[var(--color-primary-700)] bg-white/60 px-3 py-1.5 rounded-full font-bold shadow-sm border border-[var(--glass-border)] backdrop-blur-md">
          Top {data.top_candidates.length} Candidates
        </span>
      </div>
      
      <div className="px-5 py-3 bg-[var(--clinical-warning-bg)] text-[var(--clinical-warning-text)] text-[11px] border-b border-[var(--clinical-warning-border)] flex items-start gap-3 backdrop-blur-sm">
        <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
        <p className="font-medium leading-relaxed">This ranking is a decision-support algorithmic suggestion grounded in FDA data. Independent clinician review is strictly required.</p>
      </div>

      <div className="divide-y divide-[var(--border-default)]">
        <AnimatePresence>
        {data.top_candidates.map((candidate, idx) => (
          <motion.div 
            key={idx} 
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="flex flex-col bg-white/40 hover:bg-white/80 transition-all duration-300"
          >
            <div 
              className="p-5 flex items-center justify-between cursor-pointer"
              onClick={() => setExpandedIndex(expandedIndex === idx ? null : idx)}
            >
              <div className="flex items-center gap-5">
                <div className="w-8 h-8 flex items-center justify-center rounded-xl bg-[var(--color-primary-100)] text-[var(--color-primary-700)] font-bold text-sm shrink-0 shadow-inner">
                  {idx + 1}
                </div>
                <div>
                  <h4 className="font-bold text-gray-900 text-lg tracking-tight">{candidate.disease}</h4>
                  <div className="text-xs text-gray-500 mt-1.5 flex items-center gap-3">
                    <div className="w-32 h-2 bg-gray-200/50 rounded-full overflow-hidden shadow-inner">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min(100, Math.max(5, candidate.score * 100))}%` }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        className={`h-full rounded-full ${candidate.score > 0.6 ? 'bg-gradient-to-r from-emerald-400 to-emerald-500' : candidate.score > 0.3 ? 'bg-gradient-to-r from-amber-400 to-amber-500' : 'bg-gradient-to-r from-orange-400 to-orange-500'}`} 
                      />
                    </div>
                    <span className="font-bold text-gray-700">{Math.round(candidate.score * 100)}% Match</span>
                  </div>
                  {candidate.safety_decision && candidate.safety_decision.decision !== "ALLOW" && (
                    <div className="mt-2 flex items-center gap-1">
                      <span className={`flex items-center gap-1 text-[10px] px-2 py-1 rounded-md font-bold shadow-sm ${
                        candidate.safety_decision.decision === 'ABSTAIN' ? 'bg-red-100/80 text-red-700 border border-red-200' : 'bg-yellow-100/80 text-yellow-700 border border-yellow-200'
                      }`}>
                        <ShieldAlert className="w-3 h-3"/> {candidate.safety_decision.decision === 'ABSTAIN' ? 'UNSAFE' : 'WARNING'}
                      </span>
                    </div>
                  )}
                </div>
              </div>
              <div className="text-[var(--color-primary-400)] transition-transform duration-300">
                {expandedIndex === idx ? <ChevronUp className="w-5 h-5"/> : <ChevronDown className="w-5 h-5"/>}
              </div>
            </div>

            <AnimatePresence>
            {expandedIndex === idx && (
              <motion.div 
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="px-16 pb-6 pt-2 space-y-6 overflow-hidden"
              >
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Supporting Findings */}
                  <div className="bg-white/50 p-4 rounded-xl border border-[var(--glass-border)] shadow-sm">
                    <h5 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3">Supporting Findings</h5>
                    {candidate.supporting_findings.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {candidate.supporting_findings.map((f, i) => (
                          <span key={i} className="bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-md text-[11px] font-medium border border-emerald-100 shadow-sm">{f}</span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-gray-400 text-xs italic">None documented</span>
                    )}
                  </div>

                  {/* Missing/Contradicting */}
                  <div className="bg-white/50 p-4 rounded-xl border border-[var(--glass-border)] shadow-sm">
                    <h5 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3">Missing / Contradicting</h5>
                    {candidate.missing_expected_findings.length > 0 || candidate.contradicting_information.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {candidate.missing_expected_findings.map((f, i) => (
                          <span key={`m-${i}`} className="bg-gray-100 text-gray-600 px-2.5 py-1 rounded-md text-[11px] font-medium border border-gray-200 shadow-sm flex items-center gap-1"><span className="text-gray-400 line-through text-[9px]">EXPECTED</span> {f}</span>
                        ))}
                        {candidate.contradicting_information.map((f, i) => (
                          <span key={`c-${i}`} className="bg-rose-50 text-rose-700 px-2.5 py-1 rounded-md text-[11px] font-medium border border-rose-100 shadow-sm flex items-center gap-1"><span className="text-rose-400 font-bold text-[9px]">CONTRADICTS</span> {f}</span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-gray-400 text-xs italic">None identified</span>
                    )}
                  </div>
                </div>

                {/* Explanation Reference */}
                <div className="bg-[var(--color-primary-50)]/50 p-4 rounded-xl border border-[var(--color-primary-100)] shadow-sm">
                  <h5 className="text-[10px] font-bold text-[var(--color-primary-700)] uppercase tracking-widest mb-2">FDA Grounded Rationale</h5>
                  <p className="text-xs text-gray-700 leading-relaxed">{candidate.explanation_reference}</p>
                </div>

                <div className="flex gap-3 pt-2">
                  <button 
                    onClick={() => {
                        setShowInvestigationsFor(showInvestigationsFor === candidate.disease ? null : candidate.disease);
                        setShowMedicationsFor(null);
                    }}
                    className="text-[11px] font-bold text-[var(--color-primary-700)] bg-[var(--color-primary-50)] hover:bg-[var(--color-primary-100)] border border-[var(--color-primary-200)] px-4 py-2 rounded-lg transition-all shadow-sm"
                  >
                    {showInvestigationsFor === candidate.disease ? 'Hide' : 'View'} Expected Investigations
                  </button>
                  <button 
                    onClick={() => {
                        setShowMedicationsFor(showMedicationsFor === candidate.disease ? null : candidate.disease);
                        setShowInvestigationsFor(null);
                    }}
                    className="text-[11px] font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 px-4 py-2 rounded-lg transition-all shadow-sm"
                  >
                    {showMedicationsFor === candidate.disease ? 'Hide' : 'View'} Safe Medications
                  </button>
                </div>
                  
                {/* Collapsible Sub-panels */}
                <AnimatePresence>
                {showInvestigationsFor === candidate.disease && (
                  <motion.div initial={{opacity:0, y:-10}} animate={{opacity:1, y:0}} exit={{opacity:0, height:0}} className="mt-4">
                    <InvestigationPanel consultationId={consultationId} disease={candidate.disease} />
                  </motion.div>
                )}
                {showMedicationsFor === candidate.disease && (
                  <motion.div initial={{opacity:0, y:-10}} animate={{opacity:1, y:0}} exit={{opacity:0, height:0}} className="mt-4">
                    <MedicationPanel consultationId={consultationId} disease={candidate.disease} />
                  </motion.div>
                )}
                </AnimatePresence>
              </motion.div>
            )}
            </AnimatePresence>
          </motion.div>
        ))}
        </AnimatePresence>
      </div>
      
      <div className="bg-gray-50 p-2 border-t border-[var(--border-default)] text-right">
        <span className="text-[10px] text-gray-400 font-mono">Provider: {data.provider_metadata.provider} v{data.provider_metadata.version}</span>
      </div>
    </motion.div>
  );
}
