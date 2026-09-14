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
    <div className="profile-dropdown-container" ref={containerRef}>
      {/* Trigger button */}
      <button
        id="profile-menu-btn"
        className="profile-trigger"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls="profile-menu"
        onClick={() => setOpen((o) => !o)}
      >
        <span className="profile-avatar" aria-hidden="true">
          {initials}
        </span>
        <span className="profile-trigger-name">{user.full_name}</span>
        <svg
          className={`profile-trigger-caret ${open ? "profile-trigger-caret--open" : ""}`}
          width="12"
          height="12"
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
          className="profile-menu"
          role="menu"
          aria-labelledby="profile-menu-btn"
        >
          {/* Identity */}
          <div className="profile-menu-identity">
            <span className="profile-menu-name">{user.full_name}</span>
            <span className="profile-menu-email">{user.email}</span>
            <span
              className={`profile-menu-role ${isAdmin ? "profile-menu-role--admin" : ""}`}
            >
              {isAdmin ? "Administrator" : "Clinician"}
            </span>
          </div>

          <div className="profile-menu-divider" role="separator" />

          {/* Actions */}
          <button
            id="logout-btn"
            className="profile-menu-action profile-menu-action--danger"
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
