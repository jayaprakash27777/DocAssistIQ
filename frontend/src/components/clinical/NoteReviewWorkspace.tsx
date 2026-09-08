"use client";

import React, { useState, useEffect } from "react";
import { getClinicalNote, getConsultation, getTranscript, reviewClinicalFinding } from "@/lib/api";
import type { ConsultationResponse, TranscriptResponse, ClinicalFindingResponse } from "@/lib/api";
import ClinicalNoteEditor from "@/components/clinical/ClinicalNoteEditor";

export default function NoteReviewWorkspace({ consultationId }: { consultationId: string }) {
  const [consultation, setConsultation] = useState<ConsultationResponse | null>(null);
  const [transcript, setTranscript] = useState<TranscriptResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeSegmentId, setActiveSegmentId] = useState<string | null>(null);

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
    <div className="flex flex-col lg:flex-row h-[calc(100vh-100px)] gap-4 w-full">
      {/* LEFT PANE: Transcript and Extracted Facts */}
      <div className="w-full lg:w-1/2 flex flex-col gap-4 overflow-hidden border rounded-md shadow-sm bg-white">
        
        {/* Facts / Findings */}
        <div className="flex-1 overflow-y-auto border-b">
          <div className="sticky top-0 bg-gray-50 p-3 border-b font-semibold text-sm text-gray-700 z-10">
            Extracted Facts & Findings
          </div>
          <div className="p-4 space-y-3">
            {consultation.findings.length === 0 ? (
              <p className="text-sm text-gray-500">No findings extracted.</p>
            ) : (
              consultation.findings.map((finding) => (
                <div key={finding.id} className="border rounded-md p-3 bg-gray-50 hover:bg-white transition-colors text-sm">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <span className="font-medium text-gray-800">{finding.finding_text}</span>
                      {finding.concept && (
                        <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded border border-blue-200">
                          {finding.concept}
                        </span>
                      )}
                    </div>
                    <div className="flex gap-2 shrink-0 ml-4">
                      {finding.status === 'suggested' && (
                        <>
                          <button 
                            onClick={() => handleFindingReview(finding.id, "confirm")}
                            className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                          >
                            Accept
                          </button>
                          <button 
                            onClick={() => handleFindingReview(finding.id, "reject")}
                            className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                          >
                            Reject
                          </button>
                        </>
                      )}
                      {finding.status === 'confirmed' && (
                        <span className="text-xs text-green-600 font-medium bg-green-50 px-2 py-1 rounded">✓ Confirmed</span>
                      )}
                      {finding.status === 'rejected' && (
                        <span className="text-xs text-red-600 font-medium bg-red-50 px-2 py-1 rounded">✗ Rejected</span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Transcript Reference */}
        <div className="h-1/3 min-h-[200px] overflow-y-auto bg-gray-50">
          <div className="sticky top-0 bg-gray-100 p-2 border-b font-semibold text-xs text-gray-600 uppercase tracking-wider z-10 shadow-sm">
            Source Transcript
          </div>
          <div className="p-4 space-y-2 text-sm">
            {!transcript || transcript.segments.length === 0 ? (
              <p className="text-gray-500 italic">No transcript available.</p>
            ) : (
              transcript.segments.map((seg) => (
                <div 
                  key={seg.id} 
                  className={`p-2 rounded transition-colors ${activeSegmentId === seg.id ? 'bg-yellow-100 border border-yellow-300 shadow-sm' : 'hover:bg-gray-100'}`}
                >
                  <span className="font-semibold text-gray-600 text-xs mr-2 w-16 inline-block">
                    {seg.speaker_label || 'Unknown'}:
                  </span>
                  <span className="text-gray-800">{seg.clinician_corrected_text || seg.processed_text || seg.raw_text}</span>
                </div>
              ))
            )}
          </div>
        </div>

      </div>

      {/* RIGHT PANE: Note Editor */}
      <div className="w-full lg:w-1/2 flex flex-col overflow-hidden h-full">
        <ClinicalNoteEditor consultationId={consultationId} />
      </div>
    </div>
  );
}
