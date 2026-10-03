/* eslint-disable @typescript-eslint/no-unused-vars */
"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import NoteReviewWorkspace from "@/components/clinical/NoteReviewWorkspace";
import { PLACEHOLDER_LABEL } from "@/lib/api";
import { ChevronLeft, Copy, Check, FileCheck, Sparkles, ArrowRight, ShieldCheck, Brain } from "lucide-react";
import { useToast } from "@/components/shell/ToastProvider";

export default function NoteReviewPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;
  const [copiedId, setCopiedId] = useState(false);

  if (!id) {
    return (
      <div className="flex items-center justify-center min-h-[50vh] p-8 text-center text-red-500">
        Invalid Consultation Encounter ID
      </div>
    );
  }

  const handleCopyId = () => {
    navigator.clipboard.writeText(id);
    setCopiedId(true);
    toast.success("Encounter ID copied");
    setTimeout(() => setCopiedId(false), 2000);
  };

  return (
    <div className="review-workspace-root flex flex-col h-full min-h-0 overflow-hidden relative w-full bg-[var(--surface-base)]">
      {/* ── Tier 1: Executive Review Header ────────────────────────────────────────── */}
      <header className="px-4 sm:px-6 py-2.5 border-b border-slate-200/90 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl shadow-xs flex flex-wrap items-center justify-between gap-3 shrink-0 z-20">
        <div className="flex items-center gap-3 min-w-0">
          <Link
            href={`/consultations/${id}`}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 bg-slate-100/90 dark:bg-slate-800/90 hover:bg-slate-200/90 transition-colors border border-slate-200/60 dark:border-slate-700/60 shrink-0"
            title="Return to primary consultation room"
          >
            <ChevronLeft className="w-4 h-4 text-slate-500" />
            <span>Consultation Room</span>
          </Link>
          <span className="text-slate-300 dark:text-slate-700 hidden sm:inline">/</span>

          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-base sm:text-lg font-black text-slate-900 dark:text-white tracking-tight font-heading m-0">
                Clinical Note Review &amp; Verification
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 shrink-0">
                Pre-Signature
              </span>
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider hidden sm:inline">
                {PLACEHOLDER_LABEL}
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 font-medium hidden md:block">
              Verify AI-extracted clinical findings, review diarized source transcript, and sign off extended SOAP+ note.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <button
            type="button"
            onClick={handleCopyId}
            className="hidden sm:inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 font-mono transition-colors bg-slate-50 dark:bg-slate-800/60 px-2.5 py-1.5 rounded-xl border border-slate-200/80 dark:border-slate-700/80"
            title="Click to copy full encounter ID"
          >
            <span>ENC #{id.slice(0, 8)}</span>
            {copiedId ? (
              <Check className="w-3.5 h-3.5 text-emerald-600" />
            ) : (
              <Copy className="w-3.5 h-3.5 opacity-60" />
            )}
          </button>

          <Link
            href={`/ai?cid=${id}`}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-indigo-800 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-950/40 hover:bg-indigo-100 border border-indigo-200/80 dark:border-indigo-800 transition-colors shadow-2xs"
            title="Ask DocAssist IQ AI questions or generate certified clinical documents"
          >
            <Brain className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
            <span>DocAssist IQ AI</span>
          </Link>

          <Link
            href={`/consultations/${id}/intake`}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-teal-800 dark:text-teal-300 bg-teal-50 dark:bg-teal-950/40 hover:bg-teal-100 border border-teal-200/80 dark:border-teal-800 transition-colors shadow-2xs"
            title="View structured intake answers"
          >
            <Sparkles className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
            <span className="hidden sm:inline">Intake Form</span>
          </Link>

          <Link 
            href={`/consultations/${id}`}
            className="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-bold text-white bg-gradient-to-r from-teal-600 via-indigo-600 to-indigo-700 hover:from-teal-500 hover:to-indigo-600 rounded-xl shadow-md shadow-indigo-600/20 transition-all"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Complete in Workspace</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </header>

      {/* ── Main Review Canvas ──────────────────────────────────────────────────────── */}
      <div className="flex-1 min-h-0 overflow-hidden p-3 sm:p-5 lg:p-6 bg-slate-50/60">
        <NoteReviewWorkspace consultationId={id} />
      </div>
    </div>
  );
}
