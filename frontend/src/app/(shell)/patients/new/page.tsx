/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, UserPlus, ShieldAlert } from "lucide-react";
import { createPatientProfile } from "@/lib/api";

export default function NewPatientProfile() {
  const router = useRouter();
  const [patientRef, setPatientRef] = useState("");
  const [ageGroup, setAgeGroup] = useState("");
  const [sex, setSex] = useState("");
  const [conditionsText, setConditionsText] = useState("");
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const conditions = conditionsText
        .split(",")
        .map(c => c.trim())
        .filter(c => c.length > 0)
        .reduce((acc, curr) => ({ ...acc, [curr]: "active" }), {});

      const response = await createPatientProfile({
        patient_ref: patientRef,
        age_group: ageGroup || null,
        biological_sex: sex || null,
        baseline_conditions: conditions,
      });

      if (response.ok && response.data) {
        router.push(`/patients/${response.data.id}`);
      } else {
        setError(!response.ok ? response.error.message : "Failed to create patient record");
      }
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6 py-6 px-4">
      <header className="flex flex-col gap-4">
        <Link
          href="/patients"
          className="flex items-center gap-2 text-sm text-slate-500 hover:text-teal-700 transition-colors w-fit font-semibold"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Patients
        </Link>
        <div>
          <h1 className="text-3xl font-black tracking-tight text-slate-900 flex items-center gap-3 font-heading">
            <div className="w-10 h-10 rounded-2xl bg-teal-50 text-teal-600 border border-teal-200/60 flex items-center justify-center shrink-0 shadow-sm">
              <UserPlus className="w-5 h-5" />
            </div>
            Create Patient Record
          </h1>
          <p className="text-slate-500 mt-1.5 text-sm font-medium">
            Register a new de-identified longitudinal patient profile for the clinical registry.
          </p>
        </div>
      </header>

      <div className="bg-sky-50/80 border border-sky-200/70 rounded-2xl p-4 flex gap-3.5 shadow-sm">
        <ShieldAlert className="w-5 h-5 text-sky-600 shrink-0 mt-0.5" />
        <p className="text-xs text-sky-900 leading-relaxed m-0 font-medium">
          <strong className="font-bold">Clinical Safety Requirement:</strong> Do not enter any Personally Identifiable Information (PII) such as Name, Date of Birth, Address, or SSN/NHS Number. Use opaque reference IDs only.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="glass-panel-4k gpu-accelerated border border-slate-200/90 rounded-3xl p-8 space-y-6 bg-white/85 backdrop-blur-2xl shadow-[0_12px_36px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.9)] ring-1 ring-black/5">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-2xl text-sm font-medium">
            {error}
          </div>
        )}

        <div className="space-y-5">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
              Patient Reference ID <span className="text-red-500">*</span>
            </label>
            <input
              required
              type="text"
              value={patientRef}
              onChange={(e) => setPatientRef(e.target.value)}
              placeholder="e.g., EMR-8492-A"
              className="w-full bg-white/90 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all shadow-sm font-mono text-sm"
            />
            <p className="text-[11px] text-slate-400 mt-1">An opaque identifier from your hospital system.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                Age Group (Optional)
              </label>
              <select
                value={ageGroup}
                onChange={(e) => setAgeGroup(e.target.value)}
                className="w-full bg-white/90 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all shadow-sm text-sm"
              >
                <option value="">Select range...</option>
                <option value="0-18">0-18</option>
                <option value="19-30">19-30</option>
                <option value="31-50">31-50</option>
                <option value="51-70">51-70</option>
                <option value="71+">71+</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                Biological Sex (Optional)
              </label>
              <select
                value={sex}
                onChange={(e) => setSex(e.target.value)}
                className="w-full bg-white/90 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all shadow-sm text-sm"
              >
                <option value="">Select sex...</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
              Baseline Conditions (Optional)
            </label>
            <input
              type="text"
              value={conditionsText}
              onChange={(e) => setConditionsText(e.target.value)}
              placeholder="e.g., hypertension, type_2_diabetes"
              className="w-full bg-white/90 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all shadow-sm text-sm"
            />
            <p className="text-[11px] text-slate-400 mt-1">Comma separated list of chronic conditions.</p>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 flex justify-end items-center gap-3">
          <Link
            href="/patients"
            className="px-4 py-2 text-slate-500 hover:text-slate-800 transition-colors font-semibold text-sm"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={loading || !patientRef.trim()}
            className="bg-gradient-to-r from-teal-500 to-indigo-600 hover:brightness-110 text-white px-6 py-2.5 rounded-xl transition-all font-bold text-sm shadow-md shadow-teal-500/20 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Creating..." : "Create Record"}
          </button>
        </div>
      </form>
    </div>
  );
}
