/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PlusCircle, Search, Users, Activity, ChevronRight, FileText, AlertTriangle, Brain, FileCheck, ShieldCheck } from "lucide-react";
import { getPatientProfiles, PatientProfileResponse } from "@/lib/api";
import { motion, Variants } from "framer-motion";

function extractConditionsList(rawBase: any, keys: string[]): string[] {
  if (!rawBase || typeof rawBase !== "object") return [];
  for (const k of keys) {
    const val = rawBase[k];
    if (Array.isArray(val)) return val.map(String).map((s) => s.trim()).filter(Boolean);
    if (typeof val === "string" && val.trim()) {
      return val.split(/,\s*|\n|;\s*/).map((s) => s.trim()).filter(Boolean);
    }
    if (typeof val === "object" && val !== null && !Array.isArray(val)) {
      const entries = Object.keys(val).filter(Boolean);
      if (entries.length > 0 && !["allergies", "chronic_conditions", "vitals", "current_medications"].includes(entries[0])) {
        return entries;
      }
    }
  }
  // Check if rawBase itself has condition keys
  const directKeys = Object.keys(rawBase).filter(
    (k) => !["allergies", "chronic_conditions", "vitals", "blood_type", "code_status", "current_medications"].includes(k)
  );
  if (directKeys.length > 0 && keys.includes("conditions")) {
    return directKeys;
  }
  return [];
}

