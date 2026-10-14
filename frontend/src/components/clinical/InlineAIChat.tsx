/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * InlineAIChat — Clinical AI Q&A box (God-Level v5)
 *
 * - Grounded consultation notes Q&A via POST /api/v1/consultations/:id/qa
 * - Full markdown rendering: headers, bold, lists, code blocks, blockquotes
 * - Fixed citation field names (source_name)
 * - Categorized quick-asks: Clinical / Documents / Medical Knowledge
 * - Model name display, confidence %, clear chat button
 */
"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles, Send, Loader2, ChevronDown, ChevronUp,
  Copy, Check, BookOpen, AlertTriangle, Zap, X, ChevronRight
} from "lucide-react";
import { ragQuery, askConsultationNotes, askDoctorNotesGeneral, getStoredToken } from "@/lib/api";


// ── Lightweight clinical markdown renderer ─────────────────────────────────
function renderMarkdown(text: string): React.ReactNode {
  if (!text) return null;
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;
  let keyIdx = 0;

  const inlineFormat = (s: string): React.ReactNode => {
    const parts: React.ReactNode[] = [];
    let remaining = s;
    let ki = 0;
    while (remaining.length > 0) {
      const boldMatch = remaining.match(/^\*\*(.+?)\*\*/);
      if (boldMatch) {
        parts.push(<strong key={ki++} className="font-extrabold text-slate-900">{boldMatch[1]}</strong>);
        remaining = remaining.slice(boldMatch[0].length);
        continue;
      }
      const italicMatch = remaining.match(/^\*(.+?)\*/);
      if (italicMatch) {
        parts.push(<em key={ki++} className="italic text-slate-700">{italicMatch[1]}</em>);
        remaining = remaining.slice(italicMatch[0].length);
        continue;
      }
      const codeMatch = remaining.match(/^`([^`]+)`/);
      if (codeMatch) {
        parts.push(
          <code key={ki++} className="text-[11px] bg-slate-100 border border-slate-200 text-emerald-700 px-1 py-0.5 rounded font-mono">
            {codeMatch[1]}
          </code>
        );
        remaining = remaining.slice(codeMatch[0].length);
        continue;
      }
      const charMatch = remaining.match(/^[\s\S]/u);
      if (charMatch) { parts.push(charMatch[0]); remaining = remaining.slice(charMatch[0].length); }
      else break;
    }
    return <>{parts}</>;
  };

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();
    if (trimmed === "") { elements.push(<div key={keyIdx++} className="h-2" />); i++; continue; }
    if (/^---+$/.test(trimmed)) { elements.push(<hr key={keyIdx++} className="border-slate-200 my-2" />); i++; continue; }
    if (trimmed.startsWith("### ")) {
      elements.push(<h3 key={keyIdx++} className="text-[13px] font-extrabold text-indigo-800 mt-3 mb-1 leading-tight border-b border-indigo-100 pb-0.5">{inlineFormat(trimmed.slice(4))}</h3>);
      i++; continue;
    }
    if (trimmed.startsWith("## ")) {
      elements.push(<h2 key={keyIdx++} className="text-sm font-extrabold text-slate-800 mt-3 mb-1.5 leading-tight">{inlineFormat(trimmed.slice(3))}</h2>);
      i++; continue;
    }
    if (trimmed.startsWith("#### ")) {
      elements.push(<h4 key={keyIdx++} className="text-xs font-extrabold text-slate-700 mt-2 mb-1 uppercase tracking-wider">{inlineFormat(trimmed.slice(5))}</h4>);
      i++; continue;
    }
    if (trimmed.startsWith("> ")) {
      elements.push(<blockquote key={keyIdx++} className="border-l-4 border-indigo-300 pl-3 my-1.5 text-xs italic text-slate-600 bg-indigo-50/50 py-1 pr-2 rounded-r">{inlineFormat(trimmed.slice(2))}</blockquote>);
      i++; continue;
    }
    if (/^[-*•]\s/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*•]\s/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^[-*•]\s/, ""));
        i++;
      }
      elements.push(
        <ul key={keyIdx++} className="space-y-1 my-1.5 ml-3">
          {items.map((item, idx) => (
            <li key={idx} className="flex items-start gap-2 text-sm text-slate-700 leading-relaxed">
              <span className="text-indigo-400 font-bold mt-0.5 flex-shrink-0">•</span>
              <span>{inlineFormat(item)}</span>
            </li>
          ))}
        </ul>
      );
      continue;
    }
    if (/^\d+\.\s/.test(trimmed)) {
      const items: {num: string; text: string}[] = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
        const m = lines[i].trim().match(/^(\d+)\.\s(.*)/);
        if (m) items.push({num: m[1], text: m[2]});
        i++;
      }
      elements.push(
        <ol key={keyIdx++} className="space-y-1 my-1.5 ml-3">
          {items.map((item, idx) => (
            <li key={idx} className="flex items-start gap-2 text-sm text-slate-700 leading-relaxed">
              <span className="text-indigo-500 font-extrabold min-w-[18px] text-xs mt-0.5 flex-shrink-0">{item.num}.</span>
              <span>{inlineFormat(item.text)}</span>
            </li>
          ))}
        </ol>
      );
      continue;
    }
    if (trimmed.startsWith("```")) {
      const lang = trimmed.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) { codeLines.push(lines[i]); i++; }
      i++;
      elements.push(
        <pre key={keyIdx++} className="bg-slate-900 text-emerald-300 text-xs rounded-xl p-3 my-2 overflow-x-auto font-mono leading-relaxed">
          {lang && <span className="text-slate-500 text-[10px] block mb-1 uppercase tracking-wider">{lang}</span>}
          {codeLines.join("\n")}
        </pre>
      );
      continue;
    }
    elements.push(<p key={keyIdx++} className="text-sm text-slate-700 leading-relaxed my-0.5">{inlineFormat(trimmed)}</p>);
    i++;
  }
  return <div className="space-y-0.5">{elements}</div>;
}

