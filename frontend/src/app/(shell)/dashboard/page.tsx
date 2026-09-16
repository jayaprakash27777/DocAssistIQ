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
      className="dashboard-shell"
      variants={containerVariants}
      initial="hidden"
      animate="show"
    >
      {/* Welcome Header */}
      <motion.section variants={itemVariants} className="dashboard-welcome">
        <div className="relative overflow-hidden rounded-3xl bg-[var(--glass-bg)] backdrop-blur-xl border border-[var(--border-default)] shadow-sm">
          <div className="absolute top-0 right-0 -mr-20 -mt-20 w-64 h-64 rounded-full bg-[var(--color-primary-200)] opacity-30 blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-80 h-80 rounded-full bg-[var(--color-primary-100)] opacity-20 blur-3xl pointer-events-none" />
          
          <div className="relative z-10 px-8 py-10 sm:px-12 sm:py-12 flex flex-col sm:flex-row items-center gap-8">
            <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-full bg-gradient-to-tr from-[var(--color-primary-600)] to-[var(--color-primary-400)] text-white flex items-center justify-center text-4xl sm:text-5xl font-bold shadow-xl border-4 border-white/50 shrink-0">
              {user.full_name.charAt(0).toUpperCase()}
            </div>
            <div className="text-center sm:text-left flex-1">
              <div className="flex items-center justify-center sm:justify-start gap-3 mb-2">
                <h1 className="dashboard-welcome-title">
                  Welcome back, {user.full_name.split(' ')[0]}
                </h1>
                {isAdmin && (
                  <span className="bg-[var(--color-primary-600)] text-white text-[0.65rem] uppercase tracking-widest px-2.5 py-1 rounded-full font-bold shadow-sm">
                    Admin
                  </span>
                )}
              </div>
              <p className="dashboard-welcome-sub">
                {isAdmin ? "Overview of clinical operations and system health." : "Your clinical workspace is ready. Here's a summary of your recent activity."}
              </p>
              <div className="mt-6 flex flex-wrap justify-center sm:justify-start gap-3">
                <Button onClick={() => window.location.href = '/consultations/new'} variant="primary" className="bg-[var(--color-primary-600)] text-white hover:bg-[var(--color-primary-700)] rounded-xl h-11 px-6 shadow-md transition-all gap-2">
                  <PlayCircle className="w-5 h-5" /> Start Consultation
                </Button>
                <Button onClick={() => window.location.href = '/consultations'} variant="outline" className="bg-white/50 hover:bg-white/80 rounded-xl h-11 px-6 border-[var(--border-strong)] transition-all gap-2 text-[var(--text-primary)]">
                  <FileEdit className="w-5 h-5" /> View Records
                </Button>
              </div>
            </div>
          </div>
        </div>
      </motion.section>

      {/* Stats Grid */}
      <motion.section variants={containerVariants} className="dashboard-cards mb-8">
        {[
          { 
            label: "Total Consultations", 
            value: loading ? 0 : totalConsultations, 
            icon: Activity,
            color: "text-[var(--color-primary-600)]",
            bg: "bg-[var(--color-primary-50)]",
          },
          { 
            label: "Account Status", 
            value: user.is_verified ? "Verified" : "Pending", 
            icon: user.is_verified ? ShieldCheck : Clock,
            color: user.is_verified ? "text-emerald-600" : "text-amber-600",
            bg: user.is_verified ? "bg-emerald-50" : "bg-amber-50",
            isString: true
          },
          { 
            label: "Member Since", 
            value: memberSince, 
            icon: Clock,
            color: "text-[var(--text-secondary)]",
            bg: "bg-slate-50",
            isString: true
          },
          { 
            label: "System Health", 
            value: "Optimal", 
            icon: Zap,
            color: "text-emerald-600",
            bg: "bg-emerald-50",
            isString: true
          },
        ].map((stat, i) => (
          <motion.div key={i} variants={itemVariants} className="dashboard-card">
            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${stat.bg} ${stat.color} shrink-0`}>
              <stat.icon className="w-7 h-7" />
            </div>
            <div className="dashboard-card-body">
              <div className="text-3xl font-bold text-[var(--text-primary)] mb-1 font-heading tracking-tight">
                {stat.isString ? stat.value : <CountUp end={stat.value as number} duration={2} />}
              </div>
              <div className="text-[0.75rem] font-bold text-[var(--text-secondary)] uppercase tracking-widest">{stat.label}</div>
            </div>
          </motion.div>
        ))}
      </motion.section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Activity Chart */}
        <motion.section variants={itemVariants} className="lg:col-span-2 dashboard-card !block">
          <div className="flex justify-between items-end mb-8 relative z-10">
            <div>
              <h2 className="dashboard-card-title text-xl">Activity Overview</h2>
              <p className="dashboard-card-hint">Consultation volume over the last 7 days</p>
            </div>
          </div>
          
          <div className="h-[300px] w-full relative z-10">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorConsults" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-primary-500)" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="var(--color-primary-500)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-default)" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: 'var(--text-tertiary)' }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: 'var(--text-tertiary)' }} />
                <Tooltip 
                  contentStyle={{ borderRadius: '16px', border: '1px solid var(--border-default)', boxShadow: '0 10px 30px -5px rgba(0, 0, 0, 0.1)', fontWeight: 600, background: 'rgba(255,255,255,0.9)', backdropFilter: 'blur(10px)' }}
                  itemStyle={{ color: 'var(--color-primary-600)' }}
                />
                <Area type="monotone" dataKey="consultations" stroke="var(--color-primary-500)" strokeWidth={4} fillOpacity={1} fill="url(#colorConsults)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.section>

        {/* Recent Consultations */}
        <motion.section variants={itemVariants} className="dashboard-card !flex flex-col">
          <div className="flex justify-between items-center mb-6 relative z-10">
            <h2 className="dashboard-card-title text-xl !mb-0">Recent History</h2>
            <Link href="/consultations" className="text-sm font-bold text-[var(--color-primary-600)] hover:text-[var(--color-primary-800)] flex items-center gap-1 transition-colors">
              View all <ChevronRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="flex-1 overflow-hidden relative z-10">
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="flex gap-4 items-center">
                    <div className="w-10 h-10 rounded-full bg-[var(--color-neutral-100)] animate-pulse shrink-0" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-[var(--color-neutral-100)] rounded w-3/4 animate-pulse" />
                      <div className="h-3 bg-[var(--color-neutral-100)] rounded w-1/2 animate-pulse" />
                    </div>
                  </div>
                ))}
              </div>
            ) : recentConsultations.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 bg-[var(--color-neutral-50)] rounded-2xl border border-dashed border-[var(--border-default)]">
                <FileEdit className="w-12 h-12 text-[var(--text-tertiary)] mb-4 opacity-50" />
                <p className="text-[var(--text-secondary)] font-medium">No recent consultations found.</p>
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
                      transition={{ delay: i * 0.1 }}
                    >
                      <Link 
                        href={`/consultations/${c.id}`}
                        className="group flex items-center justify-between p-3 rounded-xl hover:bg-[var(--color-neutral-100)] transition-colors border border-transparent hover:border-[var(--border-default)]"
                      >
                        <div>
                          <div className="font-mono text-sm font-bold text-[var(--text-primary)] mb-1 group-hover:text-[var(--color-primary-600)] transition-colors">
                            {c.id.slice(0, 8)}...
                          </div>
                          <div className="text-xs text-[var(--text-tertiary)] flex items-center gap-2">
                            <Clock className="w-3 h-3" />
                            {new Date(c.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                          </div>
                        </div>
                        <div className="px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider border shadow-sm" style={{ color: status.color, backgroundColor: status.bg, borderColor: `${status.color}30` }}>
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
