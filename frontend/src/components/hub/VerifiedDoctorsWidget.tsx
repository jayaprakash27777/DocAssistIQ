"use client";

import React, { useState, useEffect } from "react";
import { DoctorProfile } from "@/types/social";
import { getStoredToken } from "@/lib/api";
import { getSharedRealtimeClient } from "@/lib/ws";

interface VerifiedDoctorsWidgetProps {
  doctors?: DoctorProfile[];
  onToggleFollow?: (doctorId: string) => void;
}

export function VerifiedDoctorsWidget({
  doctors: initialDoctors,
  onToggleFollow,
}: VerifiedDoctorsWidgetProps) {
  const [doctors, setDoctors] = useState<DoctorProfile[]>(initialDoctors || []);

  useEffect(() => {
    if (initialDoctors && initialDoctors.length > 0) {
      setDoctors(initialDoctors);
    } else {
      const token = getStoredToken();
      fetch("/api/v1/hub/explore", {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (Array.isArray(data)) {
            setDoctors(data);
          } else if (data && Array.isArray(data.doctors)) {
            setDoctors(data.doctors);
          }
        })
        .catch(() => {});
    }

    const token = getStoredToken();
    const ws = getSharedRealtimeClient(token);
    const unsub = ws.subscribeMessages((type, payload) => {
      if (type === "hub_doctor_followed" && payload?.doctor_id) {
        setDoctors((prev) =>
          prev.map((d) =>
            d.id === payload.doctor_id
              ? { ...d, followers_count: payload.followers_count }
              : d
          )
        );
      }
    });

    return () => {
      unsub();
    };
  }, [initialDoctors]);

  const handleToggle = async (docId: string) => {
    if (onToggleFollow) {
      onToggleFollow(docId);
      return;
    }
    // Optimistic toggle
    setDoctors((prev) =>
      prev.map((d) => (d.id === docId ? { ...d, is_following: !d.is_following } : d))
    );
    try {
      const token = getStoredToken();
      await fetch(`/api/v1/hub/doctors/${docId}/follow`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
    } catch {}
  };

  if (!doctors || doctors.length === 0) return null;


  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-xs">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-extrabold text-xs text-slate-900 uppercase tracking-wider flex items-center gap-2">
          <svg className="w-4 h-4 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <span>Verified Specialists</span>
        </h3>
        <span className="text-[10px] text-slate-400 font-bold">Global Network</span>
      </div>

      <div className="space-y-3">
        {doctors.slice(0, 5).map((doc) => (
          <div key={doc.id} className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-slate-700 to-slate-900 text-white font-black text-xs flex items-center justify-center flex-shrink-0">
                {doc.full_name ? doc.full_name[0].toUpperCase() : "D"}
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1">
                  <p className="text-xs font-bold text-slate-900 truncate">
                    {doc.full_name}
                  </p>
                  <span className="text-teal-600 text-[10px] flex-shrink-0" title="Verified Medical License">
                    ✓
                  </span>
                </div>
                <p className="text-[10px] text-slate-500 truncate">
                  {doc.specialization || "Clinical Specialist"}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => handleToggle(doc.id)}
              className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer flex-shrink-0 ${
                doc.is_following
                  ? "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  : "bg-teal-600 hover:bg-teal-700 text-white shadow-xs"
              }`}
            >
              {doc.is_following ? "Following" : "Follow"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default VerifiedDoctorsWidget;
