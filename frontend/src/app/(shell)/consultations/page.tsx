"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/shell/ToastProvider";
import { 
  Search, Stethoscope, PlusCircle, Clock, FileText, ArrowRight, UserCircle,
  Copy, Check, FileCheck, ShieldCheck, Radio, Brain, Tag
} from "lucide-react";
import { motion, AnimatePresence, Variants } from "framer-motion";
import { useConsultations, useSearchConsultations, useCreateConsultation } from "@/hooks/useConsultations";

type StatusFilter = "all" | "recording" | "in_review" | "finalized";

export default function ConsultationsListPage() {
  const { toast } = useToast();
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery.trim()), 400);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const { data: listData, isLoading: isListLoading } = useConsultations();
  const { data: searchData, isLoading: isSearchLoading } = useSearchConsultations(debouncedQuery);
  const createMutation = useCreateConsultation();

  const handleCreate = async () => {
    try {
      const data = await createMutation.mutateAsync();
      toast.success("New consultation initiated");
      router.push(`/consultations/${data.id}`);
    } catch (e: unknown) {
      toast.error((e as Error)?.message || "Failed to initiate session");
    }
  };

  const handleCopyId = (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    e.stopPropagation();
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    toast.success("Encounter ID copied");
    setTimeout(() => setCopiedId(null), 2000);
  };

  const isSearching = debouncedQuery.length >= 3;
  const loading = isSearching ? isSearchLoading : isListLoading;
  const creating = createMutation.isPending;

  const rawConsultations = useMemo(() => {
    return isSearching ? (searchData || []) : (listData || []);
  }, [isSearching, searchData, listData]);

  // Filter consultations by search query and selected status tab
  const filteredConsultations = useMemo(() => {
    let list = rawConsultations;
    if (searchQuery.trim() && !isSearching) {
      const q = searchQuery.toLowerCase();
      list = list.filter(c => 
        c.id.toLowerCase().includes(q) ||
        (c.patient_ref && c.patient_ref.toLowerCase().includes(q)) ||
        (c.input_preview && c.input_preview.toLowerCase().includes(q))
      );
    }
    if (statusFilter === "all") return list;
    if (statusFilter === "recording") return list.filter(c => c.status === "recording");
    if (statusFilter === "in_review") return list.filter(c => ["draft", "under_review", "analysis_ready"].includes(c.status));
    if (statusFilter === "finalized") return list.filter(c => ["finalized", "amended", "completed"].includes(c.status));
    return list;
  }, [rawConsultations, statusFilter, searchQuery, isSearching]);

  // Aggregate metrics
  const totalCount = listData?.length || 0;
  const recordingCount = listData?.filter(c => c.status === "recording").length || 0;
  const inReviewCount = listData?.filter(c => ["draft", "under_review", "analysis_ready"].includes(c.status)).length || 0;
  const finalizedCount = listData?.filter(c => ["finalized", "amended", "completed"].includes(c.status)).length || 0;

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.06 }
    }
  };

  const cardVariants: Variants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 320, damping: 25 } }
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* ── Executive Header ────────────────────────────────────────────────────────── */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <span className="px-3 py-1 rounded-full text-[11px] font-black uppercase tracking-wider bg-teal-500/10 text-teal-700 dark:text-teal-400 border border-teal-500/20">
              EHR Clinical Encounter Directory
            </span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-black font-heading text-slate-900 dark:text-white tracking-tight m-0">
            Patient Consultations
          </h1>
          <p className="text-sm sm:text-base text-slate-500 dark:text-slate-400 font-medium mt-1">
            Manage ambient clinical encounters, live transcription streams, and evidence-grounded care plans.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/consultations/new"
            className="flex items-center gap-2 bg-gradient-to-r from-teal-600 via-indigo-600 to-teal-700 text-white px-6 py-3.5 rounded-2xl font-bold shadow-lg transition-all hover:brightness-110 cursor-pointer shrink-0"
            style={{ boxShadow: "0 8px 24px rgba(13,148,136,0.35), inset 0 1px 0 rgba(255,255,255,0.3)" }}
          >
            <PlusCircle className="w-5 h-5" />
            <span>New Consultation</span>
          </Link>
        </div>
      </header>

      {/* ── Clinical Key Metrics Row ────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-xl bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 flex items-center justify-center border border-teal-200/80 dark:border-teal-800 shrink-0">
            <Stethoscope className="w-5 h-5 text-teal-600" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900 dark:text-white font-heading leading-tight">
              {totalCount}
            </div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Total Encounters
            </div>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-xl bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-400 flex items-center justify-center border border-rose-200/80 dark:border-rose-800 shrink-0">
            <Radio className="w-5 h-5 text-rose-600 animate-pulse" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900 dark:text-white font-heading leading-tight">
              {recordingCount}
            </div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Active Recordings
            </div>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-400 flex items-center justify-center border border-indigo-200/80 dark:border-indigo-800 shrink-0">
            <FileText className="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900 dark:text-white font-heading leading-tight">
              {inReviewCount}
            </div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              In Review / Draft
            </div>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 flex items-center justify-center border border-emerald-200/80 dark:border-emerald-800 shrink-0">
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900 dark:text-white font-heading leading-tight">
              {finalizedCount}
            </div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Finalized &amp; Signed
            </div>
          </div>
        </div>
      </div>

      {/* ── Search Bar & Status Filter Bar ────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        {/* Modern Semantic Search */}
        <div className="relative flex-1 max-w-xl group">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-teal-600" />
          </div>
          <input
            type="text"
            className="block w-full pl-11 pr-4 py-3 bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl border border-slate-200/90 dark:border-slate-800 rounded-2xl text-sm leading-5 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:bg-white dark:focus:bg-slate-900 transition-all shadow-2xs"
            placeholder="Semantic Patient Search (e.g. '34yo male with chest pain' or 'ENC #98c212')..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-xs text-slate-400 hover:text-slate-600"
            >
              Clear
            </button>
          )}
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-100/90 dark:bg-slate-800/80 rounded-2xl border border-slate-200/80 dark:border-slate-700/80 self-start md:self-auto overflow-x-auto max-w-full">
          <button
            type="button"
            onClick={() => setStatusFilter("all")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 ${
              statusFilter === "all"
                ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-2xs"
                : "text-slate-500 hover:text-slate-800 dark:text-slate-400"
            }`}
          >
            All ({totalCount})
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter("recording")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 flex items-center gap-1.5 ${
              statusFilter === "recording"
                ? "bg-white dark:bg-slate-700 text-rose-700 dark:text-rose-400 shadow-2xs"
                : "text-slate-500 hover:text-slate-800 dark:text-slate-400"
            }`}
          >
            {recordingCount > 0 && <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />}
            Recording ({recordingCount})
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter("in_review")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 ${
              statusFilter === "in_review"
                ? "bg-white dark:bg-slate-700 text-indigo-700 dark:text-indigo-400 shadow-2xs"
                : "text-slate-500 hover:text-slate-800 dark:text-slate-400"
            }`}
          >
            In Review ({inReviewCount})
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter("finalized")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 ${
              statusFilter === "finalized"
                ? "bg-white dark:bg-slate-700 text-emerald-700 dark:text-emerald-400 shadow-2xs"
                : "text-slate-500 hover:text-slate-800 dark:text-slate-400"
            }`}
          >
            Finalized ({finalizedCount})
          </button>
        </div>
      </div>

      {/* ── Consultations Grid ──────────────────────────────────────────────────────── */}
      <AnimatePresence mode="wait">
        {loading ? (
          <motion.div 
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} data-testid="skeleton" className="p-6 rounded-3xl border border-slate-200/80 dark:border-slate-800 animate-pulse bg-white/70 dark:bg-slate-900/60 shadow-sm">
                <div className="h-6 bg-slate-200 dark:bg-slate-800 rounded-xl w-1/3 mb-4"></div>
                <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded-lg w-1/2 mb-8"></div>
                <div className="h-10 bg-slate-200 dark:bg-slate-800 rounded-xl w-full"></div>
              </div>
            ))}
          </motion.div>
        ) : filteredConsultations.length > 0 ? (
          <motion.div 
            key="grid"
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6"
          >
            {filteredConsultations.map((c) => {
              const isFinal = ["finalized", "amended", "completed"].includes(c.status);
              const isRec = c.status === "recording";
              const isProc = c.status === "processing";

              return (
                <motion.div 
                  key={c.id}
                  variants={cardVariants}
                  whileHover={{ y: -3 }}
                  className={`group flex flex-col justify-between p-6 rounded-3xl border transition-all shadow-sm hover:shadow-xl bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl ${
                    isRec 
                      ? "border-rose-300 ring-2 ring-rose-200/50 dark:border-rose-800" 
                      : isFinal
                        ? "border-emerald-200/90 dark:border-emerald-900/50"
                        : "border-slate-200/90 dark:border-slate-800 hover:border-indigo-300 dark:hover:border-indigo-700"
                  }`}
                >
                  <div>
                    {/* Header Row: Session ID & Status Badge */}
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex items-center gap-3">
                        <div className={`p-2.5 rounded-2xl border shadow-2xs ${
                          isRec 
                            ? "bg-rose-50 text-rose-700 border-rose-200" 
                            : isFinal 
                              ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                              : "bg-gradient-to-br from-teal-50 to-indigo-50 text-teal-700 border-teal-200/70"
                        }`}>
                          <UserCircle className="w-6 h-6" />
                        </div>
                        <div>
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <h3 className="font-extrabold text-slate-900 dark:text-white text-base m-0 tracking-tight font-heading">
                              Session #{c.id.substring(0, 8).toUpperCase()}
                            </h3>
                            <button
                              type="button"
                              onClick={(e) => handleCopyId(e, `@${c.id.substring(0, 8)}`)}
                              className="inline-flex items-center gap-1 text-[11px] font-mono font-bold text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-950/50 hover:bg-indigo-100 border border-indigo-200/80 dark:border-indigo-800 px-2 py-0.5 rounded-lg transition-colors cursor-pointer"
                              title="Click to copy @mention tag for DocAssist IQ AI"
                            >
                              <Tag className="w-3 h-3 text-indigo-500" />
                              <span>@{c.id.substring(0, 8)}</span>
                              {copiedId === `@${c.id.substring(0, 8)}` ? (
                                <Check className="w-3 h-3 text-emerald-600" />
                              ) : (
                                <Copy className="w-3 h-3 opacity-60" />
                              )}
                            </button>
                          </div>
                          <div className="flex items-center text-xs text-slate-400 gap-1.5 mt-0.5 font-medium">
                            <Clock className="w-3.5 h-3.5" />
                            {new Date(c.created_at).toLocaleDateString(undefined, { 
                              month: 'short', 
                              day: 'numeric', 
                              hour: '2-digit', 
                              minute: '2-digit' 
                            })}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-1.5 flex-wrap justify-end">
                        {isFinal && (
                          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                            <FileCheck className="w-3 h-3 text-emerald-600" />
                            <span className="hidden sm:inline">Signed Docs</span>
                          </span>
                        )}
                        <span className={`px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider shadow-2xs border ${
                          isFinal
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-300 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800' 
                            : isRec
                              ? 'bg-rose-50 text-rose-700 border-rose-300 ring-2 ring-rose-200/50 animate-pulse dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-800'
                              : isProc
                                ? 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/60 dark:text-purple-300 dark:border-purple-800'
                                : 'bg-amber-50 text-amber-800 border-amber-300 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-800'
                        }`}>
                          {c.status.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                    
                    {/* Patient EHR Linkage Badge */}
                    <div className="mb-3 flex items-center justify-between gap-2 flex-wrap">
                      {c.patient_ref && c.patient_id ? (
                        <Link
                          href={`/patients/${c.patient_id}`}
                          onClick={(e) => e.stopPropagation()}
                          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold text-teal-800 dark:text-teal-300 bg-teal-50/90 dark:bg-teal-950/60 hover:bg-teal-100 dark:hover:bg-teal-900 border border-teal-200/90 dark:border-teal-800 transition-colors shadow-2xs group/pt"
                          title="Open verified Patient EHR file"
                        >
                          <UserCircle className="w-3.5 h-3.5 text-teal-600" />
                          <span>Patient: <strong className="font-extrabold">{c.patient_ref}</strong></span>
                          {c.patient_demographics && (
                            <span className="text-[10px] text-teal-700/80 dark:text-teal-400 font-semibold border-l border-teal-300 dark:border-teal-700 pl-1.5 ml-0.5">
                              {[c.patient_demographics.biological_sex, c.patient_demographics.age_group].filter(Boolean).join(" • ")}
                            </span>
                          )}
                          <ArrowRight className="w-3 h-3 text-teal-500 opacity-60 group-hover/pt:opacity-100 group-hover/pt:translate-x-0.5 transition-all" />
                        </Link>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-400 dark:text-slate-500 bg-slate-50 dark:bg-slate-800/40 px-2 py-0.5 rounded-lg border border-slate-200 dark:border-slate-800">
                          Auto-assigned Patient Profile
                        </span>
                      )}
                    </div>

                    {/* Clinical Note Preview Snippet */}
                    <div className="mt-3 mb-5 p-3.5 rounded-2xl bg-slate-50/70 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                      <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-3 leading-relaxed font-normal m-0">
                        {c.input_preview || <span className="italic text-slate-400">No clinical notes recorded yet.</span>}
                      </p>
                    </div>
                  </div>

                  {/* Card Bottom Actions */}
                  <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5">
                      <Link 
                        href={`/consultations/${c.id}/intake`}
                        className="text-[11px] font-bold text-teal-800 dark:text-teal-300 bg-teal-50 dark:bg-teal-950/40 hover:bg-teal-100 dark:hover:bg-teal-900/60 px-2.5 py-1.5 rounded-xl border border-teal-200/80 dark:border-teal-800 transition-colors"
                        title="Open structured clinical intake"
                      >
                        Intake
                      </Link>
                      <Link 
                        href={`/consultations/${c.id}/review`}
                        className="text-[11px] font-bold text-indigo-800 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-950/40 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 px-2.5 py-1.5 rounded-xl border border-indigo-200/80 dark:border-indigo-800 transition-colors"
                        title="Review and sign off clinical note"
                      >
                        Review
                      </Link>
                      <Link
                        href={`/ai?cid=${c.id}`}
                        className="text-[11px] font-bold text-indigo-700 dark:text-indigo-300 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-950/40 dark:to-purple-950/40 hover:from-indigo-100 hover:to-purple-100 px-2.5 py-1.5 rounded-xl border border-indigo-200/80 dark:border-indigo-800 transition-all flex items-center gap-1.5 shadow-2xs"
                        title="Query encounter & generate certified documents with DocAssist IQ AI"
                      >
                        <Brain className="w-3.5 h-3.5 text-indigo-600" />
                        <span>DocAssist IQ AI</span>
                      </Link>
                    </div>

                    <Link 
                      href={`/consultations/${c.id}`} 
                      className="flex items-center gap-1.5 text-xs font-bold text-white bg-gradient-to-r from-teal-600 to-indigo-600 hover:from-teal-500 hover:to-indigo-500 px-3.5 py-1.5 rounded-xl shadow-xs transition-all group/btn"
                    >
                      <span>Open Room</span>
                      <ArrowRight className="w-3.5 h-3.5 group-hover/btn:translate-x-0.5 transition-transform" />
                    </Link>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        ) : (
          <motion.div 
            key="empty"
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center justify-center py-20 text-center rounded-3xl border border-dashed border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/60 p-8 shadow-sm"
          >
            <div className="w-20 h-20 bg-gradient-to-tr from-teal-50 to-indigo-50 dark:from-slate-800 dark:to-slate-700 rounded-3xl flex items-center justify-center mb-5 shadow-sm border border-slate-200 dark:border-slate-700">
              <Stethoscope className="w-10 h-10 text-teal-600 dark:text-teal-400" />
            </div>
            <h3 className="text-xl font-bold font-heading text-slate-900 dark:text-white mb-2">
              {searchQuery ? "No matching encounters found" : "Clinical Directory Clear"}
            </h3>
            <p className="text-slate-500 dark:text-slate-400 max-w-md mx-auto mb-6 text-sm leading-relaxed">
              {searchQuery 
                ? "We couldn't find any sessions matching your query. Try adjusting your semantic search parameters." 
                : "No consultations yet. Your clinical workspace is ready. Initiate a new consultation to begin analyzing clinical notes and formulating evidence-based care plans."}
            </p>
            {!searchQuery && (
              <button 
                onClick={handleCreate}
                disabled={creating}
                className="bg-gradient-to-r from-teal-600 to-indigo-600 text-white px-6 py-3 rounded-2xl font-bold transition-all shadow-md hover:brightness-110 flex items-center gap-2 text-sm cursor-pointer"
              >
                <PlusCircle className="w-4 h-4" />
                Start First Consultation
              </button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
