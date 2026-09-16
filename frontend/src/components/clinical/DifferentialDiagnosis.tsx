/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable react/no-unescaped-entities */
"use client";

import React, { useState, useEffect } from "react";
import { getDifferentialDiagnosis, DifferentialDiagnosisResponse } from "@/lib/api";
import { toast } from "react-hot-toast";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, ChevronDown, ChevronUp, AlertTriangle, ShieldAlert } from "lucide-react";
import InvestigationPanel from "./InvestigationPanel";
import MedicationPanel from "./MedicationPanel";
import DiseaseIntelligencePanel from "./DiseaseIntelligencePanel";
import EarlyWarningBanner from "./EarlyWarningBanner";
import EpiRadarAlert from "./EpiRadarAlert";
import ControversyScanner from "./ControversyScanner";
import FeedbackButtons from "./FeedbackButtons";
import ClinicalLoader from "./ClinicalLoader";
import { Button } from "@/components/ui/button";

export default function DifferentialDiagnosis({ consultationId, trigger }: { consultationId: string, trigger?: any }) {
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
  }, [consultationId, trigger]);

  if (loading) {
    return <ClinicalLoader label="Generating Differential Diagnosis..." />;
  }

  if (!data) {
    return null;
  }

  if (data.status === "INSUFFICIENT_INFO") {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel overflow-hidden mb-6 rounded-2xl border border-[var(--border-default)]"
      >
        <div className="bg-[var(--color-primary-50)] px-4 py-3 border-b border-[var(--color-primary-200)] flex items-center gap-2">
          <Bot className="w-5 h-5 text-[var(--color-primary-600)]" />
          <h3 className="font-semibold text-[var(--color-primary-900)] text-sm tracking-wide">AI DIFFERENTIAL SUGGESTION</h3>
        </div>
        <div className="p-8 flex flex-col items-center justify-center text-center">
          <div className="w-16 h-16 bg-[var(--surface-sunken)] rounded-full flex items-center justify-center mb-4 shadow-inner text-2xl">
            🤷
          </div>
          <h4 className="text-lg font-bold text-[var(--text-primary)] mb-2">Insufficient Information</h4>
          <p className="text-sm text-[var(--text-secondary)] max-w-sm mb-6">
            {data.message || "Not enough clinical information provided to generate a safe differential diagnosis."}
          </p>
          {data.missing_critical_info.length > 0 && (
            <div className="text-left bg-[var(--color-warning-50)] text-[var(--color-warning-800)] p-4 rounded-xl border border-[var(--color-warning-200)] text-xs w-full max-w-sm shadow-sm">
              <strong className="block mb-2 flex items-center gap-1 font-bold"><AlertTriangle className="w-3 h-3"/> Missing Requirements:</strong>
              <ul className="list-disc pl-4 space-y-1 font-medium">
                {data.missing_critical_info.map((info, i) => (
                  <li key={i}>{info}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </motion.div>
    );
  }

  if (data.top_candidates.length === 0) {
    return (
      <div className="glass-panel mb-8 p-8 flex flex-col items-center justify-center text-center rounded-2xl border border-[var(--border-default)]">
        <div className="w-16 h-16 bg-[var(--surface-sunken)] rounded-full flex items-center justify-center mb-4 shadow-inner text-2xl">
          🔍
        </div>
        <h4 className="text-lg font-bold text-[var(--text-primary)] mb-2">No Candidates Identified</h4>
        <p className="text-sm text-[var(--text-secondary)] max-w-sm">
          The AI was unable to confidently identify differential diagnosis candidates based on the current clinical findings.
        </p>
      </div>
    );
  }

  return (
    <>
      <EarlyWarningBanner consultationId={consultationId} trigger={trigger} />
      <EpiRadarAlert consultationId={consultationId} trigger={trigger} />
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 overflow-hidden rounded-3xl shadow-[0_8px_40px_rgb(0,0,0,0.04)] border border-white/60 bg-white/40 backdrop-blur-2xl relative"
      >
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 opacity-70"></div>
      
      <div className="bg-gradient-to-r from-blue-50/80 to-transparent px-6 py-5 border-b border-white/50 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <div className="p-2.5 bg-white rounded-2xl shadow-sm border border-blue-100/50">
            <Bot className="w-6 h-6 text-blue-600" />
          </div>
          <h3 className="font-black text-slate-800 text-lg tracking-tight">AI DIFFERENTIAL SUGGESTION</h3>
        </div>
        <span className="text-xs text-blue-700 bg-white/80 px-4 py-1.5 rounded-full font-bold shadow-sm border border-blue-100 backdrop-blur-md">
          Top {data.top_candidates.length} Candidates
        </span>
      </div>
      
      <div className="px-5 py-3 bg-[var(--clinical-warning-bg)] text-[var(--clinical-warning-text)] text-[11px] border-b border-[var(--clinical-warning-border)] flex justify-between items-start gap-3 backdrop-blur-sm">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
          <p className="font-medium leading-relaxed">This ranking is a decision-support algorithmic suggestion grounded in FDA data. Independent clinician review is strictly required.</p>
        </div>
        <div className="shrink-0 pt-0.5 pr-2">
           <FeedbackButtons 
             suggestionId={`diff-${data.consultation_id}`} 
             suggestionType="diagnosis" 
             suggestionContext={data} 
           />
        </div>
      </div>

      {/* AI Synthesis Summary - Enterprise Style */}
      <div className="px-6 py-6 mb-4 flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-white/40 bg-white/20">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 mb-4 rounded-full bg-blue-50/80 border border-blue-100/50">
            <Bot className="w-4 h-4 text-blue-600" />
            <span className="text-[10px] font-black text-blue-700 uppercase tracking-widest">AI Intelligence Synthesis</span>
          </div>
          <h3 className="text-2xl md:text-3xl font-black tracking-tight text-slate-900 mb-3">Clinical Synthesis</h3>
          <p className="text-base text-[var(--text-secondary)] max-w-3xl leading-relaxed">
            Based on the clinical representation, the AI identifies <strong className="text-[var(--text-primary)] font-semibold">{data.top_candidates[0].disease}</strong> as the primary differential. 
            {data.top_candidates.length > 1 ? ` Several other etiologies, including ${data.top_candidates[1].disease}, must also be ruled out.` : ` Clinical correlation is required.`}
          </p>
        </div>
      </div>

      <div className="space-y-4 px-6 pb-8">
        <AnimatePresence>
        {data.top_candidates.map((candidate, idx) => {
          const scorePercent = Math.round(candidate.score * 100);
          const circumference = 2 * Math.PI * 20;
          const strokeDashoffset = circumference - (scorePercent / 100) * circumference;

          return (
          <motion.div 
            key={idx}
            draggable={true}
            onDragStart={(e) => {
              e.dataTransfer.setData("text/plain", `Assessment: ${candidate.disease} (AI Confidence: ${scorePercent}%)`);
            }}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.08, duration: 0.4, ease: "easeOut" }}
            className="group bg-white/60 backdrop-blur-2xl rounded-2xl border border-white/80 hover:border-blue-300 shadow-[0_2px_10px_rgb(0,0,0,0.02)] hover:shadow-[0_8px_30px_rgb(59,130,246,0.1)] transition-all duration-300 overflow-hidden relative cursor-grab active:cursor-grabbing"
          >
            {/* Clickable Header Area */}
            <div 
              className="p-5 md:p-6 flex items-center justify-between cursor-pointer relative z-10"
              onClick={() => setExpandedIndex(expandedIndex === idx ? null : idx)}
            >
              <div className="flex items-center gap-5 w-full">
                <div className="text-slate-300 hover:text-slate-500 cursor-grab px-1 -ml-2" title="Drag to Clinical Note">
                  <span className="text-xl leading-none">⠿</span>
                </div>
                
                {/* SVG Circular Progress */}
                <div className="relative w-14 h-14 flex-shrink-0 flex items-center justify-center">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 48 48">
                    <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="4" fill="transparent" className="text-[var(--surface-sunken)]" />
                    <motion.circle 
                      initial={{ strokeDashoffset: circumference }}
                      animate={{ strokeDashoffset }}
                      transition={{ duration: 1.5, ease: "easeOut", delay: 0.2 }}
                      cx="24" cy="24" r="20" 
                      stroke="currentColor" 
                      strokeWidth="4" 
                      fill="transparent" 
                      strokeLinecap="round"
                      strokeDasharray={circumference}
                      className={idx === 0 ? "text-[var(--color-primary-500)]" : "text-slate-300"} 
                    />
                  </svg>
                  <span className={`absolute text-sm font-bold ${idx === 0 ? 'text-[var(--color-primary-700)]' : 'text-[var(--text-secondary)]'}`}>
                    {scorePercent}
                  </span>
                </div>
                
                <div className="flex-grow">
                  <div className="flex items-center gap-3 mb-1">
                    <h4 className={`text-xl font-bold tracking-tight transition-colors ${idx === 0 ? 'text-[var(--color-primary-700)]' : 'text-[var(--text-primary)]'}`}>
                      {candidate.disease}
                    </h4>
                    {idx === 0 && (
                      <span className="px-2 py-0.5 text-[9px] font-black uppercase tracking-widest bg-[var(--color-primary-100)] text-[var(--color-primary-700)] rounded-full">
                        Primary
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-3 text-xs font-medium">
                    <span className="text-[var(--text-tertiary)] uppercase tracking-wider">
                      {candidate.uncertainty} Uncertainty
                    </span>
                    
                    {candidate.safety_decision && candidate.safety_decision.decision !== "ALLOW" && (
                      <>
                        <span className="w-1 h-1 rounded-full bg-[var(--border-default)]" />
                        <span className={`flex items-center gap-1 ${
                          candidate.safety_decision.decision === 'ABSTAIN' ? 'text-[var(--color-danger-600)]' : 'text-[var(--color-warning-600)]'
                        }`}>
                          <ShieldAlert className="w-3.5 h-3.5"/> {candidate.safety_decision.decision === 'ABSTAIN' ? 'UNSAFE' : 'WARNING'}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="text-[var(--text-tertiary)] flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full group-hover:bg-[var(--surface-sunken)] transition-colors">
                {expandedIndex === idx ? <ChevronUp className="w-5 h-5"/> : <ChevronDown className="w-5 h-5"/>}
              </div>
            </div>

            {/* Expandable Content Area */}
            <AnimatePresence>
            {expandedIndex === idx && (
              <motion.div 
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden border-t border-[var(--border-subtle)] bg-[var(--surface-sunken)]"
              >
                <div className="p-6 md:p-8">
                  
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Left Column: Rationale */}
                    <div className="lg:col-span-2 space-y-6">
                      <div>
                        <h5 className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-widest mb-3">
                           Clinical Rationale
                        </h5>
                        <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{candidate.explanation_reference}</p>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Supporting Findings */}
                        <div>
                          <h5 className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-widest mb-3">
                             Supporting Findings
                          </h5>
                          {candidate.supporting_findings.length > 0 ? (
                            <ul className="space-y-2">
                              {candidate.supporting_findings.map((f, i) => (
                                <li key={i} className="flex items-start gap-2 text-[var(--text-primary)] text-sm font-medium">
                                  <span className="text-[var(--color-primary-500)] mt-0.5 opacity-80">•</span> {f}
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <span className="text-[var(--text-tertiary)] text-sm italic">None documented</span>
                          )}
                        </div>

                        {/* Missing/Contradicting */}
                        <div>
                          <h5 className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-widest mb-3">
                             Contradicting / Missing
                          </h5>
                          {(candidate.missing_expected_findings.length > 0 || candidate.contradicting_information.length > 0) ? (
                            <ul className="space-y-2">
                              {candidate.missing_expected_findings.map((f, i) => (
                                <li key={`m-${i}`} className="flex items-start gap-2 text-[var(--text-secondary)] text-sm">
                                  <span className="text-[var(--text-tertiary)] mt-0.5 opacity-50">-</span> {f} <span className="text-[10px] text-[var(--text-tertiary)] uppercase tracking-widest ml-1 mt-0.5 opacity-60">Expected</span>
                                </li>
                              ))}
                              {candidate.contradicting_information.map((f, i) => (
                                <li key={`c-${i}`} className="flex items-start gap-2 text-[var(--text-primary)] text-sm">
                                  <span className="text-[var(--color-danger-500)] mt-0.5 font-bold">!</span> {f} <span className="text-[10px] text-[var(--color-danger-500)] uppercase tracking-widest ml-1 mt-0.5">Contradicts</span>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <span className="text-[var(--text-tertiary)] text-sm italic">None identified</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Right Column: Actions */}
                    <div className="flex flex-col gap-3">
                       <h5 className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-widest mb-1">
                         Action Plan
                       </h5>
                       <Button 
                         variant={showInvestigationsFor === candidate.disease ? "primary" : "outline"}
                         onClick={(e) => {
                             e.stopPropagation();
                             setShowInvestigationsFor(showInvestigationsFor === candidate.disease ? null : candidate.disease);
                             setShowMedicationsFor(null);
                         }}
                         className="w-full justify-start rounded-xl font-medium shadow-sm h-11"
                       >
                         {showInvestigationsFor === candidate.disease ? 'Hide' : 'View'} Investigations
                       </Button>
                       <Button 
                         variant={showMedicationsFor === candidate.disease ? "primary" : "outline"}
                         onClick={(e) => {
                             e.stopPropagation();
                             setShowMedicationsFor(showMedicationsFor === candidate.disease ? null : candidate.disease);
                             setShowInvestigationsFor(null);
                         }}
                         className="w-full justify-start rounded-xl font-medium shadow-sm h-11"
                       >
                         {showMedicationsFor === candidate.disease ? 'Hide' : 'View'} Safe Medications
                       </Button>
                       <Button 
                         variant={showInvestigationsFor === `${candidate.disease}_intel` ? "primary" : "outline"}
                         onClick={(e) => {
                             e.stopPropagation();
                             setShowInvestigationsFor(showInvestigationsFor === `${candidate.disease}_intel` ? null : `${candidate.disease}_intel`);
                             setShowMedicationsFor(null);
                         }}
                         className="w-full justify-start rounded-xl font-medium shadow-sm h-11 border-[var(--color-primary-300)] text-[var(--color-primary-700)] bg-[var(--color-primary-50)] hover:bg-[var(--color-primary-100)]"
                       >
                         {showInvestigationsFor === `${candidate.disease}_intel` ? 'Hide' : 'View'} Disease Intelligence
                       </Button>
                    </div>
                  </div>
                  
                  {/* Collapsible Sub-panels */}
                  <AnimatePresence>
                  {showInvestigationsFor === candidate.disease && (
                    <motion.div initial={{opacity:0, height:0}} animate={{opacity:1, height:'auto'}} exit={{opacity:0, height:0}} className="pt-8 overflow-hidden">
                      <InvestigationPanel 
                        consultationId={consultationId} 
                        disease={candidate.disease} 
                        competing={data.top_candidates.filter(c => c.disease !== candidate.disease).map(c => c.disease)}
                      />
                    </motion.div>
                  )}
                  {showMedicationsFor === candidate.disease && (
                    <motion.div initial={{opacity:0, height:0}} animate={{opacity:1, height:'auto'}} exit={{opacity:0, height:0}} className="pt-8 overflow-hidden">
                      <MedicationPanel consultationId={consultationId} disease={candidate.disease} />
                    </motion.div>
                  )}
                  {showInvestigationsFor === `${candidate.disease}_intel` && (
                    <motion.div initial={{opacity:0, height:0}} animate={{opacity:1, height:'auto'}} exit={{opacity:0, height:0}} className="pt-8 overflow-hidden">
                      <DiseaseIntelligencePanel consultationId={consultationId} disease={candidate.disease} />
                      <ControversyScanner consultationId={consultationId} disease={candidate.disease} />
                    </motion.div>
                  )}
                  </AnimatePresence>
                </div>
              </motion.div>
            )}
            </AnimatePresence>
          </motion.div>
          );
        })}
        </AnimatePresence>
      </div>
      
      <div className="bg-[var(--surface-sunken)] p-2 border-t border-[var(--border-default)] text-right rounded-b-2xl">
        <span className="text-[10px] text-[var(--text-tertiary)] font-mono">Provider: {data.provider_metadata.provider} v{data.provider_metadata.version}</span>
      </div>
    </motion.div>
    </>
  );
}
