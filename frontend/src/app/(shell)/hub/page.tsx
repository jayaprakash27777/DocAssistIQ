"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { SocialNavRail } from "@/components/hub/SocialNavRail";
import { SocialPostCard } from "@/components/hub/SocialPostCard";
import { SocialCaseComposer } from "@/components/hub/SocialCaseComposer";
import { TrendingHashtagsWidget } from "@/components/hub/TrendingHashtagsWidget";
import { EmergencyRadarWidget } from "@/components/hub/EmergencyRadarWidget";
import { VerifiedDoctorsWidget } from "@/components/hub/VerifiedDoctorsWidget";
import { StatEmergencyPagerBanner } from "@/components/hub/StatEmergencyPagerBanner";
import { DoctorPost } from "@/types/social";
import { getSharedRealtimeClient } from "@/lib/ws";
import { getStoredToken } from "@/lib/api";
import {
  Sparkles,
  AlertTriangle,
  Stethoscope,
  Pill,
  Search,
  X,
  PlusCircle,
  FileImage,
  Vote,
  RefreshCw,
  ShieldCheck,
  ArrowUp
} from "lucide-react";

type FeedFilter = "all" | "emergency" | "dilemma" | "treatment";

function HubFeedContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialQuery = searchParams.get("q") || "";

  const [posts, setPosts] = useState<DoctorPost[]>([]);
  const [newIncomingPosts, setNewIncomingPosts] = useState<DoctorPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<FeedFilter>("all");
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [activeTag, setActiveTag] = useState<string | null>(
    initialQuery ? (initialQuery.startsWith("#") ? initialQuery : `#${initialQuery}`) : null
  );
  const [isComposerOpen, setIsComposerOpen] = useState(false);
  const [composerDefaultEmergency, setComposerDefaultEmergency] = useState(false);
  const [wsLive, setWsLive] = useState(false);

  // Sync state if URL query param changes
  useEffect(() => {
    const q = searchParams.get("q");
    if (q) {
      setSearchQuery(q);
      setActiveTag(q.startsWith("#") ? q : `#${q}`);
    } else {
      setActiveTag(null);
    }
  }, [searchParams]);

  // Fetch real posts from backend API
  const fetchPosts = useCallback(async (tag?: string | null, isEmergency?: boolean) => {
    try {
      let url = "/api/v1/hub/posts?limit=50";
      if (tag) {
        const cleanTag = tag.replace(/^#/, "");
        url += `&tag=${encodeURIComponent(cleanTag)}`;
      }
      if (isEmergency) {
        url += "&is_emergency=true";
      }

      const token = getStoredToken();
      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        const rawPosts = Array.isArray(data) ? data : (data.posts || []);
        setPosts(rawPosts);
        setNewIncomingPosts([]);
      }
    } catch (err) {
      console.error("Failed to load clinical feed posts:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchPosts(activeTag, filter === "emergency");
  }, [activeTag, filter, fetchPosts]);

  // Real-time WebSocket subscriptions for live doctor feed updates
  useEffect(() => {
    const token = getStoredToken();
    const ws = getSharedRealtimeClient(token);

    const unsubState = ws.subscribeState((state) => {
      setWsLive(state === "LIVE");
    });

    const unsubMessages = ws.subscribeMessages((type, payload) => {
      if (type === "hub_new_post") {
        const incoming = payload?.post || (payload?.id ? payload : null);
        if (incoming) {
          setNewIncomingPosts((prev) => [incoming, ...prev]);
        }
      } else if (type === "hub_post_liked" && payload?.post_id) {
        setPosts((prev) =>
          prev.map((post) =>
            post.id === payload.post_id
              ? { ...post, likes_count: payload.likes_count }
              : post
          )
        );
      } else if (type === "hub_post_outcome_updated" && payload?.post_id) {
        setPosts((prev) =>
          prev.map((post) =>
            post.id === payload.post_id
              ? {
                  ...post,
                  patient_outcome: payload.patient_outcome,
                  is_solved: payload.is_solved,
                  outcome_reported_at: payload.outcome_reported_at,
                  case_status: payload.is_solved ? "solved" : post.case_status,
                }
              : post
          )
        );
      } else if (type === "hub_new_treatment_suggestion" && payload?.suggestion) {
        setPosts((prev) =>
          prev.map((post) => {
            if (post.id === payload.post_id) {
              const existing = post.treatment_suggestions || [];
              return {
                ...post,
                treatment_suggestions: [payload.suggestion, ...existing],
                suggestions_count: (post.suggestions_count || 0) + 1,
              };
            }
            return post;
          })
        );
      } else if (type === "hub_suggestion_endorsed" && payload?.suggestion_id) {
        setPosts((prev) =>
          prev.map((post) => {
            if (post.id === payload.post_id) {
              return {
                ...post,
                treatment_suggestions: (post.treatment_suggestions || []).map((sugg) =>
                  sugg.id === payload.suggestion_id
                    ? { ...sugg, endorsements_count: payload.endorsements_count }
                    : sugg
                ),
              };
            }
            return post;
          })
        );
      } else if (type === "hub_suggestion_adopted" && payload?.suggestion_id) {
        setPosts((prev) =>
          prev.map((post) => {
            if (post.id === payload.post_id) {
              return {
                ...post,
                treatment_suggestions: (post.treatment_suggestions || []).map((sugg) => ({
                  ...sugg,
                  is_adopted: sugg.id === payload.suggestion_id,
                })),
              };
            }
            return post;
          })
        );
      } else if (type === "hub_new_comment" && payload?.comment) {
        setPosts((prev) =>
          prev.map((post) => {
            if (post.id === payload.post_id) {
              const existing = post.comments || [];
              return {
                ...post,
                comments: [...existing, payload.comment],
                comments_count: (post.comments_count || 0) + 1,
              };
            }
            return post;
          })
        );
      } else if ((type === "hub_poll_vote" || type === "hub_new_vote") && payload?.post_id) {
        setPosts((prev) =>
          prev.map((post) => {
            if (post.id === payload.post_id && post.poll_data) {
              return {
                ...post,
                poll_data: {
                  ...post.poll_data,
                  options: payload.options || post.poll_data.options,
                  total_votes: payload.total_votes ?? post.poll_data.total_votes,
                },
              };
            }
            return post;
          })
        );
      }
    });

    return () => {
      unsubState();
      unsubMessages();
    };
  }, []);

  const handleSelectHashtag = (tag: string) => {
    setActiveTag(tag);
    setSearchQuery(tag);
    router.push(`/hub?q=${encodeURIComponent(tag)}`);
  };

  const handleClearFilter = () => {
    setActiveTag(null);
    setSearchQuery("");
    router.push("/hub");
  };

  const handleManualRefresh = () => {
    setRefreshing(true);
    fetchPosts(activeTag, filter === "emergency");
  };

  const handleApplyIncomingPosts = () => {
    setPosts((prev) => [...newIncomingPosts, ...prev]);
    setNewIncomingPosts([]);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleOpenEmergencyComposer = () => {
    setComposerDefaultEmergency(true);
    setIsComposerOpen(true);
  };

  const handleOpenStandardComposer = () => {
    setComposerDefaultEmergency(false);
    setIsComposerOpen(true);
  };

  // Filter posts based on active filter button
  const displayedPosts = posts.filter((post) => {
    const isEmerg = post.is_emergency || post.is_urgent_consult;
    if (filter === "emergency") return Boolean(isEmerg);
    const allTags = [...(post.specialty_tags || []), ...(post.tags || [])];
    if (filter === "dilemma") {
      return (
        post.poll_data !== undefined ||
        allTags.some((t: string) => t.toLowerCase().includes("dilemma") || t.toLowerCase().includes("diagnostic"))
      );
    }
    if (filter === "treatment") {
      return (
        (post.treatment_suggestions && post.treatment_suggestions.length > 0) ||
        allTags.some((t: string) => t.toLowerCase().includes("treatment") || t.toLowerCase().includes("therapy"))
      );
    }
    return true;
  });

  const urgentCount = posts.filter((p) => p.is_emergency || p.is_urgent_consult).length;

  return (
    <div className="min-h-full bg-slate-50 text-slate-900 pb-28">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* ── 3-Column Social Network Grid (Aligned & Responsive) ── */}
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr_310px] gap-6 items-start">
          {/* ══════════════ LEFT SIDEBAR ══════════════ */}
          <SocialNavRail
            onOpenCompose={handleOpenStandardComposer}
            urgentCasesCount={urgentCount}
          />

          {/* ══════════════ CENTER TIMELINE FEED ══════════════ */}
          <main className="min-w-0 space-y-4">
            {/* Real-time STAT Emergency Audio Pager Banner */}
            <StatEmergencyPagerBanner
              urgentCases={posts.filter((p) => p.is_emergency || p.is_urgent_consult)}
              onSelectCase={(c) => {
                setSearchQuery(c.disease_name);
              }}
            />

            {/* Top Control Header Card */}
            <div className="bg-white rounded-2xl border border-slate-200/90 p-4 shadow-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <h1 className="text-lg font-black text-slate-900 tracking-tight">
                    Clinical Timeline
                  </h1>
                  <span className="inline-flex items-center gap-1 text-[11px] font-bold bg-teal-50 text-teal-800 px-2.5 py-0.5 rounded-full border border-teal-200">
                    <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                    Verified Clinicians
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  {/* Real-time Indicator */}
                  <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
                    <span className={`w-2 h-2 rounded-full ${wsLive ? "bg-emerald-500 animate-pulse" : "bg-amber-400"}`} />
                    <span>{wsLive ? "Live Sync" : "Syncing"}</span>
                  </div>

                  <button
                    onClick={handleManualRefresh}
                    disabled={refreshing}
                    title="Refresh Timeline"
                    className="p-1.5 text-slate-400 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition cursor-pointer"
                  >
                    <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin text-teal-600" : ""}`} />
                  </button>
                </div>
              </div>

              {/* Feed Filter Tabs */}
              <div className="flex items-center gap-1.5 mt-3 pt-3 border-t border-slate-100 overflow-x-auto no-scrollbar">
                <button
                  onClick={() => setFilter("all")}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer ${
                    filter === "all"
                      ? "bg-teal-600 text-white shadow-xs"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  All Cases
                </button>

                <button
                  onClick={() => setFilter("emergency")}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer ${
                    filter === "emergency"
                      ? "bg-rose-600 text-white shadow-xs"
                      : "bg-rose-50 text-rose-800 hover:bg-rose-100 border border-rose-100"
                  }`}
                >
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-500" />
                  STAT Emergency ({urgentCount})
                </button>

                <button
                  onClick={() => setFilter("dilemma")}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer ${
                    filter === "dilemma"
                      ? "bg-indigo-600 text-white shadow-xs"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  <Stethoscope className="w-3.5 h-3.5 text-indigo-500" />
                  Diagnostic Dilemmas
                </button>

                <button
                  onClick={() => setFilter("treatment")}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer ${
                    filter === "treatment"
                      ? "bg-teal-700 text-white shadow-xs"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  <Pill className="w-3.5 h-3.5 text-teal-600" />
                  Treatment Regimens
                </button>
              </div>

              {/* Active Hashtag or Search Filter Banner */}
              {activeTag && (
                <div className="flex items-center gap-2 mt-2 pt-2 border-t border-slate-100 text-xs">
                  <span className="text-slate-500 font-medium">Filtering by:</span>
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-xs font-bold bg-teal-50 text-teal-800 border border-teal-200">
                    {activeTag}
                    <button onClick={handleClearFilter} className="hover:text-rose-600 transition cursor-pointer">
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                  <span className="text-slate-400">
                    ({displayedPosts.length} {displayedPosts.length === 1 ? "case" : "cases"})
                  </span>
                </div>
              )}
            </div>

            {/* Real-time Floating Incoming Posts Banner (Twitter / X style) */}
            {newIncomingPosts.length > 0 && (
              <button
                onClick={handleApplyIncomingPosts}
                className="w-full py-2.5 px-4 bg-teal-600 hover:bg-teal-700 text-white text-xs font-black rounded-2xl shadow-sm transition-all flex items-center justify-center gap-2 cursor-pointer animate-bounce"
              >
                <ArrowUp className="w-4 h-4" />
                <span>
                  {newIncomingPosts.length} new clinical {newIncomingPosts.length === 1 ? "case" : "cases"} posted • Click to view
                </span>
              </button>
            )}

            {/* In-Feed Case Composer Trigger Card */}
            <div className="bg-white rounded-2xl border border-slate-200/90 p-4 shadow-xs space-y-3">
              <div className="flex gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-teal-600 to-emerald-500 flex items-center justify-center text-sm font-black text-white shrink-0 shadow-xs">
                  MD
                </div>
                <button
                  type="button"
                  onClick={handleOpenStandardComposer}
                  className="flex-1 text-left px-4 py-2.5 bg-slate-50 hover:bg-slate-100 text-slate-500 text-xs rounded-xl border border-slate-200 transition cursor-pointer"
                >
                  Share a clinical dilemma, diagnostic imaging, or treatment question with colleagues worldwide...
                </button>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={handleOpenStandardComposer}
                    className="px-2.5 py-1.5 rounded-lg text-xs font-bold text-slate-600 hover:text-teal-700 hover:bg-teal-50 transition flex items-center gap-1.5 cursor-pointer"
                  >
                    <FileImage className="w-4 h-4 text-teal-600" />
                    <span>Attach Imaging</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleOpenStandardComposer}
                    className="px-2.5 py-1.5 rounded-lg text-xs font-bold text-slate-600 hover:text-indigo-700 hover:bg-indigo-50 transition flex items-center gap-1.5 cursor-pointer"
                  >
                    <Vote className="w-4 h-4 text-indigo-600" />
                    <span>Consensus Poll</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleOpenEmergencyComposer}
                    className="px-2.5 py-1.5 rounded-lg text-xs font-bold text-rose-700 hover:text-rose-800 hover:bg-rose-50 transition flex items-center gap-1.5 cursor-pointer"
                  >
                    <AlertTriangle className="w-4 h-4 text-rose-600" />
                    <span>STAT 2nd Opinion</span>
                  </button>
                </div>

                <button
                  type="button"
                  onClick={handleOpenStandardComposer}
                  className="px-4 py-1.5 bg-teal-600 hover:bg-teal-700 text-white font-black text-xs rounded-xl transition shadow-xs flex items-center gap-1 cursor-pointer"
                >
                  <PlusCircle className="w-3.5 h-3.5" />
                  <span>Share Case</span>
                </button>
              </div>
            </div>

            {/* Posts Feed List */}
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((n) => (
                  <div key={n} className="bg-white rounded-2xl p-6 border border-slate-200 animate-pulse space-y-3 shadow-xs">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-slate-200 rounded-full" />
                      <div className="space-y-1.5 flex-1">
                        <div className="h-4 bg-slate-200 rounded w-1/4" />
                        <div className="h-3 bg-slate-100 rounded w-1/3" />
                      </div>
                    </div>
                    <div className="h-4 bg-slate-200 rounded w-2/3" />
                    <div className="h-16 bg-slate-100 rounded" />
                  </div>
                ))}
              </div>
            ) : displayedPosts.length === 0 ? (
              <div className="text-center py-16 bg-white rounded-2xl border border-slate-200 p-8 shadow-xs space-y-3">
                <span className="text-4xl">🩺</span>
                <h3 className="text-base font-bold text-slate-900">No clinical cases found</h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  {activeTag
                    ? `No current discussions under ${activeTag}. Be the first verified clinician to share a case!`
                    : "No cases match your selected filter. Start a clinical discussion or request a second opinion."}
                </p>
                <div className="pt-2 flex justify-center gap-2">
                  {activeTag && (
                    <button
                      onClick={handleClearFilter}
                      className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition cursor-pointer"
                    >
                      View All Cases
                    </button>
                  )}
                  <button
                    onClick={handleOpenStandardComposer}
                    className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white font-black text-xs rounded-xl transition shadow-xs cursor-pointer"
                  >
                    Share New Case
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {displayedPosts.map((post) => (
                  <SocialPostCard
                    key={post.id}
                    post={post}
                    onHashtagClick={handleSelectHashtag}
                  />
                ))}
              </div>
            )}
          </main>

          {/* ══════════════ RIGHT SIDEBAR ══════════════ */}
          <aside className="space-y-4 sticky top-6">
            {/* Live Search Card */}
            <div className="bg-white rounded-2xl border border-slate-200/90 p-3 shadow-xs">
              <div className="relative">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search diseases, drugs, or #tags..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    if (e.target.value.length === 0) handleClearFilter();
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && searchQuery.trim()) {
                      handleSelectHashtag(searchQuery.trim());
                    }
                  }}
                  className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 text-xs text-slate-900 bg-slate-50 focus:bg-white outline-none focus:border-teal-600 transition"
                />
              </div>
            </div>

            {/* Emergency STAT Radar Widget */}
            <EmergencyRadarWidget />

            {/* Trending Clinical Hashtags Widget */}
            <TrendingHashtagsWidget onSelectHashtag={handleSelectHashtag} />

            {/* Verified Global Doctors Directory Widget */}
            <VerifiedDoctorsWidget />

            {/* Global Physician Network Notice */}
            <div className="p-3 bg-teal-50/60 rounded-2xl border border-teal-100 text-[11px] text-teal-900 space-y-1">
              <div className="font-extrabold flex items-center gap-1.5 text-teal-800">
                <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                <span>Global Medical Network</span>
              </div>
              <p className="text-teal-700 leading-snug">
                For verified medical doctors worldwide. All case sharing conforms to HIPAA & GDPR de-identification standards.
              </p>
            </div>
          </aside>
        </div>
      </div>

      {/* Case Composer Modal */}
      {isComposerOpen && (
        <SocialCaseComposer
          initialEmergency={composerDefaultEmergency}
          onClose={() => setIsComposerOpen(false)}
          onPostCreated={(newPost: DoctorPost) => {
            setPosts((prev) => [newPost, ...prev]);
            setIsComposerOpen(false);
          }}
        />
      )}
    </div>
  );
}

export default function ClinicalHubPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-full bg-slate-50 flex items-center justify-center p-20 text-slate-500">
          <div className="w-8 h-8 border-2 border-teal-600 border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <HubFeedContent />
    </Suspense>
  );
}
