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
import { ClinicalStoriesTray } from "@/components/hub/ClinicalStoriesTray";
import { ClinicalReelsModal, ClinicalReel } from "@/components/hub/ClinicalReelsModal";
import { AudioSpaceModal, AudioSpaceData } from "@/components/hub/AudioSpaceModal";
import { DoctorCirclesModal, CircleData } from "@/components/hub/DoctorCirclesModal";
import { CurbsideMessengerDrawer } from "@/components/hub/CurbsideMessengerDrawer";
import { CMEEventsModal } from "@/components/hub/CMEEventsModal";
import { DDICheckerModal } from "@/components/hub/DDICheckerModal";
import { DoctorPost, QuotedPostSummary } from "@/types/social";
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
  ArrowUp,
  Radio,
  MessageSquare,
  Users
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

  // Composer state
  const [isComposerOpen, setIsComposerOpen] = useState(false);
  const [composerDefaultEmergency, setComposerDefaultEmergency] = useState(false);
  const [quotedPost, setQuotedPost] = useState<QuotedPostSummary | null>(null);

  // Real-time modules state
  const [reels, setReels] = useState<ClinicalReel[]>([]);
  const [isReelsOpen, setIsReelsOpen] = useState(false);
  const [selectedReelIndex, setSelectedReelIndex] = useState(0);

  const [activeSpace, setActiveSpace] = useState<AudioSpaceData | null>(null);
  const [isAudioSpaceOpen, setIsAudioSpaceOpen] = useState(false);

  const [isCirclesOpen, setIsCirclesOpen] = useState(false);

  const [isCurbsideMessengerOpen, setIsCurbsideMessengerOpen] = useState(false);
  const [curbsideActiveColleagueId, setCurbsideActiveColleagueId] = useState<string | null>(null);
  const [curbsideAttachedCase, setCurbsideAttachedCase] = useState<{ id: string; disease_name: string; diagnosis?: string } | null>(null);

  const [isDDIOpen, setIsDDIOpen] = useState(false);
  const [isCMEOpen, setIsCMEOpen] = useState(false);

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

  // Fetch real-time initial modules (Reels, Live Spaces)
  useEffect(() => {
    const fetchRealtimeModules = async () => {
      try {
        const token = getStoredToken();
        const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

        // Fetch Reels
        fetch("/api/v1/hub/reels", { headers })
          .then((r) => (r.ok ? r.json() : []))
          .then((data) => {
            if (Array.isArray(data) && data.length > 0) setReels(data);
          })
          .catch(() => {});

        // Fetch Live Spaces
        fetch("/api/v1/hub/spaces", { headers })
          .then((r) => (r.ok ? r.json() : null))
          .then((data) => {
            if (data && data.is_live) setActiveSpace(data);
          })
          .catch(() => {});
      } catch (err) {
        console.error("Failed to fetch initial hub modules", err);
      }
    };
    fetchRealtimeModules();
  }, []);

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
      } else if (type === "hub_post_reaction" && payload?.post_id) {
        setPosts((prev) =>
          prev.map((post) =>
            post.id === payload.post_id
              ? {
                  ...post,
                  likes_count: payload.likes_count ?? post.likes_count,
                  reactions_breakdown: payload.reactions_breakdown ?? post.reactions_breakdown,
                }
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
            onOpenComposer={handleOpenStandardComposer}
            onOpenAudioSpace={() => setIsAudioSpaceOpen(true)}
            onOpenDoctorCircles={() => setIsCirclesOpen(true)}
            onOpenClinicalReels={() => {
              setSelectedReelIndex(0);
              setIsReelsOpen(true);
            }}
            onOpenCurbsideMessenger={() => {
              setCurbsideActiveColleagueId(null);
              setCurbsideAttachedCase(null);
              setIsCurbsideMessengerOpen(true);
            }}
            onOpenDDIChecker={() => setIsDDIOpen(true)}
            onOpenCMEEvents={() => setIsCMEOpen(true)}
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

            {/* Live Audio Space Banner (Twitter Spaces style) */}
            {activeSpace && activeSpace.is_live && (
              <div className="bg-gradient-to-r from-rose-500 via-rose-600 to-pink-600 text-white rounded-2xl p-4 shadow-xs flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center shrink-0">
                    <Radio className="w-5 h-5 text-white animate-pulse" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-black uppercase tracking-wider bg-white/25 px-2 py-0.5 rounded-full">
                        ● LIVE AUDIO DISCUSSION
                      </span>
                      <span className="text-xs text-rose-100 font-bold">
                        {activeSpace.listeners_count} doctors listening
                      </span>
                    </div>
                    <h3 className="text-sm font-black text-white mt-0.5">
                      {activeSpace.title}
                    </h3>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setIsAudioSpaceOpen(true)}
                  className="px-4 py-2 bg-white text-rose-600 hover:bg-rose-50 text-xs font-black rounded-xl shadow-xs transition shrink-0 cursor-pointer"
                >
                  Listen In Live →
                </button>
              </div>
            )}

            {/* Instagram / Reels Stories Tray */}
            {reels.length > 0 && (
              <ClinicalStoriesTray
                reels={reels}
                onSelectReel={(idx) => {
                  setSelectedReelIndex(idx);
                  setIsReelsOpen(true);
                }}
                onOpenComposer={handleOpenStandardComposer}
              />
            )}

            {/* Top Control Header Card */}
            <div className="bg-white rounded-2xl border border-slate-200/90 p-4 shadow-xs">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-lg font-black text-slate-900 tracking-tight">
                      Doctor Community Feed
                    </h1>
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold bg-teal-50 text-teal-800 px-2.5 py-0.5 rounded-full border border-teal-200">
                      <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                      Verified Doctors
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Discuss real patient cases, get quick second opinions, and learn from colleagues worldwide.
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  {/* Real-time Indicator */}
                  <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
                    <span className={`w-2 h-2 rounded-full ${wsLive ? "bg-emerald-500 animate-pulse" : "bg-amber-400"}`} />
                    <span>{wsLive ? "Live" : "Connecting"}</span>
                  </div>

                  <button
                    onClick={handleManualRefresh}
                    disabled={refreshing}
                    title="Refresh Feed"
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
                  🚨 Urgent Help ({urgentCount})
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
                  🤔 Unclear Diagnoses
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
                  💊 Treatment Plans
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
                  {newIncomingPosts.length} new {newIncomingPosts.length === 1 ? "case" : "cases"} posted • Tap to see newest
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
                  Have a patient case to discuss? Ask colleagues, add test results, or get a quick second opinion...
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
                    <span>Add Images</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleOpenStandardComposer}
                    className="px-2.5 py-1.5 rounded-lg text-xs font-bold text-slate-600 hover:text-indigo-700 hover:bg-indigo-50 transition flex items-center gap-1.5 cursor-pointer"
                  >
                    <Vote className="w-4 h-4 text-indigo-600" />
                    <span>Create Poll</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleOpenEmergencyComposer}
                    className="px-2.5 py-1.5 rounded-lg text-xs font-bold text-rose-700 hover:text-rose-800 hover:bg-rose-50 transition flex items-center gap-1.5 cursor-pointer"
                  >
                    <AlertTriangle className="w-4 h-4 text-rose-600" />
                    <span>Urgent 2nd Opinion</span>
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
                <h3 className="text-base font-bold text-slate-900">No cases found here yet</h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  {activeTag
                    ? `No discussions under ${activeTag} yet. Be the first doctor to share a case!`
                    : "No cases match this filter. Start a clinical discussion or ask colleagues for advice."}
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
                    Share a Case
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
                    onQuotePost={(p) => {
                      setQuotedPost({
                        id: p.id,
                        author_name: p.author_name || "Dr. Attending Specialist",
                        author_specialty: p.author_specialty,
                        author_institution: p.author_institution,
                        disease_name: p.disease_name,
                        diagnosis: p.diagnosis,
                        clinical_findings: p.clinical_findings,
                        created_at: p.created_at,
                        is_urgent_consult: p.is_urgent_consult,
                      });
                      setIsComposerOpen(true);
                    }}
                    onOpenCurbside={(p) => {
                      setCurbsideActiveColleagueId(p.author_id);
                      setCurbsideAttachedCase({
                        id: p.id,
                        disease_name: p.disease_name,
                        diagnosis: p.diagnosis,
                      });
                      setIsCurbsideMessengerOpen(true);
                    }}
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
                  placeholder="Search cases, symptoms, medicines, or #topics..."
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

            {/* Safe Doctor Network Notice */}
            <div className="p-3 bg-teal-50/60 rounded-2xl border border-teal-100 text-[11px] text-teal-900 space-y-1">
              <div className="font-extrabold flex items-center gap-1.5 text-teal-800">
                <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                <span>Safe Doctor Network</span>
              </div>
              <p className="text-teal-700 leading-snug">
                Private network for verified doctors. All patient names and personal details are strictly protected.
              </p>
            </div>
          </aside>
        </div>
      </div>

      {/* ── Floating Curbside Messenger Trigger Button ── */}
      {!isCurbsideMessengerOpen && (
        <button
          type="button"
          onClick={() => {
            setCurbsideActiveColleagueId(null);
            setCurbsideAttachedCase(null);
            setIsCurbsideMessengerOpen(true);
          }}
          className="fixed bottom-6 right-6 z-40 bg-teal-600 hover:bg-teal-700 text-white px-4 py-3 rounded-full shadow-lg flex items-center gap-2.5 font-black text-xs transition-all duration-200 hover:scale-105 cursor-pointer border border-teal-500"
        >
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-300 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400" />
          </span>
          <MessageSquare className="w-4 h-4" />
          <span>Doctor Chat</span>
        </button>
      )}

      {/* ── Real-Time Modals & Drawers ── */}
      {isReelsOpen && (
        <ClinicalReelsModal
          reels={reels}
          initialIndex={selectedReelIndex}
          onClose={() => setIsReelsOpen(false)}
        />
      )}

      {isAudioSpaceOpen && (
        <AudioSpaceModal
          space={activeSpace}
          onClose={() => setIsAudioSpaceOpen(false)}
        />
      )}

      {isCirclesOpen && (
        <DoctorCirclesModal
          onSelectCircleFilter={(c) => {
            setIsCirclesOpen(false);
            handleSelectHashtag(c.specialty);
          }}
          onClose={() => setIsCirclesOpen(false)}
        />
      )}

      {isCurbsideMessengerOpen && (
        <CurbsideMessengerDrawer
          onClose={() => {
            setIsCurbsideMessengerOpen(false);
            setCurbsideActiveColleagueId(null);
            setCurbsideAttachedCase(null);
          }}
          targetColleagueId={curbsideActiveColleagueId}
          activeCaseToAttach={curbsideAttachedCase}
          onClearAttachedCase={() => setCurbsideAttachedCase(null)}
        />
      )}

      {isDDIOpen && (
        <DDICheckerModal
          onClose={() => setIsDDIOpen(false)}
        />
      )}

      {isCMEOpen && (
        <CMEEventsModal
          onClose={() => setIsCMEOpen(false)}
        />
      )}

      {/* Case Composer Modal */}
      {isComposerOpen && (
        <SocialCaseComposer
          initialEmergency={composerDefaultEmergency}
          quotedPost={quotedPost}
          onClearQuote={() => setQuotedPost(null)}
          onClose={() => {
            setIsComposerOpen(false);
            setQuotedPost(null);
          }}
          onPostCreated={(newPost: DoctorPost) => {
            setPosts((prev) => [newPost, ...prev]);
            setIsComposerOpen(false);
            setQuotedPost(null);
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
