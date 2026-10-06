/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import React, { useEffect, useState, useCallback, useRef, useMemo } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useClinicalNote, useUpdateClinicalNote, noteKeys } from "@/hooks/useConsultations";
import {
  NoteSection,
  ClinicalNoteResponse,
  NotePatientEncounterHeader,
  NoteTimelineMilestone,
  NoteInvestigationItem,
  NoteDifferentialCandidate,
  orderInvestigationInNote,
  recordInvestigationResultInNote,
  performDifferentialActionInNote,
  rerunDifferentialInNote,
  generateConsultationNote,
  getStoredToken,
} from "@/lib/api";
import { useToast } from "@/components/shell/ToastProvider";
import { motion, AnimatePresence } from "framer-motion";
import FeedbackButtons from "./FeedbackButtons";
import {
  saveOfflineNoteDraft,
  getOfflineNoteDraft,
  clearOfflineNoteDraft,
  registerNetworkReconnectionSync,
} from "@/lib/offlineSync";

import {
  Copy,
  ChevronsUpDown,
  Download,
  Share2,
  Sparkles,
  FileSpreadsheet,
  Check,
  MessageSquare,
  Clock,
  Search,
  Folder,
  Activity,
  Pill,
  AlertTriangle,
  Users,
  Globe,
  HeartPulse,
  Stethoscope,
  FlaskConical,
  Target,
  CheckCircle2,
  ClipboardList,
  Calendar,
  ShieldAlert,
  Plus,
  RefreshCw,
  X,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Building2,
  User,
  Bed,
  CheckSquare,
  XCircle,
  ArrowUpRight,
  FileText,
} from "lucide-react";

// ─── Extended SOAP+ Category Structure ────────────────────────────────────────
const SOAP_GROUPS = [
  {
    groupId: "subjective",
    groupLabel: "Subjective",
    color: "blue",
    icon: MessageSquare,
    sections: [
      { id: "chief_complaint", label: "Chief Complaint", icon: MessageSquare, required: true },
      { id: "hpi", label: "History of Present Illness", icon: Clock, required: true },
      { id: "review_of_systems", label: "Review of Systems", icon: Search, required: false },
      { id: "past_medical_history", label: "Past Medical History", icon: Folder, required: false },
      { id: "surgical_history", label: "Past Surgical History", icon: Activity, required: false },
      { id: "medications", label: "Current Medications", icon: Pill, required: false },
      { id: "allergies", label: "Allergies & Adverse Reactions", icon: AlertTriangle, required: false },
      { id: "family_history", label: "Family History", icon: Users, required: false },
      { id: "social_history", label: "Social, Travel & Epidemiological History", icon: Globe, required: false },
    ],
  },
  {
    groupId: "objective",
    groupLabel: "Objective",
    color: "emerald",
    icon: Stethoscope,
    sections: [
      { id: "vitals", label: "Vital Signs", icon: HeartPulse, required: true },
      { id: "physical_examination", label: "Physical Examination", icon: Stethoscope, required: true },
      { id: "investigations", label: "Investigations Summary", icon: FlaskConical, required: false, dropZone: true },
    ],
  },
  {
    groupId: "assessment_plan",
    groupLabel: "Assessment & Differential",
    color: "purple",
    icon: ClipboardList,
    sections: [
      { id: "assessment", label: "Assessment (Working Clinical Synthesis)", icon: CheckCircle2, required: true, clinicianFill: true },
      { id: "differential_diagnosis", label: "Differential Diagnosis (Clinical Synthesis)", icon: Target, required: false },
      { id: "plan", label: "Management Plan (Medications, Monitoring, Care)", icon: ClipboardList, required: true, clinicianFill: true, dropZone: true },
    ],
  },
  {
    groupId: "course_disposition",
    groupLabel: "Hospital Course & Disposition",
    color: "amber",
    icon: ShieldAlert,
    sections: [
      { id: "clinical_response", label: "Response to Treatment & Hospital Course", icon: Activity, required: false },
      { id: "disposition", label: "Disposition & Condition at Disposition", icon: Building2, required: false },
      { id: "follow_up_plan", label: "Follow-Up & Required Review", icon: Calendar, required: false },
      { id: "safety_net", label: "Safety Net & Return Precautions", icon: ShieldAlert, required: false },
      { id: "authentication", label: "Clinician Authentication & Sign-Off", icon: CheckSquare, required: false },
    ],
  },
];

const GROUP_COLORS: Record<string, { border: string; bg: string; text: string; badge: string; header: string }> = {
  blue: {
    border: "border-blue-200",
    bg: "bg-blue-50/30",
    text: "text-blue-800",
    badge: "bg-blue-100 text-blue-700 border-blue-200",
    header: "from-blue-50 to-transparent border-blue-100",
  },
  emerald: {
    border: "border-emerald-200",
    bg: "bg-emerald-50/20",
    text: "text-emerald-800",
    badge: "bg-emerald-100 text-emerald-700 border-emerald-200",
    header: "from-emerald-50 to-transparent border-emerald-100",
  },
  purple: {
    border: "border-purple-200",
    bg: "bg-purple-50/20",
    text: "text-purple-800",
    badge: "bg-purple-100 text-purple-700 border-purple-200",
    header: "from-purple-50 to-transparent border-purple-100",
  },
  amber: {
    border: "border-amber-200",
    bg: "bg-amber-50/20",
    text: "text-amber-800",
    badge: "bg-amber-100 text-amber-700 border-amber-200",
    header: "from-amber-50 to-transparent border-amber-100",
  },
};

// ─── Vitals structured display ─────────────────────────────────────────────────
function parseVitals(text: any): Record<string, string> {
  const vitals: Record<string, string> = {};
  if (!text) return vitals;
  const safeText = typeof text === "string" ? text : String(text);
  const parts = safeText.split("|").map((p: string) => p.trim());
  for (const part of parts) {
    const colonIdx = part.indexOf(":");
    if (colonIdx > 0) {
      const k = part.slice(0, colonIdx).trim();
      const v = part.slice(colonIdx + 1).trim();
      if (k && v) vitals[k] = v;
    }
  }
  return vitals;
}

const VITAL_ICONS: Record<string, string> = {
  BP: "BP",
  HR: "HR",
  RR: "RR",
  Temp: "T",
  SpO2: "O2",
  Weight: "Wt",
  Height: "Ht",
  BMI: "BMI",
  GCS: "GCS",
};

const VITAL_UNITS: Record<string, string> = {
  BP: "mmHg",
  HR: "bpm",
  RR: "/min",
  Temp: "°C",
  SpO2: "%",
  Weight: "kg",
  Height: "cm",
  BMI: "kg/m²",
  GCS: "/15",
};

function isAbnormalVital(key: string, val: string): boolean {
  if (!val || val === "Not documented") return false;
  const num = parseFloat(val.replace(/[^\d.]/g, ""));
  if (isNaN(num)) return false;
  if (key === "SpO2" && num < 95) return true;
  if (key === "HR" && (num > 100 || num < 50)) return true;
  if (key === "RR" && (num > 20 || num < 10)) return true;
  if (key === "Temp" && (num >= 38.0 || num < 35.5)) return true;
  if (key === "BP") {
    const parts = val.split("/");
    if (parts.length === 2) {
      const s = parseInt(parts[0].trim());
      const d = parseInt(parts[1].trim());
      if ((!isNaN(s) && (s >= 140 || s < 90)) || (!isNaN(d) && (d >= 90 || d < 60))) return true;
    }
  }
  return false;
}

const SECTION_BOILERPLATES: Record<string, { label: string; text: string }> = {
  review_of_systems: {
    label: "+ Standard Negative ROS",
    text: "Constitutional: Negative for unintentional weight loss or rigors.\nEyes: Negative for acute vision changes, blurriness, or retro-orbital pain.\nENT: Negative for sore throat, epistaxis, or rhinorrhea.\nCardiovascular: Negative for palpitations, orthopnea, or ankle edema.\nRespiratory: Negative for cough, hemoptysis, or wheeze.\nGastrointestinal: Negative for hematemesis, melena, or severe diarrhea.\nGenitourinary: Negative for dysuria, frequency, or gross hematuria.\nMusculoskeletal: Negative for joint swelling or warmth.\nNeurological: Negative for witnessed seizures, focal limb weakness, or sensory loss.",
  },
  physical_examination: {
    label: "+ Normal Physical Exam",
    text: "General: Alert, oriented, in no acute cardiorespiratory distress.\nHEENT: Normocephalic, atraumatic. Pupils equal and reactive to light. Oropharynx clear.\nCardiovascular: Normal S1 and S2, regular rhythm, no murmurs.\nRespiratory: Lungs clear to auscultation bilaterally, no crackles or wheezes.\nAbdomen: Soft, non-tender, non-distended. Normal bowel sounds.\nNeurological: GCS 15/15. Cranial nerves II-XII intact. Motor power 5/5 in all 4 limbs. No neck stiffness.\nExtremities: Warm, well-perfused, no peripheral edema.",
  },
  safety_net: {
    label: "+ Emergency Red Flags",
    text: "Return Precautions Explained to Patient & Family:\n1. Immediate Emergency Evaluation: Seek emergency care immediately if experiencing recurrent high fever, new or worsening confusion, seizure, persistent vomiting, severe worsening headache, focal limb weakness, or respiratory distress.\n2. Scheduled Review: Follow up in outpatient clinic within 7 to 10 days or earlier upon availability of pending laboratory cultures.\n3. Medication Adherence: Complete full course of prescribed therapy and report adverse effects.",
  },
};

