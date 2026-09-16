/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * DocAssistIQ — Consultation Detail View (Phase 21).
 *
 * Implements the Consultation Lifecycle State Machine & Informed Consent enforcement.
 */

"use client";

import { useCallback, useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import { Button } from "@/components/ui/button";
import * as Tabs from "@radix-ui/react-tabs";
import { GripVertical, Mic, Square, CheckCircle, FileText, Activity, AlertCircle } from "lucide-react";
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
import LiveTranscriptionPanel from "@/components/clinical/LiveTranscriptionPanel";
import TranscriptEditorPanel from "@/components/clinical/TranscriptEditorPanel";
import AuditTimeline from "@/components/clinical/AuditTimeline";
import { SimilarCasesPanel } from "@/components/clinical/SimilarCasesPanel";
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
  const [pendingTransition, setPendingTransition] = useState<string | null>(null);
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

  // Resizable pane state
  const [rightPaneWidth, setRightPaneWidth] = useState(600);
  const isDragging = useRef(false);

  const startDragging = useCallback((e: React.MouseEvent) => {
    isDragging.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, []);

  const onDrag = useCallback((e: MouseEvent) => {
    if (!isDragging.current) return;
    const newWidth = window.innerWidth - e.clientX;
    // Constrain width between 400px and 900px
    setRightPaneWidth(Math.min(Math.max(newWidth, 400), 900));
  }, []);

  const stopDragging = useCallback(() => {
    isDragging.current = false;
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }, []);

  useEffect(() => {
    window.addEventListener('mousemove', onDrag);
    window.addEventListener('mouseup', stopDragging);
    return () => {
      window.removeEventListener('mousemove', onDrag);
      window.removeEventListener('mouseup', stopDragging);
    };
  }, [onDrag, stopDragging]);

  const fetchConsultation = useCallback(async () => {
    if (!id) return;
    const res = await getConsultation(id);
    if (res.ok) {
      setConsultation(res.data);
      setInputText(prev => {
        if (!prev && res.data.input_text) return res.data.input_text;
        return prev;
      });
      
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
  }, [id, router, toast]);

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
      setPendingTransition(newStatus);
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
      
      if (pendingTransition) {
        const transition = pendingTransition;
        setPendingTransition(null);
        handleTransition(transition);
      }
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
    <div className="flex flex-col h-[calc(100vh-64px)] bg-[var(--surface-base)] overflow-hidden relative">
      
      {/* Sticky Premium Header */}
      <header className="px-6 py-4 bg-[var(--glass-bg)] backdrop-blur-xl border-b border-[var(--glass-border)] shrink-0 z-20 flex justify-between items-center shadow-sm sticky top-0">
        <div>
          <h2 className="text-xl font-bold font-heading text-[var(--text-primary)] flex items-center gap-3">
            Consultation Workspace
            <span className={`px-2.5 py-1 rounded-full text-[10px] uppercase tracking-widest font-bold ${
              currentStatus === 'finalized' ? 'bg-[var(--color-success-50)] text-[var(--color-success-700)] border border-[var(--color-success-200)]' : 
              currentStatus === 'recording' ? 'bg-[var(--color-danger-50)] text-[var(--color-danger-700)] border border-[var(--color-danger-200)] animate-pulse' : 
              'bg-[var(--color-primary-50)] text-[var(--color-primary-700)] border border-[var(--color-primary-200)]'
            }`}>
              {currentStatus.replace('_', ' ')}
            </span>
          </h2>
          <div className="text-xs text-[var(--text-tertiary)] mt-1 font-mono">
            ID: {consultation.id}
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          {consent ? (
            <div className="flex items-center gap-2 bg-[var(--color-success-50)] text-[var(--color-success-700)] px-3 py-1.5 rounded-full border border-[var(--color-success-200)] shadow-sm">
              <CheckCircle className="w-4 h-4" />
              <span className="text-xs font-bold uppercase tracking-wide">Consent Granted</span>
              {["created", "recording"].includes(currentStatus) && (
                <button onClick={handleRevokeConsent} disabled={actionLoading} className="ml-2 text-[10px] underline hover:text-[var(--color-danger-600)] transition-colors">
                  Revoke
                </button>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2 bg-[var(--color-danger-50)] text-[var(--color-danger-700)] px-3 py-1.5 rounded-full border border-[var(--color-danger-200)] shadow-sm">
              <AlertCircle className="w-4 h-4" />
              <span className="text-xs font-bold uppercase tracking-wide">Missing Consent</span>
            </div>
          )}
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

      {/* Phase 42: Red Flag Banner */}

        {/* Main Content Area */}
        <div className={`flex flex-1 overflow-hidden relative ${!isSplitPane ? 'max-w-4xl mx-auto w-full' : ''}`}>
        
        {/* Left Pane (Timeline / Transcript) */}
        <div className="flex-1 flex flex-col h-full bg-white relative">
          {/* Consent Form */}
          <div className="px-6 pt-6 shrink-0">
            <AnimatePresence>
              {showConsentForm && !consent && (
                <motion.div 
                  initial={{ opacity: 0, y: 10, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="p-6 bg-white border border-[var(--border-default)] rounded-2xl shadow-sm mb-4 relative overflow-hidden"
                >
                  <div className="absolute top-0 left-0 w-1 h-full bg-[var(--color-primary-500)]" />
                  <div className="flex items-start gap-4 mb-6">
                    <div className="p-3 bg-[var(--color-primary-50)] rounded-xl text-[var(--color-primary-600)] shrink-0 shadow-inner">
                      <FileText className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold font-heading text-[var(--text-primary)] m-0">Informed Consent Required</h3>
                      <p className="text-[var(--text-secondary)] mt-1 text-sm">
                        By granting consent, you confirm that the patient has been informed of the clinical AI analysis and recording process, and has explicitly agreed to proceed.
                      </p>
                    </div>
                  </div>
                  
                  <form onSubmit={handleGrantConsent}>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-6">
                      <div>
                        <label className="block text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-wider mb-2">Actor Name</label>
                        <input 
                          type="text" 
                          className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl p-3 text-sm text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] outline-none transition-all shadow-inner" 
                          value={consentActor} 
                          onChange={(e) => setConsentActor(e.target.value)} 
                          required 
                          placeholder="e.g. John Doe" 
                          disabled={actionLoading} 
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-wider mb-2">Relationship</label>
                        <select 
                          className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl p-3 text-sm text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] outline-none transition-all shadow-inner" 
                          value={consentRelation} 
                          onChange={(e) => setConsentRelation(e.target.value)} 
                          disabled={actionLoading}
                        >
                          <option value="self">Self (Patient)</option>
                          <option value="parent">Parent</option>
                          <option value="legal_guardian">Legal Guardian</option>
                          <option value="proxy">Proxy / Healthcare Surrogate</option>
                        </select>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 border-t border-[var(--border-default)] pt-5">
                      <Button type="submit" variant="primary" disabled={actionLoading} isLoading={actionLoading}>
                        Grant & Record Consent
                      </Button>
                      <Button type="button" variant="ghost" onClick={() => setShowConsentForm(false)} disabled={actionLoading}>
                        Cancel
                      </Button>
                    </div>
                  </form>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <Tabs.Root defaultValue="ai-assistant" className="flex flex-col h-full">
            <div className="px-6 border-b border-[var(--border-default)] shrink-0">
              <Tabs.List className="flex gap-6">
                <Tabs.Trigger 
                  value="ai-assistant" 
                  className="pb-3 text-sm font-bold uppercase tracking-wider text-[var(--text-tertiary)] data-[state=active]:text-[var(--color-primary-600)] data-[state=active]:border-b-2 data-[state=active]:border-[var(--color-primary-600)] transition-colors hover:text-[var(--text-primary)] outline-none"
                >
                  AI Assistant
                </Tabs.Trigger>
                <Tabs.Trigger 
                  value="transcript" 
                  className="pb-3 text-sm font-bold uppercase tracking-wider text-[var(--text-tertiary)] data-[state=active]:text-[var(--color-primary-600)] data-[state=active]:border-b-2 data-[state=active]:border-[var(--color-primary-600)] transition-colors hover:text-[var(--text-primary)] outline-none"
                >
                  Transcript & Review
                </Tabs.Trigger>
                <Tabs.Trigger 
                  value="scratchpad" 
                  className="pb-3 text-sm font-bold uppercase tracking-wider text-[var(--text-tertiary)] data-[state=active]:text-[var(--color-primary-600)] data-[state=active]:border-b-2 data-[state=active]:border-[var(--color-primary-600)] transition-colors hover:text-[var(--text-primary)] outline-none"
                >
                  Scratchpad
                </Tabs.Trigger>
              </Tabs.List>
            </div>

            <div className="flex-1 overflow-y-auto p-6 pb-32">
              
              <Tabs.Content value="ai-assistant" className="space-y-6 outline-none">
                <div className="mb-6">
                  <LiveTranscriptionPanel
                    audioState={audio.state}
                    audioStream={audio.stream}
                    asrText={asrText}
                    partialAsr={partialAsr}
                    diarizedSegments={diarizedSegments}
                    elapsedMs={audio.elapsedMs}
                    onStart={() => handleTransition("recording")}
                    onPause={() => audio.pause()}
                    onStop={() => handleTransition("processing")}
                  />
                </div>
                
                {consultation?.findings && consultation.findings.length > 0 && (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-6 p-5 bg-white border border-[var(--color-primary-200)] shadow-sm rounded-2xl relative overflow-hidden"
                  >
                    <div className="absolute top-0 left-0 w-1 h-full bg-[var(--color-primary-500)]" />
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-sm font-bold tracking-wide text-[var(--color-primary-800)] uppercase flex items-center gap-2 m-0">
                        <Activity className="w-4 h-4" />
                        Extracted Clinical Findings
                      </h3>
                      <span className="text-[0.65rem] font-bold px-2.5 py-1 bg-[var(--color-primary-50)] text-[var(--color-primary-700)] rounded-full uppercase tracking-widest border border-[var(--color-primary-200)] flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-primary-500)] animate-pulse" />
                        AI Suggested
                      </span>
                    </div>
                    
                    <div className="flex flex-wrap gap-2.5">
                      {consultation.findings.map((finding: any) => (
                        <motion.div 
                          key={finding.id} 
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          whileHover={{ scale: 1.02 }}
                          className={`p-3 rounded-xl border flex flex-col gap-1.5 min-w-[160px] shadow-sm transition-colors ${
                            finding.negated 
                              ? "bg-[var(--color-danger-50)] border-[var(--color-danger-200)]" 
                              : finding.status === "confirmed" 
                                ? "bg-[var(--color-success-50)] border-[var(--color-success-200)]"
                                : "bg-white border-[var(--border-default)] hover:border-[var(--color-primary-300)]"
                          }`}
                        >
                          <div className="flex justify-between items-start gap-2">
                            <span className={`text-sm font-bold capitalize ${finding.negated ? "text-[var(--color-danger-700)] line-through opacity-80" : "text-[var(--text-primary)]"}`}>
                              {finding.value}
                            </span>
                            {finding.confidence_score && (
                              <span className="text-[0.65rem] font-mono text-[var(--text-tertiary)] bg-[var(--surface-sunken)] px-1.5 rounded">
                                {(finding.confidence_score * 100).toFixed(0)}%
                              </span>
                            )}
                          </div>
                          
                          {finding.canonical_concept && finding.canonical_concept !== finding.value.toLowerCase() && (
                            <div className="text-[0.7rem] text-[var(--text-secondary)] italic flex items-center gap-1">
                              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 10 4 15 9 20"></polyline><path d="M20 4v7a4 4 0 0 1-4 4H4"></path></svg>
                              {finding.canonical_concept}
                              {finding.mapping_source && <span className="opacity-60">({finding.mapping_source})</span>}
                            </div>
                          )}
                          
                          <div className="flex flex-wrap gap-1.5 mt-1">
                            <span className="text-[0.65rem] px-1.5 py-0.5 bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded text-[var(--text-secondary)] font-medium">
                              {finding.concept || finding.finding_type}
                            </span>
                            {finding.temporality && finding.temporality !== "current" && (
                              <span className="text-[0.65rem] px-1.5 py-0.5 bg-[var(--color-warning-50)] border border-[var(--color-warning-200)] rounded text-[var(--color-warning-700)] font-medium">
                                {finding.temporality}
                              </span>
                            )}
                            {finding.negated && (
                              <span className="text-[0.65rem] px-1.5 py-0.5 bg-[var(--color-danger-100)] text-[var(--color-danger-700)] rounded font-bold">
                                NEGATED
                              </span>
                            )}
                            {finding.status === "confirmed" && (
                              <span className="text-[0.65rem] px-1.5 py-0.5 bg-[var(--color-success-100)] text-[var(--color-success-700)] rounded font-bold flex items-center gap-1">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
                                CONFIRMED
                              </span>
                            )}
                            {finding.status === "rejected" && (
                              <span className="text-[0.65rem] px-1.5 py-0.5 bg-[var(--color-danger-100)] text-[var(--color-danger-700)] rounded font-bold flex items-center gap-1">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                                REJECTED
                              </span>
                            )}
                          </div>
                          
                          {finding.status === "pending" && (
                            <div className="flex gap-1.5 mt-2 pt-2 border-t border-[var(--border-default)]">
                              <button type="button" className="flex-1 py-1 px-2 text-[0.65rem] font-bold rounded bg-[var(--surface-sunken)] hover:bg-[var(--color-danger-50)] hover:text-[var(--color-danger-600)] transition-colors border border-[var(--border-default)]" onClick={() => handleReviewFinding(finding.id, "reject")}>Reject</button>
                              <button type="button" className="flex-1 py-1 px-2 text-[0.65rem] font-bold rounded bg-[var(--color-primary-50)] text-[var(--color-primary-700)] hover:bg-[var(--color-primary-100)] transition-colors border border-[var(--color-primary-200)]" onClick={() => handleReviewFinding(finding.id, "confirm")}>Confirm</button>
                            </div>
                          )}
                        </motion.div>
                      ))}
                    </div>
                  </motion.div>
                )}

                {consultation && <DifferentialDiagnosis consultationId={consultation.id} trigger={consultation.findings?.length || consultation.status} />}
                
                {consultation && (
                  <div style={{ marginBottom: "1rem" }}>
                    <SimilarCasesPanel consultationId={consultation.id} />
                  </div>
                )}
              </Tabs.Content>

              <Tabs.Content value="transcript" className="space-y-6 outline-none">
                {savedTranscript && ["draft", "under_review", "finalized"].includes(currentStatus) ? (
                  <div style={{ marginBottom: "1rem" }}>
                    <TranscriptEditorPanel
                      transcript={savedTranscript}
                      currentStatus={currentStatus}
                      onSaveSegment={handleSaveSegment}
                    />
                  </div>
                ) : (
                  <div className="text-center text-[var(--text-tertiary)] py-12 bg-[var(--surface-sunken)] rounded-xl border border-dashed border-[var(--border-default)]">
                    No transcript available yet. Please complete a recording session.
                  </div>
                )}
                
                {consultation && (
                  <div className="mt-8 border-t border-[var(--border-default)] pt-8">
                    <h3 className="text-lg font-bold mb-4 font-heading">Consultation Audit Trail</h3>
                    <AuditTimeline consultationId={consultation.id} />
                  </div>
                )}
              </Tabs.Content>

              <Tabs.Content value="scratchpad" className="space-y-6 outline-none h-full flex flex-col">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-sm font-bold tracking-wide text-[var(--color-primary-800)] uppercase">
                    Unstructured Doctor Notes
                  </h3>
                  <Link href={`/consultations/${id}/intake`} className="text-xs font-bold text-[var(--color-primary-600)] hover:underline flex items-center gap-1">
                    📝 Open Structured Intake Form
                  </Link>
                </div>
                <textarea
                  className="flex-1 w-full min-h-[300px] bg-yellow-50/50 border border-yellow-200 rounded-xl p-4 text-[var(--text-primary)] shadow-inner focus:ring-2 focus:ring-yellow-400 outline-none transition-all resize-none font-mono"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  disabled={
                    actionLoading || 
                    currentStatus === "processing" || 
                    currentStatus === "finalized"
                  }
                  placeholder={
                    currentStatus === "recording" 
                      ? "Recording in progress... (type manual scratchpad notes here)" 
                      : "Type free-form notes during the consultation..."
                  }
                />
                <div className="flex justify-end mt-4">
                  <Button 
                    variant="primary" 
                    onClick={() => handleTransition("draft")}
                    disabled={actionLoading || !inputText.trim() || currentStatus === "finalized"}
                    isLoading={actionLoading}
                    className="shadow-md"
                  >
                    Analyze Notes
                  </Button>
                </div>
              </Tabs.Content>
            </div>
          </Tabs.Root>

          {/* Floating Action Bar (Phase 5) */}
          <motion.div 
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="absolute bottom-6 left-1/2 -translate-x-1/2 z-50 bg-[var(--glass-bg)] backdrop-blur-xl border border-[var(--glass-border)] shadow-2xl rounded-full px-4 py-3 flex items-center gap-3"
          >
            {currentStatus === "created" && (
              <Button 
                variant="primary" 
                onClick={() => {
                  if (!consent) setShowConsentForm(true);
                  else handleTransition("recording");
                }}
                disabled={actionLoading}
                className="rounded-full shadow-lg gap-2 px-6"
              >
                <Mic className="w-4 h-4" /> Start Recording
              </Button>
            )}

            {currentStatus === "recording" && (
              <>
                <Button 
                  variant="primary" 
                  onClick={() => handleTransition("processing")}
                  disabled={actionLoading}
                  className="rounded-full shadow-lg px-6"
                >
                  Submit for Analysis
                </Button>
                <Button 
                  variant="ghost" 
                  onClick={() => handleTransition("created")}
                  disabled={actionLoading}
                  className="rounded-full gap-2 text-[var(--color-danger-600)] hover:bg-[var(--color-danger-50)] bg-white/50"
                >
                  <Square className="w-4 h-4" /> Stop
                </Button>
                <div className="px-4 font-mono text-sm font-bold text-[var(--color-danger-600)] flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[var(--color-danger-500)] animate-pulse" />
                  {formatElapsed(audio.elapsedMs)}
                </div>
              </>
            )}

            {currentStatus === "processing" && (
              <div className="px-6 flex items-center gap-3 text-sm font-bold text-[var(--color-primary-600)]">
                <span className="w-4 h-4 rounded-full border-2 border-[var(--color-primary-600)] border-t-transparent animate-spin" />
                AI is processing audio & notes...
              </div>
            )}

            {currentStatus === "draft" && (
              <Button variant="primary" onClick={() => handleTransition("under_review")} disabled={actionLoading} className="rounded-full shadow-lg px-6">
                Begin Note Review
              </Button>
            )}

            {currentStatus === "under_review" && (
              <>
                <Button variant="primary" onClick={() => handleTransition("analysis_ready")} disabled={actionLoading} className="rounded-full shadow-lg px-6">
                  Mark Analysis Ready
                </Button>
                <Button variant="ghost" onClick={() => handleTransition("draft")} disabled={actionLoading} className="rounded-full bg-white/50">
                  Back to Draft
                </Button>
              </>
            )}

            {currentStatus === "analysis_ready" && (
              <>
                <Button variant="primary" onClick={() => handleTransition("finalized")} disabled={actionLoading} className="rounded-full shadow-lg px-6 gap-2">
                  <CheckCircle className="w-4 h-4" /> Sign Off & Finalize
                </Button>
                <Button variant="ghost" onClick={() => handleTransition("under_review")} disabled={actionLoading} className="rounded-full bg-white/50">
                  Re-review
                </Button>
              </>
            )}

            {currentStatus === "finalized" && (
              <Button variant="ghost" onClick={() => handleTransition("amended")} disabled={actionLoading} className="rounded-full bg-white/50 border border-[var(--border-default)]">
                Amend Finalized Record
              </Button>
            )}

            {currentStatus === "amended" && (
              <Button variant="primary" onClick={() => handleTransition("finalized")} disabled={actionLoading} className="rounded-full shadow-lg px-6 gap-2">
                <CheckCircle className="w-4 h-4" /> Sign Off Amendment
              </Button>
            )}
          </motion.div>
        </div>
        
        {/* Resizable Divider */}
        {isSplitPane && (
          <div 
            className="w-2 bg-[var(--surface-base)] hover:bg-[var(--color-primary-200)] flex items-center justify-center cursor-col-resize transition-colors border-l border-r border-[var(--border-default)] z-10 shrink-0 group/divider"
            onMouseDown={startDragging}
          >
            <GripVertical className="w-4 h-4 text-[var(--text-tertiary)] group-hover/divider:text-[var(--color-primary-600)]" />
          </div>
        )}

        {/* Right Pane (Clinical Note Editor) */}
        {isSplitPane && (
          <div 
            className="shrink-0 bg-white overflow-y-auto shadow-[-4px_0_24px_rgba(0,0,0,0.02)] relative z-0" 
            style={{ width: `${rightPaneWidth}px` }}
          >
            <ClinicalNoteEditor consultationId={consultation.id} />
          </div>
        )}
      </div>
    </div>
  );
}
