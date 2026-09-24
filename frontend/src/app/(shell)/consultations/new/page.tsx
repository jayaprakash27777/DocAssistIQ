/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react/no-unescaped-entities */
/**
 * DocAssistIQ — New Consultation Page.
 *
 * Clinician enters a text description of the clinical scenario.
 * Submits to POST /api/v1/consultations/ → redirects to /consultations/{id}.
 *
 * States: idle → submitting → success (redirect) | error
 * Validation: min 10 / max 10 000 chars (client-side matches backend).
 */

"use client";

import { FormEvent, useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { createConsultation, PLACEHOLDER_LABEL } from "@/lib/api";
import { useToast } from "@/components/shell/ToastProvider";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles } from "lucide-react";

const MIN_CHARS = 10;
const MAX_CHARS = 10_000;

const CLINICAL_SCENARIO_STARTERS = [
  {
    label: "RLQ Pain (Appendicitis)",
    icon: "🩺",
    text: "42-year-old male presents with acute periumbilical abdominal pain migrating to the right lower quadrant over the past 24 hours. Accompanied by nausea, anorexia, and subjective fever. On examination, localized tenderness at McBurney's point with positive Rovsing's sign and mild rebound tenderness. BP: 128/82, HR: 94, Temp: 38.1°C, SpO2: 99%."
  },
  {
    label: "Chest Pain (Suspected ACS)",
    icon: "❤️",
    text: "58-year-old female with history of hypertension and hyperlipidemia presents with sudden onset substernal chest tightness radiating to the left arm and jaw for 2 hours. Associated with diaphoresis, dyspnea, and mild nausea. Denies relief with rest. Vitals: BP: 154/92, HR: 88, RR: 20, SpO2: 96% on room air."
  },
  {
    label: "Fever & Cough (Pneumonia)",
    icon: "🫁",
    text: "65-year-old female presents with a 4-day history of high-grade fever, chills, pleuritic right-sided chest pain, and productive cough with rust-colored sputum. Auscultation reveals bronchial breath sounds and inspiratory crackles in the right lower lobe with dullness to percussion. Vitals: BP: 118/76, HR: 104, RR: 24, SpO2: 92% on room air, Temp: 38.8°C."
  },
  {
    label: "Dyspnea & Leg Swelling (PE)",
    icon: "⚠️",
    text: "34-year-old female presents with sudden onset shortness of breath and pleuritic chest pain following an 8-hour international flight 3 days ago. Also notes unilateral right calf pain and swelling. Vital signs: HR: 112 bpm, BP: 110/70, RR: 26 /min, SpO2: 91% on room air. Right calf is erythematous with 3cm increased circumference."
  },
];

