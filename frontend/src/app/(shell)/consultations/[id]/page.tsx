/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * DocAssistIQ — Consultation Detail View (Phase 21).
 *
 * Implements the Consultation Lifecycle State Machine & Informed Consent enforcement.
 */

"use client";

import { useCallback, useEffect, useState, useRef, useMemo } from "react";
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
  AlertTriangle
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
  PLACEHOLDER_LABEL,
} from "@/lib/api";
import ClinicalNoteEditor from "@/components/clinical/ClinicalNoteEditor";
import DifferentialDiagnosis from "@/components/clinical/DifferentialDiagnosis";
import LiveTranscriptionPanel from "@/components/clinical/LiveTranscriptionPanel";
import TranscriptEditorPanel from "@/components/clinical/TranscriptEditorPanel";
import AuditTimeline from "@/components/clinical/AuditTimeline";
import { SimilarCasesPanel } from "@/components/clinical/SimilarCasesPanel";
import InlineAIChat from "@/components/clinical/InlineAIChat";

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

export default function ConsultationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const id = Array.isArray(params.id) ? params.id[0] : params.id;
  
  const [consultation, setConsultation] = useState<ConsultationResponse | null>(null);
  const [consent, setConsent] = useState<ConsentRecordResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [inputText, setInputText] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [copiedScratchpad, setCopiedScratchpad] = useState(false);
  const [copiedId, setCopiedId] = useState(false);
  const [isScratchpadDdxOpen, setIsScratchpadDdxOpen] = useState(false);

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
      <div className="p-6" data-testid="dashboard-skeleton">
        <Skeleton className="h-[20px] w-full mb-2" />
        <Skeleton className="h-[20px] w-3/4 mb-4" />
        <Skeleton className="h-[20px] w-full mb-2" />
        <Skeleton className="h-[20px] w-5/6" />
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
          className="px-5 py-2.5 rounded-xl bg-slate-900 text-white font-medium text-sm hover:bg-slate-800 transition-colors shadow-sm"
        >
          Back to Consultations
        </Link>
      </div>
    );
  }

  const currentStatus = consultation.status;
  const isSplitPane = ["draft", "under_review", "analysis_ready", "finalized", "amended"].includes(currentStatus);

  return (
    <div className="flex flex-col h-[calc(100vh-72px)] bg-[var(--surface-base)] overflow-hidden relative">
      
      {/* Clinical Governance & System Integrity Bar */}
      <div 
        role="alert" 
        aria-label="Simulation Notice — Not a clinical result" 
        className="px-6 py-1 bg-slate-900 border-b border-slate-800 text-xs text-slate-300 flex items-center justify-between shrink-0"
      >
        <div className="flex items-center gap-2">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400" />
          <span className="font-mono text-[10px] uppercase tracking-wider text-slate-200 font-bold">
            {PLACEHOLDER_LABEL}
          </span>
          <span className="text-[10px] text-slate-400">• Clinician Review &amp; Verification Required</span>
        </div>
        <span className="text-[10px] text-slate-400 hidden sm:inline font-mono">
          ISO 13485 / Local Edge Compute Mode
        </span>
      </div>
      
      {/* Sticky Premium Clinical Command Header */}
      <header className="px-4 sm:px-6 py-3.5 bg-white/95 backdrop-blur-xl border-b border-slate-200/90 shrink-0 z-30 flex flex-wrap items-center justify-between gap-4 shadow-2xs sticky top-0">
        <div className="flex items-center gap-3">
          <Link
            href="/consultations"
            className="p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors border border-transparent hover:border-slate-200"
            title="Back to consultations"
          >
            <ChevronLeft className="w-5 h-5" />
          </Link>

          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-lg font-black font-heading text-slate-900 tracking-tight flex items-center gap-2">
                Consultation Workspace
              </h2>
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] uppercase tracking-wider font-extrabold flex items-center gap-1.5 shadow-2xs ${
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
                {currentStatus.replace('_', ' ')}
              </span>
            </div>

            <div className="flex items-center gap-2 mt-0.5">
              <button
                type="button"
                onClick={handleCopyId}
                className="group flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 font-mono transition-colors"
                title="Click to copy consultation ID"
              >
                <span>ID: {consultation.id}</span>
                {copiedId ? (
                  <Check className="w-3 h-3 text-emerald-600" />
                ) : (
                  <Copy className="w-3 h-3 opacity-60 group-hover:opacity-100" />
                )}
              </button>
            </div>
          </div>
        </div>
        
        {/* Executive Workflow Action Console */}
        <div className="flex items-center gap-3">
          {currentStatus === "created" && (
            <button 
              type="button"
              onClick={() => {
                if (!consent) setShowConsentForm(true);
                else handleTransition("recording");
              }}
              disabled={actionLoading}
              className="px-4 py-2 rounded-xl text-xs font-bold text-white transition-all bg-gradient-to-r from-teal-600 via-indigo-600 to-indigo-700 hover:from-teal-500 hover:to-indigo-600 shadow-md shadow-indigo-500/20 active:scale-95 flex items-center gap-2"
            >
              <Mic className="w-4 h-4 text-teal-200 animate-pulse" />
              <span>Start Recording</span>
            </button>
          )}

          {currentStatus === "recording" && (
            <div className="flex items-center gap-2">
              <div className="px-3 py-1.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 font-mono text-xs font-bold flex items-center gap-2 shadow-2xs">
                <span className="w-2 h-2 rounded-full bg-rose-600 animate-ping" />
                <span>REC {formatElapsed(audio.elapsedMs)}</span>
                
                {/* Real-time audio waveform / volume indicator */}
                <div className="flex items-center gap-0.5 ml-1.5 h-3.5" title={`Mic volume: ${audio.audioLevel}%`}>
                  <span 
                    className="w-1 bg-emerald-500 rounded-full transition-all duration-75"
                    style={{ height: `${Math.max(20, Math.min(100, audio.audioLevel * 1.2))}%` }} 
                  />
                  <span 
                    className="w-1 bg-emerald-500 rounded-full transition-all duration-75"
                    style={{ height: `${Math.max(15, Math.min(100, audio.audioLevel * 0.8))}%` }} 
                  />
                  <span 
                    className="w-1 bg-emerald-500 rounded-full transition-all duration-75"
                    style={{ height: `${Math.max(25, Math.min(100, audio.audioLevel * 1.4))}%` }} 
                  />
                </div>

                {audio.isSilent && (
                  <span className="text-[10px] text-amber-700 font-sans font-medium px-1.5 py-0.5 rounded bg-amber-100/90 border border-amber-300 animate-pulse">
                    Mic silent
                  </span>
                )}
              </div>
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
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-purple-50 border border-purple-200 text-xs font-bold text-purple-700">
              <div className="w-3.5 h-3.5 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
              <span>Processing Audio &amp; Synthesizing...</span>
            </div>
          )}

          {currentStatus === "draft" && (
            <Button 
              variant="primary" 
              onClick={() => handleTransition("under_review")} 
              disabled={actionLoading} 
              className="h-8 px-4 text-xs font-bold bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-xs flex items-center gap-1.5"
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
                className="h-8 px-3.5 text-xs font-bold bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-xs"
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
                className="h-8 px-3.5 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-xs flex items-center gap-1.5"
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
              className="h-8 px-3 text-xs font-bold rounded-xl border border-slate-200 hover:bg-slate-50"
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

          <div className="h-5 w-px bg-slate-200 mx-1 hidden sm:block" />

          {/* Quick Intake Form Link */}
          <Link
            href={`/consultations/${id}/intake`}
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-teal-800 bg-teal-50 hover:bg-teal-100 border border-teal-200/80 shadow-2xs transition-all active:scale-95"
          >
            <Sparkles className="w-3.5 h-3.5 text-teal-600" />
            <span>Intake Form</span>
          </Link>

          {/* Consent Status Badge */}
          {consent ? (
            <div className="flex items-center gap-1.5 bg-emerald-50 text-emerald-800 px-3 py-1.5 rounded-xl border border-emerald-200 shadow-2xs">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
              <span className="text-xs font-bold uppercase tracking-wide hidden md:inline">Consent Granted</span>
              {["created", "recording"].includes(currentStatus) && (
                <button 
                  type="button"
                  onClick={handleRevokeConsent} 
                  disabled={actionLoading} 
                  className="ml-1 text-[10px] underline hover:text-rose-600 text-slate-500 font-bold transition-colors"
                >
                  Revoke
                </button>
              )}
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setShowConsentForm(true)}
              className="flex items-center gap-1.5 bg-rose-50 hover:bg-rose-100 text-rose-800 px-3 py-1.5 rounded-xl border border-rose-200 shadow-2xs transition-all"
            >
              <AlertCircle className="w-3.5 h-3.5 text-rose-600 animate-pulse" />
              <span className="text-xs font-bold uppercase tracking-wide">Missing Consent</span>
            </button>
          )}
        </div>
      </header>

      {/* Phase 42: Red Flag Banner */}
      {representation?.safety_decision && representation.safety_decision.decision !== "ALLOW" && (
        <div className="bg-red-50 border-b-4 border-red-600 p-4 shrink-0 shadow-sm animate-pulse-slow z-50 sticky top-0">
          <div className="flex items-start max-w-7xl mx-auto">
            <div className="flex-shrink-0 mt-0.5">
              <AlertOctagon className="w-6 h-6 text-red-600" aria-hidden="true" />
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
                    <span className="mt-0.5">
                      {flag.severity === 'CRITICAL' ? (
                        <AlertOctagon className="w-4 h-4 text-red-600 shrink-0" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                      )}
                    </span>
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

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden relative w-full">
        
        {/* Left Pane (Timeline / Transcript) */}
        <div className="flex-1 flex flex-col h-full bg-slate-50/50 relative overflow-hidden">
          {/* Consent Form */}
          <div className="px-4 sm:px-6 lg:px-8 pt-4 shrink-0">
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
                        Grant &amp; Record Consent
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

          <Tabs.Root defaultValue="ai-assistant" className="flex flex-1 flex-col h-full overflow-hidden">
            <div className="px-4 sm:px-6 lg:px-8 py-2.5 border-b border-slate-200/80 bg-white/90 backdrop-blur-md shrink-0 flex flex-wrap items-center justify-between gap-3">
              <Tabs.List className="flex flex-wrap items-center gap-1.5 p-1 bg-slate-100/90 rounded-2xl border border-slate-200/80">
                <Tabs.Trigger 
                  value="ai-assistant" 
                  className="px-4 py-2 text-xs font-bold rounded-xl transition-all flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs text-slate-500 hover:text-slate-800 outline-none"
                >
                  <Activity className="w-3.5 h-3.5 text-teal-600" />
                  <span>Live AI Cockpit</span>
                  {currentStatus === "recording" && (
                    <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                  )}
                </Tabs.Trigger>
                <Tabs.Trigger 
                  value="intelligence" 
                  className="px-4 py-2 text-xs font-bold rounded-xl transition-all flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs text-slate-500 hover:text-slate-800 outline-none"
                >
                  <Zap className="w-3.5 h-3.5 text-amber-500" />
                  <span>Clinical Intelligence &amp; DDx</span>
                </Tabs.Trigger>
                <Tabs.Trigger 
                  value="transcript" 
                  className="px-4 py-2 text-xs font-bold rounded-xl transition-all flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs text-slate-500 hover:text-slate-800 outline-none"
                >
                  <Radio className="w-3.5 h-3.5 text-indigo-500" />
                  <span>Transcript &amp; Audit</span>
                </Tabs.Trigger>
                <Tabs.Trigger 
                  value="scratchpad" 
                  className="px-4 py-2 text-xs font-bold rounded-xl transition-all flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs text-slate-500 hover:text-slate-800 outline-none"
                >
                  <FileText className="w-3.5 h-3.5 text-slate-600" />
                  <span>Doctor Notes &amp; Scratchpad</span>
                  {inputText.trim() && (
                    <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
                  )}
                </Tabs.Trigger>
              </Tabs.List>

              <div className="hidden lg:flex items-center gap-2.5 text-xs text-slate-400 font-mono">
                <span className="bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200 text-slate-600 font-semibold">
                  ENC #{consultation.id.slice(0, 8)}
                </span>
                <span>•</span>
                <span className="uppercase text-[10px] tracking-wider font-extrabold text-slate-500">
                  Phase: {currentStatus}
                </span>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 pb-32">
              
              <Tabs.Content value="ai-assistant" className="space-y-6 outline-none">
                {!isSplitPane ? (
                  /* Spacious 2-Column Clinical Cockpit for wide displays */
                  <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
                    {/* Left Column: Recording, Transcript, Extracted Findings, Chat */}
                    <div className="xl:col-span-5 space-y-6">
                      {consultation.input_text && (
                        <div className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-2xs">
                          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                            Clinical Scenario
                          </span>
                          <p className="text-sm text-slate-700 leading-relaxed font-medium">
                            {consultation.input_text}
                          </p>
                        </div>
                      )}

                      <LiveTranscriptionPanel
                        consultationId={consultation.id}
                        isConsultationRecording={currentStatus === "recording"}
                        onStartConsultationRecording={() => {
                          if (!consent) setShowConsentForm(true);
                          else handleTransition("recording");
                        }}
                        onStopConsultationRecording={() => handleTransition("processing")}
                        onTranscriptReady={(text, segments) => {
                          // Handle transcript ready — pass to note generation
                        }}
                      />

                      {consultation?.findings && consultation.findings.length > 0 && (
                        <motion.div 
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="p-5 bg-white border border-indigo-200 shadow-2xs rounded-2xl relative overflow-hidden"
                        >
                          <div className="absolute top-0 left-0 w-1 h-full bg-indigo-600" />
                          <div className="flex justify-between items-center mb-4">
                            <h3 className="text-sm font-bold tracking-wide text-indigo-900 uppercase flex items-center gap-2 m-0 font-heading">
                              <Activity className="w-4 h-4 text-indigo-600" />
                              Extracted Clinical Findings
                            </h3>
                            <span className="text-[0.65rem] font-bold px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-full uppercase tracking-widest border border-indigo-200 flex items-center gap-1.5">
                              <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-pulse" />
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
                                className={`p-3 rounded-xl border flex flex-col gap-1.5 min-w-[160px] shadow-2xs transition-colors ${
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
                                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 10 4 15 9 20"></polyline><path d="M20 4v7a4 4 0 0 1-4 4H4"></path></svg>
                                    {finding.canonical_concept}
                                    {finding.mapping_source && <span className="opacity-60">({finding.mapping_source})</span>}
                                  </div>
                                )}
                                
                                <div className="flex flex-wrap gap-1.5 mt-1">
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
                                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
                                      CONFIRMED
                                    </span>
                                  )}
                                  {finding.status === "rejected" && (
                                    <span className="text-[0.65rem] px-1.5 py-0.5 bg-rose-100 text-rose-700 rounded font-bold flex items-center gap-1">
                                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                                      REJECTED
                                    </span>
                                  )}
                                </div>
                                
                                {finding.status === "pending" && (
                                  <div className="flex gap-1.5 mt-2 pt-2 border-t border-slate-100">
                                    <button type="button" className="flex-1 py-1 px-2 text-[0.65rem] font-bold rounded bg-slate-100 hover:bg-rose-50 hover:text-rose-600 transition-colors border border-slate-200" onClick={() => handleReviewFinding(finding.id, "reject")}>Reject</button>
                                    <button type="button" className="flex-1 py-1 px-2 text-[0.65rem] font-bold rounded bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-colors border border-indigo-200" onClick={() => handleReviewFinding(finding.id, "confirm")}>Confirm</button>
                                  </div>
                                )}
                              </motion.div>
                            ))}
                          </div>
                        </motion.div>
                      )}

                      <InlineAIChat consultationId={consultation.id} />
                    </div>

                    {/* Right Column: Full-Width AI Differential Diagnosis & Similar Cases */}
                    <div className="xl:col-span-7 space-y-6">
                      <DifferentialDiagnosis 
                        consultationId={consultation.id} 
                        trigger={consultation.findings?.length || consultation.status}
                        initialQuery={consultation.input_text || inputText}
                      />

                      <SimilarCasesPanel consultationId={consultation.id} />
                    </div>
                  </div>
                ) : (
                  /* Split-Pane Single-Column Layout when Clinical Note Editor is active */
                  <div className="space-y-6">
                    {consultation.input_text && (
                      <div className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-2xs">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                          Clinical Scenario
                        </span>
                        <p className="text-sm text-slate-700 leading-relaxed font-medium">
                          {consultation.input_text}
                        </p>
                      </div>
                    )}

                    <LiveTranscriptionPanel
                      consultationId={consultation.id}
                      isConsultationRecording={currentStatus === "recording"}
                      onStartConsultationRecording={() => {
                        if (!consent) setShowConsentForm(true);
                        else handleTransition("recording");
                      }}
                      onStopConsultationRecording={() => handleTransition("processing")}
                      onTranscriptReady={(text, segments) => {
                        // Handle transcript ready — pass to note generation
                      }}
                    />

                    <InlineAIChat consultationId={consultation.id} />

                    {consultation?.findings && consultation.findings.length > 0 && (
                      <motion.div 
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-5 bg-white border border-indigo-200 shadow-2xs rounded-2xl relative overflow-hidden"
                      >
                        <div className="absolute top-0 left-0 w-1 h-full bg-indigo-600" />
                        <div className="flex justify-between items-center mb-4">
                          <h3 className="text-sm font-bold tracking-wide text-indigo-900 uppercase flex items-center gap-2 m-0 font-heading">
                            <Activity className="w-4 h-4 text-indigo-600" />
                            Extracted Clinical Findings
                          </h3>
                          <span className="text-[0.65rem] font-bold px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-full uppercase tracking-widest border border-indigo-200 flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-pulse" />
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
                              className={`p-3 rounded-xl border flex flex-col gap-1.5 min-w-[160px] shadow-2xs transition-colors ${
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
                                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 10 4 15 9 20"></polyline><path d="M20 4v7a4 4 0 0 1-4 4H4"></path></svg>
                                  {finding.canonical_concept}
                                  {finding.mapping_source && <span className="opacity-60">({finding.mapping_source})</span>}
                                </div>
                              )}
                              
                              <div className="flex flex-wrap gap-1.5 mt-1">
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
                                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
                                    CONFIRMED
                                  </span>
                                )}
                                {finding.status === "rejected" && (
                                  <span className="text-[0.65rem] px-1.5 py-0.5 bg-rose-100 text-rose-700 rounded font-bold flex items-center gap-1">
                                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                                    REJECTED
                                  </span>
                                )}
                              </div>
                              
                              {finding.status === "pending" && (
                                <div className="flex gap-1.5 mt-2 pt-2 border-t border-slate-100">
                                  <button type="button" className="flex-1 py-1 px-2 text-[0.65rem] font-bold rounded bg-slate-100 hover:bg-rose-50 hover:text-rose-600 transition-colors border border-slate-200" onClick={() => handleReviewFinding(finding.id, "reject")}>Reject</button>
                                  <button type="button" className="flex-1 py-1 px-2 text-[0.65rem] font-bold rounded bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-colors border border-indigo-200" onClick={() => handleReviewFinding(finding.id, "confirm")}>Confirm</button>
                                </div>
                              )}
                            </motion.div>
                          ))}
                        </div>
                      </motion.div>
                    )}

                    <DifferentialDiagnosis 
                      consultationId={consultation.id} 
                      trigger={consultation.findings?.length || consultation.status}
                      initialQuery={consultation.input_text || inputText}
                    />
                    
                    <SimilarCasesPanel consultationId={consultation.id} />
                  </div>
                )}
              </Tabs.Content>

              <Tabs.Content value="intelligence" className="space-y-6 outline-none">
                {consultation && (
                  <DifferentialDiagnosis 
                    consultationId={consultation.id} 
                    trigger={consultation.findings?.length || consultation.status}
                    initialQuery={consultation.input_text || inputText}
                  />
                )}
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
                {/* Header & Quick Links */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200/80">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-teal-500/10 text-teal-700 border border-teal-500/20 flex items-center justify-center shadow-xs">
                      <FileText className="w-5 h-5 text-teal-600" />
                    </div>
                    <div>
                      <h3 className="text-base font-black tracking-tight text-slate-900 font-heading flex items-center gap-2">
                        Doctor Notes Workspace
                        <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200">
                          Live Scratchpad
                        </span>
                      </h3>
                      <p className="text-xs text-slate-500 font-medium">
                        Document free-form observations, clinical dictations, or insert hospital templates below.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <Link
                      href={`/consultations/${id}/intake`}
                      className="text-xs font-bold text-teal-700 bg-teal-50/80 hover:bg-teal-100 px-3.5 py-2 rounded-xl border border-teal-200 shadow-2xs transition-all flex items-center gap-1.5 active:scale-95"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-teal-600" />
                      Structured Intake Form
                    </Link>
                  </div>
                </div>

                {/* Clinical Template & Quick Section Insert Bar */}
                <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-2xs space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-2.5">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5 font-heading">
                      <Sparkles className="w-3.5 h-3.5 text-teal-600" />
                      1-Click Comprehensive Clinical Templates:
                    </span>
                    <span className="text-[10px] text-slate-400 font-medium">Inserts full clinical benchmark template</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {CLINICAL_TEMPLATES.map((tmpl) => (
                      <button
                        key={tmpl.id}
                        type="button"
                        onClick={() => handleInsertTemplate(tmpl.text)}
                        disabled={actionLoading || currentStatus === "finalized"}
                        className="group inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-teal-50 border border-slate-200/80 hover:border-teal-300 text-xs font-medium text-slate-700 hover:text-teal-900 shadow-2xs transition-all active:scale-95 disabled:opacity-50"
                      >
                        {tmpl.iconType === "heart" ? (
                          <HeartPulse className="w-3.5 h-3.5 text-rose-500 group-hover:scale-110 transition-transform" />
                        ) : tmpl.iconType === "temp" ? (
                          <Thermometer className="w-3.5 h-3.5 text-amber-500 group-hover:scale-110 transition-transform" />
                        ) : tmpl.iconType === "scope" ? (
                          <Stethoscope className="w-3.5 h-3.5 text-teal-600 group-hover:scale-110 transition-transform" />
                        ) : tmpl.iconType === "activity" ? (
                          <Activity className="w-3.5 h-3.5 text-blue-500 group-hover:scale-110 transition-transform" />
                        ) : (
                          <FileText className="w-3.5 h-3.5 text-indigo-500 group-hover:scale-110 transition-transform" />
                        )}
                        <span className="font-bold">{tmpl.label}</span>
                        <span className="text-[9px] font-semibold uppercase px-1.5 py-0.5 rounded-md bg-white group-hover:bg-teal-100/70 text-slate-500 group-hover:text-teal-700 border border-slate-200/60 group-hover:border-teal-200 transition-colors">
                          {tmpl.badge}
                        </span>
                      </button>
                    ))}
                  </div>

                  {/* Rapid 1-Click Clinical Section Inserters */}
                  <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mr-1 flex items-center gap-1">
                      <Plus className="w-3 h-3 text-slate-400" /> Add Section:
                    </span>
                    {SCRATCHPAD_SECTIONS.map((sec) => (
                      <button
                        key={sec.id}
                        type="button"
                        onClick={() => handleInsertSection(sec.snippet)}
                        disabled={actionLoading || currentStatus === "finalized"}
                        className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-white hover:bg-indigo-50 border border-slate-200 hover:border-indigo-300 text-slate-600 hover:text-indigo-700 shadow-2xs transition-all active:scale-95 disabled:opacity-50"
                      >
                        {sec.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Expansive Editor Canvas Card */}
                <div className="rounded-3xl border border-slate-200/90 bg-white shadow-sm overflow-hidden flex flex-col focus-within:ring-4 focus-within:ring-teal-500/10 focus-within:border-teal-500 transition-all">
                  {/* Editor Utility Toolbar */}
                  <div className="bg-slate-50/90 border-b border-slate-200/90 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={handleInsertTimestamp}
                        disabled={actionLoading || currentStatus === "finalized"}
                        title="Insert current timestamp [HH:MM]"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-200 shadow-2xs transition-all active:scale-95 disabled:opacity-40"
                      >
                        <Clock className="w-3.5 h-3.5 text-slate-500" />
                        Timestamp
                      </button>

                      <button
                        type="button"
                        onClick={handleCopyScratchpad}
                        disabled={!inputText.trim()}
                        title="Copy all doctor notes to clipboard"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-200 shadow-2xs transition-all active:scale-95 disabled:opacity-40"
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
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-200 shadow-2xs transition-all active:scale-95"
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
                        className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-medium text-rose-600 hover:text-rose-700 bg-white hover:bg-rose-50 border border-slate-200 hover:border-rose-200 shadow-2xs transition-all disabled:opacity-30 active:scale-95"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        Clear
                      </button>
                    </div>

                    {/* Live Word & Char Metrics */}
                    <div className="flex items-center gap-3 text-xs font-mono font-medium text-slate-500 bg-white px-3 py-1 rounded-xl border border-slate-200 shadow-2xs">
                      <span>{scratchpadStats.words} words</span>
                      <span className="text-slate-300">•</span>
                      <span>{scratchpadStats.chars} chars</span>
                      <span className="text-slate-300">•</span>
                      <span className="text-slate-400">~{scratchpadStats.readingTime} read</span>
                    </div>
                  </div>

                  {/* Textarea - Expansive High-Readability Workspace */}
                  <textarea
                    className="w-full min-h-[460px] lg:min-h-[520px] p-6 text-slate-800 bg-transparent placeholder-slate-400 font-mono text-sm leading-relaxed resize-y outline-none"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={(e) => {
                      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                        e.preventDefault();
                        if (!actionLoading && inputText.trim() && currentStatus !== "finalized") {
                          handleTransition("draft");
                        }
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
                        : "Type free-form notes during the consultation, or click any clinical template or section above...\n\nShortcut: Press Ctrl+Enter to trigger AI Clinical Synthesis into structured note."
                    }
                  />

                  {/* Textarea Footer / Status Bar */}
                  <div className="bg-slate-50/90 border-t border-slate-200/80 px-5 py-3.5 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
                    <div className="flex items-center gap-2 text-slate-600 font-medium">
                      <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                      <span className="text-xs">
                        Live synchronized with Differential Diagnosis Engine &amp; Clinical Knowledge Graph
                      </span>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="text-[11px] text-slate-400 hidden sm:inline">
                        Press <kbd className="px-1.5 py-0.5 rounded bg-slate-200 text-slate-700 font-mono text-[10px] font-bold">Ctrl+Enter</kbd>
                      </span>
                      <Button 
                        variant="primary" 
                        onClick={() => handleTransition("draft")}
                        disabled={actionLoading || !inputText.trim() || currentStatus === "finalized"}
                        isLoading={actionLoading}
                        className="h-10 px-6 text-xs font-bold shadow-md bg-gradient-to-r from-teal-600 via-indigo-600 to-indigo-700 text-white hover:brightness-110 active:scale-95 rounded-xl flex items-center gap-2"
                      >
                        <Sparkles className="w-4 h-4 text-teal-200" />
                        Analyze Notes &amp; Formulate SOAP Note
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Collapsible Real-Time Differential Diagnosis Evaluation Drawer */}
                <div className="rounded-3xl border border-slate-200/90 bg-white p-5 shadow-2xs space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                    <button
                      type="button"
                      onClick={() => setIsScratchpadDdxOpen(prev => !prev)}
                      className="flex items-center gap-3 text-left group"
                    >
                      <div className="w-10 h-10 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600 group-hover:scale-105 transition-transform shadow-2xs">
                        <Zap className="w-5 h-5 text-amber-500 fill-amber-500 animate-pulse" />
                      </div>
                      <div>
                        <h4 className="text-sm font-black uppercase tracking-wider text-slate-800 flex items-center gap-2 font-heading">
                          Live Differential Diagnosis
                          <span className="text-[10px] bg-indigo-50 text-indigo-700 border border-indigo-200 px-2.5 py-0.5 rounded-full font-bold">
                            ⚡ Real-Time Scratchpad Evaluation
                          </span>
                        </h4>
                        <p className="text-xs text-slate-500 font-medium">
                          Continuous probability scoring &amp; literature benchmark synthesis from your notes.
                        </p>
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => setIsScratchpadDdxOpen(prev => !prev)}
                      className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 border border-slate-200 shadow-2xs transition-all active:scale-95 shrink-0"
                    >
                      <span>{isScratchpadDdxOpen ? "Collapse Diagnostic Engine" : "Expand Diagnostic Engine"}</span>
                      {isScratchpadDdxOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
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
            </div>
          </Tabs.Root>

          {/* Floating Action Bar (Phase 5) */}
          <motion.div 
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-slate-900/95 text-white backdrop-blur-2xl border border-slate-700/80 shadow-[0_20px_60px_rgba(0,0,0,0.35)] rounded-full px-5 py-2.5 flex items-center gap-3 ring-1 ring-white/10"
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
                <button 
                  type="button"
                  onClick={() => handleTransition("created")}
                  disabled={actionLoading}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full font-semibold text-xs text-rose-300 hover:text-white bg-rose-500/20 hover:bg-rose-600/40 border border-rose-500/30 transition-all active:scale-95 disabled:opacity-50"
                >
                  <Square className="w-3.5 h-3.5" /> Stop
                </button>
                <div className="px-3 font-mono text-xs font-bold text-rose-400 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                  {formatElapsed(audio.elapsedMs)}
                </div>
              </>
            )}

            {currentStatus === "processing" && (
              <div className="px-6 flex items-center gap-3 text-sm font-bold text-teal-400">
                <span className="w-4 h-4 rounded-full border-2 border-teal-400 border-t-transparent animate-spin" />
                AI is processing audio &amp; notes...
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
                <button 
                  type="button"
                  onClick={() => handleTransition("draft")} 
                  disabled={actionLoading} 
                  className="px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800 rounded-full border border-slate-700/80 transition-colors"
                >
                  Back to Draft
                </button>
              </>
            )}

            {currentStatus === "analysis_ready" && (
              <>
                <Button variant="primary" onClick={() => handleTransition("finalized")} disabled={actionLoading} className="rounded-full shadow-lg px-6 gap-2">
                  <CheckCircle className="w-4 h-4" /> Sign Off &amp; Finalize
                </Button>
                <button 
                  type="button"
                  onClick={() => handleTransition("under_review")} 
                  disabled={actionLoading} 
                  className="px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800 rounded-full border border-slate-700/80 transition-colors"
                >
                  Re-review
                </button>
              </>
            )}

            {currentStatus === "finalized" && (
              <button 
                type="button"
                onClick={() => handleTransition("amended")} 
                disabled={actionLoading} 
                className="px-5 py-2 text-xs font-semibold text-slate-200 hover:text-white bg-slate-800/80 hover:bg-slate-700 border border-slate-600 rounded-full transition-colors"
              >
                Amend Finalized Record
              </button>
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

      {/* Safety Footer */}
      <footer className="px-6 py-2.5 bg-slate-50 border-t border-slate-200/80 shrink-0 text-center">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
          REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED
        </span>
      </footer>
    </div>
  );
}
