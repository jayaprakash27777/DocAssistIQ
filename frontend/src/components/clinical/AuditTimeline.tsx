/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useState } from "react";
import { Clock, ShieldCheck, UserCheck, CheckCircle, Activity } from "lucide-react";
import { getConsultationAudit, ConsultationAuditData } from "@/lib/api";

export default function AuditTimeline({ consultationId }: { consultationId: string }) {
  const [data, setData] = useState<ConsultationAuditData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadAudit() {
      const res = await getConsultationAudit(consultationId);
      if (res.ok && res.data) {
        setData(res.data);
      }
      setLoading(false);
    }
    loadAudit();
  }, [consultationId]);

  if (loading) return <div className="p-4 text-sm text-gray-500">Loading audit trail...</div>;
  if (!data) return <div className="p-4 text-sm text-red-500">Failed to load audit trail</div>;

  // Combine and sort events
  const events = [
    ...data.audits.map(a => ({
      type: "status_change",
      date: new Date(a.created_at),
      title: "Status Changed",
      desc: `Consultation transitioned from ${a.from_status || "None"} to ${a.to_status}`,
      icon: <Activity className="w-4 h-4 text-blue-400" />
    })),
    ...data.consents.map(c => ({
      type: "consent",
      date: new Date(c.created_at),
      title: `Consent ${c.status === "granted" ? "Granted" : "Revoked"}`,
      desc: `Actor: ${c.actor_name} (${c.actor_relationship}). Purpose: ${c.purpose}`,
      icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />
    }))
  ].sort((a, b) => b.date.getTime() - a.date.getTime()); // newest first

  return (
    <div className="glass-panel-4k gpu-accelerated border border-slate-200/90 rounded-3xl p-6 bg-white/85 backdrop-blur-2xl shadow-[0_12px_36px_rgba(0,0,0,0.05),inset_0_1px_0_rgba(255,255,255,0.9)] h-full ring-1 ring-black/5">
      <h2 className="text-lg font-black text-slate-900 tracking-tight flex items-center gap-2 mb-6 border-b border-slate-200/80 pb-3">
        <Clock className="w-5 h-5 text-teal-600" />
        Clinical Audit Trail
      </h2>

      {events.length > 0 ? (
        <div className="relative border-l-2 border-slate-200 ml-3 space-y-6">
          {events.map((event, idx) => (
            <div key={idx} className="relative pl-6">
              <div className="absolute -left-[9px] top-1 w-4 h-4 bg-white rounded-full flex items-center justify-center ring-4 ring-teal-50 border-2 border-teal-500 shadow-sm">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-600" />
              </div>
              <div className="bg-white/70 hover:bg-white border border-slate-200/80 hover:border-teal-300 rounded-2xl p-4 transition-all shadow-sm">
                <div className="flex justify-between items-start mb-1 gap-2">
                  <span className="font-bold text-sm text-slate-800 flex items-center gap-2">
                    {event.icon}
                    {event.title}
                  </span>
                  <span className="text-[11px] font-mono text-slate-400 font-semibold shrink-0">
                    {event.date.toLocaleString()}
                  </span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed m-0 font-medium">
                  {event.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-slate-400 text-center py-6 font-medium">No audit records found.</p>
      )}
    </div>
  );
}
