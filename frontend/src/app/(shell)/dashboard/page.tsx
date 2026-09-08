/**
 * DocAssistIQ — Dashboard Page (Enhanced).
 *
 * Displays real-time stats from the API including consultation counts,
 * recent activity, and system status. No fake metrics.
 */

"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { listConsultations, type ConsultationSummary } from "@/lib/api";

interface DashboardStats {
  totalConsultations: number;
  recentConsultations: ConsultationSummary[];
  loading: boolean;
}

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  created: { label: "New", color: "var(--color-neutral-500)" },
  recording: { label: "Recording", color: "var(--color-danger-500)" },
  processing: { label: "Processing", color: "var(--color-warning-500)" },
  draft: { label: "Draft", color: "var(--color-primary-500)" },
  under_review: { label: "Review", color: "var(--color-warning-700)" },
  analysis_ready: { label: "Ready", color: "var(--color-success-500)" },
  finalized: { label: "Finalized", color: "var(--color-success-700)" },
  amended: { label: "Amended", color: "var(--color-neutral-600)" },
};

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    totalConsultations: 0,
    recentConsultations: [],
    loading: true,
  });

  useEffect(() => {
    async function loadStats() {
      // listConsultations(page, page_size) — page 1, 5 items
      const res = await listConsultations(1, 5);
      if (res.ok) {
        setStats({
          totalConsultations: res.data.total,
          recentConsultations: res.data.items,
          loading: false,
        });
      } else {
        setStats((s) => ({ ...s, loading: false }));
      }
    }
    loadStats();
  }, []);

  if (!user) return null;

  const isAdmin = user.role === "admin";
  const memberSince = new Date(user.created_at).toLocaleDateString("en-GB", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="dashboard-page">
      {/* Welcome header */}
      <section className="dashboard-welcome" aria-labelledby="dashboard-heading">
        <div className="dashboard-welcome-inner">
          <div className="dashboard-avatar" aria-hidden="true">
            {user.full_name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h1 id="dashboard-heading" className="dashboard-welcome-title">
              Welcome back, {user.full_name}
              {isAdmin && (
                <span className="dashboard-admin-badge" aria-label="Administrator">
                  Admin
                </span>
              )}
            </h1>
            <p className="dashboard-welcome-sub">
              {isAdmin ? "Clinical Operations Dashboard" : "Your Clinical Workspace"}
            </p>
          </div>
        </div>
      </section>

      {/* Stats row */}
      <div className="dashboard-stats">
        <div className="dashboard-stat-card">
          <div className="dashboard-stat-icon" aria-hidden="true">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.99 12 19.79 19.79 0 0 1 1.99 3.38a2 2 0 0 1 2-2.18h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>
            </svg>
          </div>
          <div className="dashboard-stat-body">
            <span className="dashboard-stat-value">
              {stats.loading ? "—" : stats.totalConsultations}
            </span>
            <span className="dashboard-stat-label">Total Consultations</span>
          </div>
        </div>

        <div className="dashboard-stat-card">
          <div className="dashboard-stat-icon dashboard-stat-icon--green" aria-hidden="true">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
          <div className="dashboard-stat-body">
            <span className="dashboard-stat-value">{user.role}</span>
            <span className="dashboard-stat-label">Account Role</span>
          </div>
        </div>

        <div className="dashboard-stat-card">
          <div className="dashboard-stat-icon dashboard-stat-icon--amber" aria-hidden="true">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
              <line x1="16" y1="2" x2="16" y2="6"/>
              <line x1="8" y1="2" x2="8" y2="6"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
          </div>
          <div className="dashboard-stat-body">
            <span className="dashboard-stat-value dashboard-stat-value--sm">{memberSince}</span>
            <span className="dashboard-stat-label">Member Since</span>
          </div>
        </div>

        <div className="dashboard-stat-card">
          <div
            className={`dashboard-stat-icon ${user.is_verified ? "dashboard-stat-icon--green" : "dashboard-stat-icon--amber"}`}
            aria-hidden="true"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {user.is_verified ? (
                <path d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/>
              ) : (
                <circle cx="12" cy="12" r="10"/>
              )}
            </svg>
          </div>
          <div className="dashboard-stat-body">
            <span className="dashboard-stat-value">{user.is_verified ? "Verified" : "Pending"}</span>
            <span className="dashboard-stat-label">Verification</span>
          </div>
        </div>
      </div>

      {/* Quick actions */}
      <div className="dashboard-actions">
        <Link href="/consultations/new" className="dashboard-action-btn dashboard-action-btn--primary">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          New Consultation
        </Link>
        <Link href="/consultations" className="dashboard-action-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.99 12 19.79 19.79 0 0 1 1.99 3.38a2 2 0 0 1 2-2.18h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>
          </svg>
          View All Consultations
        </Link>
        <Link href="/profile" className="dashboard-action-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
          My Profile
        </Link>
        {isAdmin && (
          <Link href="/admin" className="dashboard-action-btn dashboard-action-btn--admin">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
            Admin Panel
          </Link>
        )}
      </div>

      {/* Recent consultations */}
      <section className="dashboard-section" aria-labelledby="recent-heading">
        <div className="dashboard-section-header">
          <h2 id="recent-heading" className="dashboard-section-title">Recent Consultations</h2>
          <Link href="/consultations" className="dashboard-section-link">View all →</Link>
        </div>

        {stats.loading ? (
          <div className="dashboard-list-skeleton" aria-busy="true" aria-label="Loading consultations">
            {[1, 2, 3].map((i) => (
              <div key={i} className="dashboard-skeleton-row" />
            ))}
          </div>
        ) : stats.recentConsultations.length === 0 ? (
          <div className="dashboard-empty">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.99 12 19.79 19.79 0 0 1 1.99 3.38a2 2 0 0 1 2-2.18h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>
            </svg>
            <p>No consultations yet.</p>
            <Link href="/consultations/new" className="dashboard-empty-link">Start your first consultation →</Link>
          </div>
        ) : (
          <ul className="dashboard-consultation-list" role="list">
            {stats.recentConsultations.map((c) => {
              const statusInfo = STATUS_LABELS[c.status] ?? { label: c.status, color: "var(--color-neutral-500)" };
              return (
                <li key={c.id} className="dashboard-consultation-item">
                  <Link href={`/consultations/${c.id}`} className="dashboard-consultation-link">
                    <div className="dashboard-consultation-id">
                      <span className="dashboard-consultation-id-label">ID</span>
                      <code>{c.id.slice(0, 8)}…</code>
                    </div>
                    <div className="dashboard-consultation-meta">
                      <span
                        className="dashboard-consultation-status"
                        style={{ color: statusInfo.color }}
                        aria-label={`Status: ${statusInfo.label}`}
                      >
                        ● {statusInfo.label}
                      </span>
                      <time
                        className="dashboard-consultation-time"
                        dateTime={c.created_at}
                      >
                        {new Date(c.created_at).toLocaleDateString()}
                      </time>
                    </div>
                    <svg className="dashboard-consultation-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                      <polyline points="9 18 15 12 9 6"/>
                    </svg>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {/* Clinical safety notice */}
      <p className="dashboard-safety-notice" role="note">
        REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED
      </p>
    </div>
  );
}
