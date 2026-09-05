"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { authGetMe, authLogout, getStoredToken, type MeResponse } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
        setError("Unable to load your profile. Please sign in again.");
        router.replace("/login?next=/dashboard");
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

  if (error || !user) {
    return (
      <div className="dashboard-error" role="alert">
        {error ?? "Something went wrong. Please sign in."}
      </div>
    );
  }

  return (
    <div className="dashboard-shell">
      <header className="dashboard-header">
        <div className="dashboard-brand">
          <span className="dashboard-logo">DocAssistIQ</span>
          <span className="dashboard-logo-tag">Clinical Decision Support</span>
        </div>
        <div className="dashboard-header-right">
          <span className="dashboard-user-pill">
            <span className="dashboard-user-role">{user.role}</span>
            <span className="dashboard-user-name">{user.full_name}</span>
          </span>
          <button id="logout-btn" className="dashboard-logout-btn" onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="dashboard-welcome">
          <h1 className="dashboard-welcome-title">Welcome, {user.full_name}</h1>
          <p className="dashboard-welcome-sub">
            Your clinical workspace is ready. More features will appear as the platform
            is built out in subsequent phases.
          </p>
        </div>

        <div className="dashboard-cards">
          <div className="dashboard-card">
            <div className="dashboard-card-icon">👤</div>
            <div className="dashboard-card-body">
              <h2 className="dashboard-card-title">Account</h2>
              <dl className="dashboard-card-dl">
                <dt>Email</dt><dd>{user.email}</dd>
                <dt>Role</dt><dd className="dashboard-card-role">{user.role}</dd>
                <dt>Verified</dt><dd>{user.is_verified ? "Yes" : "Pending"}</dd>
              </dl>
            </div>
          </div>

          <div className="dashboard-card dashboard-card--coming-soon">
            <div className="dashboard-card-icon">🩺</div>
            <div className="dashboard-card-body">
              <h2 className="dashboard-card-title">Consultations</h2>
              <p className="dashboard-card-hint">Coming in Phase 8 — Patient & Consultation Management</p>
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
