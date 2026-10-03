"use client";

import { useEffect, useState, useRef } from "react";
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
  type AdminStatsResponse, 
  type ReadinessResponse, 
  type AdminAIConfigResponse,
  type AdminAuditLogsResponse,
  type AuditLogItem,
  type ProbeAIResponse,
} from "@/lib/api";
import { getSharedRealtimeClient, type WSConnectionState } from "@/lib/ws";
import { 
  Activity, Users, ShieldAlert, Database, Server, ClipboardList, BookOpen, 
  Layers, TestTube2, FlaskConical, HardDrive, CheckCircle2, AlertCircle, Cpu, 
  Zap, RefreshCw, Radio, Sparkles, Check, ArrowRight, Lock, Unlock, Stethoscope,
  Terminal, ShieldCheck, Gauge, AlertTriangle, Eye, ChevronDown, ChevronUp, Clock, Globe,
  Wifi, WifiOff, Play, Pause, Flame
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

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
    icon: <Users size={28} className="text-violet-500" />,
    id: "admin-card-users",
  },
  {
    href: "/admin/doctors",
    title: "Doctor Verifications",
    description: "Review and approve or reject pending doctor credential submissions.",
    icon: <ShieldAlert size={28} className="text-sky-500" />,
    id: "admin-card-doctors",
  },
  {
    href: "/admin/sources",
    title: "Medical Sources",
    description: "Manage and verify clinical knowledge sources for the registry.",
    icon: <BookOpen size={28} className="text-emerald-500" />,
    id: "admin-card-sources",
  },
  {
    href: "/admin/ingestion",
    title: "Knowledge Ingestion",
    description: "Monitor background ingestion queues and review parsed knowledge.",
    icon: <Server size={28} className="text-purple-500" />,
    id: "admin-card-ingestion",
  },
  {
    href: "/admin/knowledge",
    title: "Knowledge Publication",
    description: "Safely review and publish clinical knowledge to production.",
    icon: <ClipboardList size={28} className="text-blue-500" />,
    id: "admin-card-knowledge",
  },
  {
    href: "/admin/datasets",
    title: "Dataset Registry & Governance",
    description: "Manage ML datasets and enforce PII validation rules.",
    icon: <Database size={28} className="text-indigo-500" />,
    id: "admin-card-datasets",
  },
  {
    href: "/admin/evaluations",
    title: "Baseline Evaluation Harness",
    description: "Run repeatable metrics against fixed hold-out datasets.",
    icon: <TestTube2 size={28} className="text-pink-500" />,
    id: "admin-card-evaluations",
  },
  {
    href: "/admin/experiments",
    title: "ML Experiment Tracking",
    description: "Track model training runs, hyperparameters, and artifacts.",
    icon: <FlaskConical size={28} className="text-rose-500" />,
    id: "admin-card-experiments",
  },
];

