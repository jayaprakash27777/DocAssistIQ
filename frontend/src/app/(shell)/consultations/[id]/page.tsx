/**
 * DocAssistIQ — Consultation Result Page.
 *
 * Displays a single consultation by ID.
 * Fetches GET /api/v1/consultations/{id}.
 *
 * States:
 *   - loading → skeleton
 *   - 404 / other user's consultation → not-found panel
 *   - success → response with MANDATORY PLACEHOLDER banner
 */

"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { getConsultation, PLACEHOLDER_LABEL, type ConsultationResponse } from "@/lib/api";
import { DashboardSkeleton } from "@/components/shell/LoadingSkeleton";

interface Props {
  params: Promise<{ id: string }>;
}

export default function ConsultationResultPage({ params }: Props) {
  const { id } = use(params);
  const [consultation, setConsultation] = useState<ConsultationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const result = await getConsultation(id);
      if (cancelled) return;
      setLoading(false);
      if (!result.ok) {
        setNotFound(true);
        return;
      }
      setConsultation(result.data);
    }

    load();
    return () => { cancelled = true; };
  }, [id]);

  if (loading) {
    return (
      <div aria-live="polite" aria-busy="true">
        <DashboardSkeleton />
      </div>
    );
  }

  if (notFound || !consultation) {
    return (
      <div className="consult-notfound" role="alert">
        <div className="consult-notfound-icon" aria-hidden="true">⊘</div>
        <h2 className="consult-notfound-title">Consultation not found</h2>
        <p className="consult-notfound-text">
          This consultation does not exist or does not belong to your account.
        </p>
        <Link href="/consultations" className="consult-notfound-link">
          ← Back to consultations
        </Link>
      </div>
    );
  }

  const date = new Date(consultation.created_at).toLocaleString();

  return (
    <div className="consult-result-page">
      {/* MANDATORY PLACEHOLDER BANNER — always visible */}
      <div
        className="consult-placeholder-banner"
        role="alert"
        aria-label="This is not a clinical result"
      >
        <span className="consult-placeholder-banner-icon" aria-hidden="true">⚠</span>
        <strong>{PLACEHOLDER_LABEL}</strong>
      </div>

      {/* Metadata */}
      <div className="consult-result-meta">
        <Link href="/consultations" className="consult-back-link">
          ← Consultations
        </Link>
        <time dateTime={consultation.created_at} className="consult-result-date">
          {date}
        </time>
      </div>

      {/* Input */}
      <section className="consult-section" aria-labelledby="consult-input-heading">
        <h2 id="consult-input-heading" className="consult-section-title">
          Clinical input
        </h2>
        <div className="consult-input-box">
          <p className="consult-input-text">{consultation.input_text}</p>
          <p className="consult-input-chars">
            {consultation.input_text.length.toLocaleString()} characters
          </p>
        </div>
      </section>

      {/* Response */}
      <section className="consult-section" aria-labelledby="consult-response-heading">
        <h2 id="consult-response-heading" className="consult-section-title">
          Response
          <span className="consult-status-pill consult-status-pill--completed">
            {consultation.status}
          </span>
        </h2>

        {consultation.placeholder_response ? (
          <div className="consult-response-box">
            <pre className="consult-response-text">
              {consultation.placeholder_response}
            </pre>
          </div>
        ) : (
          <p className="consult-response-empty">No response available yet.</p>
        )}
      </section>

      {/* Footer safety */}
      <p className="consult-result-safety" role="note">
        REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED
      </p>
    </div>
  );
}
