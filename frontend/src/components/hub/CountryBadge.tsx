"use client";

import React from "react";

interface CountryBadgeProps {
  country?: string | null;
  licenseBody?: string | null;
  className?: string;
}

export function CountryBadge({ country, licenseBody, className = "" }: CountryBadgeProps) {
  const c = country?.toLowerCase() || "";
  const b = licenseBody?.toUpperCase() || "";

  let flag = "🌐";
  let label = "Global Board";

  if (c.includes("united kingdom") || c.includes("uk") || b.includes("GMC") || b.includes("NHS")) {
    flag = "🇬🇧";
    label = "UK GMC";
  } else if (c.includes("united states") || c.includes("us") || b.includes("USMLE") || b.includes("ABMS") || b.includes("ABEM")) {
    flag = "🇺🇸";
    label = "US ABMS/USMLE";
  } else if (c.includes("india") || b.includes("NMC") || b.includes("MCI")) {
    flag = "🇮🇳";
    label = "India NMC";
  } else if (c.includes("australia") || b.includes("AHPRA")) {
    flag = "🇦🇺";
    label = "Australia AHPRA";
  } else if (c.includes("canada") || b.includes("RCPSC") || b.includes("MCC")) {
    flag = "🇨🇦";
    label = "Canada RCPSC";
  } else if (c.includes("germany") || b.includes("APPROBATION")) {
    flag = "🇩🇪";
    label = "Germany Approbation";
  } else if (licenseBody) {
    label = licenseBody;
  }

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200/90 shadow-2xs select-none ${className}`}
      title={`Verified Clinician: ${label}`}
    >
      <span className="text-xs leading-none">{flag}</span>
      <span>{label}</span>
    </span>
  );
}

export default CountryBadge;
