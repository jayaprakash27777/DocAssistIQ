/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, UserPlus, ShieldAlert, HeartPulse, Pill, Activity, AlertTriangle } from "lucide-react";
import { createPatientProfile } from "@/lib/api";

export default function NewPatientProfile() {
  const router = useRouter();
  const [patientRef, setPatientRef] = useState("");
  const [ageGroup, setAgeGroup] = useState("");
  const [sex, setSex] = useState("");
  const [allergiesText, setAllergiesText] = useState("");
  const [conditionsText, setConditionsText] = useState("");
  const [medicationsText, setMedicationsText] = useState("");
  const [bloodType, setBloodType] = useState("");
  const [codeStatus, setCodeStatus] = useState("");

  // Optional baseline vitals
  const [bp, setBp] = useState("");
  const [hr, setHr] = useState("");
  const [spo2, setSpo2] = useState("");
  const [temp, setTemp] = useState("");
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const allergiesList = allergiesText
        .split(",")
        .map(c => c.trim())
        .filter(c => c.length > 0);
      const chronicList = conditionsText
        .split(",")
        .map(c => c.trim())
        .filter(c => c.length > 0);
      const medicationsList = medicationsText
        .split(",")
        .map(c => c.trim())
        .filter(c => c.length > 0);

      const vitalsObj: Record<string, string> = {};
      if (bp.trim()) vitalsObj.blood_pressure = bp.trim();
      if (hr.trim()) vitalsObj.heart_rate = hr.trim();
      if (spo2.trim()) vitalsObj.spo2 = spo2.trim();
      if (temp.trim()) vitalsObj.temperature = temp.trim();

      const baseline: Record<string, any> = {
        chronic_conditions: chronicList,
        allergies: allergiesList,
        current_medications: medicationsList,
      };
      if (bloodType) baseline.blood_type = bloodType;
      if (codeStatus) baseline.code_status = codeStatus;
      if (Object.keys(vitalsObj).length > 0) baseline.vitals = vitalsObj;

      const response = await createPatientProfile({
        patient_ref: patientRef.trim(),
        age_group: ageGroup || null,
        biological_sex: sex || null,
        baseline_conditions: baseline,
      });

      if (response.ok && response.data) {
        router.push(`/patients/${response.data.id}`);
      } else {
        setError(!response.ok ? response.error.message : "Failed to create patient record");
      }
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 py-6 px-4">
      <header className="flex flex-col gap-4">
        <Link
          href="/patients"
          className="flex items-center gap-2 text-sm text-slate-500 hover:text-teal-700 transition-colors w-fit font-semibold"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Patient Registry
        </Link>
        <div>
          <h1 className="text-3xl font-black tracking-tight text-slate-900 flex items-center gap-3 font-heading">
            <div className="w-10 h-10 rounded-2xl bg-teal-50 text-teal-600 border border-teal-200/60 flex items-center justify-center shrink-0 shadow-sm">
              <UserPlus className="w-5 h-5" />
            </div>
            Create Clinical Patient Record
          </h1>
          <p className="text-slate-500 mt-1.5 text-sm font-medium">
            Register a new longitudinal patient profile with real baseline conditions, allergies, and vitals.
          </p>
        </div>
      </header>

      <div className="bg-sky-50/80 border border-sky-200/70 rounded-2xl p-4 flex gap-3.5 shadow-sm">
        <ShieldAlert className="w-5 h-5 text-sky-600 shrink-0 mt-0.5" />
        <p className="text-xs text-sky-900 leading-relaxed m-0 font-medium">
          <strong className="font-bold">Clinical Safety Protocol:</strong> Do not enter direct PII (e.g. Full Name, SSN, Home Address). Use hospital/EMR reference identifiers (e.g. MRN-5049, PT-8921).
        </p>
      </div>

      <form onSubmit={handleSubmit} className="glass-panel-4k gpu-accelerated border border-slate-200/90 rounded-3xl p-6 sm:p-8 space-y-6 bg-white/85 backdrop-blur-2xl shadow-[0_12px_36px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.9)] ring-1 ring-black/5">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-2xl text-sm font-medium">
            {error}
          </div>
        )}

        <div className="space-y-6">
          {/* Identity & Demographics */}
          <div>
            <h3 className="text-xs font-black uppercase tracking-wider text-slate-900 mb-3 pb-2 border-b border-slate-100 flex items-center gap-2">
              <Activity className="w-4 h-4 text-teal-600" />
              <span>Demographics &amp; Hospital Identifier</span>
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                  Patient Reference ID / MRN <span className="text-red-500">*</span>
                </label>
                <input
                  required
                  type="text"
                  value={patientRef}
                  onChange={(e) => setPatientRef(e.target.value)}
                  placeholder="e.g., PT-8492 or MRN-9921"
                  className="w-full bg-white/90 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all shadow-sm font-mono text-sm"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                    Age Group
                  </label>
                  <select
                    value={ageGroup}
                    onChange={(e) => setAgeGroup(e.target.value)}
                    className="w-full bg-white/90 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all shadow-sm text-sm cursor-pointer"
                  >
                    <option value="">Select range...</option>
                    <option value="0-18">0-18 (Pediatric)</option>
                    <option value="19-30">19-30</option>
                    <option value="31-50">31-50</option>
                    <option value="51-70">51-70</option>
                    <option value="71+">71+ (Geriatric)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                    Biological Sex
                  </label>
                  <select
                    value={sex}
                    onChange={(e) => setSex(e.target.value)}
                    className="w-full bg-white/90 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all shadow-sm text-sm cursor-pointer"
                  >
                    <option value="">Select sex...</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other / Unspecified</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                    Blood Group (Optional)
                  </label>
                  <select
                    value={bloodType}
                    onChange={(e) => setBloodType(e.target.value)}
                    className="w-full bg-white/90 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all shadow-sm text-sm cursor-pointer"
                  >
                    <option value="">Select blood type...</option>
                    <option value="O+">O+ (Rh Positive)</option>
                    <option value="O-">O- (Rh Negative)</option>
                    <option value="A+">A+ (Rh Positive)</option>
                    <option value="A-">A- (Rh Negative)</option>
                    <option value="B+">B+ (Rh Positive)</option>
                    <option value="B-">B- (Rh Negative)</option>
                    <option value="AB+">AB+ (Rh Positive)</option>
                    <option value="AB-">AB- (Rh Negative)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                    Code Status / Directives (Optional)
                  </label>
                  <select
                    value={codeStatus}
                    onChange={(e) => setCodeStatus(e.target.value)}
                    className="w-full bg-white/90 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all shadow-sm text-sm cursor-pointer"
                  >
                    <option value="">Select code status...</option>
                    <option value="Full Code">Full Code (Resuscitative Intent Active)</option>
                    <option value="DNR">DNR (Do Not Resuscitate)</option>
                    <option value="DNI">DNI (Do Not Intubate)</option>
                    <option value="Comfort Measures Only">Comfort Measures Only</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Clinical Conditions & Allergies */}
          <div>
            <h3 className="text-xs font-black uppercase tracking-wider text-slate-900 mb-3 pb-2 border-b border-slate-100 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>Safety Alerts, Allergies &amp; Chronic Conditions</span>
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                  Documented Allergies &amp; Drug Reactions
                </label>
                <input
                  type="text"
                  value={allergiesText}
                  onChange={(e) => setAllergiesText(e.target.value)}
                  placeholder="e.g., Penicillin, Aspirin, Sulfa drugs"
                  className="w-full bg-white/90 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all shadow-sm text-sm"
                />
                <p className="text-[11px] text-slate-400 mt-1">Comma-separated list of known allergies. Leave blank if none (NKDA).</p>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                  Active Chronic Conditions
                </label>
                <input
                  type="text"
                  value={conditionsText}
                  onChange={(e) => setConditionsText(e.target.value)}
                  placeholder="e.g., Type 2 Diabetes, Essential Hypertension, Asthma"
                  className="w-full bg-white/90 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all shadow-sm text-sm"
                />
                <p className="text-[11px] text-slate-400 mt-1">Comma-separated list of diagnosed conditions.</p>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                  Active Maintenance Medications
                </label>
                <input
                  type="text"
                  value={medicationsText}
                  onChange={(e) => setMedicationsText(e.target.value)}
                  placeholder="e.g., Metformin 500mg daily, Lisinopril 10mg daily"
                  className="w-full bg-white/90 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all shadow-sm text-sm"
                />
                <p className="text-[11px] text-slate-400 mt-1">Comma-separated list of regular pharmacotherapy.</p>
              </div>
            </div>
          </div>

          {/* Optional Baseline Vitals */}
          <div>
            <h3 className="text-xs font-black uppercase tracking-wider text-slate-900 mb-3 pb-2 border-b border-slate-100 flex items-center gap-2">
              <HeartPulse className="w-4 h-4 text-rose-600" />
              <span>Initial Baseline Vitals (Optional)</span>
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div>
                <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                  Blood Pressure
                </label>
                <input
                  type="text"
                  value={bp}
                  onChange={(e) => setBp(e.target.value)}
                  placeholder="e.g. 120/80"
                  className="w-full bg-white/90 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 text-xs"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                  Heart Rate (bpm)
                </label>
                <input
                  type="text"
                  value={hr}
                  onChange={(e) => setHr(e.target.value)}
                  placeholder="e.g. 72"
                  className="w-full bg-white/90 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 text-xs"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                  SpO2 (%)
                </label>
                <input
                  type="text"
                  value={spo2}
                  onChange={(e) => setSpo2(e.target.value)}
                  placeholder="e.g. 98"
                  className="w-full bg-white/90 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 text-xs"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                  Temperature (°C)
                </label>
                <input
                  type="text"
                  value={temp}
                  onChange={(e) => setTemp(e.target.value)}
                  placeholder="e.g. 37.0"
                  className="w-full bg-white/90 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 text-xs"
                />
              </div>
            </div>
            <p className="text-[11px] text-slate-400 mt-1.5">Leave blank if triage has not been completed.</p>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 flex justify-end items-center gap-3">
          <Link
            href="/patients"
            className="px-4 py-2 text-slate-500 hover:text-slate-800 transition-colors font-semibold text-sm"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={loading || !patientRef.trim()}
            className="bg-gradient-to-r from-teal-500 to-indigo-600 hover:brightness-110 text-white px-6 py-2.5 rounded-xl transition-all font-bold text-sm shadow-md shadow-teal-500/20 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {loading ? "Creating..." : "Save Patient Profile"}
          </button>
        </div>
      </form>
    </div>
  );
}
