"use client";

import React from "react";
import StateOutbreakRadar from "@/components/clinical/StateOutbreakRadar";
import { useRouter } from "next/navigation";

export default function OutbreaksPage() {
  const router = useRouter();

  const handleSelectOutbreak = (simulationQuery: string) => {
    sessionStorage.setItem("outbreak_simulation_query", simulationQuery);
    router.push("/consultations/new");
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <StateOutbreakRadar onSelectOutbreakForDiagnosis={handleSelectOutbreak} />
    </div>
  );
}
