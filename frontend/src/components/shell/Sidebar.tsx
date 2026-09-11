/**
 * DocAssistIQ — Sidebar Navigation.
 *
 * Collapsible sidebar with:
 *   - Role-aware nav items (admin sees Administration)
 *   - Collapse/expand toggle (persisted in localStorage)
 *   - Keyboard: Escape collapses on mobile overlay
 *   - Icon-only collapsed mode (56px wide)
 *   - Full label expanded mode (240px)
 *   - Responsive: hidden off-screen on mobile, shown as overlay
 *   - Reduced-motion: no slide animation
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { SidebarItem } from "./SidebarItem";

const STORAGE_KEY = "docassistiq_sidebar_collapsed";

// Nav icons
const Icons = {
  dashboard: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" />
      <rect x="14" y="3" width="7" height="7" />
      <rect x="14" y="14" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" />
    </svg>
  ),
  consultations: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.99 12 19.79 19.79 0 0 1 1.99 3.38a2 2 0 0 1 2-2.18h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z" />
    </svg>
  ),
  notes: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14,2 14,8 20,8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10,9 9,9 8,9" />
    </svg>
  ),
  admin: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
      <path d="M4.93 4.93a10 10 0 0 0 0 14.14" />
    </svg>
  ),
  profile: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  ),
  files: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="12" y1="18" x2="12" y2="12" />
      <line x1="9" y1="15" x2="15" y2="15" />
    </svg>
  ),
};

interface Props {
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function Sidebar({ mobileOpen, onMobileClose }: Props) {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [collapsed, setCollapsed] = useState<boolean>(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem(STORAGE_KEY) === "true";
  });

  const toggleCollapse = useCallback(() => {
    setCollapsed((c) => {
      const next = !c;
      localStorage.setItem(STORAGE_KEY, String(next));
      return next;
    });
  }, []);

  // Escape closes mobile overlay
  useEffect(() => {
    if (!mobileOpen) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onMobileClose();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [mobileOpen, onMobileClose]);

  return (
    <>
      {/* Mobile overlay backdrop */}
      {mobileOpen && (
        <div
          className="sidebar-backdrop"
          aria-hidden="true"
          onClick={onMobileClose}
        />
      )}

      <aside
        className={[
          "sidebar",
          collapsed ? "sidebar--collapsed" : "",
          mobileOpen ? "sidebar--mobile-open" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label="Main navigation"
      >
        {/* Brand + toggle */}
        <div className="sidebar-header">
          {!collapsed && (
            <div className="sidebar-brand">
              <span className="sidebar-brand-name">DocAssistIQ</span>
              <span className="sidebar-brand-tag">Clinical Decision Support</span>
            </div>
          )}
          <button
            className="sidebar-toggle"
            onClick={toggleCollapse}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-expanded={!collapsed}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              aria-hidden="true"
            >
              {collapsed ? (
                <path d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              ) : (
                <path d="M11 5l-7 7 7 7M19 5l-7 7 7 7" />
              )}
            </svg>
          </button>
        </div>

        {/* Nav */}
        <nav className="sidebar-nav" aria-label="Application sections">
          <SidebarItem
            href="/dashboard"
            label="Dashboard"
            icon={Icons.dashboard}
            collapsed={collapsed}
          />
          <SidebarItem
            href="/consultations"
            label="Consultations"
            icon={Icons.consultations}
            collapsed={collapsed}
          />
          <SidebarItem
            href="/notes"
            label="Clinical Notes"
            icon={Icons.notes}
            collapsed={collapsed}
          />
          <SidebarItem
            href="/files"
            label="File Storage"
            icon={Icons.files}
            collapsed={collapsed}
          />
          <SidebarItem
            href="/hub"
            label="Clinical Hub"
            icon={Icons.dashboard}
            collapsed={collapsed}
          />
          <SidebarItem
            href="/profile"
            label="My Profile"
            icon={Icons.profile}
            collapsed={collapsed}
          />
          {isAdmin && (
            <SidebarItem
              href="/admin"
              label="Administration"
              icon={Icons.admin}
              collapsed={collapsed}
            />
          )}
        </nav>

        {/* Footer status */}
        {!collapsed && (
          <div className="sidebar-footer">
            <span className="sidebar-footer-label">
              REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED
            </span>
          </div>
        )}
      </aside>
    </>
  );
}
