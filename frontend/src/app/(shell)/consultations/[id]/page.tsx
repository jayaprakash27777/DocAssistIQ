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
  Minimize2
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
  PLACEHOLDER_LABEL,
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
  const [isScratchpadDdxOpen, setIsScratchpadDdxOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<string>("ai-assistant");
  const [findingsFilter, setFindingsFilter] = useState<"all" | "pending" | "confirmed" | "negated">("all");
  const [paneMode, setPaneMode] = useState<"split" | "full-cockpit" | "full-notes">("split");
  const [isInlineDdxExpanded, setIsInlineDdxExpanded] = useState(true);
  const [explainFindingId, setExplainFindingId] = useState<string | null>(null);
  const [isSafetyAlertDismissed, setIsSafetyAlertDismissed] = useState(false);
  const [isSafetyAlertExpanded, setIsSafetyAlertExpanded] = useState(false);

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
    toast.success("Consultation ID copied to clipboard");
    setTimeout(() => setCopiedId(false), 2000);
  };

  const handleClearScratchpad = () => {
    if (!inputText) return;
    if (window.confirm("Are you sure you want to clear your scratchpad notes?")) {
      setInputText("");
      toast.info("Doctor notes cleared");
    }
  };

  const handleRestoreOriginal = () => {
    if (consultation?.input_text) {
      setInputText(consultation.input_text);
      toast.success("Restored original consultation notes");
    }
  };
  
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
  const [rightPaneWidth, setRightPaneWidth] = useState(460);
  const isDragging = useRef(false);

  const startDragging = useCallback((e: React.MouseEvent) => {
    isDragging.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, []);

  const onDrag = useCallback((e: MouseEvent) => {
    if (!isDragging.current) return;
    const newWidth = window.innerWidth - e.clientX;
    // Constrain width between 300px and 880px
    setRightPaneWidth(Math.min(Math.max(newWidth, 300), 880));
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
      queryClient.invalidateQueries({ queryKey: noteKeys.detail(id) });
      
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

      // Fetch Patient Profile if session linked
      if (res.data.patient_session_id) {
        const patRes = await getPatientProfile(res.data.patient_session_id);
        if (patRes.ok) {
          setPatientProfile(patRes.data);
        }
      }
    } else {
      toast.error(res.error.message || "Failed to load consultation");
      router.push("/consultations");
    }
    setLoading(false);
  }, [id, router, toast, queryClient]);

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
    if (audio.error) {
      toast.error(audio.error);
    }
  }, [audio.error, toast]);

  useEffect(() => {
    fetchConsultation();
  }, [fetchConsultation]);

  const handleTransition = async (newStatus: string, explicitConsent?: ConsentRecordResponse | null) => {
    if (!consultation) return;
    
    // UI Consent Guard
    const effectiveConsent = explicitConsent !== undefined ? explicitConsent : consent;
    if (newStatus === "recording" && (!effectiveConsent || !effectiveConsent.recording_permitted)) {
      toast.error("Explicit consent is required to start recording.");
      setPendingTransition(newStatus);
      setShowConsentForm(true);
      return;
    }
    
    setActionLoading(true);
    try {
      const res = await transitionConsultationStatus(consultation.id, {
        new_status: newStatus,
        input_text: inputText,
      });
      
      if (res.ok) {
        toast.success(`Transitioned to ${newStatus.toUpperCase()}`);
        setConsultation(res.data);
        queryClient.invalidateQueries({ queryKey: noteKeys.detail(consultation.id) });
        queryClient.invalidateQueries({ queryKey: consultationKeys.detail(consultation.id) });
        
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
          
          // Asynchronously process recorded audio with dual fail-safe
          setTimeout(async () => {
            let transcribedDirectly = false;
            const audioBlob = audio.getAudioBlob();
            
            if (audioBlob && audioBlob.size > 200) {
              toast.info("Transcribing audio with faster-whisper & speaker diarization...");
              const transRes = await transcribeConsultationAudio(consultation.id, audioBlob);
              if (transRes.ok && transRes.data.segments && transRes.data.segments.length > 0) {
                transcribedDirectly = true;
                toast.success("Speech-to-text diarization complete!");
                setDiarizedSegments(transRes.data.segments);
                setAsrText(transRes.data.text || "");
                const tRes = await getTranscript(consultation.id);
                if (tRes.ok) setSavedTranscript(tRes.data);
                await fetchConsultation();
              }
            }

            // Fallback: save live WebSocket diarized segments if direct upload didn't yield segments
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

            setTimeout(() => {
              handleTransition("draft");
            }, 1500);
          }, 300);
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
      fetchConsultation(); // Refresh findings list
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
        toast.success("Consent granted & recorded.");
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
    if (!consultation || !confirm("Are you sure you want to revoke consent? This will stop any active recording.")) return;
    setActionLoading(true);
    try {
      const res = await revokeConsent(consultation.id);
      if (res.ok) {
        toast.success("Consent revoked.");
        setConsent(null);
        fetchConsultation(); // Refresh consultation in case state changed
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
  }, [consultation?.findings, findingsFilter]);

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
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 text-center">
        <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-4 text-slate-400">
          <AlertCircle size={32} />
        </div>
        <h2 className="text-xl font-bold text-slate-800 mb-2 font-heading">Consultation Not Found</h2>
        <p className="text-slate-500 mb-6 text-sm">The requested consultation could not be found or has been removed.</p>
        <Link
          href="/consultations"
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-teal-600 to-indigo-600 text-white font-bold text-sm hover:brightness-110 transition-all shadow-sm"
        >
          Back to Consultations
        </Link>
      </div>
    );
  }

  const currentStatus = consultation.status;
  const isSplitPane = ["draft", "under_review", "analysis_ready", "finalized", "amended"].includes(currentStatus);
  const currentStageIndex = STAGE_INDEX_MAP[currentStatus] ?? 0;
  const pendingFindingsCount = consultation?.findings?.filter(f => f.status === "pending").length || 0;

  // Active CTA Button Generator for Header & Bottom Dock
  const renderWorkflowActions = (isCompact = false) => {
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
              className={`rounded-xl font-bold text-white transition-all bg-gradient-to-r from-teal-600 via-indigo-600 to-indigo-700 hover:from-teal-500 hover:to-indigo-600 shadow-md shadow-indigo-500/20 flex items-center gap-1.5 ${
                isCompact ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-xs"
              }`}
              title="Start real-time clinical audio capture with automated Doctor/Patient diarization"
            >
              <Mic className="w-3.5 h-3.5 text-teal-200 animate-pulse" />
              <span>Live Audio Recording</span>
            </button>
            <button 
              type="button"
              onClick={() => {
                setActiveTab("scratchpad");
                toast.info("Switched to Doctor Notes scratchpad — insert templates or enter findings.");
              }}
              disabled={actionLoading}
              className={`rounded-xl font-bold text-slate-700 dark:text-slate-200 transition-all bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-750 border border-slate-200 dark:border-slate-700 shadow-xs flex items-center gap-1.5 ${
                isCompact ? "px-2.5 py-1.5 text-xs" : "px-3.5 py-2 text-xs"
              }`}
              title="Enter manual doctor notes, clinical templates, or physical exam findings directly"
            >
              <FileText className="w-3.5 h-3.5 text-teal-600" />
              <span>Manual Doctor Notes</span>
            </button>
          </div>
        )}

        {currentStatus === "recording" && (
          <div className="flex items-center gap-2">
            <Button 
              variant="primary" 
              onClick={() => handleTransition("processing")}
              disabled={actionLoading}
              className={`font-bold bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-xs ${
                isCompact ? "h-8 px-3 text-xs" : "h-9 px-4 text-xs"
              }`}
            >
              Submit for Analysis
            </Button>
            <Button 
              variant="ghost" 
              onClick={() => handleTransition("created")}
              disabled={actionLoading}
              className={`font-bold text-rose-600 hover:bg-rose-50 rounded-xl ${
                isCompact ? "h-8 px-2.5 text-xs" : "h-9 px-3 text-xs"
              }`}
            >
              <Square className="w-3.5 h-3.5 mr-1" /> Stop
            </Button>
          </div>
        )}

        {currentStatus === "processing" && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800 text-xs font-bold text-purple-700 dark:text-purple-300 shadow-2xs">
            <div className="w-3.5 h-3.5 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
            <span>Synthesizing Audio &amp; Facts...</span>
          </div>
        )}

        {currentStatus === "draft" && (
          <Button 
            variant="primary" 
            onClick={() => handleTransition("under_review")} 
            disabled={actionLoading} 
            className={`font-bold bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-xs flex items-center gap-1.5 ${
              isCompact ? "h-8 px-3.5 text-xs" : "h-9 px-4 text-xs"
            }`}
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
              className={`font-bold bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-xs ${
                isCompact ? "h-8 px-3 text-xs" : "h-9 px-4 text-xs"
              }`}
            >
              Mark Analysis Ready
            </Button>
            <Button 
              variant="ghost" 
              onClick={() => handleTransition("draft")} 
              disabled={actionLoading} 
              className="h-8 px-2.5 text-xs font-medium rounded-xl"
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
              className={`font-bold bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-xs flex items-center gap-1.5 ${
                isCompact ? "h-8 px-3 text-xs" : "h-9 px-4 text-xs"
              }`}
            >
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Sign Off &amp; Finalize</span>
            </Button>
            <Button 
              variant="ghost" 
              onClick={() => handleTransition("under_review")} 
              disabled={actionLoading} 
              className="h-8 px-2.5 text-xs font-medium rounded-xl"
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
            className="h-8 px-3 text-xs font-bold rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800"
          >
            Amend Finalized Record
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
    <div className="consultation-workspace-root flex flex-col h-full min-h-0 overflow-hidden relative w-full bg-[var(--surface-base)]">
      
      {/* ── Tier 1: Executive Clinical Command Header ───────────────────────────────── */}
      <header className="bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border-b border-slate-200/90 dark:border-slate-800 shrink-0 z-20 shadow-xs">
        {/* Row 1: Identity, Metadata & Controls */}
        <div className="px-4 sm:px-6 py-2.5 flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800/80">
          <div className="flex items-center gap-3 min-w-0">
            <Link
              href="/consultations"
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-100/80 hover:bg-slate-200/80 transition-colors border border-slate-200/60 shrink-0"
              title="Back to consultations directory"
            >
              <ChevronLeft className="w-4 h-4 text-slate-500" />
              <span className="hidden sm:inline">Consultations</span>
            </Link>
            <span className="text-slate-300 dark:text-slate-700 hidden sm:inline">/</span>

            <div className="flex items-center gap-2.5 min-w-0">
              <h1 className="text-base sm:text-lg font-black font-heading text-slate-900 dark:text-white tracking-tight truncate">
                Consultation Workspace
              </h1>
              
              {/* Status Badge */}
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] uppercase tracking-wider font-extrabold flex items-center gap-1.5 shrink-0 shadow-2xs ${
                currentStatus === 'finalized' ? 'bg-emerald-50 text-emerald-800 border border-emerald-300 dark:bg-emerald-950/50 dark:text-emerald-300 dark:border-emerald-800' : 
                currentStatus === 'recording' ? 'bg-rose-50 text-rose-800 border border-rose-300 ring-2 ring-rose-200/50 dark:bg-rose-950/50 dark:text-rose-300 dark:border-rose-800' : 
                currentStatus === 'processing' ? 'bg-purple-50 text-purple-800 border border-purple-300 dark:bg-purple-950/50 dark:text-purple-300 dark:border-purple-800' :
                currentStatus === 'draft' ? 'bg-indigo-50 text-indigo-800 border border-indigo-300 dark:bg-indigo-950/50 dark:text-indigo-300 dark:border-indigo-800' :
                currentStatus === 'under_review' ? 'bg-amber-50 text-amber-800 border border-amber-300 dark:bg-amber-950/50 dark:text-amber-300 dark:border-amber-800' :
                'bg-slate-100 text-slate-700 border border-slate-300 dark:bg-slate-800 dark:text-slate-300'
              }`}>
                <span className={`w-2 h-2 rounded-full ${
                  currentStatus === 'recording' ? 'bg-rose-600 animate-ping' :
                  currentStatus === 'finalized' ? 'bg-emerald-600' :
                  currentStatus === 'processing' ? 'bg-purple-600 animate-pulse' :
                  'bg-indigo-600'
                }`} />
                <span>{currentStatus.replace('_', ' ')}</span>
              </span>

              {/* Minimized Red Flag Alert Pill (Takes 0 height in workspace) */}
              {representation?.safety_decision && representation.safety_decision.decision !== "ALLOW" && isSafetyAlertDismissed && (
                <button
                  type="button"
                  onClick={() => setIsSafetyAlertDismissed(false)}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black bg-red-600 hover:bg-red-700 text-white shadow-xs animate-pulse transition-all cursor-pointer shrink-0"
                  title="Click to review critical clinical safety warning"
                >
                  <AlertOctagon className="w-3.5 h-3.5 text-red-200" />
                  <span>RED FLAG ALERT ({representation.safety_decision.flags.length})</span>
                  <span className="text-[10px] font-semibold underline opacity-90 ml-0.5">Review</span>
                </button>
              )}
            </div>

            {/* Copyable Encounter ID Pill */}
            <button
              type="button"
              onClick={handleCopyId}
              className="group hidden md:inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 font-mono transition-colors bg-slate-50 dark:bg-slate-800/60 px-2.5 py-1 rounded-lg border border-slate-200/80 dark:border-slate-700/80 shrink-0"
              title="Click to copy full consultation ID"
            >
              <span>ENC #{consultation.id.slice(0, 8)}</span>
              {copiedId ? (
                <Check className="w-3 h-3 text-emerald-600" />
              ) : (
                <Copy className="w-3 h-3 opacity-60 group-hover:opacity-100" />
              )}
            </button>

            {/* Patient Context Badge */}
            {patientProfile ? (
              <Link
                href={`/patients/${patientProfile.id}`}
                className="hidden lg:inline-flex items-center gap-1.5 text-xs text-teal-800 dark:text-teal-300 bg-teal-50 dark:bg-teal-950/40 hover:bg-teal-100 px-2.5 py-1 rounded-lg border border-teal-200/80 dark:border-teal-800 transition-colors"
                title={`Patient: ${patientProfile.patient_ref} · Click to view profile`}
              >
                <User className="w-3 h-3 text-teal-600 dark:text-teal-400" />
                <span className="font-bold">{patientProfile.patient_ref}</span>
                {patientProfile.age_group && <span className="opacity-70">({patientProfile.age_group})</span>}
                {patientProfile.biological_sex && <span className="opacity-70">{patientProfile.biological_sex}</span>}
              </Link>
            ) : consultation.patient_session_id ? (
              <span className="hidden xl:inline-flex items-center gap-1 text-[11px] font-mono text-slate-400 bg-slate-50 dark:bg-slate-800/40 px-2 py-0.5 rounded border border-slate-200/60">
                Session: {consultation.patient_session_id.slice(0, 8)}
              </span>
            ) : (
              <span className="hidden xl:inline-flex items-center gap-1 text-[11px] text-slate-400 bg-slate-50 dark:bg-slate-800/40 px-2 py-0.5 rounded border border-slate-200/60">
                General Encounter
              </span>
            )}
          </div>

          {/* Right Controls: View Mode Switcher, Intake Link, Review Link, Informed Consent */}
          <div className="flex items-center gap-2 shrink-0">
            {/* View Mode Switcher for Split Screen */}
            {isSplitPane && (
              <div className="inline-flex items-center p-0.5 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700/80">
                <button
                  type="button"
                  onClick={() => setPaneMode("full-cockpit")}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all flex items-center gap-1.5 ${
                    paneMode === "full-cockpit"
                      ? "bg-white dark:bg-slate-700 text-teal-700 dark:text-teal-300 shadow-2xs font-black"
                      : "text-slate-600 hover:text-slate-900 dark:text-slate-400"
                  }`}
                  title="Big Screen Cockpit — Maximize Diagnostic Cockpit & Differential Diagnosis to 100% width"
                >
                  <Maximize2 className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                  <span>Big Screen Cockpit</span>
                </button>
                <button
                  type="button"
                  onClick={() => setPaneMode("split")}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all flex items-center gap-1 ${
                    paneMode === "split"
                      ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-2xs font-black"
                      : "text-slate-600 hover:text-slate-900 dark:text-slate-400"
                  }`}
                  title="Split View (Side-by-side Cockpit + Notes)"
                >
                  <Columns className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Split</span>
                </button>
                <button
                  type="button"
                  onClick={() => setPaneMode("full-notes")}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all flex items-center gap-1 ${
                    paneMode === "full-notes"
                      ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-2xs font-black"
                      : "text-slate-600 hover:text-slate-900 dark:text-slate-400"
                  }`}
                  title="Focus Notes (Full screen note editor)"
                >
                  <PanelRightOpen className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Notes</span>
                </button>
              </div>
            )}

            {/* Quick Intake Form Link */}
            <Link
              href={`/consultations/${id}/intake`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-teal-800 bg-teal-50 hover:bg-teal-100 border border-teal-200/80 shadow-2xs transition-all dark:bg-teal-950/40 dark:text-teal-300 dark:border-teal-800"
              title="Open structured clinical intake form"
            >
              <Sparkles className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
              <span className="hidden sm:inline">Intake Form</span>
            </Link>

            {/* Review Workspace Link */}
            <Link
              href={`/consultations/${id}/review`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-indigo-800 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200/80 shadow-2xs transition-all dark:bg-indigo-950/40 dark:text-indigo-300 dark:border-indigo-800"
              title="Open full Note Review Workspace"
            >
              <FileCheck className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
              <span className="hidden sm:inline">Review Workspace</span>
            </Link>

            {/* Informed Consent Status Badge */}
            {consent ? (
              <div className="flex items-center gap-1.5 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 px-3 py-1.5 rounded-xl border border-emerald-200 dark:border-emerald-800/80 shadow-2xs text-xs font-bold">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                <span className="hidden md:inline uppercase tracking-wide">Consent Granted</span>
                {["created", "recording"].includes(currentStatus) && (
                  <button 
                    type="button"
                    onClick={handleRevokeConsent} 
                    disabled={actionLoading} 
                    className="ml-1 text-[10px] underline hover:text-rose-600 text-slate-500 dark:text-slate-400 font-bold transition-colors"
                    title="Revoke recorded patient consent"
                  >
                    Revoke
                  </button>
                )}
              </div>
            ) : (
              <button
                type="button"
                onClick={() => {
                  setPendingTransition("recording");
                  setShowConsentForm(true);
                }}
                className="flex items-center gap-1.5 bg-rose-50 dark:bg-rose-950/40 hover:bg-rose-100 text-rose-800 dark:text-rose-300 px-3 py-1.5 rounded-xl border border-rose-200 dark:border-rose-800 shadow-2xs transition-all text-xs font-bold"
                title="Patient consent required before clinical recording"
              >
                <AlertCircle className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400 animate-pulse" />
                <span className="uppercase tracking-wide">Missing Consent</span>
              </button>
            )}
          </div>
        </div>

        {/* Row 2: Workflow Stepper & Primary Context Action Bar */}
        <div className="px-4 sm:px-6 py-1.5 bg-slate-50/70 dark:bg-slate-900/60 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 dark:border-slate-800/80">
          {/* Ultra-Compact Clinical Lifecycle Stepper */}
          <div className="flex items-center gap-2.5 shrink-0 py-0.5">
            <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider hidden sm:inline">
              Lifecycle:
            </span>
            <div className="flex items-center gap-1.5 bg-white dark:bg-slate-800 px-2.5 py-1 rounded-xl border border-slate-200/90 dark:border-slate-700 shadow-2xs">
              <span className="w-4 h-4 rounded-full bg-indigo-600 text-white flex items-center justify-center text-[10px] font-black">
                {currentStageIndex + 1}
              </span>
              <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                {WORKFLOW_STAGES[currentStageIndex]?.label || currentStatus.replace('_', ' ')}
              </span>
              <span className="text-[10px] text-slate-400 font-medium hidden md:inline">
                ({currentStageIndex + 1} of 7)
              </span>
            </div>

            {/* Segmented Micro Track with All 7 Stage Tooltips */}
            <div className="flex items-center gap-1" role="progressbar" aria-valuenow={currentStageIndex + 1} aria-valuemin={1} aria-valuemax={7}>
              {WORKFLOW_STAGES.map((st, idx) => {
                const isCurrent = st.id === currentStatus;
                const isPassed = currentStageIndex > idx;
                return (
                  <div
                    key={st.id}
                    title={`Stage ${idx + 1}: ${st.label} — ${st.desc}`}
                    className={`h-2 rounded-full transition-all cursor-help ${
                      isCurrent
                        ? "w-5 bg-indigo-600 shadow-xs ring-1 ring-indigo-300 dark:ring-indigo-700"
                        : isPassed
                        ? "w-2.5 bg-emerald-500"
                        : "w-1.5 bg-slate-200 dark:bg-slate-700"
                    }`}
                  />
                );
              })}
            </div>
          </div>

          {/* Right Action Box: Telemetry & Actions */}
          <div className="flex items-center gap-3 shrink-0">
            {/* Recording Audio Visualizer and Mic Status */}
            {currentStatus === "recording" && (
              <div className="px-3 py-1 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 font-mono text-xs font-bold flex items-center gap-2 shadow-2xs dark:bg-rose-950/50 dark:border-rose-800 dark:text-rose-300">
                <span className="w-2 h-2 rounded-full bg-rose-600 animate-ping" />
                <span>REC {formatElapsed(audio.elapsedMs)}</span>
                <div className="flex items-end gap-0.5 ml-1 h-3.5" title={`Mic volume: ${audio.audioLevel}%`}>
                  <span className="w-1 bg-emerald-500 rounded-full transition-all duration-75" style={{ height: `${Math.max(20, Math.min(100, audio.audioLevel * 1.2))}%` }} />
                  <span className="w-1 bg-emerald-500 rounded-full transition-all duration-75" style={{ height: `${Math.max(15, Math.min(100, audio.audioLevel * 0.8))}%` }} />
                  <span className="w-1 bg-emerald-500 rounded-full transition-all duration-75" style={{ height: `${Math.max(25, Math.min(100, audio.audioLevel * 1.4))}%` }} />
                  <span className="w-1 bg-emerald-500 rounded-full transition-all duration-75" style={{ height: `${Math.max(10, Math.min(100, audio.audioLevel * 1.0))}%` }} />
                </div>
                {audio.isSilent && (
                  <span className="text-[10px] text-amber-700 dark:text-amber-300 font-sans font-medium px-1.5 py-0.5 rounded bg-amber-100/90 dark:bg-amber-900/50 border border-amber-300 animate-pulse">
                    Mic silent
                  </span>
                )}
              </div>
            )}

            {/* Action transition CTA */}
            {renderWorkflowActions(true)}
          </div>
        </div>
      </header>

      {/* ── Phase 42: Red Flag Safety Decision Banner (Compact & Collapsible) ───────────────── */}
      {representation?.safety_decision && representation.safety_decision.decision !== "ALLOW" && !isSafetyAlertDismissed && (
        <div className="bg-red-50 dark:bg-red-950/70 border-b border-red-300 dark:border-red-800 px-4 sm:px-6 py-2 shrink-0 z-20 shadow-xs">
          <div className="flex flex-wrap items-center justify-between gap-3 max-w-7xl mx-auto">
            {/* Left: Badge, Heading, Version, Primary Message */}
            <div className="flex items-center gap-2.5 min-w-0 flex-1">
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-red-600 text-white text-[10px] font-black uppercase tracking-wider shrink-0 shadow-2xs">
                <AlertOctagon className="w-3 h-3 text-red-100 animate-pulse" />
                <span>RED FLAG</span>
              </span>

              <span className="text-xs font-bold text-red-950 dark:text-red-100 shrink-0">
                Critical Safety Warning
              </span>

              <span className="hidden sm:inline-block bg-red-100 text-red-800 text-[10px] px-1.5 py-0.5 rounded font-mono border border-red-200 dark:bg-red-900/60 dark:text-red-300 shrink-0">
                v{representation.safety_decision.flags[0]?.rule_version || "1.0"}
              </span>

              <p className="text-xs text-red-800 dark:text-red-200 font-semibold truncate min-w-0 flex-1" title={representation.safety_decision.flags[0]?.message}>
                {representation.safety_decision.flags[0]?.message || "Altered consciousness or critical safety indicator detected."}
              </p>
            </div>

            {/* Right: Expand details + Acknowledge & Minimize */}
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={() => setIsSafetyAlertExpanded(prev => !prev)}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold text-red-900 hover:text-red-950 bg-red-100 hover:bg-red-200/80 border border-red-200 dark:bg-red-900/60 dark:text-red-200 transition-colors cursor-pointer"
              >
                <span>{isSafetyAlertExpanded ? "Hide Details" : `Details (${representation.safety_decision.flags.length})`}</span>
                {isSafetyAlertExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>

              <button
                type="button"
                onClick={() => {
                  setIsSafetyAlertDismissed(true);
                  toast.success("Critical safety alert minimized to top bar. Workspace expanded!");
                }}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold text-white bg-red-700 hover:bg-red-800 shadow-2xs transition-colors cursor-pointer"
                title="Acknowledge alert and minimize into header to grant full screen space to Differential Diagnosis"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Acknowledge &amp; Minimize</span>
              </button>
            </div>
          </div>

          {/* Collapsible Details Drawer */}
          {isSafetyAlertExpanded && (
            <div className="mt-2.5 pt-2.5 border-t border-red-200 dark:border-red-800/80 space-y-2 max-w-7xl mx-auto animate-in fade-in duration-150">
              {representation.safety_decision.flags.map((flag, idx) => (
                <div key={idx} className="bg-white/90 dark:bg-slate-900/90 p-3 rounded-xl border border-red-200 dark:border-red-900/60 shadow-2xs flex items-start gap-2.5">
                  <span className="mt-0.5">
                    {flag.severity === 'CRITICAL' ? (
                      <AlertOctagon className="w-4 h-4 text-red-600 shrink-0" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                    )}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-red-950 dark:text-red-100 text-xs uppercase tracking-wide">
                        {flag.category.replace('_', ' ')}
                      </span>
                      <span className="text-[10px] font-mono text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-950 px-1.5 py-0.5 rounded border border-red-200/60 font-bold">
                        {flag.severity}
                      </span>
                    </div>
                    <p className="text-red-800 dark:text-red-200 text-xs font-medium mt-0.5 leading-relaxed">{flag.message}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Main Workspace Body (Split / Multi-Pane Layout) ─────────────────────────── */}
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
            <div className="px-4 sm:px-6 py-2 border-b border-slate-200/80 bg-white/95 backdrop-blur-md shrink-0 flex flex-wrap items-center justify-between gap-3">
              <Tabs.List className="flex flex-wrap items-center gap-1.5 p-1 bg-slate-100 rounded-2xl border border-slate-200/80">
                <Tabs.Trigger 
                  value="ai-assistant" 
                  className="px-3.5 py-1.5 text-xs font-bold rounded-xl transition-all flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs text-slate-600 hover:text-slate-900 outline-none"
                >
                  <Activity className="w-3.5 h-3.5 text-teal-600" />
                  <span>Live AI Cockpit</span>
                  {currentStatus === "recording" && (
                    <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                  )}
                </Tabs.Trigger>

                <Tabs.Trigger 
                  value="intelligence" 
                  className="px-3.5 py-1.5 text-xs font-bold rounded-xl transition-all flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs text-slate-600 hover:text-slate-900 outline-none"
                >
                  <Zap className="w-3.5 h-3.5 text-amber-500" />
                  <span>Differential &amp; Intelligence (Full View)</span>
                  {consultation.findings && consultation.findings.length > 0 && (
                    <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-indigo-100 text-indigo-700 font-mono font-bold">
                      {consultation.findings.length}
                    </span>
                  )}
                </Tabs.Trigger>

                <Tabs.Trigger 
                  value="transcript" 
                  className="px-3.5 py-1.5 text-xs font-bold rounded-xl transition-all flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs text-slate-600 hover:text-slate-900 outline-none"
                >
                  <Radio className="w-3.5 h-3.5 text-indigo-500" />
                  <span>Transcript &amp; Audit</span>
                </Tabs.Trigger>

                <Tabs.Trigger 
                  value="scratchpad" 
                  className="px-3.5 py-1.5 text-xs font-bold rounded-xl transition-all flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs text-slate-600 hover:text-slate-900 outline-none"
                >
                  <FileText className="w-3.5 h-3.5 text-slate-600" />
                  <span>Doctor Notes</span>
                  {inputText.trim() && (
                    <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
                  )}
                </Tabs.Trigger>

                <Tabs.Trigger 
                  value="evidence" 
                  className="px-3.5 py-1.5 text-xs font-bold rounded-xl transition-all flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs text-slate-600 hover:text-slate-900 outline-none"
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
                <span className="text-[10px] uppercase tracking-wider font-extrabold text-slate-600 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200/80">
                  Stage: {currentStatus}
                </span>
              </div>
            </div>

            {/* Scrollable Tab Content Container */}
            <div className="flex-1 min-h-0 overflow-y-auto p-4 sm:p-6 lg:p-7 space-y-6">
              
              {/* TAB 1: Live AI Cockpit */}
              <Tabs.Content value="ai-assistant" className="space-y-6 outline-none">
                {(!isSplitPane || paneMode === "full-cockpit") ? (
                  /* Spacious 2-Column Clinical Cockpit for wide displays */
                  <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
                    {/* Left Column: Scenario, Recording, Findings, Chat */}
                    <div className="xl:col-span-5 space-y-6">
                      {consultation.input_text && (
                        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs">
                          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                            Clinical Scenario / Chief Complaint
                          </span>
                          <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                            {consultation.input_text}
                          </p>
                        </div>
                      )}

                      {currentStatus === "created" && (
                        <div className="p-4 rounded-2xl bg-gradient-to-r from-teal-50/70 via-indigo-50/40 to-white dark:from-slate-800 dark:to-slate-900 border border-teal-200/80 dark:border-teal-900/60 shadow-2xs space-y-2.5">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <Sparkles className="w-4 h-4 text-teal-600" />
                              <span className="text-xs font-black uppercase tracking-wider text-slate-800 dark:text-slate-200 font-heading">
                                Choose Documentation Modality
                              </span>
                            </div>
                            <span className="text-[10px] font-bold text-teal-700 bg-teal-100/70 dark:bg-teal-950/60 px-2 py-0.5 rounded-full border border-teal-200 dark:border-teal-800">
                              Clinical Grade
                            </span>
                          </div>
                          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed font-medium">
                            Document the encounter using live ambient audio transcription with Doctor/Patient diarization or type notes directly into the clinical scratchpad:
                          </p>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
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
                              className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-teal-200 hover:border-teal-400 hover:shadow-xs transition-all text-left flex items-start gap-3 group"
                            >
                              <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center shrink-0 border border-teal-200 group-hover:bg-teal-600 group-hover:text-white transition-colors">
                                <Mic className="w-4 h-4" />
                              </div>
                              <div>
                                <span className="text-xs font-bold text-slate-800 dark:text-white block">
                                  Live Audio Transcription
                                </span>
                                <span className="text-[11px] text-slate-500 block leading-snug">
                                  Natural dialogue capture with Doctor &amp; Patient diarization.
                                </span>
                              </div>
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                setActiveTab("scratchpad");
                                toast.info("Switched to Doctor Notes scratchpad — insert templates or enter findings.");
                              }}
                              className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-indigo-200 hover:border-indigo-400 hover:shadow-xs transition-all text-left flex items-start gap-3 group"
                            >
                              <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0 border border-indigo-200 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                                <FileText className="w-4 h-4" />
                              </div>
                              <div>
                                <span className="text-xs font-bold text-slate-800 dark:text-white block">
                                  Manual Doctor Notes
                                </span>
                                <span className="text-[11px] text-slate-500 block leading-snug">
                                  Type or paste findings and templates. No audio consent needed.
                                </span>
                              </div>
                            </button>
                          </div>
                        </div>
                      )}

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
                        <div className="p-5 bg-white dark:bg-slate-900 border border-indigo-200 dark:border-indigo-900/60 shadow-2xs rounded-3xl relative overflow-hidden">
                          <div className="absolute top-0 left-0 w-1.5 h-full bg-indigo-600" />
                          <div className="flex flex-wrap justify-between items-center gap-2 mb-4">
                            <h3 className="text-sm font-bold tracking-wide text-indigo-900 dark:text-indigo-300 uppercase flex items-center gap-2 m-0 font-heading">
                              <Activity className="w-4 h-4 text-indigo-600" />
                              Extracted Clinical Findings ({consultation.findings.length})
                            </h3>
                            <div className="flex items-center gap-1.5">
                              {pendingFindingsCount > 0 && (
                                <button
                                  type="button"
                                  onClick={handleConfirmAllFindings}
                                  disabled={actionLoading}
                                  className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 transition-colors flex items-center gap-1"
                                  title="Confirm all pending findings at once"
                                >
                                  <CheckCheck className="w-3 h-3 text-emerald-600" />
                                  Confirm All ({pendingFindingsCount})
                                </button>
                              )}
                              <button
                                type="button"
                                onClick={() => setFindingsFilter("all")}
                                className={`px-2 py-0.5 rounded-lg text-[10px] font-bold ${
                                  findingsFilter === "all" ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                                }`}
                              >
                                All
                              </button>
                              <button
                                type="button"
                                onClick={() => setFindingsFilter("pending")}
                                className={`px-2 py-0.5 rounded-lg text-[10px] font-bold ${
                                  findingsFilter === "pending" ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                                }`}
                              >
                                Pending
                              </button>
                              <button
                                type="button"
                                onClick={() => setFindingsFilter("confirmed")}
                                className={`px-2 py-0.5 rounded-lg text-[10px] font-bold ${
                                  findingsFilter === "confirmed" ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                                }`}
                              >
                                Confirmed
                              </button>
                            </div>
                          </div>
                          
                          <div className="flex flex-wrap gap-2.5">
                            {filteredFindings.map((finding: any) => (
                              <motion.div 
                                key={finding.id} 
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className={`p-3 rounded-2xl border flex flex-col gap-1.5 min-w-[170px] shadow-2xs transition-colors ${
                                  finding.negated 
                                    ? "bg-rose-50/70 border-rose-200" 
                                    : finding.status === "confirmed" 
                                      ? "bg-emerald-50/80 border-emerald-200" 
                                      : "bg-white border-slate-200 hover:border-indigo-300"
                                }`}
                              >
                                <div className="flex justify-between items-start gap-2">
                                  <span className={`text-sm font-bold capitalize ${finding.negated ? "text-rose-700 line-through opacity-80" : "text-slate-800"}`}>
                                    {finding.value}
                                  </span>
                                  {finding.confidence_score && (
                                    <span className="text-[0.65rem] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                                      {(finding.confidence_score * 100).toFixed(0)}%
                                    </span>
                                  )}
                                </div>
                                
                                {finding.canonical_concept && finding.canonical_concept !== finding.value.toLowerCase() && (
                                  <div className="text-[0.7rem] text-slate-500 italic flex items-center gap-1">
                                    <ArrowRight className="w-2.5 h-2.5 text-slate-400" />
                                    <span>{finding.canonical_concept}</span>
                                    {finding.mapping_source && <span className="opacity-60">({finding.mapping_source})</span>}
                                  </div>
                                )}
                                
                                <div className="flex flex-wrap gap-1 mt-1">
                                  <span className="text-[0.65rem] px-1.5 py-0.5 bg-slate-100 border border-slate-200 rounded text-slate-600 font-medium">
                                    {finding.concept || finding.finding_type}
                                  </span>
                                  {finding.temporality && finding.temporality !== "current" && (
                                    <span className="text-[0.65rem] px-1.5 py-0.5 bg-amber-50 border border-amber-200 rounded text-amber-700 font-medium">
                                      {finding.temporality}
                                    </span>
                                  )}
                                  {finding.negated && (
                                    <span className="text-[0.65rem] px-1.5 py-0.5 bg-rose-100 text-rose-700 rounded font-bold">
                                      NEGATED
                                    </span>
                                  )}
                                  {finding.status === "confirmed" && (
                                    <span className="text-[0.65rem] px-1.5 py-0.5 bg-emerald-100 text-emerald-700 rounded font-bold flex items-center gap-1">
                                      <Check className="w-2.5 h-2.5" /> CONFIRMED
                                    </span>
                                  )}
                                  {finding.status === "rejected" && (
                                    <span className="text-[0.65rem] px-1.5 py-0.5 bg-rose-100 text-rose-700 rounded font-bold flex items-center gap-1">
                                      <X className="w-2.5 h-2.5" /> REJECTED
                                    </span>
                                  )}
                                </div>
                                
                                <div className="flex items-center gap-1.5 mt-2 pt-2 border-t border-slate-100">
                                  <button
                                    type="button"
                                    onClick={() => setExplainFindingId(finding.id)}
                                    className="px-2 py-1 text-[0.65rem] font-bold text-indigo-700 bg-indigo-50/70 hover:bg-indigo-100 rounded-lg border border-indigo-200 transition-colors flex items-center gap-1"
                                    title="View clinical rationale and evidence provenance"
                                  >
                                    <HelpCircle className="w-2.5 h-2.5" />
                                    Why?
                                  </button>
                                  {finding.status === "pending" && (
                                    <>
                                      <button 
                                        type="button" 
                                        className="flex-1 py-1 px-2 text-[0.65rem] font-bold rounded-lg bg-slate-100 hover:bg-rose-50 hover:text-rose-600 transition-colors border border-slate-200" 
                                        onClick={() => handleReviewFinding(finding.id, "reject")}
                                      >
                                        Reject
                                      </button>
                                      <button 
                                        type="button" 
                                        className="flex-1 py-1 px-2 text-[0.65rem] font-bold rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-colors border border-indigo-200" 
                                        onClick={() => handleReviewFinding(finding.id, "confirm")}
                                      >
                                        Confirm
                                      </button>
                                    </>
                                  )}
                                </div>
                              </motion.div>
                            ))}
                          </div>
                        </div>
                      )}

                      <InlineAIChat consultationId={consultation.id} notes={consultation.input_text || inputText} />
                    </div>

                    {/* Right Column: Full-Width AI Differential Diagnosis & Similar Cases */}
                    <div className="xl:col-span-7 space-y-6">
                      {isSplitPane && paneMode === "full-cockpit" && (
                        <div className="flex items-center justify-between p-3 rounded-2xl bg-teal-50 dark:bg-slate-800 border border-teal-200 dark:border-teal-900/60 shadow-2xs">
                          <div className="flex items-center gap-2">
                            <Maximize2 className="w-4 h-4 text-teal-600" />
                            <span className="text-xs font-bold text-teal-950 dark:text-teal-200">
                              Big Screen Cockpit Mode Active — Differential Diagnosis maximized
                            </span>
                          </div>
                          <button
                            type="button"
                            onClick={() => setPaneMode("split")}
                            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold text-slate-700 bg-white hover:bg-slate-100 border border-slate-300 shadow-2xs transition-colors cursor-pointer"
                          >
                            <Columns className="w-3.5 h-3.5 text-slate-600" />
                            <span>Restore Split View</span>
                          </button>
                        </div>
                      )}

                      <DifferentialDiagnosis 
                        consultationId={consultation.id} 
                        trigger={consultation.findings?.length || consultation.status}
                        initialQuery={consultation.input_text || inputText}
                      />

                      <SimilarCasesPanel consultationId={consultation.id} />
                    </div>
                  </div>
                ) : (
                  /* Split-Pane Single Column Layout: Perfectly Structured Cards */
                  <div className="space-y-6">
                    {consultation.input_text && (
                      <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                          Clinical Scenario / Chief Complaint
                        </span>
                        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                          {consultation.input_text}
                        </p>
                      </div>
                    )}

                    {currentStatus === "created" && (
                      <div className="p-4 rounded-2xl bg-gradient-to-r from-teal-50/70 via-indigo-50/40 to-white dark:from-slate-800 dark:to-slate-900 border border-teal-200/80 dark:border-teal-900/60 shadow-2xs space-y-2.5">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <Sparkles className="w-4 h-4 text-teal-600" />
                            <span className="text-xs font-black uppercase tracking-wider text-slate-800 dark:text-slate-200 font-heading">
                              Choose Documentation Modality
                            </span>
                          </div>
                          <span className="text-[10px] font-bold text-teal-700 bg-teal-100/70 dark:bg-teal-950/60 px-2 py-0.5 rounded-full border border-teal-200 dark:border-teal-800">
                            Clinical Grade
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed font-medium">
                          Document the encounter using live ambient audio transcription with Doctor/Patient diarization or type notes directly into the clinical scratchpad:
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                          <button
                            type="button"
                            onClick={() => {
                              if (!consent) setShowConsentForm(true);
                              else handleTransition("recording");
                            }}
                            className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-teal-200 hover:border-teal-400 hover:shadow-xs transition-all text-left flex items-start gap-3 group"
                          >
                            <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center shrink-0 border border-teal-200 group-hover:bg-teal-600 group-hover:text-white transition-colors">
                              <Mic className="w-4 h-4" />
                            </div>
                            <div>
                              <span className="text-xs font-bold text-slate-800 dark:text-white block">
                                Live Audio Transcription
                              </span>
                              <span className="text-[11px] text-slate-500 block leading-snug">
                                Natural dialogue capture with Doctor &amp; Patient diarization.
                              </span>
                            </div>
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              setActiveTab("scratchpad");
                              toast.info("Switched to Doctor Notes scratchpad — insert templates or enter findings.");
                            }}
                            className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-indigo-200 hover:border-indigo-400 hover:shadow-xs transition-all text-left flex items-start gap-3 group"
                          >
                            <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0 border border-indigo-200 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                              <FileText className="w-4 h-4" />
                            </div>
                            <div>
                              <span className="text-xs font-bold text-slate-800 dark:text-white block">
                                Manual Doctor Notes
                              </span>
                              <span className="text-[11px] text-slate-500 block leading-snug">
                                Type or paste findings and templates. No audio consent needed.
                              </span>
                            </div>
                          </button>
                        </div>
                      </div>
                    )}

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
                      <div className="p-5 bg-white dark:bg-slate-900 border border-indigo-200 dark:border-indigo-900/60 shadow-2xs rounded-3xl relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-1.5 h-full bg-indigo-600" />
                        <div className="flex flex-wrap justify-between items-center gap-2 mb-4">
                          <h3 className="text-sm font-bold tracking-wide text-indigo-900 dark:text-indigo-300 uppercase flex items-center gap-2 m-0 font-heading">
                            <Activity className="w-4 h-4 text-indigo-600" />
                            Extracted Clinical Findings ({consultation.findings.length})
                          </h3>
                          <div className="flex items-center gap-1.5">
                            {pendingFindingsCount > 0 && (
                              <button
                                type="button"
                                onClick={handleConfirmAllFindings}
                                disabled={actionLoading}
                                className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 transition-colors flex items-center gap-1"
                                title="Confirm all pending findings at once"
                              >
                                <CheckCheck className="w-3 h-3 text-emerald-600" />
                                Confirm All ({pendingFindingsCount})
                              </button>
                            )}
                            <button
                              type="button"
                              onClick={() => setFindingsFilter("all")}
                              className={`px-2 py-0.5 rounded-lg text-[10px] font-bold ${
                                findingsFilter === "all" ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                              }`}
                            >
                              All
                            </button>
                            <button
                              type="button"
                              onClick={() => setFindingsFilter("pending")}
                              className={`px-2 py-0.5 rounded-lg text-[10px] font-bold ${
                                findingsFilter === "pending" ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                              }`}
                            >
                              Pending
                            </button>
                            <button
                              type="button"
                              onClick={() => setFindingsFilter("confirmed")}
                              className={`px-2 py-0.5 rounded-lg text-[10px] font-bold ${
                                findingsFilter === "confirmed" ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                              }`}
                            >
                              Confirmed
                            </button>
                          </div>
                        </div>
                        
                        <div className="flex flex-wrap gap-2.5">
                          {filteredFindings.map((finding: any) => (
                            <div 
                              key={finding.id} 
                              className={`p-3 rounded-2xl border flex flex-col gap-1.5 min-w-[170px] shadow-2xs transition-colors ${
                                finding.negated 
                                  ? "bg-rose-50/70 border-rose-200" 
                                  : finding.status === "confirmed" 
                                    ? "bg-emerald-50/80 border-emerald-200" 
                                    : "bg-white border-slate-200 hover:border-indigo-300"
                              }`}
                            >
                              <div className="flex justify-between items-start gap-2">
                                <span className={`text-sm font-bold capitalize ${finding.negated ? "text-rose-700 line-through opacity-80" : "text-slate-800"}`}>
                                  {finding.value}
                                </span>
                                {finding.confidence_score && (
                                  <span className="text-[0.65rem] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                                    {(finding.confidence_score * 100).toFixed(0)}%
                                  </span>
                                )}
                              </div>
                              
                              {finding.canonical_concept && finding.canonical_concept !== finding.value.toLowerCase() && (
                                <div className="text-[0.7rem] text-slate-500 italic flex items-center gap-1">
                                  <ArrowRight className="w-2.5 h-2.5 text-slate-400" />
                                  <span>{finding.canonical_concept}</span>
                                </div>
                              )}
                              
                              <div className="flex flex-wrap gap-1 mt-1">
                                <span className="text-[0.65rem] px-1.5 py-0.5 bg-slate-100 border border-slate-200 rounded text-slate-600 font-medium">
                                  {finding.concept || finding.finding_type}
                                </span>
                                {finding.temporality && finding.temporality !== "current" && (
                                  <span className="text-[0.65rem] px-1.5 py-0.5 bg-amber-50 border border-amber-200 rounded text-amber-700 font-medium">
                                    {finding.temporality}
                                  </span>
                                )}
                                {finding.negated && (
                                  <span className="text-[0.65rem] px-1.5 py-0.5 bg-rose-100 text-rose-700 rounded font-bold">
                                    NEGATED
                                  </span>
                                )}
                                {finding.status === "confirmed" && (
                                  <span className="text-[0.65rem] px-1.5 py-0.5 bg-emerald-100 text-emerald-700 rounded font-bold flex items-center gap-1">
                                    <Check className="w-2.5 h-2.5" /> CONFIRMED
                                  </span>
                                )}
                                {finding.status === "rejected" && (
                                  <span className="text-[0.65rem] px-1.5 py-0.5 bg-rose-100 text-rose-700 rounded font-bold flex items-center gap-1">
                                    <X className="w-2.5 h-2.5" /> REJECTED
                                  </span>
                                )}
                              </div>
                              
                              <div className="flex items-center gap-1.5 mt-2 pt-2 border-t border-slate-100">
                                <button
                                  type="button"
                                  onClick={() => setExplainFindingId(finding.id)}
                                  className="px-2 py-1 text-[0.65rem] font-bold text-indigo-700 bg-indigo-50/70 hover:bg-indigo-100 rounded-lg border border-indigo-200 transition-colors flex items-center gap-1"
                                  title="View clinical rationale and evidence provenance"
                                >
                                  <HelpCircle className="w-2.5 h-2.5" />
                                  Why?
                                </button>
                                {finding.status === "pending" && (
                                  <>
                                    <button 
                                      type="button" 
                                      className="flex-1 py-1 px-2 text-[0.65rem] font-bold rounded-lg bg-slate-100 hover:bg-rose-50 hover:text-rose-600 transition-colors border border-slate-200" 
                                      onClick={() => handleReviewFinding(finding.id, "reject")}
                                    >
                                      Reject
                                    </button>
                                    <button 
                                      type="button" 
                                      className="flex-1 py-1 px-2 text-[0.65rem] font-bold rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-colors border border-indigo-200" 
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

                    <InlineAIChat consultationId={consultation.id} notes={consultation.input_text || inputText} />

                    {/* Integrated Differential Diagnosis Section in Split View */}
                    <div className="rounded-3xl border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 shadow-2xs space-y-4">
                      <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-2xl bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-800 flex items-center justify-center text-amber-600">
                            <Zap className="w-4 h-4 text-amber-500 fill-amber-500 animate-pulse" />
                          </div>
                          <div>
                            <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider font-heading m-0">
                              Differential Diagnosis &amp; Decision Support
                            </h3>
                            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                              Real-time clinical probability scoring &amp; disease surveillance
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => setPaneMode("full-cockpit")}
                            className="text-xs font-bold text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-3 py-1.5 rounded-xl border border-teal-200/80 transition-colors flex items-center gap-1.5 shadow-2xs cursor-pointer"
                            title="Maximize Differential Diagnosis and Clinical Cockpit to Big Screen full width"
                          >
                            <Maximize2 className="w-3.5 h-3.5 text-teal-600" />
                            <span>Big Screen Cockpit</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => setActiveTab("intelligence")}
                            className="text-xs font-bold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-3 py-1.5 rounded-xl border border-indigo-200/80 transition-colors"
                          >
                            Full Deep-Dive Tab →
                          </button>
                          <button
                            type="button"
                            onClick={() => setIsInlineDdxExpanded(prev => !prev)}
                            className="p-1.5 rounded-xl text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                          >
                            {isInlineDdxExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>

                      {isInlineDdxExpanded && (
                        <div className="pt-2">
                          <DifferentialDiagnosis 
                            consultationId={consultation.id} 
                            trigger={consultation.findings?.length || consultation.status}
                            initialQuery={consultation.input_text || inputText}
                          />
                        </div>
                      )}
                    </div>
                    
                    <SimilarCasesPanel consultationId={consultation.id} />
                  </div>
                )}
              </Tabs.Content>

              {/* TAB 2: Clinical Intelligence & DDx (Expansive Dedicated View) */}
              <Tabs.Content value="intelligence" className="space-y-6 outline-none">
                <DifferentialDiagnosis 
                  consultationId={consultation.id} 
                  trigger={consultation.findings?.length || consultation.status}
                  initialQuery={consultation.input_text || inputText}
                />
                <SimilarCasesPanel consultationId={consultation.id} />
              </Tabs.Content>

              {/* TAB 3: Transcript & Clinical Audit Trail */}
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
                  <div className="text-center text-slate-500 py-12 bg-white dark:bg-slate-900 rounded-3xl border border-dashed border-slate-200 dark:border-slate-800 p-8 shadow-2xs">
                    <Radio className="w-8 h-8 text-slate-400 mx-auto mb-3" />
                    <h4 className="font-bold text-slate-800 dark:text-slate-200 text-sm">No Diarized Transcript Available Yet</h4>
                    <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                      Complete a live ambient audio recording session using the button above to generate a timestamped transcript.
                    </p>
                  </div>
                )}
                
                {/* Clinical Audit Timeline */}
                <div className="pt-4">
                  <AuditTimeline consultationId={consultation.id} />
                </div>
              </Tabs.Content>

              {/* TAB 4: Doctor Notes & Scratchpad */}
              <Tabs.Content value="scratchpad" className="space-y-6 outline-none flex flex-col">
                {/* Header & Quick Links */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200/80">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-teal-500/10 text-teal-700 border border-teal-500/20 flex items-center justify-center shadow-xs">
                      <FileText className="w-5 h-5 text-teal-600" />
                    </div>
                    <div>
                      <h3 className="text-base font-black tracking-tight text-slate-900 dark:text-white font-heading flex items-center gap-2">
                        Doctor Notes Workspace
                        <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200">
                          Live Scratchpad
                        </span>
                      </h3>
                      <p className="text-xs text-slate-500 font-medium">
                        Document free-form clinical observations or insert validated hospital benchmark templates.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <Link
                      href={`/consultations/${id}/intake`}
                      className="text-xs font-bold text-teal-700 bg-teal-50/80 hover:bg-teal-100 px-3.5 py-2 rounded-xl border border-teal-200 shadow-2xs transition-all flex items-center gap-1.5"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-teal-600" />
                      Structured Intake Form
                    </Link>
                  </div>
                </div>

                {/* 1-Click Clinical Template Bar (Compact Ergonomic Toolbar) */}
                <div className="bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-2xl p-3 sm:p-3.5 shadow-2xs space-y-2.5">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-1.5 font-heading">
                      <Sparkles className="w-3.5 h-3.5 text-teal-600" />
                      1-Click Clinical Templates:
                    </span>
                    <span className="text-[10px] text-slate-400 font-medium">Instantly populates structured medical sections</span>
                  </div>
                  
                  <div className="flex flex-wrap items-center gap-1.5">
                    {CLINICAL_TEMPLATES.map((tmpl) => (
                      <button
                        key={tmpl.id}
                        type="button"
                        onClick={() => handleInsertTemplate(tmpl.text)}
                        disabled={actionLoading || currentStatus === "finalized"}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 hover:bg-teal-50 dark:hover:bg-teal-950/40 border border-slate-200/80 hover:border-teal-300 text-xs font-semibold text-slate-700 hover:text-teal-900 shadow-2xs transition-colors disabled:opacity-50 text-left"
                      >
                        {tmpl.iconType === "heart" ? (
                          <HeartPulse className="w-3.5 h-3.5 text-rose-500 shrink-0" />
                        ) : tmpl.iconType === "temp" ? (
                          <Thermometer className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                        ) : tmpl.iconType === "scope" ? (
                          <Stethoscope className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                        ) : tmpl.iconType === "activity" ? (
                          <Activity className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                        ) : (
                          <FileText className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                        )}
                        <span>{tmpl.label}</span>
                        <span className="text-[9px] font-semibold uppercase px-1.5 py-0.5 rounded-md bg-white dark:bg-slate-700 text-slate-500 dark:text-slate-300 border border-slate-200/60 dark:border-slate-600">
                          {tmpl.badge}
                        </span>
                      </button>
                    ))}
                  </div>

                  {/* Rapid 1-Click Section Inserters */}
                  <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center gap-1.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mr-1 flex items-center gap-1">
                      <Plus className="w-3 h-3 text-slate-400" /> Add Section:
                    </span>
                    {SCRATCHPAD_SECTIONS.map((sec) => (
                      <button
                        key={sec.id}
                        type="button"
                        onClick={() => handleInsertSection(sec.snippet)}
                        disabled={actionLoading || currentStatus === "finalized"}
                        className="px-2.5 py-1 rounded-xl text-xs font-semibold bg-white dark:bg-slate-800 hover:bg-indigo-50 border border-slate-200 hover:border-indigo-300 text-slate-600 hover:text-indigo-700 shadow-2xs transition-colors disabled:opacity-50"
                      >
                        {sec.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Expansive Editor Canvas Card */}
                <div className="rounded-3xl border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm overflow-hidden flex flex-col focus-within:ring-4 focus-within:ring-teal-500/10 focus-within:border-teal-500 transition-all">
                  {/* Editor Utility Toolbar */}
                  <div className="bg-slate-50/90 dark:bg-slate-800/80 border-b border-slate-200/90 dark:border-slate-800 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={handleInsertTimestamp}
                        disabled={actionLoading || currentStatus === "finalized"}
                        title="Insert current timestamp [HH:MM]"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-200 shadow-2xs transition-all disabled:opacity-40"
                      >
                        <Clock className="w-3.5 h-3.5 text-slate-500" />
                        Timestamp
                      </button>

                      <button
                        type="button"
                        onClick={handleCopyScratchpad}
                        disabled={!inputText.trim()}
                        title="Copy all doctor notes to clipboard"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-200 shadow-2xs transition-all disabled:opacity-40"
                      >
                        {copiedScratchpad ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-emerald-600" />
                            <span className="text-emerald-700">Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5 text-slate-500" />
                            Copy Notes
                          </>
                        )}
                      </button>

                      {consultation?.input_text && consultation.input_text !== inputText && (
                        <button
                          type="button"
                          onClick={handleRestoreOriginal}
                          title="Restore original consultation input"
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-200 shadow-2xs transition-all"
                        >
                          <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
                          Restore Original
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={handleClearScratchpad}
                        disabled={!inputText.trim() || actionLoading || currentStatus === "finalized"}
                        title="Clear notes"
                        className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-medium text-rose-600 hover:text-rose-700 bg-white hover:bg-rose-50 border border-slate-200 hover:border-rose-200 shadow-2xs transition-all disabled:opacity-30"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        Clear
                      </button>
                    </div>

                    {/* Live Word & Char Metrics */}
                    <div className="flex items-center gap-3 text-xs font-mono font-medium text-slate-500 bg-white dark:bg-slate-700 px-3 py-1 rounded-xl border border-slate-200 dark:border-slate-600 shadow-2xs">
                      <span>{scratchpadStats.words} words</span>
                      <span className="text-slate-300">•</span>
                      <span>{scratchpadStats.chars} chars</span>
                      <span className="text-slate-300">•</span>
                      <span className="text-slate-400">~{scratchpadStats.readingTime} read</span>
                    </div>
                  </div>

                  {/* Textarea - Expansive High-Readability Workspace */}
                  <textarea
                    className="w-full min-h-[460px] lg:min-h-[520px] p-6 text-slate-800 dark:text-slate-100 bg-transparent placeholder-slate-400 font-mono text-sm leading-relaxed resize-y outline-none"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={(e) => {
                      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                        e.preventDefault();
                        if (!actionLoading && inputText.trim() && currentStatus !== "finalized") {
                          handleTransition("draft");
                        }
                      }
                      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
                        e.preventDefault();
                        toast.success("Doctor notes draft auto-saved");
                      }
                    }}
                    disabled={
                      actionLoading || 
                      currentStatus === "processing" || 
                      currentStatus === "finalized"
                    }
                    placeholder={
                      currentStatus === "recording" 
                        ? "Recording in progress... (type manual observations, clinical impressions, or physical exam findings here)" 
                        : "Type free-form notes during the consultation, or click any clinical template or section above...\n\nShortcuts: Press Ctrl+Enter to trigger AI Clinical Synthesis, or Ctrl+S to save."
                    }
                  />

                  {/* Textarea Footer / Status Bar */}
                  <div className="bg-slate-50/90 dark:bg-slate-800/80 border-t border-slate-200/80 dark:border-slate-800 px-5 py-3.5 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
                    <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400 font-medium">
                      <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                      <span className="text-xs">
                        Synchronized with Differential Diagnosis Engine &amp; Clinical Knowledge Graph
                      </span>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="text-[11px] text-slate-400 hidden sm:inline">
                        Press <kbd className="px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 font-mono text-[10px] font-bold">Ctrl+Enter</kbd>
                      </span>
                      <Button 
                        variant="primary" 
                        onClick={() => handleTransition("draft")}
                        disabled={actionLoading || !inputText.trim() || currentStatus === "finalized"}
                        isLoading={actionLoading}
                        className="h-10 px-6 text-xs font-bold shadow-md bg-gradient-to-r from-teal-600 via-indigo-600 to-indigo-700 text-white hover:brightness-110 rounded-xl flex items-center gap-2"
                      >
                        <Sparkles className="w-4 h-4 text-teal-200" />
                        Analyze Notes &amp; Formulate SOAP Note
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Collapsible Real-Time Differential Diagnosis Evaluation Drawer */}
                <div className="rounded-2xl border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 sm:p-5 shadow-2xs space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
                    <button
                      type="button"
                      onClick={() => setIsScratchpadDdxOpen(prev => !prev)}
                      className="flex items-center gap-3 text-left group"
                    >
                      <div className="w-9 h-9 rounded-xl bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-800 flex items-center justify-center text-amber-600 shadow-2xs shrink-0">
                        <Zap className="w-4 h-4 text-amber-500 fill-amber-500" />
                      </div>
                      <div>
                        <h4 className="text-xs font-black uppercase tracking-wider text-slate-800 dark:text-white flex items-center gap-2 font-heading">
                          Live Differential Diagnosis
                          <span className="text-[9px] bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 px-2 py-0.5 rounded-full font-bold">
                            ⚡ Real-Time Note Sync
                          </span>
                        </h4>
                        <p className="text-[11px] text-slate-500 font-medium">
                          Continuous probability scoring &amp; literature benchmark synthesis from your notes.
                        </p>
                      </div>
                    </button>

                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        type="button"
                        onClick={() => setActiveTab("intelligence")}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-indigo-700 hover:text-indigo-900 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200/80 shadow-2xs transition-colors"
                      >
                        <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                        <span>Clinical Intelligence Tab →</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setIsScratchpadDdxOpen(prev => !prev)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 border border-slate-200 shadow-2xs transition-colors"
                      >
                        <span>{isScratchpadDdxOpen ? "Hide Inline" : "View Inline"}</span>
                        {isScratchpadDdxOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>

                  {isScratchpadDdxOpen && consultation && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="pt-2"
                    >
                      <DifferentialDiagnosis 
                        consultationId={consultation.id} 
                        trigger={consultation.findings?.length || consultation.status}
                        initialQuery={inputText || consultation.input_text}
                      />
                    </motion.div>
                  )}
                </div>
              </Tabs.Content>

              {/* TAB 5: Clinical Evidence & Citation Verification */}
              <Tabs.Content value="evidence" className="space-y-6 outline-none">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
                  {/* Left: Literature Guideline RAG Assistant */}
                  <div className="rounded-3xl border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xs overflow-hidden min-h-[560px] flex flex-col">
                    <div className="p-4 border-b border-slate-100 dark:border-slate-800 bg-teal-50/60 dark:bg-teal-950/40 flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <Sparkles className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                        <div>
                          <h4 className="text-sm font-bold text-slate-900 dark:text-white m-0">Medical Literature Assistant</h4>
                          <p className="text-[10px] text-slate-500 font-medium">Approved medical trials, clinical guidelines, and drug data</p>
                        </div>
                      </div>
                    </div>
                    <div className="flex-1">
                      <RAGAssistant />
                    </div>
                  </div>

                  {/* Right: Cryptographic Citation Verifier */}
                  <div className="rounded-3xl border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xs overflow-hidden min-h-[560px] flex flex-col">
                    <div className="p-4 border-b border-slate-100 dark:border-slate-800 bg-purple-50/60 dark:bg-purple-950/40 flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <ShieldCheck className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                        <div>
                          <h4 className="text-sm font-bold text-slate-900 dark:text-white m-0">Citation &amp; Claim Verifier</h4>
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

          {/* ── Docked Executive Action Dock at bottom of Left Pane ───────────────────── */}
          <div className="shrink-0 bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border-t border-slate-200/90 dark:border-slate-800 px-4 sm:px-6 py-2.5 flex items-center justify-between gap-4 z-10 shadow-[0_-4px_16px_rgba(0,0,0,0.03)]">
            <div className="flex items-center gap-2.5 text-xs text-slate-600 dark:text-slate-400 font-medium">
              <span className={`w-2 h-2 rounded-full ${
                currentStatus === "recording" ? "bg-rose-500 animate-ping" :
                currentStatus === "finalized" ? "bg-emerald-500" :
                currentStatus === "processing" ? "bg-purple-500 animate-pulse" :
                "bg-teal-500"
              }`} />
              <span className="font-bold text-slate-900 dark:text-white uppercase tracking-wider text-[11px]">
                {currentStatus.replace('_', ' ')}
              </span>
              <span className="text-slate-300 dark:text-slate-700 hidden sm:inline">•</span>
              <span className="text-slate-500 dark:text-slate-400 hidden sm:inline text-[11px]">
                {currentStatus === "recording" ? `Ambient audio recording in progress (${formatElapsed(audio.elapsedMs)})` :
                 currentStatus === "draft" ? "SOAP note drafted · Ready for review" :
                 currentStatus === "under_review" ? "Clinician verification in progress" :
                 currentStatus === "analysis_ready" ? "Verification complete · Ready for signature" :
                 currentStatus === "finalized" ? "Signed and locked by attending physician" :
                 "Ready for clinical recording"}
              </span>
            </div>

            <div className="flex items-center gap-2">
              {renderWorkflowActions(true)}
            </div>
          </div>
        </div>
        
        {/* ── Resizable Split Divider ──────────────────────────────────────────────── */}
        {isSplitPane && paneMode === "split" && (
          <div 
            className="w-2 bg-slate-200/80 dark:bg-slate-800 hover:bg-indigo-400/30 flex flex-col items-center justify-center cursor-col-resize transition-colors border-l border-r border-slate-300/80 dark:border-slate-700/80 z-10 shrink-0 group/divider relative"
            onMouseDown={startDragging}
            title="Drag to resize split panes"
          >
            <GripVertical className="w-3.5 h-3.5 text-slate-400 group-hover/divider:text-indigo-600 transition-colors" />
          </div>
        )}

        {/* ── Right Pane (Extended SOAP+ Clinical Note Editor) ────────────────────── */}
        {isSplitPane && paneMode !== "full-cockpit" && (
          <div 
            className={`shrink-0 bg-white dark:bg-slate-900 h-full flex flex-col border-l border-slate-200/90 dark:border-slate-800 shadow-[-8px_0_24px_rgba(0,0,0,0.03)] relative z-10 overflow-hidden ${
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
          <div className="fixed inset-0 z-50 bg-slate-950/50 backdrop-blur-xs flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 15 }}
              className="w-full max-w-2xl max-h-[85vh] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl overflow-hidden flex flex-col"
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
          <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="w-full max-w-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-7 shadow-2xl relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-teal-500 via-indigo-600 to-indigo-700" />
              
              <div className="flex items-start gap-4 mb-5">
                <div className="p-3 bg-teal-50 dark:bg-teal-950/60 rounded-2xl text-teal-600 dark:text-teal-400 shrink-0 border border-teal-100 dark:border-teal-800/80">
                  <FileText className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-xl font-black font-heading text-slate-900 dark:text-white m-0 tracking-tight">
                    Informed Consent Required
                  </h3>
                  <p className="text-slate-500 dark:text-slate-400 mt-1 text-xs leading-relaxed">
                    In compliance with clinical AI governance and healthcare privacy regulations, please verify that the patient or surrogate has provided explicit consent for real-time audio capture and AI synthesis.
                  </p>
                </div>
              </div>
              
              <form onSubmit={handleGrantConsent}>
                <div className="space-y-4 mb-6">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5">
                      Actor / Consenting Party Name
                    </label>
                    <input 
                      type="text" 
                      className="w-full bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-xl p-3 text-sm text-slate-900 dark:text-white focus:bg-white focus:ring-2 focus:ring-teal-500 outline-none transition-all shadow-inner" 
                      value={consentActor} 
                      onChange={(e) => setConsentActor(e.target.value)} 
                      required 
                      placeholder="e.g. Patient Name or Legal Guardian" 
                      disabled={actionLoading} 
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5">
                      Relationship to Patient
                    </label>
                    <select 
                      className="w-full bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-xl p-3 text-sm text-slate-900 dark:text-white focus:bg-white focus:ring-2 focus:ring-teal-500 outline-none transition-all shadow-inner" 
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

                <div className="flex flex-wrap items-center justify-end gap-2.5 border-t border-slate-100 dark:border-slate-800 pt-4">
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
                      toast.info("Switched to Manual Doctor Notes. No audio recording or consent required.");
                    }} 
                    disabled={actionLoading}
                    className="text-xs font-semibold text-teal-700 dark:text-teal-400 hover:bg-teal-50 dark:hover:bg-teal-950/40"
                  >
                    ✍️ Use Manual Notes Instead
                  </Button>
                  <Button 
                    type="submit" 
                    variant="primary" 
                    disabled={actionLoading} 
                    isLoading={actionLoading}
                    className="bg-indigo-600 hover:bg-indigo-700 text-xs font-bold px-5"
                  >
                    Grant &amp; Record Consent
                  </Button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ── Tier 3: Safety & Regulatory Compliance Footer ───────────────────────────── */}
      <footer
        role="alert"
        aria-label="Placeholder response — not a clinical result"
        className="px-4 sm:px-6 py-1.5 bg-slate-50 border-t border-slate-200/90 shrink-0 text-center flex items-center justify-between text-[10px] text-slate-500 font-mono"
      >
        <span className="font-bold text-slate-600">{PLACEHOLDER_LABEL}</span>
        <span className="font-bold text-slate-700 uppercase tracking-wider mx-auto sm:mx-0">
          REFERENCE INFORMATION ONLY · CLINICIAN VERIFICATION &amp; OVERSIGHT REQUIRED
        </span>
        <span className="hidden sm:inline text-teal-700 font-bold">ISO 13485 / IEC 62304 Compliant</span>
      </footer>
    </div>
  );
}
