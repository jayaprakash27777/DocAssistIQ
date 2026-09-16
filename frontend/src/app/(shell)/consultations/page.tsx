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
    <div className="w-full max-w-6xl mx-auto px-4 py-8">
      {/* Premium Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-6">
        <div>
          <motion.h1 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="text-4xl font-extrabold font-heading text-[var(--text-primary)] tracking-tight mb-2"
          >
            Clinical Sessions
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="text-lg text-[var(--text-secondary)] font-medium"
          >
            Manage active workflows and review patient history.
          </motion.p>
        </div>
        <motion.button 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          whileHover={{ scale: 1.02, boxShadow: "0 10px 30px -10px rgba(75, 170, 160, 0.4)" }}
          whileTap={{ scale: 0.98 }}
          onClick={handleCreate} 
          disabled={creating}
          className="flex items-center gap-2 bg-gradient-to-r from-[var(--color-primary-500)] to-[var(--color-primary-600)] text-white px-6 py-3.5 rounded-xl font-bold shadow-lg transition-all disabled:opacity-70"
        >
          {creating ? <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <PlusCircle className="w-5 h-5" />}
          {creating ? "Initiating..." : "New Consultation"}
        </motion.button>
      </header>

      {/* Modern Search Bar */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="relative max-w-2xl mb-12 group"
      >
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-[var(--color-primary-500)] group-focus-within:text-[var(--color-primary-600)] transition-colors" />
        </div>
        <input
          type="text"
          className="block w-full pl-12 pr-4 py-4 bg-white/60  backdrop-blur-md border border-[var(--border-default)] rounded-2xl text-base leading-5 placeholder-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-400)] focus:border-transparent focus:bg-white :bg-slate-900 transition-all shadow-sm hover:shadow-md"
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
              <div key={i} className="bg-white/40 rounded-2xl p-6 h-48 animate-pulse border border-[var(--border-default)]">
                <div className="h-6 bg-slate-200 rounded w-1/3 mb-4"></div>
                <div className="h-4 bg-slate-200 rounded w-1/2 mb-8"></div>
                <div className="h-10 bg-slate-200 rounded w-full"></div>
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
                className="group relative bg-white/70 backdrop-blur-xl border border-[var(--border-default)] hover:border-[var(--color-primary-400)] rounded-3xl p-6 transition-all duration-300 hover:shadow-[var(--shadow-premium)] flex flex-col justify-between"
              >
                <div>
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-3">
                      <div className="bg-[var(--color-primary-50)] p-2.5 rounded-xl text-[var(--color-primary-600)]">
                        <UserCircle className="w-6 h-6" />
                      </div>
                      <div>
                        <h3 className="font-bold text-[var(--text-primary)]">Session {c.id.substring(0, 6).toUpperCase()}</h3>
                        <div className="flex items-center text-xs text-[var(--text-tertiary)] gap-1 mt-0.5">
                          <Clock className="w-3 h-3" />
                          {new Date(c.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                      c.status === 'completed' 
                        ? 'bg-emerald-100 text-emerald-700' 
                        : 'bg-amber-100 text-amber-700'
                    }`}>
                      {c.status}
                    </span>
                  </div>
                  
                  <div className="mt-4 mb-6">
                    <p className="text-sm text-[var(--text-secondary)] line-clamp-3 leading-relaxed">
                      {c.input_preview || <span className="italic opacity-60">No clinical notes recorded yet.</span>}
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-[var(--border-default)]">
                  <div className="flex items-center gap-2 text-xs font-medium text-[var(--text-tertiary)]">
                    <FileText className="w-4 h-4" />
                    {c.input_preview?.length || 0} chars
                  </div>
                  <Link href={`/consultations/${c.id}`} className="flex items-center gap-2 text-sm font-bold text-[var(--color-primary-600)] hover:text-[var(--color-primary-700)] transition-colors group-hover:translate-x-1 duration-200">
                    Open Room <ArrowRight className="w-4 h-4" />
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
            className="flex flex-col items-center justify-center py-24 text-center"
          >
            <div className="w-24 h-24 bg-gradient-to-tr from-[var(--color-primary-100)] to-white [var(--color-primary-900)]  rounded-3xl flex items-center justify-center mb-6 shadow-sm border border-[var(--border-default)] rotate-3">
              <Stethoscope className="w-12 h-12 text-[var(--color-primary-500)] -rotate-3" />
            </div>
            <h3 className="text-2xl font-bold font-heading text-[var(--text-primary)] mb-3">
              {searchQuery ? "No matches found" : "Workspace Clear"}
            </h3>
            <p className="text-[var(--text-secondary)] max-w-md mx-auto mb-8 leading-relaxed">
              {searchQuery 
                ? "We couldn't find any sessions matching your query. Try adjusting your semantic search parameters." 
                : "Your clinical workspace is ready. Initiate a new consultation to begin analyzing clinical notes and formulating evidence-based care plans."}
            </p>
            {!searchQuery && (
              <button 
                onClick={handleCreate}
                disabled={creating}
                className="bg-white  border-2 border-[var(--border-default)] hover:border-[var(--color-primary-400)] text-[var(--text-primary)] px-6 py-3 rounded-xl font-bold transition-all shadow-sm hover:shadow-md flex items-center gap-2"
              >
                <PlusCircle className="w-5 h-5 text-[var(--color-primary-500)]" />
                Start First Consultation
              </button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
