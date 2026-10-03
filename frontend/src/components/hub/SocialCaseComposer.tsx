"use client";

import React, { useState } from "react";
import { QuotedPostSummary, DoctorPost } from "@/types/social";
import { getStoredToken } from "@/lib/api";

interface SocialCaseComposerProps {
  onClose: () => void;
  onPublish?: (
    postData: {
      disease_name: string;
      clinical_findings: string;
      diagnosis: string;
      treatment_plan: string;
      drugs_used: string[];
      specialty_tags: string[];
      is_urgent_consult: boolean;
      poll_question?: string;
      poll_options?: string[];
      quoted_post_id?: string;
    },
    files: File[]
  ) => Promise<void>;
  onPostCreated?: (post: DoctorPost) => void;
  initialEmergency?: boolean;
  quotedPost?: QuotedPostSummary | null;
  onClearQuote?: () => void;
}

export function SocialCaseComposer({
  onClose,
  onPublish,
  onPostCreated,
  initialEmergency = false,
  quotedPost,
  onClearQuote,
}: SocialCaseComposerProps) {
  const [diseaseName, setDiseaseName] = useState("");
  const [clinicalFindings, setClinicalFindings] = useState("");
  const [diagnosis, setDiagnosis] = useState("");
  const [treatmentPlan, setTreatmentPlan] = useState("");
  const [drugsInput, setDrugsInput] = useState("");
  const [tagsInput, setTagsInput] = useState("");
  const [isUrgent, setIsUrgent] = useState(initialEmergency);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [showPoll, setShowPoll] = useState(false);
  const [pollQuestion, setPollQuestion] = useState("");
  const [pollOptions, setPollOptions] = useState<string[]>(["", ""]);


  // 1-Click HIPAA Sanitizer
  const handleScrubPHI = () => {
    let sanitized = clinicalFindings;
    sanitized = sanitized.replace(/\b[A-Z][a-z]+ [A-Z][a-z]+\b/g, "[Patient]");
    sanitized = sanitized.replace(/MRN[:\s#]*\d+/gi, "MRN:[REDACTED]");
    sanitized = sanitized.replace(/\b\d{3}-\d{2}-\d{4}\b/g, "[SSN-REDACTED]");
    sanitized = sanitized.replace(/\b\d{10}\b/g, "[PHONE-REDACTED]");
    sanitized = sanitized.replace(/\b\d{1,2}\/\d{1,2}\/\d{2,4}\b/g, "[DATE]");
    setClinicalFindings(sanitized);
  };

  const handleAddPollOption = () => {
    if (pollOptions.length < 5) {
      setPollOptions([...pollOptions, ""]);
    }
  };

  const handlePollOptionChange = (idx: number, val: string) => {
    const updated = [...pollOptions];
    updated[idx] = val;
    setPollOptions(updated);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!diseaseName.trim() || !clinicalFindings.trim() || !diagnosis.trim() || !treatmentPlan.trim()) {
      return;
    }

    const drugs = drugsInput
      .split(",")
      .map((d) => d.trim())
      .filter(Boolean);

    const tags = tagsInput
      .split(/[\s,]+/)
      .map((t) => (t.startsWith("#") ? t : `#${t}`))
      .filter((t) => t.length > 1);

    setIsSubmitting(true);
    try {
      if (onPublish) {
        await onPublish(
          {
            disease_name: diseaseName.trim(),
            clinical_findings: clinicalFindings.trim(),
            diagnosis: diagnosis.trim(),
            treatment_plan: treatmentPlan.trim(),
            drugs_used: drugs,
            specialty_tags: tags.length > 0 ? tags : ["#ClinicalCase"],
            is_urgent_consult: isUrgent,
            poll_question: showPoll && pollQuestion.trim() ? pollQuestion.trim() : undefined,
            poll_options: showPoll ? pollOptions.filter((o) => o.trim().length > 0) : undefined,
            quoted_post_id: quotedPost?.id,
          },
          files
        );
      } else {
        const token = getStoredToken();
        const payload = {
          disease_name: diseaseName.trim(),
          clinical_findings: clinicalFindings.trim(),
          diagnosis: diagnosis.trim(),
          treatment_plan: treatmentPlan.trim(),
          drugs_used: drugs,
          specialty_tags: tags.length > 0 ? tags : ["#ClinicalCase"],
          is_urgent_consult: isUrgent,
          poll_question: showPoll && pollQuestion.trim() ? pollQuestion.trim() : undefined,
          poll_options: showPoll ? pollOptions.filter((o) => o.trim().length > 0) : undefined,
          quoted_post_id: quotedPost?.id,
        };
        const res = await fetch("/api/v1/hub/posts", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          const newPost = await res.json();
          if (onPostCreated) onPostCreated(newPost);
        }
      }
      onClose();
    } catch (err) {
      console.error("Failed to submit case:", err);
    } finally {
      setIsSubmitting(false);
    }
  };


  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-2xl w-full p-6 space-y-4 my-8">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h2 className="text-lg font-black text-slate-900 tracking-tight flex items-center gap-2">
              <span>✍️ Share Clinical Case with Global Doctors</span>
            </h2>
            <p className="text-xs text-slate-500">
              Verified peer discussion, multidisciplinary review, and treatment consensus.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 hover:text-slate-800 text-xs font-bold flex items-center justify-center transition-colors cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* ── Quoted Post Summary (if quoting) ── */}
        {quotedPost && (
          <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200 text-xs relative">
            <button
              type="button"
              onClick={onClearQuote}
              className="absolute top-2 right-2 text-slate-400 hover:text-slate-600 font-bold"
            >
              ✕
            </button>
            <span className="font-bold text-teal-700">Quoting Case:</span>
            <p className="font-extrabold text-slate-900">{quotedPost.disease_name}</p>
            <p className="text-slate-500 line-clamp-1">{quotedPost.clinical_findings}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3.5">
          {/* STAT Emergency Toggle Switch */}
          <div
            onClick={() => setIsUrgent(!isUrgent)}
            className={`p-3 rounded-2xl border transition-all cursor-pointer flex items-center justify-between ${
              isUrgent
                ? "bg-rose-50 border-rose-300 ring-2 ring-rose-200"
                : "bg-slate-50 border-slate-200 hover:bg-slate-100/70"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <span className="text-xl">🚨</span>
              <div>
                <p className="text-xs font-black text-slate-900">
                  Request Emergency STAT 2nd Opinion
                </p>
                <p className="text-[11px] text-slate-500">
                  Alert on-call specialists globally for urgent acute guidance.
                </p>
              </div>
            </div>
            <div
              className={`w-11 h-6 rounded-full transition-colors relative flex items-center px-0.5 ${
                isUrgent ? "bg-rose-600 justify-end" : "bg-slate-300 justify-start"
              }`}
            >
              <div className="w-5 h-5 rounded-full bg-white shadow-xs" />
            </div>
          </div>

          {/* Condition / Presentation Title */}
          <div>
            <label className="block text-xs font-extrabold text-slate-800 mb-1">
              Disease / Condition Dilemma *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Atypical Takotsubo with Cardiogenic Shock & LVOTO"
              value={diseaseName}
              onChange={(e) => setDiseaseName(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs font-semibold text-slate-900 outline-none focus:border-teal-600 shadow-2xs"
            />
          </div>

          {/* Clinical Findings & Presentation Narrative */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-extrabold text-slate-800">
                Patient Presentation & History *
              </label>
              <button
                type="button"
                onClick={handleScrubPHI}
                className="text-[11px] font-bold text-teal-700 hover:text-teal-900 hover:underline cursor-pointer flex items-center gap-1"
                title="Automatically strip names, MRNs, and phone numbers"
              >
                <span>🛡️ Scrub PHI (HIPAA Sanitize)</span>
              </button>
            </div>
            <textarea
              required
              rows={3}
              placeholder="Describe age, symptoms, vital signs, acute triggers, and hospital day..."
              value={clinicalFindings}
              onChange={(e) => setClinicalFindings(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs text-slate-900 outline-none focus:border-teal-600 shadow-2xs resize-none"
            />
          </div>

          {/* Diagnosis & Treatment Plan */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-extrabold text-slate-800 mb-1">
                Diagnosis / Differential *
              </label>
              <textarea
                required
                rows={2}
                placeholder="Confirmed or differential diagnostic considerations..."
                value={diagnosis}
                onChange={(e) => setDiagnosis(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs text-slate-900 outline-none focus:border-teal-600 shadow-2xs resize-none"
              />
            </div>
            <div>
              <label className="block text-xs font-extrabold text-slate-800 mb-1">
                Current Treatment & Plan *
              </label>
              <textarea
                required
                rows={2}
                placeholder="Initiated therapy, monitoring, response, and clinical questions..."
                value={treatmentPlan}
                onChange={(e) => setTreatmentPlan(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs text-slate-900 outline-none focus:border-teal-600 shadow-2xs resize-none"
              />
            </div>
          </div>

          {/* Medications & Specialty Hashtags */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-bold text-slate-700 mb-1">
                Drugs Used (comma separated)
              </label>
              <input
                type="text"
                placeholder="e.g. Norepinephrine, Vasopressin, Hydrocortisone"
                value={drugsInput}
                onChange={(e) => setDrugsInput(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs text-slate-900 outline-none focus:border-teal-600 shadow-2xs"
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-slate-700 mb-1">
                Specialty Tags & #Hashtags
              </label>
              <input
                type="text"
                placeholder="e.g. #Cardiology #CriticalCare #Shock"
                value={tagsInput}
                onChange={(e) => setTagsInput(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs text-slate-900 outline-none focus:border-teal-600 shadow-2xs"
              />
            </div>
          </div>

          {/* File Attachments Upload (DICOM / ECG / X-Ray) */}
          <div>
            <label className="block text-[11px] font-bold text-slate-700 mb-1">
              Attach Imaging & Diagnostic Scans (X-Ray, CT, ECG, Histology)
            </label>
            <input
              type="file"
              multiple
              accept="image/*,.dcm"
              onChange={handleFileChange}
              className="w-full text-xs text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-teal-50 file:text-teal-700 hover:file:bg-teal-100 cursor-pointer"
            />
            {files.length > 0 && (
              <p className="text-[10px] text-teal-700 font-semibold mt-1">
                {files.length} file(s) selected for upload
              </p>
            )}
          </div>

          {/* Consensus Dilemma Poll Toggle */}
          <div className="pt-1">
            <button
              type="button"
              onClick={() => setShowPoll(!showPoll)}
              className="text-xs font-bold text-teal-700 hover:underline cursor-pointer flex items-center gap-1.5"
            >
              <span>{showPoll ? "✕ Remove Consensus Poll" : "🗳️ + Attach Clinical Consensus Poll"}</span>
            </button>

            {showPoll && (
              <div className="mt-2 p-3 bg-slate-50 rounded-2xl border border-slate-200 space-y-2">
                <input
                  type="text"
                  placeholder="Poll Question: e.g. Which vasopressor should be initiated next?"
                  value={pollQuestion}
                  onChange={(e) => setPollQuestion(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-xl border border-slate-300 text-xs bg-white outline-none focus:border-teal-600"
                />
                {pollOptions.map((opt, idx) => (
                  <input
                    key={idx}
                    type="text"
                    placeholder={`Option ${idx + 1}`}
                    value={opt}
                    onChange={(e) => handlePollOptionChange(idx, e.target.value)}
                    className="w-full px-3 py-1.5 rounded-xl border border-slate-300 text-xs bg-white outline-none focus:border-teal-600"
                  />
                ))}
                {pollOptions.length < 5 && (
                  <button
                    type="button"
                    onClick={handleAddPollOption}
                    className="text-[11px] font-bold text-teal-700 hover:underline cursor-pointer"
                  >
                    + Add Option
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Form Actions */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-bold text-slate-600 hover:text-slate-800 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !diseaseName.trim() || !clinicalFindings.trim()}
              className="px-6 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-black shadow-sm transition-all disabled:opacity-50 cursor-pointer"
            >
              {isSubmitting ? "Publishing Case..." : isUrgent ? "🚨 Broadcast STAT Case" : "Share Case to Hub"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default SocialCaseComposer;
