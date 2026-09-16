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
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white [#111111] w-full max-w-4xl max-h-[90vh] rounded-3xl shadow-2xl border border-[var(--glass-border)] flex flex-col overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[var(--border-default)] bg-[var(--surface-sunken)]">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-[var(--color-primary-500)] to-[var(--color-primary-700)] rounded-xl shadow-lg">
              <Dna className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-[var(--text-primary)]">Polypharmacy & Pharmacogenomics Simulator</h2>
              <p className="text-sm text-[var(--text-secondary)]">Simulate complex drug-drug and drug-gene interactions in real-time.</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-raised)] rounded-full transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col lg:flex-row gap-8">
          
          {/* Left Column: Input */}
          <div className="lg:w-1/3 flex flex-col gap-6">
            <div className="bg-[var(--surface-raised)] p-5 rounded-2xl border border-[var(--border-default)]">
              <h3 className="font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                <Activity className="w-4 h-4 text-[var(--color-primary-500)]"/>
                Proposed Regimen
              </h3>
              
              <form onSubmit={handleAddMed} className="flex gap-2 mb-4">
                <input 
                  type="text" 
                  value={newMed}
                  onChange={(e) => setNewMed(e.target.value)}
                  placeholder="e.g. Warfarin"
                  className="flex-1 bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]/50"
                />
                <button type="submit" className="bg-[var(--color-primary-500)] hover:bg-[var(--color-primary-600)] text-white px-4 py-2 rounded-xl text-sm font-bold transition-colors">
                  Add
                </button>
              </form>

              <div className="space-y-2">
                <AnimatePresence>
                  {proposedMeds.map((med, idx) => (
                    <motion.div 
                      key={med}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      className="flex items-center justify-between bg-white [#1a1a1a] p-3 rounded-xl border border-[var(--border-default)] shadow-sm"
                    >
                      <span className="font-medium text-[var(--text-primary)] text-sm">{med}</span>
                      <button onClick={() => handleRemoveMed(med)} className="text-[var(--text-tertiary)] hover:text-[var(--color-danger-500)] transition-colors">
                        <X className="w-4 h-4" />
                      </button>
                    </motion.div>
                  ))}
                </AnimatePresence>
                {proposedMeds.length === 0 && (
                  <p className="text-xs text-[var(--text-tertiary)] italic text-center py-4">No medications added.</p>
                )}
              </div>
            </div>

            <button 
              onClick={handleSimulate}
              disabled={loading || proposedMeds.length === 0}
              className="w-full bg-[var(--text-primary)] text-[var(--bg-default)] p-4 rounded-2xl font-bold flex items-center justify-center gap-2 hover:opacity-90 disabled:opacity-50 transition-opacity shadow-lg"
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-[var(--bg-default)] border-t-transparent rounded-full animate-spin"></div>
                  Analyzing Pathways...
                </div>
              ) : (
                <>
                  <Play className="w-5 h-5" fill="currentColor"/>
                  Run Simulation
                </>
              )}
            </button>

            {error && (
              <div className="p-4 bg-[var(--color-danger-50)] [var(--color-danger-900)]/20 border border-[var(--color-danger-200)] [var(--color-danger-800)] text-[var(--color-danger-700)] [var(--color-danger-400)] text-sm rounded-xl flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                {error}
              </div>
            )}
          </div>

          {/* Right Column: Results */}
          <div className="lg:w-2/3">
            {!result && !loading && (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 border-2 border-dashed border-[var(--border-default)] rounded-3xl bg-[var(--surface-sunken)]/50">
                <div className="w-16 h-16 bg-[var(--surface-raised)] rounded-2xl flex items-center justify-center mb-4 shadow-sm border border-[var(--border-default)]">
                  <Dna className="w-8 h-8 text-[var(--text-tertiary)]" />
                </div>
                <h4 className="text-lg font-bold text-[var(--text-primary)] mb-2">Simulation Pending</h4>
                <p className="text-[var(--text-secondary)] text-sm max-w-sm">
                  Add the proposed medications and run the simulation to check for dangerous interactions, CYP450 enzyme conflicts, and pharmacogenomic risks against the patient's existing profile.
                </p>
              </div>
            )}

            {loading && (
              <div className="h-full flex flex-col items-center justify-center text-center p-8">
                <div className="relative w-20 h-20 mb-6">
                  <div className="absolute inset-0 border-4 border-[var(--color-primary-100)] [var(--color-primary-900)] rounded-full"></div>
                  <div className="absolute inset-0 border-4 border-[var(--color-primary-500)] rounded-full border-t-transparent animate-spin"></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Activity className="w-8 h-8 text-[var(--color-primary-500)] animate-pulse" />
                  </div>
                </div>
                <h4 className="text-lg font-bold text-[var(--text-primary)] animate-pulse">Running Safety Simulation...</h4>
                <p className="text-[var(--text-tertiary)] text-sm mt-2">Checking metabolic pathways and receptor affinities.</p>
              </div>
            )}

            {result && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                {/* Summary Card */}
                <div className={`p-5 rounded-2xl border flex items-start gap-4 shadow-sm ${result.is_safe ? 'bg-[var(--color-success-50)] [var(--color-success-900)]/20 border-[var(--color-success-200)] [var(--color-success-800)]' : 'bg-[var(--color-danger-50)] [var(--color-danger-900)]/20 border-[var(--color-danger-200)] [var(--color-danger-800)]'}`}>
                  <div className={`p-3 rounded-xl shadow-sm ${result.is_safe ? 'bg-white [var(--color-success-800)] text-[var(--color-success-600)] ' : 'bg-white [var(--color-danger-800)] text-[var(--color-danger-600)] '}`}>
                    {result.is_safe ? <CheckCircle className="w-6 h-6" /> : <ShieldAlert className="w-6 h-6" />}
                  </div>
                  <div>
                    <h3 className={`text-lg font-bold ${result.is_safe ? 'text-[var(--color-success-800)] [var(--color-success-300)]' : 'text-[var(--color-danger-800)] [var(--color-danger-300)]'}`}>
                      {result.is_safe ? 'Regimen Appears Safe' : 'CRITICAL WARNING'}
                    </h3>
                    <p className={`text-sm mt-1 leading-relaxed ${result.is_safe ? 'text-[var(--color-success-700)] [var(--color-success-400)]' : 'text-[var(--color-danger-700)] [var(--color-danger-400)]'}`}>
                      {result.summary_assessment}
                    </p>
                  </div>
                </div>

                {/* Interactions */}
                {result.interactions.length > 0 ? (
                  <div className="space-y-4">
                    <h4 className="font-bold text-[var(--text-primary)] flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-[var(--color-warning-500)]"/>
                      Detected Interactions
                    </h4>
                    {result.interactions.map((interaction, idx) => (
                      <div 
                        key={idx}
                        className={`p-5 rounded-2xl border shadow-sm backdrop-blur-sm ${
                          interaction.severity === 'CRITICAL' ? 'bg-white/80  border-[var(--color-danger-200)] [var(--color-danger-800)]' :
                          interaction.severity === 'WARNING' ? 'bg-white/80  border-[var(--color-warning-200)] [var(--color-warning-800)]' :
                          'bg-white/80  border-[var(--border-default)]'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            {interaction.drugs_involved.map((drug, d_idx) => (
                              <React.Fragment key={drug}>
                                <span className="px-2.5 py-1 bg-[var(--surface-raised)] border border-[var(--border-default)] rounded-lg text-xs font-bold text-[var(--text-primary)]">
                                  {drug}
                                </span>
                                {d_idx < interaction.drugs_involved.length - 1 && <span className="text-[var(--text-tertiary)]">+</span>}
                              </React.Fragment>
                            ))}
                          </div>
                          <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-1 rounded shadow-sm ${
                            interaction.severity === 'CRITICAL' ? 'bg-[var(--color-danger-500)] text-white' :
                            interaction.severity === 'WARNING' ? 'bg-[var(--color-warning-500)] text-white' :
                            'bg-[var(--surface-raised)] text-[var(--text-secondary)] border border-[var(--border-default)]'
                          }`}>
                            {interaction.severity}
                          </span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                          <div className="bg-[var(--surface-sunken)] p-3 rounded-xl border border-[var(--border-default)]">
                            <span className="block text-[9px] uppercase font-bold text-[var(--text-tertiary)] tracking-wider mb-1">Mechanism</span>
                            <p className="text-xs font-medium text-[var(--text-secondary)]">{interaction.mechanism}</p>
                          </div>
                          <div className="bg-[var(--surface-sunken)] p-3 rounded-xl border border-[var(--border-default)]">
                            <span className="block text-[9px] uppercase font-bold text-[var(--text-tertiary)] tracking-wider mb-1">Clinical Effect</span>
                            <p className="text-xs font-medium text-[var(--text-secondary)]">{interaction.clinical_effect}</p>
                          </div>
                        </div>

                        <div className={`mt-4 p-3 rounded-xl text-xs flex gap-3 items-start border ${
                          interaction.severity === 'CRITICAL' ? 'bg-[var(--color-danger-50)]/50 [var(--color-danger-900)]/20 text-[var(--color-danger-800)] [var(--color-danger-300)] border-[var(--color-danger-200)] [var(--color-danger-800)]' : 
                          'bg-[var(--color-primary-50)]/50 [var(--color-primary-900)]/20 text-[var(--color-primary-800)] [var(--color-primary-300)] border-[var(--color-primary-200)] [var(--color-primary-800)]'
                        }`}>
                          <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
                          <div>
                            <span className="block font-bold uppercase tracking-wider text-[9px] opacity-80 mb-0.5">Recommendation</span>
                            <p className="font-medium leading-relaxed">{interaction.recommendation}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-6 bg-[var(--surface-raised)] rounded-2xl border border-[var(--border-default)] text-center shadow-inner">
                    <CheckCircle className="w-8 h-8 text-[var(--color-success-500)] mx-auto mb-3" />
                    <h4 className="font-bold text-[var(--text-primary)]">No Significant Interactions Detected</h4>
                    <p className="text-sm text-[var(--text-secondary)] mt-1">
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
