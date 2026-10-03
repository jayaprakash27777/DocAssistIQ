/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Sparkles,
  ShieldCheck,
  FileText,
  Pill,
  FileBadge,
  Activity,
  Users,
  Calendar,
  Clock,
  ArrowRight,
  Stethoscope,
  ExternalLink,
  ChevronRight,
  Hash,
  UserCheck
} from "lucide-react";
import { listConsultations, type ConsultationSummary } from "@/lib/api";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [consultations, setConsultations] = useState<ConsultationSummary[]>([]);
  const [loadingConsultations, setLoadingConsultations] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const router = useRouter();

  // Listen for keyboard shortcut & custom open event
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    };

    const handleCustomOpen = () => setOpen(true);

    document.addEventListener("keydown", down);
    window.addEventListener("open-command-palette", handleCustomOpen);
    return () => {
      document.removeEventListener("keydown", down);
      window.removeEventListener("open-command-palette", handleCustomOpen);
    };
  }, []);

  // Fetch recent consultations on open
  useEffect(() => {
    if (open && consultations.length === 0) {
      setLoadingConsultations(true);
      listConsultations(1, 15)
        .then((res) => {
          if (res.ok && res.data?.items) {
            setConsultations(res.data.items);
          }
        })
        .catch(() => {})
        .finally(() => setLoadingConsultations(false));
    }
  }, [open, consultations.length]);

  const staticCommands = [
    {
      id: "ai-main",
      category: "DocAssist IQ AI",
      name: "Open DocAssist IQ AI",
      detail: "Clinical intelligence chat with @consultation tagging",
      icon: Sparkles,
      color: "text-indigo-600 bg-indigo-50",
      action: () => router.push("/ai"),
    },
    {
      id: "verify-portal",
      category: "Document Integrity",
      name: "Verify Clinical Document",
      detail: "Public digital signature validation portal & SHA-256 check",
      icon: ShieldCheck,
      color: "text-emerald-600 bg-emerald-50",
      action: () => router.push("/verify"),
    },
    {
      id: "ai-rx",
      category: "Document Generation",
      name: "Generate E-Prescription",
      detail: "Create certified electronic medical prescription with digital signature",
      icon: Pill,
      color: "text-emerald-600 bg-emerald-50",
      action: () => router.push("/ai?prompt=Generate%20official%20certified%20electronic%20prescription%20with%20digital%20signature"),
    },
    {
      id: "ai-discharge",
      category: "Document Generation",
      name: "Generate Discharge Summary",
      detail: "Create inpatient / encounter discharge record with digital signature",
      icon: FileText,
      color: "text-indigo-600 bg-indigo-50",
      action: () => router.push("/ai?prompt=Generate%20certified%20discharge%20summary%20with%20digital%20signature"),
    },
    {
      id: "ai-certificate",
      category: "Document Generation",
      name: "Generate Medical Certificate",
      detail: "Official fitness / sickness certification with statutory clinician signature",
      icon: FileBadge,
      color: "text-purple-600 bg-purple-50",
      action: () => router.push("/ai?prompt=Generate%20official%20medical%20certificate%20for%20patient%20with%20digital%20signature"),
    },
    {
      id: "nav-dash",
      category: "Navigation",
      name: "Clinician Dashboard",
      detail: "Real-time clinical metrics & recent encounters",
      icon: Activity,
      color: "text-blue-600 bg-blue-50",
      action: () => router.push("/dashboard"),
    },
    {
      id: "nav-cons",
      category: "Navigation",
      name: "Consultations & Encounters",
      detail: "Complete patient session archive with @tags",
      icon: Stethoscope,
      color: "text-teal-600 bg-teal-50",
      action: () => router.push("/consultations"),
    },
    {
      id: "nav-patients",
      category: "Navigation",
      name: "Longitudinal Patient Records",
      detail: "Patient profiles, chronic conditions & timeline",
      icon: Users,
      color: "text-sky-600 bg-sky-50",
      action: () => router.push("/patients"),
    },
    {
      id: "nav-notes",
      category: "Navigation",
      name: "Clinical Notes & SOAP",
      detail: "Doctor notes, audio transcripts & clinical summaries",
      icon: FileText,
      color: "text-slate-600 bg-slate-100",
      action: () => router.push("/notes"),
    },
  ];

  // Filter static commands
  const filteredCommands = query.trim() === ""
    ? staticCommands
    : staticCommands.filter((c) =>
        c.name.toLowerCase().includes(query.toLowerCase()) ||
        c.category.toLowerCase().includes(query.toLowerCase()) ||
        c.detail.toLowerCase().includes(query.toLowerCase())
      );

  // Filter consultation items matching query
  const matchingEncounters = consultations.filter((c) => {
    if (!query.trim()) return false;
    const q = query.toLowerCase().replace(/^@/, "");
    return (
      c.id.toLowerCase().includes(q) ||
      (c.input_preview && c.input_preview.toLowerCase().includes(q)) ||
      (c.status && c.status.toLowerCase().includes(q))
    );
  }).slice(0, 5);

  const totalItems = filteredCommands.length + matchingEncounters.length;

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, totalItems));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + totalItems) % Math.max(1, totalItems));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (selectedIndex < filteredCommands.length) {
        filteredCommands[selectedIndex]?.action();
        setOpen(false);
      } else {
        const encounter = matchingEncounters[selectedIndex - filteredCommands.length];
        if (encounter) {
          router.push(`/ai?cid=${encounter.id}`);
          setOpen(false);
        }
      }
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setOpen(false)}
            className="fixed inset-0 z-50 bg-slate-900/30 backdrop-blur-xs"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -20 }}
            transition={{ type: "spring", stiffness: 350, damping: 28 }}
            className="fixed inset-x-0 top-[12%] z-50 mx-auto max-w-2xl overflow-hidden rounded-3xl bg-white shadow-2xl border border-slate-200/80 divide-y divide-slate-100"
            onKeyDown={handleKeyDown}
          >
            {/* Search Header */}
            <div className="p-4 flex items-center gap-3 bg-slate-50/50">
              <Search className="w-5 h-5 text-indigo-600 shrink-0" />
              <input
                type="text"
                autoFocus
                className="w-full bg-transparent text-slate-800 placeholder-slate-400 outline-none text-base font-medium"
                placeholder="Search commands, navigate, or type @ to find consultations..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <div className="flex items-center gap-1.5 shrink-0">
                <kbd className="px-2 py-0.5 text-[11px] font-mono bg-white border border-slate-200 rounded-md text-slate-500 shadow-2xs">
                  ↑↓ Navigate
                </kbd>
                <kbd className="px-2 py-0.5 text-[11px] font-mono bg-white border border-slate-200 rounded-md text-slate-500 shadow-2xs">
                  ESC
                </kbd>
              </div>
            </div>

            {/* List */}
            <div className="max-h-[60vh] overflow-y-auto p-2 space-y-1">
              {/* Encounter Match Section if any */}
              {matchingEncounters.length > 0 && (
                <div className="mb-2">
                  <div className="px-3 py-1.5 text-[10px] font-extrabold uppercase tracking-wider text-indigo-600 bg-indigo-50/50 rounded-lg flex items-center justify-between">
                    <span>Matching Clinical Encounters</span>
                    <span>Press Enter to query in DocAssist IQ AI</span>
                  </div>
                  <div className="mt-1 space-y-1">
                    {matchingEncounters.map((c, idx) => {
                      const itemIndex = filteredCommands.length + idx;
                      const isSelected = selectedIndex === itemIndex;
                      return (
                        <div
                          key={c.id}
                          onClick={() => {
                            router.push(`/ai?cid=${c.id}`);
                            setOpen(false);
                          }}
                          className={`px-3 py-2.5 rounded-xl cursor-pointer flex items-center justify-between transition-colors ${
                            isSelected ? "bg-indigo-50 text-indigo-950" : "hover:bg-slate-50 text-slate-700"
                          }`}
                        >
                          <div className="flex items-center gap-2.5 min-w-0">
                            <div className="w-7 h-7 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-mono text-xs font-bold shrink-0">
                              @
                            </div>
                            <div className="min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-xs font-bold text-indigo-700">
                                  @{c.id.substring(0, 8)}
                                </span>
                                <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-slate-100 text-slate-700">
                                  {c.status}
                                </span>
                              </div>
                              <p className="text-[11px] text-slate-500 truncate">
                                {c.input_preview || "Clinical encounter record"}
                              </p>
                            </div>
                          </div>
                          <span className="text-[11px] font-semibold text-indigo-600 shrink-0 flex items-center gap-1">
                            DocAssist IQ AI <ChevronRight className="w-3 h-3" />
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Static Commands */}
              {filteredCommands.length === 0 && matchingEncounters.length === 0 ? (
                <div className="p-8 text-center text-slate-500">
                  <p className="font-semibold text-slate-700 text-sm">No commands or consultations match &quot;{query}&quot;</p>
                  <p className="text-xs text-slate-400 mt-1">Try searching for &quot;AI&quot;, &quot;prescription&quot;, &quot;discharge&quot;, or &quot;verify&quot;</p>
                </div>
              ) : (
                filteredCommands.map((command, idx) => {
                  const isSelected = selectedIndex === idx;
                  const Icon = command.icon;
                  return (
                    <div
                      key={command.id}
                      onClick={() => {
                        command.action();
                        setOpen(false);
                      }}
                      className={`px-3.5 py-3 rounded-2xl cursor-pointer flex items-center justify-between transition-colors ${
                        isSelected ? "bg-indigo-50/90 text-indigo-950" : "hover:bg-slate-50 text-slate-800"
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${command.color}`}>
                          <Icon className="w-4 h-4" />
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-xs sm:text-sm text-slate-900 truncate">
                              {command.name}
                            </span>
                            <span className="text-[10px] uppercase font-bold px-1.5 py-0.2 rounded-md bg-slate-100 text-slate-500">
                              {command.category}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-500 truncate mt-0.5">
                            {command.detail}
                          </p>
                        </div>
                      </div>
                      <ArrowRight className={`w-4 h-4 shrink-0 transition-transform ${isSelected ? "text-indigo-600 translate-x-1" : "text-slate-300"}`} />
                    </div>
                  );
                })
              )}
            </div>

            {/* Footer */}
            <div className="px-4 py-2.5 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
              <span className="flex items-center gap-1.5 font-medium">
                <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
                DocAssist IQ AI Command Center
              </span>
              <span>Press <kbd className="px-1.5 py-0.5 rounded bg-white border border-slate-200 font-mono text-[10px]">Enter</kbd> to execute</span>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
