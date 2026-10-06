"use client";
import React, { useState, useMemo, useEffect } from "react";
import { motion } from "framer-motion";
import { getStoredToken } from "@/lib/api";

export interface DDIItem {
  drug1: string;
  drug2: string;
  severity: "CONTRAINDICATED" | "MAJOR" | "MODERATE" | "MINOR";
  mechanism: string;
  clinical_effect: string;
  recommendation: string;
  evidence_level: string;
}

  interface DDICheckerModalProps {
  onClose: () => void;
  initialDrugs?: string[];
}

const COMMON_DRUGS = [
  "Ticagrelor",
  "Aspirin",
  "Warfarin",
  "Amiodarone",
  "Sildenafil",
  "Nitroglycerin",
  "Allopurinol",
  "Azathioprine",
  "Clopidogrel",
  "Omeprazole",
  "Lithium",
  "Ibuprofen",
  "Methotrexate",
  "Trimethoprim",
  "Atorvastatin",
  "Metoprolol",
  "Heparin",
];

const KNOWN_DDI_RULES: Array<{
  pair: [string, string];
  severity: DDIItem["severity"];
  mechanism: string;
  clinical_effect: string;
  recommendation: string;
  evidence_level: string;
}> = [
  {
    pair: ["ticagrelor", "aspirin"],
    severity: "MODERATE",
    mechanism:
      "Synergistic antiplatelet inhibition; high maintenance aspirin (>100mg) reduces clinical efficacy of ticagrelor via thromboxane/prostacyclin imbalance.",
    clinical_effect: "Increased risk of major bleeding and reduced ischemic protection if aspirin > 100 mg.",
    recommendation:
      "Maintain maintenance aspirin dose at ≤ 81-100 mg daily when co-prescribed with Ticagrelor (PLATO trial guideline).",
    evidence_level: "Level 1A (ACC/AHA Class I Guideline)",
  },
  {
    pair: ["warfarin", "amiodarone"],
    severity: "MAJOR",
    mechanism:
      "Amiodarone potent inhibition of CYP2C9 and CYP3A4, drastically slowing S-warfarin hepatic clearance.",
    clinical_effect:
      "Doubling of plasma warfarin concentration, severe INR prolongation, life-threatening internal or intracranial hemorrhage.",
    recommendation:
      "Empirically reduce warfarin dose by 33% to 50% upon initiating amiodarone; monitor INR twice weekly until steady state.",
    evidence_level: "Level 1A (Definitive Pharmacokinetic Evidence)",
  },
  {
    pair: ["sildenafil", "nitroglycerin"],
    severity: "CONTRAINDICATED",
    mechanism:
      "Synergistic cGMP-mediated vascular smooth muscle relaxation and severe systemic vasodilation.",
    clinical_effect:
      "Precipitous, refractory, potentially fatal systemic hypotension and coronary hypoperfusion.",
    recommendation:
      "STRICT CONTRAINDICATION: Absolute avoidance within 24 hours of sildenafil or 48 hours of tadalafil. Use non-nitrate anti-anginals.",
    evidence_level: "Level 1A (FDA Black Box & ACC/AHA Contraindication)",
  },
  {
    pair: ["clopidogrel", "omeprazole"],
    severity: "MAJOR",
    mechanism:
      "Competitive inhibition of hepatic CYP2C19 bioactivation required to convert clopidogrel into its active thiol metabolite.",
    clinical_effect:
      "Significantly attenuated platelet inhibition, increased risk of stent thrombosis and recurrent myocardial infarction.",
    recommendation:
      "Avoid omeprazole and esomeprazole; if gastroprotection required, switch to pantoprazole or famotidine (minimal CYP2C19 interaction).",
    evidence_level: "Level 1B (FDA Safety Communication & ACC/AHA)",
  },
  {
    pair: ["allopurinol", "azathioprine"],
    severity: "CONTRAINDICATED",
    mechanism:
      "Allopurinol inhibition of xanthine oxidase, which is the primary metabolic inactivation pathway for 6-mercaptopurine.",
    clinical_effect:
      "Catastrophic 4- to 5-fold surge in active cytotoxic thiopurine metabolites, precipitating profound pancytopenia, severe bone marrow failure, and fatal sepsis.",
    recommendation:
      "CONTRAINDICATED unless deliberate low-dose co-therapy: reduce azathioprine dose by 75% with weekly CBC monitoring, or switch to febuxostat/mycophenolate.",
    evidence_level: "Level 1A (FDA Black Box Warning)",
  },
  {
    pair: ["lithium", "ibuprofen"],
    severity: "MAJOR",
    mechanism:
      "NSAID inhibition of renal prostaglandin synthesis, reducing renal blood flow and decreasing tubular lithium clearance.",
    clinical_effect:
      "Lithium serum accumulation by 30-60%, precipitating neurotoxicity (ataxia, tremors, confusion, seizures, renal failure).",
    recommendation:
      "Avoid systemic NSAIDs; use acetaminophen, tramadol, or low-dose topical formulations; check lithium level within 3-5 days if unavoidable.",
    evidence_level: "Level 1B (Established Pharmacokinetic Guideline)",
  },
  {
    pair: ["methotrexate", "trimethoprim"],
    severity: "MAJOR",
    mechanism:
      "Dual inhibition of dihydrofolate reductase (DHFR) plus competition for renal tubular excretion.",
    clinical_effect:
      "Extreme intracellular folate depletion, megaloblastic pancytopenia, severe mucositis, and acute nephrotoxicity.",
    recommendation:
      "Avoid trimethoprim or cotrimoxazole in patients taking methotrexate. Substitute with amoxicillin, cephalosporins, or macrolides.",
    evidence_level: "Level 1B (Practice Guideline)",
  },
];

