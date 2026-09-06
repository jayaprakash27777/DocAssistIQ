/**
 * DocAssistIQ — WebSocket Connection Status Pill.
 *
 * Shows the real-time connection state in the shell header:
 *   🟢 LIVE       — connected and receiving pings
 *   🟡 CONNECTING — initial connection attempt
 *   🟠 RECONNECTING — reconnect in progress (after disconnect)
 *   🔴 UNAVAILABLE — max retries exhausted
 *
 * Reconnect strategy: exponential back-off (1s → 2s → 4s → … → 30s cap).
 * Max 8 retries before entering UNAVAILABLE state.
 *
 * Respects prefers-reduced-motion (no pulsing animation).
 */

"use client";

import { useEffect, useRef, useState } from "react";
import { getStoredToken } from "@/lib/api";

type WsStatus = "connecting" | "live" | "reconnecting" | "unavailable";

const WS_URL =
  (process.env.NEXT_PUBLIC_API_URL?.replace(/^http/, "ws")?.replace(/\/api\/v1$/, "") ??
    "ws://localhost:8000") + "/ws/v1/stream";

const MAX_RETRIES = 8;
const BASE_BACKOFF_MS = 1_000;
const MAX_BACKOFF_MS = 30_000;

const STATUS_CONFIG: Record<
  WsStatus,
  { label: string; dot: string; title: string }
> = {
  connecting:   { label: "CONNECTING",   dot: "🟡", title: "Establishing connection…" },
  live:         { label: "LIVE",         dot: "🟢", title: "Connected — real-time updates active" },
  reconnecting: { label: "RECONNECTING", dot: "🟠", title: "Connection lost — attempting to reconnect" },
  unavailable:  { label: "UNAVAILABLE",  dot: "🔴", title: "Real-time connection unavailable" },
};

export function WsStatus() {
  const [status, setStatus] = useState<WsStatus>("connecting");
  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef(0);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const unmountedRef = useRef(false);

  useEffect(() => {
    unmountedRef.current = false;

    function connect() {
      if (unmountedRef.current) return;

      const token = getStoredToken();
      if (!token) {
        setStatus("unavailable");
        return;
      }

      const ws = new WebSocket(`${WS_URL}?token=${token}`);
      wsRef.current = ws;

      ws.onopen = () => {
        if (unmountedRef.current) { ws.close(); return; }
        // Wait for the "connected" message before setting LIVE
      };

      ws.onmessage = (event) => {
        if (unmountedRef.current) return;
        try {
          const data = JSON.parse(event.data as string);
          if (data.type === "connected" || data.type === "ping") {
            retryCountRef.current = 0;
            setStatus("live");
          }
        } catch {
          // Ignore malformed messages
        }
      };

      ws.onclose = () => {
        if (unmountedRef.current) return;
        wsRef.current = null;

        if (retryCountRef.current >= MAX_RETRIES) {
          setStatus("unavailable");
          return;
        }

        setStatus(retryCountRef.current === 0 ? "connecting" : "reconnecting");
        const delay = Math.min(
          BASE_BACKOFF_MS * 2 ** retryCountRef.current,
          MAX_BACKOFF_MS,
        );
        retryCountRef.current += 1;
        retryTimerRef.current = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        // onclose fires after onerror; no duplicate handling needed
      };
    }

    connect();

    return () => {
      unmountedRef.current = true;
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect on intentional unmount
        wsRef.current.close();
      }
    };
  }, []);

  const cfg = STATUS_CONFIG[status];

  return (
    <div
      className={`ws-status ws-status--${status}`}
      title={cfg.title}
      aria-label={`Connection: ${cfg.label}`}
      role="status"
    >
      <span className="ws-status-dot" aria-hidden="true">
        {cfg.dot}
      </span>
      <span className="ws-status-label">{cfg.label}</span>
    </div>
  );
}
