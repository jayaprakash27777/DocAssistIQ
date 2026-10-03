"use client";

import React, { useState, useEffect, useRef } from "react";
import { X, Send, Stethoscope, Lock, MessageSquare } from "lucide-react";
import { CurbsideMessage } from "@/types/social";
import { getStoredToken } from "@/lib/api";
import { getSharedRealtimeClient } from "@/lib/ws";

interface CurbsideConsultDrawerProps {
  postId: string;
  caseTitle: string;
  authorDoctorId: string;
  authorDoctorName: string;
  authorSpecialty?: string;
  onClose: () => void;
}

export function CurbsideConsultDrawer({
  postId,
  caseTitle,
  authorDoctorId,
  authorDoctorName,
  authorSpecialty = "Specialist",
  onClose,
}: CurbsideConsultDrawerProps) {
  const [messages, setMessages] = useState<CurbsideMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    fetchMessages();
  }, [postId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Subscribe to real-time curbside messages via WebSocket
  useEffect(() => {
    const token = getStoredToken();
    const ws = getSharedRealtimeClient(token);

    const unsub = ws.subscribeMessages((type, payload) => {
      if (type === "hub_new_curbside_message" && payload?.post_id === postId) {
        setMessages((prev) => {
          if (prev.some((m) => m.id === payload.id)) return prev;
          return [...prev, payload];
        });
      }
    });

    return () => {
      unsub();
    };
  }, [postId]);

  const fetchMessages = async () => {
    setLoading(true);
    try {
      const token = getStoredToken();
      const res = await fetch(`/api/v1/hub/curbside/${postId}/messages`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data);
      }
    } catch {
      // Gracefully start with empty
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const textToSend = inputText.trim();
    setInputText("");
    setSending(true);

    try {
      const token = getStoredToken();
      const res = await fetch("/api/v1/hub/curbside/messages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          post_id: postId,
          receiver_id: authorDoctorId,
          content: textToSend,
        }),
      });

      if (res.ok) {
        const newMsg: CurbsideMessage = await res.json();
        setMessages((prev) => [...prev, newMsg]);
      }
    } catch (err) {
      console.error("Failed to send curbside message:", err);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-xs">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col border-l border-slate-200 animate-in slide-in-from-right duration-200">
        {/* Drawer Header */}
        <div className="p-4 border-b border-slate-200/90 flex items-center justify-between bg-slate-50/70">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-10 h-10 rounded-full bg-teal-600 text-white font-black text-sm flex items-center justify-center shrink-0 shadow-xs">
              {authorDoctorName ? authorDoctorName[0].toUpperCase() : "D"}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-black text-xs text-slate-900 truncate">
                  {authorDoctorName}
                </span>
                <span className="text-[10px] bg-teal-50 text-teal-800 font-bold px-1.5 py-0.2 rounded border border-teal-200">
                  Verified
                </span>
              </div>
              <p className="text-[11px] text-slate-500 truncate">{authorSpecialty}</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 rounded-xl transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Linked Case Reference Strip */}
        <div className="px-4 py-2 bg-teal-50/60 border-b border-teal-100 flex items-center justify-between text-xs">
          <div className="flex items-center gap-1.5 text-teal-900 font-bold truncate">
            <Stethoscope className="w-3.5 h-3.5 text-teal-600 shrink-0" />
            <span className="truncate">Ref: {caseTitle}</span>
          </div>
          <span className="inline-flex items-center gap-1 text-[10px] text-teal-700 font-medium shrink-0">
            <Lock className="w-3 h-3" />
            Encrypted
          </span>
        </div>

        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[#f8fafc]">
          {loading ? (
            <div className="text-center py-12 text-slate-400 text-xs">
              Loading curbside consultation history...
            </div>
          ) : messages.length === 0 ? (
            <div className="text-center py-12 space-y-2">
              <div className="w-10 h-10 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center mx-auto">
                <MessageSquare className="w-5 h-5" />
              </div>
              <h4 className="text-xs font-bold text-slate-800">
                Direct Curbside Consultation
              </h4>
              <p className="text-[11px] text-slate-500 max-w-xs mx-auto leading-relaxed">
                Connect directly with {authorDoctorName} regarding dosing, diagnostic dilemmas, or inter-hospital transfer coordination.
              </p>
            </div>
          ) : (
            messages.map((m) => {
              const isMe = m.sender_id !== authorDoctorId;
              return (
                <div
                  key={m.id}
                  className={`flex flex-col ${isMe ? "items-end" : "items-start"}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-xs shadow-2xs leading-relaxed ${
                      isMe
                        ? "bg-teal-600 text-white rounded-br-xs"
                        : "bg-white text-slate-800 border border-slate-200 rounded-bl-xs"
                    }`}
                  >
                    {!isMe && (
                      <p className="text-[10px] font-black text-teal-700 mb-0.5">
                        {m.sender_name}
                      </p>
                    )}
                    <p>{m.content}</p>
                  </div>
                  <span className="text-[9px] text-slate-400 mt-1 font-mono px-1">
                    {new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
              );
            })
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <form onSubmit={handleSend} className="p-3 border-t border-slate-200 bg-white flex gap-2">
          <input
            type="text"
            required
            placeholder={`Message Dr. ${authorDoctorName.split(" ").slice(-1)[0]}...`}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            className="flex-1 px-3.5 py-2 rounded-xl border border-slate-300 text-xs text-slate-900 bg-slate-50 focus:bg-white outline-none focus:border-teal-600"
          />
          <button
            type="submit"
            disabled={sending || !inputText.trim()}
            className="px-3.5 py-2 bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white rounded-xl transition shadow-xs cursor-pointer flex items-center justify-center"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}

export default CurbsideConsultDrawer;
