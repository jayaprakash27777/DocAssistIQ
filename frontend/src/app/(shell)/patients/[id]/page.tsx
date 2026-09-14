/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, User, Activity, Clock, FileText, History } from "lucide-react";
import { getPatientProfile, PatientProfileResponse } from "@/lib/api";
import PatientTimeline from "@/components/patients/PatientTimeline";

export default function PatientDetail() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [patient, setPatient] = useState<PatientProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"encounters" | "timeline">("timeline");

  useEffect(() => {
    async function loadPatient() {
      try {
        const response = await getPatientProfile(id);
        if (response.ok && response.data) {
          setPatient(response.data);
        } else {
          setError(!response.ok ? response.error.message : "Failed to load patient");
        }
      } catch (err: any) {
        setError(err.message || "An unexpected error occurred");
      } finally {
        setLoading(false);
      }
    }

    if (id) loadPatient();
  }, [id]);

  if (loading) {
    return <div className="p-8 text-center text-gray-400">Loading patient profile...</div>;
  }

  if (error || !patient) {
    return <div className="p-8 text-center text-red-400">{error || "Patient not found"}</div>;
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-entrance pb-12">
      <header className="flex flex-col gap-6">
        <button
          onClick={() => router.push("/patients")}
          className="flex items-center gap-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors w-fit font-medium"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Patients
        </button>

        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-6 bg-[var(--surface-secondary)] p-8 rounded-2xl border border-[var(--border-default)] shadow-sm relative overflow-hidden">
          {/* Decorative mesh gradient background */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-[var(--color-primary-100)] to-[var(--color-primary-50)] rounded-full blur-3xl opacity-50 -translate-y-1/2 translate-x-1/2 pointer-events-none" />
          
          <div className="flex items-center gap-6 relative z-10">
            {/* Dynamic Avatar */}
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[var(--color-primary-400)] to-[var(--color-primary-600)] flex items-center justify-center text-white text-3xl font-bold font-heading shadow-md border-4 border-white">
              {patient.patient_ref.substring(0, 2).toUpperCase()}
            </div>
            
            <div>
              <h1 className="text-3xl font-bold font-heading text-[var(--text-primary)] flex items-center gap-3">
                {patient.patient_ref}
              </h1>
              <div className="flex gap-4 mt-2 text-sm text-[var(--text-secondary)]">
                <span className="flex items-center gap-1.5 bg-[var(--surface-sunken)] px-3 py-1 rounded-full border border-[var(--border-default)] shadow-sm">
                  <span className="font-bold text-[var(--text-tertiary)] uppercase text-[10px] tracking-wider">Age Group:</span>
                  <span className="font-semibold text-[var(--text-primary)]">{patient.age_group || "Unknown"}</span>
                </span>
                <span className="flex items-center gap-1.5 bg-[var(--surface-sunken)] px-3 py-1 rounded-full border border-[var(--border-default)] shadow-sm">
                  <span className="font-bold text-[var(--text-tertiary)] uppercase text-[10px] tracking-wider">Sex:</span>
                  <span className="capitalize font-semibold text-[var(--text-primary)]">{patient.biological_sex || "Unknown"}</span>
                </span>
              </div>
            </div>
          </div>
          
          <Link
            href={`/consultations/new?patient_id=${patient.id}`}
            className="bg-gradient-to-r from-[var(--color-primary-500)] to-[var(--color-primary-600)] hover:from-[var(--color-primary-600)] hover:to-[var(--color-primary-700)] text-white px-6 py-3 rounded-xl flex items-center gap-2 transition-all font-bold shadow-md hover:shadow-lg relative z-10"
          >
            <PlusCircle className="w-5 h-5" />
            New Encounter
          </Link>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Sidebar: Conditions */}
        <div className="bg-white border border-[var(--border-default)] rounded-2xl p-6 shadow-sm h-fit">
          <h2 className="text-lg font-bold font-heading text-[var(--text-primary)] flex items-center gap-2 mb-5">
            <Activity className="w-5 h-5 text-[var(--color-primary-500)]" />
            Baseline Conditions
          </h2>
          {Object.keys(patient.baseline_conditions || {}).length > 0 ? (
            <ul className="space-y-3">
              {Object.entries(patient.baseline_conditions).map(([key, value]) => (
                <li key={key} className="bg-[var(--surface-sunken)] p-3.5 rounded-xl border border-[var(--border-default)] shadow-inner">
                  <p className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-wider mb-1">{key.replace(/_/g, " ")}</p>
                  <p className="text-sm font-semibold text-[var(--text-primary)]">{String(value)}</p>
                </li>
              ))}
            </ul>
          ) : (
            <div className="p-4 bg-[var(--surface-sunken)] rounded-xl border border-[var(--border-default)] text-center">
              <p className="text-sm text-[var(--text-secondary)] font-medium">No baseline conditions recorded.</p>
            </div>
          )}
        </div>

        {/* Main content: Tabs */}
        <div className="md:col-span-2 space-y-6">
          {/* Tabs header */}
          <div className="flex space-x-2 border-b border-[var(--border-default)] mb-6 pb-px">
            <button
              onClick={() => setActiveTab("timeline")}
              className={`px-4 py-3 border-b-2 text-sm font-bold flex items-center gap-2 transition-all ${
                activeTab === "timeline" 
                  ? "border-[var(--color-primary-500)] text-[var(--color-primary-600)]" 
                  : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)]"
              }`}
            >
              <History className="w-4 h-4" />
              Full Timeline
            </button>
            <button
              onClick={() => setActiveTab("encounters")}
              className={`px-4 py-3 border-b-2 text-sm font-bold flex items-center gap-2 transition-all ${
                activeTab === "encounters" 
                  ? "border-[var(--color-primary-500)] text-[var(--color-primary-600)]" 
                  : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)]"
              }`}
            >
              <Clock className="w-4 h-4" />
              Encounter Summaries
            </button>
          </div>

          {activeTab === "timeline" ? (
            <PatientTimeline patientId={id} />
          ) : (
            <div className="bg-white border border-[var(--border-default)] rounded-2xl p-6 shadow-sm relative overflow-hidden">
              <h2 className="text-lg font-bold font-heading text-[var(--text-primary)] flex items-center gap-2 mb-6">
                <Clock className="w-5 h-5 text-[var(--color-primary-500)]" />
                Encounter Summaries
              </h2>

              {patient.sessions.length > 0 ? (
                <div className="relative border-l-2 border-[var(--border-default)] ml-4 space-y-10 py-2">
                  {patient.sessions.map((session, idx) => (
                    <div key={session.id} className="relative pl-8">
                      <div className="absolute -left-[9px] top-1.5 w-4 h-4 bg-white rounded-full border-4 border-[var(--color-primary-500)]" />
                      <div className="bg-white border border-[var(--border-default)] rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex justify-between items-start mb-3">
                          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-[var(--color-primary-50)] text-[var(--color-primary-700)] uppercase tracking-wider border border-[var(--color-primary-200)]">
                            {session.encounter_type}
                          </span>
                          <span className="text-xs font-mono text-[var(--text-tertiary)] bg-[var(--surface-sunken)] px-2 py-1 rounded border border-[var(--border-default)]">
                            ID: {session.id.split('-')[0]}
                          </span>
                        </div>
                        <p className="text-sm text-[var(--text-secondary)] mb-4 leading-relaxed font-medium">
                          {session.clinical_notes_summary || "No summary available."}
                        </p>
                        <Link
                          href={`/consultations/${session.id}`}
                          className="text-sm font-bold text-[var(--color-primary-600)] hover:text-[var(--color-primary-700)] flex items-center gap-1.5 w-fit"
                        >
                          <FileText className="w-4 h-4" />
                          View Full Note
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 bg-[var(--surface-sunken)] rounded-xl border border-[var(--border-default)]">
                  <p className="text-[var(--text-secondary)] font-medium">No past encounters found for this patient.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Temporary import for the icon that was missing at the top
function PlusCircle(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <path d="M8 12h8" />
      <path d="M12 8v8" />
    </svg>
  );
}
