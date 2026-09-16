/**
 * DocAssistIQ — Live Outbreak Intelligence Banner
 *
 * A real-time animated banner that:
 * - Shows active WHO/CDC outbreak alerts from the live scanner
 * - Displays newly discovered/emerging diseases with confidence level
 * - Pulses with a live indicator when scanner is active
 * - Auto-refreshes every 5 minutes
 */
"use client";

import { useEffect, useState, useCallback } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface DynamicDisease {
  name: string;
  severity: string;
  confidence: string;
  learned_at: string;
  sources: string[];
  is_sparse: boolean;
}

interface ScannerStatus {
  running: boolean;
  last_scan: string | null;
  scans_completed: number;
  dynamic_diseases_active: number;
  new_this_session: number;
  active_dynamic_diseases: DynamicDisease[];
}

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: "#ff3b30",
    high:     "#ff9500",
    moderate: "#ffcc00",
    low:      "#34c759",
    unknown:  "#8e8e93",
  };
  return (
    <span style={{
      background: colors[severity] ?? colors.unknown,
      color: "#000",
      fontWeight: 700,
      fontSize: "0.65rem",
      padding: "2px 7px",
      borderRadius: "20px",
      textTransform: "uppercase",
      letterSpacing: "0.04em",
    }}>
      {severity}
    </span>
  );
}

function ConfidenceDot({ confidence }: { confidence: string }) {
  const colors: Record<string, string> = {
    high:      "#34c759",
    medium:    "#ffcc00",
    low:       "#ff9500",
    very_low:  "#ff3b30",
  };
  return (
    <span style={{
      display: "inline-block",
      width: 8, height: 8,
      borderRadius: "50%",
      background: colors[confidence] ?? "#8e8e93",
      marginRight: 5,
    }} title={`Confidence: ${confidence}`} />
  );
}

export function LiveOutbreakBanner() {
  const [status, setStatus] = useState<ScannerStatus | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/intelligence/outbreak-scanner/status`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("access_token") ?? ""}` },
      });
      if (res.ok) setStatus(await res.json());
    } catch {
      // Silently fail — non-blocking
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const iv = setInterval(fetchStatus, 5 * 60 * 1000); // Refresh every 5 min
    return () => clearInterval(iv);
  }, [fetchStatus]);

  if (loading || !status) return null;

  const hasDynamic = (status.active_dynamic_diseases?.length ?? 0) > 0;
  const isActive = status.running;

  return (
    <div
      id="live-outbreak-banner"
      style={{
        background: hasDynamic
          ? "linear-gradient(90deg, rgba(255,59,48,0.08) 0%, rgba(255,149,0,0.06) 100%)"
          : "linear-gradient(90deg, rgba(52,199,89,0.06) 0%, rgba(0,122,255,0.04) 100%)",
        border: hasDynamic ? "1px solid rgba(255,149,0,0.3)" : "1px solid rgba(52,199,89,0.2)",
        borderRadius: 10,
        padding: "8px 14px",
        margin: "0 0 12px 0",
        display: "flex",
        flexDirection: "column",
        gap: 6,
        fontSize: "0.82rem",
        transition: "all 0.3s ease",
      }}
    >
      {/* Top row */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {/* Live pulse dot */}
          <span style={{ position: "relative", display: "inline-flex", width: 10, height: 10 }}>
            {isActive && (
              <span style={{
                position: "absolute", width: "100%", height: "100%",
                borderRadius: "50%",
                background: hasDynamic ? "#ff9500" : "#34c759",
                opacity: 0.5,
                animation: "outbreak-pulse 1.6s cubic-bezier(0.4,0,0.6,1) infinite",
              }} />
            )}
            <span style={{
              width: 10, height: 10, borderRadius: "50%",
              background: isActive ? (hasDynamic ? "#ff9500" : "#34c759") : "#8e8e93",
              display: "inline-block",
            }} />
          </span>

          <span style={{ fontWeight: 600, color: "var(--color-text-primary)" }}>
            🌐 Live Disease Intelligence
          </span>

          <span style={{
            fontSize: "0.7rem",
            color: "var(--color-text-muted)",
            background: "var(--color-surface-raised)",
            padding: "2px 8px",
            borderRadius: 20,
          }}>
            {status.dynamic_diseases_active} emerging monitored
            {status.new_this_session > 0 && (
              <span style={{ color: "#ff3b30", marginLeft: 4, fontWeight: 700 }}>
                +{status.new_this_session} NEW
              </span>
            )}
          </span>

          <span style={{ fontSize: "0.68rem", color: "var(--color-text-muted)" }}>
            Polls WHO • CDC • ProMED • ECDC every 15 min
          </span>
        </div>

        {hasDynamic && (
          <button
            onClick={() => setExpanded(e => !e)}
            style={{
              background: "none", border: "1px solid var(--color-border)",
              borderRadius: 6, padding: "2px 10px",
              fontSize: "0.75rem", cursor: "pointer",
              color: "var(--color-text-secondary)",
              transition: "all 0.2s",
            }}
          >
            {expanded ? "▲ Hide" : "▼ View alerts"}
          </button>
        )}
      </div>

      {/* Expanded disease list */}
      {expanded && hasDynamic && (
        <div style={{
          display: "flex", flexDirection: "column", gap: 6,
          paddingTop: 8,
          borderTop: "1px solid var(--color-border)",
        }}>
          <p style={{ margin: 0, fontSize: "0.73rem", color: "var(--color-text-muted)", fontStyle: "italic" }}>
            These profiles were auto-generated from live WHO/CDC/ProMED feeds.
            They are included in all diagnostic scoring automatically.
          </p>
          {status.active_dynamic_diseases.map((d, i) => (
            <div key={i} style={{
              display: "flex", alignItems: "center", gap: 10,
              background: "var(--color-surface-raised)",
              borderRadius: 8, padding: "6px 12px",
              border: d.is_sparse ? "1px dashed rgba(255,149,0,0.4)" : "1px solid var(--color-border)",
            }}>
              <ConfidenceDot confidence={d.confidence} />
              <span style={{ fontWeight: 600, flex: 1 }}>{d.name}</span>
              <SeverityBadge severity={d.severity} />
              {d.is_sparse && (
                <span style={{ fontSize: "0.66rem", color: "#ff9500", fontStyle: "italic" }}>
                  ⚠ Sparse data
                </span>
              )}
              <span style={{ fontSize: "0.67rem", color: "var(--color-text-muted)" }}>
                {new Date(d.learned_at).toLocaleTimeString()}
              </span>
            </div>
          ))}
        </div>
      )}

      <style>{`
        @keyframes outbreak-pulse {
          0%, 100% { transform: scale(1); opacity: 0.5; }
          50% { transform: scale(2); opacity: 0; }
        }
      `}</style>
    </div>
  );
}
