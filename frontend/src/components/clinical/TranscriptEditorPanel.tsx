/* eslint-disable @typescript-eslint/no-unused-vars */
"use client";

import React, { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Edit3, CheckCircle2, History, X, Save, ShieldAlert } from "lucide-react";
import type { TranscriptResponse, TranscriptSegmentResponse } from "@/lib/api";

interface TranscriptEditorPanelProps {
  transcript: TranscriptResponse;
  currentStatus: string;
  onSaveSegment: (segmentId: string, correctedText: string) => Promise<void>;
}

type ViewMode = "final" | "raw" | "processed";

export default function TranscriptEditorPanel({ 
  transcript, 
  currentStatus, 
  onSaveSegment 
}: TranscriptEditorPanelProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("final");
  const [searchQuery, setSearchQuery] = useState("");
  const [editingSegment, setEditingSegment] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  // Filter segments based on search
  const filteredSegments = useMemo(() => {
    if (!searchQuery) return transcript.segments;
    const lowerQuery = searchQuery.toLowerCase();
    return transcript.segments.filter(seg => 
      (seg.raw_text?.toLowerCase().includes(lowerQuery)) ||
      (seg.processed_text?.toLowerCase().includes(lowerQuery)) ||
      (seg.clinician_corrected_text?.toLowerCase().includes(lowerQuery)) ||
      (seg.speaker_label?.toLowerCase().includes(lowerQuery))
    );
  }, [transcript.segments, searchQuery]);

  const handleEditClick = (seg: TranscriptSegmentResponse) => {
    if (currentStatus === "finalized") return;
    setEditingSegment(seg.id);
    setEditText(seg.clinician_corrected_text || seg.processed_text || seg.raw_text);
  };

  const handleSave = async (segId: string) => {
    if (!editText.trim()) return;
    setIsSaving(true);
    try {
      await onSaveSegment(segId, editText.trim());
      setEditingSegment(null);
    } catch (err) {
      console.error("Failed to save segment", err);
    } finally {
      setIsSaving(false);
    }
  };

  // Helper to render the text based on the view mode
  const getDisplayText = (seg: TranscriptSegmentResponse) => {
    switch (viewMode) {
      case "raw": return seg.raw_text;
      case "processed": return seg.processed_text || seg.raw_text;
      case "final":
      default:
        return seg.clinician_corrected_text || seg.processed_text || seg.raw_text;
    }
  };

  return (
    <div className="glass-panel-4k gpu-accelerated flex flex-col h-[600px] rounded-3xl border border-slate-200/90 overflow-hidden shadow-[0_20px_50px_rgba(0,0,0,0.08),inset_0_1px_0_rgba(255,255,255,0.9)] bg-white/80 backdrop-blur-2xl">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-200/80 flex flex-wrap justify-between items-center gap-4 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white shadow-md relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-teal-500/10 via-indigo-500/10 to-purple-500/10 pointer-events-none" />
        
        <div className="flex items-center gap-3 relative z-10">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center text-white shadow-lg shadow-emerald-500/30 ring-1 ring-white/30">
            <ShieldAlert size={20} />
          </div>
          <div>
            <h3 className="m-0 text-base font-bold text-white tracking-tight flex items-center gap-2">
              Clinical Transcript Editor
              <span className="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                Audit Ready
              </span>
            </h3>
            <p className="m-0 text-xs text-slate-300">
              Compliant workspace for clinical auditing & forensic review
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-3 items-center relative z-10">
          {/* View Mode Toggle */}
          <div className="flex bg-white/10 p-1 rounded-xl border border-white/15 backdrop-blur-md">
            {(["raw", "processed", "final"] as ViewMode[]).map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  viewMode === mode
                    ? "bg-white text-slate-900 shadow-md scale-102"
                    : "text-slate-300 hover:text-white"
                }`}
              >
                {mode === "raw" ? "Raw ASR" : mode === "processed" ? "AI Processed" : "Final Output"}
              </button>
            ))}
          </div>
          
          {/* Search */}
          <div className="relative flex items-center">
            <Search size={14} className="absolute left-3 text-slate-400 pointer-events-none" />
            <input 
              type="text" 
              placeholder="Search transcript..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-8 py-1.5 rounded-xl border border-white/20 bg-white/10 text-white placeholder-slate-400 text-xs w-48 focus:outline-none focus:ring-2 focus:ring-teal-400/50 backdrop-blur-md transition-all shadow-inner"
            />
            {searchQuery && (
              <X 
                size={14} 
                onClick={() => setSearchQuery("")}
                className="absolute right-2.5 text-slate-400 hover:text-white cursor-pointer transition-colors" 
              />
            )}
          </div>
        </div>
      </div>

      {/* Transcript Segments List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50/60">
        <AnimatePresence>
          {filteredSegments.length === 0 ? (
            <div className="text-center py-16 text-slate-400 text-sm font-medium">
              No transcript segments match your search query.
            </div>
          ) : (
            filteredSegments.map((seg, idx) => {
              const isEditing = editingSegment === seg.id;
              const isDoctor = seg.speaker_label?.toLowerCase().includes("doctor");
              
              return (
                <motion.div
                  key={seg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: Math.min(idx * 0.02, 0.5) }}
                  className={`p-4 rounded-2xl transition-all border ${
                    isEditing 
                      ? "bg-white border-indigo-400 shadow-lg ring-2 ring-indigo-500/20" 
                      : "bg-white/90 hover:bg-white border-slate-200/80 hover:border-slate-300 shadow-sm hover:shadow-md"
                  } ${(!isEditing && currentStatus !== "finalized" && viewMode === "final") ? "cursor-pointer" : "cursor-default"}`}
                  onClick={() => {
                    if (!isEditing && viewMode === "final") {
                      handleEditClick(seg);
                    }
                  }}
                >
                  <div className="flex justify-between items-start mb-2.5">
                    <div className="flex items-center gap-2.5">
                      <span className={`text-xs font-bold px-2.5 py-1 rounded-lg flex items-center gap-1.5 border shadow-sm ${
                        isDoctor 
                          ? "bg-indigo-50 text-indigo-700 border-indigo-200" 
                          : "bg-emerald-50 text-emerald-700 border-emerald-200"
                      }`}>
                        {isDoctor ? "🩺" : "🧑"} {seg.speaker_label || "Unknown Speaker"}
                      </span>
                      <span className="text-[11px] text-slate-400 font-mono">
                        {new Date(seg.start_time * 1000).toISOString().substr(14, 5)} - {new Date(seg.end_time * 1000).toISOString().substr(14, 5)}
                      </span>
                    </div>

                    <div className="flex gap-1.5 items-center">
                      {seg.is_corrected && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full shadow-sm">
                          <CheckCircle2 size={10} /> Edited
                        </span>
                      )}
                      {viewMode !== "final" && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full shadow-sm">
                          <History size={10} /> {viewMode.toUpperCase()}
                        </span>
                      )}
                    </div>
                  </div>

                  {isEditing ? (
                    <div onClick={e => e.stopPropagation()} className="mt-2 space-y-3">
                      <textarea
                        autoFocus
                        value={editText}
                        onChange={(e) => setEditText(e.target.value)}
                        className="w-full p-3 rounded-xl border border-indigo-300 bg-slate-50 text-slate-900 text-sm leading-relaxed min-h-[90px] focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/30 transition-all font-sans resize-y shadow-inner"
                      />
                      <div className="flex justify-end gap-2">
                        <button 
                          onClick={(e) => { e.stopPropagation(); setEditingSegment(null); }}
                          className="px-3.5 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 text-xs font-bold transition-all shadow-sm flex items-center gap-1.5"
                        >
                          <X size={14} /> Cancel
                        </button>
                        <button 
                          onClick={(e) => { e.stopPropagation(); handleSave(seg.id); }}
                          disabled={isSaving}
                          className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-teal-600 text-white text-xs font-bold hover:brightness-110 disabled:opacity-50 transition-all shadow-md flex items-center gap-1.5"
                          style={{ boxShadow: "0 4px 12px rgba(79,70,229,0.3), inset 0 1px 0 rgba(255,255,255,0.25)" }}
                        >
                          <Save size={14} /> {isSaving ? "Saving..." : "Save Correction"}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="text-sm leading-relaxed text-slate-800 flex justify-between gap-3 font-normal">
                      <span>{getDisplayText(seg)}</span>
                      {viewMode === "final" && currentStatus !== "finalized" && (
                        <div className="opacity-40 hover:opacity-100 transition-opacity shrink-0 text-indigo-600" title="Click to edit">
                          <Edit3 size={15} />
                        </div>
                      )}
                    </div>
                  )}
                </motion.div>
              );
            })
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
