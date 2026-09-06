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

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/consultations": "Consultations",
  "/notes": "Clinical Notes",
  "/profile": "My Profile",
  "/admin": "Administration",
  "/admin/doctors": "Doctor Verifications",
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
    <header className="shell-header" role="banner">
      <div className="shell-header-left">
        {/* Mobile hamburger */}
        <button
          id="sidebar-toggle-btn"
          className="header-menu-btn"
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

        <h1 className="shell-header-title">{title}</h1>
      </div>

      <div className="shell-header-right">
        <WsStatus />
        <NotificationBell unreadCount={0} />
        {user && <ProfileDropdown user={user} />}
      </div>
    </header>
  );
}
