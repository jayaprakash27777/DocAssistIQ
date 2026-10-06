"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { getStoredToken } from "@/lib/api";
import { getSharedRealtimeClient } from "@/lib/ws";
import { Users, Search, Check, Plus, Filter, Sparkles, X, ShieldCheck } from "lucide-react";

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
  circles?: CircleData[];
  onToggleJoin?: (circleId: string) => void;
  onSelectCircleFilter: (circle: CircleData) => void;
  onClose: () => void;
}

export function DoctorCirclesModal({
  circles: propCircles,
  onToggleJoin,
  onSelectCircleFilter,
  onClose,
}: DoctorCirclesModalProps) {
  const [circles, setCircles] = useState<CircleData[]>(propCircles || []);
  const [search, setSearch] = useState("");
  const [selectedTab, setSelectedTab] = useState<"all" | "joined">("all");
  const [loading, setLoading] = useState(false);

  // Fetch real circles from backend if none passed
  useEffect(() => {
    if (!propCircles || propCircles.length === 0) {
      setLoading(true);
      const token = getStoredToken();
      fetch("/api/v1/hub/circles", {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
        .then((res) => (res.ok ? res.json() : []))
        .then((data: CircleData[]) => {
          if (Array.isArray(data) && data.length > 0) {
            setCircles(data);
          }
        })
        .finally(() => setLoading(false));
    } else {
      setCircles(propCircles);
    }
  }, [propCircles]);

  // Real-time WebSocket sync for circle membership changes
  useEffect(() => {
    const token = getStoredToken();
    const ws = getSharedRealtimeClient(token);
    if (ws) {
      const unsub = ws.subscribeMessages((type, payload) => {
        if (type === "hub_circle_membership" && payload?.circle_id) {
          setCircles((prev) =>
            prev.map((c) =>
              c.id === payload.circle_id
                ? {
                    ...c,
                    member_count: payload.member_count ?? c.member_count,
                  }
                : c
            )
          );
        }
      });
      return () => {
        unsub();
      };
    }
  }, []);

  const handleToggle = async (circleId: string) => {
    // Optimistic toggle
    setCircles((prev) =>
      prev.map((c) =>
        c.id === circleId
          ? {
              ...c,
              is_joined: !c.is_joined,
              member_count: c.is_joined ? Math.max(0, c.member_count - 1) : c.member_count + 1,
            }
          : c
      )
    );

    if (onToggleJoin) onToggleJoin(circleId);

    try {
      const token = getStoredToken();
      const res = await fetch(`/api/v1/hub/circles/${circleId}/join`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setCircles((prev) =>
          prev.map((c) =>
            c.id === circleId
              ? { ...c, is_joined: data.is_joined, member_count: data.member_count }
              : c
          )
        );
      }
    } catch {}
  };

  const filteredCircles = circles.filter((c) => {
    const matchesSearch =
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.specialty.toLowerCase().includes(search.toLowerCase()) ||
      c.description.toLowerCase().includes(search.toLowerCase());
    const matchesTab = selectedTab === "all" || (selectedTab === "joined" && c.is_joined);
    return matchesSearch && matchesTab;
  });

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
              <span className="text-xl">👥</span>
              <h2 className="text-lg font-black text-slate-900 tracking-tight">
                Specialty Doctor Groups
              </h2>
              <span className="text-[10px] bg-teal-50 text-teal-800 border border-teal-200 px-2 py-0.5 rounded-full font-bold">
                Doctor Groups
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Join medical groups to discuss cases and share updates with colleagues.
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

        {/* Filter & Search Bar */}
        <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row gap-3 bg-slate-50/50">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search groups by specialty or topic..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 bg-white text-xs text-slate-900 outline-none focus:border-teal-600 shadow-xs transition"
            />
          </div>

          <div className="flex items-center gap-1.5 p-1 bg-slate-200/60 rounded-xl">
            <button
              type="button"
              onClick={() => setSelectedTab("all")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                selectedTab === "all"
                  ? "bg-white text-teal-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              All Groups ({circles.length})
            </button>
            <button
              type="button"
              onClick={() => setSelectedTab("joined")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                selectedTab === "joined"
                  ? "bg-white text-teal-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              My Groups ({circles.filter((c) => c.is_joined).length})
            </button>
          </div>
        </div>

        {/* Circles Grid */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 no-scrollbar bg-slate-50/30">
          {filteredCircles.length === 0 ? (
            <div className="text-center py-14 text-slate-400 space-y-2">
              <Users className="w-8 h-8 mx-auto text-slate-300" />
              <p className="text-sm font-bold text-slate-700">No doctor groups match &quot;{search}&quot;</p>
              <p className="text-xs text-slate-400">Try searching for Cardiology, Neurology, or Emergency Medicine</p>
            </div>
          ) : (
            filteredCircles.map((circle) => (
              <div
                key={circle.id}
                className="p-4 rounded-2xl bg-white border border-slate-200/90 hover:border-teal-300 transition-all shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
              >
                <div className="flex items-start gap-3.5 min-w-0 flex-1">
                  <div className="w-12 h-12 rounded-2xl bg-teal-50 border border-teal-200 flex items-center justify-center text-2xl shrink-0 shadow-xs">
                    {circle.icon}
                  </div>

                  <div className="min-w-0 space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="font-extrabold text-sm text-slate-900 truncate">
                        {circle.name}
                      </h4>
                      <span className="text-[10px] bg-slate-100 text-slate-700 font-bold px-2 py-0.5 rounded-md">
                        {circle.specialty}
                      </span>
                      {circle.is_joined && (
                        <span className="text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold px-2 py-0.5 rounded-md flex items-center gap-1">
                          <Check className="w-3 h-3 text-emerald-600" />
                          <span>Member</span>
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-slate-600 leading-snug line-clamp-2">
                      {circle.description}
                    </p>

                    <div className="flex items-center gap-3 text-[11px] text-slate-500 pt-1">
                      <span className="font-bold flex items-center gap-1 text-slate-700">
                        <Users className="w-3.5 h-3.5 text-slate-400" />
                        <span>{circle.member_count} {circle.member_count === 1 ? "doctor" : "doctors"}</span>
                      </span>
                      <span>•</span>
                      <span className="text-teal-700 font-medium">
                        {circle.weekly_cases_count} cases this week
                      </span>
                    </div>
                  </div>
                </div>

                {/* Right Action Buttons */}
                <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto justify-end">
                  {/* Filter Timeline feed by this circle */}
                  <button
                    type="button"
                    onClick={() => {
                      onSelectCircleFilter(circle);
                      onClose();
                    }}
                    className="px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shadow-xs"
                    title="View only this group's cases"
                  >
                    <Filter className="w-3.5 h-3.5 text-slate-500" />
                    <span>View Cases</span>
                  </button>

                  {/* Join / Leave toggle */}
                  <button
                    type="button"
                    onClick={() => handleToggle(circle.id)}
                    className={`px-4 py-2 rounded-xl text-xs font-black transition flex items-center gap-1.5 cursor-pointer shadow-xs ${
                      circle.is_joined
                        ? "bg-slate-100 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-200 border border-slate-200 text-slate-700"
                        : "bg-teal-600 hover:bg-teal-700 text-white"
                    }`}
                  >
                    {circle.is_joined ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Joined ✓</span>
                      </>
                    ) : (
                      <>
                        <Plus className="w-3.5 h-3.5" />
                        <span>+ Join Group</span>
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
