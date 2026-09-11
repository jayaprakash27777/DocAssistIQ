"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PlusCircle, Search, Users, Activity } from "lucide-react";
import { getPatientProfiles, PatientProfileResponse } from "@/lib/api";

export default function PatientsDashboard() {
  const [patients, setPatients] = useState<PatientProfileResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
            <Users className="w-8 h-8 text-blue-400" />
            Patient Management
          </h1>
          <p className="text-gray-400 mt-1">
            Secure, de-identified patient profiles and longitudinal records.
          </p>
        </div>
        <Link
          href="/patients/new"
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors font-medium shadow-lg shadow-blue-900/20"
        >
          <PlusCircle className="w-5 h-5" />
          Add Patient Record
        </Link>
      </header>

      {/* Stats/Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 flex items-center gap-4">
          <div className="p-3 bg-blue-500/20 rounded-lg">
            <Users className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-400">Total Profiles</p>
            <p className="text-2xl font-bold text-white">{patients.length}</p>
          </div>
        </div>
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 flex items-center gap-4">
          <div className="p-3 bg-emerald-500/20 rounded-lg">
            <Activity className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-400">Total Consultations</p>
            <p className="text-2xl font-bold text-white">
              {patients.reduce((acc, p) => acc + p.sessions.length, 0)}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-gray-800/50 border border-gray-700 rounded-xl overflow-hidden backdrop-blur-xl">
        <div className="p-4 border-b border-gray-700 flex items-center gap-2">
          <Search className="w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search by Patient Reference..."
            className="bg-transparent border-none focus:ring-0 text-white w-full placeholder:text-gray-500"
          />
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-400">Loading patient records...</div>
        ) : error ? (
          <div className="p-8 text-center text-red-400">{error}</div>
        ) : patients.length === 0 ? (
          <div className="p-12 text-center flex flex-col items-center">
            <Users className="w-12 h-12 text-gray-600 mb-4" />
            <h3 className="text-lg font-medium text-white">No patient records found</h3>
            <p className="text-gray-400 mt-1 max-w-sm">
              Get started by creating a new de-identified patient record to link consultations to.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-800/80 border-b border-gray-700 text-sm font-medium text-gray-400">
                  <th className="p-4 whitespace-nowrap">Patient Ref</th>
                  <th className="p-4 whitespace-nowrap">Age Group</th>
                  <th className="p-4 whitespace-nowrap">Sex</th>
                  <th className="p-4 whitespace-nowrap">Past Encounters</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {patients.map((patient) => (
                  <tr
                    key={patient.id}
                    className="hover:bg-gray-700/30 transition-colors cursor-pointer"
                  >
                    <td className="p-4">
                      <Link href={`/patients/${patient.id}`} className="font-medium text-blue-400 hover:underline">
                        {patient.patient_ref}
                      </Link>
                    </td>
                    <td className="p-4 text-gray-300">{patient.age_group || "—"}</td>
                    <td className="p-4 text-gray-300 capitalize">{patient.biological_sex || "—"}</td>
                    <td className="p-4 text-gray-300">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400">
                        {patient.sessions.length} sessions
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
