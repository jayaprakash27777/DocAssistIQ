"use client";

import React, { useState, useEffect } from "react";
import { DoctorPost } from "@/types/social";
import { TreatmentSuggestionBox } from "./TreatmentSuggestionBox";
import { CountryBadge } from "./CountryBadge";
import { CaseOutcomeModal } from "./CaseOutcomeModal";
import { CurbsideConsultDrawer } from "./CurbsideConsultDrawer";
import { GrandRoundsExportModal } from "./GrandRoundsExportModal";
import { BookmarkFolderModal } from "./BookmarkFolderModal";
import { getStoredToken } from "@/lib/api";
import {
  CheckCircle2,
  Clock,
  Printer,
  MessageSquare,
  Folder,
  Sparkles,
  Share2,
  Heart,
  Bookmark,
  MessageCircle,
  Repeat
} from "lucide-react";

interface SocialPostCardProps {
  post: DoctorPost;
  currentDoctorId?: string;
  onLike?: (postId: string) => Promise<void> | void;
  onBookmark?: (postId: string) => Promise<void> | void;
  onComment?: (postId: string, text: string) => Promise<void> | void;
  onVotePoll?: (postId: string, optionIndex: number) => Promise<void> | void;
  onAddTreatmentSuggestion?: (
    postId: string,
    data: {
      drug_or_intervention: string;
      dosage_and_route?: string;
      clinical_rationale: string;
      evidence_grade?: string;
    }
  ) => Promise<void> | void;
  onEndorseTreatmentSuggestion?: (postId: string, suggestionId: string) => Promise<void> | void;
  onAdoptTreatmentSuggestion?: (postId: string, suggestionId: string) => Promise<void> | void;
  onSelectHashtag?: (tag: string) => void;
  onHashtagClick?: (tag: string) => void;
  onOpenImage?: (url: string) => void;
  onQuotePost?: (post: DoctorPost) => void;
}