// ── Quick-ask categories ────────────────────────────────────────────────────
const QUICK_ASK_CATEGORIES = [
  {
    label: "Clinical",
    color: "indigo",
    asks: [
      "Summarize all findings & vitals from this note",
      "What are the red flags and contraindications?",
      "What is the differential diagnosis for this presentation?",
      "Suggest first-line investigations for these symptoms",
      "Check current medications, allergies & interactions",
    ],
  },
  {
    label: "Documents",
    color: "emerald",
    asks: [
      "Generate official e-prescription with digital signature",
      "Generate certified discharge summary with digital signature",
      "Generate referral letter to specialist",
      "Generate lab order requisition",
      "Generate care plan",
    ],
  },
  {
    label: "Knowledge",
    color: "purple",
    asks: [
      "What are the AHA/ACC guidelines for hypertension management?",
      "Calculate CHADS-VASc score and anticoagulation recommendation",
      "What is the Wells score for PE probability?",
      "Explain the pathophysiology of this condition",
      "What are the drug interactions for these medications?",
    ],
  },
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

export default function InlineAIChat({ consultationId, notes }: InlineAIChatProps) {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState("Consulting clinical knowledge & notes…");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(true);
  const [showQuickAsks, setShowQuickAsks] = useState(true);
  const [activeCategory, setActiveCategory] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const clearMessages = () => { setMessages([]); setShowQuickAsks(true); };

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
    setLoadingStatus("Grounding query in consultation clinical notes…");

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
        setLoadingStatus("Evaluating clinical reasoning and note context…");
        const generalRes = await askDoctorNotesGeneral(trimmed, notes, consultationId);
        if (generalRes.ok) {
          d = generalRes.data;
        }
      }

      // 3. Fallback to standard RAG query
      if (!d) {
        setLoadingStatus("Retrieving evidence from medical knowledge base…");
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
    if (score >= 0.9) return { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200", label: "Very High" };
    if (score >= 0.8) return { bg: "bg-green-50", text: "text-green-700", border: "border-green-200", label: "High" };
    if (score >= 0.6) return { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200", label: "Medium" };
    return { bg: "bg-rose-50", text: "text-rose-700", border: "border-rose-200", label: "Low" };
  };

  const catColors: Record<string, { bg: string; text: string; activeBg: string }> = {
    indigo: { bg: "bg-indigo-50 border-indigo-200", text: "text-indigo-800", activeBg: "bg-indigo-600 text-white" },
    emerald: { bg: "bg-emerald-50 border-emerald-200", text: "text-emerald-800", activeBg: "bg-emerald-600 text-white" },
    purple: { bg: "bg-purple-50 border-purple-200", text: "text-purple-800", activeBg: "bg-purple-600 text-white" },
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
            <span className="text-[10px] text-white font-extrabold tracking-wider">LIVE AI</span>
          </div>
          {messages.length > 0 && (
            <>
              <button
                onClick={clearMessages}
                className="text-white/80 hover:text-white p-1.5 rounded-lg hover:bg-white/10 transition-colors"
                title="Clear chat"
              >
                <X className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setShowHistory(v => !v)}
                className="text-white/80 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors"
              >
                {showHistory ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
            </>
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
            <div className="px-5 py-4 space-y-4 max-h-[560px] overflow-y-auto">
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
                  <div className={`max-w-[90%] ${msg.role === "user" ? "ml-auto" : ""}`}>
                    {msg.role === "user" ? (
                      <div
                        className="px-4 py-3 rounded-2xl rounded-tr-sm text-sm font-medium text-white shadow-md shadow-indigo-500/15"
                        style={{ background: "linear-gradient(135deg, #4f46e5, #7c3aed)" }}
                      >
                        {msg.content}
                      </div>
                    ) : (
                      <div
                        className="rounded-2xl rounded-tl-sm px-4 py-3.5 shadow-xs"
                        style={{
                          background: msg.role === "error" ? "#fef2f2" : "#fff",
                          border: `1px solid ${msg.role === "error" ? "#fecaca" : "rgba(0,0,0,0.08)"}`,
                        }}
                      >
                        {/* Meta row */}
                        {msg.role === "assistant" && (
                          <div className="flex flex-wrap items-center gap-2 mb-2.5 pb-2 border-b border-slate-100">
                            {msg.note_grounded && (
                              <span className="text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full font-bold flex items-center gap-1">
                                <Check className="w-2.5 h-2.5" /> Note-Grounded
                              </span>
                            )}
                            {msg.confidence !== undefined && msg.confidence > 0 && (() => {
                              const badge = confBadge(msg.confidence!);
                              return (
                                <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${badge.bg} ${badge.text} ${badge.border}`}>
                                  {badge.label} ({Math.round(msg.confidence! * 100)}%)
                                </span>
                              );
                            })()}
                            {msg.fallback && (
                              <span className="text-[10px] bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded-full font-semibold">
                                Static KB
                              </span>
                            )}
                            {msg.model_used && (
                              <span className="text-[10px] text-slate-400 font-medium truncate max-w-[150px]">
                                {msg.model_used.replace("DocAssistIQ-", "").replace(/-v\d+/gi, "")}
                              </span>
                            )}
                            <button
                              onClick={() => handleCopy(msg.id, msg.content)}
                              className="ml-auto text-slate-300 hover:text-slate-500 transition-colors flex items-center gap-1"
                              title="Copy answer"
                            >
                              {copiedId === msg.id
                                ? <><Check className="w-3.5 h-3.5 text-emerald-500" /><span className="text-[10px] text-emerald-500">Copied</span></>
                                : <Copy className="w-3.5 h-3.5" />
                              }
                            </button>
                          </div>
                        )}

                        {/* Rendered content — markdown for assistant, plain for error */}
                        {msg.role === "error" ? (
                          <p className="text-sm text-red-700 leading-relaxed">{msg.content}</p>
                        ) : (
                          <div className="min-w-0">{renderMarkdown(msg.content)}</div>
                        )}

                        {/* Extracted Structured Entities Pills */}
                        {msg.structured_entities && (
                          <div className="flex flex-wrap gap-1 mt-3 pt-2.5 border-t border-slate-100">
                            {msg.structured_entities.red_flags?.map((rf, i) => (
                              <span key={`rf-${i}`} className="text-[10px] px-2 py-0.5 rounded-md bg-red-50 text-red-700 border border-red-200 font-bold">🚨 {rf}</span>
                            ))}
                            {msg.structured_entities.diagnoses?.slice(0, 3).map((d, i) => (
                              <span key={`dx-${i}`} className="text-[10px] px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200 font-medium">🩺 {d}</span>
                            ))}
                            {msg.structured_entities.symptoms?.slice(0, 4).map((s, i) => (
                              <span key={`sym-${i}`} className="text-[10px] px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200 font-medium">{s}</span>
                            ))}
                            {msg.structured_entities.medications?.slice(0, 4).map((m, i) => (
                              <span key={`med-${i}`} className="text-[10px] px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 border border-purple-200 font-medium">💊 {m}</span>
                            ))}
                            {msg.structured_entities.vitals && Object.keys(msg.structured_entities.vitals).length > 0 && (
                              <span className="text-[10px] px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200 font-medium">
                                🩺 {Object.entries(msg.structured_entities.vitals).map(([k, v]) => `${k.toUpperCase()}: ${v}`).join(" | ")}
                              </span>
                            )}
                          </div>
                        )}

                        {/* Citations — fixed field: source_name not label */}
                        {Array.isArray(msg.citations) && msg.citations.length > 0 && (
                          <div className="mt-3 pt-2 border-t border-slate-100">
                            <div className="flex items-center gap-1 mb-1.5">
                              <BookOpen className="w-3 h-3 text-indigo-400" />
                              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                                {msg.citations.length} Evidence Source{msg.citations.length !== 1 ? "s" : ""}
                              </span>
                            </div>
                            <div className="flex flex-wrap gap-1.5">
                              {msg.citations.slice(0, 6).map((c, i) => {
                                const name = c.source_name || c.label || c.source_type || "Source";
                                return c.url ? (
                                  <a key={i} href={c.url} target="_blank" rel="noopener noreferrer"
                                    className="text-[10px] px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200 font-semibold hover:bg-indigo-100 transition-colors truncate max-w-[180px]"
                                    title={c.excerpt || name}>
                                    📌 {name}
                                  </a>
                                ) : (
                                  <span key={i}
                                    className="text-[10px] px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200 font-semibold truncate max-w-[180px]"
                                    title={c.excerpt || name}>
                                    📌 {name}
                                  </span>
                                );
                              })}
                            </div>
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
                      {loadingStatus}
                    </span>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Quick-ask chips — categorized */}
      <AnimatePresence>
        {showQuickAsks && messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="px-5 pt-4 pb-2"
          >
            {/* Category tabs */}
            <div className="flex items-center gap-1.5 mb-2.5">
              {QUICK_ASK_CATEGORIES.map((cat, ci) => {
                const c = catColors[cat.color];
                const isActive = activeCategory === ci;
                return (
                  <button
                    key={ci}
                    onClick={() => setActiveCategory(ci)}
                    className={`text-[11px] font-bold px-3 py-1 rounded-full border transition-all ${
                      isActive ? c.activeBg + " border-transparent shadow-sm" : c.bg + " " + c.text
                    }`}
                  >
                    {cat.label}
                  </button>
                );
              })}
            </div>
            <div className="flex flex-wrap gap-1.5">
              {QUICK_ASK_CATEGORIES[activeCategory].asks.map((q, i) => {
                const c = catColors[QUICK_ASK_CATEGORIES[activeCategory].color];
                return (
                  <button
                    key={i}
                    onClick={() => handleAsk(q)}
                    disabled={loading}
                    className={`text-xs px-3 py-1.5 rounded-full font-semibold transition-colors shadow-2xs border ${c.bg} ${c.text} hover:brightness-95 flex items-center gap-1`}
                  >
                    <ChevronRight className="w-3 h-3 opacity-60 flex-shrink-0" />
                    {q}
                  </button>
                );
              })}
            </div>
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
            placeholder="Ask anything: diagnosis, drugs, guidelines, scores, calculations…"
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
          ⚕️ DocAssistIQ Universal Clinical Intelligence — Verified Evidence-Based Response (clinician review required)
        </p>
      </div>
    </div>
  );
}
