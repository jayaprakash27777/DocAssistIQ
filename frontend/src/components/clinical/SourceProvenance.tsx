/* eslint-disable @typescript-eslint/no-unused-vars */
/**
 * DocAssistIQ — Source Provenance Component (Phase 12).
 *
 * Displays reference citations and evidence grades for clinical claims.
 * Enforces the clinical safety requirement that all AI suggestions must
 * carry a traceable source.
 */

import React from "react";

export interface EvidenceInfo {
  id: string;
  sourceCode: string;
  sourceName: string;
  articleTitle?: string;
  evidenceGrade: string; // e.g. "Ia", "IIb"
  url?: string;
  isAiGenerated: boolean;
}

interface SourceProvenanceProps {
  evidence: EvidenceInfo[];
  className?: string;
}

export function SourceProvenance({ evidence, className = "" }: SourceProvenanceProps) {
  if (!evidence || evidence.length === 0) return null;

  return (
    <div className={`source-provenance ${className}`} role="complementary" aria-label="Clinical References">
      <h4 className="source-provenance-title">Evidence &amp; References</h4>
      <ul className="source-provenance-list">
        {evidence.map((ev) => (
          <li key={ev.id} className="source-provenance-item">
            <div className="source-provenance-meta">
              <span className={`evidence-grade grade-${ev.evidenceGrade.toLowerCase()}`}>
                Level {ev.evidenceGrade}
              </span>
              <span className="source-name" title={ev.sourceCode}>
                {ev.sourceName}
              </span>
              {ev.isAiGenerated && (
                <span className="ai-badge" title="Extracted via AI Analysis — Requires Clinical Review">
                  AI Extracted
                </span>
              )}
            </div>
            
            {ev.articleTitle && (
              <div className="source-article">
                {ev.url ? (
                  <a href={ev.url} target="_blank" rel="noopener noreferrer" className="source-link">
                    {ev.articleTitle}
                  </a>
                ) : (
                  <span>{ev.articleTitle}</span>
                )}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
