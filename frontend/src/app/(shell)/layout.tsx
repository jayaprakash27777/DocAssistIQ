/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/**
 * DocAssistIQ — Authenticated Shell Layout.
 *
 * Wraps all authenticated pages with:
 *   - AuthProvider (loads user from API, provides useAuth())
 *   - ToastProvider (global toast notifications)
 *   - Sidebar (collapsible navigation)
 *   - Header (top bar with profile dropdown)
 *   - Error boundary
 *   - Auth gate: unauthenticated → /login, forbidden → 403 panel
 *
 * This is the Next.js layout for the (shell) route group.
 * URL paths are unchanged (no /shell prefix).
 */

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthProvider, useAuth } from "@/lib/auth-context";
import { ToastProvider } from "@/components/shell/ToastProvider";
import { ErrorBoundary } from "@/components/shell/ErrorBoundary";
import { Sidebar } from "@/components/shell/Sidebar";
import { Header } from "@/components/shell/Header";
import { DashboardSkeleton } from "@/components/shell/LoadingSkeleton";
import { CommandPalette } from "@/components/shell/CommandPalette";

// ── Inner layout (reads auth context) ────────────────────────

function ShellInner({ children }: { children: React.ReactNode }) {
  const { state } = useAuth();
  const router = useRouter();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    if (state.status === "unauthenticated") {
      const path = typeof window !== "undefined" ? window.location.pathname : "/dashboard";
      router.replace(`/login?next=${encodeURIComponent(path)}`);
    }
  }, [state.status, router]);

  if (state.status === "loading") {
    return (
      <div className="shell-loading" aria-live="polite" aria-busy="true">
        <DashboardSkeleton />
      </div>
    );
  }

  if (state.status === "unauthenticated") {
    // Redirect in progress — render nothing
    return null;
  }

  if (state.status === "forbidden") {
    return (
      <div className="shell-forbidden" role="alert">
        <div className="forbidden-shell">
          <div className="forbidden-card">
            <div className="forbidden-icon" aria-hidden="true">
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2.5">
                <circle cx="24" cy="24" r="22" />
                <path d="M15 15L33 33M33 15L15 33" strokeLinecap="round" />
              </svg>
            </div>
            <h1 className="forbidden-title">Access Denied</h1>
            <p className="forbidden-text">
              Your account does not have sufficient permissions to access this area.
              Contact your administrator if you believe this is an error.
            </p>
            <p className="forbidden-safety-notice">
              REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED
            </p>
            <div className="forbidden-actions">
              <a href="/login" className="forbidden-btn-secondary">Sign in with a different account</a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="shell">
      <Sidebar
        mobileOpen={mobileNavOpen}
        onMobileClose={() => setMobileNavOpen(false)}
      />
      <div className="shell-content">
        <Header onMenuToggle={() => setMobileNavOpen((o) => !o)} />
        <main className="shell-main" id="main-content" tabIndex={-1}>
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </main>
      </div>
      <CommandPalette />
    </div>
  );
}

// ── Exported layout ───────────────────────────────────────────

export default function ShellLayout({ children }: { children: React.ReactNode }) {
  return (
    <ToastProvider>
      <AuthProvider>
        <ShellInner>{children}</ShellInner>
      </AuthProvider>
    </ToastProvider>
  );
}
