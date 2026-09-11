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
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5 backdrop-blur-xl h-full">
      <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-6 border-b border-gray-700 pb-3">
        <Clock className="w-5 h-5 text-purple-400" />
        Clinical Audit Trail
      </h2>

      {events.length > 0 ? (
        <div className="relative border-l border-gray-700 ml-3 space-y-6">
          {events.map((event, idx) => (
            <div key={idx} className="relative pl-6">
              <div className="absolute -left-2.5 top-1 w-5 h-5 bg-gray-900 rounded-full flex items-center justify-center ring-4 ring-gray-900 border border-gray-700">
                {event.icon}
              </div>
              <div className="bg-gray-900/50 border border-gray-700/50 rounded-lg p-3">
                <div className="flex justify-between items-start mb-1">
                  <span className="font-medium text-sm text-gray-200">
                    {event.title}
                  </span>
                  <span className="text-[10px] text-gray-500">
                    {event.date.toLocaleString()}
                  </span>
                </div>
                <p className="text-xs text-gray-400">
                  {event.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-gray-500 text-center py-6">No audit records found.</p>
      )}
    </div>
  );
}
