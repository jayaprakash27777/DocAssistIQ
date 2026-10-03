/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { getClinicalNote, getConsultation, getTranscript, reviewClinicalFinding, listDocumentsForConsultation } from "@/lib/api";
import type { ConsultationResponse, TranscriptResponse, ClinicalFindingResponse, VerifiedDocumentRecord } from "@/lib/api";
import ClinicalNoteEditor from "@/components/clinical/ClinicalNoteEditor";
import RAGAssistant from "@/components/clinical/RAGAssistant";
import CitationVerifier from "@/components/clinical/CitationVerifier";
import ExplanationPanel from "@/components/clinical/ExplanationPanel";
import { 
  ShieldCheck, Sparkles, Brain, Check, X, Search, CheckCheck, 
  FileText, Radio, HelpCircle, Activity, ChevronRight, FileCheck, Download 
} from "lucide-react";
import { useToast } from "@/components/shell/ToastProvider";

type FindingStatusFilter = "all" | "pending" | "confirmed" | "rejected";

export default function NoteReviewWorkspace({ consultationId }: { consultationId: string }) {
  const { toast } = useToast();
  const [consultation, setConsultation] = useState<ConsultationResponse | null>(null);
  const [transcript, setTranscript] = useState<TranscriptResponse | null>(null);
  const [documents, setDocuments] = useState<VerifiedDocumentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeSegmentId, setActiveSegmentId] = useState<string | null>(null);
  const [rightPanel, setRightPanel] = useState<"none" | "rag" | "verify" | "explain" | "documents">("none");
  const [explainFindingId, setExplainFindingId] = useState<string | null>(null);
  const [findingQuery, setFindingQuery] = useState("");
  const [findingFilter, setFindingFilter] = useState<FindingStatusFilter>("all");
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        const [consRes, transRes, docsRes] = await Promise.all([
          getConsultation(consultationId),
          getTranscript(consultationId),
          listDocumentsForConsultation(consultationId)
        ]);

        if (consRes.ok) setConsultation(consRes.data);
        else setError(consRes.error?.message || "Failed to load consultation");

        if (transRes.ok) setTranscript(transRes.data);
        if (docsRes.ok && docsRes.data?.documents) setDocuments(docsRes.data.documents);
        
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
    if (!res.ok) {
      toast.error(res.error?.message || `Failed to ${action} finding`);
      return;
    }
    if (consultation) {
      setConsultation({
        ...consultation,
        findings: consultation.findings.map(f => f.id === findingId ? res.data : f)
      });
    }
    toast.success(`Finding ${action === "confirm" ? "confirmed" : "rejected"}`);
  };

  const handleConfirmAllPending = async () => {
    if (!consultation?.findings) return;
    const pending = consultation.findings.filter(f => f.status === "pending" || f.status === "suggested");
    if (pending.length === 0) {
      toast.info("No pending findings to confirm");
      return;
    }

    setActionLoading(true);
    for (const f of pending) {
      await reviewClinicalFinding(consultationId, f.id, "confirm");
    }
    setActionLoading(false);

    // Refresh state locally
    setConsultation({
      ...consultation,
      findings: consultation.findings.map(f => (f.status === "pending" || f.status === "suggested") ? { ...f, status: "confirmed" } : f)
    });
    toast.success(`Confirmed all ${pending.length} pending findings`);
  };

  // Filtered Findings
  const filteredFindings = useMemo(() => {
    if (!consultation?.findings) return [];
    let list = consultation.findings;

    if (findingFilter === "pending") {
      list = list.filter(f => f.status === "pending" || f.status === "suggested");
    } else if (findingFilter === "confirmed") {
      list = list.filter(f => f.status === "confirmed");
    } else if (findingFilter === "rejected") {
      list = list.filter(f => f.status === "rejected");
    }

    if (findingQuery.trim()) {
      const q = findingQuery.toLowerCase();
      list = list.filter(f => 
        (f.finding_text && f.finding_text.toLowerCase().includes(q)) ||
        (f.concept && f.concept.toLowerCase().includes(q)) ||
        (f.value && f.value.toLowerCase().includes(q))
      );
    }

    return list;
  }, [consultation?.findings, findingFilter, findingQuery]);

  const pendingCount = consultation?.findings?.filter(f => f.status === "pending" || f.status === "suggested").length || 0;

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-64 gap-3">
      <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      <span className="text-sm font-medium text-slate-500">Loading Review Workspace...</span>
    </div>
  );

  if (error) return (
    <div className="p-8 text-center bg-rose-50 text-rose-700 rounded-3xl border border-rose-200">
      <h3 className="font-bold text-base mb-1">Failed to load consultation encounter</h3>
      <p className="text-xs">{error}</p>
    </div>
  );

  if (!consultation) return (
    <div className="p-8 text-center text-slate-500">
      Consultation encounter not found.
    </div>
  );

  return (
    <div className="flex flex-col lg:flex-row h-full min-h-0 gap-5 w-full overflow-hidden">
      {/* ── LEFT PANE: Extracted Facts & Diarized Transcript ───────────────────────── */}
      <div className="w-full lg:w-1/2 flex flex-col min-h-0 overflow-hidden rounded-3xl border border-slate-200/90 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl shadow-xs relative">
        
        {/* Facts Header with Search & Filter Bar */}
        <div className="shrink-0 bg-slate-50/90 dark:bg-slate-800/80 p-4 border-b border-slate-200/80 dark:border-slate-800 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
              <h2 className="text-sm font-bold text-slate-900 dark:text-white font-heading m-0 uppercase tracking-wider">
                Extracted Facts &amp; Clinical Findings
              </h2>
            </div>
            <div className="flex items-center gap-2">
              {pendingCount > 0 && (
                <button
                  type="button"
                  onClick={handleConfirmAllPending}
                  disabled={actionLoading}
                  className="px-2.5 py-1 rounded-xl text-xs font-bold bg-emerald-50 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 transition-colors flex items-center gap-1 shadow-2xs"
                  title="Confirm all pending facts"
                >
                  <CheckCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Confirm All ({pendingCount})</span>
                </button>
              )}
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-200/80 dark:bg-slate-700 text-slate-700 dark:text-slate-300 font-mono font-bold">
                {consultation.findings.length}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={findingQuery}
                onChange={(e) => setFindingQuery(e.target.value)}
                placeholder="Filter facts (e.g. fever, murmur)..."
                className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
              />
            </div>
            <div className="flex items-center p-0.5 rounded-xl bg-slate-200/80 dark:bg-slate-700 text-[10px] font-bold">
              <button
                type="button"
                onClick={() => setFindingFilter("all")}
                className={`px-2 py-1 rounded-lg transition-colors ${findingFilter === "all" ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-2xs" : "text-slate-500 dark:text-slate-400"}`}
              >
                All
              </button>
              <button
                type="button"
                onClick={() => setFindingFilter("pending")}
                className={`px-2 py-1 rounded-lg transition-colors ${findingFilter === "pending" ? "bg-white dark:bg-slate-900 text-indigo-700 dark:text-indigo-400 shadow-2xs" : "text-slate-500 dark:text-slate-400"}`}
              >
                Pending
              </button>
              <button
                type="button"
                onClick={() => setFindingFilter("confirmed")}
                className={`px-2 py-1 rounded-lg transition-colors ${findingFilter === "confirmed" ? "bg-white dark:bg-slate-900 text-emerald-700 dark:text-emerald-400 shadow-2xs" : "text-slate-500 dark:text-slate-400"}`}
              >
                Confirmed
              </button>
            </div>
          </div>
        </div>

        {/* Scrollable Findings List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[220px]">
          {filteredFindings.length === 0 ? (
            <div className="py-12 text-center text-slate-400 text-xs italic">
              {findingQuery ? "No findings matching filter." : "No clinical findings recorded for this encounter."}
            </div>
          ) : (
            filteredFindings.map((finding) => (
              <div 
                key={finding.id} 
                className={`border rounded-2xl p-3.5 transition-all text-xs shadow-2xs ${
                  finding.status === "confirmed" 
                    ? "bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900/60" 
                    : finding.status === "rejected"
                      ? "bg-rose-50/50 dark:bg-rose-950/20 border-rose-200 dark:border-rose-900/60 opacity-60"
                      : "bg-white dark:bg-slate-900 border-slate-200/90 dark:border-slate-800 hover:border-indigo-300 dark:hover:border-indigo-700"
                }`}
              >
                <div className="flex justify-between items-start gap-2">
                  <div className="flex-1">
                    <span className="font-bold text-slate-900 dark:text-white text-sm">
                      {finding.finding_text || finding.value}
                    </span>
                    {finding.concept && (
                      <span className="ml-2 px-2 py-0.5 bg-blue-50 dark:bg-blue-950/50 text-blue-700 dark:text-blue-300 text-[10px] font-mono font-medium rounded-full border border-blue-200 dark:border-blue-800">
                        {finding.concept}
                      </span>
                    )}
                  </div>
                  
                  {/* Actions */}
                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      type="button"
                      onClick={() => {
                        setExplainFindingId(finding.id);
                        setRightPanel("explain");
                      }}
                      className="inline-flex items-center gap-1 text-[11px] px-2.5 py-1 bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 rounded-lg hover:bg-indigo-100 font-semibold transition-colors"
                      title="View AI extraction evidence & provenance"
                    >
                      <Brain className="w-3 h-3 text-indigo-600 dark:text-indigo-400" />
                      Evidence
                    </button>
                    {(finding.status === 'suggested' || finding.status === 'pending') && (
                      <>
                        <button 
                          type="button"
                          onClick={() => handleFindingReview(finding.id, "confirm")}
                          className="inline-flex items-center gap-1 text-[11px] px-2.5 py-1 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 rounded-lg hover:bg-emerald-100 font-bold transition-colors"
                        >
                          <Check className="w-3 h-3 text-emerald-600" /> Accept
                        </button>
                        <button 
                          type="button"
                          onClick={() => handleFindingReview(finding.id, "reject")}
                          className="inline-flex items-center gap-1 text-[11px] px-2.5 py-1 bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300 border border-rose-200 dark:border-rose-800 rounded-lg hover:bg-rose-100 font-bold transition-colors"
                        >
                          <X className="w-3 h-3 text-rose-600" /> Reject
                        </button>
                      </>
                    )}
                    {finding.status === 'confirmed' && (
                      <span className="inline-flex items-center gap-1 text-[10px] text-emerald-700 dark:text-emerald-400 font-bold bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 px-2 py-0.5 rounded-lg">
                        <Check className="w-3 h-3 text-emerald-600" /> Confirmed
                      </span>
                    )}
                    {finding.status === 'rejected' && (
                      <span className="inline-flex items-center gap-1 text-[10px] text-rose-700 dark:text-rose-400 font-bold bg-rose-50 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-800 px-2 py-0.5 rounded-lg">
                        <X className="w-3 h-3 text-rose-600" /> Rejected
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Bottom Half: Diarized Consultation Transcript */}
        <div className="h-2/5 min-h-[190px] flex flex-col border-t border-slate-200/90 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/60">
          <div className="sticky top-0 bg-slate-100/90 dark:bg-slate-800/90 backdrop-blur-md px-4 py-2.5 border-b border-slate-200/80 dark:border-slate-700 font-bold text-xs text-slate-700 dark:text-slate-300 uppercase tracking-wider z-10 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Radio className="w-3.5 h-3.5 text-indigo-500" />
              <span>Diarized Consultation Transcript</span>
            </div>
            {transcript?.segments && (
              <span className="text-[10px] text-slate-400 font-mono font-medium">
                {transcript.segments.length} speech segments
              </span>
            )}
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-2 text-xs">
            {!transcript || transcript.segments.length === 0 ? (
              <p className="text-slate-400 italic text-center py-6">
                No recorded audio transcript segments available for this encounter.
              </p>
            ) : (
              transcript.segments.map((seg) => (
                <div 
                  key={seg.id} 
                  onClick={() => setActiveSegmentId(seg.id)}
                  className={`p-2.5 rounded-xl cursor-pointer transition-colors border ${
                    activeSegmentId === seg.id 
                      ? 'bg-indigo-50/80 dark:bg-indigo-950/40 border-indigo-300 dark:border-indigo-800 shadow-2xs' 
                      : 'bg-white dark:bg-slate-900/80 border-slate-200/60 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800'
                  }`}
                >
                  <span className="font-bold text-indigo-700 dark:text-indigo-400 mr-2 uppercase tracking-wider text-[10px]">
                    {seg.speaker_label || 'Speaker'}:
                  </span>
                  <span className="text-slate-800 dark:text-slate-200 leading-relaxed font-medium">
                    {seg.clinician_corrected_text || seg.processed_text || seg.raw_text}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

      </div>

      {/* ── RIGHT PANE: Extended SOAP+ Note Editor & Verification Assistants ───────── */}
      <div className="w-full lg:w-1/2 flex flex-col min-h-0 overflow-hidden h-full rounded-3xl border border-slate-200/90 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl shadow-xs relative">
        {/* Toggle Bar for Verification Assistants */}
        <div className="bg-slate-50/90 dark:bg-slate-800/80 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800 px-4 py-2.5 flex items-center justify-between gap-2.5 relative z-20 shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider font-heading">
              Clinical Note Canvas
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setRightPanel(rightPanel === "documents" ? "none" : "documents")}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-xl transition-all shadow-2xs cursor-pointer ${
                rightPanel === "documents" 
                  ? 'bg-emerald-600 text-white shadow-emerald-600/20' 
                  : 'bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-50 border border-slate-200 dark:border-slate-600'
              }`}
            >
              <FileCheck className={`w-3.5 h-3.5 ${rightPanel === "documents" ? "text-white" : "text-emerald-600"}`} />
              <span>{rightPanel === "documents" ? "Hide Documents" : `Signed Documents (${documents.length})`}</span>
            </button>
            <button
              type="button"
              onClick={() => setRightPanel(rightPanel === "verify" ? "none" : "verify")}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-xl transition-all shadow-2xs cursor-pointer ${
                rightPanel === "verify" 
                  ? 'bg-purple-600 text-white shadow-purple-600/20' 
                  : 'bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-50 border border-slate-200 dark:border-slate-600'
              }`}
            >
              <ShieldCheck className={`w-3.5 h-3.5 ${rightPanel === "verify" ? "text-white" : "text-purple-600"}`} />
              <span>{rightPanel === "verify" ? "Hide Verifier" : "Verify Claims"}</span>
            </button>
            <button
              type="button"
              onClick={() => setRightPanel(rightPanel === "rag" ? "none" : "rag")}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-xl transition-all shadow-2xs cursor-pointer ${
                rightPanel === "rag" 
                  ? 'bg-teal-600 text-white shadow-teal-600/20' 
                  : 'bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-50 border border-slate-200 dark:border-slate-600'
              }`}
            >
              <Sparkles className={`w-3.5 h-3.5 ${rightPanel === "rag" ? "text-white" : "text-teal-600"}`} />
              <span>{rightPanel === "rag" ? "Hide RAG" : "Medical RAG"}</span>
            </button>
          </div>
        </div>

        <div className="flex flex-1 min-h-0 overflow-hidden">
          <div className={`flex-1 transition-all duration-300 h-full overflow-hidden ${rightPanel !== "none" ? 'w-1/2 border-r border-slate-200/90' : 'w-full'}`}>
            <ClinicalNoteEditor consultationId={consultationId} />
          </div>
          
          {rightPanel === "documents" && (
            <div className="w-1/2 transition-all duration-300 h-full overflow-y-auto bg-slate-50 border-l border-slate-200 p-4 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center">
                    <FileCheck className="w-4 h-4 text-emerald-700" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">Certified Documents</h3>
                    <p className="text-[11px] text-slate-500">{documents.length} verified records</p>
                  </div>
                </div>
                <Link
                  href={`/ai?cid=${consultationId}`}
                  className="flex items-center gap-1 text-[11px] font-bold text-indigo-700 hover:text-indigo-900 bg-indigo-50 px-2.5 py-1 rounded-lg border border-indigo-200"
                >
                  <Sparkles className="w-3 h-3" />
                  <span>Ask AI</span>
                </Link>
              </div>

              {documents.length === 0 ? (
                <div className="p-8 text-center bg-white rounded-2xl border border-slate-200 space-y-2.5">
                  <FileText className="w-8 h-8 text-slate-400 mx-auto" />
                  <h4 className="text-xs font-bold text-slate-800">No Certified Documents Generated Yet</h4>
                  <p className="text-[11px] text-slate-500">
                    Use DocAssist IQ AI to generate official e-prescriptions, discharge summaries, or certificates.
                  </p>
                  <Link
                    href={`/ai?cid=${consultationId}`}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 mt-2"
                  >
                    <Brain className="w-3.5 h-3.5" />
                    <span>Generate in DocAssist IQ AI</span>
                  </Link>
                </div>
              ) : (
                documents.map((d: VerifiedDocumentRecord, idx: number) => (
                  <div key={idx} className="p-3.5 rounded-2xl bg-white border border-slate-200 space-y-2.5 shadow-2xs">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-extrabold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100">
                        {d.document_type.replace(/_/g, " ")}
                      </span>
                      <span className="text-[10px] font-mono text-emerald-800 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        {d.verification_code}
                      </span>
                    </div>
                    <h4 className="text-xs font-bold text-slate-900 leading-snug">{d.title}</h4>
                    <p className="text-[11px] text-slate-500">
                      Signed by {d.doctor_name?.startsWith("Dr.") ? d.doctor_name : `Dr. ${d.doctor_name || "Attending Clinician"}`} ({d.doctor_specialty}) • {d.signed_at_formatted}
                    </p>
                    <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                      <a
                        href={`http://localhost:8000/api/v1/consultations/${encodeURIComponent(consultationId)}/documents/${encodeURIComponent(d.document_type)}/pdf`}
                        download
                        className="px-2.5 py-1 rounded-lg text-[11px] font-bold text-white bg-rose-600 hover:bg-rose-700 transition-colors"
                      >
                        PDF
                      </a>
                      <a
                        href={`http://localhost:8000/api/v1/consultations/${encodeURIComponent(consultationId)}/documents/${encodeURIComponent(d.document_type)}/docx`}
                        download
                        className="px-2.5 py-1 rounded-lg text-[11px] font-bold text-white bg-indigo-600 hover:bg-indigo-700 transition-colors"
                      >
                        DOCX
                      </a>
                      <a
                        href={`/verify?code=${encodeURIComponent(d.verification_code)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-2.5 py-1 rounded-lg text-[11px] font-bold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 transition-colors"
                      >
                        Verify
                      </a>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {rightPanel === "rag" && (
            <div className="w-1/2 transition-all duration-300 h-full overflow-y-auto bg-slate-50 border-l border-slate-200/90">
              <RAGAssistant />
            </div>
          )}

          {rightPanel === "verify" && (
            <div className="w-1/2 transition-all duration-300 h-full overflow-y-auto bg-slate-50 border-l border-slate-200/90">
              <CitationVerifier />
            </div>
          )}

          {rightPanel === "explain" && explainFindingId && (
            <div className="w-1/2 transition-all duration-300 h-full overflow-y-auto bg-slate-50 border-l border-slate-200/90 p-2">
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
