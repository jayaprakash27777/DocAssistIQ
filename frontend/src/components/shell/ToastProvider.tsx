/* eslint-disable @typescript-eslint/no-unused-vars */
/**
 * DocAssistIQ — Toast Context and Provider.
 *
 * Provides a globally accessible toast notification system:
 *   - Three variants: success (green), error (red), info (blue)
 *   - Auto-dismiss after 4 s (error: 6 s)
 *   - Manual dismiss with × button
 *   - Max 5 visible, older toasts removed first
 *   - Rendered in a fixed portal (bottom-right)
 *   - Respects prefers-reduced-motion
 */

"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useId,
  useState,
} from "react";

// ── Types ─────────────────────────────────────────────────────

export type ToastVariant = "success" | "error" | "info";

export interface Toast {
  id: string;
  variant: ToastVariant;
  message: string;
}

interface ToastContextValue {
  toasts: Toast[];
  addToast: (variant: ToastVariant, message: string) => void;
  removeToast: (id: string) => void;
}

// ── Context ───────────────────────────────────────────────────

const ToastContext = createContext<ToastContextValue | null>(null);

const DISMISS_MS: Record<ToastVariant, number> = {
  success: 4000,
  info: 4000,
  error: 6000,
};

const MAX_TOASTS = 5;

// ── Provider ──────────────────────────────────────────────────

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (variant: ToastVariant, message: string) => {
      const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
      setToasts((prev) => {
        const next = [...prev, { id, variant, message }];
        return next.length > MAX_TOASTS ? next.slice(next.length - MAX_TOASTS) : next;
      });
      setTimeout(() => removeToast(id), DISMISS_MS[variant]);
    },
    [removeToast],
  );

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastPortal />
    </ToastContext.Provider>
  );
}

// ── Portal ────────────────────────────────────────────────────

const VARIANT_ICON: Record<ToastVariant, string> = {
  success: "✓",
  error: "✕",
  info: "i",
};

function ToastPortal() {
  const ctx = useContext(ToastContext);
  if (!ctx || ctx.toasts.length === 0) return null;

  return (
    <div
      className="toast-portal"
      role="region"
      aria-label="Notifications"
      aria-live="polite"
      aria-atomic="false"
    >
      {ctx.toasts.map((toast) => (
        <div
          key={toast.id}
          className={`toast toast--${toast.variant}`}
          role={toast.variant === "error" ? "alert" : "status"}
        >
          <span className={`toast-icon toast-icon--${toast.variant}`} aria-hidden="true">
            {VARIANT_ICON[toast.variant]}
          </span>
          <p className="toast-message">{toast.message}</p>
          <button
            className="toast-dismiss"
            onClick={() => ctx.removeToast(toast.id)}
            aria-label="Dismiss notification"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}

// ── Hook ──────────────────────────────────────────────────────

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast() must be used inside <ToastProvider>");

  return {
    toast: React.useMemo(() => ({
      success: (message: string) => ctx.addToast("success", message),
      error: (message: string) => ctx.addToast("error", message),
      info: (message: string) => ctx.addToast("info", message),
    }), [ctx.addToast]),
  };
}
