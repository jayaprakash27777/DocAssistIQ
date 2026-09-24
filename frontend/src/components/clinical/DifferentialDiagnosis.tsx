/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable react/no-unescaped-entities */
"use client";

import React, { useState, useEffect } from "react";
import { 
  getDifferentialDiagnosis, 
  predictRealtime, 
  getConsultationRealtimePrediction,
  DifferentialDiagnosisResponse,
  RealtimePredictionResponse,
  RealtimePredictionCandidate
} from "@/lib/api";
import { toast } from "react-hot-toast";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Bot, ChevronDown, ChevronUp, AlertTriangle, ShieldAlert, Globe, Clock, 
  Zap, Sparkles, Activity, CheckCircle2, Flame, Stethoscope, ArrowRight, ShieldCheck,
  Target, FlaskConical, Scale, FileText, Copy, Check, Table, HelpCircle, FileCheck, Pill
} from "lucide-react";
import InvestigationPanel from "./InvestigationPanel";
import MedicationPanel from "./MedicationPanel";
import DiseaseIntelligencePanel from "./DiseaseIntelligencePanel";
import EarlyWarningBanner from "./EarlyWarningBanner";
import EpiRadarAlert from "./EpiRadarAlert";
import ControversyScanner from "./ControversyScanner";
import FeedbackButtons from "./FeedbackButtons";
import ClinicalLoader from "./ClinicalLoader";
import { Button } from "@/components/ui/button";

const CLINICAL_PRESETS = [
  {
    label: "📋 Modified Duke Endocarditis Note",
    query: "48yo male with history of bicuspid aortic valve presenting with 3 weeks of intermittent fevers (Tmax 38.8C), night sweats, weight loss, and new pleuritic chest pain. On physical exam: BP 118/74, HR 98, new 3/6 holosystolic regurgitant murmur at apex, splinter hemorrhages beneath fingernails, and painless erythematous macules on palms (Janeway lesions). Labs: 2 separate blood cultures positive for Streptococcus viridans. Transthoracic echocardiogram demonstrates a 1.2 cm oscillating mobile vegetation on anterior mitral valve leaflet with severe mitral regurgitation. Denies IV drug use."
  },
  {
    label: "📋 Severe HAGMA / DKA Note",
    query: "24yo female with Type 1 Diabetes presenting with 2 days of severe nausea, persistent vomiting, diffuse abdominal pain, and rapid deep breathing. Exam: BP 102/68, HR 122, RR 32 (Kussmaul respirations), SpO2 99%, fruity odor on breath. Labs: Sodium 134 mEq/L, Potassium 5.4 mEq/L, Chloride 98 mEq/L, Bicarbonate 10 mEq/L, Glucose 480 mg/dL, BUN 38 mg/dL, Creatinine 1.4 mg/dL. Urinalysis reveals 4+ ketones and 4+ glucosuria. Denies fever or cough."
  },
  {
    label: "📋 Acute PE & Wells Note",
    query: "54yo female 10 days status-post total right hip arthroplasty presenting to the ED with sudden onset pleuritic right-sided chest pain, acute dyspnea, and hemoptysis. Exam: BP 112/76, HR 118, RR 28, SpO2 88% on room air. Right lower extremity is noticeably swollen, warm, and tender with right calf diameter 4.5 cm greater than left. 12-lead EKG shows sinus tachycardia with S1Q3T3 pattern. Denies fever, purulent sputum, or previous DVT history."
  },
  {
    label: "📋 Dermatomyositis / Inflammatory Myopathy Note",
    query: "46yo female presenting with 2 months of progressive proximal muscle weakness in bilateral deltoids and quadriceps, difficulty climbing stairs and combing hair. Physical exam: violaceous heliotrope rash on upper eyelids with periorbital edema, erythematous scaly Gottron papules overlying MCP and PIP joints, and mechanic's hands with hyperkeratotic fissuring. Labs: serum CK 14,200 U/L, positive anti-Jo-1 antibodies, aldolase 42 U/L, ALT 98 U/L, AST 112 U/L. EMG shows myopathic motor unit potentials with membrane irritability. Denies dysphagia."
  },
  {
    label: "📋 Acute Intermittent Porphyria Note",
    query: "29yo female presenting with severe diffuse colicky abdominal pain out of proportion to physical exam, nausea, and persistent vomiting following a 3-day water fast. Physical exam: BP 162/104, HR 116, abdomen is soft and non-distended without peritoneal signs, guarding, or rebound tenderness. Neurological exam reveals mild proximal upper-extremity motor weakness. Urinalysis demonstrates port-wine reddish-dark urine upon standing. Spot urine porphobilinogen (PBG) is markedly elevated at 48 mg/g creatinine. Denies fever, diarrhea, or previous abdominal surgeries."
  },
  {
    label: "📋 Bundibugyo VHF vs Malaria Note",
    query: "36yo male humanitarian field worker returning 6 days ago from rural community outbreak in Democratic Republic of Congo (DRC) presenting with high remittent fever 40.1°C, intense retro-orbital headache, diffuse myalgias, profound prostration, and conjunctival injection. On day 5 of illness developed spontaneous bleeding from venipuncture sites, melena, and petechial purpura on trunk. Exam: BP 88/54, HR 128, petechiae, ecchymoses, tender hepatomegaly. Labs: platelets 24,000/µL, AST 840 U/L, ALT 610 U/L. Denies recent mosquito net usage."
  },
  {
    label: "📋 Acute Stroke Note",
    query: "68yo male with PMH of HTN, HLD presenting with sudden onset right-sided hemiparesis and expressive aphasia starting 90 minutes ago. On exam: BP 178/102, HR 88, SpO2 98% RA. Right facial droop present. Pupils equal and reactive. Denies chest pain, shortness of breath, fever, or head trauma."
  },
  {
    label: "📋 Severe Preeclampsia Note",
    query: "31yo female G1P0 at 34 weeks gestation presenting with severe throbbing frontal headache and visual scotoma. Vitals: BP is 172/112 mmHg, HR 86, RR 18. Physical examination reveals 3+ bilateral lower extremity pitting edema, brisk deep tendon reflexes with 3 beats of unsustained clonus, and right upper quadrant abdominal tenderness. Urinalysis reveals 3+ proteinuria. Denies vaginal bleeding, leakage of fluid, or chest pain."
  },
  {
    label: "📋 STEMI EKG Note",
    query: "59yo male with 2-hour history of crushing retrosternal chest pressure radiating down left arm and into jaw, accompanied by profound diaphoresis and nausea. Vitals: BP 148/92, HR 104, SpO2 96%. 12-lead EKG shows marked ST-segment elevation in leads V1-V4. Denies cough, pleuritic pain, hemoptysis, or calf pain."
  },
  {
    label: "📋 Acute Heart Failure Note",
    query: "72yo female with past medical history of CAD and ischemic cardiomyopathy presenting with progressive shortness of breath, severe orthopnea requiring 4 pillows to sleep, and paroxysmal nocturnal dyspnea. Exam: BP 168/98, HR 108, RR 26, SpO2 89% on room air. Auscultation reveals bilateral basilar crackles, elevated JVP at 8 cm above sternal angle, audible S3 gallop, and 2+ pretibial pitting edema. Denies fever, chills, purulent sputum, or calf tenderness."
  },
  {
    label: "📋 SLE Lupus Flare",
    query: "27yo female presenting with 3-month history of fatigue, inflammatory polyarthritis of PIP and MCP joints with morning stiffness lasting >1 hour, and an erythematous photosensitive malar butterfly rash sparing the nasolabial folds. Laboratory evaluation demonstrates positive ANA at 1:640 titer, positive anti-dsDNA antibodies, and hypocomplementemia with low C3 and C4. Denies oral ulcers, alopecia, or lower extremity edema."
  },
  {
    label: "📋 Pulmonary Embolism (Wells Score)",
    query: "58yo female presenting with acute pleuritic chest pain and shortness of breath 12 days post right total knee arthroplasty with limited mobility. Exam: HR 114 bpm, RR 24, SpO2 91% RA. Right lower extremity demonstrates asymmetric calf swelling with 3 cm greater circumference than left and deep tenderness (signs of DVT)."
  },
  {
    label: "📋 Infective Endocarditis (Duke Criteria)",
    query: "35yo male with history of IVDU presenting with 2 weeks of persistent daily fevers, drenching night sweats, and progressive fatigue. Exam: T 38.6°C, HR 98, new grade 3/6 holosystolic regurgitant murmur at apex, Janeway lesions on palms, subungual splinter hemorrhages. TTE shows 1.2 cm oscillating mobile mitral valve vegetation with regurgitation. Blood cultures x2 grow Enterococcus faecalis."
  },
  { label: "🎯 Appendicitis", query: "periumbilical pain migrating to right lower quadrant, nausea, vomiting, fever, McBurney point tenderness" },
  { label: "🚨 Acute MI", query: "central crushing chest pain, radiating to left arm, diaphoresis, shortness of breath, nausea" },
  { label: "🚨 Aortic Dissection", query: "sudden severe tearing chest pain radiating to back between shoulder blades, bp discrepancy between arms" },
  { label: "⚡ Gout (Podagra)", query: "acute severe joint pain in great toe, podagra, first mtp redness and exquisite tenderness" },
  { label: "⚠️ Temporal Arteritis", query: "severe temporal headache, jaw claudication, scalp tenderness, blurred vision in 70yo" },
  { label: "🚨 Kawasaki Disease", query: "high fever for 6 days, strawberry tongue, bilateral conjunctivitis, cracked red lips, swollen hands" },
  { label: "🚨 Epiglottitis", query: "severe sore throat, difficulty swallowing, drooling, tripod position, inspiratory stridor" },
  { label: "🧬 Wilson Disease", query: "kayser-fleischer rings, copper accumulation, asterixis, jaundice, tremor" },
  { label: "🚨 Anaphylaxis", query: "facial swelling, lip swelling, angioedema, hives, stridor, wheezing, hypotension after allergen" },
  { label: "🚨 Tension Pneumothorax", query: "sudden sharp pleuritic chest pain, severe shortness of breath, tracheal deviation away from affected side, absent breath sounds" },
  { label: "🎯 Lyme Disease", query: "expanding bullseye rash, erythema migrans, tick bite history, fever, fatigue" },
];

