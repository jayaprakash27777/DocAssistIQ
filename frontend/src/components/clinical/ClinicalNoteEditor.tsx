"use client";

import { useEffect, useState, useCallback } from "react";
import { getClinicalNote, updateClinicalNote, ClinicalNoteResponse, ClinicalNoteUpdate, NoteSection } from "@/lib/api";
import FeedbackButtons from "./FeedbackButtons";

const SOAP_STRUCTURE = [
  {
    groupId: "subjective",
    groupLabel: "Subjective",
    sections: [
      { id: "chief_complaint", label: "Chief Complaint" },
      { id: "hpi", label: "History of Present Illness" },
      { id: "past_medical_history", label: "Past Medical History" },
      { id: "medications", label: "Medications" },
      { id: "allergies", label: "Allergies" },
      { id: "family_history", label: "Family History" },
      { id: "social_history", label: "Social History" },
    ]
  },
  {
    groupId: "objective",
    groupLabel: "Objective",
    sections: [
      { id: "examination", label: "Physical Examination" },
      { id: "investigations", label: "Investigations" },
    ]
  },
  {
    groupId: "assessment",
    groupLabel: "Assessment",
    sections: [
      { id: "assessment", label: "Assessment" }
    ]
  },
  {
    groupId: "plan",
    groupLabel: "Plan",
    sections: [
      { id: "plan", label: "Plan" }
    ]
  }
];

