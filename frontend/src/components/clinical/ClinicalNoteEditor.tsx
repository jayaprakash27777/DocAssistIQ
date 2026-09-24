/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useClinicalNote, useUpdateClinicalNote } from "@/hooks/useConsultations";
import { NoteSection, getStoredToken } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import FeedbackButtons from "./FeedbackButtons";
import { saveOfflineNoteDraft, getOfflineNoteDraft, clearOfflineNoteDraft, registerNetworkReconnectionSync } from "@/lib/offlineSync";

// ─── Complete SOAP+ Structure (matches backend note_generator.py) ─────────────
const SOAP_GROUPS = [
  {
    groupId: "subjective",
    groupLabel: "Subjective",
    color: "blue",
    icon: "🗣",
    sections: [
      { id: "chief_complaint",     label: "Chief Complaint",              icon: "💬", required: true },
      { id: "hpi",                 label: "History of Present Illness",    icon: "📋", required: true },
      { id: "review_of_systems",   label: "Review of Systems",             icon: "🔍", required: false },
      { id: "past_medical_history",label: "Past Medical History",          icon: "📂", required: false },
      { id: "surgical_history",    label: "Surgical History",              icon: "🔬", required: false },
      { id: "medications",         label: "Current Medications",           icon: "💊", required: false },
      { id: "allergies",           label: "Allergies",                     icon: "⚠️", required: false },
      { id: "family_history",      label: "Family History",                icon: "👨‍👩‍👧", required: false },
      { id: "social_history",      label: "Social & Travel History",       icon: "🌍", required: false },
    ],
  },
  {
    groupId: "objective",
    groupLabel: "Objective",
    color: "emerald",
    icon: "🩺",
    sections: [
      { id: "vitals",              label: "Vital Signs",                   icon: "❤️", required: true },
      { id: "physical_examination",label: "Physical Examination",          icon: "🏥", required: true },
      { id: "investigations",      label: "Investigations & Results",      icon: "🧪", required: false, dropZone: true },
    ],
  },
  {
    groupId: "assessment_plan",
    groupLabel: "Assessment & Plan",
    color: "purple",
    icon: "📝",
    sections: [
      { id: "differential_diagnosis", label: "Differential Diagnosis",    icon: "🔭", required: false },
      { id: "assessment",          label: "Assessment",                    icon: "✅", required: true, clinicianFill: true },
      { id: "plan",                label: "Management Plan",               icon: "🎯", required: true, clinicianFill: true, dropZone: true },
    ],
  },
  {
    groupId: "followup",
    groupLabel: "Follow-Up & Safety",
    color: "amber",
    icon: "🔔",
    sections: [
      { id: "follow_up_plan",      label: "Follow-Up Plan",               icon: "📅", required: false },
      { id: "safety_net",          label: "Safety Net Advice",             icon: "🚨", required: false },
    ],
  },
];

// Color config per group
const GROUP_COLORS: Record<string, { border: string; bg: string; text: string; badge: string; header: string }> = {
  blue:    { border: "border-blue-200",    bg: "bg-blue-50/30",   text: "text-blue-700",    badge: "bg-blue-100 text-blue-700 border-blue-200",    header: "from-blue-50 to-transparent border-blue-100" },
  emerald: { border: "border-emerald-200", bg: "bg-emerald-50/20",text: "text-emerald-700", badge: "bg-emerald-100 text-emerald-700 border-emerald-200", header: "from-emerald-50 to-transparent border-emerald-100" },
  purple:  { border: "border-purple-200",  bg: "bg-purple-50/20", text: "text-purple-700",  badge: "bg-purple-100 text-purple-700 border-purple-200",  header: "from-purple-50 to-transparent border-purple-100" },
  amber:   { border: "border-amber-200",   bg: "bg-amber-50/20",  text: "text-amber-700",   badge: "bg-amber-100 text-amber-700 border-amber-200",    header: "from-amber-50 to-transparent border-amber-100" },
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
  BP: "🩸", HR: "❤️", RR: "🫁", Temp: "🌡️", SpO2: "💨",
  Weight: "⚖️", Height: "📏", BMI: "📊", GCS: "🧠",
};

