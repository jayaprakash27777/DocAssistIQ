/**
 * DocAssistIQ — Live Transcription Panel v5 (Executive UI + Advanced Diarization)
 *
 * Features:
 * - Full-width clinical console design with responsive spacious height
 * - Real-time speaker diarization (Doctor / Patient / Unknown)
 * - Speaker confidence badges with color coding
 * - Speaker stats bar (Doctor % | Patient % | Unknown %)
 * - Force-next-speaker quick buttons during recording
 * - Speaker mode selector: Auto / Doctor Only / Patient Only
 * - Manual role override per segment
 * - Generate clinical note from transcript
 * - Copy & export transcript
 * - Animated segment entrance & live audio visualization waveform
 * - Auto-scroll with pause-on-hover
 * - Synchronized consultation recording triggers
 * - Doctor-asked indicator: "Patient reply expected →"
 */
"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mic, Pause, Square, Loader2, FileText, Copy, Check,
  Trash2, ChevronDown, Stethoscope, User, HelpCircle,
  Activity, Clock, BarChart2, ArrowRight, Zap, Volume2, Sparkles
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
    gradient: "linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)",
    border: "#93c5fd",
    label: "#1d4ed8",
    dot: "#3b82f6",
    badge: { bg: "#dbeafe", text: "#1e40af", border: "#bfdbfe" },
    bar: "#3b82f6",
    icon: <Stethoscope className="w-4 h-4" />,
  },
  Patient: {
    gradient: "linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)",
    border: "#86efac",
    label: "#15803d",
    dot: "#22c55e",
    badge: { bg: "#dcfce7", text: "#166534", border: "#bbf7d0" },
    bar: "#22c55e",
    icon: <User className="w-4 h-4" />,
  },
  Unknown: {
    gradient: "linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)",
    border: "#fcd34d",
    label: "#b45309",
    dot: "#f59e0b",
    badge: { bg: "#fef3c7", text: "#92400e", border: "#fde68a" },
    bar: "#f59e0b",
    icon: <HelpCircle className="w-4 h-4" />,
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
  isConsultationRecording?: boolean;
  onStartConsultationRecording?: () => void;
  onStopConsultationRecording?: () => void;
  currentConsultationStatus?: string;
}

