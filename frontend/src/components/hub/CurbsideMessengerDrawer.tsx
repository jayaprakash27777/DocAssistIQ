"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { getSharedRealtimeClient } from "@/lib/ws";
import { getStoredToken } from "@/lib/api";
import { Send, AlertTriangle, Paperclip, Mic, MicOff, Minus, Maximize2, X, MessageSquare, ShieldCheck, CheckCheck } from "lucide-react";

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

export interface Colleague {
  id: string;
  name: string;
  specialty: string;
  status: string;
  isOnline: boolean;
  avatarGradient: string;
  last_message?: string | null;
  last_message_time?: string | null;
}

interface CurbsideMessengerDrawerProps {
  onClose: () => void;
  activeCaseToAttach?: { id: string; disease_name: string; diagnosis?: string } | null;
  onClearAttachedCase?: () => void;
  targetColleagueId?: string | null;
}

export function CurbsideMessengerDrawer({
  onClose,
  activeCaseToAttach,
  onClearAttachedCase,
  targetColleagueId,
}: CurbsideMessengerDrawerProps) {
  const [isMinimized, setIsMinimized] = useState(false);
  const [colleagues, setColleagues] = useState<Colleague[]>([]);
  const [selectedColleague, setSelectedColleague] = useState<Colleague | null>(null);
  const [messageText, setMessageText] = useState("");
  const [isStatPriority, setIsStatPriority] = useState(false);
  const [messages, setMessages] = useState<CurbsideMessage[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [isRecordingVoice, setIsRecordingVoice] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Fetch real colleagues from API
  useEffect(() => {
    const token = getStoredToken();
    fetch("/api/v1/hub/curbside/colleagues", {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((res) => (res.ok ? res.json() : []))
      .then((data: Colleague[]) => {
        if (Array.isArray(data) && data.length > 0) {
          setColleagues(data);
          if (targetColleagueId) {
            const target = data.find((c) => c.id === targetColleagueId);
            setSelectedColleague(target || data[0]);
          } else {
            setSelectedColleague(data[0]);
          }
        }
      })
      .catch(() => {});
  }, [targetColleagueId]);

  // Fetch real messages for the selected colleague
  useEffect(() => {
    if (!selectedColleague) return;
    setLoadingMessages(true);
    const token = getStoredToken();
    fetch(`/api/v1/hub/curbside/history?colleague_id=${selectedColleague.id}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((res) => (res.ok ? res.json() : []))
      .then((data: CurbsideMessage[]) => {
        if (Array.isArray(data)) {
          setMessages(data);
        }
      })
      .catch(() => {})
      .finally(() => setLoadingMessages(false));
  }, [selectedColleague]);

  // Real-time WebSocket subscriptions for new curbside messages
  useEffect(() => {
    const token = getStoredToken();
    const ws = getSharedRealtimeClient(token);
    if (ws) {
      ws.connect();
      const unsub = ws.subscribeMessages((type, payload) => {
        if (type === "hub_new_curbside_message" && payload) {
          const incoming: CurbsideMessage = {
            id: payload.id || `msg-${Date.now()}`,
            sender_doctor_id: payload.sender_doctor_id || "peer",
            recipient_doctor_id: payload.recipient_doctor_id || "me",
            sender_name: payload.sender_name || "Dr. Colleague",
            sender_specialty: payload.sender_specialty || "Specialist",
            content: payload.content || "",
            priority: payload.priority === "stat" ? "stat" : "routine",
            case_id: payload.case_id,
            case_title: payload.case_title,
            has_voice_note: Boolean(payload.has_voice_note),
            voice_duration: payload.voice_duration,
            created_at: payload.created_at || new Date().toISOString(),
            is_read: true,
          };

          setMessages((prev) => {
            if (prev.some((m) => m.id === incoming.id)) return prev;
            return [...prev, incoming];
          });
        }
      });
      return () => {
        unsub();
      };
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isMinimized]);

  const handleSendMessage = async () => {
    if ((!messageText.trim() && !activeCaseToAttach) || !selectedColleague) return;

    const currentText = messageText.trim() || "Attached clinical case for second opinion.";
    const currentPriority = isStatPriority ? "stat" : "routine";

    // Optimistic message
    const tempId = `temp-${Date.now()}`;
    const optimisticMsg: CurbsideMessage = {
      id: tempId,
      sender_doctor_id: "me",
      recipient_doctor_id: selectedColleague.id,
      sender_name: "Dr. Attending (You)",
      sender_specialty: "Clinical Specialist",
      content: currentText,
      priority: currentPriority,
      case_id: activeCaseToAttach?.id,
      case_title: activeCaseToAttach?.disease_name,
      has_voice_note: isRecordingVoice,
      voice_duration: isRecordingVoice ? 8 : undefined,
      created_at: new Date().toISOString(),
      is_read: true,
    };

    setMessages((prev) => [...prev, optimisticMsg]);
    setMessageText("");
    setIsRecordingVoice(false);
    if (onClearAttachedCase) onClearAttachedCase();

    try {
      const token = getStoredToken();
      const res = await fetch("/api/v1/hub/curbside/messages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          peer_doctor_id: selectedColleague.id,
          content: currentText,
          priority: currentPriority,
          case_id: activeCaseToAttach?.id,
          has_voice_note: optimisticMsg.has_voice_note,
          voice_duration: optimisticMsg.voice_duration,
        }),
      });
      if (res.ok) {
        const savedMsg = await res.json();
        setMessages((prev) =>
          prev.map((m) => (m.id === tempId ? { ...savedMsg, id: savedMsg.id } : m))
        );
      }
    } catch {}
  };

  return (
    <div className="fixed bottom-4 right-4 z-[115] flex flex-col items-end">
      {/* Minimized Pill */}
      {isMinimized ? (
        <motion.button
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          type="button"
          onClick={() => setIsMinimized(false)}
          className="flex items-center gap-2.5 px-4 py-3 bg-teal-600 hover:bg-teal-700 text-white rounded-full font-bold shadow-xl border border-teal-500 cursor-pointer transition-all"
        >
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-300 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400" />
          </span>
          <span className="text-xs">
            Doctor Chat ({selectedColleague?.name.split(",")[0] || "Online"})
          </span>
          <span className="text-[10px] bg-teal-800 px-1.5 py-0.5 rounded-full font-mono">
            {messages.length}
          </span>
        </motion.button>
      ) : (
        /* Expanded Messenger Window - Clean light theme */
        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 30, scale: 0.95 }}
          className="w-[94vw] sm:w-[440px] h-[580px] max-h-[85vh] rounded-3xl bg-white border border-slate-200/90 shadow-2xl flex flex-col overflow-hidden"
        >
          {/* Header */}
          <div className="p-3.5 bg-white border-b border-slate-200 flex items-center justify-between gap-2 shadow-xs">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="relative">
                <div
                  className={`w-9 h-9 rounded-full bg-gradient-to-tr ${
                    selectedColleague?.avatarGradient || "from-teal-600 to-emerald-500"
                  } text-white font-black text-xs flex items-center justify-center shrink-0 shadow-xs`}
                >
                  {selectedColleague?.name ? selectedColleague.name.replace(/Dr\.\s*/i, "")[0] : "D"}
                </div>
                <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 border-2 border-white" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1">
                  <h4 className="font-extrabold text-xs text-slate-900 truncate">
                    {selectedColleague?.name || "Doctor Chat"}
                  </h4>
                  <ShieldCheck className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                </div>
                <p className="text-[10px] text-slate-500 truncate">
                  {selectedColleague?.specialty || "Verified Doctor"} • {selectedColleague?.status || "Available"}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1 shrink-0">
              <button
                type="button"
                onClick={() => setIsMinimized(true)}
                className="w-7 h-7 rounded-lg hover:bg-slate-100 text-slate-500 flex items-center justify-center transition cursor-pointer"
                title="Minimize"
              >
                <Minus className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={onClose}
                className="w-7 h-7 rounded-lg hover:bg-slate-100 text-slate-500 flex items-center justify-center transition cursor-pointer"
                title="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Colleague Selection Pill Strip */}
          {colleagues.length > 1 && (
            <div className="px-3 py-2 bg-slate-50 border-b border-slate-100 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
              <span className="text-[10px] font-bold text-slate-400 shrink-0 uppercase tracking-wider">
                Doctors:
              </span>
              {colleagues.map((colleague) => {
                const isSelected = selectedColleague?.id === colleague.id;
                return (
                  <button
                    key={colleague.id}
                    type="button"
                    onClick={() => setSelectedColleague(colleague)}
                    className={`px-2.5 py-1 rounded-xl text-[11px] font-bold transition-all shrink-0 flex items-center gap-1 cursor-pointer ${
                      isSelected
                        ? "bg-teal-600 text-white shadow-xs"
                        : "bg-white hover:bg-slate-100 text-slate-700 border border-slate-200/80"
                    }`}
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    <span>{colleague.name.replace(/^(Dr\.\s*)/i, "").split(",")[0]}</span>
                  </button>
                );
              })}
            </div>
          )}

          {/* Active Attached Case Pill (if attached from post card) */}
          {activeCaseToAttach && (
            <div className="p-2.5 bg-rose-50 border-b border-rose-100 flex items-center justify-between gap-2 text-xs">
              <div className="flex items-center gap-1.5 min-w-0">
                <Paperclip className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                <span className="font-bold text-rose-900 truncate">
                  Case attached: {activeCaseToAttach.disease_name}
                </span>
              </div>
              {onClearAttachedCase && (
                <button
                  type="button"
                  onClick={onClearAttachedCase}
                  className="text-rose-600 hover:text-rose-800 text-[10px] font-bold cursor-pointer"
                >
                  Detach
                </button>
              )}
            </div>
          )}

          {/* Messages Feed */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50/40 no-scrollbar">
            {loadingMessages ? (
              <div className="text-center py-10 text-xs text-slate-400">Loading conversation...</div>
            ) : messages.length === 0 ? (
              <div className="text-center py-12 text-slate-400 space-y-2">
                <MessageSquare className="w-8 h-8 mx-auto text-slate-300" />
                <p className="text-xs font-bold text-slate-700">No messages yet</p>
                <p className="text-[11px] text-slate-400 max-w-[240px] mx-auto">
                  Send a private message or discuss a patient case with {selectedColleague?.name || "a colleague"}.
                </p>
              </div>
            ) : (
              messages.map((msg) => {
                const isMe = msg.sender_doctor_id === "me" || msg.sender_name.includes("You");
                const isStat = msg.priority === "stat";

                return (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${isMe ? "items-end" : "items-start"}`}
                  >
                    {/* Sender label */}
                    <div className="flex items-center gap-1 text-[10px] text-slate-400 px-1 mb-0.5 font-medium">
                      <span>{msg.sender_name.split(",")[0]}</span>
                      {isStat && (
                        <span className="bg-rose-100 text-rose-800 font-extrabold px-1.5 py-0.2 rounded text-[9px]">
                          🚨 URGENT
                        </span>
                      )}
                    </div>

                    {/* Chat Bubble */}
                    <div
                      className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-xs shadow-xs leading-relaxed ${
                        isMe
                          ? "bg-teal-600 text-white rounded-br-xs"
                          : isStat
                          ? "bg-rose-50 border border-rose-200 text-rose-950 rounded-bl-xs"
                          : "bg-white border border-slate-200 text-slate-900 rounded-bl-xs"
                      }`}
                    >
                      {/* Attached Case header in bubble */}
                      {msg.case_title && (
                        <div
                          className={`mb-1.5 pb-1.5 text-[10px] font-bold border-b ${
                            isMe ? "border-teal-500 text-teal-100" : "border-slate-200 text-teal-700"
                          }`}
                        >
                          📌 Case: {msg.case_title}
                        </div>
                      )}

                      <p>{msg.content}</p>

                      {/* Simulated Voice note indicator */}
                      {msg.has_voice_note && (
                        <div className="mt-2 pt-1.5 border-t border-teal-500/30 flex items-center gap-2">
                          <button
                            type="button"
                            className="w-6 h-6 rounded-full bg-white text-teal-700 flex items-center justify-center text-xs font-bold shadow-xs cursor-pointer"
                          >
                            ▶
                          </button>
                          <div className="flex-1 flex items-center gap-0.5">
                            {[1, 2, 3, 4, 5, 6].map((n) => (
                              <span
                                key={n}
                                className={`w-1 rounded-full ${isMe ? "bg-white/80" : "bg-teal-600"}`}
                                style={{ height: `${4 + (n % 4) * 4}px` }}
                              />
                            ))}
                          </div>
                          <span className="text-[10px] opacity-80 font-mono">
                            0:{msg.voice_duration || 8}s
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Timestamp */}
                    <div className="flex items-center gap-1 text-[9px] text-slate-400 px-1 mt-0.5">
                      <span>
                        {msg.created_at.includes("T")
                          ? new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                          : msg.created_at}
                      </span>
                      {isMe && <CheckCheck className="w-3 h-3 text-teal-600" />}
                    </div>
                  </div>
                );
              })
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Bottom Chat Composer Bar */}
          <div className="p-3 bg-white border-t border-slate-200 space-y-2">
            {/* Priority Selector & Voice Toggle */}
            <div className="flex items-center justify-between text-xs px-0.5">
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => setIsStatPriority(false)}
                  className={`px-2 py-0.5 rounded-lg text-[10px] font-bold transition cursor-pointer ${
                    !isStatPriority
                      ? "bg-slate-200 text-slate-900 font-extrabold"
                      : "text-slate-500 hover:text-slate-800"
                  }`}
                >
                  Standard
                </button>
                <button
                  type="button"
                  onClick={() => setIsStatPriority(true)}
                  className={`px-2 py-0.5 rounded-lg text-[10px] font-bold transition cursor-pointer flex items-center gap-1 ${
                    isStatPriority
                      ? "bg-rose-600 text-white font-extrabold shadow-xs"
                      : "text-rose-600 hover:bg-rose-50"
                  }`}
                >
                  <AlertTriangle className="w-3 h-3" />
                  <span>🚨 Urgent</span>
                </button>
              </div>

              <button
                type="button"
                onClick={() => setIsRecordingVoice(!isRecordingVoice)}
                className={`flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-lg transition cursor-pointer ${
                  isRecordingVoice
                    ? "bg-rose-100 text-rose-700 animate-pulse border border-rose-200"
                    : "text-slate-500 hover:bg-slate-100"
                }`}
                title="Attach Voice Note"
              >
                {isRecordingVoice ? <Mic className="w-3 h-3 text-rose-600" /> : <MicOff className="w-3 h-3 text-slate-400" />}
                <span>{isRecordingVoice ? "Voice Attached" : "Add Voice"}</span>
              </button>
            </div>

            {/* Input Row */}
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder={
                  activeCaseToAttach
                    ? "Ask about this case..."
                    : "Type a message..."
                }
                value={messageText}
                onChange={(e) => setMessageText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                className="flex-1 px-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-900 outline-none focus:bg-white focus:border-teal-600 transition"
              />

              <button
                type="button"
                onClick={handleSendMessage}
                disabled={!messageText.trim() && !activeCaseToAttach}
                className="w-9 h-9 rounded-xl bg-teal-600 hover:bg-teal-700 disabled:opacity-40 text-white flex items-center justify-center transition shadow-xs cursor-pointer shrink-0"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
