"use client";

import React from "react";
import { X, Printer, Download, ShieldCheck, Stethoscope, FileText, CheckCircle2 } from "lucide-react";
import { DoctorPost } from "@/types/social";

interface GrandRoundsExportModalProps {
  post: DoctorPost;
  onClose: () => void;
}

export function GrandRoundsExportModal({ post, onClose }: GrandRoundsExportModalProps) {
  const handlePrint = () => {
    if (typeof window !== "undefined") {
      window.print();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs overflow-y-auto">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-3xl w-full p-6 sm:p-8 space-y-6 my-8 print:p-0 print:border-none print:shadow-none">
        {/* Modal Controls (Hidden in Print) */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 print:hidden">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-teal-600" />
            <span className="text-sm font-black text-slate-900">
              Case Summary & Export (Print / PDF)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="px-4 py-1.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold transition shadow-xs flex items-center gap-1.5 cursor-pointer"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print / Save PDF</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* ── Printable Hospital Report Document ── */}
        <div className="space-y-6 text-slate-900">
          {/* Institutional Header */}
          <div className="border-b-2 border-slate-900 pb-4">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-xl font-black tracking-tight text-slate-900 uppercase">
                  DocAssistIQ Doctor Case Review
                </h1>
                <p className="text-xs font-medium text-slate-600">
                  Doctor Discussion & Second Opinions
                </p>
              </div>
              <div className="text-right text-xs text-slate-500 font-mono">
                <p>Case ID: {post.id.slice(0, 13)}</p>
                <p>Date: {new Date(post.created_at).toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" })}</p>
              </div>
            </div>

            <div className="mt-3 flex items-center gap-2 text-[11px] text-teal-800 bg-teal-50 px-3 py-1.5 rounded-lg border border-teal-200">
              <ShieldCheck className="w-4 h-4 text-teal-600 shrink-0" />
              <span>
                <strong>Patient Privacy Protected:</strong> All personal identifiers and patient names removed.
              </span>
            </div>
          </div>

          {/* Attending Physician Profile */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div>
              <span className="block text-[10px] font-bold text-slate-500 uppercase">Author</span>
              <span className="font-bold text-slate-900">{post.author_name || "Verified Doctor"}</span>
            </div>
            <div>
              <span className="block text-[10px] font-bold text-slate-500 uppercase">Specialty</span>
              <span className="font-bold text-slate-900">{post.author_specialty || "Specialist"}</span>
            </div>
            <div>
              <span className="block text-[10px] font-bold text-slate-500 uppercase">Credentials</span>
              <span className="font-mono font-bold text-teal-700">{post.author_credentials || "Verified MD"}</span>
            </div>
            <div>
              <span className="block text-[10px] font-bold text-slate-500 uppercase">Status</span>
              <span className={`font-bold ${post.is_solved ? "text-emerald-700" : "text-rose-700"}`}>
                {post.is_solved ? "✓ Solved Case" : "Active Case"}
              </span>
            </div>
          </div>

          {/* Case Title & Clinical Findings */}
          <div className="space-y-2">
            <h2 className="text-lg font-black text-slate-900">
              {post.disease_name}
            </h2>
            <div className="p-4 bg-white rounded-xl border border-slate-200 text-xs leading-relaxed text-slate-800 whitespace-pre-line">
              <strong className="block text-slate-900 mb-1">Patient Presentation & History:</strong>
              {post.clinical_findings}
            </div>
          </div>

          {/* Diagnosis & Workup Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <strong className="block text-slate-900 mb-1">Diagnosis:</strong>
              <p className="text-slate-700">{post.diagnosis}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <strong className="block text-slate-900 mb-1">Medicines Given:</strong>
              <p className="text-slate-700">
                {post.drugs_used && post.drugs_used.length > 0 ? post.drugs_used.join(", ") : "Standard protocol"}
              </p>
            </div>
          </div>

          {/* Consensus Poll Findings if Present */}
          {post.poll_data && (
            <div className="p-4 bg-indigo-50/60 rounded-xl border border-indigo-200 text-xs space-y-2">
              <strong className="block text-indigo-950">
                Doctor Poll Results ({post.poll_data.total_votes} votes):
              </strong>
              <p className="text-indigo-900 font-medium">{post.poll_data.question}</p>
              <div className="grid grid-cols-2 gap-2 pt-1">
                {post.poll_data.options.map((opt) => (
                  <div key={opt.label} className="p-2 bg-white rounded-lg border border-indigo-100 flex justify-between font-medium">
                    <span>{opt.label}</span>
                    <span className="font-bold text-indigo-700">{opt.votes} votes</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Adopted or Peer Treatment Suggestions */}
          {post.treatment_suggestions && post.treatment_suggestions.length > 0 && (
            <div className="space-y-2 text-xs">
              <strong className="block text-slate-900">
                Treatment Suggestions from Colleagues ({post.treatment_suggestions.length}):
              </strong>
              <div className="space-y-2">
                {post.treatment_suggestions.map((s) => (
                  <div
                    key={s.id}
                    className={`p-3 rounded-xl border ${
                      s.is_adopted
                        ? "bg-emerald-50/70 border-emerald-300"
                        : "bg-slate-50 border-slate-200"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-1.5 font-bold text-slate-900">
                        <span>{s.drug_or_intervention}</span>
                        {s.dosage_and_route && <span className="text-slate-600 font-normal">({s.dosage_and_route})</span>}
                      </div>
                      {s.is_adopted && (
                        <span className="text-[10px] bg-emerald-600 text-white font-black px-2 py-0.5 rounded-md">
                          Chosen Treatment
                        </span>
                      )}
                    </div>
                    <p className="text-slate-700 leading-relaxed">{s.clinical_rationale}</p>
                    <div className="flex items-center gap-3 mt-1.5 text-[10px] text-slate-500 font-medium">
                      <span>By {s.author_name} ({s.author_specialty})</span>
                      <span>• Evidence: {s.evidence_grade || "Standard Guideline"}</span>
                      <span>• {s.endorsements_count} Colleague Votes</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 48h Patient Outcome if Solved */}
          {post.patient_outcome && (
            <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-300 text-xs space-y-1">
              <div className="flex items-center gap-1.5 text-emerald-900 font-black">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Patient Outcome & Follow-Up:</span>
              </div>
              <p className="text-emerald-950 leading-relaxed pl-5">
                {post.patient_outcome}
              </p>
            </div>
          )}

          {/* Signoff Footer */}
          <div className="pt-4 border-t border-slate-200 flex items-center justify-between text-[11px] text-slate-500 font-mono">
            <span>DocAssistIQ Clinical Social Network • Verified Peer Review</span>
            <span>Page 1 of 1</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default GrandRoundsExportModal;