export default function PatientsDashboard() {
  const [patients, setPatients] = useState<PatientProfileResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    async function fetchPatients() {
      try {
        const res = await getPatientProfiles();
        if (res.ok && res.data) {
          setPatients(res.data);
        } else {
          setError(!res.ok ? res.error.message : "Failed to load patient profiles");
        }
      } catch (err: any) {
        setError(err.message || "An unexpected error occurred");
      } finally {
        setLoading(false);
      }
    }

    fetchPatients();
  }, []);

  const filteredPatients = patients.filter((p) => {
    const q = searchQuery.toLowerCase();
    const matchesRef = p.patient_ref.toLowerCase().includes(q);
    const allergies = extractConditionsList(p.baseline_conditions, ["allergies", "documented_allergies"]);
    const chronic = extractConditionsList(p.baseline_conditions, ["chronic_conditions", "active_problems", "conditions"]);
    const matchesAllergy = allergies.some((a: string) => a.toLowerCase().includes(q));
    const matchesChronic = chronic.some((c: string) => c.toLowerCase().includes(q));
    return matchesRef || matchesAllergy || matchesChronic;
  });

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <motion.div 
      className="dashboard-shell space-y-8"
      variants={containerVariants}
      initial="hidden"
      animate="show"
    >
      <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6 mb-8">
        <div>
          <motion.h1 variants={itemVariants} className="text-4xl font-extrabold font-heading text-[var(--text-primary)] tracking-tight flex items-center gap-3">
            <div className="bg-[var(--color-primary-50)] p-2 rounded-xl text-[var(--color-primary-600)]">
              <Users className="w-8 h-8" />
            </div>
            Patient Management
          </motion.h1>
          <motion.p variants={itemVariants} className="text-[var(--text-secondary)] mt-2 text-lg font-medium">
            Secure, de-identified patient profiles and longitudinal records.
          </motion.p>
        </div>
        <motion.div variants={itemVariants}>
          <Link
            href="/patients/new"
            className="flex items-center gap-2 bg-gradient-to-r from-[var(--color-primary-500)] to-[var(--color-primary-600)] text-white px-6 py-3.5 rounded-xl font-bold shadow-lg transition-all hover:brightness-105 hover:shadow-[var(--shadow-glow)]"
          >
            <PlusCircle className="w-5 h-5" />
            Add Patient Record
          </Link>
        </motion.div>
      </header>

      {/* Stats/Metrics */}
      <motion.div variants={containerVariants} className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-8">
        <motion.div variants={itemVariants} className="glass-panel-4k gpu-accelerated p-6 rounded-3xl border border-slate-200/90 bg-white/85 backdrop-blur-xl shadow-[0_12px_36px_rgba(0,0,0,0.05),inset_0_1px_0_rgba(255,255,255,0.9)] flex items-center gap-4 ring-1 ring-black/5">
          <div className="p-4 bg-[var(--color-primary-50)] text-[var(--color-primary-600)] border border-[var(--color-primary-200)]/60 rounded-2xl shrink-0 shadow-sm">
            <Users className="w-8 h-8" />
          </div>
          <div>
            <p className="text-[0.75rem] font-bold text-[var(--text-secondary)] uppercase tracking-widest">Total Profiles</p>
            <p className="text-3xl font-extrabold text-[var(--text-primary)] font-heading">{patients.length}</p>
          </div>
        </motion.div>
        <motion.div variants={itemVariants} className="glass-panel-4k gpu-accelerated p-6 rounded-3xl border border-slate-200/90 bg-white/85 backdrop-blur-xl shadow-[0_12px_36px_rgba(0,0,0,0.05),inset_0_1px_0_rgba(255,255,255,0.9)] flex items-center gap-4 ring-1 ring-black/5">
          <div className="p-4 bg-emerald-50 text-emerald-600 border border-emerald-200/60 rounded-2xl shrink-0 shadow-sm">
            <Activity className="w-8 h-8" />
          </div>
          <div>
            <p className="text-[0.75rem] font-bold text-[var(--text-secondary)] uppercase tracking-widest">Total Consultations</p>
            <p className="text-3xl font-extrabold text-[var(--text-primary)] font-heading">
              {patients.reduce((acc, p) => acc + p.sessions.length, 0)}
            </p>
          </div>
        </motion.div>
      </motion.div>

      <motion.div variants={itemVariants} className="glass-panel-4k gpu-accelerated rounded-3xl border border-slate-200/90 bg-white/85 backdrop-blur-2xl shadow-[0_12px_36px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.9)] overflow-hidden z-10 ring-1 ring-black/5">
        <div className="p-6 border-b border-[var(--border-default)] flex items-center gap-4 bg-white/50 backdrop-blur-md rounded-t-3xl">
          <div className="relative flex-1 max-w-md group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-[var(--color-primary-500)] group-focus-within:text-[var(--color-primary-600)] transition-colors" />
            </div>
            <input
              type="text"
              placeholder="Search by Patient Reference..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="block w-full pl-12 pr-4 py-3 bg-white/80 backdrop-blur border border-[var(--border-default)] rounded-xl text-base placeholder-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-400)] focus:border-transparent transition-all shadow-sm hover:shadow-md"
            />
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center text-[var(--text-tertiary)] flex flex-col items-center">
            <div className="w-12 h-12 border-4 border-[var(--color-primary-200)] border-t-[var(--color-primary-600)] rounded-full animate-spin mb-4" />
            <span className="font-medium text-lg">Loading patient records...</span>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-red-500 font-medium bg-red-50 rounded-b-3xl m-4">{error}</div>
        ) : filteredPatients.length === 0 ? (
          <div className="p-16 text-center flex flex-col items-center">
            <div className="w-20 h-20 bg-[var(--color-neutral-100)] rounded-full flex items-center justify-center mb-6">
              <Users className="w-10 h-10 text-[var(--text-tertiary)]" />
            </div>
            <h3 className="text-xl font-bold text-[var(--text-primary)] font-heading">No records found</h3>
            <p className="text-[var(--text-secondary)] mt-2 max-w-md">
              {searchQuery ? "No patients matched your search criteria." : "Get started by creating a new de-identified patient record."}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-b-3xl bg-white/40">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[var(--color-neutral-50)]/80 border-b border-[var(--border-default)] text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">
                  <th className="p-5 whitespace-nowrap">Patient Ref</th>
                  <th className="p-5 whitespace-nowrap">Demographics</th>
                  <th className="p-5 whitespace-nowrap">Safety & Allergies</th>
                  <th className="p-5 whitespace-nowrap">Chronic Conditions</th>
                  <th className="p-5 whitespace-nowrap">Encounters</th>
                  <th className="p-5 whitespace-nowrap text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-default)]">
                {filteredPatients.map((patient) => {
                  const allergies = extractConditionsList(patient.baseline_conditions, ["allergies", "documented_allergies"]);
                  const chronic = extractConditionsList(patient.baseline_conditions, ["chronic_conditions", "active_problems", "conditions"]);
                  const latestSessionId = patient.sessions?.[0]?.id;

                  return (
                    <tr
                      key={patient.id}
                      className="hover:bg-white transition-colors group relative"
                    >
                      <td className="p-5">
                        <Link href={`/patients/${patient.id}`} className="font-bold text-[var(--color-primary-700)] group-hover:text-[var(--color-primary-600)] transition-colors flex items-center gap-2">
                          <FileText className="w-4 h-4 text-[var(--color-primary-400)] shrink-0" />
                          <span className="font-mono tracking-tight">{patient.patient_ref}</span>
                        </Link>
                      </td>
                      <td className="p-5 font-medium text-[var(--text-secondary)] text-sm">
                        <div className="flex items-center gap-1.5">
                          <span>{patient.age_group || "Adult"}</span>
                          <span className="text-slate-300">•</span>
                          <span className="capitalize">{patient.biological_sex || "—"}</span>
                        </div>
                      </td>
                      <td className="p-5">
                        {allergies.length > 0 ? (
                          <div className="flex flex-wrap gap-1 items-center">
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200 shadow-xs">
                              <AlertTriangle className="w-3 h-3 text-amber-600 shrink-0" />
                              {allergies.slice(0, 2).join(", ")}
                              {allergies.length > 2 && ` +${allergies.length - 2}`}
                            </span>
                          </div>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <ShieldCheck className="w-3 h-3 text-emerald-600 shrink-0" />
                            NKDA
                          </span>
                        )}
                      </td>
                      <td className="p-5">
                        {chronic.length > 0 ? (
                          <div className="flex flex-wrap gap-1 items-center max-w-xs">
                            {chronic.slice(0, 2).map((c, i) => (
                              <span key={i} className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                                {c}
                              </span>
                            ))}
                            {chronic.length > 2 && (
                              <span className="text-[11px] text-slate-400 font-medium">+{chronic.length - 2} more</span>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-[var(--text-tertiary)] italic">None documented</span>
                        )}
                      </td>
                      <td className="p-5">
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[var(--color-primary-50)] text-[var(--color-primary-700)] border border-[var(--color-primary-200)] shadow-xs">
                          {patient.sessions.length} encounter{patient.sessions.length !== 1 ? 's' : ''}
                        </span>
                      </td>
                      <td className="p-5 text-right">
                        <div className="inline-flex items-center gap-2">
                          <Link
                            href={`/ai?patient_ref=${encodeURIComponent(patient.patient_ref)}${latestSessionId ? `&cid=${latestSessionId}` : ''}`}
                            title={`Consult DocAssist IQ AI regarding ${patient.patient_ref}`}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 shadow-xs transition-colors"
                          >
                            <Brain className="w-3.5 h-3.5 text-indigo-600" />
                            <span>Ask AI</span>
                          </Link>
                          <Link
                            href={`/patients/${patient.id}`}
                            className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-[var(--color-neutral-100)] text-[var(--text-secondary)] hover:bg-[var(--color-primary-50)] hover:text-[var(--color-primary-600)] transition-colors"
                          >
                            <ChevronRight className="w-5 h-5" />
                          </Link>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}