export function DDICheckerModal({
  onClose,
  initialDrugs = ["Ticagrelor", "Aspirin"],
}: DDICheckerModalProps) {
  const [selectedDrugs, setSelectedDrugs] = useState<string[]>(initialDrugs);
  const [searchQuery, setSearchQuery] = useState("");
  const [copyFeedback, setCopyFeedback] = useState(false);
  const [serverInteractions, setServerInteractions] = useState<DDIItem[]>([]);
  const [acbScore, setAcbScore] = useState<number | null>(null);
  const [isEvaluatingServer, setIsEvaluatingServer] = useState(false);

  useEffect(() => {
    let active = true;
    const fetchServerDDI = async () => {
      if (selectedDrugs.length < 2) {
        setServerInteractions([]);
        setAcbScore(null);
        return;
      }
      setIsEvaluatingServer(true);
      try {
        const token = getStoredToken();
        const res = await fetch("/api/v1/hub/ddi-check", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ drugs: selectedDrugs }),
        });
        if (res.ok) {
          const data = await res.json();
          if (active) {
            if (Array.isArray(data.interactions)) {
              setServerInteractions(data.interactions);
            }
            if (data.anticholinergic_burden?.total_acb_score !== undefined) {
              setAcbScore(data.anticholinergic_burden.total_acb_score);
            }
          }
        }
      } catch {
        // Fallback safely to client rules
      } finally {
        if (active) setIsEvaluatingServer(false);
      }
    };
    fetchServerDDI();
    return () => {
      active = false;
    };
  }, [selectedDrugs]);

  // Unified interactions: combines local CPIC rules + server live polypharmacy evaluation
  const interactions: DDIItem[] = useMemo(() => {
    const list = selectedDrugs.map((d) => d.toLowerCase().trim());
    const results: DDIItem[] = [];
    const seen = new Set<string>();

    // 1. Process server interactions
    for (const s of serverInteractions) {
      const key = [s.drug1.toLowerCase(), s.drug2.toLowerCase()].sort().join("::");
      if (!seen.has(key)) {
        seen.add(key);
        results.push(s);
      }
    }

    // 2. Process local known high-alert rules
    for (let i = 0; i < list.length; i++) {
      for (let j = i + 1; j < list.length; j++) {
        const d1 = list[i];
        const d2 = list[j];

        for (const rule of KNOWN_DDI_RULES) {
          const [r1, r2] = rule.pair;
          if (
            ((d1.includes(r1) || r1.includes(d1)) && (d2.includes(r2) || r2.includes(d2))) ||
            ((d1.includes(r2) || r2.includes(d1)) && (d2.includes(r1) || r1.includes(d2)))
          ) {
            const key = [d1, d2].sort().join("::");
            if (!seen.has(key)) {
              seen.add(key);
              results.push({
                drug1: d1.charAt(0).toUpperCase() + d1.slice(1),
                drug2: d2.charAt(0).toUpperCase() + d2.slice(1),
                severity: rule.severity,
                mechanism: rule.mechanism,
                clinical_effect: rule.clinical_effect,
                recommendation: rule.recommendation,
                evidence_level: rule.evidence_level,
              });
            }
          }
        }
      }
    }
    return results;
  }, [selectedDrugs, serverInteractions]);

  const addDrug = (drugName: string) => {
    const trimmed = drugName.trim();
    if (!trimmed) return;
    if (!selectedDrugs.some((d) => d.toLowerCase() === trimmed.toLowerCase())) {
      setSelectedDrugs((prev) => [...prev, trimmed]);
    }
    setSearchQuery("");
  };

  const removeDrug = (drugName: string) => {
    setSelectedDrugs((prev) => prev.filter((d) => d.toLowerCase() !== drugName.toLowerCase()));
  };

  const hasContraindication = interactions.some((i) => i.severity === "CONTRAINDICATED");
  const hasMajor = interactions.some((i) => i.severity === "MAJOR");

  const copyReport = () => {
    const lines = [
      "DocAssistIQ — Clinical Pharmacokinetics & Drug Interaction Report",
      `Analyzed Agents: ${selectedDrugs.join(", ")}`,
      `Safety Status: ${
        hasContraindication
          ? "CRITICAL CONTRAINDICATION DETECTED"
          : hasMajor
          ? "MAJOR PHARMACOKINETIC INTERACTION"
          : interactions.length > 0
          ? "MODERATE INTERACTION"
          : "NO KNOWN MAJOR INTERACTIONS"
      }`,
      "",
      ...interactions.map(
        (int, idx) =>
          `[${idx + 1}] ${int.drug1} + ${int.drug2} (${int.severity})\n` +
          `Mechanism: ${int.mechanism}\n` +
          `Clinical Effect: ${int.clinical_effect}\n` +
          `Recommendation: ${int.recommendation}\n` +
          `Evidence: ${int.evidence_level}\n`
      ),
    ];

    navigator.clipboard?.writeText(lines.join("\n"));
    setCopyFeedback(true);
    setTimeout(() => setCopyFeedback(false), 2500);
  };

  return (
    <div className="fixed inset-0 z-[120] flex items-center justify-center p-3 sm:p-5 bg-slate-900/60 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="relative w-full max-w-2xl max-h-[90vh] flex flex-col rounded-3xl bg-white border border-slate-200 shadow-2xl overflow-hidden"
      >
        {/* Header */}
        <div className="p-5 border-b border-slate-200/80 flex items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl">💊</span>
              <h2 className="text-lg font-black tracking-tight text-slate-900">
                Medicine Safety & Interaction Checker
              </h2>
              <span className="text-[10px] bg-teal-50 text-teal-800 border border-teal-200 px-2 py-0.5 rounded-full font-bold">
                Safety Checker
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Check if two or more medications can be safely taken together.
            </p>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-600 flex items-center justify-center text-sm font-bold transition-colors cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* Selected Drugs Chips & Add Bar */}
        <div className="p-4 border-b border-slate-100 space-y-3">
          {/* Active Chips */}
          <div className="flex flex-wrap gap-1.5 min-h-[32px] items-center">
            {selectedDrugs.map((d) => (
              <span
                key={d}
                className="px-2.5 py-1 rounded-xl bg-teal-50 text-teal-800 border border-teal-200 text-xs font-bold flex items-center gap-1.5 shadow-2xs"
              >
                <span>{d}</span>
                <button
                  type="button"
                  onClick={() => removeDrug(d)}
                  className="hover:text-rose-600 transition-colors cursor-pointer font-black"
                >
                  ✕
                </button>
              </span>
            ))}
            {selectedDrugs.length === 0 && (
              <span className="text-xs text-slate-400 italic">
                Type medicine names below to check for interactions...
              </span>
            )}
            {acbScore !== null && (
              <span className="px-2.5 py-1 rounded-xl bg-purple-50 text-purple-800 border border-purple-200 text-xs font-bold flex items-center gap-1 shadow-2xs">
                🧠 Sedation / Confusion Risk: {acbScore >= 3 ? "High" : acbScore >= 1 ? "Moderate" : "Low"}
              </span>
            )}
            {isEvaluatingServer && (
              <span className="px-2.5 py-1 rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs font-semibold flex items-center gap-1.5 animate-pulse">
                ⚡ Checking safety database...
              </span>
            )}
          </div>

          {/* Input & Search */}
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs">
                💊
              </span>
              <input
                type="text"
                placeholder="Type a medicine name (e.g. Aspirin, Warfarin) and press enter..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && searchQuery.trim()) {
                    addDrug(searchQuery);
                  }
                }}
                className="w-full pl-8 pr-4 py-2 rounded-xl border border-slate-200 bg-white text-xs outline-none focus:border-teal-500 shadow-xs"
              />
            </div>
            <button
              onClick={() => addDrug(searchQuery)}
              disabled={!searchQuery.trim()}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold disabled:opacity-40 transition-all cursor-pointer"
            >
              + Add
            </button>
          </div>

          {/* Quick-add chips */}
          <div className="flex items-center gap-1.5 overflow-x-auto custom-scrollbar pb-1">
            <span className="text-[10px] uppercase font-bold text-slate-400 whitespace-nowrap">
              Quick Test:
            </span>
            {COMMON_DRUGS.slice(0, 8).map((d) => (
              <button
                key={d}
                onClick={() => addDrug(d)}
                className="text-[10px] font-bold px-2 py-0.5 rounded-lg border border-slate-200 hover:bg-teal-50 text-slate-600 transition-colors whitespace-nowrap cursor-pointer"
              >
                +{d}
              </button>
            ))}
          </div>
        </div>

        {/* Results Area */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar">
          {/* Status Alert Banner */}
          {interactions.length > 0 ? (
            <div
              className={`p-4 rounded-2xl border flex items-center justify-between gap-3 ${
                hasContraindication
                  ? "bg-rose-50 border-rose-300 text-rose-900"
                  : hasMajor
                  ? "bg-amber-50 border-amber-300 text-amber-900"
                  : "bg-teal-50 border-teal-300 text-teal-900"
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">
                  {hasContraindication ? "🚫" : hasMajor ? "⚠️" : "ℹ️"}
                </span>
                <div>
                  <h4 className="font-extrabold text-sm">
                    {hasContraindication
                      ? "DANGEROUS: DO NOT COMBINE"
                      : hasMajor
                      ? "MAJOR WARNING: USE CAUTION"
                      : "NOTICE: MONITOR PATIENT"}
                  </h4>
                  <p className="text-xs opacity-90 mt-0.5">
                    {interactions.length} warning(s) found between the {selectedDrugs.length} selected medicines.
                  </p>
                </div>
              </div>

              <button
                onClick={copyReport}
                className="px-3 py-1.5 rounded-xl bg-white border border-slate-300 text-xs font-bold text-slate-800 hover:bg-slate-50 transition-colors cursor-pointer shadow-xs whitespace-nowrap"
              >
                {copyFeedback ? "Copied ✓" : "Copy Report"}
              </button>
            </div>
          ) : (
            <div className="p-4 rounded-2xl border bg-emerald-50 border-emerald-200 text-emerald-900 flex items-center gap-3">
              <span className="text-2xl">✅</span>
              <div>
                <h4 className="font-extrabold text-sm">Safe: No Dangerous Interaction Found</h4>
                <p className="text-xs text-emerald-800 mt-0.5">
                  The selected medicines do not have any known major harmful interactions.
                </p>
              </div>
            </div>
          )}

          {/* Detailed Interaction Cards */}
          <div className="space-y-3">
            {interactions.map((int, i) => (
              <div
                key={i}
                className="p-4 rounded-2xl border border-slate-200 bg-white shadow-xs space-y-2.5"
              >
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-black text-slate-900">
                      {int.drug1} + {int.drug2}
                    </span>
                    <span
                      className={`text-[9px] font-black uppercase px-2 py-0.5 rounded-full ${
                        int.severity === "CONTRAINDICATED"
                          ? "bg-rose-100 text-rose-800"
                          : int.severity === "MAJOR"
                          ? "bg-amber-100 text-amber-800"
                          : "bg-teal-100 text-teal-800"
                      }`}
                    >
                      {int.severity === "CONTRAINDICATED"
                        ? "DO NOT COMBINE"
                        : int.severity === "MAJOR"
                        ? "HIGH RISK"
                        : "CAUTION"}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono">{int.evidence_level}</span>
                </div>

                <div className="text-xs space-y-1.5">
                  <p className="text-slate-600">
                    <strong className="text-slate-800">How they interact: </strong>
                    {int.mechanism}
                  </p>
                  <p className="text-slate-600">
                    <strong className="text-slate-800">Possible side effects: </strong>
                    {int.clinical_effect}
                  </p>
                  <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200/80 text-teal-900">
                    <strong className="text-slate-900">Recommended action: </strong>
                    {int.recommendation}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
