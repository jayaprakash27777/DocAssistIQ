"use client";

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { 
  AlertTriangle, 
  Activity, 
  CheckCircle, 
  ShieldAlert, 
  Dna,
  X,
  Play
} from "lucide-react";
import { simulatePolypharmacy, PolypharmacyResponse } from "@/lib/api";

export default function PolypharmacySimulator({ 
  consultationId, 
  initialMedications = [],
  onClose
}: { 
  consultationId: string;
  initialMedications?: string[];
  onClose: () => void;
}) {
  const [proposedMeds, setProposedMeds] = useState<string[]>(initialMedications);
  const [newMed, setNewMed] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PolypharmacyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  const handleAddMed = (e: React.FormEvent) => {
    e.preventDefault();
    if (newMed.trim() && !proposedMeds.includes(newMed.trim())) {
      setProposedMeds([...proposedMeds, newMed.trim()]);
      setNewMed("");
    }
  };

  const handleRemoveMed = (med: string) => {
    setProposedMeds(proposedMeds.filter(m => m !== med));
  };

  const handleSimulate = async () => {
    if (proposedMeds.length === 0) {
      setError("Please add at least one medication to simulate.");
      return;
    }
    
    setLoading(true);
    setError(null);
    setResult(null);
    
    const res = await simulatePolypharmacy(consultationId, proposedMeds);
    
    if (res.ok) {
      setResult(res.data);
    } else {
      setError(res.error.message || "Simulation failed");
    }
    setLoading(false);
  };

  if (!mounted) return null;

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 10 }}
        className="bg-white/95 w-full max-w-4xl max-h-[90vh] rounded-3xl shadow-[0_25px_60px_rgba(0,0,0,0.3),inset_0_1px_0_rgba(255,255,255,0.95)] border border-slate-200/90 flex flex-col overflow-hidden glass-panel-4k gpu-accelerated"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200/80 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white shadow-md relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-teal-500/10 via-indigo-500/10 to-purple-500/10 pointer-events-none" />
          <div className="flex items-center gap-3.5 relative z-10">
            <div className="p-2.5 bg-gradient-to-br from-teal-400 to-indigo-500 rounded-2xl shadow-lg shadow-teal-500/30 ring-1 ring-white/30 text-white">
              <Dna className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold tracking-tight text-white m-0">Polypharmacy & Pharmacogenomics Simulator</h2>
              <p className="text-xs text-slate-300 m-0">Simulate complex multi-drug regimens, CYP450 metabolism, and receptor interactions in real-time.</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-xl transition-colors relative z-10"
            title="Close simulator"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col lg:flex-row gap-6 bg-slate-50/60">
          
          {/* Left Column: Input */}
          <div className="lg:w-1/3 flex flex-col gap-5">
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
              <h3 className="font-bold text-slate-900 mb-3 flex items-center gap-2 text-sm tracking-tight">
                <Activity className="w-4 h-4 text-teal-600"/>
                Proposed Regimen
              </h3>
              
              <form onSubmit={handleAddMed} className="flex gap-2 mb-4">
                <input 
                  type="text" 
                  value={newMed}
                  onChange={(e) => setNewMed(e.target.value)}
                  placeholder="e.g. Warfarin, Clopidogrel..."
                  className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:bg-white transition-all shadow-inner"
                />
                <button 
                  type="submit" 
                  className="bg-gradient-to-r from-teal-600 to-indigo-600 hover:brightness-110 text-white px-4 py-2 rounded-xl text-sm font-bold transition-all shadow-md active:scale-95"
                  style={{ boxShadow: "0 4px 12px rgba(13,148,136,0.3), inset 0 1px 0 rgba(255,255,255,0.25)" }}
                >
                  Add
                </button>
              </form>

              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                <AnimatePresence>
                  {proposedMeds.map((med) => (
                    <motion.div 
                      key={med}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      className="flex items-center justify-between bg-slate-50 p-2.5 rounded-xl border border-slate-200 shadow-sm"
                    >
                      <span className="font-semibold text-slate-800 text-sm">{med}</span>
                      <button 
                        onClick={() => handleRemoveMed(med)} 
                        className="text-slate-400 hover:text-rose-600 p-1 transition-colors"
                        title="Remove medication"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </motion.div>
                  ))}
                </AnimatePresence>
                {proposedMeds.length === 0 && (
                  <p className="text-xs text-slate-400 italic text-center py-4">No medications added yet.</p>
                )}
              </div>
            </div>

            <button 
              onClick={handleSimulate}
              disabled={loading || proposedMeds.length === 0}
              className="w-full bg-gradient-to-r from-teal-600 via-indigo-600 to-teal-700 text-white p-3.5 rounded-2xl font-bold flex items-center justify-center gap-2 hover:brightness-110 disabled:opacity-50 transition-all shadow-lg active:scale-98"
              style={{ boxShadow: "0 6px 20px rgba(13,148,136,0.35), inset 0 1px 0 rgba(255,255,255,0.3)" }}
            >
              {loading ? (
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Analyzing Metabolic Pathways...
                </div>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current"/>
                  Run Safety Simulation
                </>
              )}
            </button>

            {error && (
              <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-start gap-2 shadow-sm">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
                <span>{error}</span>
              </div>
            )}
          </div>

          {/* Right Column: Results */}
          <div className="lg:w-2/3">
            {!result && !loading && (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 border-2 border-dashed border-slate-200 rounded-3xl bg-white/60">
                <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mb-4 shadow-sm border border-slate-200">
                  <Dna className="w-8 h-8 text-teal-600" />
                </div>
                <h4 className="text-base font-bold text-slate-800 mb-1.5">Simulation Ready</h4>
                <p className="text-slate-500 text-xs max-w-sm leading-relaxed">
                  Add the proposed medications and run the simulation to check for dangerous drug-drug interactions, CYP450 enzyme competition, and pharmacogenomic contraindications.
                </p>
              </div>
            )}

            {loading && (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 bg-white/60 rounded-3xl border border-slate-200">
                <div className="relative w-16 h-16 mb-4">
                  <div className="absolute inset-0 border-4 border-teal-100 rounded-full"></div>
                  <div className="absolute inset-0 border-4 border-teal-600 rounded-full border-t-transparent animate-spin"></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Activity className="w-6 h-6 text-teal-600 animate-pulse" />
                  </div>
                </div>
                <h4 className="text-base font-bold text-slate-800 animate-pulse">Running Safety Simulation...</h4>
                <p className="text-slate-400 text-xs mt-1">Cross-referencing metabolic pathways and clinical guidelines.</p>
              </div>
            )}

            {result && (
              <motion.div 
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-5"
              >
                {/* Summary Card */}
                <div className={`p-5 rounded-2xl border flex items-start gap-4 shadow-sm ${
                  result.is_safe 
                    ? 'bg-emerald-50/90 border-emerald-300 text-emerald-950' 
                    : 'bg-rose-50/90 border-rose-300 text-rose-950'
                }`}>
                  <div className={`p-2.5 rounded-xl shadow-sm text-white ${
                    result.is_safe ? 'bg-emerald-600' : 'bg-rose-600'
                  }`}>
                    {result.is_safe ? <CheckCircle className="w-5 h-5" /> : <ShieldAlert className="w-5 h-5" />}
                  </div>
                  <div>
                    <h3 className={`text-base font-bold m-0 ${
                      result.is_safe ? 'text-emerald-900' : 'text-rose-900'
                    }`}>
                      {result.is_safe ? 'Regimen Appears Safe' : 'CRITICAL SAFETY WARNING'}
                    </h3>
                    <p className={`text-xs mt-1 leading-relaxed m-0 ${
                      result.is_safe ? 'text-emerald-800' : 'text-rose-800'
                    }`}>
                      {result.summary_assessment}
                    </p>
                  </div>
                </div>

                {/* Interactions */}
                {result.interactions.length > 0 ? (
                  <div className="space-y-3.5">
                    <h4 className="font-bold text-slate-800 flex items-center gap-2 text-xs uppercase tracking-wider">
                      <AlertTriangle className="w-4 h-4 text-amber-500"/>
                      Detected Interactions ({result.interactions.length})
                    </h4>
                    {result.interactions.map((interaction, idx) => (
                      <div 
                        key={idx}
                        className={`p-4 rounded-2xl border shadow-sm ${
                          interaction.severity === 'CRITICAL' ? 'bg-rose-50/40 border-rose-200' :
                          interaction.severity === 'WARNING' ? 'bg-amber-50/40 border-amber-200' :
                          'bg-white border-slate-200'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            {interaction.drugs_involved.map((drug, d_idx) => (
                              <React.Fragment key={drug}>
                                <span className="px-2.5 py-1 bg-white border border-slate-200 rounded-lg text-xs font-bold text-slate-800 shadow-sm">
                                  {drug}
                                </span>
                                {d_idx < interaction.drugs_involved.length - 1 && <span className="text-slate-400 font-bold">+</span>}
                              </React.Fragment>
                            ))}
                          </div>
                          <span className={`text-[10px] uppercase font-black tracking-wider px-2.5 py-0.5 rounded-full shadow-sm text-white ${
                            interaction.severity === 'CRITICAL' ? 'bg-rose-600' :
                            interaction.severity === 'WARNING' ? 'bg-amber-600' :
                            'bg-slate-600'
                          }`}>
                            {interaction.severity}
                          </span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
                          <div className="bg-white p-3 rounded-xl border border-slate-100 shadow-sm">
                            <span className="block text-[9px] uppercase font-bold text-slate-400 tracking-wider mb-1">Mechanism</span>
                            <p className="text-xs font-medium text-slate-700 m-0">{interaction.mechanism}</p>
                          </div>
                          <div className="bg-white p-3 rounded-xl border border-slate-100 shadow-sm">
                            <span className="block text-[9px] uppercase font-bold text-slate-400 tracking-wider mb-1">Clinical Effect</span>
                            <p className="text-xs font-medium text-slate-700 m-0">{interaction.clinical_effect}</p>
                          </div>
                        </div>

                        <div className={`mt-3 p-3 rounded-xl text-xs flex gap-2.5 items-start border ${
                          interaction.severity === 'CRITICAL' 
                            ? 'bg-rose-100/70 text-rose-900 border-rose-200' 
                            : 'bg-indigo-50/70 text-indigo-900 border-indigo-200'
                        }`}>
                          <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5 text-indigo-600" />
                          <div>
                            <span className="block font-bold uppercase tracking-wider text-[9px] opacity-80 mb-0.5">Clinical Recommendation</span>
                            <p className="font-medium leading-relaxed m-0">{interaction.recommendation}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-6 bg-white rounded-2xl border border-slate-200 text-center shadow-sm">
                    <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                    <h4 className="font-bold text-slate-800 text-sm">No Significant Interactions Detected</h4>
                    <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                      The proposed regimen does not show any known CRITICAL or WARNING level interactions with the patient&apos;s current profile.
                    </p>
                  </div>
                )}
              </motion.div>
            )}
          </div>
        </div>
      </motion.div>
    </div>,
    document.body
  );
}
