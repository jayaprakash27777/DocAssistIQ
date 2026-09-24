/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/**
 * DocAssistIQ — Profile Dropdown.
 *
 * Animated dropdown triggered by clicking the avatar/name in the header.
 * Shows: full_name, email, role pill, sign-out button.
 * Closes on: Escape key, click outside, sign-out.
 */

"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { authLogout, type MeResponse } from "@/lib/api";
import { useToast } from "./ToastProvider";

interface Props {
  user: MeResponse;
}

export function ProfileDropdown({ user }: Props) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const { toast } = useToast();

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    function onPointerDown(e: PointerEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open]);

  async function handleLogout() {
    setOpen(false);
    await authLogout();
    toast.info("You have been signed out.");
    router.replace("/login");
  }

  const initials = user.full_name
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");

  const isAdmin = user.role === "admin";

  return (
    <div className="profile-dropdown-container relative" ref={containerRef}>
      {/* Trigger button */}
      <button
        id="profile-menu-btn"
        className="flex items-center gap-2.5 px-3 py-1.5 rounded-2xl bg-white/70 hover:bg-white border border-slate-200/80 hover:border-teal-300 shadow-sm transition-all text-left group"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls="profile-menu"
        onClick={() => setOpen((o) => !o)}
      >
        <span className="w-8 h-8 rounded-xl bg-gradient-to-br from-teal-500 to-indigo-600 text-white font-bold text-xs flex items-center justify-center shadow-sm shrink-0" aria-hidden="true">
          {initials}
        </span>
        <span className="text-xs font-bold text-slate-800 tracking-tight max-w-[120px] truncate">{user.full_name}</span>
        <svg
          className={`w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          viewBox="0 0 12 12"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          aria-hidden="true"
        >
          <path d="M2 4l4 4 4-4" />
        </svg>
      </button>

      {/* Dropdown panel */}
      {open && (
        <div
          id="profile-menu"
          className="absolute right-0 mt-2 w-64 rounded-2xl glass-panel-4k gpu-accelerated p-3 border border-slate-200/90 bg-white/95 backdrop-blur-2xl shadow-[0_20px_50px_rgba(0,0,0,0.12),inset_0_1px_0_rgba(255,255,255,0.95)] z-50 ring-1 ring-black/5"
          role="menu"
          aria-labelledby="profile-menu-btn"
        >
          {/* Identity */}
          <div className="p-2.5 rounded-xl bg-slate-50/80 border border-slate-100 mb-2">
            <span className="block text-sm font-black text-slate-900 leading-snug truncate">{user.full_name}</span>
            <span className="block text-xs text-slate-500 truncate mb-2">{user.email}</span>
            <span
              className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                isAdmin 
                  ? "bg-purple-100 text-purple-700 border border-purple-200" 
                  : "bg-teal-100 text-teal-700 border border-teal-200"
              }`}
            >
              {isAdmin ? "Administrator" : "Clinician"}
            </span>
          </div>

          <div className="h-px bg-slate-100 my-1" role="separator" />

          {/* Actions */}
          <button
            id="logout-btn"
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-bold text-red-600 hover:bg-red-50 hover:text-red-700 transition-colors"
            role="menuitem"
            onClick={handleLogout}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              aria-hidden="true"
            >
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16,17 21,12 16,7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}
