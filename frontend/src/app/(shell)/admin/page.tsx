"use client";

import { useEffect, useState, useRef, useMemo, useCallback } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { 
  getAdminStats, 
  getReady, 
  getAdminAIConfig, 
  switchAdminAIModel, 
  resetAdminCircuitBreaker, 
  getAdminAuditLogs,
  probeAdminAI,
  getStoredToken,
  getAdminInfrastructureTelemetry,
  flushAdminCache,
  toggleAdminMaintenance,
  runAdminDbAnalyze,
  triggerAdminRetentionPurge,
  listPendingDoctors,
  verifyDoctor,
  verifyAllPendingDoctors,
  getAdminUsers,
  updateAdminUser,
  rescanLiveFeeds,
  type AdminStatsResponse, 
  type ReadinessResponse, 
  type AdminAIConfigResponse,
  type AdminAuditLogsResponse,
  type AuditLogItem,
  type ProbeAIResponse,
  type InfrastructureTelemetryResponse,
  type DoctorResponse,
  type AdminUserItem,
} from "@/lib/api";
import { getSharedRealtimeClient, type WSConnectionState } from "@/lib/ws";
import { 
  Activity, Users, ShieldAlert, Database, Server, ClipboardList, BookOpen, 
  Layers, TestTube2, FlaskConical, HardDrive, CheckCircle2, AlertCircle, Cpu, 
  Zap, RefreshCw, Radio, Sparkles, Check, ArrowRight, Lock, Unlock,
  Terminal, ShieldCheck, Gauge, AlertTriangle, Eye, ChevronDown, ChevronUp, Clock, Globe,
  Wifi, WifiOff, Play, Pause, Flame, Trash2, Power, Search, Filter, CheckSquare, XCircle,
  FileText, CornerDownRight, ShieldX, KeyRound, MonitorCheck, HardDriveDownload, UserCheck, Shield, RotateCw
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "react-hot-toast";

interface AdminCard {
  href: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  id: string;
}

const ADMIN_CARDS: AdminCard[] = [
  {
    href: "/admin/users",
    title: "User Directory & RBAC",
    description: "Manage clinician permissions, promote administrators, and enforce access controls.",
    icon: <Users size={24} className="text-violet-600" />,
    id: "admin-card-users",
  },
  {
    href: "/admin/doctors",
    title: "Doctor Verifications",
    description: "Review and approve or reject pending doctor credential submissions.",
    icon: <ShieldAlert size={24} className="text-sky-600" />,
    id: "admin-card-doctors",
  },
  {
    href: "/admin/sources",
    title: "Medical Sources",
    description: "Manage and verify clinical knowledge sources for the registry.",
    icon: <BookOpen size={24} className="text-emerald-600" />,
    id: "admin-card-sources",
  },
  {
    href: "/admin/ingestion",
    title: "Knowledge Ingestion",
    description: "Monitor background ingestion queues and review parsed knowledge.",
    icon: <Server size={24} className="text-purple-600" />,
    id: "admin-card-ingestion",
  },
  {
    href: "/admin/knowledge",
    title: "Knowledge Publication",
    description: "Safely review and publish clinical knowledge to production.",
    icon: <ClipboardList size={24} className="text-blue-600" />,
    id: "admin-card-knowledge",
  },
  {
    href: "/admin/datasets",
    title: "Dataset Registry & Governance",
    description: "Manage ML datasets and enforce PII validation rules.",
    icon: <Database size={24} className="text-indigo-600" />,
    id: "admin-card-datasets",
  },
  {
    href: "/admin/evaluations",
    title: "Baseline Evaluation Harness",
    description: "Run repeatable metrics against fixed hold-out datasets.",
    icon: <TestTube2 size={24} className="text-pink-600" />,
    id: "admin-card-evaluations",
  },
  {
    href: "/admin/experiments",
    title: "ML Experiment Tracking",
    description: "Track model training runs, hyperparameters, and artifacts.",
    icon: <FlaskConical size={24} className="text-rose-600" />,
    id: "admin-card-experiments",
  },
];

export default function AdminPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<AdminStatsResponse | null>(null);
  const [health, setHealth] = useState<ReadinessResponse | null>(null);
  const [infra, setInfra] = useState<InfrastructureTelemetryResponse | null>(null);
  const [aiConfig, setAiConfig] = useState<AdminAIConfigResponse | null>(null);
  const [auditLogs, setAuditLogs] = useState<AdminAuditLogsResponse | null>(null);
  const [pendingDoctors, setPendingDoctors] = useState<DoctorResponse[]>([]);
  const [pendingDoctorsCount, setPendingDoctorsCount] = useState<number>(0);
  const [usersList, setUsersList] = useState<AdminUserItem[]>([]);
  const [usersTotal, setUsersTotal] = useState<number>(0);
  
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  
  // Real-time WebSocket and telemetry stream state
  const [wsState, setWsState] = useState<WSConnectionState>("UNAVAILABLE");
  const [refreshIntervalMs, setRefreshIntervalMs] = useState<number>(3000);
  const [isLivePulse, setIsLivePulse] = useState(false);
  const [newlyArrivedLogId, setNewlyArrivedLogId] = useState<string | null>(null);

  // Active Command Center Sub-Console Tab
  const [activeConsoleTab, setActiveConsoleTab] = useState<"ai" | "doctors" | "users" | "audit" | "surveillance">("ai");

  // Model switching & Circuit breaker mutation state
  const [switching, setSwitching] = useState(false);
  const [customModelInput, setCustomModelInput] = useState("");

  // Live Diagnostic AI Inference Probe state
  const [probing, setProbing] = useState(false);
  const [probeElapsedMs, setProbeElapsedMs] = useState<number>(0);
  const [probeResult, setProbeResult] = useState<ProbeAIResponse | null>(null);
  const [probeError, setProbeError] = useState<string | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Maintenance & System Lockdown State
  const [maintenanceLoading, setMaintenanceLoading] = useState(false);
  const [showMaintenanceModal, setShowMaintenanceModal] = useState(false);
  const [maintenanceReasonInput, setMaintenanceReasonInput] = useState("");

  // Cache Flush & DB Analyze state
  const [flushingCache, setFlushingCache] = useState(false);
  const [cacheNamespace, setCacheNamespace] = useState<string>("all");
  const [analyzingDb, setAnalyzingDb] = useState(false);
  const [purgingStorage, setPurgingStorage] = useState(false);
  const [rescanningFeeds, setRescanningFeeds] = useState(false);

  // Doctor verification inline actions state
  const [verifyingDoctorId, setVerifyingDoctorId] = useState<string | null>(null);
  const [verifyingAll, setVerifyingAll] = useState(false);

  // User management inline search & role update state
  const [userSearchTerm, setUserSearchTerm] = useState("");
  const [updatingUserId, setUpdatingUserId] = useState<string | null>(null);

  // Audit feed UI state
  const [auditFilter, setAuditFilter] = useState<"all" | "alerts" | "ai" | "users">("all");
  const [auditSearchTerm, setAuditSearchTerm] = useState("");
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);

  const isAdmin = user?.role === "admin" || user?.role === "super_admin";

  const fetchTelemetry = useCallback(async (isManual = false) => {
    if (isManual) setSyncing(true);
    try {
      const [statsRes, healthRes, infraRes, aiRes, auditRes, doctorsRes, usersRes] = await Promise.all([
        getAdminStats(),
        getReady(),
        getAdminInfrastructureTelemetry(),
        getAdminAIConfig(),
        getAdminAuditLogs({ limit: 40 }),
        listPendingDoctors(1, 20),
        getAdminUsers({ page: 1, page_size: 15, search: userSearchTerm || undefined }),
      ]);
      if (statsRes.ok) setStats(statsRes.data);
      if (healthRes.ok) setHealth(healthRes.data);
      if (infraRes.ok) setInfra(infraRes.data);
      if (aiRes.ok) setAiConfig(aiRes.data);
      if (auditRes.ok) setAuditLogs(auditRes.data);
      if (doctorsRes.ok) {
        setPendingDoctors(doctorsRes.data.items);
        setPendingDoctorsCount(doctorsRes.data.total);
      }
      if (usersRes.ok) {
        setUsersList(usersRes.data.items);
        setUsersTotal(usersRes.data.total);
      }
      setLastUpdated(new Date());
      setIsLivePulse(true);
      setTimeout(() => setIsLivePulse(false), 800);
    } finally {
      setLoading(false);
      if (isManual) setSyncing(false);
    }
  }, [userSearchTerm]);

  // 1. Establish Bi-directional Real-Time WebSocket Streaming
  useEffect(() => {
    if (!isAdmin) {
      setLoading(false);
      return;
    }

    const token = getStoredToken() || (typeof window !== "undefined" ? localStorage.getItem("access_token") : null) || "";
    const client = getSharedRealtimeClient(token);

    const unsubState = client.subscribeState((state) => {
      setWsState(state);
    });

    const unsubMessages = client.subscribeMessages((type, payload) => {
      setIsLivePulse(true);
      setTimeout(() => setIsLivePulse(false), 900);

      if (type === "audit.event" && payload) {
        const newLog: AuditLogItem = {
          id: payload.id || `evt-${Date.now()}`,
          created_at: payload.created_at || new Date().toISOString(),
          actor_id: payload.actor_id || null,
          actor_email: payload.actor_email || null,
          actor_role: payload.actor_role || null,
          action: payload.action,
          entity_type: payload.entity_type,
          entity_id: payload.entity_id || null,
          ip_address: payload.ip_address || null,
          user_agent: payload.user_agent || null,
          request_id: payload.request_id || null,
          diff: payload.diff || null,
          severity: (payload.severity as "info" | "warning" | "critical") || "info",
        };

        setNewlyArrivedLogId(newLog.id);
        setTimeout(() => setNewlyArrivedLogId(null), 4000);

        setAuditLogs((prev) => {
          if (!prev) {
            return {
              items: [newLog],
              total: 1,
              critical_count: newLog.severity === "critical" ? 1 : 0,
              warning_count: newLog.severity === "warning" ? 1 : 0,
              safety_watermark: "REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED",
            };
          }
          if (prev.items.some((item) => item.id === newLog.id)) return prev;

          return {
            ...prev,
            items: [newLog, ...prev.items.slice(0, 39)],
            total: prev.total + 1,
            critical_count: newLog.severity === "critical" ? prev.critical_count + 1 : prev.critical_count,
            warning_count: newLog.severity === "warning" ? prev.warning_count + 1 : prev.warning_count,
          };
        });
      }

      if (type === "system.maintenance" && payload) {
        setInfra((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            maintenance_mode: Boolean(payload.enabled),
            maintenance_reason: payload.reason || null,
          };
        });
        toast(
          payload.enabled 
            ? "⚠️ Emergency Platform Lockdown Activated" 
            : "✅ Platform restored to normal operational state",
          { icon: payload.enabled ? "🚨" : "🛡️", duration: 6000 }
        );
      }

      if (type === "ai.model_switched" || type === "ai.circuit_breaker_reset" || type === "circuit_breaker.updated") {
        if (payload && payload.active_model) {
          setAiConfig(payload as AdminAIConfigResponse);
        } else {
          getAdminAIConfig().then((res) => { if (res.ok) setAiConfig(res.data); });
        }
      }

      if (type === "user.updated" || type === "doctor.verified") {
        fetchTelemetry(false);
      }
    });

    return () => {
      unsubState();
      unsubMessages();
    };
  }, [isAdmin, fetchTelemetry]);

  // 2. Real-time Telemetry Polling Loop
  useEffect(() => {
    if (!isAdmin) return;
    let mounted = true;

    fetchTelemetry();

    if (refreshIntervalMs > 0) {
      const intervalId = setInterval(() => {
        if (mounted) {
          fetchTelemetry();
        }
      }, refreshIntervalMs);
      return () => {
        mounted = false;
        clearInterval(intervalId);
      };
    }
  }, [isAdmin, refreshIntervalMs, fetchTelemetry]);

  // Clean up timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  // Operation 1: Switch System AI Model
  const handleSwitchModel = async (targetModel: string) => {
    const cleaned = targetModel.trim();
    if (!cleaned || switching) return;
    setSwitching(true);
    try {
      const res = await switchAdminAIModel({ model_name: cleaned });
      if (res.ok) {
        setAiConfig(res.data);
        setCustomModelInput("");
        toast.success(`AI Model switched to "${res.data.active_model}" in real time!`);
        getAdminAuditLogs({ limit: 40 }).then((r) => { if (r.ok) setAuditLogs(r.data); });
      } else {
        toast.error(res.error?.message || "Failed to switch AI model.");
      }
    } catch {
      toast.error("Network communication error.");
    } finally {
      setSwitching(false);
    }
  };

  // Operation 2: Reset Circuit Breaker
  const handleResetCircuitBreaker = async () => {
    if (switching) return;
    setSwitching(true);
    try {
      const res = await resetAdminCircuitBreaker();
      if (res.ok) {
        setAiConfig(res.data);
        toast.success("Circuit breaker reset. Normal inference restored.");
      } else {
        toast.error(res.error?.message || "Failed to reset breaker.");
      }
    } finally {
      setSwitching(false);
    }
  };

  // Operation 3: Toggle Force Offline
  const handleToggleForceOffline = async () => {
    if (!aiConfig || switching) return;
    setSwitching(true);
    const willForce = !aiConfig.circuit_breaker.forced_offline;
    try {
      const res = await switchAdminAIModel({
        model_name: aiConfig.active_model,
        force_offline: willForce,
      });
      if (res.ok) {
        setAiConfig(res.data);
        toast.success(
          willForce
            ? "Offline Fallback Enforced: static clinical knowledge active."
            : "Deterministic override disabled. Resumed live LLM connectivity."
        );
      }
    } finally {
      setSwitching(false);
    }
  };

  // Operation 4: Live Diagnostic Inference Probe
  const handleRunInferenceProbe = async () => {
    if (probing) return;
    setProbing(true);
    setProbeError(null);
    setProbeResult(null);
    setProbeElapsedMs(0);

    const startTime = performance.now();
    timerRef.current = setInterval(() => {
      setProbeElapsedMs(Math.round(performance.now() - startTime));
    }, 25);

    try {
      const res = await probeAdminAI();
      if (timerRef.current) clearInterval(timerRef.current);
      setProbeElapsedMs(Math.round(performance.now() - startTime));
      if (res.ok) {
        setProbeResult(res.data);
        getAdminAIConfig().then((aiRes) => { if (aiRes.ok) setAiConfig(aiRes.data); });
      } else {
        setProbeError(res.error?.message || "Probe failed to communicate with AI engine.");
      }
    } catch (err: unknown) {
      if (timerRef.current) clearInterval(timerRef.current);
      setProbeElapsedMs(Math.round(performance.now() - startTime));
      const msg = err instanceof Error ? err.message : "Network error during inference probe.";
      setProbeError(msg);
    } finally {
      setProbing(false);
    }
  };

  // Operation 5: Master Emergency Maintenance Switch
  const handleToggleMaintenance = async () => {
    const isCurrentlyActive = infra?.maintenance_mode ?? false;
    setMaintenanceLoading(true);
    try {
      const res = await toggleAdminMaintenance(!isCurrentlyActive, maintenanceReasonInput || undefined);
      if (res.ok) {
        setInfra((prev) => prev ? { ...prev, maintenance_mode: res.data.maintenance_mode, maintenance_reason: res.data.reason } : prev);
        setShowMaintenanceModal(false);
        setMaintenanceReasonInput("");
        toast.success(res.data.maintenance_mode ? "Platform placed in Emergency Lockdown!" : "Emergency Maintenance Mode Lifted.");
        fetchTelemetry(false);
      } else {
        toast.error("Could not update platform maintenance state.");
      }
    } finally {
      setMaintenanceLoading(false);
    }
  };

  // Operation 6: Live Redis Cache Flush
  const handleFlushCache = async (ns: string = "all") => {
    if (flushingCache) return;
    setFlushingCache(true);
    try {
      const res = await flushAdminCache(ns);
      if (res.ok) {
        toast.success(`Purged ${res.data.keys_purged} keys from Redis namespace [${res.data.namespace}]!`, { icon: "🧹" });
        fetchTelemetry(false);
      } else {
        toast.error("Cache purge failed.");
      }
    } finally {
      setFlushingCache(false);
    }
  };

  // Operation 7: PostgreSQL Database ANALYZE Optimizer
  const handleAnalyzeDatabase = async () => {
    if (analyzingDb) return;
    setAnalyzingDb(true);
    try {
      const res = await runAdminDbAnalyze();
      if (res.ok) {
        toast.success(`PostgreSQL ANALYZE completed in ${res.data.duration_ms}ms! Query plans optimized.`, { icon: "⚡" });
        fetchTelemetry(false);
      } else {
        toast.error("Database optimization query failed.");
      }
    } finally {
      setAnalyzingDb(false);
    }
  };

  // Operation 8: Storage Retention Purge
  const handleRetentionPurge = async () => {
    if (purgingStorage) return;
    setPurgingStorage(true);
    try {
      const res = await triggerAdminRetentionPurge();
      if (res.ok) {
        toast.success("HIPAA data retention purge executed successfully!", { icon: "🗑️" });
        fetchTelemetry(false);
      } else {
        toast.error("Retention purge execution failed.");
      }
    } finally {
      setPurgingStorage(false);
    }
  };

  // Operation 9: Upstream Epidemic Feeds Live Rescan
  const handleRescanSurveillance = async () => {
    if (rescanningFeeds) return;
    setRescanningFeeds(true);
    try {
      const res = await rescanLiveFeeds();
      if (res.ok) {
        toast.success(`Autonomous surveillance scan executed: ${res.data.total_alerts} live alerts refreshed!`, { icon: "📡" });
        fetchTelemetry(false);
      } else {
        toast.error("Surveillance scanner trigger failed.");
      }
    } finally {
      setRescanningFeeds(false);
    }
  };

  // Operation 10: Doctor Verification Inline Action
  const handleVerifyDoctor = async (doctorId: string, action: "verify" | "reject", reason?: string) => {
    setVerifyingDoctorId(doctorId);
    try {
      const res = await verifyDoctor(doctorId, { action, rejection_reason: reason });
      if (res.ok) {
        toast.success(action === "verify" ? "Doctor verified & activated!" : "Doctor submission rejected.");
        fetchTelemetry(false);
      } else {
        toast.error(res.error?.message || "Failed to update doctor verification.");
      }
    } finally {
      setVerifyingDoctorId(null);
    }
  };

  // Operation 11: Bulk Verify All Pending Doctors
  const handleVerifyAllDoctors = async () => {
    if (verifyingAll || pendingDoctors.length === 0) return;
    setVerifyingAll(true);
    try {
      const res = await verifyAllPendingDoctors();
      if (res.ok) {
        toast.success(`Batch verified ${res.data.verified_count} doctors!`, { icon: "✅" });
        fetchTelemetry(false);
      } else {
        toast.error("Batch verification failed.");
      }
    } finally {
      setVerifyingAll(false);
    }
  };

  // Operation 12: Update User RBAC Role or Active Status
  const handleUpdateUser = async (userId: string, newRole?: string, newActive?: boolean) => {
    setUpdatingUserId(userId);
    try {
      const res = await updateAdminUser(userId, { role: newRole, is_active: newActive });
      if (res.ok) {
        toast.success(`Updated account for ${res.data.email}!`);
        fetchTelemetry(false);
      } else {
        toast.error(res.error?.message || "Failed to update user.");
      }
    } finally {
      setUpdatingUserId(null);
    }
  };

  if (!user) return null;

  if (!isAdmin) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center p-8 bg-slate-50 text-slate-900">
        <div className="p-8 rounded-3xl border border-rose-200 bg-white shadow-xl max-w-md text-center">
          <div className="w-16 h-16 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto mb-4 border border-rose-200">
            <ShieldAlert size={32} />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2 font-heading">
            Access Denied: Administrator Required
          </h2>
          <p className="text-slate-600 mb-6 text-sm leading-relaxed">
            Your account ({user.email}) has role <strong className="text-rose-600 font-semibold">{user.role}</strong>. The System Command Center is restricted strictly to platform operations administrators.
          </p>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-sm shadow-md"
          >
            Return to Clinical Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const isCircuitOpen = aiConfig?.circuit_breaker.is_open ?? false;
  const isForcedOffline = aiConfig?.circuit_breaker.forced_offline ?? false;
  const isLiveLLM = aiConfig?.mode === "llm_active";

  // Filter audit logs based on tab & search
  const filteredLogs = (auditLogs?.items || []).filter((item) => {
    if (auditFilter === "alerts" && item.severity !== "warning" && item.severity !== "critical") return false;
    if (auditFilter === "ai" && item.entity_type !== "ai_engine" && !item.action.includes("model") && !item.action.includes("circuit")) return false;
    if (auditFilter === "users" && item.entity_type !== "user" && !item.action.includes("user") && !item.action.includes("rbac") && !item.action.includes("auth")) return false;
    if (auditSearchTerm) {
      const term = auditSearchTerm.toLowerCase();
      const matchAction = item.action.toLowerCase().includes(term);
      const matchActor = (item.actor_email || "").toLowerCase().includes(term);
      const matchIp = (item.ip_address || "").toLowerCase().includes(term);
      if (!matchAction && !matchActor && !matchIp) return false;
    }
    return true;
  });

  return (
    <div className="min-h-full w-full bg-slate-50 text-slate-900 relative p-4 md:p-6 lg:p-8 font-sans space-y-8">
      {/* Background Architectural Accent */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden opacity-40">
        <div className="absolute top-[-80px] left-[-80px] w-[450px] h-[450px] bg-cyan-200/30 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-80px] right-[-80px] w-[500px] h-[500px] bg-indigo-200/30 rounded-full blur-[140px]" />
        <div className="absolute inset-0 opacity-[0.035]" style={{ backgroundImage: 'radial-gradient(#0f172a 1px, transparent 1px)', backgroundSize: '24px 24px' }} />
      </div>

      <div className="max-w-[1600px] mx-auto space-y-8 relative z-10">
        
        {/* ============================================================ */}
        {/* TOP COMMAND HEADER & REAL-TIME OPS TELEMETRY BAR             */}
        {/* ============================================================ */}
        <header className="flex flex-col xl:flex-row xl:items-center justify-between gap-6 pb-6 border-b border-slate-200/90">
          <div>
            {/* Eyebrow Status Badges */}
            <div className="flex items-center gap-2.5 mb-2.5 flex-wrap">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-black uppercase tracking-wider bg-teal-500/10 text-teal-700 border border-teal-500/20 font-heading">
                <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                Root SecOps · Tier-1 Executive Console
              </span>
              {infra?.maintenance_mode ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-black uppercase tracking-wider bg-rose-600 text-white animate-pulse shadow-xs font-heading">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  Emergency Lockdown Active
                </span>
              ) : (
                <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-2xs">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                  Normal Production Run
                </span>
              )}
            </div>

            {/* Main Title & System Icon */}
            <div className="flex items-center gap-3.5">
              <div className="p-2.5 rounded-2xl bg-teal-500/10 text-teal-600 border border-teal-500/20 shadow-xs flex items-center justify-center shrink-0">
                <Terminal className="w-7 h-7" />
              </div>
              <h1 className="text-3xl sm:text-4xl font-black font-heading text-slate-900 tracking-tight m-0">
                System Command Center
              </h1>
            </div>

            {/* Subtitle in System Sans font */}
            <p className="text-sm sm:text-base text-slate-500 font-medium mt-2 max-w-2xl leading-relaxed">
              Global platform telemetry, autonomous infrastructure controls, and HIPAA compliance governance.
            </p>
          </div>

          {/* Master Operational Controls & Live Stream Telemetry */}
          <div className="flex flex-wrap items-center gap-3">
            
            {/* Emergency Maintenance Master Switch */}
            <button
              onClick={() => setShowMaintenanceModal(true)}
              className={`px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all border shadow-2xs ${
                infra?.maintenance_mode
                  ? "bg-rose-600 hover:bg-rose-700 text-white border-rose-700 shadow-rose-600/30"
                  : "bg-white hover:bg-rose-50 text-slate-800 hover:text-rose-700 border-slate-300 hover:border-rose-300"
              }`}
            >
              <Power className={`w-4 h-4 ${infra?.maintenance_mode ? "animate-spin" : "text-amber-500"}`} />
              <span>{infra?.maintenance_mode ? "Disable Lockdown" : "Emergency Lockdown"}</span>
            </button>

            {/* WebSocket Stream Badge */}
            <div className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium border shadow-2xs transition-colors ${
              wsState === 'LIVE'
                ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                : wsState === 'CONNECTING' || wsState === 'RECONNECTING'
                ? "bg-amber-50 border-amber-200 text-amber-800 animate-pulse"
                : "bg-white border-slate-200 text-slate-600"
            }`}>
              {wsState === 'LIVE' ? (
                <>
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </span>
                  <Wifi size={13} className="text-emerald-600" />
                  <span className="font-semibold">Live Push (0ms)</span>
                </>
              ) : (
                <>
                  <WifiOff size={13} className="text-slate-400" />
                  <span>Polling Sync</span>
                </>
              )}
            </div>

            {/* Telemetry Polling Rate Selector */}
            <div className="flex items-center gap-1 bg-white border border-slate-200 p-1 rounded-xl text-xs font-medium text-slate-600 shadow-2xs">
              <span className="px-2 text-xs text-slate-400 font-semibold hidden sm:inline">
                Rate:
              </span>
              <button
                onClick={() => setRefreshIntervalMs(1000)}
                title="Hyper Mode: Poll every 1 second"
                className={`px-2.5 py-1 rounded-lg transition-all flex items-center gap-1 ${
                  refreshIntervalMs === 1000 
                    ? "bg-slate-900 text-white font-bold shadow-2xs" 
                    : "hover:bg-slate-100 text-slate-600 hover:text-slate-900"
                }`}
              >
                <Flame size={12} className={refreshIntervalMs === 1000 ? "text-amber-400" : "text-amber-500"} />
                1s
              </button>
              <button
                onClick={() => setRefreshIntervalMs(3000)}
                title="Standard: Poll every 3 seconds"
                className={`px-2.5 py-1 rounded-lg transition-all ${
                  refreshIntervalMs === 3000 
                    ? "bg-slate-900 text-white font-bold shadow-2xs" 
                    : "hover:bg-slate-100 text-slate-600 hover:text-slate-900"
                }`}
              >
                3s
              </button>
              <button
                onClick={() => setRefreshIntervalMs(5000)}
                title="Balanced: Poll every 5 seconds"
                className={`px-2.5 py-1 rounded-lg transition-all ${
                  refreshIntervalMs === 5000 
                    ? "bg-slate-900 text-white font-bold shadow-2xs" 
                    : "hover:bg-slate-100 text-slate-600 hover:text-slate-900"
                }`}
              >
                5s
              </button>
            </div>

            {/* Manual Sync Trigger */}
            <button
              onClick={() => fetchTelemetry(true)}
              disabled={syncing}
              title="Force manual telemetry sync"
              className="p-2.5 bg-white hover:bg-slate-100 border border-slate-200 rounded-xl text-slate-700 hover:text-cyan-700 transition-colors shadow-2xs"
            >
              <RefreshCw size={15} className={syncing ? "animate-spin text-cyan-600" : ""} />
            </button>
          </div>
        </header>

        {/* ============================================================ */}
        {/* DEEP INFRASTRUCTURE TELEMETRY RACK (4 REAL-TIME NODES)      */}
        {/* ============================================================ */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-1 rounded-lg bg-teal-500/10 text-teal-600 border border-teal-500/20">
                <Server className="w-3.5 h-3.5" />
              </div>
              <h2 className="text-xs font-black uppercase tracking-wider text-slate-700 font-heading">
                Real-Time Node Topology &amp; Hardware Telemetry Rack
              </h2>
            </div>
            <span className="text-xs text-slate-500 font-medium">
              Synced: <strong className="text-slate-700 font-semibold">{lastUpdated.toLocaleTimeString()}</strong>
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            
            {/* NODE 1: PostgreSQL 16 Relational & Vector Engine */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Database className="w-5 h-5 text-indigo-600" />
                    <span className="font-bold text-sm text-slate-900 font-heading">PostgreSQL 16 Engine</span>
                  </div>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    infra?.database.status === 'healthy' 
                      ? "bg-emerald-50 border border-emerald-200 text-emerald-700" 
                      : "bg-rose-50 border border-rose-200 text-rose-700"
                  }`}>
                    {infra?.database.status === 'healthy' ? "Online" : "Degraded"}
                  </span>
                </div>
                
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center text-slate-500">
                    <span>Ping Latency:</span>
                    <span className="text-emerald-700 font-bold font-mono">{infra?.database.latency_ms ?? 12.1} ms</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-500">
                    <span>Active Connections:</span>
                    <span className="text-slate-900 font-semibold">{infra?.database.active_connections ?? 10}</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-500">
                    <span>Database Users:</span>
                    <span className="text-slate-900 font-semibold">{infra?.database.table_counts.users ?? stats?.total_users ?? 0}</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-500">
                    <span>Consultations:</span>
                    <span className="text-indigo-600 font-semibold">{infra?.database.table_counts.consultations ?? stats?.total_consultations ?? 0}</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-500">
                    <span>Audit Logs:</span>
                    <span className="text-violet-700 font-semibold">{infra?.database.table_counts.audit_logs ?? 0}</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                <button
                  onClick={handleAnalyzeDatabase}
                  disabled={analyzingDb}
                  className="w-full py-2 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs font-semibold flex items-center justify-center gap-1.5 transition-all shadow-2xs"
                >
                  <Zap className={`w-3.5 h-3.5 ${analyzingDb ? "animate-spin text-amber-500" : "text-indigo-600"}`} />
                  <span>{analyzingDb ? "Analyzing Index..." : "Run ANALYZE Optimizer"}</span>
                </button>
              </div>
            </div>

            {/* NODE 2: Redis 7 In-Memory Cache & Stream Broker */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-rose-600" />
                    <span className="font-bold text-sm text-slate-900 font-heading">Redis 7 Broker</span>
                  </div>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    infra?.redis.status === 'healthy' 
                      ? "bg-emerald-50 border border-emerald-200 text-emerald-700" 
                      : "bg-rose-50 border border-rose-200 text-rose-700"
                  }`}>
                    {infra?.redis.status === 'healthy' ? "Online" : "Degraded"}
                  </span>
                </div>
                
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center text-slate-500">
                    <span>Ping Latency:</span>
                    <span className="text-emerald-700 font-bold font-mono">{infra?.redis.latency_ms ?? 4.2} ms</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-500">
                    <span>Engine Version:</span>
                    <span className="text-slate-900 font-semibold">{infra?.redis.redis_version ?? "7.4.11"}</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-500">
                    <span>Memory Used:</span>
                    <span className="text-cyan-700 font-bold font-mono">{infra?.redis.used_memory_human ?? "1.56M"}</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-500">
                    <span>Client Connections:</span>
                    <span className="text-slate-900 font-semibold">{infra?.redis.connected_clients ?? 15}</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-500">
                    <span>Stored Keys:</span>
                    <span className="text-amber-700 font-semibold font-mono">{infra?.redis.total_keys ?? 0}</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-2">
                <select
                  value={cacheNamespace}
                  onChange={(e) => setCacheNamespace(e.target.value)}
                  className="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-xl px-2 py-2 font-medium"
                >
                  <option value="all">All Keys</option>
                  <option value="consultations">Consultations</option>
                  <option value="outbreaks">Outbreaks</option>
                  <option value="diagnostics">Diagnostics</option>
                </select>
                <button
                  onClick={() => handleFlushCache(cacheNamespace)}
                  disabled={flushingCache}
                  className="flex-1 py-2 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-semibold flex items-center justify-center gap-1 transition-all shadow-2xs"
                >
                  <Trash2 className={`w-3.5 h-3.5 ${flushingCache ? "animate-spin text-amber-500" : "text-rose-600"}`} />
                  <span>Flush</span>
                </button>
              </div>
            </div>

            {/* NODE 3: MinIO S3 Object Storage Cluster */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <HardDrive className="w-5 h-5 text-amber-600" />
                    <span className="font-bold text-sm text-slate-900 font-heading">MinIO S3 Cluster</span>
                  </div>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    infra?.storage.status === 'healthy' 
                      ? "bg-emerald-50 border border-emerald-200 text-emerald-700" 
                      : "bg-rose-50 border border-rose-200 text-rose-700"
                  }`}>
                    {infra?.storage.status === 'healthy' ? "Online" : "Degraded"}
                  </span>
                </div>
                
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center text-slate-500">
                    <span>S3 Latency:</span>
                    <span className="text-emerald-700 font-bold font-mono">{infra?.storage.latency_ms ?? 31.9} ms</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-500">
                    <span>Target Bucket:</span>
                    <span className="text-slate-900 font-semibold">{infra?.storage.bucket_name ?? "docassistiq"}</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-500">
                    <span>Stored Objects:</span>
                    <span className="text-indigo-600 font-bold font-mono">{infra?.storage.total_objects ?? 6}</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-500">
                    <span>Storage Footprint:</span>
                    <span className="text-slate-900 font-semibold">{Math.round((infra?.storage.total_size_bytes ?? 31626) / 1024)} KB</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-500">
                    <span>S3 Endpoint:</span>
                    <span className="text-slate-600 truncate max-w-[120px] font-mono">{infra?.storage.endpoint ?? "localhost:9010"}</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100">
                <button
                  onClick={handleRetentionPurge}
                  disabled={purgingStorage}
                  className="w-full py-2 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 text-xs font-semibold flex items-center justify-center gap-1.5 transition-all shadow-2xs"
                >
                  <HardDriveDownload className={`w-3.5 h-3.5 ${purgingStorage ? "animate-spin text-amber-600" : "text-amber-600"}`} />
                  <span>{purgingStorage ? "Purging Expired..." : "Execute Retention Purge"}</span>
                </button>
              </div>
            </div>

            {/* NODE 4: Local Ollama Clinical AI Engine */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-5 h-5 text-cyan-600" />
                    <span className="font-bold text-sm text-slate-900 font-heading">Ollama Clinical AI</span>
                  </div>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    aiConfig?.is_connected 
                      ? "bg-emerald-50 border border-emerald-200 text-emerald-700" 
                      : "bg-amber-50 border border-amber-200 text-amber-800"
                  }`}>
                    {aiConfig?.mode === "llm_active" ? "LLM Active" : "KB Fallback"}
                  </span>
                </div>
                
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center text-slate-500">
                    <span>Active Model:</span>
                    <span className="text-cyan-700 font-bold truncate max-w-[130px]">{aiConfig?.active_model || "llama3.2:latest"}</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-500">
                    <span>Breaker State:</span>
                    <span className={isCircuitOpen ? "text-rose-600 font-bold" : "text-emerald-700 font-bold"}>
                      {aiConfig?.circuit_breaker.state || "CLOSED"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-slate-500">
                    <span>Inference Latency:</span>
                    <span className="text-slate-900 font-semibold font-mono">{Math.round(aiConfig?.latency_ms ?? 0)} ms</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-500">
                    <span>Installed Models:</span>
                    <span className="text-slate-900 font-semibold">{aiConfig?.installed_models?.length ?? 4} models</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-500">
                    <span>Endpoint:</span>
                    <span className="text-slate-600 truncate max-w-[120px] font-mono">{aiConfig?.base_url || "localhost:11434"}</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100">
                <button
                  onClick={handleRunInferenceProbe}
                  disabled={probing}
                  className="w-full py-2 rounded-xl bg-cyan-50 hover:bg-cyan-100 text-cyan-800 border border-cyan-200 text-xs font-semibold flex items-center justify-center gap-1.5 transition-all shadow-2xs"
                >
                  <Gauge className={`w-3.5 h-3.5 ${probing ? "animate-spin text-cyan-600" : "text-cyan-600"}`} />
                  <span>{probing ? "Probing LLM..." : "Run Real-Time AI Probe"}</span>
                </button>
              </div>
            </div>

          </div>
        </section>

        {/* ============================================================ */}
        {/* PRIMARY COMMAND CONTROL DESK: TAB NAVIGATION                */}
        {/* ============================================================ */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 border-b border-slate-200 pb-2 overflow-x-auto">
            <button
              onClick={() => setActiveConsoleTab("ai")}
              className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold font-heading flex items-center gap-2 transition-all ${
                activeConsoleTab === "ai"
                  ? "bg-slate-900 text-white shadow-md shadow-slate-900/15"
                  : "bg-white hover:bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-200 shadow-2xs"
              }`}
            >
              <Cpu size={16} />
              <span>AI Fleet &amp; Circuit Breaker</span>
            </button>

            <button
              onClick={() => setActiveConsoleTab("doctors")}
              className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold font-heading flex items-center gap-2 transition-all ${
                activeConsoleTab === "doctors"
                  ? "bg-slate-900 text-white shadow-md shadow-slate-900/15"
                  : "bg-white hover:bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-200 shadow-2xs"
              }`}
            >
              <ShieldAlert size={16} />
              <span>Doctor Verifications ({pendingDoctorsCount})</span>
            </button>

            <button
              onClick={() => setActiveConsoleTab("users")}
              className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold font-heading flex items-center gap-2 transition-all ${
                activeConsoleTab === "users"
                  ? "bg-slate-900 text-white shadow-md shadow-slate-900/15"
                  : "bg-white hover:bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-200 shadow-2xs"
              }`}
            >
              <Users size={16} />
              <span>User Directory &amp; RBAC ({usersTotal})</span>
            </button>

            <button
              onClick={() => setActiveConsoleTab("audit")}
              className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold font-heading flex items-center gap-2 transition-all ${
                activeConsoleTab === "audit"
                  ? "bg-slate-900 text-white shadow-md shadow-slate-900/15"
                  : "bg-white hover:bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-200 shadow-2xs"
              }`}
            >
              <ClipboardList size={16} />
              <span>HIPAA Security Audit Feed</span>
            </button>

            <button
              onClick={() => setActiveConsoleTab("surveillance")}
              className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold font-heading flex items-center gap-2 transition-all ${
                activeConsoleTab === "surveillance"
                  ? "bg-slate-900 text-white shadow-md shadow-slate-900/15"
                  : "bg-white hover:bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-200 shadow-2xs"
              }`}
            >
              <Globe size={16} />
              <span>Epidemic Feeds Scanner</span>
            </button>
          </div>

          {/* TAB 1: AI FLEET & CIRCUIT BREAKER CONSOLE */}
          {activeConsoleTab === "ai" && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* Left Column: Model Fleet Hot-Swap */}
              <div className="lg:col-span-2 p-6 rounded-2xl bg-white border border-slate-200/90 shadow-sm space-y-6">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 font-heading flex items-center gap-2">
                    <Cpu className="w-5 h-5 text-cyan-600" />
                    <span>Live Model Fleet &amp; System Inference Controller</span>
                  </h3>
                  <p className="text-sm text-slate-500 font-normal mt-1">
                    Hot-swap active LLM weights system-wide with zero downtime across clinical decision support, differentials, and note drafting.
                  </p>
                </div>

                {/* Available Installed Models Grid */}
                <div className="space-y-3">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">
                    Installed Local Models (1-Click Hot Swap):
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {(aiConfig?.installed_models || ["llama3.2:latest", "ii-medical:8b", "llama3.1:8b", "nomic-embed-text:latest"]).map((m) => {
                      const isCurrent = aiConfig?.active_model === m;
                      return (
                        <div
                          key={m}
                          className={`p-4 rounded-xl border transition-all flex items-center justify-between ${
                            isCurrent
                              ? "bg-cyan-50/70 border-cyan-300 shadow-xs"
                              : "bg-slate-50/80 border-slate-200 hover:border-slate-300"
                          }`}
                        >
                          <div>
                            <span className="font-bold text-sm text-slate-900 block font-heading">{m}</span>
                            <span className="text-xs text-slate-500 font-normal">
                              {m.includes("medical") ? "Clinical Fine-Tuned" : m.includes("embed") ? "Vector Embeddings" : "General Diagnostic"}
                            </span>
                          </div>
                          {isCurrent ? (
                            <span className="px-2.5 py-1 rounded-md bg-cyan-700 text-white text-xs font-bold shadow-xs">
                              Active
                            </span>
                          ) : (
                            <button
                              onClick={() => handleSwitchModel(m)}
                              disabled={switching}
                              className="px-3.5 py-1.5 rounded-lg bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold border border-slate-300 shadow-2xs transition-colors"
                            >
                              Activate
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Custom Model Input */}
                <div className="pt-4 border-t border-slate-100 flex items-center gap-3">
                  <input
                    type="text"
                    value={customModelInput}
                    onChange={(e) => setCustomModelInput(e.target.value)}
                    placeholder="Enter custom Ollama tag (e.g. medalpaca:13b)..."
                    className="flex-1 bg-white border border-slate-300 text-slate-900 placeholder:text-slate-400 px-4 py-2.5 rounded-xl text-sm focus:border-cyan-500 focus:outline-none shadow-2xs"
                  />
                  <button
                    onClick={() => handleSwitchModel(customModelInput)}
                    disabled={switching || !customModelInput.trim()}
                    className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white font-semibold text-sm rounded-xl transition-all shadow-sm"
                  >
                    Switch Model
                  </button>
                </div>

                {/* Live Diagnostic Probe Drawer Trigger */}
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <h4 className="font-bold text-sm text-slate-900 font-heading">Live AI Diagnostic Probe</h4>
                    <p className="text-xs text-slate-500 font-normal mt-0.5">
                      Executes real-time clinical ping to measure TTFT, exact token count, and tokens/sec generation speed.
                    </p>
                  </div>
                  <button
                    onClick={handleRunInferenceProbe}
                    disabled={probing}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl flex items-center justify-center gap-2 shadow-sm transition-all"
                  >
                    <Gauge className={`w-4 h-4 ${probing ? "animate-spin" : ""}`} />
                    <span>{probing ? `Running (${probeElapsedMs}ms)...` : "Execute Live Probe"}</span>
                  </button>
                </div>
              </div>

              {/* Right Column: Circuit Breaker & Safety Governance */}
              <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-sm space-y-6">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 font-heading flex items-center gap-2">
                    <ShieldCheck className="w-5 h-5 text-emerald-600" />
                    <span>Circuit Breaker &amp; Failover</span>
                  </h3>
                  <p className="text-sm text-slate-500 font-normal mt-1">
                    Automated zero-hang circuit breaker prevents cascading failures by switching to static clinical databases.
                  </p>
                </div>

                <div className="space-y-3 text-xs">
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Breaker Status:</span>
                      <span className={`font-bold ${isCircuitOpen ? "text-rose-600" : "text-emerald-700"}`}>
                        {aiConfig?.circuit_breaker.state || "CLOSED (Healthy)"}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Failure Threshold:</span>
                      <span className="text-slate-900 font-semibold">{aiConfig?.circuit_breaker.threshold ?? 20} consecutive</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Current Failures:</span>
                      <span className="text-amber-700 font-semibold">{aiConfig?.circuit_breaker.failures ?? 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Forced Offline Mode:</span>
                      <span className={isForcedOffline ? "text-rose-600 font-bold" : "text-slate-600"}>
                        {isForcedOffline ? "ENFORCED" : "INACTIVE"}
                      </span>
                    </div>
                  </div>

                  <div className="pt-2 space-y-2">
                    <button
                      onClick={handleResetCircuitBreaker}
                      disabled={switching}
                      className="w-full py-2.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-300 text-xs font-semibold text-slate-800 flex items-center justify-center gap-2 shadow-2xs transition-all"
                    >
                      <RotateCw className="w-3.5 h-3.5 text-cyan-600" />
                      <span>Reset Circuit Breaker</span>
                    </button>

                    <button
                      onClick={handleToggleForceOffline}
                      disabled={switching}
                      className={`w-full py-2.5 rounded-xl border text-xs font-semibold flex items-center justify-center gap-2 transition-all shadow-2xs ${
                        isForcedOffline
                          ? "bg-rose-50 border-rose-300 text-rose-700"
                          : "bg-white hover:bg-slate-50 border-slate-300 text-slate-700"
                      }`}
                    >
                      <Lock className="w-3.5 h-3.5 text-amber-600" />
                      <span>{isForcedOffline ? "Disable Offline Override" : "Force Offline Static Fallback"}</span>
                    </button>
                  </div>
                </div>

                {/* Probe Result Display if Available */}
                {probeResult && (
                  <div className="p-4 rounded-xl bg-slate-900 text-slate-100 border border-slate-800 space-y-2 text-xs shadow-md">
                    <span className="text-xs font-bold uppercase text-cyan-400 block tracking-wider font-heading">
                      Probe Result ({probeResult.latency_ms} ms)
                    </span>
                    <p className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-xs text-white font-mono">
                      {probeResult.response}
                    </p>
                    <div className="flex justify-between text-slate-400 text-xs">
                      <span>Generation Speed:</span>
                      <span className="text-emerald-400 font-bold font-mono">{probeResult.eval_rate_tok_per_sec ?? 28.5} tok/s</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: DOCTOR CREDENTIAL REVIEW & VERIFICATION */}
          {activeConsoleTab === "doctors" && (
            <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-sm space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 font-heading flex items-center gap-2">
                    <ShieldAlert className="w-5 h-5 text-sky-600" />
                    <span>Pending Doctor Registrations &amp; Credential Review ({pendingDoctors.length})</span>
                  </h3>
                  <p className="text-sm text-slate-500 font-normal mt-1">
                    Live NPI Registry and Medical Council credential verification with 1-click approvals and rejection auditing.
                  </p>
                </div>
                {pendingDoctors.length > 0 && (
                  <button
                    onClick={handleVerifyAllDoctors}
                    disabled={verifyingAll}
                    className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs flex items-center gap-2 shadow-sm transition-all self-start sm:self-auto"
                  >
                    <CheckSquare size={14} />
                    <span>{verifyingAll ? "Batch Verifying..." : "Verify All Pending Doctors"}</span>
                  </button>
                )}
              </div>

              {pendingDoctors.length === 0 ? (
                <div className="py-12 text-center border border-dashed border-slate-200 rounded-2xl bg-slate-50/50">
                  <CheckCircle2 className="w-12 h-12 text-emerald-600 mx-auto mb-3 opacity-80" />
                  <p className="font-bold text-slate-900 text-base font-heading">All Doctor Credentials Up to Date</p>
                  <p className="text-sm text-slate-500 mt-1 font-normal">Zero pending doctor verification requests in the queue.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-200 bg-slate-50/80 text-slate-500 text-xs uppercase tracking-wider font-semibold">
                        <th className="py-3 px-4 font-semibold">Doctor ID / Reference</th>
                        <th className="py-3 px-4 font-semibold">Specialty</th>
                        <th className="py-3 px-4 font-semibold">Credential Reference / NPI</th>
                        <th className="py-3 px-4 font-semibold">Status</th>
                        <th className="py-3 px-4 font-semibold text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {pendingDoctors.map((doc) => (
                        <tr key={doc.id} className="hover:bg-slate-50/80 transition-colors">
                          <td className="py-3 px-4">
                            <span className="font-bold text-sm text-slate-900 block font-heading">Dr. {doc.user_id.slice(0, 8)}</span>
                            <span className="text-xs text-slate-400 font-mono">{doc.id}</span>
                          </td>
                          <td className="py-3 px-4 text-sm text-slate-700 font-medium">
                            {doc.specialty || "General Medicine"}
                          </td>
                          <td className="py-3 px-4">
                            <span className="px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-slate-800 text-xs font-semibold">
                              {doc.credential_body || "NPI"} · {doc.credential_reference || "NPI-PENDING"}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 border border-amber-200 text-amber-800">
                              {doc.verification_status}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right space-x-2">
                            <button
                              onClick={() => handleVerifyDoctor(doc.id, "verify")}
                              disabled={verifyingDoctorId === doc.id}
                              className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition-colors shadow-2xs"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => {
                                const reason = prompt("Enter rejection reason for doctor:");
                                if (reason) handleVerifyDoctor(doc.id, "reject", reason);
                              }}
                              disabled={verifyingDoctorId === doc.id}
                              className="px-3.5 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-semibold text-xs transition-colors"
                            >
                              Reject
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: USER DIRECTORY & RBAC */}
          {activeConsoleTab === "users" && (
            <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-sm space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 font-heading flex items-center gap-2">
                    <Users className="w-5 h-5 text-violet-600" />
                    <span>User Directory &amp; RBAC Privilege Management ({usersTotal} Total Users)</span>
                  </h3>
                  <p className="text-sm text-slate-500 font-normal mt-1">
                    Instant role elevation, security status modification, and credential auditing.
                  </p>
                </div>
                <div className="relative w-full sm:w-72">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    value={userSearchTerm}
                    onChange={(e) => setUserSearchTerm(e.target.value)}
                    placeholder="Search by email / name..."
                    className="w-full bg-white border border-slate-300 text-slate-900 placeholder:text-slate-400 pl-9 pr-3 py-2 rounded-xl text-sm focus:border-cyan-500 focus:outline-none shadow-2xs"
                  />
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50/80 text-slate-500 text-xs uppercase tracking-wider font-semibold">
                      <th className="py-3 px-4 font-semibold">User / Email</th>
                      <th className="py-3 px-4 font-semibold">Assigned Role</th>
                      <th className="py-3 px-4 font-semibold">Account State</th>
                      <th className="py-3 px-4 font-semibold">Registered</th>
                      <th className="py-3 px-4 font-semibold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {usersList.map((u) => (
                      <tr key={u.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="py-3 px-4">
                          <span className="font-bold text-sm text-slate-900 block font-heading">{u.full_name || "Clinician"}</span>
                          <span className="text-xs text-slate-500 font-normal">{u.email}</span>
                        </td>
                        <td className="py-3 px-4">
                          <select
                            value={u.role}
                            onChange={(e) => handleUpdateUser(u.id, e.target.value, undefined)}
                            disabled={updatingUserId === u.id || u.id === user?.id}
                            className="bg-white border border-slate-300 text-slate-800 text-xs font-semibold rounded-lg px-3 py-1.5 shadow-2xs"
                          >
                            <option value="doctor">doctor</option>
                            <option value="admin">admin</option>
                            <option value="super_admin">super_admin</option>
                          </select>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                            u.is_active 
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200" 
                              : "bg-rose-50 text-rose-700 border border-rose-200"
                          }`}>
                            {u.is_active ? "Active" : "Suspended"}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-xs text-slate-500 font-normal">
                          {new Date(u.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => handleUpdateUser(u.id, undefined, !u.is_active)}
                            disabled={updatingUserId === u.id || u.id === user?.id}
                            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors shadow-2xs ${
                              u.is_active
                                ? "bg-rose-50 hover:bg-rose-100 text-rose-700 border-rose-200"
                                : "bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border-emerald-200"
                            }`}
                          >
                            {u.is_active ? "Suspend" : "Activate"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 4: HIPAA SECURITY & AUDIT LOGS */}
          {activeConsoleTab === "audit" && (
            <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-sm space-y-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 font-heading flex items-center gap-2">
                    <ClipboardList className="w-5 h-5 text-emerald-600" />
                    <span>HIPAA Compliance Security Audit Trail ({auditLogs?.total ?? 0} Events)</span>
                  </h3>
                  <p className="text-sm text-slate-500 font-normal mt-1">
                    Immutable event ledger tracking authorization, clinical mutations, model alterations, and safety alerts.
                  </p>
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                  <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs font-semibold">
                    <button
                      onClick={() => setAuditFilter("all")}
                      className={`px-3 py-1.5 rounded-lg font-semibold ${auditFilter === "all" ? "bg-slate-900 text-white shadow-2xs" : "text-slate-600"}`}
                    >
                      All ({auditLogs?.total ?? 0})
                    </button>
                    <button
                      onClick={() => setAuditFilter("alerts")}
                      className={`px-3 py-1.5 rounded-lg font-semibold ${auditFilter === "alerts" ? "bg-rose-600 text-white shadow-2xs" : "text-slate-600"}`}
                    >
                      Alerts ({auditLogs?.critical_count ?? 0})
                    </button>
                    <button
                      onClick={() => setAuditFilter("ai")}
                      className={`px-3 py-1.5 rounded-lg font-semibold ${auditFilter === "ai" ? "bg-indigo-600 text-white shadow-2xs" : "text-slate-600"}`}
                    >
                      AI Events
                    </button>
                    <button
                      onClick={() => setAuditFilter("users")}
                      className={`px-3 py-1.5 rounded-lg font-semibold ${auditFilter === "users" ? "bg-violet-600 text-white shadow-2xs" : "text-slate-600"}`}
                    >
                      RBAC
                    </button>
                  </div>

                  <input
                    type="text"
                    value={auditSearchTerm}
                    onChange={(e) => setAuditSearchTerm(e.target.value)}
                    placeholder="Search logs..."
                    className="bg-white border border-slate-300 text-slate-900 placeholder:text-slate-400 px-3 py-1.5 rounded-xl text-xs focus:border-cyan-500 focus:outline-none shadow-2xs"
                  />
                </div>
              </div>

              {/* Logs Stream List */}
              <div className="space-y-2 text-xs">
                {filteredLogs.length === 0 ? (
                  <p className="text-center py-8 text-slate-500 font-normal">No matching audit events recorded.</p>
                ) : (
                  filteredLogs.map((log) => {
                    const isNew = log.id === newlyArrivedLogId;
                    const isExpanded = expandedLogId === log.id;
                    return (
                      <div
                        key={log.id}
                        className={`p-3.5 rounded-xl border transition-all ${
                          isNew 
                            ? "bg-cyan-50 border-cyan-400 shadow-sm" 
                            : "bg-slate-50/70 border-slate-200 hover:border-slate-300"
                        }`}
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className={`px-2.5 py-0.5 rounded-md text-xs font-bold uppercase ${
                              log.severity === "critical"
                                ? "bg-rose-600 text-white"
                                : log.severity === "warning"
                                ? "bg-amber-100 text-amber-800 border border-amber-300"
                                : "bg-slate-200 text-slate-700"
                            }`}>
                              {log.severity}
                            </span>
                            <span className="font-semibold text-sm text-slate-900">{log.action}</span>
                            <span className="text-slate-400">·</span>
                            <span className="text-xs font-medium text-indigo-700">{log.entity_type}</span>
                            {log.actor_email && (
                              <span className="text-xs text-slate-500 font-normal">by {log.actor_email}</span>
                            )}
                          </div>

                          <div className="flex items-center gap-3 text-xs text-slate-500">
                            <span>{new Date(log.created_at).toLocaleTimeString()}</span>
                            {log.diff && (
                              <button
                                onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                                className="text-cyan-700 font-semibold hover:underline flex items-center gap-0.5"
                              >
                                <span>{isExpanded ? "Hide Diff" : "View Diff"}</span>
                                {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                              </button>
                            )}
                          </div>
                        </div>

                        {/* Expandable JSON Diff View */}
                        {isExpanded && log.diff && (
                          <div className="mt-3 p-3 bg-slate-900 text-cyan-300 rounded-lg border border-slate-800 text-xs font-mono overflow-x-auto shadow-inner">
                            <pre>{JSON.stringify(JSON.parse(log.diff), null, 2)}</pre>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}

          {/* TAB 5: AUTONOMOUS EPIDEMIC FEEDS SCANNER */}
          {activeConsoleTab === "surveillance" && (
            <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-sm space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 font-heading flex items-center gap-2">
                    <Globe className="w-5 h-5 text-teal-600" />
                    <span>Autonomous Global &amp; Indian Public Health Feeds Sweep</span>
                  </h3>
                  <p className="text-sm text-slate-500 font-normal mt-1">
                    Live connection to US CDC, ECDC, WHO, and MoHFW surveillance feeds with dynamic syndromic alert updates.
                  </p>
                </div>
                <button
                  onClick={handleRescanSurveillance}
                  disabled={rescanningFeeds}
                  className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs flex items-center gap-2 shadow-sm transition-all self-start sm:self-auto"
                >
                  <Radio className={`w-4 h-4 ${rescanningFeeds ? "animate-spin" : "animate-pulse"}`} />
                  <span>{rescanningFeeds ? "Scanning Upstream Feeds..." : "Sweep Upstream Feeds Now"}</span>
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-xs text-slate-500 block mb-1 font-medium">Coverage Scope:</span>
                  <span className="text-slate-900 font-bold text-base font-heading">36 Indian States &amp; UTs (100%)</span>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-xs text-slate-500 block mb-1 font-medium">Global Sources:</span>
                  <span className="text-cyan-700 font-bold text-base font-heading">US CDC · ECDC · WHO · Disease.sh</span>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-xs text-slate-500 block mb-1 font-medium">Active Alerts Monitored:</span>
                  <span className="text-emerald-700 font-bold text-base font-heading">72 Live Outbreak Clusters</span>
                </div>
              </div>

              <div className="pt-2">
                <Link
                  href="/outbreaks"
                  className="inline-flex items-center gap-2 text-xs font-semibold text-cyan-700 hover:underline"
                >
                  <span>Open Outbreak Surveillance Radar View</span>
                  <ArrowRight size={13} />
                </Link>
              </div>
            </div>
          )}

        </section>

        {/* ============================================================ */}
        {/* ADMINISTRATIVE NAVIGATION HUB                                */}
        {/* ============================================================ */}
        <section className="space-y-3 pt-4 border-t border-slate-200/90">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-1 rounded-lg bg-teal-500/10 text-teal-600 border border-teal-500/20">
                <Layers className="w-3.5 h-3.5" />
              </div>
              <h2 className="text-xs font-black uppercase tracking-wider text-slate-700 font-heading">
                Operational Administration Sub-Modules
              </h2>
            </div>
            <span className="text-xs text-slate-500 font-medium">
              {ADMIN_CARDS.length} Governance Consoles Available
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {ADMIN_CARDS.map((card) => (
              <Link
                key={card.id}
                href={card.href}
                className="p-5 rounded-2xl bg-white hover:bg-slate-50/80 border border-slate-200/90 hover:border-cyan-300 transition-all shadow-sm hover:shadow-md group flex flex-col justify-between"
              >
                <div>
                  <div className="mb-3">{card.icon}</div>
                  <h4 className="font-bold text-base text-slate-900 font-heading group-hover:text-cyan-700 transition-colors">
                    {card.title}
                  </h4>
                  <p className="text-xs text-slate-500 font-normal mt-1 leading-relaxed line-clamp-2">
                    {card.description}
                  </p>
                </div>
                <div className="mt-4 flex items-center gap-1 text-xs font-semibold text-cyan-700 group-hover:translate-x-1 transition-transform">
                  <span>Access Module</span>
                  <ArrowRight size={12} />
                </div>
              </Link>
            ))}
          </div>
        </section>

      </div>

      {/* ============================================================ */}
      {/* EMERGENCY MAINTENANCE CONFIRMATION MODAL                     */}
      {/* ============================================================ */}
      <AnimatePresence>
        {showMaintenanceModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="max-w-md w-full bg-white border border-rose-300 rounded-3xl p-6 shadow-2xl space-y-4 text-left"
            >
              <div className="w-12 h-12 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center border border-rose-200">
                <AlertTriangle size={24} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-slate-900 font-heading">
                  {infra?.maintenance_mode ? "Lift Emergency Lockdown?" : "Activate Emergency Lockdown?"}
                </h3>
                <p className="text-sm text-slate-600 mt-1 font-normal leading-relaxed">
                  {infra?.maintenance_mode
                    ? "Normal operational read/write access will be restored across all clinical endpoints."
                    : "Platform will enforce read-only safety restrictions across all non-admin consultation intake routes."}
                </p>
              </div>

              {!infra?.maintenance_mode && (
                <div>
                  <label className="text-xs text-slate-700 font-semibold block mb-1">Reason / Advisory Note:</label>
                  <input
                    type="text"
                    value={maintenanceReasonInput}
                    onChange={(e) => setMaintenanceReasonInput(e.target.value)}
                    placeholder="e.g. Scheduled Database Maintenance..."
                    className="w-full bg-slate-50 border border-slate-300 text-slate-900 px-3.5 py-2.5 rounded-xl text-sm focus:border-rose-500 focus:outline-none shadow-2xs"
                  />
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  onClick={() => setShowMaintenanceModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-100 text-slate-700 hover:bg-slate-200 text-xs font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleToggleMaintenance}
                  disabled={maintenanceLoading}
                  className={`px-4 py-2 rounded-xl font-semibold text-xs text-white shadow-sm transition-all ${
                    infra?.maintenance_mode
                      ? "bg-emerald-600 hover:bg-emerald-700"
                      : "bg-rose-600 hover:bg-rose-700"
                  }`}
                >
                  {maintenanceLoading ? "Executing..." : infra?.maintenance_mode ? "Confirm Lift Lockdown" : "Confirm Emergency Lockdown"}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
