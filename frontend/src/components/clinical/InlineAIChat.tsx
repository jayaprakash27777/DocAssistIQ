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
import { ragQuery, type RAGResponse } from "@/lib/api";
import { useToast } from "@/components/shell/ToastProvider";

const CONSULTATION_QUICK_ASKS = [
  "What are the red flag symptoms for this presentation?",
  "Suggest first-line investigations for these symptoms",
  "What is the differential diagnosis for fever with rash?",
  "Recommended initial management for acute chest pain?",
];

interface InlineAIChatProps {
  consultationId: string;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "error";
  content: string;
  citations?: number;
  confidence?: number;
  fallback?: boolean;
}

const LOADING_STEPS = [
  "Analyzing medical knowledge base…",
  "Scanning clinical guidelines & trials…",
  "Synthesizing evidence…",
  "Local AI compiling comprehensive response…",
];

export default function InlineAIChat({ consultationId }: InlineAIChatProps) {
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
    const t1 = setTimeout(() => setLoadingStep(1), 3000);
    const t2 = setTimeout(() => setLoadingStep(2), 8000);
    const t3 = setTimeout(() => setLoadingStep(3), 16000);
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
      // Primary: use the public /ai/ask endpoint (no auth issues, works always)
      const rawUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const rootUrl = rawUrl.replace(/\/api\/v1\/?$/, "");
      const askUrl = `${rootUrl}/ai/ask`;
      const resp = await fetch(askUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: trimmed, consultation_id: consultationId, top_k: 5 }),
        signal: AbortSignal.timeout(90000),
      });

      if (resp.ok) {
        const d = await resp.json();
        setMessages(prev => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: "assistant" as const,
            content: d.answer || "No answer returned.",
            citations: d.citations?.length ?? 0,
            confidence: d.confidence_score ?? 0,
            fallback: d.fallback_used ?? false,
          },
        ]);
      } else {
        // Fallback: authenticated RAG query
        const ragRes = await ragQuery({
          query: trimmed,
          top_k: 5,
          filters: { only_approved: false },
          consultation_id: consultationId,
        });
        if (ragRes.ok) {
          const d = ragRes.data;
          setMessages(prev => [
            ...prev,
            {
              id: crypto.randomUUID(),
              role: "assistant" as const,
              content: d.answer || "No answer returned.",
              citations: d.citations?.length ?? 0,
              confidence: d.confidence_score ?? 0,
              fallback: d.fallback_used ?? false,
            },
          ]);
        } else {
          setMessages(prev => [
            ...prev,
            {
              id: crypto.randomUUID(),
              role: "error" as const,
              content: ragRes.error?.message || "AI query failed. Please try again.",
            },
          ]);
        }
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
  }, [loading, consultationId]);


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
                          <div className="flex items-center gap-2 mb-2">
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
                            {(msg.citations ?? 0) > 0 && (
                              <span className="text-[10px] text-slate-400 flex items-center gap-1">
                                <BookOpen className="w-3 h-3" />
                                {msg.citations} source{msg.citations !== 1 ? "s" : ""}
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
                className="text-xs px-3.5 py-1.5 rounded-full font-bold transition-all hover:scale-105 active:scale-95 shadow-xs border border-indigo-200/70 bg-indigo-50/80 hover:bg-indigo-100/80 text-indigo-800"
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
          <motion.button
            whileTap={{ scale: 0.95 }}
            whileHover={{ scale: 1.02 }}
            onClick={() => handleAsk(query)}
            disabled={!query.trim() || loading}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white shrink-0 transition-all shadow-sm"
            style={{
              background: !query.trim() || loading
                ? "#94a3b8"
                : "linear-gradient(135deg, #4f46e5, #7c3aed)",
            }}
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
            {loading ? "Thinking…" : "Ask"}
          </motion.button>
        </div>
        <p className="text-[11px] font-medium text-slate-400 mt-2 text-center">
          ⚕️ AI suggestions require clinician review — decision-support only
        </p>
      </div>
    </div>
  );
}
