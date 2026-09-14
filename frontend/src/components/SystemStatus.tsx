/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
"use client";

/**
 * DocAssistIQ — System Status component.
 *
 * A sticky status bar that polls /health and /ready every 30 seconds
 * and displays the current system state to clinicians.
 *
 * States:
 *   connecting  — initial load, checking services
 *   operational — all dependencies healthy
 *   degraded    — one or more dependencies unhealthy (lists which ones)
 *   offline     — liveness probe failed (process unreachable)
 *
 * Design rules (per spec Section 3):
 *   - 2D only, no 3D or excessive motion
 *   - Transitions: 180ms ease-default
 *   - prefers-reduced-motion respected
 *   - Clinical semantic tokens for color (no raw red/green)
 *   - Keyboard-accessible dismiss for non-critical notices
 *   - WCAG AA contrast ratios
 */

import { useCallback, useEffect, useReducer } from "react";

import { getHealth, getReady } from "@/lib/api";
import type { ReadinessResponse } from "@/lib/api";

// ============================================================
// Types & State
// ============================================================

type SystemState =
  | { kind: "connecting" }
  | { kind: "operational" }
  | { kind: "degraded"; readiness: ReadinessResponse; dismissed: boolean }
  | { kind: "offline"; error: string };

type Action =
  | { type: "CHECK_START" }
  | { type: "ALL_HEALTHY" }
  | { type: "DEGRADED"; readiness: ReadinessResponse }
  | { type: "OFFLINE"; error: string }
  | { type: "DISMISS" };

function reducer(state: SystemState, action: Action): SystemState {
  switch (action.type) {
    case "CHECK_START":
      // Only show "connecting" on first load, not on re-polls
      return state.kind === "connecting" ? { kind: "connecting" } : state;
    case "ALL_HEALTHY":
      return { kind: "operational" };
    case "DEGRADED":
      return {
        kind: "degraded",
        readiness: action.readiness,
        // Reset dismissed when state changes to degraded
        dismissed:
          state.kind === "degraded" &&
          state.readiness.status === action.readiness.status
            ? state.dismissed
            : false,
      };
    case "OFFLINE":
      return { kind: "offline", error: action.error };
    case "DISMISS":
      return state.kind === "degraded"
        ? { ...state, dismissed: true }
        : state;
    default:
      return state;
  }
}

// ============================================================
// Helpers
// ============================================================

/** Return the names of unhealthy dependencies. */
function getUnhealthyDeps(readiness: ReadinessResponse): string[] {
  return Object.entries(readiness.dependencies)
    .filter(([, dep]) => dep.status === "unhealthy")
    .map(([name]) => name);
}

/** Capitalise a dependency name for display. */
function formatDepName(dep: string): string {
  const labels: Record<string, string> = {
    database: "Database",
    redis: "Cache (Redis)",
    storage: "Object Storage",
  };
  return labels[dep] ?? dep;
}

// ============================================================
// Main Component
// ============================================================

