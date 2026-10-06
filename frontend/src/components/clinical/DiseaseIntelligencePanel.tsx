/**
 * DocAssistIQ - Deep Disease Intelligence Panel (v3 World-Class)
 *
 * Tabbed layout covering all 20+ intelligence fields:
 * Tab 1: Overview (summary, pathophysiology, etiology, ICD code)
 * Tab 2: Clinical (symptoms, signs, stages, red flags)
 * Tab 3: Investigations (prioritized test list with rationale)
 * Tab 4: Management (treatment, first-line, monitoring)
 * Tab 5: Epidemiology (incidence, regions, risk groups, prevention)
 * Tab 6: Special Populations + Public Health
 */
"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity, AlertTriangle, FlaskConical, Pill, Globe, Users,
  Info, BookOpen, ChevronRight, ExternalLink, Shield, Zap, Calendar, AlertOctagon,
  Network, Layers, CheckCircle2, Search
} from "lucide-react";
import { getStoredToken } from "@/lib/api";


interface GraphNode {
  id: string;
  code: string;
  name: string;
  category?: string;
  node_type: string;
}

interface GraphEdge {
  source_id: string;
  target_id: string;
  relationship: string;
  metadata?: Record<string, unknown>;
}

interface DiseaseKnowledgeGraphData {
  disease_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/api\/v1\/?$/, "");

interface EpidemiologyData {
  global_incidence?: string;
  mortality_rate?: string;
  affected_regions: string[];
  outbreak_status?: string;
  seasonal_pattern?: string;
  high_risk_groups: string[];
}

interface SpecialPopulation {
  population: string;
  warning: string;
  recommendation: string;
}

interface DiseaseIntelligence {
  disease_name: string;
  summary: string;
  pathophysiology?: string;
  etiology?: string;
  icd11_code?: string;
  who_classification?: string;
  disease_class?: string;
  is_notifiable: boolean;
  is_outbreak_active: boolean;
  symptoms: string[];
  cardinal_symptoms: string[];
  signs_on_examination: string[];
  red_flags: string[];
  incubation_period?: string;
  disease_stages: string[];
  prognosis?: string;
  complications: string[];
  first_line_treatment?: string;
  treatments: string[];
  medications?: string[];
  monitoring_parameters: string[];
  investigations: string[];
  differential_diagnosis_clues: string[];
  epidemiology?: EpidemiologyData;
  prevention: string[];
  public_health_measures: string[];
  special_populations: SpecialPopulation[];
  citations: { source_type: string; source_uri: string; preview_text: string }[];
  data_sources: string[];
  last_updated?: string;
}

const TABS = [
  { id: "overview",       label: "Overview",         icon: BookOpen },
  { id: "clinical",       label: "Clinical",         icon: Activity },
  { id: "investigations", label: "Investigations",   icon: FlaskConical },
  { id: "management",     label: "Management",       icon: Pill },
  { id: "epidemiology",   label: "Epidemiology",     icon: Globe },
  { id: "populations",    label: "Populations",      icon: Users },
  { id: "graph",          label: "Knowledge Graph",  icon: Network },
];

