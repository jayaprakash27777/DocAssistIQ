/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable react/no-unescaped-entities */
/**
 * DocAssistIQ — Structured Manual Clinical Intake Form (Phase 22).
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import {
  getIntake,
  updateIntake,
  finalizeIntake,
  type ManualIntakeResponse,
  type ManualIntakeUpdate,
  PLACEHOLDER_LABEL,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ChevronLeft, Copy, Check, Sparkles, HeartPulse, Activity, Stethoscope, 
  Pill, AlertTriangle, ShieldCheck, Thermometer, Clock, FileText, CheckCircle2 
} from "lucide-react";

const DEBOUNCE_MS = 1500;

const VITALS_PRESETS = [
  {
    label: "Normal Adult",
    snippet: "BP: 120/80 mmHg | HR: 72 bpm | Temp: 36.8°C | RR: 16/min | SpO2: 99% on room air",
  },
  {
    label: "Febrile / Sepsis Alert",
    snippet: "BP: 94/60 mmHg | HR: 116 bpm | Temp: 39.2°C | RR: 24/min | SpO2: 93% on room air",
  },
  {
    label: "Hypertensive Crisis",
    snippet: "BP: 198/112 mmHg | HR: 96 bpm | Temp: 37.0°C | RR: 18/min | SpO2: 97% on room air",
  },
];

export default function ManualIntakePage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;

  const [intake, setIntake] = useState<ManualIntakeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [copiedId, setCopiedId] = useState(false);
  
  // Form State
  const [formData, setFormData] = useState<ManualIntakeUpdate>({});
  
  // Autosave State
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [unsavedChanges, setUnsavedChanges] = useState(false);

  // Load draft
  const fetchIntake = useCallback(async () => {
    if (!id) return;
    const res = await getIntake(id);
    if (res.ok) {
      setIntake(res.data);
      setFormData({
        chief_complaint: res.data.chief_complaint || "",
        symptoms: res.data.symptoms || "",
        duration: res.data.duration || "",
        severity: res.data.severity || "",
        onset: res.data.onset || "",
        location: res.data.location || "",
        associated_symptoms: res.data.associated_symptoms || "",
        aggravating_factors: res.data.aggravating_factors || "",
        relieving_factors: res.data.relieving_factors || "",
        negations: res.data.negations || "",
        past_medical_history: res.data.past_medical_history || "",
        medications: res.data.medications || "",
        allergies: res.data.allergies || "",
        family_social_history: res.data.family_social_history || "",
        vitals: res.data.vitals || "",
        previous_investigations: res.data.previous_investigations || "",
      });
      setLastSaved(new Date(res.data.updated_at));
    } else {
      toast.error("Failed to load intake draft");
    }
    setLoading(false);
  }, [id, toast]);

  useEffect(() => {
    fetchIntake();
  }, [fetchIntake]);

  // Unsaved changes protection
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (unsavedChanges) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [unsavedChanges]);

  // Autosave logic
  useEffect(() => {
    if (!unsavedChanges || !id || intake?.status === "final") return;

    const timer = setTimeout(async () => {
      setSaving(true);
      const res = await updateIntake(id, formData);
      if (res.ok) {
        setLastSaved(new Date());
        setUnsavedChanges(false);
      }
      setSaving(false);
    }, DEBOUNCE_MS);

    return () => clearTimeout(timer);
  }, [formData, unsavedChanges, id, intake?.status]);

  const handleChange = (field: keyof ManualIntakeUpdate, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setUnsavedChanges(true);
  };

  const handleCopyId = () => {
    if (!id) return;
    navigator.clipboard.writeText(id);
    setCopiedId(true);
    toast.success("Encounter ID copied");
    setTimeout(() => setCopiedId(false), 2000);
  };

  const handleFinalize = async () => {
    if (!id) return;
    if (unsavedChanges) {
      setSaving(true);
      await updateIntake(id, formData);
    }
    
    setSaving(true);
    const res = await finalizeIntake(id);
    setSaving(false);
    if (res.ok) {
      toast.success("Clinical intake finalized successfully");
      router.push(`/consultations/${id}`);
    } else {
      toast.error(res.error.message || "Failed to finalize intake");
    }
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6 space-y-6">
        <Skeleton className="h-10 w-1/3 rounded-xl" />
        <Skeleton className="h-20 w-full rounded-2xl" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton className="h-[400px] w-full rounded-2xl" />
          <Skeleton className="h-[400px] w-full rounded-2xl" />
        </div>
      </div>
    );
  }

  const isFinal = intake?.status === "final";

  return (
    <div className="w-full flex flex-col min-h-0 bg-[var(--surface-base)]">
      <div className="max-w-6xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6 w-full">
        {/* ── Sticky Top Header with Breadcrumbs & Autosave Status ──────────────────── */}
        <motion.header 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border border-slate-200/90 dark:border-slate-800 p-5 rounded-3xl shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4"
        >
          <div>
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <Link 
                href={`/consultations/${id}`} 
                className="text-xs font-bold text-teal-700 dark:text-teal-400 hover:text-teal-800 flex items-center gap-1 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Return to Consultation Room</span>
              </Link>
              <span className="text-slate-300 dark:text-slate-700">•</span>
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider hidden sm:inline">
                {PLACEHOLDER_LABEL}
              </span>
              <span className="text-slate-300 dark:text-slate-700">•</span>
              <button
                type="button"
                onClick={handleCopyId}
                className="text-[11px] font-mono text-slate-500 hover:text-slate-800 dark:text-slate-400 flex items-center gap-1"
                title="Copy encounter ID"
              >
                <span>ENC #{id?.slice(0, 8)}</span>
                {copiedId ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3 opacity-60" />}
              </button>
            </div>
            
            <h1 className="text-2xl sm:text-3xl font-black font-heading text-slate-900 dark:text-white m-0 tracking-tight">
              Structured Manual Clinical Intake
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1 font-medium m-0">
              Structured history of presenting illness, organ review, baseline vitals, and pertinent negations.
            </p>
          </div>
          
          <div className="flex items-center gap-4 shrink-0">
            {/* Live Autosave Indicator */}
            <div className="text-xs text-slate-500 dark:text-slate-400 font-medium flex items-center gap-2">
              {saving ? (
                <span className="flex items-center gap-1.5 text-teal-600 dark:text-teal-400 font-bold">
                  <div className="w-3.5 h-3.5 border-2 border-teal-600 border-t-transparent rounded-full animate-spin" />
                  Saving...
                </span>
              ) : unsavedChanges ? (
                <span className="text-amber-600 dark:text-amber-400 flex items-center gap-1.5 font-bold">
                  <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                  Unsaved changes
                </span>
              ) : lastSaved ? (
                <span className="text-slate-400 flex items-center gap-1.5 font-mono text-[11px]">
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  Saved {lastSaved.toLocaleTimeString()}
                </span>
              ) : (
                <span className="text-slate-400 font-mono text-[11px]">Draft Active</span>
              )}
            </div>
            
            <Button 
              variant="primary" 
              onClick={handleFinalize} 
              disabled={saving || isFinal}
              isLoading={saving}
              className="bg-gradient-to-r from-teal-600 via-indigo-600 to-indigo-700 text-white font-bold px-5 py-2.5 rounded-xl shadow-md shadow-indigo-600/20 text-xs"
            >
              {isFinal ? "Intake Finalized" : "Finalize & Sign Intake"}
            </Button>
          </div>
        </motion.header>

        {/* Finalized Banner Notice */}
        <AnimatePresence>
          {isFinal && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 p-4 rounded-2xl font-bold text-xs flex items-center gap-3 shadow-xs"
            >
              <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0" />
              <span>This clinical intake record has been signed and locked into the patient file. Further edits require clinician amendment.</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Two-Column High-Readability Form Grid ─────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8 items-start">
          
          {/* LEFT COLUMN: History of Presenting Illness */}
          <motion.section 
            initial={{ opacity: 0, x: -15 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white/95 dark:bg-slate-900/95 p-6 sm:p-7 rounded-3xl border border-slate-200/90 dark:border-slate-800 shadow-sm flex flex-col gap-5"
          >
            <div className="border-b border-slate-100 dark:border-slate-800 pb-4 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-teal-600" />
                  <h2 className="text-base font-bold font-heading text-slate-900 dark:text-white m-0">
                    History of Presenting Illness (HPI)
                  </h2>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-medium m-0">
                  Chronological progression of the primary complaint and associated symptoms.
                </p>
              </div>
            </div>
            
            {/* Chief Complaint */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                Chief Complaint <span className="text-rose-500">*</span>
              </label>
              <textarea 
                className="w-full bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200/90 dark:border-slate-700 rounded-xl p-3 text-xs sm:text-sm text-slate-900 dark:text-white focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-teal-500/40 outline-none transition-all resize-y min-h-[75px]" 
                rows={2} 
                value={formData.chief_complaint || ""} 
                onChange={e => handleChange("chief_complaint", e.target.value)} 
                disabled={isFinal} 
                placeholder="e.g. Acute chest tightness radiating to left arm for 3 hours..." 
              />
            </div>
            
            {/* Onset & Duration */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                  Onset
                </label>
                <input 
                  type="text" 
                  className="w-full bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200/90 dark:border-slate-700 rounded-xl p-3 text-xs sm:text-sm text-slate-900 dark:text-white focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-teal-500/40 outline-none transition-all" 
                  value={formData.onset || ""} 
                  onChange={e => handleChange("onset", e.target.value)} 
                  disabled={isFinal} 
                  placeholder="e.g. Sudden / Gradual / 2 hours ago" 
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                  Duration
                </label>
                <input 
                  type="text" 
                  className="w-full bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200/90 dark:border-slate-700 rounded-xl p-3 text-xs sm:text-sm text-slate-900 dark:text-white focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-teal-500/40 outline-none transition-all" 
                  value={formData.duration || ""} 
                  onChange={e => handleChange("duration", e.target.value)} 
                  disabled={isFinal} 
                  placeholder="e.g. 48 hours / 3 weeks" 
                />
              </div>
            </div>

            {/* Quick Duration Buttons */}
            {!isFinal && (
              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mr-1">Presets:</span>
                {["Acute (< 24h)", "Subacute (1-7d)", "Recurrent Episodes", "Chronic (> 3mo)"].map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => handleChange("duration", d)}
                    className="px-2 py-1 rounded-lg text-[10px] font-semibold bg-slate-100 hover:bg-teal-50 dark:bg-slate-800 dark:hover:bg-teal-950/40 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:text-teal-800 transition-colors"
                  >
                    {d}
                  </button>
                ))}
              </div>
            )}

            {/* Symptoms Detailed Description */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                Detailed Symptoms &amp; Character
              </label>
              <textarea 
                className="w-full bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200/90 dark:border-slate-700 rounded-xl p-3 text-xs sm:text-sm text-slate-900 dark:text-white focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-teal-500/40 outline-none transition-all resize-y min-h-[90px]" 
                rows={3} 
                value={formData.symptoms || ""} 
                onChange={e => handleChange("symptoms", e.target.value)} 
                disabled={isFinal} 
                placeholder="Quality of pain (crushing, burning, stabbing), frequency, pattern..." 
              />
            </div>

            {/* Severity & Location */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                  Severity / Score
                </label>
                <input 
                  type="text" 
                  className="w-full bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200/90 dark:border-slate-700 rounded-xl p-3 text-xs sm:text-sm text-slate-900 dark:text-white focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-teal-500/40 outline-none transition-all" 
                  value={formData.severity || ""} 
                  onChange={e => handleChange("severity", e.target.value)} 
                  disabled={isFinal} 
                  placeholder="e.g. Severe (8/10), Mild, Moderate" 
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                  Anatomical Location
                </label>
                <input 
                  type="text" 
                  className="w-full bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200/90 dark:border-slate-700 rounded-xl p-3 text-xs sm:text-sm text-slate-900 dark:text-white focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-teal-500/40 outline-none transition-all" 
                  value={formData.location || ""} 
                  onChange={e => handleChange("location", e.target.value)} 
                  disabled={isFinal} 
                  placeholder="e.g. Substernal radiating to jaw / RLQ" 
                />
              </div>
            </div>
            
            {/* Associated Symptoms */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                Associated Symptoms
              </label>
              <input 
                type="text" 
                className="w-full bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200/90 dark:border-slate-700 rounded-xl p-3 text-xs sm:text-sm text-slate-900 dark:text-white focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-teal-500/40 outline-none transition-all" 
                value={formData.associated_symptoms || ""} 
                onChange={e => handleChange("associated_symptoms", e.target.value)} 
                disabled={isFinal} 
                placeholder="e.g. Diaphoresis, dyspnea, nausea, lightheadedness..." 
              />
            </div>

            {/* Aggravating & Relieving Factors */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                  Aggravating Factors
                </label>
                <input 
                  type="text" 
                  className="w-full bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200/90 dark:border-slate-700 rounded-xl p-3 text-xs sm:text-sm text-slate-900 dark:text-white focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-teal-500/40 outline-none transition-all" 
                  value={formData.aggravating_factors || ""} 
                  onChange={e => handleChange("aggravating_factors", e.target.value)} 
                  disabled={isFinal} 
                  placeholder="e.g. Exertion, inspiration, food..." 
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                  Relieving Factors
                </label>
                <input 
                  type="text" 
                  className="w-full bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200/90 dark:border-slate-700 rounded-xl p-3 text-xs sm:text-sm text-slate-900 dark:text-white focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-teal-500/40 outline-none transition-all" 
                  value={formData.relieving_factors || ""} 
                  onChange={e => handleChange("relieving_factors", e.target.value)} 
                  disabled={isFinal} 
                  placeholder="e.g. Rest, nitroglycerin, sitting up..." 
                />
              </div>
            </div>

            {/* Pertinent Negatives */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                Pertinent Negatives (Negations)
              </label>
              <input 
                type="text" 
                className="w-full bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200/90 dark:border-slate-700 rounded-xl p-3 text-xs sm:text-sm text-slate-900 dark:text-white focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-teal-500/40 outline-none transition-all" 
                value={formData.negations || ""} 
                onChange={e => handleChange("negations", e.target.value)} 
                disabled={isFinal} 
                placeholder="e.g. Denies syncope, denies palpitations, denies hemoptysis..." 
              />
            </div>
          </motion.section>

          {/* RIGHT COLUMN: History, Vitals & Investigations */}
          <motion.section 
            initial={{ opacity: 0, x: 15 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.15 }}
            className="bg-white/95 dark:bg-slate-900/95 p-6 sm:p-7 rounded-3xl border border-slate-200/90 dark:border-slate-800 shadow-sm flex flex-col gap-5"
          >
            <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
              <div className="flex items-center gap-2">
                <HeartPulse className="w-4 h-4 text-rose-500" />
                <h2 className="text-base font-bold font-heading text-slate-900 dark:text-white m-0">
                  Vitals, Past History &amp; Diagnostics
                </h2>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-medium m-0">
                Baseline physiological parameters, medication reconciliation, and diagnostic tests.
              </p>
            </div>

            {/* Vitals with 1-Click Formatter */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Vital Signs (BP, HR, Temp, RR, SpO2)
                </label>
                <span className="text-[10px] text-slate-400 font-medium">Standardized vitals</span>
              </div>
              
              {!isFinal && (
                <div className="flex flex-wrap items-center gap-1.5 mb-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mr-1">1-Click Vitals:</span>
                  {VITALS_PRESETS.map((vp) => (
                    <button
                      key={vp.label}
                      type="button"
                      onClick={() => handleChange("vitals", vp.snippet)}
                      className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-slate-100 hover:bg-rose-50 dark:bg-slate-800 dark:hover:bg-rose-950/40 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:text-rose-700 transition-colors"
                    >
                      {vp.label}
                    </button>
                  ))}
                </div>
              )}

              <textarea 
                className="w-full bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200/90 dark:border-slate-700 rounded-xl p-3 text-xs sm:text-sm text-slate-900 dark:text-white font-mono focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-teal-500/40 outline-none transition-all resize-y min-h-[75px]" 
                rows={2} 
                value={formData.vitals || ""} 
                onChange={e => handleChange("vitals", e.target.value)} 
                disabled={isFinal} 
                placeholder="BP: 128/82, HR: 78, Temp: 37.0°C, RR: 16, SpO2: 99% RA" 
              />
            </div>
            
            {/* Past Medical History */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                Past Medical &amp; Surgical History
              </label>
              <textarea 
                className="w-full bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200/90 dark:border-slate-700 rounded-xl p-3 text-xs sm:text-sm text-slate-900 dark:text-white focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-teal-500/40 outline-none transition-all resize-y min-h-[75px]" 
                rows={2} 
                value={formData.past_medical_history || ""} 
                onChange={e => handleChange("past_medical_history", e.target.value)} 
                disabled={isFinal} 
                placeholder="e.g. Hypertension (10y), T2DM (5y), appendectomy (2018)..." 
              />
            </div>

            {/* Current Medications & Allergies */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
                  <Pill className="w-3.5 h-3.5 text-indigo-500" />
                  <span>Current Medications</span>
                </label>
                <textarea 
                  className="w-full bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200/90 dark:border-slate-700 rounded-xl p-3 text-xs sm:text-sm text-slate-900 dark:text-white focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-teal-500/40 outline-none transition-all resize-y min-h-[75px]" 
                  rows={2} 
                  value={formData.medications || ""} 
                  onChange={e => handleChange("medications", e.target.value)} 
                  disabled={isFinal} 
                  placeholder="e.g. Lisinopril 20mg daily, Metformin 500mg BID..." 
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                  <span>Allergies</span>
                </label>
                <textarea 
                  className="w-full bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200/90 dark:border-slate-700 rounded-xl p-3 text-xs sm:text-sm text-slate-900 dark:text-white focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-teal-500/40 outline-none transition-all resize-y min-h-[75px]" 
                  rows={2} 
                  value={formData.allergies || ""} 
                  onChange={e => handleChange("allergies", e.target.value)} 
                  disabled={isFinal} 
                  placeholder="e.g. Penicillin (anaphylaxis), Sulfa (rash), NKDA..." 
                />
              </div>
            </div>

            {/* Family & Social History */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                Family &amp; Social History
              </label>
              <textarea 
                className="w-full bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200/90 dark:border-slate-700 rounded-xl p-3 text-xs sm:text-sm text-slate-900 dark:text-white focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-teal-500/40 outline-none transition-all resize-y min-h-[75px]" 
                rows={2} 
                value={formData.family_social_history || ""} 
                onChange={e => handleChange("family_social_history", e.target.value)} 
                disabled={isFinal} 
                placeholder="e.g. Father MI at 52; non-smoker, occasional alcohol, no illicit substances..." 
              />
            </div>

            {/* Previous Investigations */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                Previous Investigations &amp; Diagnostics
              </label>
              <textarea 
                className="w-full bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200/90 dark:border-slate-700 rounded-xl p-3 text-xs sm:text-sm text-slate-900 dark:text-white focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-teal-500/40 outline-none transition-all resize-y min-h-[75px]" 
                rows={2} 
                value={formData.previous_investigations || ""} 
                onChange={e => handleChange("previous_investigations", e.target.value)} 
                disabled={isFinal} 
                placeholder="e.g. ECG normal sinus rhythm, CXR clear, HbA1c 7.2%..." 
              />
            </div>
          </motion.section>
          
        </div>
      </div>
    </div>
  );
}
