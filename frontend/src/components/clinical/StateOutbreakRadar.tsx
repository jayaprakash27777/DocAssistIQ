"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Globe, ShieldAlert, AlertTriangle, Search, Filter, RefreshCw,
  FlaskConical, Stethoscope, MapPin, Building2,
  ArrowRight, ShieldCheck, CheckCircle2, Radio, Zap, Wifi, BellRing, Sparkles
} from "lucide-react";
import {
  getStateOutbreaks,
  rescanLiveFeeds,
  getStoredToken,
  type StateOutbreakResponse,
  type OutbreakAlertItem
} from "@/lib/api";
import { getSharedRealtimeClient } from "@/lib/ws";
import { useRouter } from "next/navigation";
import { toast } from "react-hot-toast";

const ALL_INDIAN_STATES_UTS = [
  "All States & Union Territories",
  "Kerala",
  "Karnataka",
  "Gujarat",
  "Maharashtra",
  "Tamil Nadu",
  "Delhi / NCR",
  "Assam",
  "Uttar Pradesh",
  "Bihar",
  "West Bengal",
  "Rajasthan",
  "Himachal Pradesh",
  "Odisha",
  "Andhra Pradesh",
  "Telangana",
  "Punjab",
  "Haryana",
  "Madhya Pradesh",
  "Uttarakhand",
  "Jammu and Kashmir",
  "Goa",
  "Jharkhand",
  "Chhattisgarh",
  "Tripura",
  "Manipur",
  "Meghalaya",
  "Nagaland",
  "Mizoram",
  "Sikkim",
  "Arunachal Pradesh",
  "Ladakh",
  "Puducherry",
  "Chandigarh",
  "Andaman and Nicobar Islands",
  "Dadra and Nagar Haveli and Daman and Diu",
  "Lakshadweep",
];

