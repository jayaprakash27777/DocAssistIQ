"use client";

import React, { useState, useEffect } from "react";
import { toast } from "react-hot-toast";
import { motion } from "framer-motion";
import { ShieldAlert, BookOpen, Activity, Loader2, Globe } from "lucide-react";

interface RAGCitation {
    source_id: string;
    source_type: string;
    source_uri: string;
    preview_text: string;
}

interface DiseaseIntelligenceResponse {
    disease_name: string;
    summary: string;
    symptoms: string[];
    treatments: string[];
    investigations: string[];
    citations: RAGCitation[];
}

export default function DiseaseIntelligencePanel({ consultationId, disease }: { consultationId: string, disease: string }) {
    const [data, setData] = useState<DiseaseIntelligenceResponse | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchIntel() {
            setLoading(true);
            try {
                // In a real app we'd add this to the api client, doing a raw fetch here for phase 4/prototype
                const res = await fetch(`/api/v1/consultations/${consultationId}/disease-intelligence?disease=${encodeURIComponent(disease)}`, {
                    headers: {
                        "Authorization": `Bearer ${localStorage.getItem("token")}`
                    }
                });
                if (!res.ok) {
                    throw new Error("Failed to load disease intelligence.");
                }
                const json = await res.json();
                setData(json);
            } catch (err: any) {
                toast.error(err.message || "Failed to load disease intelligence.");
            }
            setLoading(false);
        }
        if (disease) {
            fetchIntel();
        }
    }, [consultationId, disease]);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center p-8 text-[var(--text-tertiary)]">
                <Loader2 className="w-8 h-8 animate-spin mb-4 text-[var(--color-primary-500)]" />
                <p className="text-sm font-medium animate-pulse">Consulting World Health Data for {disease}...</p>
            </div>
        );
    }

    if (!data) return null;

    return (
        <div className="bg-[var(--surface-sunken)] p-6 rounded-xl border border-[var(--border-subtle)]">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                <div className="flex items-center gap-2">
                    <Globe className="w-5 h-5 text-[var(--color-primary-600)]" />
                    <h4 className="text-lg font-bold text-[var(--color-primary-950)]">Geographic Disease Intelligence</h4>
                </div>
                <div className="flex items-center gap-1.5 px-3 py-1 bg-green-50 text-green-700   rounded-full border border-green-200  shadow-sm self-start">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    <span className="text-[10px] font-bold uppercase tracking-widest">Live Sync</span>
                </div>
            </div>
            
            <p className="text-sm text-[var(--text-secondary)] mb-6 leading-relaxed">
                {data.summary}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div className="bg-white/50 rounded-lg p-4 border border-[var(--border-default)]">
                    <h5 className="flex items-center gap-2 text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-widest mb-3">
                        <Activity className="w-4 h-4"/> Symptoms
                    </h5>
                    <ul className="space-y-1">
                        {data.symptoms.map((s, i) => (
                            <li key={i} className="text-sm text-[var(--text-primary)] font-medium">• {s}</li>
                        ))}
                    </ul>
                </div>
                
                <div className="bg-white/50 rounded-lg p-4 border border-[var(--border-default)]">
                    <h5 className="flex items-center gap-2 text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-widest mb-3">
                        <ShieldAlert className="w-4 h-4"/> Treatments
                    </h5>
                    <ul className="space-y-1">
                        {data.treatments.map((t, i) => (
                            <li key={i} className="text-sm text-[var(--text-primary)] font-medium">• {t}</li>
                        ))}
                    </ul>
                </div>
                
                <div className="bg-white/50 rounded-lg p-4 border border-[var(--border-default)]">
                    <h5 className="flex items-center gap-2 text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-widest mb-3">
                        <BookOpen className="w-4 h-4"/> Investigations
                    </h5>
                    <ul className="space-y-1">
                        {data.investigations.map((inv, i) => (
                            <li key={i} className="text-sm text-[var(--text-primary)] font-medium">• {inv}</li>
                        ))}
                    </ul>
                </div>
            </div>

            {data.citations && data.citations.length > 0 && (
                <div className="pt-4 border-t border-[var(--border-subtle)]">
                    <h5 className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-widest mb-3">
                        RAG Citations (CDC / WHO)
                    </h5>
                    <div className="space-y-2">
                        {data.citations.map((c, i) => (
                            <div key={i} className="text-xs text-[var(--text-secondary)]">
                                <a href={c.source_uri} target="_blank" rel="noreferrer" className="text-[var(--color-primary-600)] hover:underline font-medium">[{i+1}] {c.source_type}</a>: {c.preview_text.substring(0, 100)}...
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
