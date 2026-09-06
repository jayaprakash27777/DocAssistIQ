/**
 * DocAssistIQ — Sidebar Navigation Item.
 *
 * A single nav item in the sidebar. Renders as a Next.js <Link>.
 * Marks itself as active (aria-current="page") when href matches.
 */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
  /** If true, item only appears when sidebar is expanded */
  labelOnly?: boolean;
}

interface Props extends NavItem {
  collapsed: boolean;
}

export function SidebarItem({ href, label, icon, collapsed }: Props) {
  const pathname = usePathname();
  const isActive = pathname === href || pathname.startsWith(href + "/");

  return (
    <Link
      href={href}
      className={`nav-item ${isActive ? "nav-item--active" : ""} ${collapsed ? "nav-item--collapsed" : ""}`}
      aria-current={isActive ? "page" : undefined}
      title={collapsed ? label : undefined}
    >
      <span className="nav-item-icon" aria-hidden="true">
        {icon}
      </span>
      {!collapsed && <span className="nav-item-label">{label}</span>}
    </Link>
  );
}
