"use client";

import React, { useState, useEffect } from "react";
import { AlertTriangle, Volume2, VolumeX, ShieldAlert, Check, BellRing } from "lucide-react";
import { DoctorPost } from "@/types/social";
import { getSharedRealtimeClient } from "@/lib/ws";
import { getStoredToken } from "@/lib/api";

interface StatEmergencyPagerBannerProps {
  urgentCases?: DoctorPost[];
  onSelectCase?: (post: DoctorPost) => void;
}

export function StatEmergencyPagerBanner({
  urgentCases = [],
  onSelectCase,
}: StatEmergencyPagerBannerProps) {
  const [isOnCall, setIsOnCall] = useState(true);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [activeAlert, setActiveAlert] = useState<DoctorPost | null>(urgentCases?.[0] || null);

  // Play a soft hospital pager chime using Web Audio API
  const playPagerChime = () => {
    if (!soundEnabled || typeof window === "undefined") return;
    try {
      const AudioCtxClass = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (!AudioCtxClass) return;
      const audioCtx = new AudioCtxClass();
      const osc1 = audioCtx.createOscillator();
      const osc2 = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      osc1.type = "sine";
      osc2.type = "sine";
      osc1.frequency.setValueAtTime(880, audioCtx.currentTime); // A5
      osc2.frequency.setValueAtTime(1760, audioCtx.currentTime + 0.1); // A6

      gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.35);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(audioCtx.destination);

      osc1.start();
      osc1.stop(audioCtx.currentTime + 0.12);
      osc2.start(audioCtx.currentTime + 0.12);
      osc2.stop(audioCtx.currentTime + 0.35);
    } catch {}
  };

  // Set latest active urgent consult on load or WebSocket broadcast
  useEffect(() => {
    if (urgentCases && urgentCases.length > 0) {
      const timer = setTimeout(() => {
        setActiveAlert(urgentCases[0]);
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [urgentCases]);

  useEffect(() => {
    const token = getStoredToken();
    const ws = getSharedRealtimeClient(token);

    const unsub = ws.subscribeMessages((type, payload) => {
      if (type === "hub_new_post" && payload?.post && (payload.post.is_urgent || payload.post.is_emergency || payload.post.is_urgent_consult)) {
        setActiveAlert(payload.post);
        if (isOnCall) {
          playPagerChime();
        }
      }
    });

    return () => {
      unsub();
    };
  }, [isOnCall, soundEnabled]);

  if (!activeAlert && !isOnCall) return null;

  return (
    <div className="bg-gradient-to-r from-rose-600 via-rose-700 to-red-700 text-white rounded-2xl p-3.5 shadow-sm space-y-2">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
        {/* Left: Live Pager Identity & Status */}
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="relative flex h-3 w-3 shrink-0">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-white" />
          </div>
          <div>
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-xs font-black uppercase tracking-wider">
                🚨 Urgent Case Alert
              </span>
              <span className="text-[10px] bg-white/20 text-white font-extrabold px-1.5 py-0.2 rounded">
                Live
              </span>
            </div>
            {activeAlert ? (
              <p className="text-xs text-rose-100 font-semibold truncate max-w-xl">
                Urgent Case: <span className="text-white underline decoration-white/40">{activeAlert.disease_name}</span> — Doctor needs quick advice
              </p>
            ) : (
              <p className="text-[11px] text-rose-200">
                You are available to help colleagues with urgent patient cases.
              </p>
            )}
          </div>
        </div>

        {/* Right: Controls & Jump Action */}
        <div className="flex items-center gap-2 shrink-0">
          {/* Audio Chime Toggle */}
          <button
            type="button"
            onClick={() => {
              setSoundEnabled(!soundEnabled);
              if (!soundEnabled) playPagerChime();
            }}
            className="p-1.5 bg-rose-800/60 hover:bg-rose-800 rounded-xl transition text-rose-100 hover:text-white cursor-pointer"
            title={soundEnabled ? "Mute Alert Sound" : "Turn On Alert Sound"}
          >
            {soundEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4 text-rose-300" />}
          </button>

          {/* On-Call Status Switch */}
          <button
            type="button"
            onClick={() => setIsOnCall(!isOnCall)}
            className={`px-2.5 py-1 rounded-xl text-[11px] font-black transition cursor-pointer flex items-center gap-1 ${
              isOnCall
                ? "bg-emerald-500/20 text-emerald-100 border border-emerald-400/40"
                : "bg-white/10 text-white/70"
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${isOnCall ? "bg-emerald-400" : "bg-slate-400"}`} />
            <span>{isOnCall ? "Available" : "Away"}</span>
          </button>

          {/* Jump to Case Button */}
          {activeAlert && (
            <button
              type="button"
              onClick={() => {
                if (onSelectCase) onSelectCase(activeAlert);
                else window.location.href = `/hub/emergency`;
              }}
              className="px-3.5 py-1.5 bg-white text-rose-900 hover:bg-rose-50 text-xs font-black rounded-xl transition shadow-xs cursor-pointer"
            >
              Help / Reply ➔
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default StatEmergencyPagerBanner;
