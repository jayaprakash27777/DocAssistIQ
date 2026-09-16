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

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);
  const pauseTimeRef = useRef<number>(0); // Timestamp when paused
  const accumulatedMsRef = useRef<number>(0); // Total ms before current resume
const stop = useCallback(() => {
    if (mediaRecorderRef.current?.state !== "inactive") {
      setState("stopping");
      mediaRecorderRef.current?.stop();
    }
  }, []);

  // Cleanup function to release the microphone
  const releaseMicrophone = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      setStream(null);
    }
  }, []);

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
        // Simple device change check; a real app might attempt to re-acquire the exact stream
        const devices = await navigator.mediaDevices.enumerateDevices();
        const hasMic = devices.some((d) => d.kind === "audioinput");
        if (!hasMic) {
          setError("Microphone disconnected during recording.");
          stop(); // Force stop
        }
      }
    };
    navigator.mediaDevices.addEventListener("devicechange", handleDeviceChange);
    return () => navigator.mediaDevices.removeEventListener("devicechange", handleDeviceChange);
  }, [state]);

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
      };

      recorder.onresume = () => {
        setState("recording");
        startTimeRef.current = Date.now();
        timerRef.current = setInterval(updateTimer, 1000);
      };

      recorder.onerror = (e: Event) => {
        console.error("MediaRecorder error", e);
        setError("An error occurred with the recording device.");
        stop();
      };

      const token = getStoredToken();
      const wsClient = token ? getSharedRealtimeClient(token) : null;

      // We capture blobs in Phase 25 (Streaming ASR).
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

      // Start recording with a larger timeslice (2000ms) to reduce CPU load on backend decoding while maintaining real-time feel
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
  }, [releaseMicrophone, updateTimer, stop]);

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
    setState("idle");
    setElapsedMs(0);
    setError(null);
    accumulatedMsRef.current = 0;
  }, []);

  return {
    state,
    elapsedMs,
    error,
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
