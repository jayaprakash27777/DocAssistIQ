/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { getStoredToken } from "@/lib/api";
import { getSharedRealtimeClient } from "@/lib/ws";
import { DoctorPost, TrendingHashtag } from "@/types/social";
import { SocialNavRail } from "@/components/hub/SocialNavRail";
import { SocialPostCard } from "@/components/hub/SocialPostCard";
import { TrendingHashtagsWidget } from "@/components/hub/TrendingHashtagsWidget";
import { EmergencyRadarWidget } from "@/components/hub/EmergencyRadarWidget";

export default function SavedHubPage() {
  const [posts, setPosts] = useState<DoctorPost[]>([]);
  const [hashtags, setHashtags] = useState<TrendingHashtag[]>([]);
  const [loading, setLoading] = useState(true);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [folders, setFolders] = useState<string[]>(["All"]);
  const [activeFolder, setActiveFolder] = useState<string>("All");

  const token = () =>
    getStoredToken() ||
    (typeof window !== "undefined"
      ? localStorage.getItem("access_token") || localStorage.getItem("token")
      : null) ||
    "";

  const authHeaders = (extra: Record<string, string> = {}) => {
    const t = token();
    return t ? { ...extra, Authorization: `Bearer ${t}` } : { ...extra };
  };

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const fetchSavedPosts = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/hub/feed", { headers: authHeaders() });
      if (res.ok) {
        const data: DoctorPost[] = await res.json();
        setPosts(data.filter((p) => p.is_bookmarked_by_me));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchFolders = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/hub/bookmarks/folders", { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        const list = Array.isArray(data) ? data : (data.folders || []);
        setFolders(Array.from(new Set(["All", ...list])));
      }
    } catch {}
  }, []);

  const fetchTrendingHashtags = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/hub/hashtags", { headers: authHeaders() });
      if (res.ok) setHashtags(await res.json());
    } catch {}
  }, []);

  useEffect(() => {
    fetchSavedPosts();
    fetchFolders();
    fetchTrendingHashtags();

    const authToken = token();
    if (!authToken) return;
    const client = getSharedRealtimeClient(authToken);

    const unsubscribe = client.subscribeMessages((type, payload) => {
      if (type === "hub_post_liked" && payload?.post_id) {
        setPosts((prev) =>
          prev.map((p) =>
            p.id === payload.post_id ? { ...p, likes_count: payload.likes_count } : p
          )
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
      } else if (type === "hub_new_comment" && payload?.comment) {
        setPosts((prev) =>
          prev.map((p) =>
            p.id === payload.post_id
              ? {
                  ...p,
                  comments_count: (p.comments_count || 0) + 1,
                  comments: [...(p.comments || []), payload.comment],
                }
              : p
          )
        );
      } else if (type === "hub_new_treatment_suggestion" && payload?.suggestion) {
        setPosts((prev) =>
          prev.map((p) =>
            p.id === payload.post_id
              ? {
                  ...p,
                  treatment_suggestions: [payload.suggestion, ...(p.treatment_suggestions || [])],
                }
              : p
          )
        );
      }
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const handleLike = async (postId: string) => {
    try {
      const res = await fetch(`/api/v1/hub/posts/${postId}/like`, {
        method: "POST",
        headers: authHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setPosts((prev) =>
          prev.map((p) =>
            p.id === postId ? { ...p, is_liked_by_me: data.liked, likes_count: data.likes_count } : p
          )
        );
      }
    } catch {}
  };

  const handleBookmark = async (postId: string) => {
    try {
      const res = await fetch(`/api/v1/hub/posts/${postId}/bookmark`, {
        method: "POST",
        headers: authHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setPosts((prev) => prev.filter((p) => p.id !== postId));
        showToast("Case removed from Saved Library");
      }
    } catch {}
  };

  const handleComment = async (postId: string, text: string) => {
    try {
      const res = await fetch(`/api/v1/hub/posts/${postId}/comments`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ content: text }),
      });
      if (res.ok) {
        const commentData = await res.json();
        setPosts((prev) =>
          prev.map((p) =>
            p.id === postId
              ? {
                  ...p,
                  comments_count: p.comments_count + 1,
                  comments: [commentData, ...p.comments.filter((c) => c.id !== commentData.id)],
                }
              : p
          )
        );
        showToast("Comment recorded");
      }
    } catch {}
  };

  const handleVotePoll = async (postId: string, optionIndex: number) => {
    try {
      const res = await fetch(`/api/v1/hub/posts/${postId}/poll-vote`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ option_index: optionIndex }),
      });
      if (res.ok) {
        const data = await res.json();
        setPosts((prev) =>
          prev.map((p) =>
            p.id === postId
              ? {
                  ...p,
                  poll_data: {
                    ...p.poll_data!,
                    options: data.options,
                    total_votes: data.total_votes,
                    has_voted: true,
                    voted_index: data.voted_index,
                  },
                }
              : p
          )
        );
      }
    } catch {}
  };

  const handleAddTreatmentSuggestion = async (
    postId: string,
    data: {
      drug_or_intervention: string;
      dosage_and_route?: string;
      clinical_rationale: string;
      evidence_grade?: string;
    }
  ) => {
    try {
      const res = await fetch(`/api/v1/hub/posts/${postId}/treatment-suggestions`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify(data),
      });
      if (res.ok) {
        const sugg = await res.json();
        setPosts((prev) =>
          prev.map((p) =>
            p.id === postId
              ? {
                  ...p,
                  treatment_suggestions: [sugg, ...(p.treatment_suggestions || [])],
                }
              : p
          )
        );
        showToast("Treatment suggestion recorded!");
      }
    } catch {}
  };

  const handleEndorseSuggestion = async (postId: string, suggestionId: string) => {
    try {
      const res = await fetch(
        `/api/v1/hub/posts/${postId}/treatment-suggestions/${suggestionId}/endorse`,
        { method: "POST", headers: authHeaders() }
      );
      if (res.ok) {
        const data = await res.json();
        setPosts((prev) =>
          prev.map((p) =>
            p.id === postId
              ? {
                  ...p,
                  treatment_suggestions: p.treatment_suggestions?.map((s) =>
                    s.id === suggestionId ? { ...s, endorsements_count: data.endorsements_count } : s
                  ),
                }
              : p
          )
        );
      }
    } catch {}
  };

  const handleAdoptSuggestion = async (postId: string, suggestionId: string) => {
    try {
      const res = await fetch(
        `/api/v1/hub/posts/${postId}/treatment-suggestions/${suggestionId}/adopt`,
        { method: "POST", headers: authHeaders() }
      );
      if (res.ok) {
        const data = await res.json();
        setPosts((prev) =>
          prev.map((p) =>
            p.id === postId
              ? {
                  ...p,
                  treatment_suggestions: p.treatment_suggestions?.map((s) =>
                    s.id === suggestionId ? { ...s, is_adopted: data.is_adopted } : s
                  ),
                }
              : p
          )
        );
      }
    } catch {}
  };

  return (
    <div className="min-h-full bg-slate-50 text-slate-900 pb-28">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr_310px] gap-6 items-start">
          <SocialNavRail
            onOpenCompose={() => {
              window.location.href = "/hub";
            }}
            savedCasesCount={posts.length}
          />

          <main className="min-w-0 space-y-4">
            <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-xl">🔖</span>
                <div>
                  <h1 className="text-lg font-black text-slate-900 tracking-tight">
                    Saved Clinical Library
                  </h1>
                  <p className="text-xs text-slate-500">
                    Your personal reference repository of validated clinical cases and treatment protocols.
                  </p>
                </div>
              </div>

              {/* Folder Filter Tabs */}
              <div className="flex items-center gap-2 pt-2 border-t border-slate-100 overflow-x-auto no-scrollbar">
                {folders.map((folder) => (
                  <button
                    key={folder}
                    type="button"
                    onClick={() => setActiveFolder(folder)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                      activeFolder === folder
                        ? "bg-teal-600 text-white shadow-xs"
                        : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                    }`}
                  >
                    📁 {folder}
                  </button>
                ))}
              </div>
            </div>

            {(() => {
              const displayedPosts =
                activeFolder === "All"
                  ? posts
                  : posts.filter((p) => (p.bookmark_folder || "General") === activeFolder);

              if (loading) {
                return (
                  <div className="space-y-4">
                    {[1, 2].map((n) => (
                      <div key={n} className="bg-white rounded-2xl p-6 border border-slate-200 animate-pulse space-y-3">
                        <div className="h-4 bg-slate-200 rounded w-1/3" />
                        <div className="h-6 bg-slate-200 rounded w-2/3" />
                      </div>
                    ))}
                  </div>
                );
              }

              if (displayedPosts.length === 0) {
                return (
                  <div className="text-center py-16 bg-white rounded-2xl border border-slate-200 p-8 shadow-xs space-y-3">
                    <span className="text-3xl">📚</span>
                    <h3 className="text-base font-bold text-slate-800">
                      {activeFolder === "All"
                        ? "No Saved Cases in Your Library Yet"
                        : `No cases saved in folder "${activeFolder}"`}
                    </h3>
                    <p className="text-xs text-slate-500 max-w-sm mx-auto">
                      Click the bookmark icon on any clinical case in the timeline to organize and save it for rapid reference.
                    </p>
                    <Link
                      href="/hub"
                      className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl transition-all shadow-xs cursor-pointer inline-flex items-center gap-1.5"
                    >
                      <span>Explore Timeline Feed</span>
                    </Link>
                  </div>
                );
              }

              return (
                <div className="space-y-4">
                  {displayedPosts.map((post) => (
                    <SocialPostCard
                      key={post.id}
                      post={post}
                      onLike={handleLike}
                      onBookmark={handleBookmark}
                      onComment={handleComment}
                      onVotePoll={handleVotePoll}
                      onAddTreatmentSuggestion={handleAddTreatmentSuggestion}
                      onEndorseTreatmentSuggestion={handleEndorseSuggestion}
                      onAdoptTreatmentSuggestion={handleAdoptSuggestion}
                    />
                  ))}
                </div>
              );
            })()}
          </main>

          <aside className="hidden lg:block space-y-4 sticky top-6">
            <EmergencyRadarWidget />
            <TrendingHashtagsWidget
              hashtags={hashtags}
              onSelectHashtag={(tag) => {
                window.location.href = `/hub?q=${encodeURIComponent(tag)}`;
              }}
            />
          </aside>
        </div>
      </div>

      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white border border-slate-700 rounded-2xl px-4 py-3 shadow-xl flex items-center gap-2.5 text-xs font-bold animate-in fade-in slide-in-from-bottom-5">
          <span className="w-2 h-2 rounded-full bg-teal-400 animate-ping" />
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  );
}
