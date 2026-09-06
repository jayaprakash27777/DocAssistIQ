/**
 * DocAssistIQ — Consultations List Page.
 *
 * Lists the current user's consultations, paginated, newest-first.
 * Fetches GET /api/v1/consultations/?page=N&page_size=20.
 *
 * States:
 *   - loading → skeleton rows
 *   - empty → call-to-action panel
 *   - list → consultation cards with pagination
 *   - error → error message
 */

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  listConsultations,
  PLACEHOLDER_LABEL,
  type ConsultationSummary,
  type PagedResponse,
} from "@/lib/api";
import { Skeleton } from "@/components/shell/LoadingSkeleton";

const PAGE_SIZE = 20;

export default function ConsultationsPage() {
  const [data, setData] = useState<PagedResponse<ConsultationSummary> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    async function load() {
      const result = await listConsultations(page, PAGE_SIZE);
      if (cancelled) return;
      setLoading(false);
      if (!result.ok) {
        setError(result.error.message ?? "Failed to load consultations.");
        return;
      }
      setData(result.data);
    }

    load();
    return () => { cancelled = true; };
  }, [page]);

  return (
    <div className="consult-list-page">
      {/* Page header */}
      <div className="consult-list-header">
        <div>
          <h2 className="consult-list-title">Consultations</h2>
          <p className="consult-list-subtitle">
            {data ? `${data.total} total` : "Loading…"}
          </p>
        </div>
        <Link href="/consultations/new" className="consult-new-btn" id="new-consultation-link">
          + New consultation
        </Link>
      </div>

      {/* Dev notice */}
      <div className="consult-list-notice" role="note">
        {PLACEHOLDER_LABEL}
      </div>

      {/* Loading */}
      {loading && (
        <div aria-busy="true" aria-label="Loading consultations…">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="consult-list-skeleton-row">
              <Skeleton height="0.875rem" width="40%" />
              <Skeleton height="0.75rem" width="60%" />
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="consult-list-error" role="alert">
          <p>{error}</p>
          <button onClick={() => { setError(null); setPage(1); }}>
            Retry
          </button>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && data?.total === 0 && (
        <div className="consult-list-empty">
          <div className="consult-list-empty-icon" aria-hidden="true">📋</div>
          <h3 className="consult-list-empty-title">No consultations yet</h3>
          <p className="consult-list-empty-text">
            Submit your first consultation to get started.
          </p>
          <Link href="/consultations/new" className="consult-new-btn">
            Start a new consultation
          </Link>
        </div>
      )}

      {/* Consultation list */}
      {!loading && !error && data && data.total > 0 && (
        <>
          <ul className="consult-list" aria-label="Consultations">
            {data.items.map((c) => (
              <li key={c.id} className="consult-list-item">
                <Link
                  href={`/consultations/${c.id}`}
                  className="consult-list-link"
                  id={`consultation-${c.id}`}
                >
                  <div className="consult-list-item-body">
                    <p className="consult-list-item-preview">{c.input_preview}</p>
                    <div className="consult-list-item-meta">
                      <span
                        className={`consult-status-pill consult-status-pill--${c.status}`}
                      >
                        {c.status}
                      </span>
                      <time
                        dateTime={c.created_at}
                        className="consult-list-item-date"
                      >
                        {new Date(c.created_at).toLocaleDateString()}
                      </time>
                      {c.is_placeholder && (
                        <span className="consult-list-item-placeholder-tag">
                          Placeholder
                        </span>
                      )}
                    </div>
                  </div>
                  <span className="consult-list-item-arrow" aria-hidden="true">→</span>
                </Link>
              </li>
            ))}
          </ul>

          {/* Pagination */}
          {data.pages > 1 && (
            <nav className="consult-list-pagination" aria-label="Consultation pages">
              <button
                className="consult-page-btn"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                aria-label="Previous page"
              >
                ← Previous
              </button>
              <span className="consult-page-info">
                Page {page} of {data.pages}
              </span>
              <button
                className="consult-page-btn"
                onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                disabled={page >= data.pages}
                aria-label="Next page"
              >
                Next →
              </button>
            </nav>
          )}
        </>
      )}

      {/* Safety footer */}
      <p className="consult-list-safety" role="note">
        REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED
      </p>
    </div>
  );
}
