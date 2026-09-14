/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react/no-unescaped-entities */
"use client";

import React from "react";
import { motion } from "framer-motion";
import { ClipboardList } from "lucide-react";

export default function NotesPage() {
  return (
    <div className="flex flex-col items-center justify-center h-full p-8">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center justify-center max-w-md mx-auto text-center"
      >
        <motion.div 
          initial={{ y: -10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="w-24 h-24 bg-gradient-to-tr from-[var(--color-primary-100)] to-[var(--color-info-50)] rounded-full flex items-center justify-center mb-6 shadow-md border-2 border-[var(--surface-secondary)]"
        >
          <ClipboardList className="w-12 h-12 text-[var(--color-primary-600)]" />
        </motion.div>
        
        <motion.h1 
          initial={{ y: 10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="text-3xl font-extrabold font-heading text-[var(--text-primary)] mb-3 tracking-tight"
        >
          Clinical Notes Dashboard
        </motion.h1>
        
        <motion.p 
          initial={{ y: 10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-lg text-[var(--text-secondary)] font-medium leading-relaxed"
        >
          The standalone Clinical Notes dashboard is coming soon in a future phase. 
          Currently, you can access and generate individual clinical notes directly inside each patient's Consultation Details page.
        </motion.p>
      </motion.div>
    </div>
  );
}
