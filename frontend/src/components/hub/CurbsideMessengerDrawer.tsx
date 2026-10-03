"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

export interface CurbsideMessage {
  id: string;
  sender_doctor_id: string;
  recipient_doctor_id: string;
  sender_name: string;
  sender_specialty: string;
  content: string;
  priority: "routine" | "stat";
  case_id?: string | null;
  case_title?: string | null;
  has_voice_note?: boolean;
  voice_duration?: number | null;
  created_at: string;
  is_read?: boolean;
}

interface Colleague {
  id: string;
  name: string;
  specialty: string;
  status: string;
  isOnline: boolean;
  avatarGradient: string;
}

const COLLEAGUES: Colleague[] = [
  {
    id: "dr-chen",
    name: "Dr. Sarah Chen, MD, FACC",
    specialty: "Interventional Cardiology",
    status: "Cath Lab On-Call",
    isOnline: true,
    avatarGradient: "from-teal-600 to-emerald-600",
  },
  {
    id: "dr-thorne",
    name: "Dr. Marcus Thorne, MD, FACEP",
    specialty: "Emergency Medicine",
    status: "Resus Bay Active",
    isOnline: true,
    avatarGradient: "from-rose-600 to-pink-600",
  },
  {
    id: "dr-vance",
    name: "Dr. David Vance, MD, FAAN",
    specialty: "Neurology",
    status: "Neuro-ICU Rounds",
    isOnline: true,
    avatarGradient: "from-indigo-600 to-purple-600",
  },
  {
    id: "dr-rostova",
    name: "Dr. Elena Rostova, MD, PhD",
    specialty: "Pediatrics",
    status: "Clinic Available",
    isOnline: false,
    avatarGradient: "from-amber-600 to-orange-600",
  },
  {
    id: "dr-nair",
    name: "Dr. Priya Nair, MD, DNB",
    specialty: "Dermatology",
    status: "Derm-ICU Consults",
    isOnline: true,
    avatarGradient: "from-cyan-600 to-blue-600",
  },
];

interface CurbsideMessengerDrawerProps {
  onClose: () => void;
  activeCaseToAttach?: { id: string; disease_name: string; diagnosis: string } | null;
  onClearAttachedCase?: () => void;
  isNightMode?: boolean;
}