function VitalsGrid({ text, onChange }: { text: any; onChange: (v: string) => void }) {
  const safeText = typeof text === "string" ? text : String(text ?? "");
  const vitals = parseVitals(safeText);
  const fields = ["BP", "HR", "RR", "Temp", "SpO2", "GCS", "Weight", "Height", "BMI"];
  const [local, setLocal] = useState<Record<string, string>>(vitals);

  useEffect(() => {
    setLocal(parseVitals(safeText));
  }, [text, safeText]);

  const commit = (updated: Record<string, string>) => {
    const out = Object.entries(updated)
      .filter(([, v]) => v && v !== "Not documented")
      .map(([k, v]) => `${k}: ${v}`)
      .join(" | ");
    onChange(out || safeText);
  };

  return (
    <div className="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-9 gap-2 mt-1">
      {fields.map((f) => {
        const val = local[f] || "";
        const abnormal = isAbnormalVital(f, val);

        return (
          <div
            key={f}
            className={`relative rounded-xl border overflow-hidden transition-all ${
              abnormal
                ? "bg-amber-50 border-amber-300 ring-2 ring-amber-400/20"
                : "bg-white border-slate-200 hover:border-blue-300"
            }`}
          >
            <div className="flex items-center justify-between px-2 pt-1.5 pb-0.5">
              <span className="text-[10px] font-black text-slate-500 bg-slate-100 rounded px-1">
                {VITAL_ICONS[f] || f}
              </span>
              <div className="flex items-center gap-1">
                {abnormal && (
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" title="Abnormal value" />
                )}
                <span className="text-[9px] font-mono text-slate-400 font-semibold">{VITAL_UNITS[f]}</span>
              </div>
            </div>
            <input
              type="text"
              value={val}
              onChange={(e) => {
                const updated = { ...local, [f]: e.target.value };
                setLocal(updated);
                commit(updated);
              }}
              placeholder="—"
              className={`w-full px-2 pb-1.5 text-xs font-semibold outline-none bg-transparent placeholder:text-slate-300 ${
                abnormal ? "text-amber-900" : "text-slate-800"
              }`}
            />
          </div>
        );
      })}
    </div>
  );
}

function SectionField({
  section,
  value,
  onChange,
  isDragOver,
  onDragOver,
  onDragLeave,
  onDrop,
  isDropZone,
  clinicianFill,
}: {
  section: { id: string; label: string; icon: any; required?: boolean; clinicianFill?: boolean };
  value: string;
  onChange: (v: string) => void;
  isDragOver: boolean;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => void;
  isDropZone?: boolean;
  clinicianFill?: boolean;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = "auto";
      ref.current.style.height = `${Math.max(ref.current.scrollHeight, 60)}px`;
    }
  }, [value]);

  return (
    <div
      className={`relative rounded-xl transition-all duration-200 ${
        isDragOver ? "ring-4 ring-blue-400/40 bg-blue-50/80 shadow-[0_0_20px_rgba(59,130,246,0.25)]" : ""
      }`}
    >
      {isDropZone && (
        <div
          className={`absolute -top-2 -right-2 text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full z-10 transition-all ${
            isDragOver
              ? "bg-blue-600 text-white shadow-md ring-2 ring-blue-200"
              : "bg-slate-100 text-slate-400 border border-slate-200"
          }`}
        >
          Drop zone
        </div>
      )}
      <textarea
        ref={ref}
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          if (ref.current) {
            ref.current.style.height = "auto";
            ref.current.style.height = `${Math.max(ref.current.scrollHeight, 60)}px`;
          }
        }}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        placeholder={
          clinicianFill
            ? `Clinician completes ${section.label.toLowerCase()} here...`
            : isDropZone
            ? `Drag AI-suggested findings here, or type directly...`
            : `Enter ${section.label.toLowerCase()}...`
        }
        className={`w-full min-h-[64px] p-3 text-xs leading-relaxed rounded-xl border resize-none outline-none shadow-xs transition-all font-mono ${
          isDragOver
            ? "bg-blue-50 border-blue-400 text-blue-900"
            : clinicianFill
            ? "bg-amber-50/40 border-amber-200 text-slate-800 focus:ring-2 focus:ring-amber-400/40 focus:border-amber-300 focus:bg-white"
            : "bg-slate-50 border-slate-200 text-slate-800 focus:ring-2 focus:ring-blue-400/30 focus:border-blue-300 focus:bg-white hover:bg-white"
        }`}
      />
    </div>
  );
}

function getSectionText(val: any): string {
  if (!val) return "";
  if (typeof val === "string") return val;
  if (typeof val?.text === "string") return val.text;
  if (val?.text != null) return String(val.text);
  return "";
}

function normalizeBody(raw: Record<string, any>): Record<string, NoteSection> {
  const out: Record<string, NoteSection> = {};
  for (const [key, val] of Object.entries(raw)) {
    if (key.startsWith("_")) continue;
    if (["patient_encounter_header", "clinical_timeline", "investigations_list", "differential_candidates"].includes(key)) {
      continue;
    }
    if (typeof val === "string") {
      out[key] = { text: val, original_ai_text: val, status: "draft" };
    } else if (val && typeof val === "object" && "text" in val) {
      out[key] = { ...val, text: typeof val.text === "string" ? val.text : String(val.text ?? "") };
    } else {
      out[key] = { text: "", original_ai_text: null, status: "draft" };
    }
  }
  return out;
}

