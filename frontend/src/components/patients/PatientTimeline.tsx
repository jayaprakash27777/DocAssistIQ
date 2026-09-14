/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useEffect, useState } from "react";
import { getPatientTimeline, TimelineEvent } from "@/lib/api";
import { Activity, Stethoscope, FileCheck, ShieldCheck, ChevronRight, Clock } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

interface PatientTimelineProps {
  patientId: string;
}

const TYPE_CONFIG: Record<string, { icon: any; colorClass: string; bgClass: string }> = {
  consultation: {
    icon: Stethoscope,
    colorClass: "text-[var(--color-info-600)]",
    bgClass: "bg-[var(--color-info-50)] border-[var(--color-info-200)]",
  },
  diagnosis: {
    icon: Activity,
    colorClass: "text-[var(--color-warning-600)]",
    bgClass: "bg-[var(--color-warning-50)] border-[var(--color-warning-200)]",
  },
  consent: {
    icon: ShieldCheck,
    colorClass: "text-[var(--color-success-600)]",
    bgClass: "bg-[var(--color-success-50)] border-[var(--color-success-200)]",
  },
  default: {
    icon: FileCheck,
    colorClass: "text-[var(--text-secondary)]",
    bgClass: "bg-[var(--surface-sunken)] border-[var(--border-default)]",
  }
};

export default function PatientTimeline({ patientId }: PatientTimelineProps) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>("");

  useEffect(() => {
    async function loadTimeline() {
      setLoading(true);
      try {
        const response = await getPatientTimeline(patientId, 50, 0, filterType || undefined);
        if (response.ok && response.data) {
          setEvents(response.data.events);
        } else {
          setError(!response.ok ? response.error.message : "Failed to load timeline");
        }
      } catch (err: any) {
        setError(err.message || "An unexpected error occurred");
      } finally {
        setLoading(false);
      }
    }
    loadTimeline();
  }, [patientId, filterType]);

  if (error) {
    return (
      <div className="bg-red-50 text-red-600 p-4 rounded-lg">
        <p className="font-semibold">Error Loading Timeline</p>
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-[var(--border-default)] overflow-hidden relative">
      <div className="p-5 border-b border-[var(--border-default)] flex items-center justify-between bg-[var(--surface-sunken)] relative z-10">
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-[var(--color-primary-500)]" />
          <h2 className="font-bold font-heading text-[var(--text-primary)]">Chronological Timeline</h2>
        </div>
        <div className="flex gap-2">
          <select 
            className="text-sm border border-[var(--border-default)] rounded-lg bg-white px-3 py-1.5 outline-none text-[var(--text-primary)] shadow-sm font-medium focus:ring-2 focus:ring-[var(--color-primary-500)]"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="">All Events</option>
            <option value="consultation">Consultations</option>
            <option value="diagnosis">Diagnoses</option>
            <option value="consent">Consents</option>
          </select>
        </div>
      </div>

      <div className="p-8 pb-12 relative">
        {loading ? (
          <div className="space-y-6 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-[var(--border-strong)] before:to-transparent">
             {[1, 2, 3].map(i => (
                <div key={i} className="animate-pulse relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                  <div className="flex items-center justify-center w-12 h-12 rounded-full border-4 border-white bg-[var(--surface-sunken)] shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-sm z-10"></div>
                  <div className="w-[calc(100%-4rem)] md:w-[calc(50%-3rem)] bg-[var(--surface-sunken)] p-5 rounded-2xl shadow-sm h-32 border border-[var(--border-default)]"></div>
                </div>
             ))}
          </div>
        ) : events.length === 0 ? (
          <div className="text-center py-16 text-[var(--text-secondary)]">
            <Clock className="w-16 h-16 text-[var(--text-tertiary)] mx-auto mb-4 opacity-50" />
            <p className="font-medium text-lg">No historical events found for this patient.</p>
          </div>
        ) : (
          <div className="space-y-10 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-[var(--border-strong)] before:to-transparent">
            {events.map((event, index) => {
              const config = TYPE_CONFIG[event.type] || TYPE_CONFIG.default;
              const Icon = config.icon;
              
              return (
                <motion.div 
                  key={event.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1, duration: 0.5 }}
                  className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group"
                >
                  <div className={`flex items-center justify-center w-12 h-12 rounded-full border-4 border-white ${config.bgClass} shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-md z-10 transition-transform group-hover:scale-110`}>
                    <Icon className={`w-5 h-5 ${config.colorClass}`} />
                  </div>
                  
                  <div className="w-[calc(100%-4rem)] md:w-[calc(50%-3rem)] bg-white p-6 rounded-2xl border border-[var(--border-default)] shadow-sm hover:shadow-lg transition-all hover:border-[var(--border-strong)]">
                    <div className="flex items-center justify-between mb-2">
                      <time className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-wider">
                        {event.timestamp ? new Date(event.timestamp).toLocaleString() : 'Unknown Time'}
                      </time>
                      <span className={`text-[10px] uppercase font-bold px-2.5 py-1 rounded-full border ${config.bgClass} ${config.colorClass}`}>
                        {event.type}
                      </span>
                    </div>
                    
                    <h3 className="text-base font-bold text-[var(--text-primary)] mt-2">{event.title}</h3>
                    <p className="text-sm text-[var(--text-secondary)] mt-2 leading-relaxed font-medium">
                      {event.description}
                    </p>
                    
                    {event.status && (
                      <div className="mt-4">
                        <span className="text-[10px] font-mono bg-[var(--surface-sunken)] text-[var(--text-secondary)] px-2 py-1 rounded border border-[var(--border-default)] font-bold">
                          STATUS: {event.status.toUpperCase()}
                        </span>
                      </div>
                    )}

                    {event.consultation_id && event.type !== 'consultation' && (
                       <div className="mt-5 pt-4 border-t border-[var(--border-default)] flex justify-end">
                         <Link href={`/consultations/${event.consultation_id}`} className="text-xs text-[var(--color-primary-600)] font-bold flex items-center hover:text-[var(--color-primary-700)] transition-colors">
                           View Related Consultation <ChevronRight className="w-4 h-4 ml-1" />
                         </Link>
                       </div>
                    )}
                    {event.type === 'consultation' && (
                       <div className="mt-5 pt-4 border-t border-[var(--border-default)] flex justify-end">
                         <Link href={`/consultations/${event.consultation_id}`} className="text-xs text-[var(--color-primary-600)] font-bold flex items-center hover:text-[var(--color-primary-700)] transition-colors">
                           Open Consultation <ChevronRight className="w-4 h-4 ml-1" />
                         </Link>
                       </div>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
