/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import AudioVisualizer from "./AudioVisualizer";
import { Mic, Pause, Square, Loader2 } from "lucide-react";

interface LiveTranscriptionPanelProps {
  audioState: "idle" | "requesting_permission" | "recording" | "paused" | "stopping" | "processing" | "unavailable";
  audioStream: MediaStream | null;
  asrText: string;
  partialAsr: string;
  diarizedSegments: any[];
  onStart: () => void;
  onPause: () => void;
  onStop: () => void;
  elapsedMs: number;
}

const formatElapsed = (ms: number) => {
  const totalSeconds = Math.floor(ms / 1000);
  const m = Math.floor(totalSeconds / 60).toString().padStart(2, "0");
  const s = (totalSeconds % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
};

export default function LiveTranscriptionPanel({
  audioState,
  audioStream,
  asrText,
  partialAsr,
  diarizedSegments,
  onStart,
  onPause,
  onStop,
  elapsedMs,
}: LiveTranscriptionPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new text arrives
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [asrText, partialAsr, diarizedSegments]);

  const isRecording = audioState === "recording";
  const isPaused = audioState === "paused";
  const isProcessing = audioState === "processing";

  return (
    <div className="flex flex-col bg-white/70 backdrop-blur-xl border border-[var(--glass-border)] rounded-2xl shadow-lg overflow-hidden relative transition-all duration-500">
      
      {/* Header & Controls */}
      <div className="flex items-center justify-between p-4 bg-emerald-950/5 border-b border-[var(--glass-border)]">
        <div className="flex items-center gap-4 w-1/3">
          {audioState === "idle" || audioState === "unavailable" ? (
            <button
              onClick={onStart}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-full shadow-md transition-all active:scale-95"
            >
              <Mic className="w-4 h-4" /> Start Recording
            </button>
          ) : (
            <div className="flex items-center gap-2">
              {isRecording ? (
                <button
                  onClick={onPause}
                  className="p-2 bg-amber-100 hover:bg-amber-200 text-amber-700 rounded-full transition-all shadow-sm active:scale-95"
                  title="Pause Recording"
                >
                  <Pause className="w-5 h-5" />
                </button>
              ) : (
                <button
                  onClick={onStart}
                  disabled={isProcessing}
                  className="p-2 bg-emerald-100 hover:bg-emerald-200 text-emerald-700 rounded-full transition-all shadow-sm active:scale-95 disabled:opacity-50"
                  title="Resume Recording"
                >
                  <Mic className="w-5 h-5" />
                </button>
              )}
              <button
                onClick={onStop}
                disabled={isProcessing}
                className="p-2 bg-rose-100 hover:bg-rose-200 text-rose-700 rounded-full transition-all shadow-sm active:scale-95 disabled:opacity-50"
                title="Stop Recording"
              >
                <Square className="w-5 h-5" fill="currentColor" />
              </button>
            </div>
          )}
          
          <div className="font-mono text-sm text-emerald-800 bg-emerald-100/50 px-3 py-1 rounded-full border border-emerald-200/50">
            {formatElapsed(elapsedMs)}
          </div>
        </div>

        {/* Audio Visualizer Centered */}
        <div className="w-1/3 flex justify-center">
           <div className="w-48">
              <AudioVisualizer state={audioState} stream={audioStream} />
           </div>
        </div>
        
        {/* Status Indicator */}
        <div className="w-1/3 flex justify-end">
          {isRecording && (
            <span className="flex items-center gap-2 text-xs font-bold text-rose-600 tracking-wider animate-pulse">
              <div className="w-2 h-2 rounded-full bg-rose-500"></div> LIVE
            </span>
          )}
          {isPaused && (
            <span className="text-xs font-bold text-amber-600 tracking-wider">PAUSED</span>
          )}
          {isProcessing && (
            <span className="flex items-center gap-2 text-xs font-bold text-emerald-600 tracking-wider">
              <Loader2 className="w-4 h-4 animate-spin" /> PROCESSING
            </span>
          )}
        </div>
      </div>

      {/* Transcription Area */}
      <div 
        ref={scrollRef}
        className="p-6 h-[300px] overflow-y-auto scroll-smooth flex flex-col gap-4 relative"
      >
        {diarizedSegments.length === 0 && !asrText && !partialAsr && audioState !== 'idle' && (
          <div className="absolute inset-0 flex items-center justify-center text-emerald-900/30 font-medium italic">
            Listening for speech...
          </div>
        )}
        
        <AnimatePresence>
          {diarizedSegments.map((seg, idx) => (
            <motion.div 
              key={idx} 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white/60 p-4 rounded-xl border border-emerald-100 shadow-sm"
            >
              <div className="flex items-center gap-2 mb-2 text-xs font-semibold">
                <span className="text-emerald-800">{seg.speaker || "Unknown Speaker"}</span>
                <span className="text-emerald-900/40 font-mono">
                  {seg.start.toFixed(1)}s - {seg.end.toFixed(1)}s
                </span>
                {seg.confidence < 0.5 && (
                  <span className="bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full text-[10px]">
                    Low Confidence
                  </span>
                )}
              </div>
              <p className="text-gray-800 leading-relaxed text-sm md:text-base">
                {seg.text}
              </p>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Live / Partial Text Stream */}
        {(partialAsr || (asrText && diarizedSegments.length === 0)) && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="p-4"
          >
            {diarizedSegments.length === 0 && asrText && (
              <span className="text-gray-800 leading-relaxed text-sm md:text-base mr-1">
                {asrText}
              </span>
            )}
            {partialAsr && (
              <span className="text-emerald-700/60 italic leading-relaxed text-sm md:text-base transition-all duration-100">
                {partialAsr}
              </span>
            )}
            {isRecording && <span className="inline-block w-2 h-4 bg-emerald-400 ml-1 animate-pulse align-middle rounded-sm"></span>}
          </motion.div>
        )}
      </div>
    </div>
  );
}
