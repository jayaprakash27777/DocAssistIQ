/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable react/no-unescaped-entities */
/**
 * DocAssistIQ — Consultations List (Phase 20).
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import {
  listConsultations,
  createConsultation,
  searchConsultations,
  type ConsultationSummary,
} from "@/lib/api";
import { Search, Stethoscope, PlusCircle } from "lucide-react";
import { motion } from "framer-motion";

export default function ConsultationsListPage() {
  const { toast } = useToast();
  const router = useRouter();
  const [consultations, setConsultations] = useState<ConsultationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");

  const fetchConsultations = useCallback(async () => {
    setLoading(true);
    const r = await listConsultations();
    setLoading(false);
    if (r.ok) {
      setConsultations(r.data.items);
    } else {
      toast.error(r.error.message || "Failed to load consultations");
    }
  }, [toast]);

  const performSearch = useCallback(async (query: string) => {
    setLoading(true);
    const r = await searchConsultations(query);
    setLoading(false);
    if (r.ok) {
      setConsultations(r.data);
    } else {
      toast.error(r.error.message || "Search failed");
    }
  }, [toast]);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (searchQuery.trim().length >= 3) {
        performSearch(searchQuery.trim());
      } else if (searchQuery.trim().length === 0) {
        fetchConsultations();
      }
    }, 500);

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery, fetchConsultations, performSearch]);

  const handleCreate = async () => {
    setCreating(true);
    const r = await createConsultation();
    setCreating(false);
    if (r.ok) {
      toast.success("New consultation created");
      router.push(`/consultations/${r.data.id}`);
    } else {
      toast.error(r.error.message || "Failed to create consultation");
    }
  };

  return (
    <div className="consultations-page" style={{ maxWidth: "1000px" }}>
      <header className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <h2 className="page-title">My Consultations</h2>
          <p className="page-subtitle">View and manage clinical sessions.</p>
        </div>
        <button className="btn-primary" onClick={handleCreate} disabled={creating}>
          {creating ? "Creating..." : "+ New Consultation"}
        </button>
      </header>

      <div className="mt-8 mb-4 relative max-w-lg">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-gray-400" />
        </div>
        <input
          type="text"
          className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 sm:text-sm"
          placeholder="Semantic Patient Search (e.g. 'headache and nausea')..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <div style={{ marginTop: "1rem" }}>
        {loading ? (
          <div className="data-table">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} style={{ padding: "1rem", borderBottom: "1px solid var(--border-subtle)" }}>
                <Skeleton height="1.5rem" width="100%" />
              </div>
            ))}
          </div>
        ) : (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID / Time</th>
                  <th>Patient Session</th>
                  <th>Status</th>
                  <th>Notes Length</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {consultations.map((c, index) => (
                  <motion.tr 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    key={c.id}
                  >
                    <td>
                      <div><strong>{c.id.substring(0, 8)}</strong></div>
                      <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                        {new Date(c.created_at).toLocaleString()}
                      </div>
                    </td>
                    <td>
                      <code style={{ fontSize: "0.8125rem" }}>
                        --
                      </code>
                    </td>
                    <td>
                      <span className={`status-badge status-${c.status.toLowerCase()}`}>
                        {c.status.toUpperCase()}
                      </span>
                    </td>
                    <td>{c.input_preview?.length || 0} chars</td>
                    <td>
                      <Link href={`/consultations/${c.id}`} className="btn-secondary btn-sm">
                        Open Room
                      </Link>
                    </td>
                  </motion.tr>
                ))}
                {consultations.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-20 text-center">
                      <motion.div 
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="flex flex-col items-center justify-center max-w-md mx-auto"
                      >
                        <motion.div 
                          initial={{ y: -10, opacity: 0 }}
                          animate={{ y: 0, opacity: 1 }}
                          transition={{ delay: 0.1 }}
                          className="w-20 h-20 bg-gradient-to-tr from-[var(--color-primary-100)] to-[var(--color-info-50)] rounded-full flex items-center justify-center mb-6 shadow-sm border-2 border-white dark:border-[var(--surface-primary)]"
                        >
                          <Stethoscope className="w-10 h-10 text-[var(--color-primary-600)]" />
                        </motion.div>
                        <motion.h3 
                          initial={{ y: 10, opacity: 0 }}
                          animate={{ y: 0, opacity: 1 }}
                          transition={{ delay: 0.2 }}
                          className="text-2xl font-bold font-heading text-[var(--text-primary)] mb-2"
                        >
                          No Clinical Sessions
                        </motion.h3>
                        <motion.p 
                          initial={{ y: 10, opacity: 0 }}
                          animate={{ y: 0, opacity: 1 }}
                          transition={{ delay: 0.3 }}
                          className="text-[var(--text-secondary)] font-medium mb-8"
                        >
                          Your workspace is clear. Initiate a new consultation to begin analyzing clinical notes, extracting conditions, and formulating care plans.
                        </motion.p>
                        <motion.button 
                          initial={{ y: 10, opacity: 0 }}
                          animate={{ y: 0, opacity: 1 }}
                          transition={{ delay: 0.4 }}
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={handleCreate}
                          disabled={creating}
                          className="bg-gradient-to-r from-[var(--color-primary-500)] to-[var(--color-primary-600)] hover:from-[var(--color-primary-600)] hover:to-[var(--color-primary-700)] text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-[var(--color-primary-500)]/30 transition-all flex items-center gap-2"
                        >
                          <PlusCircle className="w-5 h-5" />
                          {creating ? "Initiating..." : "Start New Consultation"}
                        </motion.button>
                      </motion.div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
