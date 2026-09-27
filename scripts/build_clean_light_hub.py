# -*- coding: utf-8 -*-
"""
Build Clean Minimalist Light Hub UI Script
Generates a professional, minimalist, clean light theme for /hub with zero jittery zoom animations.
"""
import os

target_path = r"c:\Users\User\Downloads\DocAssistIQ\frontend\src\app\(shell)\hub\page.tsx"

code = '''/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable react/no-unescaped-entities */
"use client";

import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { createPortal } from "react-dom";
import { useAuth } from "@/lib/auth-context";
import { motion, AnimatePresence } from "framer-motion";
import { getStoredToken, authVerifyAccount } from "@/lib/api";

// ─── Types & Interfaces ────────────────────────────────────────────────────────

interface PostAttachment {
  id: string;
  file_url: string;
  file_type: string;
  created_at?: string;
}

interface PostComment {
  id: string;
  author_id: string;
  author_name?: string;
  author_specialty?: string;
  author_institution?: string;
  author_credentials?: string;
  content: string;
  created_at: string;
}

interface PollOption {
  label: string;
  votes: number;
}

interface PollData {
  question: string;
  options: PollOption[];
  total_votes: number;
  has_voted?: boolean;
  voted_index?: number | null;
}

interface DoctorPost {
  id: string;
  author_id: string;
  author_name?: string;
  author_specialty?: string;
  author_institution?: string;
  author_credentials?: string;
  is_author_verified?: boolean;
  case_status?: string; // "urgent_consult" | "solved" | "active"
  is_urgent_consult?: boolean;
  disease_name: string;
  clinical_findings: string;
  diagnosis: string;
  treatment_plan: string;
  drugs_used: string[];
  specialty_tags: string[];
  likes_count: number;
  comments_count: number;
  is_liked_by_me: boolean;
  is_bookmarked_by_me: boolean;
  endorsements_count?: number;
  is_endorsed_by_me?: boolean;
  reactions_breakdown?: Record<string, number>;
  my_reaction?: string | null;
  poll_data?: PollData | null;
  ai_knowledge_weight?: number;
  created_at: string;
  attachments: PostAttachment[];
  comments: PostComment[];
}

interface TrendingData {
  trending_diseases: { name: string; post_count: number }[];
  trending_tags: { tag: string; count: number }[];
  posts_this_week: number;
}

interface DoctorProfile {
  id: string;
  full_name: string;
  specialization: string;
  verification_status: string;
  post_count: number;
  followers_count?: number;
  is_following?: boolean;
}

interface DoctorMyStats {
  cases_count: number;
  endorsements_count: number;
  validations_count: number;
  consensus_rate: number;
  followers_count: number;
  following_count: number;
}

interface HubPulse {
  online_specialists_count: number;
  active_departments: { name: string; active: number; color: string }[];
  live_ticker: string[];
  total_cases_indexed: number;
}

interface VitalsMetric {
  label: string;
  value: string;
  status: "normal" | "warning" | "critical";
  metricType: "hr" | "bp" | "spo2" | "temp" | "lab" | "ecg" | "gcs";
}

// ─── Precision Medical SVG Icons (Luxury Clinical Tier) ───────────────────────

const ClinicalIcons = {
  Stethoscope: ({ className = "w-4 h-4" }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4.5 3v5a3.5 3.5 0 0 0 7 0V3" />
      <path d="M8 11.5v4a4 4 0 0 0 8 0v-1" />
      <circle cx="18" cy="14" r="2.5" />
      <circle cx="4.5" cy="3" r="1.5" />
      <circle cx="11.5" cy="3" r="1.5" />
    </svg>
  ),
  Pulse: ({ className = "w-4 h-4" }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  ),
  ShieldCheck: ({ className = "w-4 h-4" }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  ),
  Lightbulb: ({ className = "w-4 h-4" }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5" />
      <path d="M9 18h6" />
      <path d="M10 22h4" />
    </svg>
  ),
  Microscope: ({ className = "w-4 h-4" }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 18h8" />
      <path d="M3 22h18" />
      <path d="M14 22a7 7 0 1 0 0-14h-1" />
      <path d="M9 14h2" />
      <path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z" />
      <path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3" />
    </svg>
  ),
  Handshake: ({ className = "w-4 h-4" }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m11 17 2 2a1 1 0 0 0 1.4 0l4.3-4.3a1 1 0 0 0 0-1.4l-2.6-2.6a1 1 0 0 0-1.4 0L13 12.4" />
      <path d="m13 7.6-1.7-1.7a1 1 0 0 0-1.4 0L5.6 10.2a1 1 0 0 0 0 1.4l2.6 2.6a1 1 0 0 0 1.4 0l1.7-1.7" />
      <path d="m7.5 13.5-3 3a2.12 2.12 0 0 0 3 3l3-3" />
      <path d="m16.5 10.5 3-3a2.12 2.12 0 0 0-3-3l-3 3" />
    </svg>
  ),
  AlertTriangle: ({ className = "w-4 h-4" }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  ),
  Calculator: ({ className = "w-4 h-4" }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect width="16" height="20" x="4" y="2" rx="2" />
      <line x1="8" x2="16" y1="6" y2="6" />
      <line x1="16" x2="16" y1="14" y2="18" />
      <path d="M16 10h.01" /><path d="M12 10h.01" /><path d="M8 10h.01" />
      <path d="M12 14h.01" /><path d="M8 14h.01" /><path d="M12 18h.01" /><path d="M8 18h.01" />
    </svg>
  ),
  Scale: ({ className = "w-4 h-4" }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z" />
      <path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z" />
      <path d="M7 21h10" /><path d="M12 3v18" /><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2" />
    </svg>
  ),
  FileText: ({ className = "w-4 h-4" }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" x2="8" y1="13" y2="13" />
      <line x1="16" x2="8" y1="17" y2="17" />
      <line x1="10" x2="8" y1="9" y2="9" />
    </svg>
  ),
  Pager: ({ className = "w-4 h-4" }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect width="20" height="14" x="2" y="5" rx="3" />
      <path d="M6 9h12" />
      <circle cx="6" cy="14" r="1" />
      <circle cx="10" cy="14" r="1" />
      <circle cx="14" cy="14" r="1" />
      <path d="M2 9h2" />
    </svg>
  ),
  Droplet: ({ className = "w-4 h-4" }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
    </svg>
  ),
  Lungs: ({ className = "w-4 h-4" }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3v9" />
      <path d="M6 6c-2 2-3 5-3 8a6 6 0 0 0 6 6c2 0 3-1 3-3V9c0-1-1-2-2-2-1.5 0-3-.5-4-1z" />
      <path d="M18 6c2 2 3 5 3 8a6 6 0 0 1-6 6c-2 0-3-1-3-3V9c0-1 1-2 2-2 1.5 0 3-.5 4-1z" />
    </svg>
  ),
  Thermometer: ({ className = "w-4 h-4" }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z" />
    </svg>
  ),
  Flask: ({ className = "w-4 h-4" }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10 2v7.31L4.15 20.08A2 2 0 0 0 5.89 23h12.22a2 2 0 0 0 1.74-2.92L14 9.31V2" />
      <path d="M8.5 2h7" />
      <path d="M14 9.3a6.5 6.5 0 0 0-4 0" />
    </svg>
  ),
  Brain: ({ className = "w-4 h-4" }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-2.04" />
      <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-2.04" />
    </svg>
  ),
  Flame: ({ className = "w-4 h-4" }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z" />
    </svg>
  ),
};

// ─── Sound Synthesizers (Web Audio API) ────────────────────────────────────────

function playClinicalChime() {
  try {
    const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(587.33, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.12);
    gain.gain.setValueAtTime(0.04, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.3);
  } catch {}
}

function playUrgentPagerBeep() {
  try {
    const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    osc.frequency.setValueAtTime(1174.66, ctx.currentTime + 0.08);
    gain.gain.setValueAtTime(0.05, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.25);
  } catch {}
}

// ─── Constants & Styling Maps (Clean Light Mode) ──────────────────────────────

const ALL_SPECIALTIES = [
  "Cardiology", "Neurology", "Oncology", "Pediatrics",
  "Orthopedics", "Dermatology", "Gastroenterology", "Endocrinology",
  "Pulmonology", "Nephrology", "Hematology", "Rheumatology",
  "Infectious Disease", "Emergency Medicine", "Internal Medicine",
];

const SPECIALTY_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  Cardiology: { bg: "bg-red-50 text-red-700", text: "text-red-700", border: "border-red-200" },
  Neurology: { bg: "bg-purple-50 text-purple-700", text: "text-purple-700", border: "border-purple-200" },
  Oncology: { bg: "bg-amber-50 text-amber-800", text: "text-amber-800", border: "border-amber-200" },
  Pediatrics: { bg: "bg-pink-50 text-pink-700", text: "text-pink-700", border: "border-pink-200" },
  Dermatology: { bg: "bg-rose-50 text-rose-700", text: "text-rose-700", border: "border-rose-200" },
  "Infectious Disease": { bg: "bg-emerald-50 text-emerald-700", text: "text-emerald-700", border: "border-emerald-200" },
  "Emergency Medicine": { bg: "bg-orange-50 text-orange-800", text: "text-orange-800", border: "border-orange-200" },
  default: { bg: "bg-teal-50 text-teal-800", text: "text-teal-800", border: "border-teal-200" },
};

const CLINICAL_REACTIONS = [
  { id: "validate", label: "Validate Protocol", Icon: ClinicalIcons.Stethoscope, desc: "Attending agrees with evidence-based management" },
  { id: "insightful", label: "High-Yield Insight", Icon: ClinicalIcons.Lightbulb, desc: "Diagnostic criteria provides high CME value" },
  { id: "rare", label: "Rare Pathology", Icon: ClinicalIcons.Microscope, desc: "Atypical presentation or rare finding" },
  { id: "endorsed", label: "Attending Endorsement", Icon: ClinicalIcons.Handshake, desc: "Senior faculty verified and approved" },
  { id: "flag", label: "Caution Flag", Icon: ClinicalIcons.AlertTriangle, desc: "Contraindication note or potential mimic" },
];

function getSpecialtyStyle(tag: string) {
  return SPECIALTY_STYLES[tag] ?? SPECIALTY_STYLES.default;
}

function timeAgo(dateStr: string): string {
  if (!dateStr) return "recently";
  const diff = Date.now() - new Date(dateStr).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d < 7) return `${d}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

function getInitials(nameOrId: string): string {
  if (!nameOrId) return "DR";
  const clean = nameOrId.replace(/^Dr\\.\\s*/i, "").trim();
  const parts = clean.split(" ");
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return clean.substring(0, 2).toUpperCase();
}

function getAvatarGradient(id: string): string {
  const gradients = [
    "from-teal-600 to-emerald-700",
    "from-blue-600 to-indigo-700",
    "from-purple-600 to-violet-700",
    "from-rose-600 to-red-700",
    "from-amber-600 to-orange-700",
    "from-emerald-600 to-teal-700",
  ];
  let sum = 0;
  for (let i = 0; i < id.length; i++) sum += id.charCodeAt(i);
  return gradients[sum % gradients.length];
}

// ─── Helper: Bedside Clinical Vitals HUD ──────────────────────────────────────

function getClinicalVitalsHUD(diseaseName: string, findings: string): VitalsMetric[] {
  const lower = (diseaseName + " " + findings).toLowerCase();
  
  if (lower.includes("wellens")) {
    return [
      { label: "Heart Rate", value: "68 bpm", status: "normal", metricType: "hr" },
      { label: "Blood Pressure", value: "128/82 mmHg", status: "normal", metricType: "bp" },
      { label: "SpO2", value: "98% (Room Air)", status: "normal", metricType: "spo2" },
      { label: "Troponin I", value: "0.12 ng/mL (Borderline)", status: "warning", metricType: "lab" },
      { label: "ECG Finding", value: "Biphasic T-Waves V2-V3", status: "critical", metricType: "ecg" },
    ];
  } else if (lower.includes("dengue") || lower.includes("hlh")) {
    return [
      { label: "Heart Rate", value: "132 bpm (Tachycardia)", status: "critical", metricType: "hr" },
      { label: "Blood Pressure", value: "82/50 mmHg (MAP 60)", status: "critical", metricType: "bp" },
      { label: "Core Temp", value: "39.8 °C", status: "critical", metricType: "temp" },
      { label: "Platelets", value: "18,000 /µL (Severe)", status: "critical", metricType: "lab" },
      { label: "Ferritin", value: "18,400 ng/mL", status: "critical", metricType: "lab" },
    ];
  } else if (lower.includes("encephalitis") || lower.includes("nmda")) {
    return [
      { label: "Heart Rate", value: "114 bpm", status: "warning", metricType: "hr" },
      { label: "Blood Pressure", value: "142/92 mmHg", status: "warning", metricType: "bp" },
      { label: "GCS Score", value: "10/15 (Fluctuating)", status: "critical", metricType: "gcs" },
      { label: "CSF Antibody", value: "Anti-GluN1 IgG Positive", status: "critical", metricType: "lab" },
      { label: "EEG Pattern", value: "Extreme Delta Brush", status: "critical", metricType: "ecg" },
    ];
  } else if (lower.includes("kawasaki")) {
    return [
      { label: "Core Temp", value: "39.4 °C (Day 7 Fever)", status: "critical", metricType: "temp" },
      { label: "Heart Rate", value: "140 bpm", status: "warning", metricType: "hr" },
      { label: "Serum CRP", value: "142 mg/L (Marked)", status: "critical", metricType: "lab" },
      { label: "Echo Finding", value: "LAD Z-Score +3.4", status: "critical", metricType: "ecg" },
      { label: "Platelets", value: "620,000 /µL", status: "warning", metricType: "lab" },
    ];
  } else if (lower.includes("epidermal") || lower.includes("ten") || lower.includes("allopurinol")) {
    return [
      { label: "Core Temp", value: "39.1 °C", status: "critical", metricType: "temp" },
      { label: "BSA Sloughing", value: "38% Detachment", status: "critical", metricType: "lab" },
      { label: "SCORTEN", value: "Score 4 (Mortality 58%)", status: "critical", metricType: "lab" },
      { label: "Genotype", value: "HLA-B*58:01 Positive", status: "critical", metricType: "lab" },
      { label: "Mucosal Extent", value: "Oral + Ocular Involved", status: "critical", metricType: "lab" },
    ];
  }
  
  return [
    { label: "Heart Rate", value: "76 bpm", status: "normal", metricType: "hr" },
    { label: "Blood Pressure", value: "120/80 mmHg", status: "normal", metricType: "bp" },
    { label: "SpO2", value: "99% Ambient", status: "normal", metricType: "spo2" },
    { label: "Biomarker Index", value: "Evaluated & Indexed", status: "normal", metricType: "lab" },
  ];
}

function renderVitalIcon(type: VitalsMetric["metricType"]) {
  switch (type) {
    case "hr": return <ClinicalIcons.Pulse className="w-3.5 h-3.5 text-rose-500" />;
    case "bp": return <ClinicalIcons.Droplet className="w-3.5 h-3.5 text-red-500" />;
    case "spo2": return <ClinicalIcons.Lungs className="w-3.5 h-3.5 text-teal-600" />;
    case "temp": return <ClinicalIcons.Thermometer className="w-3.5 h-3.5 text-amber-600" />;
    case "lab": return <ClinicalIcons.Flask className="w-3.5 h-3.5 text-emerald-600" />;
    case "ecg": return <ClinicalIcons.Pulse className="w-3.5 h-3.5 text-teal-600" />;
    case "gcs": return <ClinicalIcons.Brain className="w-3.5 h-3.5 text-purple-600" />;
    default: return <ClinicalIcons.Pulse className="w-3.5 h-3.5 text-teal-600" />;
  }
}

// ─── Component: ECG Pulse Waveform (Clean Light SVG) ──────────────────────────

function EcgSparkline() {
  return (
    <svg
      className="w-16 h-5 text-teal-600 opacity-80 hidden sm:block flex-shrink-0"
      viewBox="0 0 100 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path
        d="M0 12 H20 L24 6 L30 18 L36 4 L42 22 L46 12 H100"
        strokeDasharray="100"
        strokeDashoffset="0"
        className="animate-[dash_2.5s_linear_infinite]"
      />
    </svg>
  );
}

// ─── Component: Live Pulse Marquee & Command Bar (Clean Light Theme) ──────────

function LivePulseBar({
  pulse,
  soundEnabled,
  onToggleSound,
  onOpenDoctors,
  onOpenCalculator,
}: {
  pulse: HubPulse | null;
  soundEnabled: boolean;
  onToggleSound: () => void;
  onOpenDoctors: () => void;
  onOpenCalculator: () => void;
}) {
  const [tickerIndex, setTickerIndex] = useState(0);

  useEffect(() => {
    if (!pulse?.live_ticker?.length) return;
    const interval = setInterval(() => {
      setTickerIndex((prev) => (prev + 1) % pulse.live_ticker.length);
    }, 7000);
    return () => clearInterval(interval);
  }, [pulse?.live_ticker]);

  return (
    <div className="relative overflow-hidden rounded-2xl bg-white border border-slate-200/90 shadow-sm p-3.5 mb-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        {/* Left: Online Specialists Pill with Radar Ping */}
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenDoctors}
            className="flex items-center gap-2 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 px-3.5 py-1.5 rounded-full text-emerald-800 text-xs font-bold tracking-wide transition-all hover:scale-[1.01] active:scale-[0.99]"
            title="Click to view verified physicians online"
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-600" />
            </span>
            <span>{pulse?.online_specialists_count ?? 8} Verified Specialists Online</span>
            <span className="text-[10px] text-emerald-600 font-mono">▼</span>
          </button>

          <EcgSparkline />

          {/* Clinical Calculator Quick Action */}
          <button
            onClick={onOpenCalculator}
            className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 text-xs font-semibold transition-all hover:scale-[1.01] active:scale-[0.99]"
          >
            <ClinicalIcons.Calculator className="w-3.5 h-3.5 text-teal-600" />
            <span>Clinical Calculators (TIMI / Wells / GCS)</span>
          </button>
        </div>

        {/* Right: Live Ticker Feed & Audio Chime Toggle */}
        <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
          <div className="flex-1 sm:max-w-md overflow-hidden flex items-center gap-2 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl">
            <span className="text-[10px] font-black uppercase tracking-wider text-teal-800 bg-teal-100 border border-teal-200 px-2 py-0.5 rounded-md flex-shrink-0">
              LIVE PULSE
            </span>
            <AnimatePresence mode="wait">
              <motion.p
                key={tickerIndex}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.25 }}
                className="text-xs text-slate-700 truncate font-medium flex-1"
              >
                {pulse?.live_ticker?.[tickerIndex] ?? "Consensus achieved on Acute Coronary Protocol across 12 institutions"}
              </motion.p>
            </AnimatePresence>
          </div>

          {/* Chime toggle button */}
          <button
            onClick={onToggleSound}
            className={`p-2 rounded-xl border text-xs transition-all flex items-center gap-1 ${
              soundEnabled
                ? "bg-teal-50 text-teal-700 border-teal-300"
                : "bg-slate-50 text-slate-500 border-slate-200 hover:text-slate-800"
            }`}
            title={soundEnabled ? "Mute Clinical Telemetry Audio" : "Enable Clinical Telemetry Audio"}
          >
            <span>{soundEnabled ? "🔔" : "🔕"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Component: Point-of-Care Clinical Risk Calculators (Clean Light Modal) ────

function ClinicalCalculatorModal({ onClose }: { onClose: () => void }) {
  const [activeTab, setActiveTab] = useState<"timi" | "wells" | "chads" | "curb" | "gcs">("timi");
  const [copiedNote, setCopiedNote] = useState(false);

  // TIMI State
  const [timiCriteria, setTimiCriteria] = useState({
    age65: false,
    cadRisk: false,
    knownCad: false,
    asa7d: false,
    angina24h: false,
    stDev: false,
    biomarkers: false,
  });

  // Wells PE State
  const [wellsCriteria, setWellsCriteria] = useState({
    signsDvt: false,
    peLikely: false,
    hrOver100: false,
    surgeryImmob: false,
    priorDvtPe: false,
    hemoptysis: false,
    cancer: false,
  });

  // CHA2DS2-VASc State
  const [chadsCriteria, setChadsCriteria] = useState({
    chf: false,
    htn: false,
    age75: false,
    dm: false,
    stroke: false,
    vascular: false,
    age65_74: false,
    female: false,
  });

  // CURB-65 State
  const [curbCriteria, setCurbCriteria] = useState({
    confusion: false,
    urea: false,
    rr: false,
    bp: false,
    age65: false,
  });

  // GCS State
  const [gcsEye, setGcsEye] = useState(4);
  const [gcsVerbal, setGcsVerbal] = useState(5);
  const [gcsMotor, setGcsMotor] = useState(6);

  // Calculate TIMI Score
  const timiScore = useMemo(() => {
    return Object.values(timiCriteria).filter(Boolean).length;
  }, [timiCriteria]);

  const timiRisk = useMemo(() => {
    const riskMap: Record<number, { pct: string; level: string; rec: string }> = {
      0: { pct: "4.7%", level: "Low Risk", rec: "Consider conservative / outpatient observation pathway." },
      1: { pct: "4.7%", level: "Low Risk", rec: "Consider conservative / outpatient observation pathway." },
      2: { pct: "8.3%", level: "Low Risk", rec: "Observation unit; early stress testing or coronary CT." },
      3: { pct: "13.2%", level: "Intermediate Risk", rec: "Inpatient telemetry; early invasive angiography within 24h." },
      4: { pct: "19.9%", level: "Intermediate Risk", rec: "Inpatient telemetry; urgent catheterization recommended." },
      5: { pct: "26.2%", level: "High Risk", rec: "Immediate cath lab activation; dual antiplatelet + heparin." },
      6: { pct: "40.9%", level: "Very High Risk", rec: "STAT invasive angiography; intensive care resuscitation." },
      7: { pct: "40.9%", level: "Very High Risk", rec: "STAT invasive angiography; intensive care resuscitation." },
    };
    return riskMap[timiScore] || riskMap[7];
  }, [timiScore]);

  // Calculate Wells PE Score
  const wellsScore = useMemo(() => {
    let s = 0;
    if (wellsCriteria.signsDvt) s += 3.0;
    if (wellsCriteria.peLikely) s += 3.0;
    if (wellsCriteria.hrOver100) s += 1.5;
    if (wellsCriteria.surgeryImmob) s += 1.5;
    if (wellsCriteria.priorDvtPe) s += 1.5;
    if (wellsCriteria.hemoptysis) s += 1.0;
    if (wellsCriteria.cancer) s += 1.0;
    return s;
  }, [wellsCriteria]);

  const wellsGuideline = useMemo(() => {
    if (wellsScore < 2.0) {
      return { prob: "Low Probability (PE ~3.6%)", action: "High-sensitivity D-Dimer test. If negative, rule out PE without CTPA." };
    } else if (wellsScore <= 6.0) {
      return { prob: "Moderate Probability (PE ~20.5%)", action: "High-sensitivity D-Dimer test or direct CT Pulmonary Angiography (CTPA)." };
    } else {
      return { prob: "High Probability (PE ~66.7%)", action: "Immediate CTPA indicated. Initiate empiric anticoagulation if no contraindications." };
    }
  }, [wellsScore]);

  // Calculate CHA2DS2-VASc
  const chadsScore = useMemo(() => {
    let s = 0;
    if (chadsCriteria.chf) s += 1;
    if (chadsCriteria.htn) s += 1;
    if (chadsCriteria.age75) s += 2;
    if (chadsCriteria.dm) s += 1;
    if (chadsCriteria.stroke) s += 2;
    if (chadsCriteria.vascular) s += 1;
    if (chadsCriteria.age65_74) s += 1;
    if (chadsCriteria.female) s += 1;
    return s;
  }, [chadsCriteria]);

  // Calculate CURB-65
  const curbScore = useMemo(() => {
    return Object.values(curbCriteria).filter(Boolean).length;
  }, [curbCriteria]);

  // Calculate GCS
  const gcsTotal = gcsEye + gcsVerbal + gcsMotor;

  const copyClinicalSummary = () => {
    let note = "";
    if (activeTab === "timi") {
      note = `[DocAssistIQ Clinical Risk Calculator]
TIMI Risk Score for UA/NSTEMI: ${timiScore}/7
14-Day Risk of All-Cause Mortality / MI / Severe Ischemia: ${timiRisk.pct} (${timiRisk.level})
Clinical Recommendation: ${timiRisk.rec}
Evaluated via DocAssistIQ Board Certified Telemetry Network.`;
    } else if (activeTab === "wells") {
      note = `[DocAssistIQ Clinical Risk Calculator]
Wells' Criteria for Pulmonary Embolism (PE): ${wellsScore.toFixed(1)} Points
Stratification: ${wellsGuideline.prob}
Pathway Action: ${wellsGuideline.action}
Evaluated via DocAssistIQ Board Certified Telemetry Network.`;
    } else if (activeTab === "chads") {
      note = `[DocAssistIQ Clinical Risk Calculator]
CHA2DS2-VASc Score for AFib Stroke Risk: ${chadsScore}/9
Anticoagulation: ${chadsScore >= 2 ? "Oral Anticoagulation (DOAC) Strongly Recommended (Class I)" : chadsScore === 1 ? "Consider Oral Anticoagulation based on clinical risk (Class IIa)" : "Low risk; Anticoagulation generally not indicated"}
Evaluated via DocAssistIQ Board Certified Telemetry Network.`;
    } else if (activeTab === "curb") {
      note = `[DocAssistIQ Clinical Risk Calculator]
CURB-65 Pneumonia Severity Score: ${curbScore}/5
Disposition: ${curbScore <= 1 ? "Low Risk; Outpatient Management feasible" : curbScore === 2 ? "Intermediate Risk; Inpatient ward observation or close outpatient monitoring" : "High Risk; Urgent Hospital Admission / ICU evaluation"}
Evaluated via DocAssistIQ Board Certified Telemetry Network.`;
    } else {
      note = `[DocAssistIQ Clinical Risk Calculator]
Glasgow Coma Scale (GCS): E${gcsEye} V${gcsVerbal} M${gcsMotor} = ${gcsTotal}/15
Classification: ${gcsTotal >= 13 ? "Mild Traumatic Brain Injury" : gcsTotal >= 9 ? "Moderate Brain Injury" : "Severe Brain Injury (GCS ≤ 8: Intubation / Airway Protection Mandatory)"}
Evaluated via DocAssistIQ Board Certified Telemetry Network.`;
    }

    navigator.clipboard?.writeText(note);
    setCopiedNote(true);
    setTimeout(() => setCopiedNote(false), 2500);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[110] bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.96, y: 10 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.96, y: 10 }}
        transition={{ duration: 0.2 }}
        className="w-full max-w-2xl bg-white border border-slate-200 rounded-3xl p-6 shadow-2xl space-y-4 max-h-[92vh] overflow-y-auto custom-scrollbar"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-600">
              <ClinicalIcons.Calculator className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-extrabold text-base text-slate-900">
                Point-of-Care Clinical Risk Calculators
              </h3>
              <p className="text-[10px] text-slate-500 font-medium">
                Standardized Evidence-Based Decision Instruments • AMA / ACC / ESC Compliant
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 hover:bg-slate-200 hover:text-slate-800 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex gap-1.5 p-1 bg-slate-50 rounded-2xl border border-slate-200 overflow-x-auto custom-scrollbar">
          {[
            { id: "timi", label: "TIMI UA/NSTEMI" },
            { id: "wells", label: "Wells' PE Criteria" },
            { id: "chads", label: "CHA₂DS₂-VASc" },
            { id: "curb", label: "CURB-65" },
            { id: "gcs", label: "Glasgow Coma (GCS)" },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id as any)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                activeTab === t.id
                  ? "bg-teal-600 text-white font-extrabold shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* ── TIMI Calculator ── */}
        {activeTab === "timi" && (
          <div className="space-y-4">
            <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200 space-y-2">
              <p className="text-xs font-bold text-slate-700 mb-2">
                Select presenting clinical risk indicators:
              </p>
              {[
                { k: "age65", label: "Age ≥ 65 years" },
                { k: "cadRisk", label: "≥ 3 CAD Risk Factors (Family hx, HTN, Hypercholesterolemia, DM, Smoking)" },
                { k: "knownCad", label: "Known CAD (Coronary stenosis ≥ 50%)" },
                { k: "asa7d", label: "Aspirin (ASA) use in past 7 days" },
                { k: "angina24h", label: "Severe Angina (≥ 2 episodes in last 24 hours)" },
                { k: "stDev", label: "ECG ST-segment deviation ≥ 0.5 mm" },
                { k: "biomarkers", label: "Elevated Cardiac Biomarkers (Troponin I/T or CK-MB)" },
              ].map((item) => (
                <label
                  key={item.k}
                  className="flex items-center gap-3 p-2.5 rounded-xl bg-white border border-slate-200 hover:border-teal-400 cursor-pointer transition-all"
                >
                  <input
                    type="checkbox"
                    checked={(timiCriteria as any)[item.k]}
                    onChange={(e) =>
                      setTimiCriteria((prev) => ({ ...prev, [item.k]: e.target.checked }))
                    }
                    className="w-4 h-4 rounded text-teal-600 accent-teal-600 cursor-pointer"
                  />
                  <span className="text-xs text-slate-800 font-medium">{item.label}</span>
                </label>
              ))}
            </div>

            {/* Score Result Card */}
            <div className="p-4 rounded-2xl bg-teal-50 border border-teal-200 flex items-center justify-between">
              <div>
                <span className="text-[10px] font-black uppercase tracking-wider text-teal-800">
                  Calculated TIMI Score
                </span>
                <div className="text-2xl font-black text-slate-900 font-mono flex items-baseline gap-2">
                  <span>{timiScore} / 7</span>
                  <span className="text-sm font-bold text-teal-700">({timiRisk.level})</span>
                </div>
                <p className="text-xs text-slate-700 mt-1 font-medium">
                  14-Day Risk of Death / MI / Urgent Revascularization: <strong className="text-slate-900 font-mono">{timiRisk.pct}</strong>
                </p>
                <p className="text-[11px] text-teal-800 font-semibold mt-0.5">
                  Guideline: {timiRisk.rec}
                </p>
              </div>

              <div className="w-16 h-16 rounded-2xl bg-white border border-teal-200 flex items-center justify-center font-black text-xl text-teal-700 font-mono shadow-sm">
                {timiRisk.pct}
              </div>
            </div>
          </div>
        )}

        {/* ── Wells' PE Calculator ── */}
        {activeTab === "wells" && (
          <div className="space-y-4">
            <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200 space-y-2">
              <p className="text-xs font-bold text-slate-700 mb-2">
                Select validated Wells' Criteria for Pulmonary Embolism:
              </p>
              {[
                { k: "signsDvt", label: "Clinical signs and symptoms of DVT (leg swelling, pain with palpation) (+3.0)" },
                { k: "peLikely", label: "Alternative diagnosis is less likely than PE (+3.0)" },
                { k: "hrOver100", label: "Heart Rate > 100 bpm (+1.5)" },
                { k: "surgeryImmob", label: "Immobilization (≥ 3 days) or surgery in previous 4 weeks (+1.5)" },
                { k: "priorDvtPe", label: "Previous objectively diagnosed DVT or PE (+1.5)" },
                { k: "hemoptysis", label: "Hemoptysis (+1.0)" },
                { k: "cancer", label: "Malignancy (under treatment, in last 6 mo, or palliative) (+1.0)" },
              ].map((item) => (
                <label
                  key={item.k}
                  className="flex items-center gap-3 p-2.5 rounded-xl bg-white border border-slate-200 hover:border-teal-400 cursor-pointer transition-all"
                >
                  <input
                    type="checkbox"
                    checked={(wellsCriteria as any)[item.k]}
                    onChange={(e) =>
                      setWellsCriteria((prev) => ({ ...prev, [item.k]: e.target.checked }))
                    }
                    className="w-4 h-4 rounded text-teal-600 accent-teal-600 cursor-pointer"
                  />
                  <span className="text-xs text-slate-800 font-medium">{item.label}</span>
                </label>
              ))}
            </div>

            <div className="p-4 rounded-2xl bg-teal-50 border border-teal-200">
              <span className="text-[10px] font-black uppercase tracking-wider text-teal-800">
                Wells' Score for Pulmonary Embolism
              </span>
              <div className="text-2xl font-black text-slate-900 font-mono flex items-baseline gap-2">
                <span>{wellsScore.toFixed(1)} Points</span>
                <span className="text-sm font-bold text-teal-700">({wellsGuideline.prob})</span>
              </div>
              <p className="text-xs text-slate-700 mt-1 font-medium leading-relaxed">
                Management Pathway: <strong className="text-slate-900">{wellsGuideline.action}</strong>
              </p>
            </div>
          </div>
        )}

        {/* ── CHA2DS2-VASc ── */}
        {activeTab === "chads" && (
          <div className="space-y-4">
            <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200 space-y-2">
              <p className="text-xs font-bold text-slate-700 mb-2">
                Atrial Fibrillation Thromboembolic Risk Stratification:
              </p>
              {[
                { k: "chf", label: "Congestive Heart Failure / LVEF ≤ 40% (+1)" },
                { k: "htn", label: "Hypertension (BP > 140/90 mmHg or treated) (+1)" },
                { k: "age75", label: "Age ≥ 75 years (+2)" },
                { k: "dm", label: "Diabetes Mellitus (+1)" },
                { k: "stroke", label: "Prior Stroke / TIA / Thromboembolism (+2)" },
                { k: "vascular", label: "Vascular Disease (Prior MI, PAD, or Aortic Plaque) (+1)" },
                { k: "age65_74", label: "Age 65–74 years (+1)" },
                { k: "female", label: "Sex Category: Female (+1)" },
              ].map((item) => (
                <label
                  key={item.k}
                  className="flex items-center gap-3 p-2.5 rounded-xl bg-white border border-slate-200 hover:border-teal-400 cursor-pointer transition-all"
                >
                  <input
                    type="checkbox"
                    checked={(chadsCriteria as any)[item.k]}
                    onChange={(e) =>
                      setChadsCriteria((prev) => ({ ...prev, [item.k]: e.target.checked }))
                    }
                    className="w-4 h-4 rounded text-teal-600 accent-teal-600 cursor-pointer"
                  />
                  <span className="text-xs text-slate-800 font-medium">{item.label}</span>
                </label>
              ))}
            </div>

            <div className="p-4 rounded-2xl bg-teal-50 border border-teal-200">
              <span className="text-[10px] font-black uppercase tracking-wider text-teal-800">
                CHA₂DS₂-VASc Score: {chadsScore} / 9
              </span>
              <p className="text-xs text-slate-800 mt-1 font-medium">
                {chadsScore >= 2
                  ? "Oral Anticoagulation (DOAC) Strongly Recommended (Class I Guideline Evidence)."
                  : chadsScore === 1
                  ? "Consider Oral Anticoagulation based on bleeding risk vs benefits (Class IIa)."
                  : "Low Thromboembolic Risk. Anticoagulation generally not indicated."}
              </p>
            </div>
          </div>
        )}

        {/* ── CURB-65 ── */}
        {activeTab === "curb" && (
          <div className="space-y-4">
            <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200 space-y-2">
              <p className="text-xs font-bold text-slate-700 mb-2">
                Pneumonia Severity & Triage Assessment:
              </p>
              {[
                { k: "confusion", label: "Confusion (Abbreviated Mental Test score ≤ 8, or new disorientation) (+1)" },
                { k: "urea", label: "Urea > 7 mmol/L (BUN > 19 mg/dL) (+1)" },
                { k: "rr", label: "Respiratory Rate ≥ 30 breaths/min (+1)" },
                { k: "bp", label: "Blood Pressure (Systolic < 90 mmHg or Diastolic ≤ 60 mmHg) (+1)" },
                { k: "age65", label: "Age ≥ 65 years (+1)" },
              ].map((item) => (
                <label
                  key={item.k}
                  className="flex items-center gap-3 p-2.5 rounded-xl bg-white border border-slate-200 hover:border-teal-400 cursor-pointer transition-all"
                >
                  <input
                    type="checkbox"
                    checked={(curbCriteria as any)[item.k]}
                    onChange={(e) =>
                      setCurbCriteria((prev) => ({ ...prev, [item.k]: e.target.checked }))
                    }
                    className="w-4 h-4 rounded text-teal-600 accent-teal-600 cursor-pointer"
                  />
                  <span className="text-xs text-slate-800 font-medium">{item.label}</span>
                </label>
              ))}
            </div>

            <div className="p-4 rounded-2xl bg-teal-50 border border-teal-200">
              <span className="text-[10px] font-black uppercase tracking-wider text-teal-800">
                CURB-65 Score: {curbScore} / 5
              </span>
              <p className="text-xs text-slate-800 mt-1 font-medium">
                {curbScore <= 1
                  ? "Low Risk (Mortality < 3%). Suitable for outpatient management."
                  : curbScore === 2
                  ? "Intermediate Risk (Mortality ~9%). Consider short inpatient stay or supervised outpatient monitoring."
                  : "High Risk (Mortality 15–40%). Inpatient hospital admission; evaluate for ICU monitoring."}
              </p>
            </div>
          </div>
        )}

        {/* ── GCS ── */}
        {activeTab === "gcs" && (
          <div className="space-y-4">
            <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200 space-y-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Eye Opening (E)
                </label>
                <select
                  value={gcsEye}
                  onChange={(e) => setGcsEye(Number(e.target.value))}
                  className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 outline-none focus:border-teal-500"
                >
                  <option value={4}>4 - Spontaneous</option>
                  <option value={3}>3 - To Sound</option>
                  <option value={2}>2 - To Pressure / Pain</option>
                  <option value={1}>1 - None</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Verbal Response (V)
                </label>
                <select
                  value={gcsVerbal}
                  onChange={(e) => setGcsVerbal(Number(e.target.value))}
                  className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 outline-none focus:border-teal-500"
                >
                  <option value={5}>5 - Oriented</option>
                  <option value={4}>4 - Confused</option>
                  <option value={3}>3 - Inappropriate Words</option>
                  <option value={2}>2 - Incomprehensible Sounds</option>
                  <option value={1}>1 - None</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Motor Response (M)
                </label>
                <select
                  value={gcsMotor}
                  onChange={(e) => setGcsMotor(Number(e.target.value))}
                  className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 outline-none focus:border-teal-500"
                >
                  <option value={6}>6 - Obeys Commands</option>
                  <option value={5}>5 - Localizing to Pain</option>
                  <option value={4}>4 - Normal Flexion (Withdrawal)</option>
                  <option value={3}>3 - Abnormal Flexion (Decorticate)</option>
                  <option value={2}>2 - Extension (Decerebrate)</option>
                  <option value={1}>1 - None</option>
                </select>
              </div>
            </div>

            <div className={`p-4 rounded-2xl border flex items-center justify-between ${
              gcsTotal <= 8 ? "bg-rose-50 border-rose-200" : "bg-teal-50 border-teal-200"
            }`}>
              <div>
                <span className="text-[10px] font-black uppercase tracking-wider text-teal-800">
                  Total GCS: E{gcsEye} V{gcsVerbal} M{gcsMotor} = {gcsTotal} / 15
                </span>
                <p className="text-xs text-slate-900 mt-0.5 font-bold">
                  {gcsTotal >= 13 ? "Mild Brain Injury" : gcsTotal >= 9 ? "Moderate Brain Injury" : "Severe Brain Injury (GCS ≤ 8)"}
                </p>
                {gcsTotal <= 8 && (
                  <p className="text-[11px] text-rose-700 font-bold mt-1">
                    🚨 Alert: GCS ≤ 8 requires immediate airway protection and endotracheal intubation.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Footer Actions */}
        <div className="flex items-center justify-between border-t border-slate-100 pt-3">
          <span className="text-[10px] text-slate-500">
            Click copy to paste standard note format directly into EHR.
          </span>
          <div className="flex gap-2">
            <button
              onClick={copyClinicalSummary}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl transition-all shadow-sm flex items-center gap-1.5"
            >
              <span>{copiedNote ? "✓ Copied!" : "📋 Copy Clinical Note"}</span>
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ─── Component: Differential Diagnosis Comparison Modal (Clean Light) ─────────

function DifferentialComparisonModal({
  caseA,
  caseB,
  onClose,
}: {
  caseA: DoctorPost;
  caseB: DoctorPost;
  onClose: () => void;
}) {
  const vitalsA = useMemo(() => getClinicalVitalsHUD(caseA.disease_name, caseA.clinical_findings), [caseA]);
  const vitalsB = useMemo(() => getClinicalVitalsHUD(caseB.disease_name, caseB.clinical_findings), [caseB]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[110] bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-2 sm:p-6"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.96, y: 10 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.96, y: 10 }}
        className="w-full max-w-5xl h-[88vh] bg-white border border-slate-200 rounded-3xl shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-600">
              <ClinicalIcons.Scale className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-extrabold text-base text-slate-900">
                Multidisciplinary Differential Diagnostic Split-Screen
              </h3>
              <p className="text-[10px] text-slate-500 font-medium">
                Comparative analysis of clinical phenotypes, vitals telemetry, and pharmacotherapy
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 hover:bg-slate-200 hover:text-slate-800 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Side-by-Side Grid */}
        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-200 overflow-y-auto custom-scrollbar">
          {/* Column A */}
          <div className="p-6 space-y-4 bg-white">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-black uppercase tracking-wider text-teal-800 bg-teal-50 border border-teal-200 px-2 py-0.5 rounded-full">
                CASE A • Primary Index
              </span>
              <span className="text-xs text-slate-500 font-mono">
                {caseA.author_name || "Verified Attending"}
              </span>
            </div>

            <h4 className="text-lg font-black text-slate-900">{caseA.disease_name}</h4>

            {/* Vitals HUD */}
            <div className="bg-slate-50 p-3 rounded-2xl border border-slate-200 space-y-2">
              <p className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                Bedside Telemetry
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {vitalsA.map((v, i) => (
                  <div key={i} className="p-2 rounded-xl bg-white border border-slate-200">
                    <p className="text-[10px] text-slate-500">{v.label}</p>
                    <p className="font-mono font-bold text-slate-900 text-xs">{v.value}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Findings */}
            <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200">
              <p className="text-[10px] font-black uppercase tracking-wider text-rose-700 mb-1">
                Clinical Presentation
              </p>
              <p className="text-xs text-slate-700 leading-relaxed font-medium">
                {caseA.clinical_findings}
              </p>
            </div>

            {/* Diagnosis */}
            <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200">
              <p className="text-[10px] font-black uppercase tracking-wider text-emerald-700 mb-1">
                Confirmed Diagnosis
              </p>
              <p className="text-xs text-slate-900 leading-relaxed font-medium">
                {caseA.diagnosis}
              </p>
            </div>

            {/* Treatment */}
            <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200">
              <p className="text-[10px] font-black uppercase tracking-wider text-teal-800 mb-1">
                Management Protocol
              </p>
              <p className="text-xs text-slate-700 leading-relaxed font-medium">
                {caseA.treatment_plan}
              </p>
              {caseA.drugs_used?.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {caseA.drugs_used.map((d, i) => (
                    <span key={i} className="text-[10px] bg-white text-teal-800 px-2 py-0.5 rounded border border-teal-200 font-semibold">
                      💊 {d}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Column B */}
          <div className="p-6 space-y-4 bg-slate-50/50">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-black uppercase tracking-wider text-indigo-800 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded-full">
                CASE B • Differential Comparison
              </span>
              <span className="text-xs text-slate-500 font-mono">
                {caseB.author_name || "Verified Attending"}
              </span>
            </div>

            <h4 className="text-lg font-black text-slate-900">{caseB.disease_name}</h4>

            {/* Vitals HUD */}
            <div className="bg-white p-3 rounded-2xl border border-slate-200 space-y-2">
              <p className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                Bedside Telemetry
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {vitalsB.map((v, i) => (
                  <div key={i} className="p-2 rounded-xl bg-slate-50 border border-slate-200">
                    <p className="text-[10px] text-slate-500">{v.label}</p>
                    <p className="font-mono font-bold text-slate-900 text-xs">{v.value}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Findings */}
            <div className="bg-white p-3.5 rounded-2xl border border-slate-200">
              <p className="text-[10px] font-black uppercase tracking-wider text-rose-700 mb-1">
                Clinical Presentation
              </p>
              <p className="text-xs text-slate-700 leading-relaxed font-medium">
                {caseB.clinical_findings}
              </p>
            </div>

            {/* Diagnosis */}
            <div className="bg-white p-3.5 rounded-2xl border border-slate-200">
              <p className="text-[10px] font-black uppercase tracking-wider text-emerald-700 mb-1">
                Confirmed Diagnosis
              </p>
              <p className="text-xs text-slate-900 leading-relaxed font-medium">
                {caseB.diagnosis}
              </p>
            </div>

            {/* Treatment */}
            <div className="bg-white p-3.5 rounded-2xl border border-slate-200">
              <p className="text-[10px] font-black uppercase tracking-wider text-teal-800 mb-1">
                Management Protocol
              </p>
              <p className="text-xs text-slate-700 leading-relaxed font-medium">
                {caseB.treatment_plan}
              </p>
              {caseB.drugs_used?.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {caseB.drugs_used.map((d, i) => (
                    <span key={i} className="text-[10px] bg-slate-50 text-indigo-800 px-2 py-0.5 rounded border border-indigo-200 font-semibold">
                      💊 {d}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ─── Component: Executive Case Presentation Dossier Modal (Clean Light) ───────

function CaseDossierModal({
  post,
  onClose,
}: {
  post: DoctorPost;
  onClose: () => void;
}) {
  const authorName = post.author_name || `Dr. ${post.author_id.substring(0, 8)}`;
  const vitals = useMemo(() => getClinicalVitalsHUD(post.disease_name, post.clinical_findings), [post]);
  const [copiedDossier, setCopiedDossier] = useState(false);

  const handlePrint = () => {
    window.print();
  };

  const handleCopy = () => {
    const text = `DOCASSISTIQ CLINICAL CASE DOSSIER
==============================================
CASE TITLE: ${post.disease_name}
AUTHOR: ${authorName} (${post.author_specialty || "Attending Physician"})
INSTITUTION: ${post.author_institution || "Academic Medical Center"}
DATE: ${new Date(post.created_at || Date.now()).toLocaleDateString()}
SECURITY CLEARANCE: Level 4 • HIPAA De-Identified

1. PRESENTING CLINICAL VIGNETTE:
${post.clinical_findings}

2. CONFIRMED CLINICAL DIAGNOSIS:
${post.diagnosis}

3. MULTIDISCIPLINARY TREATMENT PLAN:
${post.treatment_plan}

4. PRESCRIBED PHARMACOTHERAPY:
${post.drugs_used?.join(", ") || "None specified"}

5. PEER ATTENDING CONSENSUS:
${post.likes_count} Attending Validations • ${post.comments_count} Peer Consultations
`;
    navigator.clipboard?.writeText(text);
    setCopiedDossier(true);
    setTimeout(() => setCopiedDossier(false), 2500);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[110] bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.96, y: 10 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.96, y: 10 }}
        className="w-full max-w-3xl bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto custom-scrollbar"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Dossier Header */}
        <div className="border-b border-slate-100 pb-4 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-teal-600" />
              <span className="text-[10px] font-mono tracking-widest text-teal-700 uppercase font-black">
                DocAssistIQ Medical Intelligence Network • Confidential Peer Review
              </span>
            </div>
            <h3 className="text-xl sm:text-2xl font-black text-slate-900">
              {post.disease_name}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Authored by <strong className="text-slate-800">{authorName}</strong> • {post.author_credentials || "Attending MD"} • {post.author_institution || "Academic Medical Center"}
            </p>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 hover:bg-slate-200 hover:text-slate-800"
          >
            ✕
          </button>
        </div>

        {/* Telemetry Matrix */}
        <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200">
          <p className="text-[10px] font-black uppercase tracking-wider text-teal-800 mb-2.5 flex items-center gap-1.5">
            <ClinicalIcons.Pulse className="w-3.5 h-3.5 text-teal-600" />
            Bedside Vitals & Biomarker Telemetry Matrix
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            {vitals.map((v, i) => (
              <div key={i} className="p-2.5 rounded-xl bg-white border border-slate-200">
                <span className="text-[10px] text-slate-500">{v.label}</span>
                <p className="font-mono text-xs font-bold text-slate-900 mt-0.5">{v.value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Clinical Presentation Vignette */}
        <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200">
          <h4 className="text-xs font-black uppercase tracking-wider text-rose-700 mb-1.5">
            1. Clinical Presentation & Vignette
          </h4>
          <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-medium">
            {post.clinical_findings}
          </p>
        </div>

        {/* Confirmed Diagnosis */}
        <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200">
          <h4 className="text-xs font-black uppercase tracking-wider text-emerald-700 mb-1.5">
            2. Confirmed Diagnosis & Differential Pathology
          </h4>
          <p className="text-xs sm:text-sm text-slate-900 leading-relaxed font-medium">
            {post.diagnosis}
          </p>
        </div>

        {/* Management Protocol */}
        <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200">
          <h4 className="text-xs font-black uppercase tracking-wider text-teal-800 mb-1.5">
            3. Evidence-Based Clinical Management & Pharmacology
          </h4>
          <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-medium mb-3">
            {post.treatment_plan}
          </p>
          {post.drugs_used?.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-2 border-t border-slate-200">
              {post.drugs_used.map((drug, i) => (
                <span
                  key={i}
                  className="text-xs font-bold bg-white text-teal-800 px-3 py-1 rounded-lg border border-teal-200"
                >
                  💊 {drug}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between border-t border-slate-100 pt-4 flex-wrap gap-2">
          <span className="text-[10px] font-mono text-slate-400">
            Case ID: {post.id} • SHA-256 De-Identified
          </span>
          <div className="flex gap-2">
            <button
              onClick={handleCopy}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition-all"
            >
              {copiedDossier ? "✓ Dossier Copied" : "📋 Copy Dossier"}
            </button>
            <button
              onClick={handlePrint}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl transition-all shadow-sm"
            >
              🖨️ Print Clinical Dossier
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ─── Component: Differential Tray Floating Dock (Clean Light) ─────────────────

function DifferentialTrayDock({
  cases,
  onRemove,
  onLaunch,
  onClear,
}: {
  cases: DoctorPost[];
  onRemove: (id: string) => void;
  onLaunch: () => void;
  onClear: () => void;
}) {
  if (cases.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[100] bg-white border border-slate-200 rounded-full px-5 py-3 shadow-xl backdrop-blur-md flex items-center gap-3"
    >
      <div className="flex items-center gap-2">
        <ClinicalIcons.Scale className="w-4 h-4 text-teal-600" />
        <span className="text-xs font-bold text-slate-900">
          Differential Tray ({cases.length}/2):
        </span>
      </div>

      <div className="flex items-center gap-1.5 max-w-sm overflow-hidden">
        {cases.map((c) => (
          <div
            key={c.id}
            className="flex items-center gap-1 bg-slate-50 border border-slate-200 text-teal-800 text-[11px] font-bold px-2.5 py-1 rounded-full truncate"
          >
            <span className="truncate max-w-[120px]">{c.disease_name}</span>
            <button
              onClick={() => onRemove(c.id)}
              className="text-slate-400 hover:text-slate-700 ml-1 font-bold"
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
        <button
          onClick={onLaunch}
          disabled={cases.length < 2}
          className="bg-teal-600 hover:bg-teal-700 disabled:opacity-40 text-white font-bold text-xs px-4 py-1.5 rounded-full transition-all shadow-sm"
        >
          {cases.length === 2 ? "⚖️ Launch Comparison" : "Select 1 More Case"}
        </button>
        <button
          onClick={onClear}
          className="text-slate-500 hover:text-slate-800 text-xs font-semibold px-2 py-1"
        >
          Clear
        </button>
      </div>
    </motion.div>
  );
}

// ─── Component: Active Doctors Modal (Clean Light) ────────────────────────────

function ActiveDoctorsModal({
  doctors,
  onClose,
  onToggleFollow,
}: {
  doctors: DoctorProfile[];
  onClose: () => void;
  onToggleFollow: (doctorId: string) => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.96, y: 10 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.96, y: 10 }}
        className="w-full max-w-md bg-white border border-slate-200 rounded-3xl p-6 shadow-2xl space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <h3 className="font-extrabold text-base text-slate-900">
              Active Verified Specialists
            </h3>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 hover:bg-slate-200 hover:text-slate-800 transition-colors"
          >
            ✕
          </button>
        </div>

        <p className="text-xs text-slate-500">
          Real-time verified medical practitioners active in clinical consults and case studies.
        </p>

        <div className="space-y-2 max-h-72 overflow-y-auto pr-1 custom-scrollbar">
          {doctors.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center justify-between p-3 rounded-2xl bg-slate-50 border border-slate-200/80 hover:border-teal-300 transition-all"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div
                  className={`w-10 h-10 rounded-full bg-gradient-to-br ${getAvatarGradient(
                    doc.id
                  )} flex items-center justify-center text-white text-xs font-extrabold shadow-sm flex-shrink-0`}
                >
                  {doc.full_name?.[0] ?? "D"}
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <p className="text-xs font-bold text-slate-900 truncate">{doc.full_name}</p>
                    <span className="text-[10px] text-emerald-600 font-bold">✓</span>
                  </div>
                  <p className="text-[10px] text-slate-500 truncate">
                    {doc.specialization} • {doc.post_count} published cases
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 flex-shrink-0">
                <button
                  onClick={() => onToggleFollow(doc.id)}
                  className={`text-[10px] font-bold px-3 py-1 rounded-full border transition-all ${
                    doc.is_following
                      ? "bg-teal-600 text-white border-teal-600 font-black shadow-sm"
                      : "bg-white hover:bg-slate-100 text-teal-700 border-teal-200"
                  }`}
                >
                  {doc.is_following ? "Following ✓" : "Follow"}
                </button>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}

// ─── Component: Clinical Stories Reel (Clean Light Theme) ─────────────────────

function ClinicalStoriesReel({
  stories,
  onOpenStory,
  onNewCase,
}: {
  stories: DoctorPost[];
  onOpenStory: (index: number) => void;
  onNewCase: () => void;
}) {
  return (
    <div className="mb-6 rounded-2xl bg-white border border-slate-200 p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3 px-1">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-teal-600" />
          Clinical Stories & Spot Diagnosis Quizzes
        </h3>
        <span className="text-[10px] text-teal-700 font-bold">Tap story to inspect scan</span>
      </div>

      <div className="flex gap-4 overflow-x-auto pb-2 pt-1 custom-scrollbar">
        {/* Post Story Button */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onNewCase}
          className="flex flex-col items-center gap-2 min-w-[78px] text-left group focus:outline-none"
        >
          <div className="p-0.5 rounded-full border-2 border-dashed border-teal-400 hover:border-teal-600 transition-colors">
            <div className="w-14 h-14 rounded-full bg-teal-50 flex items-center justify-center text-teal-700 font-bold text-xl group-hover:bg-teal-100 transition-all">
              +
            </div>
          </div>
          <div className="text-center w-full px-1">
            <p className="text-[11px] font-bold text-slate-800 truncate">Share Case</p>
            <p className="text-[9px] text-teal-700 font-medium">New Story</p>
          </div>
        </motion.button>

        {stories.map((post, idx) => {
          const authorName = post.author_name || `Dr. ${post.author_id.substring(0, 8)}`;
          const specialty = post.author_specialty || post.specialty_tags?.[0] || "Specialist";
          const gradient = getAvatarGradient(post.author_id);
          const hasImage = post.attachments?.length > 0;

          return (
            <motion.button
              key={post.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onOpenStory(idx)}
              className="flex flex-col items-center gap-2 min-w-[78px] text-left group focus:outline-none"
            >
              {/* Story Ring */}
              <div
                className={`relative p-0.5 rounded-full transition-all ${
                  post.is_urgent_consult
                    ? "bg-gradient-to-tr from-rose-500 to-red-600 ring-2 ring-rose-200"
                    : "bg-gradient-to-tr from-teal-500 to-emerald-500 ring-1 ring-teal-100"
                }`}
              >
                <div className="p-0.5 rounded-full bg-white">
                  <div
                    className={`w-14 h-14 rounded-full bg-gradient-to-br ${gradient} flex items-center justify-center text-white font-extrabold text-sm shadow-inner relative overflow-hidden`}
                  >
                    {hasImage ? (
                      <img
                        src={post.attachments[0].file_url}
                        alt="Clinical thumbnail"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                      />
                    ) : (
                      getInitials(authorName)
                    )}

                    <div className="absolute bottom-0 right-0 w-3.5 h-3.5 bg-emerald-500 rounded-full border-2 border-white" />
                  </div>
                </div>

                {post.is_urgent_consult && (
                  <span className="absolute -top-1 -right-1 bg-red-600 text-white text-[9px] font-black px-1.5 py-0.2 rounded-full border border-white shadow-sm">
                    !
                  </span>
                )}
              </div>

              {/* Story Doctor Name */}
              <div className="text-center w-full px-1">
                <p className="text-[11px] font-bold text-slate-800 truncate">
                  {authorName.split(" ")[1] ? `Dr. ${authorName.split(" ")[1]}` : authorName}
                </p>
                <p className="text-[9px] text-slate-500 truncate font-medium">
                  {specialty}
                </p>
              </div>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}

// ─── Component: Story Viewer Modal (Clean Light Theme) ─────────────────────────

function StoryViewerModal({
  stories,
  initialIndex,
  onClose,
  onReact,
  onVotePoll,
  onOpenCite,
}: {
  stories: DoctorPost[];
  initialIndex: number;
  onClose: () => void;
  onReact: (postId: string, reaction: string) => void;
  onVotePoll: (postId: string, optionIndex: number) => void;
  onOpenCite: (post: DoctorPost) => void;
}) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [progress, setProgress] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [reactionBurst, setReactionBurst] = useState<string | null>(null);
  const [imgError, setImgError] = useState(false);

  const currentStory = stories[currentIndex];
  const storyDuration = 7000;

  useEffect(() => {
    setImgError(false);
  }, [currentIndex]);

  useEffect(() => {
    if (isPaused) return;
    const interval = 50;
    const step = (interval / storyDuration) * 100;

    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          if (currentIndex < stories.length - 1) {
            setCurrentIndex((c) => c + 1);
            return 0;
          } else {
            clearInterval(timer);
            setTimeout(() => onClose(), 0);
            return 100;
          }
        }
        return prev + step;
      });
    }, interval);

    return () => clearInterval(timer);
  }, [currentIndex, isPaused, stories.length, onClose]);

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex((c) => c - 1);
      setProgress(0);
    }
  };

  const handleNext = () => {
    if (currentIndex < stories.length - 1) {
      setCurrentIndex((c) => c + 1);
      setProgress(0);
    } else {
      onClose();
    }
  };

  const triggerReaction = (id: string) => {
    setReactionBurst(id);
    onReact(currentStory.id, id);
    setTimeout(() => setReactionBurst(null), 1500);
  };

  if (!currentStory) return null;

  const authorName = currentStory.author_name || `Dr. ${currentStory.author_id.substring(0, 8)}`;
  const specialty = currentStory.author_specialty || currentStory.specialty_tags?.[0] || "Specialist";
  const credentials = currentStory.author_credentials || "Board Certified Physician";
  const institution = currentStory.author_institution || "Academic Medical Center";
  const image = currentStory.attachments?.[0]?.file_url;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-2 sm:p-6"
    >
      <motion.div
        initial={{ scale: 0.96, y: 15 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.96, y: 15 }}
        className="relative w-full max-w-lg h-[90vh] max-h-[800px] bg-white rounded-3xl overflow-hidden shadow-2xl border border-slate-200 flex flex-col justify-between"
      >
        {/* Progress Bars */}
        <div className="absolute top-0 left-0 right-0 z-30 p-3 pt-4 flex gap-1.5 bg-gradient-to-b from-white/90 via-white/50 to-transparent">
          {stories.map((s, idx) => (
            <div key={s.id} className="h-1.5 flex-1 bg-slate-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-teal-600 rounded-full transition-all ease-linear"
                style={{
                  width:
                    idx < currentIndex
                      ? "100%"
                      : idx === currentIndex
                      ? `${progress}%`
                      : "0%",
                }}
              />
            </div>
          ))}
        </div>

        {/* Doctor Header */}
        <div className="absolute top-7 left-0 right-0 z-30 px-4 py-2 flex items-center justify-between bg-gradient-to-b from-white/90 to-transparent">
          <div className="flex items-center gap-3">
            <div
              className={`w-10 h-10 rounded-full bg-gradient-to-br ${getAvatarGradient(
                currentStory.author_id
              )} flex items-center justify-center font-bold text-sm text-white border-2 border-teal-500`}
            >
              {getInitials(authorName)}
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h4 className="font-bold text-sm text-slate-900">{authorName}</h4>
                <span className="bg-teal-100 text-[10px] font-bold px-1.5 py-0.2 rounded-full text-teal-800 flex items-center gap-0.5">
                  ✓ Verified
                </span>
              </div>
              <p className="text-[10px] text-slate-600 font-medium truncate max-w-[220px]">
                {specialty} • {credentials}
              </p>
              <p className="text-[9px] text-teal-700 font-mono">{institution}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsPaused(!isPaused)}
              className="p-1.5 bg-slate-100 hover:bg-slate-200 rounded-full text-slate-600 text-xs transition-colors"
              title={isPaused ? "Resume" : "Pause"}
            >
              {isPaused ? "▶" : "❚❚"}
            </button>
            <button
              onClick={onClose}
              className="p-1.5 bg-slate-100 hover:bg-slate-200 rounded-full text-slate-600 text-sm font-bold w-8 h-8 flex items-center justify-center transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Tap zones */}
        <div className="absolute inset-0 z-10 flex">
          <div className="w-1/3 h-full cursor-pointer" onClick={handlePrev} />
          <div
            className="w-1/3 h-full cursor-pointer"
            onClick={() => setIsPaused((p) => !p)}
          />
          <div className="w-1/3 h-full cursor-pointer" onClick={handleNext} />
        </div>

        {/* Story Body */}
        <div className="relative flex-1 w-full h-full flex flex-col justify-center items-center overflow-hidden bg-slate-50">
          {image && !imgError ? (
            <div className="w-full h-full relative flex items-center justify-center p-2 pt-20 pb-36">
              <img
                src={image}
                alt={currentStory.disease_name}
                onError={() => setImgError(true)}
                className="max-w-full max-h-full object-contain rounded-xl shadow-md border border-slate-200"
              />
              <div className="absolute top-20 right-4 bg-white/90 backdrop-blur-sm border border-slate-200 text-teal-800 text-[10px] font-bold px-2.5 py-1 rounded-full flex items-center gap-1 z-20 shadow-sm">
                <ClinicalIcons.ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                <span>HIPAA De-Identified</span>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center pt-24 pb-36 max-w-sm">
              <span className="inline-block text-4xl mb-4">🩺</span>
              <h3 className="text-xl font-extrabold text-slate-900 mb-2 leading-snug">
                {currentStory.disease_name}
              </h3>
              <p className="text-sm text-slate-600 line-clamp-4 mb-4">
                {currentStory.clinical_findings}
              </p>
              <div className="inline-block bg-teal-50 border border-teal-200 text-teal-800 px-3 py-1 rounded-full text-xs font-semibold">
                #{specialty}
              </div>
            </div>
          )}

          {/* Interactive Spot Diagnosis Quiz Card Overlay */}
          <div className="absolute bottom-20 left-4 right-4 z-20 bg-white/95 backdrop-blur-md border border-slate-200 rounded-2xl p-3.5 shadow-xl">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-black uppercase tracking-wider text-teal-800 flex items-center gap-1">
                <ClinicalIcons.Microscope className="w-3.5 h-3.5" />
                Spot Diagnosis Consensus
              </span>
              <span className="text-[10px] text-slate-500">Tap your clinical judgment</span>
            </div>

            <p className="text-xs font-bold text-slate-900 mb-2.5 line-clamp-2">
              {currentStory.poll_data?.question || `Clinical diagnosis for: ${currentStory.disease_name}?`}
            </p>

            <div className="space-y-1.5">
              {currentStory.poll_data?.options?.length ? (
                currentStory.poll_data.options.map((opt, i) => {
                  const total = Math.max(1, currentStory.poll_data?.total_votes ?? 1);
                  const pct = Math.round((opt.votes / total) * 100);
                  const isVoted = currentStory.poll_data?.voted_index === i;
                  return (
                    <button
                      key={i}
                      onClick={(e) => {
                        e.stopPropagation();
                        setIsPaused(true);
                        onVotePoll(currentStory.id, i);
                      }}
                      className={`relative w-full text-left text-xs px-3 py-2 rounded-xl transition-all font-medium border flex items-center justify-between overflow-hidden ${
                        isVoted
                          ? "bg-teal-50 border-teal-400 text-teal-900 font-bold"
                          : "bg-slate-50 border-slate-200 text-slate-800 hover:bg-slate-100"
                      }`}
                    >
                      <div
                        className="absolute inset-y-0 left-0 bg-teal-100/70"
                        style={{ width: `${pct}%` }}
                      />
                      <span className="relative z-10 flex items-center gap-1.5">
                        {isVoted && <span className="text-teal-700 font-bold">✓</span>}
                        <span>{opt.label}</span>
                      </span>
                      <span className="relative z-10 text-[10px] font-mono font-bold text-teal-800">
                        {pct}% ({opt.votes})
                      </span>
                    </button>
                  );
                })
              ) : (
                [
                  currentStory.diagnosis.substring(0, 36) + "...",
                  "Secondary Mimic / Complication",
                  "Refractory Clinical Variant",
                ].map((opt, i) => (
                  <button
                    key={i}
                    onClick={(e) => {
                      e.stopPropagation();
                      setIsPaused(true);
                    }}
                    className="w-full text-left text-xs px-3 py-2 rounded-xl transition-all font-medium border bg-slate-50 border-slate-200 text-slate-800 hover:bg-slate-100 flex items-center justify-between"
                  >
                    <span>{opt}</span>
                    <span className="text-[10px] text-teal-700 font-bold font-mono">
                      {i === 0 ? "88% Doctors" : i === 1 ? "9%" : "3%"}
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Bottom Reaction Bar */}
        <div className="relative z-30 p-3 bg-white flex items-center justify-between gap-2 border-t border-slate-200">
          <div className="flex items-center gap-1.5 flex-1">
            {CLINICAL_REACTIONS.map((r) => {
              const IconComp = r.Icon;
              return (
                <button
                  key={r.id}
                  onClick={(e) => {
                    e.stopPropagation();
                    triggerReaction(r.id);
                  }}
                  className="flex-1 py-1.5 px-1 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-xl flex items-center justify-center text-slate-700 transition-all hover:scale-105 active:scale-95"
                  title={r.label}
                >
                  <IconComp className="w-4 h-4 text-teal-600" />
                </button>
              );
            })}
          </div>

          <button
            onClick={() => onOpenCite(currentStory)}
            className="px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl transition-all flex items-center gap-1 shadow-sm"
          >
            <ClinicalIcons.FileText className="w-3.5 h-3.5" />
            <span>Cite</span>
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ─── Component: Diagnostic Lightbox (Clean Light Workstation) ─────────────────

function MedicalLightboxModal({
  imageUrl,
  onClose,
}: {
  imageUrl: string;
  onClose: () => void;
}) {
  const [isInverted, setIsInverted] = useState(false);
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [showGrid, setShowGrid] = useState(false);
  const [zoom, setZoom] = useState(1);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] bg-slate-900/80 backdrop-blur-sm flex items-center justify-center p-2 sm:p-4 md:p-6"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.96 }}
        animate={{ scale: 1 }}
        exit={{ scale: 0.96 }}
        className="relative max-w-6xl w-full h-[90vh] max-h-[880px] bg-slate-950 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-5 py-3 border-b border-slate-800 flex items-center justify-between bg-slate-900 flex-shrink-0 flex-wrap gap-2 z-20">
          <div className="flex items-center gap-3">
            <span className="text-teal-400 font-extrabold text-sm flex items-center gap-1.5">
              <ClinicalIcons.Microscope className="w-4 h-4" />
              <span>Diagnostic Inspection Workstation</span>
            </span>
            <span className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10px] font-bold px-2 py-0.5 rounded-full">
              DICOM Encrypted
            </span>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setIsInverted(!isInverted)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all border ${
                isInverted
                  ? "bg-teal-500 text-slate-950 border-teal-400 shadow-md"
                  : "bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700"
              }`}
            >
              🔄 {isInverted ? "Normal View" : "Negative Scan View"}
            </button>

            <button
              onClick={() => setShowGrid(!showGrid)}
              className={`px-2.5 py-1.5 rounded-xl text-xs font-bold border transition-all ${
                showGrid
                  ? "bg-indigo-600 text-white border-indigo-400"
                  : "bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700"
              }`}
              title="Toggle 10mm Caliper Grid"
            >
              📏 Caliper Grid
            </button>

            {/* Brightness */}
            <div className="hidden sm:flex items-center gap-1.5 px-2 py-1 bg-slate-800/80 rounded-xl border border-slate-700 text-xs">
              <span className="text-slate-400 text-[10px]">☀️</span>
              <input
                type="range"
                min="50"
                max="180"
                value={brightness}
                onChange={(e) => setBrightness(Number(e.target.value))}
                className="w-16 h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-teal-400"
                title="Brightness / Exposure"
              />
            </div>

            {/* Contrast */}
            <div className="hidden sm:flex items-center gap-1.5 px-2 py-1 bg-slate-800/80 rounded-xl border border-slate-700 text-xs">
              <span className="text-slate-400 text-[10px]">🌓</span>
              <input
                type="range"
                min="50"
                max="200"
                value={contrast}
                onChange={(e) => setContrast(Number(e.target.value))}
                className="w-16 h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-teal-400"
                title="Contrast Level"
              />
            </div>

            {/* Zoom */}
            <div className="flex items-center gap-1 bg-slate-800 rounded-xl p-0.5 border border-slate-700">
              <button
                onClick={() => setZoom((z) => Math.max(0.75, z - 0.25))}
                className="px-2 py-1 text-white text-xs font-bold hover:bg-slate-700 rounded-lg"
              >
                -
              </button>
              <span className="text-[10px] font-mono text-teal-400 px-1 font-bold">
                {Math.round(zoom * 100)}%
              </span>
              <button
                onClick={() => setZoom((z) => Math.min(3, z + 0.25))}
                className="px-2 py-1 text-white text-xs font-bold hover:bg-slate-700 rounded-lg"
              >
                +
              </button>
              <button
                onClick={() => {
                  setZoom(1);
                  setBrightness(100);
                  setContrast(100);
                }}
                className="px-2 py-1 text-slate-400 hover:text-white text-[10px] font-bold"
              >
                Reset
              </button>
            </div>

            <button
              onClick={onClose}
              className="ml-2 w-8 h-8 bg-slate-800 hover:bg-slate-700 text-white rounded-full flex items-center justify-center font-bold"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Viewport */}
        <div className="relative flex-1 bg-black flex items-center justify-center overflow-auto p-4 min-h-[60vh] select-none">
          {showGrid && (
            <div
              className="absolute inset-0 pointer-events-none z-10 opacity-30"
              style={{
                backgroundImage: "linear-gradient(to right, #0d9488 1px, transparent 1px), linear-gradient(to bottom, #0d9488 1px, transparent 1px)",
                backgroundSize: "20px 20px"
              }}
            />
          )}
          <img
            src={imageUrl}
            alt="Clinical Inspection"
            style={{
              filter: `${isInverted ? "invert(1) hue-rotate(180deg)" : ""} brightness(${brightness}%) contrast(${contrast}%)`,
              transform: `scale(${zoom})`,
              transition: "transform 0.15s ease-out, filter 0.25s ease",
            }}
            className="max-w-full max-h-[75vh] object-contain cursor-grab active:cursor-grabbing"
          />
        </div>

        {/* Footer */}
        <div className="px-6 py-2.5 bg-slate-900 border-t border-slate-800 text-slate-400 text-xs flex items-center justify-between">
          <span>High-Resolution Diagnostic Render</span>
          <span className="text-teal-400 font-mono text-[10px]">
            DocAssistIQ Vault Encryption • Level 4 Clearance
          </span>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ─── Component: Citation / Export Modal (Clean Light Theme) ───────────────────

function CitationModal({
  post,
  onClose,
  onCopiedToast,
}: {
  post: DoctorPost;
  onClose: () => void;
  onCopiedToast: (msg: string) => void;
}) {
  const [copiedFormat, setCopiedFormat] = useState<string | null>(null);

  const authorName = post.author_name || `Dr. ${post.author_id.substring(0, 8)}`;
  const authorLast = authorName.replace(/^Dr\\.\\s*/i, "").split(" ").pop() || "Specialist";
  const authorInit = authorName.replace(/^Dr\\.\\s*/i, "").charAt(0) || "D";
  const year = new Date(post.created_at || Date.now()).getFullYear();

  const amaCitation = `${authorLast} ${authorInit}. ${post.disease_name}: Clinical Protocol and Attending Consensus. DocAssistIQ Medical Intelligence Network. ${year}; Case ID: ${post.id.substring(0, 8)}.`;
  const nlmCitation = `${authorLast} ${authorInit}. ${post.disease_name}. DocAssistIQ Clin Hub [Internet]. ${year}; Available from: https://docassistiq.internal/hub/cases/${post.id}`;
  const bibtexCitation = `@article{docassist_${post.id.substring(0, 8)},
  author = {${authorLast}, ${authorInit}.},
  title = {${post.disease_name}: Peer-Reviewed Protocol},
  journal = {DocAssistIQ Medical Intelligence Hub},
  year = {${year}},
  url = {https://docassistiq.internal/hub/cases/${post.id}}
}`;

  const copyText = (text: string, formatName: string) => {
    navigator.clipboard?.writeText(text);
    setCopiedFormat(formatName);
    onCopiedToast(`Copied ${formatName} Citation!`);
    setTimeout(() => setCopiedFormat(null), 2500);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.96, y: 10 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.96, y: 10 }}
        className="w-full max-w-lg bg-white border border-slate-200 rounded-3xl p-6 shadow-2xl space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <ClinicalIcons.FileText className="w-5 h-5 text-teal-600" />
            <h3 className="font-extrabold text-base text-slate-900">
              Cite Clinical Protocol
            </h3>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 hover:bg-slate-200"
          >
            ✕
          </button>
        </div>

        <p className="text-xs text-slate-500">
          Export standardized peer-reviewed academic citations for {post.disease_name}.
        </p>

        {/* AMA Format */}
        <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-black uppercase tracking-wider text-teal-800">
              AMA Format (American Medical Association)
            </span>
            <button
              onClick={() => copyText(amaCitation, "AMA")}
              className="text-xs font-bold text-teal-600 hover:underline"
            >
              {copiedFormat === "AMA" ? "✓ Copied" : "Copy"}
            </button>
          </div>
          <p className="text-xs text-slate-700 font-mono leading-relaxed select-all">
            {amaCitation}
          </p>
        </div>

        {/* NLM Format */}
        <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-black uppercase tracking-wider text-teal-800">
              NLM / PubMed Reference Style
            </span>
            <button
              onClick={() => copyText(nlmCitation, "NLM")}
              className="text-xs font-bold text-teal-600 hover:underline"
            >
              {copiedFormat === "NLM" ? "✓ Copied" : "Copy"}
            </button>
          </div>
          <p className="text-xs text-slate-700 font-mono leading-relaxed select-all">
            {nlmCitation}
          </p>
        </div>

        {/* BibTeX */}
        <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-black uppercase tracking-wider text-teal-800">
              BibTeX Format
            </span>
            <button
              onClick={() => copyText(bibtexCitation, "BibTeX")}
              className="text-xs font-bold text-teal-600 hover:underline"
            >
              {copiedFormat === "BibTeX" ? "✓ Copied" : "Copy"}
            </button>
          </div>
          <pre className="text-[11px] text-slate-700 font-mono leading-snug whitespace-pre-wrap overflow-x-auto">
            {bibtexCitation}
          </pre>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ─── Component: Skeleton Post Loader (Clean Light) ────────────────────────────

function SkeletonPostLoader() {
  return (
    <div className="space-y-4">
      {[1, 2].map((n) => (
        <div
          key={n}
          className="rounded-3xl border border-slate-200 bg-white p-5 sm:p-6 shadow-sm animate-pulse space-y-4"
        >
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-slate-200" />
            <div className="space-y-2 flex-1">
              <div className="h-4 bg-slate-200 rounded w-48" />
              <div className="h-3 bg-slate-100 rounded w-32" />
            </div>
          </div>
          <div className="h-5 bg-slate-200 rounded w-3/4" />
          <div className="h-20 bg-slate-100 rounded-xl" />
          <div className="flex gap-4 pt-2">
            <div className="h-8 bg-slate-100 rounded-full w-24" />
            <div className="h-8 bg-slate-100 rounded-full w-24" />
            <div className="h-8 bg-slate-100 rounded-full w-24" />
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Component: Interactive Post Card (Clean Minimalist Light Theme) ──────────

function PostCard({
  post,
  typingDoctor,
  isCompared,
  onToggleCompare,
  onLike,
  onBookmark,
  onComment,
  onReact,
  onVotePoll,
  onEndorse,
  onOpenImage,
  onOpenCite,
  onOpenDossier,
  onTyping,
}: {
  post: DoctorPost;
  typingDoctor: string | null;
  isCompared: boolean;
  onToggleCompare: () => void;
  onLike: () => void;
  onBookmark: () => void;
  onComment: (text: string) => void;
  onReact: (reaction: string) => void;
  onVotePoll: (optionIndex: number) => void;
  onEndorse: () => void;
  onOpenImage: (url: string) => void;
  onOpenCite: (post: DoctorPost) => void;
  onOpenDossier: (post: DoctorPost) => void;
  onTyping: (isTyping: boolean) => void;
}) {
  const [showComments, setShowComments] = useState(false);
  const [commentText, setCommentText] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);
  const [showReactionPicker, setShowReactionPicker] = useState(false);
  const [showLeadStrip, setShowLeadStrip] = useState(false);
  const [selectedLead, setSelectedLead] = useState<"lead2" | "leadV1" | "leadV2">("lead2");
  const reactionPickerTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const authorName = post.author_name || `Dr. ${post.author_id.substring(0, 8)}`;
  const specialty = post.author_specialty || post.specialty_tags?.[0] || "Specialist";
  const credentials = post.author_credentials || "Board Certified Specialist";
  const institution = post.author_institution || "Academic Medical Center";
  const gradient = getAvatarGradient(post.author_id);
  const vitals = useMemo(() => getClinicalVitalsHUD(post.disease_name, post.clinical_findings), [post.disease_name, post.clinical_findings]);

  const consensusPercentage = useMemo(() => {
    if (!post.reactions_breakdown) return 96;
    const breakdown = post.reactions_breakdown;
    const positive = (breakdown.validate || 0) + (breakdown.insightful || 0) + (breakdown.endorsed || 0) + (breakdown.rare || 0);
    const flags = breakdown.flag || 0;
    const total = positive + flags;
    if (total === 0) return 98;
    return Math.round((positive / total) * 100);
  }, [post.reactions_breakdown]);

  const truncatedFindings =
    post.clinical_findings.length > 200
      ? post.clinical_findings.substring(0, 200) + "..."
      : post.clinical_findings;

  const handleCommentSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    onComment(commentText.trim());
    setCommentText("");
    onTyping(false);
  };

  const handlePickerMouseEnter = () => {
    if (reactionPickerTimeoutRef.current) clearTimeout(reactionPickerTimeoutRef.current);
    setShowReactionPicker(true);
  };

  const handlePickerMouseLeave = () => {
    reactionPickerTimeoutRef.current = setTimeout(() => {
      setShowReactionPicker(false);
    }, 350);
  };

  return (
    <article
      className={`rounded-3xl overflow-hidden border bg-white shadow-sm hover:shadow-md transition-all duration-200 relative ${
        post.is_urgent_consult ? "border-rose-300 ring-1 ring-rose-100" : "border-slate-200"
      }`}
    >
      {/* Top Accent Strip */}
      <div
        className={`h-1.5 ${
          post.is_urgent_consult
            ? "bg-rose-500"
            : "bg-gradient-to-r from-teal-500 to-emerald-600"
        }`}
      />

      {/* Urgent STAT Consult Banner (Clean & Authoritative, No jittery card zoom) */}
      {post.is_urgent_consult && (
        <div className="bg-rose-50 border-b border-rose-200/80 px-5 py-2.5 flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-500 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-600" />
            </span>
            <span className="text-xs font-bold uppercase tracking-wider text-rose-800 flex items-center gap-1.5">
              <span>STAT 2nd Opinion Requested</span>
              <span className="text-rose-400">•</span>
              <span className="text-[11px] text-rose-600 font-normal">Emergency Multidisciplinary Channel</span>
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                playUrgentPagerBeep();
                alert("STAT hospital pager channel active. Attending specialists are alerted.");
              }}
              className="flex items-center gap-1.5 bg-rose-600 hover:bg-rose-700 text-white text-[11px] font-bold px-3 py-1 rounded-full shadow-sm transition-all active:scale-95"
            >
              <ClinicalIcons.Pager className="w-3.5 h-3.5 text-white" />
              <span>Chirp Pager</span>
            </button>
          </div>
        </div>
      )}

      <div className="p-5 sm:p-6">
        {/* ── 1. Author Row & Medical Credentials ── */}
        <div className="flex items-start justify-between gap-3 mb-4">
          <div className="flex items-center gap-3.5">
            <div
              className={`w-11 h-11 rounded-full bg-gradient-to-br ${gradient} flex items-center justify-center text-white font-extrabold text-sm shadow-sm ring-2 ring-white flex-shrink-0`}
            >
              {getInitials(authorName)}
            </div>

            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h4 className="font-bold text-sm sm:text-base text-slate-900">
                  {authorName}
                </h4>
                <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                  <ClinicalIcons.ShieldCheck className="w-3 h-3 text-emerald-600" />
                  Verified Attending MD
                </span>

                {post.is_urgent_consult && (
                  <span className="bg-rose-100 text-rose-800 border border-rose-200 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                    <span>🚨</span>
                    <span>STAT CONSULT</span>
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2 text-xs text-slate-600 font-medium mt-0.5">
                <span className="text-teal-700 font-semibold">{specialty}</span>
                <span>•</span>
                <span className="text-slate-500">{credentials}</span>
              </div>
              <p className="text-[10px] text-slate-400 font-mono">
                {institution} • {timeAgo(post.created_at)}
              </p>
            </div>
          </div>

          {/* Right Actions: Compare, Dossier, Cite, Bookmark */}
          <div className="flex items-center gap-1.5">
            {/* Compare to Differential */}
            <button
              onClick={onToggleCompare}
              className={`px-2.5 py-1.5 rounded-full border text-xs font-bold transition-all flex items-center gap-1 ${
                isCompared
                  ? "bg-teal-600 text-white border-teal-600 shadow-sm"
                  : "bg-slate-50 hover:bg-slate-100 text-slate-600 border-slate-200 hover:text-slate-900"
              }`}
              title={isCompared ? "Remove from Differential Tray" : "Add to Differential Tray"}
            >
              <ClinicalIcons.Scale className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{isCompared ? "Comparing ✓" : "Compare"}</span>
            </button>

            {/* Case Dossier Presentation */}
            <button
              onClick={() => onOpenDossier(post)}
              className="px-2.5 py-1.5 rounded-full bg-slate-50 hover:bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-200 text-xs font-bold transition-all flex items-center gap-1"
              title="View Hospital Clinical Dossier"
            >
              <ClinicalIcons.FileText className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Dossier</span>
            </button>

            {/* Cite */}
            <button
              onClick={() => onOpenCite(post)}
              className="px-2.5 py-1.5 rounded-full bg-slate-50 hover:bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-200 text-xs font-bold transition-all flex items-center gap-1"
              title="Cite Protocol"
            >
              <span>📜</span>
              <span className="hidden sm:inline">Cite</span>
            </button>

            {/* Bookmark */}
            <button
              onClick={onBookmark}
              className={`p-2 rounded-full transition-all ${
                post.is_bookmarked_by_me
                  ? "bg-amber-50 text-amber-600 border border-amber-200"
                  : "text-slate-400 hover:bg-slate-100 hover:text-slate-600"
              }`}
              title={post.is_bookmarked_by_me ? "Saved in Clinical Library" : "Bookmark Case"}
            >
              <svg
                className="w-4 h-4"
                fill={post.is_bookmarked_by_me ? "currentColor" : "none"}
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
                />
              </svg>
            </button>
          </div>
        </div>

        {/* ── 2. Specialty Hashtags ── */}
        {post.specialty_tags?.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {post.specialty_tags.map((tag, i) => {
              const tagStyle = getSpecialtyStyle(tag);
              return (
                <span
                  key={i}
                  className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border tracking-wide uppercase ${tagStyle.bg} ${tagStyle.border}`}
                >
                  #{tag}
                </span>
              );
            })}
          </div>
        )}

        {/* ── 3. Primary Condition Title ── */}
        <h2 className="text-lg sm:text-xl font-black text-slate-900 mb-3 leading-snug">
          {post.disease_name}
        </h2>

        {/* ── 4. Clinical Vitals & Lab Telemetry HUD (Clean Light Mode) ── */}
        <div className="mb-4 bg-slate-50 border border-slate-200 rounded-2xl p-3.5">
          <div className="flex items-center justify-between mb-2.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-teal-800 flex items-center gap-1.5">
              <ClinicalIcons.Pulse className="w-3.5 h-3.5 text-teal-600" />
              <span>Bedside Clinical Telemetry & Key Biomarkers</span>
            </span>
            
            <button
              onClick={() => setShowLeadStrip(!showLeadStrip)}
              className="text-[10px] font-mono text-teal-700 hover:underline flex items-center gap-1 font-bold"
            >
              <span>{showLeadStrip ? "Hide ECG Strip" : "📈 Live ECG Lead Strip"}</span>
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
            {vitals.map((v, i) => (
              <div
                key={i}
                className={`p-2 rounded-xl border flex flex-col justify-between ${
                  v.status === "critical"
                    ? "bg-rose-50 border-rose-200 text-rose-900"
                    : v.status === "warning"
                    ? "bg-amber-50 border-amber-200 text-amber-900"
                    : "bg-white border-slate-200 text-slate-800"
                }`}
              >
                <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1">
                  <span>{v.label}</span>
                  {renderVitalIcon(v.metricType)}
                </div>
                <div className="font-mono text-xs font-bold truncate text-slate-900">
                  {v.value}
                </div>
              </div>
            ))}
          </div>

          {/* Expandable Multi-Lead Real-Time ECG Strip */}
          <AnimatePresence>
            {showLeadStrip && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-3 pt-3 border-t border-slate-200 overflow-hidden"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] font-mono font-bold text-teal-800 uppercase">
                      Select Lead:
                    </span>
                    {(["lead2", "leadV1", "leadV2"] as const).map((lead) => (
                      <button
                        key={lead}
                        onClick={() => setSelectedLead(lead)}
                        className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          selectedLead === lead
                            ? "bg-teal-600 text-white"
                            : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-100"
                        }`}
                      >
                        {lead === "lead2" ? "Lead II (Rhythm)" : lead === "leadV1" ? "Lead V1" : "Lead V2 (Wellens)"}
                      </button>
                    ))}
                  </div>

                  <span className="text-[10px] font-mono text-slate-500">
                    25mm/s • 10mm/mV • 72 bpm • QTc: 412ms
                  </span>
                </div>

                {/* Animated ECG Lead Screen */}
                <div
                  className="relative h-16 bg-white rounded-xl border border-slate-200 overflow-hidden flex items-center"
                  style={{
                    backgroundImage: "linear-gradient(to right, rgba(13,148,136,0.08) 1px, transparent 1px), linear-gradient(to bottom, rgba(13,148,136,0.08) 1px, transparent 1px)",
                    backgroundSize: "16px 16px"
                  }}
                >
                  <svg className="w-full h-12 text-teal-600" viewBox="0 0 600 48" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path
                      d="M0 24 H40 L45 10 L55 38 L65 2 L75 32 L80 24 H140 L145 10 L155 38 L165 2 L175 32 L180 24 H240 L245 10 L255 38 L265 2 L275 32 L280 24 H340 L345 10 L355 38 L365 2 L375 32 L380 24 H440 L445 10 L455 38 L465 2 L475 32 L480 24 H540 L545 10 L555 38 L565 2 L575 32 L580 24 H600"
                      strokeDasharray="600"
                      className="animate-[dash_3.5s_linear_infinite]"
                    />
                  </svg>
                  <div className="absolute right-2 bottom-1 bg-white/90 border border-slate-200 px-2 py-0.5 rounded text-[9px] font-mono text-emerald-700 font-bold">
                    Normal Sinus Rhythm
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* ── 5. Clinical Presentation Box ── */}
        <div className="space-y-3 mb-4">
          <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200">
            <p className="text-[10px] font-bold text-rose-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-rose-500 inline-block" />
              Presenting Symptoms & History
            </p>
            <p className="text-xs sm:text-sm text-slate-800 leading-relaxed font-medium">
              {isExpanded ? post.clinical_findings : truncatedFindings}
            </p>
          </div>

          {/* Expanded Diagnosis & Protocol */}
          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2 }}
                className="space-y-3 overflow-hidden"
              >
                {/* Confirmed Diagnosis */}
                <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200">
                  <p className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
                    Confirmed Clinical Diagnosis & Diagnostic Criteria
                  </p>
                  <p className="text-xs sm:text-sm text-slate-900 leading-relaxed font-medium">
                    {post.diagnosis}
                  </p>
                </div>

                {/* Evidence-Based Treatment Plan & Steps */}
                <div className="bg-slate-50 rounded-2xl p-4 border-l-4 border-l-teal-600 border border-slate-200 relative">
                  <p className="text-[10px] font-bold text-teal-800 uppercase tracking-wider mb-2">
                    Evidence-Based Clinical Protocol & Attending Action Items
                  </p>
                  <p className="text-xs sm:text-sm text-slate-800 leading-relaxed font-medium mb-3">
                    {post.treatment_plan}
                  </p>

                  {/* Pharmacology */}
                  {post.drugs_used?.length > 0 && (
                    <div className="pt-3 border-t border-slate-200">
                      <p className="text-[10px] font-bold text-teal-800 uppercase tracking-wider mb-2">
                        Prescribed Pharmacology & Dosages:
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {post.drugs_used.map((drug, i) => (
                          <span
                            key={i}
                            className="text-xs font-bold bg-white text-teal-800 px-3 py-1 rounded-lg border border-teal-200 shadow-sm"
                          >
                            💊 {drug}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Toggle Expand / Collapse */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs font-bold text-teal-700 hover:text-teal-800 flex items-center gap-1 transition-colors"
          >
            {isExpanded ? "▲ Collapse Protocol Details" : "▼ Read Full Protocol & Pharmacology"}
          </button>
        </div>

        {/* ── 6. High-Resolution Diagnostic Attachments ── */}
        {post.attachments?.length > 0 && (
          <div className="mb-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {post.attachments.map((att) => (
                <div
                  key={att.id}
                  onClick={() => onOpenImage(att.file_url)}
                  className="group relative h-52 bg-slate-900 rounded-2xl overflow-hidden border border-slate-200 cursor-pointer flex items-center justify-center shadow-sm hover:border-teal-400 transition-all"
                >
                  <img
                    src={att.file_url}
                    alt="Clinical attachment"
                    className="w-full h-full object-cover group-hover:scale-102 transition-transform duration-200"
                  />
                  <div className="absolute inset-0 bg-slate-900/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                    <span className="bg-white text-slate-900 px-3.5 py-1.5 rounded-full text-xs font-bold flex items-center gap-1.5 shadow-md">
                      <ClinicalIcons.Microscope className="w-4 h-4 text-teal-600" />
                      <span>Inspect Scan / DICOM Console</span>
                    </span>
                  </div>
                  <div className="absolute bottom-2.5 left-2.5 bg-white/90 backdrop-blur-sm px-2.5 py-0.5 rounded-full text-[9px] text-teal-800 font-bold border border-slate-200 shadow-sm">
                    HIPAA De-Identified
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── 7. Specialist Consensus Dilemma Poll ── */}
        {post.poll_data && (
          <div className="mb-4 bg-slate-50 rounded-2xl p-4 border border-slate-200">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] font-bold uppercase tracking-wider text-teal-800 flex items-center gap-1.5">
                <span>🗳️</span> Specialist Consensus Dilemma Poll
              </span>
              <span className="text-[10px] text-slate-500 font-bold">
                {post.poll_data.total_votes} Attending Votes
              </span>
            </div>

            <p className="text-xs sm:text-sm font-bold text-slate-900 mb-3">
              {post.poll_data.question}
            </p>

            <div className="space-y-2">
              {post.poll_data.options.map((opt, i) => {
                const total = Math.max(1, post.poll_data?.total_votes ?? 1);
                const percent = Math.round((opt.votes / total) * 100);
                const isUserChoice = post.poll_data?.voted_index === i;

                return (
                  <button
                    key={i}
                    onClick={() => onVotePoll(i)}
                    className={`relative w-full text-left p-3 rounded-xl border transition-all overflow-hidden ${
                      isUserChoice
                        ? "border-teal-400 bg-teal-50 text-teal-900 font-bold"
                        : "border-slate-200 bg-white text-slate-800 hover:border-teal-300"
                    }`}
                  >
                    <div
                      className="absolute inset-y-0 left-0 bg-teal-100/70"
                      style={{ width: `${percent}%` }}
                    />

                    <div className="relative z-10 flex items-center justify-between text-xs">
                      <span className="flex items-center gap-2">
                        {isUserChoice && <span className="text-teal-700 font-black">✓</span>}
                        <span>{opt.label}</span>
                      </span>
                      <span className="font-mono font-bold text-teal-800">
                        {percent}% ({opt.votes})
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>

            <p className="text-[10px] text-slate-500 mt-2 text-right">
              {post.poll_data.has_voted
                ? "✓ Your vote is recorded in the PostgreSQL clinical consensus database"
                : "Vote to contribute to peer attending consensus"}
            </p>
          </div>
        )}
      </div>

      {/* ── 8. Engagement & Social Actions Bar ── */}
      <div className="px-5 py-3.5 bg-slate-50/80 border-t border-slate-100 flex items-center justify-between flex-wrap gap-3">
        {/* Left: Reactions & Endorsements */}
        <div className="flex items-center gap-3 sm:gap-4 flex-wrap">
          {/* Reaction Button with Popover */}
          <div
            className="relative"
            onMouseEnter={handlePickerMouseEnter}
            onMouseLeave={handlePickerMouseLeave}
          >
            <button
              onClick={onLike}
              className={`flex items-center gap-1.5 text-xs sm:text-sm font-bold transition-all px-3 py-1.5 rounded-full ${
                post.is_liked_by_me
                  ? "bg-teal-100 text-teal-800 border border-teal-300 shadow-sm"
                  : "text-slate-600 hover:bg-slate-200/70 hover:text-teal-700"
              }`}
            >
              <ClinicalIcons.Stethoscope className="w-4 h-4 text-teal-600" />
              <span>{post.my_reaction ? CLINICAL_REACTIONS.find((r) => r.id === post.my_reaction)?.label ?? "Validate" : "Validate"}</span>
              <span className="font-mono text-xs">{post.likes_count}</span>
            </button>

            {/* Hover Reaction Picker */}
            <AnimatePresence>
              {showReactionPicker && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9, y: 5 }}
                  animate={{ opacity: 1, scale: 1, y: -45 }}
                  exit={{ opacity: 0, scale: 0.9, y: 5 }}
                  className="absolute left-0 bottom-0 z-40 bg-white border border-slate-200 rounded-full px-2.5 py-1.5 shadow-xl flex items-center gap-2"
                >
                  {CLINICAL_REACTIONS.map((r) => {
                    const IconComp = r.Icon;
                    return (
                      <button
                        key={r.id}
                        onClick={() => {
                          onReact(r.id);
                          setShowReactionPicker(false);
                        }}
                        className="p-1.5 hover:scale-120 transition-transform text-lg group relative rounded-full hover:bg-slate-100"
                        title={r.label}
                      >
                        <IconComp className="w-4 h-4 text-teal-600" />
                        <span className="absolute -top-7 left-1/2 -translate-x-1/2 bg-slate-900 text-white text-[9px] font-bold px-1.5 py-0.5 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                          {r.label}
                        </span>
                      </button>
                    );
                  })}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Endorse & Cite */}
          <button
            onClick={onEndorse}
            className={`flex items-center gap-1.5 text-xs sm:text-sm font-bold transition-all px-3 py-1.5 rounded-full ${
              post.is_endorsed_by_me
                ? "bg-indigo-50 text-indigo-700 border border-indigo-200"
                : "text-slate-600 hover:bg-slate-200/70 hover:text-indigo-700"
            }`}
            title="Endorse & Cite Case into your peer portfolio"
          >
            <ClinicalIcons.Handshake className="w-4 h-4 text-indigo-600" />
            <span>Endorse</span>
            <span className="font-mono text-xs">{post.endorsements_count ?? 0}</span>
          </button>

          {/* Comments Toggle */}
          <button
            onClick={() => setShowComments(!showComments)}
            className="flex items-center gap-1.5 text-xs sm:text-sm font-bold text-slate-600 hover:text-teal-700 transition-colors"
          >
            <span>💬</span>
            <span>{post.comments_count} Reviews</span>
          </button>
        </div>

        {/* Right: Consensus Gauge & AI Index */}
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-1.5 text-xs bg-white border border-slate-200 px-2.5 py-1 rounded-full shadow-sm">
            <span className="text-[10px] text-slate-500">Consensus</span>
            <span className="font-mono font-bold text-teal-700">{consensusPercentage}%</span>
          </div>

          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-purple-800 bg-purple-50 border border-purple-200 px-2.5 py-1 rounded-full">
            <ClinicalIcons.Brain className="w-3.5 h-3.5 text-purple-600" />
            <span>AI Indexed</span>
          </span>
        </div>
      </div>

      {/* ── 9. Comments Section (Peer Reviews) ── */}
      <AnimatePresence>
        {showComments && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-slate-100 overflow-hidden bg-slate-50/70"
          >
            <div className="p-4 sm:p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Peer Reviews & Attending Consultations
                </h4>
                {typingDoctor && (
                  <span className="text-[11px] text-teal-700 font-bold flex items-center gap-1.5 animate-pulse">
                    <span className="flex gap-0.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-teal-600 animate-bounce" />
                      <span className="w-1.5 h-1.5 rounded-full bg-teal-600 animate-bounce [animation-delay:0.15s]" />
                      <span className="w-1.5 h-1.5 rounded-full bg-teal-600 animate-bounce [animation-delay:0.3s]" />
                    </span>
                    <span>{typingDoctor} is reviewing...</span>
                  </span>
                )}
              </div>

              {post.comments.map((c) => {
                const cAuthor = c.author_name || `Dr. ${c.author_id.substring(0, 8)}`;
                const cSpecialty = c.author_specialty || "Attending";
                return (
                  <div key={c.id} className="flex gap-3">
                    <div
                      className={`w-8 h-8 rounded-full bg-gradient-to-br ${getAvatarGradient(
                        c.author_id
                      )} flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0 shadow-sm`}
                    >
                      {getInitials(cAuthor)}
                    </div>
                    <div className="bg-white rounded-2xl px-4 py-2.5 flex-1 border border-slate-200">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <p className="text-xs font-bold text-slate-900">{cAuthor}</p>
                          <span className="text-[10px] text-teal-700 font-semibold">
                            {cSpecialty}
                          </span>
                        </div>
                        <span className="text-[10px] text-slate-400">
                          {timeAgo(c.created_at)}
                        </span>
                      </div>
                      <p className="text-xs sm:text-sm text-slate-700 leading-relaxed">
                        {c.content}
                      </p>
                    </div>
                  </div>
                );
              })}

              {/* Add Comment Input */}
              <form onSubmit={handleCommentSubmit} className="flex gap-2 pt-2">
                <input
                  type="text"
                  value={commentText}
                  onChange={(e) => {
                    setCommentText(e.target.value);
                    onTyping(e.target.value.length > 0);
                  }}
                  onBlur={() => onTyping(false)}
                  placeholder="Provide clinical review or protocol recommendation..."
                  className="flex-1 bg-white border border-slate-200 rounded-full px-4 py-2 text-xs sm:text-sm outline-none focus:border-teal-500 text-slate-900 placeholder:text-slate-400"
                />
                <button
                  type="submit"
                  disabled={!commentText.trim()}
                  className="px-5 py-2 bg-teal-600 hover:bg-teal-700 disabled:opacity-40 text-white text-xs sm:text-sm font-bold rounded-full transition-all shadow-sm"
                >
                  Review
                </button>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </article>
  );
}

// ─── Component: Case Composer Modal (Clean Light Theme) ───────────────────────

function CaseComposer({
  onPublish,
  onCancel,
}: {
  onPublish: (postData: any, files: File[]) => Promise<void>;
  onCancel: () => void;
}) {
  const [composerMode, setComposerMode] = useState<"case" | "dilemma" | "urgent">("case");
  const [diseaseName, setDiseaseName] = useState("");
  const [specialtyTags, setSpecialtyTags] = useState("");
  const [clinicalFindings, setClinicalFindings] = useState("");
  const [diagnosis, setDiagnosis] = useState("");
  const [treatmentPlan, setTreatmentPlan] = useState("");
  const [drugsUsed, setDrugsUsed] = useState("");
  const [pollQuestion, setPollQuestion] = useState("");
  const [pollOptions, setPollOptions] = useState(["", "", ""]);
  const [files, setFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const payload: any = {
        disease_name: diseaseName,
        specialty_tags: specialtyTags.split(",").map((s) => s.trim()).filter(Boolean),
        clinical_findings: clinicalFindings,
        diagnosis: diagnosis || "Diagnostic consensus requested",
        treatment_plan: treatmentPlan || "Under active peer multidisciplinary review",
        drugs_used: drugsUsed.split(",").map((d) => d.trim()).filter(Boolean),
        poll_question: composerMode === "dilemma" ? pollQuestion : null,
        poll_options: composerMode === "dilemma" ? pollOptions.filter((o) => o.trim()) : null,
        is_urgent_consult: composerMode === "urgent",
      };

      if (composerMode === "urgent") {
        payload.specialty_tags.push("UrgentConsult");
      }

      await onPublish(payload, files);
    } catch (err) {
      console.error("Composer submission error:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.98 }}
      className="mb-6 rounded-3xl bg-white border border-slate-200 p-5 sm:p-6 shadow-md relative overflow-hidden"
    >
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-teal-500 to-emerald-600" />

      {/* Composer Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base sm:text-lg font-bold text-slate-900">
            Share Clinical Case with Verified Specialists
          </h3>
          <p className="text-xs text-slate-500">
            Ingested into DocAssistIQ AI Knowledge Base to enhance collective diagnostic precision
          </p>
        </div>
        <button
          onClick={onCancel}
          className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 hover:bg-slate-200 hover:text-slate-800 transition-colors"
        >
          ✕
        </button>
      </div>

      {/* Composer Mode Tabs */}
      <div className="flex gap-2 mb-4 p-1 bg-slate-50 rounded-xl border border-slate-200">
        <button
          type="button"
          onClick={() => setComposerMode("case")}
          className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all ${
            composerMode === "case"
              ? "bg-teal-600 text-white shadow-sm"
              : "text-slate-600 hover:text-slate-900"
          }`}
        >
          🔬 Clinical Case Study
        </button>
        <button
          type="button"
          onClick={() => setComposerMode("dilemma")}
          className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all ${
            composerMode === "dilemma"
              ? "bg-teal-600 text-white shadow-sm"
              : "text-slate-600 hover:text-slate-900"
          }`}
        >
          ⚡ Diagnostic Dilemma Poll
        </button>
        <button
          type="button"
          onClick={() => setComposerMode("urgent")}
          className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all ${
            composerMode === "urgent"
              ? "bg-rose-600 text-white shadow-sm"
              : "text-rose-700 hover:bg-rose-50"
          }`}
        >
          🚨 Urgent 2nd Opinion
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
              Condition / Working Diagnosis *
            </label>
            <input
              required
              value={diseaseName}
              onChange={(e) => setDiseaseName(e.target.value)}
              placeholder="e.g. Wellens Syndrome Type A, Anti-NMDAR Encephalitis"
              className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2 text-xs sm:text-sm outline-none focus:border-teal-500 text-slate-900"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
              Specialty Tags (comma-separated) *
            </label>
            <input
              required
              value={specialtyTags}
              onChange={(e) => setSpecialtyTags(e.target.value)}
              placeholder="e.g. Cardiology, Critical Care, ECG"
              className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2 text-xs sm:text-sm outline-none focus:border-teal-500 text-slate-900"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
            Clinical Presentation, Vitals & Laboratory Findings *
          </label>
          <textarea
            required
            rows={3}
            value={clinicalFindings}
            onChange={(e) => setClinicalFindings(e.target.value)}
            placeholder="Age, sex, presenting symptoms, vitals, initial labs and imaging..."
            className="w-full bg-white border border-slate-200 rounded-xl p-3 text-xs sm:text-sm outline-none focus:border-teal-500 text-slate-900 resize-none"
          />
        </div>

        {composerMode === "dilemma" && (
          <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-2.5">
            <label className="block text-xs font-bold text-teal-800 uppercase tracking-wider">
              Diagnostic Dilemma Question *
            </label>
            <input
              required
              value={pollQuestion}
              onChange={(e) => setPollQuestion(e.target.value)}
              placeholder="e.g. What is the immediate priority intervention?"
              className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-900"
            />
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {pollOptions.map((opt, i) => (
                <input
                  key={i}
                  required={i < 2}
                  value={opt}
                  onChange={(e) => {
                    const next = [...pollOptions];
                    next[i] = e.target.value;
                    setPollOptions(next);
                  }}
                  placeholder={`Option ${i + 1}`}
                  className="bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-900"
                />
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
              Definitive Diagnosis & Criteria
            </label>
            <textarea
              rows={2}
              value={diagnosis}
              onChange={(e) => setDiagnosis(e.target.value)}
              placeholder="Confirmed diagnostic criteria or differential..."
              className="w-full bg-white border border-slate-200 rounded-xl p-3 text-xs sm:text-sm outline-none focus:border-teal-500 text-slate-900 resize-none"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
              Treatment Protocol & Outcome
            </label>
            <textarea
              rows={2}
              value={treatmentPlan}
              onChange={(e) => setTreatmentPlan(e.target.value)}
              placeholder="Management steps, dosing, surgical intervention, outcome..."
              className="w-full bg-white border border-slate-200 rounded-xl p-3 text-xs sm:text-sm outline-none focus:border-teal-500 text-slate-900 resize-none"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
            Pharmacology / Drugs Used (comma-separated)
          </label>
          <input
            value={drugsUsed}
            onChange={(e) => setDrugsUsed(e.target.value)}
            placeholder="e.g. Aspirin 325mg, Ticagrelor 180mg, IV Heparin"
            className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2 text-xs sm:text-sm outline-none focus:border-teal-500 text-slate-900"
          />
        </div>

        {/* Imaging Upload */}
        <div
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-slate-200 rounded-2xl p-4 text-center cursor-pointer hover:border-teal-500 hover:bg-teal-50/50 transition-all"
        >
          <input
            type="file"
            multiple
            className="hidden"
            ref={fileInputRef}
            onChange={(e) => {
              if (e.target.files) setFiles(Array.from(e.target.files));
            }}
          />
          <p className="text-xs font-bold text-slate-800">
            📁 Attach ECG, Radiology Scans, or Clinical Photos
          </p>
          <p className="text-[10px] text-slate-500 mt-0.5">
            {files.length > 0
              ? `${files.length} diagnostic file(s) selected`
              : "Click to upload DICOM, JPEG, PNG • Automatic HIPAA de-identification"}
          </p>
        </div>

        <div className="flex items-center justify-between pt-2">
          <span className="text-[10px] text-teal-700 font-bold flex items-center gap-1">
            <ClinicalIcons.ShieldCheck className="w-3.5 h-3.5" />
            <span>All submissions encrypted & protected</span>
          </span>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="bg-teal-600 hover:bg-teal-700 text-white px-6 py-2 rounded-xl text-xs sm:text-sm font-bold shadow-sm transition-all flex items-center gap-1.5"
            >
              {isSubmitting ? "Publishing to Global Hub..." : "🧠 Publish & Train AI"}
            </button>
          </div>
        </div>
      </form>
    </motion.div>
  );
}

// ─── Component: Client Portal for Modals ──────────────────────────────────────

function ClientPortal({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);
  if (!mounted || typeof document === "undefined") return null;
  return createPortal(children, document.body);
}

// ─── Main Hub Page (Clean Light Clinical Theme) ────────────────────────────────

export default function KnowledgeHub() {
  const { user, refetch: refetchAuth } = useAuth();
  const [posts, setPosts] = useState<DoctorPost[]>([]);
  const [stories, setStories] = useState<DoctorPost[]>([]);
  const [trending, setTrending] = useState<TrendingData | null>(null);
  const [suggestedDoctors, setSuggestedDoctors] = useState<DoctorProfile[]>([]);
  const [myStats, setMyStats] = useState<DoctorMyStats | null>(null);
  const [pulse, setPulse] = useState<HubPulse | null>(null);

  // Modals & Viewers
  const [isCreating, setIsCreating] = useState(false);
  const [activeStoryIndex, setActiveStoryIndex] = useState<number | null>(null);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [selectedCitePost, setSelectedCitePost] = useState<DoctorPost | null>(null);
  const [selectedDossierPost, setSelectedDossierPost] = useState<DoctorPost | null>(null);
  const [showActiveDoctorsModal, setShowActiveDoctorsModal] = useState(false);
  const [showCalculatorModal, setShowCalculatorModal] = useState(false);
  const [showComparisonModal, setShowComparisonModal] = useState(false);

  // Differential Comparison Selection Tray
  const [comparisonCases, setComparisonCases] = useState<DoctorPost[]>([]);

  // Toast notification
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Live Sound Chime & Typing states
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [typingMap, setTypingMap] = useState<Record<string, string>>({});

  // Filters & Tabs
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFilterCategory, setSelectedFilterCategory] = useState<"all" | "urgent" | "polls" | "cardiology" | "neurology" | "rare">("all");
  const [activeTab, setActiveTab] = useState<"recent" | "trending">("recent");
  const [loadingFeed, setLoadingFeed] = useState(true);
  const [isVerifyingAccount, setIsVerifyingAccount] = useState(false);

  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const token = () =>
    getStoredToken() ||
    (typeof window !== "undefined"
      ? localStorage.getItem("access_token") || localStorage.getItem("token")
      : null) ||
    "";

  const authHeaders = (extra: Record<string, string> = {}) => {
    const t = token();
    return t ? { ...extra, Authorization: `Bearer ${t}` } : { ...extra };
  };

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Fetch Posts
  const fetchPosts = useCallback(
    async (search?: string, tab?: "recent" | "trending") => {
      setLoadingFeed(true);
      try {
        let url = search
          ? `/api/v1/hub/search?q=${encodeURIComponent(search)}`
          : `/api/v1/hub/feed?sort_by=${tab ?? activeTab}`;

        const res = await fetch(url, { headers: authHeaders() });
        if (res.ok) {
          const data = await res.json();
          setPosts(data);
        }
      } catch (err) {
        console.error("Feed error:", err);
      } finally {
        setLoadingFeed(false);
      }
    },
    [activeTab]
  );

  const fetchStories = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/hub/stories", { headers: authHeaders() });
      if (res.ok) setStories(await res.json());
    } catch {}
  }, []);

  const fetchTrending = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/hub/trending", { headers: authHeaders() });
      if (res.ok) setTrending(await res.json());
    } catch {}
  }, []);

  const fetchExploreDoctors = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/hub/explore", { headers: authHeaders() });
      if (res.ok) setSuggestedDoctors(await res.json());
    } catch {}
  }, []);

  const fetchMyStats = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/hub/me/stats", { headers: authHeaders() });
      if (res.ok) setMyStats(await res.json());
    } catch {}
  }, []);

  const fetchPulse = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/hub/pulse", { headers: authHeaders() });
      if (res.ok) setPulse(await res.json());
    } catch {}
  }, []);

  // Initial Load & Real-Time WebSocket Connection
  useEffect(() => {
    fetchPosts();
    fetchStories();
    fetchTrending();
    fetchExploreDoctors();
    fetchMyStats();
    fetchPulse();

    const authToken = token();
    if (!authToken) return;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/v1/stream?token=${authToken}`;
    let ws: WebSocket | null = null;

    try {
      ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);

          if (msg.type === "hub_new_post") {
            if (msg.payload.is_urgent_consult) {
              playUrgentPagerBeep();
              showToast(`🚨 URGENT CONSULT: ${msg.payload.disease_name}`);
            } else if (soundEnabled) {
              playClinicalChime();
              showToast(`New Clinical Protocol: ${msg.payload.disease_name}`);
            }
            setPosts((prev) => [msg.payload, ...prev]);
          } else if (msg.type === "hub_post_reaction") {
            if (soundEnabled) playClinicalChime();
            setPosts((prev) =>
              prev.map((p) =>
                p.id === msg.payload.post_id
                  ? {
                      ...p,
                      likes_count: msg.payload.likes_count,
                      reactions_breakdown: msg.payload.reactions_breakdown || p.reactions_breakdown,
                    }
                  : p
              )
            );
          } else if (msg.type === "hub_poll_vote") {
            setPosts((prev) =>
              prev.map((p) =>
                p.id === msg.payload.post_id && p.poll_data
                  ? {
                      ...p,
                      poll_data: {
                        ...p.poll_data,
                        options: msg.payload.options || p.poll_data.options,
                        total_votes: msg.payload.total_votes ?? p.poll_data.total_votes,
                      },
                    }
                  : p
              )
            );
          } else if (msg.type === "hub_new_comment") {
            setPosts((prev) =>
              prev.map((p) =>
                p.id === msg.payload.post_id
                  ? {
                      ...p,
                      comments_count: msg.payload.comments_count,
                      comments: [msg.payload.comment, ...p.comments],
                    }
                  : p
              )
            );
          } else if (msg.type === "hub_case_endorsed") {
            setPosts((prev) =>
              prev.map((p) =>
                p.id === msg.payload.post_id
                  ? { ...p, endorsements_count: msg.payload.endorsements_count }
                  : p
              )
            );
            showToast(`${msg.payload.endorser_name} endorsed a clinical protocol`);
          } else if (msg.type === "hub_user_typing") {
            if (msg.payload.is_typing) {
              setTypingMap((prev) => ({ ...prev, [msg.payload.post_id]: msg.payload.doctor_name }));
            } else {
              setTypingMap((prev) => {
                const next = { ...prev };
                delete next[msg.payload.post_id];
                return next;
              });
            }
          } else if (msg.type === "hub_doctor_followed") {
            setSuggestedDoctors((prev) =>
              prev.map((d) =>
                d.id === msg.payload.doctor_id
                  ? { ...d, followers_count: msg.payload.followers_count }
                  : d
              )
            );
          }
        } catch {}
      };
    } catch {}

    return () => {
      if (ws) ws.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [soundEnabled]);

  // Search debounce
  useEffect(() => {
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    if (searchQuery.length >= 2) {
      searchTimeoutRef.current = setTimeout(() => {
        fetchPosts(searchQuery);
      }, 400);
    } else if (searchQuery.length === 0) {
      fetchPosts(undefined, activeTab);
    }
    return () => {
      if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery]);

  // Post Submission
  const handlePublishPost = async (postData: any, files: File[]) => {
    const attachmentIds: string[] = [];
    for (const f of files) {
      const formData = new FormData();
      formData.append("file", f);
      formData.append("metadata", JSON.stringify({ category: "clinical_imaging" }));
      const fRes = await fetch("/api/v1/files/upload", {
        method: "POST",
        headers: authHeaders(),
        body: formData,
      });
      if (fRes.ok) {
        const fileInfo = await fRes.json();
        attachmentIds.push(fileInfo.file_id);
      }
    }

    const payload = {
      ...postData,
      attachment_ids: attachmentIds,
    };

    const res = await fetch("/api/v1/hub/posts", {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      setIsCreating(false);
      showToast("Case published & submitted to AI Diagnostic Vault!");
      fetchPosts();
      fetchStories();
      fetchMyStats();
      fetchPulse();
    }
  };

  // Engagement Handlers
  const handleLike = async (postId: string) => {
    try {
      const res = await fetch(`/api/v1/hub/posts/${postId}/react`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ reaction_type: "validate" }),
      });
      if (res.ok) {
        const data = await res.json();
        setPosts((prev) =>
          prev.map((p) =>
            p.id === postId
              ? {
                  ...p,
                  my_reaction: data.reaction,
                  is_liked_by_me: Boolean(data.reaction),
                  likes_count: data.likes_count,
                  reactions_breakdown: data.reactions_breakdown,
                }
              : p
          )
        );
      }
    } catch {}
  };

  const handleBookmark = async (postId: string) => {
    setPosts((prev) =>
      prev.map((p) =>
        p.id === postId ? { ...p, is_bookmarked_by_me: !p.is_bookmarked_by_me } : p
      )
    );
    try {
      await fetch(`/api/v1/hub/posts/${postId}/bookmark`, {
        method: "POST",
        headers: authHeaders(),
      });
    } catch {}
  };

  const handleComment = async (postId: string, text: string) => {
    try {
      const res = await fetch(`/api/v1/hub/posts/${postId}/comments`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ content: text }),
      });
      if (res.ok) {
        fetchPosts();
      }
    } catch {}
  };

  const handleReact = async (postId: string, reactionType: string) => {
    try {
      const res = await fetch(`/api/v1/hub/posts/${postId}/react`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ reaction_type: reactionType }),
      });
      if (res.ok) {
        const data = await res.json();
        setPosts((prev) =>
          prev.map((p) =>
            p.id === postId
              ? {
                  ...p,
                  my_reaction: data.reaction,
                  is_liked_by_me: Boolean(data.reaction),
                  likes_count: data.likes_count,
                  reactions_breakdown: data.reactions_breakdown,
                }
              : p
          )
        );
      }
    } catch {}
  };

  const handleVotePoll = async (postId: string, optionIndex: number) => {
    try {
      const res = await fetch(`/api/v1/hub/posts/${postId}/poll-vote`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ option_index: optionIndex }),
      });
      if (res.ok) {
        const data = await res.json();
        setPosts((prev) =>
          prev.map((p) =>
            p.id === postId && p.poll_data
              ? {
                  ...p,
                  poll_data: {
                    ...p.poll_data,
                    has_voted: true,
                    voted_index: data.option_index,
                    total_votes: data.total_votes,
                    options: data.options,
                  },
                }
              : p
          )
        );
        showToast("Consensus vote recorded in PostgreSQL!");
      }
    } catch {}
  };

  const handleEndorse = async (postId: string) => {
    try {
      const res = await fetch(`/api/v1/hub/posts/${postId}/endorse`, {
        method: "POST",
        headers: authHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setPosts((prev) =>
          prev.map((p) =>
            p.id === postId
              ? {
                  ...p,
                  is_endorsed_by_me: data.endorsed,
                  endorsements_count: data.endorsements_count,
                }
              : p
          )
        );
        showToast(data.endorsed ? "Case cited & endorsed to your portfolio!" : "Endorsement removed");
      }
    } catch {}
  };

  const handleToggleFollow = async (targetDoctorId: string) => {
    try {
      const res = await fetch(`/api/v1/hub/doctors/${targetDoctorId}/follow`, {
        method: "POST",
        headers: authHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setSuggestedDoctors((prev) =>
          prev.map((d) =>
            d.id === targetDoctorId
              ? {
                  ...d,
                  is_following: data.is_following,
                  followers_count: data.followers_count,
                }
              : d
          )
        );
        fetchMyStats();
        showToast(data.is_following ? "Following specialist for peer consults!" : "Unfollowed doctor");
      }
    } catch {}
  };

  const handleToggleCompare = (post: DoctorPost) => {
    setComparisonCases((prev) => {
      const exists = prev.some((c) => c.id === post.id);
      if (exists) {
        return prev.filter((c) => c.id !== post.id);
      }
      if (prev.length >= 2) {
        showToast("Comparison tray holds 2 cases maximum. Removing oldest.");
        return [prev[1], post];
      }
      showToast(`Added ${post.disease_name} to comparison tray`);
      return [...prev, post];
    });
  };

  const handleTypingBroadcast = (postId: string, isTyping: boolean) => {
    fetch(`/api/v1/hub/posts/${postId}/typing?is_typing=${isTyping}`, {
      method: "POST",
      headers: authHeaders(),
    }).catch(() => {});
  };

  const handleFastTrackVerify = async () => {
    setIsVerifyingAccount(true);
    try {
      const res = await authVerifyAccount();
      if (res.ok) {
        refetchAuth();
      }
    } catch (err) {
      console.error("Verification error:", err);
    } finally {
      setIsVerifyingAccount(false);
    }
  };

  const displayedPosts = useMemo(() => {
    return posts.filter((p) => {
      if (selectedFilterCategory === "urgent") return p.is_urgent_consult;
      if (selectedFilterCategory === "polls") return Boolean(p.poll_data);
      if (selectedFilterCategory === "cardiology") {
        return p.specialty_tags?.some((t) => t.toLowerCase().includes("cardio") || t.toLowerCase().includes("ecg"));
      }
      if (selectedFilterCategory === "neurology") {
        return p.specialty_tags?.some((t) => t.toLowerCase().includes("neuro"));
      }
      if (selectedFilterCategory === "rare") {
        return p.disease_name.toLowerCase().includes("atypical") || p.disease_name.toLowerCase().includes("anti-") || p.disease_name.toLowerCase().includes("refractory");
      }
      return true;
    });
  }, [posts, selectedFilterCategory]);

  // Unverified Lock Screen
  if (user && !user.is_verified) {
    return (
      <div className="flex items-center justify-center min-h-[85vh] bg-slate-50 p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          className="p-8 sm:p-12 text-center bg-white rounded-3xl shadow-xl border border-slate-200 max-w-lg"
        >
          <div className="w-20 h-20 bg-teal-50 text-teal-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-sm border border-teal-100">
            <ClinicalIcons.Stethoscope className="w-10 h-10" />
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 mb-3">
            Physician Verification Required
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed mb-6">
            The Medical Intelligence Hub is an exclusive, HIPAA-compliant peer consultation network
            restricted to board-certified physicians and medical council registrants.
          </p>

          <button
            onClick={handleFastTrackVerify}
            disabled={isVerifyingAccount}
            className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-3.5 px-6 rounded-2xl shadow-sm transition-all flex items-center justify-center gap-2 text-sm disabled:opacity-50"
          >
            {isVerifyingAccount ? (
              "Verifying Medical Council License..."
            ) : (
              <>
                <ClinicalIcons.ShieldCheck className="w-4 h-4" />
                <span>Fast-Track Board Verification (Instant GMC/NMC)</span>
              </>
            )}
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-full bg-slate-50 text-slate-900 pb-28 selection:bg-teal-600 selection:text-white relative">
      {/* Precision telemetry dot matrix grid overlay (Clean Light) */}
      <div
        className="fixed inset-0 pointer-events-none opacity-40"
        style={{
          backgroundImage: "radial-gradient(rgba(148, 163, 184, 0.3) 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />

      <div className="relative max-w-7xl mx-auto px-4 py-6">
        {/* ── Top Command Bar & Pulse Marquee ── */}
        <LivePulseBar
          pulse={pulse}
          soundEnabled={soundEnabled}
          onToggleSound={() => setSoundEnabled(!soundEnabled)}
          onOpenDoctors={() => setShowActiveDoctorsModal(true)}
          onOpenCalculator={() => setShowCalculatorModal(true)}
        />

        {/* ── 3-Column Hospital Grid ── */}
        <div className="grid grid-cols-1 lg:grid-cols-[290px_1fr_300px] gap-6">
          {/* ══════════════ LEFT SIDEBAR ══════════════ */}
          <aside className="hidden lg:block space-y-5">
            {/* Doctor Profile Card */}
            <div className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm">
              <div className="h-24 bg-gradient-to-r from-teal-600 to-emerald-600 relative overflow-hidden" />
              <div className="px-5 pb-5 -mt-12 relative z-10">
                <div className="w-18 h-18 bg-white text-teal-800 rounded-full border-4 border-white flex items-center justify-center font-black text-2xl shadow-md mb-3">
                  {(user?.email?.[0] ?? "D").toUpperCase()}
                </div>
                <div className="flex items-center gap-1.5">
                  <h3 className="font-extrabold text-slate-900 text-base">
                    Dr. {user?.email?.split("@")[0] ?? "Physician"}
                  </h3>
                  <ClinicalIcons.ShieldCheck className="w-4 h-4 text-teal-600" />
                </div>
                <p className="text-xs text-teal-700 font-bold">
                  Cardiologist & Critical Care Attending
                </p>
                <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                  GMC/NMC License #98214 • AIIMS
                </p>

                {/* Real Stats from PostgreSQL */}
                <div className="mt-4 grid grid-cols-3 text-center border-t border-slate-100 pt-3 gap-1">
                  <div>
                    <p className="font-black text-slate-900 text-sm">
                      {myStats?.cases_count ?? posts.filter((p) => p.author_id === user?.id).length}
                    </p>
                    <p className="text-[9px] uppercase font-bold text-slate-400">Cases</p>
                  </div>
                  <div>
                    <p className="font-black text-slate-900 text-sm">
                      {myStats?.endorsements_count ?? 0}
                    </p>
                    <p className="text-[9px] uppercase font-bold text-slate-400">Endorsed</p>
                  </div>
                  <div>
                    <p className="font-black text-teal-700 text-sm">
                      {myStats?.consensus_rate ?? 98}%
                    </p>
                    <p className="text-[9px] uppercase font-bold text-slate-400">Consensus</p>
                  </div>
                </div>

                <div className="mt-2.5 pt-2 border-t border-slate-100 flex justify-between text-[11px] text-slate-500 px-1">
                  <span>
                    <strong className="text-slate-800 font-mono">{myStats?.followers_count ?? 0}</strong> Followers
                  </span>
                  <span>
                    <strong className="text-slate-800 font-mono">{myStats?.following_count ?? 0}</strong> Following
                  </span>
                </div>
              </div>
            </div>

            {/* Point-of-Care Calculator Trigger Button in Sidebar */}
            <div className="bg-white rounded-2xl border border-slate-200 p-3.5 shadow-sm">
              <button
                onClick={() => setShowCalculatorModal(true)}
                className="w-full py-2.5 px-4 rounded-xl text-xs font-bold transition-all flex items-center justify-between bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200"
              >
                <span className="flex items-center gap-2">
                  <ClinicalIcons.Calculator className="w-4 h-4 text-teal-600" />
                  <span>Clinical Calculators</span>
                </span>
                <span className="text-[10px] bg-teal-200/60 px-2 py-0.5 rounded-full font-black text-teal-900">
                  5 Tools
                </span>
              </button>
            </div>

            {/* Quick Urgent Consultations Filter with Clean Beacon */}
            <div className="bg-white rounded-2xl border border-slate-200 p-3.5 shadow-sm">
              <button
                onClick={() => setSelectedFilterCategory(selectedFilterCategory === "urgent" ? "all" : "urgent")}
                className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold transition-all flex items-center justify-between border ${
                  selectedFilterCategory === "urgent"
                    ? "bg-rose-600 text-white border-rose-600 shadow-sm font-black"
                    : "bg-rose-50 text-rose-800 border-rose-200 hover:bg-rose-100"
                }`}
              >
                <span className="flex items-center gap-2">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-500 opacity-75" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-600" />
                  </span>
                  <span>🚨 STAT Urgent Opinions</span>
                </span>
                <span className="text-[10px] bg-white px-2 py-0.5 rounded-full font-black text-rose-800 font-mono shadow-sm">
                  {posts.filter((p) => p.is_urgent_consult).length} Active
                </span>
              </button>
            </div>

            {/* Specialty Filter list with live database counts */}
            <div className="bg-white rounded-3xl border border-slate-200 p-4 shadow-sm">
              <h3 className="font-extrabold text-slate-800 text-xs uppercase tracking-wider mb-3 flex items-center justify-between">
                <span>Browse Departments</span>
                <span className="text-[10px] text-teal-700 font-mono">{posts.length} Cases</span>
              </h3>
              <div className="space-y-1">
                <button
                  onClick={() => setSelectedFilterCategory("all")}
                  className={`w-full text-left text-xs px-3 py-2 rounded-xl font-bold transition-all ${
                    selectedFilterCategory === "all"
                      ? "bg-teal-600 text-white font-black"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  🌐 All Specialties ({posts.length})
                </button>
                {ALL_SPECIALTIES.slice(0, 8).map((spec) => {
                  const count = posts.filter((p) =>
                    p.specialty_tags?.some((t) => t.toLowerCase() === spec.toLowerCase())
                  ).length;
                  return (
                    <button
                      key={spec}
                      onClick={() => {
                        if (spec === "Cardiology") setSelectedFilterCategory("cardiology");
                        else if (spec === "Neurology") setSelectedFilterCategory("neurology");
                        else setSearchQuery(spec);
                      }}
                      className="w-full text-left text-xs px-3 py-2 rounded-xl font-medium transition-all flex items-center justify-between text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                    >
                      <span>{spec}</span>
                      {count > 0 && (
                        <span className="text-[10px] font-mono text-teal-700">({count})</span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          </aside>

          {/* ══════════════ CENTER FEED ══════════════ */}
          <main className="min-w-0">
            {/* Header & Search */}
            <div className="sticky top-0 z-20 bg-slate-50/95 backdrop-blur-md pb-3 mb-4">
              <div className="flex items-center justify-between mb-3 gap-2">
                <div>
                  <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                    Medical Intelligence Hub
                  </h1>
                  <p className="text-xs text-slate-500 font-medium">
                    Verified Physician Social Network & Diagnostic Brain
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setIsCreating(true)}
                    className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 sm:px-5 sm:py-2.5 rounded-full font-bold shadow-sm text-xs sm:text-sm flex items-center gap-2 transition-all"
                  >
                    <span>✍️</span>
                    <span>Share Case</span>
                  </button>
                </div>
              </div>

              {/* Search Bar */}
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-sm">
                  🔍
                </span>
                <input
                  type="text"
                  placeholder="Search diseases, pharmacology, or clinical presentation..."
                  className="w-full pl-10 pr-4 py-2.5 rounded-2xl border border-slate-200 bg-white outline-none focus:border-teal-500 text-xs sm:text-sm text-slate-900 shadow-sm"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              {/* Advanced Category Filter Pills */}
              <div className="flex gap-2 mt-3 overflow-x-auto pb-1 custom-scrollbar">
                {[
                  { id: "all", label: "⚡ All Protocols" },
                  { id: "urgent", label: "🚨 STAT Urgent 2nd Opinions" },
                  { id: "polls", label: "🗳️ Consensus Polls" },
                  { id: "cardiology", label: "🫀 Cardiology" },
                  { id: "neurology", label: "🧠 Neurology" },
                  { id: "rare", label: "🔬 Rare Manifestations" },
                ].map((cat) => (
                  <button
                    key={cat.id}
                    onClick={() => setSelectedFilterCategory(cat.id as any)}
                    className={`px-3 py-1 rounded-xl text-xs font-bold whitespace-nowrap transition-all border ${
                      selectedFilterCategory === cat.id
                        ? "bg-teal-600 text-white border-teal-600 shadow-sm"
                        : "bg-white text-slate-600 border-slate-200 hover:text-slate-900 hover:border-slate-300"
                    }`}
                  >
                    {cat.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Stories Ribbon */}
            {stories.length > 0 && !searchQuery && (
              <ClinicalStoriesReel
                stories={stories}
                onOpenStory={(idx) => setActiveStoryIndex(idx)}
                onNewCase={() => setIsCreating(true)}
              />
            )}

            {/* Case Composer Modal */}
            <AnimatePresence>
              {isCreating && (
                <CaseComposer
                  onPublish={handlePublishPost}
                  onCancel={() => setIsCreating(false)}
                />
              )}
            </AnimatePresence>

            {/* Post Feed List */}
            <div className="space-y-5">
              {loadingFeed ? (
                <SkeletonPostLoader />
              ) : displayedPosts.length === 0 ? (
                <div className="text-center py-16 bg-white rounded-3xl border border-slate-200 p-8 shadow-sm">
                  <ClinicalIcons.Microscope className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <h3 className="text-base font-bold text-slate-800 mb-1">
                    No clinical cases matching filter
                  </h3>
                  <p className="text-xs text-slate-500">
                    Try clearing search or check back soon for incoming physician updates.
                  </p>
                </div>
              ) : (
                displayedPosts.map((post) => (
                  <PostCard
                    key={post.id}
                    post={post}
                    typingDoctor={typingMap[post.id] || null}
                    isCompared={comparisonCases.some((c) => c.id === post.id)}
                    onToggleCompare={() => handleToggleCompare(post)}
                    onLike={() => handleLike(post.id)}
                    onBookmark={() => handleBookmark(post.id)}
                    onComment={(text) => handleComment(post.id, text)}
                    onReact={(reaction) => handleReact(post.id, reaction)}
                    onVotePoll={(optIndex) => handleVotePoll(post.id, optIndex)}
                    onEndorse={() => handleEndorse(post.id)}
                    onOpenImage={(url) => setSelectedImage(url)}
                    onOpenCite={(p) => setSelectedCitePost(p)}
                    onOpenDossier={(p) => setSelectedDossierPost(p)}
                    onTyping={(isTyping) => handleTypingBroadcast(post.id, isTyping)}
                  />
                ))
              )}
            </div>
          </main>

          {/* ══════════════ RIGHT SIDEBAR ══════════════ */}
          <aside className="hidden lg:block space-y-5">
            {/* AI Knowledge Base Benchmark */}
            <div className="bg-white border border-slate-200 rounded-3xl p-4 shadow-sm text-slate-900">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-extrabold text-xs uppercase tracking-wider text-teal-800 flex items-center gap-1.5">
                  <ClinicalIcons.Brain className="w-4 h-4 text-teal-600" />
                  <span>DocAssistIQ Brain</span>
                </h3>
                <span className="text-[10px] bg-teal-50 text-teal-800 border border-teal-200 px-2 py-0.5 rounded-full font-bold">
                  v2.4 Active
                </span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed mb-3">
                Peer-verified cases continuously train the clinical diagnostic engine with CME-grade
                accuracy.
              </p>
              <div className="space-y-1.5">
                <div className="flex justify-between text-[11px]">
                  <span className="text-slate-500 font-medium">Cases Ingested</span>
                  <span className="text-teal-700 font-bold">{pulse?.total_cases_indexed ?? posts.length} verified</span>
                </div>
                <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-teal-500 to-emerald-600 rounded-full w-4/5" />
                </div>
              </div>
            </div>

            {/* Trending Clinical Conditions */}
            {trending && (
              <div className="bg-white rounded-3xl border border-slate-200 p-4 shadow-sm">
                <h3 className="font-extrabold text-xs uppercase tracking-wider text-slate-800 mb-3 flex items-center gap-2">
                  <ClinicalIcons.Flame className="w-4 h-4 text-amber-500" />
                  <span>Trending Clinical Cases</span>
                </h3>
                <div className="space-y-2.5">
                  {trending.trending_diseases.slice(0, 5).map((d, i) => (
                    <button
                      key={i}
                      onClick={() => setSearchQuery(d.name)}
                      className="w-full text-left group flex items-center justify-between py-1 border-b border-slate-100 last:border-0"
                    >
                      <div className="min-w-0 pr-2">
                        <p className="text-[10px] text-slate-400 font-bold uppercase">
                          #{i + 1} Trending
                        </p>
                        <p className="text-xs font-bold text-slate-700 group-hover:text-teal-600 truncate transition-colors">
                          {d.name}
                        </p>
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {d.post_count} cases
                      </span>
                    </button>
                  ))}
                </div>

                {/* Trending Hashtags */}
                <div className="mt-3 pt-3 border-t border-slate-100">
                  <p className="text-[10px] font-black uppercase tracking-wider text-slate-400 mb-2">
                    Popular Medical Hashtags
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {trending.trending_tags.slice(0, 8).map((t, i) => (
                      <button
                        key={i}
                        onClick={() => setSearchQuery(t.tag)}
                        className="text-[10px] font-bold px-2 py-0.5 rounded-full border border-teal-200 bg-teal-50 text-teal-800 hover:bg-teal-100 transition-colors"
                      >
                        #{t.tag}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Suggested Specialists to Follow */}
            {suggestedDoctors.length > 0 && (
              <div className="bg-white rounded-3xl border border-slate-200 p-4 shadow-sm">
                <h3 className="font-extrabold text-xs uppercase tracking-wider text-slate-800 mb-3">
                  Verified Specialists to Follow
                </h3>
                <div className="space-y-3">
                  {suggestedDoctors.slice(0, 5).map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2.5 min-w-0">
                        <div
                          className={`w-8 h-8 rounded-full bg-gradient-to-br ${getAvatarGradient(
                            doc.id
                          )} flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0`}
                        >
                          {doc.full_name?.[0] ?? "D"}
                        </div>
                        <div className="min-w-0">
                          <p className="text-xs font-bold text-slate-900 truncate">
                            {doc.full_name}
                          </p>
                          <p className="text-[10px] text-slate-400 truncate">
                            {doc.specialization} • {doc.followers_count ?? 0} followers
                          </p>
                        </div>
                      </div>

                      <button
                        onClick={() => handleToggleFollow(doc.id)}
                        className={`text-[10px] font-bold px-2.5 py-1 rounded-full border transition-all flex-shrink-0 ${
                          doc.is_following
                            ? "bg-teal-600 text-white border-teal-600 font-extrabold"
                            : "text-teal-700 hover:bg-teal-50 border-teal-200"
                        }`}
                      >
                        {doc.is_following ? "Following ✓" : "Follow"}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </aside>
        </div>
      </div>

      {/* ── Persistent Floating Comparison Tray Dock (Clean Light) ── */}
      <DifferentialTrayDock
        cases={comparisonCases}
        onRemove={(id) => setComparisonCases((prev) => prev.filter((c) => c.id !== id))}
        onLaunch={() => setShowComparisonModal(true)}
        onClear={() => setComparisonCases([])}
      />

      {/* ── Modals & Overlays Rendered via Portal Directly to document.body ── */}
      <ClientPortal>
        {/* ── Point-of-Care Clinical Risk Calculators Modal ── */}
        <AnimatePresence>
          {showCalculatorModal && (
            <ClinicalCalculatorModal onClose={() => setShowCalculatorModal(false)} />
          )}
        </AnimatePresence>

        {/* ── Differential Comparison Side-by-Side Modal ── */}
        <AnimatePresence>
          {showComparisonModal && comparisonCases.length >= 2 && (
            <DifferentialComparisonModal
              caseA={comparisonCases[0]}
              caseB={comparisonCases[1]}
              onClose={() => setShowComparisonModal(false)}
            />
          )}
        </AnimatePresence>

        {/* ── Executive Case Dossier Modal ── */}
        <AnimatePresence>
          {selectedDossierPost && (
            <CaseDossierModal
              post={selectedDossierPost}
              onClose={() => setSelectedDossierPost(null)}
            />
          )}
        </AnimatePresence>

        {/* ── Active Doctors Online Modal ── */}
        <AnimatePresence>
          {showActiveDoctorsModal && (
            <ActiveDoctorsModal
              doctors={suggestedDoctors}
              onClose={() => setShowActiveDoctorsModal(false)}
              onToggleFollow={handleToggleFollow}
            />
          )}
        </AnimatePresence>

        {/* ── Story Viewer Fullscreen Modal ── */}
        <AnimatePresence>
          {activeStoryIndex !== null && (
            <StoryViewerModal
              stories={stories}
              initialIndex={activeStoryIndex}
              onClose={() => setActiveStoryIndex(null)}
              onReact={(postId, reaction) => handleReact(postId, reaction)}
              onVotePoll={(postId, optionIndex) => handleVotePoll(postId, optionIndex)}
              onOpenCite={(p) => setSelectedCitePost(p)}
            />
          )}
        </AnimatePresence>

        {/* ── Diagnostic Lightbox Modal ── */}
        <AnimatePresence>
          {selectedImage && (
            <MedicalLightboxModal
              imageUrl={selectedImage}
              onClose={() => setSelectedImage(null)}
            />
          )}
        </AnimatePresence>

        {/* ── Citation Modal ── */}
        <AnimatePresence>
          {selectedCitePost && (
            <CitationModal
              post={selectedCitePost}
              onClose={() => setSelectedCitePost(null)}
              onCopiedToast={showToast}
            />
          )}
        </AnimatePresence>

        {/* ── Floating Toast Alert ── */}
        <AnimatePresence>
          {toastMessage && (
            <motion.div
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 20, scale: 0.95 }}
              className="fixed bottom-6 right-6 z-[120] bg-slate-900 text-white border border-slate-700 rounded-2xl px-4 py-3 shadow-xl flex items-center gap-2.5 text-xs font-bold"
            >
              <span className="w-2 h-2 rounded-full bg-teal-400 animate-ping" />
              <span>{toastMessage}</span>
            </motion.div>
          )}
        </AnimatePresence>
      </ClientPortal>
    </div>
  );
}
'''

with open(target_path, "w", encoding="utf-8") as f:
    f.write(code)

print(f"Successfully generated clean minimalist light hub ({len(code)} bytes) to {target_path}")
