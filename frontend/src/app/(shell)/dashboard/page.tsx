/**
 * DocAssistIQ — Dashboard Page.
 *
 * The main workspace screen for authenticated users.
 * Auth state is provided by the shell layout via AuthContext —
 * this page does NOT call authGetMe() directly.
 *
 * Displays:
 *   - Welcome heading (with admin badge for admin users)
 *   - Account info card (real data from API)
 *   - Consultations placeholder (coming Phase 8)
 *   - Clinical Notes placeholder
 *   - Admin panel (admin role only)
 *
 * No fake metrics or hardcoded statistics.
 */

"use client";

import { useAuth } from "@/lib/auth-context";

export default function DashboardPage() {
  const { user } = useAuth();

  // Shell layout handles loading/auth states — user is always non-null here
  if (!user) return null;

  const isAdmin = user.role === "admin";

  return (
    <div className="dashboard-page">
      {/* Welcome */}
      <section className="dashboard-welcome" aria-labelledby="dashboard-heading">
        <h2 id="dashboard-heading" className="dashboard-welcome-title">
          Welcome, {user.full_name}
          {isAdmin && (
            <span className="dashboard-admin-badge" aria-label="Administrator">
              Admin
            </span>
          )}
        </h2>
        <p className="dashboard-welcome-sub">
          Your clinical workspace. Features will expand in subsequent phases.
        </p>
      </section>

      {/* Admin panel */}
      {isAdmin && (
        <div
          className="dashboard-admin-panel"
          role="region"
          aria-label="Administration"
        >
          <div className="dashboard-admin-panel-icon" aria-hidden="true">⚙</div>
          <div className="dashboard-admin-panel-body">
            <h3 className="dashboard-admin-panel-title">Administration</h3>
            <p className="dashboard-admin-panel-text">
              You have administrator access. Administrative controls will be
              available in a later phase.
            </p>
          </div>
        </div>
      )}

      {/* Cards */}
      <div className="dashboard-cards">
        {/* Account card — real API data */}
        <div className="dashboard-card">
          <div className="dashboard-card-icon" aria-hidden="true">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </div>
          <div className="dashboard-card-body">
            <h3 className="dashboard-card-title">Account</h3>
            <dl className="dashboard-card-dl">
              <dt>Email</dt>
              <dd>{user.email}</dd>
              <dt>Role</dt>
              <dd>
                <span
                  className={`dashboard-card-role${isAdmin ? " dashboard-card-role--admin" : ""}`}
                >
                  {user.role}
                </span>
              </dd>
              <dt>Verified</dt>
              <dd>{user.is_verified ? "Yes" : "Pending"}</dd>
              <dt>Member since</dt>
              <dd>{new Date(user.created_at).toLocaleDateString()}</dd>
            </dl>
          </div>
        </div>

        {/* Consultations — placeholder */}
        <div className="dashboard-card dashboard-card--coming-soon">
          <div className="dashboard-card-icon" aria-hidden="true">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.99 12 19.79 19.79 0 0 1 1.99 3.38a2 2 0 0 1 2-2.18h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z" />
            </svg>
          </div>
          <div className="dashboard-card-body">
            <h3 className="dashboard-card-title">Consultations</h3>
            <p className="dashboard-card-hint">
              Coming in Phase 8 — Patient &amp; Consultation Management
            </p>
          </div>
        </div>

        {/* Clinical Notes — placeholder */}
        <div className="dashboard-card dashboard-card--coming-soon">
          <div className="dashboard-card-icon" aria-hidden="true">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14,2 14,8 20,8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
          </div>
          <div className="dashboard-card-body">
            <h3 className="dashboard-card-title">Clinical Notes</h3>
            <p className="dashboard-card-hint">Coming in a later phase</p>
          </div>
        </div>
      </div>

      {/* Clinical safety notice */}
      <p className="dashboard-safety-notice" role="note">
        REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED
      </p>
    </div>
  );
}
