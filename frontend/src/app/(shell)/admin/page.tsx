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
