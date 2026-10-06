"use client";

import React, { useRef } from "react";
import { Plus, ChevronLeft, ChevronRight, Sparkles, AlertCircle } from "lucide-react";
import { ClinicalReel } from "./ClinicalReelsModal";

interface ClinicalStoriesTrayProps {
  reels: ClinicalReel[];
  onSelectReel: (index: number) => void;
  onOpenComposer: () => void;
}

export function ClinicalStoriesTray({
  reels,
  onSelectReel,
  onOpenComposer,
}: ClinicalStoriesTrayProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const scrollLeft = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({ left: -240, behavior: "smooth" });
    }
  };

  const scrollRight = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({ left: 240, behavior: "smooth" });
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 p-3.5 shadow-xs relative group/tray">
      {/* Header bar */}
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
          <h2 className="text-xs font-black uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
            <span>Doctor Stories & Case Videos</span>
            <span className="text-[10px] font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full border border-teal-200">
              Quick Pearls
            </span>
          </h2>
        </div>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={scrollLeft}
            className="w-6 h-6 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-600 flex items-center justify-center transition cursor-pointer"
            title="Scroll left"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={scrollRight}
            className="w-6 h-6 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-600 flex items-center justify-center transition cursor-pointer"
            title="Scroll right"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Stories horizontal carousel */}
      <div
        ref={scrollContainerRef}
        className="flex items-center gap-3 overflow-x-auto no-scrollbar scroll-smooth pb-1 px-1"
      >
        {/* Item 0: Share Story / Spotter Reel */}
        <button
          type="button"
          onClick={onOpenComposer}
          className="flex flex-col items-center gap-1.5 shrink-0 w-[72px] group cursor-pointer focus:outline-none"
        >
          <div className="relative">
            <div className="w-14 h-14 rounded-full border-2 border-dashed border-teal-400 p-0.5 group-hover:border-teal-600 transition-all flex items-center justify-center bg-teal-50/60">
              <div className="w-full h-full rounded-full bg-white flex items-center justify-center shadow-xs">
                <Plus className="w-5 h-5 text-teal-600 group-hover:scale-110 transition-transform" />
              </div>
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full bg-teal-600 text-white flex items-center justify-center text-[10px] font-black border-2 border-white shadow-xs">
              +
            </div>
          </div>
          <span className="text-[11px] font-bold text-slate-700 group-hover:text-teal-700 transition truncate max-w-full">
            Share Story
          </span>
        </button>

        {/* Stories List */}
        {reels.map((reel, idx) => {
          const isEmergency =
            reel.disease_name.toLowerCase().includes("wellens") ||
            reel.disease_name.toLowerCase().includes("dengue") ||
            reel.disease_name.toLowerCase().includes("ten") ||
            reel.disease_name.toLowerCase().includes("stat") ||
            reel.disease_name.toLowerCase().includes("urgent");

          const ringGradient = isEmergency
            ? "from-rose-500 via-amber-500 to-red-500"
            : "from-teal-500 via-emerald-400 to-cyan-500";

          // Short author name
          const shortName = reel.author_name
            ? reel.author_name.replace(/^(Dr\.\s*)/i, "Dr. ").split(",")[0]
            : "Dr. Peer";

          return (
            <button
              key={reel.id || idx}
              type="button"
              onClick={() => onSelectReel(idx)}
              className="flex flex-col items-center gap-1.5 shrink-0 w-[74px] group cursor-pointer focus:outline-none"
            >
              <div className="relative">
                {/* Gradient Ring (Instagram style) */}
                <div
                  className={`w-14 h-14 rounded-full p-[2.5px] bg-gradient-to-tr ${ringGradient} shadow-xs group-hover:scale-105 transition-transform duration-200`}
                >
                  <div className="w-full h-full rounded-full overflow-hidden bg-white p-[1.5px]">
                    <img
                      src={reel.media_url}
                      alt={reel.title}
                      className="w-full h-full object-cover rounded-full"
                    />
                  </div>
                </div>

                {/* Priority / Specialty micro-pill badge */}
                {isEmergency ? (
                  <span
                    className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-rose-600 text-white flex items-center justify-center text-[9px] font-black border-2 border-white shadow-xs animate-pulse"
                    title="STAT Case"
                  >
                    !
                  </span>
                ) : (
                  <span
                    className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-teal-600 text-white flex items-center justify-center text-[8px] font-black border-2 border-white shadow-xs"
                    title="Verified Specialist"
                  >
                    ✓
                  </span>
                )}
              </div>

              {/* Story text */}
              <div className="text-center w-full px-0.5">
                <p className="text-[11px] font-bold text-slate-800 truncate group-hover:text-teal-700 transition">
                  {shortName}
                </p>
                <p className="text-[9px] font-medium text-slate-400 truncate mt-0.5">
                  {reel.specialty || "Specialist"}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
