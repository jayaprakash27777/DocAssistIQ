/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

/**
 * DocAssistIQ — System Status Banner.
 *
 * Displays clinical system health and readiness probe status.
 * States:
 *   - connecting  : Initial health probe in progress (role="status")
 *   - operational : All dependencies healthy → renders nothing
 *   - degraded    : One or more dependencies unhealthy (database, redis, storage) → dismissable alert
 *   - offline     : API or backend unreachable (network error) → non-dismissable critical alert
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { getHealth, getReady, type ReadinessResponse } from "@/lib/api";
import { AlertTriangle, WifiOff, X, RefreshCw } from "lucide-react";

type SystemState = "connecting" | "operational" | "degraded" | "offline";

export default function SystemStatus() {
  const [state, setState] = useState<SystemState>("connecting");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [unhealthyDeps, setUnhealthyDeps] = useState<string[]>([]);
  const [dismissed, setDismissed] = useState(false);
  const mountedRef = useRef(true);

  const checkStatus = useCallback(async () => {
    try {
      const [healthRes, readyRes] = await Promise.all([getHealth(), getReady()]);

      if (!mountedRef.current) return;

      if (!healthRes.ok) {
        setState("offline");
        setErrorMessage(healthRes.error?.message || "Network error");
        return;
      }

      if (readyRes.ok && readyRes.data) {
        const deps = readyRes.data.dependencies;
        const failed: string[] = [];

        if (deps?.database?.status !== "healthy") failed.push("Database");
        if (deps?.redis?.status !== "healthy") failed.push("Cache");
        if (deps?.storage?.status !== "healthy") failed.push("Object Storage");

        if (failed.length > 0 || readyRes.data.status === "degraded") {
          setState("degraded");
          setUnhealthyDeps(failed.length > 0 ? failed : ["Subsystem"]);
          return;
        }
      }

      setState("operational");
      setUnhealthyDeps([]);
      setErrorMessage("");
    } catch (e: any) {
      if (!mountedRef.current) return;
      setState("offline");
      setErrorMessage(e?.message || "Network error");
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    checkStatus();

    const intervalId = setInterval(checkStatus, 30_000);
    return () => {
      mountedRef.current = false;
      clearInterval(intervalId);
    };
  }, [checkStatus]);

  // Operational: render nothing
  if (state === "operational") {
    return null;
  }

  // Connecting: accessible status element
  if (state === "connecting") {
    return (
      <div
        role="status"
        aria-live="polite"
        className="sr-only"
      >
        Connecting to clinical backend...
      </div>
    );
  }

  // Degraded: dismissable alert
  if (state === "degraded") {
    if (dismissed) return null;

    return (
      <div
        role="alert"
        aria-live="assertive"
        className="bg-amber-500/95 text-white px-4 py-2.5 flex items-center justify-between text-xs font-semibold shadow-md backdrop-blur-md z-50 sticky top-0 border-b border-amber-600/30"
      >
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-200" />
          <span>
            System Degraded: High latency or issues detected in{" "}
            <strong>{unhealthyDeps.join(", ")}</strong>. Clinical decision features remain available with fallback data.
          </span>
        </div>
        <button
          onClick={() => setDismissed(true)}
          aria-label="Dismiss"
          className="p-1 rounded-lg hover:bg-white/20 text-white transition-colors ml-4 shrink-0"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    );
  }

  // Offline: non-dismissable critical alert
  if (state === "offline") {
    return (
      <div
        role="alert"
        aria-live="assertive"
        className="bg-rose-600 text-white px-4 py-3 flex items-center justify-between text-xs font-semibold shadow-lg backdrop-blur-md z-50 sticky top-0 border-b border-rose-700/40"
      >
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 rounded-lg bg-white/20 flex items-center justify-center shrink-0">
            <WifiOff className="w-3.5 h-3.5 text-rose-100" />
          </div>
          <div>
            <span className="font-bold uppercase tracking-wider text-[11px] block">
              Backend Offline
            </span>
            <span className="text-rose-100 font-normal">
              {errorMessage ? `Error: ${errorMessage}` : "Network error. Unable to reach clinical backend server."}
            </span>
          </div>
        </div>
        <button
          onClick={() => {
            setState("connecting");
            checkStatus();
          }}
          className="px-3 py-1.5 rounded-xl bg-white/20 hover:bg-white/30 text-white text-xs font-bold transition-all flex items-center gap-1.5 shrink-0 ml-4"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Retry
        </button>
      </div>
    );
  }

  return null;
}