const VITAL_UNITS: Record<string, string> = {
  BP: "mmHg", HR: "bpm", RR: "/min", Temp: "°C", SpO2: "%",
  Weight: "kg", Height: "cm", BMI: "kg/m²", GCS: "/15",
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
    label: "+ 14-Point Negative ROS",
    text: "Constitutional: Negative for fever, chills, night sweats, or unintentional weight loss.\nEyes: Negative for acute vision loss, blurriness, or eye pain.\nENT: Negative for sore throat, dysphagia, rhinorrhea, or epistaxis.\nCardiovascular: Negative for palpitations, orthopnea, or lower extremity edema.\nRespiratory: Negative for shortness of breath, wheezing, or hemoptysis.\nGastrointestinal: Negative for nausea, vomiting, hematemesis, melena, or hematochezia.\nGenitourinary: Negative for dysuria, frequency, urgency, or gross hematuria.\nMusculoskeletal: Negative for joint swelling, warmth, or severe myalgias.\nSkin: Negative for acute rashes, petechiae, or non-healing ulcers.\nNeurological: Negative for syncopal episodes, seizures, or focal sensory/motor deficits.\nPsychiatric: Negative for acute suicidal ideation, hallucinations, or severe agitation.",
  },
  physical_examination: {
    label: "+ Normal Exam WNL",
    text: "General: Patient is alert, attentive, and oriented x 4. Appears comfortable, in no acute distress.\nHEENT: Normocephalic, atraumatic. Pupils equal, round, and reactive to light. Oropharynx clear with moist mucous membranes.\nCardiovascular: Normal S1 and S2 present. Regular rate and rhythm. No murmurs, rubs, or gallops auscultated. Peripheral pulses 2+ symmetric.\nRespiratory: Lungs clear to auscultation bilaterally. Vesicular breath sounds throughout. No wheezes, rales, or rhonchi.\nAbdomen: Soft, non-distended, non-tender to palpation throughout all quadrants. Active bowel sounds. No guarding, rigidity, or rebound.\nExtremities: Warm and well-perfused. No cyanosis, clubbing, or peripheral edema.\nNeurological: Cranial nerves II-XII grossly intact. Normal muscle bulk and 5/5 tone throughout all extremities. Sensation intact.",
  },
  safety_net: {
    label: "+ Red Flag Precautions",
    text: "Safety Net & Return Precautions Discussed with Patient:\n1. Emergency Return: Return immediately to the Emergency Department or dial emergency services if experiencing worsening acute pain, chest pressure or pain radiating to arm/jaw, acute shortness of breath, high persistent fevers (>38.5°C), persistent vomiting with inability to tolerate oral fluids, confusion, focal weakness, or syncope.\n2. Scheduled Follow-up: Follow up in clinic in 48 to 72 hours for reassessment if symptoms fail to improve or if pending laboratory results indicate further intervention.\n3. Medication Compliance: Take all prescribed medications as instructed and immediately report any allergic symptoms or unexpected reactions.",
  },
};

function VitalsGrid({ text, onChange }: { text: any; onChange: (v: string) => void }) {
  const safeText = typeof text === "string" ? text : String(text ?? "");
  const vitals = parseVitals(safeText);
  const fields = ["BP", "HR", "RR", "Temp", "SpO2", "Weight", "Height", "BMI", "GCS"];
  const [local, setLocal] = useState<Record<string, string>>(vitals);

  useEffect(() => {
    setLocal(parseVitals(safeText));
  }, [text]);

  const commit = (updated: Record<string, string>) => {
    const out = Object.entries(updated)
      .filter(([, v]) => v && v !== "Not documented")
      .map(([k, v]) => `${k}: ${v}`)
      .join(" | ");
    onChange(out || safeText);
  };

  return (
    <div className="grid grid-cols-3 md:grid-cols-5 gap-2 mt-1">
      {fields.map(f => {
        const val = local[f] || "";
        const abnormal = isAbnormalVital(f, val);

        return (
          <div 
            key={f} 
            className={`relative rounded-xl border shadow-2xs overflow-hidden transition-all ${
              abnormal 
                ? "bg-amber-50/70 border-amber-300 ring-2 ring-amber-400/20" 
                : "bg-white border-slate-200 hover:border-blue-300"
            }`}
          >
            <div className="flex items-center justify-between px-2.5 pt-2 pb-1">
              <div className="flex items-center gap-1">
                <span className="text-xs">{VITAL_ICONS[f] || "📋"}</span>
                <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">{f}</span>
              </div>
              <div className="flex items-center gap-1">
                {abnormal && (
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" title="Outside standard reference range" />
                )}
                <span className="text-[9px] font-mono text-slate-400 font-semibold">{VITAL_UNITS[f]}</span>
              </div>
            </div>
            <input
              type="text"
              value={val}
              onChange={e => {
                const updated = { ...local, [f]: e.target.value };
                setLocal(updated);
                commit(updated);
              }}
              placeholder="—"
              className={`w-full px-2.5 pb-2 text-sm font-semibold outline-none bg-transparent placeholder:text-slate-300 placeholder:font-normal ${
                abnormal ? "text-amber-900" : "text-slate-800"
              }`}
            />
          </div>
        );
      })}
    </div>
  );
}

