"use client";

import React, { useState, useEffect } from "react";
import { getMedicationsForDisease, MedicationResponse } from "@/lib/api";

export default function MedicationPanel({ consultationId, disease }: { consultationId: string, disease: string }) {
  const [data, setData] = useState<MedicationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const res = await getMedicationsForDisease(consultationId, disease);
      if (res.ok) {
        setData(res.data);
      } else {
        if (res.error.message !== "Not Found") {
          setError(res.error.message || "Failed to load medications");
        }
      }
      setLoading(false);
    }
    load();
  }, [consultationId, disease]);

  if (loading) {
    return (
      <div className="mt-4 p-4 border border-teal-100 rounded bg-teal-50/50 animate-pulse">
        <div className="h-4 bg-teal-200 rounded w-1/4 mb-4"></div>
        <div className="h-10 bg-teal-100 rounded w-full mb-2"></div>
        <div className="h-10 bg-teal-100 rounded w-full"></div>
      </div>
    );
  }

  if (error) {
    return <div className="mt-4 p-3 text-xs text-red-600 bg-red-50 rounded border border-red-100">{error}</div>;
  }

  if (!data || data.suggestions.length === 0) {
    return (
      <div className="mt-4 p-3 text-xs text-gray-500 bg-gray-50 rounded border border-gray-100 italic">
        No reference medications available for {disease}.
      </div>
    );
  }

  return (
    <div className="mt-4 p-4 border border-teal-200 bg-teal-50/30 rounded-lg">
      <div className="flex items-center gap-2 mb-3 border-b border-teal-100 pb-2">
        <span className="text-teal-500 text-lg">💊</span>
        <div>
          <h5 className="font-bold text-teal-900 text-sm">Reference Medications</h5>
          <p className="text-[9px] text-teal-600 font-bold bg-teal-100 inline-block px-1 rounded">
            REFERENCE INFORMATION - CLINICIAN REVIEW REQUIRED
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {data.suggestions.map((med, idx) => (
          <div key={idx} className="bg-white border border-gray-200 rounded p-4 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 px-2 py-1 bg-gray-100 text-gray-500 text-[9px] font-mono border-l border-b border-gray-200 rounded-bl">
              Source: {med.source_evidence}
            </div>
            
            <h6 className="font-bold text-gray-800 text-base mb-1">{med.generic_name}</h6>
            <div className="text-[11px] text-gray-500 mb-3 flex gap-2">
              <span className="bg-gray-100 px-1.5 py-0.5 rounded border border-gray-200">{med.formulation}</span>
              <span className="bg-gray-100 px-1.5 py-0.5 rounded border border-gray-200">{med.route}</span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-4 gap-y-3 text-xs">
              <div>
                <span className="block text-[10px] uppercase font-semibold text-gray-500 mb-0.5">Indication</span>
                <p className="text-gray-800">{med.indication}</p>
              </div>

              <div>
                <span className="block text-[10px] uppercase font-semibold text-gray-500 mb-0.5">Standard Reference Dosing</span>
                <p className="text-gray-800 bg-teal-50 border border-teal-100 px-2 py-1 rounded inline-block font-mono text-[10px]">
                  {med.standard_reference_dosing}
                </p>
              </div>

              <div>
                <span className="block text-[10px] uppercase font-semibold text-gray-500 mb-0.5">Contraindications</span>
                {med.contraindications.length > 0 ? (
                  <ul className="list-disc pl-4 text-red-700">
                    {med.contraindications.map((c, i) => <li key={i}>{c}</li>)}
                  </ul>
                ) : (
                  <span className="text-gray-400 italic">None listed</span>
                )}
              </div>

              <div>
                <span className="block text-[10px] uppercase font-semibold text-gray-500 mb-0.5">Interactions</span>
                {med.interactions.length > 0 ? (
                  <ul className="list-disc pl-4 text-orange-700">
                    {med.interactions.map((i, k) => <li key={k}>{i}</li>)}
                  </ul>
                ) : (
                  <span className="text-gray-400 italic">None listed</span>
                )}
              </div>
            </div>

            <div className="mt-3 pt-3 border-t border-gray-100 grid grid-cols-2 lg:grid-cols-4 gap-3 text-[10px]">
              <div>
                <span className="block font-semibold text-gray-600">Allergy</span>
                <span className={med.allergy_considerations === "Unavailable" ? "text-gray-400 italic" : "text-gray-800"}>{med.allergy_considerations}</span>
              </div>
              <div>
                <span className="block font-semibold text-gray-600">Renal</span>
                <span className={med.renal_considerations === "Unavailable" ? "text-gray-400 italic" : "text-gray-800"}>{med.renal_considerations}</span>
              </div>
              <div>
                <span className="block font-semibold text-gray-600">Hepatic</span>
                <span className={med.hepatic_considerations === "Unavailable" ? "text-gray-400 italic" : "text-gray-800"}>{med.hepatic_considerations}</span>
              </div>
              <div>
                <span className="block font-semibold text-gray-600">Pregnancy/Lactation</span>
                <span className={med.pregnancy_lactation_considerations === "Unavailable" ? "text-gray-400 italic" : "text-gray-800"}>{med.pregnancy_lactation_considerations}</span>
              </div>
              <div>
                <span className="block font-semibold text-gray-600">Age</span>
                <span className={med.age_considerations === "Unavailable" ? "text-gray-400 italic" : "text-gray-800"}>{med.age_considerations}</span>
              </div>
              <div className="col-span-2 lg:col-span-3">
                <span className="block font-semibold text-gray-600">Monitoring</span>
                <span className={med.monitoring_reference_information === "Unavailable" ? "text-gray-400 italic" : "text-gray-800"}>{med.monitoring_reference_information}</span>
              </div>
            </div>

          </div>
        ))}
      </div>
    </div>
  );
}
