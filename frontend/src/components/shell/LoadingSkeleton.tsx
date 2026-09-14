/* eslint-disable @typescript-eslint/no-unused-vars */
/**
 * DocAssistIQ — Loading Skeleton.
 *
 * Generic shimmer skeleton components for loading states.
 *
 * Usage:
 *   <Skeleton width="100%" height="1.5rem" />
 *   <Skeleton.Text lines={3} />
 *   <Skeleton.Card />
 *   <Skeleton.Row />
 */

import React from "react";
import { Skeleton as UiSkeleton } from "@/components/ui/skeleton";

interface SkeletonProps {
  width?: string;
  height?: string;
  className?: string;
  borderRadius?: string;
}

export function Skeleton({
  width = "100%",
  height = "1rem",
  className = "",
  borderRadius = "6px",
}: SkeletonProps) {
  return (
    <UiSkeleton
      className={className}
      style={{ width, height, borderRadius }}
      aria-hidden="true"
    />
  );
}

// ── Composites ────────────────────────────────────────────────

interface TextProps {
  lines?: number;
  lastLineWidth?: string;
}

Skeleton.Text = function SkeletonText({ lines = 3, lastLineWidth = "60%" }: TextProps) {
  return (
    <div className="skeleton-text" aria-hidden="true">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          height="0.875rem"
          width={i === lines - 1 ? lastLineWidth : "100%"}
        />
      ))}
    </div>
  );
};

Skeleton.Card = function SkeletonCard() {
  return (
    <div className="skeleton-card" aria-hidden="true" aria-label="Loading…">
      <div className="skeleton-card-icon">
        <Skeleton width="2.5rem" height="2.5rem" borderRadius="50%" />
      </div>
      <div className="skeleton-card-body">
        <Skeleton height="1rem" width="40%" />
        <Skeleton.Text lines={2} lastLineWidth="70%" />
      </div>
    </div>
  );
};

Skeleton.Row = function SkeletonRow() {
  return (
    <div className="skeleton-row" aria-hidden="true">
      <Skeleton width="2rem" height="2rem" borderRadius="50%" />
      <div className="skeleton-row-content">
        <Skeleton height="0.875rem" width="30%" />
        <Skeleton height="0.75rem" width="50%" />
      </div>
      <Skeleton width="4rem" height="1.5rem" />
    </div>
  );
};

// ── Dashboard skeleton ─────────────────────────────────────────

export function DashboardSkeleton() {
  return (
    <div className="dashboard-skeleton" aria-label="Loading workspace…" aria-busy="true">
      <div className="dashboard-skeleton-welcome">
        <Skeleton height="1.75rem" width="280px" />
        <Skeleton height="1rem" width="420px" />
      </div>
      <div className="dashboard-skeleton-cards">
        {[0, 1, 2].map((i) => (
          <Skeleton.Card key={i} />
        ))}
      </div>
    </div>
  );
}