export default function AdminPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<AdminStatsResponse | null>(null);
  const [health, setHealth] = useState<ReadinessResponse | null>(null);
  const [aiConfig, setAiConfig] = useState<AdminAIConfigResponse | null>(null);
  const [auditLogs, setAuditLogs] = useState<AdminAuditLogsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  
  // Real-time WebSocket and telemetry stream state
  const [wsState, setWsState] = useState<WSConnectionState>("UNAVAILABLE");
  const [refreshIntervalMs, setRefreshIntervalMs] = useState<number>(3000);
  const [isLivePulse, setIsLivePulse] = useState(false);
  const [newlyArrivedLogId, setNewlyArrivedLogId] = useState<string | null>(null);

  // Model switching & Circuit breaker mutation state
  const [switching, setSwitching] = useState(false);
  const [customModelInput, setCustomModelInput] = useState("");
  const [actionFeedback, setActionFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Live Diagnostic AI Inference Probe state
  const [probing, setProbing] = useState(false);
  const [probeElapsedMs, setProbeElapsedMs] = useState<number>(0);
  const [probeResult, setProbeResult] = useState<ProbeAIResponse | null>(null);
  const [probeError, setProbeError] = useState<string | null>(null);
  const [showProbeDrawer, setShowProbeDrawer] = useState<boolean>(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Audit feed UI state
  const [auditFilter, setAuditFilter] = useState<"all" | "alerts" | "ai" | "users">("all");
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);

  const isAdmin = user?.role === "admin" || user?.role === "super_admin";

  const fetchTelemetry = async (isManual = false) => {
    if (isManual) setSyncing(true);
    try {
      const [statsRes, healthRes, aiRes, auditRes] = await Promise.all([
        getAdminStats(),
        getReady(),
        getAdminAIConfig(),
        getAdminAuditLogs({ limit: 30 }),
      ]);
      if (statsRes.ok) setStats(statsRes.data);
      if (healthRes.ok) setHealth(healthRes.data);
      if (aiRes.ok) setAiConfig(aiRes.data);
      if (auditRes.ok) setAuditLogs(auditRes.data);
      setLastUpdated(new Date());
      setIsLivePulse(true);
      setTimeout(() => setIsLivePulse(false), 800);
    } finally {
      setLoading(false);
      if (isManual) setSyncing(false);
    }
  };

  // 1. Establish Bi-directional Real-Time WebSocket Streaming
  useEffect(() => {
    if (!isAdmin) {
      setLoading(false);
      return;
    }

    const token = getStoredToken() || (typeof window !== "undefined" ? localStorage.getItem("access_token") : null) || "";
    const client = getSharedRealtimeClient(token);

    // Track real-time connection state
    const unsubState = client.subscribeState((state) => {
      setWsState(state);
    });

    // Handle real-time push events from backend without waiting for polling
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

        // Instantly increment platform stats in real time
        setStats((prev) => {
          if (!prev) return prev;
          const updated = { ...prev };
          if (newLog.severity === "critical") {
            updated.active_critical_alerts = (updated.active_critical_alerts ?? 0) + 1;
            updated.total_safety_alerts = (updated.total_safety_alerts ?? 0) + 1;
          } else if (newLog.severity === "warning") {
            updated.total_safety_alerts = (updated.total_safety_alerts ?? 0) + 1;
          }
          if (newLog.action.includes("consultation")) {
            updated.total_consultations = (updated.total_consultations ?? 0) + 1;
          }
          return updated;
        });
      }

      if (type === "ai.model_switched" || type === "ai.circuit_breaker_reset" || type === "circuit_breaker.updated") {
        if (payload && payload.active_model) {
          setAiConfig(payload as AdminAIConfigResponse);
        } else {
          getAdminAIConfig().then((res) => { if (res.ok) setAiConfig(res.data); });
        }
      }

      if (type === "user.updated") {
        getAdminStats().then((res) => { if (res.ok) setStats(res.data); });
      }
    });

    return () => {
      unsubState();
      unsubMessages();
    };
  }, [isAdmin]);

  // 2. Telemetry polling loop with user-configurable refresh frequency
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
  }, [isAdmin, refreshIntervalMs]);

  // Clean up stopwatch on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const handleSwitchModel = async (targetModel: string) => {
    const cleaned = targetModel.trim();
    if (!cleaned || switching) return;
    setSwitching(true);
    setActionFeedback(null);
    try {
      const res = await switchAdminAIModel({ model_name: cleaned });
      if (res.ok) {
        setAiConfig(res.data);
        setCustomModelInput("");
        setActionFeedback({
          type: "success",
          text: `System AI model successfully switched to "${res.data.active_model}" across all services in real time!`,
        });
        const auditRes = await getAdminAuditLogs({ limit: 30 });
        if (auditRes.ok) setAuditLogs(auditRes.data);
      } else {
        setActionFeedback({
          type: "error",
          text: res.error?.message || "Failed to switch system AI model.",
        });
      }
    } catch {
      setActionFeedback({
        type: "error",
        text: "Network error occurred while communicating with admin AI config.",
      });
    } finally {
      setSwitching(false);
    }
  };

  const handleResetCircuitBreaker = async () => {
    if (switching) return;
    setSwitching(true);
    setActionFeedback(null);
    try {
      const res = await resetAdminCircuitBreaker();
      if (res.ok) {
        setAiConfig(res.data);
        setActionFeedback({
          type: "success",
          text: "Circuit breaker manually reset. Normal live inference mode restored.",
        });
        const auditRes = await getAdminAuditLogs({ limit: 30 });
        if (auditRes.ok) setAuditLogs(auditRes.data);
      } else {
        setActionFeedback({
          type: "error",
          text: res.error?.message || "Failed to reset circuit breaker.",
        });
      }
    } catch {
      setActionFeedback({
        type: "error",
        text: "Network error occurred while resetting circuit breaker.",
      });
    } finally {
      setSwitching(false);
    }
  };

  const handleToggleForceOffline = async () => {
    if (!aiConfig || switching) return;
    setSwitching(true);
    setActionFeedback(null);
    const willForce = !aiConfig.circuit_breaker.forced_offline;
    try {
      const res = await switchAdminAIModel({
        model_name: aiConfig.active_model,
        force_offline: willForce,
      });
      if (res.ok) {
        setAiConfig(res.data);
        setActionFeedback({
          type: "success",
          text: willForce
            ? "Offline Fallback Mode enforced. All system inferences are now safely serviced by static clinical knowledge."
            : "Deterministic offline override disabled. Resumed live LLM connectivity.",
        });
        const auditRes = await getAdminAuditLogs({ limit: 30 });
        if (auditRes.ok) setAuditLogs(auditRes.data);
      } else {
        setActionFeedback({
          type: "error",
          text: res.error?.message || "Failed to toggle offline fallback mode.",
        });
      }
    } catch {
      setActionFeedback({
        type: "error",
        text: "Network error occurred while toggling fallback mode.",
      });
    } finally {
      setSwitching(false);
    }
  };

  // Run live diagnostic inference probe with live stopwatch
  const handleRunInferenceProbe = async () => {
    if (probing) return;
    setProbing(true);
    setProbeError(null);
    setProbeResult(null);
    setShowProbeDrawer(true);
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
        // Refresh aiConfig to update latency
        getAdminAIConfig().then((aiRes) => {
          if (aiRes.ok) setAiConfig(aiRes.data);
        });
      } else {
        setProbeError(res.error?.message || "Inference probe failed to communicate with AI engine.");
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

  if (!user) return null;

  if (!isAdmin) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center p-8">
        <div className="glass-panel-4k p-10 rounded-3xl border border-slate-200/90 bg-white/85 backdrop-blur-2xl shadow-xl max-w-md text-center ring-1 ring-black/5">
          <div className="w-16 h-16 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto mb-4 border border-amber-200 shadow-inner">
            <ShieldAlert size={32} />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2 font-heading">
            Administrator Access Required
          </h2>
          <p className="text-slate-500 mb-6 text-sm leading-relaxed">
            Your account ({user.email}) has the <strong>{user.role}</strong> role. The System Command Center is restricted to platform administrators.
          </p>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-sm transition-colors shadow-md shadow-slate-900/10"
          >
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const isCircuitOpen = aiConfig?.circuit_breaker.is_open ?? false;
  const isForcedOffline = aiConfig?.circuit_breaker.forced_offline ?? false;
  const isLiveLLM = aiConfig?.mode === "llm_active";

  // Filter audit logs based on tab selection
  const filteredLogs = (auditLogs?.items || []).filter((log) => {
    if (auditFilter === "alerts") return log.severity === "warning" || log.severity === "critical";
    if (auditFilter === "ai") return log.entity_type === "ai_engine" || log.action.includes("model") || log.action.includes("circuit");
    if (auditFilter === "users") return log.entity_type === "user" || log.action.includes("user") || log.action.includes("rbac") || log.action.includes("auth");
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-50 relative overflow-hidden p-6 md:p-8 pt-10">
      {/* Animated background shapes */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-300/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '8s' }}></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-300/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '12s' }}></div>
      
      {/* Dot Grid Overlay */}
      <div className="absolute inset-0 z-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>

      <div className="max-w-7xl mx-auto space-y-10 relative z-10">
        
        {/* Header & Real-Time Telemetry Control Bar */}
        <header className="flex flex-col lg:flex-row lg:items-end justify-between gap-6 pb-2">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="relative p-2.5 bg-emerald-500/10 rounded-xl border border-emerald-500/20 shadow-sm overflow-hidden">
                <div className="absolute inset-0 bg-emerald-400/20 animate-pulse"></div>
                <Activity size={28} className="text-emerald-600 relative z-10" />
              </div>
              <h1 className="text-4xl font-bold text-slate-900 tracking-tight font-heading">
                System Command Center
              </h1>
            </div>
            <p className="text-slate-500 text-base md:text-lg max-w-2xl font-medium">
              Global platform telemetry, live AI engine controls, HIPAA compliance audit trail, and user RBAC.
            </p>
          </div>
          
          {/* Real-time Streaming Status & Frequency Toolbar */}
          <div className="flex flex-wrap items-center gap-2.5 bg-white/85 backdrop-blur-xl p-2 rounded-2xl border border-slate-200/90 shadow-md">
            
            {/* WebSocket Stream Indicator Badge */}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-bold border transition-colors ${
              wsState === 'LIVE'
                ? "bg-emerald-50 border-emerald-300 text-emerald-700"
                : wsState === 'CONNECTING' || wsState === 'RECONNECTING'
                ? "bg-amber-50 border-amber-300 text-amber-700 animate-pulse"
                : "bg-slate-100 border-slate-300 text-slate-600"
            }`}>
              {wsState === 'LIVE' ? (
                <>
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                  </span>
                  <Wifi size={13} className="text-emerald-600" />
                  <span>WS STREAM ACTIVE</span>
                </>
              ) : wsState === 'RECONNECTING' ? (
                <>
                  <RefreshCw size={13} className="animate-spin text-amber-600" />
                  <span>RECONNECTING...</span>
                </>
              ) : (
                <>
                  <WifiOff size={13} className="text-slate-400" />
                  <span>HTTP POLLING</span>
                </>
              )}
            </div>

            {/* Stream Refresh Rate Selector */}
            <div className="flex items-center gap-1 bg-slate-100/80 p-1 rounded-xl text-xs font-semibold text-slate-600">
              <span className="px-2 text-[11px] uppercase tracking-wider text-slate-400 font-bold hidden sm:inline">
                Rate:
              </span>
              <button
                onClick={() => setRefreshIntervalMs(1000)}
                title="Hyper Real-Time: Poll every 1 second"
                className={`px-2.5 py-1 rounded-lg transition-all flex items-center gap-1 ${
                  refreshIntervalMs === 1000 
                    ? "bg-slate-900 text-white shadow-xs font-bold" 
                    : "hover:bg-slate-200 text-slate-700"
                }`}
              >
                <Flame size={12} className={refreshIntervalMs === 1000 ? "text-amber-400" : ""} />
                1s
              </button>
              <button
                onClick={() => setRefreshIntervalMs(3000)}
                title="Standard Real-Time: Poll every 3 seconds"
                className={`px-2.5 py-1 rounded-lg transition-all ${
                  refreshIntervalMs === 3000 
                    ? "bg-slate-900 text-white shadow-xs font-bold" 
                    : "hover:bg-slate-200 text-slate-700"
                }`}
              >
                3s
              </button>
              <button
                onClick={() => setRefreshIntervalMs(5000)}
                title="Balanced: Poll every 5 seconds"
                className={`px-2.5 py-1 rounded-lg transition-all ${
                  refreshIntervalMs === 5000 
                    ? "bg-slate-900 text-white shadow-xs font-bold" 
                    : "hover:bg-slate-200 text-slate-700"
                }`}
              >
                5s
              </button>
              <button
                onClick={() => setRefreshIntervalMs(refreshIntervalMs === 0 ? 3000 : 0)}
                title={refreshIntervalMs === 0 ? "Resume telemetry streaming" : "Freeze telemetry streaming"}
                className={`px-2 py-1 rounded-lg transition-all ${
                  refreshIntervalMs === 0 
                    ? "bg-amber-600 text-white font-bold" 
                    : "hover:bg-slate-200 text-slate-500"
                }`}
              >
                {refreshIntervalMs === 0 ? <Play size={12} /> : <Pause size={12} />}
              </button>
            </div>

            {/* Manual Sync Now Button */}
            <button
              onClick={() => fetchTelemetry(true)}
              disabled={syncing}
              title="Force synchronous telemetry refresh"
              className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 active:scale-95 transition-all text-slate-700"
            >
              <RefreshCw size={14} className={syncing || isLivePulse ? "animate-spin text-emerald-600" : ""} />
            </button>

            <span className="text-[11px] font-mono text-slate-400 pl-1 pr-2 hidden md:inline">
              {lastUpdated.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' })}
            </span>
          </div>
        </header>

        {/* Action Feedback Banner */}
        <AnimatePresence>
          {actionFeedback && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`p-4 rounded-2xl flex items-center justify-between border shadow-lg ${
                actionFeedback.type === "success"
                  ? "bg-emerald-50/95 border-emerald-200 text-emerald-900 shadow-emerald-500/10"
                  : "bg-rose-50/95 border-rose-200 text-rose-900 shadow-rose-500/10"
              }`}
            >
              <div className="flex items-center gap-3">
                {actionFeedback.type === "success" ? (
                  <CheckCircle2 size={20} className="text-emerald-600 shrink-0" />
                ) : (
                  <AlertCircle size={20} className="text-rose-600 shrink-0" />
                )}
                <span className="text-sm font-semibold">{actionFeedback.text}</span>
              </div>
              <button
                onClick={() => setActionFeedback(null)}
                className="text-xs px-2.5 py-1 rounded-lg bg-black/5 hover:bg-black/10 transition-colors font-medium ml-4"
              >
                Dismiss
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Real-time Metrics Overview (Computed by Backend) */}
        <section className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <MetricCard 
            title="Total Consultations" 
            value={stats?.total_consultations} 
            loading={loading}
            delay={0}
            icon={<Stethoscope className="text-teal-500" size={22} />}
            gradient="from-teal-500/15 to-transparent"
          />
          <MetricCard 
            title="Safety Alerts" 
            value={stats?.total_safety_alerts} 
            loading={loading}
            delay={0.05}
            icon={<ShieldAlert className={stats?.active_critical_alerts ? "text-rose-500 animate-pulse" : "text-amber-500"} size={22} />}
            gradient={stats?.active_critical_alerts ? "from-rose-500/20 to-transparent" : "from-amber-500/15 to-transparent"}
            alert={!!stats?.active_critical_alerts}
            subtitle={stats?.active_critical_alerts ? `${stats.active_critical_alerts} Critical Active` : "All clear"}
          />
          <MetricCard 
            title="Total Users" 
            value={stats?.total_users} 
            loading={loading}
            delay={0.1}
            icon={<Users className="text-blue-500" size={22} />}
            gradient="from-blue-500/15 to-transparent"
          />
          <MetricCard 
            title="Registered Doctors" 
            value={stats?.total_doctors} 
            loading={loading}
            delay={0.15}
            icon={<Activity className="text-emerald-500" size={22} />}
            gradient="from-emerald-500/15 to-transparent"
          />
          <MetricCard 
            title="Platform Admins" 
            value={stats?.total_admins} 
            loading={loading}
            delay={0.2}
            icon={<Server className="text-purple-500" size={22} />}
            gradient="from-purple-500/15 to-transparent"
          />
          <MetricCard 
            title="Pending Verifications" 
            value={stats?.pending_verifications} 
            loading={loading}
            delay={0.25}
            icon={<ShieldCheck className={stats?.pending_verifications ? "text-sky-500 animate-pulse" : "text-slate-400"} size={22} />}
            gradient={stats?.pending_verifications ? "from-sky-500/20 to-transparent" : "from-slate-500/5 to-transparent"}
            alert={!!stats?.pending_verifications}
          />
        </section>

        {/* ============================================================ */}
        {/* AI Provider & Circuit Breaker Health Card (System-Wide Control) */}
        {/* ============================================================ */}
        <section className="bg-gradient-to-br from-white/90 via-white/80 to-slate-50/90 backdrop-blur-2xl border border-slate-200/90 rounded-3xl p-6 md:p-8 shadow-2xl shadow-slate-300/40 relative overflow-hidden">
          {/* Subtle accent glow */}
          <div className={`absolute top-0 right-0 w-96 h-96 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20 opacity-25 ${isLiveLLM ? 'bg-emerald-400' : 'bg-amber-400'}`} />

          <div className="relative z-10 space-y-6">
            
            {/* Top Bar: Title & High-level Live State Badge */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-slate-200/70">
              <div className="flex items-center gap-3.5">
                <div className={`p-3 rounded-2xl border shadow-sm ${
                  isLiveLLM 
                    ? "bg-emerald-50 border-emerald-200 text-emerald-600" 
                    : "bg-amber-50 border-amber-200 text-amber-600"
                }`}>
                  {isLiveLLM ? <Zap size={24} className="animate-pulse" /> : <ShieldAlert size={24} />}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-2xl font-bold text-slate-900 font-heading">
                      AI Provider & Circuit Breaker Control
                    </h2>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 border border-slate-200">
                      System-Wide
                    </span>
                  </div>
                  <p className="text-sm text-slate-500 font-medium">
                    Immediate telemetry on active LLM vs offline fallback & dynamic system model switching.
                  </p>
                </div>
              </div>

              {/* Status Indicator Pill */}
              <div className="flex flex-wrap items-center gap-3">
                <div className={`flex items-center gap-2.5 px-4 py-2 rounded-2xl border text-sm font-bold shadow-sm ${
                  isLiveLLM 
                    ? "bg-emerald-500/10 text-emerald-700 border-emerald-300/80" 
                    : "bg-amber-500/15 text-amber-800 border-amber-300/90"
                }`}>
                  <span className="relative flex h-3 w-3">
                    {isLiveLLM ? (
                      <>
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                      </>
                    ) : (
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-amber-500"></span>
                    )}
                  </span>
                  <span>{isLiveLLM ? "LIVE LLM ACTIVE" : "OFFLINE FALLBACK MODE"}</span>
                </div>

                {/* Circuit Breaker State Pill */}
                <div className="px-3.5 py-1.5 rounded-xl bg-slate-100 border border-slate-200/90 text-xs font-mono font-semibold text-slate-700 flex items-center gap-2">
                  <span className="text-slate-400">CIRCUIT:</span>
                  <span className={`px-2 py-0.5 rounded font-bold ${
                    aiConfig?.circuit_breaker.state === "CLOSED" 
                      ? "bg-emerald-100 text-emerald-800" 
                      : aiConfig?.circuit_breaker.state === "FORCED_OFFLINE"
                      ? "bg-rose-100 text-rose-800"
                      : "bg-amber-100 text-amber-800"
                  }`}>
                    {aiConfig?.circuit_breaker.state || "CHECKING"}
                  </span>
                </div>
              </div>
            </div>

            {/* Diagnostic Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              
              {/* Active Model */}
              <div className="p-4 rounded-2xl bg-white/70 border border-slate-200/80 shadow-sm flex flex-col justify-between">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-500 mb-2">
                  <span className="flex items-center gap-1.5">
                    <Sparkles size={14} className="text-indigo-500" />
                    ACTIVE SYSTEM MODEL
                  </span>
                  <span className="text-[10px] uppercase font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">Global</span>
                </div>
                <div className="text-lg font-bold font-mono text-slate-900 truncate" title={aiConfig?.active_model}>
                  {aiConfig?.active_model || "Loading..."}
                </div>
                <div className="text-xs text-slate-500 mt-2 flex items-center justify-between">
                  <span>Fast/Edge: <strong className="font-mono text-slate-700">{aiConfig?.fast_model || "none"}</strong></span>
                </div>
              </div>

              {/* Provider Connection & Latency */}
              <div className="p-4 rounded-2xl bg-white/70 border border-slate-200/80 shadow-sm flex flex-col justify-between">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-500 mb-2">
                  <span className="flex items-center gap-1.5">
                    <Gauge size={14} className="text-emerald-500" />
                    LATENCY & HOST
                  </span>
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                    aiConfig?.is_connected ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"
                  }`}>
                    {aiConfig?.is_connected ? "Connected" : "Unreachable"}
                  </span>
                </div>
                <div className="text-2xl font-bold font-heading text-slate-900 flex items-baseline gap-1">
                  <span>{aiConfig?.latency_ms ?? "--"}</span>
                  <span className="text-xs text-slate-500 font-sans font-medium">ms</span>
                </div>
                <div className="text-xs text-slate-500 mt-2 truncate font-mono" title={aiConfig?.base_url}>
                  {aiConfig?.base_url || "http://localhost:11434"}
                </div>
              </div>

              {/* Circuit Breaker Failures */}
              <div className="p-4 rounded-2xl bg-white/70 border border-slate-200/80 shadow-sm flex flex-col justify-between">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-500 mb-2">
                  <span className="flex items-center gap-1.5">
                    <ShieldCheck size={14} className="text-sky-500" />
                    TRIP THRESHOLD
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">
                    Max: {aiConfig?.circuit_breaker.threshold ?? 3} fails
                  </span>
                </div>
                <div className="text-2xl font-bold font-heading text-slate-900 flex items-baseline gap-2">
                  <span className={aiConfig?.circuit_breaker.failures ? "text-amber-600" : "text-emerald-600"}>
                    {aiConfig?.circuit_breaker.failures ?? 0}
                  </span>
                  <span className="text-xs text-slate-400 font-sans font-medium">
                    / {aiConfig?.circuit_breaker.threshold ?? 3} failures
                  </span>
                </div>
                <div className="text-xs text-slate-500 mt-2">
                  Cooldown: <strong className="text-slate-700">{aiConfig?.circuit_breaker.recovery_s ?? 60}s</strong>
                </div>
              </div>

              {/* Active Recovery & Controls */}
              <div className="p-4 rounded-2xl bg-white/70 border border-slate-200/80 shadow-sm flex flex-col justify-between">
                <div className="text-xs font-semibold text-slate-500 mb-2 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Terminal size={14} className="text-purple-500" />
                    CIRCUIT CONTROLS
                  </span>
                </div>
                <div className="flex flex-col gap-2">
                  <button
                    onClick={handleResetCircuitBreaker}
                    disabled={switching}
                    id="admin-btn-reset-circuit-breaker"
                    className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-xl bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white text-xs font-semibold transition-all shadow-sm"
                  >
                    <RefreshCw size={13} className={switching ? "animate-spin" : ""} />
                    Reset Breaker
                  </button>
                  <button
                    onClick={handleToggleForceOffline}
                    disabled={switching}
                    id="admin-btn-toggle-force-offline"
                    className={`w-full flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-xl border text-xs font-semibold transition-all ${
                      isForcedOffline
                        ? "bg-emerald-50 border-emerald-300 text-emerald-700 hover:bg-emerald-100"
                        : "bg-amber-50 border-amber-300 text-amber-800 hover:bg-amber-100"
                    }`}
                  >
                    {isForcedOffline ? <Unlock size={13} /> : <Lock size={13} />}
                    {isForcedOffline ? "Resume Live Inference" : "Force Offline Fallback"}
                  </button>
                </div>
              </div>

            </div>

            {/* Live Diagnostic Inference Probe Section */}
            <div className="pt-2">
              <div className="p-4 rounded-2xl bg-slate-900 text-white border border-slate-800 shadow-xl space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                      <Zap size={18} className={probing ? "animate-spin text-amber-300" : ""} />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold font-heading text-slate-100 flex items-center gap-2">
                        Live AI Diagnostic Inference Probe
                        <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-400/20">
                          Real-Time Probe
                        </span>
                      </h4>
                      <p className="text-xs text-slate-400 font-medium">
                        Dispatches a round-trip clinical query to verify active model TTFT, token throughput rate, and live response stream.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={handleRunInferenceProbe}
                      disabled={probing}
                      id="admin-btn-run-live-probe"
                      className="px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 disabled:opacity-50 text-white text-xs font-bold transition-all shadow-md shadow-indigo-500/20 flex items-center gap-2"
                    >
                      <Zap size={14} className={probing ? "animate-spin text-amber-300" : "text-amber-300"} />
                      {probing ? `Probing Live LLM (${probeElapsedMs} ms)...` : "Run Live Inference Probe"}
                    </button>
                    {showProbeDrawer && (
                      <button
                        onClick={() => setShowProbeDrawer(false)}
                        className="p-2 rounded-xl bg-white/10 hover:bg-white/20 text-slate-400 hover:text-white transition-colors"
                        title="Collapse diagnostic panel"
                      >
                        <ChevronUp size={16} />
                      </button>
                    )}
                  </div>
                </div>

                {/* Expanded Diagnostic Result Drawer */}
                <AnimatePresence>
                  {showProbeDrawer && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="pt-3 border-t border-slate-800 space-y-3"
                    >
                      {/* In-Flight Probing Timer */}
                      {probing && (
                        <div className="py-4 text-center font-mono text-xs text-amber-300 bg-black/30 rounded-xl border border-amber-500/30 flex items-center justify-center gap-2">
                          <RefreshCw size={14} className="animate-spin" />
                          <span>Streaming prompt round-trip to {aiConfig?.active_model}... ({probeElapsedMs} ms elapsed)</span>
                        </div>
                      )}

                      {/* Error Display */}
                      {probeError && (
                        <div className="p-3 rounded-xl bg-rose-950/70 border border-rose-800 text-xs font-mono text-rose-300 flex items-center gap-2">
                          <AlertTriangle size={15} className="text-rose-400 shrink-0" />
                          <span>{probeError}</span>
                        </div>
                      )}

                      {/* Verified Telemetry Result */}
                      {probeResult && !probing && (
                        <div className="space-y-3">
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs font-mono">
                            <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700">
                              <span className="text-slate-400 text-[10px] block uppercase font-bold tracking-wider">Model Verified</span>
                              <span className="text-white font-bold truncate block mt-0.5" title={probeResult.model}>
                                {probeResult.model}
                              </span>
                            </div>
                            <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700">
                              <span className="text-slate-400 text-[10px] block uppercase font-bold tracking-wider">Round-Trip Latency</span>
                              <span className={`font-bold block mt-0.5 ${
                                probeResult.latency_ms < 300 
                                  ? "text-emerald-400" 
                                  : probeResult.latency_ms < 1000 
                                  ? "text-amber-400" 
                                  : "text-rose-400"
                              }`}>
                                {probeResult.latency_ms} ms
                              </span>
                            </div>
                            <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700">
                              <span className="text-slate-400 text-[10px] block uppercase font-bold tracking-wider">Evaluation Speed</span>
                              <span className="text-indigo-300 font-bold block mt-0.5">
                                {probeResult.eval_rate_tok_per_sec ? `${probeResult.eval_rate_tok_per_sec} tok/sec` : "Deterministic"}
                              </span>
                            </div>
                            <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700">
                              <span className="text-slate-400 text-[10px] block uppercase font-bold tracking-wider">Execution Mode</span>
                              <span className={`font-bold block mt-0.5 ${probeResult.mode === 'llm_active' ? 'text-emerald-400' : 'text-amber-400'}`}>
                                {probeResult.mode === 'llm_active' ? "LIVE LLM STREAM" : "OFFLINE FALLBACK"}
                              </span>
                            </div>
                          </div>

                          {/* Live Output Preview */}
                          <div className="p-3.5 rounded-xl bg-black/50 border border-slate-800 text-xs font-mono space-y-1">
                            <div className="flex items-center justify-between text-slate-400 text-[10px] uppercase tracking-wider pb-1 border-b border-slate-800/60">
                              <span>Verified Model Output Stream</span>
                              <span className="font-sans text-slate-500">
                                Tokens: {probeResult.tokens_generated ?? 0} gen / {probeResult.tokens_evaluated ?? 0} prompt
                              </span>
                            </div>
                            <p className="text-emerald-300/90 leading-relaxed pt-1 whitespace-pre-wrap">
                              {probeResult.response}
                            </p>
                          </div>
                        </div>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* Dynamic Model Switcher Section */}
            <div className="pt-4 border-t border-slate-200/70 space-y-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 font-heading flex items-center gap-2">
                  <Radio size={16} className="text-emerald-500 animate-pulse" />
                  System-Wide Model Switcher (Instant Hot-Swap)
                </h3>
                <p className="text-xs text-slate-500 font-medium mt-0.5">
                  Switches the primary LLM across all clinical notes, consultation triage, RAG lookups, and diagnostic summaries globally.
                </p>
              </div>

              {/* Recommended Preset Models */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
                {aiConfig?.recommended_models?.map((preset) => {
                  const isCurrent = aiConfig.active_model.toLowerCase() === preset.id.toLowerCase();
                  return (
                    <div
                      key={preset.id}
                      className={`p-3.5 rounded-2xl border transition-all flex flex-col justify-between ${
                        isCurrent 
                          ? "bg-emerald-50/90 border-emerald-400 shadow-md shadow-emerald-500/10 ring-1 ring-emerald-500/20" 
                          : "bg-white/80 border-slate-200 hover:border-slate-300 hover:bg-white"
                      }`}
                    >
                      <div>
                        <div className="flex items-center justify-between mb-1.5">
                          <span className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                            preset.type === 'medical' 
                              ? 'bg-rose-100 text-rose-800' 
                              : preset.type === 'edge' 
                              ? 'bg-amber-100 text-amber-800' 
                              : 'bg-blue-100 text-blue-800'
                          }`}>
                            {preset.type}
                          </span>
                          {isCurrent && (
                            <span className="flex items-center gap-1 text-[10px] font-extrabold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded-full">
                              <Check size={10} strokeWidth={3} /> ACTIVE
                            </span>
                          )}
                        </div>
                        <h4 className="text-xs font-bold text-slate-900 font-mono leading-tight">{preset.id}</h4>
                        <p className="text-[11px] text-slate-500 mt-1 leading-snug">{preset.label}</p>
                      </div>

                      <div className="mt-3">
                        <button
                          onClick={() => handleSwitchModel(preset.id)}
                          disabled={isCurrent || switching}
                          className={`w-full py-1.5 px-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                            isCurrent
                              ? "bg-emerald-600 text-white cursor-default shadow-sm"
                              : "bg-slate-900 hover:bg-slate-800 text-white disabled:opacity-50"
                          }`}
                        >
                          {isCurrent ? (
                            <>
                              <Check size={12} strokeWidth={2.5} /> Active System Model
                            </>
                          ) : (
                            <>
                              Switch to Model <ArrowRight size={12} />
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Detected Installed Models on Local Host */}
              {aiConfig?.installed_models && aiConfig.installed_models.length > 0 && (
                <div className="p-3 rounded-2xl bg-slate-100/70 border border-slate-200/80 flex flex-col md:flex-row md:items-center justify-between gap-2">
                  <div className="text-xs font-semibold text-slate-600 flex items-center gap-2">
                    <Cpu size={14} className="text-slate-400" />
                    <span>Locally Installed Ollama Models:</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-1.5">
                    {aiConfig.installed_models.map((tag) => {
                      const isTagActive = aiConfig.active_model.toLowerCase() === tag.toLowerCase();
                      return (
                        <button
                          key={tag}
                          onClick={() => handleSwitchModel(tag)}
                          disabled={isTagActive || switching}
                          className={`px-2.5 py-1 rounded-lg text-xs font-mono font-medium transition-all ${
                            isTagActive
                              ? "bg-emerald-600 text-white font-bold shadow-sm"
                              : "bg-white border border-slate-200 text-slate-700 hover:border-slate-400 hover:bg-slate-50"
                          }`}
                        >
                          {tag} {isTagActive && "✓"}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Custom Model Input */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 pt-2">
                <div className="relative flex-grow">
                  <input
                    type="text"
                    value={customModelInput}
                    onChange={(e) => setCustomModelInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && customModelInput.trim()) {
                        handleSwitchModel(customModelInput);
                      }
                    }}
                    placeholder="Enter custom model tag (e.g. ii-medical:8b, mistral-nemo, deepseek-r1:8b)..."
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-sm font-mono text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 shadow-inner"
                  />
                </div>
                <button
                  onClick={() => handleSwitchModel(customModelInput)}
                  disabled={!customModelInput.trim() || switching}
                  id="admin-btn-apply-custom-model"
                  className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-white font-bold text-sm transition-all shadow-md shadow-slate-900/10 flex items-center justify-center gap-2 shrink-0"
                >
                  {switching ? <RefreshCw size={15} className="animate-spin" /> : <Sparkles size={15} className="text-emerald-400" />}
                  Apply to Entire System
                </button>
              </div>

            </div>

            {/* Clinical Safety Watermark Banner */}
            <div className="pt-3 border-t border-slate-200/50 flex items-center justify-center text-center">
              <span className="text-[11px] font-bold tracking-wider text-slate-500 uppercase bg-slate-100/90 px-3 py-1 rounded-full border border-slate-200/80">
                {aiConfig?.safety_watermark || "REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED"}
              </span>
            </div>

          </div>
        </section>

        {/* ============================================================ */}
        {/* Live Security Audit Feed Widget (HIPAA Compliance Visibility) */}
        {/* ============================================================ */}
        <section className="bg-white/80 backdrop-blur-2xl border border-slate-200/90 rounded-3xl p-6 md:p-8 shadow-xl shadow-slate-200/50 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200/70">
            <div className="flex items-center gap-3.5">
              <div className="p-3 bg-indigo-50 border border-indigo-200 text-indigo-600 rounded-2xl shadow-xs">
                <ShieldCheck size={24} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-2xl font-bold text-slate-900 font-heading">
                    Live Security Audit Feed
                  </h2>
                  <span className="text-[10px] font-bold uppercase tracking-wider bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded-full border border-indigo-200">
                    HIPAA Compliance Trail
                  </span>
                </div>
                <p className="text-xs text-slate-500 font-medium mt-0.5">
                  Append-only immutable record of administrative actions, model changes, user authorization, and clinical events.
                </p>
              </div>
            </div>

            {/* Filter Tabs */}
            <div className="flex flex-wrap items-center gap-2 text-xs font-semibold">
              <button
                onClick={() => setAuditFilter("all")}
                className={`px-3 py-1.5 rounded-xl transition-all ${
                  auditFilter === "all"
                    ? "bg-slate-900 text-white shadow-xs"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                All Events ({auditLogs?.total || 0})
              </button>
              <button
                onClick={() => setAuditFilter("alerts")}
                className={`px-3 py-1.5 rounded-xl transition-all flex items-center gap-1.5 ${
                  auditFilter === "alerts"
                    ? "bg-amber-600 text-white shadow-xs font-bold"
                    : "bg-amber-50 text-amber-800 hover:bg-amber-100 border border-amber-200"
                }`}
              >
                <AlertTriangle size={13} />
                Alerts & Warnings ({((auditLogs?.critical_count || 0) + (auditLogs?.warning_count || 0))})
              </button>
              <button
                onClick={() => setAuditFilter("ai")}
                className={`px-3 py-1.5 rounded-xl transition-all ${
                  auditFilter === "ai"
                    ? "bg-emerald-600 text-white shadow-xs font-bold"
                    : "bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200"
                }`}
              >
                AI Engine
              </button>
              <button
                onClick={() => setAuditFilter("users")}
                className={`px-3 py-1.5 rounded-xl transition-all ${
                  auditFilter === "users"
                    ? "bg-purple-600 text-white shadow-xs font-bold"
                    : "bg-purple-50 text-purple-800 hover:bg-purple-100 border border-purple-200"
                }`}
              >
                RBAC & Auth
              </button>
            </div>
          </div>

          {/* Audit Log Stream */}
          <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1 divide-y divide-slate-100">
            {loading && !auditLogs ? (
              <div className="py-12 text-center text-slate-400">
                <RefreshCw size={24} className="animate-spin mx-auto mb-2 text-indigo-500" />
                Connecting to live audit feed...
              </div>
            ) : filteredLogs.length === 0 ? (
              <div className="py-8 text-center text-slate-400 text-xs">
                No audit events found matching the selected filter.
              </div>
            ) : (
              filteredLogs.map((log) => {
                const isExpanded = expandedLogId === log.id;
                const isCritical = log.severity === "critical";
                const isWarning = log.severity === "warning";
                const isNewlyArrived = newlyArrivedLogId === log.id;

                return (
                  <div key={log.id} className="pt-2.5 first:pt-0">
                    <div className={`p-3.5 rounded-2xl border transition-all flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-xs ${
                      isNewlyArrived
                        ? "bg-emerald-50/90 border-emerald-400 ring-2 ring-emerald-500/40 shadow-emerald-500/10"
                        : "bg-white/70 border-slate-200/80 hover:border-slate-300"
                    }`}>
                      <div className="flex items-start md:items-center gap-3">
                        {/* Severity Badge */}
                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-extrabold uppercase tracking-wider shrink-0 ${
                          isCritical
                            ? "bg-rose-100 text-rose-800 border border-rose-300"
                            : isWarning
                            ? "bg-amber-100 text-amber-800 border border-amber-300"
                            : "bg-slate-100 text-slate-700 border border-slate-200"
                        }`}>
                          {log.severity}
                        </span>

                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-mono text-xs font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">
                              {log.action}
                            </span>
                            <span className="text-xs text-slate-500 font-medium">
                              on <strong className="text-slate-700">{log.entity_type}</strong>
                            </span>
                            {isNewlyArrived && (
                              <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded-full animate-pulse">
                                ⚡ LIVE EVENT
                              </span>
                            )}
                            {log.actor_email && (
                              <span className="text-xs text-slate-600 font-mono flex items-center gap-1">
                                by <span className="font-semibold">{log.actor_email}</span>
                                {log.actor_role && (
                                  <span className="text-[10px] font-bold text-purple-700 bg-purple-50 px-1.5 py-0.2 rounded">
                                    {log.actor_role}
                                  </span>
                                )}
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-3 text-[11px] text-slate-400 font-mono mt-1">
                            <span className="flex items-center gap-1">
                              <Clock size={11} />
                              {new Date(log.created_at).toLocaleString([], {
                                dateStyle: "short",
                                timeStyle: "medium",
                              })}
                            </span>
                            {log.ip_address && (
                              <span className="flex items-center gap-1">
                                <Globe size={11} />
                                IP: {log.ip_address}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Diff & Expand Action */}
                      <div className="flex items-center gap-2 self-end md:self-center">
                        {log.diff && (
                          <button
                            onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                            className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors flex items-center gap-1"
                          >
                            <Eye size={12} />
                            <span>{isExpanded ? "Hide Diff" : "View Diff"}</span>
                            {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Expanded Diff Viewer */}
                    {isExpanded && log.diff && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        className="mt-2 p-3 rounded-xl bg-slate-900 text-slate-200 font-mono text-xs overflow-x-auto border border-slate-800 shadow-inner"
                      >
                        <pre className="whitespace-pre-wrap">
                          {(() => {
                            try {
                              return JSON.stringify(JSON.parse(log.diff), null, 2);
                            } catch {
                              return log.diff;
                            }
                          })()}
                        </pre>
                      </motion.div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </section>

        {/* Infrastructure Health */}
        <section className="bg-white/60 backdrop-blur-xl border border-white rounded-3xl p-6 shadow-xl shadow-slate-200/50">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-slate-800 font-heading flex items-center gap-2">
              <Cpu className="text-slate-400" />
              Infrastructure Health
            </h2>
            <div className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 ${health?.status === 'healthy' ? 'bg-emerald-100 text-emerald-700 border border-emerald-200' : 'bg-amber-100 text-amber-700 border border-amber-200'}`}>
              <span className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`}></span>
              {health?.status || 'CHECKING...'}
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <HealthWidget name="Main Database" icon={<Database size={18}/>} status={health?.dependencies?.database?.status} loading={loading} />
            <HealthWidget name="Redis Cache" icon={<Server size={18}/>} status={health?.dependencies?.redis?.status} loading={loading} />
            <HealthWidget name="Object Storage" icon={<HardDrive size={18}/>} status={health?.dependencies?.storage?.status} loading={loading} />
            <HealthWidget 
              name="AI Diagnostic Engine" 
              icon={<Zap size={18}/>} 
              status={aiConfig?.is_connected ? 'healthy' : isCircuitOpen ? 'offline' : 'degraded'} 
              loading={loading} 
              detail={aiConfig?.latency_ms ? `${aiConfig.latency_ms}ms` : undefined}
            />
          </div>
        </section>

        {/* Admin Operations Grid */}
        <section>
          <h2 className="text-2xl font-bold text-slate-800 mb-6 font-heading flex items-center gap-2">
            <Layers className="text-slate-400" />
            Control Modules
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {ADMIN_CARDS.map((card, idx) => (
              <motion.div
                key={card.href}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.04 * idx }}
                whileHover={{ y: -4, scale: 1.02 }}
                className="group h-full"
              >
                <Link
                  href={card.href}
                  id={card.id}
                  className="flex flex-col h-full bg-white/70 backdrop-blur-xl border border-white hover:border-emerald-200 rounded-3xl p-6 shadow-lg shadow-slate-200/40 hover:shadow-2xl hover:shadow-emerald-900/10 transition-all duration-300 relative overflow-hidden"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-transparent to-slate-50/50 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  <div className="h-14 w-14 rounded-2xl bg-white border border-slate-100 flex items-center justify-center mb-5 group-hover:scale-110 group-hover:bg-emerald-50 group-hover:border-emerald-100 transition-all duration-300 shadow-sm relative z-10">
                    {card.icon}
                  </div>
                  <h3 className="text-lg font-bold text-slate-800 mb-2 group-hover:text-emerald-700 transition-colors relative z-10 font-heading">
                    {card.title}
                  </h3>
                  <p className="text-sm text-slate-500 leading-relaxed group-hover:text-slate-600 transition-colors flex-grow relative z-10 font-medium">
                    {card.description}
                  </p>
                </Link>
              </motion.div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

function HealthWidget({ 
  name, 
  icon, 
  status, 
  loading,
  detail 
}: { 
  name: string; 
  icon: React.ReactNode; 
  status?: string; 
  loading: boolean;
  detail?: string;
}) {
  const isHealthy = status === 'healthy';
  return (
    <div className="flex items-center justify-between p-4 rounded-2xl bg-slate-50/50 border border-slate-100">
      <div className="flex items-center gap-3">
        <div className="text-slate-400">
          {icon}
        </div>
        <div>
          <span className="font-semibold text-slate-700 text-sm block">{name}</span>
          {detail && <span className="text-[11px] font-mono text-slate-400">{detail}</span>}
        </div>
      </div>
      <div>
        {loading ? (
          <span className="inline-block w-16 h-5 bg-slate-200 rounded animate-pulse"></span>
        ) : (
          <div className="flex items-center gap-1.5">
            {isHealthy ? (
              <>
                <CheckCircle2 size={16} className="text-emerald-500" />
                <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider">Online</span>
              </>
            ) : (
              <>
                <AlertCircle size={16} className="text-amber-500" />
                <span className="text-xs font-bold text-amber-600 uppercase tracking-wider">{status || 'Offline'}</span>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({ 
  title, 
  value, 
  loading, 
  delay, 
  icon, 
  gradient, 
  alert = false,
  subtitle
}: { 
  title: string; 
  value?: number; 
  loading: boolean; 
  delay: number; 
  icon: React.ReactNode; 
  gradient: string; 
  alert?: boolean; 
  subtitle?: string;
}) {
  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay, ease: "easeOut" }}
      className={`group relative overflow-hidden bg-white/80 backdrop-blur-xl border ${alert ? 'border-amber-300 shadow-amber-900/5' : 'border-white'} rounded-3xl p-5 shadow-xl shadow-slate-200/50 transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:shadow-slate-300/50 flex flex-col justify-between`}
    >
      <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${gradient} rounded-bl-full -mr-16 -mt-16 opacity-70 transition-transform duration-500 group-hover:scale-125 group-hover:opacity-100`}></div>
      <div className="relative z-10">
        <div className="flex justify-between items-start mb-3">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider leading-tight">{title}</span>
          <div className="p-2 bg-white rounded-xl shadow-xs border border-slate-100 text-slate-600 transition-transform duration-300 group-hover:scale-110">
            {icon}
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className={`text-3xl lg:text-4xl font-extrabold tracking-tight font-heading ${alert ? 'text-amber-600' : 'text-slate-800'}`}>
            {loading ? (
              <span className="inline-block w-16 h-9 bg-slate-200 rounded animate-pulse mt-1"></span>
            ) : (
              <motion.span
                key={value}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="inline-block"
              >
                {value?.toLocaleString() || "0"}
              </motion.span>
            )}
          </span>
        </div>
        {subtitle && (
          <div className="mt-1 text-[11px] font-semibold text-slate-400">
            {subtitle}
          </div>
        )}
        <div className="mt-3 opacity-30 transition-opacity duration-300 group-hover:opacity-60">
          <svg viewBox="0 0 100 20" className="w-full h-5" preserveAspectRatio="none">
            <path d="M0,20 C20,20 20,5 40,10 C60,15 80,0 100,5" fill="none" stroke={alert ? '#f59e0b' : '#94a3b8'} strokeWidth="2" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
          </svg>
        </div>
      </div>
    </motion.div>
  );
}
