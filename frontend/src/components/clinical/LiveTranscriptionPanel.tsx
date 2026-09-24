/**
 * DocAssistIQ — Live Transcription Panel v4 (Premium UI + Advanced Diarization)
 *
 * Features:
 * - Glassmorphic premium card design with gradient accents
 * - Real-time speaker diarization (Doctor / Patient / Unknown)
 * - Speaker confidence badges with color coding
 * - Speaker stats bar (Doctor % | Patient % | Unknown %)
 * - Force-next-speaker quick buttons during recording
 * - Speaker mode selector: Auto / Doctor Only / Patient Only
 * - Manual role override per segment
 * - Generate clinical note from transcript
 * - Copy & export transcript
 * - Animated segment entrance
 * - Auto-scroll with pause-on-hover
 * - Doctor-asked indicator: "Patient reply expected →"
 */
"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mic, Pause, Square, Loader2, FileText, Copy, Check,
  Trash2, ChevronDown, Stethoscope, User, HelpCircle,
  Activity, Clock, BarChart2, ArrowRight, Zap
} from "lucide-react";
import { useWebSpeechASR, SpeakerRole, TranscriptSegment } from "@/hooks/useWebSpeechASR";
import { getStoredToken } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL?.replace(/\/api\/v1\/?$/, "") ?? "http://localhost:8000";

const fmt = (ms: number) => {
  const s = Math.floor(ms / 1000);
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
};

// Premium speaker color tokens
const SPEAKER_CONFIG = {
  Doctor: {
    gradient: "linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%)",
    border: "#93c5fd",
    label: "#1d4ed8",
    dot: "#3b82f6",
    badge: { bg: "#dbeafe", text: "#1e40af", border: "#bfdbfe" },
    bar: "#3b82f6",
    icon: <Stethoscope className="w-3.5 h-3.5" />,
    emoji: "🩺",
  },
  Patient: {
    gradient: "linear-gradient(135deg, #dcfce7 0%, #f0fdf4 100%)",
    border: "#86efac",
    label: "#15803d",
    dot: "#22c55e",
    badge: { bg: "#dcfce7", text: "#166534", border: "#bbf7d0" },
    bar: "#22c55e",
    icon: <User className="w-3.5 h-3.5" />,
    emoji: "🧑",
  },
  Unknown: {
    gradient: "linear-gradient(135deg, #fef3c7 0%, #fffbeb 100%)",
    border: "#fcd34d",
    label: "#b45309",
    dot: "#f59e0b",
    badge: { bg: "#fef3c7", text: "#92400e", border: "#fde68a" },
    bar: "#f59e0b",
    icon: <HelpCircle className="w-3.5 h-3.5" />,
    emoji: "❓",
  },
} as const;

const confLabel = (c: number) => c >= 0.8 ? "High" : c >= 0.6 ? "Med" : "Low";
const confColor = (c: number) =>
  c >= 0.8 ? { bg: "#d1fae5", text: "#065f46", border: "#a7f3d0" }
  : c >= 0.6 ? { bg: "#fef3c7", text: "#92400e", border: "#fde68a" }
  : { bg: "#fee2e2", text: "#991b1b", border: "#fecaca" };

type SpeakerMode = "auto" | "doctor" | "patient";

interface Props {
  consultationId?: string;
  onTranscriptReady?: (text: string, segments: TranscriptSegment[]) => void;
  onGenerateNote?: (transcriptText: string) => void;
}

