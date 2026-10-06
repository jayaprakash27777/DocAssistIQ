"use client";

import React, { useState } from "react";
import { TreatmentSuggestion } from "@/types/social";

interface TreatmentSuggestionBoxProps {
  postId: string;
  postAuthorId: string;
  currentDoctorId?: string;
  suggestions?: TreatmentSuggestion[];
  onAddSuggestion: (
    postId: string,
    data: {
      drug_or_intervention: string;
      dosage_and_route?: string;
      clinical_rationale: string;
      evidence_grade?: string;
    }
  ) => Promise<void>;
  onEndorseSuggestion: (postId: string, suggestionId: string) => Promise<void>;
  onAdoptSuggestion: (postId: string, suggestionId: string) => Promise<void>;
}

export function TreatmentSuggestionBox({
  postId,
  postAuthorId,
  currentDoctorId,
  suggestions = [],
  onAddSuggestion,
  onEndorseSuggestion,
  onAdoptSuggestion,
}: TreatmentSuggestionBoxProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [drug, setDrug] = useState("");
  const [dosage, setDosage] = useState("");
  const [rationale, setRationale] = useState("");
  const [evidenceGrade, setEvidenceGrade] = useState("Class I, Level A (Practice Guideline)");

  const isAuthor = currentDoctorId && postAuthorId && currentDoctorId === postAuthorId;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!drug.trim() || !rationale.trim()) return;

    setIsSubmitting(true);
    try {
      await onAddSuggestion(postId, {
        drug_or_intervention: drug.trim(),
        dosage_and_route: dosage.trim() || undefined,
        clinical_rationale: rationale.trim(),
        evidence_grade: evidenceGrade,
      });
      setDrug("");
      setDosage("");
      setRationale("");
      setIsOpen(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mt-4 pt-3 border-t border-slate-100 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-teal-600 font-black text-xs">💊</span>
          <h4 className="text-xs font-extrabold text-slate-900 tracking-tight">
            Treatment Suggestions ({suggestions.length})
          </h4>
        </div>
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="text-xs font-bold text-teal-700 hover:text-teal-800 bg-teal-50 hover:bg-teal-100 px-2.5 py-1 rounded-lg transition-all cursor-pointer flex items-center gap-1 border border-teal-200"
        >
          <span>{isOpen ? "✕ Cancel" : "+ Suggest Treatment"}</span>
        </button>
      </div>

      {/* ── Form to Submit Treatment Suggestion ── */}
      {isOpen && (
        <form onSubmit={handleSubmit} className="p-3.5 bg-slate-50 rounded-2xl border border-teal-200/80 space-y-2.5">
          <div className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
            <span>Suggest a Medicine or Treatment Plan</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                Medicine or Treatment *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Amoxicillin or supportive fluids"
                value={drug}
                onChange={(e) => setDrug(e.target.value)}
                className="w-full px-3 py-1.5 rounded-xl border border-slate-300 bg-white text-xs text-slate-900 outline-none focus:border-teal-600 shadow-2xs"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                Dosage & Schedule (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. 500mg twice daily for 7 days"
                value={dosage}
                onChange={(e) => setDosage(e.target.value)}
                className="w-full px-3 py-1.5 rounded-xl border border-slate-300 bg-white text-xs text-slate-900 outline-none focus:border-teal-600 shadow-2xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
              Reason & Clinical Advice *
            </label>
            <textarea
              required
              rows={2}
              placeholder="Explain why this medicine or plan is helpful for this patient..."
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              className="w-full px-3 py-1.5 rounded-xl border border-slate-300 bg-white text-xs text-slate-900 outline-none focus:border-teal-600 shadow-2xs resize-none"
            />
          </div>

          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold text-slate-500">Guideline Level:</span>
              <select
                value={evidenceGrade}
                onChange={(e) => setEvidenceGrade(e.target.value)}
                className="text-[11px] font-medium bg-white border border-slate-300 rounded-lg px-2 py-1 text-slate-800 outline-none"
              >
                <option value="Standard Clinical Guideline">Standard Clinical Guideline</option>
                <option value="Supported by Clinical Trials">Supported by Clinical Trials</option>
                <option value="Doctor Consensus / Best Practice">Doctor Consensus / Best Practice</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !drug.trim() || !rationale.trim()}
              className="px-4 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs shadow-xs transition-all disabled:opacity-50 cursor-pointer"
            >
              {isSubmitting ? "Submitting..." : "Post Suggestion"}
            </button>
          </div>
        </form>
      )}

      {/* ── List of Suggestions ── */}
      {suggestions.length > 0 ? (
        <div className="space-y-2.5">
          {suggestions.map((s) => (
            <div
              key={s.id}
              className={`p-3 rounded-2xl border transition-all ${
                s.is_adopted
                  ? "bg-emerald-50/80 border-emerald-300 shadow-2xs"
                  : "bg-slate-50/70 border-slate-200"
              }`}
            >
              <div className="flex items-start justify-between gap-2 mb-1.5">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-slate-800 text-white text-[10px] font-bold flex items-center justify-center flex-shrink-0">
                    {s.author_name ? s.author_name[0].toUpperCase() : "D"}
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-bold text-slate-900">
                        {s.author_name}
                      </span>
                      <span className="text-[10px] text-teal-600 font-bold">
                        ✓ {s.author_credentials || "Verified Doctor"}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-500">
                      {s.author_specialty || "Specialist"} • {new Date(s.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>

                {s.is_adopted && (
                  <span className="inline-flex items-center gap-1 bg-emerald-600 text-white text-[10px] font-black px-2 py-0.5 rounded-full shadow-2xs">
                    <span>✓ Used for Patient</span>
                  </span>
                )}
              </div>

              {/* Suggested Regimen Card */}
              <div className="p-2.5 bg-white rounded-xl border border-slate-200/90 mb-2">
                <div className="flex items-center justify-between text-xs font-black text-teal-900">
                  <span>💊 {s.drug_or_intervention}</span>
                  {s.dosage_and_route && (
                    <span className="text-[11px] font-mono text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">
                      {s.dosage_and_route}
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-700 mt-1 leading-relaxed">
                  {s.clinical_rationale}
                </p>
                {s.evidence_grade && (
                  <div className="mt-1.5 flex items-center gap-1.5 text-[10px] text-teal-700 font-medium">
                    <span className="font-bold">Guideline:</span>
                    <span>{s.evidence_grade}</span>
                  </div>
                )}
              </div>

              {/* Actions: Endorse & Adopt */}
              <div className="flex items-center justify-between text-xs pt-1">
                <button
                  type="button"
                  onClick={() => onEndorseSuggestion(postId, s.id)}
                  className="inline-flex items-center gap-1.5 text-slate-600 hover:text-teal-700 font-bold transition-colors cursor-pointer px-2 py-1 rounded-lg hover:bg-white"
                >
                  <span>👍 Agree</span>
                  <span className="font-mono bg-slate-200/80 px-1.5 py-0.2 rounded-md text-[10px]">
                    {s.endorsements_count || 0}
                  </span>
                </button>

                {isAuthor && (
                  <button
                    type="button"
                    onClick={() => onAdoptSuggestion(postId, s.id)}
                    className={`text-[11px] font-bold px-2.5 py-1 rounded-lg transition-all cursor-pointer ${
                      s.is_adopted
                        ? "bg-emerald-100 text-emerald-800 hover:bg-emerald-200"
                        : "bg-slate-200 text-slate-800 hover:bg-emerald-600 hover:text-white"
                    }`}
                  >
                    {s.is_adopted ? "✓ Used for Patient" : "Choose this Treatment"}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-slate-400 italic">
          No treatment suggestions yet. Suggest a medicine or care plan to help!
        </p>
      )}
    </div>
  );
}
