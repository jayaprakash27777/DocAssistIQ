"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import {
  Home,
  AlertTriangle,
  Compass,
  Bookmark,
  User,
  Radio,
  Users,
  Film,
  MessageCircle,
  Pill,
  GraduationCap,
  PlusCircle,
  ShieldCheck
} from "lucide-react";

interface SocialNavRailProps {
  onOpenCompose?: () => void;
  onOpenComposer?: () => void;
  onOpenAudioSpace?: () => void;
  onOpenDoctorCircles?: () => void;
  onOpenClinicalReels?: () => void;
  onOpenCurbsideMessenger?: () => void;
  onOpenDDIChecker?: () => void;
  onOpenCMEEvents?: () => void;
  urgentCasesCount?: number;
  savedCasesCount?: number;
}

export function SocialNavRail({
  onOpenCompose,
  onOpenComposer,
  onOpenAudioSpace,
  onOpenDoctorCircles,
  onOpenClinicalReels,
  onOpenCurbsideMessenger,
  onOpenDDIChecker,
  onOpenCMEEvents,
  urgentCasesCount = 0,
  savedCasesCount = 0,
}: SocialNavRailProps) {
  const pathname = usePathname();
  const { user } = useAuth();
  const handleCompose = onOpenComposer || onOpenCompose || (() => {});

  const navItems = [
    {
      href: "/hub",
      label: "Community Feed",
      icon: <Home className="w-4 h-4" />,
      exact: true,
    },
    {
      href: "/hub/emergency",
      label: "Urgent Cases",
      icon: <AlertTriangle className="w-4 h-4 text-rose-500" />,
      badge: urgentCasesCount > 0 ? `${urgentCasesCount} Urgent` : undefined,
      badgeColor: "bg-rose-600 text-white animate-pulse font-black",
    },
    {
      href: "/hub/explore",
      label: "Explore Topics",
      icon: <Compass className="w-4 h-4" />,
    },
    {
      href: "/hub/saved",
      label: "Saved Cases",
      icon: <Bookmark className="w-4 h-4" />,
      badge: savedCasesCount > 0 ? `${savedCasesCount}` : undefined,
      badgeColor: "bg-teal-100 text-teal-800 font-bold",
    },
    {
      href: "/hub/profile",
      label: "My Cases & Profile",
      icon: <User className="w-4 h-4" />,
    },
  ];

  return (
    <aside className="sticky top-6 space-y-4">
      {/* ── Doctor Verified Identity Card ── */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-4 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-teal-600 to-emerald-500 text-white font-black text-lg flex items-center justify-center shadow-xs shrink-0">
            {user?.full_name ? user.full_name.replace(/Dr\.\s*/i, "")[0].toUpperCase() : "D"}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-sm text-slate-900 truncate">
                {user?.full_name || "Dr. Attending Specialist"}
              </span>
              <span title="Verified Medical License">
                <ShieldCheck className="w-4 h-4 text-teal-600 shrink-0" />
              </span>
            </div>
            <p className="text-xs text-slate-500 truncate mt-0.5">
              {(user as { specialty?: string; role?: string } | null)?.specialty || user?.role || "Board Certified Clinician"}
            </p>
            <div className="mt-1 flex items-center gap-1.5">
              <span className="text-[10px] font-bold bg-teal-50 text-teal-700 px-2 py-0.5 rounded-md border border-teal-100">
                Verified Doctor
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Main Social Navigation Menu ── */}
      <nav className="bg-white rounded-2xl border border-slate-200/90 p-2 shadow-xs space-y-1">
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
                  className={`text-[10px] px-2 py-0.5 rounded-full ${
                    isActive ? "bg-white text-teal-800 font-black" : item.badgeColor || "bg-slate-100 text-slate-700"
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* ── Quick Doctor Tools ── */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-2 shadow-xs space-y-1">
        <div className="px-3 pt-2 pb-1">
          <span className="text-[10px] font-black uppercase tracking-wider text-slate-400">
            Quick Tools
          </span>
        </div>

        {/* Live Audio Rounds */}
        {onOpenAudioSpace && (
          <button
            type="button"
            onClick={onOpenAudioSpace}
            className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl font-bold text-xs text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <Radio className="w-4 h-4 text-rose-500 animate-pulse" />
              <span>Live Audio Rounds</span>
            </div>
            <span className="text-[10px] font-black bg-rose-50 text-rose-700 border border-rose-200 px-2 py-0.5 rounded-full flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-600 animate-ping" />
              LIVE
            </span>
          </button>
        )}

        {/* Specialty Groups */}
        {onOpenDoctorCircles && (
          <button
            type="button"
            onClick={onOpenDoctorCircles}
            className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl font-bold text-xs text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <Users className="w-4 h-4 text-indigo-500" />
              <span>Specialty Groups</span>
            </div>
            <span className="text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 px-2 py-0.5 rounded-full">
              7 Groups
            </span>
          </button>
        )}

        {/* Case Videos & Reels */}
        {onOpenClinicalReels && (
          <button
            type="button"
            onClick={onOpenClinicalReels}
            className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl font-bold text-xs text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <Film className="w-4 h-4 text-teal-600" />
              <span>Case Videos & Reels</span>
            </div>
            <span className="text-[10px] font-bold bg-teal-50 text-teal-800 border border-teal-200 px-2 py-0.5 rounded-full">
              30s Videos
            </span>
          </button>
        )}

        {/* Doctor Chat */}
        {onOpenCurbsideMessenger && (
          <button
            type="button"
            onClick={onOpenCurbsideMessenger}
            className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl font-bold text-xs text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <MessageCircle className="w-4 h-4 text-emerald-500" />
              <span>Doctor Chat</span>
            </div>
            <span className="text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded-full">
              Online
            </span>
          </button>
        )}

        {/* Medicine Safety Checker */}
        {onOpenDDIChecker && (
          <button
            type="button"
            onClick={onOpenDDIChecker}
            className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl font-bold text-xs text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <Pill className="w-4 h-4 text-amber-500" />
              <span>Medicine Safety</span>
            </div>
            <span className="text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded-full">
              Check Rx
            </span>
          </button>
        )}

        {/* CME Events */}
        {onOpenCMEEvents && (
          <button
            type="button"
            onClick={onOpenCMEEvents}
            className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl font-bold text-xs text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <GraduationCap className="w-4 h-4 text-purple-500" />
              <span>Webinars & CME</span>
            </div>
            <span className="text-[10px] font-bold bg-purple-50 text-purple-800 border border-purple-200 px-2 py-0.5 rounded-full">
              Credits
            </span>
          </button>
        )}
      </div>

      {/* ── Quick Share Patient Case Button ── */}
      <button
        type="button"
        onClick={handleCompose}
        className="w-full py-3 px-4 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-black text-sm shadow-sm transition-all flex items-center justify-center gap-2 cursor-pointer active:scale-98"
      >
        <PlusCircle className="w-5 h-5" />
        <span>Share a Case</span>
      </button>

      {/* ── Urgent Cases Banner ── */}
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
              Urgent Cases Need Advice
            </span>
          </div>
          <span className="text-[10px] font-black text-rose-700 bg-rose-100 px-2 py-0.5 rounded-md">
            Urgent
          </span>
        </div>
        <p className="text-[11px] text-rose-800 leading-snug">
          Patients in urgent condition needing quick review from specialist doctors.
        </p>
      </Link>
    </aside>
  );
}

export default SocialNavRail;