export default function ClinicalNoteEditor({ consultationId }: { consultationId: string }) {
  const [note, setNote] = useState<ClinicalNoteResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [body, setBody] = useState<Record<string, NoteSection>>({});
  const [saveTimeout, setSaveTimeout] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    async function loadNote() {
      const result = await getClinicalNote(consultationId);
      if (result.ok) {
        setNote(result.data);
        setBody(result.data.body || {});
      } else {
        setError(result.error?.message || "Failed to load clinical note.");
      }
      setLoading(false);
    }
    loadNote();
  }, [consultationId]);

  const saveNote = useCallback(
    async (updatedBody: Record<string, NoteSection>, currentVersion: number) => {
      setSaving(true);
      setError(null);
      
      const payload: ClinicalNoteUpdate = {
        body: updatedBody,
        version: currentVersion,
      };

      const result = await updateClinicalNote(consultationId, payload);
      
      if (result.ok) {
        setNote(result.data); // Update with new version and status
      } else {
        if (result.error?.code === "OPTIMISTIC_CONCURRENCY_ERROR") {
          setError("Conflict: The note was modified elsewhere. Please refresh.");
        } else {
          setError(result.error?.message || "Failed to save note.");
        }
      }
      setSaving(false);
    },
    [consultationId]
  );

  const handleSectionChange = (sectionId: string, value: string) => {
    const currentSection = body[sectionId] || { text: "", original_ai_text: null, status: "draft" };
    const updatedSection = { ...currentSection, text: value };
    const updatedBody = { ...body, [sectionId]: updatedSection };
    setBody(updatedBody);

    if (saveTimeout) clearTimeout(saveTimeout);
    
    // Auto-save after 1 second of typing
    const timeout = setTimeout(() => {
      if (note) {
        saveNote(updatedBody, note.version);
      }
    }, 1000);
    setSaveTimeout(timeout);
  };

  const handleSectionAccept = (sectionId: string) => {
    const currentSection = body[sectionId];
    if (!currentSection) return;
    const updatedSection = { ...currentSection, status: "accepted" as const };
    const updatedBody = { ...body, [sectionId]: updatedSection };
    setBody(updatedBody);
    if (note) saveNote(updatedBody, note.version);
  };

  const handleSectionRevert = (sectionId: string) => {
    const currentSection = body[sectionId];
    if (!currentSection || !currentSection.original_ai_text) return;
    const updatedSection = { ...currentSection, text: currentSection.original_ai_text, status: "draft" as const };
    const updatedBody = { ...body, [sectionId]: updatedSection };
    setBody(updatedBody);
    if (note) saveNote(updatedBody, note.version);
  };

  const handleExport = async (format: "pdf" | "fhir") => {
    try {
      const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const token = localStorage.getItem("token");
      const url = `${BASE_URL}/api/v1/consultations/${consultationId}/export?format=${format}`;
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      
      if (!res.ok) {
        throw new Error("Failed to export (Ensure note is finalized)");
      }
      
      if (format === "pdf") {
        const text = await res.text();
        // Create a blob and download
        const blob = new Blob([text], { type: "text/markdown" });
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = `consultation_${consultationId}.md`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);
      } else if (format === "fhir") {
        const json = await res.json();
        navigator.clipboard.writeText(JSON.stringify(json, null, 2));
        alert("FHIR JSON copied to clipboard!");
      }
    } catch (err: any) {
      alert(err.message);
    }
  };

  if (loading) return <div className="text-sm text-gray-500 animate-pulse">Loading note...</div>;
  if (!note) return <div className="text-sm text-red-500">{error || "No note found"}</div>;

  return (
    <div className="bg-white border rounded-md shadow-sm flex flex-col h-full overflow-hidden">
      <div className="flex justify-between items-center p-4 border-b bg-gray-50 shrink-0">
        <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          Clinical Note
          {note.is_ai_generated && (
            <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full font-medium border border-blue-200 shadow-sm">
              AI Drafted
            </span>
          )}
        </h2>
        <div className="flex items-center gap-4 text-sm">
          <div className="flex gap-2 mr-2">
            <button 
              onClick={() => handleExport("pdf")}
              className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-1 rounded border border-gray-300 transition-colors"
            >
              Export PDF (MD)
            </button>
            <button 
              onClick={() => handleExport("fhir")}
              className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-1 rounded border border-gray-300 transition-colors"
            >
              Copy FHIR
            </button>
          </div>
          {saving ? (
            <span className="text-blue-600 flex items-center gap-1">
              <span className="w-2 h-2 bg-blue-600 rounded-full animate-ping"></span>
              Saving...
            </span>
          ) : (
            <span className="text-green-600 flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Saved
            </span>
          )}
        </div>
      </div>
      
      {error && (
        <div className="p-3 bg-red-50 text-red-700 text-sm border-b border-red-200">
          {error}
        </div>
      )}

      <div className="p-4 overflow-y-auto flex-1 space-y-8 bg-gray-50/50">
        {SOAP_STRUCTURE.map((group) => (
          <div key={group.groupId} className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
            <div className="bg-gray-50/80 px-4 py-3 border-b border-gray-200">
              <h3 className="font-bold text-gray-800 tracking-wide">{group.groupLabel}</h3>
            </div>
            <div className="p-4 space-y-6">
              {group.sections.map((section) => (
                <div key={section.id} className="space-y-1.5 group/section">
                  <div className="flex justify-between items-center">
                    <label className="block text-[11px] font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2">
                      {section.label}
                      {body[section.id]?.status === "accepted" && (
                        <span className="text-emerald-600 text-[10px] flex items-center gap-0.5 bg-emerald-50 px-1.5 py-0.5 rounded">
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                          </svg>
                          Accepted
                        </span>
                      )}
                      {body[section.id]?.status === "draft" && body[section.id]?.original_ai_text && (
                        <span className="text-blue-600 text-[10px] flex items-center gap-1 bg-blue-50 px-1.5 py-0.5 rounded">
                          AI Draft
                        </span>
                      )}
                    </label>
                    <div className="flex gap-2">
                      {body[section.id]?.status === "draft" && body[section.id]?.original_ai_text && (
                        <FeedbackButtons
                          suggestionId={`note-${consultationId}-${section.id}-${note?.version}`}
                          suggestionType="clinical_note"
                          suggestionContext={{ section: section.id, original_text: body[section.id]?.original_ai_text, edited_text: body[section.id]?.text }}
                          onFeedbackSubmitted={(decision) => {
                            if (decision === "ACCEPT") {
                              handleSectionAccept(section.id);
                            } else if (decision === "REJECT") {
                              handleSectionRevert(section.id);
                            }
                          }}
                        />
                      )}
                    </div>
                  </div>
                  <textarea
                    className={`w-full min-h-[60px] p-3 text-sm text-gray-800 border rounded-lg transition-all resize-y shadow-inner ${
                      body[section.id]?.status === "accepted" 
                        ? "bg-white border-emerald-200 focus:ring-emerald-500 focus:border-emerald-500" 
                        : body[section.id]?.original_ai_text && body[section.id]?.text === body[section.id]?.original_ai_text
                          ? "bg-blue-50/40 border-blue-200 focus:ring-blue-500 focus:border-blue-500"
                          : "bg-gray-50/50 focus:bg-white focus:ring-blue-500 focus:border-blue-500"
                    }`}
                    value={body[section.id]?.text || ""}
                    onChange={(e) => handleSectionChange(section.id, e.target.value)}
                    placeholder={`Enter ${section.label.toLowerCase()}...`}
                  />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