// ─── Main ClinicalNoteEditor Component ─────────────────────────────────────────
export default function ClinicalNoteEditor({ consultationId }: { consultationId: string }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { data: note, isLoading, error: fetchError } = useClinicalNote(consultationId);
  const updateMutation = useUpdateClinicalNote(consultationId);

  const [body, setBody] = useState<Record<string, NoteSection>>({});
  const [saveTimeout, setSaveTimeout] = useState<NodeJS.Timeout | null>(null);
  const [dragOverSection, setDragOverSection] = useState<string | null>(null);
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());
  const [copiedFull, setCopiedFull] = useState(false);
  const [copiedSectionId, setCopiedSectionId] = useState<string | null>(null);

  // Active view tabs for hospital sections
  const [activeTab, setActiveTab] = useState<"note" | "timeline" | "investigations" | "differential">("note");

  // Investigation order form state
  const [newTestName, setNewTestName] = useState("");
  const [newTestCategory, setNewTestCategory] = useState("Laboratory");
  const [newTestPriority, setNewTestPriority] = useState("Routine");
  const [newTestRationale, setNewTestRationale] = useState("");
  const [isOrderingTest, setIsOrderingTest] = useState(false);

  // Investigation result entry state
  const [enteringResultForInv, setEnteringResultForInv] = useState<NoteInvestigationItem | null>(null);
  const [resultText, setResultText] = useState("");
  const [resultFlag, setResultFlag] = useState<"Normal" | "Abnormal" | "Critical">("Normal");
  const [isSubmittingResult, setIsSubmittingResult] = useState(false);

  // Differential action state
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);
  const [isRerunningDiff, setIsRerunningDiff] = useState(false);
  const [isGeneratingNote, setIsGeneratingNote] = useState(false);

  // Extract structured clinical objects from note.body
  const rawBody = useMemo(() => (note?.body as Record<string, any>) || {}, [note?.body]);
  const patientHeader: NotePatientEncounterHeader | null = rawBody.patient_encounter_header || null;
  const clinicalTimeline: NoteTimelineMilestone[] = Array.isArray(rawBody.clinical_timeline)
    ? rawBody.clinical_timeline
    : [];
  const investigationsList: NoteInvestigationItem[] = Array.isArray(rawBody.investigations_list)
    ? rawBody.investigations_list
    : [];
  const differentialCandidates: NoteDifferentialCandidate[] = Array.isArray(rawBody.differential_candidates)
    ? rawBody.differential_candidates
    : [];

  useEffect(() => {
    if (note?.body) {
      setBody(normalizeBody(note.body as Record<string, any>));
    } else {
      getOfflineNoteDraft(consultationId).then((draft) => {
        if (draft?.body) setBody(normalizeBody(draft.body));
      });
    }
  }, [note?.version, consultationId, note?.body]);

  const saveNote = useCallback(
    (updatedBody: Record<string, NoteSection>, currentVersion: number) => {
      // Preserve structured clinical fields in note.body when updating plain sections
      const mergedBody: Record<string, any> = {
        ...rawBody,
        ...updatedBody,
      };
      updateMutation.mutate({ body: mergedBody, version: currentVersion });
    },
    [updateMutation, rawBody]
  );

  useEffect(() => {
    return registerNetworkReconnectionSync(() => {
      if (note && body) {
        saveNote(body, note.version);
      }
    });
  }, [note, body, saveNote]);

  const handleChange = (sectionId: string, value: string) => {
    const cur = body[sectionId] || { text: "", original_ai_text: null, status: "draft" };
    const updated = { ...body, [sectionId]: { ...cur, text: value } };
    setBody(updated);
    saveOfflineNoteDraft(consultationId, updated, note?.version || 1);
    if (saveTimeout) clearTimeout(saveTimeout);
    const t = setTimeout(() => {
      if (note) saveNote(updated, note.version);
    }, 1000);
    setSaveTimeout(t);
  };

  const handleCopySection = (sectionId: string, text: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedSectionId(sectionId);
    setTimeout(() => setCopiedSectionId(null), 2000);
  };

  const handleInsertBoilerplate = (sectionId: string, boilerplateText: string) => {
    const cur = getSectionText(body[sectionId]);
    const updatedText = cur ? `${cur}\n\n${boilerplateText}` : boilerplateText;
    handleChange(sectionId, updatedText);
  };

  const handleCopyFullHospitalNote = () => {
    // If backend formatted markdown is available, use it directly
    if (rawBody._meta?.formatted_ehr_text) {
      navigator.clipboard.writeText(rawBody._meta.formatted_ehr_text);
      setCopiedFull(true);
      setTimeout(() => setCopiedFull(false), 2000);
      return;
    }

    // Fallback: build standard hospital markdown note matching Example 1 & Example 2
    const lines: string[] = [
      `# INPATIENT CLINICAL NOTE`,
      "",
      `**Patient Name:** ${patientHeader?.patient_name || "Not documented"}`,
      `**Age/Sex:** ${patientHeader?.age_sex || patientHeader?.dob_age || "Not documented"}`,
      `**UHID / MRN:** ${patientHeader?.mrn_uhid || "Pending assignment"}`,
      `**Date of Admission:** ${patientHeader?.date_of_admission || "Pending admission"}`,
      `**Date of Discharge:** ${patientHeader?.date_of_discharge || "Inpatient (Active)"}`,
      `**Ward / Unit:** ${patientHeader?.ward_unit || "General Ward"}`,
      `**Consultant:** ${patientHeader?.attending_consultant || "Department of General Medicine"}`,
      `**Author:** ${patientHeader?.author || "Attending Clinician"}`,
      `**Chief Complaint:** ${patientHeader?.chief_complaint || getSectionText(body.chief_complaint) || "Not documented"}`,
      "",
      "---",
      "",
      "## CLINICAL TIMELINE & ENCOUNTER AUDIT",
      "",
    ];

    if (clinicalTimeline.length > 0) {
      clinicalTimeline.forEach((tl) => {
        lines.push(`### ${tl.timestamp} | ${tl.stage} [${tl.source === "clinician" ? "CLINICIAN" : "AI DECISION SUPPORT"}]`);
        lines.push(`* **Event:** ${tl.event}`);
        if (tl.findings) lines.push(`* **Findings:** ${tl.findings}`);
        if (tl.actions) lines.push(`* **Action:** ${tl.actions}`);
        if (tl.response) lines.push(`* **Response:** ${tl.response}`);
        lines.push("");
      });
    } else {
      lines.push("No chronological milestones recorded yet.");
      lines.push("");
    }

    lines.push("---", "", "## INVESTIGATIONS", "");
    if (investigationsList.length > 0) {
      investigationsList.forEach((inv) => {
        lines.push(`* **${inv.name}** (${inv.category} - ${inv.priority}) [${inv.status.toUpperCase()}]: ${inv.result} (Flag: ${inv.flag})`);
      });
    } else {
      lines.push("No investigations currently ordered.");
    }
    lines.push("");

    lines.push("---", "", "## ASSESSMENT & DIFFERENTIAL DIAGNOSIS", "");
    lines.push(`### Working Assessment`);
    lines.push(getSectionText(body.assessment) || "Clinical formulation in progress.");
    lines.push("");

    if (differentialCandidates.length > 0) {
      lines.push("### Differential Diagnoses Considered (AI-Assisted Reasoning)");
      lines.push("> *Reference information generated for clinician review. Not a confirmed diagnosis.*");
      lines.push("");
      differentialCandidates.forEach((cand, idx) => {
        lines.push(`${idx + 1}. **${cand.disease}** (${cand.tier} — ${cand.display_score}) [Status: ${cand.clinician_status.toUpperCase()}]`);
        lines.push(`   * **Why considered:** ${cand.rationale}`);
        lines.push(`   * **Supporting evidence:** ${cand.supporting_findings?.join(", ") || "None documented"}`);
        lines.push(`   * **Contradicting / absent:** ${cand.contradicting_findings?.join(", ") || "None"}`);
        lines.push(`   * **Recommended confirmation tests:** ${cand.recommended_tests?.join(", ") || "Standard monitoring"}`);
        lines.push("");
      });
    }

    lines.push("---", "", "## MANAGEMENT PLAN", "");
    lines.push(getSectionText(body.plan) || "Standard supportive care and monitoring.");
    lines.push("");

    lines.push("## HOSPITAL COURSE & DISPOSITION", "");
    lines.push(`**Response to Treatment:** ${getSectionText(body.clinical_response) || "Stable under observation."}`);
    lines.push(`**Disposition:** ${getSectionText(body.disposition) || "Inpatient observation"}`);
    lines.push(`**Follow-Up:** ${getSectionText(body.follow_up_plan) || "As per clinical indication."}`);
    lines.push(`**Safety Net Precautions:** ${getSectionText(body.safety_net) || "Standard red-flag instructions provided."}`);
    lines.push("");

    lines.push("## CLINICIAN AUTHENTICATION", "");
    lines.push(getSectionText(body.authentication) || `Electronically authenticated by ${patientHeader?.attending_consultant || "Attending Physician"}.`);

    navigator.clipboard.writeText(lines.join("\n"));
    setCopiedFull(true);
    setTimeout(() => setCopiedFull(false), 2000);
  };

  // ── Handlers for In-Note Investigation Ordering ──
  const handleOrderInvestigation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTestName.trim()) return;
    setIsOrderingTest(true);
    try {
      const res = await orderInvestigationInNote(consultationId, {
        name: newTestName.trim(),
        category: newTestCategory,
        priority: newTestPriority,
        rationale: newTestRationale.trim() || undefined,
      });
      if (res.ok) {
        queryClient.setQueryData(noteKeys.detail(consultationId), res.data);
        setNewTestName("");
        setNewTestRationale("");
        toast.success(`Investigation ordered: ${newTestName.trim()}`);
      } else {
        toast.error(res.error.message || "Failed to order investigation.");
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to order investigation.");
    } finally {
      setIsOrderingTest(false);
    }
  };

  // ── Handler for Recording Investigation Results ──
  const handleSubmitInvestigationResult = async () => {
    if (!enteringResultForInv || !resultText.trim()) return;
    setIsSubmittingResult(true);
    try {
      const res = await recordInvestigationResultInNote(consultationId, enteringResultForInv.id, {
        result: resultText.trim(),
        flag: resultFlag,
      });
      if (res.ok) {
        queryClient.setQueryData(noteKeys.detail(consultationId), res.data);
        setEnteringResultForInv(null);
        setResultText("");
        setResultFlag("Normal");
        toast.success("Investigation result recorded.");
      } else {
        toast.error(res.error.message || "Failed to record result.");
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to record result.");
    } finally {
      setIsSubmittingResult(false);
    }
  };

  // ── Handlers for Clinician Differential Actions ──
  const handleDifferentialAction = async (candidateId: string, action: "accept" | "reject" | "rule_out") => {
    setActionInProgress(candidateId);
    try {
      const res = await performDifferentialActionInNote(consultationId, candidateId, { action });
      if (res.ok) {
        queryClient.setQueryData(noteKeys.detail(consultationId), res.data);
        toast.success(`Differential candidate ${action}ed.`);
      } else {
        toast.error(res.error.message || "Failed to update differential diagnosis.");
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to update differential diagnosis.");
    } finally {
      setActionInProgress(null);
    }
  };

  const handleRerunDifferential = async () => {
    setIsRerunningDiff(true);
    try {
      const res = await rerunDifferentialInNote(consultationId);
      if (res.ok) {
        queryClient.setQueryData(noteKeys.detail(consultationId), res.data);
        toast.success("Diagnostic engine re-executed.");
      } else {
        toast.error(res.error.message || "Failed to re-run diagnostic engine.");
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to re-run diagnostic engine.");
    } finally {
      setIsRerunningDiff(false);
    }
  };

  const handleGenerateInitialNote = async () => {
    setIsGeneratingNote(true);
    try {
      const res = await generateConsultationNote(consultationId);
      if (res.ok) {
        queryClient.setQueryData(noteKeys.detail(consultationId), res.data);
        toast.success("Hospital clinical note generated.");
      } else {
        toast.error(res.error.message || "Failed to generate hospital clinical note.");
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to generate hospital clinical note.");
    } finally {
      setIsGeneratingNote(false);
    }
  };

  const handleQuickOrderSuggested = async (testName: string, candidateDisease: string) => {
    try {
      const res = await orderInvestigationInNote(consultationId, {
        name: testName,
        category: "Laboratory",
        priority: "Urgent",
        rationale: `Clinician ordered from AI differential recommendation for ${candidateDisease}`,
      });
      if (res.ok && res.data) {
        queryClient.setQueryData(noteKeys.detail(consultationId), res.data);
        setActiveTab("investigations");
        toast.success(`Ordered ${testName} for ${candidateDisease}.`);
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to order test.");
    }
  };

  const handleExport = async (format: "pdf" | "docx" | "fhir") => {
    try {
      const BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/api\/v1\/?$/, "");
      const token =
        getStoredToken() ||
        (typeof window !== "undefined"
          ? localStorage.getItem("docassistiq_access_token") || localStorage.getItem("access_token") || localStorage.getItem("token")
          : null) ||
        "";
      const url = `${BASE_URL}/api/v1/consultations/${consultationId}/export?format=${format}`;
      const res = await fetch(url, { headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) } });
      if (!res.ok) {
        let errMsg = "Failed to export note";
        try {
          const errData = await res.json();
          if (errData?.detail) errMsg = errData.detail;
        } catch {
          // ignore
        }
        throw new Error(errMsg);
      }
      if (format === "pdf") {
        const blob = await res.blob();
        const blobUrl = URL.createObjectURL(new Blob([blob], { type: "application/pdf" }));
        const a = Object.assign(document.createElement("a"), {
          href: blobUrl,
          download: `hospital_note_${consultationId.slice(0, 8)}.pdf`,
        });
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(blobUrl);
        toast.success("Hospital PDF Note downloaded.");
      } else if (format === "docx") {
        const blob = await res.blob();
        const blobUrl = URL.createObjectURL(
          new Blob([blob], { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" })
        );
        const a = Object.assign(document.createElement("a"), {
          href: blobUrl,
          download: `hospital_note_${consultationId.slice(0, 8)}.docx`,
        });
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(blobUrl);
        toast.success("Microsoft Word DOCX Note downloaded.");
      } else {
        const fhirData = await res.json();
        const fhirBlob = new Blob([JSON.stringify(fhirData, null, 2)], { type: "application/json" });
        const blobUrl = URL.createObjectURL(fhirBlob);
        const a = Object.assign(document.createElement("a"), {
          href: blobUrl,
          download: `hospital_record_${consultationId.slice(0, 8)}_fhir_r4.json`,
        });
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(blobUrl);
        navigator.clipboard.writeText(JSON.stringify(fhirData, null, 2));
        toast.success("HL7 FHIR R4 Bundle downloaded & copied to clipboard!");
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to export note.");
    }
  };

  const handleDrop = (e: React.DragEvent, sectionId: string) => {
    e.preventDefault();
    setDragOverSection(null);
    const dragged = e.dataTransfer.getData("text/plain");
    if (!dragged) return;
    const cur = getSectionText(body[sectionId]);
    const formatted = cur ? `${cur}\n\n[Clinical Finding] ${dragged}` : `[Clinical Finding] ${dragged}`;
    handleChange(sectionId, formatted);
    const el = document.getElementById(`section-${sectionId}`);
    if (el) {
      el.classList.add("ring-4", "ring-emerald-400", "bg-emerald-50");
      setTimeout(() => el.classList.remove("ring-4", "ring-emerald-400", "bg-emerald-50"), 1200);
    }
  };

  const handleAccept = (sectionId: string) => {
    const cur = body[sectionId];
    if (!cur) return;
    const updated = { ...body, [sectionId]: { ...cur, status: "accepted" as const } };
    setBody(updated);
    saveOfflineNoteDraft(consultationId, updated, note?.version || 1);
    if (note) saveNote(updated, note.version);
  };

  const handleRevert = (sectionId: string) => {
    const cur = body[sectionId];
    if (!cur?.original_ai_text) return;
    const updated = { ...body, [sectionId]: { ...cur, text: cur.original_ai_text, status: "draft" as const } };
    setBody(updated);
    saveOfflineNoteDraft(consultationId, updated, note?.version || 1);
    if (note) saveNote(updated, note.version);
  };

  const allSections = SOAP_GROUPS.flatMap((g) => g.sections);
  const filled = allSections.filter((s) => getSectionText(body[s.id]).trim().length > 0).length;
  const total = allSections.length;
  const pct = Math.round((filled / total) * 100);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 bg-white">
        <div className="w-8 h-8 border-3 border-teal-600 border-t-transparent rounded-full animate-spin" />
        <span className="text-xs text-slate-500 font-semibold tracking-wide">
          Loading hospital EHR clinical record...
        </span>
      </div>
    );
  }

  if (fetchError || !note) {
    return (
      <div className="p-8 bg-white border border-slate-200 rounded-2xl m-6 shadow-xs text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-teal-50 border border-teal-200 text-teal-700 flex items-center justify-center mx-auto">
          <FileSpreadsheet className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-base font-extrabold text-slate-900">Hospital Clinical Note Pending</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
            Generate a full real-time inpatient clinical note with timeline, investigation tracking, and AI differential reasoning for this consultation.
          </p>
        </div>
        <button
          type="button"
          onClick={handleGenerateInitialNote}
          disabled={isGeneratingNote}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-xs transition-all disabled:opacity-50"
        >
          {isGeneratingNote ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Formulating Hospital Record...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-3.5 h-3.5" />
              <span>Generate Hospital Clinical Note</span>
            </>
          )}
        </button>
      </div>
    );
  }

  const saving = updateMutation.isPending;

  return (
    <div className="bg-white flex flex-col h-full overflow-hidden text-slate-900">
      {/* ── Top Hospital Bar ── */}
      <div className="shrink-0 bg-white px-5 py-3 border-b border-slate-200 shadow-2xs">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-teal-50 border border-teal-200 rounded-xl flex items-center justify-center text-teal-700 shadow-2xs">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-slate-900 font-extrabold text-sm tracking-tight font-heading">
                  INPATIENT CLINICAL NOTE
                </h2>
                <span className="text-[10px] font-black uppercase tracking-wider bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md border border-slate-200">
                  {note.status || "DRAFT"}
                </span>
                {patientHeader?.mrn_uhid && (
                  <span className="text-[10px] font-mono font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded-md border border-teal-200">
                    UHID: {patientHeader.mrn_uhid}
                  </span>
                )}
              </div>
              <p className="text-slate-500 text-[10px] font-semibold mt-0.5">
                Clinical Progress Note · Electronic Health Record · Version {note.version}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {/* Completeness Ring */}
            <div className="flex items-center gap-2 bg-slate-50 px-2.5 py-1 rounded-xl border border-slate-200">
              <svg className="w-6 h-6 -rotate-90" viewBox="0 0 32 32">
                <circle cx="16" cy="16" r="12" fill="none" stroke="#e2e8f0" strokeWidth="3" />
                <circle
                  cx="16"
                  cy="16"
                  r="12"
                  fill="none"
                  stroke={pct >= 80 ? "#059669" : pct >= 50 ? "#d97706" : "#2563eb"}
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  strokeDasharray={`${2 * Math.PI * 12}`}
                  strokeDashoffset={`${2 * Math.PI * 12 * (1 - pct / 100)}`}
                />
              </svg>
              <div className="text-right">
                <div className="text-slate-900 font-extrabold text-[11px] leading-none">{pct}%</div>
                <div className="text-slate-400 text-[8px] font-bold uppercase tracking-wider">Filled</div>
              </div>
            </div>

            {/* Save Status */}
            <div
              className={`flex items-center gap-1.5 text-[10px] font-extrabold uppercase tracking-wider px-2 py-1 rounded-lg ${
                saving ? "text-amber-700 bg-amber-50 border border-amber-200" : "text-emerald-700 bg-emerald-50 border border-emerald-200"
              }`}
            >
              {saving ? (
                <>
                  <span className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-ping" />
                  Saving
                </>
              ) : (
                <>
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
                  Saved
                </>
              )}
            </div>

            {/* EHR Markdown 1-Click Copy */}
            <button
              type="button"
              onClick={handleCopyFullHospitalNote}
              title="Copy complete hospital note formatted for EHR/EMR (matching Example 1 & 2)"
              className="text-xs font-bold text-teal-800 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-3 py-1.5 rounded-xl border border-teal-200 transition-colors shadow-2xs flex items-center gap-1.5 cursor-pointer"
            >
              {copiedFull ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="text-emerald-700 font-extrabold">Copied for EHR!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-teal-700" />
                  <span>Copy Complete Note</span>
                </>
              )}
            </button>

            {/* Toggle Sections */}
            <button
              type="button"
              onClick={() => {
                if (collapsedGroups.size === SOAP_GROUPS.length) {
                  setCollapsedGroups(new Set());
                } else {
                  setCollapsedGroups(new Set(SOAP_GROUPS.map((g) => g.groupId)));
                }
              }}
              title="Toggle all categories"
              className="text-xs font-bold text-slate-700 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 px-2.5 py-1.5 rounded-xl border border-slate-200 transition-colors shadow-2xs flex items-center gap-1 cursor-pointer"
            >
              <ChevronsUpDown className="w-3.5 h-3.5 text-slate-500" />
              <span>Toggle</span>
            </button>

            {/* PDF Export */}
            <button
              type="button"
              onClick={() => handleExport("pdf")}
              title="Download official hospital clinical note as PDF"
              className="text-xs font-bold text-rose-700 hover:text-rose-900 bg-rose-50 hover:bg-rose-100 px-2.5 py-1.5 rounded-xl border border-rose-200 transition-colors shadow-2xs flex items-center gap-1 cursor-pointer"
            >
              <FileText className="w-3.5 h-3.5 text-rose-600" />
              <span>PDF</span>
            </button>

            {/* DOCX Export */}
            <button
              type="button"
              onClick={() => handleExport("docx")}
              title="Download official hospital clinical note as Microsoft Word DOCX"
              className="text-xs font-bold text-indigo-700 hover:text-indigo-900 bg-indigo-50 hover:bg-indigo-100 px-2.5 py-1.5 rounded-xl border border-indigo-200 transition-colors shadow-2xs flex items-center gap-1 cursor-pointer"
            >
              <Download className="w-3.5 h-3.5 text-indigo-600" />
              <span>DOCX</span>
            </button>

            {/* FHIR Export */}
            <button
              type="button"
              onClick={() => handleExport("fhir")}
              title="Export as HL7 FHIR R4 Bundle"
              className="text-xs font-bold text-slate-700 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 px-2.5 py-1.5 rounded-xl border border-slate-200 transition-colors shadow-2xs flex items-center gap-1 cursor-pointer"
            >
              <Share2 className="w-3.5 h-3.5 text-slate-500" />
              <span>FHIR</span>
            </button>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center gap-1 mt-3 border-t border-slate-100 pt-2">
          <button
            type="button"
            onClick={() => setActiveTab("note")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
              activeTab === "note"
                ? "bg-slate-900 text-white shadow-2xs"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Hospital Note (SOAP+)</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("timeline")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
              activeTab === "timeline"
                ? "bg-teal-700 text-white shadow-2xs"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            <span>Encounter Timeline</span>
            <span className="text-[10px] font-black px-1.5 py-0.2 rounded-full bg-slate-200 text-slate-800">
              {clinicalTimeline.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("investigations")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
              activeTab === "investigations"
                ? "bg-blue-700 text-white shadow-2xs"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            }`}
          >
            <FlaskConical className="w-3.5 h-3.5" />
            <span>In-Note Investigations</span>
            <span className="text-[10px] font-black px-1.5 py-0.2 rounded-full bg-slate-200 text-slate-800">
              {investigationsList.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("differential")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
              activeTab === "differential"
                ? "bg-purple-700 text-white shadow-2xs"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            }`}
          >
            <Target className="w-3.5 h-3.5" />
            <span>AI Differential & Reasoning</span>
            <span className="text-[10px] font-black px-1.5 py-0.2 rounded-full bg-slate-200 text-slate-800">
              {differentialCandidates.length}
            </span>
          </button>
        </div>
      </div>

      {/* ── Main Scrollable Body ── */}
      <div className="flex-1 overflow-y-auto bg-slate-50/60 p-5">
        <div className="max-w-4xl mx-auto space-y-6 pb-24">
          {/* ══════════════════════════════════════════════════════════════════
              PATIENT / ENCOUNTER HEADER (Matches Example 1 & Example 2)
              ══════════════════════════════════════════════════════════════════ */}
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Building2 className="w-4 h-4 text-teal-600" />
                <h3 className="text-xs font-black tracking-wider uppercase text-slate-800 font-heading">
                  PATIENT / ENCOUNTER INFORMATION
                </h3>
              </div>
              <span className="text-[10px] font-mono text-slate-400">
                Generated: {patientHeader?.date_time_of_note || "Current local time"}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Patient Name</span>
                <span className="font-extrabold text-slate-900">{patientHeader?.patient_name || "Not documented"}</span>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">MRN / UHID</span>
                <span className="font-mono font-bold text-teal-700">{patientHeader?.mrn_uhid || "Pending assignment"}</span>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Age / Sex</span>
                <span className="font-semibold text-slate-800">
                  {patientHeader?.age_sex || patientHeader?.dob_age || "Not documented"}
                </span>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Encounter Type</span>
                <span className="font-semibold text-slate-800">{patientHeader?.encounter_type || "Inpatient Encounter"}</span>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Admission Date</span>
                <span className="font-semibold text-slate-800">{patientHeader?.date_of_admission || "Pending admission"}</span>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Discharge Date</span>
                <span className="font-semibold text-slate-800">{patientHeader?.date_of_discharge || "Active Inpatient"}</span>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Ward / Unit</span>
                <span className="font-semibold text-slate-800">{patientHeader?.ward_unit || "General Medicine Ward"}</span>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Consultant / Author</span>
                <span className="font-semibold text-slate-800 truncate block" title={patientHeader?.attending_consultant}>
                  {patientHeader?.attending_consultant || "Attending Physician"}
                </span>
              </div>
            </div>

            {/* Chief Complaint Highlight Box */}
            <div className="mt-3 p-3 rounded-xl bg-teal-50/50 border border-teal-100 flex items-start gap-2.5">
              <span className="text-[10px] font-black text-teal-800 uppercase tracking-wider bg-teal-100 px-2 py-0.5 rounded shrink-0">
                Chief Complaint
              </span>
              <p className="text-xs font-semibold text-slate-800 leading-relaxed">
                {patientHeader?.chief_complaint || getSectionText(body.chief_complaint) || "Not recorded"}
              </p>
            </div>
          </div>

          {/* ══════════════════════════════════════════════════════════════════
              TAB 1: COMPLETE HOSPITAL NOTE (SOAP+ Narrative & Clinical Sections)
              ══════════════════════════════════════════════════════════════════ */}
          {activeTab === "note" && (
            <div className="space-y-6">
              {SOAP_GROUPS.map((group, gIdx) => {
                const colors = GROUP_COLORS[group.color];
                const isCollapsed = collapsedGroups.has(group.groupId);

                return (
                  <motion.div
                    key={group.groupId}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: gIdx * 0.05, duration: 0.3 }}
                    className={`rounded-2xl border ${colors.border} overflow-hidden shadow-xs bg-white`}
                  >
                    {/* Category Header */}
                    <button
                      type="button"
                      onClick={() =>
                        setCollapsedGroups((prev) => {
                          const next = new Set(prev);
                          if (next.has(group.groupId)) next.delete(group.groupId);
                          else next.add(group.groupId);
                          return next;
                        })
                      }
                      className={`w-full flex items-center justify-between px-5 py-3.5 bg-gradient-to-r ${colors.header} border-b ${colors.border} hover:brightness-98 transition-all cursor-pointer`}
                    >
                      <div className="flex items-center gap-3">
                        <group.icon className="w-4 h-4 text-current shrink-0" />
                        <div className="text-left">
                          <h3 className={`font-black text-xs ${colors.text} uppercase tracking-widest font-heading`}>
                            {group.groupLabel}
                          </h3>
                          <p className="text-[10px] text-slate-500 mt-0.5">
                            {group.sections.filter((s) => getSectionText(body[s.id]).trim().length > 0).length} of{" "}
                            {group.sections.length} sections recorded
                          </p>
                        </div>
                      </div>
                      <span className={`text-base font-bold ${colors.text} opacity-70`}>
                        {isCollapsed ? "+" : "−"}
                      </span>
                    </button>

                    {/* Section Fields */}
                    <AnimatePresence>
                      {!isCollapsed && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden"
                        >
                          <div className="divide-y divide-slate-100">
                            {group.sections.map((section, sIdx) => {
                              const sectionData = body[section.id];
                              const text = getSectionText(sectionData);
                              const isAiDraft = sectionData?.status === "draft" && !!sectionData?.original_ai_text;
                              const isAccepted = sectionData?.status === "accepted";
                              const isDragOver = dragOverSection === section.id;

                              return (
                                <div
                                  key={section.id}
                                  id={`section-${section.id}`}
                                  className="p-4 transition-colors group hover:bg-slate-50/40"
                                >
                                  {/* Section Title & Tools */}
                                  <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2 flex-wrap">
                                      <section.icon className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                                      <label className="font-bold text-xs text-slate-800 tracking-tight">
                                        {section.label}
                                      </label>
                                      {section.required && (
                                        <span className="text-red-500 text-[10px] font-black" title="Required">*</span>
                                      )}

                                      {isAccepted && (
                                        <span className="text-[9px] font-black uppercase tracking-widest bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full flex items-center gap-1">
                                          ✓ Accepted
                                        </span>
                                      )}

                                      {isAiDraft && !isAccepted && (
                                        <span className="text-[9px] font-black uppercase tracking-widest bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-full flex items-center gap-1">
                                          <Sparkles className="w-2.5 h-2.5 text-blue-600" />
                                          AI Drafted
                                        </span>
                                      )}

                                      {(section as any).clinicianFill && (
                                        <span className="text-[9px] font-black uppercase tracking-widest bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full">
                                          Clinician Fill
                                        </span>
                                      )}

                                      {SECTION_BOILERPLATES[section.id] && !text.trim() && (
                                        <button
                                          type="button"
                                          onClick={() =>
                                            handleInsertBoilerplate(section.id, SECTION_BOILERPLATES[section.id].text)
                                          }
                                          className="text-[10px] font-bold text-teal-700 bg-teal-50 hover:bg-teal-100 px-2 py-0.5 rounded-md border border-teal-200 transition-colors flex items-center gap-1 cursor-pointer"
                                        >
                                          {SECTION_BOILERPLATES[section.id].label}
                                        </button>
                                      )}
                                    </div>

                                    {/* Action buttons */}
                                    <div className="flex items-center gap-1.5 opacity-90 group-hover:opacity-100 transition-opacity">
                                      {text && (
                                        <button
                                          type="button"
                                          onClick={() => handleCopySection(section.id, text)}
                                          title="Copy section"
                                          className="text-[10px] font-bold text-slate-600 hover:text-slate-800 bg-slate-50 hover:bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200 shadow-2xs transition-all flex items-center gap-1 cursor-pointer"
                                        >
                                          {copiedSectionId === section.id ? (
                                            <span className="text-emerald-600 font-extrabold flex items-center gap-1">
                                              <Check className="w-3 h-3" /> Copied
                                            </span>
                                          ) : (
                                            <>
                                              <Copy className="w-3 h-3" />
                                              <span>Copy</span>
                                            </>
                                          )}
                                        </button>
                                      )}

                                      {isAiDraft && (
                                        <>
                                          <button
                                            type="button"
                                            onClick={() => handleAccept(section.id)}
                                            className="text-[10px] font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 px-2.5 py-1 rounded-lg border border-emerald-200 transition-all shadow-2xs cursor-pointer"
                                          >
                                            ✓ Accept
                                          </button>
                                          <button
                                            type="button"
                                            onClick={() => handleRevert(section.id)}
                                            className="text-[10px] font-bold text-slate-600 bg-slate-50 hover:bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200 transition-all shadow-2xs cursor-pointer"
                                          >
                                            ↩ Revert
                                          </button>
                                        </>
                                      )}
                                    </div>
                                  </div>

                                  {/* Field content */}
                                  {section.id === "vitals" ? (
                                    <div>
                                      <VitalsGrid text={text} onChange={(v) => handleChange("vitals", v)} />
                                      <textarea
                                        className="mt-2 w-full min-h-[36px] p-2.5 text-xs leading-relaxed rounded-xl border border-slate-200 bg-slate-50 text-slate-600 resize-none outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-300 focus:bg-white transition-all font-mono"
                                        value={text}
                                        onChange={(e) => handleChange("vitals", e.target.value)}
                                        placeholder="Full vitals string: BP: 120/80 | HR: 72 | Temp: 37.2 | SpO2: 98 | RR: 16 | GCS: 15"
                                        rows={1}
                                      />
                                    </div>
                                  ) : (
                                    <SectionField
                                      section={section}
                                      value={text}
                                      onChange={(v) => handleChange(section.id, v)}
                                      isDragOver={isDragOver}
                                      onDragOver={(e) => {
                                        e.preventDefault();
                                        setDragOverSection(section.id);
                                      }}
                                      onDragLeave={(e) => {
                                        e.preventDefault();
                                        setDragOverSection(null);
                                      }}
                                      onDrop={(e) => handleDrop(e, section.id)}
                                      isDropZone={(section as any).dropZone}
                                      clinicianFill={(section as any).clinicianFill}
                                    />
                                  )}

                                  {/* AI Feedback rating */}
                                  <AnimatePresence>
                                    {isAiDraft && (
                                      <motion.div
                                        initial={{ opacity: 0, height: 0 }}
                                        animate={{ opacity: 1, height: "auto" }}
                                        exit={{ opacity: 0, height: 0 }}
                                        className="mt-2 pt-2 border-t border-slate-100"
                                      >
                                        <FeedbackButtons
                                          suggestionId={`note-${consultationId}-${section.id}-${note?.version}`}
                                          suggestionType="clinical_note"
                                          suggestionContext={{
                                            section: section.id,
                                            original_text: sectionData?.original_ai_text,
                                            edited_text: text,
                                          }}
                                          onFeedbackSubmitted={(decision) => {
                                            if (decision === "ACCEPT") handleAccept(section.id);
                                            else if (decision === "REJECT") handleRevert(section.id);
                                          }}
                                        />
                                      </motion.div>
                                    )}
                                  </AnimatePresence>
                                </div>
                              );
                            })}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                );
              })}
            </div>
          )}

          {/* ══════════════════════════════════════════════════════════════════
              TAB 2: CHRONOLOGICAL CLINICAL TIMELINE (Real-Time Encounter Flow)
              ══════════════════════════════════════════════════════════════════ */}
          {activeTab === "timeline" && (
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100">
                <div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-teal-600" />
                    <h3 className="text-xs font-black tracking-wider uppercase text-slate-800 font-heading">
                      CHRONOLOGICAL ENCOUNTER TIMELINE
                    </h3>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Real-time hospital encounter audit from admission through investigations, AI updates, and clinician decision.
                  </p>
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                  {clinicalTimeline.length} Chronological Milestones
                </span>
              </div>

              {clinicalTimeline.length === 0 ? (
                <div className="p-8 text-center text-slate-400 text-xs">
                  No chronological events recorded yet. Milestones will be added automatically as investigations are ordered, results are reported, and clinician decisions are logged.
                </div>
              ) : (
                <div className="relative pl-6 space-y-6 before:content-[''] before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
                  {clinicalTimeline.map((item, idx) => {
                    const isClinician = item.source === "clinician";
                    return (
                      <div key={item.id || idx} className="relative group">
                        {/* Timeline Node Dot */}
                        <div
                          className={`absolute -left-6 top-1 w-5 h-5 rounded-full border-2 border-white shadow-xs flex items-center justify-center ${
                            isClinician ? "bg-emerald-600" : "bg-indigo-600"
                          }`}
                        >
                          <div className="w-1.5 h-1.5 rounded-full bg-white" />
                        </div>

                        {/* Milestone Card */}
                        <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-2xs hover:border-slate-300 transition-all space-y-2">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-[11px] font-bold text-slate-500">
                                {item.timestamp}
                              </span>
                              <span className="text-slate-300">•</span>
                              <span className="text-xs font-black text-slate-900 font-heading">
                                {item.stage}
                              </span>
                            </div>

                            <span
                              className={`text-[9px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                                isClinician
                                  ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                                  : "bg-indigo-50 text-indigo-800 border-indigo-200"
                              }`}
                            >
                              {isClinician ? "Clinician Authenticated" : "AI Decision Support"}
                            </span>
                          </div>

                          <div className="text-xs font-bold text-slate-800">{item.event}</div>

                          {item.findings && (
                            <div className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                              <span className="font-bold text-slate-700">Findings: </span>
                              {item.findings}
                            </div>
                          )}

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                            {item.actions && (
                              <div className="text-slate-600">
                                <span className="font-bold text-slate-700">Action: </span>
                                {item.actions}
                              </div>
                            )}
                            {item.response && (
                              <div className="text-slate-600">
                                <span className="font-bold text-slate-700">Response / Evolution: </span>
                                {item.response}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* ══════════════════════════════════════════════════════════════════
              TAB 3: IN-NOTE INVESTIGATIONS WORKSPACE (Order & View in Note)
              ══════════════════════════════════════════════════════════════════ */}
          {activeTab === "investigations" && (
            <div className="space-y-6">
              {/* Order Investigation Box */}
              <div className="rounded-2xl border border-blue-200 bg-white p-5 shadow-xs space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <FlaskConical className="w-4 h-4 text-blue-700" />
                    <h3 className="text-xs font-black tracking-wider uppercase text-slate-800 font-heading">
                      ORDER INVESTIGATION IN NOTE
                    </h3>
                  </div>
                  <span className="text-[10px] text-slate-400 font-medium">
                    Direct EHR Dispatch
                  </span>
                </div>

                <form onSubmit={handleOrderInvestigation} className="space-y-3">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="sm:col-span-2">
                      <label className="block text-[10px] font-bold text-slate-600 uppercase tracking-wider mb-1">
                        Investigation / Test Name
                      </label>
                      <input
                        type="text"
                        value={newTestName}
                        onChange={(e) => setNewTestName(e.target.value)}
                        placeholder="e.g., Lumbar Puncture (CSF analysis), MRI Brain with contrast, Blood Cultures x2"
                        className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-blue-400/30 outline-none font-semibold text-slate-800"
                        required
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-[10px] font-bold text-slate-600 uppercase tracking-wider mb-1">
                          Category
                        </label>
                        <select
                          value={newTestCategory}
                          onChange={(e) => setNewTestCategory(e.target.value)}
                          className="w-full px-2 py-2 text-xs rounded-xl border border-slate-200 bg-slate-50 focus:bg-white outline-none font-semibold text-slate-800"
                        >
                          <option value="Laboratory">Laboratory</option>
                          <option value="Imaging">Imaging</option>
                          <option value="Microbiology">Microbiology</option>
                          <option value="Pathology">Pathology</option>
                          <option value="Cardiology">Cardiology</option>
                          <option value="Other">Other</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-[10px] font-bold text-slate-600 uppercase tracking-wider mb-1">
                          Priority
                        </label>
                        <select
                          value={newTestPriority}
                          onChange={(e) => setNewTestPriority(e.target.value)}
                          className="w-full px-2 py-2 text-xs rounded-xl border border-slate-200 bg-slate-50 focus:bg-white outline-none font-semibold text-slate-800"
                        >
                          <option value="Routine">Routine</option>
                          <option value="Urgent">Urgent</option>
                          <option value="STAT">STAT</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-slate-600 uppercase tracking-wider mb-1">
                      Clinical Indication / Rationale
                    </label>
                    <input
                      type="text"
                      value={newTestRationale}
                      onChange={(e) => setNewTestRationale(e.target.value)}
                      placeholder="e.g., Rule out viral meningoencephalitis vs arboviral etiology following rural travel."
                      className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-blue-400/30 outline-none text-slate-700"
                    />
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-[10px] text-slate-400 font-bold">Quick add:</span>
                      {[
                        "Lumbar Puncture (CSF)",
                        "MRI Brain with contrast",
                        "Japanese Encephalitis CSF IgM",
                        "CBC with Differential",
                        "Serum Electrolytes",
                      ].map((quick) => (
                        <button
                          key={quick}
                          type="button"
                          onClick={() => setNewTestName(quick)}
                          className="text-[10px] px-2 py-0.5 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors font-medium cursor-pointer"
                        >
                          {quick}
                        </button>
                      ))}
                    </div>

                    <button
                      type="submit"
                      disabled={isOrderingTest || !newTestName.trim()}
                      className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
                    >
                      {isOrderingTest ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Ordering...</span>
                        </>
                      ) : (
                        <>
                          <Plus className="w-3.5 h-3.5" />
                          <span>Order Investigation</span>
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>

              {/* Active Investigations List */}
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <ClipboardList className="w-4 h-4 text-slate-700" />
                    <h3 className="text-xs font-black tracking-wider uppercase text-slate-800 font-heading">
                      ACTIVE & REPORTED INVESTIGATIONS ({investigationsList.length})
                    </h3>
                  </div>
                  <span className="text-[10px] font-bold text-slate-500">
                    Live Status in Note
                  </span>
                </div>

                {investigationsList.length === 0 ? (
                  <div className="p-8 text-center text-slate-400 text-xs">
                    No investigations currently ordered for this patient. Use the form above to order diagnostic tests.
                  </div>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {investigationsList.map((inv) => {
                      const isReported = inv.status === "Reported";
                      const priorityColor =
                        inv.priority === "STAT"
                          ? "bg-red-50 text-red-700 border-red-200"
                          : inv.priority === "Urgent"
                          ? "bg-amber-50 text-amber-700 border-amber-200"
                          : "bg-blue-50 text-blue-700 border-blue-200";

                      const statusColor = isReported
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                        : "bg-slate-100 text-slate-600 border-slate-200";

                      return (
                        <div key={inv.id} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                          <div className="space-y-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-extrabold text-xs text-slate-900">{inv.name}</span>
                              <span className="text-[9px] font-bold uppercase tracking-wider text-slate-500 bg-slate-100 px-1.5 py-0.2 rounded border border-slate-200">
                                {inv.category}
                              </span>
                              <span className={`text-[9px] font-black uppercase tracking-wider px-2 py-0.2 rounded border ${priorityColor}`}>
                                {inv.priority}
                              </span>
                              <span className={`text-[9px] font-black uppercase tracking-wider px-2 py-0.2 rounded border ${statusColor}`}>
                                {inv.status}
                              </span>
                            </div>

                            <p className="text-xs text-slate-600">
                              <span className="font-bold text-slate-700">Result: </span>
                              {inv.result}
                              {inv.flag && inv.flag !== "Pending" && (
                                <span
                                  className={`ml-2 text-[9px] font-bold px-1.5 py-0.2 rounded ${
                                    inv.flag === "Critical"
                                      ? "bg-red-100 text-red-800"
                                      : inv.flag === "Abnormal"
                                      ? "bg-amber-100 text-amber-800"
                                      : "bg-emerald-100 text-emerald-800"
                                  }`}
                                >
                                  {inv.flag}
                                </span>
                              )}
                            </p>

                            <div className="flex items-center gap-3 text-[10px] text-slate-400 font-mono">
                              <span>Ordered: {inv.ordered_at}</span>
                              {inv.reported_at && <span>Reported: {inv.reported_at}</span>}
                            </div>
                          </div>

                          <div className="shrink-0 flex items-center gap-2">
                            <button
                              type="button"
                              onClick={() => {
                                setEnteringResultForInv(inv);
                                setResultText(inv.result && inv.result !== "Pending" ? inv.result : "");
                                setResultFlag((inv.flag as any) || "Normal");
                              }}
                              className="px-3 py-1.5 rounded-xl border border-teal-200 bg-teal-50 hover:bg-teal-100 text-teal-800 text-xs font-bold transition-all shadow-2xs flex items-center gap-1 cursor-pointer"
                            >
                              <FileText className="w-3.5 h-3.5" />
                              <span>{isReported ? "Edit Result" : "Enter Result"}</span>
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ══════════════════════════════════════════════════════════════════
              TAB 4: AI DIFFERENTIAL DIAGNOSIS & CLINICAL REASONING
              ══════════════════════════════════════════════════════════════════ */}
          {activeTab === "differential" && (
            <div className="space-y-6">
              {/* Prominent Rule 85 Notice */}
              <div className="p-4 rounded-2xl bg-amber-50/70 border border-amber-200 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
                <div className="text-xs">
                  <h4 className="font-extrabold text-amber-900 uppercase tracking-wide">
                    CLINICAL DECISION SUPPORT — REFERENCE ONLY
                  </h4>
                  <p className="text-amber-800/90 mt-0.5 leading-relaxed">
                    AI differential diagnosis is synthesized from the patient&apos;s verified findings using the clinical reasoning engine. It does not replace clinical judgment and is never displayed as a confirmed diagnosis until authenticated by the attending physician.
                  </p>
                </div>
              </div>

              {/* Differential Action Header */}
              <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
                <div>
                  <h3 className="text-xs font-black tracking-wider uppercase text-slate-800 font-heading">
                    EVALUATED DIFFERENTIAL DIAGNOSES ({differentialCandidates.length})
                  </h3>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Select a candidate to confirm as the working diagnosis, rule out, or order suggested diagnostic tests.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleRerunDifferential}
                  disabled={isRerunningDiff}
                  className="px-3.5 py-1.5 rounded-xl border border-purple-200 bg-purple-50 hover:bg-purple-100 text-purple-800 text-xs font-bold transition-all shadow-2xs flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isRerunningDiff ? "animate-spin" : ""}`} />
                  <span>Re-run Diagnostic Engine</span>
                </button>
              </div>

              {/* Candidate Cards */}
              {differentialCandidates.length === 0 ? (
                <div className="p-8 text-center text-slate-400 text-xs bg-white rounded-2xl border border-slate-200">
                  No differential candidates synthesized yet. Click &quot;Re-run Diagnostic Engine&quot; to score candidates based on current patient findings.
                </div>
              ) : (
                <div className="space-y-4">
                  {differentialCandidates.map((cand, idx) => {
                    const isAccepted = cand.clinician_status === "accepted";
                    const isRejected = cand.clinician_status === "rejected" || cand.clinician_status === "ruled_out";
                    const isBusy = actionInProgress === cand.id;

                    return (
                      <div
                        key={cand.id || idx}
                        className={`rounded-2xl border p-5 transition-all shadow-xs bg-white ${
                          isAccepted
                            ? "border-emerald-300 ring-2 ring-emerald-400/20 bg-emerald-50/20"
                            : isRejected
                            ? "border-slate-200 opacity-60 bg-slate-50/50"
                            : "border-slate-200 hover:border-purple-200"
                        }`}
                      >
                        {/* Card Header */}
                        <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-100">
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-purple-100 text-purple-800 font-black text-xs flex items-center justify-center">
                              {idx + 1}
                            </span>
                            <h4 className="text-sm font-extrabold text-slate-900 font-heading">
                              {cand.disease}
                            </h4>
                            <span className="text-[10px] font-black uppercase px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 border border-purple-200">
                              {cand.tier}
                            </span>
                            <span className="text-[10px] font-mono font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                              {cand.display_score}
                            </span>
                          </div>

                          <div className="flex items-center gap-2">
                            {isAccepted && (
                              <span className="text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1">
                                <Check className="w-3 h-3 text-emerald-700" />
                                Working Diagnosis
                              </span>
                            )}
                            {isRejected && (
                              <span className="text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800 border border-rose-200 flex items-center gap-1">
                                <X className="w-3 h-3 text-rose-700" />
                                Ruled Out
                              </span>
                            )}
                            {!isAccepted && !isRejected && (
                              <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                                AI Suggested
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Why Considered Rationale */}
                        <div className="mt-3">
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                            Why Considered
                          </span>
                          <p className="text-xs text-slate-700 leading-relaxed font-medium">
                            {cand.rationale}
                          </p>
                        </div>

                        {/* Supporting vs Contradicting Findings */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3">
                          <div className="p-2.5 rounded-xl bg-emerald-50/40 border border-emerald-100">
                            <span className="text-[10px] font-black text-emerald-800 uppercase tracking-wider block mb-1.5">
                              Supporting Clinical Evidence
                            </span>
                            <div className="flex flex-wrap gap-1">
                              {cand.supporting_findings && cand.supporting_findings.length > 0 ? (
                                cand.supporting_findings.map((f, i) => (
                                  <span
                                    key={i}
                                    className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800 border border-emerald-200"
                                  >
                                    + {f}
                                  </span>
                                ))
                              ) : (
                                <span className="text-[10px] text-slate-400">None documented</span>
                              )}
                            </div>
                          </div>

                          <div className="p-2.5 rounded-xl bg-amber-50/30 border border-amber-100">
                            <span className="text-[10px] font-black text-amber-800 uppercase tracking-wider block mb-1.5">
                              Contradicting / Absent Evidence
                            </span>
                            <div className="flex flex-wrap gap-1">
                              {cand.contradicting_findings && cand.contradicting_findings.length > 0 ? (
                                cand.contradicting_findings.map((f, i) => (
                                  <span
                                    key={i}
                                    className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-amber-100 text-amber-800 border border-amber-200"
                                  >
                                    − {f}
                                  </span>
                                ))
                              ) : (
                                <span className="text-[10px] text-slate-400">No contradictions detected</span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Recommended Confirmation Tests */}
                        <div className="mt-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-2">
                            Recommended Confirmation / Exclusion Tests (1-Click Order)
                          </span>
                          <div className="flex flex-wrap gap-2">
                            {cand.recommended_tests && cand.recommended_tests.length > 0 ? (
                              cand.recommended_tests.map((test, i) => (
                                <button
                                  key={i}
                                  type="button"
                                  onClick={() => handleQuickOrderSuggested(test, cand.disease)}
                                  className="text-[10px] font-bold text-blue-700 bg-white hover:bg-blue-50 px-2.5 py-1 rounded-lg border border-blue-200 transition-colors shadow-2xs flex items-center gap-1 cursor-pointer"
                                  title="Order this test directly into patient's note"
                                >
                                  <Plus className="w-3 h-3 text-blue-600" />
                                  <span>{test}</span>
                                </button>
                              ))
                            ) : (
                              <span className="text-[10px] text-slate-400">Routine follow-up</span>
                            )}
                          </div>
                        </div>

                        {/* First-Line Guideline Management */}
                        {cand.first_line_treatment && (
                          <div className="mt-2.5 text-[11px] text-slate-600">
                            <span className="font-bold text-slate-700">Guideline Treatment: </span>
                            {cand.first_line_treatment}
                          </div>
                        )}

                        {/* Clinician Authentication Buttons */}
                        <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2">
                          <span className="text-[10px] text-slate-400 font-semibold">
                            Clinician Authentication Action
                          </span>

                          <div className="flex items-center gap-2">
                            {!isAccepted && (
                              <button
                                type="button"
                                onClick={() => handleDifferentialAction(cand.id, "accept")}
                                disabled={isBusy}
                                className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1 cursor-pointer disabled:opacity-50"
                              >
                                <Check className="w-3.5 h-3.5" />
                                <span>Accept as Working Diagnosis</span>
                              </button>
                            )}

                            {!isRejected && (
                              <button
                                type="button"
                                onClick={() => handleDifferentialAction(cand.id, "reject")}
                                disabled={isBusy}
                                className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition-all border border-slate-200 flex items-center gap-1 cursor-pointer disabled:opacity-50"
                              >
                                <X className="w-3.5 h-3.5" />
                                <span>Reject / Rule Out</span>
                              </button>
                            )}

                            {(isAccepted || isRejected) && (
                              <button
                                type="button"
                                onClick={() => handleDifferentialAction(cand.id, "accept")}
                                disabled={isBusy}
                                className="text-[10px] text-slate-500 hover:text-slate-800 underline ml-1 cursor-pointer"
                              >
                                Re-evaluate
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* ══════════════════════════════════════════════════════════════════
              RECORD RESULT MODAL / SLIDE-IN
              ══════════════════════════════════════════════════════════════════ */}
          <AnimatePresence>
            {enteringResultForInv && (
              <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/40 backdrop-blur-xs">
                <motion.div
                  initial={{ opacity: 0, scale: 0.95, y: 10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95, y: 10 }}
                  className="bg-white rounded-3xl p-6 max-w-lg w-full shadow-2xl border border-slate-200 space-y-4"
                >
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <div className="flex items-center gap-2">
                      <FlaskConical className="w-5 h-5 text-teal-600" />
                      <div>
                        <h3 className="text-sm font-extrabold text-slate-900 font-heading">
                          Record Investigation Result
                        </h3>
                        <p className="text-[10px] text-slate-500">
                          {enteringResultForInv.name} ({enteringResultForInv.category})
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setEnteringResultForInv(null)}
                      className="p-1 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="block text-[10px] font-bold text-slate-600 uppercase tracking-wider mb-1">
                        Reported Findings & Values
                      </label>
                      <textarea
                        value={resultText}
                        onChange={(e) => setResultText(e.target.value)}
                        placeholder="e.g., Japanese Encephalitis virus IgM in CSF: Positive (Titer 1:160). Or CBC: WBC 8,900, Hb 13.8, Platelets 176,000."
                        rows={4}
                        className="w-full p-3 text-xs leading-relaxed rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-teal-400/30 outline-none font-mono text-slate-800"
                        autoFocus
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[10px] font-bold text-slate-600 uppercase tracking-wider mb-1">
                          Diagnostic Flag
                        </label>
                        <select
                          value={resultFlag}
                          onChange={(e) => setResultFlag(e.target.value as any)}
                          className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-slate-50 focus:bg-white outline-none font-semibold text-slate-800"
                        >
                          <option value="Normal">Normal</option>
                          <option value="Abnormal">Abnormal</option>
                          <option value="Critical">Critical</option>
                        </select>
                      </div>

                      <div className="p-2.5 rounded-xl bg-blue-50/60 border border-blue-100 text-[10px] text-blue-900 leading-tight">
                        <span className="font-bold">Real-time reasoning: </span>
                        Submitting will update the timeline and re-evaluate the AI differential automatically.
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                    <button
                      type="button"
                      onClick={() => setEnteringResultForInv(null)}
                      className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleSubmitInvestigationResult}
                      disabled={isSubmittingResult || !resultText.trim()}
                      className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
                    >
                      {isSubmittingResult ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Updating Differential...</span>
                        </>
                      ) : (
                        <>
                          <Check className="w-3.5 h-3.5" />
                          <span>Submit Result & Update Differential</span>
                        </>
                      )}
                    </button>
                  </div>
                </motion.div>
              </div>
            )}
          </AnimatePresence>

          {/* ── Footer ── */}
          <div className="text-center pt-2 pb-8">
            <p className="text-[10px] text-slate-400 font-medium">
              {(note.body as any)?._meta?.generated_at
                ? `AI Drafted: ${(note.body as any)._meta?.generated_at} · `
                : ""}
              {(note.body as any)?._meta?.note_format || "International Hospital EHR Note"} · DocAssistIQ Clinical Intelligence · Version {note.version}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
