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

import React, { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain, Send, Loader2, Sparkles, AlertTriangle, BookOpen,
  Copy, Check, ChevronDown, ChevronUp, Zap, Search,
  ShieldCheck, Activity, Stethoscope, Pill, FlaskConical,
  RefreshCw, Info, CheckCircle2, Clock
} from "lucide-react";
import { ragQuery, getDiseaseIntelligence, type RAGResponse, type DiseaseIntelligenceResponse } from "@/lib/api";
import { useToast } from "@/components/shell/ToastProvider";

// ── Constants ─────────────────────────────────────────────────────

const QUICK_ASKS = [
  { icon: Stethoscope, label: "Chest pain DDx", query: "What are the differential diagnoses for acute chest pain with radiation to left arm?" },
  { icon: Pill, label: "Antibiotic choice", query: "What is the first-line antibiotic for community-acquired pneumonia in an adult without comorbidities?" },
  { icon: FlaskConical, label: "Lab interpretation", query: "How do I interpret a high D-dimer with a normal troponin in a chest pain patient?" },
  { icon: Activity, label: "ECG findings", query: "What are the ECG findings in ST-elevation myocardial infarction (STEMI)?" },
  { icon: AlertTriangle, label: "Red flags", query: "What are the red flag symptoms in a patient presenting with headache that require urgent investigation?" },
  { icon: Brain, label: "Neurological exam", query: "How do I assess for signs of meningitis on clinical examination?" },
];

const LOADING_PHASES = [
  { icon: Search, text: "Searching PubMed & clinical KB…" },
  { icon: BookOpen, text: "Retrieving MedlinePlus evidence…" },
  { icon: Activity, text: "Cross-referencing clinical data…" },
  { icon: ShieldCheck, text: "Synthesizing answer…" },
];

// ── Types ─────────────────────────────────────────────────────────

type QueryMode = "rag" | "disease";

interface Message {
  id: string;
  role: "user" | "assistant" | "error";
  content: string;
  ragData?: RAGResponse;
  diseaseData?: DiseaseIntelligenceResponse;
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

function AssistantMessage({ msg }: { msg: Message }) {
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
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 28 }}
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
              <span className="text-xs font-bold text-indigo-600">Clinical AI</span>
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

// ── Main page ─────────────────────────────────────────────────────

