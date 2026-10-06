/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * DocAssistIQ — New Consultation Page.
 *
 * Clinician enters a text description of the clinical scenario and links
 * or selects a patient from EHR Patient Management.
 * Submits to POST /api/v1/consultations/ → redirects to /consultations/{id}.
 *
 * States: idle → submitting → success (redirect) | error
 * Validation: min 10 / max 10 000 chars (client-side matches backend).
 */

"use client";

import { FormEvent, useCallback, useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  createConsultation,
  getPatientProfiles,
  type PatientProfileResponse,
} from "@/lib/api";
import { useToast } from "@/components/shell/ToastProvider";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Stethoscope,
  HeartPulse,
  Activity,
  AlertTriangle,
  ShieldAlert,
  User,
  UserCheck,
  ChevronRight,
  ExternalLink,
  Layers,
  Pill,
} from "lucide-react";

const MIN_CHARS = 10;
const MAX_CHARS = 10_000;

const CLINICAL_SCENARIO_STARTERS = [
  {
    id: "appendicitis",
    label: "RLQ Pain (Appendicitis)",
    iconType: "scope",
    text: "42-year-old male presents with acute periumbilical abdominal pain migrating to the right lower quadrant over the past 24 hours. Accompanied by nausea, anorexia, and subjective fever. On examination, localized tenderness at McBurney's point with positive Rovsing's sign and mild rebound tenderness. BP: 128/82, HR: 94, Temp: 38.1°C, SpO2: 99%.",
  },
  {
    id: "acs",
    label: "Chest Pain (Suspected ACS)",
    iconType: "heart",
    text: "58-year-old female with history of hypertension and hyperlipidemia presents with sudden onset substernal chest tightness radiating to the left arm and jaw for 2 hours. Associated with diaphoresis, dyspnea, and mild nausea. Denies relief with rest. Vitals: BP: 154/92, HR: 88, RR: 20, SpO2: 96% on room air.",
  },
  {
    id: "pneumonia",
    label: "Fever & Cough (Pneumonia)",
    iconType: "activity",
    text: "65-year-old female presents with a 4-day history of high-grade fever, chills, pleuritic right-sided chest pain, and productive cough with rust-colored sputum. Auscultation reveals bronchial breath sounds and inspiratory crackles in the right lower lobe with dullness to percussion. Vitals: BP: 118/76, HR: 104, RR: 24, SpO2: 92% on room air, Temp: 38.8°C.",
  },
  {
    id: "pe",
    label: "Dyspnea & Leg Swelling (PE)",
    iconType: "alert",
    text: "34-year-old female presents with sudden onset shortness of breath and pleuritic chest pain following an 8-hour international flight 3 days ago. Also notes unilateral right calf pain and swelling. Vital signs: HR: 112 bpm, BP: 110/70, RR: 26 /min, SpO2: 91% on room air. Right calf is erythematous with 3cm increased circumference.",
  },
];

const OUTBREAK_SCENARIO_STARTERS = [
  {
    id: "nipah-kerala",
    label: "Kerala: Nipah Alert",
    state: "Kerala",
    text: "28-year-old male from Kozhikode, Kerala presents with 4-day history of sudden high fever, headache, dizziness, mental confusion, myalgia, and progressive acute respiratory distress. Vitals: Temp: 39.4°C, HR: 116 bpm, BP: 98/60, SpO2: 89% on ambient air. Family notes recent contact with fallen orchard fruit in endemic district.",
  },
  {
    id: "chandipura-gujarat",
    label: "Gujarat: Chandipura Alert",
    state: "Gujarat",
    text: "7-year-old child from Sabarkantha, Gujarat presents with sudden high-grade fever, recurrent vomiting, drowsiness progressing rapidly to altered sensorium, generalized convulsions, and hepatomegaly within 24 hours of onset during monsoon season. Sandfly exposure reported.",
  },
  {
    id: "kfd-karnataka",
    label: "Karnataka: Monkey Fever (KFD)",
    state: "Karnataka",
    text: "36-year-old male farmer from Shimoga, Karnataka presents with sudden severe frontal headache, high persistent fever, conjunctival suffusion, severe backache, prostration, and petechial hemorrhages after clearing forest area where monkey deaths were reported.",
  },
  {
    id: "marburg-global",
    label: "Global: Marburg Notice",
    state: "Rwanda / WHO",
    text: "38-year-old healthcare worker returning from Kigali, Rwanda presents with abrupt high fever, severe headache, malaise, non-bloody diarrhea followed by hematemesis, epistaxis, spontaneous bleeding from IV puncture sites, and maculopapular rash.",
  },
];

