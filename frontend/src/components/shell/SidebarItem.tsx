/* eslint-disable @typescript-eslint/no-unused-vars */
/**
 * DocAssistIQ — Sidebar Navigation Item.
 *
 * A single nav item in the sidebar. Renders as a Next.js <Link>.
 * Marks itself as active (aria-current="page") when href matches.
 */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";

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
      className={`sidebar-item ${isActive ? "sidebar-item--active" : ""} ${collapsed ? "justify-center px-0" : ""}`}
      aria-current={isActive ? "page" : undefined}
      title={collapsed ? label : undefined}
    >
      {isActive && (
        <motion.div
          layoutId="sidebar-active-pill"
          className="absolute inset-0 bg-[var(--color-primary-50)] rounded-xl border border-[var(--color-primary-200)] shadow-sm"
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
        />
      )}
      <span className="sidebar-item-icon relative z-10 flex items-center justify-center" aria-hidden="true">
        {icon}
      </span>
      {!collapsed && <span className="relative z-10 font-bold ml-1">{label}</span>}
    </Link>
  );
}
