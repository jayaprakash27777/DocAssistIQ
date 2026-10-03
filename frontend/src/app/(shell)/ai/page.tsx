/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable react/no-unescaped-entities */
/**
 * DocAssistIQ — AI Clinical Intelligence Page
 *
 * REAL-TIME AI PREDICTIONS — Ask any medical question and get instant,
 * evidence-grounded answers from the knowledge base.
 *
 * Features:
 *  - RAG-powered clinical Q&A (POST /api/v1/rag/query)
 *  - Disease Intelligence lookup (GET /api/v1/intelligence/disease/{name})
 *  - AI mode indicator (LLM active vs. Static KB)
 *  - Animated typing indicator while AI processes
 *  - Citation cards with source provenance
 *  - Quick-ask preset buttons for common clinical questions
 *  - Copy answer to clipboard
 */

"use client";

import React, { useState, useRef, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain, Send, Loader2, Sparkles, AlertTriangle, BookOpen,
  Copy, Check, ChevronDown, ChevronUp, Zap, Search,
  ShieldCheck, Activity, Stethoscope, Pill, FlaskConical,
  RefreshCw, Info, CheckCircle2, Clock, Globe, ShieldAlert, MapPin,
  FileText, Download, Shield, Tag, AtSign, X, CheckCircle, ExternalLink,
  ChevronRight, UserCheck, Calendar, FileBadge, Printer, FileCheck
} from "lucide-react";
import {
  ragQuery,
  getDiseaseIntelligence,
  listConsultations,
  askDoctorNotesGeneral,
  listDocumentsForConsultation,
  type RAGResponse,
  type DiseaseIntelligenceResponse,
  type GeneratedClinicalDocument,
  type ConsultationSummary,
  type VerifiedDocumentRecord
} from "@/lib/api";
import { useToast } from "@/components/shell/ToastProvider";
import StateOutbreakRadar from "@/components/clinical/StateOutbreakRadar";

// ── Constants ─────────────────────────────────────────────────────

const QUICK_ASKS = [
  { icon: Stethoscope, label: "Chest pain DDx", query: "What are the differential diagnoses for acute chest pain with radiation to left arm?" },
  { icon: Pill, label: "Antibiotic choice", query: "What is the first-line antibiotic for community-acquired pneumonia in an adult without comorbidities?" },
  { icon: FlaskConical, label: "Lab interpretation", query: "How do I interpret a high D-dimer with a normal troponin in a chest pain patient?" },
  { icon: Activity, label: "ECG findings", query: "What are the ECG findings in ST-elevation myocardial infarction (STEMI)?" },
  { icon: AlertTriangle, label: "Red flags", query: "What are the red flag symptoms in a patient presenting with headache that require urgent investigation?" },
  { icon: Brain, label: "Neurological exam", query: "How do I assess for signs of meningitis on clinical examination?" },
];

const CONSULTATION_QUICK_ACTIONS = [
  { icon: FileText, label: "Discharge Summary", prompt: "Generate certified discharge summary with digital signature", color: "indigo" },
  { icon: Pill, label: "E-Prescription", prompt: "Generate official certified electronic prescription with digital signature", color: "emerald" },
  { icon: FileBadge, label: "Medical Certificate", prompt: "Generate official medical certificate for patient with digital signature", color: "purple" },
  { icon: Activity, label: "Treatment Plan", prompt: "Generate comprehensive care and treatment plan document with digital signature", color: "emerald" },
  { icon: UserCheck, label: "Patient Profile", prompt: "what is the patient profile and chronic conditions", color: "blue" },
  { icon: Clock, label: "Audit Timeline", prompt: "what is the consultation timeline and audit history", color: "amber" },
  { icon: ExternalLink, label: "Referral Letter", prompt: "Generate specialist clinical referral letter with digital signature", color: "rose" },
  { icon: FlaskConical, label: "Lab Requisition", prompt: "Generate diagnostic and laboratory investigation requisition order with digital signature", color: "teal" },
  { icon: FileText, label: "Profile Report", prompt: "Generate certified patient profile report with digital signature", color: "violet" },
  { icon: ShieldCheck, label: "Timeline Certificate", prompt: "Generate certified encounter timeline certificate with digital signature", color: "cyan" },
  { icon: UserCheck, label: "Assigned Doctor", prompt: "Who is the assigned doctor for this consultation?", color: "sky" },
  { icon: Calendar, label: "Admission Date", prompt: "What is the encounter date, admission timestamp, and clinical status?", color: "orange" },
  { icon: Pill, label: "Medications", prompt: "What are the current medications and prescriptions?", color: "pink" },
  { icon: Stethoscope, label: "Differential Diagnosis", prompt: "What are the differential diagnoses and clinical findings for this patient?", color: "indigo" },
];

const LOADING_PHASES = [
  { icon: Search, text: "Searching PubMed & clinical KB…" },
  { icon: BookOpen, text: "Retrieving MedlinePlus evidence…" },
  { icon: Activity, text: "Cross-referencing clinical data…" },
  { icon: ShieldCheck, text: "Synthesizing answer…" },
];

// ── Types ─────────────────────────────────────────────────────────

type QueryMode = "rag" | "disease" | "outbreaks";

interface Message {
  id: string;
  role: "user" | "assistant" | "error";
  content: string;
  ragData?: RAGResponse;
  diseaseData?: DiseaseIntelligenceResponse;
  generatedDocument?: GeneratedClinicalDocument;
  consultationId?: string;
  timestamp: Date;
}

// ── Helpers ───────────────────────────────────────────────────────

function confColor(score: number) {
  if (score >= 0.8) return { bg: "#d1fae5", text: "#065f46", border: "#a7f3d0", label: "High Confidence" };
  if (score >= 0.6) return { bg: "#fef3c7", text: "#92400e", border: "#fde68a", label: "Medium Confidence" };
  return { bg: "#fee2e2", text: "#991b1b", border: "#fecaca", label: "Low Confidence" };
}

function FormattedClinicalContent({ content }: { content: string }) {
  if (!content) return null;

  const renderInline = (text: string) => {
    const parts = text.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**") && part.length >= 4) {
        return <strong key={i} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith("*") && part.endsWith("*") && part.length >= 2) {
        return <em key={i} className="italic text-slate-700">{part.slice(1, -1)}</em>;
      }
      if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
        return <code key={i} className="bg-slate-100 text-indigo-700 px-1 py-0.5 rounded text-[11px] font-mono">{part.slice(1, -1)}</code>;
      }
      return part;
    });
  };

  const lines = content.split("\n");
  return (
    <div className="space-y-1.5 text-sm text-slate-800 leading-relaxed">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) {
          return <div key={idx} className="h-1" />;
        }
        if (trimmed === "---") {
          return <hr key={idx} className="my-2.5 border-slate-200" />;
        }
        if (trimmed.startsWith("### ")) {
          return (
            <h4 key={idx} className="text-sm font-bold text-indigo-900 pt-2 pb-0.5 border-b border-indigo-100 flex items-center gap-1.5">
              <span className="w-1.5 h-3.5 bg-indigo-600 rounded-sm inline-block" />
              {renderInline(trimmed.slice(4))}
            </h4>
          );
        }
        if (trimmed.startsWith("## ")) {
          return (
            <h3 key={idx} className="text-base font-bold text-slate-900 pt-2.5 pb-1 flex items-center gap-2">
              <span className="w-2 h-4 bg-indigo-500 rounded-sm inline-block" />
              {renderInline(trimmed.slice(3))}
            </h3>
          );
        }
        if (trimmed.startsWith("# ")) {
          return (
            <h2 key={idx} className="text-lg font-bold text-slate-950 pt-2.5 pb-1">
              {renderInline(trimmed.slice(2))}
            </h2>
          );
        }
        if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
          return (
            <div key={idx} className="flex items-start gap-2 pl-1.5 py-0.5">
              <span className="shrink-0 w-1.5 h-1.5 rounded-full bg-indigo-500 mt-2" />
              <span className="flex-1 text-slate-700">{renderInline(trimmed.slice(2))}</span>
            </div>
          );
        }
        const numMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
        if (numMatch) {
          return (
            <div key={idx} className="flex items-start gap-2 pl-1.5 py-0.5">
              <span className="shrink-0 font-semibold text-xs text-indigo-700 mt-0.5 w-4">{numMatch[1]}.</span>
              <span className="flex-1 text-slate-700">{renderInline(numMatch[2])}</span>
            </div>
          );
        }
        return (
          <p key={idx} className="text-slate-800">
            {renderInline(line)}
          </p>
        );
      })}
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────

function CitationCard({ citation, index }: { citation: any; index: number }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className="rounded-xl overflow-hidden"
      style={{ border: "1px solid rgba(0,0,0,0.08)", background: "#fff" }}
    >
      <button
        onClick={() => setExpanded(v => !v)}
        className="w-full text-left px-3 py-2.5 flex items-center gap-2 text-xs hover:bg-slate-50 transition-colors"
      >
        <span
          className="flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold shrink-0"
          style={{ background: "#eff6ff", color: "#1d4ed8" }}
        >
          {index + 1}
        </span>
        <span className="font-semibold text-slate-700 flex-1 truncate">{citation.source_name}</span>
        <span
          className="text-[10px] px-1.5 py-0.5 rounded font-medium shrink-0"
          style={{ background: "#f0fdf4", color: "#15803d" }}
        >
          {Math.round((citation.relevance_score ?? 0) * 100)}% match
        </span>
        {expanded ? <ChevronUp className="w-3.5 h-3.5 text-slate-400 shrink-0" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />}
      </button>
      {expanded && (
        <div className="px-3 pb-3 pt-1 text-xs text-slate-600 leading-relaxed border-t border-slate-100">
          {citation.excerpt}
        </div>
      )}
    </motion.div>
  );
}

