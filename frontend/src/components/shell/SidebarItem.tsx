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
          className="absolute inset-0 bg-gradient-to-r from-[var(--color-primary-50)] via-[var(--color-primary-50)] to-white/80 rounded-xl border border-[var(--color-primary-200)] shadow-[0_2px_10px_rgba(75,170,160,0.12),inset_0_1px_0_rgba(255,255,255,0.95)]"
          transition={{ type: "spring", stiffness: 350, damping: 30 }}
        >
          {!collapsed && (
            <div className="absolute left-0 top-2.5 bottom-2.5 w-1 rounded-r-full bg-[var(--color-primary-600)] shadow-sm" />
          )}
        </motion.div>
      )}
      <span className={`sidebar-item-icon relative z-10 flex items-center justify-center ${isActive ? "text-[var(--color-primary-700)]" : "text-slate-500"}`} aria-hidden="true">
        {icon}
      </span>
      {!collapsed && <span className={`relative z-10 font-bold ml-1 tracking-tight ${isActive ? "text-[var(--color-primary-900)]" : "text-slate-700"}`}>{label}</span>}
    </Link>
  );
}
