"use client";

import React, { useState, useEffect } from "react";
import { SocialNavRail } from "@/components/hub/SocialNavRail";
import { TrendingHashtagsWidget } from "@/components/hub/TrendingHashtagsWidget";
import { EmergencyRadarWidget } from "@/components/hub/EmergencyRadarWidget";
import { SocialPostCard } from "@/components/hub/SocialPostCard";
import { SocialCaseComposer } from "@/components/hub/SocialCaseComposer";
import { DoctorPost, DoctorProfile } from "@/types/social";
import { getStoredToken } from "@/lib/api";
import { 
  Building2, 
  MapPin, 
  FileText, 
  Sparkles,
  ShieldCheck,
  Globe,
  Award
} from "lucide-react";

import { getSharedRealtimeClient } from "@/lib/ws";

export default function DoctorProfilePage() {
  const [profile, setProfile] = useState<DoctorProfile | null>(null);
  const [posts, setPosts] = useState<DoctorPost[]>([]);
  const [suggestedPosts, setSuggestedPosts] = useState<DoctorPost[]>([]);
  const [activeTab, setActiveTab] = useState<"cases" | "suggestions">("cases");
  const [loading, setLoading] = useState(true);
  const [isComposerOpen, setIsComposerOpen] = useState(false);

  useEffect(() => {
    fetchProfileAndPosts();
  }, []);

  const fetchProfileAndPosts = async () => {
    setLoading(true);
    try {
      const token = getStoredToken();
      const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

      // 1. Fetch real verified profile for logged-in physician
      const pRes = await fetch("/api/v1/hub/profile", { headers });
      let currentDocId = "";
      if (pRes.ok) {
        const pData: DoctorProfile = await pRes.json();
        setProfile(pData);
        currentDocId = pData.id;
      }

      // 2. Fetch posts
      const feedRes = await fetch("/api/v1/hub/posts?limit=50", { headers });
      if (feedRes.ok) {
        const allPosts: DoctorPost[] = await feedRes.json();
        const rawList = Array.isArray(allPosts) ? allPosts : [];
        if (currentDocId) {
          const myCases = rawList.filter((p) => p.author_id === currentDocId);
          setPosts(myCases.length > 0 ? myCases : rawList.slice(0, 5));
          const withMySuggestions = rawList.filter((p) =>
            (p.treatment_suggestions || []).some((s) => s.author_id === currentDocId)
          );
          setSuggestedPosts(withMySuggestions);
        } else {
          setPosts(rawList);
        }
      }
    } catch (err) {
      console.error("Failed to load doctor profile:", err);
    } finally {
      setLoading(false);
    }
  };

  // Real-time WebSocket updates for doctor profile
  useEffect(() => {
    const token = getStoredToken();
    if (!token) return;
    const ws = getSharedRealtimeClient(token);

    const unsub = ws.subscribeMessages((type, payload) => {
      if (type === "hub_post_liked" && payload?.post_id) {
        setPosts((prev) =>
          prev.map((p) => (p.id === payload.post_id ? { ...p, likes_count: payload.likes_count } : p))
        );
      } else if (type === "hub_post_outcome_updated" && payload?.post_id) {
        setPosts((prev) =>
          prev.map((p) =>
            p.id === payload.post_id
              ? {
                  ...p,
                  patient_outcome: payload.patient_outcome,
                  is_solved: payload.is_solved,
                  outcome_reported_at: payload.outcome_reported_at,
                  case_status: payload.is_solved ? "solved" : p.case_status,
                }
              : p
          )
        );
      } else if (type === "hub_suggestion_endorsed" && payload?.suggestion_id) {
        setPosts((prev) =>
          prev.map((post) => ({
            ...post,
            treatment_suggestions: (post.treatment_suggestions || []).map((sugg) =>
              sugg.id === payload.suggestion_id
                ? { ...sugg, endorsements_count: payload.endorsements_count }
                : sugg
            ),
          }))
        );
        // Live update peer endorsement metric
        setProfile((prev) =>
          prev ? { ...prev, endorsements_count: (prev.endorsements_count || 0) + 1 } : prev
        );
      }
    });

    return () => {
      unsub();
    };
  }, []);

  return (
    <div className="min-h-full bg-slate-50 text-slate-900 pb-28">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* ── 3-Column Social Network Grid ── */}
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr_310px] gap-6 items-start">
          {/* ══════════════ LEFT SIDEBAR ══════════════ */}
          <SocialNavRail
            onOpenCompose={() => setIsComposerOpen(true)}
            urgentCasesCount={posts.filter((p) => p.is_emergency || p.is_urgent_consult).length}
          />

          {/* ══════════════ CENTER PROFILE ══════════════ */}
          <main className="min-w-0 space-y-4">
            {/* Header Banner & Profile Card */}
            <div className="bg-white rounded-2xl border border-slate-200/90 overflow-hidden shadow-xs">
              <div className="h-36 bg-gradient-to-r from-teal-700 via-teal-600 to-emerald-600 relative p-4 flex justify-end items-start">
                <span className="px-3 py-1 bg-white/20 backdrop-blur-xs text-white rounded-full text-xs font-bold flex items-center gap-1.5 shadow-2xs">
                  <Globe className="w-3.5 h-3.5 text-teal-100" />
                  Global Clinical Network
                </span>
              </div>

              <div className="px-6 pb-6 pt-0 relative">
                <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 -mt-12 mb-4">
                  <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-teal-600 to-emerald-600 border-4 border-white flex items-center justify-center text-2xl font-black text-white shadow-md">
                    {(() => {
                      const dName = profile?.name || profile?.full_name || "Doctor";
                      return (
                        dName
                          .replace(/^Dr\.\s*/i, "")
                          .split(" ")
                          .filter(Boolean)
                          .slice(0, 2)
                          .map((n: string) => n[0].toUpperCase())
                          .join("") || "MD"
                      );
                    })()}
                  </div>

                  <button
                    onClick={() => setIsComposerOpen(true)}
                    className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white font-black text-xs rounded-xl transition shadow-xs cursor-pointer"
                  >
                    + Share Clinical Case
                  </button>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h1 className="text-xl font-black text-slate-900 tracking-tight">
                      {profile?.name || profile?.full_name || "Verified Physician"}
                    </h1>
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-teal-50 text-teal-800 border border-teal-200">
                      <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                      Verified Doctor
                    </span>
                  </div>

                  <p className="text-xs font-bold text-teal-700">{profile?.specialty || "Clinical Specialist"}</p>

                  <p className="text-xs text-slate-600 leading-relaxed max-w-2xl pt-1">
                    {profile?.bio || "Board-certified specialist practicing evidence-based clinical medicine."}
                  </p>

                  <div className="flex flex-wrap items-center gap-y-1.5 gap-x-4 text-xs text-slate-500 pt-2 font-medium">
                    <div className="flex items-center gap-1 text-emerald-700 font-mono font-bold">
                      <Award className="w-3.5 h-3.5" />
                      <span>{profile?.license_verification || "Medical License Verified"}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Building2 className="w-3.5 h-3.5 text-slate-400" />
                      <span>{profile?.institution || "Academic Medical Center"}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      <span>{profile?.country || "Global"}</span>
                    </div>
                  </div>
                </div>

                {/* Clinical Impact Metrics — Dynamic from Real Database */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5 pt-4 border-t border-slate-100">
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
                    <div className="text-[11px] font-bold text-slate-500">Cases Published</div>
                    <div className="text-lg font-black text-slate-900 mt-0.5">
                      {profile?.cases_count ?? posts.length}
                    </div>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
                    <div className="text-[11px] font-bold text-slate-500">Treatment Regimens</div>
                    <div className="text-lg font-black text-teal-700 mt-0.5">
                      {profile?.suggestions_count ?? suggestedPosts.length}
                    </div>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
                    <div className="text-[11px] font-bold text-slate-500">Peer Endorsements</div>
                    <div className="text-lg font-black text-indigo-700 mt-0.5">
                      {profile?.endorsements_count ?? 0}
                    </div>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
                    <div className="text-[11px] font-bold text-slate-500">Clinical Trust Score</div>
                    <div className="text-lg font-black text-emerald-700 mt-0.5">
                      {profile?.reputation_score ?? 95}%
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Profile Tab Navigation */}
            <div className="bg-white rounded-2xl border border-slate-200/90 p-2 shadow-xs flex items-center gap-2">
              <button
                onClick={() => setActiveTab("cases")}
                className={`py-2 px-4 rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer ${
                  activeTab === "cases"
                    ? "bg-teal-600 text-white shadow-xs"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                Published Cases ({posts.length})
              </button>
              <button
                onClick={() => setActiveTab("suggestions")}
                className={`py-2 px-4 rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer ${
                  activeTab === "suggestions"
                    ? "bg-teal-600 text-white shadow-xs"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                Adopted Regimens ({suggestedPosts.length})
              </button>
            </div>

            {/* Posts Feed */}
            {(() => {
              const activePosts = activeTab === "cases" ? posts : suggestedPosts;

              if (loading) {
                return (
                  <div className="space-y-4">
                    {[1, 2].map((n) => (
                      <div key={n} className="bg-white rounded-2xl p-6 border border-slate-200 animate-pulse space-y-3 shadow-xs">
                        <div className="h-4 bg-slate-200 rounded w-1/3" />
                        <div className="h-6 bg-slate-200 rounded w-2/3" />
                        <div className="h-16 bg-slate-100 rounded" />
                      </div>
                    ))}
                  </div>
                );
              }

              if (activePosts.length === 0) {
                return (
                  <div className="text-center py-16 bg-white rounded-2xl border border-slate-200 p-8 shadow-xs space-y-3">
                    <span className="text-3xl">📝</span>
                    <h3 className="text-base font-bold text-slate-800">
                      {activeTab === "cases" ? "No cases published yet" : "No treatment regimens contributed yet"}
                    </h3>
                    <p className="text-xs text-slate-500 max-w-sm mx-auto">
                      {activeTab === "cases"
                        ? "Share a diagnostic dilemma or complex case with the international clinician network."
                        : "Contribute evidence-based treatment regimens to complex dilemmas in the clinical feed."}
                    </p>
                    <button
                      onClick={() => setIsComposerOpen(true)}
                      className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl transition shadow-xs cursor-pointer"
                    >
                      Share First Case
                    </button>
                  </div>
                );
              }

              return (
                <div className="space-y-4">
                  {activePosts.map((post) => (
                    <SocialPostCard
                      key={post.id}
                      post={post}
                      onHashtagClick={(tag: string) => (window.location.href = `/hub?q=${encodeURIComponent(tag)}`)}
                    />
                  ))}
                </div>
              );
            })()}
          </main>

          {/* ══════════════ RIGHT SIDEBAR ══════════════ */}
          <aside className="space-y-4 sticky top-6">
            <EmergencyRadarWidget />
            <TrendingHashtagsWidget
              onSelectHashtag={(tag: string) => (window.location.href = `/hub?q=${encodeURIComponent(tag)}`)}
            />
          </aside>
        </div>
      </div>

      {/* Case Composer Modal */}
      {isComposerOpen && (
        <SocialCaseComposer
          onClose={() => setIsComposerOpen(false)}
          onPostCreated={(newPost: DoctorPost) => {
            setPosts((prev) => [newPost, ...prev]);
            setProfile((prev) => (prev ? { ...prev, cases_count: (prev.cases_count || 0) + 1 } : prev));
            setIsComposerOpen(false);
          }}
        />
      )}
    </div>
  );
}