export default function LiveTranscriptionPanel({ 
  consultationId, 
  onTranscriptReady, 
  onGenerateNote,
  isConsultationRecording,
  onStartConsultationRecording,
  onStopConsultationRecording,
  currentConsultationStatus,
}: Props) {
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
    setAutoScroll(scrollHeight - scrollTop - clientHeight < 50);
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

  // Handle start recording with synchronized consultation trigger
  const handleStartRecording = () => {
    controls.start();
    if (onStartConsultationRecording) {
      onStartConsultationRecording();
    }
  };

  const handleStopRecording = () => {
    controls.stop();
    if (onStopConsultationRecording) {
      onStopConsultationRecording();
    }
  };

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

  const isActive = (asr.isRecording && !asr.isPaused) || isConsultationRecording === true;
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
      className="flex flex-col rounded-3xl overflow-hidden bg-white shadow-[0_16px_40px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.95)] border border-slate-200/90 w-full transition-all"
    >
      {/* ── Header ────────────────────────────────────────────── */}
      <div
        className="flex flex-wrap items-center justify-between px-6 py-4 border-b border-slate-200/80 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white shadow-md relative overflow-hidden gap-3"
      >
        <div className="absolute inset-0 bg-gradient-to-r from-teal-500/10 via-indigo-500/10 to-purple-500/10 pointer-events-none" />
        
        {/* Left: Title + recording status */}
        <div className="flex items-center gap-3.5 relative z-10">
          <div
            className={`flex items-center justify-center w-11 h-11 rounded-2xl shadow-md transition-all ${
              isActive 
                ? "bg-gradient-to-br from-rose-500 to-red-600 shadow-rose-500/40 ring-4 ring-rose-500/20 animate-pulse" 
                : "bg-gradient-to-br from-teal-400 to-indigo-600 shadow-teal-500/30 ring-2 ring-white/20"
            }`}
          >
            <Mic className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <span className="text-base font-extrabold text-white tracking-tight font-heading">
                Live Clinical Transcription
              </span>
              {isActive ? (
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-500/25 border border-rose-400/50 text-rose-200 shadow-xs">
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500" />
                  </span>
                  <span className="text-[11px] font-black uppercase tracking-wider">LIVE RECORDING</span>
                </span>
              ) : (
                <span className="text-[11px] font-bold text-slate-300 bg-white/10 px-2.5 py-0.5 rounded-full border border-white/10">
                  Ready to Listen
                </span>
              )}
            </div>
            <div className="text-xs text-slate-300 mt-0.5 flex items-center gap-2.5">
              <Clock className="w-3.5 h-3.5 text-teal-300" />
              <span className="font-mono font-bold text-white">{fmt(asr.elapsedMs)}</span>
              <span className="text-slate-500">•</span>
              <span className="font-medium text-slate-300">
                {asr.segments.length} dialogue segment{asr.segments.length !== 1 ? "s" : ""}
              </span>
              {isActive && (
                <>
                  <span className="text-slate-500">•</span>
                  <span className="flex items-center gap-1 text-teal-300 font-semibold text-[11px]">
                    <Volume2 className="w-3.5 h-3.5 animate-pulse" />
                    WebSpeech Stream Active
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Right: Controls */}
        <div className="flex items-center gap-2.5 relative z-10">
          {/* Speaker Mode selector */}
          <div className="relative">
            <button
              onClick={() => setShowModeDropdown(v => !v)}
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all bg-white/10 hover:bg-white/20 border border-white/20 text-white shadow-sm backdrop-blur-md active:scale-95"
            >
              {speakerMode === "auto" ? (
                <span className="flex items-center gap-1.5"><Sparkles className="w-3.5 h-3.5 text-indigo-300" /> Speaker: Auto</span>
              ) : speakerMode === "doctor" ? (
                <span className="flex items-center gap-1.5"><Stethoscope className="w-3.5 h-3.5 text-blue-300" /> Doctor Only</span>
              ) : (
                <span className="flex items-center gap-1.5"><User className="w-3.5 h-3.5 text-emerald-300" /> Patient Only</span>
              )}
              <ChevronDown className="w-3.5 h-3.5 text-slate-300" />
            </button>
            <AnimatePresence>
              {showModeDropdown && (
                <motion.div
                  initial={{ opacity: 0, y: -4, scale: 0.96 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -4, scale: 0.96 }}
                  transition={{ duration: 0.12 }}
                  className="absolute right-0 top-full mt-1.5 z-50 rounded-2xl overflow-hidden bg-white border border-slate-200 shadow-xl min-w-[170px]"
                >
                  <div className="p-1.5 space-y-1">
                    {(["auto", "doctor", "patient"] as SpeakerMode[]).map(m => (
                      <button
                        key={m}
                        onClick={() => handleModeChange(m)}
                        className={`w-full text-left px-3 py-2 text-xs font-bold rounded-xl transition-colors flex items-center justify-between ${
                          speakerMode === m 
                            ? "bg-indigo-50 text-indigo-700" 
                            : "text-slate-700 hover:bg-slate-50"
                        }`}
                      >
                        <span className="flex items-center gap-1.5">
                          {m === "auto" ? <Sparkles className="w-3.5 h-3.5 text-indigo-500" /> : m === "doctor" ? <Stethoscope className="w-3.5 h-3.5 text-blue-500" /> : <User className="w-3.5 h-3.5 text-emerald-500" />}
                          {m === "auto" ? "Auto-Detect" : m === "doctor" ? "Doctor Only" : "Patient Only"}
                        </span>
                        {speakerMode === m && <Check className="w-3.5 h-3.5 text-indigo-600" />}
                      </button>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Copy */}
          {asr.segments.length > 0 && (
            <button
              onClick={handleCopy}
              className="px-3 py-2 rounded-xl text-xs font-bold transition-all hover:scale-105 active:scale-95 flex items-center gap-1.5 shadow-sm"
              title="Copy transcript"
              style={{
                background: copied ? "rgba(16,185,129,0.25)" : "rgba(255,255,255,0.12)",
                border: copied ? "1px solid rgba(16,185,129,0.5)" : "1px solid rgba(255,255,255,0.2)",
                color: copied ? "#34d399" : "#e2e8f0",
              }}
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy</span>
                </>
              )}
            </button>
          )}

          {/* Clear */}
          {asr.segments.length > 0 && (
            <button
              onClick={controls.clearTranscript}
              className="p-2 rounded-xl transition-all hover:scale-105 active:scale-95 bg-white/10 hover:bg-rose-500/25 border border-white/20 text-slate-300 hover:text-rose-200"
              title="Clear transcript"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* ── Speaker Stats Bar ──────────────────────────────────── */}
      {asr.segments.length > 0 && (
        <div className="px-6 py-3 flex flex-wrap items-center justify-between gap-3 bg-slate-50/90 border-b border-slate-200/80">
          <div className="flex items-center gap-3 flex-1 min-w-[240px]">
            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700 shrink-0">
              <BarChart2 className="w-4 h-4 text-indigo-600" />
              <span>Diarization Breakdown:</span>
            </div>
            <div className="flex-1 flex h-2.5 rounded-full overflow-hidden gap-0.5 bg-slate-200/80 p-0.5 shadow-inner">
              {(["Doctor", "Patient", "Unknown"] as SpeakerRole[]).map(role => (
                <motion.div
                  key={role}
                  initial={{ width: 0 }}
                  animate={{ width: `${pct(role)}%` }}
                  transition={{ duration: 0.4, ease: "easeOut" }}
                  className="rounded-full shadow-xs"
                  style={{ background: SPEAKER_CONFIG[role].bar }}
                  title={`${role}: ${pct(role)}%`}
                />
              ))}
            </div>
          </div>
          <div className="flex items-center gap-3.5 text-xs font-bold">
            {(["Doctor", "Patient", "Unknown"] as SpeakerRole[]).map(role => (
              pct(role) > 0 ? (
                <span key={role} className="flex items-center gap-1.5" style={{ color: SPEAKER_CONFIG[role].label }}>
                  <span className="w-2.5 h-2.5 rounded-full ring-1 ring-black/10" style={{ background: SPEAKER_CONFIG[role].bar }} />
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
          className="flex flex-wrap items-center gap-3 px-6 py-2.5 bg-gradient-to-r from-teal-50/60 via-indigo-50/40 to-teal-50/60 border-b border-teal-200/70"
        >
          <span className="text-xs text-slate-700 font-extrabold uppercase tracking-wider shrink-0 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-teal-600" />
            Quick Speaker Cue:
          </span>
          <div className="flex items-center gap-2">
            {(["Doctor", "Patient"] as SpeakerRole[]).map(role => (
              <button
                key={role}
                onClick={() => controls.forceNextSpeaker(role)}
                className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all shadow-xs hover:scale-105 active:scale-95"
                style={{
                  background: SPEAKER_CONFIG[role].badge.bg,
                  border: `1px solid ${SPEAKER_CONFIG[role].badge.border}`,
                  color: SPEAKER_CONFIG[role].badge.text,
                }}
              >
                <span className="shrink-0">{SPEAKER_CONFIG[role].icon}</span>
                <span>{role} Speaking Next</span>
              </button>
            ))}
          </div>
          {asr.lastDoctorQuestion && (
            <span
              className="ml-auto flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-xs"
            >
              <ArrowRight className="w-3.5 h-3.5 text-emerald-600" />
              Doctor asked question — Patient reply expected
            </span>
          )}
        </div>
      )}

      {/* ── Transcript scroll area (Spacious, Ergonomic) ───────── */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-3.5 min-h-[380px] lg:min-h-[460px] max-h-[600px] bg-slate-50/40"
      >
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center min-h-[360px] text-center p-6">
            <div
              className="w-20 h-20 rounded-3xl flex items-center justify-center mb-5 shadow-lg"
              style={{ background: "linear-gradient(135deg, #eff6ff 0%, #e0e7ff 100%)" }}
            >
              <Mic className="w-9 h-9 text-indigo-600" />
            </div>
            <h4 className="text-base font-extrabold text-slate-800 font-heading">
              Continuous Live Speech-to-Text Ready
            </h4>
            <p className="text-sm text-slate-500 mt-2 max-w-md leading-relaxed font-medium">
              Click the <strong className="text-teal-700">Start Recording</strong> button below to capture the clinician-patient dialogue. 
              The AI automatically diarizes speakers, captures symptoms, and builds the clinical record in real time.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-2 mt-5">
              <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white text-xs font-bold text-slate-700 border border-slate-200 shadow-2xs">
                <Stethoscope className="w-3.5 h-3.5 text-blue-600" /> Doctor Diarization
              </span>
              <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white text-xs font-bold text-slate-700 border border-slate-200 shadow-2xs">
                <User className="w-3.5 h-3.5 text-emerald-600" /> Patient Diarization
              </span>
              <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white text-xs font-bold text-slate-700 border border-slate-200 shadow-2xs">
                <Zap className="w-3.5 h-3.5 text-amber-500" /> Sub-second Latency
              </span>
            </div>
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
                    className="flex gap-3.5 group"
                  >
                    {/* Speaker Avatar / Icon */}
                    <div className="flex flex-col items-center pt-1 shrink-0">
                      <div
                        className="w-8 h-8 rounded-xl flex items-center justify-center shadow-xs"
                        style={{ background: cfg.bar, color: "#fff" }}
                      >
                        {cfg.icon}
                      </div>
                    </div>

                    {/* Bubble */}
                    <div
                      className="flex-1 rounded-2xl px-4 py-3.5 min-w-0 shadow-xs transition-shadow hover:shadow-md"
                      style={{
                        background: cfg.gradient,
                        border: `1px solid ${cfg.border}`,
                      }}
                    >
                      {/* Bubble header */}
                      <div className="flex items-center gap-2.5 mb-2">
                        <span
                          className="flex items-center gap-1.5 text-xs font-extrabold font-heading"
                          style={{ color: cfg.label }}
                        >
                          <span className="shrink-0">{cfg.icon}</span>
                          <span>{role}</span>
                        </span>

                        {/* Confidence badge */}
                        <span
                          className="text-[10px] font-bold px-2 py-0.5 rounded-full border shadow-2xs"
                          style={{ background: cc.bg, color: cc.text, borderColor: cc.border }}
                        >
                          {confLabel(seg.confidence)} Confidence ({(seg.confidence * 100).toFixed(0)}%)
                        </span>

                        {/* Time */}
                        <span className="text-[11px] font-mono text-slate-500 ml-auto">
                          {new Date(seg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                        </span>

                        {/* Manual override buttons (appear on hover) */}
                        <div className="hidden group-hover:flex items-center gap-1.5 ml-2">
                          <span className="text-[10px] text-slate-400 font-medium">Reassign:</span>
                          {(["Doctor", "Patient", "Unknown"] as SpeakerRole[]).filter(r => r !== role).map(r => (
                            <button
                              key={r}
                              onClick={() => overrideSegment(seg.id, r)}
                              className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-lg border font-bold transition-all hover:scale-105 active:scale-95"
                              style={{
                                background: SPEAKER_CONFIG[r].badge.bg,
                                borderColor: SPEAKER_CONFIG[r].badge.border,
                                color: SPEAKER_CONFIG[r].badge.text,
                              }}
                              title={`Reassign to ${r}`}
                            >
                              <span className="shrink-0 scale-75">{SPEAKER_CONFIG[r].icon}</span>
                              <span>{r}</span>
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Text */}
                      <p
                        className="text-sm font-medium leading-relaxed text-slate-800"
                        style={{ opacity: seg.confidence < 0.5 ? 0.75 : 1 }}
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
                className="flex gap-3.5"
              >
                <div className="w-8 shrink-0 flex justify-center pt-2">
                  <span className="block w-3 h-3 rounded-full bg-teal-500 animate-ping" />
                </div>
                <div
                  className="flex-1 rounded-2xl px-4 py-3 bg-white border border-teal-200 border-dashed shadow-xs"
                >
                  <span className="text-xs text-teal-700 font-bold flex items-center gap-1.5 mb-1">
                    <Volume2 className="w-3.5 h-3.5 animate-pulse text-teal-600" />
                    Transcribing speech stream…
                  </span>
                  <p className="text-sm font-medium text-slate-600 italic">{asr.interimText}</p>
                </div>
              </motion.div>
            )}
          </>
        )}
      </div>

      {/* ── Prominent Controls Footer ──────────────────────────── */}
      <div
        className="px-6 py-4 flex flex-wrap items-center justify-between gap-4 bg-gradient-to-r from-slate-50 via-indigo-50/30 to-slate-50 border-t border-slate-200/90 shadow-[inset_0_1px_0_rgba(255,255,255,0.9)]"
      >
        {/* Not supported warning */}
        {!asr.isSupported && (
          <p className="text-xs text-amber-800 font-bold flex items-center gap-2 bg-amber-50 px-4 py-2 rounded-xl border border-amber-200">
            <Activity className="w-4 h-4 text-amber-600" />
            Please use Google Chrome or Microsoft Edge for native real-time WebSpeech transcription.
          </p>
        )}

        {asr.isSupported && (
          <div className="flex flex-wrap items-center gap-3">
            {/* Start / Pause / Resume */}
            {!asr.isRecording ? (
              <motion.button
                whileTap={{ scale: 0.96 }}
                whileHover={{ scale: 1.02, y: -1 }}
                onClick={handleStartRecording}
                className="flex items-center gap-2.5 px-6 py-3 rounded-2xl text-sm font-extrabold text-white shadow-lg transition-all"
                style={{
                  background: "linear-gradient(135deg, #0d9488 0%, #0284c7 100%)",
                  boxShadow: "0 6px 20px rgba(13,148,136,0.35), inset 0 1px 0 rgba(255,255,255,0.3)",
                }}
              >
                <Mic className="w-4 h-4" />
                <span>Start Live Voice Recording</span>
              </motion.button>
            ) : asr.isPaused ? (
              <motion.button
                whileTap={{ scale: 0.96 }}
                whileHover={{ scale: 1.02, y: -1 }}
                onClick={controls.resume}
                className="flex items-center gap-2 px-5 py-3 rounded-2xl text-sm font-extrabold text-white shadow-lg"
                style={{
                  background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                  boxShadow: "0 6px 18px rgba(16,185,129,0.35), inset 0 1px 0 rgba(255,255,255,0.3)",
                }}
              >
                <Mic className="w-4 h-4" />
                <span>Resume Recording</span>
              </motion.button>
            ) : (
              <motion.button
                whileTap={{ scale: 0.96 }}
                whileHover={{ scale: 1.02, y: -1 }}
                onClick={controls.pause}
                className="flex items-center gap-2 px-5 py-3 rounded-2xl text-sm font-extrabold text-white shadow-md"
                style={{
                  background: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
                  boxShadow: "0 6px 18px rgba(245,158,11,0.35), inset 0 1px 0 rgba(255,255,255,0.3)",
                }}
              >
                <Pause className="w-4 h-4" />
                <span>Pause Recording</span>
              </motion.button>
            )}

            {/* Stop */}
            {asr.isRecording && (
              <motion.button
                whileTap={{ scale: 0.96 }}
                whileHover={{ scale: 1.02, y: -1 }}
                onClick={handleStopRecording}
                className="flex items-center gap-2 px-5 py-3 rounded-2xl text-sm font-extrabold text-white shadow-md"
                style={{
                  background: "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)",
                  boxShadow: "0 6px 18px rgba(239,68,68,0.35), inset 0 1px 0 rgba(255,255,255,0.3)",
                }}
              >
                <Square className="w-4 h-4" />
                <span>Stop Recording</span>
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
            className="ml-auto flex items-center gap-2.5 px-6 py-3 rounded-2xl text-sm font-extrabold text-white transition-all disabled:opacity-70 shadow-lg"
            style={{
              background: generatingNote
                ? "linear-gradient(135deg, #94a3b8 0%, #64748b 100%)"
                : "linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%)",
              boxShadow: generatingNote ? "none" : "0 6px 20px rgba(124,58,237,0.35), inset 0 1px 0 rgba(255,255,255,0.3)",
            }}
          >
            {generatingNote ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Zap className="w-4 h-4" />
            )}
            <span>{noteGenStatus ?? "Synthesize Clinical Note From Audio"}</span>
          </motion.button>
        )}
      </div>
    </div>
  );
}