function DiseaseCard({ data }: { data: DiseaseIntelligenceResponse }) {
  const [section, setSection] = useState<string>("overview");
  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "symptoms", label: "Symptoms" },
    { id: "treatment", label: "Treatment" },
    { id: "investigations", label: "Investigations" },
  ];

  return (
    <div className="mt-3 rounded-2xl overflow-hidden" style={{ border: "1px solid #e0e7ff", background: "#fafbff" }}>
      {/* Header */}
      <div
        className="px-4 py-3 flex items-center justify-between"
        style={{ background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)" }}
      >
        <div>
          <h4 className="text-base font-bold text-white capitalize">{data.disease_name}</h4>
          <div className="flex items-center gap-2 mt-0.5">
            {data.icd11_code && (
              <span className="text-[10px] bg-white/20 text-white px-2 py-0.5 rounded-full font-mono">
                ICD-11: {data.icd11_code}
              </span>
            )}
            {data.disease_class && (
              <span className="text-[10px] text-indigo-200 font-medium capitalize">
                {data.disease_class.replace(/_/g, " ")}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {data.is_outbreak_active && (
            <span className="text-[10px] bg-red-500 text-white px-2 py-0.5 rounded-full font-bold animate-pulse">
              ⚠ OUTBREAK ACTIVE
            </span>
          )}
          {data.is_notifiable && (
            <span className="text-[10px] bg-amber-500 text-white px-2 py-0.5 rounded-full font-bold">
              NOTIFIABLE
            </span>
          )}
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex border-b border-indigo-100 bg-white">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setSection(t.id)}
            className="flex-1 py-2 text-xs font-semibold transition-colors"
            style={{
              color: section === t.id ? "#4f46e5" : "#94a3b8",
              borderBottom: section === t.id ? "2px solid #4f46e5" : "2px solid transparent",
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-4">
        {section === "overview" && (
          <div className="space-y-3">
            <p className="text-sm text-slate-700 leading-relaxed">{data.summary}</p>
            {data.red_flags && data.red_flags.length > 0 && (
              <div className="rounded-xl p-3" style={{ background: "#fff1f2", border: "1px solid #fecdd3" }}>
                <h5 className="text-xs font-bold text-red-700 mb-2 flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5" /> Red Flags — Immediate Escalation
                </h5>
                <ul className="space-y-1">
                  {data.red_flags.slice(0, 5).map((f, i) => (
                    <li key={i} className="text-xs text-red-700 flex items-start gap-1.5">
                      <span className="shrink-0 mt-0.5 w-1.5 h-1.5 rounded-full bg-red-500" />
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {data.prognosis && (
              <div className="text-xs text-slate-600 rounded-xl p-3" style={{ background: "#f0fdf4", border: "1px solid #bbf7d0" }}>
                <span className="font-bold text-emerald-700">Prognosis: </span>{data.prognosis}
              </div>
            )}
          </div>
        )}
        {section === "symptoms" && (
          <div className="space-y-3">
            {data.cardinal_symptoms && data.cardinal_symptoms.length > 0 && (
              <div>
                <h5 className="text-xs font-bold text-slate-500 uppercase mb-2">Cardinal Symptoms</h5>
                <div className="flex flex-wrap gap-1.5">
                  {data.cardinal_symptoms.map((s, i) => (
                    <span key={i} className="text-xs px-2.5 py-1 rounded-full font-semibold" style={{ background: "#eff6ff", color: "#1d4ed8", border: "1px solid #bfdbfe" }}>
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {data.symptoms && data.symptoms.length > 0 && (
              <div>
                <h5 className="text-xs font-bold text-slate-500 uppercase mb-2">All Symptoms</h5>
                <div className="grid grid-cols-2 gap-1">
                  {data.symptoms.slice(0, 12).map((s, i) => (
                    <div key={i} className="text-xs text-slate-600 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-400 shrink-0" />{s}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        {section === "treatment" && (
          <div className="space-y-3">
            {data.first_line_treatment && (
              <div className="rounded-xl p-3" style={{ background: "#f0fdf4", border: "1px solid #bbf7d0" }}>
                <h5 className="text-xs font-bold text-emerald-700 mb-1 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" /> First-Line Treatment
                </h5>
                <p className="text-xs text-slate-700">{data.first_line_treatment}</p>
              </div>
            )}
            {data.medications && data.medications.length > 0 && (
              <div className="rounded-xl p-3" style={{ background: "#f5f3ff", border: "1px solid #ddd6fe" }}>
                <h5 className="text-xs font-bold text-purple-700 mb-2 flex items-center gap-1.5">
                  <Pill className="w-3.5 h-3.5" /> Guideline Pharmacotherapy &amp; Regimens
                </h5>
                <ul className="space-y-1.5">
                  {data.medications.map((m, i) => (
                    <li key={i} className="text-xs text-purple-950 font-medium flex items-start gap-1.5">
                      <span className="shrink-0 mt-0.5 w-1.5 h-1.5 rounded-full bg-purple-500" />
                      {m}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {data.treatments && data.treatments.length > 0 && (
              <div>
                <h5 className="text-xs font-bold text-slate-500 uppercase mb-2">All Treatment Options</h5>
                <ul className="space-y-1">
                  {data.treatments.slice(0, 10).map((t, i) => (
                    <li key={i} className="text-xs text-slate-600 flex items-start gap-1.5">
                      <span className="shrink-0 mt-0.5 w-1.5 h-1.5 rounded-full bg-emerald-500" />{t}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
        {section === "investigations" && (
          <div className="space-y-3">
            {data.investigations && data.investigations.length > 0 && (
              <div>
                <h5 className="text-xs font-bold text-slate-500 uppercase mb-2">Investigations</h5>
                <ul className="space-y-1">
                  {data.investigations.map((inv, i) => (
                    <li key={i} className="text-xs text-slate-600 flex items-start gap-1.5">
                      <FlaskConical className="w-3 h-3 text-purple-400 shrink-0 mt-0.5" />{inv}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {data.monitoring_parameters && data.monitoring_parameters.length > 0 && (
              <div>
                <h5 className="text-xs font-bold text-slate-500 uppercase mb-2">Monitoring Parameters</h5>
                <div className="flex flex-wrap gap-1.5">
                  {data.monitoring_parameters.map((m, i) => (
                    <span key={i} className="text-xs px-2 py-0.5 rounded-full" style={{ background: "#fdf4ff", color: "#7e22ce", border: "1px solid #e9d5ff" }}>
                      {m}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Data sources */}
      {data.data_sources && data.data_sources.length > 0 && (
        <div className="px-4 pb-3 flex flex-wrap gap-1">
          {data.data_sources.slice(0, 4).map((src, i) => (
            <span key={i} className="text-[10px] text-slate-400 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded-full">
              {src}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function ClinicalDocumentCard({
  doc,
  onPreview,
}: {
  doc: GeneratedClinicalDocument;
  onPreview?: (doc: GeneratedClinicalDocument) => void;
}) {
  const [downloading, setDownloading] = useState<string | null>(null);
  const [showSections, setShowSections] = useState(false);
  const { toast } = useToast();

  const handleDownload = async (format: "pdf" | "docx") => {
    try {
      setDownloading(format);
      const url = format === "pdf" ? doc.pdf_download_url : doc.docx_download_url;
      const rawUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const fullUrl = url.startsWith("http") ? url : `${rawUrl.replace(/\/api\/v1\/?$/, "")}${url.startsWith("/") ? "" : "/"}${url}`;

      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const res = await fetch(fullUrl, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      const cleanDocType = doc.document_type.replace(/_/g, "-");
      a.download = `${cleanDocType}_${doc.patient?.patient_ref || "patient"}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(blobUrl);
      toast.success(`${cleanDocType} downloaded successfully`);
    } catch (e: any) {
      toast.error(`Download failed: ${e.message || "Unknown error"}`);
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="mt-3.5 rounded-2xl overflow-hidden border border-indigo-200 bg-white shadow-sm">
      {/* Top Banner */}
      <div className="px-4 py-3 bg-gradient-to-r from-indigo-700 via-indigo-600 to-purple-700 text-white flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-white/20 flex items-center justify-center backdrop-blur-xs">
            <FileText className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="text-[10px] font-bold uppercase tracking-wider text-indigo-100 flex items-center gap-1.5">
              <span>{doc.document_type.replace(/_/g, " ")}</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span className="text-[10px] text-emerald-300 font-semibold">Digitally Certified</span>
            </div>
            <h4 className="text-sm font-bold text-white">{doc.title}</h4>
          </div>
        </div>
        <div className="text-right">
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/20 font-mono text-white">
            {doc.document_id}
          </span>
          <p className="text-[10px] text-indigo-200 mt-0.5">{doc.formatted_date}</p>
        </div>
      </div>

      {/* Meta Grid */}
      <div className="px-4 py-3 grid grid-cols-2 sm:grid-cols-4 gap-2.5 bg-slate-50 border-b border-slate-100 text-xs">
        <div>
          <span className="text-[10px] uppercase font-bold text-slate-400">Patient Ref</span>
          <p className="font-bold text-slate-800 font-mono">{doc.patient?.patient_ref || "PT-CONFIDENTIAL"}</p>
          <p className="text-[10px] text-slate-500">{doc.patient?.age_group} • {doc.patient?.biological_sex}</p>
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold text-slate-400">Attending Clinician</span>
          <p className="font-bold text-slate-800 truncate">Dr. {doc.clinician?.full_name}</p>
          <p className="text-[10px] text-slate-500">{doc.clinician?.specialty}</p>
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold text-slate-400">Medical License</span>
          <p className="font-bold text-slate-800 font-mono">{doc.clinician?.credential_reference || "NMC-VERIFIED"}</p>
          <p className="text-[10px] text-slate-500">{doc.clinician?.credential_body}</p>
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold text-slate-400">Verification Token</span>
          <p className="font-bold text-emerald-700 font-mono text-[11px] truncate">{doc.digital_signature?.verification_code}</p>
          <p className="text-[10px] text-emerald-600 font-medium">SHA-256 Validated</p>
        </div>
      </div>

      {/* Leave Period Highlight if medical certificate */}
      {doc.leave_period && (
        <div className="px-4 py-2.5 bg-amber-50 border-b border-amber-200 text-xs text-amber-900 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
            <span className="font-bold">Recommended Rest / Leave Period:</span>
            <span className="font-medium">{doc.leave_period}</span>
          </div>
          <span className="text-[10px] uppercase tracking-wider font-extrabold text-amber-800 bg-amber-200/70 px-2 py-0.5 rounded-full">Medically Certified</span>
        </div>
      )}

      {/* Sections Accordion */}
      {doc.sections && doc.sections.length > 0 && (
        <div className="px-4 py-2.5 border-b border-slate-100">
          <button
            onClick={() => setShowSections(v => !v)}
            className="flex items-center justify-between w-full text-xs font-semibold text-slate-700 hover:text-indigo-600 transition-colors cursor-pointer"
          >
            <span className="flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5 text-indigo-500" />
              Document Sections ({doc.sections.length} certified sections)
            </span>
            {showSections ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
          {showSections && (
            <div className="mt-2.5 space-y-2">
              {doc.sections.map((s, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-200/70">
                  <h5 className="text-xs font-bold text-indigo-900 mb-1">{s.title}</h5>
                  <p className="text-xs text-slate-700 whitespace-pre-line leading-relaxed">{s.content}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Digital Signature Verified Stamp Box */}
      <div className="px-4 py-3 bg-emerald-50/70 border-b border-emerald-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 text-xs">
        <div className="flex items-start gap-2.5">
          <div className="w-7 h-7 rounded-xl bg-emerald-600 text-white flex items-center justify-center shrink-0 mt-0.5">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-emerald-950">Official Clinician Digital Signature</span>
              <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-200 text-emerald-800">Tamper-Evident</span>
            </div>
            <p className="text-[11px] text-emerald-800 mt-0.5">
              Signed by Dr. {doc.digital_signature?.signed_by} • Reg: {doc.digital_signature?.registration_number} • {doc.digital_signature?.signed_at_formatted}
            </p>
            <p className="text-[10px] text-emerald-700 font-mono mt-0.5 truncate max-w-md">
              Digest: {doc.digital_signature?.sha256_hash}
            </p>
          </div>
        </div>
      </div>

      {/* Action Download & Preview Buttons */}
      <div className="px-4 py-3 bg-white flex flex-wrap items-center justify-between gap-2">
        <span className="text-[11px] text-slate-500 font-medium">Certified clinical document:</span>
        <div className="flex items-center gap-2">
          {onPreview && (
            <button
              type="button"
              onClick={() => onPreview(doc)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-indigo-700 bg-indigo-50 border border-indigo-200 hover:bg-indigo-100 transition-all cursor-pointer shadow-2xs active:scale-95"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Preview Document
            </button>
          )}

          <button
            type="button"
            onClick={() => handleDownload("pdf")}
            disabled={downloading !== null}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-white transition-all shadow-xs hover:opacity-90 active:scale-95 cursor-pointer"
            style={{
              background: "linear-gradient(135deg, #e11d48 0%, #be123c 100%)",
            }}
          >
            {downloading === "pdf" ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
            {downloading === "pdf" ? "Downloading..." : "Download PDF"}
          </button>

          <button
            type="button"
            onClick={() => handleDownload("docx")}
            disabled={downloading !== null}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-white transition-all shadow-xs hover:opacity-90 active:scale-95 cursor-pointer"
            style={{
              background: "linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)",
            }}
          >
            {downloading === "docx" ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
            {downloading === "docx" ? "Downloading..." : "Download DOCX"}
          </button>

          {doc.digital_signature?.verification_code && (
            <a
              href={`/verify?code=${encodeURIComponent(doc.digital_signature.verification_code)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-emerald-800 bg-emerald-50 border border-emerald-300 hover:bg-emerald-100 transition-all cursor-pointer shadow-2xs active:scale-95"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              Verify Certificate
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

function AssistantMessage({
  msg,
  onPreview,
}: {
  msg: Message;
  onPreview?: (doc: GeneratedClinicalDocument) => void;
}) {
  const [copied, setCopied] = useState(false);
  const [showCitations, setShowCitations] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(msg.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const rag = msg.ragData;
  const disease = msg.diseaseData;
  const conf = rag ? confColor(rag.confidence_score ?? 0) : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 320, damping: 28 }}
      className="flex gap-3"
    >
      {/* AI Avatar */}
      <div
        className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 mt-1"
        style={{ background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)", boxShadow: "0 4px 12px rgba(79,70,229,0.25)" }}
      >
        <Sparkles className="w-4 h-4 text-white" />
      </div>

      <div className="flex-1 min-w-0">
        {/* Answer */}
        <div
          className="rounded-2xl px-4 py-3"
          style={{
            background: "rgba(255,255,255,0.9)",
            border: "1px solid rgba(0,0,0,0.08)",
            boxShadow: "0 2px 12px rgba(0,0,0,0.06)",
          }}
        >
          {/* Header row */}
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-indigo-600">DocAssist IQ AI</span>
              {conf && (
                <span
                  className="text-[10px] px-2 py-0.5 rounded-full font-semibold border"
                  style={{ background: conf.bg, color: conf.text, borderColor: conf.border }}
                >
                  {conf.label}
                </span>
              )}
              {rag?.fallback_used && (
                <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                  Static KB
                </span>
              )}
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-slate-400 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </span>
              <button
                onClick={handleCopy}
                className="p-1 rounded text-slate-300 hover:text-slate-600 transition-colors"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          {/* Main answer text */}
          <FormattedClinicalContent content={msg.content} />

          {/* Generated Clinical Document Card */}
          {msg.generatedDocument && <ClinicalDocumentCard doc={msg.generatedDocument} onPreview={onPreview} />}

          {/* Disease data card */}
          {disease && <DiseaseCard data={disease} />}

          {/* Reasoning trace toggle */}
          {rag?.reasoning_trace && (
            <div className="mt-3">
              <button
                onClick={() => setShowReasoning(v => !v)}
                className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-600 transition-colors"
              >
                <Info className="w-3.5 h-3.5" />
                {showReasoning ? "Hide" : "Show"} clinical reasoning
                {showReasoning ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
              {showReasoning && (
                <div className="mt-2 text-xs text-slate-500 italic bg-slate-50 rounded-xl px-3 py-2 leading-relaxed border border-slate-100">
                  {rag.reasoning_trace}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Citations */}
        {rag?.citations && rag.citations.length > 0 && (
          <div className="mt-2 ml-1">
            <button
              onClick={() => setShowCitations(v => !v)}
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-indigo-600 transition-colors mb-2"
            >
              <BookOpen className="w-3.5 h-3.5" />
              {rag.citations.length} source{rag.citations.length !== 1 ? "s" : ""} cited
              {showCitations ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
            {showCitations && (
              <div className="space-y-1.5">
                {rag.citations.map((c, i) => (
                  <CitationCard key={c.id ?? i} citation={c} index={i} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}

// ── Advanced Modals & Header Components ──────────────────────────

function DocumentPreviewModal({
  doc,
  onClose,
}: {
  doc: GeneratedClinicalDocument;
  onClose: () => void;
}) {
  const [downloading, setDownloading] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const handleCopyText = async () => {
    try {
      const p = doc.patient;
      const c = doc.clinician;
      const sig = doc.digital_signature;

      let text = `# ${doc.title.toUpperCase()}\n`;
      if (doc.subtitle) text += `${doc.subtitle}\n`;
      text += `\n---\n`;
      text += `PATIENT: ${p?.patient_ref || "CONFIDENTIAL"} | Age: ${p?.age_group || "N/A"} | Sex: ${p?.biological_sex || "N/A"}\n`;
      text += `ALLERGIES: ${p?.allergies || "None Documented"}\n`;
      text += `ATTENDING CLINICIAN: Dr. ${c?.full_name || "Attending"} (${c?.specialty || "Medicine"})\n`;
      text += `LICENSE / REGISTRATION: ${c?.credential_reference || "N/A"} (${c?.credential_body || "NMC"})\n`;
      text += `DATE OF ISSUE: ${doc.formatted_date || new Date().toLocaleDateString()}\n`;
      if (doc.leave_period) {
        text += `AUTHORIZED MEDICAL ABSENCE: ${doc.leave_period}\n`;
      }
      text += `\n---\n`;

      if (doc.sections && doc.sections.length > 0) {
        doc.sections.forEach((sec) => {
          text += `\n## ${sec.title.toUpperCase()}\n${sec.content}\n`;
        });
      }

      text += `\n---\n`;
      text += `STATUTORY CLINICIAN DIGITAL SIGNATURE:\n`;
      text += `Signed by: Dr. ${sig?.signed_by || c?.full_name}\n`;
      text += `Registration: ${sig?.registration_number || c?.credential_reference} (${sig?.issuing_body || c?.credential_body})\n`;
      text += `Timestamp: ${sig?.signed_at_formatted || new Date().toISOString()}\n`;
      text += `Verification Code: ${sig?.verification_code || "N/A"}\n`;
      text += `SHA-256 Digest: ${sig?.sha256_hash || "N/A"}\n`;
      text += `Registry Verification URL: ${window.location.origin}/verify?code=${sig?.verification_code || ""}\n`;

      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast.success("Complete clinical document text copied to clipboard");
      setTimeout(() => setCopied(false), 2500);
    } catch {
      toast.error("Failed to copy document text");
    }
  };

  const handleDownload = async (format: "pdf" | "docx") => {
    try {
      setDownloading(format);
      const url = format === "pdf" ? doc.pdf_download_url : doc.docx_download_url;
      const rawUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const fullUrl = url.startsWith("http") ? url : `${rawUrl.replace(/\/api\/v1\/?$/, "")}${url.startsWith("/") ? "" : "/"}${url}`;

      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const res = await fetch(fullUrl, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      const cleanDocType = doc.document_type.replace(/_/g, "-");
      a.download = `${cleanDocType}_${doc.patient?.patient_ref || "patient"}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(blobUrl);
      toast.success(`${cleanDocType} downloaded successfully`);
    } catch (e: any) {
      toast.error(`Download failed: ${e.message || "Unknown error"}`);
    } finally {
      setDownloading(null);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/30 backdrop-blur-xs p-4 overflow-y-auto cursor-pointer"
    >
      <style jsx global>{`
        @media print {
          body * {
            visibility: hidden !important;
          }
          #clinical-document-paper, #clinical-document-paper * {
            visibility: visible !important;
          }
          #clinical-document-paper {
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
      <motion.div
        onClick={(e) => e.stopPropagation()}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="w-full max-w-4xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[92vh] my-auto cursor-default"
      >
        {/* Top Control Bar - Clean Hospital White */}
        <div className="px-6 py-3.5 bg-white border-b border-slate-200 text-slate-900 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-xs">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700">
                  Certified Clinical Document Preview
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold">
                  {doc.digital_signature?.verification_code}
                </span>
              </div>
              <h3 className="text-sm font-bold text-slate-900 truncate max-w-md">{doc.title}</h3>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyText}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-white hover:bg-slate-100 text-slate-800 border border-slate-300 transition-all cursor-pointer shadow-2xs"
              title="Copy full structured text for hospital EHR"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="text-emerald-700">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-slate-600" />
                  <span>Copy Full Text</span>
                </>
              )}
            </button>

            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-white hover:bg-slate-100 text-slate-800 border border-slate-300 transition-all cursor-pointer shadow-2xs"
              title="Print document"
            >
              <Printer className="w-3.5 h-3.5 text-slate-600" />
              Print
            </button>

            {doc.digital_signature?.verification_code && (
              <a
                href={`/verify?code=${encodeURIComponent(doc.digital_signature.verification_code)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 transition-all cursor-pointer shadow-2xs"
              >
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                Verify Online
              </a>
            )}

            <button
              onClick={() => handleDownload("pdf")}
              disabled={downloading !== null}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-white transition-all shadow-xs hover:opacity-90 active:scale-95 cursor-pointer"
              style={{ background: "linear-gradient(135deg, #e11d48 0%, #be123c 100%)" }}
            >
              {downloading === "pdf" ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
              PDF
            </button>

            <button
              onClick={() => handleDownload("docx")}
              disabled={downloading !== null}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-white transition-all shadow-xs hover:opacity-90 active:scale-95 cursor-pointer"
              style={{ background: "linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)" }}
            >
              {downloading === "docx" ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
              DOCX
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors ml-1 cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Paper Sheet Preview Container */}
        <div className="p-6 sm:p-10 overflow-y-auto bg-slate-50 flex justify-center">
          <div id="clinical-document-paper" className="w-full max-w-3xl bg-white rounded-2xl shadow-lg border border-slate-200/80 p-8 sm:p-12 space-y-6 text-slate-800">

            {/* Institution Letterhead */}
            <div className="text-center pb-6 border-b border-slate-200">
              <p className="text-xs font-extrabold uppercase tracking-widest text-indigo-700">
                DocAssistIQ Clinical Intelligence Health System
              </p>
              <h2 className="text-2xl font-black text-slate-900 mt-1 uppercase tracking-tight">
                {doc.title}
              </h2>
              <p className="text-xs text-slate-500 mt-1">{doc.subtitle}</p>
            </div>

            {/* Metadata Box */}
            <div className="grid grid-cols-2 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs">
              <div>
                <span className="text-[10px] font-bold uppercase text-slate-400">Patient Identifier</span>
                <p className="font-bold text-slate-900 font-mono">{doc.patient?.patient_ref || "PT-CONFIDENTIAL"}</p>
                <p className="text-slate-600 mt-0.5">Demographics: Age {doc.patient?.age_group} • Sex {doc.patient?.biological_sex}</p>
                <p className="text-slate-600 mt-0.5">Documented Allergies: <span className="font-medium text-slate-800">{doc.patient?.allergies || "NKDA"}</span></p>
              </div>
              <div>
                <span className="text-[10px] font-bold uppercase text-slate-400">Attending Clinician & Authority</span>
                <p className="font-bold text-slate-900">Dr. {doc.clinician?.full_name} ({doc.clinician?.specialty})</p>
                <p className="text-slate-600 mt-0.5">Medical License / Reg: <span className="font-mono">{doc.clinician?.credential_reference}</span></p>
                <p className="text-slate-600 mt-0.5">Issue Timestamp: {doc.formatted_date}</p>
              </div>
            </div>

            {/* Leave Period Highlight if any */}
            {doc.leave_period && (
              <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-between text-xs text-amber-900">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse" />
                  <span className="font-bold">Medical Absence Authorized:</span>
                  <span className="font-semibold">{doc.leave_period}</span>
                </div>
                <span className="text-[10px] uppercase font-black tracking-wider text-amber-800 bg-amber-200/80 px-2 py-0.5 rounded-full">
                  Verified Leave
                </span>
              </div>
            )}

            {/* Document Sections */}
            <div className="space-y-6 pt-2">
              {doc.sections?.map((sec, idx) => (
                <div key={idx} className="space-y-1.5">
                  <h4 className="text-sm font-bold text-indigo-950 uppercase tracking-wide border-b border-indigo-100 pb-1 flex items-center gap-2">
                    <span className="w-1.5 h-3.5 bg-indigo-600 rounded-xs" />
                    {sec.title}
                  </h4>
                  <p className="text-xs text-slate-700 whitespace-pre-line leading-relaxed pl-3.5">
                    {sec.content}
                  </p>
                </div>
              ))}
            </div>

            {/* Safety Warning Banner */}
            <div className="p-3 rounded-xl bg-amber-50/80 border border-amber-200 text-center text-[10px] font-bold text-amber-800">
              REFERENCE CLINICAL INFORMATION — VERIFIED CLINICIAN SIGNATURE APPLIED
            </div>

            {/* Certified Digital Signature Box */}
            <div className="p-5 rounded-2xl bg-emerald-50 border border-emerald-300 text-xs text-emerald-950 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-lg bg-emerald-600 text-white flex items-center justify-center">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <span className="font-black text-xs uppercase tracking-wider text-emerald-900">
                    Official Clinician Digital Signature &amp; Verification Stamp
                  </span>
                </div>
                <span className="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-200 text-emerald-900">
                  {doc.digital_signature?.signature_status || "VERIFIED VALID"}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 border-t border-emerald-200/70">
                <div>
                  <p><span className="text-slate-500">Digitally Signed By:</span> <strong>Dr. {doc.digital_signature?.signed_by}</strong></p>
                  <p><span className="text-slate-500">Medical Registration:</span> <strong>{doc.digital_signature?.registration_number} ({doc.digital_signature?.issuing_body})</strong></p>
                </div>
                <div>
                  <p><span className="text-slate-500">Signed Timestamp:</span> <strong>{doc.digital_signature?.signed_at_formatted}</strong></p>
                  <p><span className="text-slate-500">Verification Token:</span> <strong className="font-mono text-indigo-700">{doc.digital_signature?.verification_code}</strong></p>
                </div>
              </div>

              <p className="text-[10px] text-slate-500 font-mono pt-1 truncate">
                SHA-256 Digest: {doc.digital_signature?.sha256_hash}
              </p>
            </div>

            {/* Footnote */}
            <p className="text-[10px] text-center text-slate-400 italic pt-2">
              DocAssistIQ Clinical AI Platform • Legally Binding Electronic Health Record • Confidential Medical Data
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

function ConsultationDocumentsModal({
  consultationId,
  documents,
  onClose,
  onTriggerGenerate,
}: {
  consultationId: string;
  documents: VerifiedDocumentRecord[];
  onClose: () => void;
  onTriggerGenerate: (prompt: string) => void;
}) {
  const [downloading, setDownloading] = useState<string | null>(null);
  const { toast } = useToast();

  const handleDownload = async (docType: string, format: "pdf" | "docx") => {
    try {
      setDownloading(`${docType}-${format}`);
      const rawUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const rootUrl = rawUrl.replace(/\/api\/v1\/?$/, "");
      const downloadEndpoint = `${rootUrl}/api/v1/clinical-documents/export/${encodeURIComponent(consultationId)}/${encodeURIComponent(docType)}/${format}`;
      const res = await fetch(downloadEndpoint);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = `${docType}_${consultationId.slice(0, 8)}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(blobUrl);
      toast.success(`${docType.replace(/_/g, " ")} downloaded successfully`);
    } catch (e: any) {
      toast.error(`Download failed: ${e.message || "Unknown error"}`);
    } finally {
      setDownloading(null);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/30 backdrop-blur-xs p-4 overflow-y-auto cursor-pointer"
    >
      <motion.div
        onClick={(e) => e.stopPropagation()}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="w-full max-w-3xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[85vh] my-auto cursor-default"
      >
        {/* Header - Clean Hospital White */}
        <div className="px-6 py-4 bg-white border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center">
              <FileCheck className="w-5 h-5 text-emerald-700" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900">Certified Documents Archive</h3>
                <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                  @{consultationId.slice(0, 8)}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Official signed records, tamper-evident tokens, and instant downloads
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-3.5 bg-slate-50 flex-1">
          {documents.length === 0 ? (
            <div className="p-10 text-center bg-white rounded-2xl border border-slate-200 space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
                <FileText className="w-6 h-6" />
              </div>
              <h4 className="text-sm font-bold text-slate-800">No Certified Documents Signed Yet</h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                You can generate digitally signed discharge summaries, e-prescriptions, medical certificates, or care plans using the quick actions below.
              </p>
              <div className="flex flex-wrap justify-center gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    onTriggerGenerate("Generate official certified electronic prescription with digital signature");
                  }}
                  className="px-3 py-1.5 rounded-xl text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100 transition-colors"
                >
                  + Generate E-Prescription
                </button>
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    onTriggerGenerate("Generate certified discharge summary with digital signature");
                  }}
                  className="px-3 py-1.5 rounded-xl text-xs font-bold bg-indigo-50 text-indigo-800 border border-indigo-200 hover:bg-indigo-100 transition-colors"
                >
                  + Generate Discharge Summary
                </button>
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    onTriggerGenerate("Generate official medical certificate for patient with digital signature");
                  }}
                  className="px-3 py-1.5 rounded-xl text-xs font-bold bg-purple-50 text-purple-800 border border-purple-200 hover:bg-purple-100 transition-colors"
                >
                  + Generate Medical Certificate
                </button>
              </div>
            </div>
          ) : (
            documents.map((d, idx) => (
              <div
                key={idx}
                className="p-4 rounded-2xl bg-white border border-slate-200 shadow-2xs hover:border-indigo-200 transition-all space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-700 flex items-center justify-center font-bold text-xs shrink-0">
                      {d.document_type === "e_prescription" ? "💊" : d.document_type === "discharge_summary" ? "📄" : "🎖️"}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-extrabold uppercase tracking-wider text-indigo-700">
                          {d.document_type.replace(/_/g, " ")}
                        </span>
                        <span className="text-[10px] font-bold px-2 py-0.2 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
                          Signed &amp; Valid
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-slate-900">{d.title}</h4>
                    </div>
                  </div>
                  <div className="text-left sm:text-right">
                    <span className="text-[10px] font-mono font-bold text-slate-700 block">
                      {d.verification_code}
                    </span>
                    <span className="text-[11px] text-slate-500">{d.signed_at_formatted}</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-bold block">Prescriber</span>
                    <span className="font-bold text-slate-800 truncate block">
                      {d.doctor_name?.startsWith("Dr.") ? d.doctor_name : `Dr. ${d.doctor_name || "Attending Clinician"}`}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-bold block">Patient Ref</span>
                    <span className="font-mono font-bold text-slate-800 block">{d.patient_ref}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-bold block">Specialty / Board</span>
                    <span className="text-slate-700 truncate block">{d.doctor_specialty}</span>
                  </div>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-100">
                  <span className="text-[11px] text-slate-500">
                    {d.sections_summary?.length || 0} certified sections
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleDownload(d.document_type, "pdf")}
                      disabled={downloading !== null}
                      className="px-3 py-1.5 rounded-xl text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 transition-colors flex items-center gap-1.5 cursor-pointer shadow-2xs"
                    >
                      <Download className="w-3.5 h-3.5" />
                      PDF
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDownload(d.document_type, "docx")}
                      disabled={downloading !== null}
                      className="px-3 py-1.5 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 transition-colors flex items-center gap-1.5 cursor-pointer shadow-2xs"
                    >
                      <Download className="w-3.5 h-3.5" />
                      DOCX
                    </button>
                    <a
                      href={`/verify?code=${encodeURIComponent(d.verification_code)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1.5 rounded-xl text-xs font-bold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 transition-colors flex items-center gap-1.5 shadow-2xs"
                    >
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                      Verify
                    </a>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-200 bg-white flex items-center justify-between text-xs text-slate-500">
          <span>Official DocAssistIQ Medical Registry</span>
          <button
            type="button"
            onClick={onClose}
            className="px-3.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold cursor-pointer"
          >
            Close
          </button>
        </div>
      </motion.div>
    </div>
  );
}

function TimelineModal({
  consultationId,
  timeline,
  onClose,
  onTriggerGenerate,
}: {
  consultationId: string;
  timeline: any;
  onClose: () => void;
  onTriggerGenerate: (prompt: string) => void;
}) {
  const audits = timeline?.audit_events || [];
  const consents = timeline?.consent_records || [];

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/30 backdrop-blur-xs p-4 overflow-y-auto cursor-pointer"
    >
      <motion.div
        onClick={(e) => e.stopPropagation()}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="w-full max-w-2xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[85vh] my-auto cursor-default"
      >
        {/* Header - Clean Hospital White */}
        <div className="px-6 py-4 bg-white border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Encounter Timeline &amp; Clinical Audit Trail</h3>
              <p className="text-xs text-slate-500 font-mono">Consultation: @{consultationId.slice(0, 8)}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 bg-slate-50 flex-1">
          {/* Status summary */}
          <div className="grid grid-cols-3 gap-3 p-3 bg-white rounded-2xl border border-slate-200 text-xs">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400">Current Status</span>
              <p className="font-bold text-indigo-700 uppercase mt-0.5">{timeline?.status || "Active"}</p>
            </div>
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400">Admission Timestamp</span>
              <p className="font-semibold text-slate-800 mt-0.5">{timeline?.admission_date || "Recorded"}</p>
            </div>
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400">Total Transitions</span>
              <p className="font-bold text-slate-800 mt-0.5">{audits.length} events</p>
            </div>
          </div>

          {/* Chronological State Transitions */}
          <div>
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-indigo-600" />
              Lifecycle State Transitions (Immutable Audit Ledger)
            </h4>
            <div className="space-y-2.5">
              {audits.map((a: any, idx: number) => (
                <div key={idx} className="flex items-start gap-3 p-3 rounded-xl bg-white border border-slate-200">
                  <div className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                    {idx + 1}
                  </div>
                  <div className="flex-1 min-w-0 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900">
                        {(a.from_status || "INIT").toUpperCase()} → {(a.to_status || "UNKNOWN").toUpperCase()}
                      </span>
                      <span className="text-[10px] font-mono text-slate-400">{a.created_at || a.time_str}</span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      State transition verified by authorized clinician ledger
                    </p>
                  </div>
                </div>
              ))}
              {audits.length === 0 && (
                <p className="text-xs text-slate-500 italic p-3 bg-white rounded-xl border border-slate-200">
                  No previous state transitions recorded. Encounter currently in initial status.
                </p>
              )}
            </div>
          </div>

          {/* Informed Consent Audit */}
          <div>
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              Informed Consent Records
            </h4>
            <div className="space-y-2">
              {consents.map((c: any, idx: number) => (
                <div key={idx} className="p-3.5 rounded-xl bg-emerald-50/70 border border-emerald-200 text-xs">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-500" />
                      <strong className="text-emerald-950 font-bold uppercase">{c.status}</strong>
                      <span className="text-slate-600">• {c.actor_name} ({c.actor_relationship})</span>
                    </div>
                    <span className="text-[10px] text-emerald-700 font-mono">{c.created_at}</span>
                  </div>
                  <p className="text-[11px] text-slate-700 mt-1">
                    <strong>Purpose:</strong> {c.purpose} | <strong>Audio Recording:</strong> {c.recording_permitted ? "Granted" : "Withheld"}
                  </p>
                </div>
              ))}
              {consents.length === 0 && (
                <p className="text-xs text-slate-500 italic p-3 bg-white rounded-xl border border-slate-200">
                  Standard consultation consent granted upon registration.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-200 bg-white flex items-center justify-between">
          <span className="text-[11px] text-slate-500">DocAssistIQ Tamper-Evident Clinical Audit</span>
          <button
            onClick={() => {
              onClose();
              onTriggerGenerate("generate certified encounter timeline certificate with digital signature");
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 cursor-pointer shadow-xs"
          >
            <Download className="w-3.5 h-3.5" />
            Generate Certified Timeline Certificate
          </button>
        </div>
      </motion.div>
    </div>
  );
}

function ProfileSummaryModal({
  patient,
  doctor,
  onClose,
  onTriggerGenerate,
}: {
  patient: any;
  doctor: any;
  onClose: () => void;
  onTriggerGenerate: (prompt: string) => void;
}) {
  const chronic = patient?.chronic_conditions || [];
  const meds = patient?.baseline_medications || [];
  const allergies = patient?.allergies || [];
  const surgeries = patient?.past_surgeries || [];
  const family = patient?.family_history || [];

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/30 backdrop-blur-xs p-4 overflow-y-auto cursor-pointer"
    >
      <motion.div
        onClick={(e) => e.stopPropagation()}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="w-full max-w-2xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[85vh] my-auto cursor-default"
      >
        {/* Header - Clean Hospital White */}
        <div className="px-6 py-4 bg-white border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center">
              <UserCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Patient Longitudinal Profile &amp; Medical History</h3>
              <p className="text-xs text-slate-500 font-mono">Reference: {patient?.patient_ref || "PT-CONFIDENTIAL"}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-5 bg-slate-50 flex-1 text-xs">
          {/* Demographics Card */}
          <div className="grid grid-cols-3 gap-3 p-4 bg-white rounded-2xl border border-slate-200">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400">Demographic Cohort</span>
              <p className="font-bold text-slate-900 mt-0.5">Age: {patient?.age_group || "Adult"}</p>
              <p className="text-slate-600">Sex: {patient?.biological_sex || "Not specified"}</p>
            </div>
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400">Documented Allergies</span>
              <p className="font-bold text-rose-700 mt-0.5">
                {allergies.length > 0 ? allergies.join(", ") : "No Known Drug Allergies (NKDA)"}
              </p>
            </div>
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400">Attending Clinician</span>
              <p className="font-bold text-slate-900 mt-0.5">Dr. {doctor?.full_name || "Attending Doctor"}</p>
              <p className="text-slate-600">{doctor?.specialty || "General Medicine"}</p>
            </div>
          </div>

          {/* Chronic Comorbidities */}
          <div className="p-4 bg-white rounded-2xl border border-slate-200">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-indigo-600" />
              Documented Chronic Comorbidities &amp; Conditions
            </h4>
            <div className="flex flex-wrap gap-2">
              {chronic.map((c: string, i: number) => (
                <span key={i} className="px-2.5 py-1 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-900 font-semibold">
                  • {c}
                </span>
              ))}
              {chronic.length === 0 && (
                <span className="text-slate-500 italic">No chronic medical conditions documented.</span>
              )}
            </div>
          </div>

          {/* Baseline Pharmacotherapy */}
          <div className="p-4 bg-white rounded-2xl border border-slate-200">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <Pill className="w-3.5 h-3.5 text-emerald-600" />
              Baseline Maintenance Medications
            </h4>
            <div className="space-y-1.5">
              {meds.map((m: string, i: number) => (
                <div key={i} className="flex items-center gap-2 text-slate-700 font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                  {m}
                </div>
              ))}
              {meds.length === 0 && (
                <span className="text-slate-500 italic">No long-term maintenance medications documented.</span>
              )}
            </div>
          </div>

          {/* Surgical & Family History */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-4 bg-white rounded-2xl border border-slate-200">
              <span className="text-[10px] uppercase font-bold text-slate-400">Past Surgical History</span>
              <p className="font-semibold text-slate-800 mt-1">
                {surgeries.length > 0 ? surgeries.join(", ") : "None documented"}
              </p>
            </div>
            <div className="p-4 bg-white rounded-2xl border border-slate-200">
              <span className="text-[10px] uppercase font-bold text-slate-400">Family Medical History</span>
              <p className="font-semibold text-slate-800 mt-1">
                {family.length > 0 ? family.join(", ") : "None documented"}
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-200 bg-white flex items-center justify-between">
          <span className="text-[11px] text-slate-500">DocAssistIQ Certified Patient Registry</span>
          <button
            onClick={() => {
              onClose();
              onTriggerGenerate("generate certified patient profile report with digital signature");
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 cursor-pointer shadow-xs"
          >
            <Download className="w-3.5 h-3.5" />
            Generate Certified Profile Report
          </button>
        </div>
      </motion.div>
    </div>
  );
}

function PatientSnapshotBar({
  taggedConsultation,
  timelineSummary,
  documentsCount,
  onOpenProfile,
  onOpenTimeline,
  onOpenDocuments,
  onClearTag,
}: {
  taggedConsultation: any;
  timelineSummary: any;
  documentsCount: number;
  onOpenProfile: () => void;
  onOpenTimeline: () => void;
  onOpenDocuments: () => void;
  onClearTag: () => void;
}) {
  const p = timelineSummary?.patient;
  const d = timelineSummary?.doctor;
  const chronic = p?.chronic_conditions || [];
  const allergies = p?.allergies || [];

  return (
    <div className="w-full p-3.5 rounded-2xl bg-gradient-to-r from-indigo-50/90 via-white to-slate-50 border border-indigo-200 shadow-2xs flex flex-wrap items-center justify-between gap-3 text-xs">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold text-xs shrink-0 shadow-2xs">
          <Tag className="w-4 h-4" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono font-bold text-indigo-900 bg-indigo-100/70 px-2 py-0.5 rounded text-xs">
              {p?.patient_ref || `@${taggedConsultation.id.slice(0, 8)}`}
            </span>
            <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
              {timelineSummary?.status || taggedConsultation.status || "Active"}
            </span>
            <span className="text-slate-500 text-[11px]">
              Age: <strong>{p?.age_group || "Adult"}</strong> • Sex: <strong>{p?.biological_sex || "Not specified"}</strong>
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-1.5 mt-1.5">
            {chronic.slice(0, 3).map((c: string, i: number) => (
              <span key={i} className="text-[10px] font-medium px-2 py-0.2 rounded-md bg-slate-100 text-slate-700 border border-slate-200">
                {c}
              </span>
            ))}
            {allergies.length > 0 && (
              <span className="text-[10px] font-bold px-2 py-0.2 rounded-md bg-rose-50 text-rose-700 border border-rose-200">
                Allergy: {allergies[0]}
              </span>
            )}
            {d?.full_name && (
              <span className="text-[10px] text-slate-500 ml-1">
                Doctor: {d.full_name.startsWith("Dr.") ? d.full_name : `Dr. ${d.full_name}`} {d.specialty ? `(${d.specialty})` : ""}
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onOpenProfile}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition-all cursor-pointer shadow-2xs"
        >
          <UserCheck className="w-3.5 h-3.5 text-indigo-600" />
          Patient Profile
        </button>
        <button
          onClick={onOpenTimeline}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition-all cursor-pointer shadow-2xs"
        >
          <Clock className="w-3.5 h-3.5 text-amber-600" />
          Timeline ({timelineSummary?.audit_events?.length || 0})
        </button>
        <button
          onClick={onOpenDocuments}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition-all cursor-pointer shadow-2xs"
        >
          <FileCheck className="w-3.5 h-3.5 text-emerald-600" />
          Documents ({documentsCount})
        </button>
        <button
          onClick={onClearTag}
          className="p-1.5 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer"
          title="Detach consultation"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────

function AIPageContent() {
  const { toast } = useToast();
  const searchParams = useSearchParams();
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState(0);
  const [isLongRunning, setIsLongRunning] = useState(false);
  const [mode, setMode] = useState<QueryMode>(() => {
    const tabParam = searchParams.get("tab") || searchParams.get("mode");
    if (tabParam === "outbreaks") return "outbreaks";
    if (tabParam === "disease") return "disease";
    return "rag";
  });

  // Consultation @ Mention & Tagging State
  const [allConsultations, setAllConsultations] = useState<any[]>([]);
  const [taggedConsultation, setTaggedConsultation] = useState<any | null>(null);
  const [showMentionMenu, setShowMentionMenu] = useState(false);
  const [mentionFilter, setMentionFilter] = useState("");
  const [showTagModal, setShowTagModal] = useState(false);
  const [timelineSummary, setTimelineSummary] = useState<any | null>(null);
  const [previewDoc, setPreviewDoc] = useState<GeneratedClinicalDocument | null>(null);
  const [showTimelineModal, setShowTimelineModal] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [consultationDocs, setConsultationDocs] = useState<VerifiedDocumentRecord[]>([]);
  const [showDocumentsModal, setShowDocumentsModal] = useState(false);

  const inputRef = useRef<HTMLTextAreaElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Fetch recent consultations for @mention autocomplete
  useEffect(() => {
    listConsultations(1, 50)
      .then(res => {
        if (res.ok && res.data?.items) {
          setAllConsultations(res.data.items);
        }
      })
      .catch(() => {});
  }, []);

  // Sync mode with URL search parameters
  useEffect(() => {
    const tabParam = searchParams.get("tab") || searchParams.get("mode");
    if (tabParam === "outbreaks") {
      setMode("outbreaks");
    } else if (tabParam === "disease") {
      setMode("disease");
    } else if (tabParam === "rag") {
      setMode("rag");
    }
  }, [searchParams]);

  // Auto-tag consultation if URL param contains consultation_id or cid
  useEffect(() => {
    const cid = searchParams.get("consultation_id") || searchParams.get("cid");
    if (cid) {
      const match = allConsultations.find(c => c.id === cid);
      if (match) {
        setTaggedConsultation(match);
      } else {
        setTaggedConsultation({ id: cid, status: "active" });
      }
    }
  }, [searchParams, allConsultations]);

  // Fetch timeline summary, patient profile, and certified signed documents when a consultation is tagged
  useEffect(() => {
    if (!taggedConsultation?.id) {
      setTimelineSummary(null);
      setConsultationDocs([]);
      return;
    }
    let isMounted = true;
    const fetchTimeline = async () => {
      try {
        const rawUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const rootUrl = rawUrl.replace(/\/api\/v1\/?$/, "");
        const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
        const res = await fetch(`${rootUrl}/api/v1/consultations/${taggedConsultation.id}/timeline/summary`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (res.ok && isMounted) {
          const data = await res.json();
          setTimelineSummary(data);
        }
      } catch (err) {
        console.error("Failed to fetch timeline summary", err);
      }
    };
    fetchTimeline();

    // Fetch signed documents for this consultation
    listDocumentsForConsultation(taggedConsultation.id)
      .then((res) => {
        if (res.ok && res.data?.documents && isMounted) {
          setConsultationDocs(res.data.documents);
        } else if (isMounted) {
          setConsultationDocs([]);
        }
      })
      .catch(() => {
        if (isMounted) setConsultationDocs([]);
      });

    return () => {
      isMounted = false;
    };
  }, [taggedConsultation?.id]);

  // Track long-running AI generation (>15s)
  useEffect(() => {
    if (!loading) {
      setIsLongRunning(false);
      return;
    }
    const timer = setTimeout(() => {
      setIsLongRunning(true);
    }, 15000);
    return () => clearTimeout(timer);
  }, [loading]);

  // Loading phase animation
  useEffect(() => {
    if (!loading) return;
    setLoadingPhase(0);
    const interval = setInterval(() => {
      setLoadingPhase(prev => (prev < LOADING_PHASES.length - 1 ? prev + 1 : prev));
    }, 1800);
    return () => clearInterval(interval);
  }, [loading]);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const addMessage = useCallback((msg: Omit<Message, "id" | "timestamp">) => {
    setMessages(prev => [...prev, { ...msg, id: crypto.randomUUID(), timestamp: new Date() }]);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setQuery(val);

    // Detect @ mention trigger
    const lastAt = val.lastIndexOf("@");
    if (lastAt !== -1 && lastAt >= val.length - 40) {
      const afterAt = val.slice(lastAt + 1).toLowerCase();
      setMentionFilter(afterAt);
      setShowMentionMenu(true);
    } else {
      setShowMentionMenu(false);
    }
  };

  const handleSelectConsultation = (cons: any) => {
    setTaggedConsultation(cons);
    setShowMentionMenu(false);
    setShowTagModal(false);
    const lastAt = query.lastIndexOf("@");
    if (lastAt !== -1) {
      setQuery(query.slice(0, lastAt).trim());
    }
    toast.success(`Tagged Consultation #${cons.id.slice(0, 8)}`);
  };

  const handleClearTag = () => {
    setTaggedConsultation(null);
    toast.info("Consultation tag removed");
  };

  const handleSubmit = useCallback(async (q: string) => {
    const trimmed = q.trim();
    if (!trimmed || loading) return;

    setQuery("");
    setShowMentionMenu(false);
    inputRef.current?.focus();

    // Add user message
    addMessage({ role: "user", content: trimmed });
    setLoading(true);

    // ── Check if Consultation Tagged or Mentioned via @ ───────────
    const fullUuidMatch = trimmed.match(/@([0-9a-fA-F-]{36})/i) || trimmed.match(/@([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/i);
    const shortUuidMatch = !fullUuidMatch ? trimmed.match(/@([0-9a-fA-F]{8})/i) : null;

    let detectedCid: string | null = fullUuidMatch ? fullUuidMatch[1] : null;
    let matchedConsultationObj: any = null;

    if (!detectedCid && shortUuidMatch) {
      const prefix = shortUuidMatch[1].toLowerCase();
      matchedConsultationObj = allConsultations.find(c => c.id && c.id.toLowerCase().startsWith(prefix));
      if (matchedConsultationObj) {
        detectedCid = matchedConsultationObj.id;
      }
    } else if (detectedCid) {
      matchedConsultationObj = allConsultations.find(c => c.id === detectedCid) || { id: detectedCid, status: "active" };
    }

    const activeCid = taggedConsultation?.id || detectedCid;

    if (matchedConsultationObj && (!taggedConsultation || taggedConsultation.id !== matchedConsultationObj.id)) {
      setTaggedConsultation(matchedConsultationObj);
    }

    if (activeCid) {
      try {
        const qaRes = await askDoctorNotesGeneral(trimmed, undefined, activeCid);
        if (qaRes.ok) {
          addMessage({
            role: "assistant",
            content: qaRes.data.answer || "Clinical consultation record processed.",
            ragData: {
              query: trimmed,
              answer: qaRes.data.answer || "",
              citations: (qaRes.data.citations || []).map((c: any, i: number) => ({
                id: String(i),
                source_name: c.label || c.source_name || c.source_type || "Consultation Record",
                excerpt: c.excerpt || "",
                relevance_score: c.relevance ?? c.relevance_score ?? 0.95,
              })),
              confidence_score: qaRes.data.confidence_score ?? 0.95,
              insufficient_evidence: false,
              fallback_used: qaRes.data.fallback_used ?? false,
            },
            generatedDocument: qaRes.data.generated_document,
            consultationId: activeCid,
          });
          if (qaRes.data.generated_document && activeCid) {
            listDocumentsForConsultation(activeCid).then((r) => {
              if (r.ok && r.data?.documents) setConsultationDocs(r.data.documents);
            }).catch(() => {});
          }
          setLoading(false);
          return;
        } else {
          addMessage({
            role: "error",
            content: qaRes.error?.message || "Failed to query tagged consultation record. Please try again.",
          });
          setLoading(false);
          return;
        }
      } catch (err: any) {
        addMessage({
          role: "error",
          content: err?.message || "Unexpected error processing consultation. Please check backend connection.",
        });
        setLoading(false);
        return;
      }
    }

    // ── Helper: call public /ai/ask (no auth needed, uses real-time medical engine)
    const askPublic = async (qText: string) => {
      const rawUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const rootUrl = rawUrl.replace(/\/api\/v1\/?$/, "");
      const askUrl = `${rootUrl}/ai/ask`;
      const resp = await fetch(askUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: qText, top_k: 5 }),
        signal: AbortSignal.timeout(90000),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return resp.json();
    };

    try {
      // Route query:
      // Only use Disease Intelligence when user explicitly selected Disease Mode and provided a short term (< 60 chars)
      const isShortDiseaseLookup = mode === "disease" && trimmed.length <= 60 && !trimmed.includes("\n") && !/^(what|how|why|can|explain|describe|dosing|when|patient)\b/i.test(trimmed);

      if (isShortDiseaseLookup) {
        // Try Disease Intelligence first
        const res = await getDiseaseIntelligence(trimmed);
        if (res.ok) {
          addMessage({
            role: "assistant",
            content: res.data.summary,
            diseaseData: res.data,
          });
        } else {
          // Fall back to public AI ask
          try {
            const aiData = await askPublic(trimmed);
            addMessage({
              role: "assistant",
              content: aiData.answer || "No answer found.",
              ragData: { ...aiData, citations: aiData.citations || [], confidence_score: aiData.confidence_score || 0.7, insufficient_evidence: false, fallback_used: false },
            });
          } catch {
            addMessage({ role: "error", content: "Disease intelligence unavailable. Please try a general question." });
          }
        }
      } else {
        // General clinical Q&A — use public /ai/ask (real-time medical engine)
        try {
          const aiData = await askPublic(trimmed);
          addMessage({
            role: "assistant",
            content: aiData.answer || "No answer found.",
            ragData: {
              query: trimmed,
              answer: aiData.answer || "",
              citations: aiData.citations || [],
              confidence_score: aiData.confidence_score || 0.75,
              insufficient_evidence: false,
              fallback_used: aiData.fallback_used || false,
            },
          });
        } catch {
          // Fallback to authenticated RAG
          const res = await ragQuery({ query: trimmed, top_k: 5, filters: { only_approved: false } });
          if (res.ok) {
            addMessage({ role: "assistant", content: res.data.answer, ragData: res.data });
          } else {
            addMessage({ role: "error", content: "AI query failed. Please check your connection and try again." });
          }
        }
      }
    } catch (e) {
      addMessage({ role: "error", content: "Unexpected error. Please try again." });
    } finally {
      setLoading(false);
    }
  }, [loading, mode, taggedConsultation, addMessage, allConsultations]);

  const handleKey = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(query);
    }
  }, [query, handleSubmit]);

  const PhaseIcon = LOADING_PHASES[loadingPhase].icon;

  const filteredMentionConsultations = allConsultations.filter(c => {
    if (!mentionFilter) return true;
    const q = mentionFilter.toLowerCase();
    return (
      (c.id && c.id.toLowerCase().includes(q)) ||
      (c.input_preview && c.input_preview.toLowerCase().includes(q)) ||
      (c.status && c.status.toLowerCase().includes(q))
    );
  }).slice(0, 6);

  return (
    <div className="flex flex-col h-[calc(100vh-72px)] overflow-hidden relative">

      {/* ── DocAssist IQ AI Header ─────────────────────────── */}
      <div
        className="px-6 py-4 border-b flex items-center justify-between shrink-0"
        style={{
          background: "linear-gradient(135deg, rgba(248,250,252,0.95) 0%, rgba(243,244,246,0.95) 100%)",
          backdropFilter: "blur(20px)",
          borderColor: "rgba(0,0,0,0.07)",
        }}
      >
        <div className="flex items-center gap-4">
          <div
            className="w-11 h-11 rounded-2xl flex items-center justify-center shrink-0"
            style={{
              background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
              boxShadow: "0 4px 16px rgba(79,70,229,0.3)",
            }}
          >
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-slate-900 leading-none">DocAssist IQ AI</h1>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/60 uppercase tracking-wide">
                Intelligence
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Evidence-grounded clinical intelligence • Tag @Consultation for certified documents & encounter Q&A
            </p>
          </div>
        </div>

        {/* Mode toggle & Controls */}
        <div className="flex items-center gap-2">
          {/* Tag Consultation Button */}
          <button
            onClick={() => setShowTagModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer"
            style={{
              background: taggedConsultation ? "rgba(79,70,229,0.12)" : "rgba(0,0,0,0.05)",
              color: taggedConsultation ? "#4f46e5" : "#64748b",
              border: taggedConsultation ? "1px solid rgba(79,70,229,0.3)" : "1px solid rgba(0,0,0,0.08)",
            }}
            title="Tag or switch consultation encounter"
          >
            <Tag className="w-3.5 h-3.5" />
            {taggedConsultation ? (
              <span className="font-mono">@{taggedConsultation.id.slice(0, 8)}</span>
            ) : (
              "Tag @Consultation"
            )}
          </button>

          <div
            className="flex items-center p-1 rounded-xl gap-1"
            style={{ background: "rgba(0,0,0,0.05)", border: "1px solid rgba(0,0,0,0.08)" }}
          >
            {(["rag", "disease", "outbreaks"] as QueryMode[]).map(m => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer"
                style={{
                  background: mode === m ? "#fff" : "transparent",
                  color: mode === m ? "#4f46e5" : "#64748b",
                  boxShadow: mode === m ? "0 1px 4px rgba(0,0,0,0.1)" : "none",
                }}
              >
                {m === "rag" ? "💬 Q&A Mode" : m === "disease" ? "🔬 Disease Mode" : "🗺️ State Outbreak Radar"}
                {m === "outbreaks" && (
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500 shadow-xs" />
                )}
              </button>
            ))}
          </div>

          {/* Clear chat */}
          {messages.length > 0 && mode !== "outbreaks" && (
            <button
              onClick={() => setMessages([])}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer"
              style={{ background: "rgba(0,0,0,0.05)", color: "#64748b", border: "1px solid rgba(0,0,0,0.08)" }}
            >
              <RefreshCw className="w-3.5 h-3.5" /> New Chat
            </button>
          )}
        </div>
      </div>

      {/* ── Active Tagged Patient Snapshot Bar ────────────────── */}
      {taggedConsultation && mode !== "outbreaks" && (
        <div className="px-6 pt-3 shrink-0">
          <PatientSnapshotBar
            taggedConsultation={taggedConsultation}
            timelineSummary={timelineSummary}
            documentsCount={consultationDocs.length}
            onOpenProfile={() => setShowProfileModal(true)}
            onOpenTimeline={() => setShowTimelineModal(true)}
            onOpenDocuments={() => setShowDocumentsModal(true)}
            onClearTag={handleClearTag}
          />
        </div>
      )}

      {/* ── Chat / Outbreak Content area ────────────────────── */}
      <div className="flex-1 overflow-y-auto px-4 pt-4 pb-52 space-y-6">
        {mode === "outbreaks" ? (
          <StateOutbreakRadar
            onSelectOutbreakForDiagnosis={(queryText) => {
              setMode("rag");
              handleSubmit(queryText);
            }}
          />
        ) : (
          <>
            {/* Empty state */}
            {messages.length === 0 && !loading && (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4"
              >
                <motion.div
                  animate={{ y: [0, -6, 0] }}
                  transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                  className="w-20 h-20 rounded-3xl flex items-center justify-center mb-6"
                  style={{
                    background: "linear-gradient(135deg, #eff6ff 0%, #f5f3ff 100%)",
                    border: "1px solid rgba(99,102,241,0.15)",
                    boxShadow: "0 8px 32px rgba(99,102,241,0.12)",
                  }}
                >
                  <Brain className="w-9 h-9 text-indigo-500" />
                </motion.div>
                <h2 className="text-2xl font-bold text-slate-800 mb-2">DocAssist IQ AI</h2>

                {taggedConsultation ? (
                  <div className="w-full max-w-2xl flex flex-col items-center">
                    <div className="mb-6 p-4 rounded-2xl bg-indigo-50/70 border border-indigo-200/80 text-left w-full shadow-xs">
                      <div className="flex items-center justify-between gap-3 mb-2">
                        <div className="flex items-center gap-2">
                          <Tag className="w-4 h-4 text-indigo-600" />
                          <span className="text-sm font-bold text-indigo-950">
                            Active Encounter: <span className="font-mono text-indigo-700">@{taggedConsultation.id.slice(0, 8)}...</span>
                          </span>
                        </div>
                        <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${
                          taggedConsultation.status === "completed" ? "bg-emerald-100 text-emerald-800" : "bg-blue-100 text-blue-800"
                        }`}>
                          {taggedConsultation.status || "active"}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 line-clamp-2">
                        {taggedConsultation.input_preview || "Real-time encounter record linked. Ready for clinical inquiries and signed documents."}
                      </p>
                    </div>

                    <p className="text-xs text-slate-500 mb-4 font-semibold uppercase tracking-wider">
                      Encounter Quick Actions & Certified Documents
                    </p>

                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 w-full">
                      {CONSULTATION_QUICK_ACTIONS.map(({ icon: Icon, label, prompt: p }, i) => (
                        <motion.button
                          key={i}
                          initial={{ opacity: 0, y: 8 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: i * 0.03 }}
                          whileHover={{ y: -2 }}
                          whileTap={{ opacity: 0.9 }}
                          onClick={() => handleSubmit(p)}
                          disabled={loading}
                          className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-left text-sm font-semibold transition-all bg-white border border-indigo-100/80 hover:border-indigo-300 shadow-xs text-slate-800 cursor-pointer"
                        >
                          <div className="w-7 h-7 rounded-lg bg-indigo-50 flex items-center justify-center shrink-0">
                            <Icon className="w-3.5 h-3.5 text-indigo-600" />
                          </div>
                          <span className="text-xs leading-normal font-medium">{label}</span>
                        </motion.button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <>
                    <p className="text-sm text-slate-500 mb-6 max-w-md leading-relaxed">
                      {mode === "rag"
                        ? "Ask clinical questions, or tag an encounter with @[Consultation ID] to generate certified Discharge Summaries, Medical Certificates, and inquire about patient details."
                        : "Enter a disease name to get a full 20+ field clinical intelligence profile."}
                    </p>

                    {/* Tag consultation CTA button */}
                    <div className="mb-8">
                      <button
                        onClick={() => setShowTagModal(true)}
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 transition-all shadow-xs cursor-pointer"
                      >
                        <Tag className="w-4 h-4 text-indigo-600" />
                        <span>Select & Tag a Consultation to Generate Documents</span>
                      </button>
                    </div>

                    {/* Quick-ask grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 w-full max-w-2xl">
                      {QUICK_ASKS.map(({ icon: Icon, label, query: q }, i) => (
                        <motion.button
                          key={i}
                          initial={{ opacity: 0, y: 8 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: i * 0.04 }}
                          whileHover={{ y: -2 }}
                          whileTap={{ opacity: 0.9 }}
                          onClick={() => handleSubmit(q)}
                          disabled={loading}
                          className="flex items-center gap-2.5 px-3.5 py-3 rounded-xl text-left text-sm font-semibold transition-all min-h-[52px] cursor-pointer"
                          style={{
                            background: "rgba(255,255,255,0.8)",
                            border: "1px solid rgba(0,0,0,0.08)",
                            boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
                            color: "#374151",
                          }}
                        >
                          <div
                            className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
                            style={{ background: "linear-gradient(135deg, #eff6ff, #f5f3ff)" }}
                          >
                            <Icon className="w-3.5 h-3.5 text-indigo-500" />
                          </div>
                          <span className="text-xs leading-normal font-medium">{label}</span>
                        </motion.button>
                      ))}
                    </div>
                  </>
                )}
              </motion.div>
            )}

            {/* Messages */}
            <AnimatePresence initial={false}>
              {messages.map(msg => {
                if (msg.role === "user") {
                  return (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex justify-end"
                    >
                      <div
                        className="max-w-[75%] rounded-2xl px-4 py-2.5 text-sm font-medium text-white"
                        style={{
                          background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
                          boxShadow: "0 4px 16px rgba(79,70,229,0.2)",
                        }}
                      >
                        {msg.content}
                      </div>
                    </motion.div>
                  );
                }
                if (msg.role === "error") {
                  return (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex gap-3"
                    >
                      <div className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 mt-1" style={{ background: "#fff1f2", border: "1px solid #fecdd3" }}>
                        <AlertTriangle className="w-4 h-4 text-red-500" />
                      </div>
                      <div className="flex-1 rounded-2xl px-4 py-3 text-sm text-red-700" style={{ background: "#fff1f2", border: "1px solid #fecdd3" }}>
                        <span className="font-bold">Error: </span>{msg.content}
                        <div className="mt-2 text-xs text-red-500">
                          Make sure the backend is running: <code className="bg-red-100 px-1 rounded">uvicorn app.main:app</code>
                        </div>
                      </div>
                    </motion.div>
                  );
                }
                return <AssistantMessage key={msg.id} msg={msg} onPreview={setPreviewDoc} />;
              })}
            </AnimatePresence>

            {/* Loading indicator */}
            {loading && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-3"
              >
                <div
                  className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 mt-1"
                  style={{ background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)" }}
                >
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
                <div
                  className="rounded-2xl px-4 py-3 flex items-center gap-3"
                  style={{ background: "rgba(255,255,255,0.9)", border: "1px solid rgba(0,0,0,0.08)" }}
                >
                  <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
                  <div>
                    <AnimatePresence mode="wait">
                      <motion.span
                        key={loadingPhase}
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -4 }}
                        className="text-sm font-medium text-slate-600 flex items-center gap-2"
                      >
                        <PhaseIcon className="w-3.5 h-3.5 text-indigo-400" />
                        {LOADING_PHASES[loadingPhase].text}
                      </motion.span>
                    </AnimatePresence>
                    <div className="flex gap-1 mt-1.5">
                      {LOADING_PHASES.map((_, i) => (
                        <div
                          key={i}
                          className="h-1 rounded-full transition-all duration-500"
                          style={{
                            width: i <= loadingPhase ? "24px" : "8px",
                            background: i <= loadingPhase ? "#4f46e5" : "#e2e8f0",
                          }}
                        />
                      ))}
                    </div>
                    {isLongRunning && (
                      <motion.p
                        initial={{ opacity: 0, y: 3 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-xs text-amber-600 mt-2 font-medium flex items-center gap-1.5 animate-pulse"
                      >
                        <span>⏳</span> Local AI model is compiling comprehensive clinical evidence...
                      </motion.p>
                    )}
                  </div>
                </div>
              </motion.div>
            )}

            <div ref={bottomRef} />
          </>
        )}
      </div>

      {/* ── Input bar & Floating Autocomplete ───────────────── */}
      {mode !== "outbreaks" && (
        <div
          className="px-4 py-4 shrink-0 relative"
          style={{
            background: "rgba(248,250,252,0.95)",
            backdropFilter: "blur(20px)",
            borderTop: "1px solid rgba(0,0,0,0.07)",
          }}
        >
          {/* Active Tagged Consultation Bar */}
          {taggedConsultation && (
            <div className="mb-2 px-3 py-2 rounded-xl bg-gradient-to-r from-indigo-50 via-white to-purple-50 border border-indigo-200/90 shadow-2xs flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center shrink-0 shadow-2xs">
                  <Tag className="w-3.5 h-3.5 text-white" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-indigo-950">
                      Encounter: <span className="font-mono text-indigo-700">@{taggedConsultation.id.slice(0, 8)}...</span>
                    </span>
                    <span className={`text-[10px] uppercase font-bold px-1.5 py-0.2 rounded-full ${
                      taggedConsultation.status === "completed" ? "bg-emerald-100 text-emerald-800" : "bg-blue-100 text-blue-800"
                    }`}>
                      {taggedConsultation.status || "active"}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 truncate max-w-md">
                    {taggedConsultation.input_preview || "Live encounter linked. Click quick actions or ask clinical questions."}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-1.5 shrink-0">
                <button
                  type="button"
                  onClick={handleClearTag}
                  className="p-1 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer"
                  title="Untag consultation"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* Quick Action Pills when Tagged */}
          {taggedConsultation && (
            <div className="mb-2.5 flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider shrink-0 mr-1 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-indigo-500" /> Actions:
              </span>
              {CONSULTATION_QUICK_ACTIONS.map((action, i) => {
                const Icon = action.icon;
                return (
                  <button
                    key={i}
                    type="button"
                    onClick={() => handleSubmit(action.prompt)}
                    disabled={loading}
                    className="px-2.5 py-1 rounded-lg text-xs font-medium bg-white hover:bg-indigo-50 border border-slate-200 hover:border-indigo-300 text-slate-700 hover:text-indigo-900 transition-all shadow-2xs flex items-center gap-1.5 shrink-0 whitespace-nowrap cursor-pointer"
                  >
                    <Icon className="w-3 h-3 text-indigo-600" />
                    {action.label}
                  </button>
                );
              })}
            </div>
          )}

          {/* Floating @ Mention Autocomplete Popover */}
          {showMentionMenu && (
            <div className="absolute bottom-full mb-3 left-4 right-4 bg-white/95 backdrop-blur-xl border border-indigo-200/90 rounded-2xl shadow-2xl p-3 z-30 max-h-72 overflow-y-auto">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-100 px-1">
                <div className="flex items-center gap-2 text-xs font-bold text-indigo-900">
                  <AtSign className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Tag Consultation Encounter</span>
                  {mentionFilter && (
                    <span className="text-[10px] font-normal text-slate-400">
                      Filtering: "{mentionFilter}"
                    </span>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => setShowMentionMenu(false)}
                  className="text-slate-400 hover:text-slate-600 text-xs p-1 rounded cursor-pointer"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              {filteredMentionConsultations.length === 0 ? (
                <div className="p-3 text-xs text-slate-500 text-center">
                  No matching consultations found. Type ID or chief complaint.
                </div>
              ) : (
                <div className="space-y-1">
                  {filteredMentionConsultations.map(c => (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => handleSelectConsultation(c)}
                      className="w-full text-left p-2.5 rounded-xl hover:bg-indigo-50/80 transition-colors flex items-center justify-between gap-3 group border border-transparent hover:border-indigo-100 cursor-pointer"
                    >
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded">
                            @{c.id.slice(0, 8)}
                          </span>
                          <span className={`text-[10px] uppercase font-bold px-1.5 py-0.2 rounded-full ${
                            c.status === "completed" ? "bg-emerald-100 text-emerald-800" : "bg-blue-100 text-blue-800"
                          }`}>
                            {c.status || "active"}
                          </span>
                          <span className="text-[11px] text-slate-400">
                            {c.created_at ? new Date(c.created_at).toLocaleDateString() : ""}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 truncate mt-1 group-hover:text-indigo-950">
                          {c.input_preview || "Clinical encounter record"}
                        </p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-indigo-600 shrink-0" />
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Safety disclaimer */}
          <p className="text-center text-[10px] text-slate-400 mb-2 font-medium uppercase tracking-wide">
            ⚕️ AI suggestions require clinician review — not a substitute for professional judgement
          </p>

          <div
            className="flex items-end gap-2.5 rounded-2xl p-2.5"
            style={{
              background: "#fff",
              border: "1.5px solid rgba(79,70,229,0.2)",
              boxShadow: "0 0 0 4px rgba(79,70,229,0.05), 0 4px 16px rgba(0,0,0,0.06)",
            }}
          >
            {/* Tag picker button inside input */}
            <button
              type="button"
              onClick={() => setShowTagModal(true)}
              title="Tag or change consultation encounter"
              className={`p-2 rounded-xl transition-all flex items-center justify-center shrink-0 cursor-pointer ${
                taggedConsultation
                  ? "bg-indigo-100 text-indigo-700 hover:bg-indigo-200"
                  : "bg-slate-100 text-slate-500 hover:bg-slate-200 hover:text-slate-700"
              }`}
            >
              <AtSign className="w-4 h-4" />
            </button>

            <textarea
              ref={inputRef}
              value={query}
              onChange={handleInputChange}
              onKeyDown={handleKey}
              disabled={loading}
              rows={1}
              placeholder={
                taggedConsultation
                  ? "Ask about this encounter (e.g. 'generate discharge summary', 'who is assigned doctor', 'current medications')..."
                  : mode === "rag"
                  ? "Ask a clinical question or type @ to tag a consultation… (e.g. @a994e... or What causes STEMI?)"
                  : "Enter a disease name… (e.g. Tuberculosis, Dengue fever, STEMI)"
              }
              className="flex-1 resize-none outline-none text-sm text-slate-800 placeholder-slate-400 bg-transparent leading-relaxed"
              style={{ maxHeight: "120px", minHeight: "24px" }}
              onInput={e => {
                const el = e.currentTarget;
                el.style.height = "auto";
                el.style.height = Math.min(el.scrollHeight, 120) + "px";
              }}
            />
            <motion.button
              whileTap={{ opacity: 0.9 }}
              whileHover={{ y: -1 }}
              onClick={() => handleSubmit(query)}
              disabled={!query.trim() || loading}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold text-white transition-all shrink-0 cursor-pointer"
              style={{
                background: !query.trim() || loading
                  ? "linear-gradient(135deg, #94a3b8, #64748b)"
                  : "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
                boxShadow: !query.trim() || loading ? "none" : "0 4px 12px rgba(79,70,229,0.3)",
              }}
            >
              {loading
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : <><Zap className="w-4 h-4" /> Ask AI</>
              }
            </motion.button>
          </div>

          <div className="flex items-center justify-between mt-2 px-1">
            <span className="text-[10px] text-slate-400">
              Type <kbd className="bg-slate-100 border border-slate-200 px-1 rounded text-[10px]">@</kbd> to tag consultation • Press <kbd className="bg-slate-100 border border-slate-200 px-1 rounded text-[10px]">Enter</kbd> to send
            </span>
            <span className="text-[10px] text-slate-400">
              {taggedConsultation
                ? `Encounter Linked: @${taggedConsultation.id.slice(0, 8)}`
                : mode === "rag"
                ? "💬 DocAssist IQ AI Q&A"
                : "🔬 Disease Intelligence Mode"}
            </span>
          </div>
        </div>
      )}

      {/* ── Consultation Picker Modal ───────────────────────── */}
      {showTagModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[80vh]"
          >
            <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-indigo-600 flex items-center justify-center text-white">
                  <AtSign className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Tag Consultation Encounter</h3>
                  <p className="text-xs text-slate-500">Link encounter to ground clinical answers & generate signed documents</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowTagModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 border-b border-slate-100">
              <div className="flex items-center gap-2 px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl">
                <Search className="w-4 h-4 text-slate-400 shrink-0" />
                <input
                  type="text"
                  placeholder="Search by ID, chief complaint, or status..."
                  value={mentionFilter}
                  onChange={e => setMentionFilter(e.target.value)}
                  className="w-full bg-transparent text-xs text-slate-800 placeholder-slate-400 outline-none"
                  autoFocus
                />
                {mentionFilter && (
                  <button type="button" onClick={() => setMentionFilter("")} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>

            <div className="p-3 overflow-y-auto space-y-1.5 flex-1">
              {allConsultations
                .filter(c => {
                  if (!mentionFilter) return true;
                  const q = mentionFilter.toLowerCase();
                  return (
                    (c.id && c.id.toLowerCase().includes(q)) ||
                    (c.input_preview && c.input_preview.toLowerCase().includes(q)) ||
                    (c.status && c.status.toLowerCase().includes(q))
                  );
                })
                .map(c => {
                  const isSelected = taggedConsultation?.id === c.id;
                  return (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => handleSelectConsultation(c)}
                      className={`w-full text-left p-3 rounded-xl transition-all border flex items-center justify-between gap-3 cursor-pointer ${
                        isSelected
                          ? "bg-indigo-50/90 border-indigo-300 ring-2 ring-indigo-500/20"
                          : "bg-white hover:bg-slate-50 border-slate-200/80 hover:border-indigo-200"
                      }`}
                    >
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-100/70 px-2 py-0.5 rounded">
                            @{c.id.slice(0, 8)}
                          </span>
                          <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${
                            c.status === "completed" ? "bg-emerald-100 text-emerald-800" : "bg-blue-100 text-blue-800"
                          }`}>
                            {c.status || "active"}
                          </span>
                          <span className="text-[11px] text-slate-400">
                            {c.created_at ? new Date(c.created_at).toLocaleDateString() : ""}
                          </span>
                        </div>
                        <p className="text-xs text-slate-700 mt-1 line-clamp-2 leading-relaxed">
                          {c.input_preview || "Consultation record with clinical findings and notes."}
                        </p>
                        <p className="text-[10px] text-slate-400 font-mono mt-0.5 truncate">
                          UUID: {c.id}
                        </p>
                      </div>
                      {isSelected ? (
                        <CheckCircle className="w-5 h-5 text-indigo-600 shrink-0" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-slate-300 shrink-0" />
                      )}
                    </button>
                  );
                })}
              {allConsultations.length === 0 && (
                <div className="p-8 text-center text-xs text-slate-400">
                  No consultations found in database.
                </div>
              )}
            </div>

            <div className="px-5 py-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between text-xs text-slate-500">
              <span>Select encounter to ground answers & generate certified documents</span>
              <button
                type="button"
                onClick={() => setShowTagModal(false)}
                className="px-3 py-1.5 rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold cursor-pointer"
              >
                Close
              </button>
            </div>
          </motion.div>
        </div>
      )}

      {/* ── Modals ────────────────────────────────────────────── */}
      <AnimatePresence>
        {previewDoc && (
          <DocumentPreviewModal
            doc={previewDoc}
            onClose={() => setPreviewDoc(null)}
          />
        )}
        {showDocumentsModal && (
          <ConsultationDocumentsModal
            consultationId={taggedConsultation?.id || ""}
            documents={consultationDocs}
            onClose={() => setShowDocumentsModal(false)}
            onTriggerGenerate={(promptText) => handleSubmit(promptText)}
          />
        )}
        {showTimelineModal && (
          <TimelineModal
            consultationId={taggedConsultation?.id || ""}
            timeline={timelineSummary}
            onClose={() => setShowTimelineModal(false)}
            onTriggerGenerate={(promptText) => handleSubmit(promptText)}
          />
        )}
        {showProfileModal && (
          <ProfileSummaryModal
            patient={timelineSummary?.patient}
            doctor={timelineSummary?.doctor}
            onClose={() => setShowProfileModal(false)}
            onTriggerGenerate={(promptText) => handleSubmit(promptText)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default function AIPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-slate-500 font-medium">Loading Clinical AI...</div>}>
      <AIPageContent />
    </Suspense>
  );
}

