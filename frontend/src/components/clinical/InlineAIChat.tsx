/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * InlineAIChat — Compact AI Q&A box for inside the Consultation page.
 *
 * - Asks clinical questions via RAG (POST /api/v1/rag/query)
 * - Shows answer inline with confidence, citations count
 * - Can also ask questions in context of the current consultation
 * - Compact design so it doesn't overwhelm the consultation layout
 */
"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles, Send, Loader2, ChevronDown, ChevronUp,
  Copy, Check, BookOpen, AlertTriangle, Zap
} from "lucide-react";
import { ragQuery, getStoredToken, askConsultationNotes, askDoctorNotesGeneral } from "@/lib/api";
import { useToast } from "@/components/shell/ToastProvider";

const CONSULTATION_QUICK_ASKS = [
  "Summarize all findings & vitals from this note",
  "Generate official e-prescription with digital signature",
  "Generate certified discharge summary with digital signature",
  "What are the red flags and contraindications in this note?",
  "Check current medications, allergies & interactions",
  "What is the differential diagnosis for this presentation?",
  "Suggest first-line investigations for these symptoms",
];

interface InlineAIChatProps {
  consultationId: string;
  notes?: string;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "error";
  content: string;
  citations?: any[];
  confidence?: number;
  fallback?: boolean;
  note_grounded?: boolean;
  model_used?: string;
  structured_entities?: {
    symptoms?: string[];
    vitals?: Record<string, any>;
    medications?: string[];
    allergies?: string[];
    diagnoses?: string[];
    red_flags?: string[];
  };
}

const LOADING_STEPS = [
  "Reading & grounding in doctor notes…",
  "Analyzing medical knowledge base & guidelines…",
  "Evaluating differential reasoning & red flags…",
  "Compiling evidence-grounded clinical response…",
];

