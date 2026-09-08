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
    <div className="consultations-page" style={{ maxWidth: "1000px" }}>
      <header className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", position: "sticky", top: 0, background: "var(--background)", zIndex: 10, padding: "1rem 0", borderBottom: "1px solid var(--border-subtle)" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
            <Link href={`/consultations/${id}`} style={{ color: "var(--primary)", textDecoration: "none", fontSize: "0.875rem" }}>
              ← Back to Consultation
            </Link>
          </div>
          <h2 className="page-title" style={{ margin: 0 }}>Structured Manual Intake</h2>
        </div>
        
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            {saving ? (
              <>
                <div className="spinner" style={{ width: "12px", height: "12px", border: "2px solid var(--primary)", borderTopColor: "transparent", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
                Saving...
              </>
            ) : unsavedChanges ? (
              "Unsaved changes"
            ) : lastSaved ? (
              `Saved ${lastSaved.toLocaleTimeString()}`
            ) : (
              "Draft"
            )}
          </div>
          
          <button 
            className="btn-primary" 
            onClick={handleFinalize} 
            disabled={saving || isFinal}
          >
            {isFinal ? "Finalized" : "Finalize Intake"}
          </button>
        </div>
      </header>

      {isFinal && (
        <div style={{ background: "rgba(16, 185, 129, 0.1)", color: "var(--success)", padding: "1rem", borderRadius: "8px", marginTop: "1rem", fontWeight: 600 }}>
          This intake form has been finalized and is now read-only.
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem", marginTop: "2rem" }}>
        
        {/* Core Section */}
        <section style={{ background: "var(--surface-base)", padding: "1.5rem", borderRadius: "8px" }}>
          <h3 style={{ marginTop: 0, marginBottom: "1.5rem", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "0.5rem" }}>
            History of Presenting Illness
          </h3>
          
          <div className="form-group">
            <label>Chief Complaint</label>
            <textarea className="input-field" rows={2} value={formData.chief_complaint || ""} onChange={e => handleChange("chief_complaint", e.target.value)} disabled={isFinal} placeholder="Primary reason for visit" />
          </div>
          
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div className="form-group">
              <label>Onset</label>
              <input type="text" className="input-field" value={formData.onset || ""} onChange={e => handleChange("onset", e.target.value)} disabled={isFinal} placeholder="When did it start?" />
            </div>
            <div className="form-group">
              <label>Duration</label>
              <input type="text" className="input-field" value={formData.duration || ""} onChange={e => handleChange("duration", e.target.value)} disabled={isFinal} placeholder="How long?" />
            </div>
          </div>

          <div className="form-group">
            <label>Symptoms</label>
            <textarea className="input-field" rows={3} value={formData.symptoms || ""} onChange={e => handleChange("symptoms", e.target.value)} disabled={isFinal} placeholder="Detailed symptom description" />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div className="form-group">
              <label>Severity</label>
              <input type="text" className="input-field" value={formData.severity || ""} onChange={e => handleChange("severity", e.target.value)} disabled={isFinal} placeholder="Mild, moderate, 8/10, etc." />
            </div>
            <div className="form-group">
              <label>Location</label>
              <input type="text" className="input-field" value={formData.location || ""} onChange={e => handleChange("location", e.target.value)} disabled={isFinal} placeholder="Anatomical location/radiation" />
            </div>
          </div>
          
          <div className="form-group">
            <label>Associated Symptoms</label>
            <input type="text" className="input-field" value={formData.associated_symptoms || ""} onChange={e => handleChange("associated_symptoms", e.target.value)} disabled={isFinal} placeholder="Symptoms occurring together" />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div className="form-group">
              <label>Aggravating Factors</label>
              <input type="text" className="input-field" value={formData.aggravating_factors || ""} onChange={e => handleChange("aggravating_factors", e.target.value)} disabled={isFinal} placeholder="What makes it worse?" />
            </div>
            <div className="form-group">
              <label>Relieving Factors</label>
              <input type="text" className="input-field" value={formData.relieving_factors || ""} onChange={e => handleChange("relieving_factors", e.target.value)} disabled={isFinal} placeholder="What makes it better?" />
            </div>
          </div>

          <div className="form-group">
            <label>Pertinent Negatives (Negations)</label>
            <input type="text" className="input-field" value={formData.negations || ""} onChange={e => handleChange("negations", e.target.value)} disabled={isFinal} placeholder="Absence of specific symptoms" />
          </div>
        </section>

        {/* History & Vitals Section */}
        <section style={{ background: "var(--surface-base)", padding: "1.5rem", borderRadius: "8px" }}>
          <h3 style={{ marginTop: 0, marginBottom: "1.5rem", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "0.5rem" }}>
            History & Vitals
          </h3>
          
          <div className="form-group">
            <label>Past Medical History</label>
            <textarea className="input-field" rows={3} value={formData.past_medical_history || ""} onChange={e => handleChange("past_medical_history", e.target.value)} disabled={isFinal} placeholder="Prior conditions, surgeries, etc." />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div className="form-group">
              <label>Medications</label>
              <textarea className="input-field" rows={2} value={formData.medications || ""} onChange={e => handleChange("medications", e.target.value)} disabled={isFinal} placeholder="Current meds & doses" />
            </div>
            <div className="form-group">
              <label>Allergies</label>
              <textarea className="input-field" rows={2} value={formData.allergies || ""} onChange={e => handleChange("allergies", e.target.value)} disabled={isFinal} placeholder="Drug or environmental allergies" />
            </div>
          </div>

          <div className="form-group">
            <label>Family & Social History</label>
            <textarea className="input-field" rows={2} value={formData.family_social_history || ""} onChange={e => handleChange("family_social_history", e.target.value)} disabled={isFinal} placeholder="Smoking, alcohol, hereditary conditions" />
          </div>

          <div className="form-group">
            <label>Vitals</label>
            <textarea className="input-field" rows={2} value={formData.vitals || ""} onChange={e => handleChange("vitals", e.target.value)} disabled={isFinal} placeholder="BP, HR, Temp, RR, SpO2, Weight" />
          </div>

          <div className="form-group">
            <label>Previous Investigations</label>
            <textarea className="input-field" rows={2} value={formData.previous_investigations || ""} onChange={e => handleChange("previous_investigations", e.target.value)} disabled={isFinal} placeholder="Recent lab results, imaging, etc." />
          </div>
        </section>
        
      </div>
    </div>
  );
}
