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

type PageState = "loading" | "none" | "view" | "edit" | "create";

const STATUS_CONFIG = {
  pending: {
    label: "Verification Pending",
    color: "doctor-status--pending",
    icon: "🟡",
    message:
      "Your profile is awaiting review by an administrator. Some clinical features may be restricted until your credentials are verified.",
  },
  verified: {
    label: "Verified",
    color: "doctor-status--verified",
    icon: "🟢",
    message: "Your credentials have been verified. You have full access to clinical features.",
  },
  rejected: {
    label: "Verification Rejected",
    color: "doctor-status--rejected",
    icon: "🔴",
    message:
      "Your verification was declined. Please review the reason below and update your profile to re-submit.",
  },
};

export default function DoctorProfilePage() {
  const { toast } = useToast();
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
      <div className="doctor-profile-page" aria-busy="true">
        <div className="doctor-profile-skeleton">
          <Skeleton height="2rem" width="40%" />
          <Skeleton height="1rem" width="60%" />
          <Skeleton height="5rem" />
        </div>
      </div>
    );
  }

  const cfg = profile ? STATUS_CONFIG[profile.verification_status] : null;

  return (
    <div className="doctor-profile-page">
      <header className="doctor-profile-header">
        <div>
          <h2 className="doctor-profile-title">Doctor Profile</h2>
          <p className="doctor-profile-subtitle">
            Professional identity and verification status
          </p>
        </div>
        {state === "view" && (
          <button
            className="doctor-profile-edit-btn"
            onClick={() => setState("edit")}
            id="edit-doctor-profile-btn"
          >
            Edit profile
          </button>
        )}
      </header>

      {/* Verification status banner */}
      {profile && cfg && (
        <div
          className={`doctor-status-banner ${cfg.color}`}
          role="status"
          aria-label={`Verification status: ${cfg.label}`}
        >
          <span className="doctor-status-icon" aria-hidden="true">{cfg.icon}</span>
          <div className="doctor-status-body">
            <strong className="doctor-status-label">{cfg.label}</strong>
            <p className="doctor-status-message">{cfg.message}</p>
            {profile.verification_status === "rejected" && profile.rejection_reason && (
              <div className="doctor-rejection-reason" role="note">
                <strong>Reason:</strong> {profile.rejection_reason}
              </div>
            )}
          </div>
        </div>
      )}

      {/* No profile yet */}
      {state === "none" && (
        <div className="doctor-noprofile">
          <div className="doctor-noprofile-icon" aria-hidden="true">👨‍⚕️</div>
          <h3>No doctor profile yet</h3>
          <p>
            Create your doctor profile to request credential verification and
            access clinical features.
          </p>
          <button
            className="doctor-create-btn"
            onClick={() => setState("create")}
            id="create-doctor-profile-btn"
          >
            Create profile
          </button>
        </div>
      )}

      {/* View mode */}
      {state === "view" && profile && (
        <div className="doctor-profile-view">
          <dl className="doctor-profile-dl">
            <div className="doctor-profile-row">
              <dt>Specialty</dt>
              <dd>{profile.specialty || <span className="doctor-empty">—</span>}</dd>
            </div>
            <div className="doctor-profile-row">
              <dt>Credential reference</dt>
              <dd>{profile.credential_reference || <span className="doctor-empty">—</span>}</dd>
            </div>
            <div className="doctor-profile-row">
              <dt>Credential body</dt>
              <dd>{profile.credential_body || <span className="doctor-empty">—</span>}</dd>
            </div>
            <div className="doctor-profile-row">
              <dt>Bio</dt>
              <dd className="doctor-profile-bio">
                {profile.bio || <span className="doctor-empty">—</span>}
              </dd>
            </div>
            <div className="doctor-profile-row">
              <dt>Profile created</dt>
              <dd>
                <time dateTime={profile.created_at}>
                  {new Date(profile.created_at).toLocaleDateString()}
                </time>
              </dd>
            </div>
          </dl>

          {profile.verification_status === "rejected" && (
            <button
              className="doctor-resubmit-btn"
              onClick={() => setState("edit")}
              id="resubmit-profile-btn"
            >
              Update &amp; re-submit for verification
            </button>
          )}
        </div>
      )}

      {/* Create / Edit form */}
      {(state === "create" || state === "edit") && (
        <form
          id="doctor-profile-form"
          className="doctor-profile-form"
          onSubmit={state === "create" ? handleCreate : handleUpdate}
        >
          <div className="doctor-form-field">
            <label htmlFor="doctor-specialty">Specialty</label>
            <input
              id="doctor-specialty"
              type="text"
              value={specialty}
              onChange={(e) => setSpecialty(e.target.value)}
              maxLength={120}
              placeholder="e.g. Cardiology, General Practice"
              disabled={saving}
            />
          </div>
          <div className="doctor-form-field">
            <label htmlFor="doctor-cred-ref">
              Medical registration / license number
            </label>
            <input
              id="doctor-cred-ref"
              type="text"
              value={credRef}
              onChange={(e) => setCredRef(e.target.value)}
              maxLength={200}
              placeholder="e.g. GMC1234567"
              disabled={saving}
            />
            <p className="doctor-form-hint">
              Opaque reference only — this is not stored as a verified identifier.
              <br />
              <strong>Changing this field will reset your verification status to Pending.</strong>
            </p>
          </div>
          <div className="doctor-form-field">
            <label htmlFor="doctor-cred-body">Issuing body</label>
            <input
              id="doctor-cred-body"
              type="text"
              value={credBody}
              onChange={(e) => setCredBody(e.target.value)}
              maxLength={120}
              placeholder="e.g. GMC, NMC, MCI"
              disabled={saving}
            />
          </div>
          <div className="doctor-form-field">
            <label htmlFor="doctor-bio">Professional bio</label>
            <textarea
              id="doctor-bio"
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              rows={4}
              maxLength={2000}
              placeholder="Optional brief professional biography"
              disabled={saving}
            />
          </div>

          <div className="doctor-form-actions">
            <button
              type="button"
              className="doctor-cancel-btn"
              onClick={() => {
                if (profile) {
                  populateForm(profile);
                  setState("view");
                } else {
                  setState("none");
                }
              }}
              disabled={saving}
            >
              Cancel
            </button>
            <button
              id="save-doctor-profile-btn"
              type="submit"
              className="doctor-save-btn"
              disabled={saving}
              aria-busy={saving}
            >
              {saving ? "Saving…" : state === "create" ? "Create profile" : "Save changes"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
