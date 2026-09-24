"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/shell/ToastProvider";
import { Search, Stethoscope, PlusCircle, Clock, FileText, ArrowRight, UserCircle } from "lucide-react";
import { motion, AnimatePresence, Variants } from "framer-motion";
import { useConsultations, useSearchConsultations, useCreateConsultation } from "@/hooks/useConsultations";

export default function ConsultationsListPage() {
  const { toast } = useToast();
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery.trim()), 500);
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
    } catch (e: any) {
      toast.error(e.message || "Failed to initiate session");
    }
  };

  const isSearching = debouncedQuery.length >= 3;
  const loading = isSearching ? isSearchLoading : isListLoading;
  const consultations = isSearching ? (searchData || []) : (listData || []);
  const creating = createMutation.isPending;

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const cardVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 py-8">
      {/* Simulation / Placeholder Banner */}
      <div 
        role="alert" 
        aria-label="Simulation Notice — Not a clinical result" 
        className="mb-6 px-6 py-2.5 bg-amber-50/80 border border-amber-200/80 rounded-2xl text-xs text-amber-800 flex items-center justify-between shadow-sm"
      >
        <span className="font-bold text-[11px] uppercase tracking-wider">
          PLACEHOLDER DEVELOPMENT RESPONSE — NOT CLINICAL
        </span>
        <span className="text-[11px] text-amber-700 hidden sm:inline font-medium">
          Demonstration mode only. Verified clinician oversight required.
        </span>
      </div>

      {/* Premium Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-6">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-black uppercase tracking-wider bg-teal-500/10 text-teal-700 border border-teal-500/20">
              Workflows & Sessions
            </span>
          </div>
          <motion.h1 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="text-3xl sm:text-4xl font-black font-heading text-slate-900 tracking-tight"
          >
            Clinical Consultations
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="text-base text-slate-500 font-normal mt-1"
          >
            Manage active patient workflows, ambient transcriptions, and evidence-grounded care plans.
          </motion.p>
        </div>
        <motion.button 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          whileHover={{ scale: 1.02, y: -1 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleCreate} 
          disabled={creating}
          className="flex items-center gap-2 bg-gradient-to-r from-teal-600 via-indigo-600 to-teal-700 text-white px-6 py-3.5 rounded-2xl font-bold shadow-lg transition-all disabled:opacity-70 active:scale-95"
          style={{ boxShadow: "0 8px 24px rgba(13,148,136,0.35), inset 0 1px 0 rgba(255,255,255,0.3)" }}
        >
          {creating ? <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <PlusCircle className="w-5 h-5" />}
          {creating ? "Initiating Session..." : "New Consultation"}
        </motion.button>
      </header>

      {/* Modern Search Bar */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="relative max-w-2xl mb-8 group"
      >
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-teal-600 transition-colors" />
        </div>
        <input
          type="text"
          className="block w-full pl-12 pr-4 py-3.5 bg-white/80 backdrop-blur-xl border border-slate-200/90 rounded-2xl text-sm leading-5 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:bg-white focus:border-transparent transition-all shadow-sm hover:shadow-md"
          placeholder="Semantic Patient Search (e.g. '34yo male with acute migraine')..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </motion.div>

      {/* Grid Layout */}
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
              <div key={i} data-testid="skeleton" className="glass-panel-4k p-6 rounded-3xl border border-slate-200/80 animate-pulse bg-white/70">
                <div className="h-6 bg-slate-200 rounded-xl w-1/3 mb-4"></div>
                <div className="h-4 bg-slate-200 rounded-lg w-1/2 mb-8"></div>
                <div className="h-10 bg-slate-200 rounded-xl w-full"></div>
              </div>
            ))}
          </motion.div>
        ) : consultations.length > 0 ? (
          <motion.div 
            key="grid"
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6"
          >
            {consultations.map((c) => (
              <motion.div 
                key={c.id}
                variants={cardVariants}
                whileHover={{ y: -3 }}
                className="glass-panel-4k gpu-accelerated flex flex-col justify-between p-6 rounded-3xl border border-slate-200/90 bg-white/85 backdrop-blur-2xl shadow-[0_12px_36px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.9)] hover:shadow-xl hover:border-indigo-300 transition-all ring-1 ring-black/5"
              >
                <div>
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-3">
                      <div className="bg-gradient-to-br from-teal-50 to-indigo-50 p-2.5 rounded-2xl text-teal-700 border border-teal-200/70 shadow-sm">
                        <UserCircle className="w-6 h-6" />
                      </div>
                      <div>
                        <h3 className="font-bold text-slate-900 text-base m-0 tracking-tight">Session {c.id.substring(0, 6).toUpperCase()}</h3>
                        <div className="flex items-center text-xs text-slate-400 gap-1 mt-0.5 font-medium">
                          <Clock className="w-3.5 h-3.5" />
                          {new Date(c.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>
                    </div>
                    <span className={`px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider shadow-sm border ${
                      c.status === 'completed' || c.status === 'finalized'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                        : c.status === 'recording'
                        ? 'bg-rose-50 text-rose-700 border-rose-200 animate-pulse'
                        : 'bg-amber-50 text-amber-800 border-amber-200'
                    }`}>
                      {c.status}
                    </span>
                  </div>
                  
                  <div className="mt-4 mb-6">
                    <p className="text-sm text-slate-600 line-clamp-3 leading-relaxed font-normal m-0">
                      {c.input_preview || <span className="italic text-slate-400">No clinical notes recorded yet.</span>}
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-400">
                    <FileText className="w-3.5 h-3.5 text-slate-400" />
                    {c.input_preview?.length || 0} chars
                  </div>
                  <Link 
                    href={`/consultations/${c.id}`} 
                    className="flex items-center gap-1.5 text-xs font-bold text-teal-700 hover:text-indigo-600 transition-colors px-3 py-1.5 rounded-xl bg-teal-50 hover:bg-teal-100/70 border border-teal-200/70 shadow-sm"
                  >
                    Open Room <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </Link>
                </div>
              </motion.div>
            ))}
          </motion.div>
        ) : (
          <motion.div 
            key="empty"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center justify-center py-20 text-center glass-panel-4k rounded-3xl border border-slate-200/80 bg-white/70 p-8"
          >
            <div className="w-20 h-20 bg-gradient-to-tr from-teal-50 to-indigo-50 rounded-3xl flex items-center justify-center mb-5 shadow-md border border-slate-200">
              <Stethoscope className="w-10 h-10 text-teal-600" />
            </div>
            <h3 className="text-xl font-bold font-heading text-slate-900 mb-2">
              {searchQuery ? "No matching sessions found" : "Workspace Clear"}
            </h3>
            <p className="text-slate-500 max-w-md mx-auto mb-6 text-sm leading-relaxed">
              {searchQuery 
                ? "We couldn't find any sessions matching your query. Try adjusting your semantic search parameters." 
                : "No consultations yet. Your clinical workspace is ready. Initiate a new consultation to begin analyzing clinical notes and formulating evidence-based care plans."}
            </p>
            {!searchQuery && (
              <button 
                onClick={handleCreate}
                disabled={creating}
                className="bg-white border border-slate-200 hover:border-teal-400 text-slate-800 px-6 py-3 rounded-2xl font-bold transition-all shadow-sm hover:shadow-md flex items-center gap-2 text-sm"
              >
                <PlusCircle className="w-4 h-4 text-teal-600" />
                Start First Consultation
              </button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
