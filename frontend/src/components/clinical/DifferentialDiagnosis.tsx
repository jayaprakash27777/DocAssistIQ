/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable react/no-unescaped-entities */
"use client";

import React, { useState, useEffect, useCallback } from "react";
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
  Target, FlaskConical, Scale, FileText, Copy, Check, Table, HelpCircle, FileCheck, Pill,
  Layers, Search, Brain, Lightbulb, Maximize2, Minimize2, X
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

interface ClinicalPreset {
  label: string;
  category: "emergency" | "complex" | "bedside" | "outbreak";
  query: string;
}

const CLINICAL_PRESETS: ClinicalPreset[] = [
  {
    category: "outbreak",
    label: "Kerala Nipah Encephalitis Outbreak (IDSP/NCDC)",
    query: "32yo male from Kozhikode Kerala presenting with high remittent fever, altered mental status, segmental myoclonus, disorientation, and progressive acute respiratory distress after consuming fresh date palm sap."
  },
  {
    category: "outbreak",
    label: "Gujarat Chandipura Pediatric Encephalitis (IDSP)",
    query: "5yo female from Sabarkantha Gujarat presenting with sudden onset high fever, recurrent generalized tonic-clonic seizures, altered sensorium, vomiting, and rapid neurological decline during monsoon season."
  },
  {
    category: "outbreak",
    label: "Karnataka Kyasanur Forest Disease / KFD (NCDC)",
    query: "42yo male farmer from Shivamogga Karnataka presenting with sudden onset high fever, severe frontal headache, intense prostration, conjunctival suffusion, generalized myalgia, and bleeding from oral mucosa following tick exposure in forest area."
  },
  {
    category: "outbreak",
    label: "Himachal Pradesh Scrub Typhus Surge (IDSP)",
    query: "28yo female from Kangra Himachal Pradesh presenting with high continuous fever, severe headache, prominent black necrotic eschar with erythematous rim on groin, regional lymphadenopathy, and maculopapular rash."
  },
  {
    category: "outbreak",
    label: "Assam Japanese Encephalitis Surge (AES)",
    query: "36yo male farmer from Dibrugarh Assam presenting with high fever, acute encephalopathy, altered sensorium, parkinsonian mask-like facies, tremors, and neck stiffness."
  },
  {
    category: "outbreak",
    label: "Rwanda Marburg Virus Disease (WHO/CDC Alert)",
    query: "39yo male healthcare worker returning 5 days ago from Kigali Rwanda presenting with high remittent fever 40.2C, severe retro-orbital headache, watery diarrhea, spontaneous venipuncture site bleeding, and purpuric rash."
  },
  {
    category: "complex",
    label: "Modified Duke Endocarditis Note",
    query: "48yo male with history of bicuspid aortic valve presenting with 3 weeks of intermittent fevers (Tmax 38.8C), night sweats, weight loss, and new pleuritic chest pain. On physical exam: BP 118/74, HR 98, new 3/6 holosystolic regurgitant murmur at apex, splinter hemorrhages beneath fingernails, and painless erythematous macules on palms (Janeway lesions). Labs: 2 separate blood cultures positive for Streptococcus viridans. Transthoracic echocardiogram demonstrates a 1.2 cm oscillating mobile vegetation on anterior mitral valve leaflet with severe mitral regurgitation. Denies IV drug use."
  },
  {
    category: "emergency",
    label: "Severe HAGMA / DKA Note",
    query: "24yo female with Type 1 Diabetes presenting with 2 days of severe nausea, persistent vomiting, diffuse abdominal pain, and rapid deep breathing. Exam: BP 102/68, HR 122, RR 32 (Kussmaul respirations), SpO2 99%, fruity odor on breath. Labs: Sodium 134 mEq/L, Potassium 5.4 mEq/L, Chloride 98 mEq/L, Bicarbonate 10 mEq/L, Glucose 480 mg/dL, BUN 38 mg/dL, Creatinine 1.4 mg/dL. Urinalysis reveals 4+ ketones and 4+ glucosuria. Denies fever or cough."
  },
  {
    category: "emergency",
    label: "Acute PE & Wells Note",
    query: "54yo female 10 days status-post total right hip arthroplasty presenting to the ED with sudden onset pleuritic right-sided chest pain, acute dyspnea, and hemoptysis. Exam: BP 112/76, HR 118, RR 28, SpO2 88% on room air. Right lower extremity is noticeably swollen, warm, and tender with right calf diameter 4.5 cm greater than left. 12-lead EKG shows sinus tachycardia with S1Q3T3 pattern. Denies fever, purulent sputum, or previous DVT history."
  },
  {
    category: "complex",
    label: "Dermatomyositis / Inflammatory Myopathy Note",
    query: "46yo female presenting with 2 months of progressive proximal muscle weakness in bilateral deltoids and quadriceps, difficulty climbing stairs and combing hair. Physical exam: violaceous heliotrope rash on upper eyelids with periorbital edema, erythematous scaly Gottron papules overlying MCP and PIP joints, and mechanic's hands with hyperkeratotic fissuring. Labs: serum CK 14,200 U/L, positive anti-Jo-1 antibodies, aldolase 42 U/L, ALT 98 U/L, AST 112 U/L. EMG shows myopathic motor unit potentials with membrane irritability. Denies dysphagia."
  },
  {
    category: "complex",
    label: "Acute Intermittent Porphyria Note",
    query: "29yo female presenting with severe diffuse colicky abdominal pain out of proportion to physical exam, nausea, and persistent vomiting following a 3-day water fast. Physical exam: BP 162/104, HR 116, abdomen is soft and non-distended without peritoneal signs, guarding, or rebound tenderness. Neurological exam reveals mild proximal upper-extremity motor weakness. Urinalysis demonstrates port-wine reddish-dark urine upon standing. Spot urine porphobilinogen (PBG) is markedly elevated at 48 mg/g creatinine. Denies fever, diarrhea, or previous abdominal surgeries."
  },
  {
    category: "emergency",
    label: "Bundibugyo VHF vs Malaria Note",
    query: "36yo male humanitarian field worker returning 6 days ago from rural community outbreak in Democratic Republic of Congo (DRC) presenting with high remittent fever 40.1°C, intense retro-orbital headache, diffuse myalgias, profound prostration, and conjunctival injection. On day 5 of illness developed spontaneous bleeding from venipuncture sites, melena, and petechial purpura on trunk. Exam: BP 88/54, HR 128, petechiae, ecchymoses, tender hepatomegaly. Labs: platelets 24,000/µL, AST 840 U/L, ALT 610 U/L. Denies recent mosquito net usage."
  },
  {
    category: "emergency",
    label: "Acute Stroke Note",
    query: "68yo male with PMH of HTN, HLD presenting with sudden onset right-sided hemiparesis and expressive aphasia starting 90 minutes ago. On exam: BP 178/102, HR 88, SpO2 98% RA. Right facial droop present. Pupils equal and reactive. Denies chest pain, shortness of breath, fever, or head trauma."
  },
  {
    category: "emergency",
    label: "Severe Preeclampsia Note",
    query: "31yo female G1P0 at 34 weeks gestation presenting with severe throbbing frontal headache and visual scotoma. Vitals: BP is 172/112 mmHg, HR 86, RR 18. Physical examination reveals 3+ bilateral lower extremity pitting edema, brisk deep tendon reflexes with 3 beats of unsustained clonus, and right upper quadrant abdominal tenderness. Urinalysis reveals 3+ proteinuria. Denies vaginal bleeding, leakage of fluid, or chest pain."
  },
  {
    category: "emergency",
    label: "STEMI EKG Note",
    query: "59yo male with 2-hour history of crushing retrosternal chest pressure radiating down left arm and into jaw, accompanied by profound diaphoresis and nausea. Vitals: BP 148/92, HR 104, SpO2 96%. 12-lead EKG shows marked ST-segment elevation in leads V1-V4. Denies cough, pleuritic pain, hemoptysis, or calf pain."
  },
  {
    category: "complex",
    label: "Acute Heart Failure Note",
    query: "72yo female with past medical history of CAD and ischemic cardiomyopathy presenting with progressive shortness of breath, severe orthopnea requiring 4 pillows to sleep, and paroxysmal nocturnal dyspnea. Exam: BP 168/98, HR 108, RR 26, SpO2 89% on room air. Auscultation reveals bilateral basilar crackles, elevated JVP at 8 cm above sternal angle, audible S3 gallop, and 2+ pretibial pitting edema. Denies fever, chills, purulent sputum, or calf tenderness."
  },
  {
    category: "complex",
    label: "SLE Lupus Flare",
    query: "27yo female presenting with 3-month history of fatigue, inflammatory polyarthritis of PIP and MCP joints with morning stiffness lasting >1 hour, and an erythematous photosensitive malar butterfly rash sparing the nasolabial folds. Laboratory evaluation demonstrates positive ANA at 1:640 titer, positive anti-dsDNA antibodies, and hypocomplementemia with low C3 and C4. Denies oral ulcers, alopecia, or lower extremity edema."
  },
  {
    category: "emergency",
    label: "Pulmonary Embolism (Wells Score)",
    query: "58yo female presenting with acute pleuritic chest pain and shortness of breath 12 days post right total knee arthroplasty with limited mobility. Exam: HR 114 bpm, RR 24, SpO2 91% RA. Right lower extremity demonstrates asymmetric calf swelling with 3 cm greater circumference than left and deep tenderness (signs of DVT)."
  },
  {
    category: "complex",
    label: "Infective Endocarditis (Duke Criteria)",
    query: "35yo male with history of IVDU presenting with 2 weeks of persistent daily fevers, drenching night sweats, and progressive fatigue. Exam: T 38.6°C, HR 98, new grade 3/6 holosystolic regurgitant murmur at apex, Janeway lesions on palms, subungual splinter hemorrhages. TTE shows 1.2 cm oscillating mobile mitral valve vegetation with regurgitation. Blood cultures x2 grow Enterococcus faecalis."
  },
  { category: "bedside", label: "Acute Appendicitis", query: "periumbilical pain migrating to right lower quadrant, nausea, vomiting, fever, McBurney point tenderness" },
  { category: "emergency", label: "Acute Myocardial Infarction", query: "central crushing chest pain, radiating to left arm, diaphoresis, shortness of breath, nausea" },
  { category: "emergency", label: "Aortic Dissection", query: "sudden severe tearing chest pain radiating to back between shoulder blades, bp discrepancy between arms" },
  { category: "bedside", label: "Gout (Acute Podagra)", query: "acute severe joint pain in great toe, podagra, first mtp redness and exquisite tenderness" },
  { category: "bedside", label: "Temporal Arteritis", query: "severe temporal headache, jaw claudication, scalp tenderness, blurred vision in 70yo" },
  { category: "bedside", label: "Kawasaki Disease", query: "high fever for 6 days, strawberry tongue, bilateral conjunctivitis, cracked red lips, swollen hands" },
  { category: "emergency", label: "Acute Epiglottitis", query: "severe sore throat, difficulty swallowing, drooling, tripod position, inspiratory stridor" },
  { category: "bedside", label: "Wilson Disease", query: "kayser-fleischer rings, copper accumulation, asterixis, jaundice, tremor" },
  { category: "emergency", label: "Anaphylaxis", query: "facial swelling, lip swelling, angioedema, hives, stridor, wheezing, hypotension after allergen" },
  { category: "emergency", label: "Tension Pneumothorax", query: "sudden sharp pleuritic chest pain, severe shortness of breath, tracheal deviation away from affected side, absent breath sounds" },
  { category: "bedside", label: "Lyme Disease (Erythema Migrans)", query: "expanding bullseye rash, erythema migrans, tick bite history, fever, fatigue" },
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

  // Big Screen Full Viewport Studio state
  const [isBigScreen, setIsBigScreen] = useState(false);

  // Keyboard shortcut to close Big Screen (Escape)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isBigScreen) {
        setIsBigScreen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isBigScreen]);

  // Preset filter state
  const [presetCategory, setPresetCategory] = useState<"all" | "emergency" | "complex" | "bedside" | "outbreak">("all");
  const [presetSearch, setPresetSearch] = useState("");
  const [showBenchmarks, setShowBenchmarks] = useState(false);
  const [activeDiagnosticTab, setActiveDiagnosticTab] = useState<"none" | "criteria" | "parser" | "biomarkers" | "questions">("none");

  const filteredPresets = React.useMemo(() => {
    return CLINICAL_PRESETS.filter(p => {
      const matchesCat = presetCategory === "all" || p.category === presetCategory;
      const matchesSearch = !presetSearch.trim() || 
        p.label.toLowerCase().includes(presetSearch.toLowerCase()) || 
        p.query.toLowerCase().includes(presetSearch.toLowerCase());
      return matchesCat && matchesSearch;
    });
  }, [presetCategory, presetSearch]);

  // Sub-30ms Real-Time Prediction state
  const [realtimeResult, setRealtimeResult] = useState<RealtimePredictionResponse | null>(null);
  const [isPredicting, setIsPredicting] = useState(false);

  // Instant real-time prediction trigger
  const triggerRealtimePredict = useCallback(async (queryText: string) => {
    if (!queryText.trim()) return;
    setIsPredicting(true);
    const res = await predictRealtime({
      symptoms: queryText,
      consultation_id: consultationId,
    });
    if (res.ok) {
      setRealtimeResult(res.data);
    }
    setIsPredicting(false);
  }, [consultationId]);

  const handleBedsideAnswer = (token: string) => {
    const updated = symptomInput.trim() ? `${symptomInput.trim()}, ${token}` : token;
    setSymptomInput(updated);
    triggerRealtimePredict(updated);
    toast.success(`Appended finding: "${token}"`, {
      icon: "⚡",
      duration: 2500,
    });
  };

  const handleSimulateLab = (labFinding: string) => {
    const updated = symptomInput.trim() ? `${symptomInput.trim()}, ${labFinding}` : labFinding;
    setSymptomInput(updated);
    triggerRealtimePredict(updated);
    toast.success(`Simulated pending lab finding: "${labFinding}"`, {
      duration: 2500,
    });
  };

  const handlePresetSelect = (queryText: string) => {
    setSymptomInput(queryText);
    triggerRealtimePredict(queryText);
  };

  const handleCopyMdm = () => {
    if (realtimeResult?.clinical_mdm_summary) {
      navigator.clipboard.writeText(realtimeResult.clinical_mdm_summary);
      setCopiedMdm(true);
      toast.success("EMR Assessment & Plan copied to clipboard!");
      setTimeout(() => setCopiedMdm(false), 3000);
    }
  };

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

  // Ultra-responsive 80ms live prediction whenever clinician types
  useEffect(() => {
    if (!symptomInput.trim()) {
      return;
    }
    const timer = setTimeout(() => {
      triggerRealtimePredict(symptomInput);
    }, 80);

    return () => clearTimeout(timer);
  }, [symptomInput, triggerRealtimePredict]);

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
    <div className={
      isBigScreen 
        ? "fixed inset-0 z-50 overflow-y-auto bg-slate-950/70 backdrop-blur-md p-3 sm:p-6 lg:p-8 flex justify-center items-start animate-in fade-in duration-200" 
        : "w-full"
    }>
      <div className={
        isBigScreen 
          ? "w-full max-w-[1780px] bg-white dark:bg-slate-900 rounded-3xl shadow-2xl border-2 border-indigo-400 dark:border-indigo-600 overflow-hidden flex flex-col p-4 sm:p-6 space-y-6 my-auto" 
          : "w-full"
      }>
        {/* Big Screen Dedicated Studio Bar (only in Big Screen mode) */}
        {isBigScreen && (
          <div className="sticky top-0 z-30 bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border-b border-slate-200 dark:border-slate-800 pb-3 mb-2 flex flex-wrap items-center justify-between gap-3 shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-indigo-600 text-white flex items-center justify-center shadow-md shadow-indigo-500/20 shrink-0">
                <Brain className="w-5 h-5 text-indigo-100" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base sm:text-lg font-black font-heading text-slate-900 dark:text-white">
                    Differential Diagnosis &amp; Clinical Decision Studio
                  </h2>
                  <span className="text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full bg-indigo-100 text-indigo-800 border border-indigo-200 dark:bg-indigo-950/60 dark:text-indigo-300">
                    🖥️ Big Screen Mode
                  </span>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                  Expansive high-resolution clinical workspace — sub-10ms real-time probability ranking, rule-out verification &amp; medical literature
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2.5">
              {realtimeResult && (
                <span className="hidden sm:inline-flex items-center gap-1.5 text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 px-3 py-1.5 rounded-xl shadow-2xs">
                  <Activity className="w-3.5 h-3.5 text-emerald-600" />
                  {realtimeResult.latency_ms} ms Latency
                </span>
              )}
              <button
                type="button"
                onClick={() => setIsBigScreen(false)}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-black text-white bg-slate-900 hover:bg-slate-800 dark:bg-indigo-600 dark:hover:bg-indigo-500 shadow-md transition-all cursor-pointer"
                title="Exit Big Screen Mode (Esc)"
              >
                <Minimize2 className="w-4 h-4" />
                <span>Exit Big Screen</span>
                <kbd className="hidden md:inline-block ml-1 text-[10px] bg-slate-700 text-slate-200 px-1.5 py-0.5 rounded font-mono">Esc</kbd>
              </button>
            </div>
          </div>
        )}

        {/* ── Sub-30ms Real-Time Live Clinical Predictor HUD (Always Available) ── */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 rounded-3xl overflow-hidden border border-indigo-200/80 bg-gradient-to-br from-blue-50/70 via-white/90 to-indigo-50/70 shadow-[0_12px_36px_rgba(79,70,229,0.08),inset_0_1px_0_rgba(255,255,255,0.95)] backdrop-blur-2xl"
        >
          {/* Top Header */}
          <div className="px-6 py-4 flex items-center justify-between bg-gradient-to-r from-teal-50/90 via-white to-indigo-50/80 border-b border-slate-200/90 text-slate-900 shadow-xs">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center shadow-xs">
                <Zap className="w-4 h-4 text-teal-600 animate-pulse" />
              </div>
              <div>
                <h3 className="font-extrabold text-sm tracking-wider uppercase flex items-center gap-2 font-heading text-slate-900">
                  Real-Time Clinical Diagnostic Predictor
                  <span className="text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider shadow-2xs">
                    ⚡ Sub-10ms Inference
                  </span>
                </h3>
                <p className="text-[11px] text-slate-500 font-medium text-left">
                  Universal Medical Diagnostic Engine — Evaluates 260+ Clinical Profiles &amp; Open Domain Knowledge
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {realtimeResult && (
                <span className="text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 px-3 py-1 rounded-full flex items-center gap-1.5 shadow-2xs">
                  <Activity className="w-3.5 h-3.5 text-emerald-600" />
                  {realtimeResult.latency_ms} ms Latency
                </span>
              )}
              <button
                type="button"
                onClick={() => setIsBigScreen(prev => !prev)}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold text-indigo-700 hover:text-indigo-900 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200/90 shadow-2xs transition-all cursor-pointer"
                title={isBigScreen ? "Exit Big Screen Mode" : "Expand Differential Diagnosis to Big Screen Full Viewport"}
              >
                {isBigScreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
                <span>{isBigScreen ? "Exit Big Screen" : "Big Screen View"}</span>
              </button>
            </div>
          </div>

        <div className="p-6 md:p-8 flex flex-col gap-6">
          {/* Presets Bar (Categorized & Searchable - Compact Collapsible Drawer) */}
          <div className="bg-slate-50/90 rounded-2xl p-3 sm:p-3.5 border border-slate-200/90 shadow-2xs">
            <div className="flex flex-wrap items-center justify-between gap-2.5">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-teal-600" />
                <span className="text-xs font-extrabold text-slate-800 uppercase tracking-wider font-heading">
                  Clinical Case Benchmarks ({CLINICAL_PRESETS.length} Validated Scenarios):
                </span>
              </div>

              <div className="flex items-center gap-2">
                {/* Quick Search */}
                <div className="relative min-w-[200px]">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Filter cases (e.g. PE, Stroke)..."
                    value={presetSearch}
                    onChange={(e) => {
                      setPresetSearch(e.target.value);
                      if (!showBenchmarks) setShowBenchmarks(true);
                    }}
                    className="w-full text-xs pl-8 pr-3 py-1.5 rounded-xl border border-slate-200 bg-white text-slate-800 outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100 shadow-2xs"
                  />
                </div>

                <button
                  type="button"
                  onClick={() => setShowBenchmarks(prev => !prev)}
                  className="px-3 py-1.5 rounded-xl text-xs font-bold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-200 shadow-2xs transition-colors flex items-center gap-1.5 shrink-0"
                >
                  <span>{showBenchmarks ? "Hide Benchmarks" : "Browse Benchmarks"}</span>
                  {showBenchmarks ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {showBenchmarks && (
              <div className="mt-3 pt-3 border-t border-slate-200/70 space-y-2.5">
                {/* Category Filter Pills */}
                <div className="flex flex-wrap items-center gap-1.5 border-b border-slate-200/70 pb-2.5">
                  <button
                    type="button"
                    onClick={() => setPresetCategory("all")}
                    className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold transition-all ${
                      presetCategory === "all"
                        ? "bg-teal-600 text-white shadow-xs"
                        : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
                    }`}
                  >
                    <Layers className="w-3.5 h-3.5" />
                    All Benchmarks ({CLINICAL_PRESETS.length})
                  </button>

                  <button
                    type="button"
                    onClick={() => setPresetCategory("outbreak")}
                    className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold transition-all ${
                      presetCategory === "outbreak"
                        ? "bg-amber-600 text-white shadow-xs"
                        : "bg-white text-slate-600 hover:bg-amber-50 hover:text-amber-700 border border-slate-200"
                    }`}
                  >
                    <Globe className="w-3.5 h-3.5 text-amber-500" />
                    Live Outbreak Feeds ({CLINICAL_PRESETS.filter(p => p.category === "outbreak").length})
                  </button>

                  <button
                    type="button"
                    onClick={() => setPresetCategory("emergency")}
                    className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold transition-all ${
                      presetCategory === "emergency"
                        ? "bg-rose-600 text-white shadow-xs"
                        : "bg-white text-slate-600 hover:bg-rose-50 hover:text-rose-700 border border-slate-200"
                    }`}
                  >
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-500" />
                    Emergencies ({CLINICAL_PRESETS.filter(p => p.category === "emergency").length})
                  </button>

                  <button
                    type="button"
                    onClick={() => setPresetCategory("complex")}
                    className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold transition-all ${
                      presetCategory === "complex"
                        ? "bg-indigo-600 text-white shadow-xs"
                        : "bg-white text-slate-600 hover:bg-indigo-50 hover:text-indigo-700 border border-slate-200"
                    }`}
                  >
                    <FileText className="w-3.5 h-3.5 text-indigo-500" />
                    Complex EHR Notes ({CLINICAL_PRESETS.filter(p => p.category === "complex").length})
                  </button>

                  <button
                    type="button"
                    onClick={() => setPresetCategory("bedside")}
                    className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-bold transition-all ${
                      presetCategory === "bedside"
                        ? "bg-teal-700 text-white shadow-xs"
                        : "bg-white text-slate-600 hover:bg-teal-50 hover:text-teal-700 border border-slate-200"
                    }`}
                  >
                    <Stethoscope className="w-3.5 h-3.5 text-teal-600" />
                    Bedside Entities ({CLINICAL_PRESETS.filter(p => p.category === "bedside").length})
                  </button>

                  {presetSearch && (
                    <button
                      type="button"
                      onClick={() => setPresetSearch("")}
                      className="text-[11px] text-slate-500 hover:text-slate-800 underline ml-2"
                    >
                      Clear filter
                    </button>
                  )}
                </div>

                {/* Presets List */}
                <div className="flex flex-wrap gap-2 max-h-[140px] overflow-y-auto pr-1">
                  {filteredPresets.map((preset, i) => (
                    <button
                      key={i}
                      onClick={() => handlePresetSelect(preset.query)}
                      className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-white text-slate-700 border border-slate-200 hover:border-teal-400 hover:bg-teal-50/80 hover:text-teal-900 shadow-2xs transition-colors flex items-center gap-2"
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${
                        preset.category === "outbreak" ? "bg-amber-500" : preset.category === "emergency" ? "bg-rose-500" : preset.category === "complex" ? "bg-indigo-500" : "bg-teal-500"
                      }`} />
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Symptoms input area (Spacious & Ergonomic) */}
          <div className="w-full">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-extrabold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                <FileText className="w-4 h-4 text-indigo-600" />
                <span>Patient Symptoms &amp; Clinical Presentation (Real-Time Live Typing):</span>
              </label>
              <div className="flex items-center gap-3">
                {isPredicting && (
                  <span className="text-xs text-indigo-600 font-bold flex items-center gap-1.5">
                    <div className="w-3 h-3 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
                    Predicting live…
                  </span>
                )}
                {symptomInput && (
                  <button
                    onClick={() => setSymptomInput("")}
                    className="text-xs text-slate-500 hover:text-rose-600 font-semibold underline transition-colors"
                  >
                    Clear Input
                  </button>
                )}
              </div>
            </div>

            <textarea
              value={symptomInput}
              onChange={e => setSymptomInput(e.target.value)}
              placeholder="Type free-form patient symptoms, triage notes, or click a clinical case above (e.g. 59yo male with 2-hour history of crushing retrosternal chest pressure radiating down left arm...)"
              rows={4}
              className="w-full text-sm font-medium rounded-2xl px-5 py-4 resize-y outline-none border border-slate-300 bg-white text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 transition-all shadow-[inset_0_1px_2px_rgba(0,0,0,0.04)] leading-relaxed min-h-[110px]"
            />
            
            <div className="flex flex-wrap items-center justify-between text-xs font-medium text-slate-500 mt-2 px-1">
              <span className="flex items-center gap-1.5"><Sparkles className="w-3.5 h-3.5 text-indigo-500 shrink-0" /> Updates live as you type without latency. Evaluates vitals, hallmarks, and negation.</span>
              <span className="text-slate-400 font-mono">{symptomInput.length} characters</span>
            </div>

            {/* Interactive "What-If" Diagnostic Lab Simulator */}
            <div className="mt-3.5 pt-3 border-t border-slate-200/80 bg-slate-50/70 p-3.5 rounded-2xl">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <FlaskConical className="w-4 h-4 text-indigo-600" />
                  <span className="text-xs font-extrabold text-slate-700 uppercase tracking-wider font-heading">
                    "What-If?" Diagnostic Lab Simulator:
                  </span>
                </div>
                <span className="text-[11px] text-slate-500 font-medium">
                  Click chip to append simulated stat lab finding in real time
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {SIMULATED_LAB_CHIPS.map((chip, ci) => (
                  <button
                    key={ci}
                    type="button"
                    onClick={() => handleSimulateLab(chip.token)}
                    className="px-3 py-1.5 rounded-xl text-xs font-bold bg-white text-indigo-800 border border-indigo-200 hover:bg-indigo-50 hover:border-indigo-400 transition-all flex items-center gap-1.5 shadow-2xs"
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
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
                className="p-4.5 rounded-2xl bg-gradient-to-r from-rose-50 via-white to-rose-50/50 border-l-4 border-l-rose-500 border border-rose-200 text-slate-900 shadow-xs flex flex-col md:flex-row items-start md:items-center gap-3.5 relative overflow-hidden"
              >
                <div className="w-10 h-10 rounded-xl bg-rose-100 border border-rose-200 flex items-center justify-center flex-shrink-0 text-rose-600 shadow-2xs">
                  <ShieldAlert className="w-5 h-5 text-rose-600" />
                </div>
                <div className="flex-grow text-left">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <h4 className="text-sm font-black tracking-tight text-rose-950">
                      {realtimeResult.emergency_alert.condition}
                    </h4>
                    <span className="text-[10px] font-extrabold bg-rose-100 text-rose-800 border border-rose-200 px-2 py-0.5 rounded-full uppercase tracking-wider">
                      Priority Advisory
                    </span>
                  </div>
                  <p className="text-xs text-slate-700 font-medium mb-1.5 leading-relaxed">
                    {realtimeResult.emergency_alert.warning}
                  </p>
                  <p className="text-xs text-rose-800 font-bold bg-rose-100/90 px-3 py-1.5 rounded-lg border border-rose-200 inline-flex items-center gap-1.5 shadow-2xs">
                    <span>⚡ Immediate Action: {realtimeResult.emergency_alert.immediate_action}</span>
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
              className="p-5 rounded-2xl bg-gradient-to-r from-rose-50 via-white to-red-50/40 text-slate-900 shadow-xs border-2 border-rose-200 text-left"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2.5 border-b border-rose-100">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-rose-100 border border-rose-200 flex items-center justify-center shadow-2xs">
                    <ShieldAlert className="w-4 h-4 text-rose-600" />
                  </div>
                  <div>
                    <h4 className="text-xs font-black uppercase tracking-wider text-rose-900 flex items-center gap-2">
                      Must-Not-Miss Critical Emergency Watchlist
                      <span className="text-[10px] bg-rose-100 text-rose-800 border border-rose-200 px-2 py-0.5 rounded-full font-bold">
                        Cognitive Safety Net
                      </span>
                    </h4>
                    <p className="text-[11px] text-slate-600 font-medium">
                      High-acuity emergencies sharing features with current presentation — active bedside rule-out required:
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {realtimeResult.must_not_miss_candidates.map((item, mi) => (
                  <div
                    key={mi}
                    className="p-3.5 rounded-xl bg-white border border-rose-200/90 shadow-2xs flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <span className="font-extrabold text-sm text-slate-900">{item.disease}</span>
                        <span className={`text-[9px] font-black px-1.5 py-0.5 rounded ${
                          item.in_top_candidates
                            ? "bg-rose-600 text-white"
                            : "bg-slate-100 text-slate-700 border border-slate-200"
                        }`}>
                          {item.in_top_candidates ? "IN DIFFERENTIAL" : "RULE-OUT TARGET"}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-700 font-medium mb-2 leading-relaxed">
                        ⚡ <strong className="text-rose-900">Action:</strong> {item.immediate_action}
                      </p>
                    </div>
                    {item.confirmatory_tests && item.confirmatory_tests.length > 0 && (
                      <div className="text-[10px] text-slate-700 bg-rose-50/70 px-2.5 py-1.5 rounded-lg border border-rose-100 font-medium">
                        <strong className="text-rose-900">Rule-Out Test:</strong> {item.confirmatory_tests.join(", ")}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Consensus Criteria Met Notification Ribbon (if any criteria met) */}
          {realtimeResult?.criteria_evaluations && realtimeResult.criteria_evaluations.some(c => c.meets_criteria) && (
            <div className="p-3.5 rounded-2xl bg-emerald-50/90 border border-emerald-300 text-emerald-950 flex flex-wrap items-center justify-between gap-3 shadow-2xs">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-emerald-600 text-white flex items-center justify-center shrink-0 shadow-2xs">
                  <Check className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-xs font-black uppercase tracking-wider text-emerald-900 block font-heading">
                    Consensus Clinical Diagnostic Criteria Fulfilled
                  </span>
                  <span className="text-xs font-semibold text-emerald-800">
                    {realtimeResult.criteria_evaluations.filter(c => c.meets_criteria).map(c => c.criteria_name).join(" · ")}
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setActiveDiagnosticTab(prev => prev === "criteria" ? "none" : "criteria")}
                className="text-xs font-bold text-emerald-800 hover:text-emerald-900 bg-white hover:bg-emerald-100/60 px-3 py-1.5 rounded-xl border border-emerald-300 shadow-2xs transition-colors flex items-center gap-1 shrink-0"
              >
                <span>{activeDiagnosticTab === "criteria" ? "Hide Formal Criteria" : "Review Criteria Evidence →"}</span>
              </button>
            </div>
          )}

          {/* Specialized Clinical Diagnostic Toolset Toolbar */}
          {(Boolean(realtimeResult?.criteria_evaluations?.length) || Boolean(realtimeResult?.is_unstructured_note) || Boolean(realtimeResult?.calculated_indices && Object.keys(realtimeResult.calculated_indices).length > 0) || Boolean(realtimeResult?.quantitative_labs && Object.keys(realtimeResult.quantitative_labs).length > 0)) && (
            <div className="bg-white rounded-2xl border border-slate-200/90 p-3 shadow-2xs space-y-3 text-left">
              <div className="flex flex-wrap items-center justify-between gap-2.5">
                <div className="flex items-center gap-2">
                  <Brain className="w-4 h-4 text-indigo-600 shrink-0" />
                  <span className="text-xs font-black uppercase tracking-wider text-slate-800 font-heading">
                    Clinical Intelligence Suite:
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-1.5">
                  {realtimeResult?.criteria_evaluations && realtimeResult.criteria_evaluations.length > 0 && (
                    <button
                      type="button"
                      onClick={() => setActiveDiagnosticTab(prev => prev === "criteria" ? "none" : "criteria")}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                        activeDiagnosticTab === "criteria"
                          ? "bg-indigo-600 text-white shadow-xs"
                          : realtimeResult.criteria_evaluations.some(c => c.meets_criteria)
                            ? "bg-emerald-50 text-emerald-800 border border-emerald-300 hover:bg-emerald-100"
                            : "bg-slate-50 text-slate-700 border border-slate-200 hover:bg-slate-100"
                      }`}
                    >
                      <Scale className="w-3.5 h-3.5" />
                      <span>Consensus Criteria</span>
                      <span className={`text-[10px] font-black px-1.5 py-0.2 rounded-md ${
                        activeDiagnosticTab === "criteria"
                          ? "bg-white/20 text-white"
                          : realtimeResult.criteria_evaluations.some(c => c.meets_criteria)
                            ? "bg-emerald-600 text-white"
                            : "bg-slate-200 text-slate-700"
                      }`}>
                        {realtimeResult.criteria_evaluations.filter(c => c.meets_criteria).length > 0
                          ? `${realtimeResult.criteria_evaluations.filter(c => c.meets_criteria).length} Met`
                          : realtimeResult.criteria_evaluations.length}
                      </span>
                      {activeDiagnosticTab === "criteria" ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    </button>
                  )}

                  {realtimeResult?.is_unstructured_note && (
                    <button
                      type="button"
                      onClick={() => setActiveDiagnosticTab(prev => prev === "parser" ? "none" : "parser")}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                        activeDiagnosticTab === "parser"
                          ? "bg-indigo-600 text-white shadow-xs"
                          : "bg-slate-50 text-slate-700 border border-slate-200 hover:bg-slate-100"
                      }`}
                    >
                      <FileText className="w-3.5 h-3.5 text-indigo-500" />
                      <span>Note Parser</span>
                      <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded-md ${
                        activeDiagnosticTab === "parser" ? "bg-white/20 text-white" : "bg-indigo-50 text-indigo-700 border border-indigo-200"
                      }`}>
                        {realtimeResult.extracted_findings?.length || 0} Findings
                      </span>
                      {activeDiagnosticTab === "parser" ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    </button>
                  )}

                  {((realtimeResult?.calculated_indices && Object.keys(realtimeResult.calculated_indices).length > 0) ||
                    (realtimeResult?.quantitative_labs && Object.keys(realtimeResult.quantitative_labs).length > 0)) && (
                    <button
                      type="button"
                      onClick={() => setActiveDiagnosticTab(prev => prev === "biomarkers" ? "none" : "biomarkers")}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                        activeDiagnosticTab === "biomarkers"
                          ? "bg-teal-600 text-white shadow-xs"
                          : "bg-slate-50 text-slate-700 border border-slate-200 hover:bg-slate-100"
                      }`}
                    >
                      <FlaskConical className="w-3.5 h-3.5 text-teal-600" />
                      <span>Biomarkers &amp; Indices</span>
                      <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded-md ${
                        activeDiagnosticTab === "biomarkers" ? "bg-white/20 text-white" : "bg-teal-50 text-teal-700 border border-teal-200"
                      }`}>
                        {(realtimeResult?.calculated_indices ? Object.keys(realtimeResult.calculated_indices).length : 0) +
                         (realtimeResult?.quantitative_labs ? Object.keys(realtimeResult.quantitative_labs).length : 0)}
                      </span>
                      {activeDiagnosticTab === "biomarkers" ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    </button>
                  )}
                </div>
              </div>

              {/* Collapsible Active Tool Drawer */}
              <AnimatePresence>
                {activeDiagnosticTab !== "none" && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="pt-3 border-t border-slate-100 overflow-hidden"
                  >
                    {activeDiagnosticTab === "criteria" && realtimeResult?.criteria_evaluations && (
                      <div className="p-4 rounded-xl bg-gradient-to-br from-indigo-50/60 via-white to-blue-50/50 border border-indigo-200/90 text-left space-y-3">
                        <div className="flex items-center justify-between pb-2 border-b border-indigo-100">
                          <div className="flex items-center gap-2">
                            <Scale className="w-4 h-4 text-indigo-700" />
                            <h4 className="text-xs font-black uppercase tracking-wider text-indigo-900 font-heading">
                              Consensus Clinical Diagnostic Criteria Evaluator
                            </h4>
                          </div>
                          <span className="text-[10px] bg-indigo-100 text-indigo-800 border border-indigo-200 px-2 py-0.5 rounded-full font-bold">
                            Formal Validated Scoring
                          </span>
                        </div>
                        <div className="space-y-3">
                          {realtimeResult.criteria_evaluations.map((evalItem, ei) => (
                            <div
                              key={ei}
                              className={`p-3.5 rounded-xl border transition-all ${
                                evalItem.meets_criteria
                                  ? 'bg-emerald-50/90 border-emerald-300 shadow-xs'
                                  : 'bg-white border-slate-200 shadow-2xs'
                              }`}
                            >
                              <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                                <span className="font-extrabold text-sm text-slate-900 flex items-center gap-2">
                                  {evalItem.criteria_name}
                                </span>
                                <span className={`text-[10px] font-black px-2 py-0.5 rounded-lg flex items-center gap-1 shadow-2xs ${
                                  evalItem.meets_criteria
                                    ? 'bg-emerald-600 text-white'
                                    : 'bg-slate-100 text-slate-600 border border-slate-200'
                                }`}>
                                  {evalItem.meets_criteria ? '✓ CRITERIA FULFILLED' : 'SUBTHRESHOLD / RULE-OUT'}
                                </span>
                              </div>
                              <div className="text-xs font-medium text-slate-700 mb-2 flex flex-wrap items-center gap-x-4 gap-y-1">
                                {evalItem.total_score !== undefined && evalItem.total_score !== null && (
                                  <span>
                                    Calculated Score: <strong className="text-slate-900">{evalItem.total_score}</strong>
                                    {evalItem.threshold !== undefined && evalItem.threshold !== null && (
                                      <span className="text-slate-500"> (Threshold: {evalItem.threshold})</span>
                                    )}
                                  </span>
                                )}
                                {evalItem.major_criteria_met !== undefined && (
                                  <span>
                                    Major: <strong className="text-emerald-700">{evalItem.major_criteria_met}</strong> | Minor: <strong className="text-amber-700">{evalItem.minor_criteria_met}</strong>
                                  </span>
                                )}
                                {evalItem.risk_category && (
                                  <span>
                                    Risk: <strong className="text-amber-800">{evalItem.risk_category}</strong>
                                  </span>
                                )}
                                {evalItem.clinical_interpretation && (
                                  <span className="text-slate-600 italic">
                                    — {evalItem.clinical_interpretation}
                                  </span>
                                )}
                              </div>
                              {evalItem.fulfilled_items && evalItem.fulfilled_items.length > 0 && (
                                <div className="bg-slate-50 rounded-lg p-2 border border-slate-200 mb-2">
                                  <span className="text-[10px] uppercase font-extrabold text-slate-500 block mb-1">
                                    Validated Criterion Elements Met:
                                  </span>
                                  <div className="flex flex-wrap gap-1.5">
                                    {evalItem.fulfilled_items.map((item, ii) => (
                                      <span key={ii} className="text-[11px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded-md">
                                        ✓ {item}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {(evalItem.recommendation || evalItem.management_recommendation) && (
                                <div className="text-xs font-semibold text-amber-900 bg-amber-50 border border-amber-200 rounded-lg px-3 py-1.5 flex items-start gap-2 shadow-2xs">
                                  <Sparkles className="w-3.5 h-3.5 text-amber-600 flex-shrink-0 mt-0.5" />
                                  <span>
                                    <strong>Clinical Action:</strong> {evalItem.recommendation || evalItem.management_recommendation}
                                  </span>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {activeDiagnosticTab === "parser" && realtimeResult?.is_unstructured_note && (
                      <div className="p-4 rounded-xl bg-gradient-to-br from-indigo-50/60 via-white to-blue-50/50 border border-indigo-200/90 text-left space-y-3">
                        <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-indigo-100">
                          <div className="flex items-center gap-2">
                            <Brain className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                            <h4 className="text-xs font-black uppercase tracking-wider text-indigo-900 font-heading">
                              Real-Time Note Parser Transparency
                            </h4>
                            <span className="text-[10px] bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded-full border border-indigo-200 font-bold">
                              Clause-Level Scope &amp; Negation
                            </span>
                          </div>
                          {realtimeResult.note_summary && (
                            <span className="text-[11px] font-medium text-slate-600 italic">
                              {realtimeResult.note_summary}
                            </span>
                          )}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                          {realtimeResult.extracted_findings && realtimeResult.extracted_findings.length > 0 && (
                            <div className="bg-white rounded-xl p-3 border border-emerald-200 shadow-2xs">
                              <div className="font-bold text-emerald-800 mb-1.5 flex items-center gap-1">
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                                <span>Extracted Clinical Findings ({realtimeResult.extracted_findings.length}):</span>
                              </div>
                              <div className="flex flex-wrap gap-1.5">
                                {realtimeResult.extracted_findings.map((f, i) => (
                                  <span key={i} className="px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px] font-medium">
                                    {f}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {realtimeResult.extracted_negated && realtimeResult.extracted_negated.length > 0 && (
                            <div className="bg-white rounded-xl p-3 border border-rose-200 shadow-2xs">
                              <div className="font-bold text-rose-800 mb-1.5 flex items-center gap-1">
                                <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                                <span>Negated / Ruled Out Findings ({realtimeResult.extracted_negated.length}):</span>
                              </div>
                              <div className="flex flex-wrap gap-1.5">
                                {realtimeResult.extracted_negated.map((n, i) => (
                                  <span key={i} className="px-2 py-0.5 rounded-md bg-rose-50 text-rose-800 border border-rose-200 text-[11px] font-medium line-through">
                                    {n}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {realtimeResult.extracted_vitals && Object.keys(realtimeResult.extracted_vitals).length > 0 && (
                            <div className="bg-white rounded-xl p-3 border border-sky-200 shadow-2xs">
                              <div className="font-bold text-sky-800 mb-1.5 flex items-center gap-1">
                                <Activity className="w-3.5 h-3.5 text-sky-600" />
                                <span>Extracted Vital Signs:</span>
                              </div>
                              <div className="flex flex-wrap gap-2 text-[11px] font-medium text-slate-800">
                                {realtimeResult.extracted_vitals.blood_pressure && (
                                  <span className="px-2 py-0.5 rounded-md bg-sky-50 border border-sky-200">
                                    BP: <strong className="text-sky-900">{realtimeResult.extracted_vitals.blood_pressure}</strong>
                                  </span>
                                )}
                                {realtimeResult.extracted_vitals.heart_rate && (
                                  <span className="px-2 py-0.5 rounded-md bg-sky-50 border border-sky-200">
                                    HR: <strong className="text-sky-900">{realtimeResult.extracted_vitals.heart_rate} bpm</strong>
                                  </span>
                                )}
                                {realtimeResult.extracted_vitals.respiratory_rate && (
                                  <span className="px-2 py-0.5 rounded-md bg-sky-50 border border-sky-200">
                                    RR: <strong className="text-sky-900">{realtimeResult.extracted_vitals.respiratory_rate}/min</strong>
                                  </span>
                                )}
                                {realtimeResult.extracted_vitals.oxygen_saturation && (
                                  <span className="px-2 py-0.5 rounded-md bg-sky-50 border border-sky-200">
                                    SpO2: <strong className="text-sky-900">{realtimeResult.extracted_vitals.oxygen_saturation}%</strong>
                                  </span>
                                )}
                                {realtimeResult.extracted_vitals.temperature && (
                                  <span className="px-2 py-0.5 rounded-md bg-sky-50 border border-sky-200">
                                    Temp: <strong className="text-sky-900">{realtimeResult.extracted_vitals.temperature}°</strong>
                                  </span>
                                )}
                              </div>
                            </div>
                          )}

                          {realtimeResult.diagnostic_markers && realtimeResult.diagnostic_markers.length > 0 && (
                            <div className="bg-white rounded-xl p-3 border border-amber-200 shadow-2xs">
                              <div className="font-bold text-amber-800 mb-1.5 flex items-center gap-1">
                                <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                                <span>Pathognomonic Diagnostic Markers:</span>
                              </div>
                              <div className="flex flex-wrap gap-1.5">
                                {realtimeResult.diagnostic_markers.map((d, i) => (
                                  <span key={i} className="px-2 py-0.5 rounded-md bg-amber-50 text-amber-900 border border-amber-200 text-[11px] font-medium">
                                    {d}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {realtimeResult.section_breakdown && Object.keys(realtimeResult.section_breakdown).length > 0 && (
                            <div className="bg-white rounded-xl p-3 border border-indigo-200 shadow-2xs col-span-1 md:col-span-2">
                              <div className="font-bold text-indigo-900 mb-1.5 flex items-center gap-1.5">
                                <FileText className="w-3.5 h-3.5 text-indigo-600" />
                                <span>EHR Document Section Breakdown:</span>
                              </div>
                              <div className="flex flex-wrap gap-1.5">
                                {Object.keys(realtimeResult.section_breakdown).map((sec, si) => (
                                  <span key={si} className="px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-800 border border-indigo-200 text-[11px] font-semibold flex items-center gap-1">
                                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                                    {sec.replace(/_/g, ' ')}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {realtimeResult.background_history && realtimeResult.background_history.length > 0 && (
                            <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-2xs col-span-1 md:col-span-2">
                              <div className="font-bold text-slate-700 mb-1.5 flex items-center justify-between">
                                <span className="flex items-center gap-1.5">
                                  <ShieldCheck className="w-3.5 h-3.5 text-slate-500" />
                                  <span>Isolated Past Medical &amp; Background Distractors ({realtimeResult.background_history.length}):</span>
                                </span>
                                <span className="text-[10px] text-slate-400 font-medium italic">
                                  Isolated from acute diagnostic score weighting
                                </span>
                              </div>
                              <div className="flex flex-wrap gap-1.5">
                                {realtimeResult.background_history.map((h, hi) => (
                                  <span key={hi} className="px-2 py-0.5 rounded-md bg-slate-50 text-slate-700 border border-slate-200 text-[11px] font-medium">
                                    {h}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {activeDiagnosticTab === "biomarkers" && (
                      <div className="p-4 rounded-xl bg-gradient-to-br from-teal-50/60 via-white to-cyan-50/50 border border-teal-200/90 text-left space-y-3">
                        <div className="flex items-center justify-between pb-2 border-b border-teal-100">
                          <div className="flex items-center gap-2">
                            <FlaskConical className="w-4 h-4 text-teal-600" />
                            <h4 className="text-xs font-black uppercase tracking-wider text-teal-900 font-heading">
                              Quantitative Biomarkers &amp; Calculated Physiological Indices
                            </h4>
                          </div>
                          <span className="text-[10px] bg-teal-100 text-teal-800 border border-teal-200 px-2 py-0.5 rounded-full font-bold">
                            Deterministic Calculation
                          </span>
                        </div>

                        {realtimeResult?.calculated_indices && Object.keys(realtimeResult.calculated_indices).length > 0 && (
                          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                            {realtimeResult.calculated_indices.anion_gap !== undefined && (
                              <div className="bg-white rounded-xl p-3 border border-amber-200 shadow-2xs">
                                <div className="text-[10px] uppercase font-extrabold text-amber-800 tracking-wider">Serum Anion Gap</div>
                                <div className="text-lg font-black text-slate-900 mt-0.5">
                                  {realtimeResult.calculated_indices.anion_gap} <span className="text-xs font-semibold text-slate-500">mEq/L</span>
                                </div>
                                <div className="text-[11px] font-bold text-amber-700 mt-1">
                                  {realtimeResult.calculated_indices.anion_gap > 12 ? "⚠️ High Anion Gap Metabolic Acidosis (HAGMA)" : "✓ Normal Anion Gap (≤12)"}
                                </div>
                              </div>
                            )}
                            {realtimeResult.calculated_indices.bun_cr_ratio !== undefined && (
                              <div className="bg-white rounded-xl p-3 border border-sky-200 shadow-2xs">
                                <div className="text-[10px] uppercase font-extrabold text-sky-800 tracking-wider">BUN / Creatinine Ratio</div>
                                <div className="text-lg font-black text-slate-900 mt-0.5">
                                  {realtimeResult.calculated_indices.bun_cr_ratio}
                                </div>
                                <div className="text-[11px] font-bold text-sky-700 mt-1">
                                  {realtimeResult.calculated_indices.bun_cr_ratio > 20 ? "⚠️ Prerenal Azotemia Pattern (>20:1)" : "✓ Normal / Intrinsic Pattern"}
                                </div>
                              </div>
                            )}
                            {realtimeResult.calculated_indices.csf_serum_glucose_ratio !== undefined && (
                              <div className="bg-white rounded-xl p-3 border border-rose-200 shadow-2xs">
                                <div className="text-[10px] uppercase font-extrabold text-rose-800 tracking-wider">CSF / Serum Glucose Ratio</div>
                                <div className="text-lg font-black text-slate-900 mt-0.5">
                                  {realtimeResult.calculated_indices.csf_serum_glucose_ratio}
                                </div>
                                <div className="text-[11px] font-bold text-rose-700 mt-1">
                                  {realtimeResult.calculated_indices.csf_serum_glucose_ratio < 0.40 ? "Hypoglycorrhachia (Bacterial Meningitis)" : "Normal Ratio (≥0.60)"}
                                </div>
                              </div>
                            )}
                          </div>
                        )}

                        {realtimeResult?.quantitative_labs && Object.keys(realtimeResult.quantitative_labs).length > 0 && (
                          <div>
                            <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-600 mb-1.5">
                              Extracted Exact Lab Values &amp; Severity Tiers:
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {Object.entries(realtimeResult.quantitative_labs).map(([key, lab]: [string, any], li) => (
                                <div key={li} className="px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-xs flex items-center gap-1.5 shadow-2xs">
                                  <span className="font-bold text-slate-600 uppercase">{key.replace(/_/g, ' ')}:</span>
                                  <span className="font-extrabold text-teal-700">{lab.value} {lab.unit}</span>
                                  {lab.flag && (
                                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                                      lab.flag.includes('severe') || lab.flag.includes('critical') || lab.flag.includes('massive')
                                        ? 'bg-rose-100 text-rose-800 border border-rose-200'
                                        : 'bg-amber-100 text-amber-800 border border-amber-200'
                                    }`}>
                                      {lab.flag.replace(/_/g, ' ')}
                                    </span>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}

          {/* Live Real-Time Prediction Results */}
          {realtimeResult && realtimeResult.top_candidates.length > 0 && (
            <div className="space-y-4">
              {/* Active Outbreak Clinical Advisory Banner */}
              {realtimeResult.outbreak_detected && realtimeResult.outbreak_matches && realtimeResult.outbreak_matches.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
                  className="p-5 rounded-2xl bg-gradient-to-r from-rose-50 via-white to-rose-50/50 text-slate-900 shadow-xs border-l-4 border-l-rose-500 border border-rose-200 text-left relative overflow-hidden"
                >
                  <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-rose-100 mb-3">
                    <div className="flex items-center gap-2.5">
                      <div className="w-9 h-9 rounded-xl bg-rose-100 border border-rose-200 flex items-center justify-center flex-shrink-0 shadow-2xs">
                        <ShieldAlert className="w-5 h-5 text-rose-600" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="text-sm font-black uppercase tracking-wider text-rose-950">
                            Active Epidemic &amp; State Outbreak Advisory
                          </h4>
                          <span className="inline-flex items-center gap-1.5 text-[10px] bg-rose-100 text-rose-800 px-2.5 py-0.5 rounded-full font-bold border border-rose-200">
                            <span className="w-1.5 h-1.5 rounded-full bg-rose-600" />
                            LIVE SURVEILLANCE MATCH
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 font-medium mt-0.5">
                          {realtimeResult.outbreak_summary || "Patient clinical presentation matches active epidemic outbreak pathogen profiles."}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-bold bg-white px-3 py-1 rounded-xl text-rose-800 border border-rose-200 shadow-2xs">
                        Reporting: {realtimeResult.outbreak_matches[0]?.reporting_agency || "NCDC / IDSP"}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {realtimeResult.outbreak_matches.map((ob: any, obi: number) => (
                      <div key={obi} className="p-3.5 rounded-xl bg-white border border-rose-200 text-xs shadow-2xs">
                        <div className="flex items-center justify-between gap-2 mb-1.5">
                          <span className="font-extrabold text-sm text-slate-900">
                            {ob.disease_name} — {ob.state_or_country}
                          </span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                            ob.alert_level === 'CRITICAL' ? 'bg-rose-100 text-rose-800 border border-rose-300' : 'bg-amber-100 text-amber-800 border border-amber-300'
                          }`}>
                            {ob.alert_level}
                          </span>
                        </div>
                        <div className="space-y-1 text-slate-700 font-medium">
                          <div><strong className="text-rose-900">Pathogen:</strong> {ob.pathogen}</div>
                          <div><strong className="text-rose-900">Isolation Directive:</strong> {ob.isolation_protocol}</div>
                          <div><strong className="text-rose-900">Confirmatory Lab:</strong> {ob.confirmatory_test}</div>
                          {ob.districts && ob.districts.length > 0 && (
                            <div><strong className="text-rose-900">Hotspot Districts:</strong> {ob.districts.join(", ")}</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}

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
                      <Table className="w-3.5 h-3.5 text-purple-600" />
                      <span>{showComparisonMatrix ? "Hide Matrix" : "Compare Side-by-Side"}</span>
                    </button>
                  )}

                  {/* Copy MDM Note Button */}
                  {realtimeResult.clinical_mdm_summary && (
                    <button
                      type="button"
                      onClick={handleCopyMdm}
                      className="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white border border-teal-700 shadow-xs transition-colors flex items-center gap-1.5"
                    >
                      {copiedMdm ? <Check className="w-3.5 h-3.5 text-emerald-200" /> : <Copy className="w-3.5 h-3.5 text-teal-100" />}
                      <span>{copiedMdm ? "Copied MDM!" : "Copy EMR MDM Note"}</span>
                    </button>
                  )}

                  {realtimeResult.clinical_mdm_summary && (
                    <button
                      type="button"
                      onClick={() => setShowMdmModal(prev => !prev)}
                      className="px-2.5 py-1.5 rounded-xl text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 shadow-xs transition-all"
                      title="Preview full EMR Medical Decision Making Note"
                    >
                      <FileCheck className="w-3.5 h-3.5 text-slate-600" />
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
                    className="overflow-hidden rounded-2xl border border-indigo-200 bg-white text-slate-900 shadow-lg text-left"
                  >
                    <div className="p-4 bg-indigo-50/80 border-b border-indigo-100 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-indigo-700" />
                        <h4 className="text-xs font-black uppercase tracking-wider text-indigo-900">
                          EMR Medical Decision Making (MDM) Note Preview
                        </h4>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={handleCopyMdm}
                          className="px-3 py-1 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-1 shadow-xs"
                        >
                          {copiedMdm ? <Check className="w-3 h-3 text-emerald-200" /> : <Copy className="w-3 h-3" />}
                          <span>{copiedMdm ? "Copied!" : "Copy Note"}</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => setShowMdmModal(false)}
                          className="text-xs text-slate-500 hover:text-slate-800 font-bold"
                        >
                          Close
                        </button>
                      </div>
                    </div>
                    <div className="p-4">
                      <pre className="text-xs font-mono text-slate-800 whitespace-pre-wrap leading-relaxed max-h-72 overflow-y-auto bg-slate-50 p-3.5 rounded-xl border border-slate-200">
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
                    <div className="p-4 bg-gradient-to-r from-purple-50 via-white to-indigo-50 border-b border-purple-200 text-purple-950 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Table className="w-4 h-4 text-purple-700" />
                        <h4 className="text-xs font-black uppercase tracking-wider text-purple-900">
                          Multi-Candidate Diagnostic Comparison Matrix
                        </h4>
                      </div>
                      <button
                        onClick={() => setShowComparisonMatrix(false)}
                        className="text-xs text-purple-700 hover:text-purple-900 underline font-semibold"
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
                  className="p-5 rounded-2xl bg-gradient-to-r from-purple-50 via-white to-indigo-50/60 text-slate-900 shadow-xs border border-purple-200 text-left"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2.5 border-b border-purple-100">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-xl bg-purple-100 border border-purple-200 flex items-center justify-center shadow-2xs">
                        <Target className="w-4 h-4 text-purple-700" />
                      </div>
                      <div>
                        <h4 className="text-xs font-black uppercase tracking-wider text-purple-900 flex items-center gap-2">
                          Discriminative "Next Best Test" (Maximum Information Gain)
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-black uppercase tracking-wider border ${
                            realtimeResult.differentiating_recommendation.urgency === 'IMMEDIATE'
                              ? 'bg-rose-100 text-rose-800 border-rose-300 font-bold'
                              : 'bg-amber-100 text-amber-800 border-amber-300 font-bold'
                          }`}>
                            ⚡ {realtimeResult.differentiating_recommendation.urgency}
                          </span>
                        </h4>
                        <p className="text-[11px] text-slate-600 font-medium">
                          Single decisive investigation to separate #{1} <strong>{realtimeResult.differentiating_recommendation.candidate_1}</strong> from #{2} <strong>{realtimeResult.differentiating_recommendation.candidate_2}</strong>
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-white border border-purple-200 shadow-2xs">
                    <div className="text-xs font-black text-purple-950 flex items-center gap-2 mb-1">
                      <FlaskConical className="w-4 h-4 text-purple-600 flex-shrink-0" />
                      <span className="text-sm text-purple-900 font-extrabold">
                        {realtimeResult.differentiating_recommendation.differentiating_investigation}
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 font-medium pl-6 leading-relaxed">
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
                  className="p-5 rounded-2xl bg-gradient-to-r from-teal-50/70 via-white to-emerald-50/50 text-slate-900 shadow-xs border border-teal-200 text-left"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2.5 border-b border-teal-100">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-xl bg-teal-100 border border-teal-200 flex items-center justify-center shadow-2xs">
                        <HelpCircle className="w-4 h-4 text-teal-700" />
                      </div>
                      <div>
                        <h4 className="text-xs font-black uppercase tracking-wider text-teal-900 flex items-center gap-2">
                          Bedside Clarifying Examination Prompter ($0 Cost, 30-Second Rule-In/Out)
                          <span className="text-[10px] bg-teal-100 text-teal-800 border border-teal-200 px-2 py-0.5 rounded-full font-bold">
                            Interactive Socratic Aid
                          </span>
                        </h4>
                        <p className="text-[11px] text-slate-600 font-medium">
                          Targeted bedside exam maneuvers and questions to decisively separate top competing diagnoses. Click to update differential:
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    {realtimeResult.bedside_clarifying_questions.map((q, qi) => (
                      <div
                        key={qi}
                        className="p-3.5 rounded-xl bg-white border border-teal-200 shadow-2xs flex flex-col md:flex-row items-start md:items-center justify-between gap-3"
                      >
                        <div className="flex-grow">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-md bg-teal-100 text-teal-800 border border-teal-200">
                              {q.maneuver}
                            </span>
                            <span className="text-[10px] font-semibold text-slate-500">
                              Separates: <strong className="text-slate-700">{q.differentiates}</strong>
                            </span>
                          </div>
                          <p className="text-xs font-semibold text-slate-900 leading-relaxed">
                            {q.question}
                          </p>
                        </div>

                        <div className="flex items-center gap-2 flex-shrink-0">
                          <button
                            type="button"
                            onClick={() => handleBedsideAnswer(q.positive_token)}
                            className="px-3 py-1.5 rounded-xl text-xs font-bold bg-teal-600 hover:bg-teal-700 active:opacity-90 text-white shadow-2xs transition-all flex items-center gap-1"
                          >
                            <Check className="w-3.5 h-3.5" />
                            <span>{q.positive_label}</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => handleBedsideAnswer(q.negative_token)}
                            className="px-3 py-1.5 rounded-xl text-xs font-bold bg-rose-50 hover:bg-rose-100 active:opacity-90 text-rose-700 border border-rose-200 shadow-2xs transition-all flex items-center gap-1"
                          >
                            <span>{q.negative_label}</span>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Live Outbreak Surveillance Alert Banner */}
              {realtimeResult.outbreak_detected && realtimeResult.outbreak_summary && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="mb-5 p-4 rounded-2xl bg-gradient-to-r from-rose-500/10 via-amber-500/10 to-rose-500/10 border-2 border-rose-400/80 shadow-md backdrop-blur-md"
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-xl bg-rose-600 text-white shadow-sm shrink-0 mt-0.5">
                      <ShieldAlert className="w-5 h-5 animate-pulse" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-black uppercase tracking-wider text-rose-800 bg-rose-100 px-2.5 py-0.5 rounded-full border border-rose-300">
                          Active Epidemic Outbreak Surveillance Alert
                        </span>
                        <span className="text-[10px] text-rose-700 font-bold">
                          Live WHO / CDC / MoHFW Surveillance Match
                        </span>
                      </div>
                      <p className="text-sm font-black text-rose-950 leading-snug">
                        {realtimeResult.outbreak_summary}
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}

              <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
                {realtimeResult.top_candidates.map((cand, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.04 }}
                    className={`p-6 rounded-3xl border transition-all text-left bg-white shadow-sm hover:shadow-md flex flex-col justify-between ${
                      idx === 0
                        ? 'border-indigo-300 ring-2 ring-indigo-100 bg-gradient-to-br from-indigo-50/40 via-white to-white'
                        : 'border-slate-200/90 hover:border-indigo-200'
                    }`}
                  >
                    <div>
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="flex items-center gap-3">
                          <span className={`w-9 h-9 rounded-2xl flex items-center justify-center font-black text-sm ${
                            idx === 0 
                              ? 'bg-gradient-to-br from-indigo-600 to-indigo-700 text-white shadow-md shadow-indigo-500/25' 
                              : 'bg-slate-100 text-slate-700 border border-slate-200'
                          }`}>
                            #{idx + 1}
                          </span>
                          <div>
                            <h5 className="font-black text-slate-900 text-lg leading-tight font-heading">
                              {cand.disease}
                            </h5>
                            <div className="flex items-center gap-2 mt-1">
                              {cand.icd10 && (
                                <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md border border-slate-200 font-mono">
                                  ICD-10: {cand.icd10}
                                </span>
                              )}
                              {cand.icd11 && (
                                <span className="text-[10px] font-bold bg-blue-50 text-blue-700 px-2 py-0.5 rounded-md border border-blue-200 font-mono">
                                  ICD-11: {cand.icd11}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Triage & Probability Badge */}
                        <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                          <span className={`text-base font-black px-3 py-1 rounded-xl shadow-xs ${
                            idx === 0 
                              ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white' 
                              : 'bg-slate-800 text-white'
                          }`}>
                            {cand.display_score}
                          </span>
                          <span className={`text-[10px] font-black px-2.5 py-0.5 rounded-full uppercase tracking-wider ${
                            cand.triage === 'EMERGENT'
                              ? 'bg-rose-50 text-rose-700 border border-rose-200 font-bold'
                              : cand.triage === 'URGENT'
                              ? 'bg-amber-100 text-amber-800 border border-amber-200'
                              : 'bg-blue-50 text-blue-700 border border-blue-200'
                          }`}>
                            {cand.triage}
                          </span>
                        </div>
                      </div>

                      {/* Live Outbreak Match Alert Banner on Card */}
                      {cand.is_outbreak_match && (
                        <div className="mb-3.5 p-3 rounded-2xl bg-rose-50 text-slate-900 border-l-4 border-l-rose-500 border border-rose-200 shadow-2xs">
                          <div className="flex items-center justify-between gap-2 mb-1">
                            <div className="flex items-center gap-2">
                              <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
                              <span className="text-xs font-black uppercase tracking-wider text-rose-900">
                                {cand.outbreak_badge || "LIVE EPIDEMIC SURVEILLANCE MATCH"}
                              </span>
                            </div>
                            {cand.outbreak_details?.alert_level && (
                              <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                                cand.outbreak_details.alert_level === 'CRITICAL'
                                  ? 'bg-rose-100 text-rose-800 border border-rose-300'
                                  : 'bg-amber-100 text-amber-800 border border-amber-300'
                              }`}>
                                {cand.outbreak_details.alert_level}
                              </span>
                            )}
                          </div>
                          {cand.outbreak_details?.isolation_protocol && (
                            <p className="text-[11px] text-slate-700 font-semibold mb-1 leading-relaxed">
                              <strong className="text-rose-900">Isolation Protocol:</strong> {cand.outbreak_details.isolation_protocol}
                            </p>
                          )}
                          {cand.outbreak_details?.reporting_agency && (
                            <div className="text-[10px] text-slate-600 flex flex-wrap items-center gap-2 font-medium">
                              <span><strong>Agency:</strong> {cand.outbreak_details.reporting_agency}</span>
                              {cand.outbreak_details?.confirmatory_test && (
                                <span>• <strong>Lab Protocol:</strong> {cand.outbreak_details.confirmatory_test}</span>
                              )}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Progress Bar */}
                      <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden mb-3.5 border border-slate-200/50">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            idx === 0
                              ? 'bg-gradient-to-r from-indigo-500 via-teal-500 to-emerald-500'
                              : 'bg-gradient-to-r from-indigo-400 to-purple-400'
                          }`}
                          style={{ width: `${Math.min(Math.round(cand.score * 100), 100)}%` }}
                        />
                      </div>

                      {/* Hallmark Tag if matched */}
                      {cand.is_hallmark_match && (
                        <div className="mb-3 flex items-center gap-2 text-xs font-extrabold text-indigo-800 bg-indigo-50 px-3 py-1.5 rounded-xl border border-indigo-200">
                          <Sparkles className="w-4 h-4 text-indigo-600 flex-shrink-0" />
                          <span>Pathognomonic hallmark matches present</span>
                        </div>
                      )}

                      {/* Supporting Findings */}
                      {cand.supporting_findings.length > 0 && (
                        <div className="mb-3 text-left">
                          <span className="text-[11px] font-extrabold text-slate-500 uppercase tracking-wider block mb-1.5 font-heading">
                            Clinically Matched Findings:
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {cand.supporting_findings.map((finding, fi) => (
                              <span key={fi} className="text-xs font-semibold bg-slate-50 text-slate-700 px-2.5 py-1 rounded-lg border border-slate-200 flex items-center gap-1">
                                <Check className="w-3 h-3 text-emerald-600" />
                                <span>{finding}</span>
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Priority Bedside / Confirmatory Tests */}
                      {cand.immediate_tests.length > 0 && (
                        <div className="text-left bg-purple-50/70 p-3.5 rounded-2xl border border-purple-200/80 mb-3">
                          <span className="text-[11px] font-extrabold text-purple-900 uppercase tracking-wider flex items-center gap-1.5 mb-2 font-heading">
                            <FlaskConical className="w-3.5 h-3.5 text-purple-600" /> Priority Bedside &amp; Confirmatory Tests ({cand.immediate_tests.length}):
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {cand.immediate_tests.map((test, ti) => (
                              <span key={ti} className="text-xs font-semibold bg-white text-purple-950 px-2.5 py-1 rounded-lg border border-purple-200 shadow-2xs flex items-center gap-1">
                                <span className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                                <span>{test}</span>
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Pharmacotherapy / Recommended Medications */}
                      {((cand.recommended_medications && cand.recommended_medications.length > 0) || cand.treatment_summary) && (
                        <div className="text-left bg-emerald-50/70 p-3.5 rounded-2xl border border-emerald-200/80 mb-3">
                          <span className="text-[11px] font-extrabold text-emerald-900 uppercase tracking-wider flex items-center gap-1.5 mb-1.5 font-heading">
                            <Pill className="w-3.5 h-3.5 text-emerald-600" /> First-Line Pharmacotherapy / Rx:
                          </span>
                          {cand.treatment_summary && (
                            <div className="text-xs font-bold text-emerald-950 mb-1.5">
                              {cand.treatment_summary}
                            </div>
                          )}
                          {cand.recommended_medications && cand.recommended_medications.length > 0 && (
                            <div className="flex flex-wrap gap-1.5">
                              {cand.recommended_medications.map((med, mi) => (
                                <span key={mi} className="text-xs font-semibold bg-white text-emerald-950 px-2.5 py-1 rounded-lg border border-emerald-200 shadow-2xs flex items-center gap-1">
                                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                                  <span>{med}</span>
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Clinical Pearl */}
                      {cand.pearl && (
                        <p className="text-xs text-slate-600 italic mt-3 border-t border-slate-100 pt-2 text-left bg-slate-50/50 p-2.5 rounded-xl flex items-start gap-1.5">
                          <Lightbulb className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                          <span><strong>Clinical Pearl:</strong> {cand.pearl}</span>
                        </p>
                      )}
                    </div>

                    {/* Quick Action Toolbar for Real-Time Candidate */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-3.5 pt-3 border-t border-slate-100">
                      <button
                        type="button"
                        onClick={() => {
                          setRealtimePanelFor(prev => 
                            prev?.disease === cand.disease && prev?.tab === "investigations" 
                              ? null 
                              : { disease: cand.disease, tab: "investigations" }
                          );
                        }}
                        className={`px-3 py-2 rounded-xl text-xs font-bold transition-colors flex items-center justify-center gap-1.5 shadow-2xs ${
                          realtimePanelFor?.disease === cand.disease && realtimePanelFor?.tab === "investigations"
                            ? "bg-indigo-600 text-white shadow-indigo-200"
                            : "bg-indigo-50/90 text-indigo-700 hover:bg-indigo-100 border border-indigo-200"
                        }`}
                      >
                        <FlaskConical className="w-3.5 h-3.5" />
                        <span>View Investigations</span>
                        {realtimePanelFor?.disease === cand.disease && realtimePanelFor?.tab === "investigations" ? (
                          <ChevronUp className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronDown className="w-3.5 h-3.5" />
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
                        className={`px-3 py-2 rounded-xl text-xs font-bold transition-colors flex items-center justify-center gap-1.5 shadow-2xs ${
                          realtimePanelFor?.disease === cand.disease && realtimePanelFor?.tab === "medications"
                            ? "bg-emerald-600 text-white shadow-emerald-200"
                            : "bg-emerald-50/90 text-emerald-800 hover:bg-emerald-100 border border-emerald-200"
                        }`}
                      >
                        <ShieldCheck className="w-3.5 h-3.5" />
                        <span>View Safe Medications</span>
                        {realtimePanelFor?.disease === cand.disease && realtimePanelFor?.tab === "medications" ? (
                          <ChevronUp className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronDown className="w-3.5 h-3.5" />
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
                        className={`px-3 py-2 rounded-xl text-xs font-bold transition-colors flex items-center justify-center gap-1.5 shadow-2xs ${
                          realtimePanelFor?.disease === cand.disease && realtimePanelFor?.tab === "intelligence"
                            ? "bg-purple-600 text-white shadow-purple-200"
                            : "bg-purple-50/90 text-purple-700 hover:bg-purple-100 border border-purple-200"
                        }`}
                      >
                        <Globe className="w-3.5 h-3.5" />
                        <span>Disease Intelligence</span>
                        {realtimePanelFor?.disease === cand.disease && realtimePanelFor?.tab === "intelligence" ? (
                          <ChevronUp className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronDown className="w-3.5 h-3.5" />
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
              className="flex items-center gap-2 px-8 py-3.5 rounded-2xl text-sm font-bold text-white transition-all hover:brightness-105 active:opacity-90 disabled:opacity-60 bg-gradient-to-r from-indigo-600 via-indigo-700 to-purple-600 shadow-[0_4px_18px_rgba(79,70,229,0.35),inset_0_1px_0_rgba(255,255,255,0.3)] hover:shadow-[0_6px_24px_rgba(79,70,229,0.45)]"
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
            <div className="w-16 h-16 bg-[var(--surface-sunken)] rounded-full flex items-center justify-center mb-4 shadow-inner text-slate-400">
              <HelpCircle className="w-8 h-8" />
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
          <div className="w-16 h-16 bg-[var(--surface-sunken)] rounded-full flex items-center justify-center mb-4 shadow-inner text-slate-400">
            <Search className="w-8 h-8" />
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
                type="button"
                onClick={() => setIsBigScreen(prev => !prev)}
                className="text-xs text-indigo-700 bg-indigo-50 hover:bg-indigo-100 px-3 py-1.5 rounded-full font-bold shadow-2xs border border-indigo-200 transition-all flex items-center gap-1.5 cursor-pointer"
                title={isBigScreen ? "Exit Big Screen Mode" : "Expand Differential Diagnosis to Big Screen"}
              >
                {isBigScreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
                <span>{isBigScreen ? "Exit Big Screen" : "Big Screen"}</span>
              </button>
              <button
                onClick={() => runAnalysis()}
                className="text-xs text-blue-700 bg-white/90 hover:bg-white px-3.5 py-1.5 rounded-full font-bold shadow-sm border border-blue-200/70 hover:shadow hover:brightness-105 active:opacity-90 transition-all flex items-center gap-1.5"
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
        {/* Outbreak Advisory in Deep Synthesis */}
        {data.outbreak_detected && data.outbreak_matches && data.outbreak_matches.length > 0 && (
          <div className="p-4.5 rounded-2xl bg-rose-50 text-slate-900 border-l-4 border-l-rose-500 border border-rose-200 shadow-2xs text-left mb-4">
            <div className="flex items-center gap-2 mb-1.5">
              <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
              <span className="text-xs font-black uppercase tracking-wider text-rose-900">
                ACTIVE STATE &amp; GLOBAL EPIDEMIC SURVEILLANCE MATCH
              </span>
            </div>
            <p className="text-xs text-slate-700 font-semibold mb-2">
              {data.outbreak_summary}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] text-slate-700">
              {data.outbreak_matches.slice(0, 2).map((ob: any, i: number) => (
                <div key={i} className="p-2.5 rounded-xl bg-white border border-rose-200 shadow-2xs">
                  <div className="font-bold text-slate-900 mb-0.5">{ob.disease_name} ({ob.state_or_country})</div>
                  <div><strong className="text-rose-900">Protocol:</strong> {ob.isolation_protocol}</div>
                  <div><strong className="text-rose-900">Confirmatory:</strong> {ob.confirmatory_test}</div>
                </div>
              ))}
            </div>
          </div>
        )}

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

                    {candidate.is_outbreak_match && (
                      <>
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
                        <span className="inline-flex items-center gap-1 font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-300 text-[10px] tracking-wide shadow-xs" title={candidate.outbreak_badge || "Live Outbreak Alert"}>
                          <ShieldAlert className="w-3 h-3 text-rose-600" />
                          {candidate.outbreak_badge || "Live Outbreak Alert"}
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
                          <span>Stat Tests: <strong>{candidate.immediate_tests.join(", ")}</strong></span>
                        </span>
                      )}
                      {(candidate.first_line_treatment || (candidate.recommended_medications && candidate.recommended_medications.length > 0)) && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold bg-emerald-50 text-emerald-800 px-2.5 py-0.5 rounded-lg border border-emerald-200 shadow-xs">
                          <ShieldCheck className="w-3 h-3 text-emerald-600" />
                          <span>First-Line Rx: <strong>{candidate.first_line_treatment || candidate.recommended_medications?.join(", ")}</strong></span>
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
                           <div className="font-extrabold text-purple-900 mb-1.5 flex items-center gap-1">
                             <FlaskConical className="w-3.5 h-3.5 text-purple-600" />
                             <span>Immediate / Confirmatory Tests ({candidate.immediate_tests.length}):</span>
                           </div>
                           <div className="flex flex-wrap gap-1.5">
                             {candidate.immediate_tests.map((t, tidx) => (
                               <span key={tidx} className="text-xs bg-white text-purple-950 px-2.5 py-1 rounded-lg border border-purple-200 shadow-2xs font-semibold">
                                 {t}
                               </span>
                             ))}
                           </div>
                         </div>
                       )}

                       {candidate.recommended_medications && candidate.recommended_medications.length > 0 && (
                         <div className="p-3 bg-emerald-50/80 rounded-xl border border-emerald-200/70 text-xs">
                           <div className="font-extrabold text-emerald-900 mb-1.5 flex items-center gap-1">
                             <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                             <span>Guideline Pharmacotherapy ({candidate.recommended_medications.length}):</span>
                           </div>
                           <div className="flex flex-wrap gap-1.5">
                             {candidate.recommended_medications.map((m, midx) => (
                               <span key={midx} className="text-xs bg-white text-emerald-950 px-2.5 py-1 rounded-lg border border-emerald-200 shadow-2xs font-semibold">
                                 {m}
                               </span>
                             ))}
                           </div>
                         </div>
                       )}
                       <Button 
                         variant={showInvestigationsFor === candidate.disease ? "primary" : "outline"}
                         onClick={(e) => {
                             e.stopPropagation();
                             setShowInvestigationsFor(showInvestigationsFor === candidate.disease ? null : candidate.disease);
                             setShowMedicationsFor(null);
                         }}
                         className="w-full justify-start rounded-xl font-semibold shadow-2xs h-10 gap-2 border-purple-200 text-purple-900 hover:bg-purple-50"
                       >
                         <FlaskConical className="w-4 h-4 text-purple-600" />
                         <span>{showInvestigationsFor === candidate.disease ? 'Hide' : 'View'} Investigations</span>
                       </Button>
                       <Button 
                         variant={showMedicationsFor === candidate.disease ? "primary" : "outline"}
                         onClick={(e) => {
                             e.stopPropagation();
                             setShowMedicationsFor(showMedicationsFor === candidate.disease ? null : candidate.disease);
                             setShowInvestigationsFor(null);
                         }}
                         className="w-full justify-start rounded-xl font-semibold shadow-2xs h-10 gap-2 border-emerald-200 text-emerald-900 hover:bg-emerald-50"
                       >
                         <Pill className="w-4 h-4 text-emerald-600" />
                         <span>{showMedicationsFor === candidate.disease ? 'Hide' : 'View'} Safe Medications</span>
                       </Button>
                       <Button 
                         variant={showInvestigationsFor === `${candidate.disease}_intel` ? "primary" : "outline"}
                         onClick={(e) => {
                             e.stopPropagation();
                             setShowInvestigationsFor(showInvestigationsFor === `${candidate.disease}_intel` ? null : `${candidate.disease}_intel`);
                             setShowMedicationsFor(null);
                         }}
                         className="w-full justify-start rounded-xl font-semibold shadow-2xs h-10 gap-2 border-indigo-200 text-indigo-900 bg-indigo-50/50 hover:bg-indigo-50"
                       >
                         <Brain className="w-4 h-4 text-indigo-600" />
                         <span>{showInvestigationsFor === `${candidate.disease}_intel` ? 'Hide' : 'View'} Disease Intelligence</span>
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
      </div>
    </div>
  );
}