export default function AIPage() {
  const { toast } = useToast();
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState(0);
  const [isLongRunning, setIsLongRunning] = useState(false);
  const [mode, setMode] = useState<QueryMode>("rag");
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

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

  const handleSubmit = useCallback(async (q: string) => {
    const trimmed = q.trim();
    if (!trimmed || loading) return;

    setQuery("");
    inputRef.current?.focus();

    // Add user message
    addMessage({ role: "user", content: trimmed });
    setLoading(true);

    // Helper: call public /ai/ask (no auth needed, uses real-time medical engine)
    const askPublic = async (q: string) => {
      const rawUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const rootUrl = rawUrl.replace(/\/api\/v1\/?$/, "");
      const askUrl = `${rootUrl}/ai/ask`;
      const resp = await fetch(askUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, top_k: 5 }),
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
  }, [loading, mode, addMessage]);


  const handleKey = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(query);
    }
  }, [query, handleSubmit]);

  const PhaseIcon = LOADING_PHASES[loadingPhase].icon;

  return (
    <div className="flex flex-col h-[calc(100vh-72px)] overflow-hidden">

      {/* ── Premium Header ─────────────────────────────────── */}
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
            <h1 className="text-lg font-bold text-slate-900 leading-none">Clinical AI Intelligence</h1>
            <p className="text-xs text-slate-500 mt-0.5">Evidence-grounded answers from the clinical knowledge base</p>
          </div>
        </div>

        {/* Mode toggle */}
        <div className="flex items-center gap-2">
          <div
            className="flex items-center p-1 rounded-xl gap-1"
            style={{ background: "rgba(0,0,0,0.05)", border: "1px solid rgba(0,0,0,0.08)" }}
          >
            {(["rag", "disease"] as QueryMode[]).map(m => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
                style={{
                  background: mode === m ? "#fff" : "transparent",
                  color: mode === m ? "#4f46e5" : "#64748b",
                  boxShadow: mode === m ? "0 1px 4px rgba(0,0,0,0.1)" : "none",
                }}
              >
                {m === "rag" ? "💬 Q&A Mode" : "🔬 Disease Mode"}
              </button>
            ))}
          </div>

          {/* Clear chat */}
          {messages.length > 0 && (
            <button
              onClick={() => setMessages([])}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all"
              style={{ background: "rgba(0,0,0,0.05)", color: "#64748b", border: "1px solid rgba(0,0,0,0.08)" }}
            >
              <RefreshCw className="w-3.5 h-3.5" /> New Chat
            </button>
          )}
        </div>
      </div>

      {/* ── Chat area ──────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">

        {/* Empty state */}
        {messages.length === 0 && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4"
          >
            <motion.div
              animate={{ scale: [1, 1.04, 1] }}
              transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
              className="w-20 h-20 rounded-3xl flex items-center justify-center mb-6"
              style={{
                background: "linear-gradient(135deg, #eff6ff 0%, #f5f3ff 100%)",
                border: "1px solid rgba(99,102,241,0.15)",
                boxShadow: "0 8px 32px rgba(99,102,241,0.12)",
              }}
            >
              <Brain className="w-9 h-9 text-indigo-500" />
            </motion.div>
            <h2 className="text-2xl font-bold text-slate-800 mb-2">Ask the Clinical AI</h2>
            <p className="text-sm text-slate-500 mb-8 max-w-sm leading-relaxed">
              {mode === "rag"
                ? "Ask any clinical question — differentials, drug choices, investigations, red flags, guidelines."
                : "Enter a disease name to get a full 20+ field clinical intelligence profile."}
            </p>

            {/* Quick-ask grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 w-full max-w-2xl">
              {QUICK_ASKS.map(({ icon: Icon, label, query: q }, i) => (
                <motion.button
                  key={i}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleSubmit(q)}
                  disabled={loading}
                  className="flex items-center gap-2.5 px-3.5 py-3 rounded-xl text-left text-sm font-semibold transition-all min-h-[52px]"
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
          </motion.div>
        )}

        {/* Messages */}
        <AnimatePresence initial={false}>
          {messages.map(msg => {
            if (msg.role === "user") {
              return (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 8, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
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
            return <AssistantMessage key={msg.id} msg={msg} />;
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
      </div>

      {/* ── Input bar ──────────────────────────────────────── */}
      <div
        className="px-4 py-4 shrink-0"
        style={{
          background: "rgba(248,250,252,0.95)",
          backdropFilter: "blur(20px)",
          borderTop: "1px solid rgba(0,0,0,0.07)",
        }}
      >
        {/* Safety disclaimer */}
        <p className="text-center text-[10px] text-slate-400 mb-3 font-medium uppercase tracking-wide">
          ⚕️ AI suggestions require clinician review — not a substitute for professional judgement
        </p>

        <div
          className="flex items-end gap-3 rounded-2xl p-3"
          style={{
            background: "#fff",
            border: "1.5px solid rgba(79,70,229,0.2)",
            boxShadow: "0 0 0 4px rgba(79,70,229,0.05), 0 4px 16px rgba(0,0,0,0.06)",
          }}
        >
          <textarea
            ref={inputRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKey}
            disabled={loading}
            rows={1}
            placeholder={
              mode === "rag"
                ? "Ask a clinical question… (e.g. What are the causes of elevated troponin?)"
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
            whileTap={{ scale: 0.92 }}
            whileHover={{ scale: 1.05 }}
            onClick={() => handleSubmit(query)}
            disabled={!query.trim() || loading}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold text-white transition-all shrink-0"
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
            Press <kbd className="bg-slate-100 border border-slate-200 px-1 rounded text-[10px]">Enter</kbd> to send, <kbd className="bg-slate-100 border border-slate-200 px-1 rounded text-[10px]">Shift+Enter</kbd> for new line
          </span>
          <span className="text-[10px] text-slate-400">
            {mode === "rag" ? "💬 RAG Mode — Clinical Q&A" : "🔬 Disease Mode — Full profile"}
          </span>
        </div>
      </div>
    </div>
  );
}
