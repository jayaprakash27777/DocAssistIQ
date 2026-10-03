"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";

export interface CircleData {
  id: string;
  name: string;
  icon: string;
  specialty: string;
  description: string;
  member_count: number;
  weekly_cases_count: number;
  is_joined: boolean;
  tags: string[];
}

interface DoctorCirclesModalProps {
  circles: CircleData[];
  onToggleJoin: (circleId: string) => void;
  onSelectCircleFilter: (circle: CircleData) => void;
  onClose: () => void;
  isNightMode?: boolean;
}

export function DoctorCirclesModal({
  circles,
  onToggleJoin,
  onSelectCircleFilter,
  onClose,
  isNightMode = false,
}: DoctorCirclesModalProps) {
  const [search, setSearch] = useState("");
  const [selectedTab, setSelectedTab] = useState<"all" | "joined">("all");

  const fallbackCircles: CircleData[] = circles?.length
    ? circles
    : [
        {
          id: "cardio-cath",
          name: "Interventional Cardiology & Cath Lab Society",
          icon: "🫀",
          specialty: "Cardiology",
          description:
            "Multidisciplinary forum for acute coronary syndromes, structural valve interventions, and hemodynamic shock escalation.",
          member_count: 1248,
          weekly_cases_count: 19,
          is_joined: true,
          tags: ["PCI", "Shock", "ECG", "Hemodynamics"],
        },
        {
          id: "neuro-stroke",
          name: "Neurocritical Care & Rapid Stroke Response",
          icon: "🧠",
          specialty: "Neurology",
          description:
            "Comprehensive stroke management, neuro-trauma, status epilepticus, and neuro-immunology clinical protocols.",
          member_count: 894,
          weekly_cases_count: 14,
          is_joined: false,
          tags: ["Stroke", "Autoimmune", "EEG", "Neuro-ICU"],
        },
        {
          id: "rare-pediatrics",
          name: "Pediatric Rare Diseases & Genetics Forum",
          icon: "👶",
          specialty: "Pediatrics",
          description:
            "Global consults for undiagnosed pediatric syndromic presentations, metabolic anomalies, and pediatric rheumatology.",
          member_count: 742,
          weekly_cases_count: 11,
          is_joined: false,
          tags: ["Genetics", "Kawasaki", "Metabolic", "Neonatal"],
        },
        {
          id: "tumor-board",
          name: "Multidisciplinary Precision Oncology Tumor Board",
          icon: "🔬",
          specialty: "Oncology",
          description:
            "Next-generation sequencing genomics, immunotherapy resistance patterns, and complex surgical oncology margins.",
          member_count: 650,
          weekly_cases_count: 8,
          is_joined: false,
          tags: ["Genomics", "Immunotherapy", "Biopsy", "Histology"],
        },
        {
          id: "er-resuscitation",
          name: "Emergency Resuscitation & Disaster Triage Network",
          icon: "⚡",
          specialty: "Emergency Medicine",
          description:
            "ACLS / ATLS high-yield protocols, airway management disasters, toxicology antidotes, and mass casualty triage.",
          member_count: 1520,
          weekly_cases_count: 27,
          is_joined: true,
          tags: ["Resuscitation", "Trauma", "Toxicology", "Airway"],
        },
      ];

  const filteredCircles = fallbackCircles.filter((c) => {
    const matchesSearch =
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.specialty.toLowerCase().includes(search.toLowerCase()) ||
      c.description.toLowerCase().includes(search.toLowerCase());
    const matchesTab = selectedTab === "all" || (selectedTab === "joined" && c.is_joined);
    return matchesSearch && matchesTab;
  });

  const bgModal = isNightMode
    ? "bg-slate-900/95 border-slate-800 text-slate-100"
    : "bg-white border-slate-200 text-slate-900";

  const cardBg = isNightMode
    ? "bg-slate-800/80 border-slate-700/80 hover:border-teal-500/50"
    : "bg-slate-50 hover:bg-white border-slate-200/90 hover:border-teal-300";

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
              <span className="text-xl">👥</span>
              <h2 className="text-lg font-black tracking-tight">Clinical Specialty Circles</h2>
              <span className="text-[10px] bg-teal-50 text-teal-800 dark:bg-teal-950 dark:text-teal-300 border border-teal-200 dark:border-teal-800 px-2 py-0.5 rounded-full font-bold">
                Doctor Communities
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Verified multidisciplinary physician boards and clinical interest groups.
            </p>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-300 flex items-center justify-center text-sm font-bold transition-colors cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* Filter & Search Bar */}
        <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs">🔍</span>
            <input
              type="text"
              placeholder="Search circles by specialty, procedures, or condition..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-8 pr-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-teal-500 shadow-xs"
            />
          </div>

          <div className="flex items-center gap-1.5 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl">
            <button
              onClick={() => setSelectedTab("all")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                selectedTab === "all"
                  ? "bg-white dark:bg-slate-700 text-teal-800 dark:text-teal-300 shadow-xs"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              All Circles ({fallbackCircles.length})
            </button>
            <button
              onClick={() => setSelectedTab("joined")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                selectedTab === "joined"
                  ? "bg-white dark:bg-slate-700 text-teal-800 dark:text-teal-300 shadow-xs"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              My Circles ({fallbackCircles.filter((c) => c.is_joined).length})
            </button>
          </div>
        </div>

        {/* Circles Grid */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar">
          {filteredCircles.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <p className="text-sm font-bold">No specialty circles matching &quot;{search}&quot;</p>
              <p className="text-xs mt-1">Try searching for Cardiology, Neurology, or Pediatrics</p>
            </div>
          ) : (
            filteredCircles.map((circle) => (
              <div
                key={circle.id}
                className={`p-4 rounded-2xl border transition-all shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${cardBg}`}
              >
                <div className="flex items-start gap-3.5 min-w-0 flex-1">
                  <div className="w-12 h-12 rounded-2xl bg-teal-50 dark:bg-teal-950/60 border border-teal-200 dark:border-teal-800 flex items-center justify-center text-2xl flex-shrink-0 shadow-xs">
                    {circle.icon}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-extrabold text-sm text-slate-900 dark:text-slate-100">
                        {circle.name}
                      </h3>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-200/60 dark:bg-slate-700 text-slate-700 dark:text-slate-200">
                        {circle.specialty}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed line-clamp-2">
                      {circle.description}
                    </p>

                    {/* Stats & Tags */}
                    <div className="flex items-center gap-3 mt-2.5 flex-wrap">
                      <span className="text-[11px] font-mono font-bold text-slate-600 dark:text-slate-300">
                        👨‍⚕️ {circle.member_count.toLocaleString()} Physicians
                      </span>
                      <span className="text-[11px] font-mono text-teal-700 dark:text-teal-400 font-bold">
                        📊 {circle.weekly_cases_count} cases/wk
                      </span>
                      <div className="flex items-center gap-1">
                        {circle.tags.map((t) => (
                          <span
                            key={t}
                            className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 border border-slate-200/60 dark:border-slate-700"
                          >
                            #{t}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex sm:flex-col items-center sm:items-end gap-2 w-full sm:w-auto justify-end flex-shrink-0">
                  <button
                    onClick={() => onToggleJoin(circle.id)}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer border ${
                      circle.is_joined
                        ? "bg-teal-600 text-white border-teal-600 shadow-xs"
                        : "bg-white dark:bg-slate-800 hover:bg-teal-50 dark:hover:bg-slate-700 text-teal-700 dark:text-teal-300 border-teal-200 dark:border-teal-700"
                    }`}
                  >
                    {circle.is_joined ? "Joined ✓" : "+ Join Circle"}
                  </button>

                  <button
                    onClick={() => {
                      onSelectCircleFilter(circle);
                      onClose();
                    }}
                    className="text-[11px] text-slate-500 hover:text-teal-700 dark:hover:text-teal-400 font-bold hover:underline transition-colors"
                  >
                    Filter Feed ↗
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
