"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Activity, Brain } from "lucide-react";

export default function ClinicalLoader({
  label = "Synthesizing Clinical Data...",
  messages = [],
}: {
  label?: string;
  messages?: string[];
}) {
  const [elapsedMs, setElapsedMs] = useState(0);

  // Real-time elapsed stopwatch tracking active server processing
  useEffect(() => {
    const start = performance.now();
    const interval = setInterval(() => {
      setElapsedMs(Math.round(performance.now() - start));
    }, 50);
    return () => clearInterval(interval);
  }, []);

  const subtitle = messages.length > 0 ? messages.join(" • ") : "Querying medical knowledge graph & clinical guidelines";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel p-8 rounded-2xl border border-[var(--glass-border)] shadow-xl relative overflow-hidden my-4"
    >
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[var(--color-primary-500)]/5 to-transparent -translate-x-full animate-[shimmer_2s_infinite]" />

      <div className="flex flex-col items-center justify-center text-center space-y-6 relative z-10">
        <div className="relative">
          <div className="w-16 h-16 rounded-full border-4 border-[var(--color-primary-100)] border-t-[var(--color-primary-500)] animate-spin" />
          <div className="absolute inset-0 flex items-center justify-center">
            <Brain className="w-6 h-6 text-[var(--color-primary-500)] animate-pulse" />
          </div>
        </div>

        <div className="space-y-3 max-w-md w-full">
          <div className="flex items-center justify-center gap-2">
            <h4 className="text-[var(--text-primary)] font-bold tracking-tight text-base">{label}</h4>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-semibold border border-indigo-200">
              {(elapsedMs / 1000).toFixed(1)}s
            </span>
          </div>

          <div className="flex items-center justify-center">
            <div className="text-[11px] font-mono text-[var(--color-primary-700)] flex items-center gap-2 bg-[var(--color-primary-50)] px-3.5 py-1.5 rounded-full border border-[var(--color-primary-200)] shadow-xs">
              <Activity className="w-3.5 h-3.5 animate-pulse text-indigo-600 shrink-0" />
              <span className="truncate max-w-xs">{subtitle}</span>
            </div>
          </div>

          {/* Genuine indeterminate active pulse progress line */}
          <div className="w-full h-1.5 bg-[var(--surface-sunken)] rounded-full overflow-hidden shadow-inner mt-4 relative">
            <motion.div
              className="h-full bg-gradient-to-r from-[var(--color-primary-500)] via-indigo-500 to-teal-400 rounded-full"
              animate={{ x: ["-100%", "100%"] }}
              transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
              style={{ width: "50%" }}
            />
          </div>
        </div>
      </div>
    </motion.div>
  );
}
