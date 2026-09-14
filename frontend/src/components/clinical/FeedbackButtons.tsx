/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React, { useState } from "react";
import { submitClinicianFeedback } from "@/lib/api";
import { toast } from "react-hot-toast";
import { Check, X, Edit3, Loader2 } from "lucide-react";

interface FeedbackButtonsProps {
  suggestionId: string;
  suggestionType: "clinical_note" | "diagnosis" | "investigation" | "medication";
  suggestionContext: any;
  onFeedbackSubmitted?: (decision: string) => void;
}

export default function FeedbackButtons({
  suggestionId,
  suggestionType,
  suggestionContext,
  onFeedbackSubmitted
}: FeedbackButtonsProps) {
  const [loading, setLoading] = useState(false);
  const [showReason, setShowReason] = useState(false);
  const [decision, setDecision] = useState<"ACCEPT" | "MODIFY" | "REJECT" | null>(null);
  const [reason, setReason] = useState("");
  const [submittedDecision, setSubmittedDecision] = useState<string | null>(null);

  const handleAction = async (action: "ACCEPT" | "MODIFY" | "REJECT", bypassReason: boolean = false) => {
    if ((action === "REJECT" || action === "MODIFY") && !bypassReason && !showReason) {
      setDecision(action);
      setShowReason(true);
      return;
    }

    setLoading(true);
    try {
      const res = await submitClinicianFeedback({
        suggestion_id: suggestionId,
        suggestion_type: suggestionType,
        decision: action,
        reason: reason || undefined,
        suggestion_context: suggestionContext
      });

      if (res.ok) {
        toast.success(`Feedback recorded: ${action}`);
        setSubmittedDecision(action);
        setShowReason(false);
        if (onFeedbackSubmitted) onFeedbackSubmitted(action);
      } else {
        toast.error(res.error?.message || "Failed to submit feedback");
      }
    } catch (e) {
      toast.error("Network error submitting feedback");
    } finally {
      setLoading(false);
    }
  };

  if (submittedDecision) {
    return (
      <div className="flex items-center gap-2 text-xs font-bold px-3 py-1.5 rounded-full bg-gray-100 text-gray-500 border border-gray-200">
        {submittedDecision === "ACCEPT" && <Check className="w-3 h-3 text-emerald-500" />}
        {submittedDecision === "REJECT" && <X className="w-3 h-3 text-red-500" />}
        {submittedDecision === "MODIFY" && <Edit3 className="w-3 h-3 text-amber-500" />}
        <span>{submittedDecision}ED</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-end gap-2">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); handleAction("ACCEPT", true); }}
          disabled={loading}
          className="flex items-center gap-1 px-3 py-1.5 text-xs font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-lg transition-colors"
          title="Accept Suggestion"
        >
          <Check className="w-3 h-3" /> Accept
        </button>
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); handleAction("MODIFY"); }}
          disabled={loading}
          className="flex items-center gap-1 px-3 py-1.5 text-xs font-bold text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-lg transition-colors"
          title="Modify Suggestion"
        >
          <Edit3 className="w-3 h-3" /> Modify
        </button>
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); handleAction("REJECT"); }}
          disabled={loading}
          className="flex items-center gap-1 px-3 py-1.5 text-xs font-bold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-lg transition-colors"
          title="Reject Suggestion"
        >
          <X className="w-3 h-3" /> Reject
        </button>
      </div>

      {showReason && (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-sm mt-2 w-64">
          <label className="block text-[10px] font-bold text-gray-500 uppercase mb-2">Reason for {decision}</label>
          <input
            type="text"
            autoFocus
            onClick={(e) => e.stopPropagation()}
            className="w-full text-xs p-2 border border-gray-200 rounded focus:outline-none focus:border-blue-400 mb-2"
            placeholder={decision === "REJECT" ? "e.g. Hallucination, Not relevant" : "e.g. Incorrect dosage"}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); setShowReason(false); }}
              className="text-[10px] px-2 py-1 text-gray-500 hover:text-gray-700 font-bold"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); handleAction(decision!, true); }}
              disabled={loading || !reason.trim()}
              className="text-[10px] px-3 py-1 bg-blue-600 text-white rounded font-bold hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
            >
              {loading && <Loader2 className="w-3 h-3 animate-spin" />} Submit
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