export default function LiveTranscriptionPanel({ consultationId, onTranscriptReady, onGenerateNote }: Props) {
  const [asr, controls] = useWebSpeechASR();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [copied, setCopied] = useState(false);
  const [generatingNote, setGeneratingNote] = useState(false);
  const [noteGenStatus, setNoteGenStatus] = useState<string | null>(null);
  const [speakerMode, setSpeakerMode] = useState<SpeakerMode>("auto");
  const [showModeDropdown, setShowModeDropdown] = useState(false);
  const [overrideMap, setOverrideMap] = useState<Record<string, SpeakerRole>>({});

  // Auto-scroll
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [asr.segments, asr.interimText, autoScroll]);

  const handleScroll = useCallback(() => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    setAutoScroll(scrollHeight - scrollTop - clientHeight < 40);
  }, []);

  const handleCopy = useCallback(async () => {
    const text = controls.generateNoteText();
    if (!text) return;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [controls]);

  const handleGenerateNote = useCallback(async () => {
    const text = controls.generateNoteText();
    if (!text) return;
    setGeneratingNote(true);
    setNoteGenStatus("Generating note…");
    try {
      if (onGenerateNote) {
        onGenerateNote(text);
        setNoteGenStatus("✓ Note generated!");
      } else if (consultationId) {
        const res = await fetch(`${API_BASE}/api/v1/consultations/${consultationId}/notes/generate`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${getStoredToken() ?? ""}`,
          },
          body: JSON.stringify({ transcript_text: text }),
        });
        if (res.ok) {
          setNoteGenStatus("✓ Note generated!");
          onTranscriptReady?.(text, asr.segments);
        } else {
          setNoteGenStatus("⚠ Generation failed");
        }
      } else {
        setNoteGenStatus("✓ Ready to generate");
      }
    } catch {
      setNoteGenStatus("⚠ Network error");
    } finally {
      setGeneratingNote(false);
      setTimeout(() => setNoteGenStatus(null), 3000);
    }
  }, [controls, consultationId, onGenerateNote, onTranscriptReady, asr.segments]);

  const overrideSegment = useCallback((id: string, role: SpeakerRole) => {
    setOverrideMap(prev => ({ ...prev, [id]: role }));
  }, []);

  // Speaker stats
  const stats = asr.segments.reduce(
    (acc, seg) => {
      const effective = overrideMap[seg.id] ?? seg.speaker;
      acc[effective] = (acc[effective] ?? 0) + 1;
      return acc;
    },
    {} as Record<SpeakerRole, number>
  );
  const total = asr.segments.length || 1;
  const pct = (r: SpeakerRole) => Math.round(((stats[r] ?? 0) / total) * 100);

  const isActive = asr.isRecording && !asr.isPaused;
  const isEmpty = asr.segments.length === 0 && !asr.interimText;

  // Merge: get effective speaker for a segment
  const effectiveSpeaker = (seg: TranscriptSegment): SpeakerRole =>
    overrideMap[seg.id] ?? seg.speaker;

  // Handle speaker mode changes
  const handleModeChange = (mode: SpeakerMode) => {
    setSpeakerMode(mode);
    setShowModeDropdown(false);
    if (mode === "doctor") controls.setSpeaker("Doctor");
    else if (mode === "patient") controls.setSpeaker("Patient");
  };

  return (
    <div
      className="flex flex-col rounded-3xl overflow-hidden glass-panel-4k gpu-accelerated shadow-[0_20px_50px_rgba(0,0,0,0.08),inset_0_1px_0_rgba(255,255,255,0.9)] border border-slate-200/90"
    >
      {/* ── Header ────────────────────────────────────────────── */}
      <div
        className="flex items-center justify-between px-5 py-3.5 border-b border-slate-200/80 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white shadow-md relative overflow-hidden"
      >
        <div className="absolute inset-0 bg-gradient-to-r from-teal-500/10 via-indigo-500/10 to-purple-500/10 pointer-events-none" />
        
        {/* Left: Title + recording status */}
        <div className="flex items-center gap-3 relative z-10">
          <div
            className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-teal-400 to-indigo-500 shadow-md shadow-teal-500/30 ring-1 ring-white/30"
          >
            <Mic className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <span className="text-sm font-bold text-white tracking-tight">Live Clinical Transcription</span>
              {isActive && (
                <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-rose-500/20 border border-rose-400/40 text-rose-300">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500" />
                  </span>
                  <span className="text-[10px] font-black uppercase tracking-wider">LIVE REC</span>
                </span>
              )}
            </div>
            <div className="text-[11px] text-slate-300 mt-0.5 flex items-center gap-2">
              <Clock className="w-3 h-3 text-teal-400" />
              <span className="font-mono font-medium">{fmt(asr.elapsedMs)}</span>
              {asr.segments.length > 0 && (
                <span className="text-slate-500">·</span>
              )}
              {asr.segments.length > 0 && (
                <span className="font-medium text-slate-300">{asr.segments.length} segment{asr.segments.length !== 1 ? "s" : ""}</span>
              )}
            </div>
          </div>
        </div>

        {/* Right: Controls */}
        <div className="flex items-center gap-2 relative z-10">
          {/* Speaker Mode selector */}
          <div className="relative">
            <button
              onClick={() => setShowModeDropdown(v => !v)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all bg-white/10 hover:bg-white/20 border border-white/20 text-white shadow-sm backdrop-blur-md"
            >
              {speakerMode === "auto" ? "🤖 Auto" : speakerMode === "doctor" ? "🩺 Doctor" : "🧑 Patient"}
              <ChevronDown className="w-3 h-3 text-slate-300" />
            </button>
            <AnimatePresence>
              {showModeDropdown && (
                <motion.div
                  initial={{ opacity: 0, y: -4, scale: 0.96 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -4, scale: 0.96 }}
                  transition={{ duration: 0.12 }}
                  className="absolute right-0 top-full mt-1 z-50 rounded-xl overflow-hidden"
                  style={{
                    background: "#fff",
                    border: "1px solid rgba(0,0,0,0.1)",
                    boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
                    minWidth: 140,
                  }}
                >
                  {(["auto", "doctor", "patient"] as SpeakerMode[]).map(m => (
                    <button
                      key={m}
                      onClick={() => handleModeChange(m)}
                      className="w-full text-left px-3 py-2 text-xs font-medium hover:bg-slate-50 transition-colors flex items-center gap-2"
                      style={{ color: speakerMode === m ? "#3b82f6" : "#374151" }}
                    >
                      {m === "auto" ? "🤖 Auto-Detect" : m === "doctor" ? "🩺 Doctor Only" : "🧑 Patient Only"}
                      {speakerMode === m && <span className="ml-auto">✓</span>}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Copy */}
          {asr.segments.length > 0 && (
            <button
              onClick={handleCopy}
              className="p-1.5 rounded-xl transition-all hover:scale-105 active:scale-95"
              title="Copy transcript"
              style={{
                background: copied ? "rgba(16,185,129,0.2)" : "rgba(255,255,255,0.15)",
                border: copied ? "1px solid rgba(16,185,129,0.4)" : "1px solid rgba(255,255,255,0.2)",
                color: copied ? "#34d399" : "#e2e8f0",
              }}
            >
              {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          )}

          {/* Clear */}
          {asr.segments.length > 0 && (
            <button
              onClick={controls.clearTranscript}
              className="p-1.5 rounded-xl transition-all hover:scale-105 active:scale-95 hover:bg-rose-500/20"
              title="Clear transcript"
              style={{ background: "rgba(255,255,255,0.15)", border: "1px solid rgba(255,255,255,0.2)", color: "#cbd5e1" }}
            >
              <Trash2 className="w-3.5 h-3.5 hover:text-rose-400" />
            </button>
          )}
        </div>
      </div>

      {/* ── Speaker Stats Bar ──────────────────────────────────── */}
      {asr.segments.length > 0 && (
        <div className="px-5 py-2.5 flex items-center gap-3 bg-slate-50/90 border-b border-slate-200/80">
          <BarChart2 className="w-3.5 h-3.5 text-slate-500 shrink-0" />
          <div className="flex-1 flex h-2 rounded-full overflow-hidden gap-0.5 bg-slate-200/80 p-0.5 shadow-inner">
            {(["Doctor", "Patient", "Unknown"] as SpeakerRole[]).map(role => (
              <motion.div
                key={role}
                initial={{ width: 0 }}
                animate={{ width: `${pct(role)}%` }}
                transition={{ duration: 0.4, ease: "easeOut" }}
                className="rounded-full shadow-sm"
                style={{ background: SPEAKER_CONFIG[role].bar }}
                title={`${role}: ${pct(role)}%`}
              />
            ))}
          </div>
          <div className="flex items-center gap-3 text-[11px] font-semibold">
            {(["Doctor", "Patient", "Unknown"] as SpeakerRole[]).map(role => (
              pct(role) > 0 ? (
                <span key={role} className="flex items-center gap-1.5" style={{ color: SPEAKER_CONFIG[role].label }}>
                  <span className="w-2 h-2 rounded-full ring-1 ring-black/10" style={{ background: SPEAKER_CONFIG[role].bar }} />
                  {role}: {pct(role)}%
                </span>
              ) : null
            ))}
          </div>
        </div>
      )}

      {/* ── Force Next Speaker (during recording) ─────────────── */}
      {asr.isRecording && (
        <div
          className="flex items-center gap-2.5 px-5 py-2 bg-gradient-to-r from-slate-50 via-teal-50/40 to-slate-50 border-b border-slate-200/70"
        >
          <span className="text-[11px] text-slate-600 font-bold uppercase tracking-wider shrink-0">Next speaker:</span>
          {(["Doctor", "Patient"] as SpeakerRole[]).map(role => (
            <button
              key={role}
              onClick={() => controls.forceNextSpeaker(role)}
              className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold transition-all shadow-sm hover:scale-102 active:scale-98"
              style={{
                background: SPEAKER_CONFIG[role].badge.bg,
                border: `1px solid ${SPEAKER_CONFIG[role].badge.border}`,
                color: SPEAKER_CONFIG[role].badge.text,
              }}
              onMouseEnter={e => e.currentTarget.style.filter = "brightness(0.95)"}
              onMouseLeave={e => e.currentTarget.style.filter = ""}
            >
              {SPEAKER_CONFIG[role].emoji} {role}
            </button>
          ))}
          {asr.lastDoctorQuestion && (
            <span
              className="ml-auto flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-sm"
            >
              <ArrowRight className="w-3 h-3 text-emerald-600" />
              Patient reply expected
            </span>
          )}
        </div>
      )}

      {/* ── Transcript scroll area ─────────────────────────────── */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-3 space-y-2"
        style={{ minHeight: 220, maxHeight: 340 }}
      >
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center h-48 text-center">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
              style={{ background: "linear-gradient(135deg, #eff6ff 0%, #f5f3ff 100%)" }}
            >
              <Mic className="w-7 h-7 text-blue-400" />
            </div>
            <p className="text-sm font-medium text-slate-600">Ready to transcribe</p>
            <p className="text-xs text-slate-400 mt-1.5 max-w-[220px] leading-relaxed">
              Press the microphone button below to start. Speech will be automatically classified as Doctor or Patient.
            </p>
          </div>
        ) : (
          <>
            <AnimatePresence initial={false}>
              {asr.segments.map((seg) => {
                const role = effectiveSpeaker(seg);
                const cfg = SPEAKER_CONFIG[role];
                const cc = confColor(seg.confidence);
                return (
                  <motion.div
                    key={seg.id}
                    initial={{ opacity: 0, x: -12, scale: 0.98 }}
                    animate={{ opacity: 1, x: 0, scale: 1 }}
                    transition={{ type: "spring", stiffness: 400, damping: 28 }}
                    className="flex gap-2.5 group"
                  >
                    {/* Speaker dot */}
                    <div className="flex flex-col items-center pt-1 shrink-0">
                      <div
                        className="w-2 h-2 rounded-full mt-1"
                        style={{ background: cfg.bar }}
                      />
                    </div>

                    {/* Bubble */}
                    <div
                      className="flex-1 rounded-xl px-3 py-2.5 min-w-0"
                      style={{
                        background: cfg.gradient,
                        border: `1px solid ${cfg.border}`,
                      }}
                    >
                      {/* Bubble header */}
                      <div className="flex items-center gap-2 mb-1.5">
                        <span
                          className="flex items-center gap-1 text-[11px] font-bold"
                          style={{ color: cfg.label }}
                        >
                          {cfg.icon} {role}
                        </span>

                        {/* Confidence badge */}
                        <span
                          className="text-[10px] font-medium px-1.5 py-0.5 rounded-full border"
                          style={{ background: cc.bg, color: cc.text, borderColor: cc.border }}
                        >
                          {confLabel(seg.confidence)}
                        </span>

                        {/* Time */}
                        <span className="text-[10px] text-slate-400 ml-auto">
                          {new Date(seg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                        </span>

                        {/* Manual override buttons (appear on hover) */}
                        <div className="hidden group-hover:flex items-center gap-1 ml-1">
                          {(["Doctor", "Patient", "Unknown"] as SpeakerRole[]).filter(r => r !== role).map(r => (
                            <button
                              key={r}
                              onClick={() => overrideSegment(seg.id, r)}
                              className="text-[9px] px-1.5 py-0.5 rounded-full border font-semibold transition-all"
                              style={{
                                background: SPEAKER_CONFIG[r].badge.bg,
                                borderColor: SPEAKER_CONFIG[r].badge.border,
                                color: SPEAKER_CONFIG[r].badge.text,
                              }}
                              title={`Reassign to ${r}`}
                            >
                              {SPEAKER_CONFIG[r].emoji}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Text */}
                      <p
                        className="text-sm leading-relaxed text-slate-800"
                        style={{ opacity: seg.confidence < 0.5 ? 0.7 : 1 }}
                      >
                        {seg.text}
                      </p>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>

            {/* Interim text */}
            {asr.interimText && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex gap-2.5"
              >
                <div className="w-2 shrink-0 pt-2">
                  <span className="block w-2 h-2 rounded-full bg-slate-300 animate-pulse" />
                </div>
                <div
                  className="flex-1 rounded-xl px-3 py-2.5"
                  style={{ background: "#f8fafc", border: "1px dashed #cbd5e1" }}
                >
                  <span className="text-[11px] text-slate-400 font-medium">Listening…</span>
                  <p className="text-sm text-slate-500 mt-1 italic">{asr.interimText}</p>
                </div>
              </motion.div>
            )}
          </>
        )}
      </div>

      {/* ── Controls footer ────────────────────────────────────── */}
      <div
        className="px-5 py-3.5 flex items-center justify-between gap-3 bg-gradient-to-r from-slate-50 via-indigo-50/20 to-slate-50 border-t border-slate-200/80 shadow-[inset_0_1px_0_rgba(255,255,255,0.9)]"
      >
        {/* Not supported warning */}
        {!asr.isSupported && (
          <p className="text-xs text-amber-700 font-semibold flex items-center gap-1.5 bg-amber-50 px-3 py-1.5 rounded-xl border border-amber-200">
            <Activity className="w-3.5 h-3.5 text-amber-600" />
            Use Chrome or Edge for live transcription
          </p>
        )}

        {asr.isSupported && (
          <div className="flex items-center gap-2.5">
            {/* Start / Pause / Resume */}
            {!asr.isRecording ? (
              <motion.button
                whileTap={{ scale: 0.96 }}
                whileHover={{ scale: 1.02, y: -1 }}
                onClick={controls.start}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold text-white shadow-lg transition-all"
                style={{
                  background: "linear-gradient(135deg, #0d9488 0%, #0284c7 100%)",
                  boxShadow: "0 4px 14px rgba(13,148,136,0.35), inset 0 1px 0 rgba(255,255,255,0.3)",
                }}
              >
                <Mic className="w-4 h-4" />
                Start Recording
              </motion.button>
            ) : asr.isPaused ? (
              <motion.button
                whileTap={{ scale: 0.96 }}
                whileHover={{ scale: 1.02, y: -1 }}
                onClick={controls.resume}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold text-white shadow-lg"
                style={{
                  background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                  boxShadow: "0 4px 12px rgba(16,185,129,0.35), inset 0 1px 0 rgba(255,255,255,0.3)",
                }}
              >
                <Mic className="w-4 h-4" />
                Resume
              </motion.button>
            ) : (
              <motion.button
                whileTap={{ scale: 0.96 }}
                whileHover={{ scale: 1.02, y: -1 }}
                onClick={controls.pause}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold text-white shadow-md"
                style={{
                  background: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
                  boxShadow: "0 4px 12px rgba(245,158,11,0.35), inset 0 1px 0 rgba(255,255,255,0.3)",
                }}
              >
                <Pause className="w-4 h-4" />
                Pause
              </motion.button>
            )}

            {/* Stop */}
            {asr.isRecording && (
              <motion.button
                whileTap={{ scale: 0.96 }}
                whileHover={{ scale: 1.02, y: -1 }}
                onClick={controls.stop}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold text-white shadow-md"
                style={{
                  background: "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)",
                  boxShadow: "0 4px 12px rgba(239,68,68,0.35), inset 0 1px 0 rgba(255,255,255,0.3)",
                }}
              >
                <Square className="w-3.5 h-3.5" />
                Stop
              </motion.button>
            )}
          </div>
        )}

        {/* Generate note button */}
        {asr.segments.length > 0 && (
          <motion.button
            whileTap={{ scale: 0.97 }}
            whileHover={{ scale: 1.02, y: -1 }}
            onClick={handleGenerateNote}
            disabled={generatingNote}
            className="ml-auto flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold text-white transition-all disabled:opacity-70 shadow-lg"
            style={{
              background: generatingNote
                ? "linear-gradient(135deg, #94a3b8 0%, #64748b 100%)"
                : "linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%)",
              boxShadow: generatingNote ? "none" : "0 6px 18px rgba(124,58,237,0.35), inset 0 1px 0 rgba(255,255,255,0.3)",
            }}
          >
            {generatingNote ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Zap className="w-4 h-4" />
            )}
            {noteGenStatus ?? "Generate Note"}
          </motion.button>
        )}
      </div>
    </div>
  );
}