function NewConsultationContent() {
  const router = useRouter();
  const searchParams = typeof useSearchParams === "function" ? useSearchParams() : null;
  const { toast } = useToast();

  const urlPatientId = searchParams?.get("patient_id") ?? null;

  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Patient Selection & EHR Linkage State
  const [patients, setPatients] = useState<PatientProfileResponse[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>(urlPatientId || "");
  const [loadingPatients, setLoadingPatients] = useState<boolean>(true);

  // Fetch patient profiles for EHR linkage
  useEffect(() => {
    let isMounted = true;
    async function loadPatients() {
      try {
        const res = await getPatientProfiles();
        if (isMounted && res.ok && Array.isArray(res.data)) {
          setPatients(res.data);
          if (urlPatientId) {
            setSelectedPatientId(urlPatientId);
          }
        }
      } catch (err) {
        console.error("Failed to load patient profiles for consultation linking:", err);
      } finally {
        if (isMounted) setLoadingPatients(false);
      }
    }
    loadPatients();
    return () => {
      isMounted = false;
    };
  }, [urlPatientId]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      // Check if coming from Outbreak Surveillance Radar
      const simQuery = sessionStorage.getItem("outbreak_simulation_query");
      const targetDisease = sessionStorage.getItem("outbreak_target_disease");
      if (simQuery) {
        setTimeout(() => {
          setText(simQuery);
          sessionStorage.removeItem("outbreak_simulation_query");
          sessionStorage.removeItem("outbreak_target_disease");
          toast.success(
            targetDisease
              ? `Loaded ${targetDisease} epidemic surveillance scenario from Outbreak Radar!`
              : "Loaded epidemic outbreak scenario from Surveillance Radar!"
          );
        }, 0);
      }
    } catch {
      // Ignore if sessionStorage unavailable
    }
  }, [toast]);

  const activePatient = patients.find((p) => p.id === selectedPatientId) ?? null;

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

    const payload = {
      input_text: text,
      ...(selectedPatientId ? { patient_id: selectedPatientId } : {}),
    };

    const result = await createConsultation(payload);
    setSubmitting(false);

    if (!result.ok) {
      setSubmitError(result.error.message ?? "Failed to submit consultation.");
      toast.error("Submission failed. Please try again.");
      return;
    }

    if (activePatient) {
      toast.success(`Encounter linked to patient ${activePatient.patient_ref}.`);
    } else {
      toast.success("Consultation submitted and new patient record created.");
    }
    router.push(`/consultations/${result.data.id}`);
  }

  // Extract baseline condition details
  const baseline = (activePatient?.baseline_conditions || {}) as Record<string, any>;
  const allergies = Array.isArray(baseline.allergies) ? baseline.allergies : [];
  const chronic = Array.isArray(baseline.chronic_conditions) ? baseline.chronic_conditions : [];

  return (
    <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6">
      <motion.header
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="mb-6"
      >
        <div className="flex items-center justify-between gap-3 mb-1">
          <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-slate-900 font-heading m-0">
            New Clinical Consultation
          </h2>
        </div>
        <p className="text-slate-500 text-sm font-medium">
          Link a registered EHR patient and enter the clinical presentation to formulate differential diagnostics and certified care plans.
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
        <div className="p-6 sm:p-8 space-y-6">
          {/* ── EHR Patient Linkage Section ── */}
          <div className="bg-gradient-to-br from-teal-50/70 via-indigo-50/40 to-white rounded-2xl border border-teal-200/80 p-4 sm:p-5 shadow-2xs space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-teal-100">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-teal-600 text-white flex items-center justify-center font-bold shadow-2xs">
                  <UserCheck className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-black uppercase tracking-wider text-slate-900 font-heading">
                    Patient EHR Linkage
                  </h3>
                  <p className="text-[11px] text-slate-500 font-medium">
                    Connect this consultation to an existing patient record or create a new profile automatically.
                  </p>
                </div>
              </div>

              {activePatient && (
                <Link
                  href={`/patients/${activePatient.id}`}
                  target="_blank"
                  className="inline-flex items-center gap-1 text-[11px] font-bold text-teal-800 hover:text-teal-950 bg-teal-100/70 hover:bg-teal-200/80 px-2.5 py-1 rounded-lg transition-colors border border-teal-300/80 w-fit"
                  title="Open patient chart in new tab"
                >
                  <span>View Full EHR Chart</span>
                  <ExternalLink className="w-3 h-3" />
                </Link>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 items-center">
              <div>
                <label
                  htmlFor="patient-select"
                  className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1"
                >
                  Select Patient Record
                </label>
                <select
                  id="patient-select"
                  value={selectedPatientId}
                  onChange={(e) => setSelectedPatientId(e.target.value)}
                  disabled={submitting || loadingPatients}
                  className="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500/50 transition-all shadow-2xs cursor-pointer"
                >
                  <option value="">
                    + Automatically Create New Patient Profile (Default)
                  </option>
                  {patients.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.patient_ref} • {p.biological_sex || "Unspecified"} • {p.age_group || "Adult"}
                    </option>
                  ))}
                </select>
              </div>

              {/* Active Linked Patient Badge / Demographics Strip */}
              {activePatient ? (
                <div className="bg-white/90 p-3 rounded-xl border border-teal-200 shadow-2xs text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-emerald-500" />
                      {activePatient.patient_ref}
                    </span>
                    <span className="text-[10px] font-bold uppercase bg-teal-50 text-teal-800 px-2 py-0.5 rounded border border-teal-200">
                      Linked
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 flex flex-wrap gap-2">
                    <span>
                      <strong>Sex:</strong> {activePatient.biological_sex || "N/A"}
                    </span>
                    <span>•</span>
                    <span>
                      <strong>Age Group:</strong> {activePatient.age_group || "N/A"}
                    </span>
                  </div>
                  {allergies.length > 0 && (
                    <div className="text-[10px] font-bold text-amber-800 flex items-center gap-1 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 mt-1">
                      <AlertTriangle className="w-3 h-3 text-amber-600 shrink-0" />
                      <span className="truncate">Allergies: {allergies.join(", ")}</span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-3 rounded-xl bg-white/60 border border-slate-200 text-xs text-slate-500 italic">
                  A fresh Patient Profile will be instantiated upon submitting this clinical scenario.
                </div>
              )}
            </div>
          </div>

          <div>
            <div className="mb-4 flex justify-between items-end">
              <label
                htmlFor="input-text"
                className="block text-sm font-semibold text-[var(--text-primary)]"
              >
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
            <div className="mb-4 bg-slate-50/80 border border-slate-200/80 rounded-2xl p-3.5 shadow-2xs space-y-3">
              <div>
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
                      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white hover:bg-teal-50 border border-slate-200 hover:border-teal-300 text-xs font-semibold text-slate-700 hover:text-teal-900 shadow-2xs transition-all disabled:opacity-50"
                    >
                      {s.iconType === "heart" ? (
                        <HeartPulse className="w-3.5 h-3.5 text-rose-500" />
                      ) : s.iconType === "scope" ? (
                        <Stethoscope className="w-3.5 h-3.5 text-teal-600" />
                      ) : s.iconType === "alert" ? (
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                      ) : (
                        <Activity className="w-3.5 h-3.5 text-blue-500" />
                      )}
                      <span>{s.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Outbreak Surveillance Live Feed Starters */}
              <div className="pt-2.5 border-t border-slate-200/60">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-extrabold uppercase tracking-wider text-rose-700 flex items-center gap-1.5 font-heading">
                    <ShieldAlert className="w-3.5 h-3.5 text-rose-600 animate-pulse" />
                    Live Outbreak Feed Test Scenarios (India State-Wide &amp; Global):
                  </span>
                  <span className="text-[10px] font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
                    Auto-Detects in Differential
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {OUTBREAK_SCENARIO_STARTERS.map((obs) => (
                    <button
                      key={obs.id}
                      type="button"
                      onClick={() => {
                        setText(obs.text);
                        if (fieldError) setFieldError(null);
                        toast.success(`Loaded ${obs.label} scenario! Differential diagnosis will prioritize epidemic outbreak.`);
                      }}
                      disabled={submitting}
                      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-gradient-to-r from-rose-50 to-amber-50 hover:from-rose-100 hover:to-amber-100 border border-rose-300 text-xs font-bold text-rose-900 shadow-2xs transition-all disabled:opacity-50"
                    >
                      <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
                      <span>{obs.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="relative">
              <textarea
                id="input-text"
                className={`w-full bg-[var(--surface-sunken)] border transition-all duration-200 rounded-xl p-4 text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] focus:border-transparent outline-none resize-y min-h-[220px] ${fieldError ? "border-[var(--color-danger-500)] ring-1 ring-[var(--color-danger-500)]" : "border-[var(--border-default)] hover:border-[var(--border-hover)]"}`}
                value={text}
                onChange={(e) => {
                  setText(e.target.value);
                  if (fieldError) setFieldError(null);
                }}
                placeholder="Describe the clinical presentation, relevant history, and any specific questions...&#10;&#10;E.g., 45yo male presenting with a 3-day history of sharp right lower quadrant abdominal pain, accompanied by nausea and low-grade fever..."
                rows={10}
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
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  id="input-text-error"
                  className="text-[var(--color-danger-600)] text-sm mt-3 flex items-center gap-1.5"
                  role="alert"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                  </svg>
                  {fieldError}
                </motion.p>
              )}

              {submitError && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-4 p-4 bg-[var(--color-danger-50)] text-[var(--color-danger-700)] rounded-lg text-sm border border-[var(--color-danger-200)] flex items-start gap-2"
                  role="alert"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mt-0.5">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                  </svg>
                  {submitError}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        <div className="bg-slate-50/70 px-6 py-4 sm:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-100">
          <div className="text-xs text-slate-500 font-medium">
            {activePatient ? (
              <span className="text-teal-700 font-semibold flex items-center gap-1">
                <UserCheck className="w-3.5 h-3.5" />
                Will link encounter to {activePatient.patient_ref}
              </span>
            ) : (
              <span>Will auto-assign new patient record</span>
            )}
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
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
              className="w-full sm:w-auto min-w-[170px]"
            >
              {submitting ? "Submitting…" : "Submit Consultation"}
            </Button>
          </div>
        </div>
      </motion.form>
    </div>
  );
}

export default function NewConsultationPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-4xl mx-auto py-12 px-4 text-center text-slate-400">
          <div className="w-8 h-8 border-3 border-teal-200 border-t-teal-600 rounded-full animate-spin mx-auto mb-2" />
          <span className="text-xs font-semibold">Loading consultation intake workspace...</span>
        </div>
      }
    >
      <NewConsultationContent />
    </Suspense>
  );
}
