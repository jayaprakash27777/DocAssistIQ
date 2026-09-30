/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * DocAssistIQ — Audio Capture Hook (Phase 24).
 *
 * Manages microphone lifecycle: permission, recording, pausing, stopping, and cleanup.
 * Handles device failure and device changes.
 */

import { useState, useRef, useCallback, useEffect } from "react";
import { getSharedRealtimeClient } from "@/lib/ws";
import { getStoredToken } from "@/lib/api";

export type AudioCaptureState = 
  | "idle" 
  | "requesting_permission" 
  | "recording" 
  | "paused" 
  | "stopping" 
  | "processing" 
  | "unavailable";

export function useAudioCapture() {
  const [state, setState] = useState<AudioCaptureState>("idle");
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [isSilent, setIsSilent] = useState<boolean>(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);
  const pauseTimeRef = useRef<number>(0); // Timestamp when paused
  const accumulatedMsRef = useRef<number>(0); // Total ms before current resume

  // Web Audio API refs for real-time volume metering
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const silentSinceRef = useRef<number | null>(null);

  const stopAudioMeter = useCallback(() => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    analyserRef.current = null;
    silentSinceRef.current = null;
    setAudioLevel(0);
    setIsSilent(false);
  }, []);

  const startAudioMeter = useCallback((mediaStream: MediaStream) => {
    stopAudioMeter();
    if (typeof window === "undefined") return;

    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;

      const audioCtx = new AudioCtx();
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.5;

      const source = audioCtx.createMediaStreamSource(mediaStream);
      source.connect(analyser);

      audioContextRef.current = audioCtx;
      analyserRef.current = analyser;

      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      const loop = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);

        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;
        // Non-linear sensitivity curve tailored to human vocal speech (0-100)
        const normalized = Math.min(100, Math.round((avg / 120) * 100));
        setAudioLevel(normalized);

        // Dead-air detection: if level < 3 for over 3.5 seconds
        if (normalized < 3) {
          if (!silentSinceRef.current) {
            silentSinceRef.current = Date.now();
          } else if (Date.now() - silentSinceRef.current > 3500) {
            setIsSilent(true);
          }
        } else {
          silentSinceRef.current = null;
          setIsSilent(false);
        }

        animFrameRef.current = requestAnimationFrame(loop);
      };

      animFrameRef.current = requestAnimationFrame(loop);
    } catch (e) {
      console.warn("Audio meter setup skipped or unsupported:", e);
    }
  }, [stopAudioMeter]);

  const stop = useCallback(() => {
    if (mediaRecorderRef.current?.state !== "inactive") {
      setState("stopping");
      mediaRecorderRef.current?.stop();
    }
    stopAudioMeter();
  }, [stopAudioMeter]);

  // Cleanup function to release the microphone
  const releaseMicrophone = useCallback(() => {
    stopAudioMeter();
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      setStream(null);
    }
  }, [stopAudioMeter]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      releaseMicrophone();
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [releaseMicrophone]);

  // Handle device change or removal
  useEffect(() => {
    const handleDeviceChange = async () => {
      if (state === "recording" || state === "paused") {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const hasMic = devices.some((d) => d.kind === "audioinput");
        if (!hasMic) {
          setError("Microphone disconnected during recording.");
          stop(); // Force stop
        }
      }
    };
    if (typeof navigator !== "undefined" && navigator.mediaDevices?.addEventListener) {
      navigator.mediaDevices.addEventListener("devicechange", handleDeviceChange);
      return () => navigator.mediaDevices?.removeEventListener("devicechange", handleDeviceChange);
    }
  }, [state, stop]);

  const updateTimer = useCallback(() => {
    const now = Date.now();
    const elapsed = accumulatedMsRef.current + (now - startTimeRef.current);
    setElapsedMs(elapsed);
  }, []);

  const start = useCallback(async () => {
    try {
      setState("requesting_permission");
      setError(null);
      
      const streamObj = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = streamObj;
      setStream(streamObj);

      // Start real-time Web Audio API frequency visualizer
      startAudioMeter(streamObj);

      // Handle track ending externally (e.g. user revokes permission in browser)
      streamObj.getTracks().forEach(track => {
        track.onended = () => {
          if (mediaRecorderRef.current?.state !== "inactive") {
            setError("Microphone access lost.");
            stop();
          }
        };
      });

      let mimeType = "audio/webm";
      if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
        mimeType = "audio/webm;codecs=opus";
      } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
        mimeType = "audio/mp4"; // Safari fallback
      }

      const recorder = new MediaRecorder(streamObj, { mimeType });
      mediaRecorderRef.current = recorder;

      recorder.onstart = () => {
        setState("recording");
        accumulatedMsRef.current = 0;
        startTimeRef.current = Date.now();
        setElapsedMs(0);
        timerRef.current = setInterval(updateTimer, 1000);
      };

      recorder.onpause = () => {
        setState("paused");
        if (timerRef.current) clearInterval(timerRef.current);
        accumulatedMsRef.current += Date.now() - startTimeRef.current;
        pauseTimeRef.current = Date.now();
        setAudioLevel(0);
      };

      recorder.onresume = () => {
        setState("recording");
        startTimeRef.current = Date.now();
        timerRef.current = setInterval(updateTimer, 1000);
        if (streamRef.current) {
          startAudioMeter(streamRef.current);
        }
      };

      recorder.onerror = (e: Event) => {
        console.error("MediaRecorder error", e);
        setError("An error occurred with the recording device.");
        stop();
      };

      const token = getStoredToken();
      const wsClient = token ? getSharedRealtimeClient(token) : null;

      // Stream audio chunks via WebSocket
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0 && wsClient) {
          try {
            const reader = new FileReader();
            reader.onloadend = () => {
              if (reader.result) {
                const base64data = (reader.result as string).split(',')[1];
                wsClient.send("audio_chunk", { data: base64data });
              }
            };
            reader.readAsDataURL(e.data);
          } catch (err) {
            console.error("Failed to process audio chunk", err);
          }
        }
      };

      recorder.onstop = () => {
        if (timerRef.current) clearInterval(timerRef.current);
        releaseMicrophone();
        if (wsClient) {
          wsClient.send("audio_stop", {});
        }
        setState("processing"); // App logic takes over
      };

      // Start recording with timeslice (2000ms)
      recorder.start(2000); 
      
    } catch (err: any) {
      console.error("Audio capture error:", err);
      setState("unavailable");
      if (err.name === "NotAllowedError" || err.name === "SecurityError") {
        setError("Microphone access denied. Please allow microphone access in your browser.");
      } else if (err.name === "NotFoundError") {
        setError("No microphone found.");
      } else {
        setError("Failed to access microphone.");
      }
    }
  }, [releaseMicrophone, updateTimer, stop, startAudioMeter]);

  const pause = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.pause();
    }
  }, []);

  const resume = useCallback(() => {
    if (mediaRecorderRef.current?.state === "paused") {
      mediaRecorderRef.current.resume();
    }
  }, []);

  const reset = useCallback(() => {
    stopAudioMeter();
    setState("idle");
    setElapsedMs(0);
    setError(null);
    accumulatedMsRef.current = 0;
  }, [stopAudioMeter]);

  return {
    state,
    elapsedMs,
    error,
    audioLevel,
    isSilent,
    start,
    pause,
    resume,
    stop,
    reset,
    stream,
  };
}

export function formatElapsed(ms: number) {
  const totalSeconds = Math.floor(ms / 1000);
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}
