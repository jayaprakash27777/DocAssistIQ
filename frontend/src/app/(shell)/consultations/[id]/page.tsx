/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * DocAssistIQ — Consultation Detail View & Executive Clinical Workspace.
 *
 * Implements the Consultation Lifecycle State Machine, Informed Consent enforcement,
 * Real-time Speech-to-Text Diarization, AI Fact Extraction, Differential Diagnosis Engine,
 * Clinical Evidence Verification (RAG & Citations), and Extended SOAP+ Clinical Note Synthesis.
 */

"use client";

import React, { useCallback, useEffect, useState, useRef, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import { Button } from "@/components/ui/button";
import * as Tabs from "@radix-ui/react-tabs";
import { 
  GripVertical, 
  Mic, 
  Square, 
  CheckCircle, 
  FileText, 
  Activity, 
  AlertCircle, 
  Zap, 
  Sparkles,
  Clock,
  Copy,
  Check,
  RotateCcw,
  Trash2,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  Sliders,
  Stethoscope,
  Layers,
  Plus,
  Radio,
  FileCheck,
  Search,
  ExternalLink,
  HeartPulse,
  Thermometer,
  AlertOctagon,
  AlertTriangle,
  Columns,
  PanelRightClose,
  PanelRightOpen,
  Filter,
  Volume2,
  CheckCheck,
  X,
  User,
  ShieldCheck,
  BookOpen,
  HelpCircle,
  Brain,
  Maximize2,
  Minimize2,
  FileSpreadsheet
} from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { noteKeys, consultationKeys } from "@/hooks/useConsultations";
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
  getPatientProfile,
  type PatientProfileResponse,
  transcribeConsultationAudio,
} from "@/lib/api";
import ClinicalNoteEditor from "@/components/clinical/ClinicalNoteEditor";
import DifferentialDiagnosis from "@/components/clinical/DifferentialDiagnosis";
import LiveTranscriptionPanel from "@/components/clinical/LiveTranscriptionPanel";
import TranscriptEditorPanel from "@/components/clinical/TranscriptEditorPanel";
import AuditTimeline from "@/components/clinical/AuditTimeline";
import { SimilarCasesPanel } from "@/components/clinical/SimilarCasesPanel";
import InlineAIChat from "@/components/clinical/InlineAIChat";
import RAGAssistant from "@/components/clinical/RAGAssistant";
import CitationVerifier from "@/components/clinical/CitationVerifier";
import ExplanationPanel from "@/components/clinical/ExplanationPanel";

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

// Clinical Lifecycle Stages
const WORKFLOW_STAGES = [
  { id: "created", label: "Intake", desc: "Encounter created" },
  { id: "recording", label: "Audio Capture", desc: "Live ambient recording" },
  { id: "processing", label: "AI Synthesis", desc: "Diarization & fact extraction" },
  { id: "draft", label: "Draft Formulated", desc: "SOAP note drafted" },
  { id: "under_review", label: "Clinician Review", desc: "Attending review & verification" },
  { id: "analysis_ready", label: "Ready to Sign", desc: "Verified for sign-off" },
  { id: "finalized", label: "Finalized & Signed", desc: "Locked clinical record" },
];

const STAGE_INDEX_MAP: Record<string, number> = {
  created: 0,
  recording: 1,
  processing: 2,
  draft: 3,
  under_review: 4,
  analysis_ready: 5,
  finalized: 6,
  amended: 6,
};

// ─── Doctor Notes Smart Clinical Templates ─────────────────────────────────────
const CLINICAL_TEMPLATES = [
  {
    id: "soap",
    label: "SOAP Note",
    iconType: "file",
    badge: "Full Encounter",
    text: `SUBJECTIVE:
• Chief Complaint: 
• History of Present Illness (HPI): 
• Current Medications: 
• Allergies: 

OBJECTIVE:
• Vitals: BP:    | HR:    | RR:    | SpO2:    % | Temp:    °C
• General Appearance: 
• Physical Examination: 

ASSESSMENT:
• Clinical Impression / Differential: 

PLAN:
• Diagnostics / Labs: 
• Therapeutics / Prescriptions: 
• Patient Education & Safety Net: `,
  },
  {
    id: "chest_pain",
    label: "Chest Pain (OPQRST)",
    iconType: "heart",
    badge: "Cardiology",
    text: `CHEST PAIN WORKUP (OPQRST):
• Onset: Sudden / gradual onset [  ] hours ago during [activity].
• Provocation/Palliation: Worsened by exertion/inspiration? Relieved by rest/nitroglycerin?
• Quality: Pressure, squeezing, heavy, stabbing, tearing.
• Radiation: Radiates to left arm, shoulder, jaw, neck, back.
• Severity: [  ]/10 on visual analog scale.
• Timing: Constant / episodic, duration [  ] minutes.
• Associated Symptoms: Diaphoresis, dyspnea, nausea, presyncope, palpitations.
• Cardiac Risk Factors: HTN, DM, Dyslipidemia, Smoking, Family history.`,
  },
  {
    id: "infection",
    label: "Infection / Sepsis",
    iconType: "temp",
    badge: "Infectious",
    text: `INFECTION / SEPSIS SCREEN:
• Fever / Rigors: Max temperature documented [  ]°C, chills, sweats.
• Suspected Source:
  - Respiratory: Productive cough, purulent sputum, pleurisy, dyspnea.
  - Urinary: Dysuria, frequency, urgency, foul odor, flank tenderness.
  - Abdominal: Focal pain, guarding, nausea, vomiting, diarrhea.
  - Skin / Soft Tissue: Erythema, warmth, purulent drainage, induration.
• Sepsis Risk Markers: Altered mental status, tachypnea, hypotension.`,
  },
  {
    id: "exam_normal",
    label: "Exam (Normal Systems)",
    iconType: "scope",
    badge: "Physical Exam",
    text: `PHYSICAL EXAMINATION:
• Constitutional: Alert, oriented x 4, well-nourished, in no acute distress.
• Cardiovascular: Regular rate and rhythm, normal S1/S2. No murmurs, gallops, or friction rubs.
• Respiratory: Clear to auscultation bilaterally. Normal respiratory effort, no wheezing or crackles.
• Abdomen: Soft, non-distended, non-tender throughout. Normoactive bowel sounds. No guarding or rebound.
• Neurological: Cranial nerves II-XII grossly intact. Motor strength 5/5 in all extremities. Gait steady.`,
  },
  {
    id: "vitals",
    label: "Vitals Block",
    iconType: "activity",
    badge: "Vitals",
    text: `VITALS: BP: 120/80 mmHg | HR: 72 bpm | RR: 16 /min | SpO2: 98% room air | Temp: 36.8°C | GCS: 15/15`,
  },
];

// Rapid 1-Click Clinical Section Insert Snippets
const SCRATCHPAD_SECTIONS = [
  { id: "cc", label: "Chief Complaint", snippet: "CHIEF COMPLAINT:\n• " },
  { id: "hpi", label: "HPI (History)", snippet: "HISTORY OF PRESENT ILLNESS (HPI):\n• " },
  { id: "pmhx", label: "PMHx & Meds", snippet: "PAST MEDICAL HISTORY & MEDICATIONS:\n• Medical History: \n• Active Medications: \n• Allergies: NKDA" },
  { id: "vitals", label: "Physical Exam", snippet: "PHYSICAL EXAMINATION & VITALS:\n• Vitals: BP:    HR:    RR:    SpO2:    % Temp:    °C\n• General Appearance: Alert, no acute distress\n• Systemic Exam: " },
  { id: "assessment", label: "Assessment & Plan", snippet: "ASSESSMENT & PLAN:\n1. Primary Problem:\n   - Plan: \n2. Secondary Problem:\n   - Plan: " },
];

