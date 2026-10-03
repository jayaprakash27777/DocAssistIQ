/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React, { useState, useEffect, useCallback } from "react";
import { getStoredToken } from "@/lib/api";
import { getSharedRealtimeClient } from "@/lib/ws";
import { DoctorPost, TrendingHashtag, DoctorProfile } from "@/types/social";
import { SocialNavRail } from "@/components/hub/SocialNavRail";
import { SocialPostCard } from "@/components/hub/SocialPostCard";
import { TrendingHashtagsWidget } from "@/components/hub/TrendingHashtagsWidget";
import { VerifiedDoctorsWidget } from "@/components/hub/VerifiedDoctorsWidget";
import { SocialCaseComposer } from "@/components/hub/SocialCaseComposer";

export default function EmergencyHubPage() {
  const [posts, setPosts] = useState<DoctorPost[]>([]);
  const [hashtags, setHashtags] = useState<TrendingHashtag[]>([]);
  const [doctors, setDoctors] = useState<DoctorProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [showComposer, setShowComposer] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

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

  // Fetch Emergency Posts from real database
  const fetchEmergencyPosts = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/hub/emergency", { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        setPosts(data);
      }
    } catch (err) {
      console.error("Emergency feed fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchTrendingHashtags = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/hub/hashtags", { headers: authHeaders() });
      if (res.ok) setHashtags(await res.json());
    } catch {}
  }, []);

  const fetchExploreDoctors = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/hub/explore", { headers: authHeaders() });
      if (res.ok) setDoctors(await res.json());
    } catch {}
  }, []);

  useEffect(() => {
    fetchEmergencyPosts();
    fetchTrendingHashtags();
    fetchExploreDoctors();

    const authToken = token();
    if (!authToken) return;
    const client = getSharedRealtimeClient(authToken);

    const unsubscribe = client.subscribeMessages((type, payload) => {
      if (type === "hub_new_post" && payload.is_urgent_consult) {
        setPosts((prev) => [payload, ...prev.filter((p) => p.id !== payload.id)]);
        showToast(`🚨 NEW EMERGENCY STAT CONSULT: ${payload.disease_name}`);
      } else if (type === "hub_new_treatment_suggestion") {
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
      } else if (type === "hub_post_liked" && payload?.post_id) {
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
      } else if ((type === "hub_poll_vote" || type === "hub_new_vote") && payload?.post_id) {
        setPosts((prev) =>
          prev.map((p) =>
            p.id === payload.post_id && p.poll_data
              ? {
                  ...p,
                  poll_data: {
                    ...p.poll_data,
                    options: payload.options || p.poll_data.options,
                    total_votes: payload.total_votes ?? p.poll_data.total_votes,
                  },
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

  // Post Actions
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
        setPosts((prev) =>
          prev.map((p) =>
            p.id === postId ? { ...p, is_bookmarked_by_me: data.bookmarked } : p
          )
        );
        showToast(data.bookmarked ? "Case saved to Clinical Library" : "Bookmark removed");
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
        showToast("Emergency consultation response recorded");
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
        showToast("Treatment suggestion published to emergency team!");
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
        showToast("Endorsed clinical suggestion");
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
        showToast(data.is_adopted ? "Marked as Adopted Treatment!" : "Adoption revoked");
      }
    } catch {}
  };

  const handlePublishPost = async (postData: any, files: File[]) => {
    const attachmentIds: string[] = [];
    for (const f of files) {
      const formData = new FormData();
      formData.append("file", f);
      formData.append("metadata", JSON.stringify({ category: "clinical_imaging" }));
      const fRes = await fetch("/api/v1/files/upload", {
        method: "POST",
        headers: authHeaders(),
        body: formData,
      });
      if (fRes.ok) {
        const fileInfo = await fRes.json();
        if (fileInfo.id) attachmentIds.push(fileInfo.id);
      }
    }

    const payload = {
      ...postData,
      is_urgent_consult: true,
      attachment_ids: attachmentIds,
    };

    const res = await fetch("/api/v1/hub/posts", {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      const newPost = await res.json();
      setPosts((prev) => [newPost, ...prev]);
      showToast("🚨 Emergency STAT case broadcasted to global specialists!");
    }
  };

  const handleToggleFollow = async (targetDoctorId: string) => {
    try {
      const res = await fetch(`/api/v1/hub/doctors/${targetDoctorId}/follow`, {
        method: "POST",
        headers: authHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setDoctors((prev) =>
          prev.map((d) =>
            d.id === targetDoctorId
              ? { ...d, is_following: data.is_following, followers_count: data.followers_count }
              : d
          )
        );
        showToast(data.is_following ? "Following specialist" : "Unfollowed");
      }
    } catch {}
  };

  return (
    <div className="min-h-full bg-slate-50 text-slate-900 pb-28">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* ── 3-Column Social Network Grid ── */}
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr_310px] gap-6 items-start">
          {/* ══════════════ LEFT SIDEBAR ══════════════ */}
          <SocialNavRail
            onOpenCompose={() => setShowComposer(true)}
            urgentCasesCount={posts.length}
          />

          {/* ══════════════ CENTER FEED ══════════════ */}
          <main className="min-w-0 space-y-4">
            {/* Emergency Header Banner */}
            <div className="bg-gradient-to-r from-rose-600 to-red-600 text-white rounded-2xl p-5 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xl">🚨</span>
                  <h1 className="text-lg sm:text-xl font-black tracking-tight">
                    Emergency 2nd Opinions Board
                  </h1>
                </div>
                <span className="text-xs bg-white text-rose-900 font-extrabold px-3 py-1 rounded-full shadow-2xs">
                  {posts.length} Active Dilemmas
                </span>
              </div>
              <p className="text-xs text-rose-100 leading-relaxed max-w-xl">
                Critical, acute clinical presentations posted by doctors worldwide requiring rapid second opinions, ICU drug escalation, or differential confirmation before invasive intervention.
              </p>
            </div>

            {/* Emergency Posts Feed */}
            {loading ? (
              <div className="space-y-4">
                {[1, 2].map((n) => (
                  <div key={n} className="bg-white rounded-2xl p-6 border border-slate-200 animate-pulse space-y-3">
                    <div className="h-4 bg-slate-200 rounded w-1/3" />
                    <div className="h-6 bg-slate-200 rounded w-2/3" />
                    <div className="h-16 bg-slate-100 rounded" />
                  </div>
                ))}
              </div>
            ) : posts.length === 0 ? (
              <div className="text-center py-16 bg-white rounded-2xl border border-slate-200 p-8 shadow-xs space-y-3">
                <span className="text-3xl">✅</span>
                <h3 className="text-base font-bold text-slate-800">
                  No Active Emergency Consults Pending
                </h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto">
                  All emergency clinical second opinions have been addressed. Share a case if you have an acute dilemma.
                </p>
                <button
                  type="button"
                  onClick={() => setShowComposer(true)}
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-xl transition-all shadow-xs cursor-pointer inline-flex items-center gap-1.5"
                >
                  <span>🚨 Post Emergency Case</span>
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {posts.map((post) => (
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
            )}
          </main>

          {/* ══════════════ RIGHT SIDEBAR ══════════════ */}
          <aside className="hidden lg:block space-y-4 sticky top-6">
            <TrendingHashtagsWidget
              hashtags={hashtags}
              onSelectHashtag={(tag) => {
                window.location.href = `/hub?q=${encodeURIComponent(tag)}`;
              }}
            />

            <VerifiedDoctorsWidget
              doctors={doctors}
              onToggleFollow={handleToggleFollow}
            />
          </aside>
        </div>
      </div>

      {/* Case Composer Modal */}
      {showComposer && (
        <SocialCaseComposer
          onClose={() => setShowComposer(false)}
          onPublish={handlePublishPost}
        />
      )}

      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white border border-slate-700 rounded-2xl px-4 py-3 shadow-xl flex items-center gap-2.5 text-xs font-bold animate-in fade-in slide-in-from-bottom-5">
          <span className="w-2 h-2 rounded-full bg-teal-400 animate-ping" />
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  );
}
