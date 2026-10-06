"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { getSharedRealtimeClient } from "@/lib/ws";
import { getStoredToken } from "@/lib/api";
import { Mic, MicOff, Hand, Radio, ShieldCheck, X, Users, MessageSquare } from "lucide-react";

export interface AudioSpaceSpeaker {
  id: string;
  name: string;
  specialty: string;
  role: string; // host, speaker, listener
  is_speaking: boolean;
  avatar_gradient: string;
}

export interface AudioSpaceData {
  id: string;
  title: string;
  specialty: string;
  listeners_count: number;
  is_live: boolean;
  active_case_title: string;
  speakers: AudioSpaceSpeaker[];
  tags: string[];
}

interface AudioSpaceModalProps {
  space?: AudioSpaceData | null;
  onClose: () => void;
  onReaction?: (reaction: string) => void;
}

interface FloatingEmoji {
  id: number;
  emoji: string;
  x: number;
}

export function AudioSpaceModal({
  space: propSpace,
  onClose,
  onReaction,
}: AudioSpaceModalProps) {
  const [space, setSpace] = useState<AudioSpaceData | null>(propSpace || null);
  const [handRaised, setHandRaised] = useState(false);
  const [isMuted, setIsMuted] = useState(true);
  const [floatingEmojis, setFloatingEmojis] = useState<FloatingEmoji[]>([]);
  const [activeSpeakerIndex, setActiveSpeakerIndex] = useState(0);

  // Fetch real live space from API if not provided
  useEffect(() => {
    if (!propSpace) {
      const token = getStoredToken();
      fetch("/api/v1/hub/spaces", {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
        .then((res) => (res.ok ? res.json() : null))
        .then((data: AudioSpaceData | null) => {
          if (data) setSpace(data);
        })
        .catch(() => {});
    } else {
      setSpace(propSpace);
    }
  }, [propSpace]);

  const currentSpace: AudioSpaceData = space || {
    id: "space-live-grand-rounds",
    title: "🔴 LIVE Grand Rounds: Wellens' Syndrome & Critical Proximal LAD Occlusion",
    specialty: "Cardiology & Critical Care",
    listeners_count: 54,
    is_live: true,
    active_case_title: "Wellens' Syndrome Type A LAD Stenosis",
    speakers: [
      {
        id: "doc-chen",
        name: "Dr. Sarah Chen, MD, FACC",
        specialty: "Interventional Cardiology",
        role: "host",
        is_speaking: true,
        avatar_gradient: "from-teal-600 to-emerald-600",
      },
      {
        id: "doc-thorne",
        name: "Dr. Marcus Thorne, MD, FACEP",
        specialty: "Emergency Medicine",
        role: "speaker",
        is_speaking: false,
        avatar_gradient: "from-rose-600 to-pink-600",
      },
      {
        id: "doc-vance",
        name: "Dr. David Vance, MD, FAAN",
        specialty: "Neurointensivist",
        role: "speaker",
        is_speaking: false,
        avatar_gradient: "from-indigo-600 to-purple-600",
      },
      {
        id: "doc-rostova",
        name: "Dr. Elena Rostova, MD, PhD",
        specialty: "Pediatric Critical Care",
        role: "listener",
        is_speaking: false,
        avatar_gradient: "from-amber-600 to-orange-600",
      },
    ],
    tags: ["ECMO", "Shock", "CathLab", "LiveGrandRounds"],
  };

  // Real-time WebSocket subscriptions
  useEffect(() => {
    const token = getStoredToken();
    const ws = getSharedRealtimeClient(token);
    if (ws) {
      ws.connect();
      const unsub = ws.subscribeMessages((type, payload) => {
        if (type === "hub_space_reaction" && payload?.reaction) {
          reactionCounterRef.current += 1;
          const newId = reactionCounterRef.current;
          const randomX = 25 + ((newId * 17) % 55);
          setFloatingEmojis((prev) => [...prev, { id: newId, emoji: payload.reaction, x: randomX }]);
          setTimeout(() => {
            setFloatingEmojis((prev) => prev.filter((item) => item.id !== newId));
          }, 2400);
        } else if (type === "hub_space_speaker_changed" && payload) {
          if (payload.is_speaking) {
            setActiveSpeakerIndex(0);
          }
        }
      });
      return () => {
        unsub();
      };
    }
  }, []);

  const reactionCounterRef = useRef(0);
  const triggerReaction = useCallback((emoji: string) => {
    reactionCounterRef.current += 1;
    const newId = reactionCounterRef.current;
    const randomX = 25 + ((newId * 17) % 55);
    setFloatingEmojis((prev) => [...prev, { id: newId, emoji, x: randomX }]);
    setTimeout(() => {
      setFloatingEmojis((prev) => prev.filter((item) => item.id !== newId));
    }, 2400);

    const token = getStoredToken();
    fetch(`/api/v1/hub/spaces/${currentSpace.id}/reaction`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ reaction: emoji }),
    }).catch(() => {});

    if (onReaction) onReaction(emoji);
  }, [onReaction, currentSpace.id]);

  const toggleMic = async () => {
    const nextMuted = !isMuted;
    setIsMuted(nextMuted);

    const token = getStoredToken();
    try {
      await fetch(`/api/v1/hub/spaces/${currentSpace.id}/speak`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ is_speaking: !nextMuted }),
      });
    } catch {}
  };

  const toggleHandRaise = async () => {
    const nextRaised = !handRaised;
    setHandRaised(nextRaised);

    const token = getStoredToken();
    try {
      await fetch(`/api/v1/hub/spaces/${currentSpace.id}/hand-raise`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ hand_raised: nextRaised }),
      });
    } catch {}
  };

  return (
    <div className="fixed inset-0 z-[120] flex items-center justify-center p-3 sm:p-5 bg-slate-900/60 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="relative w-full max-w-2xl max-h-[92vh] flex flex-col rounded-3xl bg-white border border-slate-200 shadow-2xl overflow-hidden"
      >
        {/* Top Header Bar */}
        <div className="p-4 sm:p-5 border-b border-slate-100 flex items-center justify-between gap-3 bg-white">
          <div className="flex items-center gap-3">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-500 opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-600" />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-black tracking-wider bg-rose-50 text-rose-700 border border-rose-200 px-2 py-0.5 rounded-full">
                  Live Doctor Audio
                </span>
                <span className="text-xs text-slate-500 font-mono font-bold flex items-center gap-1">
                  <Users className="w-3.5 h-3.5 text-slate-400" />
                  <span>{currentSpace.listeners_count} Listening</span>
                </span>
              </div>
              <h2 className="text-base sm:text-lg font-black text-slate-900 tracking-tight mt-0.5 line-clamp-1">
                {currentSpace.title}
              </h2>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-600 flex items-center justify-center text-sm font-bold transition cursor-pointer"
            title="Leave Audio Room"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable Room Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5 no-scrollbar relative bg-slate-50/50">
          {/* Floating Reactions Layer */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden z-30">
            <AnimatePresence>
              {floatingEmojis.map((item) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 350, scale: 0.6 }}
                  animate={{ opacity: 1, y: 40, scale: 1.3 }}
                  exit={{ opacity: 0, y: -20, scale: 1.6 }}
                  transition={{ duration: 2.2, ease: "easeOut" }}
                  style={{ left: `${item.x}%` }}
                  className="absolute text-3xl select-none"
                >
                  {item.emoji}
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {/* Active Diagnostic Case Card */}
          <div className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-xs">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-black uppercase tracking-wider text-teal-800 flex items-center gap-1.5">
                <Radio className="w-3.5 h-3.5 text-teal-600 animate-pulse" />
                <span>Case Discussion</span>
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-teal-50 text-teal-800 border border-teal-200">
                Live Rounds
              </span>
            </div>
            <h4 className="font-extrabold text-sm text-slate-900">
              {currentSpace.active_case_title}
            </h4>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Doctors discussing treatment options, patient monitoring, and clinical guidelines in real time.
            </p>
          </div>

          {/* Speakers Podium Grid */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-black uppercase tracking-wider text-slate-700">
                Speakers ({currentSpace.speakers.length})
              </h3>
              <span className="text-[10px] text-teal-700 font-bold bg-teal-50 px-2 py-0.5 rounded-full border border-teal-100">
                Verified Doctors
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {currentSpace.speakers.map((speaker, index) => {
                const isSpeaking = speaker.is_speaking || (!isMuted && index === 0);
                return (
                  <div
                    key={speaker.id}
                    className="p-3.5 rounded-2xl bg-white border border-slate-200/90 shadow-xs flex flex-col items-center text-center relative group"
                  >
                    {/* Speaking Ripple Wave */}
                    <div className="relative mb-2">
                      {isSpeaking && (
                        <span className="absolute -inset-1 rounded-full bg-teal-500/30 animate-ping" />
                      )}
                      <div
                        className={`w-14 h-14 rounded-full bg-gradient-to-tr ${speaker.avatar_gradient} text-white font-black text-base flex items-center justify-center shadow-md relative z-10 transition-transform ${
                          isSpeaking ? "scale-105 ring-4 ring-teal-500" : ""
                        }`}
                      >
                        {speaker.name ? speaker.name.replace(/Dr\.\s*/i, "")[0] : "D"}
                      </div>

                      {/* Mic / Host Badge */}
                      <span className="absolute -bottom-1 -right-1 z-20 w-5 h-5 rounded-full bg-teal-600 text-white flex items-center justify-center text-[10px] border-2 border-white shadow-xs">
                        {speaker.role === "host" ? "👑" : "🎙️"}
                      </span>
                    </div>

                    <h5 className="font-bold text-xs text-slate-900 truncate w-full">
                      {speaker.name}
                    </h5>
                    <p className="text-[10px] text-slate-500 truncate w-full mt-0.5">
                      {speaker.specialty}
                    </p>

                    <div className="mt-2 flex items-center gap-1">
                      {isSpeaking ? (
                        <span className="inline-flex items-center gap-1 text-[9px] font-black text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full border border-teal-200">
                          <span className="w-1.5 h-1.5 rounded-full bg-teal-600 animate-pulse" />
                          Speaking
                        </span>
                      ) : (
                        <span className="text-[9px] font-medium text-slate-400 capitalize">
                          {speaker.role}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Bottom Controller Bar */}
        <div className="p-4 bg-white border-t border-slate-200 flex flex-wrap items-center justify-between gap-3">
          {/* Reaction Emojis Bar (Twitter Spaces style) */}
          <div className="flex items-center gap-1.5 bg-slate-50 p-1.5 rounded-2xl border border-slate-200">
            {["👏", "💡", "❤️", "🩺", "🔥"].map((emoji) => (
              <button
                key={emoji}
                type="button"
                onClick={() => triggerReaction(emoji)}
                className="w-8 h-8 rounded-xl hover:bg-white text-lg transition-transform active:scale-125 flex items-center justify-center cursor-pointer shadow-xs"
              >
                {emoji}
              </button>
            ))}
          </div>

          {/* Interactive Mic Controls */}
          <div className="flex items-center gap-2">
            {/* Raise Hand Toggle */}
            <button
              type="button"
              onClick={toggleHandRaise}
              className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition shadow-xs cursor-pointer ${
                handRaised
                  ? "bg-amber-100 text-amber-900 border border-amber-300"
                  : "bg-slate-100 hover:bg-slate-200 text-slate-700"
              }`}
            >
              <Hand className={`w-4 h-4 ${handRaised ? "text-amber-600 animate-bounce" : "text-slate-500"}`} />
              <span>{handRaised ? "Hand Raised" : "Raise Hand"}</span>
            </button>

            {/* Mute / Unmute Toggle */}
            <button
              type="button"
              onClick={toggleMic}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-black transition shadow-xs cursor-pointer ${
                !isMuted
                  ? "bg-teal-600 hover:bg-teal-700 text-white"
                  : "bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200"
              }`}
            >
              {!isMuted ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
              <span>{!isMuted ? "Mic On (Mute)" : "Mic Muted"}</span>
            </button>

            {/* Leave Space */}
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition cursor-pointer"
            >
              Leave Room
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
