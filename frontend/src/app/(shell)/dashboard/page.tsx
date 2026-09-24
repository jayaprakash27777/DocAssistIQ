/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable react/no-unescaped-entities */
"use client";

import { useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { type ConsultationSummary } from "@/lib/api";
import { useConsultations } from "@/hooks/useConsultations";
import { motion, Variants } from "framer-motion";
import CountUp from "react-countup";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Activity, Clock, ShieldCheck, ChevronRight, PlayCircle, FileEdit, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DashboardStats {
  totalConsultations: number;
  recentConsultations: ConsultationSummary[];
  loading: boolean;
}

const STATUS_LABELS: Record<string, { label: string; color: string; bg: string }> = {
  created: { label: "New", color: "var(--color-primary-600)", bg: "var(--color-primary-50)" },
  recording: { label: "Recording", color: "var(--color-danger-600)", bg: "var(--color-danger-50)" },
  processing: { label: "Processing", color: "var(--color-warning-600)", bg: "var(--color-warning-50)" },
  draft: { label: "Draft Note", color: "var(--color-primary-600)", bg: "var(--color-primary-50)" },
  under_review: { label: "In Review", color: "var(--color-warning-600)", bg: "var(--color-warning-50)" },
  analysis_ready: { label: "Ready", color: "var(--color-success-600)", bg: "var(--color-success-50)" },
  finalized: { label: "Finalized", color: "var(--color-success-700)", bg: "var(--color-success-100)" },
  amended: { label: "Amended", color: "var(--text-secondary)", bg: "rgba(0,0,0,0.05)" },
};

export default function DashboardPage() {
  const { user } = useAuth();
  
  // Use the React Query hook from Phase 1
  const { data: listData, isLoading: loading } = useConsultations();

  const totalConsultations = listData?.length || 0;
  const recentConsultations = listData?.slice(0, 5) || [];

  // Compute real chart data over the last 7 days (No mock data!)
  const chartData = useMemo(() => {
    if (!listData) return [];
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const now = new Date();
    const result: { name: string; dateStr: string; consultations: number }[] = [];
    
    // Initialize the last 7 days with 0 consultations
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(now.getDate() - i);
      result.push({
        name: days[d.getDay()],
        dateStr: d.toISOString().split('T')[0],
        consultations: 0
      });
    }

    // Populate actual data
    listData.forEach(c => {
      const cDate = new Date(c.created_at).toISOString().split('T')[0];
      const match = result.find(r => r.dateStr === cDate);
      if (match) {
        match.consultations += 1;
      }
    });

    return result;
  }, [listData]);

  if (!user) return null;

  const isAdmin = user.role === "admin";
  const memberSince = new Date(user.created_at).toLocaleDateString("en-GB", {
    year: "numeric",
    month: "long",
  });

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <motion.div 
      className="dashboard-shell space-y-8"
      variants={containerVariants}
      initial="hidden"
      animate="show"
    >
      {/* Welcome Header */}
      <motion.section variants={itemVariants} className="dashboard-welcome">
        <div className="relative overflow-hidden rounded-3xl glass-panel-dark-4k gpu-accelerated text-white">
          <div className="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 rounded-full bg-teal-500/20 blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-96 h-96 rounded-full bg-indigo-500/20 blur-3xl pointer-events-none" />
          
          <div className="relative z-10 px-8 py-10 sm:px-12 sm:py-12 flex flex-col sm:flex-row items-center gap-8">
            <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-3xl bg-gradient-to-br from-teal-400 to-indigo-500 text-white flex items-center justify-center text-4xl sm:text-5xl font-black shadow-2xl ring-4 ring-white/20 shrink-0">
              {user.full_name.replace(/^dr\.?\s*/i, '').charAt(0).toUpperCase() || 'D'}
            </div>
            <div className="text-center sm:text-left flex-1">
              <div className="flex items-center justify-center sm:justify-start gap-3 mb-2">
                <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white m-0">
                  Welcome back, Dr. {user.full_name.replace(/^dr\.?\s*/i, '').split(' ')[0] || user.full_name.split('@')[0]}
                </h1>
                {isAdmin && (
                  <span className="bg-gradient-to-r from-teal-400 to-emerald-400 text-slate-950 text-[10px] uppercase tracking-widest px-2.5 py-1 rounded-full font-black shadow-sm">
                    Administrator
                  </span>
                )}
              </div>
              <p className="text-sm sm:text-base text-slate-300 max-w-2xl leading-relaxed m-0">
                {isAdmin ? "Overview of clinical operations, audit trails, and system health." : "Your clinical workspace is active. Review longitudinal patient charts and formulary insights."}
              </p>
              <div className="mt-6 flex flex-wrap justify-center sm:justify-start gap-3">
                <Button 
                  onClick={() => window.location.href = '/consultations'} 
                  variant="primary" 
                  className="rounded-2xl h-11 px-6 shadow-lg transition-all gap-2 text-sm font-bold bg-gradient-to-r from-teal-500 to-indigo-600 text-white hover:brightness-110 active:scale-95"
                  style={{ boxShadow: "0 6px 20px rgba(13,148,136,0.35), inset 0 1px 0 rgba(255,255,255,0.3)" }}
                >
                  <PlayCircle className="w-4 h-4" /> Start Consultation
                </Button>
                <Button 
                  onClick={() => window.location.href = '/consultations'} 
                  variant="outline" 
                  className="rounded-2xl h-11 px-6 border-white/20 bg-white/10 hover:bg-white/20 text-white backdrop-blur-md transition-all gap-2 text-sm font-semibold active:scale-95"
                >
                  <FileEdit className="w-4 h-4" /> View Records
                </Button>
              </div>
            </div>
          </div>
        </div>
      </motion.section>

      {/* Stats Grid */}
      <motion.section variants={containerVariants} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {[
          { 
            label: "Total Consultations", 
            value: loading ? 0 : totalConsultations, 
            icon: Activity,
            color: "text-teal-600",
            bg: "bg-teal-50 border-teal-200/60",
          },
          { 
            label: "Account Status", 
            value: user.is_verified ? "Verified" : "Pending", 
            icon: user.is_verified ? ShieldCheck : Clock,
            color: user.is_verified ? "text-emerald-600" : "text-amber-600",
            bg: user.is_verified ? "bg-emerald-50 border-emerald-200/60" : "bg-amber-50 border-amber-200/60",
            isString: true
          },
          { 
            label: "Member Since", 
            value: memberSince, 
            icon: Clock,
            color: "text-indigo-600",
            bg: "bg-indigo-50 border-indigo-200/60",
            isString: true
          },
          { 
            label: "System Health", 
            value: "Operational", 
            icon: Zap,
            color: "text-teal-600",
            bg: "bg-teal-50 border-teal-200/60",
            isString: true
          },
        ].map((stat, i) => (
          <motion.div 
            key={i} 
            variants={itemVariants} 
            whileHover={{ y: -2 }}
            className="glass-panel-4k gpu-accelerated p-6 rounded-3xl border border-slate-200/90 bg-white/85 backdrop-blur-xl shadow-[0_12px_36px_rgba(0,0,0,0.05),inset_0_1px_0_rgba(255,255,255,0.9)] flex items-center gap-4 ring-1 ring-black/5"
          >
            <div className={`w-14 h-14 rounded-2xl border flex items-center justify-center ${stat.bg} ${stat.color} shadow-sm shrink-0`}>
              <stat.icon className="w-7 h-7" />
            </div>
            <div className="dashboard-card-body">
              <div className="text-2xl sm:text-3xl font-black text-slate-900 mb-0.5 font-heading tracking-tight">
                {stat.isString ? stat.value : <CountUp end={stat.value as number} duration={2} />}
              </div>
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">{stat.label}</div>
            </div>
          </motion.div>
        ))}
      </motion.section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Activity Chart */}
        <motion.section variants={itemVariants} className="lg:col-span-2 glass-panel-4k gpu-accelerated p-6 sm:p-8 rounded-3xl border border-slate-200/90 bg-white/85 backdrop-blur-2xl shadow-[0_12px_36px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.9)] ring-1 ring-black/5">
          <div className="flex justify-between items-end mb-6 relative z-10">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
                <span className="text-xs font-bold uppercase tracking-wider text-teal-700">Analytics</span>
              </div>
              <h2 className="text-xl font-black text-slate-900 tracking-tight m-0">Activity Overview</h2>
              <p className="text-xs text-slate-400 m-0">Consultation volume recorded over the last 7 days</p>
            </div>
          </div>
          
          <div className="h-[300px] w-full relative z-10">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorConsults" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0d9488" stopOpacity={0.45}/>
                    <stop offset="95%" stopColor="#0d9488" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#94a3b8' }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#94a3b8' }} />
                <Tooltip 
                  contentStyle={{ borderRadius: '16px', border: '1px solid #e2e8f0', boxShadow: '0 10px 30px -5px rgba(0, 0, 0, 0.1)', fontWeight: 600, background: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(10px)' }}
                  itemStyle={{ color: '#0d9488' }}
                />
                <Area type="monotone" dataKey="consultations" stroke="#0d9488" strokeWidth={3.5} fillOpacity={1} fill="url(#colorConsults)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.section>

        {/* Recent Consultations */}
        <motion.section variants={itemVariants} className="glass-panel-4k gpu-accelerated p-6 sm:p-8 rounded-3xl border border-slate-200/90 bg-white/85 backdrop-blur-2xl shadow-[0_12px_36px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.9)] flex flex-col ring-1 ring-black/5">
          <div className="flex justify-between items-center mb-6 relative z-10">
            <div>
              <h2 className="text-xl font-black text-slate-900 tracking-tight m-0">Recent History</h2>
              <p className="text-xs text-slate-400 m-0">Latest clinical sessions</p>
            </div>
            <Link href="/consultations" className="text-xs font-bold text-teal-700 hover:text-indigo-600 flex items-center gap-1 transition-colors px-2.5 py-1 rounded-lg bg-teal-50 border border-teal-200/60">
              View all <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="flex-1 overflow-hidden relative z-10">
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="flex gap-4 items-center">
                    <div className="w-10 h-10 rounded-2xl bg-slate-100 animate-pulse shrink-0" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-slate-100 rounded w-3/4 animate-pulse" />
                      <div className="h-3 bg-slate-100 rounded w-1/2 animate-pulse" />
                    </div>
                  </div>
                ))}
              </div>
            ) : recentConsultations.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 bg-slate-50/70 rounded-2xl border border-dashed border-slate-200">
                <FileEdit className="w-10 h-10 text-slate-300 mb-3" />
                <p className="text-slate-500 font-medium text-xs m-0">No recent consultations found.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentConsultations.map((c, i) => {
                  const status = STATUS_LABELS[c.status] || { label: c.status, color: "var(--text-secondary)", bg: "var(--color-neutral-100)" };
                  return (
                    <motion.div 
                      key={c.id}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.08 }}
                    >
                      <Link 
                        href={`/consultations/${c.id}`}
                        className="group flex items-center justify-between p-3.5 rounded-2xl bg-white/60 hover:bg-white border border-slate-200/80 hover:border-indigo-300 transition-all shadow-sm hover:shadow-md"
                      >
                        <div>
                          <div className="font-mono text-xs font-bold text-slate-900 mb-1 group-hover:text-teal-700 transition-colors">
                            SESSION {c.id.slice(0, 8).toUpperCase()}
                          </div>
                          <div className="text-[11px] text-slate-400 flex items-center gap-1.5 font-medium">
                            <Clock className="w-3 h-3 text-slate-400" />
                            {new Date(c.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                          </div>
                        </div>
                        <div className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider border shadow-sm" style={{ color: status.color, backgroundColor: status.bg, borderColor: `${status.color}30` }}>
                          {status.label}
                        </div>
                      </Link>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </div>
        </motion.section>
      </div>
    </motion.div>
  );
}
