"use client";

import React, { useState, useEffect } from "react";
import { getDifferentialDiagnosis, DifferentialDiagnosisResponse } from "@/lib/api";
import { toast } from "react-hot-toast";
import InvestigationPanel from "./InvestigationPanel";

export default function DifferentialDiagnosis({ consultationId }: { consultationId: string }) {
  const [data, setData] = useState<DifferentialDiagnosisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [showInvestigationsFor, setShowInvestigationsFor] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const res = await getDifferentialDiagnosis(consultationId);
      if (res.ok) {
        setData(res.data);
      } else {
        // Suppress 404s or empty state logs for differential if it's not ready
        if (res.error.message !== "Not Found") {
          toast.error(res.error.message || "Failed to load differential diagnosis");
        }
      }
      setLoading(false);
    }
    load();
  }, [consultationId]);

  if (loading) {
    return (
      <div className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm mb-6">
        <div className="animate-pulse flex space-x-4">
          <div className="flex-1 space-y-4 py-1">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  if (data.status === "INSUFFICIENT_INFO") {
    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm mb-6 overflow-hidden">
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center gap-2">
          <span className="text-gray-500">🤖</span>
          <h3 className="font-semibold text-gray-700 text-sm">AI DIFFERENTIAL SUGGESTION</h3>
        </div>
        <div className="p-6 flex flex-col items-center justify-center text-center">
          <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center text-2xl mb-3">
            🤷
          </div>
          <h4 className="text-sm font-bold text-gray-800 mb-2">Insufficient Information</h4>
          <p className="text-sm text-gray-600 max-w-sm mb-4">
            {data.message || "Not enough clinical information provided to generate a safe differential diagnosis."}
          </p>
          {data.missing_critical_info.length > 0 && (
            <div className="text-left bg-yellow-50 text-yellow-800 p-3 rounded border border-yellow-200 text-xs w-full max-w-sm">
              <strong className="block mb-1">Missing Requirements:</strong>
              <ul className="list-disc pl-4 space-y-1">
                {data.missing_critical_info.map((info, i) => (
                  <li key={i}>{info}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (data.top_candidates.length === 0) {
    return null;
  }

  return (
    <div className="bg-white border border-indigo-200 rounded-lg shadow-sm mb-6 overflow-hidden">
      <div className="bg-indigo-50 px-4 py-3 border-b border-indigo-100 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <span className="text-indigo-600">🤖</span>
          <h3 className="font-semibold text-indigo-900 text-sm">AI DIFFERENTIAL SUGGESTION</h3>
        </div>
        <span className="text-xs text-indigo-600 bg-indigo-100 px-2 py-1 rounded-full font-medium">
          Top {data.top_candidates.length} Candidates
        </span>
      </div>
      
      <div className="p-3 bg-yellow-50 text-yellow-800 text-[11px] border-b border-yellow-100 flex items-start gap-2">
        <span className="mt-0.5">⚠️</span>
        <p>This ranking is a decision-support algorithmic suggestion based on extracted features and does not imply diagnostic certainty. Independent clinician review is strictly required.</p>
      </div>

      <div className="divide-y divide-gray-100">
        {data.top_candidates.map((candidate, idx) => (
          <div key={idx} className="flex flex-col">
            <div 
              className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors"
              onClick={() => setExpandedIndex(expandedIndex === idx ? null : idx)}
            >
              <div className="flex items-center gap-4">
                <div className="w-6 h-6 flex items-center justify-center rounded-full bg-gray-100 text-gray-500 font-bold text-xs shrink-0">
                  {idx + 1}
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">{candidate.disease}</h4>
                  <div className="text-xs text-gray-500 mt-0.5 flex items-center gap-2">
                    <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${candidate.score > 0.6 ? 'bg-green-500' : candidate.score > 0.3 ? 'bg-yellow-400' : 'bg-orange-400'}`} 
                        style={{ width: `${Math.min(100, Math.max(5, candidate.score * 100))}%` }}
                      ></div>
                    </div>
                    <span>{Math.round(candidate.score * 100)}% Match</span>
                  </div>
                  {candidate.safety_decision && candidate.safety_decision.decision !== "ALLOW" && (
                    <div className="mt-1 flex items-center gap-1">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                        candidate.safety_decision.decision === 'ABSTAIN' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {candidate.safety_decision.decision === 'ABSTAIN' ? '🛑 UNSAFE' : '⚠️ WARNING'}
                      </span>
                    </div>
                  )}
                </div>
              </div>
              <div className="text-gray-400 text-xs font-mono">
                {expandedIndex === idx ? '▲' : '▼'}
              </div>
            </div>

            {expandedIndex === idx && (
              <div className="px-14 pb-4 pt-1 space-y-4">
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Supporting Findings */}
                  <div>
                    <h5 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2">Supporting Findings</h5>
                    {candidate.supporting_findings.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {candidate.supporting_findings.map((f, i) => (
                          <span key={i} className="text-[11px] px-2 py-0.5 bg-green-50 text-green-700 border border-green-200 rounded shadow-sm">✓ {f}</span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-xs text-gray-400">None identified</span>
                    )}
                  </div>

                  {/* Missing Findings */}
                  <div>
                    <h5 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2">Missing Expected</h5>
                    {candidate.missing_expected_findings.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {candidate.missing_expected_findings.map((f, i) => (
                          <span key={i} className="text-[11px] px-2 py-0.5 bg-gray-50 text-gray-600 border border-gray-200 rounded shadow-sm">? {f}</span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-xs text-gray-400">None identified</span>
                    )}
                  </div>
                </div>

                {/* Contradicting Findings */}
                {candidate.contradicting_information.length > 0 && (
                  <div>
                    <h5 className="text-[10px] font-semibold text-red-500 uppercase tracking-wider mb-2">Contradicting Information</h5>
                    <div className="flex flex-wrap gap-1">
                      {candidate.contradicting_information.map((f, i) => (
                        <span key={i} className="text-[11px] px-2 py-0.5 bg-red-50 text-red-700 border border-red-200 rounded shadow-sm">✗ {f} (negated)</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Safety Flags */}
                {candidate.safety_decision && candidate.safety_decision.flags.length > 0 && (
                  <div className="mt-2 border border-red-100 rounded-md overflow-hidden">
                    <div className="bg-red-50 px-3 py-1 border-b border-red-100 flex items-center justify-between">
                      <span className="text-[10px] font-bold text-red-800 uppercase tracking-wider">Safety Engine Analysis</span>
                      <span className="text-[9px] text-red-600 font-mono">v{candidate.safety_decision.flags[0].rule_version}</span>
                    </div>
                    <div className="bg-white p-2 divide-y divide-red-50">
                      {candidate.safety_decision.flags.map((flag, i) => (
                        <div key={i} className="py-1.5 flex items-start gap-2">
                          <span className="text-red-500 mt-0.5 text-[10px]">
                            {flag.severity === 'CRITICAL' ? '🛑' : '⚠️'}
                          </span>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="text-[10px] font-bold text-gray-800">{flag.category.replace('_', ' ')}</span>
                              <span className={`text-[8px] px-1 rounded-sm font-bold ${
                                flag.severity === 'CRITICAL' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                              }`}>
                                {flag.severity}
                              </span>
                            </div>
                            <p className="text-[11px] text-gray-700 mt-0.5">{flag.message}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Why / Explanation */}
                <div className="mt-4 pt-3 border-t border-gray-100 flex items-start gap-3">
                  <button 
                    className="shrink-0 px-2 py-1 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 rounded text-xs font-medium transition-colors cursor-help"
                    title="Explain this ranking"
                  >
                    Why?
                  </button>
                  <p className="text-xs text-gray-600 leading-relaxed pt-0.5 flex-1">
                    {candidate.explanation_reference}
                  </p>
                </div>

                <div className="mt-2 pt-2 flex justify-end">
                  <button
                    className="px-3 py-1.5 bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 rounded text-xs font-semibold transition-colors"
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowInvestigationsFor(showInvestigationsFor === candidate.disease ? null : candidate.disease);
                    }}
                  >
                    {showInvestigationsFor === candidate.disease ? 'Hide Reference Investigations' : 'View Reference Investigations'}
                  </button>
                </div>

                {showInvestigationsFor === candidate.disease && (
                  <InvestigationPanel consultationId={consultationId} disease={candidate.disease} />
                )}

              </div>
            )}
          </div>
        ))}
      </div>
      
      <div className="bg-gray-50 p-2 border-t border-gray-200 text-right">
        <span className="text-[10px] text-gray-400 font-mono">Provider: {data.provider_metadata.provider} v{data.provider_metadata.version}</span>
      </div>
    </div>
  );
}
