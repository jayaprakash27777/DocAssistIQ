/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React, { useState, useEffect } from "react";
import { getInvestigationsForDisease, InvestigationResponse, orderInvestigationInNote } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";
import { noteKeys } from "@/hooks/useConsultations";
import { toast } from "react-hot-toast";
import FeedbackButtons from "./FeedbackButtons";
import { motion, AnimatePresence } from "framer-motion";
import ClinicalLoader from "./ClinicalLoader";
import { AlertTriangle, AlertCircle, FileText, CheckCircle2, BookOpen, Plus, Check, Loader2 } from "lucide-react";

function getPriorityStyle(priority: string = "") {
  const p = (priority || "").toUpperCase();
  if (p.includes("HIGH") || p.includes("STAT") || p.includes("IMMEDIATE") || p.includes("URGENT") || p.includes("CONFIRMATORY")) {
    return { bg: "bg-red-50", text: "text-red-700", border: "border-red-200", dot: "bg-red-500" };
  }
  if (p.includes("CONDITIONAL") || p.includes("MONITOR") || p.includes("CONSIDER") || p.includes("SECONDARY")) {
    return { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200", dot: "bg-amber-500" };
  }
  if (p.includes("INDICATED") || p.includes("ROUTINE") || p.includes("BASELINE") || p.includes("STANDARD")) {
    return { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200", dot: "bg-blue-400" };
  }
  return { bg: "bg-slate-50", text: "text-slate-700", border: "border-slate-200", dot: "bg-slate-400" };
}

const Section = ({ title, items, color, icon: Icon, consultationId, disease }: { title: string, items: any[], color: string, icon: any, consultationId: string, disease: string }) => {
  const queryClient = useQueryClient();
  const [orderingMap, setOrderingMap] = useState<Record<string, boolean>>({});
  const [orderedMap, setOrderedMap] = useState<Record<string, boolean>>({});

  if (items.length === 0) return null;

  const handleOrderTest = async (testName: string, priority: string, rationale?: string) => {
    setOrderingMap(prev => ({ ...prev, [testName]: true }));
    try {
      const priorityClean = priority.toUpperCase().includes("STAT") || priority.toUpperCase().includes("HIGH")
        ? "STAT"
        : priority.toUpperCase().includes("URGENT")
        ? "Urgent"
        : "Routine";
      const res = await orderInvestigationInNote(consultationId, {
        name: testName,
        category: "Laboratory",
        priority: priorityClean,
        rationale: rationale || `Clinician ordered from diagnostic panel for ${disease}`,
      });
      if (res.ok) {
        queryClient.setQueryData(noteKeys.detail(consultationId), res.data);
        setOrderedMap(prev => ({ ...prev, [testName]: true }));
        toast.success(`Ordered ${testName} into patient's note!`);
      } else {
        toast.error(res.error?.message || "Failed to order investigation");
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to order investigation");
    } finally {
      setOrderingMap(prev => ({ ...prev, [testName]: false }));
    }
  };

  return (
    <div className="mb-6 last:mb-0">
      <h6 className={`text-xs font-bold uppercase tracking-widest mb-3 flex items-center gap-2 ${color}`}>
        <Icon className="w-4 h-4 shrink-0" /> {title}
        <span className="ml-auto text-[10px] font-semibold text-slate-500 normal-case tracking-normal">
          {items.length} test{items.length !== 1 ? "s" : ""}
        </span>
      </h6>
      <div className="space-y-2.5">
        {items.map((item: any, idx: number) => {
          const testName = item.name || item.investigation_name;
          const pStyle = getPriorityStyle(item.priority);
          const isOrdering = orderingMap[testName];
          const isOrdered = orderedMap[testName];

          // Rich drag payload for clinical note
          const dragText = [
            `${item.priority || "RECOMMENDED"}: ${testName}`,
            item.rationale ? `  Rationale: ${item.rationale}` : "",
            item.evidence  ? `  Evidence: ${item.evidence}` : "",
            item.safety_flags?.length ? `  ⚠️ Safety: ${item.safety_flags.join("; ")}` : "",
          ].filter(Boolean).join("\n");

          return (
            <motion.div
              key={`${testName}-${idx}`}
              draggable={true}
              onDragStart={(e) => {
                const de = (e as unknown as DragEvent);
                if (de.dataTransfer) {
                  de.dataTransfer.setData("text/plain", dragText);
                  de.dataTransfer.effectAllowed = "copy";
                }
              }}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.03 }}
              className={`group relative px-4 py-3.5 rounded-xl border ${pStyle.border} ${pStyle.bg} hover:border-slate-300 transition-colors cursor-grab active:cursor-grabbing backdrop-blur-md shadow-2xs`}
            >
              <div className="flex items-start gap-3">
                <div className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 ${pStyle.dot}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-3">
                    <span className={`font-bold text-sm ${pStyle.text} leading-tight`}>
                      {testName}
                    </span>
                    <span className={`flex-shrink-0 text-[9px] font-black uppercase tracking-wider px-2 py-0.5 rounded-md border ${pStyle.border} ${pStyle.text} bg-white/80`}>
                      {item.priority || "RECOMMENDED"}
                    </span>
                  </div>
                  {item.rationale && (
                    <p className="text-xs text-slate-600 mt-1 leading-relaxed font-normal">{item.rationale}</p>
                  )}
                  {item.evidence && (
                    <p className="text-[10px] text-slate-500 mt-1 font-medium italic flex items-center gap-1">
                      <BookOpen className="w-3 h-3 text-slate-400 shrink-0" />
                      <span>{item.evidence}</span>
                    </p>
                  )}
                  {item.safety_flags?.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {item.safety_flags.map((flag: string, fi: number) => (
                        <span key={fi} className="inline-flex items-center gap-1 text-[9px] font-bold text-red-700 bg-red-50 border border-red-200 px-2 py-0.5 rounded-md">
                          <AlertTriangle className="w-2.5 h-2.5 text-red-600 shrink-0" />
                          <span>{flag}</span>
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Real-time Order Action */}
                  <div className="mt-3 flex items-center justify-between gap-2 pt-2 border-t border-slate-200/50">
                    <button
                      type="button"
                      onClick={() => handleOrderTest(testName, item.priority || "Urgent", item.rationale)}
                      disabled={isOrdering || isOrdered}
                      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold transition-all shadow-2xs cursor-pointer disabled:cursor-default ${
                        isOrdered
                          ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                          : "bg-blue-600 hover:bg-blue-700 text-white"
                      }`}
                    >
                      {isOrdered ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-700" />
                          <span>Ordered into Note</span>
                        </>
                      ) : isOrdering ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Ordering...</span>
                        </>
                      ) : (
                        <>
                          <Plus className="w-3.5 h-3.5" />
                          <span>Order Test into Note</span>
                        </>
                      )}
                    </button>
                    <span className="text-[10px] text-slate-400 font-medium">Or drag into SOAP note</span>
                  </div>
                </div>
              </div>

              <div className="absolute top-2.5 right-2.5 opacity-0 group-hover:opacity-100 transition-opacity">
                <FeedbackButtons
                  suggestionId={`inv-${consultationId}-${disease}-${testName}`}
                  suggestionType="investigation"
                  suggestionContext={item}
                />
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};


export default function InvestigationPanel({ consultationId, disease, competing = [] }: { consultationId: string, disease: string, competing?: string[] }) {
  const [data, setData] = useState<InvestigationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const res = await getInvestigationsForDisease(consultationId, disease, competing);
      if (res.ok) {
        setData(res.data);
      } else {
        if (res.error.message !== "Not Found") {
          setError(res.error.message || "Failed to load investigations");
        }
      }
      setLoading(false);
    }
    load();
  }, [consultationId, disease, competing]);

  if (loading) {
    return <ClinicalLoader label={`Evaluating workup for ${disease}...`} messages={["Reviewing clinical presentation", "Analyzing standard of care guidelines", "Synthesizing investigation panel", "Finalizing recommendations"]} />;
  }

  if (error) {
    return <div className="mt-4 p-4 text-xs text-red-700 bg-red-50 rounded-2xl border border-red-200 flex items-center gap-2"><AlertCircle className="w-4 h-4"/> {error}</div>;
  }

  if (!data || data.suggestions.length === 0) {
    return (
      <div className="mt-4 p-4 text-xs text-slate-600 bg-slate-50 rounded-2xl border border-slate-200 italic">
        No reference investigations available for {disease}.
      </div>
    );
  }

  const highPriority = data.suggestions.filter(s => {
    const p = (s.priority || "").toUpperCase();
    return p.includes("HIGH") || p.includes("STAT") || p.includes("IMMEDIATE") || p.includes("URGENT") || p.includes("CONFIRMATORY");
  });
  const conditional = data.suggestions.filter(s => {
    const p = (s.priority || "").toUpperCase();
    return !highPriority.includes(s) && (p.includes("CONDITIONAL") || p.includes("MONITOR") || p.includes("CONSIDER") || p.includes("SECONDARY"));
  });
  const ifIndicated = data.suggestions.filter(s => {
    const p = (s.priority || "").toUpperCase();
    return !highPriority.includes(s) && !conditional.includes(s) && (p.includes("INDICATED") || p.includes("ROUTINE") || p.includes("BASELINE") || p.includes("STANDARD"));
  });
  const additional = data.suggestions.filter(s => !highPriority.includes(s) && !conditional.includes(s) && !ifIndicated.includes(s));

  return (
    <motion.div 
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-4 p-6 overflow-hidden rounded-2xl border border-slate-200/90 bg-white shadow-xs relative text-left"
    >
      <div className="flex items-start justify-between mb-5 pb-4 border-b border-slate-200/80">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-50 rounded-xl border border-blue-200 flex items-center justify-center text-blue-700">
            <FileText className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h5 className="font-extrabold text-slate-900 text-base tracking-tight font-heading">Recommended Diagnostic Workup &amp; Tests</h5>
            <p className="text-[11px] text-slate-500 font-medium">Standard-of-care lab, imaging, and bedside test protocol for {disease}</p>
          </div>
        </div>
        <div className="shrink-0 flex items-center gap-2">
          <span className="text-xs font-bold text-blue-700 bg-blue-50 border border-blue-200 px-2.5 py-1 rounded-lg">
            {data.suggestions.length} Total Tests
          </span>
          <FeedbackButtons 
            suggestionId={`inv-${consultationId}-${disease}`} 
            suggestionType="investigation" 
            suggestionContext={data} 
          />
        </div>
      </div>

      <div className="space-y-5">
        <Section title="High Priority / Immediate" items={highPriority} color="text-red-700" icon={AlertCircle} consultationId={consultationId} disease={disease} />
        <Section title="Conditional / Monitor" items={conditional} color="text-amber-700" icon={AlertTriangle} consultationId={consultationId} disease={disease} />
        <Section title="If Indicated" items={ifIndicated} color="text-blue-700" icon={CheckCircle2} consultationId={consultationId} disease={disease} />
        <Section title="Additional Diagnostic Workup" items={additional} color="text-slate-700" icon={FileText} consultationId={consultationId} disease={disease} />
      </div>
    </motion.div>
  );
}
