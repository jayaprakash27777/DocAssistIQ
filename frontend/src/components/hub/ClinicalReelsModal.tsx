"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

export interface ReelQuizOption {
  label: string;
  is_correct: boolean;
  explanation: string;
  peer_percentage: number;
}

export interface ClinicalReel {
  id: string;
  title: string;
  disease_name: string;
  specialty: string;
  author_name: string;
  author_credentials: string;
  media_url: string;
  media_type: string;
  clinical_pearl: string;
  audio_type?: string;
  quiz_question?: string;
  quiz_options?: ReelQuizOption[];
  likes_count: number;
  comments_count: number;
  shares_count: number;
  is_liked?: boolean;
}

interface ClinicalReelsModalProps {
  reels: ClinicalReel[];
  initialIndex?: number;
  onClose: () => void;
  onLikeReel?: (id: string) => void;
  isNightMode?: boolean;
}

export function ClinicalReelsModal({
  reels,
  initialIndex = 0,
  onClose,
  onLikeReel,
  isNightMode = false,
}: ClinicalReelsModalProps) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [selectedQuizAnswer, setSelectedQuizAnswer] = useState<number | null>(null);
  const [showHeartPop, setShowHeartPop] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [filterMode, setFilterMode] = useState<"normal" | "invert" | "bone">("normal");
  const [likedMap, setLikedMap] = useState<Record<string, boolean>>({});
  const [likesCountMap, setLikesCountMap] = useState<Record<string, number>>({});
  const [progress, setProgress] = useState(0);

  // Fallback demo reels if none provided
  const activeReels: ClinicalReel[] = reels?.length
    ? reels
    : [
        {
          id: "reel-1",
          title: "30-Second Rapid Spotter: The Biphasic T-Wave Trap",
          disease_name: "Wellens' Syndrome Type A",
          specialty: "Cardiology",
          author_name: "Dr. Sarah Chen, MD, FACC",
          author_credentials: "Board Certified Interventional Cardiologist",
          media_url:
            "https://images.unsplash.com/photo-1579684385127-1ef15d508118?auto=format&fit=crop&w=800&q=80",
          media_type: "ecg",
          clinical_pearl:
            "Never send this patient to a treadmill stress test. Biphasic T-waves in V2-V3 during a pain-free window signal 90-99% proximal LAD occlusion.",
          audio_type: "s4_gallop",
          quiz_question: "What is the immediate, life-saving next step for this pain-free patient?",
          quiz_options: [
            {
              label: "Emergent coronary angiography (< 24 hrs)",
              is_correct: true,
              explanation:
                "Correct! Wellens is a pre-infarction state requiring urgent revascularization before extensive anterior wall necrosis occurs.",
              peer_percentage: 92,
            },
            {
              label: "Treadmill Bruce protocol stress test",
              is_correct: false,
              explanation:
                "STRICTLY CONTRAINDICATED. Stressing an ischemic proximal LAD triggers sudden anterior STEMI or ventricular fibrillation.",
              peer_percentage: 4,
            },
            {
              label: "Discharge with oral PPI for suspected GERD",
              is_correct: false,
              explanation:
                "High mortality error. Biphasic T-waves must never be dismissed when angina symptoms recently resolved.",
              peer_percentage: 1,
            },
            {
              label: "Outpatient 48-hour Holter monitor",
              is_correct: false,
              explanation:
                "Unacceptable delay. Mean time to extensive anterior MI in untreated Wellens is approximately 8.5 days.",
              peer_percentage: 3,
            },
          ],
          likes_count: 284,
          comments_count: 39,
          shares_count: 67,
        },
        {
          id: "reel-2",
          title: "Diagnostic Spotter: Extreme Delta Brush in ICU Catatonia",
          disease_name: "Anti-NMDA Receptor Encephalitis",
          specialty: "Neurology",
          author_name: "Dr. David Vance, MD, FAAN",
          author_credentials: "Neurointensivist & Autoimmune Fellow",
          media_url:
            "https://images.unsplash.com/photo-1559757175-5700dde675bc?auto=format&fit=crop&w=800&q=80",
          media_type: "eeg",
          clinical_pearl:
            "Extreme delta brush pattern consists of rhythmic 1-3 Hz delta waves with superimposed fast beta activity (20-30 Hz). Pathognomonic for Anti-NMDA receptor encephalitis.",
          audio_type: "voice_summary",
          quiz_question:
            "Which occult neoplastic pathology must be immediately screened for in young females with this presentation?",
          quiz_options: [
            {
              label: "Ovarian Teratoma",
              is_correct: true,
              explanation:
                "Correct! Over 40-50% of young female patients have an occult mature/immature ovarian teratoma expressing neural NMDA receptors.",
              peer_percentage: 88,
            },
            {
              label: "Small Cell Lung Cancer",
              is_correct: false,
              explanation:
                "SCLC typically associates with Lambert-Eaton or Anti-Hu limbic encephalitis in older smokers.",
              peer_percentage: 6,
            },
            {
              label: "Thymoma",
              is_correct: false,
              explanation:
                "Thymomas are classically associated with Myasthenia Gravis, not Anti-NMDA encephalitis.",
              peer_percentage: 4,
            },
          ],
          likes_count: 315,
          comments_count: 48,
          shares_count: 82,
        },
        {
          id: "reel-3",
          title: "Pediatric Bedside Pearl: Strawberry Tongue & Coronary Ectasia",
          disease_name: "Kawasaki Disease",
          specialty: "Pediatrics",
          author_name: "Dr. Elena Rostova, MD, PhD",
          author_credentials: "Consultant Pediatric Infectious Diseases",
          media_url:
            "https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?auto=format&fit=crop&w=800&q=80",
          media_type: "clinical_photo",
          clinical_pearl:
            "Administer IVIG (2g/kg) strictly within 10 days of fever onset to slash coronary artery aneurysm risk from 25% down to under 3-5%.",
          audio_type: "murmur_aortic",
          quiz_question:
            "What is the primary anti-inflammatory regimen indicated in acute Kawasaki disease?",
          quiz_options: [
            {
              label: "Single dose IVIG (2 g/kg) + High-Dose Aspirin (80-100 mg/kg/day)",
              is_correct: true,
              explanation: "Class I, Level A AHA Guideline standard for reducing acute coronary arteritis.",
              peer_percentage: 94,
            },
            {
              label: "Oral Amoxicillin/Clavulanate for 10 days",
              is_correct: false,
              explanation: "Ineffective; Kawasaki is an immune vasculitis, not a bacterial infection.",
              peer_percentage: 1,
            },
            {
              label: "Ibuprofen 10 mg/kg three times daily",
              is_correct: false,
              explanation: "Avoid NSAIDs like Ibuprofen during aspirin therapy because they compete with Aspirin.",
              peer_percentage: 3,
            },
          ],
          likes_count: 420,
          comments_count: 52,
          shares_count: 110,
        },
      ];

  const currentReel = activeReels[currentIndex] || activeReels[0];

  // Auto-progress timer
  useEffect(() => {
    setProgress(0);
    setSelectedQuizAnswer(null);
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          return 100;
        }
        return prev + 1.25;
      });
    }, 150);

    return () => clearInterval(interval);
  }, [currentIndex]);

  const handleNext = () => {
    if (currentIndex < activeReels.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  const handleDoubleTap = () => {
    setShowHeartPop(true);
    setTimeout(() => setShowHeartPop(false), 900);
    toggleLike();
  };

  const toggleLike = () => {
    const isLiked = likedMap[currentReel.id];
    setLikedMap((prev) => ({ ...prev, [currentReel.id]: !isLiked }));
    setLikesCountMap((prev) => ({
      ...prev,
      [currentReel.id]: (prev[currentReel.id] ?? currentReel.likes_count) + (isLiked ? -1 : 1),
    }));
    if (onLikeReel) onLikeReel(currentReel.id);
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowDown" || e.key === "ArrowRight") handleNext();
      else if (e.key === "ArrowUp" || e.key === "ArrowLeft") handlePrev();
      else if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentIndex, activeReels.length]);

  return (
    <div className="fixed inset-0 z-[115] flex items-center justify-center p-2 sm:p-4 bg-slate-950/85 backdrop-blur-md">
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-5 right-5 z-40 w-10 h-10 rounded-full bg-slate-900/80 hover:bg-slate-800 text-white flex items-center justify-center text-lg font-bold border border-slate-700 transition-transform active:scale-95 cursor-pointer shadow-lg"
      >
        ✕
      </button>

      <div className="relative w-full max-w-[460px] h-[92vh] max-h-[820px] rounded-3xl overflow-hidden bg-slate-900 border border-slate-800 shadow-2xl flex flex-col">
        {/* Top Progress Segment Bar (Instagram Stories/Reels Style) */}
        <div className="absolute top-3 left-3 right-3 z-30 flex items-center gap-1.5">
          {activeReels.map((r, i) => (
            <div key={r.id} className="h-1 flex-1 bg-white/20 rounded-full overflow-hidden">
              <div
                className="h-full bg-teal-400 transition-all duration-100 ease-linear rounded-full"
                style={{
                  width: i < currentIndex ? "100%" : i === currentIndex ? `${progress}%` : "0%",
                }}
              />
            </div>
          ))}
        </div>

        {/* Media Canvas & Double-Tap Area */}
        <div
          onDoubleClick={handleDoubleTap}
          className="relative flex-1 bg-slate-950 overflow-hidden flex items-center justify-center cursor-pointer select-none group"
        >
          <img
            src={currentReel.media_url}
            alt={currentReel.title}
            className={`w-full h-full object-cover transition-all duration-300 ${
              filterMode === "invert"
                ? "filter invert contrast-125"
                : filterMode === "bone"
                ? "filter grayscale contrast-200 brightness-90"
                : ""
            }`}
          />

          {/* Vignette overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/30 to-slate-950/60 pointer-events-none" />

          {/* Animated Heart Pop on Double Tap */}
          <AnimatePresence>
            {showHeartPop && (
              <motion.div
                initial={{ opacity: 0, scale: 0.3 }}
                animate={{ opacity: 1, scale: 1.4 }}
                exit={{ opacity: 0, scale: 2 }}
                transition={{ duration: 0.6, ease: "easeOut" }}
                className="absolute text-7xl text-rose-500 pointer-events-none drop-shadow-2xl"
              >
                ❤️
              </motion.div>
            )}
          </AnimatePresence>

          {/* Top-Right DICOM Filter Presets Tool */}
          <div className="absolute top-8 right-3 z-20 flex flex-col gap-1.5">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setFilterMode(filterMode === "normal" ? "invert" : filterMode === "invert" ? "bone" : "normal");
              }}
              className="px-2.5 py-1 rounded-full bg-slate-900/80 backdrop-blur-md border border-slate-700 text-white text-[10px] font-bold flex items-center gap-1.5 hover:bg-slate-800 transition-colors shadow-md"
              title="Toggle DICOM Film Inversion"
            >
              <span>🔬</span>
              <span>{filterMode === "normal" ? "Normal" : filterMode === "invert" ? "Inverted" : "Bone"}</span>
            </button>

            {/* Auscultation / Voice toggle */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsPlayingAudio(!isPlayingAudio);
              }}
              className={`px-2.5 py-1 rounded-full backdrop-blur-md border text-[10px] font-bold flex items-center gap-1.5 transition-colors shadow-md ${
                isPlayingAudio
                  ? "bg-teal-600 text-white border-teal-500 ring-2 ring-teal-400"
                  : "bg-slate-900/80 border-slate-700 text-white hover:bg-slate-800"
              }`}
            >
              <span>{isPlayingAudio ? "🔊" : "🔈"}</span>
              <span>{isPlayingAudio ? "Playing" : "Sound"}</span>
            </button>
          </div>

          {/* Side Action Buttons Rail (Instagram Style) */}
          <div className="absolute right-3 bottom-24 z-20 flex flex-col items-center gap-4">
            {/* Like button */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleLike();
              }}
              className="flex flex-col items-center gap-1 group cursor-pointer"
            >
              <div
                className={`w-11 h-11 rounded-full flex items-center justify-center text-xl transition-all shadow-lg ${
                  likedMap[currentReel.id]
                    ? "bg-rose-600 text-white scale-110"
                    : "bg-slate-900/80 backdrop-blur-md text-white border border-slate-700 group-hover:bg-slate-800"
                }`}
              >
                {likedMap[currentReel.id] ? "❤️" : "🤍"}
              </div>
              <span className="text-[10px] font-bold text-white shadow-xs">
                {likesCountMap[currentReel.id] ?? currentReel.likes_count}
              </span>
            </button>

            {/* Comments button */}
            <button
              onClick={(e) => {
                e.stopPropagation();
              }}
              className="flex flex-col items-center gap-1 group cursor-pointer"
            >
              <div className="w-11 h-11 rounded-full bg-slate-900/80 backdrop-blur-md text-white border border-slate-700 flex items-center justify-center text-xl group-hover:bg-slate-800 transition-all shadow-lg">
                💬
              </div>
              <span className="text-[10px] font-bold text-white shadow-xs">
                {currentReel.comments_count}
              </span>
            </button>

            {/* Share / Consult button */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                navigator.clipboard?.writeText(window.location.href);
              }}
              className="flex flex-col items-center gap-1 group cursor-pointer"
              title="Share Clinical Reel"
            >
              <div className="w-11 h-11 rounded-full bg-slate-900/80 backdrop-blur-md text-white border border-slate-700 flex items-center justify-center text-xl group-hover:bg-slate-800 transition-all shadow-lg">
                ↗️
              </div>
              <span className="text-[10px] font-bold text-white shadow-xs">
                {currentReel.shares_count}
              </span>
            </button>
          </div>

          {/* Up / Down Navigation Chevrons */}
          <div className="absolute left-3 bottom-24 z-20 flex flex-col gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handlePrev();
              }}
              disabled={currentIndex === 0}
              className="w-9 h-9 rounded-full bg-slate-900/80 backdrop-blur-md border border-slate-700 text-white disabled:opacity-30 flex items-center justify-center text-xs font-bold hover:bg-slate-800 transition-colors cursor-pointer"
            >
              ▲
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleNext();
              }}
              disabled={currentIndex === activeReels.length - 1}
              className="w-9 h-9 rounded-full bg-slate-900/80 backdrop-blur-md border border-slate-700 text-white disabled:opacity-30 flex items-center justify-center text-xs font-bold hover:bg-slate-800 transition-colors cursor-pointer"
            >
              ▼
            </button>
          </div>
        </div>

        {/* Bottom Educational Drawer & Diagnostic Quiz */}
        <div className="bg-slate-900/95 border-t border-slate-800 p-4 z-20 space-y-2.5 max-h-[46%] overflow-y-auto custom-scrollbar">
          {/* Doctor Header */}
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-teal-500 to-emerald-400 text-white flex items-center justify-center text-xs font-black shadow-sm">
              {currentReel.author_name[4] || "D"}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5">
                <p className="text-xs font-bold text-white truncate">{currentReel.author_name}</p>
                <span className="text-[10px] text-teal-400">✓</span>
              </div>
              <p className="text-[10px] text-slate-400 truncate">{currentReel.author_credentials}</p>
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-teal-950 text-teal-300 border border-teal-800">
              {currentReel.specialty}
            </span>
          </div>

          {/* Reel Title & Clinical Pearl */}
          <div>
            <h3 className="text-xs font-black text-white">{currentReel.title}</h3>
            <p className="text-[11px] text-slate-300 leading-relaxed mt-0.5">
              💡 <span className="font-semibold text-teal-300">Pearl:</span> {currentReel.clinical_pearl}
            </p>
          </div>

          {/* Interactive Diagnostic Quiz Challenge */}
          {currentReel.quiz_question && currentReel.quiz_options && (
            <div className="pt-2 border-t border-slate-800/80">
              <p className="text-[11px] font-black text-amber-400 flex items-center gap-1 mb-2">
                <span>🎯 Rapid Diagnostic Challenge:</span>
              </p>
              <p className="text-xs font-bold text-white mb-2">{currentReel.quiz_question}</p>

              <div className="space-y-1.5">
                {currentReel.quiz_options.map((opt, optIdx) => {
                  const isAnswered = selectedQuizAnswer !== null;
                  const isThisSelected = selectedQuizAnswer === optIdx;
                  return (
                    <button
                      key={optIdx}
                      disabled={isAnswered}
                      onClick={() => setSelectedQuizAnswer(optIdx)}
                      className={`w-full text-left p-2 rounded-xl border text-xs font-medium transition-all flex items-center justify-between cursor-pointer ${
                        !isAnswered
                          ? "bg-slate-800/90 hover:bg-slate-800 border-slate-700 text-slate-200"
                          : opt.is_correct
                          ? "bg-emerald-950/80 border-emerald-500 text-emerald-200 ring-1 ring-emerald-400"
                          : isThisSelected
                          ? "bg-rose-950/80 border-rose-500 text-rose-200"
                          : "bg-slate-800/50 border-slate-800 text-slate-400 opacity-60"
                      }`}
                    >
                      <span className="min-w-0 pr-2 leading-tight">{opt.label}</span>
                      {isAnswered && (
                        <span className="font-mono text-[10px] font-bold text-teal-400 flex-shrink-0">
                          {opt.peer_percentage}%
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>

              {/* Rationale explanation if answered */}
              {selectedQuizAnswer !== null && (
                <motion.div
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-2.5 p-2.5 rounded-xl bg-teal-950/50 border border-teal-800/80 text-[11px] text-teal-200 leading-relaxed"
                >
                  <strong className="text-white">Clinical Rationale: </strong>
                  {currentReel.quiz_options[selectedQuizAnswer]?.explanation}
                </motion.div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
