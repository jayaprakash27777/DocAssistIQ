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
      <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg animate-pulse flex items-center gap-3">
        <BookOpen className="w-5 h-5 text-gray-400" />
        <span className="text-sm text-gray-500 font-medium">Scanning PubMed for controversies...</span>
      </div>
    );
  }

  if (!data || !data.controversy_found) return null;

  return (
    <div className="mt-4 border rounded-xl overflow-hidden bg-rose-50/50 dark:bg-rose-950/20 border-rose-200 dark:border-rose-900/50">
      <button 
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-rose-100/50 dark:hover:bg-rose-900/40 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="p-1.5 bg-rose-100 text-rose-600 dark:bg-rose-900 dark:text-rose-300 rounded-lg">
            <AlertCircle className="w-4 h-4" />
          </div>
          <span className="text-sm font-bold text-rose-900 dark:text-rose-200">
            PubMed Alert: Recent Controversies Found
          </span>
          <span className="px-2 py-0.5 rounded-full bg-rose-200 text-rose-800 dark:bg-rose-800 dark:text-rose-200 text-[10px] font-bold">
            {data.articles.length} ARTICLES
          </span>
        </div>
        {expanded ? <ChevronUp className="w-4 h-4 text-rose-500" /> : <ChevronDown className="w-4 h-4 text-rose-500" />}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: "auto" }}
            exit={{ height: 0 }}
            className="overflow-hidden border-t border-rose-200 dark:border-rose-900/50"
          >
            <div className="p-4 space-y-4">
              <div className="bg-white dark:bg-gray-900 p-3 rounded-lg border border-rose-100 dark:border-rose-900/50 shadow-sm">
                <h4 className="text-xs font-bold text-rose-800 dark:text-rose-400 uppercase tracking-wider mb-2">AI Summary of Controversy</h4>
                <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed font-medium">
                  {data.ai_summary}
                </p>
              </div>

              <div>
                <h4 className="text-xs font-bold text-rose-800 dark:text-rose-400 uppercase tracking-wider mb-2 px-1">Source Literature</h4>
                <ul className="space-y-2">
                  {data.articles.map((article, i) => (
                    <li key={i} className="flex gap-3 p-2 hover:bg-rose-100/30 dark:hover:bg-rose-900/20 rounded-lg transition-colors group">
                      <BookOpen className="w-4 h-4 text-rose-400 dark:text-rose-600 mt-1 flex-shrink-0" />
                      <div>
                        <a href={article.url} target="_blank" rel="noreferrer" className="text-sm font-semibold text-rose-900 dark:text-rose-200 hover:underline flex items-center gap-1 leading-tight">
                          {article.title}
                          <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </a>
                        <p className="text-xs text-rose-700 dark:text-rose-400 mt-1 font-medium">
                          {article.source} • {article.pub_date}
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
