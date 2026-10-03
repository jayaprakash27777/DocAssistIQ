"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";

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
  events: CMEEventData[];
  onToggleRSVP: (eventId: string) => void;
  onClose: () => void;
  isNightMode?: boolean;
}

export function CMEEventsModal({
  events,
  onToggleRSVP,
  onClose,
  isNightMode = false,
}: CMEEventsModalProps) {
  const [filterSpec, setFilterSpec] = useState<string>("all");

  const fallbackEvents: CMEEventData[] = events?.length
    ? events
    : [
        {
          id: "cme-1",
          title: "International Interventional Cardiology Rounds: Cardiogenic Shock & Left-Ventricular Unloading",
          specialty: "Cardiology",
          date: "Tomorrow, Oct 3, 2026",
          time: "08:00 AM EST • 13:00 UTC",
          speaker: "Prof. Sarah Chen, MD, FACC",
          speaker_title: "Chief of Interventional Cardiology & Structural Heart",
          cme_credits: 2.0,
          location: "Virtual Auditorium / Live Telecast",
          rsvp_count: 342,
          is_attending: true,
          topics: ["Cardiogenic Shock", "Impella vs VA-ECMO", "DAPT Protocols"],
        },
        {
          id: "cme-2",
          title: "Morbidity & Mortality (M&M) Review: Diagnostic Anchoring in Atypical Thoracic Aortic Dissection",
          specialty: "Emergency Medicine",
          date: "Friday, Oct 5, 2026",
          time: "12:00 PM EST • 17:00 UTC",
          speaker: "Dr. Marcus Thorne, MD, FACEP",
          speaker_title: "Director of Emergency Quality Assurance",
          cme_credits: 1.5,
          location: "Hospital Amphitheater & Live Stream",
          rsvp_count: 218,
          is_attending: false,
          topics: ["Aortic Dissection", "Cognitive Biases", "Point-of-Care Ultrasound"],
        },
        {
          id: "cme-3",
          title: "Neuro-Immunology Frontiers: Targeted Monoclonal Therapies in Autoimmune Encephalitis",
          specialty: "Neurology",
          date: "Tuesday, Oct 9, 2026",
          time: "09:00 AM EST • 14:00 UTC",
          speaker: "Dr. David Vance, MD, FAAN",
          speaker_title: "Attending Neurointensivist & Researcher",
          cme_credits: 1.0,
          location: "Academic Medical Center Virtual Hall",
          rsvp_count: 185,
          is_attending: false,
          topics: ["Anti-NMDA", "Rituximab", "Extreme Delta Brush", "CSF Biomarkers"],
        },
        {
          id: "cme-4",
          title: "Pediatric Critical Care Symposium: Refractory Cytokine Storms in Severe Dengue & MIS-C",
          specialty: "Pediatrics",
          date: "Thursday, Oct 11, 2026",
          time: "02:00 PM EST • 19:00 UTC",
          speaker: "Dr. Elena Rostova, MD, PhD",
          speaker_title: "Consultant in Pediatric Infectious Diseases",
          cme_credits: 2.0,
          location: "Global Pediatric Collaborative Hub",
          rsvp_count: 290,
          is_attending: true,
          topics: ["HLH-2004", "IVIG Pulse Therapy", "Pediatric Sepsis"],
        },
      ];

  const filtered = fallbackEvents.filter(
    (ev) => filterSpec === "all" || ev.specialty.toLowerCase() === filterSpec.toLowerCase()
  );

  const totalCredits = fallbackEvents
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

  const bgModal = isNightMode
    ? "bg-slate-900/95 border-slate-800 text-slate-100"
    : "bg-white border-slate-200 text-slate-900";

  const cardBg = isNightMode
    ? "bg-slate-800/80 border-slate-700/80"
    : "bg-slate-50 border-slate-200/90";

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className={`relative w-full max-w-3xl max-h-[90vh] flex flex-col rounded-3xl border shadow-2xl overflow-hidden ${bgModal}`}
      >
        {/* Header */}
        <div className="p-5 border-b border-slate-200/80 dark:border-slate-800 flex items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl">📅</span>
              <h2 className="text-lg font-black tracking-tight">Hospital Grand Rounds & CME</h2>
              <span className="text-[10px] bg-amber-50 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-200 dark:border-amber-800 px-2 py-0.5 rounded-full font-bold">
                Accredited Education
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Peer-reviewed lectures, M&M conferences, and accredited AMA Category 1 credits.
            </p>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-300 flex items-center justify-center text-sm font-bold transition-colors cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* CME Passport Banner */}
        <div className="p-4 bg-gradient-to-r from-teal-600 to-emerald-600 text-white flex items-center justify-between">
          <div>
            <p className="text-[10px] font-black uppercase tracking-wider text-teal-100">
              Personal CME Passport Tracker
            </p>
            <p className="text-sm font-extrabold mt-0.5">
              🎓 {totalCredits.toFixed(1)} AMA PRA Category 1 Credits™ Reserved
            </p>
          </div>
          <span className="text-[11px] bg-white/20 backdrop-blur-md px-3 py-1 rounded-full font-bold">
            Board Cycle 2026 Active
          </span>
        </div>

        {/* Specialty Filter Tabs */}
        <div className="p-3 border-b border-slate-100 dark:border-slate-800 flex items-center gap-1.5 overflow-x-auto custom-scrollbar">
          {["all", "cardiology", "neurology", "pediatrics", "emergency medicine"].map((spec) => (
            <button
              key={spec}
              onClick={() => setFilterSpec(spec)}
              className={`px-3 py-1 rounded-xl text-xs font-bold capitalize transition-all cursor-pointer whitespace-nowrap ${
                filterSpec === spec
                  ? "bg-teal-600 text-white shadow-xs"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
              }`}
            >
              {spec === "all" ? "All Specialties" : spec}
            </button>
          ))}
        </div>

        {/* Events List */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar">
          {filtered.map((event) => (
            <div
              key={event.id}
              className={`p-4 rounded-2xl border transition-all shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${cardBg}`}
            >
              <div className="flex items-start gap-3.5 min-w-0 flex-1">
                {/* Date badge */}
                <div className="w-14 h-14 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 flex flex-col items-center justify-center text-center flex-shrink-0 shadow-xs">
                  <span className="text-[9px] uppercase font-black text-rose-600">OCT</span>
                  <span className="text-lg font-black text-slate-900 dark:text-slate-100 leading-none">
                    {event.date.match(/[0-9]{1,2}/)?.[0] || "15"}
                  </span>
                  <span className="text-[8px] text-slate-400 font-mono">2026</span>
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-teal-50 dark:bg-teal-950 text-teal-800 dark:text-teal-300 border border-teal-200 dark:border-teal-800">
                      🎓 {event.cme_credits} CME Hours
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      🕒 {event.time}
                    </span>
                  </div>

                  <h3 className="font-extrabold text-sm text-slate-900 dark:text-slate-100 mt-1 leading-snug">
                    {event.title}
                  </h3>

                  <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">
                    <strong className="text-slate-800 dark:text-white">{event.speaker}</strong> • {event.speaker_title}
                  </p>

                  <div className="flex items-center gap-2 mt-2 text-[11px] text-slate-400 flex-wrap">
                    <span>📍 {event.location}</span>
                    <span>•</span>
                    <span className="font-mono text-teal-700 dark:text-teal-400 font-bold">
                      👥 {event.rsvp_count} Attending
                    </span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex sm:flex-col items-center sm:items-end gap-2 w-full sm:w-auto justify-end flex-shrink-0">
                <button
                  onClick={() => onToggleRSVP(event.id)}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer border ${
                    event.is_attending
                      ? "bg-emerald-600 text-white border-emerald-600 shadow-xs font-black"
                      : "bg-teal-50 hover:bg-teal-100 dark:bg-teal-950 dark:hover:bg-teal-900 text-teal-800 dark:text-teal-300 border-teal-200 dark:border-teal-800"
                  }`}
                >
                  {event.is_attending ? "Attending ✓" : "RSVP Attending"}
                </button>

                <button
                  onClick={() => downloadICS(event)}
                  className="text-[11px] text-slate-500 hover:text-teal-700 dark:hover:text-teal-400 font-bold flex items-center gap-1 hover:underline transition-colors"
                >
                  <span>📅</span>
                  <span>Add to Calendar</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
