/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable react/no-unescaped-entities */
/**
 * DocAssistIQ — Administration Hub Page (/admin).
 *
 * Top-level admin dashboard. Links to admin sub-sections.
 * Accessible only to users with role='admin'.
 */

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { getAdminStats, type AdminStatsResponse } from "@/lib/api";
import { Activity, Users, ShieldAlert, Database, Server, ClipboardList, BookOpen, Layers, TestTube2, FlaskConical } from "lucide-react";
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
    icon: <ShieldAlert size={28} className="text-sky-400" />,
    id: "admin-card-doctors",
  },
  {
    href: "/admin/sources",
    title: "Medical Sources",
    description: "Manage and verify clinical knowledge sources for the registry.",
    icon: <BookOpen size={28} className="text-sky-400" />,
    id: "admin-card-sources",
  },
  {
    href: "/admin/ingestion",
    title: "Knowledge Ingestion",
    description: "Monitor background ingestion queues and review parsed knowledge.",
    icon: <Server size={28} className="text-sky-400" />,
    id: "admin-card-ingestion",
  },
  {
    href: "/admin/knowledge",
    title: "Knowledge Publication",
    description: "Safely review and publish clinical knowledge to production.",
    icon: <ClipboardList size={28} className="text-sky-400" />,
    id: "admin-card-knowledge",
  },
  {
    href: "/admin/datasets",
    title: "Dataset Registry & Governance",
    description: "Manage ML datasets and enforce PII validation rules.",
    icon: <Database size={28} className="text-sky-400" />,
    id: "admin-card-datasets",
  },
  {
    href: "/admin/evaluations",
    title: "Baseline Evaluation Harness",
    description: "Run repeatable metrics against fixed hold-out datasets.",
    icon: <TestTube2 size={28} className="text-sky-400" />,
    id: "admin-card-evaluations",
  },
  {
    href: "/admin/experiments",
    title: "ML Experiment Tracking",
    description: "Track model training runs, hyperparameters, and artifacts.",
    icon: <FlaskConical size={28} className="text-sky-400" />,
    id: "admin-card-experiments",
  },
];

export default function AdminPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<AdminStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      const res = await getAdminStats();
      if (res.ok) {
        setStats(res.data);
      }
      setLoading(false);
    }
    fetchStats();
  }, []);

  if (!user) return null;

  return (
    <div className="admin-dashboard-container">
      <header className="admin-header">
        <h1>
          <Activity size={32} className="text-sky-400" /> System Command Center
        </h1>
        <p>Global platform management, monitoring, and verification controls.</p>
      </header>

      {/* Real-time Metrics Overview */}
      <section className="admin-metrics-grid">
        <motion.div 
          className="admin-metric-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <span className="admin-metric-title">Total Users</span>
          <span className="admin-metric-value">
            {loading ? "..." : stats?.total_users?.toLocaleString() || "0"}
          </span>
        </motion.div>

        <motion.div 
          className="admin-metric-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
        >
          <span className="admin-metric-title">Registered Doctors</span>
          <span className="admin-metric-value">
            {loading ? "..." : stats?.total_doctors?.toLocaleString() || "0"}
          </span>
        </motion.div>

        <motion.div 
          className="admin-metric-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
        >
          <span className="admin-metric-title">Platform Admins</span>
          <span className="admin-metric-value">
            {loading ? "..." : stats?.total_admins?.toLocaleString() || "0"}
          </span>
        </motion.div>

        <motion.div 
          className="admin-metric-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
        >
          <span className="admin-metric-title">Pending Verifications</span>
          <span className={`admin-metric-value ${stats?.pending_verifications ? 'text-amber-400' : ''}`}>
            {loading ? "..." : stats?.pending_verifications?.toLocaleString() || "0"}
          </span>
        </motion.div>
      </section>

      {/* Admin Operations Grid */}
      <section className="admin-hub-grid">
        {ADMIN_CARDS.map((card, idx) => (
          <motion.div
            key={card.href}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.1 * idx }}
          >
            <Link
              href={card.href}
              id={card.id}
              className="admin-hub-tile"
            >
              <div className="admin-tile-icon">
                {card.icon}
              </div>
              <div className="admin-tile-content">
                <h3>{card.title}</h3>
                <p>{card.description}</p>
              </div>
            </Link>
          </motion.div>
        ))}
      </section>
    </div>
  );
}
