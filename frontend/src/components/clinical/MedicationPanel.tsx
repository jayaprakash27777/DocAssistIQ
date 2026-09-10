"use client";

import React, { useState, useEffect } from "react";
import { getMedicationsForDisease, MedicationResponse } from "@/lib/api";
import { motion } from "framer-motion";
import { Pill, AlertCircle, AlertTriangle, ShieldCheck, FileText } from "lucide-react";

export default function MedicationPanel({ consultationId, disease }: { consultationId: string, disease: string }) {
  const [data, setData] = useState<MedicationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
    return (
      <div className="mt-4 p-4 border border-emerald-100 rounded-2xl bg-emerald-50/50 animate-pulse">
        <div className="h-4 bg-emerald-200 rounded w-1/4 mb-4"></div>
        <div className="h-10 bg-emerald-100 rounded-xl w-full mb-3"></div>
        <div className="h-10 bg-emerald-100 rounded-xl w-full"></div>
      </div>
    );
  }

  if (error) {
    return (
      <motion.div initial={{opacity:0}} animate={{opacity:1}} className="mt-4 p-4 text-xs text-rose-600 bg-rose-50/80 rounded-2xl border border-rose-200 flex items-center gap-2">
        <AlertCircle className="w-4 h-4"/> {error}
      </motion.div>
    );
  }

  if (!data || data.suggestions.length === 0) {
    return (
      <motion.div initial={{opacity:0}} animate={{opacity:1}} className="mt-4 p-4 text-xs text-gray-500 bg-gray-50/80 rounded-2xl border border-[var(--border-default)] italic">
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
      className="mt-4 p-5 border border-emerald-200/60 bg-emerald-50/30 rounded-2xl shadow-sm backdrop-blur-md"
    >
      <div className="flex items-center gap-3 mb-4 border-b border-emerald-100/50 pb-3">
        <div className="p-2 bg-white rounded-xl shadow-sm border border-emerald-100">
          <Pill className="w-5 h-5 text-emerald-500" />
        </div>
        <div>
          <h5 className="font-bold text-emerald-950 text-base">Reference Medications</h5>
          <p className="text-[10px] text-emerald-700 font-bold bg-emerald-100/80 inline-flex items-center gap-1 px-1.5 py-0.5 rounded shadow-sm">
            <ShieldCheck className="w-3 h-3"/> REFERENCE INFORMATION - CLINICIAN REVIEW REQUIRED
          </p>
        </div>
      </div>

      <motion.div variants={containerVars} initial="hidden" animate="show" className="space-y-4">
        {data.suggestions.map((med, idx) => (
          <motion.div 
            variants={itemVars}
            key={idx} 
            className="bg-white/80 border border-[var(--glass-border)] rounded-xl p-5 shadow-sm relative overflow-hidden backdrop-blur-sm"
          >
            <div className="absolute top-0 right-0 px-3 py-1 bg-[var(--color-primary-50)] text-[var(--color-primary-700)] text-[9px] font-mono border-l border-b border-[var(--color-primary-100)] rounded-bl-xl shadow-sm flex items-center gap-1">
              <FileText className="w-3 h-3"/> {med.source_evidence}
            </div>
            
            <div className="flex items-center gap-3 mb-2">
              <h6 className="font-bold text-gray-900 text-lg tracking-tight">{med.generic_name}</h6>
              {med.safety_decision && med.safety_decision.decision !== 'ALLOW' && (
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold flex items-center gap-1 ${med.safety_decision.decision === 'ABSTAIN' ? 'bg-rose-100 text-rose-700 border border-rose-200' : 'bg-amber-100 text-amber-700 border border-amber-200'}`}>
                  {med.safety_decision.decision === 'ABSTAIN' ? <AlertCircle className="w-3 h-3"/> : <AlertTriangle className="w-3 h-3"/>}
                  {med.safety_decision.decision === 'ABSTAIN' ? 'CONTRAINDICATED' : 'WARNING'}
                </span>
              )}
            </div>
            
            {med.safety_decision && med.safety_decision.flags.length > 0 && (
              <div className="mb-4 space-y-2">
                {med.safety_decision.flags.map((flag, fidx) => (
                  <div key={fidx} className={`p-2 rounded-lg border text-xs flex gap-2 items-start ${flag.severity === 'CRITICAL' ? 'bg-rose-50 border-rose-200 text-rose-800' : 'bg-amber-50 border-amber-200 text-amber-800'}`}>
                    <AlertTriangle className={`w-4 h-4 shrink-0 ${flag.severity === 'CRITICAL' ? 'text-rose-500' : 'text-amber-500'}`} />
                    <div>
                      <span className="font-bold block uppercase tracking-wide text-[9px] opacity-80 mb-0.5">{flag.category}</span>
                      <p>{flag.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            <div className="text-[11px] text-gray-500 mb-4 flex gap-2">
              <span className="bg-gray-100/80 px-2 py-1 rounded-md border border-[var(--border-default)] shadow-sm">{med.formulation}</span>
              <span className="bg-gray-100/80 px-2 py-1 rounded-md border border-[var(--border-default)] shadow-sm">{med.route}</span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-6 gap-y-4 text-xs">
              <div className="bg-white p-3 rounded-lg border border-[var(--glass-border)] shadow-sm">
                <span className="block text-[10px] uppercase font-bold text-gray-400 mb-1 tracking-wider">Indication</span>
                <p className="text-gray-800">{med.indication}</p>
              </div>

              <div className="bg-white p-3 rounded-lg border border-[var(--glass-border)] shadow-sm">
                <span className="block text-[10px] uppercase font-bold text-gray-400 mb-1 tracking-wider">Standard Reference Dosing</span>
                <p className="text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-1 rounded inline-block font-mono text-[11px] shadow-sm">
                  {med.standard_reference_dosing}
                </p>
              </div>

              <div className="bg-white p-3 rounded-lg border border-rose-100 shadow-sm relative overflow-hidden">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-rose-500"></div>
                <span className="flex items-center gap-1 text-[10px] uppercase font-bold text-rose-500 mb-2 tracking-wider">
                  <AlertTriangle className="w-3 h-3"/> Contraindications
                </span>
                {med.contraindications.length > 0 ? (
                  <ul className="list-disc pl-5 text-rose-700 space-y-1 font-medium">
                    {med.contraindications.map((c, i) => <li key={i}>{c}</li>)}
                  </ul>
                ) : (
                  <span className="text-gray-400 italic">None listed</span>
                )}
              </div>

              <div className="bg-white p-3 rounded-lg border border-amber-100 shadow-sm relative overflow-hidden">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-amber-500"></div>
                <span className="flex items-center gap-1 text-[10px] uppercase font-bold text-amber-500 mb-2 tracking-wider">
                  <AlertTriangle className="w-3 h-3"/> Interactions
                </span>
                {med.interactions.length > 0 ? (
                  <ul className="list-disc pl-5 text-amber-700 space-y-1 font-medium">
                    {med.interactions.map((i, k) => <li key={k}>{i}</li>)}
                  </ul>
                ) : (
                  <span className="text-gray-400 italic">None listed</span>
                )}
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-[var(--border-default)] grid grid-cols-2 lg:grid-cols-4 gap-4 text-[10px]">
              <div className="bg-gray-50/50 p-2 rounded-md border border-[var(--border-default)]">
                <span className="block font-bold text-gray-500 mb-0.5">Allergy</span>
                <span className={med.allergy_considerations === "Unavailable" ? "text-gray-400 italic" : "text-gray-800 font-medium"}>{med.allergy_considerations}</span>
              </div>
              <div className="bg-gray-50/50 p-2 rounded-md border border-[var(--border-default)]">
                <span className="block font-bold text-gray-500 mb-0.5">Renal</span>
                <span className={med.renal_considerations === "Unavailable" ? "text-gray-400 italic" : "text-gray-800 font-medium"}>{med.renal_considerations}</span>
              </div>
              <div className="bg-gray-50/50 p-2 rounded-md border border-[var(--border-default)]">
                <span className="block font-bold text-gray-500 mb-0.5">Hepatic</span>
                <span className={med.hepatic_considerations === "Unavailable" ? "text-gray-400 italic" : "text-gray-800 font-medium"}>{med.hepatic_considerations}</span>
              </div>
              <div className="bg-gray-50/50 p-2 rounded-md border border-[var(--border-default)]">
                <span className="block font-bold text-gray-500 mb-0.5">Pregnancy</span>
                <span className={med.pregnancy_lactation_considerations === "Unavailable" ? "text-gray-400 italic" : "text-gray-800 font-medium"}>{med.pregnancy_lactation_considerations}</span>
              </div>
              <div className="bg-gray-50/50 p-2 rounded-md border border-[var(--border-default)]">
                <span className="block font-bold text-gray-500 mb-0.5">Age</span>
                <span className={med.age_considerations === "Unavailable" ? "text-gray-400 italic" : "text-gray-800 font-medium"}>{med.age_considerations}</span>
              </div>
              <div className="col-span-2 lg:col-span-3 bg-[var(--color-primary-50)]/50 p-2 rounded-md border border-[var(--color-primary-100)]">
                <span className="block font-bold text-[var(--color-primary-700)] mb-0.5">Monitoring</span>
                <span className={med.monitoring_reference_information === "Unavailable" ? "text-gray-400 italic" : "text-gray-800 font-medium"}>{med.monitoring_reference_information}</span>
              </div>
            </div>

          </motion.div>
        ))}
      </motion.div>
    </motion.div>
  );
}
