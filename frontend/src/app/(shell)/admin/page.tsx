/**
 * DocAssistIQ — Administration Hub Page (/admin).
 *
 * Top-level admin dashboard. Links to admin sub-sections.
 * Accessible only to users with role='admin'.
 */

"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

interface AdminCard {
  href: string;
  title: string;
  description: string;
  icon: string;
  id: string;
}

const ADMIN_CARDS: AdminCard[] = [
  {
    href: "/admin/doctors",
    title: "Doctor Verifications",
    description: "Review and approve or reject pending doctor credential submissions.",
    icon: "👨‍⚕️",
    id: "admin-card-doctors",
  },
  {
    href: "/admin/sources",
    title: "Medical Sources",
    description: "Manage and verify clinical knowledge sources for the registry.",
    icon: "📚",
    id: "admin-card-sources",
  },
  {
    href: "/admin/ingestion",
    title: "Knowledge Ingestion",
    description: "Monitor background ingestion queues and review parsed knowledge.",
    icon: "⚙️",
    id: "admin-card-ingestion",
  },
  {
    href: "/admin/knowledge",
    title: "Knowledge Publication",
    description: "Safely review and publish clinical knowledge to production.",
    icon: "🩺",
    id: "admin-card-knowledge",
  },
  {
    href: "/admin/datasets",
    title: "Dataset Registry & Governance",
    description: "Manage ML datasets and enforce PII validation rules.",
    icon: "📊",
    id: "admin-card-datasets",
  },
  {
    href: "/admin/evaluations",
    title: "Baseline Evaluation Harness",
    description: "Run repeatable metrics against fixed hold-out datasets.",
    icon: "📈",
    id: "admin-card-evaluations",
  },
  {
    href: "/admin/experiments",
    title: "ML Experiment Tracking",
    description: "Track model training runs, hyperparameters, and artifacts.",
    icon: "🧪",
    id: "admin-card-experiments",
  },
];

export default function AdminPage() {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <div className="admin-page">
      <header className="admin-page-header">
        <h2 className="admin-page-title">Administration</h2>
        <p className="admin-page-subtitle">
          Platform management tools. Changes here affect all users.
        </p>
      </header>

      <div className="admin-cards-grid">
        {ADMIN_CARDS.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            id={card.id}
            className="admin-hub-card"
          >
            <span className="admin-hub-card-icon" aria-hidden="true">
              {card.icon}
            </span>
            <div className="admin-hub-card-body">
              <h3 className="admin-hub-card-title">{card.title}</h3>
              <p className="admin-hub-card-desc">{card.description}</p>
            </div>
            <span className="admin-hub-card-arrow" aria-hidden="true">→</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
