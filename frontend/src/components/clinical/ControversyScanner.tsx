"use client";

import React, { useState, useEffect } from "react";
import { getPubMedControversy, PubMedScannerResponse } from "@/lib/api";
import { BookOpen, AlertCircle, ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function ControversyScanner({ consultationId, disease }: { consultationId: string, disease: string }) {
  const [data, setData] = useState<PubMedScannerResponse | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const res = await getPubMedControversy(consultationId, disease);
      if (res.ok && res.data.controversy_found) {
        setData(res.data);
      }
      setLoading(false);
    }
    load();
  }, [consultationId, disease]);

  if (loading) {
    return (
      <div className="mt-4 p-3 bg-gray-50  rounded-lg animate-pulse flex items-center gap-3">
        <BookOpen className="w-5 h-5 text-gray-400" />
        <span className="text-sm text-gray-500 font-medium">Scanning PubMed for controversies...</span>
      </div>
    );
  }

  if (!data || !data.controversy_found) return null;

  return (
    <div className="mt-6 border rounded-3xl overflow-hidden glass-panel-4k gpu-accelerated border-rose-200/90 bg-rose-50/70 shadow-[0_16px_40px_rgba(244,63,94,0.08),inset_0_1px_0_rgba(255,255,255,0.9)]">
      <button 
        onClick={() => setExpanded(!expanded)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-rose-100/50 transition-colors text-left"
      >
        <div className="flex items-center gap-3.5">
          <div className="p-2.5 bg-gradient-to-br from-rose-500 to-red-600 text-white rounded-2xl shadow-md shadow-rose-500/30 ring-1 ring-white/30">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="block text-base font-bold text-slate-900 tracking-tight">
                PubMed Alert: Recent Controversies Found
              </span>
            </div>
            <span className="block text-xs font-semibold text-rose-700 mt-0.5">
              AI identified conflicting or debated clinical literature for <span className="underline decoration-rose-300 font-bold">{disease}</span>
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-3 py-1 rounded-full bg-rose-600 text-white text-[10px] font-black uppercase tracking-widest shadow-md">
            {data.articles.length} SOURCES
          </span>
          <div className="w-7 h-7 rounded-xl bg-white/60 border border-rose-200/80 flex items-center justify-center text-rose-600 shadow-sm">
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-t border-rose-200/80 bg-white/75 backdrop-blur-xl"
          >
            <div className="p-6 space-y-6">
              <div className="bg-white/95 p-5 rounded-2xl border border-rose-200/80 shadow-sm ring-1 ring-black/5">
                <div className="flex items-center gap-2 mb-2.5">
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                  <h4 className="text-xs font-black text-rose-800 uppercase tracking-wider m-0">AI Synthesis of Clinical Controversy</h4>
                </div>
                <p className="text-sm text-slate-700 leading-relaxed font-normal m-0">
                  {data.ai_summary}
                </p>
              </div>

              <div>
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 px-1">Indexed Source Literature</h4>
                <ul className="grid grid-cols-1 md:grid-cols-2 gap-3.5 list-none p-0 m-0">
                  {data.articles.map((article, i) => (
                    <li key={i} className="flex gap-3.5 p-4 bg-white hover:bg-slate-50 border border-slate-200/90 rounded-2xl transition-all group shadow-sm hover:shadow-md hover:-translate-y-0.5">
                      <div className="mt-0.5 p-2.5 bg-slate-100 border border-slate-200 rounded-xl flex-shrink-0 h-fit text-slate-500 group-hover:text-indigo-600 group-hover:bg-indigo-50 transition-colors">
                        <BookOpen className="w-4 h-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <a href={article.url} target="_blank" rel="noreferrer" className="text-sm font-bold text-slate-900 hover:text-indigo-600 transition-colors flex items-start gap-1.5 leading-snug mb-2 no-underline">
                          <span className="line-clamp-2">{article.title}</span>
                          <ExternalLink className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 mt-0.5 text-indigo-600" />
                        </a>
                        <div className="text-xs text-slate-400 font-medium flex items-center gap-2">
                          <span className="truncate max-w-[140px] font-semibold text-slate-500">{article.source}</span>
                          <span className="w-1 h-1 rounded-full bg-slate-300" />
                          <span>{article.pub_date}</span>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
