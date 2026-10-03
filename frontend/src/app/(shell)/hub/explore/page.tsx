/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { getStoredToken } from "@/lib/api";
import { TrendingHashtag, DoctorProfile, DoctorPost } from "@/types/social";
import { getSharedRealtimeClient } from "@/lib/ws";
import { SocialNavRail } from "@/components/hub/SocialNavRail";
import { SocialCaseComposer } from "@/components/hub/SocialCaseComposer";
import { TrendingHashtagsWidget } from "@/components/hub/TrendingHashtagsWidget";
import { EmergencyRadarWidget } from "@/components/hub/EmergencyRadarWidget";

export default function ExploreHubPage() {
  const [hashtags, setHashtags] = useState<TrendingHashtag[]>([]);
  const [doctors, setDoctors] = useState<DoctorProfile[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<DoctorPost[]>([]);
  const [isSearching, setIsSearching] = useState(false);
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
    fetchTrendingHashtags();
    fetchExploreDoctors();

    const authToken = token();
    if (!authToken) return;
    const client = getSharedRealtimeClient(authToken);

    const unsubscribe = client.subscribeMessages((type, payload) => {
      if (type === "hub_doctor_followed" && payload?.doctor_id) {
        setDoctors((prev) =>
          prev.map((d) =>
            d.id === payload.doctor_id
              ? { ...d, followers_count: payload.followers_count }
              : d
          )
        );
      } else if (type === "hub_new_post") {
        fetchTrendingHashtags();
      }
    });

    return () => {
      unsubscribe();
    };
  }, []);

  // Search cases dynamically
  const handleSearch = async (q: string) => {
    setSearchQuery(q);
    if (q.length < 2) {
      setSearchResults([]);
      return;
    }
    setIsSearching(true);
    try {
      const res = await fetch(`/api/v1/hub/search?q=${encodeURIComponent(q)}`, {
        headers: authHeaders(),
      });
      if (res.ok) {
        setSearchResults(await res.json());
      }
    } finally {
      setIsSearching(false);
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
        showToast(data.is_following ? "Following doctor" : "Unfollowed doctor");
      }
    } catch {}
  };

  return (
    <div className="min-h-full bg-slate-50 text-slate-900 pb-28">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr_310px] gap-6 items-start">
          {/* ══════════════ LEFT SIDEBAR ══════════════ */}
          <SocialNavRail onOpenCompose={() => setShowComposer(true)} />

          {/* ══════════════ CENTER CONTENT ══════════════ */}
          <main className="min-w-0 space-y-6">
            {/* Header & Global Search */}
            <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-xl font-black text-slate-900 tracking-tight">
                    Explore Clinical Social Network
                  </h1>
                  <p className="text-xs text-slate-500">
                    Discover trending clinical hashtags, real diagnostic cases, and verified global specialists.
                  </p>
                </div>
              </div>

              {/* Search input */}
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">
                  🔍
                </span>
                <input
                  type="text"
                  placeholder="Search diseases, drugs, clinical manifestations, or #hashtags..."
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 text-xs text-slate-900 bg-white outline-none focus:border-teal-600 shadow-2xs font-medium"
                />
              </div>

              {/* Search Results Dropdown / Preview */}
              {searchQuery.length >= 2 && (
                <div className="pt-2 border-t border-slate-100">
                  <div className="flex items-center justify-between text-xs font-bold text-slate-700 mb-2">
                    <span>Search Results ({searchResults.length})</span>
                    {isSearching && <span className="text-teal-600">Searching...</span>}
                  </div>
                  {searchResults.length === 0 && !isSearching ? (
                    <p className="text-xs text-slate-400 italic">No clinical cases found for &quot;{searchQuery}&quot;</p>
                  ) : (
                    <div className="space-y-2">
                      {searchResults.map((post) => (
                        <Link
                          key={post.id}
                          href={`/hub?q=${encodeURIComponent(post.disease_name)}`}
                          className="block p-3 rounded-xl bg-slate-50 hover:bg-teal-50 border border-slate-200 transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-black text-slate-900">
                              {post.disease_name}
                            </span>
                            <span className="text-[10px] text-teal-700 font-bold">
                              by {post.author_name || "Specialist"}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-600 line-clamp-1 mt-0.5">
                            {post.clinical_findings}
                          </p>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Trending Medical Hashtags Section */}
            <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🏷️</span>
                  <h2 className="text-base font-extrabold text-slate-900 tracking-tight">
                    Trending Medical Hashtags
                  </h2>
                </div>
                <span className="text-xs text-slate-400 font-bold">Real-Time Clinical Volume</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {hashtags.map((h) => (
                  <Link
                    key={h.tag}
                    href={`/hub?q=${encodeURIComponent(h.tag)}`}
                    className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/70 hover:bg-white hover:border-teal-300 hover:shadow-xs transition-all flex items-center justify-between group"
                  >
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-black text-teal-700 group-hover:text-teal-900">
                          {h.tag}
                        </span>
                        {h.has_urgent && (
                          <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" title="Active emergency consult" />
                        )}
                      </div>
                      <p className="text-[10px] text-slate-500 mt-0.5">
                        Clinical discussion topic
                      </p>
                    </div>
                    <span className="text-xs font-mono font-black text-slate-600 bg-white px-2 py-1 rounded-md border border-slate-200 shadow-2xs">
                      {h.count}
                    </span>
                  </Link>
                ))}
              </div>
            </div>

            {/* Global Verified Doctor Directory */}
            <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🌍</span>
                  <h2 className="text-base font-extrabold text-slate-900 tracking-tight">
                    Global Verified Physicians Directory
                  </h2>
                </div>
                <span className="text-xs text-teal-700 bg-teal-50 px-2.5 py-0.5 rounded-full font-bold border border-teal-100">
                  GMC • NMC • USMLE Verified
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                {doctors.map((doc) => (
                  <div
                    key={doc.id}
                    className="p-4 rounded-xl border border-slate-200 bg-white shadow-2xs flex items-center justify-between gap-3"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-slate-800 to-slate-900 text-white font-black text-sm flex items-center justify-center flex-shrink-0">
                        {doc.full_name ? doc.full_name[0].toUpperCase() : "D"}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5">
                          <p className="text-xs font-bold text-slate-900 truncate">
                            {doc.full_name}
                          </p>
                          <span className="text-teal-600 text-xs" title="Verified License">
                            ✓
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 truncate">
                          {doc.specialization || "Clinical Specialist"}
                        </p>
                        <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                          {doc.post_count || 0} cases • {doc.followers_count || 0} followers
                        </p>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleToggleFollow(doc.id)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex-shrink-0 ${
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
          </main>

          {/* ══════════════ RIGHT SIDEBAR ══════════════ */}
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

      {/* Case Composer Modal */}
      {showComposer && (
        <SocialCaseComposer
          onClose={() => setShowComposer(false)}
          onPublish={async (postData, files) => {
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
              attachment_ids: attachmentIds,
            };

            const res = await fetch("/api/v1/hub/posts", {
              method: "POST",
              headers: authHeaders({ "Content-Type": "application/json" }),
              body: JSON.stringify(payload),
            });
            if (res.ok) {
              showToast("Case published to Clinical Hub!");
              setShowComposer(false);
            }
          }}
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
