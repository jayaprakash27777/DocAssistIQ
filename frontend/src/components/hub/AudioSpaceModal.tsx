"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

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
  space: AudioSpaceData | null;
  onClose: () => void;
  onReaction?: (reaction: string) => void;
  isNightMode?: boolean;
}

interface FloatingEmoji {
  id: number;
  emoji: string;
  x: number;
}

export function AudioSpaceModal({
  space,
  onClose,
  onReaction,
  isNightMode = false,
}: AudioSpaceModalProps) {
  const [handRaised, setHandRaised] = useState(false);
  const [isMuted, setIsMuted] = useState(true);
  const [floatingEmojis, setFloatingEmojis] = useState<FloatingEmoji[]>([]);
  const [activeSpeakerIndex, setActiveSpeakerIndex] = useState(0);

  // Fallback demo space if none provided
  const currentSpace: AudioSpaceData = space || {
    id: "space-live-1",
    title: "🔴 LIVE Grand Rounds: Acute Cardiogenic Shock & Impella-ECMO Escalation",
    specialty: "Cardiology & Critical Care",
    listeners_count: 54,
    is_live: true,
    active_case_title: "Wellens' Syndrome Type A with Imminent Proximal LAD Occlusion",
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
        specialty: "Pediatrics & Critical Care",
        role: "listener",
        is_speaking: false,
        avatar_gradient: "from-amber-600 to-orange-600",
      },
    ],
    tags: ["ECMO", "Shock", "CathLab", "LiveGrandRounds"],
  };

  // Simulate speaker switching periodically
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveSpeakerIndex((prev) => (prev === 0 ? 1 : 0));
    }, 4500);
    return () => clearInterval(interval);
  }, []);

  const triggerReaction = (emoji: string) => {
    const newId = Date.now() + Math.random();
    const randomX = Math.floor(Math.random() * 60) + 20; // 20% to 80%
    setFloatingEmojis((prev) => [...prev, { id: newId, emoji, x: randomX }]);
    setTimeout(() => {
      setFloatingEmojis((prev) => prev.filter((item) => item.id !== newId));
    }, 2400);

    if (onReaction) onReaction(emoji);
  };

  const bgModal = isNightMode
    ? "bg-slate-900/95 border-slate-800 text-slate-100"
    : "bg-white border-slate-200 text-slate-900";

  const cardSubtle = isNightMode
    ? "bg-slate-800/80 border-slate-700/80"
    : "bg-slate-50 border-slate-200/90";

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className={`relative w-full max-w-2xl max-h-[92vh] flex flex-col rounded-3xl border shadow-2xl overflow-hidden ${bgModal}`}
      >
        {/* Top Header Bar */}
        <div className="p-5 border-b border-slate-200/80 dark:border-slate-800 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-500 opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-600" />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-black tracking-wider bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-200 dark:border-rose-900/60 px-2 py-0.5 rounded-full">
                  Grand Rounds Live Space
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                  🎧 {currentSpace.listeners_count} Tuned In
                </span>
              </div>
              <h2 className="text-base sm:text-lg font-black tracking-tight mt-0.5 line-clamp-1">
                {currentSpace.title}
              </h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-300 flex items-center justify-center text-sm font-bold transition-colors cursor-pointer"
            title="Leave Space"
          >
            ✕
          </button>
        </div>

        {/* Scrollable Stage Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5 custom-scrollbar relative">
          {/* Floating Emojis Layer */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden z-30">
            <AnimatePresence>
              {floatingEmojis.map((item) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 350, scale: 0.6 }}
                  animate={{ opacity: 1, y: 50, scale: 1.3 }}
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

          {/* Active Diagnostic Whiteboard / Pinned Case */}
          <div className={`p-4 rounded-2xl border ${cardSubtle}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-black uppercase tracking-wider text-teal-700 dark:text-teal-400 flex items-center gap-1.5">
                <span>📌 Active Case Under Review:</span>
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-teal-100/70 text-teal-800 dark:bg-teal-950 dark:text-teal-300 border border-teal-200 dark:border-teal-800">
                Synchronized Display
              </span>
            </div>
            <h4 className="font-bold text-sm text-slate-800 dark:text-slate-100">
              {currentSpace.active_case_title}
            </h4>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
              Dr. Chen is presenting the catheterization angiogram showing 95% proximal LAD stenosis.
              Discussion centers on immediate DAPT titration and timing of hemodynamic unloading.
            </p>
          </div>

          {/* Equalizer Waveform Animation */}
          <div className="flex items-center justify-center gap-1.5 py-2">
            {[40, 75, 95, 60, 80, 100, 50, 85, 65, 90, 70, 45].map((height, i) => (
              <motion.div
                key={i}
                animate={{
                  height: [12, height * 0.45, 12],
                }}
                transition={{
                  duration: 0.8 + (i % 4) * 0.2,
                  repeat: Infinity,
                  repeatType: "reverse",
                  ease: "easeInOut",
                }}
                className="w-1.5 rounded-full bg-gradient-to-t from-teal-500 to-emerald-400"
                style={{ minHeight: "8px" }}
              />
            ))}
          </div>

          {/* Stage Speakers Grid */}
          <div>
            <h3 className="text-xs font-black uppercase tracking-wider text-slate-400 mb-3">
              Speakers on Stage ({currentSpace.speakers.filter((s) => s.role !== "listener").length})
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {currentSpace.speakers
                .filter((s) => s.role !== "listener")
                .map((speaker, idx) => {
                  const isCurrentlyTalking = idx === activeSpeakerIndex;
                  return (
                    <div
                      key={speaker.id}
                      className={`p-3.5 rounded-2xl border text-center transition-all relative ${
                        isCurrentlyTalking
                          ? "bg-teal-50/80 dark:bg-teal-950/40 border-teal-400 dark:border-teal-600 shadow-md ring-2 ring-teal-400/40"
                          : cardSubtle
                      }`}
                    >
                      <div className="relative inline-block mx-auto mb-2">
                        <div
                          className={`w-14 h-14 rounded-full bg-gradient-to-br ${speaker.avatar_gradient} text-white flex items-center justify-center font-black text-lg shadow-md`}
                        >
                          {speaker.name[4] || "D"}
                        </div>
                        {isCurrentlyTalking && (
                          <span className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-emerald-500 border-2 border-white dark:border-slate-900 flex items-center justify-center text-[10px] text-white">
                            🎙️
                          </span>
                        )}
                      </div>
                      <p className="font-extrabold text-xs text-slate-900 dark:text-slate-100 truncate">
                        {speaker.name}
                      </p>
                      <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate mt-0.5">
                        {speaker.specialty}
                      </p>
                      <span
                        className={`inline-block mt-2 text-[9px] font-bold px-2 py-0.5 rounded-full ${
                          speaker.role === "host"
                            ? "bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200"
                            : "bg-slate-200/70 text-slate-700 dark:bg-slate-700 dark:text-slate-200"
                        }`}
                      >
                        {speaker.role === "host" ? "Host / Attending" : "Panelist"}
                      </span>
                    </div>
                  );
                })}
            </div>
          </div>

          {/* Listeners Grid */}
          <div>
            <h3 className="text-xs font-black uppercase tracking-wider text-slate-400 mb-3">
              Specialists Listening ({currentSpace.listeners_count})
            </h3>
            <div className="flex flex-wrap gap-2.5">
              {[
                { name: "Dr. Elena Rostova", spec: "Pediatrics" },
                { name: "Dr. Priya Nair", spec: "Dermatology" },
                { name: "Dr. James Wilson", spec: "Pulmonology" },
                { name: "Dr. Alicia Mendez", spec: "Nephrology" },
                { name: "Dr. Tariq Al-Mansoor", spec: "Cardiology Fellow" },
              ].map((doc, i) => (
                <div
                  key={i}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs ${cardSubtle}`}
                >
                  <div className="w-5 h-5 rounded-full bg-slate-400 text-white font-bold text-[9px] flex items-center justify-center">
                    {doc.name[4]}
                  </div>
                  <span className="font-bold text-slate-700 dark:text-slate-200">{doc.name}</span>
                  <span className="text-[9px] text-slate-400 font-mono">({doc.spec})</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom Reaction & Control Bar */}
        <div className="p-4 border-t border-slate-200/80 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/90 flex flex-wrap items-center justify-between gap-3">
          {/* Reaction Bursts */}
          <div className="flex items-center gap-1.5">
            {[
              { emoji: "🫀", label: "Heart" },
              { emoji: "💡", label: "Insight" },
              { emoji: "👏", label: "Endorse" },
              { emoji: "🚨", label: "STAT" },
              { emoji: "🧬", label: "Genetics" },
              { emoji: "🔬", label: "Pathology" },
            ].map((btn) => (
              <button
                key={btn.emoji}
                onClick={() => triggerReaction(btn.emoji)}
                className="w-9 h-9 rounded-full bg-white dark:bg-slate-800 hover:bg-teal-50 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-lg transition-transform active:scale-125 cursor-pointer shadow-xs"
                title={btn.label}
              >
                {btn.emoji}
              </button>
            ))}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setHandRaised(!handRaised)}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer border ${
                handRaised
                  ? "bg-amber-500 text-white border-amber-500 shadow-md ring-2 ring-amber-300"
                  : "bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-700 hover:bg-slate-100"
              }`}
            >
              <span>✋</span>
              <span>{handRaised ? "Hand Raised" : "Raise Hand"}</span>
            </button>

            <button
              onClick={() => setIsMuted(!isMuted)}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer border ${
                !isMuted
                  ? "bg-emerald-600 text-white border-emerald-600 shadow-md"
                  : "bg-slate-200/80 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-300 dark:border-slate-700"
              }`}
            >
              <span>{isMuted ? "🔇" : "🎙️"}</span>
              <span>{isMuted ? "Muted" : "Speaking"}</span>
            </button>

            <button
              onClick={onClose}
              className="px-4 py-2 bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/60 dark:hover:bg-rose-900/60 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900 text-xs font-bold rounded-xl transition-all cursor-pointer"
            >
              Leave Quietly
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
