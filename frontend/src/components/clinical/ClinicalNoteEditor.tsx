/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useClinicalNote, useUpdateClinicalNote } from "@/hooks/useConsultations";
import { NoteSection } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
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
  const { data: note, isLoading, error: fetchError } = useClinicalNote(consultationId);
  const updateMutation = useUpdateClinicalNote(consultationId);
  const [body, setBody] = useState<Record<string, NoteSection>>({});
  const [saveTimeout, setSaveTimeout] = useState<NodeJS.Timeout | null>(null);
  const [dragOverSection, setDragOverSection] = useState<string | null>(null);

  // Sync body state when data loads or changes from server
  useEffect(() => {
    if (note && note.body) {
      setBody(note.body);
    }
  }, [note?.version]); // Only sync when version changes from server to avoid clobbering typing

  const saveNote = useCallback(
    (updatedBody: Record<string, NoteSection>, currentVersion: number) => {
      updateMutation.mutate({
        body: updatedBody,
        version: currentVersion,
      });
    },
    [updateMutation]
  );

  const handleSectionChange = (sectionId: string, value: string, element?: HTMLTextAreaElement) => {
    const currentSection = body[sectionId] || { text: "", original_ai_text: null, status: "draft" };
    const updatedSection = { ...currentSection, text: value };
    const updatedBody = { ...body, [sectionId]: updatedSection };
    setBody(updatedBody);

    if (element) {
      element.style.height = 'auto';
      element.style.height = element.scrollHeight + 'px';
    }

    if (saveTimeout) clearTimeout(saveTimeout);
    
    // Auto-save after 1 second of typing
    const timeout = setTimeout(() => {
      if (note) {
        saveNote(updatedBody, note.version);
      }
    }, 1000);
    setSaveTimeout(timeout);
  };

  const handleDragOver = (e: React.DragEvent, sectionId: string) => {
    e.preventDefault();
    setDragOverSection(sectionId);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOverSection(null);
  };

  const handleDrop = (e: React.DragEvent, sectionId: string, element: HTMLTextAreaElement) => {
    e.preventDefault();
    setDragOverSection(null);
    
    const draggedText = e.dataTransfer.getData("text/plain");
    if (draggedText) {
      const currentText = body[sectionId]?.text || "";
      const newValue = currentText ? `${currentText}\n${draggedText}` : draggedText;
      handleSectionChange(sectionId, newValue, element);
    }
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

  if (isLoading) return <div className="text-sm text-[var(--text-tertiary)] animate-pulse">Loading note...</div>;
  if (fetchError || !note) return <div className="text-sm text-[var(--color-danger-500)]">{fetchError?.message || "No note found"}</div>;
  const saving = updateMutation.isPending;
  const error = updateMutation.isError ? updateMutation.error.message : null;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-[var(--border-default)] flex flex-col h-full overflow-hidden">
      <div className="flex justify-between items-center p-5 border-b border-[var(--border-default)] bg-[var(--surface-sunken)] shrink-0">
        <h2 className="text-lg font-bold font-heading text-[var(--text-primary)] flex items-center gap-3">
          Clinical Note
          {note.is_ai_generated && (
            <span className="bg-[var(--color-primary-50)] text-[var(--color-primary-700)] text-[0.65rem] uppercase tracking-widest px-2 py-0.5 rounded-full font-bold border border-[var(--color-primary-200)] shadow-sm">
              AI Drafted
            </span>
          )}
        </h2>
        <div className="flex items-center gap-4 text-sm">
          <div className="flex gap-2 mr-2">
            <button 
              onClick={() => handleExport("pdf")}
              className="text-xs font-bold text-[var(--text-secondary)] hover:text-[var(--text-primary)] bg-white hover:bg-[var(--surface-raised)] px-3 py-1.5 rounded-lg border border-[var(--border-default)] transition-all shadow-sm"
            >
              Export PDF
            </button>
            <button 
              onClick={() => handleExport("fhir")}
              className="text-xs font-bold text-[var(--text-secondary)] hover:text-[var(--text-primary)] bg-white hover:bg-[var(--surface-raised)] px-3 py-1.5 rounded-lg border border-[var(--border-default)] transition-all shadow-sm"
            >
              Copy FHIR
            </button>
          </div>
          {saving ? (
            <span className="text-[var(--color-primary-600)] flex items-center gap-2 text-xs font-bold uppercase tracking-wider">
              <span className="w-2 h-2 bg-[var(--color-primary-500)] rounded-full animate-ping"></span>
              Saving...
            </span>
          ) : (
            <span className="text-[var(--color-success-600)] flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
              Saved
            </span>
          )}
        </div>
      </div>
      
      {error && (
        <div className="p-3 bg-[var(--color-danger-50)] text-[var(--color-danger-700)] text-sm border-b border-[var(--color-danger-200)] font-medium">
          {error}
        </div>
      )}

      <div className="p-8 overflow-y-auto flex-1 bg-white">
        <div className="max-w-3xl mx-auto space-y-12 pb-20">
          {SOAP_STRUCTURE.map((group, groupIdx) => (
            <motion.div 
              key={group.groupId} 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: note.is_ai_generated ? groupIdx * 0.15 : 0, duration: 0.5 }}
              className="space-y-6"
            >
              <h3 className="text-2xl font-bold font-heading text-[var(--text-primary)] border-b-2 border-[var(--surface-sunken)] pb-2 flex items-center gap-2">
                {group.groupLabel}
              </h3>
              
              <div className="space-y-8">
                {group.sections.map((section, sectionIdx) => {
                  const isAiDraft = body[section.id]?.status === "draft" && body[section.id]?.original_ai_text;
                  const isAccepted = body[section.id]?.status === "accepted";
                  
                  return (
                  <motion.div 
                    key={section.id} 
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: note.is_ai_generated ? (groupIdx * 0.15) + (sectionIdx * 0.1) : 0 }}
                    className="space-y-3 group/section relative"
                  >
                    <div className="flex justify-between items-end">
                      <label className="block text-sm font-bold text-[var(--text-secondary)] flex items-center gap-2">
                        {section.label}
                        {isAccepted && (
                          <span className="text-[var(--color-success-700)] text-[10px] uppercase tracking-widest flex items-center gap-1 bg-[var(--color-success-50)] px-2 py-0.5 rounded-full border border-[var(--color-success-200)]">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                            </svg>
                            Accepted
                          </span>
                        )}
                        {isAiDraft && (
                          <span className="text-[var(--color-primary-700)] text-[10px] uppercase tracking-widest flex items-center gap-1 bg-[var(--color-primary-50)] px-2 py-0.5 rounded-full border border-[var(--color-primary-200)] relative overflow-hidden">
                            <span className="absolute inset-0 bg-white/40 w-full h-full transform -skew-x-12 animate-shimmer" />
                            AI Draft
                          </span>
                        )}
                      </label>
                      <AnimatePresence>
                        {isAiDraft && (
                          <motion.div 
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            className="flex gap-2"
                          >
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
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                    <div className="relative">
                      {isAiDraft && (
                        <div className="absolute -inset-0.5 bg-gradient-to-r from-[var(--color-primary-200)] to-[var(--color-primary-400)] rounded-xl blur opacity-30 animate-pulse-slow pointer-events-none" />
                      )}
                      <textarea
                        className={`w-full min-h-[40px] p-4 text-base leading-relaxed border rounded-xl transition-all resize-none shadow-sm outline-none overflow-hidden relative z-10 ${
                          dragOverSection === section.id
                            ? "bg-blue-50 border-blue-400 ring-4 ring-blue-400/20 shadow-[0_0_15px_rgba(59,130,246,0.3)] text-blue-900"
                            : isAccepted 
                            ? "bg-white border-[var(--color-success-200)] text-[var(--color-success-900)] focus:ring-2 focus:ring-[var(--color-success-500)] focus:border-transparent" 
                            : isAiDraft && body[section.id]?.text === body[section.id]?.original_ai_text
                              ? "bg-[var(--color-primary-50)]/50 border-[var(--color-primary-300)] text-[var(--color-primary-900)] focus:ring-2 focus:ring-[var(--color-primary-500)] focus:border-transparent"
                              : "bg-[var(--surface-sunken)] border-[var(--border-default)] text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] focus:border-transparent hover:bg-white"
                        }`}
                        onDragOver={(e) => handleDragOver(e, section.id)}
                        onDragLeave={handleDragLeave}
                        onDrop={(e) => handleDrop(e, section.id, e.target as HTMLTextAreaElement)}
                        value={body[section.id]?.text || ""}
                        onInput={(e) => {
                          const target = e.target as HTMLTextAreaElement;
                          target.style.height = 'auto';
                          target.style.height = target.scrollHeight + 'px';
                        }}
                        onChange={(e) => handleSectionChange(section.id, e.target.value, e.target as HTMLTextAreaElement)}
                        placeholder={`Enter ${section.label.toLowerCase()}...`}
                        ref={(el) => {
                          if (el && !el.style.height) {
                            el.style.height = 'auto';
                            el.style.height = el.scrollHeight + 'px';
                          }
                        }}
                      />
                    </div>
                  </motion.div>
                )})}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
