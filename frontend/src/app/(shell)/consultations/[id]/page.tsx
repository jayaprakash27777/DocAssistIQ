/**
 * DocAssistIQ — Consultation Detail View (Phase 21).
 *
 * Implements the Consultation Lifecycle State Machine & Informed Consent enforcement.
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import {
  getConsultation,
  transitionConsultationStatus,
  type ConsultationResponse,
  getActiveConsent,
  createConsent,
  revokeConsent,
  type ConsentRecordResponse,
  getTranscript,
  saveTranscript,
  correctTranscriptSegment,
  type TranscriptResponse,
  reviewClinicalFinding,
  getClinicalRepresentation,
  type ClinicalRepresentationResponse,
} from "@/lib/api";
import ClinicalNoteEditor from "@/components/clinical/ClinicalNoteEditor";
import DifferentialDiagnosis from "@/components/clinical/DifferentialDiagnosis";
import { useAudioCapture, formatElapsed } from "@/hooks/useAudioCapture";
import { getStoredToken } from "@/lib/api";
import { getSharedRealtimeClient } from "@/lib/ws";

const ALLOWED_TRANSITIONS: Record<string, string[]> = {
  "created": ["recording"],
  "recording": ["created", "processing"],
  "processing": ["draft"],
  "draft": ["under_review"],
  "under_review": ["draft", "analysis_ready"],
  "analysis_ready": ["finalized", "under_review"],
  "finalized": ["amended"],
  "amended": ["finalized"],
};

export default function ConsultationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  
  const id = Array.isArray(params.id) ? params.id[0] : params.id;
  
  const [consultation, setConsultation] = useState<ConsultationResponse | null>(null);
  const [consent, setConsent] = useState<ConsentRecordResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [inputText, setInputText] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  
  // Consent Form State
  const [showConsentForm, setShowConsentForm] = useState(false);
  const [consentActor, setConsentActor] = useState("");
  const [consentRelation, setConsentRelation] = useState("self");
  
  // Audio Capture Hook
  const audio = useAudioCapture();
  
  // ASR State
  const [asrText, setAsrText] = useState("");
  const [partialAsr, setPartialAsr] = useState("");
  const [diarizedSegments, setDiarizedSegments] = useState<any[]>([]);
  const [savedTranscript, setSavedTranscript] = useState<TranscriptResponse | null>(null);
  const [editingSegment, setEditingSegment] = useState<string | null>(null);
  const [editText, setEditText] = useState("");

  const [representation, setRepresentation] = useState<ClinicalRepresentationResponse | null>(null);

  const fetchConsultation = useCallback(async () => {
    if (!id) return;
    const res = await getConsultation(id);
    if (res.ok) {
      setConsultation(res.data);
      if (!inputText && res.data.input_text) {
        setInputText(res.data.input_text);
      }
      
      // Fetch Consent
      const consentRes = await getActiveConsent(id);
      if (consentRes.ok && consentRes.data.status === "granted") {
        setConsent(consentRes.data);
      } else {
        setConsent(null);
      }
      
      const transcriptRes = await getTranscript(id);
      if (transcriptRes.ok) {
        setSavedTranscript(transcriptRes.data);
      }
      
      // Fetch Representation
      const repRes = await getClinicalRepresentation(id);
      if (repRes.ok) {
        setRepresentation(repRes.data);
      }
    } else {
      toast.error(res.error.message || "Failed to load consultation");
      router.push("/consultations");
    }
    setLoading(false);
  }, [id, router, toast, inputText]);

  // Handle WebSocket ASR events
  useEffect(() => {
    const token = getStoredToken();
    if (!token) return;
    const client = getSharedRealtimeClient(token);
    
    const unsubscribe = client.subscribeMessages((type, payload) => {
      if (type === "asr_partial") {
        setPartialAsr(payload.text);
      } else if (type === "asr_final") {
        setAsrText(prev => prev + (prev ? " " : "") + payload.text);
        if (payload.diarization) {
          setDiarizedSegments(prev => [...prev, ...payload.diarization]);
        }
        setPartialAsr("");
      } else if (type === "asr_error") {
        toast.error(`ASR Error: ${payload.message}`);
      }
    });
    
    return () => { unsubscribe(); };
  }, [toast]);

  useEffect(() => {
    fetchConsultation();
  }, [fetchConsultation]);

  const handleTransition = async (newStatus: string) => {
    if (!consultation) return;
    
    // UI Consent Guard
    if (newStatus === "recording" && (!consent || !consent.recording_permitted)) {
      toast.error("Explicit consent is required to start recording.");
      setShowConsentForm(true);
      return;
    }
    
    setActionLoading(true);
    const res = await transitionConsultationStatus(consultation.id, {
      new_status: newStatus,
      input_text: inputText,
    });
    setActionLoading(false);
    
    if (res.ok) {
      toast.success(`Transitioned to ${newStatus.toUpperCase()}`);
      setConsultation(res.data);
      
      if (newStatus === "recording") {
        if (audio.state === "idle" || audio.state === "unavailable") {
          audio.start();
        } else if (audio.state === "paused") {
          audio.resume();
        }
      } else if (newStatus === "created" && audio.state === "recording") {
        audio.pause();
      } else if (newStatus === "processing") {
        audio.stop();
        
        // Save the live transcript locally
        if (diarizedSegments.length > 0) {
          const payload = {
            status: "ready",
            segments: diarizedSegments.map(s => ({
              start_time: s.start,
              end_time: s.end,
              speaker_label: s.speaker,
              speaker_confidence: s.confidence,
              speaker_source: s.source,
              raw_text: s.text,
              processed_text: s.text,
            }))
          };
          await saveTranscript(consultation.id, payload);
          // refresh it
          const tRes = await getTranscript(consultation.id);
          if (tRes.ok) setSavedTranscript(tRes.data);
        }
        
        setTimeout(() => {
          handleTransition("draft");
        }, 3000);
      }
    } else {
      toast.error(res.error.message || `Failed transition to ${newStatus}`);
    }
  };

  const handleSaveSegment = async (segmentId: string) => {
    if (!consultation || !editText.trim()) return;
    const res = await correctTranscriptSegment(consultation.id, segmentId, editText);
    if (res.ok) {
      toast.success("Segment corrected");
      setSavedTranscript(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          segments: prev.segments.map(s => s.id === segmentId ? res.data : s)
        };
      });
      setEditingSegment(null);
    } else {
      toast.error(res.error.message || "Failed to correct segment");
    }
  };

  const handleReviewFinding = async (findingId: string, action: 'confirm' | 'reject') => {
    if (!consultation) return;
    const res = await reviewClinicalFinding(consultation.id, findingId, action);
    if (res.ok) {
      toast.success(`Finding ${action}ed`);
      fetchConsultation(); // Refresh findings list
    } else {
      toast.error(res.error.message || `Failed to ${action} finding`);
    }
  };

  const handleGrantConsent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!consultation) return;
    setActionLoading(true);
    const res = await createConsent({
      consultation_id: consultation.id,
      actor_name: consentActor || "Patient",
      actor_relationship: consentRelation,
      purpose: "Clinical AI Analysis & Recording",
      recording_permitted: true,
    });
    setActionLoading(false);
    if (res.ok) {
      toast.success("Consent granted & recorded.");
      setConsent(res.data);
      setShowConsentForm(false);
    } else {
      toast.error(res.error.message || "Failed to grant consent.");
    }
  };

  const handleRevokeConsent = async () => {
    if (!consultation || !confirm("Are you sure you want to revoke consent? This will stop any active recording.")) return;
    setActionLoading(true);
    const res = await revokeConsent(consultation.id);
    setActionLoading(false);
    if (res.ok) {
      toast.success("Consent revoked.");
      setConsent(null);
      fetchConsultation(); // Refresh consultation in case state changed
    } else {
      toast.error(res.error.message || "Failed to revoke consent.");
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <Skeleton className="h-[20px] w-full mb-2" />
        <Skeleton className="h-[20px] w-3/4 mb-4" />
        <Skeleton className="h-[20px] w-full mb-2" />
        <Skeleton className="h-[20px] w-5/6" />
      </div>
    );
  }

  if (!consultation) return null;

  const currentStatus = consultation.status;
  const isSplitPane = ["draft", "under_review", "analysis_ready", "finalized", "amended"].includes(currentStatus);

  return (
    <div className={isSplitPane ? "flex flex-col h-[calc(100vh-64px)] bg-gray-50 overflow-hidden" : "consultations-page max-w-3xl mx-auto"}>
      <header className={`page-header flex justify-between items-center flex-wrap gap-4 ${isSplitPane ? "px-6 py-4 bg-white border-b shrink-0 m-0" : ""}`} style={isSplitPane ? { margin: 0, borderBottom: '1px solid #e5e7eb' } : { display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h2 className="page-title">Consultation Room</h2>
          <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)", marginTop: "0.5rem" }}>
            ID: {consultation.id}
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          {consent ? (
            <div style={{ background: "rgba(16, 185, 129, 0.1)", color: "var(--success)", padding: "0.5rem 1rem", borderRadius: "100px", fontSize: "0.875rem", fontWeight: 600, display: "flex", alignItems: "center", gap: "0.5rem" }}>
              ✅ Consent Granted
              {["created", "recording"].includes(currentStatus) && (
                <button onClick={handleRevokeConsent} disabled={actionLoading} style={{ background: "none", border: "none", color: "var(--danger)", textDecoration: "underline", cursor: "pointer", marginLeft: "0.5rem", fontSize: "0.75rem" }}>
                  Revoke
                </button>
              )}
            </div>
          ) : (
            <div style={{ background: "rgba(239, 68, 68, 0.1)", color: "var(--danger)", padding: "0.5rem 1rem", borderRadius: "100px", fontSize: "0.875rem", fontWeight: 600 }}>
              ⚠️ Missing Consent
            </div>
          )}
          <span className={`status-badge status-${currentStatus.toLowerCase()}`}>
            {currentStatus.toUpperCase()}
          </span>
        </div>
      </header>

      {/* Phase 42: Red Flag Banner */}
      {representation?.safety_decision && representation.safety_decision.decision !== "ALLOW" && (
        <div className="bg-red-50 border-b-4 border-red-600 p-4 shrink-0 shadow-sm animate-pulse-slow z-50 sticky top-0">
          <div className="flex items-start max-w-7xl mx-auto">
            <div className="flex-shrink-0">
              <span className="text-red-600 text-2xl" aria-hidden="true">🚨</span>
            </div>
            <div className="ml-3 w-full">
              <h3 className="text-sm font-bold text-red-800 uppercase tracking-wider mb-1 flex items-center gap-2">
                Critical Safety Warning
                <span className="bg-red-100 text-red-800 text-[10px] px-2 py-0.5 rounded-full font-mono border border-red-200">
                  v{representation.safety_decision.flags[0]?.rule_version || "1.0"}
                </span>
              </h3>
              <div className="mt-2 text-sm text-red-700 space-y-2">
                {representation.safety_decision.flags.map((flag, idx) => (
                  <div key={idx} className="bg-white/60 p-2 rounded border border-red-200 shadow-sm flex items-start gap-2">
                    <span className="mt-0.5">{flag.severity === 'CRITICAL' ? '🛑' : '⚠️'}</span>
                    <div>
                      <p className="font-semibold text-red-900 text-xs mb-0.5">{flag.category.replace('_', ' ')}</p>
                      <p className="text-red-800 text-xs font-medium">{flag.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {showConsentForm && !consent && (
        <div style={{ padding: "1rem", background: "var(--surface-base)", borderRadius: "8px", border: "1px solid var(--border-subtle)", marginTop: "1rem" }}>
          <h3 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "1rem" }}>Provide Informed Consent</h3>
          <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", marginBottom: "1rem" }}>
            To proceed with audio recording and automated analysis, we need explicit consent from the patient or legal guardian.
          </p>
          <div className="form-group">
            <label>Consent Provided By</label>
            <input 
              type="text" 
              className="form-input" 
              placeholder="e.g., John Doe" 
              value={consentActor} 
              onChange={e => setConsentActor(e.target.value)} 
            />
          </div>
          <div className="form-group">
            <label>Relationship to Patient</label>
            <select className="form-input" value={consentRelation} onChange={e => setConsentRelation(e.target.value)}>
              <option value="self">Self</option>
              <option value="parent">Parent</option>
              <option value="guardian">Legal Guardian</option>
            </select>
          </div>
          <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem" }}>
            <button className="btn-primary" onClick={handleGrantConsent} disabled={actionLoading || !consentActor}>
              Grant Consent & Proceed
            </button>
            <button className="btn-secondary" onClick={() => setShowConsentForm(false)}>
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className={isSplitPane ? "flex flex-1 overflow-hidden" : ""} style={!isSplitPane ? { background: "var(--surface-base)", padding: "1.5rem", borderRadius: "8px", marginTop: "2rem" } : {}}>
        
        {/* Left Pane (Timeline / Transcript) */}
        <div className={isSplitPane ? "flex-1 overflow-y-auto p-6 space-y-6" : "space-y-6"}>
        
        {/* Consent Form Modal (Inline) */}
        {showConsentForm && !consent && (
          <div style={{ padding: "1.5rem", background: "var(--surface-raised)", border: "1px solid var(--border-subtle)", borderRadius: "8px", marginBottom: "2rem" }}>
            <h3 style={{ marginTop: 0, color: "var(--text-primary)" }}>Informed Consent</h3>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
              By granting consent, you confirm that the patient has been informed of the clinical AI analysis and recording process, and has explicitly agreed to proceed.
            </p>
            <form onSubmit={handleGrantConsent}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.5rem" }}>
                <div className="form-group">
                  <label>Actor Name</label>
                  <input type="text" className="input-field" value={consentActor} onChange={(e) => setConsentActor(e.target.value)} required placeholder="e.g. John Doe" disabled={actionLoading} />
                </div>
                <div className="form-group">
                  <label>Relationship</label>
                  <select className="input-field" value={consentRelation} onChange={(e) => setConsentRelation(e.target.value)} disabled={actionLoading}>
                    <option value="self">Self (Patient)</option>
                    <option value="parent">Parent</option>
                    <option value="legal_guardian">Legal Guardian</option>
                    <option value="proxy">Proxy / Healthcare Surrogate</option>
                  </select>
                </div>
              </div>
              <div style={{ display: "flex", gap: "1rem" }}>
                <button type="submit" className="btn-primary" disabled={actionLoading}>Grant & Record Consent</button>
                <button type="button" className="btn-secondary" onClick={() => setShowConsentForm(false)} disabled={actionLoading}>Cancel</button>
              </div>
            </form>
          </div>
        )}

        {/* State Machine UI */}
        <div style={{ display: "flex", gap: "1rem", marginBottom: "2rem", flexWrap: "wrap" }}>
          {currentStatus === "created" && (
            <button 
              className="btn-primary" 
              onClick={() => {
                if (!consent) setShowConsentForm(true);
                else handleTransition("recording");
              }}
              disabled={actionLoading}
            >
              🎤 Start Recording
            </button>
          )}

          {currentStatus === "recording" && (
            <>
              <button 
                className="btn-primary" 
                onClick={() => handleTransition("processing")}
                disabled={actionLoading}
              >
                Submit for Analysis
              </button>
              <button 
                className="btn-secondary" 
                onClick={() => handleTransition("created")}
                disabled={actionLoading}
              >
                Pause Recording
              </button>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0 1rem", color: "var(--danger)", fontWeight: 600, background: "rgba(239, 68, 68, 0.1)", borderRadius: "8px" }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--danger)", animation: "pulse 1.5s infinite" }} />
                Recording {formatElapsed(audio.elapsedMs)}
              </div>
            </>
          )}
          
          {audio.error && (
            <div style={{ color: "var(--danger)", fontSize: "0.875rem", padding: "0.5rem", background: "rgba(239, 68, 68, 0.1)", borderRadius: "4px" }}>
              {audio.error}
            </div>
          )}
          
          {currentStatus === "processing" && (
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--primary)" }}>
              <div className="spinner" style={{ width: "20px", height: "20px", border: "2px solid var(--primary)", borderTopColor: "transparent", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
              AI is processing audio & clinical notes...
            </div>
          )}

          {currentStatus === "draft" && (
            <>
              <button className="btn-primary" onClick={() => handleTransition("under_review")} disabled={actionLoading}>
                Begin Note Review
              </button>
              <Link href={`/consultations/${consultation.id}/review`} className="btn-secondary" style={{ textDecoration: 'none' }}>
                Open Note Workspace
              </Link>
            </>
          )}

          {currentStatus === "under_review" && (
            <>
              <Link href={`/consultations/${consultation.id}/review`} className="btn-primary" style={{ textDecoration: 'none' }}>
                Open Review Workspace
              </Link>
              <button className="btn-secondary" onClick={() => handleTransition("analysis_ready")} disabled={actionLoading}>
                Mark Analysis Ready
              </button>
              <button className="btn-secondary" onClick={() => handleTransition("draft")} disabled={actionLoading}>
                Back to Draft
              </button>
            </>
          )}

          {currentStatus === "analysis_ready" && (
            <>
              <button className="btn-primary" onClick={() => handleTransition("finalized")} disabled={actionLoading}>
                Sign Off & Finalize
              </button>
              <button className="btn-secondary" onClick={() => handleTransition("under_review")} disabled={actionLoading}>
                Re-review
              </button>
            </>
          )}

          {currentStatus === "finalized" && (
            <button className="btn-secondary" onClick={() => handleTransition("amended")} disabled={actionLoading}>
              Amend Finalized Record
            </button>
          )}

          {currentStatus === "amended" && (
            <button className="btn-primary" onClick={() => handleTransition("finalized")} disabled={actionLoading}>
              Sign Off Amendment
            </button>
          )}
        </div>

        {/* Input Text Area */}
        <div className="form-group">
          <label style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span>Clinical Notes / Transcript</span>
            <Link href={`/consultations/${id}/intake`} className="btn-secondary btn-sm" style={{ textDecoration: "none" }}>
              📝 Open Structured Manual Intake
            </Link>
          </label>
          
          {(asrText || partialAsr) && currentStatus === "recording" && (
            <div style={{ marginBottom: "1rem", padding: "1rem", background: "var(--surface-raised)", border: "1px solid var(--border-subtle)", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--primary)", fontWeight: 600, marginBottom: "0.5rem" }}>
                LIVE TRANSCRIPT (DIARIZED)
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {diarizedSegments.map((seg, idx) => (
                  <div key={idx} style={{ padding: "0.5rem", background: "var(--surface-base)", borderRadius: "4px" }}>
                    <div style={{ fontSize: "0.75rem", color: seg.confidence < 0.5 ? "var(--warning)" : "var(--text-secondary)", fontWeight: 600, marginBottom: "0.25rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <span>{seg.speaker || "Unknown Speaker"}</span>
                      <span style={{ opacity: 0.5 }}>{seg.start.toFixed(1)}s - {seg.end.toFixed(1)}s</span>
                      {seg.confidence < 0.5 && <span style={{ background: "rgba(245, 158, 11, 0.1)", padding: "2px 6px", borderRadius: "100px", fontSize: "0.65rem" }}>Low Confidence (Heuristic)</span>}
                    </div>
                    <div style={{ lineHeight: 1.5, color: "var(--text-primary)" }}>{seg.text}</div>
                  </div>
                ))}
                
                {(partialAsr || (asrText && diarizedSegments.length === 0)) && (
                  <div style={{ padding: "0.5rem" }}>
                    {diarizedSegments.length === 0 && <span style={{ lineHeight: 1.5 }}>{asrText}</span>}
                    <span style={{ opacity: 0.5, lineHeight: 1.5 }}> {partialAsr}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Clinical Findings (NLP Extracted) */}
          {consultation?.findings && consultation.findings.length > 0 && (
            <div style={{ marginBottom: "1rem", padding: "1rem", background: "var(--surface-raised)", border: "1px solid var(--border-subtle)", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--primary)", fontWeight: 600, marginBottom: "0.75rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span>EXTRACTED CLINICAL FINDINGS (NLP)</span>
                <span style={{ fontSize: "0.65rem", padding: "2px 6px", background: "rgba(16, 185, 129, 0.1)", color: "var(--success)", borderRadius: "100px" }}>
                  AI Suggested
                </span>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                {consultation.findings.map((finding: any) => (
                  <div key={finding.id} style={{ 
                    padding: "0.5rem 0.75rem", 
                    background: finding.negated ? "rgba(239, 68, 68, 0.05)" : "var(--surface-base)", 
                    border: finding.negated ? "1px solid rgba(239, 68, 68, 0.2)" : "1px solid var(--border-subtle)",
                    borderRadius: "6px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.25rem",
                    minWidth: "150px"
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontSize: "0.85rem", fontWeight: 600, color: finding.negated ? "var(--error)" : "var(--text-primary)", textTransform: "capitalize" }}>
                        {finding.value}
                      </span>
                      {finding.confidence_score && (
                        <span style={{ fontSize: "0.65rem", color: "var(--text-tertiary)" }}>
                          {(finding.confidence_score * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                    {finding.canonical_concept && finding.canonical_concept !== finding.value.toLowerCase() && (
                      <div style={{ fontSize: "0.7rem", color: "var(--text-secondary)", fontStyle: "italic", marginBottom: "0.25rem" }}>
                        ↳ Mapped: {finding.canonical_concept}
                        {finding.mapping_source && <span style={{ opacity: 0.6, fontSize: "0.6rem", marginLeft: "4px" }}>({finding.mapping_source})</span>}
                      </div>
                    )}
                    <div style={{ display: "flex", gap: "0.25rem", flexWrap: "wrap", flex: 1 }}>
                      <span style={{ fontSize: "0.65rem", padding: "2px 4px", background: "var(--surface-sunken)", borderRadius: "4px", color: "var(--text-secondary)" }}>
                        {finding.concept || finding.finding_type}
                      </span>
                      {finding.temporality && finding.temporality !== "current" && (
                        <span style={{ fontSize: "0.65rem", padding: "2px 4px", background: "rgba(245, 158, 11, 0.1)", borderRadius: "4px", color: "var(--warning)" }}>
                          {finding.temporality}
                        </span>
                      )}
                      {finding.negated && (
                        <span style={{ fontSize: "0.65rem", padding: "2px 4px", background: "rgba(239, 68, 68, 0.1)", borderRadius: "4px", color: "var(--error)" }}>
                          negated
                        </span>
                      )}
                      {finding.status === "confirmed" && (
                        <span style={{ fontSize: "0.65rem", padding: "2px 4px", background: "rgba(16, 185, 129, 0.1)", borderRadius: "4px", color: "var(--success)" }}>
                          ✓ Confirmed
                        </span>
                      )}
                      {finding.status === "rejected" && (
                        <span style={{ fontSize: "0.65rem", padding: "2px 4px", background: "rgba(239, 68, 68, 0.1)", borderRadius: "4px", color: "var(--error)" }}>
                          ✗ Rejected
                        </span>
                      )}
                    </div>
                    {finding.status === "pending" && (
                      <div style={{ display: "flex", gap: "0.25rem", marginTop: "0.25rem" }}>
                        <button className="btn-secondary btn-sm" style={{ padding: "2px 6px", fontSize: "0.65rem", flex: 1 }} onClick={() => handleReviewFinding(finding.id, "reject")}>Reject</button>
                        <button className="btn-primary btn-sm" style={{ padding: "2px 6px", fontSize: "0.65rem", flex: 1 }} onClick={() => handleReviewFinding(finding.id, "confirm")}>Confirm</button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Differential Diagnosis (Top-5) */}
          {consultation && <DifferentialDiagnosis consultationId={consultation.id} />}

          {/* Transcript Editor */}
          {savedTranscript && ["draft", "under_review", "finalized"].includes(currentStatus) && (
            <div style={{ marginBottom: "1rem", padding: "1rem", background: "var(--surface-raised)", border: "1px solid var(--border-subtle)", borderRadius: "8px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: 600 }}>
                  TRANSCRIPT EDITOR (AUDITED)
                </div>
                <div style={{ fontSize: "0.7rem", color: "var(--text-tertiary)" }}>
                  Click any segment to correct it. Edits are versioned.
                </div>
              </div>
              
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxHeight: "400px", overflowY: "auto" }}>
                {savedTranscript.segments.map(seg => (
                  <div 
                    key={seg.id} 
                    style={{ 
                      padding: "0.75rem", 
                      background: "var(--surface-base)", 
                      borderRadius: "6px",
                      border: "1px solid var(--border-subtle)",
                      cursor: currentStatus !== "finalized" ? "pointer" : "default"
                    }}
                    onClick={() => {
                      if (currentStatus !== "finalized" && editingSegment !== seg.id) {
                        setEditingSegment(seg.id);
                        setEditText(seg.clinician_corrected_text || seg.processed_text);
                      }
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: 600, display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <span>{seg.speaker_label || "Unknown"}</span>
                        <span style={{ opacity: 0.5 }}>{seg.start_time.toFixed(1)}s - {seg.end_time.toFixed(1)}s</span>
                      </div>
                      {seg.is_corrected && (
                        <div style={{ fontSize: "0.65rem", padding: "2px 6px", background: "rgba(16, 185, 129, 0.1)", color: "var(--success)", borderRadius: "100px", fontWeight: 600 }}>
                          Clinician Corrected
                        </div>
                      )}
                    </div>
                    
                    {editingSegment === seg.id ? (
                      <div onClick={(e) => e.stopPropagation()}>
                        <textarea
                          autoFocus
                          className="input-field"
                          rows={3}
                          value={editText}
                          onChange={(e) => setEditText(e.target.value)}
                          style={{ marginBottom: "0.5rem" }}
                        />
                        <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
                          <button className="btn-secondary btn-sm" onClick={() => setEditingSegment(null)}>Cancel</button>
                          <button className="btn-primary btn-sm" onClick={() => handleSaveSegment(seg.id)}>Save Correction</button>
                        </div>
                      </div>
                    ) : (
                      <div style={{ lineHeight: 1.5, color: seg.is_corrected ? "var(--text-primary)" : "var(--text-secondary)" }}>
                        {seg.clinician_corrected_text || seg.processed_text}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          <textarea
            className="input-field"
            rows={10}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={
              actionLoading || 
              currentStatus === "processing" || 
              currentStatus === "finalized"
            }
            placeholder={
              currentStatus === "recording" 
                ? "Recording in progress... (type manual notes here)" 
                : "Enter clinical notes..."
            }
            style={{ fontFamily: "monospace", resize: "vertical" }}
          />
        </div>
        </div>

        {/* Right Pane (Clinical Note Editor) */}
        {isSplitPane && (
          <div className="w-[600px] xl:w-[700px] shrink-0 border-l border-gray-200 bg-white overflow-y-auto shadow-sm">
            <ClinicalNoteEditor consultationId={consultation.id} />
          </div>
        )}
      </div>
    </div>
  );
}
