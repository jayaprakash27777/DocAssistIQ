"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { getStoredToken } from "@/lib/api";
import { Heart, Volume2, VolumeX, Eye, Share2, Sparkles, CheckCircle2, XCircle, ArrowLeft, ArrowRight, ShieldCheck, X } from "lucide-react";

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
  audio_type?: string | null;
  quiz_question?: string | null;
  quiz_options?: ReelQuizOption[];
  likes_count: number;
  comments_count: number;
  shares_count: number;
  is_liked?: boolean;
}

interface ClinicalReelsModalProps {
  reels?: ClinicalReel[];
  initialIndex?: number;
  onClose: () => void;
  onLikeReel?: (id: string) => void;
}

export function ClinicalReelsModal({
  reels: propReels,
  initialIndex = 0,
  onClose,
  onLikeReel,
}: ClinicalReelsModalProps) {
  const [reels, setReels] = useState<ClinicalReel[]>(propReels || []);
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [selectedQuizAnswer, setSelectedQuizAnswer] = useState<number | null>(null);
  const [showHeartPop, setShowHeartPop] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [filterMode, setFilterMode] = useState<"normal" | "invert" | "contrast">("normal");
  const [likedMap, setLikedMap] = useState<Record<string, boolean>>({});
  const [likesCountMap, setLikesCountMap] = useState<Record<string, number>>({});
  const [progress, setProgress] = useState(0);
  const [copiedLink, setCopiedLink] = useState(false);

  // Fetch real reels from backend if none passed or empty
  useEffect(() => {
    if (!propReels || propReels.length === 0) {
      const token = getStoredToken();
      fetch("/api/v1/hub/reels", {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
        .then((res) => (res.ok ? res.json() : []))
        .then((data: ClinicalReel[]) => {
          if (Array.isArray(data) && data.length > 0) {
            setReels(data);
            const initialLiked: Record<string, boolean> = {};
            const initialCounts: Record<string, number> = {};
            data.forEach((r) => {
              if (r.is_liked) initialLiked[r.id] = true;
              initialCounts[r.id] = r.likes_count;
            });
            setLikedMap(initialLiked);
            setLikesCountMap(initialCounts);
          }
        })
        .catch(() => {});
    } else {
      const initialLiked: Record<string, boolean> = {};
      const initialCounts: Record<string, number> = {};
      propReels.forEach((r) => {
        if (r.is_liked) initialLiked[r.id] = true;
        initialCounts[r.id] = r.likes_count;
      });
      setLikedMap(initialLiked);
      setLikesCountMap(initialCounts);
    }
  }, [propReels]);

  const activeReels = reels.length > 0 ? reels : [
    {
      id: "reel-live-1",
      title: "30-Second Rapid Spotter: Wellens' Syndrome",
      disease_name: "Wellens' Syndrome Type A",
      specialty: "Cardiology",
      author_name: "Dr. Sarah Chen, MD, FACC",
      author_credentials: "Board Certified Interventional Cardiologist",
      media_url: "https://images.unsplash.com/photo-1579684385127-1ef15d508118?auto=format&fit=crop&w=800&q=80",
      media_type: "ecg",
      clinical_pearl: "Biphasic T-waves in leads V2-V3 during a pain-free window indicate 90-99% proximal LAD occlusion. Stress testing is strictly contraindicated.",
      quiz_question: "What is the immediate, life-saving next clinical step?",
      quiz_options: [
        {
          label: "Emergent coronary catheterization & revascularization",
          is_correct: true,
          explanation: "Wellens is a pre-infarction state requiring urgent intervention before massive anterior wall necrosis.",
          peer_percentage: 92,
        },
        {
          label: "Treadmill stress test with Bruce protocol",
          is_correct: false,
          explanation: "STRICTLY CONTRAINDICATED. Precipitates fatal anterior STEMI.",
          peer_percentage: 4,
        },
        {
          label: "Discharge with high-dose proton pump inhibitor",
          is_correct: false,
          explanation: "High mortality error. Must not dismiss recent angina relief.",
          peer_percentage: 2,
        },
        {
          label: "Outpatient 48-hour ambulatory Holter monitoring",
          is_correct: false,
          explanation: "Unacceptable delay. Mean time to extensive anterior MI is 8.5 days.",
          peer_percentage: 2,
        },
      ],
      likes_count: 324,
      comments_count: 42,
      shares_count: 58,
    },
  ];

  const currentReel = activeReels[currentIndex] || activeReels[0];

  // Auto-progress progress bar
  useEffect(() => {
    setProgress(0);
    setSelectedQuizAnswer(null);
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          return 100;
        }
        return prev + 1;
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
    setTimeout(() => setShowHeartPop(false), 800);
    toggleLike();
  };

  const toggleLike = async () => {
    const isLiked = likedMap[currentReel.id];
    setLikedMap((prev) => ({ ...prev, [currentReel.id]: !isLiked }));
    setLikesCountMap((prev) => ({
      ...prev,
      [currentReel.id]: (prev[currentReel.id] ?? currentReel.likes_count) + (isLiked ? -1 : 1),
    }));

    if (onLikeReel) onLikeReel(currentReel.id);

    try {
      const token = getStoredToken();
      await fetch(`/api/v1/hub/reels/${currentReel.id}/like`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
    } catch {}
  };

  const handleShare = () => {
    navigator.clipboard?.writeText(window.location.href);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2500);
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
    <div className="fixed inset-0 z-[120] flex items-center justify-center p-3 sm:p-5 bg-slate-900/60 backdrop-blur-sm">
      {/* Close button */}
      <button
        type="button"
        onClick={onClose}
        className="absolute top-5 right-5 z-50 w-10 h-10 rounded-full bg-white/95 hover:bg-white text-slate-700 hover:text-slate-900 flex items-center justify-center text-sm font-bold shadow-md border border-slate-200 transition-all active:scale-95 cursor-pointer"
        title="Close Reel"
      >
        <X className="w-5 h-5" />
      </button>

      {/* Main Container Card - Clean light theme */}
      <div className="relative w-full max-w-[480px] h-[92vh] max-h-[820px] rounded-3xl overflow-hidden bg-white border border-slate-200/90 shadow-2xl flex flex-col">
        {/* Top Progress Segment Bar */}
        <div className="px-4 pt-3 pb-2 flex items-center gap-1.5 z-20 bg-white/90 backdrop-blur-sm">
          {activeReels.map((r, i) => (
            <div key={r.id || i} className="h-1 flex-1 bg-slate-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-teal-600 transition-all duration-100 ease-linear rounded-full"
                style={{
                  width: i < currentIndex ? "100%" : i === currentIndex ? `${progress}%` : "0%",
                }}
              />
            </div>
          ))}
        </div>

        {/* Doctor Header Bar */}
        <div className="px-4 py-2.5 flex items-center justify-between z-20 bg-white border-b border-slate-100">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-teal-600 to-emerald-500 text-white font-black text-xs flex items-center justify-center shrink-0 shadow-xs">
              {currentReel.author_name ? currentReel.author_name.replace(/Dr\.\s*/i, "")[0] : "D"}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1">
                <span className="font-extrabold text-xs text-slate-900 truncate">
                  {currentReel.author_name}
                </span>
                <ShieldCheck className="w-3.5 h-3.5 text-teal-600 shrink-0" />
              </div>
              <p className="text-[10px] text-slate-500 truncate">
                {currentReel.specialty} • Verified Doctor
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            {/* Filter Toggle */}
            <button
              type="button"
              onClick={() => {
                setFilterMode(filterMode === "normal" ? "invert" : filterMode === "invert" ? "contrast" : "normal");
              }}
              className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[10px] font-bold transition flex items-center gap-1 cursor-pointer"
              title="Change image filter (Normal / Contrast / Invert)"
            >
              <Eye className="w-3 h-3 text-teal-600" />
              <span className="capitalize">{filterMode}</span>
            </button>

            {/* Audio Toggle */}
            <button
              type="button"
              onClick={() => setIsPlayingAudio(!isPlayingAudio)}
              className={`p-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
                isPlayingAudio ? "bg-teal-600 text-white" : "bg-slate-100 hover:bg-slate-200 text-slate-700"
              }`}
              title="Listen to Heart / Lung sounds"
            >
              {isPlayingAudio ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>

        {/* Media Viewing Canvas */}
        <div
          onDoubleClick={handleDoubleTap}
          className="relative h-[280px] bg-slate-900 flex items-center justify-center overflow-hidden cursor-pointer select-none group"
        >
          <img
            src={currentReel.media_url}
            alt={currentReel.title}
            className={`w-full h-full object-cover transition-all duration-300 ${
              filterMode === "invert"
                ? "filter invert contrast-125"
                : filterMode === "contrast"
                ? "filter contrast-150 brightness-95"
                : ""
            }`}
          />

          {/* Vignette Overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20 pointer-events-none" />

          {/* Double Tap Heart Pop Animation */}
          <AnimatePresence>
            {showHeartPop && (
              <motion.div
                initial={{ opacity: 0, scale: 0.3 }}
                animate={{ opacity: 1, scale: 1.4 }}
                exit={{ opacity: 0, scale: 1.8 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="absolute text-7xl text-rose-500 pointer-events-none drop-shadow-2xl"
              >
                ❤️
              </motion.div>
            )}
          </AnimatePresence>

          {/* Disease Title Badge on Media */}
          <div className="absolute bottom-3 left-3 right-3 flex items-end justify-between pointer-events-none">
            <div className="bg-slate-900/80 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/20 text-white max-w-[80%]">
              <span className="text-[10px] font-black uppercase text-teal-300 tracking-wider block">
                {currentReel.specialty} Case
              </span>
              <h3 className="text-xs font-black truncate">{currentReel.disease_name}</h3>
            </div>

            {/* Media Type pill */}
            <span className="bg-white/90 backdrop-blur-md text-slate-800 text-[10px] font-extrabold px-2.5 py-1 rounded-lg uppercase shadow-xs">
              {currentReel.media_type || "Imaging"}
            </span>
          </div>
        </div>

        {/* Middle: Clinical Pearl & Audio Player Wave */}
        <div className="p-4 bg-teal-50/50 border-b border-teal-100/80 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-teal-700" />
              <span className="text-[10px] font-black uppercase tracking-wider text-teal-900">
                Key Medical Tip
              </span>
            </div>
            {isPlayingAudio && (
              <div className="flex items-center gap-0.5">
                {[1, 2, 3, 4, 5].map((n) => (
                  <span
                    key={n}
                    className="w-1 bg-teal-600 rounded-full animate-pulse"
                    style={{
                      height: `${6 + (n % 3) * 6}px`,
                      animationDelay: `${n * 120}ms`,
                    }}
                  />
                ))}
              </div>
            )}
          </div>
          <p className="text-xs text-teal-950 font-medium leading-relaxed">
            {currentReel.clinical_pearl}
          </p>
        </div>

        {/* Interactive Clinical Quiz (Pedagogical Engagement) */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2.5 no-scrollbar">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-black uppercase tracking-wider text-slate-700">
              {currentReel.quiz_question || "Quick Doctor Quiz:"}
            </span>
            <span className="text-[10px] font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded-md border border-teal-200">
              Doctor Quiz
            </span>
          </div>

          <div className="space-y-2">
            {(currentReel.quiz_options || []).map((opt, oIdx) => {
              const isSelected = selectedQuizAnswer === oIdx;
              const hasAnswered = selectedQuizAnswer !== null;

              let btnStyle = "bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-800";
              if (hasAnswered) {
                if (opt.is_correct) {
                  btnStyle = "bg-emerald-50 border-emerald-300 text-emerald-950 font-bold";
                } else if (isSelected) {
                  btnStyle = "bg-rose-50 border-rose-300 text-rose-950";
                } else {
                  btnStyle = "bg-slate-50/60 border-slate-100 text-slate-400";
                }
              }

              return (
                <button
                  key={oIdx}
                  type="button"
                  onClick={() => setSelectedQuizAnswer(oIdx)}
                  className={`w-full text-left p-3 rounded-xl border text-xs transition-all relative overflow-hidden cursor-pointer ${btnStyle}`}
                >
                  {/* Peer Percentage Fill Bar */}
                  {hasAnswered && (
                    <div
                      className={`absolute top-0 bottom-0 left-0 transition-all duration-500 opacity-20 ${
                        opt.is_correct ? "bg-emerald-500" : "bg-slate-400"
                      }`}
                      style={{ width: `${opt.peer_percentage}%` }}
                    />
                  )}

                  <div className="relative flex items-start justify-between gap-2">
                    <div className="flex items-start gap-2 min-w-0">
                      {hasAnswered && (
                        opt.is_correct ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        ) : isSelected ? (
                          <XCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                        ) : null
                      )}
                      <span className="leading-snug">{opt.label}</span>
                    </div>
                    {hasAnswered && (
                      <span className="font-mono text-[11px] font-black shrink-0">
                        {opt.peer_percentage}%
                      </span>
                    )}
                  </div>

                  {/* Rationale explanation reveal */}
                  {hasAnswered && isSelected && (
                    <p className="mt-1.5 text-[11px] font-normal leading-relaxed pt-1.5 border-t border-slate-200/60">
                      {opt.explanation}
                    </p>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Bottom Action Footer Bar */}
        <div className="p-3 bg-white border-t border-slate-200 flex items-center justify-between gap-3">
          {/* Previous / Next buttons */}
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={handlePrev}
              disabled={currentIndex === 0}
              className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 disabled:opacity-40 transition cursor-pointer"
              title="Previous Reel (Left Arrow)"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <span className="text-[11px] font-mono text-slate-500 font-bold px-1">
              {currentIndex + 1} / {activeReels.length}
            </span>
            <button
              type="button"
              onClick={handleNext}
              disabled={currentIndex === activeReels.length - 1}
              className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 disabled:opacity-40 transition cursor-pointer"
              title="Next Reel (Right Arrow)"
            >
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Social Interactions: Like & Share */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={toggleLike}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition shadow-xs cursor-pointer ${
                likedMap[currentReel.id]
                  ? "bg-rose-50 text-rose-700 border border-rose-200"
                  : "bg-slate-100 hover:bg-slate-200 text-slate-700"
              }`}
            >
              <Heart
                className={`w-4 h-4 ${
                  likedMap[currentReel.id] ? "fill-rose-600 text-rose-600" : "text-slate-500"
                }`}
              />
              <span>{likesCountMap[currentReel.id] ?? currentReel.likes_count}</span>
            </button>

            <button
              type="button"
              onClick={handleShare}
              className="flex items-center gap-1 px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition cursor-pointer"
              title="Share this case video"
            >
              <Share2 className="w-4 h-4 text-slate-500" />
              <span>{copiedLink ? "Copied!" : "Share"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
