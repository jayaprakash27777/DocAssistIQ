/**
 * DocAssistIQ — Emerging/Unknown Disease Lookup Card
 *
 * When a disease is mentioned that the system doesn't recognise,
 * this card offers a one-click "Generate Intelligence Profile" button.
 * It calls /api/v1/intelligence/lookup and renders the result inline.
 */
"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface Props {
  diseaseName: string;
  context?: string;
}

interface Profile {
  found: boolean;
  source?: string;
  symptoms?: string[];
  cardinal_symptoms?: string[];
  severity?: string;
  incubation_min?: number;
  incubation_max?: number;
  geographic_zones?: string[];
  _confidence?: string;
  _treatment_summary?: string;
  _investigations?: string[];
  _transmission?: string;
  _notes?: string;
  _sources?: string[];
  _sparse?: boolean;
}

export function EmergingDiseaseCard({ diseaseName, context = "" }: Props) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function lookup() {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/v1/intelligence/lookup`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token") ?? ""}`,
        },
        body: JSON.stringify({ disease_name: diseaseName, context }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setProfile(await res.json());
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  const badgeColor = (s?: string) => ({
    critical: "#ff3b30", high: "#ff9500", moderate: "#ffcc00", low: "#34c759"
  }[s ?? ""] ?? "#8e8e93");

  return (
    <div style={{
      border: "1px solid var(--color-border)",
      borderRadius: 12,
      padding: 16,
      background: "var(--color-surface)",
      marginTop: 12,
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <span style={{ fontSize: "0.72rem", color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Unknown / Emerging Disease
          </span>
          <h4 style={{ margin: "2px 0 0", fontSize: "1rem" }}>{diseaseName}</h4>
        </div>
        {!profile && (
          <button
            id={`emerging-lookup-${diseaseName.replace(/\s+/g, "-")}`}
            onClick={lookup}
            disabled={loading}
            style={{
              background: loading ? "var(--color-surface-raised)" : "var(--color-primary)",
              color: loading ? "var(--color-text-muted)" : "#fff",
              border: "none", borderRadius: 8, padding: "8px 16px",
              fontSize: "0.82rem", fontWeight: 600, cursor: loading ? "not-allowed" : "pointer",
              transition: "all 0.2s",
            }}
          >
            {loading ? "⚡ Generating..." : "⚡ Generate Intelligence Profile"}
          </button>
        )}
      </div>

      {error && (
        <p style={{ color: "#ff3b30", fontSize: "0.8rem", marginTop: 8 }}>❌ {error}</p>
      )}

      {profile && (
        <div style={{ marginTop: 14, display: "flex", flexDirection: "column", gap: 10 }}>
          {/* Source & Confidence */}
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <span style={{
              background: "var(--color-surface-raised)", borderRadius: 20,
              padding: "3px 10px", fontSize: "0.7rem", fontWeight: 600,
            }}>
              Source: {profile.source ?? "N/A"}
            </span>
            {profile.severity && (
              <span style={{
                background: badgeColor(profile.severity), color: "#000",
                borderRadius: 20, padding: "3px 10px", fontSize: "0.7rem", fontWeight: 700,
                textTransform: "uppercase",
              }}>
                {profile.severity}
              </span>
            )}
            {profile._confidence && (
              <span style={{ fontSize: "0.7rem", color: "var(--color-text-muted)" }}>
                Confidence: <b>{profile._confidence}</b>
              </span>
            )}
            {profile._sparse && (
              <span style={{ color: "#ff9500", fontSize: "0.7rem", fontStyle: "italic" }}>
                ⚠ Sparse data — inferred from disease class patterns
              </span>
            )}
          </div>

          {/* Grid layout */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            {/* Symptoms */}
            {profile.symptoms && profile.symptoms.length > 0 && (
              <Section title="Key Symptoms">
                <ul style={{ margin: 0, paddingLeft: 16, fontSize: "0.8rem", lineHeight: 1.7 }}>
                  {profile.symptoms.slice(0, 12).map((s, i) => (
                    <li key={i} style={{
                      fontWeight: profile.cardinal_symptoms?.includes(s) ? 700 : 400,
                      color: profile.cardinal_symptoms?.includes(s) ? "var(--color-text-primary)" : "var(--color-text-secondary)",
                    }}>
                      {profile.cardinal_symptoms?.includes(s) ? "★ " : ""}{s}
                    </li>
                  ))}
                </ul>
              </Section>
            )}

            {/* Investigations */}
            {profile._investigations && profile._investigations.length > 0 && (
              <Section title="Recommended Investigations">
                <ul style={{ margin: 0, paddingLeft: 16, fontSize: "0.8rem", lineHeight: 1.7 }}>
                  {profile._investigations.map((inv, i) => <li key={i}>{inv}</li>)}
                </ul>
              </Section>
            )}

            {/* Treatment */}
            {profile._treatment_summary && (
              <Section title="Treatment Principles">
                <p style={{ margin: 0, fontSize: "0.8rem", lineHeight: 1.6 }}>
                  {profile._treatment_summary}
                </p>
              </Section>
            )}

            {/* Epidemiology */}
            <Section title="Epidemiology">
              {profile.incubation_min != null && (
                <p style={{ margin: "0 0 4px", fontSize: "0.8rem" }}>
                  🕐 Incubation: {profile.incubation_min}–{profile.incubation_max} days
                </p>
              )}
              {profile._transmission && (
                <p style={{ margin: "0 0 4px", fontSize: "0.8rem" }}>
                  🔗 Transmission: {profile._transmission}
                </p>
              )}
              {profile.geographic_zones && profile.geographic_zones.length > 0 && (
                <p style={{ margin: 0, fontSize: "0.8rem" }}>
                  🌍 Affected: {profile.geographic_zones.join(", ")}
                </p>
              )}
            </Section>
          </div>

          {/* Notes */}
          {profile._notes && (
            <div style={{
              background: "rgba(255,149,0,0.08)", border: "1px solid rgba(255,149,0,0.25)",
              borderRadius: 8, padding: "8px 12px", fontSize: "0.78rem",
              color: "var(--color-text-secondary)",
            }}>
              💡 {profile._notes}
            </div>
          )}

          {/* Sources */}
          {profile._sources && (
            <p style={{ margin: 0, fontSize: "0.68rem", color: "var(--color-text-muted)" }}>
              Data sources: {profile._sources.join(" • ")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{
      background: "var(--color-surface-raised)",
      borderRadius: 8, padding: "10px 14px",
    }}>
      <p style={{ margin: "0 0 6px", fontSize: "0.72rem", fontWeight: 700, textTransform: "uppercase",
        letterSpacing: "0.06em", color: "var(--color-text-muted)" }}>{title}</p>
      {children}
    </div>
  );
}
