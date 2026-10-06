"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { DoctorPost } from "@/types/social";
import { getStoredToken } from "@/lib/api";
import { getSharedRealtimeClient } from "@/lib/ws";

interface EmergencyRadarWidgetProps {
  urgentCases?: DoctorPost[];
  onSelectCase?: (post: DoctorPost) => void;
}

export function EmergencyRadarWidget({
  urgentCases: initialCases,
  onSelectCase,
}: EmergencyRadarWidgetProps) {
  const [urgentCases, setUrgentCases] = useState<DoctorPost[]>(initialCases || []);

  useEffect(() => {
    if (!initialCases || initialCases.length === 0) {
      const token = getStoredToken();
      fetch("/api/v1/hub/emergency", {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
        .then((res) => (res.ok ? res.json() : []))
        .then((data) => {
          if (Array.isArray(data)) {
            setUrgentCases(data);
          }
        })
        .catch(() => {});
    }

    const token = getStoredToken();
    const ws = getSharedRealtimeClient(token);
    const unsub = ws.subscribeMessages((type, payload) => {
      const p = payload?.post || (payload?.id ? payload : null);
      if (type === "hub_new_post" && p && (p.is_urgent_consult || p.is_urgent || p.is_emergency)) {
        setUrgentCases((prev) => [p, ...prev.filter((c) => c.id !== p.id)]);
      }
    });

    return () => {
      unsub();
    };
  }, [initialCases]);

  if (!urgentCases || urgentCases.length === 0) return null;


  return (
    <div className="bg-gradient-to-b from-rose-50/70 to-white rounded-2xl border border-rose-200/90 p-4 shadow-xs">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-500 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-600" />
          </span>
          <h3 className="font-extrabold text-xs text-rose-950 uppercase tracking-wider">
            Urgent Cases (Need Advice)
          </h3>
        </div>
        <Link
          href="/hub/emergency"
          className="text-[10px] font-bold text-rose-700 hover:text-rose-900 hover:underline"
        >
          View All ({urgentCases.length})
        </Link>
      </div>

      <div className="space-y-2.5">
        {urgentCases.slice(0, 3).map((c) => (
          <div
            key={c.id}
            onClick={() => onSelectCase && onSelectCase(c)}
            className="p-3 bg-white rounded-xl border border-rose-100 hover:border-rose-300 transition-all cursor-pointer shadow-2xs group"
          >
            <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1">
              <span className="font-bold text-rose-700 flex items-center gap-1">
                <span>🚨 Urgent</span>
                <span>•</span>
                <span>{c.specialty_tags?.[0] || "Critical Care"}</span>
              </span>
              <span className="font-mono text-slate-400">
                {new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
            <h4 className="text-xs font-bold text-slate-900 group-hover:text-rose-900 line-clamp-1">
              {c.disease_name}
            </h4>
            <p className="text-[11px] text-slate-600 line-clamp-2 mt-0.5 leading-snug">
              {c.clinical_findings}
            </p>
            <div className="mt-2 flex items-center justify-between text-[10px]">
              <span className="text-slate-500">
                by {c.author_name || "Doctor"}
              </span>
              <span className="font-bold text-rose-700 group-hover:underline">
                Help / Reply ➔
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default EmergencyRadarWidget;