export default function InlineAIChat({ consultationId, notes }: InlineAIChatProps) {
  const { toast } = useToast();
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(true);
  const [showQuickAsks, setShowQuickAsks] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!loading) {
      setLoadingStep(0);
      return;
    }
    const t1 = setTimeout(() => setLoadingStep(1), 2000);
    const t2 = setTimeout(() => setLoadingStep(2), 6000);
    const t3 = setTimeout(() => setLoadingStep(3), 12000);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [loading]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleCopy = async (id: string, text: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  const handleAsk = useCallback(async (q: string) => {
    const trimmed = q.trim();
    if (!trimmed || loading) return;

    setQuery("");
    setShowQuickAsks(false);

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      // 1. Try authenticated consultation grounded notes Q&A
      const token = getStoredToken();
      let d: any = null;

      if (consultationId) {
        const qaRes = await askConsultationNotes(consultationId, {
          query: trimmed,
          notes: notes,
          top_k: 5,
        });
        if (qaRes.ok) {
          d = qaRes.data;
        }
      }

      // 2. If not answered yet, try direct doctor notes endpoint
      if (!d) {
        const generalRes = await askDoctorNotesGeneral(trimmed, notes, consultationId);
        if (generalRes.ok) {
          d = generalRes.data;
        }
      }

      // 3. Fallback to standard RAG query
      if (!d) {
        const ragRes = await ragQuery({
          query: trimmed,
          top_k: 5,
          filters: { only_approved: false },
          consultation_id: consultationId,
        });
        if (ragRes.ok) {
          d = ragRes.data;
        } else {
          setMessages(prev => [
            ...prev,
            {
              id: crypto.randomUUID(),
              role: "error" as const,
              content: ragRes.error?.message || "AI query failed. Please check connection.",
            },
          ]);
          return;
        }
      }

      if (d) {
        setMessages(prev => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: "assistant" as const,
            content: d.answer || "No answer returned.",
            citations: d.citations || [],
            confidence: d.confidence_score ?? d.confidence ?? 0.85,
            fallback: d.fallback_used ?? false,
            note_grounded: d.note_grounded ?? true,
            model_used: d.model_used,
            structured_entities: d.structured_entities,
          },
        ]);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unexpected error. Please try again.";
      setMessages(prev => [
        ...prev,
        { id: crypto.randomUUID(), role: "error" as const, content: msg },
      ]);
    } finally {
      setLoading(false);
    }
  }, [loading, consultationId, notes]);


  const handleKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAsk(query);
    }
  };

  const confBadge = (score: number) => {
    if (score >= 0.8) return { bg: "#dcfce7", text: "#15803d", label: "High" };
    if (score >= 0.6) return { bg: "#fef9c3", text: "#a16207", label: "Medium" };
    return { bg: "#fee2e2", text: "#b91c1c", label: "Low" };
  };

  return (
    <div
      className="rounded-3xl overflow-hidden mb-6 border border-indigo-200/80 bg-gradient-to-br from-blue-50/70 via-white/95 to-indigo-50/70 shadow-[0_12px_36px_rgba(79,70,229,0.08),inset_0_1px_0_rgba(255,255,255,0.95)] backdrop-blur-2xl"
    >
      {/* Header */}
      <div
        className="px-6 py-4 flex items-center justify-between bg-gradient-to-r from-indigo-600 via-indigo-700 to-purple-600 shadow-sm"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-white/20 flex items-center justify-center shadow-xs">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-white leading-none tracking-wide">Clinical AI Assistant</h3>
            <p className="text-[10px] text-indigo-100/90 mt-0.5 font-medium">Evidence-grounded answers — ask anything</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Live indicator */}
          <div className="flex items-center gap-1.5 bg-white/20 px-3 py-1 rounded-full border border-white/25">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[10px] text-white font-extrabold tracking-wider">RAG ONLINE</span>
          </div>
          {messages.length > 0 && (
            <button
              onClick={() => setShowHistory(v => !v)}
              className="text-white/80 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors"
            >
              {showHistory ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>

      {/* Chat history */}
      <AnimatePresence>
        {showHistory && messages.length > 0 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="px-5 py-4 space-y-3.5 max-h-80 overflow-y-auto">
              {messages.map(msg => (
                <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "gap-3"}`}>
                  {msg.role !== "user" && (
                    <div
                      className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 mt-0.5 shadow-sm"
                      style={{ background: msg.role === "error" ? "#fef2f2" : "linear-gradient(135deg, #4f46e5, #7c3aed)" }}
                    >
                      {msg.role === "error"
                        ? <AlertTriangle className="w-4 h-4 text-red-500" />
                        : <Sparkles className="w-4 h-4 text-white" />
                      }
                    </div>
                  )}
                  <div className={`max-w-[85%] ${msg.role === "user" ? "ml-auto" : ""}`}>
                    {msg.role === "user" ? (
                      <div
                        className="px-4 py-3 rounded-2xl rounded-tr-sm text-sm font-medium text-white shadow-md shadow-indigo-500/15"
                        style={{ background: "linear-gradient(135deg, #4f46e5, #7c3aed)" }}
                      >
                        {msg.content}
                      </div>
                    ) : (
                      <div
                        className="rounded-2xl rounded-tl-sm px-4 py-3 shadow-xs"
                        style={{
                          background: msg.role === "error" ? "#fef2f2" : "#fff",
                          border: `1px solid ${msg.role === "error" ? "#fecaca" : "rgba(0,0,0,0.08)"}`,
                        }}
                      >
                        {/* Meta row */}
                        {msg.role === "assistant" && (
                          <div className="flex flex-wrap items-center gap-2 mb-2">
                            {msg.note_grounded && (
                              <span className="text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full font-bold flex items-center gap-1">
                                <Check className="w-2.5 h-2.5" /> Note-Grounded
                              </span>
                            )}
                            {msg.confidence !== undefined && msg.confidence > 0 && (() => {
                              const badge = confBadge(msg.confidence!);
                              return (
                                <span
                                  className="text-[10px] px-1.5 py-0.5 rounded font-semibold"
                                  style={{ background: badge.bg, color: badge.text }}
                                >
                                  {badge.label} confidence
                                </span>
                              );
                            })()}
                            {msg.fallback && (
                              <span className="text-[10px] bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded font-semibold">
                                Static KB
                              </span>
                            )}
                            {(Array.isArray(msg.citations) ? msg.citations.length : (msg.citations ?? 0)) > 0 && (
                              <span className="text-[10px] text-slate-500 font-medium flex items-center gap-1">
                                <BookOpen className="w-3 h-3 text-indigo-500" />
                                {Array.isArray(msg.citations) ? msg.citations.length : msg.citations} source{(Array.isArray(msg.citations) ? msg.citations.length : msg.citations) !== 1 ? "s" : ""}
                              </span>
                            )}
                            <button
                              onClick={() => handleCopy(msg.id, msg.content)}
                              className="ml-auto text-slate-300 hover:text-slate-500 transition-colors"
                            >
                              {copiedId === msg.id
                                ? <Check className="w-3.5 h-3.5 text-emerald-500" />
                                : <Copy className="w-3.5 h-3.5" />
                              }
                            </button>
                          </div>
                        )}
                        <p className={`text-sm leading-relaxed ${msg.role === "error" ? "text-red-700" : "text-slate-800"}`}>
                          {msg.content}
                        </p>

                        {/* Extracted Structured Entities Pills */}
                        {msg.structured_entities && (
                          <div className="flex flex-wrap gap-1 mt-2.5 pt-2 border-t border-slate-100">
                            {msg.structured_entities.red_flags?.map((rf, i) => (
                              <span key={`rf-${i}`} className="text-[9px] px-2 py-0.5 rounded-md bg-red-50 text-red-700 border border-red-200 font-bold">
                                🚨 {rf}
                              </span>
                            ))}
                            {msg.structured_entities.symptoms?.slice(0, 5).map((s, i) => (
                              <span key={`sym-${i}`} className="text-[9px] px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200 font-medium">
                                {s}
                              </span>
                            ))}
                            {msg.structured_entities.medications?.slice(0, 4).map((m, i) => (
                              <span key={`med-${i}`} className="text-[9px] px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 border border-purple-200 font-medium">
                                💊 {m}
                              </span>
                            ))}
                            {msg.structured_entities.vitals && Object.keys(msg.structured_entities.vitals).length > 0 && (
                              <span className="text-[9px] px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200 font-medium">
                                🩺 {Object.entries(msg.structured_entities.vitals).map(([k, v]) => `${k.toUpperCase()}: ${v}`).join(" | ")}
                              </span>
                            )}
                          </div>
                        )}

                        {/* Verifiable Citations */}
                        {Array.isArray(msg.citations) && msg.citations.length > 0 && (
                          <div className="mt-2.5 pt-2 border-t border-slate-100 flex flex-wrap gap-1.5">
                            {msg.citations.map((c, i) => (
                              <span
                                key={i}
                                className="text-[9px] px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200 font-semibold"
                                title={c.excerpt || c.label}
                              >
                                📌 {c.label || c.source_type}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Loading */}
              {loading && (
                <div className="flex gap-2.5">
                  <div
                    className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0"
                    style={{ background: "linear-gradient(135deg, #4f46e5, #7c3aed)" }}
                  >
                    <Sparkles className="w-3.5 h-3.5 text-white" />
                  </div>
                  <div
                    className="px-3.5 py-3 rounded-xl flex items-center gap-2"
                    style={{ background: "#fff", border: "1px solid rgba(0,0,0,0.07)" }}
                  >
                    <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
                    <span className="text-sm text-slate-500 transition-all duration-300">
                      {LOADING_STEPS[loadingStep]}
                    </span>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Quick-ask chips */}
      <AnimatePresence>
        {showQuickAsks && messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="px-5 pt-3.5 pb-2 flex flex-wrap gap-2"
          >
            {CONSULTATION_QUICK_ASKS.map((q, i) => (
              <button
                key={i}
                onClick={() => handleAsk(q)}
                disabled={loading}
                className="text-xs px-3.5 py-1.5 rounded-full font-bold transition-colors shadow-2xs border border-indigo-200 bg-indigo-50 hover:bg-indigo-100 text-indigo-800"
              >
                {q}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input bar */}
      <div className="px-5 pb-5 pt-3">
        <div
          className="flex items-center gap-2.5 rounded-2xl px-4 py-2.5 bg-white border border-indigo-200/80 shadow-[0_2px_8px_rgba(99,102,241,0.06)] focus-within:ring-4 focus-within:ring-indigo-100 focus-within:border-indigo-500 transition-all"
        >
          <Zap className="w-4 h-4 text-indigo-500 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKey}
            disabled={loading}
            placeholder="Ask a clinical question… (e.g. Red flags for this presentation?)"
            className="flex-1 text-sm font-medium text-slate-800 placeholder-slate-400 bg-transparent outline-none"
          />
          <button
            type="button"
            onClick={() => handleAsk(query)}
            disabled={!query.trim() || loading}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white shrink-0 transition-colors shadow-sm disabled:opacity-50"
            style={{
              background: !query.trim() || loading
                ? "#94a3b8"
                : "linear-gradient(135deg, #4f46e5, #7c3aed)",
            }}
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
            {loading ? "Thinking…" : "Ask"}
          </button>
        </div>
        <p className="text-[11px] font-medium text-slate-400 mt-2 text-center">
          ⚕️ AI suggestions require clinician review — decision-support only
        </p>
      </div>
    </div>
  );
}
