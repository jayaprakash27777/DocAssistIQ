/* eslint-disable @typescript-eslint/no-unused-vars */
/**
 * DocAssistIQ — Shell Header.
 *
 * Top header bar:
 *   - Left: hamburger button (mobile sidebar toggle), page title
 *   - Right: NotificationBell, ProfileDropdown
 */

"use client";

import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { NotificationBell } from "./NotificationBell";
import { ProfileDropdown } from "./ProfileDropdown";
import { WsStatus } from "./WsStatus";
import { ThemeToggle } from "@/components/ThemeToggle";

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/ai": "Clinical AI Assistant",
  "/consultations": "Consultations",
  "/notes": "Clinical Notes",
  "/files": "File Storage",
  "/patients": "Patient Longitudinal Records",
  "/hub": "Medical Intelligence Hub",
  "/profile": "My Profile",
  "/admin": "Administration",
  "/admin/doctors": "Doctor Verifications",
  "/admin/sources": "Medical Sources",
  "/admin/ingestion": "Knowledge Ingestion",
  "/admin/knowledge": "Knowledge Publication",
  "/admin/datasets": "Dataset Registry & Governance",
  "/admin/evaluations": "Baseline Evaluation Harness",
  "/admin/experiments": "ML Experiment Tracking",
};

function getPageTitle(pathname: string): string {
  if (PAGE_TITLES[pathname]) return PAGE_TITLES[pathname];
  // Match prefix (e.g. /consultations/123)
  for (const [prefix, title] of Object.entries(PAGE_TITLES)) {
    if (pathname.startsWith(prefix + "/")) return title;
  }
  return "DocAssistIQ";
}

interface Props {
  onMenuToggle: () => void;
}

export function Header({ onMenuToggle }: Props) {
  const pathname = usePathname();
  const { user } = useAuth();
  const title = getPageTitle(pathname);

  return (
    <header className="shell-header border-b border-slate-200/60 bg-white/80 backdrop-blur-2xl shadow-[0_4px_24px_rgba(0,0,0,0.02),inset_0_1px_0_rgba(255,255,255,0.9)]" role="banner">
      <div className="shell-header-left flex items-center gap-3">
        {/* Mobile hamburger */}
        <button
          id="sidebar-toggle-btn"
          className="header-menu-btn p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100/80 transition-colors"
          onClick={onMenuToggle}
          aria-label="Toggle navigation menu"
          aria-haspopup="dialog"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            aria-hidden="true"
          >
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>

        <h1 className="shell-header-title text-xl font-extrabold tracking-tight bg-gradient-to-r from-slate-900 via-slate-800 to-slate-700 bg-clip-text text-transparent">{title}</h1>
      </div>

      <div className="shell-header-right flex items-center gap-3">
        <div 
          className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20 text-xs font-semibold shadow-xs"
          title="Clinical Reasoning Engine: II-Medical-8B Active"
        >
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="font-mono text-[11px] tracking-wide">II-Medical:8B</span>
        </div>
        <ThemeToggle />
        <WsStatus />
        <NotificationBell unreadCount={0} />
        {user && <ProfileDropdown user={user} />}
      </div>
    </header>
  );
}