export default function ConsultationDetailPage({
  params: paramsProp,
}: {
  params?: Promise<{ id: string }> | { id: string };
} = {}) {
  const routeParams = useParams();
  let resolvedId: string | undefined;
  if (paramsProp) {
    if (typeof (paramsProp as any)?.then === "function" || paramsProp instanceof Promise) {
      const resolved = React.use(paramsProp as Promise<{ id: string }>);
      resolvedId = resolved?.id;
    } else {
      resolvedId = (paramsProp as { id: string }).id;
    }
  }
  const id = resolvedId || (Array.isArray(routeParams?.id) ? routeParams.id[0] : (routeParams?.id as string));
  const router = useRouter();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const [consultation, setConsultation] = useState<ConsultationResponse | null>(null);
  const [patientProfile, setPatientProfile] = useState<PatientProfileResponse | null>(null);
  const [consent, setConsent] = useState<ConsentRecordResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [inputText, setInputText] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [copiedScratchpad, setCopiedScratchpad] = useState(false);
  const [copiedId, setCopiedId] = useState(false);
  const [activeTab, setActiveTab] = useState<string>("ai-assistant");
  const [findingsFilter, setFindingsFilter] = useState<"all" | "pending" | "confirmed" | "negated">("all");
  const [paneMode, setPaneMode] = useState<"split" | "full-cockpit" | "full-notes">("split");
  const [explainFindingId, setExplainFindingId] = useState<string | null>(null);
  const [isSafetyAlertDismissed, setIsSafetyAlertDismissed] = useState(false);
  const [isSafetyAlertExpanded, setIsSafetyAlertExpanded] = useState(false);
  const [showRevokeConfirm, setShowRevokeConfirm] = useState(false);

  // Scratchpad Metrics
  const scratchpadStats = useMemo(() => {
    const chars = inputText.length;
    const words = inputText.trim() ? inputText.trim().split(/\s+/).length : 0;
    const readingTime = Math.max(1, Math.ceil(words / 200)) + " min";
    return { chars, words, readingTime };
  }, [inputText]);

  // Scratchpad Helper Actions
  const handleInsertTemplate = (templateText: string) => {
    setInputText((prev) => {
      if (!prev.trim()) return templateText;
      return `${prev.trim()}\n\n${templateText}`;
    });
    toast.success("Clinical template inserted");
  };

  const handleInsertSection = (snippet: string) => {
    setInputText((prev) => {
      if (!prev.trim()) return snippet;
      return `${prev.trim()}\n\n${snippet}`;
    });
    toast.success("Clinical section added to notes");
  };

  const handleInsertTimestamp = () => {
    const timeStr = `[${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}] - `;
    setInputText((prev) => `${prev ? prev + "\n" : ""}${timeStr}`);
  };

  const handleCopyScratchpad = () => {
    if (!inputText) return;
    navigator.clipboard.writeText(inputText);
    setCopiedScratchpad(true);
    toast.success("Doctor notes copied to clipboard");
    setTimeout(() => setCopiedScratchpad(false), 2000);
  };

  const handleCopyId = () => {
    if (!consultation?.id) return;
    navigator.clipboard.writeText(consultation.id);
    setCopiedId(true);
    toast.success("Encounter ID copied to clipboard");
    setTimeout(() => setCopiedId(false), 2000);
  };

  // Resizable Panes State
  const [rightPaneWidth, setRightPaneWidth] = useState<number>(560);
  const isDraggingRef = useRef(false);

  const startDragging = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isDraggingRef.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";

    const onMouseMove = (moveEvent: MouseEvent) => {
      if (!isDraggingRef.current) return;
      const newWidth = window.innerWidth - moveEvent.clientX;
      if (newWidth >= 380 && newWidth <= window.innerWidth * 0.72) {
        setRightPaneWidth(newWidth);
      }
    };

    const onMouseUp = () => {
      isDraggingRef.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
  }, []);

  // Transcription & Audio Capture state
  const wsUnsubRef = useRef<(() => void) | null>(null);
  const audio = useAudioCapture({
    timesliceMs: 1000,
    onAudioChunk: (chunkB64) => {
      const ws = getSharedRealtimeClient();
      if (ws) {
        ws.send("audio_chunk", { data: chunkB64 });
      }
    }
  });
  const [asrText, setAsrText] = useState("");
  const [diarizedSegments, setDiarizedSegments] = useState<Array<{
    speaker: string;
    text: string;
    confidence: number;
    source: string;
    start?: number;
    end?: number;
  }>>([]);
  const [savedTranscript, setSavedTranscript] = useState<TranscriptResponse | null>(null);
  const [editingSegment, setEditingSegment] = useState<string | null>(null);
  const [editText, setEditText] = useState("");

  // Consent modal state
  const [showConsentForm, setShowConsentForm] = useState(false);
  const [consentActor, setConsentActor] = useState("");
  const [consentRelation, setConsentRelation] = useState("self");
  const [pendingTransition, setPendingTransition] = useState<string | null>(null);

  // Clinical Representation (Safety Decision)
  const [representation, setRepresentation] = useState<ClinicalRepresentationResponse | null>(null);

  // Load Consultation Data
  const fetchConsultation = useCallback(async () => {
    if (!id) return;
    try {
      const res = await getConsultation(id);
      if (res.ok) {
        setConsultation(res.data);
        if (res.data.input_text) {
          setInputText(res.data.input_text);
        }

        // Fetch patient profile if available
        const profileId = res.data.patient_id || res.data.patient_profile_id;
        if (profileId) {
          const pRes = await getPatientProfile(profileId);
          if (pRes.ok) setPatientProfile(pRes.data);
        }

        // Fetch consent status
        const cRes = await getActiveConsent(id);
        if (cRes.ok && cRes.data) {
          setConsent(cRes.data);
        }

        // Fetch representation & safety flags
        const rRes = await getClinicalRepresentation(id);
        if (rRes.ok) setRepresentation(rRes.data);

        // Fetch transcript if available
        const tRes = await getTranscript(id);
        if (tRes.ok) setSavedTranscript(tRes.data);
      }
    } catch {
      toast.error("Failed to load consultation data");
    } finally {
      setLoading(false);
    }
  }, [id, toast]);

  useEffect(() => {
    fetchConsultation();
  }, [fetchConsultation]);

  // Handle Workflow State Transitions
  const handleTransition = async (newStatus: string, overrideConsent?: ConsentRecordResponse) => {
    if (!consultation) return;

    // Informed Consent enforcement for recording
    const activeConsentRecord = overrideConsent || consent;
    if (newStatus === "recording" && (!activeConsentRecord || !activeConsentRecord.recording_permitted)) {
      setPendingTransition(newStatus);
      setShowConsentForm(true);
      return;
    }

    setActionLoading(true);
    try {
      const res = await transitionConsultationStatus(consultation.id, {
        new_status: newStatus,
        input_text: consultation.input_text,
      });

      if (res.ok) {
        setConsultation(res.data);
        toast.success(`Consultation moved to: ${newStatus.replace('_', ' ')}`);

        // Invalidate react-query cache so lists update
        queryClient.invalidateQueries({ queryKey: consultationKeys.all });
        queryClient.invalidateQueries({ queryKey: noteKeys.all });

        // Handle Audio Recording Lifecycle
        if (newStatus === "recording") {
          try {
            await audio.start();
            setAsrText("");
            setDiarizedSegments([]);

            // Connect real-time WebSocket for live diarization & streaming ASR
            const token = getStoredToken();
            const ws = getSharedRealtimeClient(token);
            if (token && ws) {
              ws.connect();
              ws.send("subscribe", { consultation_id: consultation.id });

              if (wsUnsubRef.current) {
                wsUnsubRef.current();
                wsUnsubRef.current = null;
              }

              wsUnsubRef.current = ws.subscribeMessages((type, payload) => {
                if (type === "asr_partial") {
                  if (payload.text) {
                    setAsrText(payload.text);
                  }
                } else if (type === "asr_final") {
                  if (payload.text) {
                    setAsrText(prev => (prev ? `${prev} ${payload.text}` : payload.text));
                  }
                  if (payload.diarization && Array.isArray(payload.diarization) && payload.diarization.length > 0) {
                    setDiarizedSegments(prev => {
                      const newSegs = payload.diarization.map((s: any) => ({
                        speaker: s.speaker || "Doctor",
                        text: s.text || "",
                        confidence: s.confidence ?? 0.9,
                        source: s.source || "acoustic+heuristic",
                        start: s.start,
                        end: s.end,
                      }));
                      return [...prev, ...newSegs];
                    });
                  }
                }
              });
            }
          } catch (e: any) {
            toast.error("Could not initialize microphone: " + (e?.message || "Permission denied"));
          }
        } else if (consultation.status === "recording" && newStatus !== "recording") {
          // Stop audio recording & notify backend to finalize stream
          audio.stop();
          const ws = getSharedRealtimeClient();
          if (ws) {
            ws.send("audio_stop", {});
            ws.send("unsubscribe", { consultation_id: consultation.id });
          }
          if (wsUnsubRef.current) {
            wsUnsubRef.current();
            wsUnsubRef.current = null;
          }

          // Upload audio for backend transcription
          setTimeout(async () => {
            let transcribedDirectly = false;
            const audioBlob = audio.getAudioBlob();
            if (audioBlob && audioBlob.size > 1000) {
              const file = new File([audioBlob], `consultation-${consultation.id}.webm`, { type: audioBlob.type });
              const transRes = await transcribeConsultationAudio(consultation.id, file);
              if (transRes.ok) {
                transcribedDirectly = true;
                const tRes = await getTranscript(consultation.id);
                if (tRes.ok) setSavedTranscript(tRes.data);
                await fetchConsultation();
              }
            }

            // Fallback: save live WebSocket diarized segments
            if (!transcribedDirectly && diarizedSegments.length > 0) {
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
              const tRes = await getTranscript(consultation.id);
              if (tRes.ok) setSavedTranscript(tRes.data);
            }

            await handleTransition("draft");
          }, 0);
        }
      } else {
        toast.error(res.error.message || `Failed transition to ${newStatus}`);
      }
    } catch (err: any) {
      toast.error(err?.message || `Failed transition to ${newStatus}`);
    } finally {
      setActionLoading(false);
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
      fetchConsultation();
    } else {
      toast.error(res.error.message || `Failed to ${action} finding`);
    }
  };

  const handleConfirmAllFindings = async () => {
    if (!consultation?.findings) return;
    const pending = consultation.findings.filter(f => f.status === "pending");
    if (pending.length === 0) {
      toast.info("No pending findings to confirm");
      return;
    }
    setActionLoading(true);
    try {
      for (const f of pending) {
        await reviewClinicalFinding(consultation.id, f.id, "confirm");
      }
      toast.success(`Confirmed all ${pending.length} pending findings`);
      fetchConsultation();
    } catch (err: any) {
      toast.error(err?.message || "Failed to confirm all findings");
    } finally {
      setActionLoading(false);
    }
  };

  const handleGrantConsent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!consultation) return;
    setActionLoading(true);
    try {
      const res = await createConsent({
        consultation_id: consultation.id,
        actor_name: consentActor || "Patient",
        actor_relationship: consentRelation,
        purpose: "Clinical AI Analysis & Recording",
        recording_permitted: true,
      });
      if (res.ok) {
        toast.success("Patient consent recorded.");
        setConsent(res.data);
        setShowConsentForm(false);
        
        const transitionToRun = pendingTransition || "recording";
        setPendingTransition(null);
        await handleTransition(transitionToRun, res.data);
      } else {
        toast.error(res.error.message || "Failed to grant consent.");
      }
    } catch (err: any) {
      toast.error(err?.message || "Failed to grant consent.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRevokeConsent = async () => {
    if (!consultation) return;
    setShowRevokeConfirm(false);
    setActionLoading(true);
    try {
      const res = await revokeConsent(consultation.id);
      if (res.ok) {
        toast.success("Patient recording consent revoked.");
        setConsent(null);
        fetchConsultation();
      } else {
        toast.error(res.error.message || "Failed to revoke consent.");
      }
    } catch (err: any) {
      toast.error(err?.message || "Failed to revoke consent.");
    } finally {
      setActionLoading(false);
    }
  };

  // Findings filtering
  const filteredFindings = useMemo(() => {
    if (!consultation?.findings) return [];
    if (findingsFilter === "pending") return consultation.findings.filter(f => f.status === "pending");
    if (findingsFilter === "confirmed") return consultation.findings.filter(f => f.status === "confirmed");
    if (findingsFilter === "negated") return consultation.findings.filter(f => f.negated);
    return consultation.findings;
  }, [consultation, findingsFilter]);

  if (loading) {
    return (
      <div className="p-8 max-w-6xl mx-auto space-y-4" data-testid="dashboard-skeleton">
        <Skeleton className="h-10 w-1/3 mb-4 rounded-xl" />
        <Skeleton className="h-20 w-full mb-4 rounded-2xl" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton className="h-[400px] w-full rounded-2xl" />
          <Skeleton className="h-[400px] w-full rounded-2xl" />
        </div>
      </div>
    );
  }

  if (!consultation) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 text-center bg-white">
        <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-4 text-slate-400">
          <AlertCircle size={32} />
        </div>
        <h2 className="text-xl font-bold text-slate-800 mb-2 font-heading">Consultation Not Found</h2>
        <p className="text-slate-500 mb-6 text-sm">The requested consultation could not be found or has been removed.</p>
        <Link
          href="/consultations"
          className="px-5 py-2.5 rounded-xl bg-teal-600 text-white font-bold text-sm hover:bg-teal-700 transition-all shadow-xs"
        >
          Back to Consultations
        </Link>
      </div>
    );
  }

  const currentStatus = consultation.status;
  const isSplitPane = true;
  const currentStageIndex = STAGE_INDEX_MAP[currentStatus] ?? 0;
  const pendingFindingsCount = consultation?.findings?.filter(f => f.status === "pending").length || 0;

  // Primary Clinical Action Button (rendered once in header bar)
  const renderWorkflowActions = () => {
    return (
      <div className="flex items-center gap-2">
        {currentStatus === "created" && (
          <div className="flex items-center gap-2">
            <button 
              type="button"
              onClick={() => {
                if (!consent) {
                  setPendingTransition("recording");
                  setShowConsentForm(true);
                } else {
                  handleTransition("recording");
                }
              }}
              disabled={actionLoading}
              className="px-3.5 py-1.5 rounded-xl font-bold text-xs text-white bg-teal-600 hover:bg-teal-700 transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
              title="Start real-time clinical audio capture with automated diarization"
            >
              <Mic className="w-3.5 h-3.5 text-teal-100 animate-pulse" />
              <span>Live Audio Recording</span>
            </button>
            <button 
              type="button"
              onClick={() => {
                setActiveTab("scratchpad");
                toast.info("Switched to Doctor Notes scratchpad");
              }}
              disabled={actionLoading}
              className="px-3 py-1.5 rounded-xl font-bold text-xs text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 shadow-2xs flex items-center gap-1.5 cursor-pointer"
              title="Enter manual doctor notes or clinical templates"
            >
              <FileText className="w-3.5 h-3.5 text-teal-600" />
              <span>Manual Notes</span>
            </button>
          </div>
        )}

        {currentStatus === "recording" && (
          <div className="flex items-center gap-2">
            <Button 
              variant="primary" 
              onClick={() => handleTransition("processing")}
              disabled={actionLoading}
              className="h-8 px-3.5 text-xs font-bold bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-xs"
            >
              Submit for Analysis
            </Button>
            <Button 
              variant="ghost" 
              onClick={() => handleTransition("created")}
              disabled={actionLoading}
              className="h-8 px-2.5 text-xs font-bold text-rose-600 hover:bg-rose-50 rounded-xl"
            >
              <Square className="w-3.5 h-3.5 mr-1" /> Stop
            </Button>
          </div>
        )}

        {currentStatus === "processing" && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-purple-50 border border-purple-200 text-xs font-bold text-purple-700 shadow-2xs">
            <div className="w-3.5 h-3.5 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
            <span>Synthesizing Audio &amp; Facts...</span>
          </div>
        )}

        {currentStatus === "draft" && (
          <Button 
            variant="primary" 
            onClick={() => handleTransition("under_review")} 
            disabled={actionLoading} 
            className="h-8 px-3.5 text-xs font-bold bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-xs flex items-center gap-1.5"
          >
            <span>Begin Note Review</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Button>
        )}

        {currentStatus === "under_review" && (
          <div className="flex items-center gap-2">
            <Button 
              variant="primary" 
              onClick={() => handleTransition("analysis_ready")} 
              disabled={actionLoading} 
              className="h-8 px-3 text-xs font-bold bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-xs"
            >
              Mark Analysis Ready
            </Button>
            <Button 
              variant="ghost" 
              onClick={() => handleTransition("draft")} 
              disabled={actionLoading} 
              className="h-8 px-2.5 text-xs font-medium rounded-xl text-slate-600 hover:bg-slate-100"
            >
              Draft
            </Button>
          </div>
        )}

        {currentStatus === "analysis_ready" && (
          <div className="flex items-center gap-2">
            <Button 
              variant="primary" 
              onClick={() => handleTransition("finalized")} 
              disabled={actionLoading} 
              className="h-8 px-3 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-xs flex items-center gap-1.5"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Sign Off &amp; Finalize</span>
            </Button>
            <Button 
              variant="ghost" 
              onClick={() => handleTransition("under_review")} 
              disabled={actionLoading} 
              className="h-8 px-2.5 text-xs font-medium rounded-xl text-slate-600 hover:bg-slate-100"
            >
              Re-review
            </Button>
          </div>
        )}

        {currentStatus === "finalized" && (
          <Button 
            variant="ghost" 
            onClick={() => handleTransition("amended")} 
            disabled={actionLoading} 
            className="h-8 px-3 text-xs font-bold rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700"
          >
            Amend Record
          </Button>
        )}

        {currentStatus === "amended" && (
          <Button 
            variant="primary" 
            onClick={() => handleTransition("finalized")} 
            disabled={actionLoading} 
            className="h-8 px-3.5 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-xs flex items-center gap-1.5"
          >
            <CheckCircle className="w-3.5 h-3.5" />
            <span>Sign Off Amendment</span>
          </Button>
        )}
      </div>
    );
  };

  return (
    <div className="consultation-workspace-root flex flex-col h-full min-h-0 overflow-hidden relative w-full bg-slate-50/60 text-slate-900">
      
      {/* ── Tier 1: Executive Clinical Command Header ───────────────────────────────── */}
      <header className="bg-white border-b border-slate-200 shrink-0 z-20 shadow-2xs">
        {/* Main Header Bar */}
        <div className="px-4 sm:px-6 py-2.5 flex flex-wrap items-center justify-between gap-3">
          {/* Left Metadata & Identity */}
          <div className="flex items-center gap-3 min-w-0">
            <Link
              href="/consultations"
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-100/90 hover:bg-slate-200/80 transition-colors border border-slate-200/80 shrink-0"
              title="Back to consultations directory"
            >
              <ChevronLeft className="w-4 h-4 text-slate-500" />
              <span className="hidden sm:inline">Consultations</span>
            </Link>

            <span className="text-slate-300 hidden sm:inline">/</span>

            <div className="flex items-center gap-2.5 min-w-0">
              <h1 className="text-base sm:text-lg font-black font-heading text-slate-900 tracking-tight truncate m-0">
                Consultation Workspace
              </h1>
              
              {/* Status Badge */}
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] uppercase tracking-wider font-extrabold flex items-center gap-1.5 shrink-0 shadow-2xs ${
                currentStatus === 'finalized' ? 'bg-emerald-50 text-emerald-800 border border-emerald-300' : 
                currentStatus === 'recording' ? 'bg-rose-50 text-rose-800 border border-rose-300 ring-2 ring-rose-200/50' : 
                currentStatus === 'processing' ? 'bg-purple-50 text-purple-800 border border-purple-300' :
                currentStatus === 'draft' ? 'bg-indigo-50 text-indigo-800 border border-indigo-300' :
                currentStatus === 'under_review' ? 'bg-amber-50 text-amber-800 border border-amber-300' :
                'bg-slate-100 text-slate-700 border border-slate-300'
              }`}>
                <span className={`w-2 h-2 rounded-full ${
                  currentStatus === 'recording' ? 'bg-rose-600 animate-ping' :
                  currentStatus === 'finalized' ? 'bg-emerald-600' :
                  currentStatus === 'processing' ? 'bg-purple-600 animate-pulse' :
                  'bg-indigo-600'
                }`} />
                <span>{currentStatus.replace('_', ' ')}</span>
              </span>

              {/* Minimized Red Flag Alert Pill */}
              {representation?.safety_decision && representation.safety_decision.decision !== "ALLOW" && isSafetyAlertDismissed && (
                <button
                  type="button"
                  onClick={() => setIsSafetyAlertDismissed(false)}
                  className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-600 hover:bg-rose-700 text-white shadow-2xs transition-all cursor-pointer shrink-0"
                  title="Click to review critical clinical safety warning"
                >
                  <AlertOctagon className="w-3.5 h-3.5 text-rose-100" />
                  <span>Safety Alert ({representation.safety_decision.flags.length})</span>
                </button>
              )}
            </div>

            {/* Copyable Encounter ID Pill */}
            <button
              type="button"
              onClick={handleCopyId}
              className="group hidden md:inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 font-mono transition-colors bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200 shrink-0 cursor-pointer"
              title="Click to copy encounter ID"
            >
              <span>ENC #{consultation.id.slice(0, 8)}</span>
              {copiedId ? (
                <Check className="w-3 h-3 text-emerald-600" />
              ) : (
                <Copy className="w-3 h-3 opacity-60 group-hover:opacity-100" />
              )}
            </button>

            {/* Patient Context Badge */}
            {(patientProfile || consultation.patient_ref) ? (
              <Link
                href={`/patients/${patientProfile?.id || consultation.patient_id}`}
                className="inline-flex items-center gap-1.5 text-xs text-teal-800 bg-teal-50 hover:bg-teal-100 px-2.5 py-1 rounded-lg border border-teal-200 transition-colors shadow-2xs"
                title={`Patient: ${patientProfile?.patient_ref || consultation.patient_ref}`}
              >
                <User className="w-3 h-3 text-teal-600" />
                <span className="font-bold">{patientProfile?.patient_ref || consultation.patient_ref}</span>
                {(patientProfile?.age_group || consultation.patient_demographics?.age_group) && (
                  <span className="opacity-70">({patientProfile?.age_group || consultation.patient_demographics?.age_group})</span>
                )}
                {(patientProfile?.biological_sex || consultation.patient_demographics?.biological_sex) && (
                  <span className="opacity-70 capitalize">{patientProfile?.biological_sex || consultation.patient_demographics?.biological_sex}</span>
                )}
              </Link>
            ) : null}
          </div>

          {/* Right Controls: View Mode Switcher, Consent, and Primary Action CTA */}
          <div className="flex items-center gap-2.5 shrink-0">
            {/* View Mode Switcher */}
            <div className="inline-flex items-center p-0.5 rounded-xl bg-slate-100 border border-slate-200">
              <button
                type="button"
                onClick={() => setPaneMode("full-cockpit")}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                  paneMode === "full-cockpit"
                    ? "bg-white text-teal-700 shadow-2xs font-extrabold"
                    : "text-slate-600 hover:text-slate-900"
                }`}
                title="Cockpit View (Full screen diagnostic cockpit)"
              >
                <Maximize2 className="w-3.5 h-3.5 text-teal-600" />
                <span>Cockpit</span>
              </button>
              <button
                type="button"
                onClick={() => setPaneMode("split")}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all flex items-center gap-1 cursor-pointer ${
                  paneMode === "split"
                    ? "bg-white text-slate-900 shadow-2xs font-extrabold"
                    : "text-slate-600 hover:text-slate-900"
                }`}
                title="Split View (Side-by-side Cockpit + Notes)"
              >
                <Columns className="w-3.5 h-3.5" />
                <span>Split</span>
              </button>
              <button
                type="button"
                onClick={() => setPaneMode("full-notes")}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all flex items-center gap-1 cursor-pointer ${
                  paneMode === "full-notes"
                    ? "bg-white text-slate-900 shadow-2xs font-extrabold"
                    : "text-slate-600 hover:text-slate-900"
                }`}
                title="Notes View (Full screen note editor)"
              >
                <PanelRightOpen className="w-3.5 h-3.5" />
                <span>Notes</span>
              </button>
            </div>

            {/* Informed Consent Status Badge */}
            {consent ? (
              <div className="flex items-center gap-1.5 bg-emerald-50 text-emerald-800 px-2.5 py-1 rounded-xl border border-emerald-200 text-xs font-bold shadow-2xs">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                <span className="hidden sm:inline">Consent Verified</span>
                {["created", "recording"].includes(currentStatus) && (
                  showRevokeConfirm ? (
                    <span className="ml-1 inline-flex items-center gap-1.5 text-[10px] bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                      <span className="text-rose-800 font-bold">Revoke?</span>
                      <button
                        type="button"
                        onClick={handleRevokeConsent}
                        disabled={actionLoading}
                        className="text-rose-700 hover:text-rose-900 underline font-black cursor-pointer"
                      >
                        Yes
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowRevokeConfirm(false)}
                        className="text-slate-500 hover:text-slate-700 font-medium cursor-pointer"
                      >
                        No
                      </button>
                    </span>
                  ) : (
                    <button 
                      type="button"
                      onClick={() => setShowRevokeConfirm(true)} 
                      disabled={actionLoading} 
                      className="ml-1 text-[10px] underline hover:text-rose-600 text-slate-500 font-bold transition-colors cursor-pointer"
                      title="Revoke recorded patient consent"
                    >
                      Revoke
                    </button>
                  )
                )}
              </div>
            ) : (
              <button
                type="button"
                onClick={() => {
                  setPendingTransition("recording");
                  setShowConsentForm(true);
                }}
                className="flex items-center gap-1.5 bg-rose-50 hover:bg-rose-100 text-rose-800 px-2.5 py-1 rounded-xl border border-rose-200 transition-all text-xs font-bold cursor-pointer shadow-2xs"
                title="Patient consent required before audio recording"
              >
                <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                <span>Consent Required</span>
              </button>
            )}

            {/* Primary Action Button (The ONLY action button, no duplicates!) */}
            {renderWorkflowActions()}
          </div>
        </div>

        {/* Stepper Sub-Bar with Timeline & Audio Telemetry */}
        <div className="px-4 sm:px-6 py-1.5 bg-slate-50/80 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100">
          <div className="flex items-center gap-2.5 shrink-0">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider hidden sm:inline">
              Workflow Stage:
            </span>
            <div className="flex items-center gap-1.5 bg-white px-2.5 py-0.5 rounded-lg border border-slate-200 shadow-2xs">
              <span className="w-3.5 h-3.5 rounded-full bg-teal-600 text-white flex items-center justify-center text-[9px] font-bold">
                {currentStageIndex + 1}
              </span>
              <span className="text-xs font-bold text-slate-800">
                {WORKFLOW_STAGES[currentStageIndex]?.label || currentStatus.replace('_', ' ')}
              </span>
              <span className="text-[10px] text-slate-400 font-medium">
                ({currentStageIndex + 1} of 7)
              </span>
            </div>

            {/* Micro progress trail */}
            <div className="flex items-center gap-1" role="progressbar" aria-valuenow={currentStageIndex + 1} aria-valuemin={1} aria-valuemax={7}>
              {WORKFLOW_STAGES.map((st, idx) => {
                const isCurrent = st.id === currentStatus;
                const isPassed = currentStageIndex > idx;
                return (
                  <div
                    key={st.id}
                    title={`Stage ${idx + 1}: ${st.label} — ${st.desc}`}
                    className={`h-1.5 rounded-full transition-all ${
                      isCurrent
                        ? "w-4 bg-teal-600 ring-1 ring-teal-300"
                        : isPassed
                        ? "w-2 bg-emerald-500"
                        : "w-1.5 bg-slate-200"
                    }`}
                  />
                );
              })}
            </div>
          </div>

          {/* Recording Audio Visualizer */}
          {currentStatus === "recording" && (
            <div className="px-2.5 py-0.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 font-mono text-xs font-bold flex items-center gap-2 shadow-2xs">
              <span className="w-2 h-2 rounded-full bg-rose-600 animate-ping" />
              <span>REC {formatElapsed(audio.elapsedMs)}</span>
              <div className="flex items-end gap-0.5 ml-1 h-3" title={`Mic volume: ${audio.audioLevel}%`}>
                <span className="w-1 bg-emerald-500 rounded-full transition-all duration-75" style={{ height: `${Math.max(20, Math.min(100, audio.audioLevel * 1.2))}%` }} />
                <span className="w-1 bg-emerald-500 rounded-full transition-all duration-75" style={{ height: `${Math.max(15, Math.min(100, audio.audioLevel * 0.8))}%` }} />
                <span className="w-1 bg-emerald-500 rounded-full transition-all duration-75" style={{ height: `${Math.max(25, Math.min(100, audio.audioLevel * 1.4))}%` }} />
                <span className="w-1 bg-emerald-500 rounded-full transition-all duration-75" style={{ height: `${Math.max(10, Math.min(100, audio.audioLevel * 1.0))}%` }} />
              </div>
            </div>
          )}
        </div>
      </header>

      {/* ── Red Flag Safety Decision Banner (Compact & Collapsible) ───────────────── */}
      {representation?.safety_decision && representation.safety_decision.decision !== "ALLOW" && !isSafetyAlertDismissed && (
        <div className="bg-red-50 border-b border-red-200 px-4 sm:px-6 py-2 shrink-0 z-20 shadow-2xs">
          <div className="flex flex-wrap items-center justify-between gap-3 max-w-7xl mx-auto">
            <div className="flex items-center gap-2.5 min-w-0 flex-1">
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-red-600 text-white text-[10px] font-bold uppercase tracking-wider shrink-0">
                <AlertOctagon className="w-3 h-3 text-red-100" />
                <span>SAFETY ALERT</span>
              </span>

              <p className="text-xs text-red-900 font-semibold truncate min-w-0 flex-1" title={representation.safety_decision.flags[0]?.message}>
                {representation.safety_decision.flags[0]?.message || "Clinical safety indicators detected."}
              </p>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={() => setIsSafetyAlertExpanded(prev => !prev)}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold text-red-900 bg-red-100 hover:bg-red-200 border border-red-200 transition-colors cursor-pointer"
              >
                <span>{isSafetyAlertExpanded ? "Hide Details" : `Details (${representation.safety_decision.flags.length})`}</span>
                {isSafetyAlertExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>

              <button
                type="button"
                onClick={() => {
                  setIsSafetyAlertDismissed(true);
                  toast.success("Safety alert minimized to top bar.");
                }}
                className="inline-flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-bold text-white bg-red-600 hover:bg-red-700 shadow-2xs transition-colors cursor-pointer"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Dismiss</span>
              </button>
            </div>
          </div>

          {isSafetyAlertExpanded && (
            <div className="mt-2 pt-2 border-t border-red-200 space-y-2 max-w-7xl mx-auto">
              {representation.safety_decision.flags.map((flag, idx) => (
                <div key={idx} className="bg-white p-2.5 rounded-xl border border-red-200 shadow-2xs flex items-start gap-2.5">
                  <span className="mt-0.5">
                    {flag.severity === 'CRITICAL' ? (
                      <AlertOctagon className="w-4 h-4 text-red-600 shrink-0" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                    )}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-red-950 text-xs uppercase tracking-wide">
                        {flag.category.replace('_', ' ')}
                      </span>
                      <span className="text-[10px] font-mono text-red-700 bg-red-50 px-1.5 py-0.5 rounded border border-red-200 font-bold">
                        {flag.severity}
                      </span>
                    </div>
                    <p className="text-red-800 text-xs font-medium mt-0.5 leading-relaxed">{flag.message}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Main Workspace Body ────────────────────────────────────────────────────── */}
      <div className="flex flex-1 min-h-0 overflow-hidden relative w-full">
        
        {/* Left Workspace Pane (Cockpit, Intelligence, Transcript, Notes, Evidence) */}
        <div className={`flex flex-col h-full min-h-0 bg-slate-50/60 relative overflow-hidden transition-all duration-300 ${
          paneMode === "full-notes" ? "hidden" : "flex-1"
        }`}>

          <Tabs.Root 
            value={activeTab} 
            onValueChange={setActiveTab} 
            className="flex flex-1 flex-col h-full min-h-0 overflow-hidden"
          >
            {/* Tabs Navigation Bar */}
            <div className="px-4 sm:px-6 py-2 border-b border-slate-200 bg-white shrink-0 flex flex-wrap items-center justify-between gap-3 shadow-2xs">
              <Tabs.List className="flex flex-wrap items-center gap-1.5 p-1 bg-slate-100 rounded-xl border border-slate-200">
                <Tabs.Trigger 
                  value="ai-assistant" 
                  className="px-3 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs text-slate-600 hover:text-slate-900 outline-none cursor-pointer"
                >
                  <Activity className="w-3.5 h-3.5 text-teal-600" />
                  <span>Clinical Cockpit</span>
                  {currentStatus === "recording" && (
                    <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                  )}
                </Tabs.Trigger>

                <Tabs.Trigger 
                  value="intelligence" 
                  className="px-3 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs text-slate-600 hover:text-slate-900 outline-none cursor-pointer"
                >
                  <Zap className="w-3.5 h-3.5 text-amber-500" />
                  <span>Differential Diagnosis</span>
                  {consultation.findings && consultation.findings.length > 0 && (
                    <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-indigo-100 text-indigo-700 font-mono font-bold">
                      {consultation.findings.length}
                    </span>
                  )}
                </Tabs.Trigger>

                <Tabs.Trigger 
                  value="scratchpad" 
                  className="px-3 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs text-slate-600 hover:text-slate-900 outline-none cursor-pointer"
                >
                  <FileText className="w-3.5 h-3.5 text-slate-600" />
                  <span>Doctor Notes</span>
                  {inputText.trim() && (
                    <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
                  )}
                </Tabs.Trigger>

                <Tabs.Trigger 
                  value="transcript" 
                  className="px-3 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs text-slate-600 hover:text-slate-900 outline-none cursor-pointer"
                >
                  <Radio className="w-3.5 h-3.5 text-indigo-500" />
                  <span>Transcript &amp; Audit</span>
                </Tabs.Trigger>

                <Tabs.Trigger 
                  value="evidence" 
                  className="px-3 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs text-slate-600 hover:text-slate-900 outline-none cursor-pointer"
                >
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Evidence &amp; Citations</span>
                </Tabs.Trigger>
              </Tabs.List>

              <div className="hidden lg:flex items-center gap-3 text-xs text-slate-500 font-mono">
                {activeTab === "scratchpad" && (
                  <span className="text-[11px] text-slate-600 font-medium bg-slate-100 px-2.5 py-1 rounded-lg">
                    {scratchpadStats.words} words · {scratchpadStats.chars} chars
                  </span>
                )}
              </div>
            </div>

            {/* Scrollable Tab Content Container */}
            <div className="flex-1 min-h-0 overflow-y-auto p-4 sm:p-5 lg:p-6 space-y-6">
              
              {/* TAB 1: Clinical Cockpit */}
              <Tabs.Content value="ai-assistant" className="space-y-6 outline-none">
                <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
                  
                  {/* Left Column: Clinical Presentation & Real-time Live Transcription */}
                  <div className="xl:col-span-7 space-y-5">
                    {/* Clinical Scenario / Chief Complaint (if present) */}
                    {consultation.input_text && (
                      <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-2xs">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                          Clinical Presentation / Chief Complaint
                        </span>
                        <p className="text-sm text-slate-800 leading-relaxed font-medium">
                          {consultation.input_text}
                        </p>
                      </div>
                    )}

                    {/* Live Speech-to-Text Diarization & Ambient Capture */}
                    <LiveTranscriptionPanel
                      consultationId={consultation.id}
                      isConsultationRecording={currentStatus === "recording"}
                      onStartConsultationRecording={() => {
                        if (!consent) {
                          setPendingTransition("recording");
                          setShowConsentForm(true);
                        } else {
                          handleTransition("recording");
                        }
                      }}
                      onStopConsultationRecording={() => handleTransition("processing")}
                      onTranscriptReady={(text, segs) => {
                        if (text && text.trim()) {
                          setInputText(prev => {
                            if (!prev.trim()) return text;
                            if (prev.includes(text)) return prev;
                            return `${prev.trim()}\n\n${text}`;
                          });
                        }
                        if (segs && segs.length > 0) {
                          setDiarizedSegments(segs.map(s => ({
                            speaker: s.speaker,
                            text: s.text,
                            confidence: s.confidence,
                            source: "live_asr"
                          })));
                        }
                      }}
                      backendSegments={diarizedSegments}
                      backendAsrText={asrText}
                    />

                    {/* Extracted Clinical Findings Card */}
                    {consultation?.findings && consultation.findings.length > 0 && (
                      <div className="p-4 sm:p-5 bg-white border border-slate-200 shadow-2xs rounded-2xl relative overflow-hidden">
                        <div className="flex flex-wrap justify-between items-center gap-2 mb-3 pb-2.5 border-b border-slate-100">
                          <h3 className="text-xs font-bold tracking-wide text-slate-800 uppercase flex items-center gap-2 m-0 font-heading">
                            <Activity className="w-4 h-4 text-teal-600" />
                            Extracted Clinical Findings ({consultation.findings.length})
                          </h3>
                          <div className="flex items-center gap-1.5">
                            {pendingFindingsCount > 0 && (
                              <button
                                type="button"
                                onClick={handleConfirmAllFindings}
                                disabled={actionLoading}
                                className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 transition-colors flex items-center gap-1 cursor-pointer"
                                title="Confirm all pending findings at once"
                              >
                                <CheckCheck className="w-3 h-3 text-emerald-600" />
                                Confirm All ({pendingFindingsCount})
                              </button>
                            )}
                            <button
                              type="button"
                              onClick={() => setFindingsFilter("all")}
                              className={`px-2 py-0.5 rounded-lg text-[10px] font-bold cursor-pointer ${
                                findingsFilter === "all" ? "bg-teal-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                              }`}
                            >
                              All
                            </button>
                            <button
                              type="button"
                              onClick={() => setFindingsFilter("pending")}
                              className={`px-2 py-0.5 rounded-lg text-[10px] font-bold cursor-pointer ${
                                findingsFilter === "pending" ? "bg-teal-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                              }`}
                            >
                              Pending
                            </button>
                            <button
                              type="button"
                              onClick={() => setFindingsFilter("confirmed")}
                              className={`px-2 py-0.5 rounded-lg text-[10px] font-bold cursor-pointer ${
                                findingsFilter === "confirmed" ? "bg-teal-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                              }`}
                            >
                              Confirmed
                            </button>
                          </div>
                        </div>
                        
                        <div className="flex flex-wrap gap-2">
                          {filteredFindings.map((finding: any) => (
                            <div 
                              key={finding.id} 
                              className={`p-2.5 rounded-xl border flex flex-col gap-1 min-w-[160px] shadow-2xs transition-colors ${
                                finding.negated 
                                  ? "bg-rose-50/70 border-rose-200" 
                                  : finding.status === "confirmed" 
                                    ? "bg-emerald-50/80 border-emerald-200" 
                                    : "bg-white border-slate-200 hover:border-teal-300"
                              }`}
                            >
                              <div className="flex justify-between items-start gap-2">
                                <span className={`text-xs font-bold capitalize ${finding.negated ? "text-rose-700 line-through opacity-80" : "text-slate-800"}`}>
                                  {finding.value}
                                </span>
                                {finding.confidence_score && (
                                  <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                                    {(finding.confidence_score * 100).toFixed(0)}%
                                  </span>
                                )}
                              </div>
                              
                              <div className="flex flex-wrap gap-1 mt-0.5">
                                <span className="text-[10px] px-1.5 py-0.2 bg-slate-100 border border-slate-200 rounded text-slate-600 font-medium">
                                  {finding.concept || finding.finding_type}
                                </span>
                                {finding.negated && (
                                  <span className="text-[10px] px-1.5 py-0.2 bg-rose-100 text-rose-700 rounded font-bold">
                                    NEGATED
                                  </span>
                                )}
                                {finding.status === "confirmed" && (
                                  <span className="text-[10px] px-1.5 py-0.2 bg-emerald-100 text-emerald-700 rounded font-bold flex items-center gap-0.5">
                                    <Check className="w-2.5 h-2.5" /> CONFIRMED
                                  </span>
                                )}
                              </div>
                              
                              <div className="flex items-center gap-1 mt-1.5 pt-1.5 border-t border-slate-100">
                                <button
                                  type="button"
                                  onClick={() => setExplainFindingId(finding.id)}
                                  className="px-2 py-0.5 text-[10px] font-bold text-teal-700 bg-teal-50 hover:bg-teal-100 rounded border border-teal-200 transition-colors flex items-center gap-0.5 cursor-pointer"
                                  title="View clinical rationale and evidence provenance"
                                >
                                  <HelpCircle className="w-2.5 h-2.5" />
                                  Why?
                                </button>
                                {finding.status === "pending" && (
                                  <>
                                    <button 
                                      type="button" 
                                      className="flex-1 py-0.5 px-1.5 text-[10px] font-bold rounded bg-slate-100 hover:bg-rose-50 hover:text-rose-600 transition-colors border border-slate-200 cursor-pointer" 
                                      onClick={() => handleReviewFinding(finding.id, "reject")}
                                    >
                                      Reject
                                    </button>
                                    <button 
                                      type="button" 
                                      className="flex-1 py-0.5 px-1.5 text-[10px] font-bold rounded bg-teal-50 text-teal-700 hover:bg-teal-100 transition-colors border border-teal-200 cursor-pointer" 
                                      onClick={() => handleReviewFinding(finding.id, "confirm")}
                                    >
                                      Confirm
                                    </button>
                                  </>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Right Column: AI Clinical Intelligence Hub & Inline Chat */}
                  <div className="xl:col-span-5 space-y-5">
                    {/* Compact Diagnostic Decision Summary Card */}
                    <div className="p-4 sm:p-5 rounded-2xl bg-white border border-slate-200 shadow-2xs text-left space-y-3">
                      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                        <div className="flex items-center gap-2">
                          <Zap className="w-4 h-4 text-amber-500" />
                          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide font-heading m-0">
                            Diagnostic Decision Support
                          </h3>
                        </div>
                        <button
                          type="button"
                          onClick={() => setActiveTab("intelligence")}
                          className="text-xs font-bold text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-2.5 py-1 rounded-lg border border-teal-200 transition-all flex items-center gap-1 cursor-pointer"
                        >
                          <span>Full Studio →</span>
                        </button>
                      </div>

                      <p className="text-xs text-slate-600 font-medium">
                        Real-time probabilistic diagnostic inference and state disease surveillance active.
                      </p>

                      <div className="flex items-center gap-2 pt-1">
                        <button
                          type="button"
                          onClick={() => setActiveTab("intelligence")}
                          className="w-full py-2 px-3 rounded-xl text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 transition-all shadow-xs flex items-center justify-center gap-2 cursor-pointer"
                        >
                          <Activity className="w-3.5 h-3.5" />
                          <span>Open Full Differential Diagnosis Studio</span>
                        </button>
                      </div>
                    </div>

                    {/* Inline AI Assistant Chat */}
                    <InlineAIChat consultationId={consultation.id} notes={consultation.input_text || inputText} />
                  </div>
                </div>
              </Tabs.Content>

              {/* TAB 2: Full Differential Diagnosis Decision Studio */}
              <Tabs.Content value="intelligence" className="space-y-6 outline-none">
                <DifferentialDiagnosis 
                  consultationId={consultation.id} 
                  trigger={consultation.findings?.length || consultation.status}
                  initialQuery={consultation.input_text || inputText}
                />
                <SimilarCasesPanel consultationId={consultation.id} />
              </Tabs.Content>

              {/* TAB 3: Doctor Notes Scratchpad */}
              <Tabs.Content value="scratchpad" className="space-y-5 outline-none flex flex-col">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-teal-50 text-teal-700 border border-teal-200 flex items-center justify-center shadow-2xs">
                      <FileText className="w-4 h-4 text-teal-600" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold tracking-tight text-slate-900 font-heading flex items-center gap-2 m-0">
                        Doctor Notes Scratchpad
                      </h3>
                      <p className="text-xs text-slate-500 font-medium">
                        Type notes or insert clinical templates directly
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-wrap">
                    <button
                      type="button"
                      onClick={handleInsertTimestamp}
                      className="px-2.5 py-1.5 rounded-lg text-xs font-bold bg-white text-slate-700 hover:bg-slate-100 border border-slate-200 transition-colors flex items-center gap-1 shadow-2xs cursor-pointer"
                      title="Insert current timestamp into notes"
                    >
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span>Timestamp</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleCopyScratchpad}
                      disabled={!inputText.trim()}
                      className="px-3 py-1.5 rounded-lg text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white transition-colors flex items-center gap-1 shadow-xs disabled:opacity-50 cursor-pointer"
                      title="Copy notes to clipboard"
                    >
                      {copiedScratchpad ? <Check className="w-3.5 h-3.5 text-emerald-200" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedScratchpad ? "Copied!" : "Copy Notes"}</span>
                    </button>
                  </div>
                </div>

                {/* 1-Click Clinical Templates & Section Inserts */}
                <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-2.5">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
                    1-Click Clinical Templates:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {CLINICAL_TEMPLATES.map((tmpl) => (
                      <button
                        key={tmpl.id}
                        type="button"
                        onClick={() => handleInsertTemplate(tmpl.text)}
                        className="px-3 py-1 rounded-lg text-xs font-bold bg-slate-50 text-slate-700 hover:bg-teal-50 hover:text-teal-900 border border-slate-200 transition-colors flex items-center gap-1.5 cursor-pointer"
                      >
                        <Plus className="w-3 h-3 text-teal-600" />
                        <span>{tmpl.label}</span>
                      </button>
                    ))}
                  </div>

                  <div className="pt-2 border-t border-slate-100 flex flex-wrap gap-1.5">
                    {SCRATCHPAD_SECTIONS.map((sec) => (
                      <button
                        key={sec.id}
                        type="button"
                        onClick={() => handleInsertSection(sec.snippet)}
                        className="px-2.5 py-0.5 rounded-md text-[11px] font-semibold bg-white text-slate-600 hover:bg-slate-100 border border-slate-200 transition-colors cursor-pointer"
                      >
                        + {sec.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Main Scratchpad Textarea */}
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="Enter patient history, objective findings, vitals, or select a clinical template above..."
                  rows={14}
                  className="w-full text-sm font-medium rounded-xl p-4 border border-slate-300 bg-white text-slate-900 placeholder-slate-400 focus:border-teal-500 focus:ring-2 focus:ring-teal-100 outline-none transition-all shadow-inner leading-relaxed"
                />
              </Tabs.Content>

              {/* TAB 4: Transcript & Clinical Audit Trail */}
              <Tabs.Content value="transcript" className="space-y-6 outline-none">
                {savedTranscript && ["draft", "under_review", "finalized"].includes(currentStatus) ? (
                  <div className="space-y-6">
                    <TranscriptEditorPanel
                      transcript={savedTranscript}
                      currentStatus={currentStatus}
                      onSaveSegment={handleSaveSegment}
                    />
                  </div>
                ) : (
                  <div className="text-center text-slate-500 py-10 bg-white rounded-2xl border border-dashed border-slate-200 p-8 shadow-2xs">
                    <Radio className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                    <h4 className="font-bold text-slate-800 text-sm">No Transcript Available Yet</h4>
                    <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                      Complete a live ambient audio recording session to generate a timestamped transcript.
                    </p>
                  </div>
                )}
                
                {/* Clinical Audit Timeline */}
                <div className="pt-2">
                  <AuditTimeline consultationId={consultation.id} />
                </div>
              </Tabs.Content>

              {/* TAB 5: Clinical Evidence & Citation Verification */}
              <Tabs.Content value="evidence" className="space-y-6 outline-none">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
                  {/* Left: Literature Guideline RAG Assistant */}
                  <div className="rounded-2xl border border-slate-200 bg-white shadow-2xs overflow-hidden min-h-[520px] flex flex-col">
                    <div className="p-3.5 border-b border-slate-100 bg-teal-50/60 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-teal-600" />
                        <div>
                          <h4 className="text-xs font-bold text-slate-900 m-0 uppercase tracking-wide">Literature RAG Assistant</h4>
                          <p className="text-[10px] text-slate-500 font-medium">Approved clinical trials, guidelines, and drug data</p>
                        </div>
                      </div>
                    </div>
                    <div className="flex-1">
                      <RAGAssistant />
                    </div>
                  </div>

                  {/* Right: Cryptographic Citation Verifier */}
                  <div className="rounded-2xl border border-slate-200 bg-white shadow-2xs overflow-hidden min-h-[520px] flex flex-col">
                    <div className="p-3.5 border-b border-slate-100 bg-purple-50/60 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <ShieldCheck className="w-4 h-4 text-purple-600" />
                        <div>
                          <h4 className="text-xs font-bold text-slate-900 m-0 uppercase tracking-wide">Citation &amp; Claim Verifier</h4>
                          <p className="text-[10px] text-slate-500 font-medium">Verify claim hashes against ingested evidence corpus</p>
                        </div>
                      </div>
                    </div>
                    <div className="flex-1">
                      <CitationVerifier />
                    </div>
                  </div>
                </div>
              </Tabs.Content>
            </div>
          </Tabs.Root>
        </div>
        
        {/* ── Resizable Split Divider ──────────────────────────────────────────────── */}
        {isSplitPane && paneMode === "split" && (
          <div 
            className="w-2 bg-slate-200 hover:bg-teal-400/40 flex flex-col items-center justify-center cursor-col-resize transition-colors border-l border-r border-slate-300 z-10 shrink-0 group/divider relative"
            onMouseDown={startDragging}
            title="Drag to resize split panes"
          >
            <GripVertical className="w-3.5 h-3.5 text-slate-400 group-hover/divider:text-teal-600 transition-colors" />
          </div>
        )}

        {/* ── Right Pane (Extended SOAP+ Clinical Note Editor) ────────────────────── */}
        {isSplitPane && paneMode !== "full-cockpit" && (
          <div 
            className={`shrink-0 bg-white h-full flex flex-col border-l border-slate-200 shadow-[-4px_0_16px_rgba(0,0,0,0.03)] relative z-10 overflow-hidden ${
              paneMode === "full-notes" ? "w-full" : ""
            }`}
            style={{ width: paneMode === "full-notes" ? "100%" : `${rightPaneWidth}px` }}
          >
            <ClinicalNoteEditor consultationId={consultation.id} />
          </div>
        )}
      </div>

      {/* ── Clinical Finding Explanation Slide-Over Modal ────────────────────────────── */}
      <AnimatePresence>
        {explainFindingId && (
          <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 15 }}
              className="w-full max-w-2xl max-h-[85vh] bg-white border border-slate-200 rounded-3xl shadow-2xl overflow-hidden flex flex-col text-left"
            >
              <ExplanationPanel 
                findingId={explainFindingId} 
                onClose={() => setExplainFindingId(null)} 
              />
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ── Informed Consent Dialog Modal Overlay ───────────────────────────────────── */}
      <AnimatePresence>
        {showConsentForm && !consent && (
          <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="w-full max-w-lg bg-white border border-slate-200 rounded-3xl p-6 sm:p-7 shadow-2xl relative overflow-hidden text-left"
            >
              <div className="absolute top-0 left-0 right-0 h-1.5 bg-teal-600" />
              
              <div className="flex items-start gap-4 mb-5">
                <div className="p-3 bg-teal-50 rounded-2xl text-teal-600 shrink-0 border border-teal-100">
                  <FileText className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-xl font-black font-heading text-slate-900 m-0 tracking-tight">
                    Informed Consent Required
                  </h3>
                  <p className="text-slate-500 mt-1 text-xs leading-relaxed">
                    Please verify that the patient or legal surrogate has provided explicit consent for real-time audio capture and AI synthesis.
                  </p>
                </div>
              </div>
              
              <form onSubmit={handleGrantConsent}>
                <div className="space-y-4 mb-6">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                      Consenting Party Name
                    </label>
                    <input 
                      type="text" 
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm text-slate-900 focus:bg-white focus:ring-2 focus:ring-teal-500 outline-none transition-all shadow-inner" 
                      value={consentActor} 
                      onChange={(e) => setConsentActor(e.target.value)} 
                      required 
                      placeholder="e.g. Patient Name or Legal Guardian" 
                      disabled={actionLoading} 
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                      Relationship to Patient
                    </label>
                    <select 
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm text-slate-900 focus:bg-white focus:ring-2 focus:ring-teal-500 outline-none transition-all shadow-inner" 
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

                <div className="flex flex-wrap items-center justify-end gap-2.5 border-t border-slate-100 pt-4">
                  <Button 
                    type="button" 
                    variant="ghost" 
                    onClick={() => {
                      setShowConsentForm(false);
                      setPendingTransition(null);
                    }} 
                    disabled={actionLoading}
                    className="text-xs font-semibold"
                  >
                    Cancel
                  </Button>
                  <Button 
                    type="button" 
                    variant="ghost" 
                    onClick={() => {
                      setShowConsentForm(false);
                      setPendingTransition(null);
                      setActiveTab("scratchpad");
                      toast.info("Switched to Manual Doctor Notes.");
                    }} 
                    disabled={actionLoading}
                    className="text-xs font-semibold text-teal-700 hover:bg-teal-50"
                  >
                    ✍️ Use Manual Notes Instead
                  </Button>
                  <Button 
                    type="submit" 
                    variant="primary" 
                    disabled={actionLoading} 
                    isLoading={actionLoading}
                    className="bg-teal-600 hover:bg-teal-700 text-xs font-bold px-5"
                  >
                    Record Consent
                  </Button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