// ─── Section textarea with drop zone ──────────────────────────────────────────
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
  section: { id: string; label: string; icon: string; required?: boolean; clinicianFill?: boolean };
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
      ref.current.style.height = ref.current.scrollHeight + "px";
    }
  }, [value]);

  return (
    <div
      className={`relative rounded-xl transition-all duration-200 ${
        isDragOver
          ? "ring-4 ring-blue-400/40 bg-blue-50/80 shadow-[0_0_20px_rgba(59,130,246,0.25)]"
          : ""
      }`}
    >
      {isDropZone && (
        <div className={`absolute -top-2 -right-2 text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full z-10 transition-all ${
          isDragOver
            ? "bg-blue-500 text-white shadow-lg scale-110"
            : "bg-slate-100 text-slate-400 border border-slate-200"
        }`}>
          Drop zone
        </div>
      )}
      <textarea
        ref={ref}
        value={value}
        onChange={e => {
          onChange(e.target.value);
          if (ref.current) {
            ref.current.style.height = "auto";
            ref.current.style.height = ref.current.scrollHeight + "px";
          }
        }}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        placeholder={
          clinicianFill
            ? `Clinician completes ${section.label.toLowerCase()} here...`
            : isDropZone
            ? `Drag AI-suggested ${section.label.toLowerCase()} here, or type directly...`
            : `Enter ${section.label.toLowerCase()}...`
        }
        className={`w-full min-h-[60px] p-4 text-sm leading-relaxed rounded-xl border resize-none outline-none shadow-sm transition-all font-mono ${
          isDragOver
            ? "bg-blue-50 border-blue-400 text-blue-900"
            : clinicianFill
            ? "bg-amber-50/50 border-amber-200 text-slate-800 focus:ring-2 focus:ring-amber-400/40 focus:border-amber-300 focus:bg-white"
            : "bg-slate-50 border-slate-200 text-slate-800 focus:ring-2 focus:ring-blue-400/30 focus:border-blue-300 focus:bg-white hover:bg-white"
        }`}
      />
    </div>
  );
}

// ─── Safe text extraction — handles plain strings, NoteSection objects, or null ─
function getSectionText(val: any): string {
  if (!val) return "";
  if (typeof val === "string") return val;
  if (typeof val?.text === "string") return val.text;
  if (val?.text != null) return String(val.text);
  return "";
}

