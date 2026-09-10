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
    <div className="glass-panel" style={{ display: "flex", flexDirection: "column", height: "600px", border: "1px solid var(--border-subtle)", borderRadius: "8px", overflow: "hidden" }}>
      {/* Header */}
      <div style={{ padding: "1rem", borderBottom: "1px solid var(--border-subtle)", display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem", background: "var(--surface-raised)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <div style={{ 
            width: "36px", height: "36px", 
            borderRadius: "8px", 
            background: "rgba(16, 185, 129, 0.1)", 
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "var(--success)"
          }}>
            <ShieldAlert size={18} />
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)" }}>Transcript Editor</h3>
            <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
              Compliant workspace for clinical auditing
            </p>
          </div>
        </div>

        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          {/* View Mode Toggle */}
          <div style={{ display: "flex", background: "var(--surface-sunken)", padding: "4px", borderRadius: "8px" }}>
            <button
              onClick={() => setViewMode("raw")}
              style={{
                background: viewMode === "raw" ? "var(--surface-raised)" : "transparent",
                color: viewMode === "raw" ? "var(--text-primary)" : "var(--text-tertiary)",
                border: "none", borderRadius: "4px", padding: "4px 12px", fontSize: "0.75rem", fontWeight: 600, cursor: "pointer", transition: "all 0.2s"
              }}
            >
              Raw ASR
            </button>
            <button
              onClick={() => setViewMode("processed")}
              style={{
                background: viewMode === "processed" ? "var(--surface-raised)" : "transparent",
                color: viewMode === "processed" ? "var(--text-primary)" : "var(--text-tertiary)",
                border: "none", borderRadius: "4px", padding: "4px 12px", fontSize: "0.75rem", fontWeight: 600, cursor: "pointer", transition: "all 0.2s"
              }}
            >
              AI Processed
            </button>
            <button
              onClick={() => setViewMode("final")}
              style={{
                background: viewMode === "final" ? "var(--surface-raised)" : "transparent",
                color: viewMode === "final" ? "var(--text-primary)" : "var(--text-tertiary)",
                border: "none", borderRadius: "4px", padding: "4px 12px", fontSize: "0.75rem", fontWeight: 600, cursor: "pointer", transition: "all 0.2s"
              }}
            >
              Final Output
            </button>
          </div>
          
          {/* Search */}
          <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
            <Search size={14} style={{ position: "absolute", left: "10px", color: "var(--text-tertiary)" }} />
            <input 
              type="text" 
              placeholder="Search transcript..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ 
                padding: "6px 12px 6px 32px", 
                borderRadius: "6px", 
                border: "1px solid var(--border-subtle)", 
                background: "var(--surface-sunken)",
                color: "var(--text-primary)",
                fontSize: "0.8rem",
                width: "200px"
              }}
            />
            {searchQuery && (
              <X 
                size={14} 
                onClick={() => setSearchQuery("")}
                style={{ position: "absolute", right: "10px", color: "var(--text-tertiary)", cursor: "pointer" }} 
              />
            )}
          </div>
        </div>
      </div>

      {/* Transcript Segments List */}
      <div style={{ flex: 1, overflowY: "auto", padding: "1rem", display: "flex", flexDirection: "column", gap: "0.75rem", background: "var(--surface-base)" }}>
        <AnimatePresence>
          {filteredSegments.length === 0 ? (
            <div style={{ textAlign: "center", padding: "3rem", color: "var(--text-tertiary)" }}>
              No segments match your search.
            </div>
          ) : (
            filteredSegments.map((seg, idx) => {
              const isEditing = editingSegment === seg.id;
              
              return (
                <motion.div
                  key={seg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: Math.min(idx * 0.02, 0.5) }}
                  style={{
                    background: isEditing ? "var(--surface-raised)" : "var(--surface-sunken)",
                    border: isEditing ? "1px solid var(--primary)" : "1px solid transparent",
                    borderRadius: "8px",
                    padding: "1rem",
                    transition: "all 0.2s",
                    cursor: (!isEditing && currentStatus !== "finalized" && viewMode === "final") ? "pointer" : "default",
                    position: "relative"
                  }}
                  onClick={() => {
                    if (!isEditing && viewMode === "final") {
                      handleEditClick(seg);
                    }
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                      <div style={{ 
                        fontSize: "0.75rem", 
                        fontWeight: 600, 
                        color: seg.speaker_label?.toLowerCase().includes("doctor") ? "var(--primary)" : "var(--text-secondary)",
                        background: "var(--surface-base)",
                        padding: "2px 8px",
                        borderRadius: "4px"
                      }}>
                        {seg.speaker_label || "Unknown Speaker"}
                      </div>
                      <div style={{ fontSize: "0.7rem", color: "var(--text-tertiary)", fontFamily: "monospace" }}>
                        {new Date(seg.start_time * 1000).toISOString().substr(14, 5)} - {new Date(seg.end_time * 1000).toISOString().substr(14, 5)}
                      </div>
                    </div>

                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      {seg.is_corrected && (
                        <div style={{ 
                          display: "flex", alignItems: "center", gap: "4px",
                          fontSize: "0.65rem", fontWeight: 600, 
                          color: "var(--success)", background: "rgba(16,185,129,0.1)", 
                          padding: "2px 8px", borderRadius: "100px" 
                        }}>
                          <CheckCircle2 size={10} /> Edited
                        </div>
                      )}
                      {viewMode !== "final" && (
                        <div style={{ 
                          display: "flex", alignItems: "center", gap: "4px",
                          fontSize: "0.65rem", fontWeight: 600, 
                          color: "var(--warning)", background: "rgba(245,158,11,0.1)", 
                          padding: "2px 8px", borderRadius: "100px" 
                        }}>
                          <History size={10} /> {viewMode.toUpperCase()}
                        </div>
                      )}
                    </div>
                  </div>

                  {isEditing ? (
                    <div onClick={e => e.stopPropagation()}>
                      <textarea
                        autoFocus
                        value={editText}
                        onChange={(e) => setEditText(e.target.value)}
                        style={{
                          width: "100%",
                          padding: "0.75rem",
                          borderRadius: "6px",
                          border: "1px solid var(--border-strong)",
                          background: "var(--surface-base)",
                          color: "var(--text-primary)",
                          fontSize: "0.9rem",
                          lineHeight: 1.6,
                          minHeight: "80px",
                          resize: "vertical",
                          marginBottom: "0.75rem"
                        }}
                      />
                      <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem" }}>
                        <button 
                          onClick={(e) => { e.stopPropagation(); setEditingSegment(null); }}
                          style={{
                            padding: "6px 12px", borderRadius: "6px", border: "1px solid var(--border-strong)",
                            background: "transparent", color: "var(--text-secondary)", fontSize: "0.8rem", fontWeight: 500,
                            cursor: "pointer", display: "flex", alignItems: "center", gap: "6px"
                          }}
                        >
                          <X size={14} /> Cancel
                        </button>
                        <button 
                          onClick={(e) => { e.stopPropagation(); handleSave(seg.id); }}
                          disabled={isSaving}
                          style={{
                            padding: "6px 12px", borderRadius: "6px", border: "none",
                            background: "var(--primary)", color: "white", fontSize: "0.8rem", fontWeight: 500,
                            cursor: isSaving ? "not-allowed" : "pointer", opacity: isSaving ? 0.7 : 1,
                            display: "flex", alignItems: "center", gap: "6px"
                          }}
                        >
                          <Save size={14} /> {isSaving ? "Saving..." : "Save Correction"}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div style={{ 
                      fontSize: "0.9rem", 
                      lineHeight: 1.6, 
                      color: viewMode === "final" && seg.is_corrected ? "var(--text-primary)" : "var(--text-secondary)",
                      display: "flex",
                      justifyContent: "space-between",
                      gap: "0.5rem"
                    }}>
                      <span>{getDisplayText(seg)}</span>
                      {viewMode === "final" && currentStatus !== "finalized" && (
                        <div style={{ opacity: 0.3, transition: "opacity 0.2s", flexShrink: 0 }} className="hover-target">
                          <Edit3 size={16} />
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
