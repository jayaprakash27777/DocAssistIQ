/**
 * DocAssistIQ — WebSocket Connection Status Pill (Phase 23).
 *
 * Shows the real-time connection state using the hardened WS client.
 */

"use client";

import { useEffect, useState } from "react";
import { getStoredToken } from "@/lib/api";
import { getSharedRealtimeClient, type WSConnectionState } from "@/lib/ws";

export function WsStatus() {
  const [state, setState] = useState<WSConnectionState>('CONNECTING');

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setState('UNAVAILABLE');
      return;
    }
    
    const client = getSharedRealtimeClient(token);
    client.connect();

    const unsubscribe = client.subscribeState((newState) => {
      setState(newState);
    });

    return () => {
      unsubscribe();
    };
  }, []);

  let color = "var(--text-secondary)";
  let dotColor = "gray";
  let label = "Unknown";
  let showDot = true;
  let pulse = false;

  switch (state) {
    case 'CONNECTING':
      label = "CONNECTING";
      dotColor = "var(--primary)";
      pulse = true;
      break;
    case 'LIVE':
      label = "LIVE";
      dotColor = "var(--success)";
      break;
    case 'RECONNECTING':
      label = "RECONNECTING";
      dotColor = "var(--warning)";
      pulse = true;
      break;
    case 'UNAVAILABLE':
      label = "UNAVAILABLE";
      dotColor = "var(--danger)";
      break;
  }

  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: "0.5rem",
      fontSize: "0.75rem",
      fontWeight: 500,
      color: color,
      padding: "0.25rem 0.5rem",
      background: "var(--surface-raised)",
      borderRadius: "100px",
      border: "1px solid var(--border-subtle)"
    }}>
      {showDot && (
        <div style={{
          width: "8px",
          height: "8px",
          borderRadius: "50%",
          backgroundColor: dotColor,
          boxShadow: pulse ? `0 0 0 2px ${dotColor}40` : 'none',
          animation: pulse ? 'pulse 1.5s infinite' : 'none'
        }} />
      )}
      {label}
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes pulse {
          0% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.2); }
          100% { opacity: 1; transform: scale(1); }
        }
      `}} />
    </div>
  );
}