// Normalize body from server — ensures every value is a proper NoteSection object
function normalizeBody(raw: Record<string, any>): Record<string, NoteSection> {
  const out: Record<string, NoteSection> = {};
  for (const [key, val] of Object.entries(raw)) {
    if (key.startsWith("_")) continue; // skip _meta etc.
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

// ─── Main Component ────────────────────────────────────────────────────────────
export default function ClinicalNoteEditor({ consultationId }: { consultationId: string }) {
  const { data: note, isLoading, error: fetchError } = useClinicalNote(consultationId);
  const updateMutation = useUpdateClinicalNote(consultationId);
  const [body, setBody] = useState<Record<string, NoteSection>>({});
  const [saveTimeout, setSaveTimeout] = useState<NodeJS.Timeout | null>(null);
  const [dragOverSection, setDragOverSection] = useState<string | null>(null);
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());
  const [copiedFull, setCopiedFull] = useState(false);
  const [copiedSectionId, setCopiedSectionId] = useState<string | null>(null);

  const toggleAllGroups = () => {
    if (collapsedGroups.size === SOAP_GROUPS.length) {
      setCollapsedGroups(new Set());
    } else {
      setCollapsedGroups(new Set(SOAP_GROUPS.map(g => g.groupId)));
    }
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

  const handleCopyFullNote = () => {
    const lines: string[] = [
      `# DOCASSISTIQ CLINICAL NOTE (SOAP+)`,
      `Consultation ID: ${consultationId}`,
      `Date: ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`,
      `Status: ${note?.status?.toUpperCase() || "DRAFT"}`,
      `----------------------------------------\n`
    ];

    SOAP_GROUPS.forEach(group => {
      lines.push(`## ${group.groupLabel.toUpperCase()}`);
      group.sections.forEach(sec => {
        const text = getSectionText(body[sec.id]).trim();
        if (text) {
          lines.push(`### ${sec.label}`);
          lines.push(text);
          lines.push("");
        }
      });
    });

    navigator.clipboard.writeText(lines.join("\n"));
    setCopiedFull(true);
    setTimeout(() => setCopiedFull(false), 2000);
  };

  const saveNote = useCallback(
    (updatedBody: Record<string, NoteSection>, currentVersion: number) => {
      updateMutation.mutate({ body: updatedBody, version: currentVersion });
    },
    [updateMutation]
  );

  useEffect(() => {
    if (note?.body) {
      setBody(normalizeBody(note.body as Record<string, any>));
    } else {
      getOfflineNoteDraft(consultationId).then(draft => {
        if (draft?.body) setBody(normalizeBody(draft.body));
      });
    }
  }, [note?.version, consultationId]);

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
    const t = setTimeout(() => { if (note) saveNote(updated, note.version); }, 1000);
    setSaveTimeout(t);
  };

  const handleDrop = (e: React.DragEvent, sectionId: string) => {
    e.preventDefault();
    setDragOverSection(null);
    const dragged = e.dataTransfer.getData("text/plain");
    if (!dragged) return;
    const cur = getSectionText(body[sectionId]);
    // Format dropped investigation nicely
    const formatted = cur
      ? `${cur}\n\n[AI Suggested] ${dragged}`
      : `[AI Suggested] ${dragged}`;
    handleChange(sectionId, formatted);
    // Flash visual feedback
    const el = document.getElementById(`section-${sectionId}`);
    if (el) {
      el.classList.add("ring-4", "ring-green-400", "bg-green-50");
      setTimeout(() => el.classList.remove("ring-4", "ring-green-400", "bg-green-50"), 1200);
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

  const handleExport = async (format: "pdf" | "fhir") => {
    try {
      const BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/api\/v1\/?$/, "");
      const token = getStoredToken() || (typeof window !== "undefined" ? (localStorage.getItem("access_token") || localStorage.getItem("token")) : null) || "";
      const url = `${BASE_URL}/api/v1/consultations/${consultationId}/export?format=${format}`;
      const res = await fetch(url, { headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) } });
      if (!res.ok) throw new Error("Failed to export — ensure note is finalised");
      if (format === "pdf") {
        const blob = await res.blob();
        const blobUrl = URL.createObjectURL(new Blob([blob], { type: "application/pdf" }));
        const a = Object.assign(document.createElement("a"), {
          href: blobUrl,
          download: `consultation_${consultationId}.pdf`,
        });
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(blobUrl);
      } else {
        const fhirData = await res.json();
        const fhirBlob = new Blob([JSON.stringify(fhirData, null, 2)], { type: "application/json" });
        const blobUrl = URL.createObjectURL(fhirBlob);
        const a = Object.assign(document.createElement("a"), {
          href: blobUrl,
          download: `consultation_${consultationId}_fhir_r4.json`,
        });
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(blobUrl);
        navigator.clipboard.writeText(JSON.stringify(fhirData, null, 2));
        alert("HL7 FHIR R4 Bundle downloaded and copied to clipboard!");
      }
    } catch (err: any) { alert(err.message); }
  };

  // Completeness calculation — use safe getter to avoid trim() errors on non-string values
  const allSections = SOAP_GROUPS.flatMap(g => g.sections);
  const filled = allSections.filter(s => getSectionText(body[s.id]).trim().length > 0).length;
  const total = allSections.length;
  const pct = Math.round((filled / total) * 100);

  if (isLoading) return (
    <div className="flex flex-col items-center justify-center h-48 gap-3">
      <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      <span className="text-sm text-slate-500 font-medium">Loading clinical note...</span>
    </div>
  );
  if (fetchError || !note) return (
    <div className="p-6 bg-red-50 rounded-2xl border border-red-200 text-red-700 text-sm font-medium">
      {fetchError?.message || "No note found for this consultation."}
    </div>
  );

  const saving = updateMutation.isPending;

  return (
    <div className="bg-white rounded-3xl shadow-[0_12px_44px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.95)] border border-slate-200/80 flex flex-col h-full overflow-hidden">

      {/* ── Hospital Header ── */}
      <div className="shrink-0 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-800 px-6 py-4.5 border-b border-white/10 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3.5">
            <div className="w-9 h-9 bg-white/10 rounded-2xl flex items-center justify-center text-lg border border-white/15 shadow-inner">🏥</div>
            <div>
              <h2 className="text-white font-black text-base tracking-tight leading-none">CLINICAL NOTE</h2>
              <p className="text-slate-400 text-[10px] font-bold mt-1 uppercase tracking-widest">
                Extended SOAP+ · International Hospital Standard
                {note.is_ai_generated && (
                  <span className="ml-2 bg-blue-500/25 text-blue-300 border border-blue-400/40 px-2 py-0.5 rounded-full font-extrabold shadow-xs">
                    AI Drafted
                  </span>
                )}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {/* Completeness ring */}
            <div className="flex items-center gap-2.5 bg-white/5 px-3 py-1.5 rounded-2xl border border-white/10">
              <svg className="w-8 h-8 -rotate-90 filter drop-shadow-sm" viewBox="0 0 32 32">
                <circle cx="16" cy="16" r="12" fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="3" />
                <circle
                  cx="16" cy="16" r="12" fill="none"
                  stroke={pct >= 80 ? "#34d399" : pct >= 50 ? "#fbbf24" : "#60a5fa"}
                  strokeWidth="3.5" strokeLinecap="round"
                  strokeDasharray={`${2 * Math.PI * 12}`}
                  strokeDashoffset={`${2 * Math.PI * 12 * (1 - pct / 100)}`}
                  style={{ transition: "stroke-dashoffset 0.6s cubic-bezier(0.16, 1, 0.3, 1)" }}
                />
              </svg>
              <div className="text-right">
                <div className="text-white font-black text-sm leading-none">{pct}%</div>
                <div className="text-slate-400 text-[9px] font-bold uppercase tracking-wider">Complete</div>
              </div>
            </div>
            {/* Save status */}
            <div className={`flex items-center gap-1.5 text-[10px] font-extrabold uppercase tracking-widest ${saving ? "text-yellow-400" : "text-emerald-400"}`}>
              {saving ? (
                <><span className="w-2 h-2 bg-yellow-400 rounded-full animate-ping" />Saving</>
              ) : (
                <><span className="w-2 h-2 bg-emerald-400 rounded-full shadow-xs" />Saved</>
              )}
            </div>
            {/* Actions */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleCopyFullNote}
                title="Copy entire formatted SOAP note for hospital EHR"
                className="text-xs font-bold text-slate-100 hover:text-white bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-xl border border-white/15 transition-all shadow-sm hover:scale-105 active:scale-95 flex items-center gap-1.5"
              >
                {copiedFull ? (
                  <>
                    <span className="text-emerald-400 font-extrabold">✓</span>
                    <span className="text-emerald-300">Copied!</span>
                  </>
                ) : (
                  <>📋 Copy Note</>
                )}
              </button>
              <button
                type="button"
                onClick={toggleAllGroups}
                title="Expand or collapse all SOAP categories"
                className="text-xs font-bold text-slate-200 hover:text-white bg-white/10 hover:bg-white/20 px-2.5 py-1.5 rounded-xl border border-white/15 transition-all shadow-sm hover:scale-105 active:scale-95"
              >
                ↕️ Toggle
              </button>
              <button
                onClick={() => handleExport("pdf")}
                className="text-xs font-bold text-slate-200 hover:text-white bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-xl border border-white/15 transition-all shadow-sm hover:scale-105 active:scale-95"
              >
                📄 Export
              </button>
              <button
                onClick={() => handleExport("fhir")}
                className="text-xs font-bold text-slate-200 hover:text-white bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-xl border border-white/15 transition-all shadow-sm hover:scale-105 active:scale-95"
              >
                🔗 FHIR
              </button>
            </div>
          </div>
        </div>
        {/* Progress bar */}
        <div className="mt-3.5 h-1.5 bg-white/10 rounded-full overflow-hidden">
          <motion.div
            className={`h-full rounded-full shadow-sm ${pct >= 80 ? "bg-gradient-to-r from-emerald-400 to-teal-400" : pct >= 50 ? "bg-gradient-to-r from-amber-400 to-yellow-400" : "bg-gradient-to-r from-blue-400 to-indigo-400"}`}
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
        </div>
      </div>

      {/* ── Drag instruction banner ── */}
      <div className="shrink-0 bg-gradient-to-r from-blue-50/90 via-indigo-50/40 to-transparent border-b border-indigo-100/60 px-6 py-2.5 flex items-center gap-2.5">
        <span className="text-blue-600 text-sm">💡</span>
        <p className="text-[11px] text-blue-900 font-semibold tracking-wide">
          Drag AI-suggested investigations or diagnoses directly into any section below. Drop zones highlighted in blue.
        </p>
      </div>

      {/* ── Note Body ── */}
      <div className="flex-1 overflow-y-auto bg-slate-50/50 p-6">
        <div className="max-w-4xl mx-auto space-y-6 pb-24">
          {SOAP_GROUPS.map((group, gIdx) => {
            const colors = GROUP_COLORS[group.color];
            const isCollapsed = collapsedGroups.has(group.groupId);

            return (
              <motion.div
                key={group.groupId}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: gIdx * 0.08, duration: 0.4 }}
                className={`rounded-2xl border ${colors.border} overflow-hidden shadow-sm bg-white`}
              >
                {/* Group Header */}
                <button
                  onClick={() => setCollapsedGroups(prev => {
                    const next = new Set(prev);
                    if (next.has(group.groupId)) next.delete(group.groupId);
                    else next.add(group.groupId);
                    return next;
                  })}
                  className={`w-full flex items-center justify-between px-5 py-3.5 bg-gradient-to-r ${colors.header} border-b ${colors.border} hover:brightness-95 transition-all`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-lg">{group.icon}</span>
                    <div className="text-left">
                      <h3 className={`font-black text-sm ${colors.text} uppercase tracking-widest`}>
                        {group.groupLabel}
                      </h3>
                      <p className="text-[10px] text-slate-500 mt-0.5">
                        {group.sections.filter(s => getSectionText(body[s.id]).trim().length > 0).length} / {group.sections.length} sections filled
                      </p>
                    </div>
                  </div>
                  <motion.span
                    animate={{ rotate: isCollapsed ? -90 : 0 }}
                    transition={{ duration: 0.2 }}
                    className={`text-lg ${colors.text} opacity-60`}
                  >
                    ▾
                  </motion.span>
                </button>

                {/* Sections */}
                <AnimatePresence>
                  {!isCollapsed && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.25 }}
                      className="overflow-hidden"
                    >
                      <div className="divide-y divide-slate-100">
                        {group.sections.map((section, sIdx) => {
                          const sectionData = body[section.id];
                          const text = getSectionText(sectionData);
                          const isAiDraft = sectionData?.status === "draft" && !!(sectionData?.original_ai_text);
                          const isAccepted = sectionData?.status === "accepted";
                          const isDragOver = dragOverSection === section.id;

                          return (
                            <motion.div
                              key={section.id}
                              id={`section-${section.id}`}
                              initial={{ opacity: 0, x: -8 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: sIdx * 0.04, duration: 0.3 }}
                              className="p-5 transition-colors group"
                            >
                              {/* Section header row */}
                              <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="text-base">{section.icon}</span>
                                  <label className="font-bold text-sm text-slate-800 tracking-tight">
                                    {section.label}
                                  </label>
                                  {section.required && (
                                    <span className="text-red-500 text-[10px] font-black">*</span>
                                  )}
                                  {/* Status badges */}
                                  {isAccepted && (
                                    <span className="text-[9px] font-black uppercase tracking-widest bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full flex items-center gap-1 shadow-2xs">
                                      ✓ Accepted
                                    </span>
                                  )}
                                  {isAiDraft && !isAccepted && (
                                    <span className="text-[9px] font-black uppercase tracking-widest bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-full animate-pulse shadow-2xs">
                                      ✨ AI Draft
                                    </span>
                                  )}
                                  {(section as any).clinicianFill && (
                                    <span className="text-[9px] font-black uppercase tracking-widest bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full shadow-2xs">
                                      Clinician
                                    </span>
                                  )}
                                  {/* Smart Boilerplate chip if empty */}
                                  {SECTION_BOILERPLATES[section.id] && !text.trim() && (
                                    <button
                                      type="button"
                                      onClick={() => handleInsertBoilerplate(section.id, SECTION_BOILERPLATES[section.id].text)}
                                      className="text-[10px] font-bold text-teal-700 bg-teal-50 hover:bg-teal-100 px-2.5 py-0.5 rounded-lg border border-teal-200 transition-all shadow-2xs flex items-center gap-1 active:scale-95"
                                      title="Insert standard normal boilerplate"
                                    >
                                      {SECTION_BOILERPLATES[section.id].label}
                                    </button>
                                  )}
                                </div>

                                {/* Section actions */}
                                <div className="flex items-center gap-1.5 opacity-90 group-hover:opacity-100 transition-opacity">
                                  {text && (
                                    <button
                                      type="button"
                                      onClick={() => handleCopySection(section.id, text)}
                                      title="Copy section"
                                      className="text-[10px] font-bold text-slate-600 hover:text-slate-800 bg-slate-50 hover:bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200 shadow-2xs transition-all flex items-center gap-1"
                                    >
                                      {copiedSectionId === section.id ? (
                                        <span className="text-emerald-600 font-extrabold">✓ Copied</span>
                                      ) : (
                                        <>📋 Copy</>
                                      )}
                                    </button>
                                  )}
                                  {isAiDraft && (
                                    <>
                                      <button
                                        type="button"
                                        onClick={() => handleAccept(section.id)}
                                        className="text-[10px] font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 px-2.5 py-1 rounded-lg border border-emerald-200 transition-all shadow-2xs"
                                      >
                                        ✓ Accept
                                      </button>
                                      <button
                                        type="button"
                                        onClick={() => handleRevert(section.id)}
                                        className="text-[10px] font-bold text-slate-600 bg-slate-50 hover:bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200 transition-all shadow-2xs"
                                      >
                                        ↩ Revert
                                      </button>
                                    </>
                                  )}
                                </div>
                              </div>

                              {/* ── Vitals: special structured grid ── */}
                              {section.id === "vitals" ? (
                                <div>
                                  <VitalsGrid text={text} onChange={v => handleChange("vitals", v)} />
                                  <textarea
                                    className="mt-2 w-full min-h-[36px] p-3 text-xs leading-relaxed rounded-xl border border-slate-200 bg-slate-50 text-slate-600 resize-none outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-300 focus:bg-white transition-all font-mono"
                                    value={text}
                                    onChange={e => handleChange("vitals", e.target.value)}
                                    placeholder="Full vitals text (auto-updates grid above): BP: 120/80 | HR: 72 | Temp: 37.2°C | SpO2: 98% | RR: 16 | Weight: 70kg | Height: 175cm"
                                    rows={1}
                                  />
                                </div>
                              ) : (
                                /* ── Standard section field ── */
                                <SectionField
                                  section={section}
                                  value={text}
                                  onChange={v => handleChange(section.id, v)}
                                  isDragOver={isDragOver}
                                  onDragOver={e => { e.preventDefault(); setDragOverSection(section.id); }}
                                  onDragLeave={e => { e.preventDefault(); setDragOverSection(null); }}
                                  onDrop={e => handleDrop(e, section.id)}
                                  isDropZone={(section as any).dropZone}
                                  clinicianFill={(section as any).clinicianFill}
                                />
                              )}

                              {/* AI feedback buttons */}
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
                                      onFeedbackSubmitted={decision => {
                                        if (decision === "ACCEPT") handleAccept(section.id);
                                        else if (decision === "REJECT") handleRevert(section.id);
                                      }}
                                    />
                                  </motion.div>
                                )}
                              </AnimatePresence>
                            </motion.div>
                          );
                        })}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}

          {/* Note footer */}
          <div className="text-center pt-2 pb-8">
            <p className="text-[10px] text-slate-400 font-medium">
              {(note.body as any)?._meta?.generated_at
                ? `AI Drafted: ${(note.body as any)._meta?.generated_at} · `
                : ""}
              {(note.body as any)?._meta?.note_format || "Extended SOAP+ v2"} ·
              DocAssistIQ Clinical Note System · Version {note.version}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
