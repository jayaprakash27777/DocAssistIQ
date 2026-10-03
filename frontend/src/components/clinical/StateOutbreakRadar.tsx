"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Globe, ShieldAlert, AlertTriangle, Search, Filter, RefreshCw,
  FlaskConical, Stethoscope, MapPin, Building2, ExternalLink,
  ChevronRight, ArrowRight, ShieldCheck, CheckCircle2, Activity,
  Info, Sparkles, Layers
} from "lucide-react";
import { getStateOutbreaks, type StateOutbreakResponse, type OutbreakAlertItem } from "@/lib/api";
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
  onSelectOutbreakForDiagnosis?: (query: string) => void;
}) {
  const router = useRouter();
  const [data, setData] = useState<StateOutbreakResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedState, setSelectedState] = useState("All States & Union Territories");
  const [selectedAlertLevel, setSelectedAlertLevel] = useState<"ALL" | "CRITICAL" | "HIGH" | "MONITORING">("ALL");
  const [activeTab, setActiveTab] = useState<"all" | "india" | "global">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  const fetchOutbreaks = useCallback(async (isRefresh = false) => {
    setLoading(true);
    const stateParam =
      selectedState !== "All States & Union Territories" ? selectedState : undefined;
    const alertParam = selectedAlertLevel !== "ALL" ? selectedAlertLevel : undefined;
    const queryParam = searchQuery.trim() || undefined;

    const res = await getStateOutbreaks({
      state: stateParam,
      alert_level: alertParam,
      query: queryParam,
      refresh: isRefresh,
    });

    if (res.ok) {
      setData(res.data);
      setLastRefreshed(new Date());
      if (isRefresh) {
        toast.success("Real-time live feeds synchronized with CDC, ECDC, MoHFW & Disease.sh!", {
          icon: "🌐",
        });
      }
    } else {
      toast.error("Could not fetch state outbreak surveillance data.");
    }
    setLoading(false);
  }, [selectedState, selectedAlertLevel, searchQuery]);

  useEffect(() => {
    fetchOutbreaks(false);
  }, [fetchOutbreaks]);

  // Filter combined alerts based on activeTab
  const displayedAlerts = useMemo(() => {
    if (!data) return [];
    let list: OutbreakAlertItem[] = [];
    if (activeTab === "all") {
      list = [...data.india_state_alerts, ...data.global_alerts];
    } else if (activeTab === "india") {
      list = data.india_state_alerts;
    } else {
      list = data.global_alerts;
    }

    if (selectedAlertLevel !== "ALL") {
      list = list.filter((a) => a.alert_level === selectedAlertLevel);
    }

    if (selectedState !== "All States & Union Territories") {
      list = list.filter((a) =>
        a.state_or_country.toLowerCase().includes(selectedState.toLowerCase())
      );
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (a) =>
          a.disease_name.toLowerCase().includes(q) ||
          a.pathogen.toLowerCase().includes(q) ||
          a.state_or_country.toLowerCase().includes(q) ||
          a.districts.some((d) => d.toLowerCase().includes(q)) ||
          a.cardinal_symptoms.some((s) => s.toLowerCase().includes(q))
      );
    }

    return list;
  }, [data, activeTab, selectedAlertLevel, selectedState, searchQuery]);

  const handleSimulateOutbreak = (outbreak: OutbreakAlertItem) => {
    const simulationNote = `Patient presenting from ${outbreak.state_or_country} (${outbreak.districts.slice(0, 2).join(", ") || "endemic area"}) with ${outbreak.cardinal_symptoms.join(", ")}. Suspected exposure to ${outbreak.vector_reservoir}. Hallmark presentation: ${outbreak.hallmark_triggers.slice(0, 3).join(", ")}.`;

    if (onSelectOutbreakForDiagnosis) {
      onSelectOutbreakForDiagnosis(simulationNote);
      toast.success(`Loaded ${outbreak.disease_name} symptoms into Differential Diagnosis!`, {
        icon: "⚡",
      });
    } else {
      // Store in session storage and navigate to consultation creation
      sessionStorage.setItem("outbreak_simulation_query", simulationNote);
      sessionStorage.setItem("outbreak_target_disease", outbreak.disease_name);
      router.push(`/consultations/new?outbreak=${encodeURIComponent(outbreak.disease_name)}`);
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
            </div>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto">
            <button
              onClick={() => fetchOutbreaks(true)}
              disabled={loading}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-white hover:bg-slate-50 text-slate-800 border border-slate-200 shadow-2xs transition-colors disabled:opacity-60"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-teal-600 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh Feeds</span>
            </button>
            <span className="text-[11px] text-slate-500 font-medium">
              Refreshed: {lastRefreshed.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
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
              onClick={() => setActiveTab("all")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeTab === "all"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              All Outbreaks ({data?.total_active_alerts ?? 0})
            </button>
            <button
              onClick={() => setActiveTab("india")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeTab === "india"
                  ? "bg-indigo-600 text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              🇮🇳 India States ({data?.india_state_alerts.length ?? 0})
            </button>
            <button
              onClick={() => setActiveTab("global")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeTab === "global"
                  ? "bg-purple-600 text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              🌍 Global Feeds ({data?.global_alerts.length ?? 0})
            </button>
          </div>

          {/* Alert Level Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-bold text-slate-500 mr-1">Severity:</span>
            {(["ALL", "CRITICAL", "HIGH", "MONITORING"] as const).map((lvl) => (
              <button
                key={lvl}
                onClick={() => setSelectedAlertLevel(lvl)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-black transition-all ${
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

        {/* State Dropdown & Search Input */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
          {/* State Dropdown */}
          <div className="relative">
            <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
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
      </div>

      {/* Outbreak Alerts List */}
      {loading ? (
        <div className="p-12 text-center bg-white rounded-3xl border border-slate-200">
          <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs font-bold text-slate-600">Connecting to IDSP, NCDC, WHO &amp; CDC live feeds…</p>
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
              setSelectedAlertLevel("ALL");
              setSearchQuery("");
            }}
            className="mt-3 text-xs font-bold text-indigo-600 underline"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {displayedAlerts.map((outbreak) => (
            <motion.div
              key={outbreak.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-5 rounded-3xl bg-white border border-slate-200/90 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div>
                {/* Header row */}
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-[10px] font-black px-2.5 py-0.5 rounded-full uppercase tracking-wider ${
                        outbreak.alert_level === "CRITICAL"
                          ? "bg-rose-100 text-rose-700 border border-rose-300"
                          : outbreak.alert_level === "HIGH"
                          ? "bg-amber-100 text-amber-800 border border-amber-300"
                          : "bg-sky-100 text-sky-700 border border-sky-300"
                      }`}>
                        {outbreak.alert_level} ALERT
                      </span>
                      <span className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200">
                        {outbreak.region_type === "india_state" ? "🇮🇳 State Surveillance" : "🌍 Global Notice"}
                      </span>
                    </div>

                    <h3 className="text-base font-black text-slate-900 leading-tight">
                      {outbreak.disease_name}
                    </h3>
                    <p className="text-xs font-bold text-indigo-600 mt-0.5">
                      {outbreak.pathogen}
                    </p>
                  </div>

                  <div className="text-right flex-shrink-0">
                    <span className="inline-flex items-center gap-1 text-xs font-black text-slate-800 bg-slate-100 px-2.5 py-1 rounded-xl border border-slate-200">
                      <MapPin className="w-3.5 h-3.5 text-indigo-600" />
                      {outbreak.state_or_country}
                    </span>
                    {outbreak.reported_cases && (
                      <span className="text-[10px] font-semibold text-slate-500 block mt-1">
                        {outbreak.reported_cases}
                      </span>
                    )}
                  </div>
                </div>

                {/* Hotspot Districts */}
                {outbreak.districts && outbreak.districts.length > 0 && (
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

                {/* Strict Directives */}
                <div className="space-y-2 mb-3 text-xs">
                  <div className="p-2.5 rounded-xl bg-rose-50/80 border border-rose-200 text-rose-900">
                    <strong className="text-rose-700 font-extrabold">🚨 Isolation Directive:</strong>{" "}
                    <span>{outbreak.isolation_protocol}</span>
                  </div>

                  <div className="p-2.5 rounded-xl bg-purple-50/80 border border-purple-200 text-purple-900">
                    <strong className="text-purple-700 font-extrabold flex items-center gap-1 mb-0.5">
                      <FlaskConical className="w-3.5 h-3.5 text-purple-600" />
                      Confirmatory Lab Protocol:
                    </strong>
                    <span>{outbreak.confirmatory_test}</span>
                  </div>
                </div>

                {/* Clinical Pearl */}
                {outbreak.clinical_pearl && (
                  <div className="text-xs text-slate-600 italic bg-slate-50 p-2.5 rounded-xl border border-slate-200/60 mb-3">
                    <strong className="text-slate-800 not-italic font-bold">Clinical Pearl:</strong>{" "}
                    {outbreak.clinical_pearl}
                  </div>
                )}
              </div>

              {/* Bottom Actions */}
              <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-3">
                <span className="text-[10px] font-bold text-slate-400">
                  Agency: <strong className="text-slate-600">{outbreak.reporting_agency}</strong>
                </span>

                <button
                  onClick={() => handleSimulateOutbreak(outbreak)}
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-xs transition-colors flex items-center gap-1.5"
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