export function CurbsideMessengerDrawer({
  onClose,
  activeCaseToAttach,
  onClearAttachedCase,
  isNightMode = false,
}: CurbsideMessengerDrawerProps) {
  const [isMinimized, setIsMinimized] = useState(false);
  const [selectedColleague, setSelectedColleague] = useState<Colleague>(COLLEAGUES[0]);
  const [messageText, setMessageText] = useState("");
  const [isStatPriority, setIsStatPriority] = useState(false);
  const [isPlayingVoice, setIsPlayingVoice] = useState<string | null>(null);

  const [messages, setMessages] = useState<CurbsideMessage[]>([
    {
      id: "msg-1",
      sender_doctor_id: "dr-chen",
      recipient_doctor_id: "me",
      sender_name: "Dr. Sarah Chen, MD",
      sender_specialty: "Cardiology",
      content:
        "Colleague, reviewing your Wellens syndrome presentation. Did the patient exhibit any reperfusion arrhythmias post-stenting?",
      priority: "routine",
      case_id: "wellens-1",
      case_title: "Wellens' Syndrome Type A LAD Stenosis",
      has_voice_note: false,
      created_at: "10 mins ago",
      is_read: true,
    },
    {
      id: "msg-2",
      sender_doctor_id: "me",
      recipient_doctor_id: "dr-chen",
      sender_name: "Dr. Attending (You)",
      sender_specialty: "Internal Medicine",
      content:
        "Zero VT/VF noted. Hemodynamics remained rock-solid on maintenance beta-blockade and DAPT. Patient discharged to cardiac rehab.",
      priority: "routine",
      has_voice_note: false,
      created_at: "8 mins ago",
      is_read: true,
    },
    {
      id: "msg-3",
      sender_doctor_id: "dr-chen",
      recipient_doctor_id: "me",
      sender_name: "Dr. Sarah Chen, MD",
      sender_specialty: "Cardiology",
      content: "Recorded a 12s voice debrief regarding antiplatelet continuation:",
      priority: "routine",
      has_voice_note: true,
      voice_duration: 12,
      created_at: "4 mins ago",
      is_read: true,
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isMinimized]);

  const handleSendMessage = () => {
    if (!messageText.trim() && !activeCaseToAttach) return;

    const newMsg: CurbsideMessage = {
      id: `msg-${Date.now()}`,
      sender_doctor_id: "me",
      recipient_doctor_id: selectedColleague.id,
      sender_name: "Dr. Attending (You)",
      sender_specialty: "Attending Physician",
      content: messageText.trim() || "Attached clinical case for second opinion.",
      priority: isStatPriority ? "stat" : "routine",
      case_id: activeCaseToAttach?.id,
      case_title: activeCaseToAttach?.disease_name,
      has_voice_note: false,
      created_at: "Just now",
      is_read: true,
    };

    setMessages((prev) => [...prev, newMsg]);
    setMessageText("");
    if (onClearAttachedCase) onClearAttachedCase();

    // Simulate peer response after 2.5 seconds
    setTimeout(() => {
      const reply: CurbsideMessage = {
        id: `msg-${Date.now() + 1}`,
        sender_doctor_id: selectedColleague.id,
        recipient_doctor_id: "me",
        sender_name: selectedColleague.name,
        sender_specialty: selectedColleague.specialty,
        content: isStatPriority
          ? "🚨 STAT Acknowledged. I am reviewing the diagnostic biomarkers immediately from the ICU terminal."
          : "Understood. The diagnostic findings align with current ESC/ACC practice parameters. Will add clinical note.",
        priority: isStatPriority ? "stat" : "routine",
        created_at: "Just now",
        is_read: true,
      };
      setMessages((prev) => [...prev, reply]);
    }, 2500);
  };

  const bgDrawer = isNightMode
    ? "bg-slate-900 border-slate-700 text-slate-100 shadow-2xl"
    : "bg-white border-slate-200 text-slate-900 shadow-2xl";

  const cardSubtle = isNightMode
    ? "bg-slate-800/80 border-slate-700/80"
    : "bg-slate-50 border-slate-200/90";

  return (
    <div className="fixed bottom-4 right-4 z-[105] flex flex-col items-end">
      {/* Minimized Pill */}
      {isMinimized ? (
        <motion.button
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          onClick={() => setIsMinimized(false)}
          className="flex items-center gap-2.5 px-4 py-3 bg-teal-600 hover:bg-teal-700 text-white rounded-full font-bold shadow-xl border border-teal-500 cursor-pointer transition-all"
        >
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-300 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400" />
          </span>
          <span className="text-xs">Curbside Consult ({selectedColleague.name.split(",")[0]})</span>
          <span className="text-[10px] bg-teal-800 px-1.5 py-0.5 rounded-full font-mono">
            {messages.length}
          </span>
        </motion.button>
      ) : (
        /* Expanded Messenger Window */
        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 30, scale: 0.95 }}
          className={`w-[360px] sm:w-[410px] h-[520px] rounded-3xl border flex flex-col overflow-hidden ${bgDrawer}`}
        >
          {/* Header */}
          <div className="p-3.5 border-b border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900/90 flex items-center justify-between gap-2">
            <div className="flex items-center gap-2.5 min-w-0">
              <div
                className={`w-9 h-9 rounded-full bg-gradient-to-br ${selectedColleague.avatarGradient} text-white flex items-center justify-center font-black text-xs shadow-xs flex-shrink-0 relative`}
              >
                {selectedColleague.name[4]}
                {selectedColleague.isOnline && (
                  <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-500 border-2 border-white dark:border-slate-900" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <h3 className="font-extrabold text-xs text-slate-900 dark:text-slate-100 truncate">
                    {selectedColleague.name}
                  </h3>
                </div>
                <p className="text-[10px] text-teal-700 dark:text-teal-400 font-bold truncate">
                  {selectedColleague.status}
                </p>
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-1">
              <button
                onClick={() => setIsMinimized(true)}
                className="w-7 h-7 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 flex items-center justify-center text-xs font-bold transition-colors cursor-pointer"
                title="Minimize"
              >
                —
              </button>
              <button
                onClick={onClose}
                className="w-7 h-7 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 flex items-center justify-center text-xs font-bold transition-colors cursor-pointer"
                title="Close"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Colleague Quick Switcher Bar */}
          <div className="px-3 py-1.5 border-b border-slate-100 dark:border-slate-800 flex items-center gap-2 overflow-x-auto custom-scrollbar bg-white dark:bg-slate-900">
            <span className="text-[9px] uppercase font-bold text-slate-400 whitespace-nowrap">
              Colleagues:
            </span>
            {COLLEAGUES.map((col) => (
              <button
                key={col.id}
                onClick={() => setSelectedColleague(col)}
                className={`px-2 py-0.5 rounded-full text-[10px] font-bold transition-all cursor-pointer whitespace-nowrap border ${
                  selectedColleague.id === col.id
                    ? "bg-teal-600 text-white border-teal-600 shadow-2xs"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700"
                }`}
              >
                {col.name.split(" ")[1]}
              </button>
            ))}
          </div>

          {/* Attached Case Notification Bar */}
          {activeCaseToAttach && (
            <div className="px-3 py-2 bg-amber-50 dark:bg-amber-950/50 border-b border-amber-200 dark:border-amber-900/60 flex items-center justify-between gap-2 text-xs">
              <div className="min-w-0">
                <span className="text-[10px] font-bold uppercase text-amber-800 dark:text-amber-300">
                  📎 Case Attached:
                </span>
                <p className="font-extrabold text-amber-950 dark:text-amber-100 truncate text-[11px]">
                  {activeCaseToAttach.disease_name}
                </p>
              </div>
              <button
                type="button"
                onClick={onClearAttachedCase}
                className="text-[10px] text-amber-800 dark:text-amber-300 hover:underline font-bold"
              >
                Remove
              </button>
            </div>
          )}

          {/* Messages Stream */}
          <div className="flex-1 overflow-y-auto p-3.5 space-y-3 custom-scrollbar">
            {messages.map((m) => {
              const isMe = m.sender_doctor_id === "me";
              return (
                <div
                  key={m.id}
                  className={`flex flex-col ${isMe ? "items-end" : "items-start"}`}
                >
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="text-[9px] font-bold text-slate-400">{m.sender_name}</span>
                    {m.priority === "stat" && (
                      <span className="text-[8px] bg-rose-600 text-white px-1.5 py-0.2 rounded-full font-black uppercase">
                        STAT
                      </span>
                    )}
                  </div>

                  {/* Attached Case Snippet inside Bubble */}
                  {m.case_title && (
                    <div
                      className={`mb-1 p-2 rounded-xl text-left max-w-[85%] border text-xs ${
                        isMe
                          ? "bg-teal-700/30 border-teal-500/50 text-teal-900 dark:text-teal-100"
                          : cardSubtle
                      }`}
                    >
                      <span className="text-[9px] uppercase font-bold text-teal-700 dark:text-teal-400">
                        📌 Clinical Reference
                      </span>
                      <p className="font-bold truncate mt-0.5">{m.case_title}</p>
                    </div>
                  )}

                  {/* Text bubble or Voice Memo */}
                  <div
                    className={`p-3 rounded-2xl max-w-[85%] text-xs leading-relaxed shadow-xs ${
                      isMe
                        ? "bg-teal-600 text-white rounded-br-xs"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-bl-xs border border-slate-200/80 dark:border-slate-700"
                    }`}
                  >
                    {m.has_voice_note ? (
                      <div className="flex items-center gap-2.5">
                        <button
                          onClick={() =>
                            setIsPlayingVoice(isPlayingVoice === m.id ? null : m.id)
                          }
                          className="w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 text-white flex items-center justify-center text-xs font-bold transition-transform active:scale-95"
                        >
                          {isPlayingVoice === m.id ? "⏸" : "▶"}
                        </button>
                        <div>
                          <div className="flex items-center gap-1">
                            {[16, 28, 12, 24, 32, 18, 26, 14, 22].map((h, idx) => (
                              <div
                                key={idx}
                                className={`w-1 rounded-full ${
                                  isPlayingVoice === m.id ? "bg-emerald-300 animate-pulse" : "bg-white/60"
                                }`}
                                style={{ height: `${h * 0.55}px` }}
                              />
                            ))}
                          </div>
                          <span className="text-[9px] opacity-80 mt-0.5 block font-mono">
                            Voice Consult • 0:{m.voice_duration || 12}
                          </span>
                        </div>
                      </div>
                    ) : (
                      m.content
                    )}
                  </div>

                  <div className="flex items-center gap-1 mt-0.5 text-[9px] text-slate-400 font-mono">
                    <span>{m.created_at}</span>
                    {isMe && <span>• Read ✓</span>}
                  </div>
                </div>
              );
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* Message Input & Priority Controls */}
          <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900/90 space-y-2">
            <div className="flex items-center justify-between">
              {/* Urgency Switch */}
              <button
                type="button"
                onClick={() => setIsStatPriority(!isStatPriority)}
                className={`px-2.5 py-1 rounded-lg text-[10px] font-bold flex items-center gap-1.5 transition-all cursor-pointer border ${
                  isStatPriority
                    ? "bg-rose-600 text-white border-rose-600 shadow-xs"
                    : "bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700"
                }`}
              >
                <span>{isStatPriority ? "🚨 STAT Paging Mode" : "Standard Consult"}</span>
              </button>

              <span className="text-[9px] text-slate-400 font-mono">
                🔒 HIPAA De-identified Channel
              </span>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder={`Message ${selectedColleague.name.split(" ")[1]}...`}
                value={messageText}
                onChange={(e) => setMessageText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSendMessage();
                }}
                className="flex-1 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-teal-500 shadow-xs"
              />
              <button
                onClick={handleSendMessage}
                disabled={!messageText.trim() && !activeCaseToAttach}
                className="px-3.5 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold disabled:opacity-40 transition-all cursor-pointer shadow-xs"
              >
                Send
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
