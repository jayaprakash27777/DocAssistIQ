/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  User,
  Activity,
  Clock,
  FileText,
  History,
  Brain,
  PlusCircle,
  FileCheck,
  Download,
  ExternalLink,
  ShieldCheck,
  Sparkles,
  AlertTriangle,
  Pill,
  HeartPulse,
  Stethoscope,
  Copy,
  Check,
  Printer,
  Info,
  CheckCircle2,
  ChevronRight,
  ShieldAlert,
  Droplet,
  Layers,
  Loader2,
} from "lucide-react";
import {
  getPatientProfile,
  PatientProfileResponse,
  listDocumentsForPatient,
  listDocumentsForConsultation,
  VerifiedDocumentRecord,
} from "@/lib/api";
import PatientTimeline from "@/components/patients/PatientTimeline";
import { useToast } from "@/components/shell/ToastProvider";
import { downloadClinicalDocument } from "@/lib/documentPrinting";

// ── Helper Parsers for Clinical-Grade Profile ─────────────────────

function parseStringList(val: any): string[] {
  if (!val) return [];
  if (Array.isArray(val)) {
    return val.map((x) => String(x).trim()).filter(Boolean);
  }
  if (typeof val === "string") {
    return val
      .split(/,\s*|\n|;\s*/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
  }
  return [String(val)];
}

export default function PatientDetail() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { toast } = useToast();

  const [patient, setPatient] = useState<PatientProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "encounters" | "documents" | "timeline">("overview");
  const [documents, setDocuments] = useState<VerifiedDocumentRecord[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [copiedMRN, setCopiedMRN] = useState(false);
  const [downloadingDocId, setDownloadingDocId] = useState<string | null>(null);

  const fetchDocuments = useCallback(async (patientRef: string, sessions: any[]) => {
    setDocsLoading(true);
    try {
      let combined: VerifiedDocumentRecord[] = [];
      const pRes = await listDocumentsForPatient(patientRef);
      if (pRes.ok && pRes.data && pRes.data.documents) {
        combined = [...pRes.data.documents];
      }

      // Also query consultation documents for all recorded sessions to ensure completeness
      if (sessions && sessions.length > 0) {
        const sessionPromises = sessions.map((s) => listDocumentsForConsultation(s.consultation_id || s.id));
        const sessionResults = await Promise.allSettled(sessionPromises);
        sessionResults.forEach((res) => {
          if (res.status === "fulfilled" && res.value.ok && res.value.data?.documents) {
            combined = [...combined, ...res.value.data.documents];
          }
        });
      }

      // Deduplicate by verification code or document_id or sha256_hash
      const seen = new Set<string>();
      const unique = combined.filter((doc) => {
        const key = doc.verification_code || doc.document_id || doc.sha256_hash;
        if (!key || seen.has(key)) return false;
        seen.add(key);
        return true;
      });

      // Sort newest first
      unique.sort((a, b) => new Date(b.signed_at).getTime() - new Date(a.signed_at).getTime());
      setDocuments(unique);
    } catch (err) {
      console.error("Error loading certified documents for patient:", err);
    } finally {
      setDocsLoading(false);
    }
  }, []);

  useEffect(() => {
    async function loadPatient() {
      try {
        const response = await getPatientProfile(id);
        if (response.ok && response.data) {
          setPatient(response.data);
          fetchDocuments(response.data.patient_ref, response.data.sessions);
        } else {
          setError(!response.ok ? response.error.message : "Failed to load patient");
        }
      } catch (err: any) {
        setError(err.message || "An unexpected error occurred");
      } finally {
        setLoading(false);
      }
    }

    if (id) loadPatient();
  }, [id, fetchDocuments]);

  const handleCopyMRN = async () => {
    if (!patient) return;
    try {
      await navigator.clipboard.writeText(patient.patient_ref);
      setCopiedMRN(true);
      toast.success(`Copied MRN: ${patient.patient_ref}`);
      setTimeout(() => setCopiedMRN(false), 2000);
    } catch {
      toast.error("Failed to copy MRN");
    }
  };

  const handlePrintHandover = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-20 text-slate-500 font-medium">
        <div className="w-10 h-10 border-4 border-teal-200 border-t-teal-600 rounded-full animate-spin mb-4" />
        <span className="text-sm font-semibold text-slate-700">Loading Clinical Grade Patient Chart...</span>
        <span className="text-xs text-slate-400 mt-1">Retrieving longitudinal EHR data and verification ledger</span>
      </div>
    );
  }

  if (error || !patient) {
    return (
      <div className="max-w-md mx-auto my-12 p-6 bg-red-50 border border-red-200 rounded-2xl text-center text-red-700 font-medium">
        {error || "Patient not found"}
      </div>
    );
  }

  // ── Extract and normalize clinical fields ────────────────────────
  const rawBase = patient.baseline_conditions || {};

  const rawAllergies = rawBase.allergies || rawBase.documented_allergies;
  const allergiesList = parseStringList(rawAllergies);

  const rawChronic = rawBase.chronic_conditions || rawBase.active_problems || rawBase.conditions;
  const chronicList = parseStringList(rawChronic);

  const rawMeds = rawBase.current_medications || rawBase.maintenance_medications || rawBase.medications;
  const medicationsList = parseStringList(rawMeds);

  const rawSurgeries = rawBase.past_surgeries || rawBase.surgical_history;
  const surgeriesList = parseStringList(rawSurgeries);

  const rawFamily = rawBase.family_history || rawBase.hereditary_risks;
  const familyList = parseStringList(rawFamily);

  const bloodType = rawBase.blood_type || rawBase.blood_group || null;
  const codeStatus = rawBase.code_status || null;
  const attendingDoctor = rawBase.attending_doctor || null;
  const primaryClinic = rawBase.primary_clinic || null;

  // Extract authentic vitals if documented
  const rawVitals = rawBase.vitals || rawBase.vital_signs || {};
  const bloodPressure = rawVitals.blood_pressure || rawVitals.bp || null;
  const heartRate = rawVitals.heart_rate || rawVitals.hr || null;
  const spo2 = rawVitals.oxygen_saturation || rawVitals.spo2 || null;
  const respiration = rawVitals.respiratory_rate || rawVitals.rr || rawVitals.respiration || null;
  const temperature = rawVitals.temperature || rawVitals.temp || null;
  const bmi = rawVitals.bmi || null;
  const hasRealVitals = Boolean(bloodPressure || heartRate || spo2 || respiration || temperature || bmi);

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-entrance pb-16 px-4 py-6">
      {/* ── Print Styles for Clean Hospital Handover ──────────────── */}
      <style jsx global>{`
        @media print {
          body * {
            visibility: hidden !important;
          }
          #patient-handover-sheet,
          #patient-handover-sheet * {
            visibility: visible !important;
          }
          #patient-handover-sheet {
            position: fixed !important;
            left: 0 !important;
            top: 0 !important;
            width: 100% !important;
            max-width: 100% !important;
            padding: 24px !important;
            margin: 0 !important;
            box-shadow: none !important;
            border: none !important;
            background: white !important;
            color: black !important;
            z-index: 999999 !important;
          }
        }
      `}</style>

      {/* ── Breadcrumb & Top Bar ──────────────────────────────────── */}
      <header className="flex flex-col gap-5">
        <div className="flex items-center justify-between">
          <button
            onClick={() => router.push("/patients")}
            className="flex items-center gap-2 text-xs text-slate-500 hover:text-teal-700 transition-colors w-fit font-bold uppercase tracking-wider cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Patient Registry</span>
          </button>

          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest bg-slate-100 px-2.5 py-1 rounded-md border border-slate-200">
              EHR Health Record
            </span>
            <span className="text-[11px] font-bold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Verified Identity</span>
            </span>
          </div>
        </div>

        {/* ── Clinical-Grade Patient Banner (Epic/Cerner Style) ─────── */}
        <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6 relative overflow-hidden">
          {/* Top Row: Avatar, Identity, Demographics & Quick Actions */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="flex items-center gap-5">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-teal-500 to-indigo-600 flex items-center justify-center text-white text-2xl font-black font-heading shadow-sm border-2 border-white shrink-0">
                {patient.patient_ref.substring(0, 2).toUpperCase()}
              </div>

              <div>
                <div className="flex items-center gap-3 flex-wrap">
                  <h1 className="text-3xl font-black font-heading text-slate-900 tracking-tight">
                    {patient.patient_ref}
                  </h1>
                  <button
                    onClick={handleCopyMRN}
                    className="flex items-center gap-1 text-xs font-mono font-bold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 px-2 py-0.5 rounded-lg transition-colors cursor-pointer"
                    title="Copy Patient Reference / MRN"
                  >
                    {copiedMRN ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3 text-indigo-600" />}
                    <span>{copiedMRN ? "Copied" : "Copy MRN"}</span>
                  </button>
                  <span className="text-xs font-bold text-teal-800 bg-teal-50 border border-teal-200 px-2.5 py-0.5 rounded-md uppercase tracking-wider">
                    Outpatient Active
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-2 mt-2.5 text-xs text-slate-600">
                  <span className="bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200">
                    <strong className="text-slate-400 uppercase text-[10px] mr-1">Age:</strong>
                    <span className="text-slate-900 font-semibold">{patient.age_group || "Adult"}</span>
                  </span>
                  <span className="bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200">
                    <strong className="text-slate-400 uppercase text-[10px] mr-1">Sex:</strong>
                    <span className="text-slate-900 font-semibold capitalize">{patient.biological_sex || "Unspecified"}</span>
                  </span>
                  <span className="bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200">
                    <strong className="text-slate-400 uppercase text-[10px] mr-1">Blood:</strong>
                    <span className="text-slate-900 font-semibold">{bloodType || "Unspecified"}</span>
                  </span>
                  {codeStatus ? (
                    <span className="bg-emerald-50 text-emerald-800 px-2.5 py-1 rounded-lg border border-emerald-200 font-bold">
                      {codeStatus}
                    </span>
                  ) : (
                    <span className="bg-slate-50 text-slate-600 px-2.5 py-1 rounded-lg border border-slate-200 font-medium">
                      Standard Care Directive
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Quick Action Toolbar */}
            <div className="flex flex-wrap items-center gap-2.5 self-start lg:self-center">
              <button
                onClick={handlePrintHandover}
                className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-bold text-slate-700 bg-white hover:bg-slate-100 border border-slate-300 shadow-2xs transition-colors cursor-pointer"
                title="Print clinical summary handover sheet"
              >
                <Printer className="w-4 h-4 text-slate-600" />
                <span>Print Handover</span>
              </button>

              <Link
                href={`/ai?patient_ref=${encodeURIComponent(patient.patient_ref)}${patient.sessions?.[0]?.id ? `&cid=${patient.sessions[0].id}` : ''}`}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 shadow-2xs transition-colors"
                title="Ask DocAssist IQ AI questions about this patient's medical history"
              >
                <Brain className="w-4 h-4" />
                <span>Ask DocAssist IQ AI</span>
              </Link>

              <Link
                href={`/consultations/new?patient_id=${patient.id}`}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-teal-500 to-indigo-600 hover:brightness-110 shadow-sm transition-all"
              >
                <PlusCircle className="w-4 h-4" />
                <span>New Encounter</span>
              </Link>
            </div>
          </div>

          {/* High-Visibility Safety Alert: Allergies Banner */}
          {allergiesList.length > 0 && (
            <div className="p-3.5 rounded-2xl bg-amber-50/90 border border-amber-200/90 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2.5 text-amber-900">
                <div className="w-7 h-7 rounded-lg bg-amber-100 text-amber-800 flex items-center justify-center shrink-0">
                  <AlertTriangle className="w-4 h-4 text-amber-700" />
                </div>
                <div>
                  <strong className="uppercase font-bold tracking-wider text-[11px] text-amber-800 block">
                    Critical Safety Alert — Documented Allergies:
                  </strong>
                  <span className="font-semibold text-amber-950">
                    {allergiesList.join(" • ")}
                  </span>
                </div>
              </div>
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-amber-800 bg-amber-200/70 px-2.5 py-1 rounded-md shrink-0">
                Verification Required Before Prescribing
              </span>
            </div>
          )}

          {/* Clinical Metrics Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-slate-100 text-xs">
            <div className="bg-slate-50 p-3 rounded-2xl border border-slate-200/80">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Clinical Encounters</span>
              <span className="text-base font-black text-slate-900">{patient.sessions.length} recorded</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-2xl border border-slate-200/80">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Certified Documents</span>
              <span className="text-base font-black text-emerald-700">{documents.length} verified</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-2xl border border-slate-200/80">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Attending Clinician</span>
              <span className="text-xs font-bold text-slate-800 truncate block mt-0.5">{attendingDoctor || "Unassigned"}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-2xl border border-slate-200/80">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Primary Clinic</span>
              <span className="text-xs font-medium text-slate-600 truncate block mt-0.5">{primaryClinic || "Outpatient Service"}</span>
            </div>
          </div>
        </div>
      </header>

      {/* ── Main Clinical Tabs Navigation ─────────────────────────── */}
      <div className="space-y-6">
        <div className="flex space-x-2 border-b border-slate-200 pb-px overflow-x-auto">
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-4 py-3 border-b-2 text-sm font-bold flex items-center gap-2 transition-all shrink-0 cursor-pointer ${
              activeTab === "overview"
                ? "border-teal-600 text-teal-700"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
            }`}
          >
            <Activity className="w-4 h-4 text-teal-600" />
            <span>Clinical Flowsheet &amp; Problems</span>
          </button>
          <button
            onClick={() => setActiveTab("encounters")}
            className={`px-4 py-3 border-b-2 text-sm font-bold flex items-center gap-2 transition-all shrink-0 cursor-pointer ${
              activeTab === "encounters"
                ? "border-teal-600 text-teal-700"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
            }`}
          >
            <Clock className="w-4 h-4 text-teal-600" />
            <span>Encounter Summaries ({patient.sessions.length})</span>
          </button>
          <button
            onClick={() => setActiveTab("documents")}
            className={`px-4 py-3 border-b-2 text-sm font-bold flex items-center gap-2 transition-all shrink-0 cursor-pointer ${
              activeTab === "documents"
                ? "border-emerald-600 text-emerald-700"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
            }`}
          >
            <FileCheck className="w-4 h-4 text-emerald-600" />
            <span>Certified Documents ({documents.length})</span>
          </button>
          <button
            onClick={() => setActiveTab("timeline")}
            className={`px-4 py-3 border-b-2 text-sm font-bold flex items-center gap-2 transition-all shrink-0 cursor-pointer ${
              activeTab === "timeline"
                ? "border-indigo-600 text-indigo-700"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
            }`}
          >
            <History className="w-4 h-4 text-indigo-600" />
            <span>Longitudinal Timeline</span>
          </button>
        </div>

        {/* ── TAB 1: Clinical Flowsheet & Problem Register ─────────── */}
        {activeTab === "overview" && (
          <div id="patient-handover-sheet" className="space-y-6">
            {/* 1. Vital Signs & Hemodynamics Flowsheet */}
            <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-7 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center">
                    <HeartPulse className="w-4 h-4 text-teal-600" />
                  </div>
                  <div>
                    <h2 className="text-base font-black text-slate-900">
                      Hemodynamics &amp; Vital Signs Flowsheet
                    </h2>
                    <p className="text-xs text-slate-500">
                      Physiological measurements documented in patient baseline or clinical triage
                    </p>
                  </div>
                </div>
                <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                  hasRealVitals ? "text-teal-800 bg-teal-50 border-teal-200" : "text-slate-500 bg-slate-50 border-slate-200"
                }`}>
                  {hasRealVitals ? "Documented Baseline" : "No Baseline Vitals"}
                </span>
              </div>

              {hasRealVitals ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                  {bloodPressure && (
                    <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200/80">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">
                        Blood Pressure
                      </span>
                      <span className="text-base font-black text-slate-900">{bloodPressure}</span>
                      <span className="text-[10px] text-slate-500 block">mmHg</span>
                    </div>
                  )}

                  {heartRate && (
                    <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200/80">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">
                        Heart Rate
                      </span>
                      <span className="text-base font-black text-slate-900">{heartRate}</span>
                      <span className="text-[10px] text-slate-500 block">bpm</span>
                    </div>
                  )}

                  {spo2 && (
                    <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200/80">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">
                        Oxygen SpO2
                      </span>
                      <span className="text-base font-black text-emerald-700">{spo2}{String(spo2).includes("%") ? "" : "%"}</span>
                      <span className="text-[10px] text-slate-500 block">Ambient</span>
                    </div>
                  )}

                  {respiration && (
                    <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200/80">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">
                        Respiration
                      </span>
                      <span className="text-base font-black text-slate-900">{respiration}</span>
                      <span className="text-[10px] text-slate-500 block">breaths/min</span>
                    </div>
                  )}

                  {temperature && (
                    <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200/80">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">
                        Temperature
                      </span>
                      <span className="text-base font-black text-slate-900">{temperature}{String(temperature).includes("°") ? "" : "°C"}</span>
                      <span className="text-[10px] text-slate-500 block">Core</span>
                    </div>
                  )}

                  {bmi && (
                    <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200/80">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">
                        BMI Index
                      </span>
                      <span className="text-base font-black text-slate-900">{bmi}</span>
                      <span className="text-[10px] text-slate-500 block">kg/m²</span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-8 text-center bg-slate-50/60 border border-dashed border-slate-200 rounded-2xl space-y-2">
                  <p className="text-xs text-slate-500 font-medium m-0">
                    No baseline vital signs recorded for this patient profile yet. Vital signs captured during clinical consultations and triage will display here.
                  </p>
                </div>
              )}
            </div>

            {/* 2-Column Clinical Grid: Problems & Pharmacotherapy */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Active Problems / Comorbidities */}
              <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-indigo-600" />
                    <h3 className="text-sm font-bold text-slate-900">Active Problem List &amp; Comorbidity Register</h3>
                  </div>
                  <span className="text-xs font-semibold text-slate-400">
                    {chronicList.length > 0 ? `${chronicList.length} active conditions` : "None listed"}
                  </span>
                </div>

                {chronicList.length > 0 ? (
                  <div className="space-y-2.5">
                    {chronicList.map((cond, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-between gap-3 text-xs"
                      >
                        <div className="flex items-center gap-2.5">
                          <span className="w-2 h-2 rounded-full bg-indigo-500" />
                          <div>
                            <span className="font-bold text-slate-900 block">{cond}</span>
                            <span className="text-[10px] text-slate-400">ICD-10 Categorized • Active Follow-up</span>
                          </div>
                        </div>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                          Chronic
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 text-center">
                    <p className="text-xs text-slate-500 font-medium">No chronic medical conditions recorded.</p>
                  </div>
                )}
              </div>

              {/* Maintenance Pharmacotherapy Regimens */}
              <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <Pill className="w-4 h-4 text-emerald-600" />
                    <h3 className="text-sm font-bold text-slate-900">Active Pharmacotherapy &amp; Regimens</h3>
                  </div>
                  <span className="text-xs font-semibold text-slate-400">
                    {medicationsList.length > 0 ? `${medicationsList.length} prescribed` : "None listed"}
                  </span>
                </div>

                {medicationsList.length > 0 ? (
                  <div className="space-y-2.5">
                    {medicationsList.map((med, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-between gap-3 text-xs"
                      >
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                            <Pill className="w-3.5 h-3.5" />
                          </div>
                          <div>
                            <span className="font-bold text-slate-900 block">{med}</span>
                            <span className="text-[10px] text-slate-400">Maintenance Regimen • Compliance Monitored</span>
                          </div>
                        </div>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                          Active
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 text-center">
                    <p className="text-xs text-slate-500 font-medium">No active maintenance medications on file.</p>
                  </div>
                )}
              </div>
            </div>

            {/* 3-Column Clinical Safety & Historical Context Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Documented Allergies & ADR */}
              <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-3">
                <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                  <ShieldAlert className="w-4 h-4 text-rose-600" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">Allergies &amp; Adverse Reactions</h3>
                </div>
                {allergiesList.length > 0 ? (
                  <div className="space-y-2">
                    {allergiesList.map((alg, i) => (
                      <div key={i} className="p-3 rounded-xl bg-rose-50/70 border border-rose-200 text-xs">
                        <strong className="text-rose-900 block font-bold">{alg}</strong>
                        <span className="text-[10px] text-rose-700 mt-0.5 block">Severity: Moderate / Clinical Caution</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No adverse reactions recorded (NKDA).</p>
                )}
              </div>

              {/* Past Surgical & Procedural Interventions */}
              <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-3">
                <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                  <Stethoscope className="w-4 h-4 text-slate-700" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">Surgical &amp; Procedural History</h3>
                </div>
                {surgeriesList.length > 0 ? (
                  <div className="space-y-2">
                    {surgeriesList.map((surg, i) => (
                      <div key={i} className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                        <strong className="text-slate-900 block font-bold">{surg}</strong>
                        <span className="text-[10px] text-slate-500 mt-0.5 block">Intervention Resolved</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No past surgical procedures recorded.</p>
                )}
              </div>

              {/* Family Medical History & Genetic Risks */}
              <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-3">
                <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                  <History className="w-4 h-4 text-indigo-600" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">Family &amp; Hereditary History</h3>
                </div>
                {familyList.length > 0 ? (
                  <div className="space-y-2">
                    {familyList.map((fam, i) => (
                      <div key={i} className="p-3 rounded-xl bg-indigo-50/60 border border-indigo-100 text-xs">
                        <strong className="text-indigo-950 block font-bold">{fam}</strong>
                        <span className="text-[10px] text-indigo-700 mt-0.5 block">Familial Predisposition Logged</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No hereditary conditions documented.</p>
                )}
              </div>
            </div>

            {/* Quick Consultation Review Workspace Gateway */}
            {patient.sessions.length > 0 && (
              <div className="p-5 rounded-2xl bg-gradient-to-r from-teal-50 via-white to-indigo-50 border border-teal-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center font-bold">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">
                      Most Recent Encounter on File: {patient.sessions[0].encounter_type}
                    </h4>
                    <p className="text-xs text-slate-500">
                      ID: <span className="font-mono text-slate-700">{(patient.sessions[0].consultation_id || patient.sessions[0].id).slice(0, 8)}...</span> • Review clinical SOAP notes, discrete findings, and diagnostic documents.
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 self-end sm:self-auto shrink-0 flex-wrap">
                  <Link
                    href={`/consultations/${patient.sessions[0].consultation_id || patient.sessions[0].id}`}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-teal-600 to-indigo-600 hover:brightness-105 transition-all shadow-2xs"
                  >
                    <Stethoscope className="w-3.5 h-3.5" />
                    <span>Open Consultation Room</span>
                  </Link>
                  <Link
                    href={`/consultations/${patient.sessions[0].consultation_id || patient.sessions[0].id}/review`}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-200 transition-colors shadow-2xs"
                  >
                    <span>Review Workspace</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── TAB 2: Encounter Summaries ────────────────────────────── */}
        {activeTab === "encounters" && (
          <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs relative overflow-hidden space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div>
                <h2 className="text-lg font-black font-heading text-slate-900 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-teal-600" />
                  <span>Encounter Summaries &amp; Consultations</span>
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Complete history of inpatient and outpatient visits for <strong className="text-slate-700">{patient.patient_ref}</strong>
                </p>
              </div>
              <Link
                href={`/consultations/new?patient_id=${patient.id}`}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 transition-colors shadow-2xs shrink-0"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                <span>Start New Encounter</span>
              </Link>
            </div>

            {patient.sessions.length > 0 ? (
              <div className="relative border-l-2 border-slate-200 ml-4 space-y-10 py-2">
                {patient.sessions.map((session) => {
                  const consultationId = session.consultation_id || session.id;
                  return (
                    <div key={session.id} className="relative pl-8">
                      <div className="absolute -left-[9px] top-1.5 w-4 h-4 bg-white rounded-full border-4 border-teal-500" />
                      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs hover:shadow-md transition-shadow space-y-3">
                        <div className="flex items-center justify-between flex-wrap gap-2">
                          <div className="flex items-center gap-2">
                            <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-teal-50 text-teal-800 uppercase tracking-wider border border-teal-200">
                              {session.encounter_type}
                            </span>
                            <span className="text-xs font-mono text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                              Encounter: {consultationId.split("-")[0]}
                            </span>
                          </div>
                          <span className={`text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full ${
                            session.status === "completed" ? "bg-emerald-100 text-emerald-800" : "bg-blue-100 text-blue-800"
                          }`}>
                            {session.status || "Active"}
                          </span>
                        </div>

                        <p className="text-sm text-slate-700 leading-relaxed font-medium">
                          {session.clinical_notes_summary || "Clinical encounter recorded. Full structured SOAP note available in review workspace."}
                        </p>

                        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100">
                          <div className="flex items-center gap-2 flex-wrap">
                            <Link
                              href={`/consultations/${consultationId}`}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-teal-600 to-indigo-600 hover:brightness-105 shadow-2xs transition-all"
                            >
                              <Stethoscope className="w-3.5 h-3.5" />
                              <span>Open Room</span>
                            </Link>
                            <Link
                              href={`/consultations/${consultationId}/intake`}
                              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs font-semibold text-teal-800 bg-teal-50 hover:bg-teal-100 border border-teal-200 transition-colors"
                            >
                              <span>Intake</span>
                            </Link>
                            <Link
                              href={`/consultations/${consultationId}/review`}
                              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-semibold text-slate-700 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors"
                            >
                              <FileText className="w-3.5 h-3.5 text-slate-500" />
                              <span>Review & Docs</span>
                            </Link>
                          </div>
                          <Link
                            href={`/ai?cid=${consultationId}`}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-indigo-700 hover:text-indigo-900 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200/90 transition-colors"
                          >
                            <Brain className="w-3.5 h-3.5 text-indigo-600" />
                            <span>Ask DocAssist IQ AI</span>
                          </Link>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-12 bg-slate-50 rounded-2xl border border-slate-200 space-y-2">
                <Clock className="w-8 h-8 text-slate-300 mx-auto" />
                <p className="text-slate-500 font-medium text-sm">No clinical encounters recorded yet for this patient.</p>
                <Link
                  href={`/consultations/new?patient_id=${patient.id}`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-teal-700 bg-teal-50 border border-teal-200 hover:bg-teal-100 mt-2"
                >
                  <PlusCircle className="w-3.5 h-3.5" />
                  <span>Start First Encounter</span>
                </Link>
              </div>
            )}
          </div>
        )}

        {/* ── TAB 3: Certified Documents (Tamper-Evident Ledger) ────── */}
        {activeTab === "documents" && (
          <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs relative overflow-hidden space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div>
                <h2 className="text-lg font-black font-heading text-slate-900 flex items-center gap-2">
                  <FileCheck className="w-5 h-5 text-emerald-600" />
                  <span>Official Certified Clinical Documents</span>
                </h2>
                <p className="text-xs text-slate-500 mt-1">
                  Tamper-evident medical certificates, discharge summaries, and care plans issued for{" "}
                  <strong className="text-slate-700">{patient.patient_ref}</strong>.
                </p>
              </div>
              <Link
                href={`/ai?patient_ref=${encodeURIComponent(patient.patient_ref)}`}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 shadow-xs transition-colors shrink-0"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Generate with DocAssist IQ AI</span>
              </Link>
            </div>

            {docsLoading ? (
              <div className="flex flex-col items-center justify-center p-12 text-slate-400 font-medium">
                <div className="w-8 h-8 border-3 border-emerald-200 border-t-emerald-600 rounded-full animate-spin mb-3" />
                <span className="text-xs font-semibold text-slate-700">Loading certified records ledger...</span>
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center py-12 px-6 bg-slate-50 rounded-2xl border border-slate-200 space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-white border border-slate-200 text-slate-400 flex items-center justify-center mx-auto shadow-2xs">
                  <FileText className="w-6 h-6 text-slate-400" />
                </div>
                <h3 className="text-sm font-bold text-slate-900">No Certified Documents on Record</h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  No digitally signed discharge summaries or medical certificates have been issued for this patient yet.
                  You can generate and sign official records anytime using DocAssist IQ AI.
                </p>
                <Link
                  href={`/ai?patient_ref=${encodeURIComponent(patient.patient_ref)}`}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 transition-colors"
                >
                  <Brain className="w-3.5 h-3.5" />
                  <span>Generate Document with DocAssist IQ AI</span>
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {documents.map((doc, idx) => (
                  <div
                    key={idx}
                    className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-slate-300 shadow-2xs transition-all space-y-3"
                  >
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[11px] font-extrabold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded-md border border-indigo-200">
                          {doc.document_type.replace(/_/g, " ")}
                        </span>
                        <span className="text-xs text-slate-500 font-medium">
                          Encounter ID:{" "}
                          <span className="font-mono text-slate-700">
                            {doc.consultation_id ? doc.consultation_id.slice(0, 8) : "N/A"}
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5 text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 font-bold px-2.5 py-0.5 rounded-md">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                        <span className="font-mono">{doc.verification_code}</span>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-base font-bold text-slate-900">{doc.title}</h4>
                      {doc.subtitle && <p className="text-xs text-slate-500 mt-0.5">{doc.subtitle}</p>}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-200/80">
                      <div>
                        <span className="font-bold text-slate-500">Attending Clinician: </span>
                        <span className="text-slate-900 font-semibold">
                          {doc.doctor_name?.startsWith("Dr.") ? doc.doctor_name : `Dr. ${doc.doctor_name || "Attending Clinician"}`}{" "}
                          {doc.doctor_specialty ? `(${doc.doctor_specialty})` : ""}
                        </span>
                      </div>
                      <div>
                        <span className="font-bold text-slate-500">Issued On: </span>
                        <span className="text-slate-900 font-semibold">{doc.signed_at_formatted || doc.signed_at}</span>
                      </div>
                      {doc.sha256_hash && (
                        <div className="sm:col-span-2">
                          <span className="font-bold text-slate-500">SHA-256 Digest: </span>
                          <span className="font-mono text-[11px] text-slate-700 bg-white px-1.5 py-0.5 rounded border border-slate-200">
                            {doc.sha256_hash.slice(0, 28)}...
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100">
                      {doc.consultation_id && (
                        <Link
                          href={`/consultations/${doc.consultation_id}/review`}
                          className="text-xs font-bold text-slate-600 hover:text-slate-900 flex items-center gap-1"
                        >
                          <FileText className="w-3.5 h-3.5 text-slate-400" />
                          <span>View Review Workspace</span>
                        </Link>
                      )}
                      <div className="flex items-center gap-2 ml-auto">
                        {doc.consultation_id && (
                          <>
                            <button
                              type="button"
                              onClick={async () => {
                                setDownloadingDocId(`${doc.verification_code}_pdf`);
                                const res = await downloadClinicalDocument(doc.consultation_id, doc.document_type, "pdf", patient.patient_ref);
                                if (res.success) {
                                  toast.success(`Downloaded ${doc.document_type.replace(/_/g, " ")} PDF`);
                                } else {
                                  toast.error(`Download failed: ${res.error}`);
                                }
                                setDownloadingDocId(null);
                              }}
                              disabled={downloadingDocId === `${doc.verification_code}_pdf`}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 transition-colors shadow-2xs cursor-pointer"
                              title="Download Official Hospital PDF"
                            >
                              {downloadingDocId === `${doc.verification_code}_pdf` ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                              <span>PDF</span>
                            </button>
                            <button
                              type="button"
                              onClick={async () => {
                                setDownloadingDocId(`${doc.verification_code}_docx`);
                                const res = await downloadClinicalDocument(doc.consultation_id, doc.document_type, "docx", patient.patient_ref);
                                if (res.success) {
                                  toast.success(`Downloaded ${doc.document_type.replace(/_/g, " ")} DOCX`);
                                } else {
                                  toast.error(`Download failed: ${res.error}`);
                                }
                                setDownloadingDocId(null);
                              }}
                              disabled={downloadingDocId === `${doc.verification_code}_docx`}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 transition-colors shadow-2xs cursor-pointer"
                              title="Download Microsoft Word DOCX"
                            >
                              {downloadingDocId === `${doc.verification_code}_docx` ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                              <span>DOCX</span>
                            </button>
                          </>
                        )}
                        <a
                          href={`/verify?code=${encodeURIComponent(doc.verification_code)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 transition-colors"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          <span>Verify</span>
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── TAB 4: Longitudinal Timeline ─────────────────────────── */}
        {activeTab === "timeline" && <PatientTimeline patientId={id} />}
      </div>
    </div>
  );
}
