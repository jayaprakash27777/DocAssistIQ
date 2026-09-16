"use client";

import React, { useState, useRef, useEffect } from "react";
import { useToast } from "@/components/shell/ToastProvider";
import { ragQuery, type RAGResponse, type RAGQueryRequest } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, Sparkles, ChevronDown, ChevronUp, Stethoscope, AlertTriangle, Info, ShieldCheck, Search, Activity, BookOpen, Terminal, CheckCircle2 } from "lucide-react";

const LOADING_PHASES = [
  { icon: Search, text: "Vectorizing clinical query..." },
  { icon: BookOpen, text: "Scanning approved medical literature..." },
  { icon: Activity, text: "Cross-referencing knowledge graph..." },
  { icon: ShieldCheck, text: "Synthesizing evidence-based response..." }
];

export default function RAGAssistant() {
  const { toast } = useToast();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState(0);
  const [result, setResult] = useState<RAGResponse | null>(null);
  const [showReasoning, setShowReasoning] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [result, loading, showReasoning, loadingPhase]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (loading) {
      setLoadingPhase(0);
      interval = setInterval(() => {
        setLoadingPhase(prev => (prev < LOADING_PHASES.length - 1 ? prev + 1 : prev));
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    setLoading(true);
    setResult(null);
    setShowReasoning(true);

    const request: RAGQueryRequest = {
      query: query.trim(),
      top_k: 5,
      filters: {
        only_approved: true,
      }
    };

    const res = await ragQuery(request);
    setLoading(false);

    if (res.ok) {
      setResult(res.data);
    } else {
      toast.error(res.error?.message || "Failed to retrieve evidence");
    }
  };

  const parseAnswer = (rawAnswer: string) => {
    const reasoningMatch = rawAnswer.match(/<clinical_reasoning>([\s\S]*?)<\/clinical_reasoning>/);
    const reasoning = reasoningMatch ? reasoningMatch[1].trim() : null;
    const finalAnswer = rawAnswer.replace(/<clinical_reasoning>[\s\S]*?<\/clinical_reasoning>/, '').trim();
    return { reasoning, finalAnswer };
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 relative overflow-hidden font-sans">
      {/* Background Decorators */}
      <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] bg-[var(--color-primary-400)]/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>
      <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-400/10 rounded-full blur-[80px] -z-10 pointer-events-none"></div>
      <div className="absolute inset-0 z-0 opacity-[0.02] pointer-events-none" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '32px 32px' }}></div>

      {/* Premium Header */}
      <div className="px-8 py-5 bg-white/80 backdrop-blur-2xl border-b border-white/50 flex items-center justify-between sticky top-0 z-20 shadow-[0_4px_24px_rgba(0,0,0,0.02)]">
        <div className="flex items-center gap-4">
          <div className="relative flex items-center justify-center w-12 h-12 bg-gradient-to-br from-[var(--color-primary-500)] to-[var(--color-primary-700)] rounded-2xl shadow-lg shadow-[var(--color-primary-500)]/20 overflow-hidden">
            <div className="absolute inset-0 bg-white/20 transform rotate-45 translate-x-[-100%] hover:translate-x-[100%] transition-transform duration-1000"></div>
            <Sparkles className="w-6 h-6 text-white relative z-10" />
          </div>
          <div>
            <h3 className="font-heading font-black text-xl text-slate-800 tracking-tight">Clinical AI HUD</h3>
            <p className="text-xs font-bold uppercase tracking-widest text-[var(--color-primary-600)]">Evidence-Grounded Synthesizer</p>
          </div>
        </div>
        <div className="flex items-center gap-3 bg-white px-4 py-2 rounded-xl shadow-sm border border-slate-100">
          <span className="flex h-2.5 w-2.5 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </span>
          <span className="text-xs uppercase tracking-wider font-bold text-slate-600">RAG Engine Online</span>
        </div>
      </div>

      {/* Main HUD Area */}
      <div className="flex-1 overflow-y-auto p-8 flex flex-col gap-8 relative z-10 custom-scrollbar">
        {!result && !loading && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto"
          >
            <div className="relative w-32 h-32 mb-8">
              <div className="absolute inset-0 bg-[var(--color-primary-500)]/10 rounded-full animate-ping" style={{ animationDuration: '3s' }}></div>
              <div className="absolute inset-4 bg-[var(--color-primary-500)]/20 rounded-full animate-pulse"></div>
              <div className="absolute inset-8 bg-gradient-to-br from-[var(--color-primary-400)] to-[var(--color-primary-600)] rounded-full flex items-center justify-center shadow-2xl shadow-[var(--color-primary-500)]/30">
                <Stethoscope className="w-10 h-10 text-white" />
              </div>
            </div>
            <h4 className="font-heading font-black text-3xl text-slate-800 tracking-tight mb-4">Awaiting Clinical Input</h4>
            <p className="text-slate-500 text-lg leading-relaxed font-medium">
              Initialize a query to scan the knowledge base. The AI will strictly ground its synthesis in approved medical literature.
            </p>
          </motion.div>
        )}

        {/* User Query Banner */}
        <AnimatePresence>
          {(result || loading) && (
            <motion.div 
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200/60 flex items-start gap-5 relative overflow-hidden"
            >
              <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-[var(--color-primary-500)]"></div>
              <div className="w-10 h-10 rounded-full bg-[var(--color-primary-50)] flex items-center justify-center shrink-0">
                <Search className="w-5 h-5 text-[var(--color-primary-600)]" />
              </div>
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">Query Executed</span>
                <p className="text-lg font-bold text-slate-800 leading-relaxed">{result?.query || query}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Dynamic Loading HUD */}
        <AnimatePresence>
          {loading && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95, filter: "blur(10px)" }}
              className="bg-white rounded-3xl p-8 shadow-xl overflow-hidden relative border border-slate-100"
            >
              <div className="absolute top-0 left-0 right-0 h-1 bg-slate-100 overflow-hidden">
                <motion.div 
                  className="h-full bg-[var(--color-primary-500)]"
                  initial={{ width: "0%" }}
                  animate={{ width: `${((loadingPhase + 1) / Object.keys(LOADING_PHASES).length) * 100}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
              
              <div className="flex flex-col gap-6 relative z-10">
                {LOADING_PHASES.map((phase, idx) => {
                  const PhaseIcon = phase.icon;
                  const isActive = idx === loadingPhase;
                  const isDone = idx < loadingPhase;
                  
                  return (
                    <div key={idx} className={`flex items-center gap-4 transition-all duration-500 ${isActive ? 'opacity-100 scale-105 transform origin-left' : isDone ? 'opacity-50' : 'opacity-40'}`}>
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                        isActive ? 'bg-[var(--color-primary-50)] text-[var(--color-primary-600)] border border-[var(--color-primary-200)]' : 
                        isDone ? 'bg-emerald-50 text-emerald-600 border border-emerald-100' : 
                        'bg-slate-50 text-slate-400 border border-slate-100'
                      }`}>
                        {isDone ? <CheckCircle2 className="w-5 h-5" /> : isActive ? <Loader2 className="w-5 h-5 animate-spin" /> : <PhaseIcon className="w-5 h-5" />}
                      </div>
                      <span className={`font-mono text-sm tracking-wide ${isActive ? 'text-[var(--color-primary-700)] font-bold' : isDone ? 'text-emerald-700/70' : 'text-slate-400'}`}>
                        {phase.text}
                      </span>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* AI HUD Results */}
        <AnimatePresence>
          {result && !loading && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col gap-6"
            >
              {result.insufficient_evidence ? (
                <div className="bg-amber-50 border-2 border-amber-200 rounded-3xl p-8 shadow-lg shadow-amber-500/10 flex items-start gap-5">
                  <div className="p-3 bg-amber-100 rounded-2xl shrink-0">
                    <AlertTriangle className="w-8 h-8 text-amber-600" />
                  </div>
                  <div>
                    <h4 className="text-xl font-bold text-amber-900 mb-2">Insufficient Clinical Evidence</h4>
                    <p className="text-amber-800/80 leading-relaxed font-medium">
                      The safety thresholds prevent answering this query. There is not enough approved medical literature within the knowledge base to synthesize a safe, grounded response.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col gap-6">
                  
                  {/* Reasoning Matrix (Dark Mode Terminal) */}
                  {parseAnswer(result.answer).reasoning && (
                    <div className="bg-slate-50 rounded-3xl overflow-hidden shadow-sm border border-slate-200">
                      <button 
                        onClick={() => setShowReasoning(!showReasoning)}
                        className="w-full flex items-center justify-between px-6 py-4 bg-white hover:bg-slate-50 transition-colors border-b border-slate-200 focus:outline-none"
                      >
                        <div className="flex items-center gap-3">
                          <Terminal className="w-5 h-5 text-[var(--color-primary-500)]" />
                          <span className="text-xs font-bold uppercase tracking-widest text-[var(--color-primary-600)]">Clinical Reasoning Matrix</span>
                        </div>
                        {showReasoning ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
                      </button>
                      <AnimatePresence>
                        {showReasoning && (
                          <motion.div 
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="bg-slate-50 relative"
                          >
                            <div className="absolute left-6 top-0 bottom-0 w-px bg-slate-200"></div>
                            <div className="px-12 py-6 text-[13px] font-mono text-slate-600 leading-loose whitespace-pre-wrap">
                              {parseAnswer(result.answer).reasoning?.split('\n').map((line, i) => (
                                <div key={i} className="relative">
                                  <div className="absolute -left-[29px] top-[10px] w-2 h-2 rounded-full bg-slate-300"></div>
                                  <span className="text-[var(--color-primary-400)] font-bold mr-3">❯</span> {line}
                                </div>
                              ))}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  )}

                  {/* Final Synthesis */}
                  <div className="bg-white rounded-3xl p-8 shadow-xl shadow-slate-200/40 border border-slate-200/60 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-[var(--color-primary-500)]/5 rounded-bl-full"></div>
                    <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-[var(--color-primary-500)]" /> AI Synthesis
                    </h4>
                    <div className="prose prose-lg max-w-none text-slate-800 leading-relaxed font-medium whitespace-pre-wrap relative z-10">
                      {parseAnswer(result.answer).finalAnswer}
                    </div>
                  </div>
                  
                  {/* Evidence Nodes */}
                  {result.citations.length > 0 && (
                    <div className="space-y-4">
                      <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2 px-2">
                        <BookOpen className="w-4 h-4" /> Grounding Evidence
                      </h4>
                      <div className="grid grid-cols-1 gap-4">
                        {result.citations.map((cit, idx) => (
                          <motion.div 
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.1 }}
                            key={cit.evidence_id} 
                            className="bg-white/80 backdrop-blur-xl border border-slate-200 p-5 rounded-2xl shadow-sm hover:shadow-md hover:border-blue-300 transition-all group relative overflow-hidden"
                          >
                            <div className="absolute left-0 top-0 bottom-0 w-1 bg-slate-200 group-hover:bg-blue-500 transition-colors"></div>
                            <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                              <div className="flex-1">
                                <div className="flex items-center gap-3 mb-2">
                                  <span className="flex items-center justify-center w-6 h-6 rounded-full bg-slate-100 text-xs font-bold text-slate-500 group-hover:bg-blue-100 group-hover:text-blue-700 transition-colors">
                                    {idx + 1}
                                  </span>
                                  <span className="font-bold text-slate-800 group-hover:text-blue-700 transition-colors">
                                    {cit.source_name}
                                  </span>
                                </div>
                                <p className="text-slate-600 text-sm leading-relaxed ml-9 relative before:content-[''] before:absolute before:-left-3 before:top-2 before:w-1 before:h-1 before:bg-slate-300 before:rounded-full">
                                  "{cit.claim}"
                                </p>
                              </div>
                              <div className="flex flex-col items-end gap-2 shrink-0">
                                {cit.evidence_grade && (
                                  <span className="px-3 py-1 text-[10px] font-black uppercase tracking-wider bg-[var(--color-primary-50)] text-[var(--color-primary-700)] rounded-lg border border-[var(--color-primary-200)] shadow-sm">
                                    Grade {cit.evidence_grade}
                                  </span>
                                )}
                                <div className="text-[10px] font-mono text-slate-400 flex flex-col items-end">
                                  <span>{cit.source_code}</span>
                                  {cit.article_doi && <span>DOI: {cit.article_doi}</span>}
                                </div>
                              </div>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
        
        <div ref={messagesEndRef} className="h-4" />
      </div>

      {/* Glassmorphic Input Area */}
      <div className="px-8 pb-8 pt-4 relative z-20">
        <div className="absolute inset-0 bg-gradient-to-t from-slate-50 via-slate-50 to-transparent -z-10 pointer-events-none"></div>
        <form onSubmit={handleSearch} className="relative max-w-5xl mx-auto">
          <div className={`relative bg-white/90 backdrop-blur-2xl border-2 rounded-3xl shadow-2xl transition-all duration-300 overflow-hidden flex items-end p-2 ${loading ? 'border-[var(--color-primary-400)] shadow-[var(--color-primary-500)]/20' : 'border-slate-200 focus-within:border-[var(--color-primary-500)] focus-within:shadow-[var(--color-primary-500)]/20'}`}>
            <textarea
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  if (query.trim() && !loading) {
                    handleSearch(e as unknown as React.FormEvent);
                  }
                }
              }}
              placeholder="Initialize clinical query... (Shift+Enter for new line)"
              className="w-full bg-transparent px-5 py-4 text-base font-medium text-slate-800 placeholder:text-slate-400 focus:outline-none resize-none min-h-[60px] max-h-[200px] custom-scrollbar"
              rows={1}
              style={{ height: "auto", minHeight: "60px" }}
              disabled={loading}
              ref={(el) => {
                if (el) {
                  el.style.height = '60px';
                  const scrollHeight = el.scrollHeight;
                  el.style.height = scrollHeight > 200 ? '200px' : `${scrollHeight}px`;
                }
              }}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="shrink-0 h-[60px] w-[60px] ml-2 bg-[var(--color-primary-600)] text-white rounded-2xl flex items-center justify-center hover:bg-[var(--color-primary-700)] disabled:bg-slate-100 disabled:text-slate-400 disabled:shadow-none shadow-lg shadow-[var(--color-primary-500)]/20 transition-all group focus:outline-none"
            >
              {loading ? (
                <Loader2 className="w-6 h-6 animate-spin text-white" />
              ) : (
                <Send className="w-6 h-6 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
              )}
            </button>
          </div>
          <div className="text-center mt-4 flex items-center justify-center gap-2">
            <ShieldCheck className="w-3.5 h-3.5 text-slate-400" />
            <p className="text-[10px] font-bold tracking-widest uppercase text-slate-400">Decision Support Only • Verify output clinically</p>
          </div>
        </form>
      </div>
    </div>
  );
}

