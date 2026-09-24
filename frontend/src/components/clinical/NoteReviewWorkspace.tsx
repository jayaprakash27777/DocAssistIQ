/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React, { useState, useEffect } from "react";
import { getClinicalNote, getConsultation, getTranscript, reviewClinicalFinding } from "@/lib/api";
import type { ConsultationResponse, TranscriptResponse, ClinicalFindingResponse } from "@/lib/api";
import ClinicalNoteEditor from "@/components/clinical/ClinicalNoteEditor";
import RAGAssistant from "@/components/clinical/RAGAssistant";
import CitationVerifier from "@/components/clinical/CitationVerifier";
import ExplanationPanel from "@/components/clinical/ExplanationPanel";

export default function NoteReviewWorkspace({ consultationId }: { consultationId: string }) {
  const [consultation, setConsultation] = useState<ConsultationResponse | null>(null);
  const [transcript, setTranscript] = useState<TranscriptResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeSegmentId, setActiveSegmentId] = useState<string | null>(null);
  const [rightPanel, setRightPanel] = useState<"none" | "rag" | "verify" | "explain">("none");
  const [explainFindingId, setExplainFindingId] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [consRes, transRes] = await Promise.all([
          getConsultation(consultationId),
          getTranscript(consultationId)
        ]);

        if (consRes.ok) setConsultation(consRes.data);
        else setError(consRes.error?.message || "Failed to load consultation");

        if (transRes.ok) setTranscript(transRes.data);
        
      } catch (err: any) {
        setError(err.message || "An error occurred");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [consultationId]);

  const handleFindingReview = async (findingId: string, action: "confirm" | "reject") => {
    const res = await reviewClinicalFinding(consultationId, findingId, action);
    if (res.ok && consultation) {
      // Update local state
      setConsultation({
        ...consultation,
        findings: consultation.findings.map(f => f.id === findingId ? res.data : f)
      });
    }
  };

  if (loading) return <div className="p-8 animate-pulse text-gray-500">Loading Review Workspace...</div>;
  if (error) return <div className="p-8 text-red-600">Error: {error}</div>;
  if (!consultation) return <div className="p-8 text-gray-500">Consultation not found.</div>;

  return (
    <div className="flex flex-col lg:flex-row h-full gap-6 w-full">
      {/* LEFT PANE: Transcript and Extracted Facts */}
      <div className="w-full lg:w-1/2 flex flex-col gap-4 overflow-hidden rounded-3xl glass-panel-4k gpu-accelerated border border-slate-200/90 bg-white/85 backdrop-blur-2xl shadow-[0_12px_36px_rgba(0,0,0,0.06)] ring-1 ring-black/5 relative">
        
        {/* Facts / Findings */}
        <div className="flex-1 overflow-y-auto border-b border-slate-100">
          <div className="sticky top-0 bg-slate-50/90 backdrop-blur-md p-4 border-b border-slate-100 font-bold text-sm text-slate-800 font-heading z-10 flex items-center justify-between">
            <span>Extracted Clinical Facts & Findings</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-200/80 text-slate-700 font-medium">{consultation.findings.length} findings</span>
          </div>
          <div className="p-4 space-y-3">
            {consultation.findings.length === 0 ? (
              <p className="text-sm text-slate-500 italic p-4 text-center">No findings extracted yet.</p>
            ) : (
              consultation.findings.map((finding) => (
                <div key={finding.id} className="border border-slate-200/80 rounded-2xl p-4 bg-white/90 hover:bg-white hover:border-slate-300 shadow-sm transition-all text-sm">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <span className="font-semibold text-slate-900">{finding.finding_text}</span>
                      {finding.concept && (
                        <span className="ml-2 px-2 py-0.5 bg-blue-50 text-blue-700 text-xs font-medium rounded-full border border-blue-200">
                          {finding.concept}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0 ml-4">
                      <button
                        onClick={() => {
                          setExplainFindingId(finding.id);
                          setRightPanel("explain");
                        }}
                        className="text-xs px-2.5 py-1 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-lg hover:bg-indigo-100 font-medium transition-colors"
                        title="Why was this finding suggested?"
                      >
                        🧠 Evidence
                      </button>
                      {finding.status === 'suggested' && (
                        <>
                          <button 
                            onClick={() => handleFindingReview(finding.id, "confirm")}
                            className="text-xs px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg hover:bg-emerald-100 font-semibold transition-colors"
                          >
                            Accept
                          </button>
                          <button 
                            onClick={() => handleFindingReview(finding.id, "reject")}
                            className="text-xs px-2.5 py-1 bg-rose-50 text-rose-700 border border-rose-200 rounded-lg hover:bg-rose-100 font-semibold transition-colors"
                          >
                            Reject
                          </button>
                        </>
                      )}
                      {finding.status === 'confirmed' && (
                        <span className="text-xs text-emerald-700 font-semibold bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-lg">✓ Confirmed</span>
                      )}
                      {finding.status === 'rejected' && (
                        <span className="text-xs text-rose-700 font-semibold bg-rose-50 border border-rose-200 px-2.5 py-1 rounded-lg">✗ Rejected</span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Transcript Reference */}
        <div className="h-1/3 min-h-[180px] overflow-y-auto bg-slate-50/60">
          <div className="sticky top-0 bg-slate-100/90 backdrop-blur-md p-3 border-b border-slate-200/80 font-bold text-xs text-slate-700 uppercase tracking-wider z-10">
            Source Consultation Transcript
          </div>
          <div className="p-4 space-y-2 text-sm">
            {!transcript || transcript.segments.length === 0 ? (
              <p className="text-slate-400 italic text-center py-4">No transcript available.</p>
            ) : (
              transcript.segments.map((seg) => (
                <div 
                  key={seg.id} 
                  className={`p-2.5 rounded-xl transition-colors ${activeSegmentId === seg.id ? 'bg-amber-50 border border-amber-300 shadow-sm' : 'hover:bg-white'}`}
                >
                  <span className="font-bold text-slate-600 text-xs mr-2 w-16 inline-block">
                    {seg.speaker_label || 'Unknown'}:
                  </span>
                  <span className="text-slate-800">{seg.clinician_corrected_text || seg.processed_text || seg.raw_text}</span>
                </div>
              ))
            )}
          </div>
        </div>

      </div>

      {/* RIGHT PANE: Note Editor (and toggleable Assistants) */}
      <div className="w-full lg:w-1/2 flex flex-col overflow-hidden h-full rounded-3xl glass-panel-4k gpu-accelerated border border-slate-200/90 bg-white/85 backdrop-blur-2xl shadow-[0_12px_36px_rgba(0,0,0,0.06)] ring-1 ring-black/5 relative">
        {/* Toolbar to toggle RAG/Verifier */}
        <div className="bg-slate-50/80 backdrop-blur-md border-b border-slate-200/80 p-3 flex justify-end gap-2.5 relative z-20">
          <button
            onClick={() => setRightPanel(rightPanel === "verify" ? "none" : "verify")}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-xl transition-all shadow-sm ${rightPanel === "verify" ? 'bg-purple-600 text-white shadow-purple-600/20' : 'bg-white text-slate-700 hover:bg-slate-50 border border-slate-200'}`}
          >
            {rightPanel === "verify" ? "Hide Verifier" : "🛡️ Verify Citation"}
          </button>
          <button
            onClick={() => setRightPanel(rightPanel === "rag" ? "none" : "rag")}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-xl transition-all shadow-sm ${rightPanel === "rag" ? 'bg-teal-600 text-white shadow-teal-600/20' : 'bg-white text-slate-700 hover:bg-slate-50 border border-slate-200'}`}
          >
            {rightPanel === "rag" ? "Hide Assistant" : "✨ Knowledge Assistant"}
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          <div className={`flex-1 transition-all duration-300 ${rightPanel !== "none" ? 'w-1/2 border-r' : 'w-full'}`}>
            <ClinicalNoteEditor consultationId={consultationId} />
          </div>
          
          {rightPanel === "rag" && (
            <div className="w-1/2 transition-all duration-300 bg-gray-50">
              <RAGAssistant />
            </div>
          )}

          {rightPanel === "verify" && (
            <div className="w-1/2 transition-all duration-300 bg-gray-50">
              <CitationVerifier />
            </div>
          )}

          {rightPanel === "explain" && explainFindingId && (
            <div className="w-1/2 transition-all duration-300 bg-gray-50">
              <ExplanationPanel 
                findingId={explainFindingId} 
                onClose={() => {
                  setRightPanel("none");
                  setExplainFindingId(null);
                }} 
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
