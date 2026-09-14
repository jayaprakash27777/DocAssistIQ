/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable react/no-unescaped-entities */
/**
 * DocAssistIQ — Manual Clinical Intake Form (Phase 22).
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import {
  getIntake,
  updateIntake,
  finalizeIntake,
  type ManualIntakeResponse,
  type ManualIntakeUpdate
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";

const DEBOUNCE_MS = 1500;

export default function ManualIntakePage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;

  const [intake, setIntake] = useState<ManualIntakeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Form State
  const [formData, setFormData] = useState<ManualIntakeUpdate>({});
  
  // Autosave State
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [unsavedChanges, setUnsavedChanges] = useState(false);

  // Load draft
  const fetchIntake = useCallback(async () => {
    if (!id) return;
    const res = await getIntake(id);
    if (res.ok) {
      setIntake(res.data);
      setFormData({
        chief_complaint: res.data.chief_complaint || "",
        symptoms: res.data.symptoms || "",
        duration: res.data.duration || "",
        severity: res.data.severity || "",
        onset: res.data.onset || "",
        location: res.data.location || "",
        associated_symptoms: res.data.associated_symptoms || "",
        aggravating_factors: res.data.aggravating_factors || "",
        relieving_factors: res.data.relieving_factors || "",
        negations: res.data.negations || "",
        past_medical_history: res.data.past_medical_history || "",
        medications: res.data.medications || "",
        allergies: res.data.allergies || "",
        family_social_history: res.data.family_social_history || "",
        vitals: res.data.vitals || "",
        previous_investigations: res.data.previous_investigations || "",
      });
      setLastSaved(new Date(res.data.updated_at));
    } else {
      toast.error("Failed to load intake draft");
    }
    setLoading(false);
  }, [id, toast]);

  useEffect(() => {
    fetchIntake();
  }, [fetchIntake]);

  // Unsaved changes protection
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (unsavedChanges) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [unsavedChanges]);

  // Autosave logic
  useEffect(() => {
    if (!unsavedChanges || !id || intake?.status === "final") return;

    const timer = setTimeout(async () => {
      setSaving(true);
      const res = await updateIntake(id, formData);
      if (res.ok) {
        setLastSaved(new Date());
        setUnsavedChanges(false);
      }
      setSaving(false);
    }, DEBOUNCE_MS);

    return () => clearTimeout(timer);
  }, [formData, unsavedChanges, id, intake?.status]);

  const handleChange = (field: keyof ManualIntakeUpdate, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setUnsavedChanges(true);
  };

  const handleFinalize = async () => {
    if (!id) return;
    if (unsavedChanges) {
      // Force an immediate save before finalizing
      setSaving(true);
      await updateIntake(id, formData);
    }
    
    setSaving(true);
    const res = await finalizeIntake(id);
    setSaving(false);
    if (res.ok) {
      toast.success("Intake finalized successfully");
      router.push(`/consultations/${id}`);
    } else {
      toast.error(res.error.message || "Failed to finalize intake");
    }
  };

  if (loading) {
    return (
      <div className="consultations-page" style={{ maxWidth: "1000px" }}>
        <Skeleton className="h-12 w-2/5 mb-8" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  const isFinal = intake?.status === "final";

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6">
      <motion.header 
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="sticky top-0 z-10 bg-[var(--glass-bg)] backdrop-blur-md border-b border-[var(--glass-border)] py-4 px-6 -mx-6 mb-8 rounded-b-2xl shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4"
      >
        <div>
          <Link href={`/consultations/${id}`} className="text-[var(--color-primary-600)] hover:text-[var(--color-primary-700)] text-sm font-medium flex items-center gap-1.5 transition-colors mb-2">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
            Back to Consultation
          </Link>
          <h2 className="text-2xl font-bold font-heading text-[var(--text-primary)] m-0">Structured Manual Intake</h2>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="text-sm text-[var(--text-secondary)] font-medium flex items-center gap-2">
            {saving ? (
              <span className="flex items-center gap-2 text-[var(--color-primary-600)]">
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                Saving...
              </span>
            ) : unsavedChanges ? (
              <span className="text-[var(--color-warning-600)] flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[var(--color-warning-500)] animate-pulse" />
                Unsaved changes
              </span>
            ) : lastSaved ? (
              <span className="text-[var(--text-tertiary)] flex items-center gap-1.5">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                Saved {lastSaved.toLocaleTimeString()}
              </span>
            ) : (
              "Draft"
            )}
          </div>
          
          <Button 
            variant="primary" 
            onClick={handleFinalize} 
            disabled={saving || isFinal}
            isLoading={saving}
          >
            {isFinal ? "Finalized" : "Finalize Intake"}
          </Button>
        </div>
      </motion.header>

      <AnimatePresence>
        {isFinal && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="bg-[var(--color-success-50)] text-[var(--color-success-700)] border border-[var(--color-success-200)] p-4 rounded-xl mb-6 font-medium flex items-center gap-3 shadow-sm"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
            This intake form has been finalized and is securely locked.
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
        
        {/* Core Section */}
        <motion.section 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white p-6 sm:p-8 rounded-2xl border border-[var(--border-default)] shadow-sm flex flex-col gap-5"
        >
          <div className="border-b border-[var(--border-default)] pb-4 mb-2">
            <h3 className="text-lg font-bold font-heading text-[var(--text-primary)]">History of Presenting Illness</h3>
            <p className="text-sm text-[var(--text-secondary)] mt-1">Core details regarding the patient's primary concern.</p>
          </div>
          
          <div>
            <label className="block text-sm font-semibold text-[var(--text-primary)] mb-1.5">Chief Complaint</label>
            <textarea className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl p-3 text-sm text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] outline-none transition-all resize-y min-h-[80px]" rows={2} value={formData.chief_complaint || ""} onChange={e => handleChange("chief_complaint", e.target.value)} disabled={isFinal} placeholder="Primary reason for visit" />
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-[var(--text-primary)] mb-1.5">Onset</label>
              <input type="text" className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl p-3 text-sm text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] outline-none transition-all" value={formData.onset || ""} onChange={e => handleChange("onset", e.target.value)} disabled={isFinal} placeholder="When did it start?" />
            </div>
            <div>
              <label className="block text-sm font-semibold text-[var(--text-primary)] mb-1.5">Duration</label>
              <input type="text" className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl p-3 text-sm text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] outline-none transition-all" value={formData.duration || ""} onChange={e => handleChange("duration", e.target.value)} disabled={isFinal} placeholder="How long?" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-[var(--text-primary)] mb-1.5">Symptoms</label>
            <textarea className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl p-3 text-sm text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] outline-none transition-all resize-y min-h-[100px]" rows={3} value={formData.symptoms || ""} onChange={e => handleChange("symptoms", e.target.value)} disabled={isFinal} placeholder="Detailed symptom description" />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-[var(--text-primary)] mb-1.5">Severity</label>
              <input type="text" className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl p-3 text-sm text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] outline-none transition-all" value={formData.severity || ""} onChange={e => handleChange("severity", e.target.value)} disabled={isFinal} placeholder="Mild, moderate, 8/10, etc." />
            </div>
            <div>
              <label className="block text-sm font-semibold text-[var(--text-primary)] mb-1.5">Location</label>
              <input type="text" className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl p-3 text-sm text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] outline-none transition-all" value={formData.location || ""} onChange={e => handleChange("location", e.target.value)} disabled={isFinal} placeholder="Anatomical location/radiation" />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-semibold text-[var(--text-primary)] mb-1.5">Associated Symptoms</label>
            <input type="text" className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl p-3 text-sm text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] outline-none transition-all" value={formData.associated_symptoms || ""} onChange={e => handleChange("associated_symptoms", e.target.value)} disabled={isFinal} placeholder="Symptoms occurring together" />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-[var(--text-primary)] mb-1.5">Aggravating Factors</label>
              <input type="text" className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl p-3 text-sm text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] outline-none transition-all" value={formData.aggravating_factors || ""} onChange={e => handleChange("aggravating_factors", e.target.value)} disabled={isFinal} placeholder="What makes it worse?" />
            </div>
            <div>
              <label className="block text-sm font-semibold text-[var(--text-primary)] mb-1.5">Relieving Factors</label>
              <input type="text" className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl p-3 text-sm text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] outline-none transition-all" value={formData.relieving_factors || ""} onChange={e => handleChange("relieving_factors", e.target.value)} disabled={isFinal} placeholder="What makes it better?" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-[var(--text-primary)] mb-1.5">Pertinent Negatives (Negations)</label>
            <input type="text" className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl p-3 text-sm text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] outline-none transition-all" value={formData.negations || ""} onChange={e => handleChange("negations", e.target.value)} disabled={isFinal} placeholder="Absence of specific symptoms" />
          </div>
        </motion.section>

        {/* History & Vitals Section */}
        <motion.section 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white p-6 sm:p-8 rounded-2xl border border-[var(--border-default)] shadow-sm flex flex-col gap-5"
        >
          <div className="border-b border-[var(--border-default)] pb-4 mb-2">
            <h3 className="text-lg font-bold font-heading text-[var(--text-primary)]">History & Vitals</h3>
            <p className="text-sm text-[var(--text-secondary)] mt-1">Background information and current measurements.</p>
          </div>
          
          <div>
            <label className="block text-sm font-semibold text-[var(--text-primary)] mb-1.5">Past Medical History</label>
            <textarea className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl p-3 text-sm text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] outline-none transition-all resize-y min-h-[80px]" rows={3} value={formData.past_medical_history || ""} onChange={e => handleChange("past_medical_history", e.target.value)} disabled={isFinal} placeholder="Prior conditions, surgeries, etc." />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-[var(--text-primary)] mb-1.5">Medications</label>
              <textarea className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl p-3 text-sm text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] outline-none transition-all resize-y min-h-[80px]" rows={2} value={formData.medications || ""} onChange={e => handleChange("medications", e.target.value)} disabled={isFinal} placeholder="Current meds & doses" />
            </div>
            <div>
              <label className="block text-sm font-semibold text-[var(--text-primary)] mb-1.5">Allergies</label>
              <textarea className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl p-3 text-sm text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] outline-none transition-all resize-y min-h-[80px]" rows={2} value={formData.allergies || ""} onChange={e => handleChange("allergies", e.target.value)} disabled={isFinal} placeholder="Drug or environmental allergies" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-[var(--text-primary)] mb-1.5">Family & Social History</label>
            <textarea className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl p-3 text-sm text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] outline-none transition-all resize-y min-h-[80px]" rows={2} value={formData.family_social_history || ""} onChange={e => handleChange("family_social_history", e.target.value)} disabled={isFinal} placeholder="Smoking, alcohol, hereditary conditions" />
          </div>

          <div>
            <label className="block text-sm font-semibold text-[var(--text-primary)] mb-1.5">Vitals</label>
            <textarea className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl p-3 text-sm text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] outline-none transition-all resize-y min-h-[80px]" rows={2} value={formData.vitals || ""} onChange={e => handleChange("vitals", e.target.value)} disabled={isFinal} placeholder="BP, HR, Temp, RR, SpO2, Weight" />
          </div>

          <div>
            <label className="block text-sm font-semibold text-[var(--text-primary)] mb-1.5">Previous Investigations</label>
            <textarea className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl p-3 text-sm text-[var(--text-primary)] focus:bg-white focus:ring-2 focus:ring-[var(--color-primary-500)] outline-none transition-all resize-y min-h-[80px]" rows={2} value={formData.previous_investigations || ""} onChange={e => handleChange("previous_investigations", e.target.value)} disabled={isFinal} placeholder="Recent lab results, imaging, etc." />
          </div>
        </motion.section>
        
      </div>
    </div>
  );
}
