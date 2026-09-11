"use client";

import React, { useState, useEffect } from "react";
import { getInvestigationsForDisease, InvestigationResponse } from "@/lib/api";
import FeedbackButtons from "./FeedbackButtons";

export default function InvestigationPanel({ consultationId, disease }: { consultationId: string, disease: string }) {
  const [data, setData] = useState<InvestigationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const res = await getInvestigationsForDisease(consultationId, disease);
      if (res.ok) {
        setData(res.data);
      } else {
        if (res.error.message !== "Not Found") {
          setError(res.error.message || "Failed to load investigations");
        }
      }
      setLoading(false);
    }
    load();
  }, [consultationId, disease]);

  if (loading) {
    return (
      <div className="mt-4 p-4 border border-blue-100 rounded bg-blue-50/50 animate-pulse">
        <div className="h-4 bg-blue-200 rounded w-1/4 mb-4"></div>
        <div className="h-10 bg-blue-100 rounded w-full mb-2"></div>
        <div className="h-10 bg-blue-100 rounded w-full"></div>
      </div>
    );
  }

  if (error) {
    return <div className="mt-4 p-3 text-xs text-red-600 bg-red-50 rounded border border-red-100">{error}</div>;
  }

  if (!data || data.suggestions.length === 0) {
    return (
      <div className="mt-4 p-3 text-xs text-gray-500 bg-gray-50 rounded border border-gray-100 italic">
        No reference investigations available for {disease}.
      </div>
    );
  }

  const highPriority = data.suggestions.filter(s => s.priority === "HIGH PRIORITY");
  const conditional = data.suggestions.filter(s => s.priority === "CONDITIONAL");
  const ifIndicated = data.suggestions.filter(s => s.priority === "IF INDICATED");

  const Section = ({ title, items, color }: { title: string, items: any[], color: string }) => {
    if (items.length === 0) return null;
    return (
      <div className="mb-4 last:mb-0">
        <h6 className={`text-[10px] font-bold uppercase tracking-wider mb-2 ${color}`}>{title}</h6>
        <div className="space-y-3">
          {items.map((item, idx) => (
            <div key={idx} className="bg-white border border-gray-200 rounded p-3 shadow-sm">
              <div className="flex justify-between items-start mb-1">
                <span className="font-semibold text-sm text-gray-800">{item.name}</span>
                <span className="text-[9px] px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded font-mono border border-gray-200">
                  {item.provenance}
                </span>
              </div>
              <p className="text-xs text-gray-700 mb-2 leading-relaxed">{item.rationale}</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[10px]">
                {item.relevant_clinical_finding && (
                  <div className="bg-blue-50 p-1.5 rounded border border-blue-100">
                    <strong className="text-blue-800 block mb-0.5">Relevant Finding:</strong>
                    <span className="text-blue-700">{item.relevant_clinical_finding}</span>
                  </div>
                )}
                <div className="bg-gray-50 p-1.5 rounded border border-gray-100">
                  <strong className="text-gray-600 block mb-0.5">Evidence:</strong>
                  <span className="text-gray-600">{item.evidence}</span>
                </div>
              </div>
              
              <div className="mt-2 text-[10px] text-orange-700 bg-orange-50 p-1.5 rounded border border-orange-100">
                <strong className="block mb-0.5">Limitations:</strong>
                {item.limitations}
              </div>

              {item.safety_flags.length > 0 && (
                <div className="mt-2 flex gap-1 flex-wrap">
                  {item.safety_flags.map((flag: string, i: number) => (
                    <span key={i} className="text-[9px] font-bold px-1.5 py-0.5 bg-red-100 text-red-700 rounded border border-red-200">
                      ⚠️ {flag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="mt-4 p-4 border border-blue-200 bg-blue-50/30 rounded-lg">
      <div className="flex items-start justify-between mb-3 border-b border-blue-100 pb-2">
        <div className="flex items-center gap-2">
          <span className="text-blue-500 text-lg">🔬</span>
          <div>
            <h5 className="font-bold text-blue-900 text-sm">Reference Investigations</h5>
            <p className="text-[9px] text-blue-600 font-medium">NOT AN ORDER SHEET — DECISION SUPPORT ONLY</p>
          </div>
        </div>
        <div className="shrink-0 pt-1 pr-1">
          <FeedbackButtons 
            suggestionId={`inv-${consultationId}-${disease}-${Date.now()}`} 
            suggestionType="investigation" 
            suggestionContext={data} 
          />
        </div>
      </div>

      <Section title="High Priority" items={highPriority} color="text-red-600" />
      <Section title="Conditional" items={conditional} color="text-orange-600" />
      <Section title="If Indicated" items={ifIndicated} color="text-blue-600" />
    </div>
  );
}
