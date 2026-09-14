/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react/no-unescaped-entities */
"use client";

import React, { useState } from "react";
import { verifyCitation, type ClaimVerificationResponse } from "@/lib/api";
import { useToast } from "@/components/shell/ToastProvider";

export default function CitationVerifier() {
  const { toast } = useToast();
  const [evidenceId, setEvidenceId] = useState("");
  const [claimText, setClaimText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ClaimVerificationResponse | null>(null);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!evidenceId.trim() || !claimText.trim()) return;

    setLoading(true);
    setResult(null);

    const res = await verifyCitation({
      evidence_id: evidenceId.trim(),
      claim_text: claimText.trim(),
    });

    setLoading(false);

    if (res.ok) {
      setResult(res.data);
    } else {
      toast.error(res.error?.message || "Failed to verify citation");
    }
  };

  return (
    <div className="flex flex-col h-full bg-white border-l shadow-sm">
      <div className="p-4 border-b bg-gray-50 flex items-center justify-between">
        <h3 className="font-semibold text-gray-800 flex items-center gap-2">
          <span className="text-purple-600">🛡️</span> Citation Verifier
        </h3>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <form onSubmit={handleVerify} className="space-y-4 mb-6 pb-6 border-b">
          <div>
            <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1">
              Evidence UUID
            </label>
            <input
              type="text"
              value={evidenceId}
              onChange={(e) => setEvidenceId(e.target.value)}
              placeholder="e.g. 123e4567-e89b-12d3-a456-426614174000"
              className="w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono"
              disabled={loading}
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1">
              Text Claim to Verify
            </label>
            <textarea
              value={claimText}
              onChange={(e) => setClaimText(e.target.value)}
              placeholder="Paste the generated text claim..."
              className="w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 min-h-[80px]"
              disabled={loading}
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading || !evidenceId.trim() || !claimText.trim()}
            className="w-full px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-md hover:bg-purple-700 disabled:opacity-50 transition-colors"
          >
            {loading ? "Verifying..." : "Verify Citation"}
          </button>
        </form>

        {result && (
          <div className={`p-4 rounded-lg border ${result.is_verified ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
            <div className="flex items-start gap-3">
              <span className="text-xl leading-none mt-0.5">
                {result.is_verified ? "✅" : "⚠️"}
              </span>
              <div className="flex-1">
                <h4 className={`text-sm font-semibold mb-1 ${result.is_verified ? 'text-green-800' : 'text-red-800'}`}>
                  {result.status.replace("_", " ")}
                </h4>
                <p className={`text-sm mb-3 ${result.is_verified ? 'text-green-700' : 'text-red-700'}`}>
                  {result.reason}
                </p>

                {result.evidence_details && (
                  <div className="bg-white/60 p-3 rounded text-xs space-y-1 mt-2 border border-black/5">
                    <p><strong>Source:</strong> {result.evidence_details.source_name} ({result.evidence_details.source_status})</p>
                    <p><strong>Actual DB Claim:</strong> "{result.evidence_details.actual_claim}"</p>
                    <p><strong>Grade:</strong> {result.evidence_details.evidence_grade || 'N/A'}</p>
                    <p><strong>AI Extracted:</strong> {result.evidence_details.is_ai_extracted ? 'Yes' : 'No'}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
