/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, Brain } from "lucide-react";

export default function ClinicalLoader({ label = "Synthesizing Clinical Data...", messages = [] }: { label?: string, messages?: string[] }) {
  const defaultMessages = [
    "Establishing secure context...",
    "Querying medical knowledge graph...",
    "Cross-referencing FDA safety databases...",
    "Evaluating contraindications...",
    "Finalizing clinical recommendations...",
  ];

  const steps = messages.length > 0 ? messages : defaultMessages;
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
    }, 2000);
    return () => clearInterval(interval);
  }, [steps.length]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel p-8 rounded-2xl border border-[var(--glass-border)] shadow-xl relative overflow-hidden my-4"
    >
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[var(--color-primary-500)]/5 to-transparent -translate-x-full animate-[shimmer_2s_infinite]" />
      
      <div className="flex flex-col items-center justify-center text-center space-y-6 relative z-10">
        <div className="relative">
          <div className="w-16 h-16 rounded-full border-4 border-[var(--color-primary-100)] border-t-[var(--color-primary-500)] animate-spin dark:border-[var(--color-primary-900)] dark:border-t-[var(--color-primary-400)]" />
          <div className="absolute inset-0 flex items-center justify-center">
            <Brain className="w-6 h-6 text-[var(--color-primary-500)] animate-pulse" />
          </div>
        </div>

        <div className="space-y-2 max-w-md w-full">
          <h4 className="text-[var(--text-primary)] font-bold tracking-tight">{label}</h4>
          
          <div className="h-12 flex items-center justify-center">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentStep}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -5 }}
                className="text-[11px] font-mono text-[var(--color-primary-700)] flex items-center gap-2 bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-900)]/40 px-3 py-1.5 rounded-full border border-[var(--color-primary-200)] dark:border-[var(--color-primary-800)] shadow-sm"
              >
                <Activity className="w-3 h-3" />
                {steps[currentStep]}
              </motion.div>
            </AnimatePresence>
          </div>

          <div className="w-full h-1.5 bg-[var(--surface-sunken)] rounded-full overflow-hidden shadow-inner mt-4">
            <motion.div 
              className="h-full bg-[var(--color-primary-500)]"
              initial={{ width: "0%" }}
              animate={{ width: `${Math.min(100, ((currentStep + 1) / steps.length) * 100)}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
      </div>
    </motion.div>
  );
}
