/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PlusCircle, Search, Users, Activity, ChevronRight, FileText } from "lucide-react";
import { getPatientProfiles, PatientProfileResponse } from "@/lib/api";
import { motion, Variants } from "framer-motion";

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

  const filteredPatients = patients.filter(p => 
    p.patient_ref.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
            className="flex items-center gap-2 bg-gradient-to-r from-[var(--color-primary-500)] to-[var(--color-primary-600)] text-white px-6 py-3.5 rounded-xl font-bold shadow-lg transition-all hover:scale-105 hover:shadow-[var(--shadow-glow)]"
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
                  <th className="p-5 whitespace-nowrap">Age Group</th>
                  <th className="p-5 whitespace-nowrap">Sex</th>
                  <th className="p-5 whitespace-nowrap">Past Encounters</th>
                  <th className="p-5 whitespace-nowrap text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-default)]">
                {filteredPatients.map((patient) => (
                  <tr
                    key={patient.id}
                    className="hover:bg-white transition-colors group relative"
                  >
                    <td className="p-5">
                      <Link href={`/patients/${patient.id}`} className="font-bold text-[var(--color-primary-700)] group-hover:text-[var(--color-primary-600)] transition-colors flex items-center gap-2">
                        <FileText className="w-4 h-4 text-[var(--color-primary-400)]" />
                        {patient.patient_ref}
                      </Link>
                    </td>
                    <td className="p-5 font-medium text-[var(--text-secondary)]">{patient.age_group || "—"}</td>
                    <td className="p-5 font-medium text-[var(--text-secondary)] capitalize">{patient.biological_sex || "—"}</td>
                    <td className="p-5">
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[var(--color-primary-50)] text-[var(--color-primary-700)] border border-[var(--color-primary-200)] shadow-sm">
                        {patient.sessions.length} session{patient.sessions.length !== 1 ? 's' : ''}
                      </span>
                    </td>
                    <td className="p-5 text-right">
                      <Link href={`/patients/${patient.id}`} className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-[var(--color-neutral-100)] text-[var(--text-secondary)] group-hover:bg-[var(--color-primary-50)] group-hover:text-[var(--color-primary-600)] transition-colors">
                        <ChevronRight className="w-5 h-5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}
