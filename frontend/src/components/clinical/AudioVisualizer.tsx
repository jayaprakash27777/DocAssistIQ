/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";

interface AudioVisualizerProps {
  state: "idle" | "requesting_permission" | "recording" | "paused" | "stopping" | "processing" | "unavailable";
  stream?: MediaStream | null;
}

export default function AudioVisualizer({ state, stream }: AudioVisualizerProps) {
  const [bars, setBars] = useState<number[]>(Array.from({ length: 30 }, () => 0.1));
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    // If not recording, flatten the bars
    if (state !== "recording") {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      setBars(Array.from({ length: 30 }, () => 0.1));
      return;
    }

    // Initialize Web Audio API to process the actual stream
    if (stream && !audioContextRef.current) {
      try {
        const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
        const ctx = new AudioContext();
        audioContextRef.current = ctx;

        const analyser = ctx.createAnalyser();
        analyser.fftSize = 64; // 32 frequency bins
        analyser.smoothingTimeConstant = 0.8;
        analyserRef.current = analyser;

        const source = ctx.createMediaStreamSource(stream);
        source.connect(analyser);
        sourceRef.current = source;
      } catch (err) {
        console.warn("Failed to initialize AudioContext for visualizer:", err);
      }
    }

    const updateBars = () => {
      if (!analyserRef.current) {
        // Fallback to random if Web Audio API failed
        setBars((prev) => prev.map(() => 0.2 + Math.random() * 0.8));
        animationFrameRef.current = requestAnimationFrame(updateBars);
        return;
      }

      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      analyserRef.current.getByteFrequencyData(dataArray);

      // Slice to get the first 30 bins and normalize to 0.1 - 1.0
      const newBars = Array.from(dataArray).slice(0, 30).map(val => Math.max(0.1, val / 255));
      setBars(newBars);

      animationFrameRef.current = requestAnimationFrame(updateBars);
    };

    if (state === "recording") {
      updateBars();
    }

    return () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, [state, stream]);

  // Cleanup AudioContext on unmount
  useEffect(() => {
    return () => {
      if (audioContextRef.current && audioContextRef.current.state !== "closed") {
        audioContextRef.current.close().catch(console.error);
        audioContextRef.current = null;
      }
    };
  }, []);

  const isActive = state === "recording";

  return (
    <div className="flex items-center justify-center gap-[2px] h-12 w-full px-4 overflow-hidden rounded-lg bg-emerald-950/5 border border-emerald-900/10 shadow-inner relative">
      {/* Subtle glow effect behind bars */}
      {isActive && (
         <div className="absolute inset-0 bg-emerald-400/10 blur-xl pointer-events-none" />
      )}
      {bars.map((height, i) => (
        <motion.div
          key={i}
          animate={{ height: `${height * 100}%`, opacity: isActive ? 1 : 0.4 }}
          transition={{
            type: "tween",
            duration: 0.05,
            ease: "linear",
          }}
          className={`w-1.5 rounded-full ${isActive ? 'bg-emerald-500' : 'bg-emerald-700/30'}`}
          style={{
            boxShadow: isActive ? "0 0 8px rgba(16, 185, 129, 0.4)" : "none",
          }}
        />
      ))}
    </div>
  );
}