function Badge({ text, variant = "neutral" }: { text: string; variant?: "danger" | "warning" | "success" | "neutral" | "primary" }) {
  const styles = {
    danger:  "bg-red-50   text-red-700   border-red-200",
    warning: "bg-amber-50 text-amber-700 border-amber-200",
    success: "bg-green-50 text-green-700 border-green-200",
    primary: "bg-blue-50  text-blue-700  border-blue-200",
    neutral: "bg-slate-50 text-slate-700 border-slate-200",
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${styles[variant]}`}>
      {text}
    </span>
  );
}

function SectionCard({ title, icon: Icon, children, accent = "blue" }: {
  title: string; icon: React.ElementType; children: React.ReactNode; accent?: string;
}) {
  const accents: Record<string, string> = {
    blue:   "border-l-blue-500 bg-blue-50/30",
    red:    "border-l-red-500  bg-red-50/30",
    green:  "border-l-green-500 bg-green-50/30",
    amber:  "border-l-amber-500 bg-amber-50/30",
    purple: "border-l-purple-500 bg-purple-50/30",
  };
  return (
    <div className={`border-l-4 ${accents[accent] ?? accents.blue} rounded-r-xl p-4 mb-4`}>
      <div className="flex items-center gap-2 mb-3">
        <Icon className="w-4 h-4 text-slate-600" />
        <h4 className="text-sm font-bold text-slate-700 uppercase tracking-wider">{title}</h4>
      </div>
      {children}
    </div>
  );
}

function BulletList({ items, highlight = [] }: { items: string[]; highlight?: string[] }) {
  if (!items || items.length === 0) return <p className="text-xs text-slate-400 italic">Not documented</p>;
  return (
    <ul className="space-y-1.5">
      {items.map((item, i) => {
        const isHighlighted = highlight.includes(item);
        return (
          <li key={i} className={`flex items-start gap-2 text-sm ${isHighlighted ? "font-semibold text-slate-800" : "text-slate-600"}`}>
            <span className={`mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${isHighlighted ? "bg-blue-500" : "bg-slate-300"}`} />
            {isHighlighted && <span className="text-blue-500">★ </span>}
            {item}
          </li>
        );
      })}
    </ul>
  );
}

export default function DiseaseIntelligencePanel({
  disease,
  consultationId,
}: {
  disease: string;
  consultationId?: string;
}) {
  const [data, setData] = useState<DiseaseIntelligence | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [graphData, setGraphData] = useState<DiseaseKnowledgeGraphData | null>(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [graphError, setGraphError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [graphFilter, setGraphFilter] = useState<string>("all");

  useEffect(() => {
    if (!disease) return;
    let aborted = false;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 90000); // 90s max

    const load = async () => {
      setLoading(true);
      setError(null);
      const token = getStoredToken() || (typeof window !== "undefined" ? (localStorage.getItem("access_token") || localStorage.getItem("token")) : null) || "";
      const reqHeaders: Record<string, string> = {};
      if (token) reqHeaders.Authorization = `Bearer ${token}`;
      try {
        const params = consultationId ? `?consultation_id=${consultationId}` : "";
        const res = await fetch(
          `${API_BASE}/api/v1/intelligence/disease/${encodeURIComponent(disease)}${params}`,
          {
            signal: controller.signal,
            headers: reqHeaders,
          }
        );
        clearTimeout(timeoutId);
        if (aborted) return;
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        setData(await res.json());
      } catch (e: unknown) {
        clearTimeout(timeoutId);
        if (aborted) return;
        if (e instanceof Error && e.name === "AbortError") {
          setError("AI processing took too long — static clinical data shown below.");
          // Try static fallback via a second quick call (should succeed immediately from static KB)
          try {
            const params = consultationId ? `?consultation_id=${consultationId}` : "";
            const fallbackRes = await fetch(
              `${API_BASE}/api/v1/intelligence/disease/${encodeURIComponent(disease)}${params}`,
              { headers: reqHeaders }
            );
            if (fallbackRes.ok) { setData(await fallbackRes.json()); setError(null); }
          } catch { /* keep timeout error */ }
        } else {
          setError(String(e));
        }
      } finally {
        if (!aborted) setLoading(false);
      }
    };
    load();
    return () => { aborted = true; clearTimeout(timeoutId); controller.abort(); };
  }, [disease, consultationId]);


  useEffect(() => {
    if (!disease || activeTab !== "graph" || graphData) return;
    let cancelled = false;
    const fetchGraph = async () => {
      setGraphLoading(true);
      setGraphError(null);
      try {
        const token = getStoredToken() || (typeof window !== "undefined" ? (localStorage.getItem("access_token") || localStorage.getItem("token")) : null) || "";
        const reqHeaders: Record<string, string> = {};
        if (token) reqHeaders.Authorization = `Bearer ${token}`;
        const res = await fetch(`${API_BASE}/api/v1/knowledge/graph/by-disease/${encodeURIComponent(disease)}`, {
          headers: reqHeaders,
        });
        if (cancelled) return;
        if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to load graph`);
        const json = await res.json();
        setGraphData(json);
        const root = json.nodes?.find((n: GraphNode) => n.node_type === "disease");
        if (root) setSelectedNode(root);
      } catch (err: unknown) {
        if (!cancelled) setGraphError(err instanceof Error ? err.message : "Unable to load knowledge graph");
      } finally {
        if (!cancelled) setGraphLoading(false);
      }
    };
    fetchGraph();
    return () => { cancelled = true; };
  }, [disease, activeTab, graphData]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-4">
        <div className="relative">
          <div className="w-12 h-12 border-4 border-blue-100 border-t-blue-500 rounded-full animate-spin" />
          <Activity className="w-5 h-5 text-blue-500 absolute inset-0 m-auto" />
        </div>
        <p className="text-sm text-slate-500 font-medium">Generating deep clinical intelligence...</p>
        <p className="text-xs text-slate-400">Querying WHO · ICD-11 · PubMed · Wikipedia · RAG</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
        <AlertTriangle className="w-4 h-4 inline mr-2" />
        {error}
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="rounded-3xl border border-slate-200/80 bg-white shadow-[0_12px_44px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.95)] overflow-hidden">
      {/* Header */}
      <div className="bg-white border-b border-slate-200/90 px-7 py-6 shadow-xs">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-slate-900 font-black text-2xl tracking-tight font-heading">{data.disease_name}</h3>
            <div className="flex flex-wrap items-center gap-2 mt-2.5">
              {data.icd11_code && (
                <span className="text-xs bg-slate-100 text-slate-700 px-2.5 py-0.5 rounded-full font-mono border border-slate-200 font-bold">
                  ICD-11: {data.icd11_code}
                </span>
              )}
              {data.disease_class && (
                <span className="text-xs bg-blue-50 text-blue-700 px-2.5 py-0.5 rounded-full border border-blue-200 font-bold">
                  {data.disease_class}
                </span>
              )}
              {data.is_notifiable && (
                <span className="flex items-center gap-1.5 text-xs bg-amber-50 text-amber-800 px-2.5 py-0.5 rounded-full border border-amber-200 font-bold">
                  <Shield className="w-3.5 h-3.5 text-amber-600" /> Notifiable Disease
                </span>
              )}
              {data.is_outbreak_active && (
                <span className="flex items-center gap-1.5 text-xs bg-rose-50 text-rose-700 px-2.5 py-0.5 rounded-full border border-rose-200 font-extrabold shadow-2xs">
                  <Zap className="w-3.5 h-3.5 text-rose-600" /> Active Outbreak
                </span>
              )}
            </div>
          </div>
          {data.last_updated && (
            <span className="text-xs text-slate-400 shrink-0 font-medium">
              Updated: {data.last_updated}
            </span>
          )}
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex border-b border-slate-200 bg-slate-50/90 backdrop-blur-md overflow-x-auto px-2 pt-1">
        {TABS.map(tab => (
          <button
            key={tab.id}
            id={`di-tab-${tab.id}`}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-5 py-3 text-xs font-bold whitespace-nowrap transition-all border-b-2 rounded-t-xl ${
              activeTab === tab.id
                ? "border-indigo-600 text-indigo-700 bg-white shadow-xs"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:bg-white/60"
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="p-5 max-h-[520px] overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
          >
            {/* OVERVIEW TAB */}
            {activeTab === "overview" && (
              <div className="space-y-4">
                <SectionCard title="Summary" icon={Info} accent="blue">
                  <p className="text-sm text-slate-700 leading-relaxed">{data.summary || "Not available."}</p>
                </SectionCard>

                {data.pathophysiology && (
                  <SectionCard title="Pathophysiology" icon={Activity} accent="purple">
                    <p className="text-sm text-slate-700 leading-relaxed">{data.pathophysiology}</p>
                  </SectionCard>
                )}

                {data.etiology && (
                  <SectionCard title="Etiology & Transmission" icon={ChevronRight} accent="green">
                    <p className="text-sm text-slate-700 leading-relaxed">{data.etiology}</p>
                  </SectionCard>
                )}

                {data.incubation_period && (
                  <div className="flex items-center gap-3 p-3 bg-slate-50 border border-slate-200 rounded-xl">
                    <span className="text-2xl">⏱</span>
                    <div>
                      <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Incubation Period</p>
                      <p className="text-sm font-semibold text-slate-800">{data.incubation_period}</p>
                    </div>
                  </div>
                )}

                {data.prognosis && (
                  <SectionCard title="Prognosis" icon={ChevronRight} accent="amber">
                    <p className="text-sm text-slate-700 leading-relaxed">{data.prognosis}</p>
                  </SectionCard>
                )}

                {/* Sources */}
                {data.data_sources && data.data_sources.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-100">
                    <span className="text-xs text-slate-400 self-center">Sources:</span>
                    {data.data_sources.map((s, i) => (
                      <Badge key={i} text={s} variant="neutral" />
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* CLINICAL TAB */}
            {activeTab === "clinical" && (
              <div className="space-y-4">
                {data.red_flags.length > 0 && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
                    <div className="flex items-center gap-2 mb-3">
                      <AlertTriangle className="w-4 h-4 text-red-600" />
                      <h4 className="text-sm font-bold text-red-700 uppercase tracking-wider">⚠ Red Flags — Immediate Escalation</h4>
                    </div>
                    <ul className="space-y-1">
                      {data.red_flags.map((rf, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-red-700 font-medium">
                          <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0" />
                          {rf}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <SectionCard title="Cardinal Symptoms" icon={Activity} accent="blue">
                    <BulletList items={data.symptoms} highlight={data.cardinal_symptoms} />
                  </SectionCard>

                  <SectionCard title="Signs on Examination" icon={Activity} accent="purple">
                    <BulletList items={data.signs_on_examination} />
                  </SectionCard>
                </div>

                {data.disease_stages.length > 0 && (
                  <SectionCard title="Disease Stages" icon={ChevronRight} accent="green">
                    <div className="space-y-2">
                      {data.disease_stages.map((stage, i) => (
                        <div key={i} className="flex gap-3 items-start">
                          <span className="w-6 h-6 rounded-full bg-green-100 text-green-700 text-xs font-bold flex items-center justify-center flex-shrink-0">{i + 1}</span>
                          <p className="text-sm text-slate-700">{stage}</p>
                        </div>
                      ))}
                    </div>
                  </SectionCard>
                )}

                {data.complications.length > 0 && (
                  <SectionCard title="Complications" icon={AlertTriangle} accent="amber">
                    <BulletList items={data.complications} />
                  </SectionCard>
                )}

                {data.differential_diagnosis_clues.length > 0 && (
                  <SectionCard title="Differential Diagnosis Clues" icon={Info} accent="purple">
                    <BulletList items={data.differential_diagnosis_clues} />
                  </SectionCard>
                )}
              </div>
            )}

            {/* INVESTIGATIONS TAB */}
            {activeTab === "investigations" && (
              <div className="space-y-3">
                <p className="text-xs text-slate-500 italic mb-4">
                  Drag any investigation to the Clinical Note Editor to add it to the plan.
                </p>
                {data.investigations.length === 0 ? (
                  <p className="text-sm text-slate-400 italic">No investigation data available.</p>
                ) : (
                  data.investigations.map((inv, i) => (
                    <div
                      key={i}
                      draggable
                      onDragStart={e => {
                        e.dataTransfer.setData("text/plain", `Order: ${inv}`);
                      }}
                      className="group flex items-start gap-3 p-3 bg-white border border-slate-200 hover:border-blue-300 rounded-xl cursor-grab active:cursor-grabbing hover:shadow-sm transition-all"
                    >
                      <span className="text-slate-300 group-hover:text-blue-400 transition-colors text-lg leading-none">⠿</span>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-slate-800">{inv}</p>
                      </div>
                      <span className="opacity-0 group-hover:opacity-100 text-xs text-slate-400 transition-opacity">Drag to note</span>
                    </div>
                  ))
                )}

                {data.monitoring_parameters.length > 0 && (
                  <div className="mt-4">
                    <SectionCard title="Monitoring Parameters" icon={Activity} accent="green">
                      <BulletList items={data.monitoring_parameters} />
                    </SectionCard>
                  </div>
                )}
              </div>
            )}

            {/* MANAGEMENT TAB */}
            {activeTab === "management" && (
              <div className="space-y-4">
                {data.first_line_treatment && (
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl">
                    <p className="text-xs font-bold text-blue-600 uppercase tracking-wider mb-1">First-Line Treatment</p>
                    <p className="text-sm font-semibold text-blue-900">{data.first_line_treatment}</p>
                  </div>
                )}

                <SectionCard title="Treatment Options" icon={Pill} accent="blue">
                  {data.treatments.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No treatment data available.</p>
                  ) : (
                    <ul className="space-y-2">
                      {data.treatments.map((tx, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                          <span className="mt-1 w-5 h-5 bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center rounded flex-shrink-0">{i + 1}</span>
                          {tx}
                        </li>
                      ))}
                    </ul>
                  )}
                </SectionCard>

                {data.medications && data.medications.length > 0 && (
                  <SectionCard title="Medications & Pharmacotherapy" icon={Pill} accent="purple">
                    <p className="text-xs text-slate-500 italic mb-2">
                      Drag any medication to the Clinical Note Editor to add it to your prescription plan.
                    </p>
                    <div className="space-y-2">
                      {data.medications.map((med, i) => (
                        <div
                          key={i}
                          draggable
                          onDragStart={e => {
                            e.dataTransfer.setData("text/plain", `Rx: ${med}`);
                          }}
                          className="group flex items-start gap-3 p-3 bg-white border border-purple-200/80 hover:border-purple-400 rounded-xl cursor-grab active:cursor-grabbing hover:shadow-sm transition-all"
                        >
                          <span className="text-slate-300 group-hover:text-purple-500 transition-colors text-lg leading-none">⠿</span>
                          <div className="flex-1">
                            <p className="text-sm font-semibold text-purple-950">{med}</p>
                          </div>
                          <span className="opacity-0 group-hover:opacity-100 text-xs text-purple-500 font-medium transition-opacity">Drag to Rx</span>
                        </div>
                      ))}
                    </div>
                  </SectionCard>
                )}

                {data.monitoring_parameters.length > 0 && (
                  <SectionCard title="Monitoring" icon={Activity} accent="green">
                    <BulletList items={data.monitoring_parameters} />
                  </SectionCard>
                )}
              </div>
            )}

            {/* EPIDEMIOLOGY TAB */}
            {activeTab === "epidemiology" && (
              <div className="space-y-4">
                {data.epidemiology && (
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label: "Global Incidence", val: data.epidemiology.global_incidence, icon: Globe },
                      { label: "Mortality Rate", val: data.epidemiology.mortality_rate, icon: Activity },
                      { label: "Outbreak Status", val: data.epidemiology.outbreak_status, icon: AlertOctagon },
                      { label: "Seasonal Pattern", val: data.epidemiology.seasonal_pattern, icon: Calendar },
                    ].map(({ label, val, icon: Icon }) => val && (
                      <div key={label} className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                        <p className="text-xs text-slate-500 font-semibold mb-1 flex items-center gap-1.5">
                          <Icon className="w-3.5 h-3.5 text-slate-600 shrink-0" />
                          <span>{label}</span>
                        </p>
                        <p className="text-sm font-medium text-slate-800">{String(val)}</p>
                      </div>
                    ))}
                  </div>
                )}

                {data.epidemiology?.affected_regions && data.epidemiology.affected_regions.length > 0 && (
                  <SectionCard title="Affected Regions" icon={Globe} accent="blue">
                    <div className="flex flex-wrap gap-2">
                      {data.epidemiology.affected_regions.map((r, i) => (
                        <Badge key={i} text={r} variant="primary" />
                      ))}
                    </div>
                  </SectionCard>
                )}

                {data.epidemiology?.high_risk_groups && data.epidemiology.high_risk_groups.length > 0 && (
                  <SectionCard title="High-Risk Groups" icon={Users} accent="amber">
                    <BulletList items={data.epidemiology.high_risk_groups} />
                  </SectionCard>
                )}

                {data.prevention.length > 0 && (
                  <SectionCard title="Prevention" icon={Shield} accent="green">
                    <BulletList items={data.prevention} />
                  </SectionCard>
                )}

                {data.public_health_measures.length > 0 && (
                  <SectionCard title="Public Health Measures" icon={AlertTriangle} accent="red">
                    <BulletList items={data.public_health_measures} />
                  </SectionCard>
                )}
              </div>
            )}

            {/* POPULATIONS TAB */}
            {activeTab === "populations" && (
              <div className="space-y-4">
                {data.special_populations.length === 0 ? (
                  <p className="text-sm text-slate-400 italic">No special population data available.</p>
                ) : (
                  data.special_populations.map((sp, i) => (
                    <div key={i} className="p-4 border border-amber-200 bg-amber-50/50 rounded-xl">
                      <div className="flex items-center gap-2 mb-2">
                        <Users className="w-4 h-4 text-amber-600" />
                        <h5 className="font-bold text-amber-800 text-sm">{sp.population}</h5>
                      </div>
                      {sp.warning && (
                        <p className="text-sm text-amber-900 mb-2">
                          <span className="font-semibold">⚠ Warning:</span> {sp.warning}
                        </p>
                      )}
                      {sp.recommendation && (
                        <p className="text-sm text-amber-800">
                          <span className="font-semibold">✓ Recommendation:</span> {sp.recommendation}
                        </p>
                      )}
                    </div>
                  ))
                )}

                {/* Citations */}
                {data.citations && data.citations.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-slate-200">
                    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Citations</h4>
                    <div className="space-y-2">
                      {data.citations.slice(0, 5).map((c, i) => (
                        <a
                          key={i}
                          href={c.source_uri}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-start gap-2 p-2 hover:bg-slate-50 rounded-lg group transition-colors"
                        >
                          <ExternalLink className="w-3 h-3 text-blue-400 mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="text-xs font-semibold text-blue-600 group-hover:underline">{c.source_type}</p>
                            <p className="text-xs text-slate-500 line-clamp-2">{c.preview_text}</p>
                          </div>
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* KNOWLEDGE GRAPH TAB */}
            {activeTab === "graph" && (
              <div className="space-y-4">
                {graphLoading && (
                  <div className="flex flex-col items-center justify-center py-16 gap-3">
                    <div className="w-10 h-10 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin" />
                    <p className="text-xs font-semibold text-slate-500">Querying PostgreSQL Knowledge Graph & Clinical Ontologies...</p>
                  </div>
                )}

                {graphError && (
                  <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-center justify-between">
                    <span>{graphError}</span>
                    <button
                      onClick={() => { setGraphData(null); }}
                      className="px-3 py-1 bg-amber-200/60 hover:bg-amber-200 text-amber-900 rounded-lg font-bold text-xs"
                    >
                      Retry
                    </button>
                  </div>
                )}

                {graphData && (
                  <div className="space-y-4">
                    {/* Header stats & filter */}
                    <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 bg-slate-50 border border-slate-200 rounded-2xl">
                      <div className="flex items-center gap-2">
                        <Network className="w-4 h-4 text-indigo-600" />
                        <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                          Graph Topology: {graphData.nodes.length} Nodes · {graphData.edges.length} Edges
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {["all", "symptom", "investigation", "medicine"].map(type => (
                          <button
                            key={type}
                            onClick={() => setGraphFilter(type)}
                            className={`px-2.5 py-1 rounded-lg text-xs font-semibold capitalize transition-colors ${
                              graphFilter === type
                                ? "bg-indigo-600 text-white shadow-xs"
                                : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-100"
                            }`}
                          >
                            {type === "all" ? "All Nodes" : `${type}s`}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Interactive 3-Cluster Layout */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {/* Left: Symptoms */}
                      {(graphFilter === "all" || graphFilter === "symptom") && (
                        <div className="border border-slate-200 bg-slate-50/50 rounded-2xl p-3.5">
                          <div className="flex items-center justify-between mb-2.5">
                            <span className="text-xs font-bold text-blue-700 uppercase tracking-wider flex items-center gap-1.5">
                              <Activity className="w-3.5 h-3.5" /> Manifestations
                            </span>
                            <span className="text-xs font-mono bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full font-bold">
                              {graphData.nodes.filter(n => n.node_type === "symptom").length}
                            </span>
                          </div>
                          <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                            {graphData.nodes.filter(n => n.node_type === "symptom").map(node => (
                              <div
                                key={node.id}
                                onClick={() => setSelectedNode(node)}
                                className={`p-2.5 rounded-xl border transition-all cursor-pointer ${
                                  selectedNode?.id === node.id
                                    ? "bg-blue-50 border-blue-400 shadow-xs"
                                    : "bg-white border-slate-200 hover:border-blue-300"
                                }`}
                              >
                                <div className="flex items-center justify-between gap-1">
                                  <span className="text-xs font-bold text-slate-800">{node.name}</span>
                                  <span className="text-[10px] font-mono text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                                    {node.code}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Middle: Investigations */}
                      {(graphFilter === "all" || graphFilter === "investigation") && (
                        <div className="border border-slate-200 bg-slate-50/50 rounded-2xl p-3.5">
                          <div className="flex items-center justify-between mb-2.5">
                            <span className="text-xs font-bold text-purple-700 uppercase tracking-wider flex items-center gap-1.5">
                              <FlaskConical className="w-3.5 h-3.5" /> Diagnostic Workup
                            </span>
                            <span className="text-xs font-mono bg-purple-100 text-purple-800 px-2 py-0.5 rounded-full font-bold">
                              {graphData.nodes.filter(n => n.node_type === "investigation").length}
                            </span>
                          </div>
                          <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                            {graphData.nodes.filter(n => n.node_type === "investigation").map(node => (
                              <div
                                key={node.id}
                                draggable
                                onDragStart={e => e.dataTransfer.setData("text/plain", `Order: ${node.name}`)}
                                onClick={() => setSelectedNode(node)}
                                className={`p-2.5 rounded-xl border transition-all cursor-pointer group ${
                                  selectedNode?.id === node.id
                                    ? "bg-purple-50 border-purple-400 shadow-xs"
                                    : "bg-white border-slate-200 hover:border-purple-300"
                                }`}
                              >
                                <div className="flex items-center justify-between gap-1">
                                  <span className="text-xs font-bold text-slate-800">{node.name}</span>
                                  <span className="text-[10px] font-mono text-purple-600 bg-purple-50 px-1.5 py-0.5 rounded">
                                    {node.code}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Right: Medications */}
                      {(graphFilter === "all" || graphFilter === "medicine") && (
                        <div className="border border-slate-200 bg-slate-50/50 rounded-2xl p-3.5">
                          <div className="flex items-center justify-between mb-2.5">
                            <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider flex items-center gap-1.5">
                              <Pill className="w-3.5 h-3.5" /> Pharmacotherapy
                            </span>
                            <span className="text-xs font-mono bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full font-bold">
                              {graphData.nodes.filter(n => n.node_type === "medicine").length}
                            </span>
                          </div>
                          <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                            {graphData.nodes.filter(n => n.node_type === "medicine").map(node => (
                              <div
                                key={node.id}
                                draggable
                                onDragStart={e => e.dataTransfer.setData("text/plain", `Rx: ${node.name}`)}
                                onClick={() => setSelectedNode(node)}
                                className={`p-2.5 rounded-xl border transition-all cursor-pointer ${
                                  selectedNode?.id === node.id
                                    ? "bg-emerald-50 border-emerald-400 shadow-xs"
                                    : "bg-white border-slate-200 hover:border-emerald-300"
                                }`}
                              >
                                <div className="flex items-center justify-between gap-1">
                                  <span className="text-xs font-bold text-slate-800">{node.name}</span>
                                  <span className="text-[10px] font-mono text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">
                                    {node.code}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Selected Node Inspector Drawer */}
                    {selectedNode && (
                      <div className="p-4 bg-white border border-slate-200 rounded-2xl shadow-xs">
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-bold px-2 py-0.5 rounded-full uppercase tracking-wider bg-indigo-50 text-indigo-700 border border-indigo-200">
                                {selectedNode.node_type}
                              </span>
                              <h5 className="text-sm font-bold text-slate-900">{selectedNode.name}</h5>
                            </div>
                            <p className="text-xs text-slate-500 font-mono mt-1">Code: {selectedNode.code} · ID: {selectedNode.id}</p>
                          </div>
                          <span className="text-[11px] text-slate-400 italic">Connected to Root Entity</span>
                        </div>
                        {/* Connected edges */}
                        <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-slate-100">
                          {graphData.edges
                            .filter(e => e.target_id === selectedNode.id || e.source_id === selectedNode.id)
                            .map((edge, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200"
                              >
                                <span className="font-bold text-indigo-600">{edge.relationship}</span>
                                {edge.metadata && Object.keys(edge.metadata).length > 0 && (
                                  <span className="text-slate-400 font-mono text-[10px]">
                                    ({Object.entries(edge.metadata).map(([k, v]) => `${k}: ${v}`).join(", ")})
                                  </span>
                                )}
                              </span>
                            ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