export default function NewConsultationPage() {
  const router = useRouter();
  const { toast } = useToast();

  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const charCount = text.length;
  const charPct = Math.min(100, (charCount / MAX_CHARS) * 100);
  const isValid = charCount >= MIN_CHARS && charCount <= MAX_CHARS;

  const validate = useCallback((): string | null => {
    if (charCount < MIN_CHARS)
      return `Please enter at least ${MIN_CHARS} characters (${charCount} entered).`;
    if (charCount > MAX_CHARS)
      return `Maximum ${MAX_CHARS.toLocaleString()} characters allowed.`;
    return null;
  }, [charCount]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const err = validate();
    if (err) {
      setFieldError(err);
      return;
    }
    setFieldError(null);
    setSubmitError(null);
    setSubmitting(true);

    const result = await createConsultation({ input_text: text });
    setSubmitting(false);

    if (!result.ok) {
      setSubmitError(result.error.message ?? "Failed to submit consultation.");
      toast.error("Submission failed. Please try again.");
      return;
    }

    toast.success("Consultation submitted successfully.");
    router.push(`/consultations/${result.data.id}`);
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6">
      {/* Dev safety notice */}
      <motion.div 
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 p-4 bg-teal-50/80 border border-teal-200/70 rounded-2xl flex items-start gap-3 shadow-sm" 
        role="note"
      >
        <span className="text-teal-600 text-xl leading-none" aria-hidden="true">ℹ</span>
        <div className="flex-1 text-xs text-teal-900 leading-relaxed font-medium">
          <strong className="block mb-1 font-bold text-teal-950">{PLACEHOLDER_LABEL}</strong>
          This environment is for clinical demonstration and simulation. Do not enter actual Protected Health Information (PHI).
        </div>
      </motion.div>

      <motion.header 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="mb-8"
      >
        <h2 className="text-3xl font-black tracking-tight text-slate-900 font-heading mb-2">New Consultation</h2>
        <p className="text-slate-500 text-base font-medium">
          Describe the clinical scenario. Your input will be securely processed to initiate a new patient record.
        </p>
      </motion.header>

      <motion.form
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        id="new-consultation-form"
        className="glass-panel-4k gpu-accelerated rounded-3xl border border-slate-200/90 bg-white/85 backdrop-blur-2xl shadow-[0_12px_36px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.9)] overflow-hidden ring-1 ring-black/5"
        onSubmit={handleSubmit}
        noValidate
      >
        <div className="p-6 sm:p-8">
          <div className="mb-4 flex justify-between items-end">
            <label htmlFor="input-text" className="block text-sm font-semibold text-[var(--text-primary)]">
              Clinical Scenario <span className="text-[var(--color-danger-500)]" aria-hidden="true">*</span>
            </label>
            <span
              id="input-text-hint"
              className={`text-xs font-mono transition-colors ${charCount > MAX_CHARS ? "text-[var(--color-danger-500)]" : "text-[var(--text-tertiary)]"}`}
            >
              {charCount.toLocaleString()} / {MAX_CHARS.toLocaleString()}
            </span>
          </div>

          {/* Quick Clinical Scenario Starters */}
          <div className="mb-4 bg-slate-50/80 border border-slate-200/80 rounded-2xl p-3.5 shadow-2xs">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1.5 font-heading">
                <Sparkles className="w-3.5 h-3.5 text-teal-600" />
                1-Click Clinical Scenario Starters:
              </span>
              <span className="text-[10px] text-slate-400 font-medium">Click to populate intake scenario</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {CLINICAL_SCENARIO_STARTERS.map((s) => (
                <button
                  key={s.label}
                  type="button"
                  onClick={() => {
                    setText(s.text);
                    if (fieldError) setFieldError(null);
                    toast.success(`Loaded ${s.label} scenario`);
                  }}
                  disabled={submitting}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white hover:bg-teal-50 border border-slate-200 hover:border-teal-300 text-xs font-semibold text-slate-700 hover:text-teal-900 shadow-2xs transition-all active:scale-95 disabled:opacity-50"
                >
                  <span>{s.icon}</span>
                  <span>{s.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="relative">
            <textarea
              id="input-text"
              className={`w-full bg-[var(--surface-sunken)] border transition-all duration-200 rounded-xl p-4 text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] focus:border-transparent outline-none resize-y min-h-[250px] ${fieldError ? "border-[var(--color-danger-500)] ring-1 ring-[var(--color-danger-500)]" : "border-[var(--border-default)] hover:border-[var(--border-hover)]"}`}
              value={text}
              onChange={(e) => {
                setText(e.target.value);
                if (fieldError) setFieldError(null);
              }}
              placeholder="Describe the clinical presentation, relevant history, and any specific questions...&#10;&#10;E.g., 45yo male presenting with a 3-day history of sharp right lower quadrant abdominal pain, accompanied by nausea and low-grade fever..."
              rows={12}
              maxLength={MAX_CHARS}
              aria-required="true"
              aria-invalid={!!fieldError}
              aria-describedby={fieldError ? "input-text-error" : "input-text-hint"}
              disabled={submitting}
            />
          </div>

          {/* Progress Bar */}
          <div className="h-1 w-full bg-[var(--surface-sunken)] rounded-full mt-3 overflow-hidden" aria-live="polite">
            <div
              className={`h-full transition-all duration-300 rounded-full ${charPct > 90 ? "bg-[var(--color-warning-500)]" : "bg-[var(--color-primary-500)]"}`}
              style={{ width: `${charPct}%` }}
              role="progressbar"
              aria-valuenow={charCount}
              aria-valuemin={0}
              aria-valuemax={MAX_CHARS}
            />
          </div>

          <AnimatePresence>
            {fieldError && (
              <motion.p 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                id="input-text-error" 
                className="text-[var(--color-danger-600)] text-sm mt-3 flex items-center gap-1.5" 
                role="alert"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                {fieldError}
              </motion.p>
            )}
            
            {submitError && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-4 p-4 bg-[var(--color-danger-50)] text-[var(--color-danger-700)] rounded-lg text-sm border border-[var(--color-danger-200)] flex items-start gap-2" 
                role="alert"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mt-0.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                {submitError}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="bg-slate-50/70 px-6 py-4 sm:px-8 flex flex-col sm:flex-row items-center justify-end gap-3 border-t border-slate-100">
          <Button
            type="button"
            variant="ghost"
            onClick={() => router.push("/consultations")}
            disabled={submitting}
            className="w-full sm:w-auto"
          >
            Cancel
          </Button>
          <Button
            id="submit-consultation-btn"
            type="submit"
            variant="primary"
            disabled={submitting || !isValid}
            isLoading={submitting}
            className="w-full sm:w-auto min-w-[160px]"
          >
            {submitting ? "Submitting…" : "Submit Consultation"}
          </Button>
        </div>
      </motion.form>
    </div>
  );
}
