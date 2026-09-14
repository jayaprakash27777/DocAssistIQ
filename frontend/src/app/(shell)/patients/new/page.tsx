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
    <div className="max-w-2xl mx-auto space-y-6">
      <header className="flex flex-col gap-4">
        <Link
          href="/patients"
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors w-fit"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Patients
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
            <UserPlus className="w-8 h-8 text-blue-400" />
            Create Patient Record
          </h1>
          <p className="text-gray-400 mt-1">
            Register a new de-identified patient profile for the current tenant.
          </p>
        </div>
      </header>

      <div className="bg-blue-900/20 border border-blue-500/20 rounded-xl p-4 flex gap-3">
        <ShieldAlert className="w-6 h-6 text-blue-400 shrink-0" />
        <p className="text-sm text-blue-300">
          <strong>Clinical Safety Requirement:</strong> Do not enter any Personally Identifiable Information (PII) such as Name, Date of Birth, Address, or SSN/NHS Number. Use opaque reference IDs only.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-gray-800/50 border border-gray-700 rounded-xl p-6 space-y-6 backdrop-blur-xl">
        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Patient Reference ID <span className="text-red-400">*</span>
            </label>
            <input
              required
              type="text"
              value={patientRef}
              onChange={(e) => setPatientRef(e.target.value)}
              placeholder="e.g., EMR-8492-A"
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">An opaque identifier from your hospital system.</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Age Group (Optional)
              </label>
              <select
                value={ageGroup}
                onChange={(e) => setAgeGroup(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
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
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Biological Sex (Optional)
              </label>
              <select
                value={sex}
                onChange={(e) => setSex(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select sex...</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Baseline Conditions (Optional)
            </label>
            <input
              type="text"
              value={conditionsText}
              onChange={(e) => setConditionsText(e.target.value)}
              placeholder="e.g., hypertension, type_2_diabetes"
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">Comma separated list of chronic conditions.</p>
          </div>
        </div>

        <div className="pt-4 border-t border-gray-700 flex justify-end gap-3">
          <Link
            href="/patients"
            className="px-4 py-2 text-gray-300 hover:text-white transition-colors font-medium"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={loading || !patientRef.trim()}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors font-medium shadow-lg shadow-blue-900/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Creating..." : "Create Record"}
          </button>
        </div>
      </form>
    </div>
  );
}
