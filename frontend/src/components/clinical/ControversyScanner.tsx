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
    <div className="mt-6 border rounded-2xl overflow-hidden bg-[var(--color-danger-50)] border-[var(--color-danger-200)] shadow-sm">
      <button 
        onClick={() => setExpanded(!expanded)}
        className="w-full px-5 py-4 flex items-center justify-between hover:bg-[var(--color-danger-100)] transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 bg-[var(--color-danger-100)] text-[var(--color-danger-700)] rounded-xl shadow-inner border border-[var(--color-danger-200)]">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div className="text-left">
            <span className="block text-base font-bold text-[var(--color-danger-900)]">
              PubMed Alert: Recent Controversies Found
            </span>
            <span className="block text-xs font-semibold text-[var(--color-danger-700)] mt-0.5">
              AI identified conflicting literature for {disease}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="px-3 py-1 rounded-full bg-[var(--color-danger-600)] text-white text-[10px] font-black uppercase tracking-widest shadow-sm">
            {data.articles.length} SOURCES
          </span>
          {expanded ? <ChevronUp className="w-5 h-5 text-[var(--color-danger-500)]" /> : <ChevronDown className="w-5 h-5 text-[var(--color-danger-500)]" />}
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-t border-[var(--color-danger-200)] bg-white/60 backdrop-blur-md"
          >
            <div className="p-5 md:p-6 space-y-6">
              <div className="bg-white p-5 rounded-xl border border-[var(--color-danger-100)] shadow-[var(--shadow-subtle)]">
                <div className="flex items-center gap-2 mb-3">
                  <h4 className="text-xs font-bold text-[var(--color-danger-800)] uppercase tracking-widest">AI Synthesis of Controversy</h4>
                </div>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed font-medium">
                  {data.ai_summary}
                </p>
              </div>

              <div>
                <h4 className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-widest mb-3 px-1">Source Literature</h4>
                <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {data.articles.map((article, i) => (
                    <li key={i} className="flex gap-3 p-4 bg-white hover:bg-[var(--surface-sunken)] border border-[var(--border-subtle)] rounded-xl transition-all group shadow-sm hover:shadow-md">
                      <div className="mt-0.5 p-2 bg-[var(--surface-raised)] border border-[var(--border-default)] rounded-lg flex-shrink-0 h-fit">
                        <BookOpen className="w-4 h-4 text-[var(--text-tertiary)]" />
                      </div>
                      <div>
                        <a href={article.url} target="_blank" rel="noreferrer" className="text-sm font-semibold text-[var(--text-primary)] hover:text-[var(--color-primary-600)] transition-colors flex items-start gap-1.5 leading-tight mb-2">
                          {article.title}
                          <ExternalLink className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 mt-0.5" />
                        </a>
                        <p className="text-xs text-[var(--text-tertiary)] font-medium flex items-center gap-2">
                          <span className="truncate max-w-[120px]">{article.source}</span>
                          <span className="w-1 h-1 rounded-full bg-[var(--border-default)]" />
                          <span>{article.pub_date}</span>
                        </p>
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
