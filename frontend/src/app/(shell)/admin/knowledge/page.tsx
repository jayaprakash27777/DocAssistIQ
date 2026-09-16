"use client";

import { useCallback, useEffect, useState, useRef } from "react";
import { useToast } from "@/components/shell/ToastProvider";
import { Skeleton } from "@/components/shell/LoadingSkeleton";
import {
  listPendingKnowledge,
  reviewKnowledge,
  inspectProvenance,
  syncEmbedding,
  type KnowledgeEntityResponse,
  type ProvenanceItemResponse,
} from "@/lib/api";
import { ClipboardList, CheckCircle2, ShieldAlert, Cpu, Sparkles, Network, X } from "lucide-react";
import { motion } from "framer-motion";

type EntityType = "disease" | "symptom" | "investigation" | "medicine";

export default function KnowledgeReviewPage() {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<EntityType>("disease");
  const [entities, setEntities] = useState<KnowledgeEntityResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const [inspectingEntity, setInspectingEntity] = useState<KnowledgeEntityResponse | null>(null);
  const [provenanceData, setProvenanceData] = useState<ProvenanceItemResponse[]>([]);
  const [provenanceLoading, setProvenanceLoading] = useState(false);
  
  const isFetchingRef = useRef(false);

  const fetchEntities = useCallback(async (isInitial = false) => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;
    if (isInitial) setLoading(true);

    const r = await listPendingKnowledge(activeTab, 1, 50);
    
    if (isInitial) setLoading(false);
    isFetchingRef.current = false;

    if (!r.ok) {
      if (isInitial) toast.error(r.error.message || `Failed to load pending ${activeTab}s`);
      return;
    }
    setEntities(r.data.items);
    setTotal(r.data.total);
    setLastUpdated(new Date());
  }, [activeTab, toast]);

  useEffect(() => {
    fetchEntities(true);
    const interval = setInterval(() => fetchEntities(false), 3000);
    return () => clearInterval(interval);
  }, [fetchEntities]);

  async function handleInspect(entity: KnowledgeEntityResponse) {
    setInspectingEntity(entity);
    setProvenanceLoading(true);
    const r = await inspectProvenance(activeTab, entity.id);
    setProvenanceLoading(false);
    
    if (r.ok) {
      setProvenanceData(r.data);
    } else {
      toast.error(r.error.message || "Failed to load provenance");
      setProvenanceData([]);
    }
  }

  async function handleReview(status: "APPROVED" | "REJECTED" | "SUPERSEDED") {
    if (!inspectingEntity) return;
    
    const r = await reviewKnowledge(activeTab, inspectingEntity.id, status);
    if (!r.ok) {
      toast.error(r.error.message || `Failed to mark as ${status}`);
      return;
    }
    
    toast.success(`${inspectingEntity.name} marked as ${status}`);
    setInspectingEntity(null);
    fetchEntities(false);
  }

  async function handleSyncEmbedding() {
    if (!inspectingEntity) return;
    
    toast.success(`Syncing embedding for ${inspectingEntity.name}...`);
    const r = await syncEmbedding(activeTab, inspectingEntity.id);
    
    if (r.ok) {
      toast.success(`Embedding generated (${r.data.dimensions}d, model: ${r.data.model})`);
    } else {
      toast.error(r.error.message || "Failed to generate embedding");
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 relative overflow-hidden p-8 pt-10">
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-300/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '8s' }}></div>
      <div className="absolute inset-0 z-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>

      <div className="max-w-7xl mx-auto space-y-8 relative z-10">
        
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <div className="relative p-2.5 bg-blue-500/10 rounded-xl border border-blue-500/20 shadow-sm overflow-hidden">
                <div className="absolute inset-0 bg-blue-400/20 animate-pulse"></div>
                <ClipboardList size={28} className="text-blue-600 relative z-10" />
              </div>
              <h1 className="text-4xl font-bold text-slate-900 tracking-tight font-heading">
                Knowledge Review
              </h1>
            </div>
            <p className="text-slate-500 text-lg max-w-2xl font-medium">
              Safely review and publish clinical knowledge to production.
            </p>
          </div>
          
          <div className="flex items-center gap-2 text-sm font-medium text-blue-700 bg-blue-50 px-4 py-2 rounded-full border border-blue-200 shadow-sm backdrop-blur-md">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
            </span>
            Live Data Feed
            <span className="text-blue-600/60 ml-2 text-xs font-mono">
              Updated: {lastUpdated.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' })}
            </span>
          </div>
        </header>

        <section className="bg-white/60 backdrop-blur-xl border border-white rounded-3xl p-6 shadow-xl shadow-slate-200/50 flex flex-col h-full">
          
          <div className="flex gap-2 p-1.5 bg-slate-100 rounded-2xl mb-6 w-fit">
            {(["disease", "symptom", "investigation", "medicine"] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-2 rounded-xl text-sm font-bold tracking-wide capitalize transition-all ${
                  activeTab === tab 
                  ? "bg-white text-blue-700 shadow-sm border border-slate-200/50" 
                  : "text-slate-500 hover:text-slate-700 hover:bg-slate-200/50"
                }`}
              >
                {tab}s
              </button>
            ))}
          </div>

          {loading ? (
            <div className="space-y-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex gap-4 p-4 border border-slate-100 rounded-2xl bg-slate-50/50">
                  <Skeleton height="2rem" width="10%" />
                  <Skeleton height="2rem" width="30%" />
                  <Skeleton height="2rem" width="15%" />
                </div>
              ))}
            </div>
          ) : (
            <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50/80 border-b border-slate-100 text-slate-500 font-medium uppercase tracking-wider text-xs">
                  <tr>
                    <th className="px-6 py-4">Code</th>
                    <th className="px-6 py-4">Name</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4">AI Generated</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {entities.map((entity, i) => (
                    <motion.tr 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      key={entity.id} 
                      className="hover:bg-slate-50/50 transition-colors group"
                    >
                      <td className="px-6 py-4 font-mono text-xs font-bold text-slate-500">{entity.code}</td>
                      <td className="px-6 py-4 font-medium text-slate-800">{entity.name}</td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-amber-50 text-amber-700 border border-amber-200 rounded-md text-[10px] font-bold uppercase tracking-wider">
                          <ShieldAlert size={12} />
                          {entity.status}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {entity.is_ai_generated ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-md text-[10px] font-bold uppercase tracking-wider">
                            <Sparkles size={12} className="text-indigo-500" />
                            AI Extracted
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-slate-100 text-slate-600 border border-slate-200 rounded-md text-[10px] font-bold uppercase tracking-wider">
                            <CheckCircle2 size={12} />
                            Manual
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={() => handleInspect(entity)}
                            className="px-3 py-1.5 bg-blue-50 text-blue-600 hover:bg-blue-500 hover:text-white border border-blue-200 hover:border-blue-500 rounded-lg text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-1.5"
                          >
                            <Network size={14} />
                            Inspect & Review
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                  {entities.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-6 py-16 text-center">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 mb-4">
                          <CheckCircle2 size={32} className="text-slate-400" />
                        </div>
                        <h3 className="text-lg font-bold text-slate-800 mb-1">No pending reviews</h3>
                        <p className="text-slate-500">All {activeTab}s have been reviewed and published.</p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>

      {inspectingEntity && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-3xl p-8 max-w-3xl w-full shadow-2xl border border-slate-100 relative max-h-[90vh] flex flex-col"
          >
            <button onClick={() => setInspectingEntity(null)} className="absolute top-6 right-6 text-slate-400 hover:text-slate-600 transition-colors">
              <X size={24} />
            </button>
            
            <div className="mb-6">
              <h3 className="text-2xl font-bold text-slate-800 mb-2 font-heading">
                Review: {inspectingEntity.name}
              </h3>
              <div className="flex gap-2 items-center">
                <span className="px-2 py-1 bg-slate-100 text-slate-600 rounded font-mono text-xs font-bold">{inspectingEntity.code}</span>
                <span className="text-sm font-medium text-slate-500 capitalize">{activeTab}</span>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto min-h-0 bg-slate-50 rounded-2xl p-6 border border-slate-100 mb-6">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Source Provenance</h4>
              
              {provenanceLoading ? (
                <div className="space-y-4">
                  <Skeleton height="6rem" width="100%" />
                  <Skeleton height="6rem" width="100%" />
                </div>
              ) : provenanceData.length > 0 ? (
                <div className="space-y-4">
                  {provenanceData.map((prov) => (
                    <div key={prov.id} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <div className="flex justify-between items-start mb-3">
                        <div className="font-medium text-slate-800">{prov.source_name} <span className="font-mono text-xs text-slate-400">({prov.source_code})</span></div>
                        <div className="flex gap-2">
                          {prov.evidence_grade && <span className="px-2 py-0.5 bg-blue-50 text-blue-700 border border-blue-200 rounded text-[10px] font-bold uppercase tracking-wider">Level {prov.evidence_grade}</span>}
                          {prov.is_ai_extracted && <span className="px-2 py-0.5 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded text-[10px] font-bold uppercase tracking-wider">AI Extracted</span>}
                        </div>
                      </div>
                      <p className="text-sm text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">{prov.claim}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-10">
                  <p className="text-slate-400 font-medium">No specific evidence claims attached to this entity.</p>
                </div>
              )}
            </div>

            <div className="flex justify-between items-center pt-4 border-t border-slate-100">
              <button 
                onClick={handleSyncEmbedding}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-medium text-sm transition-colors flex items-center gap-2"
              >
                <Cpu size={16} /> Generate Embedding
              </button>
              
              <div className="flex gap-3">
                <button onClick={() => handleReview("REJECTED")} className="px-4 py-2 bg-red-50 hover:bg-red-500 hover:text-white text-red-600 border border-red-200 hover:border-red-500 rounded-xl font-medium text-sm transition-all shadow-sm">
                  Reject
                </button>
                <button onClick={() => handleReview("SUPERSEDED")} className="px-4 py-2 bg-amber-50 hover:bg-amber-500 hover:text-white text-amber-700 border border-amber-200 hover:border-amber-500 rounded-xl font-medium text-sm transition-all shadow-sm">
                  Mark Superseded
                </button>
                <button onClick={() => handleReview("APPROVED")} className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-medium text-sm transition-all shadow-lg shadow-emerald-500/20">
                  Approve for Production
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