const SIMULATED_LAB_CHIPS = [
  { label: "+ hs-Troponin Positive", token: "elevated cardiac troponin" },
  { label: "+ D-Dimer High (>500)", token: "elevated D-dimer" },
  { label: "+ Blood Cultures Gram +", token: "positive blood cultures" },
  { label: "+ Anion Gap > 16 (HAGMA)", token: "anion gap metabolic acidosis" },
  { label: "+ Marked Lipase Elevation", token: "elevated serum lipase" },
  { label: "+ Anti-Jo-1 / CK 1450", token: "Gottron's papules, elevated CK, positive anti-Jo-1 antibody" },
  { label: "+ Dark Port-Wine Urine", token: "port-wine urine with elevated urine porphobilinogen" },
  { label: "- Normal D-Dimer & Troponin", token: "normal d-dimer and troponin" },
];

export default function DifferentialDiagnosis({ 
  consultationId, 
  trigger, 
  initialQuery = "" 
}: { 
  consultationId: string; 
  trigger?: any; 
  initialQuery?: string;
}) {
  const [data, setData] = useState<DifferentialDiagnosisResponse | null>(null);
  const [loading, setLoading] = useState(false); // Start false — user triggers
  const [hasLoaded, setHasLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [symptomInput, setSymptomInput] = useState(initialQuery);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [showInvestigationsFor, setShowInvestigationsFor] = useState<string | null>(null);
  const [showMedicationsFor, setShowMedicationsFor] = useState<string | null>(null);
  const [realtimePanelFor, setRealtimePanelFor] = useState<{
    disease: string;
    tab: "investigations" | "medications" | "intelligence";
  } | null>(null);

  // High-Impact Physician CDS states
  const [showComparisonMatrix, setShowComparisonMatrix] = useState(false);
  const [showMdmModal, setShowMdmModal] = useState(false);
  const [copiedMdm, setCopiedMdm] = useState(false);

  const handleBedsideAnswer = (token: string) => {
    setSymptomInput(prev => {
      const clean = prev.trim();
      if (!clean) return token;
      return `${clean}, ${token}`;
    });
    toast.success(`Appended finding: "${token}"`, {
      icon: "⚡",
      duration: 2500,
    });
  };

  const handleSimulateLab = (labFinding: string) => {
    setSymptomInput(prev => {
      const clean = prev.trim();
      if (!clean) return labFinding;
      return `${clean}, ${labFinding}`;
    });
    toast.success(`Simulated pending lab finding: "${labFinding}"`, {
      icon: "🧪",
      duration: 2500,
    });
  };

  const handleCopyMdm = () => {
    if (realtimeResult?.clinical_mdm_summary) {
      navigator.clipboard.writeText(realtimeResult.clinical_mdm_summary);
      setCopiedMdm(true);
      toast.success("EMR Assessment & Plan copied to clipboard!", { icon: "📋" });
      setTimeout(() => setCopiedMdm(false), 3000);
    }
  };

  // Sub-30ms Real-Time Prediction state
  const [realtimeResult, setRealtimeResult] = useState<RealtimePredictionResponse | null>(null);
  const [isPredicting, setIsPredicting] = useState(false);

  // Sync symptomInput if initialQuery arrives late (e.g. consultation fetch)
  useEffect(() => {
    if (initialQuery && initialQuery.trim() && initialQuery !== symptomInput) {
      setSymptomInput(initialQuery);
    }
  }, [initialQuery]);

  // Initial load of real-time prediction on mount or consultationId/initialQuery change
  useEffect(() => {
    let isCancelled = false;
    const loadInitial = async () => {
      setIsPredicting(true);
      if (initialQuery?.trim()) {
        const res = await predictRealtime({
          symptoms: initialQuery,
          consultation_id: consultationId,
        });
        if (!isCancelled && res.ok && res.data.status !== "INSUFFICIENT_INFO") {
          setRealtimeResult(res.data);
        }
      } else if (consultationId) {
        const res = await getConsultationRealtimePrediction(consultationId);
        if (!isCancelled && res.ok && res.data.status !== "INSUFFICIENT_INFO") {
          setRealtimeResult(res.data);
        }
      }
      if (!isCancelled) setIsPredicting(false);
    };
    loadInitial();
    return () => { isCancelled = true; };
  }, [consultationId, initialQuery]);

  // Debounced live prediction whenever symptomInput changes
  useEffect(() => {
    if (!symptomInput.trim()) {
      return;
    }
    const timer = setTimeout(async () => {
      setIsPredicting(true);
      const res = await predictRealtime({
        symptoms: symptomInput,
        consultation_id: consultationId,
      });
      if (res.ok) {
        setRealtimeResult(res.data);
      }
      setIsPredicting(false);
    }, 150);

    return () => clearTimeout(timer);
  }, [symptomInput, consultationId]);

  const runAnalysis = async (symptomsOverride?: string) => {
    setLoading(true);
    setError(null);
    const symptomsToPass = symptomsOverride ?? symptomInput;
    const res = await getDifferentialDiagnosis(consultationId, symptomsToPass || undefined);
    if (res.ok) {
      setData(res.data);
    } else {
      const msg = res.error?.message || "AI analysis failed";
      if (msg !== "Not Found" && !msg.includes("403")) {
        setError(msg);
        toast.error(msg);
      } else {
        setError("No clinical data available yet. Add symptoms or notes first.");
      }
    }
    setLoading(false);
    setHasLoaded(true);
  };

  // Auto-load when trigger changes (e.g., findings appear or status is ready)
  useEffect(() => {
    if (trigger && (typeof trigger === "number" ? trigger > 0 : Boolean(trigger))) {
      runAnalysis();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [consultationId, trigger]);
  // ── Unified Render: Real-Time HUD always accessible + Deep Analysis below ──
  return (
    <>
      {/* ── Sub-30ms Real-Time Live Clinical Predictor HUD (Always Available) ── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6 rounded-3xl overflow-hidden border border-indigo-200/80 bg-gradient-to-br from-blue-50/70 via-white/90 to-indigo-50/70 shadow-[0_12px_36px_rgba(79,70,229,0.08),inset_0_1px_0_rgba(255,255,255,0.95)] backdrop-blur-2xl"
      >
        {/* Top Header */}
        <div className="px-6 py-4 flex items-center justify-between bg-gradient-to-r from-indigo-700 via-indigo-600 to-purple-600 text-white shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-white/20 flex items-center justify-center backdrop-blur-md">
              <Zap className="w-4 h-4 text-amber-300 animate-pulse" />
            </div>
            <div>
              <h3 className="font-black text-sm tracking-wider uppercase flex items-center gap-2">
                REAL-TIME CLINICAL PREDICTOR
                <span className="text-[10px] bg-amber-400 text-indigo-950 px-2 py-0.5 rounded-full font-black uppercase tracking-widest shadow-sm">
                  ⚡ SUB-10MS
                </span>
              </h3>
              <p className="text-[11px] text-indigo-100/90 font-medium text-left">
                Universal Medical Diagnostic Engine — Evaluates 260+ Clinical Profiles &amp; Open Domain
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {realtimeResult && (
              <span className="text-[11px] font-black bg-emerald-500/20 text-emerald-200 border border-emerald-400/30 px-3 py-1 rounded-full flex items-center gap-1.5 shadow-sm">
                <Activity className="w-3 h-3 text-emerald-400" />
                {realtimeResult.latency_ms} ms Latency
              </span>
            )}
          </div>
        </div>

        <div className="p-6 md:p-8 flex flex-col gap-6">
          {/* Presets Bar */}
          <div>
            <div className="flex items-center gap-2 mb-2.5">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              <span className="text-xs font-extrabold text-slate-700 uppercase tracking-wider">
                Instant Clinical Cases (1-Click Test Any Disease):
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {CLINICAL_PRESETS.map((preset, i) => (
                <button
                  key={i}
                  onClick={() => setSymptomInput(preset.query)}
                  className="px-3 py-1.5 rounded-xl text-xs font-bold bg-white/90 text-slate-700 border border-slate-200/80 hover:border-indigo-400 hover:bg-indigo-50/80 hover:text-indigo-700 shadow-sm transition-all hover:scale-105 active:scale-95 flex items-center gap-1.5"
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          {/* Symptoms input area */}
          <div className="w-full">
            <label className="block text-xs font-bold text-slate-700 mb-1.5 text-left flex items-center justify-between">
              <span>Patient Symptoms &amp; Clinical Presentation (Real-Time Live Typing):</span>
              {isPredicting && (
                <span className="text-[11px] text-indigo-600 font-semibold flex items-center gap-1">
                  <div className="w-2.5 h-2.5 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
                  Predicting live…
                </span>
              )}
            </label>
            <textarea
              value={symptomInput}
              onChange={e => setSymptomInput(e.target.value)}
              placeholder="Type symptoms or click a preset above (e.g. severe tearing chest pain radiating to back between shoulder blades, bp discrepancy...)"
              rows={3}
              className="w-full text-sm font-medium rounded-2xl px-4 py-3.5 resize-none outline-none border border-indigo-200/80 bg-white text-slate-800 placeholder-slate-400 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 transition-all shadow-[inset_0_1px_2px_rgba(0,0,0,0.04)]"
            />
            <div className="flex items-center justify-between text-[11px] font-medium text-slate-400 mt-1.5 px-1">
              <span>💡 Updates live as you type without waiting</span>
              <button
                onClick={() => setSymptomInput("")}
                className="text-slate-400 hover:text-slate-600 underline text-[11px]"
              >
                Clear input
              </button>
            </div>
            {/* Interactive "What-If" Diagnostic Lab Simulator */}
            <div className="mt-2.5 pt-2.5 border-t border-slate-200/50 text-left">
              <div className="flex items-center gap-1.5 mb-1.5">
                <FlaskConical className="w-3.5 h-3.5 text-indigo-600" />
                <span className="text-[11px] font-extrabold text-slate-600 uppercase tracking-wider">
                  "What-If?" Pending Diagnostic Lab Simulator:
                </span>
                <span className="text-[10px] text-slate-400 font-medium hidden sm:inline">
                  (Click to simulate stat confirmatory lab results in real-time)
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {SIMULATED_LAB_CHIPS.map((chip, ci) => (
                  <button
                    key={ci}
                    type="button"
                    onClick={() => handleSimulateLab(chip.token)}
                    className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-indigo-50/70 text-indigo-700 border border-indigo-200/60 hover:bg-indigo-100/80 hover:border-indigo-300 transition-all flex items-center gap-1 shadow-xs hover:scale-102 active:scale-98"
                  >
                    <span>{chip.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Emergency Alert Banner if detected */}
          <AnimatePresence>
            {realtimeResult?.emergency_alert?.is_emergency && (
              <motion.div
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.96 }}
                className="p-5 rounded-2xl bg-gradient-to-r from-red-500 to-rose-600 text-white shadow-lg border border-red-400/50 flex flex-col md:flex-row items-start md:items-center gap-4 animate-pulse"
              >
                <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center flex-shrink-0">
                  <ShieldAlert className="w-6 h-6 text-white" />
                </div>
                <div className="flex-grow text-left">
                  <h4 className="text-base font-black tracking-tight">{realtimeResult.emergency_alert.condition}</h4>
                  <p className="text-xs text-red-100 font-semibold mb-1">{realtimeResult.emergency_alert.warning}</p>
                  <p className="text-xs text-white/95 font-bold bg-black/20 px-3 py-1.5 rounded-lg border border-white/15 inline-block">
                    ⚡ Immediate Action: {realtimeResult.emergency_alert.immediate_action}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Must-Not-Miss / Critical Emergency Rule-Out Watchlist */}
          {realtimeResult?.must_not_miss_candidates && realtimeResult.must_not_miss_candidates.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-5 rounded-2xl bg-gradient-to-r from-red-950/90 via-rose-950/90 to-slate-950 text-white shadow-lg border border-red-500/40 text-left"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2.5 border-b border-white/10">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-red-600/30 border border-red-400/40 flex items-center justify-center">
                    <ShieldAlert className="w-4 h-4 text-red-400 animate-pulse" />
                  </div>
                  <div>
                    <h4 className="text-xs font-black uppercase tracking-wider text-red-200 flex items-center gap-2">
                      Must-Not-Miss Critical Emergency Watchlist
                      <span className="text-[10px] bg-red-500/30 text-red-200 border border-red-400/40 px-2 py-0.5 rounded-full font-bold">
                        Cognitive Safety Net
                      </span>
                    </h4>
                    <p className="text-[11px] text-red-200/80 font-medium">
                      High-acuity emergencies sharing features with current presentation — active bedside rule-out required:
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {realtimeResult.must_not_miss_candidates.map((item, mi) => (
                  <div
                    key={mi}
                    className="p-3.5 rounded-xl bg-white/5 border border-red-500/30 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <span className="font-extrabold text-sm text-white">{item.disease}</span>
                        <span className={`text-[9px] font-black px-1.5 py-0.5 rounded ${
                          item.in_top_candidates
                            ? "bg-red-500 text-white"
                            : "bg-slate-800 text-slate-300 border border-slate-700"
                        }`}>
                          {item.in_top_candidates ? "IN DIFFERENTIAL" : "RULE-OUT TARGET"}
                        </span>
                      </div>
                      <p className="text-[11px] text-red-100 font-medium mb-2 leading-relaxed">
                        ⚡ <strong>Action:</strong> {item.immediate_action}
                      </p>
                    </div>
                    {item.confirmatory_tests && item.confirmatory_tests.length > 0 && (
                      <div className="text-[10px] text-slate-300 bg-black/40 px-2 py-1.5 rounded-lg border border-white/5">
                        <strong className="text-red-300">Rule-Out Test:</strong> {item.confirmatory_tests.join(", ")}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Unstructured Clinical Note Parser Transparency Card */}
          {realtimeResult?.is_unstructured_note && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-5 rounded-2xl bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white shadow-md border border-indigo-500/30 text-left"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2.5 border-b border-white/10">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                  <h4 className="text-xs font-black uppercase tracking-wider text-indigo-200 flex items-center gap-1.5">
                    <span>🧠 Real-Time Note Parser</span>
                    <span className="text-[10px] bg-indigo-800/80 text-indigo-100 px-2 py-0.5 rounded-full border border-indigo-400/30">
                      Clause-Level Scope &amp; Negation
                    </span>
                  </h4>
                </div>
                {realtimeResult.note_summary && (
                  <span className="text-[11px] font-medium text-slate-300 italic">
                    {realtimeResult.note_summary}
                  </span>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                {/* Positive Extracted Findings */}
                {realtimeResult.extracted_findings && realtimeResult.extracted_findings.length > 0 && (
                  <div className="bg-white/5 rounded-xl p-3 border border-emerald-500/20">
                    <div className="font-bold text-emerald-400 mb-1.5 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Extracted Clinical Findings ({realtimeResult.extracted_findings.length}):</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {realtimeResult.extracted_findings.map((f, i) => (
                        <span key={i} className="px-2 py-0.5 rounded-md bg-emerald-950/60 text-emerald-200 border border-emerald-500/30 text-[11px] font-medium">
                          {f}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Negated Findings Scoped Out */}
                {realtimeResult.extracted_negated && realtimeResult.extracted_negated.length > 0 && (
                  <div className="bg-white/5 rounded-xl p-3 border border-rose-500/20">
                    <div className="font-bold text-rose-400 mb-1.5 flex items-center gap-1">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      <span>Negated / Ruled Out Findings ({realtimeResult.extracted_negated.length}):</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {realtimeResult.extracted_negated.map((n, i) => (
                        <span key={i} className="px-2 py-0.5 rounded-md bg-rose-950/60 text-rose-200 border border-rose-500/30 text-[11px] font-medium line-through">
                          {n}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Extracted Vitals */}
                {realtimeResult.extracted_vitals && Object.keys(realtimeResult.extracted_vitals).length > 0 && (
                  <div className="bg-white/5 rounded-xl p-3 border border-sky-500/20">
                    <div className="font-bold text-sky-400 mb-1.5 flex items-center gap-1">
                      <Activity className="w-3.5 h-3.5" />
                      <span>Extracted Vital Signs:</span>
                    </div>
                    <div className="flex flex-wrap gap-2 text-[11px] font-medium text-sky-200">
                      {realtimeResult.extracted_vitals.blood_pressure && (
                        <span className="px-2 py-0.5 rounded-md bg-sky-950/60 border border-sky-500/30">
                          BP: <strong>{realtimeResult.extracted_vitals.blood_pressure}</strong>
                        </span>
                      )}
                      {realtimeResult.extracted_vitals.heart_rate && (
                        <span className="px-2 py-0.5 rounded-md bg-sky-950/60 border border-sky-500/30">
                          HR: <strong>{realtimeResult.extracted_vitals.heart_rate} bpm</strong>
                        </span>
                      )}
                      {realtimeResult.extracted_vitals.respiratory_rate && (
                        <span className="px-2 py-0.5 rounded-md bg-sky-950/60 border border-sky-500/30">
                          RR: <strong>{realtimeResult.extracted_vitals.respiratory_rate}/min</strong>
                        </span>
                      )}
                      {realtimeResult.extracted_vitals.oxygen_saturation && (
                        <span className="px-2 py-0.5 rounded-md bg-sky-950/60 border border-sky-500/30">
                          SpO2: <strong>{realtimeResult.extracted_vitals.oxygen_saturation}%</strong>
                        </span>
                      )}
                      {realtimeResult.extracted_vitals.temperature && (
                        <span className="px-2 py-0.5 rounded-md bg-sky-950/60 border border-sky-500/30">
                          Temp: <strong>{realtimeResult.extracted_vitals.temperature}°</strong>
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Diagnostic Markers */}
                {realtimeResult.diagnostic_markers && realtimeResult.diagnostic_markers.length > 0 && (
                  <div className="bg-white/5 rounded-xl p-3 border border-amber-500/20">
                    <div className="font-bold text-amber-400 mb-1.5 flex items-center gap-1">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Pathognomonic Diagnostic Markers:</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {realtimeResult.diagnostic_markers.map((d, i) => (
                        <span key={i} className="px-2 py-0.5 rounded-md bg-amber-950/60 text-amber-200 border border-amber-500/30 text-[11px] font-medium">
                          {d}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* EHR Section Breakdown */}
                {realtimeResult.section_breakdown && Object.keys(realtimeResult.section_breakdown).length > 0 && (
                  <div className="bg-white/5 rounded-xl p-3 border border-indigo-500/20 col-span-1 md:col-span-2">
                    <div className="font-bold text-indigo-300 mb-1.5 flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5" />
                      <span>EHR Document Section Breakdown:</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {Object.keys(realtimeResult.section_breakdown).map((sec, si) => (
                        <span key={si} className="px-2.5 py-1 rounded-md bg-indigo-950/70 text-indigo-200 border border-indigo-500/30 text-[11px] font-semibold flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                          {sec.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Isolated Background Distractors */}
                {realtimeResult.background_history && realtimeResult.background_history.length > 0 && (
                  <div className="bg-white/5 rounded-xl p-3 border border-slate-600/30 col-span-1 md:col-span-2">
                    <div className="font-bold text-slate-300 mb-1.5 flex items-center justify-between">
                      <span className="flex items-center gap-1.5">
                        <ShieldCheck className="w-3.5 h-3.5 text-slate-400" />
                        <span>Isolated Past Medical &amp; Background Distractors ({realtimeResult.background_history.length}):</span>
                      </span>
                      <span className="text-[10px] text-slate-400 font-medium italic">
                        Isolated from acute diagnostic score weighting
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {realtimeResult.background_history.map((h, hi) => (
                        <span key={hi} className="px-2 py-0.5 rounded-md bg-slate-800/80 text-slate-300 border border-slate-600/40 text-[11px] font-medium">
                          {h}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* Quantitative Biomarkers & Calculated Indices Card */}
          {((realtimeResult?.calculated_indices && Object.keys(realtimeResult.calculated_indices).length > 0) ||
            (realtimeResult?.quantitative_labs && Object.keys(realtimeResult.quantitative_labs).length > 0)) && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-5 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-950 text-white shadow-lg border border-indigo-500/30 text-left"
            >
              <div className="flex items-center justify-between pb-3 border-b border-white/10 mb-3">
                <div className="flex items-center gap-2">
                  <FlaskConical className="w-4 h-4 text-cyan-400" />
                  <h4 className="text-xs font-black uppercase tracking-wider text-cyan-200">
                    Quantitative Biomarkers &amp; Calculated Physiological Indices
                  </h4>
                </div>
                <span className="text-[10px] bg-cyan-950 text-cyan-300 border border-cyan-500/30 px-2.5 py-0.5 rounded-full font-bold">
                  ⚡ Deterministic Calculation
                </span>
              </div>

              {/* Calculated Indices */}
              {realtimeResult.calculated_indices && Object.keys(realtimeResult.calculated_indices).length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 mb-3">
                  {realtimeResult.calculated_indices.anion_gap !== undefined && (
                    <div className="bg-white/5 rounded-xl p-3 border border-amber-500/30">
                      <div className="text-[10px] uppercase font-extrabold text-amber-300 tracking-wider">Serum Anion Gap</div>
                      <div className="text-lg font-black text-white mt-0.5">
                        {realtimeResult.calculated_indices.anion_gap} <span className="text-xs font-semibold text-slate-300">mEq/L</span>
                      </div>
                      <div className="text-[11px] font-bold text-amber-200 mt-1">
                        {realtimeResult.calculated_indices.anion_gap > 12 ? "⚠️ High Anion Gap Metabolic Acidosis (HAGMA)" : "✓ Normal Anion Gap (≤12)"}
                      </div>
                    </div>
                  )}
                  {realtimeResult.calculated_indices.bun_cr_ratio !== undefined && (
                    <div className="bg-white/5 rounded-xl p-3 border border-sky-500/30">
                      <div className="text-[10px] uppercase font-extrabold text-sky-300 tracking-wider">BUN / Creatinine Ratio</div>
                      <div className="text-lg font-black text-white mt-0.5">
                        {realtimeResult.calculated_indices.bun_cr_ratio}
                      </div>
                      <div className="text-[11px] font-bold text-sky-200 mt-1">
                        {realtimeResult.calculated_indices.bun_cr_ratio > 20 ? "⚠️ Prerenal Azotemia Pattern (>20:1)" : "✓ Normal / Intrinsic Pattern"}
                      </div>
                    </div>
                  )}
                  {realtimeResult.calculated_indices.csf_serum_glucose_ratio !== undefined && (
                    <div className="bg-white/5 rounded-xl p-3 border border-rose-500/30">
                      <div className="text-[10px] uppercase font-extrabold text-rose-300 tracking-wider">CSF / Serum Glucose Ratio</div>
                      <div className="text-lg font-black text-white mt-0.5">
                        {realtimeResult.calculated_indices.csf_serum_glucose_ratio}
                      </div>
                      <div className="text-[11px] font-bold text-rose-200 mt-1">
                        {realtimeResult.calculated_indices.csf_serum_glucose_ratio < 0.40 ? "🚨 Hypoglycorrhachia (Bacterial Meningitis)" : "✓ Normal Ratio (≥0.60)"}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Extracted Quantitative Labs */}
              {realtimeResult.quantitative_labs && Object.keys(realtimeResult.quantitative_labs).length > 0 && (
                <div>
                  <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 mb-1.5">
                    Extracted Exact Lab Values &amp; Severity Tiers:
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(realtimeResult.quantitative_labs).map(([key, lab]: [string, any], li) => (
                      <div key={li} className="px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-xs flex items-center gap-1.5">
                        <span className="font-bold text-slate-300 uppercase">{key.replace(/_/g, ' ')}:</span>
                        <span className="font-extrabold text-cyan-300">{lab.value} {lab.unit}</span>
                        {lab.flag && (
                          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                            lab.flag.includes('severe') || lab.flag.includes('critical') || lab.flag.includes('massive')
                              ? 'bg-rose-900/60 text-rose-200 border border-rose-500/40'
                              : 'bg-amber-900/60 text-amber-200 border border-amber-500/40'
                          }`}>
                            {lab.flag.replace(/_/g, ' ')}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* Consensus Clinical Diagnostic Criteria Evaluator */}
          {realtimeResult?.criteria_evaluations && realtimeResult.criteria_evaluations.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-5 rounded-2xl bg-gradient-to-br from-indigo-950/95 via-slate-900 to-slate-950 text-white shadow-xl border border-indigo-500/40 text-left"
            >
              <div className="flex items-center justify-between pb-3 border-b border-white/10 mb-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-indigo-600/60 flex items-center justify-center border border-indigo-400/30">
                    <Scale className="w-4 h-4 text-indigo-300" />
                  </div>
                  <div>
                    <h4 className="text-xs font-black uppercase tracking-wider text-indigo-200 flex items-center gap-2">
                      Consensus Clinical Diagnostic Criteria Evaluator
                      <span className="text-[10px] bg-indigo-500/30 text-indigo-200 border border-indigo-400/30 px-2 py-0.5 rounded-full font-bold">
                        Formal Validated Scoring
                      </span>
                    </h4>
                    <p className="text-[11px] text-slate-400 font-medium">
                      Automated evaluation of ACR/EULAR, Modified Duke, Wells PE &amp; PERC, Bohan &amp; Peter, Centor/McIsaac
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                {realtimeResult.criteria_evaluations.map((evalItem, ei) => (
                  <div
                    key={ei}
                    className={`p-4 rounded-xl border transition-all ${
                      evalItem.meets_criteria
                        ? 'bg-emerald-950/40 border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.15)]'
                        : 'bg-white/5 border-slate-700/60'
                    }`}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                      <span className="font-extrabold text-sm text-white flex items-center gap-2">
                        {evalItem.criteria_name}
                      </span>
                      <span className={`text-xs font-black px-2.5 py-1 rounded-lg flex items-center gap-1.5 shadow-sm ${
                        evalItem.meets_criteria
                          ? 'bg-emerald-500 text-white'
                          : 'bg-slate-700 text-slate-300'
                      }`}>
                        {evalItem.meets_criteria ? '✓ CRITERIA FULFILLED' : 'SUBTHRESHOLD / RULE-OUT'}
                      </span>
                    </div>

                    <div className="text-xs font-medium text-slate-300 mb-2 flex flex-wrap items-center gap-x-4 gap-y-1">
                      {evalItem.total_score !== undefined && evalItem.total_score !== null && (
                        <span>
                          Calculated Score: <strong className="text-white text-sm">{evalItem.total_score}</strong>
                          {evalItem.threshold !== undefined && evalItem.threshold !== null && (
                            <span className="text-slate-400"> (Threshold: {evalItem.threshold})</span>
                          )}
                        </span>
                      )}
                      {evalItem.major_criteria_met !== undefined && (
                        <span>
                          Major Criteria: <strong className="text-emerald-400">{evalItem.major_criteria_met}</strong> | Minor Criteria: <strong className="text-amber-400">{evalItem.minor_criteria_met}</strong>
                        </span>
                      )}
                      {evalItem.risk_category && (
                        <span>
                          Risk Stratification: <strong className="text-amber-300">{evalItem.risk_category}</strong>
                        </span>
                      )}
                      {evalItem.clinical_interpretation && (
                        <span className="text-slate-300 italic">
                          — {evalItem.clinical_interpretation}
                        </span>
                      )}
                    </div>

                    {/* Fulfilled items */}
                    {evalItem.fulfilled_items && evalItem.fulfilled_items.length > 0 && (
                      <div className="bg-black/30 rounded-lg p-2.5 border border-white/5 mb-2">
                        <span className="text-[10px] uppercase font-extrabold text-slate-400 block mb-1">
                          Validated Criterion Elements Met:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {evalItem.fulfilled_items.map((item, ii) => (
                            <span key={ii} className="text-[11px] font-semibold bg-emerald-900/40 text-emerald-200 border border-emerald-500/30 px-2 py-0.5 rounded-md">
                              ✓ {item}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Actionable Clinical Recommendation */}
                    {(evalItem.recommendation || evalItem.management_recommendation) && (
                      <div className="text-xs font-semibold text-amber-200 bg-amber-950/40 border border-amber-500/30 rounded-lg px-3 py-1.5 flex items-start gap-2">
                        <Sparkles className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                        <span>
                          <strong>Clinical Action:</strong> {evalItem.recommendation || evalItem.management_recommendation}
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Live Real-Time Prediction Results */}
          {realtimeResult && realtimeResult.top_candidates.length > 0 && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200/60 pb-3">
                <div className="flex items-center gap-3">
                  <h4 className="text-sm font-black text-slate-800 uppercase tracking-wider flex items-center gap-2">
                    <Stethoscope className="w-4 h-4 text-indigo-600" />
                    Live Differential Diagnosis (<span className="text-indigo-600">{realtimeResult.top_candidates.length}</span> candidates ranked)
                  </h4>
                  <span className="text-[11px] font-bold text-slate-500">
                    Computed in <strong className="text-emerald-600">{realtimeResult.latency_ms}ms</strong>
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  {/* Compare Side-by-Side Button */}
                  {realtimeResult.comparison_matrix && realtimeResult.comparison_matrix.length > 1 && (
                    <button
                      type="button"
                      onClick={() => setShowComparisonMatrix(prev => !prev)}
                      className="px-3 py-1.5 rounded-xl text-xs font-bold bg-purple-50 text-purple-700 hover:bg-purple-100 border border-purple-200/80 shadow-xs transition-all flex items-center gap-1.5"
                    >
                      <Table className="w-3.5 h-3.5" />
                      <span>{showComparisonMatrix ? "Hide Matrix" : "📊 Compare Side-by-Side"}</span>
                    </button>
                  )}

                  {/* Copy MDM Note Button */}
                  {realtimeResult.clinical_mdm_summary && (
                    <button
                      type="button"
                      onClick={handleCopyMdm}
                      className="px-3 py-1.5 rounded-xl text-xs font-bold bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white shadow-xs transition-all flex items-center gap-1.5 hover:scale-102 active:scale-98"
                    >
                      {copiedMdm ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedMdm ? "Copied MDM!" : "📋 Copy EMR MDM Note"}</span>
                    </button>
                  )}

                  {realtimeResult.clinical_mdm_summary && (
                    <button
                      type="button"
                      onClick={() => setShowMdmModal(prev => !prev)}
                      className="px-2.5 py-1.5 rounded-xl text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 shadow-xs transition-all"
                      title="Preview full EMR Medical Decision Making Note"
                    >
                      <FileCheck className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>

              {/* Collapsible EMR MDM Assessment & Plan Preview Drawer */}
              <AnimatePresence>
                {showMdmModal && realtimeResult.clinical_mdm_summary && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="overflow-hidden rounded-2xl border border-indigo-200 bg-slate-900 text-white shadow-xl text-left"
                  >
                    <div className="p-4 bg-slate-950 border-b border-white/10 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-indigo-400" />
                        <h4 className="text-xs font-black uppercase tracking-wider text-indigo-200">
                          EMR Medical Decision Making (MDM) Note Preview
                        </h4>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={handleCopyMdm}
                          className="px-3 py-1 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white flex items-center gap-1"
                        >
                          {copiedMdm ? <Check className="w-3 h-3 text-emerald-300" /> : <Copy className="w-3 h-3" />}
                          <span>{copiedMdm ? "Copied!" : "Copy Note"}</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => setShowMdmModal(false)}
                          className="text-xs text-slate-400 hover:text-white"
                        >
                          Close
                        </button>
                      </div>
                    </div>
                    <div className="p-4">
                      <pre className="text-xs font-mono text-slate-200 whitespace-pre-wrap leading-relaxed max-h-72 overflow-y-auto bg-black/40 p-3.5 rounded-xl border border-white/5">
                        {realtimeResult.clinical_mdm_summary}
                      </pre>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Side-by-Side Diagnostic Comparison Matrix */}
              <AnimatePresence>
                {showComparisonMatrix && realtimeResult.comparison_matrix && realtimeResult.comparison_matrix.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="overflow-hidden rounded-2xl border border-purple-200/80 bg-white/95 shadow-md text-left"
                  >
                    <div className="p-4 bg-gradient-to-r from-purple-900 to-indigo-950 text-white flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Table className="w-4 h-4 text-purple-300" />
                        <h4 className="text-xs font-black uppercase tracking-wider text-purple-200">
                          Multi-Candidate Diagnostic Comparison Matrix
                        </h4>
                      </div>
                      <button
                        onClick={() => setShowComparisonMatrix(false)}
                        className="text-xs text-purple-200 hover:text-white underline font-semibold"
                      >
                        Close Table
                      </button>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-xs text-left">
                        <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 uppercase tracking-wider text-[10px] font-black">
                          <tr>
                            <th className="p-3 w-1/4">Differential Entity</th>
                            <th className="p-3 w-1/4">Cardinal Hallmarks</th>
                            <th className="p-3 w-1/4">Gold-Standard Test</th>
                            <th className="p-3 w-1/4">First-Line Therapy</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {realtimeResult.comparison_matrix.map((row, ri) => (
                            <tr key={ri} className="hover:bg-indigo-50/30 transition-colors">
                              <td className="p-3 align-top">
                                <div className="font-extrabold text-slate-900 text-sm">{row.disease}</div>
                                <div className="flex items-center gap-1.5 mt-0.5">
                                  <span className="text-[10px] font-black px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                                    {row.display_score}
                                  </span>
                                  {row.icd10 && (
                                    <span className="text-[10px] text-slate-500 font-mono">ICD-10: {row.icd10}</span>
                                  )}
                                </div>
                              </td>
                              <td className="p-3 align-top">
                                <ul className="space-y-0.5">
                                  {row.cardinal_features.map((feat, fi) => (
                                    <li key={fi} className="text-slate-700 font-medium flex items-start gap-1">
                                      <span className="text-indigo-500 font-bold">•</span>
                                      <span>{feat}</span>
                                    </li>
                                  ))}
                                </ul>
                              </td>
                              <td className="p-3 align-top text-slate-800 font-semibold bg-purple-50/20">
                                <div className="flex items-start gap-1">
                                  <FlaskConical className="w-3.5 h-3.5 text-purple-600 flex-shrink-0 mt-0.5" />
                                  <span>{row.confirmatory_test}</span>
                                </div>
                              </td>
                              <td className="p-3 align-top text-slate-800 font-medium bg-emerald-50/20">
                                <div className="flex items-start gap-1">
                                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0 mt-0.5" />
                                  <span>{row.first_line_therapy}</span>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Discriminative "Next Best Test" Recommendation Card */}
              {realtimeResult.differentiating_recommendation && (
                <motion.div
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-5 rounded-2xl bg-gradient-to-r from-purple-950 via-indigo-950 to-slate-950 text-white shadow-xl border border-purple-500/40 text-left"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2.5 border-b border-white/10">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-xl bg-purple-500/20 border border-purple-400/40 flex items-center justify-center">
                        <Target className="w-4 h-4 text-purple-300" />
                      </div>
                      <div>
                        <h4 className="text-xs font-black uppercase tracking-wider text-purple-200 flex items-center gap-2">
                          Discriminative "Next Best Test" (Maximum Information Gain)
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-black uppercase tracking-wider border ${
                            realtimeResult.differentiating_recommendation.urgency === 'IMMEDIATE'
                              ? 'bg-rose-500/30 text-rose-200 border-rose-400/40 animate-pulse'
                              : 'bg-amber-500/30 text-amber-200 border-amber-400/40'
                          }`}>
                            ⚡ {realtimeResult.differentiating_recommendation.urgency}
                          </span>
                        </h4>
                        <p className="text-[11px] text-purple-100/80 font-medium">
                          Single decisive investigation to separate #{1} <strong>{realtimeResult.differentiating_recommendation.candidate_1}</strong> from #{2} <strong>{realtimeResult.differentiating_recommendation.candidate_2}</strong>
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-white/10 border border-purple-400/30">
                    <div className="text-xs font-black text-white flex items-center gap-2 mb-1">
                      <FlaskConical className="w-4 h-4 text-purple-300 flex-shrink-0" />
                      <span className="text-sm text-purple-100 font-extrabold">
                        {realtimeResult.differentiating_recommendation.differentiating_investigation}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 font-medium pl-6 leading-relaxed">
                      {realtimeResult.differentiating_recommendation.clinical_rationale}
                    </p>
                  </div>
                </motion.div>
              )}

              {/* Bedside Diagnostic Clarification Prompter */}
              {realtimeResult?.bedside_clarifying_questions && realtimeResult.bedside_clarifying_questions.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-5 rounded-2xl bg-gradient-to-r from-teal-950 via-slate-900 to-indigo-950 text-white shadow-xl border border-teal-500/40 text-left"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2.5 border-b border-white/10">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-xl bg-teal-500/20 border border-teal-400/40 flex items-center justify-center">
                        <HelpCircle className="w-4 h-4 text-teal-300" />
                      </div>
                      <div>
                        <h4 className="text-xs font-black uppercase tracking-wider text-teal-200 flex items-center gap-2">
                          Bedside Clarifying Examination Prompter ($0 Cost, 30-Second Rule-In/Out)
                          <span className="text-[10px] bg-teal-500/30 text-teal-200 border border-teal-400/30 px-2 py-0.5 rounded-full font-bold">
                            Interactive Socratic Aid
                          </span>
                        </h4>
                        <p className="text-[11px] text-teal-100/80 font-medium">
                          Targeted bedside exam maneuvers and questions to decisively separate top competing diagnoses. Click to update differential:
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    {realtimeResult.bedside_clarifying_questions.map((q, qi) => (
                      <div
                        key={qi}
                        className="p-3.5 rounded-xl bg-white/5 border border-teal-500/20 flex flex-col md:flex-row items-start md:items-center justify-between gap-3"
                      >
                        <div className="flex-grow">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-md bg-teal-900/60 text-teal-200 border border-teal-500/30">
                              {q.maneuver}
                            </span>
                            <span className="text-[10px] font-semibold text-slate-400">
                              Separates: <strong>{q.differentiates}</strong>
                            </span>
                          </div>
                          <p className="text-xs font-semibold text-white leading-relaxed">
                            {q.question}
                          </p>
                        </div>

                        <div className="flex items-center gap-2 flex-shrink-0">
                          <button
                            type="button"
                            onClick={() => handleBedsideAnswer(q.positive_token)}
                            className="px-3 py-1.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm transition-all hover:scale-105 active:scale-95 flex items-center gap-1"
                          >
                            <Check className="w-3.5 h-3.5" />
                            <span>{q.positive_label}</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => handleBedsideAnswer(q.negative_token)}
                            className="px-3 py-1.5 rounded-xl text-xs font-bold bg-rose-950/80 hover:bg-rose-900 text-rose-200 border border-rose-500/40 shadow-sm transition-all hover:scale-105 active:scale-95 flex items-center gap-1"
                          >
                            <span>{q.negative_label}</span>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {realtimeResult.top_candidates.map((cand, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.04 }}
                    className={`p-5 rounded-2xl border transition-all text-left bg-white/95 shadow-sm hover:shadow-md ${
                      idx === 0
                        ? 'border-indigo-300 ring-2 ring-indigo-100 bg-gradient-to-br from-indigo-50/40 via-white to-white'
                        : 'border-slate-200/80 hover:border-indigo-200'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3 mb-2.5">
                      <div className="flex items-center gap-2.5">
                        <span className={`w-7 h-7 rounded-xl flex items-center justify-center font-black text-xs ${
                          idx === 0 ? 'bg-indigo-600 text-white shadow-sm' : 'bg-slate-100 text-slate-700'
                        }`}>
                          #{idx + 1}
                        </span>
                        <div>
                          <h5 className="font-black text-slate-900 text-base leading-snug">
                            {cand.disease}
                          </h5>
                          <div className="flex items-center gap-2 mt-0.5">
                            {cand.icd10 && (
                              <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded border border-slate-200">
                                ICD-10: {cand.icd10}
                              </span>
                            )}
                            {cand.icd11 && (
                              <span className="text-[10px] font-bold bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded border border-blue-200">
                                ICD-11: {cand.icd11}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Triage & Probability Badge */}
                      <div className="flex flex-col items-end gap-1 flex-shrink-0">
                        <span className={`text-base font-black px-2.5 py-0.5 rounded-lg shadow-sm ${
                          idx === 0 
                            ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white' 
                            : 'bg-slate-800 text-white'
                        }`}>
                          {cand.display_score}
                        </span>
                        <span className={`text-[9px] font-extrabold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                          cand.triage === 'EMERGENT'
                            ? 'bg-red-100 text-red-700 border border-red-200'
                            : cand.triage === 'URGENT'
                            ? 'bg-amber-100 text-amber-800 border border-amber-200'
                            : 'bg-blue-50 text-blue-700 border border-blue-200'
                        }`}>
                          {cand.triage}
                        </span>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden mb-3 border border-slate-200/50">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          idx === 0
                            ? 'bg-gradient-to-r from-indigo-500 to-emerald-500'
                            : 'bg-gradient-to-r from-indigo-400 to-purple-400'
                        }`}
                        style={{ width: `${Math.min(Math.round(cand.score * 100), 100)}%` }}
                      />
                    </div>

                    {/* Hallmark Tag if matched */}
                    {cand.is_hallmark_match && (
                      <div className="mb-2.5 flex items-center gap-1.5 text-[11px] font-extrabold text-indigo-800 bg-indigo-50 px-2.5 py-1 rounded-xl border border-indigo-200">
                        <Sparkles className="w-3.5 h-3.5 text-indigo-600 flex-shrink-0" />
                        <span>Pathognomonic hallmark matches present</span>
                      </div>
                    )}

                    {/* Supporting Findings */}
                    {cand.supporting_findings.length > 0 && (
                      <div className="mb-2.5 text-left">
                        <span className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider block mb-1">
                          Matched Findings:
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {cand.supporting_findings.map((finding, fi) => (
                            <span key={fi} className="text-[11px] font-semibold bg-slate-50 text-slate-700 px-2 py-0.5 rounded-md border border-slate-200">
                              ✓ {finding}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Immediate Tests */}
                    {cand.immediate_tests.length > 0 && (
                      <div className="text-left bg-slate-50/80 p-2.5 rounded-xl border border-slate-200/60 mt-2">
                        <span className="text-[10px] font-extrabold text-indigo-700 uppercase tracking-wider flex items-center gap-1 mb-1">
                          <FlaskConical className="w-3 h-3 text-indigo-600" /> Priority Bedside / Confirmatory Tests:
                        </span>
                        <ul className="text-[11px] font-medium text-slate-600 space-y-0.5 list-disc pl-4">
                          {cand.immediate_tests.slice(0, 3).map((test, ti) => (
                            <li key={ti}>{test}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Pharmacotherapy / Recommended Medications */}
                    {((cand.recommended_medications && cand.recommended_medications.length > 0) || cand.treatment_summary) && (
                      <div className="text-left bg-emerald-50/70 p-2.5 rounded-xl border border-emerald-200/60 mt-2">
                        <span className="text-[10px] font-extrabold text-emerald-800 uppercase tracking-wider flex items-center gap-1 mb-1">
                          <Pill className="w-3 h-3 text-emerald-600" /> First-Line Pharmacotherapy / Rx:
                        </span>
                        {cand.treatment_summary && (
                          <div className="text-[11px] font-bold text-emerald-950 mb-1">
                            {cand.treatment_summary}
                          </div>
                        )}
                        {cand.recommended_medications && cand.recommended_medications.length > 0 && (
                          <ul className="text-[11px] font-medium text-emerald-900 space-y-0.5 list-disc pl-4">
                            {cand.recommended_medications.slice(0, 3).map((med, mi) => (
                              <li key={mi}>{med}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    )}

                    {/* Clinical Pearl */}
                    {cand.pearl && (
                      <p className="text-[11px] text-slate-500 italic mt-2.5 border-t border-slate-100 pt-2 text-left">
                        💡 {cand.pearl}
                      </p>
                    )}

                    {/* Quick Action Toolbar for Real-Time Candidate */}
                    <div className="flex flex-wrap items-center gap-2 mt-3 pt-2.5 border-t border-slate-100">
                      <button
                        type="button"
                        onClick={() => {
                          setRealtimePanelFor(prev => 
                            prev?.disease === cand.disease && prev?.tab === "investigations" 
                              ? null 
                              : { disease: cand.disease, tab: "investigations" }
                          );
                        }}
                        className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm ${
                          realtimePanelFor?.disease === cand.disease && realtimePanelFor?.tab === "investigations"
                            ? "bg-indigo-600 text-white shadow-indigo-200"
                            : "bg-indigo-50/80 text-indigo-700 hover:bg-indigo-100/80 border border-indigo-200/60"
                        }`}
                      >
                        <FlaskConical className="w-3.5 h-3.5" />
                        <span>View Investigations</span>
                        {realtimePanelFor?.disease === cand.disease && realtimePanelFor?.tab === "investigations" ? (
                          <ChevronUp className="w-3 h-3" />
                        ) : (
                          <ChevronDown className="w-3 h-3" />
                        )}
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setRealtimePanelFor(prev => 
                            prev?.disease === cand.disease && prev?.tab === "medications" 
                              ? null 
                              : { disease: cand.disease, tab: "medications" }
                          );
                        }}
                        className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm ${
                          realtimePanelFor?.disease === cand.disease && realtimePanelFor?.tab === "medications"
                            ? "bg-emerald-600 text-white shadow-emerald-200"
                            : "bg-emerald-50/80 text-emerald-700 hover:bg-emerald-100/80 border border-emerald-200/60"
                        }`}
                      >
                        <ShieldCheck className="w-3.5 h-3.5" />
                        <span>View Safe Medications</span>
                        {realtimePanelFor?.disease === cand.disease && realtimePanelFor?.tab === "medications" ? (
                          <ChevronUp className="w-3 h-3" />
                        ) : (
                          <ChevronDown className="w-3 h-3" />
                        )}
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setRealtimePanelFor(prev => 
                            prev?.disease === cand.disease && prev?.tab === "intelligence" 
                              ? null 
                              : { disease: cand.disease, tab: "intelligence" }
                          );
                        }}
                        className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm ${
                          realtimePanelFor?.disease === cand.disease && realtimePanelFor?.tab === "intelligence"
                            ? "bg-purple-600 text-white shadow-purple-200"
                            : "bg-purple-50/80 text-purple-700 hover:bg-purple-100/80 border border-purple-200/60"
                        }`}
                      >
                        <Globe className="w-3.5 h-3.5" />
                        <span>Disease Intelligence</span>
                        {realtimePanelFor?.disease === cand.disease && realtimePanelFor?.tab === "intelligence" ? (
                          <ChevronUp className="w-3 h-3" />
                        ) : (
                          <ChevronDown className="w-3 h-3" />
                        )}
                      </button>
                    </div>

                    {/* Inline Expandable Panel for this Real-time Candidate */}
                    <AnimatePresence>
                      {realtimePanelFor?.disease === cand.disease && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                          className="mt-3 overflow-hidden"
                        >
                          <div className="p-4 rounded-xl bg-slate-50/90 border border-slate-200 text-left">
                            {realtimePanelFor.tab === "investigations" && (
                              <InvestigationPanel
                                consultationId={consultationId}
                                disease={cand.disease}
                                competing={realtimeResult.top_candidates
                                  .filter(c => c.disease !== cand.disease)
                                  .map(c => c.disease)}
                              />
                            )}
                            {realtimePanelFor.tab === "medications" && (
                              <MedicationPanel
                                consultationId={consultationId}
                                disease={cand.disease}
                              />
                            )}
                            {realtimePanelFor.tab === "intelligence" && (
                              <div className="space-y-4">
                                <DiseaseIntelligencePanel disease={cand.disease} consultationId={consultationId} />
                                <ControversyScanner consultationId={consultationId} disease={cand.disease} />
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Action Row */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <button
              onClick={() => runAnalysis()}
              disabled={loading}
              className="flex items-center gap-2 px-8 py-3.5 rounded-2xl text-sm font-bold text-white transition-all hover:scale-105 active:scale-95 disabled:opacity-60 bg-gradient-to-r from-indigo-600 via-indigo-700 to-purple-600 shadow-[0_4px_18px_rgba(79,70,229,0.35),inset_0_1px_0_rgba(255,255,255,0.3)] hover:shadow-[0_6px_24px_rgba(79,70,229,0.45)]"
            >
              <Bot className="w-4 h-4" />
              {error ? "Retry Deep AI Analysis" : "Run Deep Multi-Source Literature Synthesis"}
            </button>
          </div>

          <p className="text-[11px] font-medium text-slate-400">
            Real-time differential computed locally in &lt;10ms. Deep analysis enriches with PubMed, MedlinePlus &amp; clinical guidelines.
          </p>
        </div>
      </motion.div>

      {/* ── Loading State for Deep Literature Synthesis ── */}
      {loading && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 rounded-3xl border border-indigo-100/80 bg-gradient-to-br from-blue-50/90 via-white/95 to-indigo-50/90 p-8 flex flex-col items-center justify-center gap-5 shadow-[0_8px_32px_rgba(99,102,241,0.08),inset_0_1px_0_rgba(255,255,255,0.9)] backdrop-blur-2xl relative overflow-hidden"
        >
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 animate-pulse" />
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-md shadow-blue-500/20 ring-4 ring-blue-100">
              <Bot className="w-5 h-5 text-white animate-pulse" />
            </div>
            <span className="font-extrabold text-slate-800 text-base tracking-tight">AI Differential Diagnosis</span>
          </div>
          <div className="flex items-center gap-3 text-sm font-semibold text-slate-600 bg-white/80 px-4 py-2 rounded-full border border-slate-200/60 shadow-sm">
            <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
            Analyzing clinical findings and generating differential diagnosis…
          </div>
          <div className="flex gap-2">
            {[0, 1, 2, 3].map(i => (
              <div key={i} className="w-2.5 h-2.5 rounded-full bg-gradient-to-tr from-blue-500 to-indigo-600 animate-bounce shadow-sm" style={{ animationDelay: `${i * 0.15}s` }} />
            ))}
          </div>
        </motion.div>
      )}

      {/* ── Deep Literature Synthesis: Insufficient Information ── */}
      {!loading && data && data.status === "INSUFFICIENT_INFO" && (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel overflow-hidden mb-6 rounded-2xl border border-[var(--border-default)]"
        >
          <div className="bg-[var(--color-primary-50)] px-4 py-3 border-b border-[var(--color-primary-200)] flex items-center gap-2">
            <Bot className="w-5 h-5 text-[var(--color-primary-600)]" />
            <h3 className="font-semibold text-[var(--color-primary-900)] text-sm tracking-wide">AI DIFFERENTIAL SUGGESTION</h3>
          </div>
          <div className="p-8 flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 bg-[var(--surface-sunken)] rounded-full flex items-center justify-center mb-4 shadow-inner text-2xl">
              🤷
            </div>
            <h4 className="text-lg font-bold text-[var(--text-primary)] mb-2">Insufficient Information</h4>
            <p className="text-sm text-[var(--text-secondary)] max-w-sm mb-6">
              {data.message || "Not enough clinical information provided to generate a safe differential diagnosis."}
            </p>
            {data.missing_critical_info && data.missing_critical_info.length > 0 && (
              <div className="text-left bg-[var(--color-warning-50)] text-[var(--color-warning-800)] p-4 rounded-xl border border-[var(--color-warning-200)] text-xs w-full max-w-sm shadow-sm">
                <strong className="block mb-2 flex items-center gap-1 font-bold"><AlertTriangle className="w-3 h-3"/> Missing Requirements:</strong>
                <ul className="list-disc pl-4 space-y-1 font-medium">
                  {data.missing_critical_info.map((info, i) => (
                    <li key={i}>{info}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* ── Deep Literature Synthesis: No Candidates ── */}
      {!loading && data && data.status !== "INSUFFICIENT_INFO" && data.top_candidates.length === 0 && (
        <div className="glass-panel mb-8 p-8 flex flex-col items-center justify-center text-center rounded-2xl border border-[var(--border-default)]">
          <div className="w-16 h-16 bg-[var(--surface-sunken)] rounded-full flex items-center justify-center mb-4 shadow-inner text-2xl">
            🔍
          </div>
          <h4 className="text-lg font-bold text-[var(--text-primary)] mb-2">No Candidates Identified</h4>
          <p className="text-sm text-[var(--text-secondary)] max-w-sm">
            The AI was unable to confidently identify differential diagnosis candidates based on the current clinical findings.
          </p>
        </div>
      )}

      {/* ── Deep Literature Differential Candidates ── */}
      {!loading && data && data.status !== "INSUFFICIENT_INFO" && data.top_candidates.length > 0 && (
        <>
          <EarlyWarningBanner consultationId={consultationId} trigger={trigger} />
          <EpiRadarAlert consultationId={consultationId} trigger={trigger} />
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8 overflow-hidden rounded-3xl shadow-[0_12px_44px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.95)] border border-white/80 bg-white/70 backdrop-blur-3xl relative"
          >
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-80" />
          
          <div className="bg-gradient-to-r from-blue-50/90 via-indigo-50/40 to-transparent px-6 py-5 border-b border-slate-200/50 flex justify-between items-center">
            <div className="flex items-center gap-3.5">
              <div className="p-2.5 bg-white rounded-2xl shadow-sm border border-blue-100/70 ring-2 ring-blue-50">
                <Bot className="w-5 h-5 text-blue-600" />
              </div>
              <h3 className="font-black text-slate-800 text-base tracking-tight">AI DIFFERENTIAL SUGGESTION</h3>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => runAnalysis()}
                className="text-xs text-blue-700 bg-white/90 hover:bg-white px-3.5 py-1.5 rounded-full font-bold shadow-sm border border-blue-200/70 hover:shadow hover:scale-105 active:scale-95 transition-all flex items-center gap-1.5"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
                Re-run
              </button>
              <span className="text-xs text-blue-800 bg-blue-50/80 px-3.5 py-1.5 rounded-full font-extrabold shadow-sm border border-blue-200/60 backdrop-blur-md">
                Top {data.top_candidates.length} Candidates
              </span>
            </div>
          </div>

      <div className="px-5 py-3 bg-[var(--clinical-warning-bg)] text-[var(--clinical-warning-text)] text-[11px] border-b border-[var(--clinical-warning-border)] flex justify-between items-start gap-3 backdrop-blur-sm">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
          <p className="font-medium leading-relaxed">This ranking is a decision-support algorithmic suggestion grounded in FDA data. Independent clinician review is strictly required.</p>
        </div>
        <div className="shrink-0 pt-0.5 pr-2">
           <FeedbackButtons 
             suggestionId={`diff-${data.consultation_id}`} 
             suggestionType="diagnosis" 
             suggestionContext={data} 
           />
        </div>
      </div>

      {/* AI Synthesis Summary - Enterprise Style */}
      <div className="px-6 py-6 mb-4 flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-slate-200/40 bg-gradient-to-r from-white/40 via-white/20 to-transparent">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 mb-3 rounded-full bg-blue-50/90 border border-blue-200/50 shadow-sm">
            <Bot className="w-3.5 h-3.5 text-blue-600" />
            <span className="text-[10px] font-black text-blue-700 uppercase tracking-widest">AI Intelligence Synthesis</span>
          </div>
          <h3 className="text-2xl md:text-3xl font-black tracking-tight text-slate-900 mb-2">Clinical Synthesis</h3>
          <p className="text-sm text-slate-600 max-w-3xl leading-relaxed font-medium">
            Based on the clinical representation, the AI identifies <strong className="text-slate-900 font-bold underline decoration-blue-400 decoration-2 underline-offset-2">{data.top_candidates[0].disease}</strong> as the primary differential. 
            {data.top_candidates.length > 1 ? ` Several other etiologies, including ${data.top_candidates[1].disease}, must also be ruled out.` : ` Clinical correlation is required.`}
          </p>
        </div>
      </div>

      <div className="space-y-4 px-6 pb-8">
        <AnimatePresence>
        {data.top_candidates.map((candidate, idx) => {
          const scorePercent = Math.round(candidate.score * 100);
          const circumference = 2 * Math.PI * 20;
          const strokeDashoffset = circumference - (scorePercent / 100) * circumference;

          return (
          <motion.div 
            key={idx}
            draggable={true}
            onDragStart={(e) => {
              const de = (e as unknown as DragEvent);
              if (de.dataTransfer) {
                de.dataTransfer.setData("text/plain", `Assessment: ${candidate.disease} (AI Confidence: ${scorePercent}%)\nSupporting: ${candidate.supporting_findings?.join(", ")}`);
              }
            }}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.08, duration: 0.4, ease: "easeOut" }}
            className="group bg-white/80 backdrop-blur-2xl rounded-2xl border border-slate-200/80 hover:border-indigo-300 shadow-[0_2px_12px_rgba(0,0,0,0.03),inset_0_1px_0_rgba(255,255,255,0.9)] hover:shadow-[0_12px_36px_rgba(79,70,229,0.12)] transition-all duration-300 overflow-hidden relative cursor-grab active:cursor-grabbing"
          >
            {/* Clickable Header Area */}
            <div 
              className="p-5 md:p-6 flex items-center justify-between cursor-pointer relative z-10"
              onClick={() => setExpandedIndex(expandedIndex === idx ? null : idx)}
            >
              <div className="flex items-center gap-5 w-full">
                <div className="text-slate-300 hover:text-slate-500 cursor-grab px-1 -ml-2 transition-colors" title="Drag to Clinical Note">
                  <span className="text-xl leading-none font-bold">⠿</span>
                </div>
                
                {/* SVG Circular Progress with Gradient Glow */}
                <div className="relative w-14 h-14 flex-shrink-0 flex items-center justify-center filter drop-shadow-sm">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 48 48">
                    <defs>
                      <linearGradient id={`candidateDial-${idx}`} x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor={idx === 0 ? "#0284c7" : "#6366f1"} />
                        <stop offset="100%" stopColor={idx === 0 ? "#059669" : "#a855f7"} />
                      </linearGradient>
                    </defs>
                    <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="4.5" fill="transparent" className="text-slate-100" />
                    <motion.circle 
                      initial={{ strokeDashoffset: circumference }}
                      animate={{ strokeDashoffset }}
                      transition={{ duration: 1.5, ease: "easeOut", delay: 0.2 }}
                      cx="24" cy="24" r="20" 
                      stroke={`url(#candidateDial-${idx})`}
                      strokeWidth="4.5" 
                      fill="transparent" 
                      strokeLinecap="round"
                      strokeDasharray={circumference}
                    />
                  </svg>
                  <span className={`absolute text-sm font-black ${idx === 0 ? 'text-slate-900' : 'text-slate-700'}`}>
                    {scorePercent}%
                  </span>
                </div>
                
                <div className="flex-grow">
                  <div className="flex items-center gap-3 mb-1">
                    <h4 className={`text-xl font-extrabold tracking-tight transition-colors ${idx === 0 ? 'text-indigo-950' : 'text-slate-800'}`}>
                      {candidate.disease}
                    </h4>
                    {idx === 0 && (
                      <span className="px-2.5 py-0.5 text-[9px] font-black uppercase tracking-widest bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-full shadow-sm">
                        Primary
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-2.5 text-xs font-semibold flex-wrap">
                    <span className="text-slate-400 uppercase tracking-wider text-[11px]">
                      {candidate.uncertainty} Uncertainty
                    </span>
                    
                    {candidate.geographic_match && (
                      <>
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
                        <span className="inline-flex items-center gap-1 font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 text-[10px] tracking-wide shadow-sm" title="Prioritized due to travel history or endemic geographic exposure">
                          <Globe className="w-3 h-3 text-emerald-600" /> Endemic Link
                        </span>
                      </>
                    )}

                    {candidate.incubation_fit && (
                      <>
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
                        <span className={`inline-flex items-center gap-1 font-bold px-2 py-0.5 rounded-full border text-[10px] tracking-wide shadow-sm ${
                          candidate.incubation_fit === 'FITS' 
                            ? 'text-indigo-700 bg-indigo-50 border-indigo-200' 
                            : 'text-amber-700 bg-amber-50 border-amber-200'
                        }`} title={`Symptom onset timeline matches disease incubation window (${candidate.incubation_fit})`}>
                          <Clock className="w-3 h-3" /> Incubation {candidate.incubation_fit}
                        </span>
                      </>
                    )}

                    {candidate.safety_decision && candidate.safety_decision.decision !== "ALLOW" && (
                      <>
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
                        <span className={`flex items-center gap-1.5 font-bold ${
                          candidate.safety_decision.decision === 'ABSTAIN' ? 'text-red-600 bg-red-50 px-2 py-0.5 rounded-full border border-red-200' : 'text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200'
                        }`}>
                          <ShieldAlert className="w-3.5 h-3.5"/> {candidate.safety_decision.decision === 'ABSTAIN' ? 'UNSAFE' : 'WARNING'}
                        </span>
                      </>
                    )}
                  </div>

                  {((candidate.immediate_tests && candidate.immediate_tests.length > 0) || (candidate.recommended_medications && candidate.recommended_medications.length > 0) || candidate.first_line_treatment) && (
                    <div className="w-full mt-2.5 flex flex-wrap items-center gap-2">
                      {candidate.immediate_tests && candidate.immediate_tests.length > 0 && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold bg-purple-50 text-purple-700 px-2.5 py-0.5 rounded-lg border border-purple-200 shadow-xs">
                          <FlaskConical className="w-3 h-3 text-purple-600" />
                          <span>Stat Tests: <strong>{candidate.immediate_tests.slice(0, 2).join(", ")}</strong></span>
                        </span>
                      )}
                      {(candidate.first_line_treatment || (candidate.recommended_medications && candidate.recommended_medications.length > 0)) && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold bg-emerald-50 text-emerald-800 px-2.5 py-0.5 rounded-lg border border-emerald-200 shadow-xs">
                          <ShieldCheck className="w-3 h-3 text-emerald-600" />
                          <span>First-Line Rx: <strong>{candidate.first_line_treatment || candidate.recommended_medications?.[0]}</strong></span>
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
              
              <div className="text-slate-400 flex-shrink-0 w-9 h-9 flex items-center justify-center rounded-full group-hover:bg-slate-100/80 transition-colors border border-transparent group-hover:border-slate-200">
                {expandedIndex === idx ? <ChevronUp className="w-5 h-5"/> : <ChevronDown className="w-5 h-5"/>}
              </div>
            </div>

            {/* Expandable Content Area */}
            <AnimatePresence>
            {expandedIndex === idx && (
              <motion.div 
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden border-t border-[var(--border-subtle)] bg-[var(--surface-sunken)]"
              >
                <div className="p-6 md:p-8">
                  
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Left Column: Rationale */}
                    <div className="lg:col-span-2 space-y-6">
                      <div>
                        <h5 className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-widest mb-3">
                           Clinical Rationale
                        </h5>
                        <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{candidate.explanation_reference}</p>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Supporting Findings */}
                        <div>
                          <h5 className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-widest mb-3">
                             Supporting Findings
                          </h5>
                          {candidate.supporting_findings.length > 0 ? (
                            <ul className="space-y-2">
                              {candidate.supporting_findings.map((f, i) => (
                                <li key={i} className="flex items-start gap-2 text-[var(--text-primary)] text-sm font-medium">
                                  <span className="text-[var(--color-primary-500)] mt-0.5 opacity-80">•</span> {f}
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <span className="text-[var(--text-tertiary)] text-sm italic">None documented</span>
                          )}
                        </div>

                        {/* Missing/Contradicting */}
                        <div>
                          <h5 className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-widest mb-3">
                             Contradicting / Missing
                          </h5>
                          {(candidate.missing_expected_findings.length > 0 || candidate.contradicting_information.length > 0) ? (
                            <ul className="space-y-2">
                              {candidate.missing_expected_findings.map((f, i) => (
                                <li key={`m-${i}`} className="flex items-start gap-2 text-[var(--text-secondary)] text-sm">
                                  <span className="text-[var(--text-tertiary)] mt-0.5 opacity-50">-</span> {f} <span className="text-[10px] text-[var(--text-tertiary)] uppercase tracking-widest ml-1 mt-0.5 opacity-60">Expected</span>
                                </li>
                              ))}
                              {candidate.contradicting_information.map((f, i) => (
                                <li key={`c-${i}`} className="flex items-start gap-2 text-[var(--text-primary)] text-sm">
                                  <span className="text-[var(--color-danger-500)] mt-0.5 font-bold">!</span> {f} <span className="text-[10px] text-[var(--color-danger-500)] uppercase tracking-widest ml-1 mt-0.5">Contradicts</span>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <span className="text-[var(--text-tertiary)] text-sm italic">None identified</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Right Column: Actions */}
                    <div className="flex flex-col gap-3">
                       <h5 className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-widest mb-1">
                         Action Plan
                       </h5>

                       {candidate.immediate_tests && candidate.immediate_tests.length > 0 && (
                         <div className="p-3 bg-purple-50/80 rounded-xl border border-purple-200/70 text-xs">
                           <div className="font-extrabold text-purple-900 mb-1 flex items-center gap-1">
                             <FlaskConical className="w-3.5 h-3.5 text-purple-600" />
                             <span>Immediate / Confirmatory Tests:</span>
                           </div>
                           <ul className="list-disc pl-4 space-y-0.5 text-purple-950 font-medium">
                             {candidate.immediate_tests.slice(0, 3).map((t, tidx) => (
                               <li key={tidx}>{t}</li>
                             ))}
                           </ul>
                         </div>
                       )}

                       {candidate.recommended_medications && candidate.recommended_medications.length > 0 && (
                         <div className="p-3 bg-emerald-50/80 rounded-xl border border-emerald-200/70 text-xs">
                           <div className="font-extrabold text-emerald-900 mb-1 flex items-center gap-1">
                             <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                             <span>Guideline Pharmacotherapy:</span>
                           </div>
                           <ul className="list-disc pl-4 space-y-0.5 text-emerald-950 font-medium">
                             {candidate.recommended_medications.slice(0, 3).map((m, midx) => (
                               <li key={midx}>{m}</li>
                             ))}
                           </ul>
                         </div>
                       )}
                       <Button 
                         variant={showInvestigationsFor === candidate.disease ? "primary" : "outline"}
                         onClick={(e) => {
                             e.stopPropagation();
                             setShowInvestigationsFor(showInvestigationsFor === candidate.disease ? null : candidate.disease);
                             setShowMedicationsFor(null);
                         }}
                         className="w-full justify-start rounded-xl font-medium shadow-sm h-11"
                       >
                         {showInvestigationsFor === candidate.disease ? 'Hide' : 'View'} Investigations
                       </Button>
                       <Button 
                         variant={showMedicationsFor === candidate.disease ? "primary" : "outline"}
                         onClick={(e) => {
                             e.stopPropagation();
                             setShowMedicationsFor(showMedicationsFor === candidate.disease ? null : candidate.disease);
                             setShowInvestigationsFor(null);
                         }}
                         className="w-full justify-start rounded-xl font-medium shadow-sm h-11"
                       >
                         {showMedicationsFor === candidate.disease ? 'Hide' : 'View'} Safe Medications
                       </Button>
                       <Button 
                         variant={showInvestigationsFor === `${candidate.disease}_intel` ? "primary" : "outline"}
                         onClick={(e) => {
                             e.stopPropagation();
                             setShowInvestigationsFor(showInvestigationsFor === `${candidate.disease}_intel` ? null : `${candidate.disease}_intel`);
                             setShowMedicationsFor(null);
                         }}
                         className="w-full justify-start rounded-xl font-medium shadow-sm h-11 border-[var(--color-primary-300)] text-[var(--color-primary-700)] bg-[var(--color-primary-50)] hover:bg-[var(--color-primary-100)]"
                       >
                         {showInvestigationsFor === `${candidate.disease}_intel` ? 'Hide' : 'View'} Disease Intelligence
                       </Button>
                    </div>
                  </div>
                  
                  {/* Collapsible Sub-panels */}
                  <AnimatePresence>
                  {showInvestigationsFor === candidate.disease && (
                    <motion.div initial={{opacity:0, height:0}} animate={{opacity:1, height:'auto'}} exit={{opacity:0, height:0}} className="pt-8 overflow-hidden">
                      <InvestigationPanel 
                        consultationId={consultationId} 
                        disease={candidate.disease} 
                        competing={data.top_candidates.filter(c => c.disease !== candidate.disease).map(c => c.disease)}
                      />
                    </motion.div>
                  )}
                  {showMedicationsFor === candidate.disease && (
                    <motion.div initial={{opacity:0, height:0}} animate={{opacity:1, height:'auto'}} exit={{opacity:0, height:0}} className="pt-8 overflow-hidden">
                      <MedicationPanel consultationId={consultationId} disease={candidate.disease} />
                    </motion.div>
                  )}
                  {showInvestigationsFor === `${candidate.disease}_intel` && (
                    <motion.div initial={{opacity:0, height:0}} animate={{opacity:1, height:'auto'}} exit={{opacity:0, height:0}} className="pt-8 overflow-hidden">
                      <DiseaseIntelligencePanel consultationId={consultationId} disease={candidate.disease} />
                      <ControversyScanner consultationId={consultationId} disease={candidate.disease} />
                    </motion.div>
                  )}
                  </AnimatePresence>
                </div>
              </motion.div>
            )}
            </AnimatePresence>
          </motion.div>
          );
        })}
        </AnimatePresence>
      </div>
      
      <div className="bg-[var(--surface-sunken)] p-2 border-t border-[var(--border-default)] text-right rounded-b-2xl">
        <span className="text-[10px] text-[var(--text-tertiary)] font-mono">Provider: {data.provider_metadata.provider} v{data.provider_metadata.version}</span>
      </div>
    </motion.div>
    </>
  )}
  </>
  );
}
