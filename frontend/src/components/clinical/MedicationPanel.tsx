/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable react/no-unescaped-entities */
"use client";

import React, { useState, useEffect } from "react";
import { getMedicationsForDisease, MedicationResponse } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { Pill, AlertCircle, AlertTriangle, ShieldCheck, FileText, Beaker, Activity, Dna } from "lucide-react";
import FeedbackButtons from "./FeedbackButtons";
import ClinicalLoader from "./ClinicalLoader";
import PolypharmacySimulator from "./PolypharmacySimulator";

export default function MedicationPanel({ consultationId, disease }: { consultationId: string, disease: string }) {
  const [data, setData] = useState<MedicationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSimulator, setShowSimulator] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const res = await getMedicationsForDisease(consultationId, disease);
      if (res.ok) {
        setData(res.data);
      } else {
        if (res.error.message !== "Not Found") {
          setError(res.error.message || "Failed to load medications");
        }
      }
      setLoading(false);
    }
    load();
  }, [consultationId, disease]);

  if (loading) {
    return <ClinicalLoader label={`Analyzing safe FDA-approved medications for ${disease}...`} messages={["Checking formulary constraints", "Evaluating pharmacokinetic data", "Cross-referencing contraindications", "Filtering interactions", "Finalizing recommendations"]} />;
  }

  if (error) {
    return (
      <motion.div initial={{opacity:0}} animate={{opacity:1}} className="mt-4 p-4 text-xs text-[var(--color-danger-700)] bg-[var(--color-danger-50)]/80 rounded-2xl border border-[var(--color-danger-200)] flex items-center gap-2">
        <AlertCircle className="w-4 h-4"/> {error}
      </motion.div>
    );
  }

  if (!data || data.suggestions.length === 0) {
    return (
      <motion.div initial={{opacity:0}} animate={{opacity:1}} className="mt-4 p-4 text-xs text-[var(--text-secondary)] bg-[var(--surface-sunken)] rounded-2xl border border-[var(--border-default)] italic">
        No reference medications available for {disease}.
      </motion.div>
    );
  }

  const containerVars = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVars = {
    hidden: { opacity: 0, x: -20 },
    show: { opacity: 1, x: 0 }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-4 p-6 border border-emerald-200/80 bg-gradient-to-br from-emerald-50/40 via-white to-teal-50/30 rounded-3xl shadow-[0_12px_44px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.95)] backdrop-blur-3xl"
    >
      <div className="flex items-start justify-between mb-5 border-b border-emerald-100 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-white rounded-2xl shadow-sm border border-emerald-200/70 ring-2 ring-emerald-50">
            <Pill className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <h5 className="font-black text-slate-800 text-base tracking-tight">Reference Medications</h5>
            <p className="text-[9px] text-emerald-800 font-extrabold bg-emerald-100/80 border border-emerald-200/60 inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full shadow-xs uppercase tracking-wider mt-1">
              <ShieldCheck className="w-3 h-3 text-emerald-600" /> REFERENCE INFORMATION - CLINICIAN REVIEW REQUIRED
            </p>
          </div>
        </div>
        <div className="shrink-0 flex items-center gap-2 pt-1 pr-1">
          <button 
            onClick={() => setShowSimulator(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white text-xs font-extrabold rounded-xl shadow-sm hover:scale-105 active:scale-95 transition-all"
          >
            <Dna className="w-4 h-4" />
            Polypharmacy Simulator
          </button>
          <FeedbackButtons 
            suggestionId={`med-${consultationId}-${disease}`} 
            suggestionType="medication" 
            suggestionContext={data} 
          />
        </div>
      </div>

      <AnimatePresence>
        {showSimulator && (
          <PolypharmacySimulator 
            consultationId={consultationId}
            initialMedications={data.suggestions.map(s => s.generic_name)}
            onClose={() => setShowSimulator(false)}
          />
        )}
      </AnimatePresence>

      {data.ddi_warnings && data.ddi_warnings.length > 0 && (
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }} 
          animate={{ opacity: 1, scale: 1 }}
          className="mb-6 bg-[var(--color-danger-500)] text-white p-4 rounded-xl shadow-lg border-2 border-[var(--color-danger-700)] overflow-hidden relative"
        >
          <div className="absolute top-0 left-0 w-full h-1 bg-[var(--color-danger-300)] animate-pulse"></div>
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-6 h-6 animate-bounce" />
            <h4 className="font-black uppercase tracking-wider text-sm">NIH RxNav Safety Alert: Severe Drug Interaction</h4>
          </div>
          <p className="text-xs mb-3 font-medium opacity-90">
            The AI has generated a medication regimen containing contraindicated generic combinations based on live NIH data.
          </p>
          <ul className="list-disc pl-5 text-xs font-bold space-y-1 bg-black/20 p-3 rounded-lg">
            {data.ddi_warnings.map((warning, wIdx) => (
              <li key={wIdx}>{warning}</li>
            ))}
          </ul>
        </motion.div>
      )}

      <motion.div variants={containerVars} initial="hidden" animate="show" className="space-y-4">
        {data.suggestions.map((med, idx) => (
          <motion.div 
            variants={itemVars}
            key={idx} 
            draggable={true}
            onDragStart={(e) => {
              const de = (e as unknown as DragEvent);
              if (de.dataTransfer) {
                de.dataTransfer.setData("text/plain", `Plan: Start ${med.generic_name} - ${med.standard_reference_dosing} (Indication: ${med.indication})`);
              }
            }}
            className="bg-white/80 border border-[var(--glass-border)] rounded-xl p-5 shadow-sm relative overflow-hidden backdrop-blur-sm cursor-grab active:cursor-grabbing group"
          >
            <div className="absolute top-0 right-0 px-3 py-1 bg-[var(--color-success-50)] [var(--color-success-900)]/30 text-[var(--color-success-700)] [var(--color-success-400)] text-[9px] font-mono border-l border-b border-[var(--color-success-100)] [var(--color-success-800)] rounded-bl-xl shadow-sm flex items-center gap-1">
              <FileText className="w-3 h-3"/> {med.source_evidence}
            </div>
            
            <div className="flex items-center gap-3 mb-2">
              <div className="text-slate-300 hover:text-slate-500 cursor-grab px-1 -ml-2" title="Drag to Clinical Note">
                <span className="text-xl leading-none">⠿</span>
              </div>
              <h6 className="font-bold text-[var(--text-primary)] text-lg tracking-tight">{med.generic_name}</h6>
              {med.safety_decision && med.safety_decision.decision !== 'ALLOW' && (
                <span className={`px-2 py-1 rounded-md text-[10px] font-bold flex items-center gap-1 shadow-sm ${med.safety_decision.decision === 'ABSTAIN' ? 'bg-[var(--color-danger-50)] [var(--color-danger-900)]/30 text-[var(--color-danger-700)] [var(--color-danger-400)] border border-[var(--color-danger-200)] [var(--color-danger-800)]' : 'bg-[var(--color-warning-50)] [var(--color-warning-900)]/30 text-[var(--color-warning-700)] [var(--color-warning-400)] border border-[var(--color-warning-200)] [var(--color-warning-800)]'}`}>
                  {med.safety_decision.decision === 'ABSTAIN' ? <AlertCircle className="w-3 h-3"/> : <AlertTriangle className="w-3 h-3"/>}
                  {med.safety_decision.decision === 'ABSTAIN' ? 'CONTRAINDICATED' : 'WARNING'}
                </span>
              )}
            </div>
            
            {med.safety_decision && med.safety_decision.flags.length > 0 && (
              <div className="mb-4 space-y-2">
                {med.safety_decision.flags.map((flag, fidx) => (
                  <div key={fidx} className={`p-2.5 rounded-lg border text-xs flex gap-2 items-start ${flag.severity === 'CRITICAL' ? 'bg-[var(--color-danger-50)] [var(--color-danger-900)]/20 border-[var(--color-danger-200)] [var(--color-danger-800)] text-[var(--color-danger-800)] [var(--color-danger-300)]' : 'bg-[var(--color-warning-50)] [var(--color-warning-900)]/20 border-[var(--color-warning-200)] [var(--color-warning-800)] text-[var(--color-warning-800)] [var(--color-warning-300)]'}`}>
                    <AlertTriangle className={`w-4 h-4 shrink-0 ${flag.severity === 'CRITICAL' ? 'text-[var(--color-danger-500)]' : 'text-[var(--color-warning-500)]'}`} />
                    <div>
                      <span className="font-bold block uppercase tracking-wider text-[9px] opacity-80 mb-0.5">{flag.category}</span>
                      <p>{flag.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            <div className="text-[11px] text-[var(--text-secondary)] mb-4 flex gap-2">
              <span className="bg-[var(--surface-sunken)] px-2.5 py-1 rounded-md border border-[var(--border-default)] shadow-sm">{med.formulation}</span>
              <span className="bg-[var(--surface-sunken)] px-2.5 py-1 rounded-md border border-[var(--border-default)] shadow-sm">{med.route}</span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-6 gap-y-4 text-xs">
              <div className="bg-white  p-4 rounded-xl border border-[var(--glass-border)] shadow-sm">
                <span className="block text-[10px] uppercase font-bold text-[var(--text-tertiary)] mb-1 tracking-wider">Indication</span>
                <p className="text-[var(--text-secondary)] font-medium leading-relaxed">{med.indication}</p>
              </div>

              <div className="bg-white  p-4 rounded-xl border border-[var(--glass-border)] shadow-sm">
                <span className="block text-[10px] uppercase font-bold text-[var(--text-tertiary)] mb-2 tracking-wider">Standard Reference Dosing</span>
                <p className="text-[var(--color-success-800)] [var(--color-success-300)] bg-[var(--color-success-50)] [var(--color-success-900)]/20 border border-[var(--color-success-200)] [var(--color-success-800)] px-2.5 py-1.5 rounded-md inline-block font-mono text-[11px] shadow-sm">
                  {med.standard_reference_dosing}
                </p>
              </div>

              <div className="bg-white  p-4 rounded-xl border border-[var(--color-danger-200)] [var(--color-danger-800)] shadow-sm relative overflow-hidden">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-[var(--color-danger-500)]"></div>
                <span className="flex items-center gap-1.5 text-[10px] uppercase font-bold text-[var(--color-danger-600)] [var(--color-danger-400)] mb-3 tracking-wider">
                  <AlertTriangle className="w-3 h-3"/> Contraindications
                </span>
                {med.contraindications.length > 0 ? (
                  <ul className="list-disc pl-5 text-[var(--color-danger-700)] [var(--color-danger-300)] space-y-1.5 font-medium text-[11px]">
                    {med.contraindications.map((c, i) => <li key={i}>{c}</li>)}
                  </ul>
                ) : (
                  <span className="text-[var(--text-tertiary)] italic">None listed</span>
                )}
              </div>

              <div className="bg-white  p-4 rounded-xl border border-[var(--color-warning-200)] [var(--color-warning-800)] shadow-sm relative overflow-hidden">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-[var(--color-warning-500)]"></div>
                <span className="flex items-center gap-1.5 text-[10px] uppercase font-bold text-[var(--color-warning-600)] [var(--color-warning-400)] mb-3 tracking-wider">
                  <Activity className="w-3 h-3"/> Interactions
                </span>
                {med.interactions.length > 0 ? (
                  <ul className="list-disc pl-5 text-[var(--color-warning-700)] [var(--color-warning-300)] space-y-1.5 font-medium text-[11px]">
                    {med.interactions.map((i, k) => <li key={k}>{i}</li>)}
                  </ul>
                ) : (
                  <span className="text-[var(--text-tertiary)] italic">None listed</span>
                )}
              </div>
            </div>

            <div className="mt-5 pt-4 border-t border-[var(--border-default)] grid grid-cols-2 lg:grid-cols-4 gap-3 text-[10px]">
              <div className="bg-[var(--surface-sunken)] p-2.5 rounded-lg border border-[var(--border-default)] shadow-sm">
                <span className="block font-bold text-[var(--text-tertiary)] uppercase tracking-wider text-[9px] mb-1">Allergy</span>
                <span className={med.allergy_considerations === "Unavailable" ? "text-[var(--text-tertiary)] italic" : "text-[var(--text-secondary)] font-medium"}>{med.allergy_considerations}</span>
              </div>
              <div className="bg-[var(--surface-sunken)] p-2.5 rounded-lg border border-[var(--border-default)] shadow-sm">
                <span className="block font-bold text-[var(--text-tertiary)] uppercase tracking-wider text-[9px] mb-1">Renal</span>
                <span className={med.renal_considerations === "Unavailable" ? "text-[var(--text-tertiary)] italic" : "text-[var(--text-secondary)] font-medium"}>{med.renal_considerations}</span>
              </div>
              <div className="bg-[var(--surface-sunken)] p-2.5 rounded-lg border border-[var(--border-default)] shadow-sm">
                <span className="block font-bold text-[var(--text-tertiary)] uppercase tracking-wider text-[9px] mb-1">Hepatic</span>
                <span className={med.hepatic_considerations === "Unavailable" ? "text-[var(--text-tertiary)] italic" : "text-[var(--text-secondary)] font-medium"}>{med.hepatic_considerations}</span>
              </div>
              <div className="bg-[var(--surface-sunken)] p-2.5 rounded-lg border border-[var(--border-default)] shadow-sm">
                <span className="block font-bold text-[var(--text-tertiary)] uppercase tracking-wider text-[9px] mb-1">Pregnancy & Age</span>
                <span className={med.pregnancy_lactation_considerations === "Unavailable" ? "text-[var(--text-tertiary)] italic" : "text-[var(--text-secondary)] font-medium"}>{med.pregnancy_lactation_considerations} / {med.age_considerations}</span>
              </div>
              <div className="col-span-2 lg:col-span-4 bg-[var(--color-primary-50)]/50 [var(--color-primary-900)]/20 p-3 rounded-lg border border-[var(--color-primary-100)] [var(--color-primary-800)] shadow-sm flex items-start gap-3">
                <Beaker className="w-4 h-4 text-[var(--color-primary-500)] shrink-0 mt-0.5" />
                <div>
                  <span className="block font-bold text-[var(--color-primary-700)] [var(--color-primary-400)] uppercase tracking-wider text-[9px] mb-1">Monitoring & Labs</span>
                  <span className={med.monitoring_reference_information === "Unavailable" ? "text-[var(--text-tertiary)] italic text-xs" : "text-[var(--text-primary)] font-medium text-xs leading-relaxed"}>{med.monitoring_reference_information}</span>
                </div>
              </div>
            </div>

          </motion.div>
        ))}
      </motion.div>
    </motion.div>
  );
}
