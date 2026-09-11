"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, User, Activity, Clock, FileText } from "lucide-react";
import { getPatientProfile, PatientProfileResponse } from "@/lib/api";

export default function PatientDetail() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [patient, setPatient] = useState<PatientProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
    <div className="max-w-5xl mx-auto space-y-6">
      <header className="flex flex-col gap-4">
        <button
          onClick={() => router.push("/patients")}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors w-fit"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Patients
        </button>

        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <User className="w-8 h-8 text-blue-400" />
              </div>
              {patient.patient_ref}
            </h1>
            <div className="flex gap-4 mt-3 text-sm text-gray-300">
              <span className="flex items-center gap-1">
                <span className="font-medium text-gray-500">Age Range:</span>{" "}
                {patient.age_group || "Unknown"}
              </span>
              <span className="flex items-center gap-1">
                <span className="font-medium text-gray-500">Sex:</span>{" "}
                <span className="capitalize">{patient.biological_sex || "Unknown"}</span>
              </span>
            </div>
          </div>
          <Link
            href={`/consultations/new?patient_id=${patient.id}`}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors font-medium shadow-lg shadow-blue-900/20"
          >
            <PlusCircle className="w-5 h-5" />
            New Encounter
          </Link>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Sidebar: Conditions */}
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5 backdrop-blur-xl h-fit">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-emerald-400" />
            Baseline Conditions
          </h2>
          {Object.keys(patient.baseline_conditions || {}).length > 0 ? (
            <ul className="space-y-3">
              {Object.entries(patient.baseline_conditions).map(([key, value]) => (
                <li key={key} className="bg-gray-900/50 p-3 rounded-lg border border-gray-700/50">
                  <p className="text-sm font-medium text-gray-300 capitalize">{key.replace(/_/g, " ")}</p>
                  <p className="text-xs text-gray-500 mt-1">{String(value)}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">No baseline conditions recorded.</p>
          )}
        </div>

        {/* Main content: Timeline */}
        <div className="md:col-span-2 space-y-6">
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5 backdrop-blur-xl">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-6">
              <Clock className="w-5 h-5 text-blue-400" />
              Encounter History
            </h2>

            {patient.sessions.length > 0 ? (
              <div className="relative border-l border-gray-700 ml-3 space-y-8">
                {patient.sessions.map((session, idx) => (
                  <div key={session.id} className="relative pl-6">
                    <div className="absolute -left-1.5 top-1.5 w-3 h-3 bg-blue-500 rounded-full ring-4 ring-gray-900" />
                    <div className="bg-gray-900/50 border border-gray-700/50 rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-700 text-gray-300 capitalize">
                          {session.encounter_type}
                        </span>
                        <span className="text-xs text-gray-500">
                          {/* Assuming we had created_at, but we only have ID here right now */}
                          ID: {session.id.split('-')[0]}
                        </span>
                      </div>
                      <p className="text-sm text-gray-300 mb-3">
                        {session.clinical_notes_summary || "No summary available."}
                      </p>
                      <Link
                        href={`/consultations/${session.id}`} // Or wherever consultations live
                        className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1 w-fit"
                      >
                        <FileText className="w-4 h-4" />
                        View Full Note
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">No past encounters found for this patient.</p>
              </div>
            )}
          </div>
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
