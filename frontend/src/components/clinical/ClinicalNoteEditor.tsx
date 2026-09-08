"use client";

import { useEffect, useState, useCallback } from "react";
import { getClinicalNote, updateClinicalNote, ClinicalNoteResponse, ClinicalNoteUpdate, NoteSection } from "@/lib/api";

const NOTE_SECTIONS = [
  { id: "chief_complaint", label: "Chief Complaint" },
  { id: "hpi", label: "History of Present Illness" },
  { id: "past_medical_history", label: "Past Medical History" },
  { id: "medications", label: "Medications" },
  { id: "allergies", label: "Allergies" },
  { id: "family_history", label: "Family History" },
  { id: "social_history", label: "Social History" },
  { id: "examination", label: "Physical Examination" },
  { id: "investigations", label: "Investigations" },
  { id: "assessment", label: "Assessment" },
  { id: "plan", label: "Plan" },
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
        <div className="text-sm">
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

      <div className="p-4 overflow-y-auto flex-1 space-y-6">
        {NOTE_SECTIONS.map((section) => (
          <div key={section.id} className="space-y-1 group">
            <div className="flex justify-between items-center">
              <label className="block text-sm font-semibold text-gray-700 tracking-wide uppercase flex items-center gap-2">
                {section.label}
                {body[section.id]?.status === "accepted" && (
                  <span className="text-green-600 text-xs flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Accepted
                  </span>
                )}
                {body[section.id]?.status === "draft" && body[section.id]?.original_ai_text && (
                  <span className="text-blue-600 text-xs flex items-center gap-1">
                    AI Suggestion
                  </span>
                )}
              </label>
              <div className="flex gap-2">
                {body[section.id]?.status === "draft" && body[section.id]?.original_ai_text && (
                  <button 
                    onClick={() => handleSectionAccept(section.id)}
                    className="text-xs px-2 py-1 bg-green-50 text-green-700 rounded hover:bg-green-100 transition-colors"
                  >
                    Accept
                  </button>
                )}
                {body[section.id]?.original_ai_text && body[section.id]?.text !== body[section.id]?.original_ai_text && (
                  <button 
                    onClick={() => handleSectionRevert(section.id)}
                    className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                  >
                    Revert to AI Draft
                  </button>
                )}
              </div>
            </div>
            <textarea
              className={`w-full min-h-[80px] p-3 text-sm text-gray-800 border rounded-md transition-colors resize-y ${
                body[section.id]?.status === "accepted" 
                  ? "bg-white border-green-200 focus:ring-green-500 focus:border-green-500" 
                  : body[section.id]?.original_ai_text && body[section.id]?.text === body[section.id]?.original_ai_text
                    ? "bg-blue-50/30 border-blue-200 focus:ring-blue-500 focus:border-blue-500"
                    : "bg-gray-50 focus:bg-white focus:ring-blue-500 focus:border-blue-500"
              }`}
              value={body[section.id]?.text || ""}
              onChange={(e) => handleSectionChange(section.id, e.target.value)}
              placeholder={`Enter ${section.label.toLowerCase()}...`}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
