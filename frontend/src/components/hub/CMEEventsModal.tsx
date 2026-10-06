"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { getStoredToken } from "@/lib/api";
import { getSharedRealtimeClient } from "@/lib/ws";
import { Calendar, Clock, MapPin, Award, Check, Plus, Download, X, BookOpen, ShieldCheck } from "lucide-react";

export interface CMEEventData {
  id: string;
  title: string;
  specialty: string;
  date: string;
  time: string;
  speaker: string;
  speaker_title: string;
  cme_credits: number;
  location: string;
  rsvp_count: number;
  is_attending: boolean;
  topics: string[];
}

interface CMEEventsModalProps {
  events?: CMEEventData[];
  onToggleRSVP?: (eventId: string) => void;
  onClose: () => void;
}

export function CMEEventsModal({
  events: propEvents,
  onToggleRSVP,
  onClose,
}: CMEEventsModalProps) {
  const [events, setEvents] = useState<CMEEventData[]>(propEvents || []);
  const [filterSpec, setFilterSpec] = useState<string>("all");
  const [loading, setLoading] = useState(false);

  // Fetch real events from API if none passed
  useEffect(() => {
    if (!propEvents || propEvents.length === 0) {
      setLoading(true);
      const token = getStoredToken();
      fetch("/api/v1/hub/cme/events", {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
        .then((res) => (res.ok ? res.json() : []))
        .then((data: CMEEventData[]) => {
          if (Array.isArray(data) && data.length > 0) {
            setEvents(data);
          }
        })
        .finally(() => setLoading(false));
    } else {
      setEvents(propEvents);
    }
  }, [propEvents]);

  // Real-time WebSocket sync for RSVP changes
  useEffect(() => {
    const token = getStoredToken();
    const ws = getSharedRealtimeClient(token);
    if (ws) {
      const unsub = ws.subscribeMessages((type, payload) => {
        if (type === "hub_cme_rsvp_updated" && payload?.event_id) {
          setEvents((prev) =>
            prev.map((e) =>
              e.id === payload.event_id
                ? {
                    ...e,
                    rsvp_count: payload.rsvp_count ?? e.rsvp_count,
                  }
                : e
            )
          );
        }
      });
      return () => {
        unsub();
      };
    }
  }, []);

  const handleToggle = async (eventId: string) => {
    // Optimistic toggle
    setEvents((prev) =>
      prev.map((e) =>
        e.id === eventId
          ? {
              ...e,
              is_attending: !e.is_attending,
              rsvp_count: e.is_attending ? Math.max(0, e.rsvp_count - 1) : e.rsvp_count + 1,
            }
          : e
      )
    );

    if (onToggleRSVP) onToggleRSVP(eventId);

    try {
      const token = getStoredToken();
      const res = await fetch(`/api/v1/hub/cme/events/${eventId}/rsvp`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setEvents((prev) =>
          prev.map((e) =>
            e.id === eventId
              ? { ...e, is_attending: data.is_attending, rsvp_count: data.rsvp_count }
              : e
          )
        );
      }
    } catch {}
  };

  const filtered = events.filter(
    (ev) => filterSpec === "all" || ev.specialty.toLowerCase().includes(filterSpec.toLowerCase())
  );

  const totalCredits = events
    .filter((e) => e.is_attending)
    .reduce((sum, e) => sum + e.cme_credits, 0);

  const downloadICS = (event: CMEEventData) => {
    const icsContent = [
      "BEGIN:VCALENDAR",
      "VERSION:2.0",
      "PRODID:-//DocAssistIQ//Medical Grand Rounds//EN",
      "BEGIN:VEVENT",
      `SUMMARY:${event.title}`,
      `DESCRIPTION:Speaker: ${event.speaker} (${event.speaker_title})\\nAccredited: ${event.cme_credits} AMA PRA Category 1 Credits™`,
      `LOCATION:${event.location}`,
      "STATUS:CONFIRMED",
      "END:VEVENT",
      "END:VCALENDAR",
    ].join("\r\n");

    const blob = new Blob([icsContent], { type: "text/calendar;charset=utf-8" });
    const link = document.createElement("a");
    link.href = window.URL.createObjectURL(blob);
    link.setAttribute("download", `${event.id}-grand-rounds.ics`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="fixed inset-0 z-[120] flex items-center justify-center p-3 sm:p-5 bg-slate-900/60 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="relative w-full max-w-3xl max-h-[90vh] flex flex-col rounded-3xl bg-white border border-slate-200 shadow-2xl overflow-hidden"
      >
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-100 flex items-center justify-between gap-3 bg-white">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl">🎓</span>
              <h2 className="text-lg font-black text-slate-900 tracking-tight">
                Webinars & Medical Lectures (CME)
              </h2>
              <span className="text-[10px] bg-teal-50 text-teal-800 border border-teal-200 px-2 py-0.5 rounded-full font-bold">
                CME Credits
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Attend live lectures and earn continuing medical education credits.
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-600 flex items-center justify-center text-sm font-bold transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* CME Passport Summary Card */}
        <div className="p-4 bg-gradient-to-r from-teal-600 to-emerald-600 text-white flex items-center justify-between shadow-xs">
          <div>
            <p className="text-[10px] font-black uppercase tracking-wider text-teal-100">
              Your Education Credits
            </p>
            <p className="text-sm font-extrabold mt-0.5">
              🎓 {totalCredits.toFixed(1)} CME Credits Saved
            </p>
          </div>
          <span className="text-[11px] bg-white/20 backdrop-blur-md px-3 py-1 rounded-full font-bold">
            2026 Cycle
          </span>
        </div>

        {/* Specialty Filter Tabs */}
        <div className="p-3 border-b border-slate-100 flex items-center gap-1.5 overflow-x-auto no-scrollbar bg-slate-50">
          {["all", "cardiology", "neurology", "pediatrics", "emergency medicine"].map((spec) => (
            <button
              key={spec}
              type="button"
              onClick={() => setFilterSpec(spec)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold capitalize transition-all cursor-pointer whitespace-nowrap ${
                filterSpec === spec
                  ? "bg-teal-600 text-white shadow-xs"
                  : "bg-white text-slate-700 hover:bg-slate-100 border border-slate-200"
              }`}
            >
              {spec === "all" ? "All Specialties" : spec}
            </button>
          ))}
        </div>

        {/* Events List */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 no-scrollbar bg-slate-50/30">
          {filtered.length === 0 ? (
            <div className="text-center py-12 text-slate-400 space-y-1">
              <BookOpen className="w-8 h-8 mx-auto text-slate-300" />
              <p className="text-sm font-bold text-slate-700">No events in this specialty</p>
            </div>
          ) : (
            filtered.map((ev) => (
              <div
                key={ev.id}
                className="p-4 rounded-2xl bg-white border border-slate-200/90 hover:border-teal-300 transition-all shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
              >
                <div className="min-w-0 space-y-1.5 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[10px] font-black uppercase tracking-wider bg-teal-50 text-teal-800 border border-teal-200 px-2 py-0.5 rounded-md">
                      {ev.specialty}
                    </span>
                    <span className="text-[10px] font-extrabold bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded-md flex items-center gap-1">
                      <Award className="w-3 h-3 text-amber-600" />
                      <span>{ev.cme_credits} CME Credits</span>
                    </span>
                  </div>

                  <h4 className="font-extrabold text-sm text-slate-900 leading-snug">
                    {ev.title}
                  </h4>

                  <p className="text-xs text-slate-600">
                    <span className="font-bold text-slate-800">{ev.speaker}</span> • {ev.speaker_title}
                  </p>

                  <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-500 pt-0.5">
                    <span className="flex items-center gap-1 font-medium">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span>{ev.date}</span>
                    </span>
                    <span className="flex items-center gap-1 font-medium">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      <span>{ev.time}</span>
                    </span>
                    <span className="flex items-center gap-1 font-medium">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      <span>{ev.location}</span>
                    </span>
                  </div>
                </div>

                {/* Right Action Buttons */}
                <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto justify-end">
                  <button
                    type="button"
                    onClick={() => downloadICS(ev)}
                    className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 transition cursor-pointer"
                    title="Add to Calendar (.ics)"
                  >
                    <Download className="w-4 h-4" />
                  </button>

                  <button
                    type="button"
                    onClick={() => handleToggle(ev.id)}
                    className={`px-4 py-2 rounded-xl text-xs font-black transition flex items-center gap-1.5 cursor-pointer shadow-xs ${
                      ev.is_attending
                        ? "bg-slate-100 text-slate-700 border border-slate-200 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-200"
                        : "bg-teal-600 hover:bg-teal-700 text-white"
                    }`}
                  >
                    {ev.is_attending ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Attending ✓</span>
                      </>
                    ) : (
                      <>
                        <Plus className="w-3.5 h-3.5" />
                        <span>Attend ({ev.rsvp_count})</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </motion.div>
    </div>
  );
}
