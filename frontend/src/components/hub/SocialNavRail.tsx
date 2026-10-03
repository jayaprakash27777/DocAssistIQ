"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

interface SocialNavRailProps {
  onOpenCompose?: () => void;
  onOpenComposer?: () => void;
  urgentCasesCount?: number;
  savedCasesCount?: number;
}

export function SocialNavRail({
  onOpenCompose,
  onOpenComposer,
  urgentCasesCount = 0,
  savedCasesCount = 0,
}: SocialNavRailProps) {
  const pathname = usePathname();
  const { user } = useAuth();
  const handleCompose = onOpenComposer || onOpenCompose || (() => {});


  const navItems = [
    {
      href: "/hub",
      label: "Home Timeline",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      ),
      exact: true,
    },
    {
      href: "/hub/emergency",
      label: "Emergency 2nd Opinions",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      ),
      badge: urgentCasesCount > 0 ? `${urgentCasesCount} STAT` : undefined,
      badgeColor: "bg-rose-600 text-white animate-pulse",
    },
    {
      href: "/hub/explore",
      label: "Explore & Trending",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
        </svg>
      ),
    },
    {
      href: "/hub/saved",
      label: "Saved Library",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
        </svg>
      ),
      badge: savedCasesCount > 0 ? `${savedCasesCount}` : undefined,
      badgeColor: "bg-amber-100 text-amber-800 font-bold",
    },
    {
      href: "/hub/profile",
      label: "My Portfolio",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      ),
    },
  ];

  return (
    <aside className="sticky top-6 space-y-4">
      {/* ── Doctor Verified Identity Card ── */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-teal-600 to-emerald-500 text-white font-black text-lg flex items-center justify-center shadow-xs flex-shrink-0">
            {user?.full_name ? user.full_name[0].toUpperCase() : "D"}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-sm text-slate-900 truncate">
                {user?.full_name || "Dr. Attending"}
              </span>
              <span className="inline-flex items-center text-teal-600 text-xs flex-shrink-0" title="Verified Global Clinician">
                <svg className="w-4 h-4 fill-teal-600" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </span>
            </div>
            <p className="text-xs text-slate-500 truncate">
              {(user as any)?.specialty || user?.role || "Verified Physician"}
            </p>
            <div className="mt-1 flex items-center gap-1.5">
              <span className="text-[10px] font-bold bg-teal-50 text-teal-700 px-2 py-0.5 rounded-md border border-teal-100">
                GMC • NMC • USMLE Verified
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Main Social Navigation Menu ── */}
      <nav className="bg-white rounded-2xl border border-slate-200/80 p-2 shadow-xs space-y-1">
        {navItems.map((item) => {
          const isActive = item.exact ? pathname === item.href : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl font-bold text-xs transition-colors ${
                isActive
                  ? "bg-teal-600 text-white shadow-xs"
                  : "text-slate-700 hover:bg-slate-100 hover:text-slate-900"
              }`}
            >
              <div className="flex items-center gap-3">
                <span className={isActive ? "text-white" : "text-slate-500"}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-black ${
                    isActive ? "bg-white text-teal-800" : item.badgeColor || "bg-slate-100 text-slate-700"
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* ── Quick Share Clinical Case Button ── */}
      <button
        type="button"
        onClick={handleCompose}
        className="w-full py-3 px-4 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-extrabold text-sm shadow-sm transition-all flex items-center justify-center gap-2 cursor-pointer"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
        </svg>
        <span>Share Clinical Case</span>
      </button>

      {/* ── Emergency STAT Broadcast Banner ── */}
      <Link
        href="/hub/emergency"
        className="block bg-gradient-to-r from-rose-50 to-red-50 border border-rose-200 rounded-2xl p-3.5 transition-all hover:border-rose-300"
      >
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-500 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-600" />
            </span>
            <span className="text-xs font-black text-rose-900 uppercase tracking-wide">
              Emergency 2nd Opinion
            </span>
          </div>
          <span className="text-[10px] font-black text-rose-700 bg-rose-100 px-2 py-0.5 rounded-md">
            STAT
          </span>
        </div>
        <p className="text-[11px] text-rose-800 leading-snug">
          Critical cases posted by fellow doctors needing rapid guidance before surgery or intervention.
        </p>
      </Link>
    </aside>
  );
}

export default SocialNavRail;
