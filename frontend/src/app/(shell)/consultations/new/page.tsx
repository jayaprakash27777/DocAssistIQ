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

const MIN_CHARS = 10;
const MAX_CHARS = 10_000;

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
        className="mb-8 p-4 bg-[var(--color-primary-50)] border border-[var(--color-primary-200)] rounded-xl flex items-start gap-3" 
        role="note"
      >
        <span className="text-[var(--color-primary-600)] text-xl leading-none" aria-hidden="true">ℹ</span>
        <div className="flex-1 text-sm text-[var(--color-primary-900)]">
          <strong className="block mb-1 font-semibold">{PLACEHOLDER_LABEL}</strong>
          This environment is for demonstration purposes. Do not enter actual Protected Health Information (PHI).
        </div>
      </motion.div>

      <motion.header 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="mb-8"
      >
        <h2 className="text-3xl font-bold tracking-tight text-[var(--text-primary)] font-heading mb-2">New Consultation</h2>
        <p className="text-[var(--text-secondary)] text-lg">
          Describe the clinical scenario. Your input will be securely processed to initiate a new patient record.
        </p>
      </motion.header>

      <motion.form
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        id="new-consultation-form"
        className="bg-white rounded-2xl shadow-sm border border-[var(--border-default)] overflow-hidden"
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

        <div className="bg-[var(--surface-sunken)] px-6 py-4 sm:px-8 flex flex-col sm:flex-row items-center justify-end gap-3 border-t border-[var(--border-default)]">
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