export function SocialPostCard({
  post,
  currentDoctorId,
  onLike,
  onBookmark,
  onComment,
  onVotePoll,
  onAddTreatmentSuggestion,
  onEndorseTreatmentSuggestion,
  onAdoptTreatmentSuggestion,
  onSelectHashtag,
  onHashtagClick,
  onOpenImage,
  onQuotePost,
}: SocialPostCardProps) {
  const [showComments, setShowComments] = useState(false);
  const [commentText, setCommentText] = useState("");
  const [isSubmittingComment, setIsSubmittingComment] = useState(false);
  const [showWorkup, setShowWorkup] = useState(false);
  const [shareCopied, setShareCopied] = useState(false);
  const [showOutcomeModal, setShowOutcomeModal] = useState(false);
  const [showCurbsideDrawer, setShowCurbsideDrawer] = useState(false);
  const [showGrandRoundsModal, setShowGrandRoundsModal] = useState(false);
  const [showFolderModal, setShowFolderModal] = useState(false);
  const [postOutcome, setPostOutcome] = useState<string | null>(post.patient_outcome || null);
  const [isSolved, setIsSolved] = useState<boolean>(Boolean(post.is_solved));
  const [bookmarkFolder, setBookmarkFolder] = useState<string>("General");

  // Optimistic real-time states
  const [likesCount, setLikesCount] = useState<number>(post.likes_count || 0);
  const [isLiked, setIsLiked] = useState<boolean>(Boolean(post.is_liked_by_me));
  const [isBookmarked, setIsBookmarked] = useState<boolean>(Boolean(post.is_bookmarked_by_me));
  const [commentsList, setCommentsList] = useState(post.comments || []);
  const [pollDataState, setPollDataState] = useState(post.poll_data);

  // Sync state whenever props update via WebSocket
  useEffect(() => {
    setLikesCount(post.likes_count || 0);
    setIsLiked(Boolean(post.is_liked_by_me));
    setIsBookmarked(Boolean(post.is_bookmarked_by_me));
    setCommentsList(post.comments || []);
    setPollDataState(post.poll_data);
    setPostOutcome(post.patient_outcome || null);
    setIsSolved(Boolean(post.is_solved));
  }, [post]);

  const activeDoctorId =
    currentDoctorId ||
    (typeof window !== "undefined"
      ? localStorage.getItem("doctor_id") || localStorage.getItem("user_id") || ""
      : "");
  const isAuthor = Boolean(activeDoctorId && post.author_id && activeDoctorId === post.author_id);

  const handleHashtag = onHashtagClick || onSelectHashtag || (() => {});

  const handleLike = async (id: string) => {
    const nextLiked = !isLiked;
    setIsLiked(nextLiked);
    setLikesCount((prev) => (nextLiked ? prev + 1 : Math.max(0, prev - 1)));

    if (onLike) {
      await onLike(id);
      return;
    }
    try {
      const token = getStoredToken();
      const res = await fetch(`/api/v1/hub/posts/${id}/like`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setLikesCount(data.likes_count);
        setIsLiked(data.liked);
      }
    } catch {
      setIsLiked(!nextLiked);
      setLikesCount((prev) => (!nextLiked ? prev + 1 : Math.max(0, prev - 1)));
    }
  };

  const handleBookmark = async (id: string) => {
    const nextSaved = !isBookmarked;
    setIsBookmarked(nextSaved);

    if (onBookmark) {
      await onBookmark(id);
      return;
    }
    try {
      const token = getStoredToken();
      await fetch(`/api/v1/hub/posts/${id}/bookmark`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
    } catch {
      setIsBookmarked(!nextSaved);
    }
  };

  const handleComment = async (id: string, text: string) => {
    const optimisticComment = {
      id: "temp-" + Date.now(),
      post_id: id,
      author_id: activeDoctorId,
      author_name: "You (Verified Doctor)",
      author_specialty: "Clinical Specialist",
      content: text,
      created_at: new Date().toISOString(),
    };
    setCommentsList((prev) => [...prev, optimisticComment]);

    if (onComment) {
      await onComment(id, text);
      return;
    }
    const token = getStoredToken();
    const res = await fetch(`/api/v1/hub/posts/${id}/comments`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ content: text }),
    });
    if (res.ok) {
      const savedComment = await res.json();
      setCommentsList((prev) => [
        ...prev.filter((c) => c.id !== optimisticComment.id),
        savedComment,
      ]);
    }
  };

  const handleVotePoll = async (id: string, idx: number) => {
    if (pollDataState && pollDataState.options) {
      const updatedOpts = [...pollDataState.options];
      if (updatedOpts[idx]) {
        updatedOpts[idx] = { ...updatedOpts[idx], votes: updatedOpts[idx].votes + 1 };
      }
      setPollDataState({
        ...pollDataState,
        options: updatedOpts,
        total_votes: (pollDataState.total_votes || 0) + 1,
        has_voted: true,
        voted_index: idx,
      });
    }

    if (onVotePoll) {
      await onVotePoll(id, idx);
      return;
    }
    const token = getStoredToken();
    const res = await fetch(`/api/v1/hub/posts/${id}/poll-vote`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ option_index: idx }),
    });
    if (res.ok) {
      const data = await res.json();
      if (data.options) {
        setPollDataState((prev) => ({
          question: prev?.question || "",
          options: data.options,
          total_votes: data.total_votes,
          has_voted: true,
          voted_index: data.voted_index,
        }));
      }
    }
  };

  const handleAddTreatmentSuggestion = async (id: string, data: any) => {
    if (onAddTreatmentSuggestion) return onAddTreatmentSuggestion(id, data);
    const token = getStoredToken();
    await fetch(`/api/v1/hub/posts/${id}/treatment-suggestions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(data),
    });
  };

  const handleEndorseTreatmentSuggestion = async (id: string, sId: string) => {
    if (onEndorseTreatmentSuggestion) return onEndorseTreatmentSuggestion(id, sId);
    const token = getStoredToken();
    await fetch(`/api/v1/hub/posts/${id}/treatment-suggestions/${sId}/endorse`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
  };

  const handleAdoptTreatmentSuggestion = async (id: string, sId: string) => {
    if (onAdoptTreatmentSuggestion) return onAdoptTreatmentSuggestion(id, sId);
    const token = getStoredToken();
    await fetch(`/api/v1/hub/posts/${id}/treatment-suggestions/${sId}/adopt`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
  };

  const isUrgent = Boolean(post.is_urgent_consult || post.case_status === "urgent_consult");

  const handleCommentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    setIsSubmittingComment(true);
    try {
      await handleComment(post.id, commentText.trim());
      setCommentText("");
      setShowComments(true);
    } finally {
      setIsSubmittingComment(false);
    }
  };


  return (
    <article
      className={`bg-white rounded-2xl border transition-all shadow-xs overflow-hidden ${
        isUrgent
          ? "border-rose-300 ring-2 ring-rose-100"
          : "border-slate-200/90 hover:border-slate-300"
      }`}
    >
      {/* ── STAT Emergency Top Header Banner ── */}
      {isUrgent && (
        <div className="bg-gradient-to-r from-rose-600 to-red-600 text-white px-4 py-2 flex items-center justify-between text-xs font-black tracking-wide">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-white" />
            </span>
            <span>🚨 STAT EMERGENCY 2ND OPINION NEEDED</span>
          </div>
          <span className="text-[10px] bg-white/20 px-2 py-0.5 rounded-full uppercase tracking-wider">
            Critical Review
          </span>
        </div>
      )}

      <div className="p-5 space-y-4">
        {/* ── Author Doctor Header ── */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-full bg-gradient-to-tr from-teal-700 via-teal-600 to-emerald-500 text-white font-black text-sm flex items-center justify-center shadow-xs flex-shrink-0">
              {post.author_name ? post.author_name[0].toUpperCase() : "D"}
            </div>
            <div>
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="font-extrabold text-sm text-slate-900">
                  {post.author_name || "Dr. Attending Specialist"}
                </span>
                <span className="inline-flex items-center gap-0.5 text-teal-600 font-bold text-xs" title="Verified Board License">
                  <svg className="w-4 h-4 fill-teal-600" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-[10px] text-teal-700 bg-teal-50 px-1.5 py-0.2 rounded font-semibold border border-teal-100">
                    {post.author_credentials || "Verified MD"}
                  </span>
                </span>
                <CountryBadge
                  country={post.author_country}
                  licenseBody={post.author_license_body}
                />
              </div>
              <p className="text-xs text-slate-500 font-medium">
                {post.author_specialty || "Clinical Specialist"}
                {post.author_institution && ` • ${post.author_institution}`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <span className="text-xs font-mono text-slate-400">
              {new Date(post.created_at).toLocaleDateString([], { month: 'short', day: 'numeric' })}
            </span>
          </div>
        </div>

        {/* ── Case Title & Core Presentation ── */}
        <div className="space-y-2">
          <h3 className="text-base font-extrabold text-slate-900 tracking-tight leading-snug">
            {post.disease_name}
          </h3>

          <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line font-normal">
            {post.clinical_findings}
          </p>
        </div>

        {/* ── Patient Outcome & 48h Follow-Up Resolution ── */}
        {(postOutcome || isSolved) ? (
          <div className="p-4 bg-gradient-to-r from-teal-50/90 to-emerald-50/90 rounded-2xl border border-teal-200/90 space-y-2 shadow-2xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="p-1 bg-teal-600 text-white rounded-lg">
                  <CheckCircle2 className="w-4 h-4" />
                </span>
                <div>
                  <span className="text-xs font-black text-teal-950 uppercase tracking-wide">
                    ✓ Solved Case • 48h Patient Outcome
                  </span>
                  {post.outcome_reported_at && (
                    <span className="block text-[10px] text-teal-700 font-mono">
                      Recorded {new Date(post.outcome_reported_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </span>
                  )}
                </div>
              </div>
              {isAuthor && (
                <button
                  type="button"
                  onClick={() => setShowOutcomeModal(true)}
                  className="text-[11px] font-bold text-teal-800 hover:text-teal-950 bg-teal-100 hover:bg-teal-200 px-2.5 py-1 rounded-lg transition cursor-pointer"
                >
                  Edit Outcome
                </button>
              )}
            </div>
            <p className="text-xs text-teal-900 leading-relaxed font-medium pl-7">
              {postOutcome || "Patient successfully treated and clinically stable following consensus treatment recommendations."}
            </p>
          </div>
        ) : isAuthor ? (
          <div className="px-4 py-2.5 bg-slate-50 border border-slate-200/80 rounded-xl flex items-center justify-between text-xs">
            <span className="text-slate-600 font-medium flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-amber-500" />
              Case in progress. Have 48h follow-up vitals or repeat labs?
            </span>
            <button
              type="button"
              onClick={() => setShowOutcomeModal(true)}
              className="text-xs font-bold text-teal-700 hover:text-teal-900 hover:underline cursor-pointer"
            >
              Record 48h Outcome →
            </button>
          </div>
        ) : null}

        {/* ── Diagnostic Image & Media Attachments ── */}
        {post.attachments && post.attachments.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 rounded-2xl overflow-hidden border border-slate-200">
            {post.attachments.map((att) => (
              <div
                key={att.id}
                onClick={() => onOpenImage && onOpenImage(att.file_url)}
                className="relative bg-slate-100 aspect-video flex items-center justify-center cursor-pointer group overflow-hidden"
              >
                <img
                  src={att.file_url}
                  alt="Clinical Diagnostic Scan"
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
                <div className="absolute inset-0 bg-slate-900/10 group-hover:bg-transparent transition-colors" />
                <span className="absolute bottom-2 right-2 text-[10px] font-bold bg-slate-900/70 text-white px-2 py-0.5 rounded-md backdrop-blur-xs">
                  🔍 View High-Res
                </span>
              </div>

            ))}
          </div>
        )}

        {/* ── Collapsible Clinical Workup & Diagnosis Details ── */}
        <div className="border border-slate-200/90 rounded-2xl overflow-hidden bg-slate-50/60">
          <button
            type="button"
            onClick={() => setShowWorkup(!showWorkup)}
            className="w-full px-4 py-2.5 flex items-center justify-between text-xs font-extrabold text-slate-800 hover:bg-slate-100/60 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <span className="text-teal-600">📋</span>
              <span>Clinical Assessment, Diagnosis & Current Rx</span>
            </div>
            <span className="text-slate-400 font-mono text-[11px]">
              {showWorkup ? "▲ Hide" : "▼ Review"}
            </span>
          </button>

          {showWorkup && (
            <div className="p-4 pt-1 border-t border-slate-200/80 space-y-2.5 text-xs text-slate-700 bg-white">
              <div>
                <span className="font-bold text-slate-900 uppercase tracking-wider text-[10px] block mb-0.5">
                  Diagnosis:
                </span>
                <p className="font-semibold text-slate-800">{post.diagnosis}</p>
              </div>

              <div>
                <span className="font-bold text-slate-900 uppercase tracking-wider text-[10px] block mb-0.5">
                  Current Management / Plan:
                </span>
                <p className="leading-relaxed">{post.treatment_plan}</p>
              </div>

              {post.drugs_used && post.drugs_used.length > 0 && (
                <div>
                  <span className="font-bold text-slate-900 uppercase tracking-wider text-[10px] block mb-1">
                    Medications Administered:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {post.drugs_used.map((drug) => (
                      <span
                        key={drug}
                        className="px-2 py-0.5 bg-teal-50 text-teal-800 rounded-md font-mono text-[11px] font-semibold border border-teal-200/80"
                      >
                        {drug}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── Specialty Tags & Trending Hashtags ── */}
        {post.specialty_tags && post.specialty_tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {post.specialty_tags.map((tag) => {
              const displayTag = tag.startsWith("#") ? tag : `#${tag.replace(/\s+/g, "")}`;
              return (
                <button
                  key={tag}
                  type="button"
                  onClick={() => handleHashtag(displayTag)}
                  className="text-xs font-bold text-teal-700 hover:text-teal-900 hover:bg-teal-50 px-2.5 py-1 rounded-lg transition-colors cursor-pointer"
                >
                  {displayTag}
                </button>
              );
            })}
          </div>
        )}

        {/* ── Interactive Dilemma Consensus Poll ── */}
        {pollDataState && pollDataState.options && pollDataState.options.length > 0 && (
          <div className="p-4 bg-slate-50/80 rounded-2xl border border-slate-200/90 space-y-2.5">
            <h4 className="text-xs font-extrabold text-slate-900 flex items-center gap-1.5">
              <span>🗳️ Clinical Consensus Poll:</span>
              <span className="font-normal text-slate-700">{pollDataState.question}</span>
            </h4>
            <div className="space-y-1.5">
              {pollDataState.options.map((opt, idx) => {
                const total = pollDataState?.total_votes || 1;
                const pct = Math.round((opt.votes / total) * 100);
                const hasVotedThis = pollDataState?.voted_index === idx;

                return (
                  <button
                    key={opt.label}
                    type="button"
                    onClick={() => handleVotePoll(post.id, idx)}
                    className={`w-full text-left p-2.5 rounded-xl border relative overflow-hidden transition-all cursor-pointer ${
                      hasVotedThis
                        ? "border-teal-500 bg-teal-50/50 ring-1 ring-teal-400"
                        : "border-slate-200 bg-white hover:border-slate-300"
                    }`}
                  >
                    <div
                      className="absolute inset-y-0 left-0 bg-teal-100/60 transition-all duration-500"
                      style={{ width: `${pct}%` }}
                    />
                    <div className="relative flex items-center justify-between text-xs font-bold text-slate-800 z-10">
                      <span>{opt.label}</span>
                      <span className="font-mono text-[11px] text-teal-800 font-black">{pct}%</span>
                    </div>
                  </button>
                );
              })}
            </div>
            <p className="text-[10px] text-slate-400 font-medium text-right">
              {pollDataState.total_votes} verified physician votes
            </p>
          </div>
        )}

        {/* ── Peer Treatment Suggestions Box (Real Database) ── */}
        <TreatmentSuggestionBox
          postId={post.id}
          postAuthorId={post.author_id}
          currentDoctorId={activeDoctorId}
          suggestions={post.treatment_suggestions || []}
          onAddSuggestion={handleAddTreatmentSuggestion}
          onEndorseSuggestion={handleEndorseTreatmentSuggestion}
          onAdoptSuggestion={handleAdoptTreatmentSuggestion}
        />

        {/* ── Social Action Bar (Twitter / Bluesky style) ── */}
        <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-slate-500 text-xs font-bold">
          {/* Endorse / Like */}
          <button
            type="button"
            onClick={() => handleLike(post.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-colors cursor-pointer ${
              isLiked
                ? "text-rose-600 bg-rose-50"
                : "hover:bg-slate-100 hover:text-slate-800"
            }`}
          >
            <span>{isLiked ? "❤️" : "🤍"}</span>
            <span>{likesCount}</span>
          </button>

          {/* Comments */}
          <button
            type="button"
            onClick={() => setShowComments(!showComments)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl hover:bg-slate-100 hover:text-slate-800 transition-colors cursor-pointer"
          >
            <span>💬</span>
            <span>{commentsList.length}</span>
          </button>

          {/* Quote / Repost */}
          {onQuotePost && (
            <button
              type="button"
              onClick={() => onQuotePost(post)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl hover:bg-slate-100 hover:text-slate-800 transition-colors cursor-pointer"
            >
              <span>🔁</span>
              <span>Quote</span>
            </button>
          )}

          {/* Curbside 1-on-1 Consult */}
          <button
            type="button"
            onClick={() => setShowCurbsideDrawer(true)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl hover:bg-teal-50 hover:text-teal-700 transition-colors cursor-pointer text-slate-600"
            title={`Start private Curbside Consult with Dr. ${post.author_name || "Specialist"}`}
          >
            <MessageSquare className="w-3.5 h-3.5 text-teal-600" />
            <span>Curbside</span>
          </button>

          {/* Grand Rounds Print / PDF */}
          <button
            type="button"
            onClick={() => setShowGrandRoundsModal(true)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl hover:bg-slate-100 hover:text-slate-800 transition-colors cursor-pointer text-slate-600"
            title="Export Case for Hospital Grand Rounds or Clinical Audit"
          >
            <Printer className="w-3.5 h-3.5 text-slate-500" />
            <span>Grand Rounds</span>
          </button>

          {/* Bookmark & Folder */}
          <div className="flex items-center">
            <button
              type="button"
              onClick={() => handleBookmark(post.id)}
              className={`flex items-center gap-1 px-2.5 py-1.5 rounded-xl transition-colors cursor-pointer ${
                isBookmarked
                  ? "text-amber-600 bg-amber-50"
                  : "hover:bg-slate-100 hover:text-slate-800"
              }`}
            >
              <span>{isBookmarked ? "🔖" : "🏷️"}</span>
              <span>{isBookmarked ? "Saved" : "Save"}</span>
            </button>
            {isBookmarked && (
              <button
                type="button"
                onClick={() => setShowFolderModal(true)}
                className="p-1 text-slate-400 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition-colors cursor-pointer"
                title="Organize into Case Folder"
              >
                <Folder className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Share Case Link */}
          <button
            type="button"
            onClick={() => {
              if (typeof window !== "undefined") {
                const url = `${window.location.origin}/hub?q=${encodeURIComponent(post.disease_name)}`;
                navigator.clipboard.writeText(url);
                setShareCopied(true);
                setTimeout(() => setShareCopied(false), 2000);
              }
            }}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl hover:bg-slate-100 hover:text-slate-800 transition-colors cursor-pointer text-slate-500"
            title="Copy clinical case link"
          >
            <span>{shareCopied ? "✓" : "↗️"}</span>
            <span>{shareCopied ? "Copied" : "Share"}</span>
          </button>
        </div>



        {/* ── Expandable Peer Comments Discussion Thread ── */}
        {showComments && (
          <div className="pt-3 border-t border-slate-100 space-y-3">
            {/* Input Form */}
            <form onSubmit={handleCommentSubmit} className="flex gap-2">
              <input
                type="text"
                required
                placeholder="Write clinical peer review consultation..."
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                className="flex-1 px-3.5 py-2 rounded-xl border border-slate-300 text-xs text-slate-900 bg-white outline-none focus:border-teal-600 shadow-2xs"
              />
              <button
                type="submit"
                disabled={isSubmittingComment || !commentText.trim()}
                className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold transition-all disabled:opacity-50 cursor-pointer shadow-xs"
              >
                {isSubmittingComment ? "Posting..." : "Reply"}
              </button>
            </form>

            {/* Comments List */}
            {commentsList && commentsList.length > 0 ? (
              <div className="space-y-2 pt-1">
                {commentsList.map((c) => (
                  <div key={c.id} className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-1.5 font-bold text-slate-900">
                        <span>{c.author_name || "Dr. Colleague"}</span>
                        <span className="text-[10px] text-teal-600">✓ {c.author_specialty || "Specialist"}</span>
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p className="text-slate-700 leading-relaxed">{c.content}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No comments yet. Start the clinical discussion.</p>
            )}
          </div>
        )}
      </div>

      {/* ── Modals & Drawers ── */}
      {showOutcomeModal && (
        <CaseOutcomeModal
          postId={post.id}
          diseaseName={post.disease_name}
          currentOutcome={postOutcome}
          onClose={() => setShowOutcomeModal(false)}
          onOutcomeUpdated={(outcome, solved) => {
            setPostOutcome(outcome);
            setIsSolved(solved);
          }}
        />
      )}

      {showCurbsideDrawer && (
        <CurbsideConsultDrawer
          postId={post.id}
          caseTitle={post.disease_name}
          authorDoctorId={post.author_id}
          authorDoctorName={post.author_name || "Dr. Attending Specialist"}
          authorSpecialty={post.author_specialty || "Clinical Specialist"}
          onClose={() => setShowCurbsideDrawer(false)}
        />
      )}

      {showGrandRoundsModal && (
        <GrandRoundsExportModal
          post={{ ...post, patient_outcome: postOutcome, is_solved: isSolved }}
          onClose={() => setShowGrandRoundsModal(false)}
        />
      )}

      {showFolderModal && (
        <BookmarkFolderModal
          postId={post.id}
          currentFolder={bookmarkFolder}
          onClose={() => setShowFolderModal(false)}
          onFolderUpdated={(folder) => setBookmarkFolder(folder)}
        />
      )}
    </article>
  );
}

export default SocialPostCard;
