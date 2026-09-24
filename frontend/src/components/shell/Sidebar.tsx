/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
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
  ai: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z" />
      <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z" />
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
        <div className="sidebar-header flex items-center justify-between px-3.5 border-b border-[var(--border-default)]">
          {!collapsed && (
            <div className="sidebar-brand flex items-center gap-3 overflow-hidden">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-teal-600 to-teal-400 flex items-center justify-center text-white shadow-md shadow-teal-500/20 ring-1 ring-white/40 shrink-0">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 4v16m-8-8h16" />
                </svg>
              </div>
              <div className="flex flex-col min-w-0">
                <span className="sidebar-brand-name font-black tracking-tight text-[1.05rem] bg-gradient-to-r from-teal-800 to-slate-900 bg-clip-text text-transparent leading-snug truncate">
                  DocAssistIQ
                </span>
                <span className="sidebar-brand-tag text-[9px] font-bold tracking-wider text-slate-400 uppercase leading-none truncate">
                  Clinical Decision Support
                </span>
              </div>
            </div>
          )}
          {collapsed && (
            <div className="w-9 h-9 mx-auto rounded-xl bg-gradient-to-tr from-teal-600 to-teal-400 flex items-center justify-center text-white shadow-md shadow-teal-500/20 ring-1 ring-white/40 shrink-0" title="DocAssistIQ">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 4v16m-8-8h16" />
              </svg>
            </div>
          )}
          <button
            className="sidebar-toggle p-2 rounded-xl text-slate-500 hover:text-[var(--color-primary-700)] hover:bg-[var(--sidebar-hover-bg)] border border-transparent hover:border-[var(--color-primary-200)] transition-all"
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
              strokeWidth="2.5"
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
            href="/ai"
            label="AI Intelligence"
            icon={Icons.ai}
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
          <div className="sidebar-footer p-3 mx-3 mb-3 rounded-2xl bg-slate-50 border border-slate-200/80 shadow-[inset_0_1px_2px_rgba(0,0,0,0.02)]">
            <span className="text-[10px] leading-snug font-bold uppercase tracking-wider text-slate-400 text-center block">
              Reference Information
            </span>
            <span className="text-[9px] leading-tight font-medium text-slate-400 text-center block mt-0.5">
              Clinician Review Required
            </span>
          </div>
        )}
      </aside>
    </>
  );
}
