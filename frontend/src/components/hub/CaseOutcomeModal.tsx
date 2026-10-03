"use client";

import React, { useState } from "react";
import { CheckCircle2, X, Sparkles, Activity } from "lucide-react";
import { getStoredToken } from "@/lib/api";

interface CaseOutcomeModalProps {
  postId: string;
  diseaseName: string;
  currentOutcome?: string | null;
  onClose: () => void;
  onOutcomeUpdated: (outcome: string, isSolved: boolean) => void;
}

export function CaseOutcomeModal({
  postId,
  diseaseName,
  currentOutcome = "",
  onClose,
  onOutcomeUpdated,
}: CaseOutcomeModalProps) {
  const [outcome, setOutcome] = useState(currentOutcome || "");
  const [isSolved, setIsSolved] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!outcome.trim()) return;

    setIsSubmitting(true);
    setError(null);
    try {
      const token = getStoredToken();
      const res = await fetch(`/api/v1/hub/posts/${postId}/outcome`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          patient_outcome: outcome.trim(),
          is_solved: isSolved,
        }),
      });

      if (res.ok) {
        onOutcomeUpdated(outcome.trim(), isSolved);
        onClose();
      } else {
        const data = await res.json().catch(() => ({}));
        setError(data.detail || "Failed to update patient outcome. Only the case author can update outcomes.");
      }
    } catch {
      setError("Network error updating patient outcome.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-lg w-full p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-black text-slate-900">
                Post 48h Patient Outcome & Resolution
              </h2>
              <p className="text-xs text-slate-500 truncate max-w-xs">
                Case: {diseaseName}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-800 mb-1">
              Patient Clinical Course & Definitive Outcome *
            </label>
            <textarea
              required
              rows={4}
              value={outcome}
              onChange={(e) => setOutcome(e.target.value)}
              placeholder="e.g. Patient successfully stabilized on adopted IV regimen. Extubated on ICU Day 2. Repeat echocardiogram showed LVEF improved from 28% to 52%. Discharged on guideline-directed therapy..."
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs text-slate-900 bg-white outline-none focus:border-teal-600 shadow-2xs resize-none"
            />
            <p className="text-[11px] text-slate-400 mt-1">
              Share repeat diagnostics, lab trends, histology confirmation, or discharge status to close the clinical loop with peer doctors.
            </p>
          </div>

          <label className="flex items-center gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer">
            <input
              type="checkbox"
              checked={isSolved}
              onChange={(e) => setIsSolved(e.target.checked)}
              className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500"
            />
            <div>
              <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                Mark Clinical Dilemma as &quot;Solved Case&quot;
              </span>
              <p className="text-[10px] text-slate-500">
                Pins this case as an educational reference pearl for the global medical community.
              </p>
            </div>
          </label>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-bold text-slate-600 hover:text-slate-800 transition cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !outcome.trim()}
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-black shadow-xs transition-all disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
            >
              <Activity className="w-3.5 h-3.5" />
              <span>{isSubmitting ? "Updating..." : "Publish Outcome & Resolve"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CaseOutcomeModal;
