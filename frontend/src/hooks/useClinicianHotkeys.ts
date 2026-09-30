"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Global Keyboard Shortcuts for Clinician Efficiency:
 * - Alt + N: Quick New Consultation
 * - Alt + D: Jump to Clinical Dashboard
 * - Alt + H: Jump to Medical Intelligence Hub
 * - Alt + P: Jump to Patient Directory
 * - Alt + S: Jump to AI & System Status
 */
export function useClinicianHotkeys() {
  const router = useRouter();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if user is actively typing in an input, textarea, or contentEditable element
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable)
      ) {
        return;
      }

      if (e.altKey && !e.ctrlKey && !e.metaKey) {
        const key = e.key.toLowerCase();
        if (key === "n") {
          e.preventDefault();
          router.push("/consultations/new");
        } else if (key === "d") {
          e.preventDefault();
          router.push("/dashboard");
        } else if (key === "h") {
          e.preventDefault();
          router.push("/hub");
        } else if (key === "p") {
          e.preventDefault();
          router.push("/patients");
        } else if (key === "s") {
          e.preventDefault();
          router.push("/ai");
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [router]);
}
