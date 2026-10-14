"use client";

import { useEffect, useState } from "react";
import { getStoredToken } from "@/lib/api";
import { getSharedRealtimeClient } from "@/lib/ws";

export function ActiveModelBadge() {
  const [modelName, setModelName] = useState<string>("Loading...");
  const [isLlmAvailable, setIsLlmAvailable] = useState<boolean>(true);

  useEffect(() => {
    let mounted = true;
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/api\/v1$/, "") || "http://127.0.0.1:8000";

    const fetchStatus = async () => {
      try {
        const res = await fetch(`${apiBaseUrl}/api/v1/ai-status`);
        if (res.ok) {
          const data = await res.json();
          if (mounted && data.model) {
            setModelName(data.model);
            setIsLlmAvailable(data.llm_available ?? true);
          }
        }
      } catch {
        // Fallback or retry
      }
    };

    fetchStatus();

    // 1. Subscribe to real-time websocket broadcast for instant update
    const token = getStoredToken();
    const client = getSharedRealtimeClient(token);
    client.connect();

    const unsubscribe = client.subscribeMessages((type, payload) => {
      if ((type === "ai.model_switched" || type === "ai.circuit_breaker_reset") && payload) {
        const targetModel = payload.active_model || payload.model;
        if (targetModel && mounted) {
          setModelName(targetModel);
          setIsLlmAvailable(payload.mode !== "static_kb_fallback");
        }
      }
    });

    // 2. Poll every 10s as safety heartbeat
    const interval = setInterval(fetchStatus, 10000);

    return () => {
      mounted = false;
      unsubscribe();
      clearInterval(interval);
    };
  }, []);

  return (
    <div
      className={`hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-semibold shadow-2xs transition-all duration-300 ${
        isLlmAvailable
          ? "bg-emerald-500/10 text-emerald-700 border-emerald-500/25"
          : "bg-amber-500/10 text-amber-700 border-amber-500/25"
      }`}
      title={`Active Clinical AI Reasoning Engine: ${modelName} (${isLlmAvailable ? "Online" : "Fallback KB Active"})`}
    >
      <span
        className={`w-2 h-2 rounded-full ${
          isLlmAvailable ? "bg-emerald-500 animate-pulse" : "bg-amber-500"
        }`}
      />
      <span className="font-mono text-[11px] tracking-wide uppercase font-bold truncate max-w-[140px]">
        {modelName || "AI ACTIVE"}
      </span>
    </div>
  );
}
