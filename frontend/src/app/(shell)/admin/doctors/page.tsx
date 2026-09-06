/**
 * DocAssistIQ — Admin Doctor Verification Page (/admin/doctors).
 *
 * Admin-only page. Lists doctors with pending verification.
 * Admin can approve (verify) or reject with a mandatory reason.
 *
 * States:
 *   - loading → skeleton rows
 *   - empty → no pending doctors message
 *   - list → table of pending doctors with verify/reject actions
 *   - confirm dialog → confirm action before submitting
 *   - success/error feedback via toast
 */

"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  listPendingDoctors,
  verifyDoctor,
  type DoctorResponse,
} from "@/lib/api";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";

interface ActionState {
  doctor: DoctorResponse;
  action: "verify" | "reject";
  rejectionReason: string;
  saving: boolean;
}

export default function AdminDoctorsPage() {
  const { toast } = useToast();
  const [doctors, setDoctors] = useState<DoctorResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [action, setAction] = useState<ActionState | null>(null);

  const PAGE_SIZE = 20;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    listPendingDoctors(page, PAGE_SIZE).then((r) => {
      if (cancelled) return;
      setLoading(false);
      if (!r.ok) {
        setError(r.error.message ?? "Failed to load pending doctors.");
        return;
      }
      setDoctors(r.data.items);
      setTotal(r.data.total);
      setPages(r.data.pages);
    });

    return () => { cancelled = true; };
  }, [page]);

  async function handleAction(e: FormEvent) {
    e.preventDefault();
    if (!action) return;

    if (action.action === "reject" && !action.rejectionReason.trim()) {
      toast.error("A rejection reason is required.");
      return;
    }

    setAction((a) => a ? { ...a, saving: true } : a);

    const r = await verifyDoctor(action.doctor.id, {
      action: action.action,
      rejection_reason: action.action === "reject" ? action.rejectionReason : undefined,
    });

    if (!r.ok) {
      setAction((a) => a ? { ...a, saving: false } : a);
      toast.error(r.error.message ?? "Action failed.");
      return;
    }

    setAction(null);
    toast.success(
      action.action === "verify"
        ? `Dr. ${action.doctor.credential_reference ?? action.doctor.id} verified.`
        : `Dr. ${action.doctor.credential_reference ?? action.doctor.id} rejected.`,
    );
    // Reload list
    setDoctors((prev) => prev.filter((d) => d.id !== action.doctor.id));
    setTotal((t) => t - 1);
  }

  return (
    <div className="admin-doctors-page">
      <header className="admin-doctors-header">
        <div>
          <h2 className="admin-doctors-title">Doctor Verifications</h2>
          <p className="admin-doctors-subtitle">
            {total > 0 ? `${total} pending review` : "No pending reviews"}
          </p>
        </div>
      </header>

      {/* Loading */}
      {loading && (
        <div aria-busy="true" aria-label="Loading pending doctors…">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="admin-doctors-skeleton-row">
              <Skeleton height="1rem" width="30%" />
              <Skeleton height="0.875rem" width="50%" />
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="admin-doctors-error" role="alert">
          <p>{error}</p>
          <button onClick={() => { setError(null); setPage(1); }}>Retry</button>
        </div>
      )}

      {/* Empty */}
      {!loading && !error && total === 0 && (
        <div className="admin-doctors-empty">
          <div className="admin-doctors-empty-icon" aria-hidden="true">✅</div>
          <h3>No pending verifications</h3>
          <p>All doctor profiles have been reviewed.</p>
        </div>
      )}

      {/* Doctor list */}
      {!loading && !error && doctors.length > 0 && (
        <>
          <div className="admin-doctors-table-wrap">
            <table className="admin-doctors-table" aria-label="Pending doctor verifications">
              <thead>
                <tr>
                  <th scope="col">Doctor ID</th>
                  <th scope="col">Specialty</th>
                  <th scope="col">Credential</th>
                  <th scope="col">Body</th>
                  <th scope="col">Submitted</th>
                  <th scope="col">Actions</th>
                </tr>
              </thead>
              <tbody>
                {doctors.map((d) => (
                  <tr key={d.id}>
                    <td className="admin-doctors-id" title={d.user_id}>
                      {d.user_id.slice(0, 8)}…
                    </td>
                    <td>{d.specialty || <span className="admin-empty">—</span>}</td>
                    <td>{d.credential_reference || <span className="admin-empty">—</span>}</td>
                    <td>{d.credential_body || <span className="admin-empty">—</span>}</td>
                    <td>
                      <time dateTime={d.created_at}>
                        {new Date(d.created_at).toLocaleDateString()}
                      </time>
                    </td>
                    <td className="admin-doctors-actions-cell">
                      <button
                        id={`verify-btn-${d.id}`}
                        className="admin-verify-btn"
                        onClick={() =>
                          setAction({ doctor: d, action: "verify", rejectionReason: "", saving: false })
                        }
                      >
                        Verify
                      </button>
                      <button
                        id={`reject-btn-${d.id}`}
                        className="admin-reject-btn"
                        onClick={() =>
                          setAction({ doctor: d, action: "reject", rejectionReason: "", saving: false })
                        }
                      >
                        Reject
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {pages > 1 && (
            <nav className="admin-doctors-pagination" aria-label="Pages">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="admin-page-btn"
              >
                ← Previous
              </button>
              <span className="admin-page-info">
                Page {page} of {pages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(pages, p + 1))}
                disabled={page >= pages}
                className="admin-page-btn"
              >
                Next →
              </button>
            </nav>
          )}
        </>
      )}

      {/* Action dialog */}
      {action && (
        <div
          className="admin-action-overlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="action-dialog-title"
        >
          <div className="admin-action-dialog">
            <h3 id="action-dialog-title" className="admin-action-title">
              {action.action === "verify" ? "Verify doctor?" : "Reject doctor?"}
            </h3>

            <p className="admin-action-desc">
              {action.action === "verify"
                ? "This will mark the doctor as verified and grant access to clinical features."
                : "This will reject the doctor's verification. Provide a clear reason."}
            </p>

            <form id="admin-action-form" onSubmit={handleAction}>
              {action.action === "reject" && (
                <div className="admin-action-field">
                  <label htmlFor="rejection-reason">
                    Rejection reason <span aria-hidden="true">*</span>
                  </label>
                  <textarea
                    id="rejection-reason"
                    rows={3}
                    value={action.rejectionReason}
                    onChange={(e) =>
                      setAction((a) => a ? { ...a, rejectionReason: e.target.value } : a)
                    }
                    required
                    maxLength={1000}
                    placeholder="Explain why the verification was declined…"
                    disabled={action.saving}
                  />
                </div>
              )}

              <div className="admin-action-buttons">
                <button
                  type="button"
                  className="admin-action-cancel"
                  onClick={() => setAction(null)}
                  disabled={action.saving}
                >
                  Cancel
                </button>
                <button
                  id="confirm-action-btn"
                  type="submit"
                  className={`admin-action-confirm ${
                    action.action === "verify"
                      ? "admin-action-confirm--verify"
                      : "admin-action-confirm--reject"
                  }`}
                  disabled={action.saving}
                  aria-busy={action.saving}
                >
                  {action.saving
                    ? "Processing…"
                    : action.action === "verify"
                    ? "Confirm verify"
                    : "Confirm reject"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
