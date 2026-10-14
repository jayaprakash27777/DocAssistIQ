/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React, { useState, useEffect, useCallback, useMemo, useTransition } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  BookOpen,
  Activity,
  ShieldAlert,
  Sparkles,
  Stethoscope,
  Filter,
  Layers,
  FileText,
  Copy,
  Check,
  ExternalLink,
  ChevronRight,
  ChevronLeft,
  X,
  Pill,
  FlaskConical,
  HeartPulse,
  Brain,
  Info,
  RefreshCw,
  SlidersHorizontal,
  Flame,
  CheckCircle2,
  Share2,
} from "lucide-react";
import {
  searchDiseaseCatalog,
  getDiseaseCatalogStats,
  getDiseaseCatalogCategories,
  getDiseaseCatalogMonograph,
  matchDiseaseCatalogSymptoms,
  type DiseaseCatalogItem,
  type DiseaseCatalogStatsResponse,
  type DiseaseCatalogCategoryItem,
} from "@/lib/api";

export default function DiseaseCatalogPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [selectedSeverity, setSelectedSeverity] = useState<string>("");
  const [selectedTriage, setSelectedTriage] = useState<string>("");
  const [page, setPage] = useState(0);
  const pageSize = 20;

  const [diseases, setDiseases] = useState<DiseaseCatalogItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DiseaseCatalogStatsResponse | null>(null);
  const [categories, setCategories] = useState<DiseaseCatalogCategoryItem[]>([]);

  // Selected disease for detailed drawer modal
  const [selectedDisease, setSelectedDisease] = useState<DiseaseCatalogItem | null>(null);
  const [copied, setCopied] = useState(false);

  // Symptom matching mode
  const [activeTab, setActiveTab] = useState<"catalog" | "symptom_matcher">("catalog");
  const [symptomInput, setSymptomInput] = useState("");
  const [matchedCandidates, setMatchedCandidates] = useState<DiseaseCatalogItem[]>([]);
  const [isMatching, setIsMatching] = useState(false);

  const [, startTransition] = useTransition();

  // Load stats and categories on mount
  useEffect(() => {
    async function loadMeta() {
      try {
        const [statsRes, catsRes] = await Promise.all([
          getDiseaseCatalogStats(),
          getDiseaseCatalogCategories(),
        ]);
        if (statsRes.ok && statsRes.data) setStats(statsRes.data);
        if (catsRes.ok && catsRes.data) setCategories(catsRes.data);
      } catch (err) {
        console.error("Failed to load catalog metadata", err);
      }
    }
    loadMeta();
  }, []);

  // Fetch diseases
  const fetchDiseases = useCallback(async () => {
    setLoading(true);
    try {
      const res = await searchDiseaseCatalog({
        q: searchTerm.trim() || undefined,
        category: selectedCategory || undefined,
        severity: selectedSeverity || undefined,
        triage: selectedTriage || undefined,
        limit: pageSize,
        offset: page * pageSize,
      });

      if (res.ok && res.data) {
        setDiseases(res.data.results);
        setTotalCount(res.data.total);
      } else {
        setDiseases([]);
        setTotalCount(0);
      }
    } catch (err) {
      console.error("Search failed", err);
      setDiseases([]);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, selectedCategory, selectedSeverity, selectedTriage, page]);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchDiseases();
    }, 200);
    return () => clearTimeout(timer);
  }, [fetchDiseases]);

  // Handle symptom matching
  const handleSymptomMatch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!symptomInput.trim()) return;

    setIsMatching(true);
    try {
      const syms = symptomInput
        .split(/[,;\n]+/)
        .map((s) => s.trim())
        .filter(Boolean);
      const res = await matchDiseaseCatalogSymptoms(syms, 12);
      if (res.ok && res.data) {
        setMatchedCandidates(res.data);
      } else {
        setMatchedCandidates([]);
      }
    } catch (err) {
      console.error("Symptom match failed", err);
    } finally {
      setIsMatching(false);
    }
  };

  const copyMonograph = (d: DiseaseCatalogItem) => {
    const text = `DISEASE: ${d.name}
ICD-10: ${d.icd10 || "N/A"} | ICD-11: ${d.icd11 || "N/A"}${d.orphacode ? ` | ORPHA: ${d.orphacode}` : ""}
SPECIALTY: ${d.category}
SEVERITY: ${d.severity.toUpperCase()} (Triage: ${d.triage})

CLINICAL PEARL:
${d.pearl}

HALLMARK SYMPTOMS:
${d.hallmark_symptoms.map((s) => "• " + s).join("\n")}

IMMEDIATE STAT TESTS:
${d.immediate_tests.map((t) => "• " + t).join("\n")}

RECOMMENDED INVESTIGATIONS:
${d.recommended_investigations.map((i) => "• " + i).join("\n")}

FIRST-LINE TREATMENT:
${d.first_line_treatment}

GUIDELINE MEDICATIONS:
${d.recommended_medications.map((m) => "• " + m).join("\n")}

SOURCE: ${d.source}
REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED`;

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  const getSeverityBadgeClass = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "critical":
        return "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-900";
      case "high":
        return "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-900";
      case "moderate":
        return "bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-950/40 dark:text-teal-300 dark:border-teal-900";
      default:
        return "bg-slate-50 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700";
    }
  };

  const quickChips = [
    "Wilson disease",
    "Friedreich ataxia",
    "Marfan syndrome",
    "Ehlers-Danlos",
    "STEMI",
    "Kawasaki disease",
    "Glioblastoma",
    "Amyloidosis",
    "Lyme disease",
    "Preeclampsia",
    "Myasthenia gravis",
    "Pheochromocytoma",
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 text-slate-900 dark:text-slate-100 p-4 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-teal-900 via-slate-900 to-indigo-950 text-white p-6 md:p-10 shadow-2xl border border-teal-800/40">
        <div className="absolute -right-16 -top-16 w-80 h-80 rounded-full bg-teal-500/10 blur-3xl pointer-events-none" />
        <div className="absolute right-32 bottom-0 w-64 h-64 rounded-full bg-indigo-500/10 blur-2xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-3 max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/20 border border-teal-400/30 text-teal-300 text-xs font-semibold uppercase tracking-wider backdrop-blur-md">
              <Sparkles className="w-3.5 h-3.5" />
              Universal Clinical Knowledge Base
            </div>
            <h1 className="text-3xl md:text-5xl font-black tracking-tight leading-tight">
              Master Disease Catalog
            </h1>
            <p className="text-slate-300 text-sm md:text-base leading-relaxed">
              Instant offline clinical intelligence spanning <strong className="text-teal-300 font-bold">20,397+ verified medical conditions</strong>, rare genetic syndromes (Orphanet), MedlinePlus clinical topics, and ICD-10/ICD-11 tabulations with sub-30ms search.
            </p>
          </div>

          {/* Quick Metrics Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 shrink-0">
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-3 border border-white/10 text-center">
              <span className="block text-2xl md:text-3xl font-black text-teal-300">
                {stats?.total_diseases ? stats.total_diseases.toLocaleString() : "20,397"}
              </span>
              <span className="text-[11px] font-medium text-slate-300 uppercase tracking-wide">
                Conditions
              </span>
            </div>
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-3 border border-white/10 text-center">
              <span className="block text-2xl md:text-3xl font-black text-amber-300">
                {stats?.total_synonyms ? stats.total_synonyms.toLocaleString() : "21,289"}
              </span>
              <span className="text-[11px] font-medium text-slate-300 uppercase tracking-wide">
                Synonyms
              </span>
            </div>
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-3 border border-white/10 text-center col-span-2 sm:col-span-1">
              <span className="block text-2xl md:text-3xl font-black text-indigo-300">
                48
              </span>
              <span className="text-[11px] font-medium text-slate-300 uppercase tracking-wide">
                Specialties
              </span>
            </div>
          </div>
        </div>

        {/* Tab switchers */}
        <div className="mt-8 flex items-center gap-2 border-t border-white/10 pt-4">
          <button
            onClick={() => setActiveTab("catalog")}
            className={`px-4 py-2 rounded-xl text-xs md:text-sm font-bold transition-all flex items-center gap-2 ${
              activeTab === "catalog"
                ? "bg-white text-slate-900 shadow-md"
                : "text-slate-300 hover:text-white hover:bg-white/10"
            }`}
          >
            <BookOpen className="w-4 h-4" />
            Full Disease Catalog (20k+)
          </button>
          <button
            onClick={() => setActiveTab("symptom_matcher")}
            className={`px-4 py-2 rounded-xl text-xs md:text-sm font-bold transition-all flex items-center gap-2 ${
              activeTab === "symptom_matcher"
                ? "bg-white text-slate-900 shadow-md"
                : "text-slate-300 hover:text-white hover:bg-white/10"
            }`}
          >
            <Stethoscope className="w-4 h-4" />
            Patient Symptom Matcher
          </button>
        </div>
      </div>

      {activeTab === "catalog" ? (
        <>
          {/* Search & Filter Toolbar */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 md:p-6 shadow-md border border-slate-200 dark:border-slate-800 space-y-4">
            <div className="flex flex-col md:flex-row gap-3">
              {/* Search input */}
              <div className="relative flex-1">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setPage(0);
                  }}
                  placeholder="Search 20,397+ diseases by name, ICD-10 (e.g. Q87.4), ICD-11, OrphaCode, or synonym..."
                  className="w-full pl-12 pr-10 py-3.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 font-medium text-sm transition-all"
                />
                {searchTerm && (
                  <button
                    onClick={() => {
                      setSearchTerm("");
                      setPage(0);
                    }}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* Specialty filter */}
              <div className="w-full md:w-72">
                <select
                  value={selectedCategory}
                  onChange={(e) => {
                    setSelectedCategory(e.target.value);
                    setPage(0);
                  }}
                  className="w-full py-3.5 px-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-teal-500 font-medium text-sm transition-all"
                >
                  <option value="">All Specialties ({stats?.total_diseases || 20397})</option>
                  {categories.map((c) => (
                    <option key={c.category} value={c.category}>
                      {c.category} ({c.count})
                    </option>
                  ))}
                </select>
              </div>

              {/* Severity filter */}
              <div className="w-full md:w-44">
                <select
                  value={selectedSeverity}
                  onChange={(e) => {
                    setSelectedSeverity(e.target.value);
                    setPage(0);
                  }}
                  className="w-full py-3.5 px-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-teal-500 font-medium text-sm transition-all"
                >
                  <option value="">All Severities</option>
                  <option value="critical">Critical / Emergent ({stats?.severity_breakdown?.critical || 913})</option>
                  <option value="high">High / Urgent ({stats?.severity_breakdown?.high || 4127})</option>
                  <option value="moderate">Moderate ({stats?.severity_breakdown?.moderate || 15345})</option>
                </select>
              </div>
            </div>

            {/* Quick chips */}
            <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs text-slate-500 scrollbar-none">
              <span className="font-bold text-slate-400 shrink-0">Popular Searches:</span>
              {quickChips.map((chip) => (
                <button
                  key={chip}
                  onClick={() => {
                    setSearchTerm(chip);
                    setSelectedCategory("");
                    setSelectedSeverity("");
                    setPage(0);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-teal-50 dark:hover:bg-teal-950/50 hover:text-teal-700 dark:hover:text-teal-300 border border-slate-200 dark:border-slate-700 shrink-0 font-medium transition-colors"
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>

          {/* Results Info & Count */}
          <div className="flex items-center justify-between text-xs md:text-sm font-semibold text-slate-500 px-1">
            <span>
              Showing {diseases.length} of {totalCount.toLocaleString()} conditions
              {searchTerm && ` for "${searchTerm}"`}
              {selectedCategory && ` in ${selectedCategory}`}
            </span>
            <span>Page {page + 1} of {Math.max(1, totalPages)}</span>
          </div>

          {/* Disease Cards Grid */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="h-64 rounded-2xl bg-slate-100 dark:bg-slate-800 animate-pulse border border-slate-200 dark:border-slate-700"
                />
              ))}
            </div>
          ) : diseases.length === 0 ? (
            <div className="bg-white dark:bg-slate-900 rounded-3xl p-12 text-center border border-slate-200 dark:border-slate-800 space-y-4">
              <div className="w-16 h-16 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mx-auto text-slate-400">
                <Search className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200">
                No matching conditions found
              </h3>
              <p className="text-slate-500 text-sm max-w-md mx-auto">
                No disease profile matched "{searchTerm}". Try clearing your filters or searching by a broader medical term or ICD-10 code.
              </p>
              <button
                onClick={() => {
                  setSearchTerm("");
                  setSelectedCategory("");
                  setSelectedSeverity("");
                }}
                className="px-4 py-2 rounded-xl bg-teal-600 text-white font-bold text-sm shadow hover:bg-teal-700"
              >
                Reset All Filters
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {diseases.map((d) => (
                <motion.div
                  key={d.id}
                  layout
                  whileHover={{ y: -3 }}
                  onClick={() => setSelectedDisease(d)}
                  className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 hover:border-teal-500/50 dark:hover:border-teal-500/50 shadow-sm hover:shadow-md transition-all cursor-pointer flex flex-col justify-between group"
                >
                  <div className="space-y-3">
                    {/* Header Badges */}
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 truncate max-w-[180px]">
                        {d.category}
                      </span>
                      <span
                        className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-md border ${getSeverityBadgeClass(
                          d.severity
                        )}`}
                      >
                        {d.severity}
                      </span>
                    </div>

                    {/* Title */}
                    <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors line-clamp-2">
                      {d.name}
                    </h3>

                    {/* Coding Badges */}
                    <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                      {d.icd10 && (
                        <span className="px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 font-mono font-bold border border-blue-200 dark:border-blue-900">
                          ICD-10: {d.icd10}
                        </span>
                      )}
                      {d.icd11 && (
                        <span className="px-2 py-0.5 rounded bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 font-mono font-bold border border-purple-200 dark:border-purple-900">
                          ICD-11: {d.icd11}
                        </span>
                      )}
                      {d.orphacode && (
                        <span className="px-2 py-0.5 rounded bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 font-mono font-bold border border-amber-200 dark:border-amber-900">
                          ORPHA:{d.orphacode}
                        </span>
                      )}
                    </div>

                    {/* Snippet / Pearl */}
                    <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-3 leading-relaxed">
                      {d.pearl || d.first_line_treatment}
                    </p>
                  </div>

                  {/* Card Footer */}
                  <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 font-medium">
                    <span className="truncate max-w-[170px] text-[10px] text-slate-400">
                      {d.source}
                    </span>
                    <span className="text-teal-600 dark:text-teal-400 font-bold inline-flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                      View Monograph <ChevronRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3 pt-6 pb-12">
              <button
                disabled={page === 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                className="px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 font-bold text-xs disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-1"
              >
                <ChevronLeft className="w-4 h-4" /> Previous
              </button>
              <span className="text-xs font-bold text-slate-500">
                Page {page + 1} of {totalPages}
              </span>
              <button
                disabled={page >= totalPages - 1}
                onClick={() => setPage((p) => p + 1)}
                className="px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 font-bold text-xs disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-1"
              >
                Next <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </>
      ) : (
        /* Symptom Matcher Mode */
        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 md:p-8 border border-slate-200 dark:border-slate-800 shadow-md space-y-4">
            <div className="space-y-1">
              <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Stethoscope className="w-5 h-5 text-teal-600" />
                Cross-Catalog Symptom Differential Matcher
              </h2>
              <p className="text-slate-500 text-sm">
                Enter free-form clinical findings, presenting symptoms, or bedside signs to compute rank scores against all 20,397+ conditions in the master database.
              </p>
            </div>

            <form onSubmit={handleSymptomMatch} className="space-y-3">
              <textarea
                rows={3}
                value={symptomInput}
                onChange={(e) => setSymptomInput(e.target.value)}
                placeholder="e.g. progressive ataxia, dysarthria, absent deep tendon reflexes, loss of proprioception, cardiomyopathy..."
                className="w-full p-4 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 font-medium text-sm transition-all"
              />
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <span>Example:</span>
                  <button
                    type="button"
                    onClick={() =>
                      setSymptomInput(
                        "jaw claudication, temporal headache, scalp tenderness, vision loss"
                      )
                    }
                    className="underline hover:text-teal-600"
                  >
                    GCA
                  </button>
                  •
                  <button
                    type="button"
                    onClick={() =>
                      setSymptomInput(
                        "fever, tremor, Kayser-Fleischer rings, elevated transaminases, dysarthria"
                      )
                    }
                    className="underline hover:text-teal-600"
                  >
                    Wilson Disease
                  </button>
                  •
                  <button
                    type="button"
                    onClick={() =>
                      setSymptomInput(
                        "sudden tearing chest pain radiating to back, unequal blood pressure, pulse deficit"
                      )
                    }
                    className="underline hover:text-teal-600"
                  >
                    Aortic Dissection
                  </button>
                </div>

                <button
                  type="submit"
                  disabled={isMatching || !symptomInput.trim()}
                  className="px-6 py-2.5 rounded-xl bg-teal-600 text-white font-bold text-sm shadow hover:bg-teal-700 disabled:opacity-50 transition-all flex items-center gap-2 shrink-0"
                >
                  {isMatching ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" /> Matching...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" /> Match Candidates
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Matched Results */}
          {matchedCandidates.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Activity className="w-4 h-4 text-teal-600" />
                Ranked Candidates ({matchedCandidates.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {matchedCandidates.map((c: any, idx) => (
                  <div
                    key={idx}
                    onClick={() => setSelectedDisease(c)}
                    className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-teal-200 dark:border-teal-900/60 shadow-sm hover:shadow-md cursor-pointer transition-all space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-black px-2 py-0.5 rounded-md bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300">
                        Score: {c.score}
                      </span>
                      <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-md border ${getSeverityBadgeClass(c.severity)}`}>
                        {c.severity}
                      </span>
                    </div>
                    <h4 className="font-bold text-base text-slate-900 dark:text-slate-100">
                      {c.disease || c.name}
                    </h4>
                    {c.matched_symptoms && c.matched_symptoms.length > 0 && (
                      <div className="space-y-1">
                        <span className="text-[10px] font-bold uppercase text-slate-400">
                          Matched Findings:
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {c.matched_symptoms.map((s: string, sIdx: number) => (
                            <span
                              key={sIdx}
                              className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800"
                            >
                              ✓ {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2">
                      {c.first_line_treatment || c.pearl}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Detailed Slide-over Drawer Monograph Modal */}
      <AnimatePresence>
        {selectedDisease && (
          <div className="fixed inset-0 z-50 flex items-center justify-end bg-slate-950/60 backdrop-blur-xs">
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 30, stiffness: 300 }}
              className="w-full max-w-2xl h-full bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col justify-between overflow-hidden"
            >
              {/* Drawer Header */}
              <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex items-start justify-between bg-slate-50 dark:bg-slate-800/50">
                <div className="space-y-2 pr-4">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full bg-teal-100 text-teal-800 dark:bg-teal-950 dark:text-teal-300 border border-teal-200 dark:border-teal-800">
                      {selectedDisease.category}
                    </span>
                    <span className={`text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full border ${getSeverityBadgeClass(selectedDisease.severity)}`}>
                      {selectedDisease.severity} ({selectedDisease.triage})
                    </span>
                  </div>
                  <h2 className="text-xl md:text-2xl font-black text-slate-900 dark:text-slate-100 leading-snug">
                    {selectedDisease.name}
                  </h2>
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    {selectedDisease.icd10 && (
                      <span className="px-2 py-0.5 rounded-md bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 font-mono font-bold">
                        ICD-10: {selectedDisease.icd10}
                      </span>
                    )}
                    {selectedDisease.icd11 && (
                      <span className="px-2 py-0.5 rounded-md bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300 font-mono font-bold">
                        ICD-11: {selectedDisease.icd11}
                      </span>
                    )}
                    {selectedDisease.orphacode && (
                      <span className="px-2 py-0.5 rounded-md bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 font-mono font-bold">
                        ORPHA: {selectedDisease.orphacode}
                      </span>
                    )}
                  </div>
                </div>

                <button
                  onClick={() => setSelectedDisease(null)}
                  className="p-2 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Drawer Scrollable Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Clinical Pearl / Summary */}
                <div className="space-y-2">
                  <h3 className="text-xs font-black uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-teal-500" />
                    Clinical Overview & Pathophysiology
                  </h3>
                  <div className="p-4 rounded-2xl bg-teal-50/60 dark:bg-teal-950/20 border border-teal-200/80 dark:border-teal-900/40 text-xs md:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                    {selectedDisease.pearl || "Verified clinical profile in DocAssistIQ Master Disease Catalog."}
                  </div>
                </div>

                {/* Hallmark Symptoms */}
                {selectedDisease.hallmark_symptoms && selectedDisease.hallmark_symptoms.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-xs font-black uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                      <Activity className="w-3.5 h-3.5 text-rose-500" />
                      Hallmark Clinical Presentation
                    </h3>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedDisease.hallmark_symptoms.map((sym, idx) => (
                        <span
                          key={idx}
                          className="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs font-medium border border-slate-200 dark:border-slate-700"
                        >
                          • {sym}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Immediate Bedside Tests */}
                {selectedDisease.immediate_tests && selectedDisease.immediate_tests.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-xs font-black uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                      <FlaskConical className="w-3.5 h-3.5 text-amber-500" />
                      Immediate Stat Bedside Investigations
                    </h3>
                    <ul className="space-y-1.5">
                      {selectedDisease.immediate_tests.map((test, idx) => (
                        <li
                          key={idx}
                          className="p-2.5 rounded-xl bg-amber-50/70 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40 text-xs text-amber-900 dark:text-amber-200 flex items-start gap-2"
                        >
                          <span className="font-bold shrink-0">[{idx + 1}]</span>
                          <span>{test}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Recommended Diagnostic Investigations */}
                {selectedDisease.recommended_investigations && selectedDisease.recommended_investigations.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-xs font-black uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-indigo-500" />
                      Confirmatory Investigations & Diagnostics
                    </h3>
                    <ul className="space-y-1.5">
                      {selectedDisease.recommended_investigations.map((inv, idx) => (
                        <li
                          key={idx}
                          className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs text-slate-700 dark:text-slate-300 flex items-start gap-2"
                        >
                          <span className="text-teal-600 dark:text-teal-400 font-bold shrink-0">✓</span>
                          <span>{inv}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* First-line Clinical Treatment */}
                {selectedDisease.first_line_treatment && (
                  <div className="space-y-2">
                    <h3 className="text-xs font-black uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                      <HeartPulse className="w-3.5 h-3.5 text-emerald-500" />
                      First-Line Clinical Management
                    </h3>
                    <div className="p-3.5 rounded-xl bg-emerald-50/70 dark:bg-emerald-950/20 border border-emerald-200/60 dark:border-emerald-900/40 text-xs text-emerald-900 dark:text-emerald-200 font-medium leading-relaxed">
                      {selectedDisease.first_line_treatment}
                    </div>
                  </div>
                )}

                {/* Guideline Medications */}
                {selectedDisease.recommended_medications && selectedDisease.recommended_medications.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-xs font-black uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                      <Pill className="w-3.5 h-3.5 text-teal-500" />
                      Guideline-Directed Medications
                    </h3>
                    <ul className="space-y-1.5">
                      {selectedDisease.recommended_medications.map((med, idx) => (
                        <li
                          key={idx}
                          className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs text-slate-700 dark:text-slate-300 flex items-start gap-2"
                        >
                          <span className="text-teal-600 dark:text-teal-400 font-bold shrink-0">Rx:</span>
                          <span>{med}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Synonyms list */}
                {selectedDisease.synonyms && selectedDisease.synonyms.length > 0 && (
                  <div className="space-y-1 pt-2">
                    <span className="text-[10px] font-bold uppercase text-slate-400">
                      Aliases & Alternative Eponyms ({selectedDisease.synonyms.length}):
                    </span>
                    <p className="text-[11px] text-slate-500 leading-relaxed">
                      {selectedDisease.synonyms.join(", ")}
                    </p>
                  </div>
                )}
              </div>

              {/* Drawer Footer Actions */}
              <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex items-center justify-between gap-3">
                <button
                  onClick={() => copyMonograph(selectedDisease)}
                  className="px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 font-bold text-xs hover:bg-slate-100 transition-colors flex items-center gap-1.5 shadow-xs"
                >
                  {copied ? (
                    <>
                      <Check className="w-4 h-4 text-emerald-600" /> Copied Monograph!
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4" /> Copy Full Monograph
                    </>
                  )}
                </button>

                <a
                  href={`/ai?query=${encodeURIComponent("Clinical intelligence and guidelines for " + selectedDisease.name)}`}
                  className="px-5 py-2.5 rounded-xl bg-teal-600 text-white font-bold text-xs hover:bg-teal-700 transition-colors shadow flex items-center gap-1.5"
                >
                  <Brain className="w-4 h-4" />
                  Ask AI About Disease
                </a>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
