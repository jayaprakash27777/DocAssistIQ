/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable react/no-unescaped-entities */
/**
 * DocAssistIQ — Doctor Profile Page (/profile).
 *
 * Shows the current doctor's verification status prominently.
 * Allows creating a profile if none exists, and editing existing one.
 *
 * Verification status display:
 *   🟡 PENDING   — awaiting admin review, explain what is blocked
 *   🟢 VERIFIED  — access granted to clinical features
 *   🔴 REJECTED  — show rejection reason, allow re-submission
 *
 * Auto-reverts to PENDING if credential fields change.
 */

"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  getMyDoctorProfile,
  createMyDoctorProfile,
  updateMyDoctorProfile,
  type DoctorResponse,
  type DoctorCreate,
} from "@/lib/api";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import { motion, AnimatePresence } from "framer-motion";
import { UserCircle, ShieldCheck, ShieldAlert, Shield, Clock, PlusCircle, Edit3, Save, X, Briefcase, FileText, Building2, MapPin, Mail, Award, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";

type PageState = "loading" | "none" | "view" | "edit" | "create";

const STATUS_CONFIG = {
  pending: {
    label: "Verification Pending",
    badgeClass: "bg-[var(--color-warning-100)] text-[var(--color-warning-700)] border-[var(--color-warning-200)]",
    colorClass: "bg-[var(--color-warning-50)] border-[var(--color-warning-200)] text-[var(--color-warning-900)]",
    iconClass: "text-[var(--color-warning-600)] bg-[var(--color-warning-100)]",
    icon: <Clock className="w-5 h-5" />,
    message: "Your profile is awaiting review by an administrator. Some clinical features may be restricted until your credentials are verified.",
  },
  verified: {
    label: "Verified Professional",
    badgeClass: "bg-[var(--color-success-100)] text-[var(--color-success-700)] border-[var(--color-success-200)]",
    colorClass: "bg-[var(--color-success-50)] border-[var(--color-success-200)] text-[var(--color-success-900)]",
    iconClass: "text-[var(--color-success-600)] bg-[var(--color-success-100)]",
    icon: <CheckCircle2 className="w-5 h-5" />,
    message: "Your credentials have been verified. You have full access to all clinical decision support features.",
  },
  rejected: {
    label: "Verification Rejected",
    badgeClass: "bg-[var(--color-danger-100)] text-[var(--color-danger-700)] border-[var(--color-danger-200)]",
    colorClass: "bg-[var(--color-danger-50)] border-[var(--color-danger-200)] text-[var(--color-danger-900)]",
    iconClass: "text-[var(--color-danger-600)] bg-[var(--color-danger-100)]",
    icon: <ShieldAlert className="w-5 h-5" />,
    message: "Your verification was declined. Please review the reason below and update your profile to re-submit.",
  },
};

export default function DoctorProfilePage() {
  const { toast } = useToast();
  const { user } = useAuth();
  const [state, setState] = useState<PageState>("loading");
  const [profile, setProfile] = useState<DoctorResponse | null>(null);

  // Form state
  const [specialty, setSpecialty] = useState("");
  const [credRef, setCredRef] = useState("");
  const [credBody, setCredBody] = useState("");
  const [bio, setBio] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getMyDoctorProfile().then((r) => {
      if (r.ok) {
        setProfile(r.data);
        populateForm(r.data);
        setState("view");
      } else if (r.statusCode === 404) {
        setState("none");
      } else {
        setState("none");
      }
    });
  }, []);

  function populateForm(d: DoctorResponse) {
    setSpecialty(d.specialty ?? "");
    setCredRef(d.credential_reference ?? "");
    setCredBody(d.credential_body ?? "");
    setBio(d.bio ?? "");
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    const payload: DoctorCreate = {
      specialty: specialty || undefined,
      credential_reference: credRef || undefined,
      credential_body: credBody || undefined,
      bio: bio || undefined,
    };
    const r = await createMyDoctorProfile(payload);
    setSaving(false);
    if (r.ok) {
      setProfile(r.data);
      populateForm(r.data);
      setState("view");
      toast.success("Doctor profile created — pending verification.");
    } else {
      toast.error(r.error.message ?? "Failed to create profile.");
    }
  }

  async function handleUpdate(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    const r = await updateMyDoctorProfile({
      specialty: specialty || undefined,
      credential_reference: credRef || undefined,
      credential_body: credBody || undefined,
      bio: bio || undefined,
    });
    setSaving(false);
    if (r.ok) {
      setProfile(r.data);
      populateForm(r.data);
      setState("view");
      toast.success(
        r.data.verification_status === "pending"
          ? "Profile updated — status reset to pending for re-verification."
          : "Profile updated.",
      );
    } else {
      toast.error(r.error.message ?? "Failed to update profile.");
    }
  }

  if (state === "loading") {
    return (
      <div className="max-w-5xl mx-auto py-8 px-4 md:px-8" aria-busy="true">
        <Skeleton height="200px" className="mb-4 rounded-3xl" />
        <Skeleton height="3rem" width="40%" className="mx-auto mb-10" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
             <Skeleton height="300px" className="rounded-3xl" />
          </div>
          <div className="lg:col-span-2 space-y-6">
             <Skeleton height="150px" className="rounded-3xl" />
             <Skeleton height="150px" className="rounded-3xl" />
          </div>
        </div>
      </div>
    );
  }

  const cfg = profile ? STATUS_CONFIG[profile.verification_status] : null;

  return (
    <div className="max-w-5xl mx-auto py-6 px-4 md:px-8 pb-20">
      
      {/* Premium Cover & Profile Header */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative mb-8 bg-white rounded-3xl shadow-xl shadow-[var(--glass-shadow)] border border-[var(--border-default)] overflow-hidden"
      >
        {/* Cover Image */}
        <div className="h-48 md:h-64 w-full relative">
          <div className="absolute inset-0 bg-gradient-to-r from-[var(--color-primary-600)] to-[var(--color-primary-400)] mix-blend-multiply opacity-90 z-10"></div>
          <img 
            src="https://images.unsplash.com/photo-1579684385127-1ef15d508118?q=80&w=1200&auto=format&fit=crop" 
            alt="Medical Cover" 
            className="w-full h-full object-cover object-center absolute inset-0"
          />
          {state === "view" && (
            <div className="absolute top-6 right-6 z-20">
              <Button
                variant="outline"
                onClick={() => setState("edit")}
                id="edit-doctor-profile-btn"
                className="flex items-center gap-2 rounded-full shadow-md bg-white/90 backdrop-blur-md hover:bg-white border-0 text-[var(--color-primary-800)] font-bold px-5"
              >
                <Edit3 className="w-4 h-4" /> Edit Profile
              </Button>
            </div>
          )}
        </div>

        {/* Profile Info Overlay */}
        <div className="px-6 md:px-10 pb-8 relative z-20 -mt-20 md:-mt-24 flex flex-col md:flex-row items-center md:items-end gap-6 text-center md:text-left">
          {/* Avatar */}
          <div className="w-32 h-32 md:w-40 md:h-40 rounded-full border-4 border-white shadow-xl bg-white overflow-hidden shrink-0 relative">
            <img 
              src={`https://api.dicebear.com/7.x/initials/svg?seed=${user?.full_name}&backgroundColor=0b968c&textColor=ffffff`}
              alt="Doctor Avatar" 
              className="w-full h-full object-cover"
            />
          </div>

          {/* Details */}
          <div className="flex-grow pt-2">
            <div className="flex flex-col md:flex-row md:items-center gap-3 mb-2">
              <h1 className="text-3xl md:text-4xl font-black tracking-tight text-[var(--text-primary)]">
                Dr. {user?.full_name}
              </h1>
              {cfg && (
                <div className={`inline-flex items-center justify-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-widest border shadow-sm ${cfg.badgeClass}`}>
                  {cfg.icon}
                  {cfg.label}
                </div>
              )}
            </div>
            
            <p className="text-lg font-medium text-[var(--color-primary-600)] mb-4 flex items-center justify-center md:justify-start gap-2">
              <Award className="w-5 h-5" /> 
              {profile?.specialty || "Specialty not specified"}
            </p>

            <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 text-sm font-medium text-[var(--text-secondary)]">
              <span className="flex items-center gap-1.5 bg-[var(--surface-sunken)] px-3 py-1.5 rounded-lg border border-[var(--border-subtle)]">
                <Mail className="w-4 h-4 text-[var(--text-tertiary)]" /> {user?.email}
              </span>
              {profile?.credential_body && (
                <span className="flex items-center gap-1.5 bg-[var(--surface-sunken)] px-3 py-1.5 rounded-lg border border-[var(--border-subtle)]">
                  <Building2 className="w-4 h-4 text-[var(--text-tertiary)]" /> {profile.credential_body}
                </span>
              )}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Verification status banner (if not verified or rejected) */}
      {profile && cfg && profile.verification_status !== "verified" && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`mb-8 p-6 rounded-3xl border flex flex-col md:flex-row items-center md:items-start gap-5 shadow-sm ${cfg.colorClass}`}
          role="status"
        >
          <div className={`shrink-0 w-12 h-12 rounded-2xl flex items-center justify-center ${cfg.iconClass} shadow-inner`}>
            {cfg.icon}
          </div>
          <div className="text-center md:text-left flex-grow">
            <h3 className="text-lg font-bold mb-1">{cfg.label}</h3>
            <p className="text-sm font-medium opacity-90 leading-relaxed">{cfg.message}</p>
            {profile.verification_status === "rejected" && profile.rejection_reason && (
              <div className="mt-4 p-4 bg-white/50 rounded-xl text-sm font-bold border border-current/10 inline-block text-left" role="note">
                <span className="uppercase tracking-widest text-[10px] opacity-70 block mb-1">Rejection Reason</span>
                {profile.rejection_reason}
              </div>
            )}
          </div>
          {profile.verification_status === "rejected" && state === "view" && (
            <Button
              variant="primary"
              onClick={() => setState("edit")}
              id="resubmit-profile-btn"
              className="rounded-full shadow-sm shrink-0"
            >
              Update &amp; Re-submit
            </Button>
          )}
        </motion.div>
      )}

      {/* No profile yet */}
      {state === "none" && (
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-[var(--surface-raised)] border border-[var(--border-default)] rounded-3xl p-12 text-center flex flex-col items-center justify-center shadow-xl shadow-[var(--glass-shadow)]"
        >
          <div className="w-20 h-20 bg-[var(--color-primary-50)] text-[var(--color-primary-600)] rounded-full flex items-center justify-center mb-6 shadow-inner">
            <Shield className="w-10 h-10" />
          </div>
          <h3 className="text-2xl font-bold text-[var(--text-primary)] mb-3">Complete Your Profile</h3>
          <p className="text-[var(--text-secondary)] font-medium max-w-md mx-auto mb-8 leading-relaxed">
            Create your professional profile to request credential verification and unlock full access to DocAssistIQ clinical features.
          </p>
          <Button
            size="lg"
            onClick={() => setState("create")}
            id="create-doctor-profile-btn"
            className="rounded-full px-8 shadow-md flex items-center gap-2"
          >
            <PlusCircle className="w-5 h-5" /> Setup Profile
          </Button>
        </motion.div>
      )}

      {/* View mode */}
      {state === "view" && profile && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column - Credentials */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-1 space-y-6"
          >
            <div className="bg-[var(--surface-raised)] border border-[var(--border-default)] rounded-3xl p-6 shadow-xl shadow-[var(--glass-shadow)]">
              <h3 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-widest mb-6 flex items-center gap-2 border-b border-[var(--border-subtle)] pb-4">
                <ShieldCheck className="w-5 h-5 text-[var(--color-primary-500)]" /> Credentials
              </h3>
              
              <div className="space-y-6">
                <div>
                  <p className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-widest mb-1.5 flex items-center gap-1.5">
                    <Building2 className="w-3.5 h-3.5" /> Issuing Body
                  </p>
                  <p className="text-[var(--text-primary)] font-semibold text-sm">
                    {profile.credential_body || <span className="text-[var(--text-tertiary)] italic">Not specified</span>}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-widest mb-1.5 flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5" /> License Number
                  </p>
                  <p className="text-[var(--text-primary)] font-mono font-semibold text-sm bg-[var(--surface-sunken)] p-2 rounded-lg border border-[var(--border-subtle)] inline-block">
                    {profile.credential_reference || <span className="text-[var(--text-tertiary)] italic font-sans">Not specified</span>}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-widest mb-1.5 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" /> Member Since
                  </p>
                  <p className="text-[var(--text-secondary)] font-medium text-sm">
                    {new Date(profile.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Right Column - Bio & Info */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-2 space-y-6"
          >
            <div className="bg-[var(--surface-raised)] border border-[var(--border-default)] rounded-3xl p-6 md:p-8 shadow-xl shadow-[var(--glass-shadow)] h-full">
              <h3 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-widest mb-6 flex items-center gap-2 border-b border-[var(--border-subtle)] pb-4">
                <UserCircle className="w-5 h-5 text-[var(--color-primary-500)]" /> Professional Biography
              </h3>
              
              <div className="prose prose-sm max-w-none text-[var(--text-secondary)] leading-loose font-medium">
                {profile.bio ? (
                  profile.bio.split('\n').map((paragraph, idx) => (
                    <p key={idx} className="mb-4">{paragraph}</p>
                  ))
                ) : (
                  <p className="italic text-[var(--text-tertiary)] text-center py-10">No professional biography has been provided yet.</p>
                )}
              </div>
            </div>
          </motion.div>

        </div>
      )}

      {/* Create / Edit form */}
      <AnimatePresence>
      {(state === "create" || state === "edit") && (
        <motion.form
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.98 }}
          id="doctor-profile-form"
          className="bg-[var(--surface-raised)] border border-[var(--border-default)] rounded-3xl overflow-hidden shadow-xl shadow-[var(--glass-shadow)] max-w-3xl mx-auto"
          onSubmit={state === "create" ? handleCreate : handleUpdate}
        >
          <div className="p-8 space-y-6">
            <h3 className="text-2xl font-black text-[var(--text-primary)] mb-2">
              {state === "create" ? "Setup Profile" : "Edit Profile"}
            </h3>
            <p className="text-sm font-medium text-[var(--text-secondary)] mb-6 pb-6 border-b border-[var(--border-subtle)]">
              Update your clinical credentials and professional information below.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label htmlFor="doctor-specialty" className="text-sm font-bold text-[var(--text-primary)]">Specialty</label>
                <input
                  id="doctor-specialty"
                  type="text"
                  value={specialty}
                  onChange={(e) => setSpecialty(e.target.value)}
                  maxLength={120}
                  placeholder="e.g. Cardiology, General Practice"
                  disabled={saving}
                  className="w-full bg-white border border-[var(--border-default)] rounded-xl px-4 py-3 text-sm font-medium focus:ring-2 focus:ring-[var(--color-primary-400)] focus:border-transparent outline-none transition-shadow"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="doctor-cred-body" className="text-sm font-bold text-[var(--text-primary)]">Issuing Body</label>
                <input
                  id="doctor-cred-body"
                  type="text"
                  value={credBody}
                  onChange={(e) => setCredBody(e.target.value)}
                  maxLength={120}
                  placeholder="e.g. GMC, NMC, MCI"
                  disabled={saving}
                  className="w-full bg-white border border-[var(--border-default)] rounded-xl px-4 py-3 text-sm font-medium focus:ring-2 focus:ring-[var(--color-primary-400)] focus:border-transparent outline-none transition-shadow"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label htmlFor="doctor-cred-ref" className="text-sm font-bold text-[var(--text-primary)]">
                Medical Registration / License Number
              </label>
              <input
                id="doctor-cred-ref"
                type="text"
                value={credRef}
                onChange={(e) => setCredRef(e.target.value)}
                maxLength={200}
                placeholder="e.g. GMC1234567"
                disabled={saving}
                className="w-full bg-white border border-[var(--border-default)] rounded-xl px-4 py-3 font-mono text-sm focus:ring-2 focus:ring-[var(--color-primary-400)] focus:border-transparent outline-none transition-shadow"
              />
              <p className="text-xs font-medium text-[var(--text-tertiary)] mt-2 flex items-start gap-2 bg-[var(--surface-sunken)] p-3 rounded-lg border border-[var(--border-subtle)]">
                <ShieldAlert className="w-4 h-4 shrink-0 text-[var(--color-warning-500)] mt-0.5" />
                <span>Opaque reference only — this is not stored as a verified identifier.<br/>
                <strong className="text-[var(--color-warning-700)]">Changing this field will immediately reset your verification status to Pending.</strong></span>
              </p>
            </div>

            <div className="space-y-2">
              <label htmlFor="doctor-bio" className="text-sm font-bold text-[var(--text-primary)]">Professional Biography</label>
              <textarea
                id="doctor-bio"
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                rows={5}
                maxLength={2000}
                placeholder="Brief summary of your clinical experience and qualifications..."
                disabled={saving}
                className="w-full bg-white border border-[var(--border-default)] rounded-xl px-4 py-3 text-sm font-medium focus:ring-2 focus:ring-[var(--color-primary-400)] focus:border-transparent outline-none transition-shadow resize-y min-h-[120px]"
              />
            </div>
          </div>

          <div className="bg-[var(--surface-sunken)] p-6 border-t border-[var(--border-default)] flex items-center justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                if (profile) {
                  populateForm(profile);
                  setState("view");
                } else {
                  setState("none");
                }
              }}
              disabled={saving}
              className="rounded-full shadow-sm bg-white"
            >
              <X className="w-4 h-4 mr-2" /> Cancel
            </Button>
            <Button
              id="save-doctor-profile-btn"
              type="submit"
              disabled={saving}
              className="rounded-full shadow-sm"
            >
              {saving ? "Saving…" : state === "create" ? <><PlusCircle className="w-4 h-4 mr-2"/> Create Profile</> : <><Save className="w-4 h-4 mr-2"/> Save Changes</>}
            </Button>
          </div>
        </motion.form>
      )}
      </AnimatePresence>
    </div>
  );
}