export default function StateOutbreakRadar({
  onSelectOutbreakForDiagnosis,
}: {
  onSelectOutbreakForDiagnosis?: (query: string, diseaseName?: string) => void;
}) {
  const router = useRouter();
  const [data, setData] = useState<StateOutbreakResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedState, setSelectedState] = useState("All States & Union Territories");
  const [selectedCountry, setSelectedCountry] = useState("All Countries & Regions");
  const [selectedAlertLevel, setSelectedAlertLevel] = useState<"ALL" | "CRITICAL" | "HIGH" | "MONITORING">("ALL");
  const [activeTab, setActiveTab] = useState<"all" | "india" | "global">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());
  const [mounted, setMounted] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [rescanning, setRescanning] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const fetchOutbreaks = useCallback(async (isRefresh = false) => {
    if (isRefresh) setLoading(true);
    setError(null);

    try {
      const res = await getStateOutbreaks({
        refresh: isRefresh,
      });

      if (res.ok && res.data) {
        setData(res.data);
        setError(null);
        setLastRefreshed(new Date());
        if (isRefresh) {
          toast.success("Real-time live feeds synchronized with CDC, ECDC, MoHFW & Disease.sh!", {
            icon: "🌐",
          });
        }
      } else {
        const msg = (res as { error?: { message?: string } })?.error?.message || "Could not fetch state outbreak surveillance data.";
        setError(msg);
        toast.error(msg);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error connecting to surveillance services.";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch on mount
  useEffect(() => {
    fetchOutbreaks(false);
  }, [fetchOutbreaks]);

  // Real-time WebSocket connection to receive 0ms instant outbreak updates
  useEffect(() => {
    let unsub: (() => void) | null = null;
    let unsubState: (() => void) | null = null;
    let pollInterval: NodeJS.Timeout | null = null;

    try {
      const token =
        getStoredToken() ||
        (typeof window !== "undefined"
          ? localStorage.getItem("access_token") || localStorage.getItem("token")
          : null) ||
        "";
      const ws = getSharedRealtimeClient(token);
      unsubState = ws.subscribeState((s) => {
        setWsConnected(s === "LIVE");
      });

      unsub = ws.subscribeMessages((type: string, payload: any) => {
        if (
          type === "outbreak_alert" ||
          type === "dynamic_disease_discovered" ||
          type === "surveillance_feed_updated"
        ) {
          if (payload?.alert && payload.alert.id) {
            const newAlert: OutbreakAlertItem = {
              ...payload.alert,
              is_dynamic_live: true,
            };

            setData((prev) => {
              if (!prev) return prev;
              const isIndia = newAlert.region_type === "india_state";
              const existingInd = prev.india_state_alerts || [];
              const existingGlob = prev.global_alerts || [];

              if (
                existingInd.some((a) => a.id === newAlert.id) ||
                existingGlob.some((a) => a.id === newAlert.id)
              ) {
                return prev;
              }

              const updatedInd = isIndia ? [newAlert, ...existingInd] : existingInd;
              const updatedGlob = !isIndia ? [newAlert, ...existingGlob] : existingGlob;

              return {
                ...prev,
                total_active_alerts: updatedInd.length + updatedGlob.length,
                india_state_alerts: updatedInd,
                global_alerts: updatedGlob,
              };
            });

            toast.custom(
              (t) => (
                <div
                  className={`${
                    t.visible ? "animate-enter" : "animate-leave"
                  } max-w-md w-full bg-slate-900 text-white shadow-2xl rounded-2xl pointer-events-auto flex ring-2 ring-rose-500/80 p-4 items-start gap-3`}
                >
                  <div className="w-9 h-9 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center flex-shrink-0 text-lg">
                    🚨
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-black uppercase tracking-wider bg-rose-600 text-white px-2 py-0.5 rounded-full">
                        Live Outbreak Trigger
                      </span>
                      <span className="text-[11px] text-slate-400">Just now</span>
                    </div>
                    <p className="text-sm font-black text-white mt-1">
                      {newAlert.disease_name}
                    </p>
                    <p className="text-xs text-slate-300 mt-0.5">
                      📍 {newAlert.state_or_country} · Alert: {newAlert.alert_level}
                    </p>
                    <p className="text-[11px] text-teal-400 mt-1 font-medium">
                      ✓ Radar automatically updated with 0ms delay
                    </p>
                  </div>
                </div>
              ),
              { duration: 8000 }
            );
          } else {
            // Background re-sync to get official enriched feeds
            fetchOutbreaks(false);
          }
          setLastRefreshed(new Date());
        }
      });
    } catch (e) {
      console.warn("WebSocket listener initialization error:", e);
    }

    // Auto-sync polling every 30 seconds so live upstream changes from CDC/ECDC/MoHFW update automatically
    pollInterval = setInterval(() => {
      fetchOutbreaks(false);
    }, 30000);

    return () => {
      if (unsub) unsub();
      if (unsubState) unsubState();
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [fetchOutbreaks]);

  const handleRescanFeeds = async () => {
    setRescanning(true);
    try {
      const res = await rescanLiveFeeds();
      if (res.ok) {
        toast.success("Autonomous scan executed: all live public health feeds synced!", {
          icon: "📡",
        });
        fetchOutbreaks(false);
      } else {
        toast.error("Could not trigger live upstream rescan.");
      }
    } catch {
      toast.error("Error connecting to live surveillance scanner.");
    } finally {
      setRescanning(false);
    }
  };

  // Extract distinct countries from live global alerts
  const globalCountries = useMemo(() => {
    if (!data?.global_alerts || !Array.isArray(data.global_alerts)) return ["All Countries & Regions"];
    const countrySet = new Set<string>();
    for (const a of data.global_alerts) {
      if (a?.state_or_country && a.state_or_country !== "Global Notice") {
        countrySet.add(a.state_or_country);
      }
    }
    return ["All Countries & Regions", ...Array.from(countrySet).sort()];
  }, [data]);

  // Instantaneous zero-latency filtered alerts based on tab, region, severity, and search
  const displayedAlerts = useMemo(() => {
    if (!data) return [];
    const indAlerts = Array.isArray(data.india_state_alerts) ? data.india_state_alerts : [];
    const globAlerts = Array.isArray(data.global_alerts) ? data.global_alerts : [];
    let list: OutbreakAlertItem[] = [];

    if (activeTab === "india") {
      list = indAlerts;
      if (selectedState !== "All States & Union Territories") {
        list = list.filter((a) =>
          a.state_or_country?.toLowerCase().includes(selectedState.toLowerCase())
        );
      }
    } else if (activeTab === "global") {
      list = globAlerts;
      if (selectedCountry !== "All Countries & Regions") {
        list = list.filter((a) =>
          a.state_or_country?.toLowerCase().includes(selectedCountry.toLowerCase())
        );
      }
    } else {
      // "all" tab
      let ind = indAlerts;
      if (selectedState !== "All States & Union Territories") {
        ind = ind.filter((a) =>
          a.state_or_country?.toLowerCase().includes(selectedState.toLowerCase())
        );
      }
      let glob = globAlerts;
      if (selectedCountry !== "All Countries & Regions") {
        glob = glob.filter((a) =>
          a.state_or_country?.toLowerCase().includes(selectedCountry.toLowerCase())
        );
      }
      list = [...ind, ...glob];
    }

    if (selectedAlertLevel !== "ALL") {
      list = list.filter((a) => a.alert_level === selectedAlertLevel);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (a) =>
          a.disease_name?.toLowerCase().includes(q) ||
          a.pathogen?.toLowerCase().includes(q) ||
          a.state_or_country?.toLowerCase().includes(q) ||
          (Array.isArray(a.districts) && a.districts.some((d) => d?.toLowerCase().includes(q))) ||
          (Array.isArray(a.cardinal_symptoms) && a.cardinal_symptoms.some((s) => s?.toLowerCase().includes(q))) ||
          (Array.isArray(a.hallmark_triggers) && a.hallmark_triggers.some((t) => t?.toLowerCase().includes(q))) ||
          a.reporting_agency?.toLowerCase().includes(q)
      );
    }

    return list;
  }, [data, activeTab, selectedAlertLevel, selectedState, selectedCountry, searchQuery]);

  const handleTestInDiagnosis = (outbreak: OutbreakAlertItem) => {
    const districtsStr = Array.isArray(outbreak.districts) && outbreak.districts.length > 0
      ? outbreak.districts.slice(0, 2).join(", ")
      : "endemic area";
    const symptomsStr = Array.isArray(outbreak.cardinal_symptoms)
      ? outbreak.cardinal_symptoms.join(", ")
      : "";
    const triggersStr = Array.isArray(outbreak.hallmark_triggers)
      ? outbreak.hallmark_triggers.slice(0, 3).join(", ")
      : "";

    const presentationNote = `Patient presenting from ${outbreak.state_or_country || "endemic focus"} (${districtsStr}) with ${symptomsStr}. Suspected exposure to ${outbreak.vector_reservoir || "known vector"}. Hallmark presentation: ${triggersStr}.`;

    sessionStorage.setItem("outbreak_simulation_query", presentationNote);
    sessionStorage.setItem("outbreak_target_disease", outbreak.disease_name);

    if (onSelectOutbreakForDiagnosis) {
      onSelectOutbreakForDiagnosis(presentationNote, outbreak.disease_name);
    } else {
      router.push(`/consultations/new?outbreak=${encodeURIComponent(outbreak.disease_name)}`);
    }
  };

  const handleTabChange = (tab: "all" | "india" | "global") => {
    setActiveTab(tab);
    if (tab === "india") {
      setSelectedCountry("All Countries & Regions");
    } else if (tab === "global") {
      setSelectedState("All States & Union Territories");
    }
  };

  return (
    <div className="space-y-5 text-left">
      {/* Live Surveillance Header Banner */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-teal-50/80 via-white to-indigo-50/70 text-slate-900 border border-teal-200/90 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-teal-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200/80">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-teal-500 to-indigo-600 flex items-center justify-center shadow-md shadow-teal-500/20">
              <Globe className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-black text-slate-900 tracking-tight">
                  State-Wide &amp; Global Epidemic Surveillance Feed
                </h2>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-rose-100 text-rose-800 border border-rose-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-600" />
                  Live Radar
                </span>
              </div>
              <p className="text-xs text-slate-600 font-medium mt-0.5">
                Real-time outbreak tracking across all 28 Indian States, 8 Union Territories &amp; Global WHO/CDC feeds.
              </p>
              {/* Live Connection & Auto-Update Status Bar */}
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                {wsConnected ? (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                    <span>WebSocket Live · 0ms Auto-Push</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
                    <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                    <span>Live Feeds Active · Auto-Syncing</span>
                  </span>
                )}
                <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-slate-600 bg-slate-100/90 px-2 py-0.5 rounded-md border border-slate-200">
                  <Radio className="w-3 h-3 text-teal-600 animate-pulse" />
                  <span>US CDC · ECDC · WHO · MoHFW (Zero Mock Data)</span>
                </span>
                <span className="text-[10px] text-slate-500 font-medium">
                  Auto-sync active (30s background sweep)
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto flex-wrap">
            <button
              onClick={handleRescanFeeds}
              disabled={rescanning || loading}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-teal-600 hover:bg-teal-500 text-white shadow-xs transition-all cursor-pointer disabled:opacity-60"
              title="Trigger an immediate live sweep across WHO, CDC, ECDC, MoHFW and Disease.sh upstream APIs"
            >
              <Radio className={`w-3.5 h-3.5 ${rescanning ? "animate-spin text-teal-200" : "animate-pulse text-teal-200"}`} />
              <span>{rescanning ? "Sweeping Upstream Feeds..." : "Sweep Upstream Feeds"}</span>
            </button>

            <button
              onClick={() => fetchOutbreaks(true)}
              disabled={loading}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-white hover:bg-slate-50 text-slate-800 border border-slate-200 shadow-2xs transition-colors disabled:opacity-60 cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-teal-600 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh Feeds</span>
            </button>
            <span className="text-[11px] text-slate-500 font-medium" suppressHydrationWarning>
              Refreshed: {mounted ? lastRefreshed.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "--:--"}
            </span>
          </div>
        </div>

        {/* Live Metrics Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4">
          <div className="bg-white rounded-2xl p-3 border border-slate-200 shadow-2xs">
            <span className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider block mb-0.5">
              Active Alerts Monitored
            </span>
            <div className="text-2xl font-black text-slate-900 flex items-center gap-2">
              <span>{data?.total_active_alerts ?? "—"}</span>
              <span className="text-[10px] px-2 py-0.5 rounded-md bg-rose-100 text-rose-800 border border-rose-200 font-bold">
                Real-Time
              </span>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-3 border border-slate-200 shadow-2xs">
            <span className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider block mb-0.5">
              Indian States &amp; UTs
            </span>
            <div className="text-2xl font-black text-slate-900 flex items-center gap-2">
              <span>36 / 36</span>
              <span className="text-[10px] px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800 border border-emerald-200 font-bold">
                100% Covered
              </span>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-3 border border-slate-200 shadow-2xs">
            <span className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider block mb-0.5">
              Primary Surveillance
            </span>
            <div className="text-sm font-extrabold text-indigo-700 truncate">
              IDSP · NCDC · ICMR · NIV Pune
            </div>
            <span className="text-[10px] text-slate-500">Integrated Lab Protocols</span>
          </div>

          <div className="bg-white rounded-2xl p-3 border border-slate-200 shadow-2xs">
            <span className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider block mb-0.5">
              Differential Integration
            </span>
            <div className="text-sm font-extrabold text-emerald-700 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Automated Symptom Rule-In</span>
            </div>
            <span className="text-[10px] text-slate-500">Direct Diagnosis Badging</span>
          </div>
        </div>
      </div>

      {/* Filter & Controls Toolbar */}
      <div className="p-4 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Tab Selector */}
          <div className="flex items-center p-1 bg-slate-100 rounded-xl gap-1">
            <button
              onClick={() => handleTabChange("all")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                activeTab === "all"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              All Outbreaks ({data?.total_active_alerts ?? 0})
            </button>
            <button
              onClick={() => handleTabChange("india")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                activeTab === "india"
                  ? "bg-indigo-600 text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              🇮🇳 India States ({data?.india_state_alerts?.length ?? 0})
            </button>
            <button
              onClick={() => handleTabChange("global")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                activeTab === "global"
                  ? "bg-purple-600 text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              🌍 Global Feeds ({data?.global_alerts?.length ?? 0})
            </button>
          </div>

          {/* Alert Level Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-bold text-slate-500 mr-1">Severity:</span>
            {(["ALL", "CRITICAL", "HIGH", "MONITORING"] as const).map((lvl) => (
              <button
                key={lvl}
                onClick={() => setSelectedAlertLevel(lvl)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-black transition-all cursor-pointer ${
                  selectedAlertLevel === lvl
                    ? lvl === "CRITICAL"
                      ? "bg-rose-600 text-white shadow-xs"
                      : lvl === "HIGH"
                      ? "bg-amber-500 text-slate-950 shadow-xs"
                      : lvl === "MONITORING"
                      ? "bg-sky-600 text-white shadow-xs"
                      : "bg-teal-600 text-white shadow-xs"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>

        {/* State / Country Dropdown & Search Input */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
          {/* Region Dropdown */}
          <div className="relative">
            {activeTab === "global" ? (
              <>
                <Globe className="w-4 h-4 text-purple-500 absolute left-3 top-2.5 pointer-events-none" />
                <select
                  value={selectedCountry}
                  onChange={(e) => setSelectedCountry(e.target.value)}
                  className="w-full text-xs font-semibold pl-9 pr-8 py-2 rounded-xl border border-slate-200 bg-white text-slate-800 outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-100 shadow-2xs appearance-none cursor-pointer"
                >
                  {globalCountries.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </>
            ) : activeTab === "india" ? (
              <>
                <MapPin className="w-4 h-4 text-indigo-500 absolute left-3 top-2.5 pointer-events-none" />
                <select
                  value={selectedState}
                  onChange={(e) => setSelectedState(e.target.value)}
                  className="w-full text-xs font-semibold pl-9 pr-8 py-2 rounded-xl border border-slate-200 bg-white text-slate-800 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 shadow-2xs appearance-none cursor-pointer"
                >
                  {ALL_INDIAN_STATES_UTS.map((st) => (
                    <option key={st} value={st}>
                      {st}
                    </option>
                  ))}
                </select>
              </>
            ) : (
              <>
                <MapPin className="w-4 h-4 text-teal-600 absolute left-3 top-2.5 pointer-events-none" />
                <select
                  value={selectedState !== "All States & Union Territories" ? `in:${selectedState}` : (selectedCountry !== "All Countries & Regions" ? `gl:${selectedCountry}` : "all")}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val === "all") {
                      setSelectedState("All States & Union Territories");
                      setSelectedCountry("All Countries & Regions");
                    } else if (val.startsWith("in:")) {
                      setSelectedState(val.replace("in:", ""));
                      setSelectedCountry("All Countries & Regions");
                    } else if (val.startsWith("gl:")) {
                      setSelectedCountry(val.replace("gl:", ""));
                      setSelectedState("All States & Union Territories");
                    }
                  }}
                  className="w-full text-xs font-semibold pl-9 pr-8 py-2 rounded-xl border border-slate-200 bg-white text-slate-800 outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100 shadow-2xs appearance-none cursor-pointer"
                >
                  <option value="all">All States, UTs &amp; Countries</option>
                  <optgroup label="🇮🇳 Indian States &amp; UTs">
                    {ALL_INDIAN_STATES_UTS.slice(1).map((st) => (
                      <option key={`in-${st}`} value={`in:${st}`}>
                        {st}
                      </option>
                    ))}
                  </optgroup>
                  <optgroup label="🌍 Global Countries &amp; Regions">
                    {globalCountries.slice(1).map((c) => (
                      <option key={`gl-${c}`} value={`gl:${c}`}>
                        {c}
                      </option>
                    ))}
                  </optgroup>
                </select>
              </>
            )}
          </div>

          {/* Search Input */}
          <div className="relative md:col-span-2">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
            <input
              type="text"
              placeholder="Search pathogen, symptoms (e.g. 'myoclonus', 'eschar'), district, or agency..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full text-xs font-semibold pl-9 pr-3 py-2 rounded-xl border border-slate-200 bg-white text-slate-800 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 shadow-2xs"
            />
          </div>
        </div>

        {/* Quick Hotspot Filter Chips */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1 text-xs">
          <span className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider mr-1">
            Quick Hotspots:
          </span>
          {(activeTab === "global"
            ? ["Brazil", "Rwanda", "Uganda", "Colombia", "Democratic Republic of the Congo", "United States"]
            : activeTab === "india"
            ? ["Kerala", "Maharashtra", "Delhi / NCR", "Gujarat", "Tamil Nadu", "West Bengal", "Uttar Pradesh"]
            : ["Kerala", "Maharashtra", "Gujarat", "Rwanda", "Brazil", "Democratic Republic of the Congo", "United States"]
          ).map((region) => {
            const isGlobChip = ["Brazil", "Rwanda", "Uganda", "Colombia", "Democratic Republic of the Congo", "United States"].includes(region);
            const isSelected = isGlobChip ? selectedCountry === region : selectedState === region;
            return (
              <button
                key={region}
                onClick={() => {
                  if (isGlobChip) {
                    setSelectedCountry(region);
                    if (activeTab === "all") setSelectedState("All States & Union Territories");
                  } else {
                    setSelectedState(region);
                    if (activeTab === "all") setSelectedCountry("All Countries & Regions");
                  }
                }}
                className={`px-2 py-0.5 rounded-lg text-[11px] font-bold transition-all border cursor-pointer ${
                  isSelected
                    ? "bg-indigo-50 text-indigo-700 border-indigo-300 shadow-2xs"
                    : "bg-slate-50 hover:bg-slate-100 text-slate-600 border-slate-200"
                }`}
              >
                {region}
              </button>
            );
          })}
          {(selectedCountry !== "All Countries & Regions" || selectedState !== "All States & Union Territories") && (
            <button
              onClick={() => {
                setSelectedState("All States & Union Territories");
                setSelectedCountry("All Countries & Regions");
              }}
              className="text-[10px] font-bold text-indigo-600 hover:text-indigo-800 underline ml-1 cursor-pointer"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Outbreak Alerts List */}
      {loading ? (
        <div className="p-12 text-center bg-white rounded-3xl border border-slate-200">
          <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs font-bold text-slate-600">Connecting to IDSP, NCDC, WHO &amp; CDC live feeds…</p>
        </div>
      ) : error && !data ? (
        <div className="p-8 text-center bg-rose-50/70 rounded-3xl border border-rose-200 text-slate-700 space-y-3">
          <AlertTriangle className="w-10 h-10 text-rose-600 mx-auto" />
          <h4 className="text-sm font-black text-rose-950">Surveillance Connectivity Notice</h4>
          <p className="text-xs text-rose-800 max-w-md mx-auto">{error}</p>
          <button
            onClick={() => fetchOutbreaks(true)}
            disabled={loading}
            className="px-4 py-2 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white shadow-xs transition-colors inline-flex items-center gap-2 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Retry Connection</span>
          </button>
        </div>
      ) : displayedAlerts.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-3xl border border-slate-200 text-slate-500">
          <ShieldCheck className="w-10 h-10 text-emerald-500 mx-auto mb-3" />
          <h4 className="text-sm font-bold text-slate-800">No Outbreak Alerts Found</h4>
          <p className="text-xs text-slate-500 mt-1">
            No active epidemic alerts matched your search criteria for this region.
          </p>
          <button
            onClick={() => {
              setSelectedState("All States & Union Territories");
              setSelectedCountry("All Countries & Regions");
              setSelectedAlertLevel("ALL");
              setSearchQuery("");
              setActiveTab("all");
            }}
            className="mt-3 text-xs font-bold text-indigo-600 underline cursor-pointer"
          >
            Reset All Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {displayedAlerts.map((outbreak, idx) => (
            <motion.div
              key={`${outbreak.id || "outbreak"}-${idx}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className={`p-5 rounded-3xl bg-white border transition-all flex flex-col justify-between ${
                outbreak.is_dynamic_live
                  ? "border-rose-400 ring-2 ring-rose-500/25 shadow-lg shadow-rose-500/5 bg-gradient-to-br from-white via-rose-50/20 to-white"
                  : "border-slate-200/90 shadow-sm hover:shadow-md"
              }`}
            >
              <div>
                {/* Header row */}
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      {outbreak.is_dynamic_live ? (
                        <span className="inline-flex items-center gap-1.5 text-[10px] font-black px-2.5 py-0.5 rounded-full uppercase tracking-wider bg-rose-600 text-white shadow-xs">
                          <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
                          LIVE DETECTED
                        </span>
                      ) : (
                        <span className={`text-[10px] font-black px-2.5 py-0.5 rounded-full uppercase tracking-wider ${
                          outbreak.alert_level === "CRITICAL"
                            ? "bg-rose-100 text-rose-700 border border-rose-300"
                            : outbreak.alert_level === "HIGH"
                            ? "bg-amber-100 text-amber-800 border border-amber-300"
                            : "bg-sky-100 text-sky-700 border border-sky-300"
                        }`}>
                          {outbreak.alert_level} ALERT
                        </span>
                      )}
                      <span className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200">
                        {outbreak.region_type === "india_state" ? "🇮🇳 State Surveillance" : "🌍 Global Notice"}
                      </span>
                      {outbreak.data_source && (
                        <span className="text-[10px] font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded-md border border-teal-200">
                          {outbreak.data_source}
                        </span>
                      )}
                    </div>

                    <h3 className="text-base font-black text-slate-900 leading-tight">
                      {outbreak.disease_name}
                    </h3>
                    <p className="text-xs font-bold text-indigo-600 mt-0.5">
                      {outbreak.pathogen}
                    </p>
                  </div>

                  <div className="text-right flex-shrink-0 max-w-[200px]">
                    <span className="inline-flex items-center gap-1 text-xs font-black text-slate-800 bg-slate-100 px-2.5 py-1 rounded-xl border border-slate-200">
                      <MapPin className="w-3.5 h-3.5 text-indigo-600" />
                      {outbreak.state_or_country}
                    </span>
                    {outbreak.reported_cases && (
                      <span className="text-[10px] font-semibold text-slate-500 block mt-1 break-words line-clamp-2" title={outbreak.reported_cases}>
                        {outbreak.reported_cases}
                      </span>
                    )}
                  </div>
                </div>

                {/* Hotspot Districts */}
                {Array.isArray(outbreak.districts) && outbreak.districts.length > 0 && (
                  <div className="mb-3 text-xs bg-slate-50 p-2.5 rounded-xl border border-slate-200/70">
                    <span className="font-extrabold text-slate-600 uppercase text-[10px] tracking-wider block mb-1">
                      Hotspot Districts / Focus Areas:
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {outbreak.districts.map((d, di) => (
                        <span key={di} className="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700 text-[11px] font-semibold">
                          {d}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Cardinal Symptoms */}
                {Array.isArray(outbreak.cardinal_symptoms) && outbreak.cardinal_symptoms.length > 0 && (
                  <div className="mb-3">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 block mb-1">
                      Cardinal Warning Symptoms:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {outbreak.cardinal_symptoms.map((sym, si) => (
                        <span
                          key={si}
                          className="px-2 py-0.5 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200/80 text-xs font-medium"
                        >
                          {sym}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Strict Directives */}
                <div className="space-y-2 mb-3 text-xs">
                  {outbreak.isolation_protocol && (
                    <div className="p-2.5 rounded-xl bg-rose-50/80 border border-rose-200 text-rose-900">
                      <strong className="text-rose-700 font-extrabold">🚨 Isolation Directive:</strong>{" "}
                      <span>{outbreak.isolation_protocol}</span>
                    </div>
                  )}

                  {outbreak.confirmatory_test && (
                    <div className="p-2.5 rounded-xl bg-purple-50/80 border border-purple-200 text-purple-900">
                      <strong className="text-purple-700 font-extrabold flex items-center gap-1 mb-0.5">
                        <FlaskConical className="w-3.5 h-3.5 text-purple-600" />
                        Confirmatory Lab Protocol:
                      </strong>
                      <span>{outbreak.confirmatory_test}</span>
                    </div>
                  )}
                </div>

                {/* Clinical Pearl */}
                {outbreak.clinical_pearl && (
                  <div className="text-xs text-slate-600 italic bg-slate-50 p-2.5 rounded-xl border border-slate-200/60 mb-3">
                    <strong className="text-slate-800 not-italic font-bold">Clinical Pearl:</strong>{" "}
                    {outbreak.clinical_pearl.replace(/<[^>]+>/g, " ").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").trim()}
                  </div>
                )}
              </div>

              {/* Bottom Actions */}
              <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-3">
                <span className="text-[10px] font-bold text-slate-400">
                  Agency: <strong className="text-slate-600">{outbreak.reporting_agency}</strong>
                </span>

                <button
                  onClick={() => handleTestInDiagnosis(outbreak)}
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-xs transition-colors flex items-center gap-1.5 cursor-pointer"
                >
                  <Stethoscope className="w-3.5 h-3.5" />
                  <span>Test in Differential Diagnosis</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