export default function SystemStatus() {
  const [state, dispatch] = useReducer(reducer, { kind: "connecting" });

  const checkStatus = useCallback(async () => {
    // 1. Liveness probe
    const healthResult = await getHealth();
    if (!healthResult.ok) {
      dispatch({ type: "OFFLINE", error: healthResult.error.message });
      return;
    }

    // 2. Readiness probe
    const readyResult = await getReady();
    if (!readyResult.ok && readyResult.statusCode === 0) {
      // Network error — treat as offline
      dispatch({ type: "OFFLINE", error: readyResult.error.message });
      return;
    }

    if (readyResult.ok && readyResult.data.status === "healthy") {
      dispatch({ type: "ALL_HEALTHY" });
    } else if ("data" in readyResult && readyResult.data) {
      dispatch({ type: "DEGRADED", readiness: readyResult.data });
    } else {
      const errMsg =
        "error" in readyResult
          ? readyResult.error.message
          : "Readiness check unavailable";
      dispatch({ type: "OFFLINE", error: errMsg });
    }
  }, []);

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 30_000);
    return () => clearInterval(interval);
  }, [checkStatus]);

  // Operational state — no banner (no noise for clinicians)
  if (state.kind === "operational") return null;

  // Connecting state
  if (state.kind === "connecting") {
    return (
      <StatusBanner
        variant="info"
        id="system-status-connecting"
        role="status"
        aria-live="polite"
      >
        <StatusDot pulse />
        <span>Connecting to services…</span>
      </StatusBanner>
    );
  }

  // Degraded state
  if (state.kind === "degraded" && !state.dismissed) {
    const unhealthy = getUnhealthyDeps(state.readiness);
    return (
      <StatusBanner
        variant="warning"
        id="system-status-degraded"
        role="alert"
        aria-live="assertive"
      >
        <StatusDot />
        <span>
          <strong>System Degraded</strong>
          {" — "}
          {unhealthy.map(formatDepName).join(", ")} unavailable
        </span>
        <DismissButton
          onClick={() => dispatch({ type: "DISMISS" })}
          label="Dismiss system status notice"
        />
      </StatusBanner>
    );
  }

  // Offline state
  if (state.kind === "offline") {
    return (
      <StatusBanner
        variant="danger"
        id="system-status-offline"
        role="alert"
        aria-live="assertive"
      >
        <StatusDot />
        <span>
          <strong>Services Offline</strong> — {state.error}
        </span>
      </StatusBanner>
    );
  }

  return null;
}

// ============================================================
// Sub-components
// ============================================================

interface StatusBannerProps {
  variant: "info" | "warning" | "danger";
  id: string;
  role: "alert" | "status";
  "aria-live": "polite" | "assertive";
  children: React.ReactNode;
}

function StatusBanner({
  variant,
  id,
  role,
  "aria-live": ariaLive,
  children,
}: StatusBannerProps) {
  const variantStyles: Record<string, React.CSSProperties> = {
    info: {
      backgroundColor: "var(--clinical-ai-suggestion-bg)",
      borderColor: "var(--clinical-ai-suggestion-border)",
      color: "var(--clinical-ai-suggestion-text)",
    },
    warning: {
      backgroundColor: "var(--clinical-warning-bg)",
      borderColor: "var(--clinical-warning-border)",
      color: "var(--clinical-warning-text)",
    },
    danger: {
      backgroundColor: "var(--clinical-danger-bg)",
      borderColor: "var(--clinical-danger-border)",
      color: "var(--clinical-danger-text)",
    },
  };

  return (
    <div
      id={id}
      role={role}
      aria-live={ariaLive}
      className="transition-normal"
      style={{
        display: "flex",
        alignItems: "center",
        gap: "var(--space-2)",
        padding: "var(--space-2) var(--space-4)",
        borderBottom: "1px solid",
        fontSize: "var(--text-sm)",
        fontWeight: "var(--font-weight-medium)",
        lineHeight: "var(--leading-normal)",
        ...variantStyles[variant],
      }}
    >
      {children}
    </div>
  );
}

interface StatusDotProps {
  pulse?: boolean;
}

function StatusDot({ pulse = false }: StatusDotProps) {
  return (
    <span
      aria-hidden="true"
      style={{
        display: "inline-block",
        width: 8,
        height: 8,
        borderRadius: "var(--radius-full)",
        backgroundColor: "currentColor",
        flexShrink: 0,
        opacity: 0.8,
        animation: pulse ? "dot-pulse 1.4s ease-in-out infinite" : undefined,
      }}
    />
  );
}

interface DismissButtonProps {
  onClick: () => void;
  label: string;
}

function DismissButton({ onClick, label }: DismissButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      className="transition-fast"
      style={{
        marginLeft: "auto",
        background: "none",
        border: "none",
        cursor: "pointer",
        color: "currentColor",
        padding: "var(--space-1)",
        borderRadius: "var(--radius-sm)",
        opacity: 0.7,
        fontSize: "var(--text-base)",
        lineHeight: 1,
      }}
    >
      ×
    </button>
  );
}
