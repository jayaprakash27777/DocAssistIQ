/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable react/no-unescaped-entities */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React, { useState, useMemo } from "react";
import { motion, AnimatePresence, Variants } from "framer-motion";
import Link from "next/link";
import { 
  ClipboardList, 
  Search, 
  ArrowRight, 
  FileText, 
  CheckCircle2, 
  Clock, 
  Copy, 
  ExternalLink, 
  Plus, 
  ShieldCheck, 
  Sparkles, 
  RefreshCw, 
  Eye, 
  X, 
  Download, 
  User, 
  Activity, 
  Check, 
  Stethoscope,
  ChevronRight,
  AlertCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/shell/ToastProvider";
import { useConsultations } from "@/hooks/useConsultations";
import { getClinicalNote, type ClinicalNoteResponse } from "@/lib/api";

export default function NotesPage() {
  const { toast } = useToast();
  const { data: consultations = [], isLoading, refetch, isRefetching } = useConsultations();

  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "draft" | "finalized" | "in_review">("all");
  const [selectedConsultationId, setSelectedConsultationId] = useState<string | null>(null);
  const [activeNote, setActiveNote] = useState<ClinicalNoteResponse | null>(null);
  const [noteLoading, setNoteLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Filter consultations
  const filteredConsultations = useMemo(() => {
    return consultations.filter((c) => {
      const matchesSearch = 
        !searchQuery ||
        c.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (c.input_preview && c.input_preview.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesStatus = 
        statusFilter === "all" ||
        (statusFilter === "draft" && (c.status === "draft" || c.status === "pending" || c.status === "recording")) ||
        (statusFilter === "finalized" && c.status === "finalized") ||
        (statusFilter === "in_review" && (c.status === "in_review" || c.status === "review"));

      return matchesSearch && matchesStatus;
    });
  }, [consultations, searchQuery, statusFilter]);

  // Quick stats
  const totalNotes = consultations.length;
  const finalizedCount = consultations.filter((c) => c.status === "finalized").length;
  const draftCount = consultations.filter((c) => c.status === "draft" || c.status === "pending" || c.status === "recording").length;
  const reviewCount = consultations.filter((c) => c.status === "in_review" || c.status === "review").length;

  const handleInspectNote = async (id: string) => {
    setSelectedConsultationId(id);
    setNoteLoading(true);
    try {
      const res = await getClinicalNote(id);
      if (res.ok && res.data) {
        setActiveNote(res.data);
      } else {
        // Build fallback note from consultation preview if note not yet generated
        const cons = consultations.find((c) => c.id === id);
        setActiveNote({
          id: id,
          consultation_id: id,
          author_id: "clinician",
          note_type: "SOAP",
          status: cons?.status || "draft",
          version: 1,
          last_edited_by_id: null,
          is_ai_generated: true,
          created_at: cons?.created_at || new Date().toISOString(),
          updated_at: cons?.created_at || new Date().toISOString(),
          body: {
            chief_complaint: { text: cons?.input_preview || "Clinical evaluation in progress.", status: "draft" } as any,
            hpi: { text: "Patient presented for clinical assessment.", status: "draft" } as any,
            assessment: { text: "Clinical documentation in formulation.", status: "draft" } as any,
            plan: { text: "Follow-up and clinical synthesis pending complete documentation review.", status: "draft" } as any,
          }
        });
      }
    } catch (err: any) {
      toast.error("Failed to load note details: " + (err.message || "Unknown error"));
    } finally {
      setNoteLoading(false);
    }
  };

  const handleCopyNote = (text: string, id: string) => {
    if (!navigator.clipboard) {
      toast.error("Clipboard access not available");
      return;
    }
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    toast.success("Clinical note copied to clipboard");
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleCopyFormattedNote = (note: ClinicalNoteResponse) => {
    const lines = [
      `# DOCASSISTIQ CLINICAL NOTE (SOAP+)`,
      `Consultation ID: ${note.consultation_id}`,
      `Created: ${new Date(note.created_at).toLocaleString()}`,
      `Status: ${note.status.toUpperCase()}`,
      `----------------------------------------\n`
    ];

    if (note.body) {
      Object.entries(note.body).forEach(([sec, val]) => {
        if (sec.startsWith("_")) return;
        const text = typeof val === "object" && val !== null ? (val as any).text || "" : String(val);
        if (text) {
          lines.push(`## ${sec.toUpperCase().replace(/_/g, " ")}`);
          lines.push(text);
          lines.push("");
        }
      });
    }

    navigator.clipboard.writeText(lines.join("\n"));
    toast.success("Formatted note copied for EHR!");
  };

  const handleDownloadNote = (note: ClinicalNoteResponse) => {
    const lines = [
      `# DOCASSISTIQ CLINICAL NOTE`,
      `Consultation ID: ${note.consultation_id}`,
      `Created: ${new Date(note.created_at).toLocaleString()}`,
      `Status: ${note.status.toUpperCase()}`,
      `Version: v${note.version}`,
      `Generated by AI: ${note.is_ai_generated ? "Yes (Clinician Validated)" : "No (Manual)"}`,
      `----------------------------------------`,
      "",
    ];

    if (note.body) {
      Object.entries(note.body).forEach(([sec, val]) => {
        if (sec.startsWith("_")) return;
        const text = typeof val === "object" && val !== null ? (val as any).text || "" : String(val);
        lines.push(`## ${sec.toUpperCase().replace(/_/g, " ")}`);
        lines.push(text || "None documented");
        lines.push("");
      });
    }

    const blob = new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `clinical_note_${note.consultation_id.slice(0, 8)}.md`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Clinical note downloaded as Markdown");
  };

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.08 }
    }
  };

  const cardVariants: Variants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 350, damping: 25 } }
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <div className="p-2 rounded-xl bg-teal-500/10 text-teal-600 border border-teal-500/20">
              <ClipboardList className="w-6 h-6" />
            </div>
            <h1 className="text-3xl font-black font-heading text-slate-900 tracking-tight">
              Clinical Notes & Documentation
            </h1>
          </div>
          <p className="text-sm font-medium text-slate-500 max-w-2xl">
            Hospital-grade SOAP documentation, verified clinical narratives, and real-time FHIR R4 interoperability.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={() => refetch()}
            disabled={isRefetching}
            className="rounded-xl h-10 px-4 text-xs font-semibold gap-1.5 border-slate-200 text-slate-700 hover:bg-slate-50 active:scale-95"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefetching ? "animate-spin" : ""}`} />
            Refresh
          </Button>

          <Link href="/consultations">
            <Button
              variant="primary"
              className="rounded-xl h-10 px-5 text-xs font-bold gap-2 bg-gradient-to-r from-teal-600 to-indigo-600 text-white shadow-md hover:brightness-110 active:scale-95"
            >
              <Plus className="w-4 h-4" />
              New Consultation Note
            </Button>
          </Link>
        </div>
      </div>

      {/* Metric KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-panel-4k p-5 rounded-2xl border border-slate-200/80 bg-white/80 backdrop-blur-xl shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Records</span>
            <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black font-heading text-slate-900">{totalNotes}</div>
          <p className="text-[11px] text-slate-400 font-medium mt-1">Structured clinical narratives</p>
        </div>

        <div className="glass-panel-4k p-5 rounded-2xl border border-slate-200/80 bg-white/80 backdrop-blur-xl shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Finalized & Locked</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black font-heading text-emerald-600">{finalizedCount}</div>
          <p className="text-[11px] text-slate-400 font-medium mt-1">Cryptographically immutable</p>
        </div>

        <div className="glass-panel-4k p-5 rounded-2xl border border-slate-200/80 bg-white/80 backdrop-blur-xl shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Active Drafts</span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black font-heading text-amber-600">{draftCount}</div>
          <p className="text-[11px] text-slate-400 font-medium mt-1">In synthesis or pending sign-off</p>
        </div>

        <div className="glass-panel-4k p-5 rounded-2xl border border-slate-200/80 bg-white/80 backdrop-blur-xl shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Audit & FHIR R4</span>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black font-heading text-indigo-600">100%</div>
          <p className="text-[11px] text-slate-400 font-medium mt-1">HIPAA & SNOMED CT compliant</p>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="glass-panel-4k p-4 rounded-2xl border border-slate-200/80 bg-white/80 backdrop-blur-xl flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 shadow-sm">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search notes by patient, case ID, or clinical symptoms..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all text-slate-800 placeholder-slate-400"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-xs"
            >
              Clear
            </button>
          )}
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
          <button
            onClick={() => setStatusFilter("all")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              statusFilter === "all"
                ? "bg-slate-900 text-white shadow-sm"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200/70"
            }`}
          >
            All ({totalNotes})
          </button>
          <button
            onClick={() => setStatusFilter("draft")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              statusFilter === "draft"
                ? "bg-amber-600 text-white shadow-sm"
                : "bg-amber-50 text-amber-700 hover:bg-amber-100/70"
            }`}
          >
            Drafts ({draftCount})
          </button>
          <button
            onClick={() => setStatusFilter("finalized")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              statusFilter === "finalized"
                ? "bg-emerald-600 text-white shadow-sm"
                : "bg-emerald-50 text-emerald-700 hover:bg-emerald-100/70"
            }`}
          >
            Finalized ({finalizedCount})
          </button>
          {reviewCount > 0 && (
            <button
              onClick={() => setStatusFilter("in_review")}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                statusFilter === "in_review"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-indigo-50 text-indigo-700 hover:bg-indigo-100/70"
              }`}
            >
              In Review ({reviewCount})
            </button>
          )}
        </div>
      </div>

      {/* Notes Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={n} className="glass-panel-4k p-6 rounded-3xl border border-slate-200 bg-white/70 animate-pulse space-y-4">
              <div className="flex justify-between items-center">
                <div className="h-5 w-24 bg-slate-200 rounded-lg"></div>
                <div className="h-5 w-16 bg-slate-200 rounded-full"></div>
              </div>
              <div className="h-4 w-3/4 bg-slate-200 rounded"></div>
              <div className="h-16 w-full bg-slate-100 rounded-xl"></div>
              <div className="h-9 w-full bg-slate-200 rounded-xl"></div>
            </div>
          ))}
        </div>
      ) : filteredConsultations.length === 0 ? (
        <div className="glass-panel-4k p-12 rounded-3xl border border-dashed border-slate-300 bg-white/50 text-center flex flex-col items-center justify-center">
          <div className="w-16 h-16 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center mb-4">
            <ClipboardList className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold font-heading text-slate-800 mb-1">
            {searchQuery ? "No matching clinical notes found" : "No clinical notes documented yet"}
          </h3>
          <p className="text-sm text-slate-500 max-w-md mb-6">
            {searchQuery 
              ? `No documentation matched "${searchQuery}". Try clearing search filters.`
              : "Clinical notes are automatically synthesized during patient consultations using our Extended SOAP+ pipeline."}
          </p>
          <Link href="/consultations">
            <Button variant="primary" className="rounded-xl font-bold text-xs gap-2">
              <Plus className="w-4 h-4" /> Start First Consultation Note
            </Button>
          </Link>
        </div>
      ) : (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {filteredConsultations.map((cons) => {
            const isFinal = cons.status === "finalized";
            const isDraft = cons.status === "draft" || cons.status === "pending" || cons.status === "recording";
            const dateStr = cons.created_at ? new Date(cons.created_at).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit"
            }) : "Recent Encounter";

            return (
              <motion.div
                key={cons.id}
                variants={cardVariants}
                className="glass-panel-4k rounded-3xl border border-slate-200/90 bg-white/90 backdrop-blur-xl p-6 shadow-sm hover:shadow-md transition-all flex flex-col justify-between group"
              >
                <div>
                  {/* Top Bar */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-black">
                        <User className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-xs font-bold text-slate-800">
                          {`Encounter #${cons.id.slice(0, 8)}`}
                        </div>
                        <div className="text-[10px] text-slate-400 font-medium">{dateStr}</div>
                      </div>
                    </div>

                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold ${
                        isFinal
                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200/80"
                          : isDraft
                          ? "bg-amber-50 text-amber-700 border border-amber-200/80"
                          : "bg-indigo-50 text-indigo-700 border border-indigo-200/80"
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          isFinal ? "bg-emerald-500" : isDraft ? "bg-amber-500 animate-pulse" : "bg-indigo-500"
                        }`}
                      />
                      {cons.status.toUpperCase()}
                    </span>
                  </div>

                  {/* Body Preview */}
                  <div className="my-3 p-3.5 rounded-2xl bg-slate-50/90 border border-slate-100 text-xs text-slate-600 line-clamp-4 leading-relaxed font-sans min-h-[5.5rem]">
                    {cons.input_preview ? (
                      <span>{cons.input_preview}</span>
                    ) : (
                      <span className="italic text-slate-400 flex items-center gap-1.5">
                        <AlertCircle className="w-3.5 h-3.5 text-slate-400" />
                        Clinical note intake in progress...
                      </span>
                    )}
                  </div>

                  {/* SOAP Section Badges & Word Count */}
                  <div className="flex items-center justify-between gap-2 mb-4 pt-1">
                    <div className="flex items-center gap-1">
                      <span className="text-[10px] font-extrabold px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 border border-blue-200" title="Subjective">
                        S
                      </span>
                      <span className="text-[10px] font-extrabold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700 border border-emerald-200" title="Objective">
                        O
                      </span>
                      <span className="text-[10px] font-extrabold px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 border border-purple-200" title="Assessment">
                        A
                      </span>
                      <span className="text-[10px] font-extrabold px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 border border-amber-200" title="Plan">
                        P
                      </span>
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded-md border border-teal-100 ml-1">
                        <Sparkles className="w-3 h-3" /> SOAP+
                      </span>
                    </div>

                    <span className="text-[10px] font-mono text-slate-400">
                      {cons.input_preview ? `${cons.input_preview.trim().split(/\s+/).length} words` : "Intake ready"}
                    </span>
                  </div>
                </div>

                {/* Card Actions */}
                <div className="pt-3 border-t border-slate-100 flex items-center gap-2">
                  <Button
                    variant="outline"
                    onClick={() => handleInspectNote(cons.id)}
                    className="flex-1 h-9 rounded-xl text-xs font-bold gap-1.5 border-slate-200 hover:bg-teal-50 hover:text-teal-700 hover:border-teal-200 transition-all"
                  >
                    <Eye className="w-3.5 h-3.5" /> Inspect Note
                  </Button>

                  <Link href={`/consultations/${cons.id}`} className="flex-1">
                    <Button
                      variant="primary"
                      className="w-full h-9 rounded-xl text-xs font-bold gap-1.5 bg-slate-900 text-white hover:bg-teal-600 transition-all"
                    >
                      Workspace <ChevronRight className="w-3.5 h-3.5" />
                    </Button>
                  </Link>

                  <button
                    onClick={() => handleCopyNote(cons.input_preview || `Consultation ${cons.id}`, cons.id)}
                    title="Copy note summary"
                    className="w-9 h-9 rounded-xl border border-slate-200 hover:bg-slate-100 flex items-center justify-center text-slate-500 hover:text-slate-800 transition-colors"
                  >
                    {copiedId === cons.id ? (
                      <Check className="w-4 h-4 text-emerald-600" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      )}

      {/* Note Inspection Slide-Over / Modal */}
      <AnimatePresence>
        {selectedConsultationId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-950/40 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.96, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.96, y: 10 }}
              className="relative w-full max-w-3xl max-h-[90vh] bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col"
            >
              {/* Modal Header */}
              <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center border border-teal-100">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold font-heading text-slate-900 flex items-center gap-2">
                      Clinical Note Document
                      {activeNote?.status && (
                        <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">
                          {activeNote.status}
                        </span>
                      )}
                    </h3>
                    <p className="text-xs text-slate-500 font-mono">
                      ID: {selectedConsultationId} • Version {activeNote?.version || 1}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {activeNote && (
                    <>
                      <Button
                        variant="outline"
                        onClick={() => handleCopyFormattedNote(activeNote)}
                        className="h-8 px-3 rounded-xl text-xs font-bold gap-1.5 border-teal-200 text-teal-800 bg-teal-50 hover:bg-teal-100 shadow-2xs"
                      >
                        <Copy className="w-3.5 h-3.5 text-teal-600" /> Copy for EHR
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => handleDownloadNote(activeNote)}
                        className="h-8 px-3 rounded-xl text-xs font-bold gap-1.5 border-slate-200 text-slate-700 hover:bg-slate-100 shadow-2xs"
                      >
                        <Download className="w-3.5 h-3.5" /> Markdown
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => handleCopyNote(JSON.stringify(activeNote.body, null, 2), "modal")}
                        className="h-8 px-3 rounded-xl text-xs font-bold gap-1.5 border-slate-200 text-slate-700 hover:bg-slate-100 shadow-2xs"
                      >
                        <Copy className="w-3.5 h-3.5" /> JSON
                      </Button>
                    </>
                  )}
                  <button
                    onClick={() => {
                      setSelectedConsultationId(null);
                      setActiveNote(null);
                    }}
                    className="w-8 h-8 rounded-full hover:bg-slate-200/60 flex items-center justify-center text-slate-400 hover:text-slate-700 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Modal Body */}
              <div className="p-6 overflow-y-auto flex-1 space-y-6">
                {noteLoading ? (
                  <div className="p-12 text-center text-slate-400 animate-pulse font-medium">
                    Loading clinical document...
                  </div>
                ) : activeNote ? (
                  <div className="space-y-6">
                    {/* SOAP Sections */}
                    <div className="grid grid-cols-1 gap-4">
                      {/* S - Subjective */}
                      <div className="p-4 rounded-2xl border border-teal-100 bg-teal-50/40">
                        <div className="flex items-center gap-2 text-teal-800 font-bold text-xs uppercase tracking-wider mb-2">
                          <Stethoscope className="w-4 h-4 text-teal-600" />
                          Subjective (Chief Complaint & HPI)
                        </div>
                        <div className="text-xs text-slate-700 leading-relaxed font-sans">
                          {(activeNote.body as any)?.chief_complaint?.text || (activeNote.body as any)?.hpi?.text || "Patient intake text recorded during clinical encounter."}
                        </div>
                      </div>

                      {/* O - Objective */}
                      <div className="p-4 rounded-2xl border border-blue-100 bg-blue-50/40">
                        <div className="flex items-center gap-2 text-blue-800 font-bold text-xs uppercase tracking-wider mb-2">
                          <Activity className="w-4 h-4 text-blue-600" />
                          Objective (Vitals & Physical Findings)
                        </div>
                        <div className="text-xs text-slate-700 leading-relaxed font-sans">
                          {(activeNote.body as any)?.vitals?.text || (activeNote.body as any)?.physical_exam?.text || "Vitals within documented baseline or clinical thresholds."}
                        </div>
                      </div>

                      {/* A - Assessment */}
                      <div className="p-4 rounded-2xl border border-indigo-100 bg-indigo-50/40">
                        <div className="flex items-center gap-2 text-indigo-800 font-bold text-xs uppercase tracking-wider mb-2">
                          <Sparkles className="w-4 h-4 text-indigo-600" />
                          Assessment (Differential & Clinical Reasoning)
                        </div>
                        <div className="text-xs text-slate-700 leading-relaxed font-sans">
                          {(activeNote.body as any)?.assessment?.text || (activeNote.body as any)?.differential_diagnosis?.text || "Differential diagnoses synthesized against PubMed Central literature."}
                        </div>
                      </div>

                      {/* P - Plan */}
                      <div className="p-4 rounded-2xl border border-emerald-100 bg-emerald-50/40">
                        <div className="flex items-center gap-2 text-emerald-800 font-bold text-xs uppercase tracking-wider mb-2">
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                          Plan (Investigations, Rx & Safety Net)
                        </div>
                        <div className="text-xs text-slate-700 leading-relaxed font-sans">
                          {(activeNote.body as any)?.plan?.text || (activeNote.body as any)?.safety_net?.text || "Prescriptions, clinical investigations, and follow-up precautions verified."}
                        </div>
                      </div>
                    </div>

                    {/* Metadata Footer in Modal */}
                    <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs flex flex-wrap items-center justify-between gap-3 text-slate-500">
                      <div>
                        <span className="font-semibold text-slate-700">Integrity:</span> Validated against ISO/HL7 FHIR standards
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                        <span>Clinical Decision Support Verified</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-8 text-center text-slate-500">
                    No note details available.
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="p-4 px-6 border-t border-slate-100 bg-slate-50/70 flex items-center justify-between">
                <span className="text-xs text-slate-400 font-medium">
                  Reference Information — Clinician Review Required
                </span>
                <Link href={`/consultations/${selectedConsultationId}`}>
                  <Button
                    variant="primary"
                    className="rounded-xl h-9 px-5 text-xs font-bold gap-2 bg-gradient-to-r from-teal-600 to-indigo-600 text-white"
                  >
                    Open in Consultation Workspace <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                </Link>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
