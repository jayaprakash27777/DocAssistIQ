"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { getAdminStats, getReady, type AdminStatsResponse, type ReadinessResponse } from "@/lib/api";
import { Activity, Users, ShieldAlert, Database, Server, ClipboardList, BookOpen, Layers, TestTube2, FlaskConical, HardDrive, CheckCircle2, AlertCircle, Cpu } from "lucide-react";
import { motion } from "framer-motion";

interface AdminCard {
  href: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  id: string;
}

const ADMIN_CARDS: AdminCard[] = [
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
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const isAdmin = user?.role === "admin" || user?.role === "super_admin";

  useEffect(() => {
    if (!isAdmin) {
      setLoading(false);
      return;
    }
    let mounted = true;
    
    async function fetchData() {
      const [statsRes, healthRes] = await Promise.all([
        getAdminStats(),
        getReady()
      ]);
      if (mounted) {
        if (statsRes.ok) setStats(statsRes.data);
        if (healthRes.ok) setHealth(healthRes.data);
        setLastUpdated(new Date());
        setLoading(false);
      }
    }
    
    fetchData();
    
    // Poll every 3 seconds for real-time updates
    const intervalId = setInterval(fetchData, 3000);
    
    return () => {
      mounted = false;
      clearInterval(intervalId);
    };
  }, [isAdmin]);

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

  return (
    <div className="min-h-screen bg-slate-50 relative overflow-hidden p-8 pt-10">
      {/* Animated background shapes */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-300/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '8s' }}></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-300/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '12s' }}></div>
      
      {/* Dot Grid Overlay */}
      <div className="absolute inset-0 z-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>

      <div className="max-w-7xl mx-auto space-y-12 relative z-10">
        
        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <div className="relative p-2.5 bg-emerald-500/10 rounded-xl border border-emerald-500/20 shadow-sm overflow-hidden">
                <div className="absolute inset-0 bg-emerald-400/20 animate-pulse"></div>
                <Activity size={28} className="text-emerald-600 relative z-10" />
              </div>
              <h1 className="text-4xl font-bold text-slate-900 tracking-tight font-heading">
                System Command Center
              </h1>
            </div>
            <p className="text-slate-500 text-lg max-w-2xl font-medium">
              Global platform management, live monitoring, and real-time verification controls.
            </p>
          </div>
          
          <div className="flex items-center gap-2 text-sm font-medium text-emerald-700 bg-emerald-50 px-4 py-2 rounded-full border border-emerald-200 shadow-sm backdrop-blur-md">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
            Live Data Feed
            <span className="text-emerald-600/60 ml-2 text-xs font-mono">
              Updated: {lastUpdated.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' })}
            </span>
          </div>
        </header>

        {/* System Health */}
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
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <HealthWidget name="Main Database" icon={<Database size={18}/>} status={health?.dependencies?.database?.status} loading={loading} />
            <HealthWidget name="Redis Cache" icon={<Server size={18}/>} status={health?.dependencies?.redis?.status} loading={loading} />
            <HealthWidget name="Object Storage" icon={<HardDrive size={18}/>} status={health?.dependencies?.storage?.status} loading={loading} />
          </div>
        </section>

        {/* Real-time Metrics Overview */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard 
            title="Total Users" 
            value={stats?.total_users} 
            loading={loading}
            delay={0}
            icon={<Users className="text-blue-500" size={24} />}
            gradient="from-blue-500/10 to-transparent"
          />
          <MetricCard 
            title="Registered Doctors" 
            value={stats?.total_doctors} 
            loading={loading}
            delay={0.1}
            icon={<Activity className="text-emerald-500" size={24} />}
            gradient="from-emerald-500/10 to-transparent"
          />
          <MetricCard 
            title="Platform Admins" 
            value={stats?.total_admins} 
            loading={loading}
            delay={0.2}
            icon={<Server className="text-purple-500" size={24} />}
            gradient="from-purple-500/10 to-transparent"
          />
          <MetricCard 
            title="Pending Verifications" 
            value={stats?.pending_verifications} 
            loading={loading}
            delay={0.3}
            icon={<ShieldAlert className={stats?.pending_verifications ? "text-amber-500 animate-pulse" : "text-slate-400"} size={24} />}
            gradient={stats?.pending_verifications ? "from-amber-500/20 to-transparent" : "from-slate-500/5 to-transparent"}
            alert={!!stats?.pending_verifications}
          />
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
                transition={{ duration: 0.4, delay: 0.1 * idx }}
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
                  <h3 className="text-lg font-bold text-slate-800 mb-2 group-hover:text-emerald-700 transition-colors relative z-10">
                    {card.title}
                  </h3>
                  <p className="text-sm text-slate-500 leading-relaxed group-hover:text-slate-600 transition-colors flex-grow relative z-10">
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

function HealthWidget({ name, icon, status, loading }: { name: string, icon: React.ReactNode, status?: string, loading: boolean }) {
  const isHealthy = status === 'healthy';
  return (
    <div className="flex items-center justify-between p-4 rounded-2xl bg-slate-50/50 border border-slate-100">
      <div className="flex items-center gap-3">
        <div className="text-slate-400">
          {icon}
        </div>
        <span className="font-semibold text-slate-700">{name}</span>
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

function MetricCard({ title, value, loading, delay, icon, gradient, alert = false }: { title: string, value?: number, loading: boolean, delay: number, icon: React.ReactNode, gradient: string, alert?: boolean }) {
  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay, ease: "easeOut" }}
      className={`group relative overflow-hidden bg-white/80 backdrop-blur-xl border ${alert ? 'border-amber-300 shadow-amber-900/5' : 'border-white'} rounded-3xl p-6 shadow-xl shadow-slate-200/50 transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:shadow-slate-300/50`}
    >
      <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${gradient} rounded-bl-full -mr-16 -mt-16 opacity-70 transition-transform duration-500 group-hover:scale-125 group-hover:opacity-100`}></div>
      <div className="relative z-10">
        <div className="flex justify-between items-start mb-4">
          <span className="text-sm font-bold text-slate-500 uppercase tracking-wider">{title}</span>
          <div className="p-2.5 bg-white rounded-xl shadow-sm border border-slate-100 text-slate-600 transition-transform duration-300 group-hover:scale-110">
            {icon}
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className={`text-5xl font-extrabold tracking-tight font-heading ${alert ? 'text-amber-600' : 'text-slate-800'}`}>
            {loading ? (
              <span className="inline-block w-20 h-12 bg-slate-200 rounded animate-pulse mt-1"></span>
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
        {/* Subtle decorative chart line (placeholder visual) */}
        <div className="mt-4 opacity-30 transition-opacity duration-300 group-hover:opacity-60">
          <svg viewBox="0 0 100 20" className="w-full h-8" preserveAspectRatio="none">
            <path d="M0,20 C20,20 20,5 40,10 C60,15 80,0 100,5" fill="none" stroke={alert ? '#f59e0b' : '#94a3b8'} strokeWidth="2" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
          </svg>
        </div>
      </div>
    </motion.div>
  );
}
