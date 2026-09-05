"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { authGetMe, authLogout, getStoredToken, type MeResponse } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      router.replace("/login?next=/dashboard");
      return;
    }

    authGetMe().then((result) => {
      if (result.ok) {
        setUser(result.data);
      } else {
        // 403 Forbidden — account exists but role insufficient
        if (result.statusCode === 403) {
          setForbidden(true);
        } else {
          // 401 or other error — redirect to login
          router.replace("/login?next=/dashboard");
        }
      }
      setLoading(false);
    });
  }, [router]);

  async function handleLogout() {
    await authLogout();
    router.replace("/login");
  }

  if (loading) {
    return (
      <div className="dashboard-loading" aria-live="polite" aria-busy="true">
        <div className="dashboard-spinner" />
        <span>Loading your workspace…</span>
      </div>
    );
  }

  // 403 — account suspended or role issue
  if (forbidden) {
    return (
      <div className="dashboard-forbidden" role="alert">
        <div className="dashboard-forbidden-icon" aria-hidden="true">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="24" cy="24" r="22" stroke="currentColor" strokeWidth="2.5" />
            <path d="M15 15L33 33M33 15L15 33" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
          </svg>
        </div>
        <h1 className="dashboard-forbidden-title">Access Denied</h1>
        <p className="dashboard-forbidden-msg">
          Your account does not have permission to access the dashboard.
          Contact your administrator if you believe this is an error.
        </p>
        <button className="dashboard-logout-btn" onClick={handleLogout}>
          Sign Out
        </button>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="dashboard-error" role="alert">
        {error ?? "Something went wrong. Please sign in."}
      </div>
    );
  }

  const isAdmin = user.role === "admin";

  return (
    <div className="dashboard-shell">
      <header className="dashboard-header">
        <div className="dashboard-brand">
          <span className="dashboard-logo">DocAssistIQ</span>
          <span className="dashboard-logo-tag">Clinical Decision Support</span>
        </div>
        <div className="dashboard-header-right">
          <span className="dashboard-user-pill">
            <span
              className={`dashboard-user-role${isAdmin ? " dashboard-user-role--admin" : ""}`}
              title={isAdmin ? "Administrator account" : "Clinician account"}
            >
              {isAdmin ? "Admin" : user.role}
            </span>
            <span className="dashboard-user-name">{user.full_name}</span>
          </span>
          <button id="logout-btn" className="dashboard-logout-btn" onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="dashboard-welcome">
          <h1 className="dashboard-welcome-title">
            Welcome, {user.full_name}
            {isAdmin && (
              <span className="dashboard-admin-badge" aria-label="Administrator">
                Admin
              </span>
            )}
          </h1>
          <p className="dashboard-welcome-sub">
            Your clinical workspace is ready. More features will appear as the platform
            is built out in subsequent phases.
          </p>
        </div>

        {/* Admin panel notice */}
        {isAdmin && (
          <div className="dashboard-admin-panel" role="region" aria-label="Administration">
            <div className="dashboard-admin-panel-icon" aria-hidden="true">⚙️</div>
            <div className="dashboard-admin-panel-body">
              <h2 className="dashboard-admin-panel-title">Administration</h2>
              <p className="dashboard-admin-panel-text">
                You have administrator access. Additional administrative controls
                will appear here in a later phase.
              </p>
            </div>
          </div>
        )}

        <div className="dashboard-cards">
          <div className="dashboard-card">
            <div className="dashboard-card-icon">👤</div>
            <div className="dashboard-card-body">
              <h2 className="dashboard-card-title">Account</h2>
              <dl className="dashboard-card-dl">
                <dt>Email</dt><dd>{user.email}</dd>
                <dt>Role</dt>
                <dd>
                  <span className={`dashboard-card-role${isAdmin ? " dashboard-card-role--admin" : ""}`}>
                    {user.role}
                  </span>
                </dd>
                <dt>Verified</dt><dd>{user.is_verified ? "Yes" : "Pending"}</dd>
              </dl>
            </div>
          </div>

          <div className="dashboard-card dashboard-card--coming-soon">
            <div className="dashboard-card-icon">🩺</div>
            <div className="dashboard-card-body">
              <h2 className="dashboard-card-title">Consultations</h2>
              <p className="dashboard-card-hint">Coming in Phase 8 — Patient &amp; Consultation Management</p>
            </div>
          </div>

          <div className="dashboard-card dashboard-card--coming-soon">
            <div className="dashboard-card-icon">📋</div>
            <div className="dashboard-card-body">
              <h2 className="dashboard-card-title">Clinical Notes</h2>
              <p className="dashboard-card-hint">Coming in a later phase</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
