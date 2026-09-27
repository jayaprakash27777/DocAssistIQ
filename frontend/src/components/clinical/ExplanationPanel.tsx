/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable react/no-unescaped-entities */
"use client";

import React, { useState, useEffect } from "react";
import { getFindingExplanation, type ExplanationResponse } from "@/lib/api";
import { Brain, AlertTriangle, Plus, Minus, X } from "lucide-react";

export default function ExplanationPanel({ findingId, onClose }: { findingId: string, onClose: () => void }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);

  useEffect(() => {
    let active = true;
    async function fetchExplanation() {
      setLoading(true);
      setError(null);
      const res = await getFindingExplanation(findingId);
      if (active) {
        if (res.ok) setExplanation(res.data);
        else setError(res.error?.message || "Failed to load explanation.");
        setLoading(false);
      }
    }
    fetchExplanation();
    return () => { active = false; };
  }, [findingId]);

  return (
    <div className="flex flex-col h-full bg-white border-l shadow-sm relative">
      <div className="p-4 border-b bg-indigo-50/80 flex items-center justify-between">
        <h3 className="font-semibold text-indigo-900 flex items-center gap-2">
          <Brain className="w-4 h-4 text-indigo-600" />
          <span>Clinical Explanation (Why?)</span>
        </h3>
        <button onClick={onClose} className="p-1 rounded-lg text-indigo-500 hover:text-indigo-800 hover:bg-indigo-100 transition-colors" title="Close explanation">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        {loading && (
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-indigo-100 rounded w-3/4"></div>
            <div className="h-4 bg-indigo-100 rounded w-1/2"></div>
            <div className="h-20 bg-indigo-50 rounded w-full"></div>
          </div>
        )}
        
        {error && (
          <div className="text-red-600 text-sm p-4 bg-red-50 border border-red-200 rounded-md">
            {error}
          </div>
        )}

        {explanation && !loading && (
          <>
            {/* Context & Metadata */}
            <div className="text-xs text-gray-500 space-y-1">
              <p>Model Version: <span className="font-mono text-gray-700">{explanation.model_version}</span></p>
              <p>Knowledge Base: <span className="font-mono text-gray-700">{explanation.knowledge_version}</span></p>
            </div>

            {/* Safety Flags */}
            {explanation.safety_flags.length > 0 && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                <h4 className="text-xs font-bold text-red-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
                  <span>Safety Flags</span>
                </h4>
                <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
                  {explanation.safety_flags.map((flag, idx) => (
                    <li key={idx}>{flag}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Findings Corroboration */}
            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-bold text-gray-600 uppercase tracking-wider mb-2">Supporting Findings</h4>
                {explanation.supporting_findings.length > 0 ? (
                  <ul className="space-y-1">
                    {explanation.supporting_findings.map((finding, idx) => (
                      <li key={idx} className="text-sm text-green-700 flex items-start gap-2">
                        <Plus className="w-3.5 h-3.5 text-green-600 mt-0.5 shrink-0" />
                        <span>{finding}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-400 italic">None found in current context.</p>
                )}
              </div>

              {explanation.contradicting_findings.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-gray-600 uppercase tracking-wider mb-2">Contradicting Findings</h4>
                  <ul className="space-y-1">
                    {explanation.contradicting_findings.map((finding, idx) => (
                      <li key={idx} className="text-sm text-amber-700 flex items-start gap-2">
                        <Minus className="w-3.5 h-3.5 text-amber-600 mt-0.5 shrink-0" />
                        <span>{finding}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {explanation.missing_information.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-gray-600 uppercase tracking-wider mb-2">Missing Information</h4>
                  <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                    {explanation.missing_information.map((info, idx) => (
                      <li key={idx}>{info}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Evidence Validation */}
            <div className="border-t pt-4 mt-4">
              <h4 className="text-xs font-bold text-gray-600 uppercase tracking-wider mb-3">Supporting Knowledge Evidence</h4>
              {explanation.supporting_evidence.length > 0 ? (
                <div className="space-y-3">
                  {explanation.supporting_evidence.map((ev) => (
                    <div key={ev.evidence_id} className="bg-gray-50 border border-gray-200 rounded-md p-3 text-sm">
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-semibold text-gray-800">{ev.source_name}</span>
                        {ev.evidence_grade && (
                          <span className="px-1.5 py-0.5 text-xs font-medium bg-indigo-100 text-indigo-800 rounded">
                            Grade {ev.evidence_grade}
                          </span>
                        )}
                      </div>
                      <p className="text-gray-600 italic">"{ev.claim}"</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                  <p className="text-sm text-yellow-800">No direct supporting evidence found in the approved knowledge base.</p>
                </div>
              )}
            </div>

          </>
        )}
      </div>
    </div>
  );
}
