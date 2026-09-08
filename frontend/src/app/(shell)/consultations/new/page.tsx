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
    <div className="new-consult-page">
      {/* Dev safety notice */}
      <div className="new-consult-safety" role="note">
        <span className="new-consult-safety-icon" aria-hidden="true">ℹ</span>
        <span>{PLACEHOLDER_LABEL}</span>
      </div>

      <header className="new-consult-header">
        <h2 className="new-consult-title">New Consultation</h2>
        <p className="new-consult-subtitle">
          Describe the clinical scenario. Your input will be processed and a
          placeholder development response will be returned.
        </p>
      </header>

      <form
        id="new-consultation-form"
        className="new-consult-form"
        onSubmit={handleSubmit}
        noValidate
      >
        <div className="new-consult-field">
          <label htmlFor="input-text" className="new-consult-label">
            Clinical scenario
            <span className="new-consult-required" aria-hidden="true"> *</span>
          </label>

          <textarea
            id="input-text"
            className={`new-consult-textarea ${fieldError ? "new-consult-textarea--error" : ""}`}
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              if (fieldError) setFieldError(null);
            }}
            placeholder="Describe the clinical presentation, relevant history, and any specific questions…"
            rows={10}
            maxLength={MAX_CHARS}
            aria-required="true"
            aria-invalid={!!fieldError}
            aria-describedby={fieldError ? "input-text-error" : "input-text-hint"}
            disabled={submitting}
          />

          {/* Char counter */}
          <div className="new-consult-counter" aria-live="polite">
            <div
              className="new-consult-counter-bar"
              role="progressbar"
              aria-valuenow={charCount}
              aria-valuemin={0}
              aria-valuemax={MAX_CHARS}
            >
              <div
                className={`new-consult-counter-fill ${charPct > 90 ? "new-consult-counter-fill--warn" : ""}`}
                style={{ width: `${charPct}%` }}
              />
            </div>
            <span
              id="input-text-hint"
              className={`new-consult-counter-label ${charCount > MAX_CHARS ? "new-consult-counter-label--over" : ""}`}
            >
              {charCount.toLocaleString()} / {MAX_CHARS.toLocaleString()}
            </span>
          </div>

          {fieldError && (
            <p id="input-text-error" className="new-consult-error" role="alert">
              {fieldError}
            </p>
          )}
        </div>

        {submitError && (
          <div className="new-consult-submit-error" role="alert">
            {submitError}
          </div>
        )}

        <div className="new-consult-actions">
          <button
            type="button"
            className="new-consult-btn-secondary"
            onClick={() => router.push("/consultations")}
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            id="submit-consultation-btn"
            type="submit"
            className="new-consult-btn-primary"
            disabled={submitting || !isValid}
            aria-busy={submitting}
          >
            {submitting ? (
              <span className="new-consult-spinner" aria-hidden="true" />
            ) : null}
            {submitting ? "Submitting…" : "Submit consultation"}
          </button>
        </div>
      </form>
    </div>
  );
}
