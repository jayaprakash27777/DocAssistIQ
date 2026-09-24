/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable react/no-unescaped-entities */
"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { motion, AnimatePresence } from "framer-motion";
import { getStoredToken } from "@/lib/api";

// ─── Types ─────────────────────────────────────────────────────────────────────

interface PostAttachment {
  id: string;
  file_url: string;
  file_type: string;
}

interface PostComment {
  id: string;
  author_id: string;
  content: string;
  created_at: string;
}

interface DoctorPost {
  id: string;
  author_id: string;
  disease_name: string;
  clinical_findings: string;
  diagnosis: string;
  treatment_plan: string;
  drugs_used: string[];
  specialty_tags: string[];
  likes_count: number;
  comments_count: number;
  is_liked_by_me: boolean;
  is_bookmarked_by_me: boolean;
  created_at: string;
  attachments: PostAttachment[];
  comments: PostComment[];
}

interface TrendingData {
  trending_diseases: { name: string; post_count: number }[];
  trending_tags: { tag: string; count: number }[];
  posts_this_week: number;
}

interface DoctorProfile {
  id: string;
  full_name: string;
  specialization: string;
  verification_status: string;
  post_count: number;
}

// ─── Constants ─────────────────────────────────────────────────────────────────

const ALL_SPECIALTIES = [
  "Cardiology", "Neurology", "Oncology", "Pediatrics",
  "Orthopedics", "Dermatology", "Gastroenterology", "Endocrinology",
  "Pulmonology", "Nephrology", "Hematology", "Rheumatology",
  "Infectious Disease", "Emergency Medicine", "Internal Medicine",
];

const SPECIALTY_COLORS: Record<string, string> = {
  Cardiology: "bg-red-100 text-red-700 border-red-200",
  Neurology: "bg-purple-100 text-purple-700 border-purple-200",
  Oncology: "bg-orange-100 text-orange-700 border-orange-200",
  Pediatrics: "bg-pink-100 text-pink-700 border-pink-200",
  default: "bg-blue-100 text-blue-700 border-blue-200",
};

const getSpecialtyColor = (tag: string) =>
  SPECIALTY_COLORS[tag] ?? SPECIALTY_COLORS.default;

// ─── Utilities ─────────────────────────────────────────────────────────────────

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d < 7) return `${d}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

function getInitials(authorId: string): string {
  return authorId.substring(0, 2).toUpperCase();
}

function getAvatarGradient(authorId: string): string {
  const gradients = [
    "from-blue-500 to-indigo-600",
    "from-emerald-500 to-teal-600",
    "from-violet-500 to-purple-600",
    "from-rose-500 to-pink-600",
    "from-amber-500 to-orange-600",
    "from-cyan-500 to-sky-600",
  ];
  const idx = authorId.charCodeAt(0) % gradients.length;
  return gradients[idx];
}

// ─── Post Card Component ────────────────────────────────────────────────────────

function PostCard({
  post,
  onLike,
  onBookmark,
  onComment,
  onExpand,
  selectedImage,
  setSelectedImage,
}: {
  post: DoctorPost;
  onLike: () => void;
  onBookmark: () => void;
  onComment: (text: string) => void;
  onExpand: () => void;
  selectedImage: string | null;
  setSelectedImage: (url: string | null) => void;
}) {
  const [showComments, setShowComments] = useState(false);
  const [commentText, setCommentText] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);
  const gradient = getAvatarGradient(post.author_id);

  const handleComment = () => {
    if (!commentText.trim()) return;
    onComment(commentText.trim());
    setCommentText("");
  };

  const truncatedFindings = post.clinical_findings.length > 180
    ? post.clinical_findings.substring(0, 180) + "..."
    : post.clinical_findings;

  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-[var(--surface-secondary)] border border-[var(--border-default)] rounded-2xl overflow-hidden shadow-sm hover:shadow-lg hover:border-[var(--color-primary-300)]/40 transition-all duration-300 group"
    >
      {/* Top accent bar */}
      <div className="h-0.5 bg-gradient-to-r from-[var(--color-primary-400)] via-[var(--color-info-400)] to-[var(--color-primary-600)]" />

      <div className="p-5">
        {/* Author row */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-11 h-11 bg-gradient-to-br ${gradient} rounded-full flex items-center justify-center text-white font-bold text-sm shadow-sm ring-2 ring-white`}>
              {getInitials(post.author_id)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="font-bold text-[var(--text-primary)] text-sm">
                  Dr. {post.author_id.substring(0, 8)}
                </h4>
                <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded-full">
                  <svg className="w-2.5 h-2.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                  </svg>
                  Verified
                </span>
              </div>
              <p className="text-[10px] text-[var(--text-tertiary)] font-medium">{timeAgo(post.created_at)}</p>
            </div>
          </div>

          <div className="flex items-center gap-1">
            {/* Bookmark */}
            <motion.button
              whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}
              onClick={onBookmark}
              className={`p-2 rounded-full transition-all ${post.is_bookmarked_by_me ? "bg-amber-50 text-amber-500" : "text-[var(--text-tertiary)] hover:bg-[var(--surface-sunken)]"}`}
            >
              <svg className="w-4 h-4" fill={post.is_bookmarked_by_me ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
              </svg>
            </motion.button>
          </div>
        </div>

        {/* Specialty tags */}
        {post.specialty_tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {post.specialty_tags.slice(0, 4).map((tag, i) => (
              <span key={i} className={`text-[10px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider ${getSpecialtyColor(tag)}`}>
                #{tag}
              </span>
            ))}
          </div>
        )}

        {/* Disease title */}
        <h2 className="text-lg font-extrabold text-[var(--text-primary)] mb-3 leading-tight">
          {post.disease_name}
        </h2>

        {/* Clinical content */}
        <div className="space-y-3 mb-4">
          <div className="bg-[var(--surface-sunken)] rounded-xl p-3.5 border border-[var(--border-default)]">
            <p className="text-[10px] font-black text-[var(--text-tertiary)] uppercase tracking-widest mb-1.5 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400 inline-block" />
              Clinical Findings
            </p>
            <p className="text-xs text-[var(--text-primary)] leading-relaxed font-medium">
              {isExpanded ? post.clinical_findings : truncatedFindings}
            </p>
          </div>

          {(isExpanded) && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
              <div className="bg-[var(--surface-sunken)] rounded-xl p-3.5 border border-[var(--border-default)]">
                <p className="text-[10px] font-black text-[var(--text-tertiary)] uppercase tracking-widest mb-1.5 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
                  Diagnosis
                </p>
                <p className="text-xs text-[var(--text-primary)] leading-relaxed font-medium">{post.diagnosis}</p>
              </div>

              <div className="bg-gradient-to-r from-[var(--color-primary-50)] to-[var(--surface-secondary)] rounded-xl p-3.5 border border-[var(--color-primary-200)] relative overflow-hidden">
                <div className="absolute left-0 top-0 w-1 h-full bg-[var(--color-primary-500)]" />
                <p className="text-[10px] font-black text-[var(--color-primary-600)] uppercase tracking-widest mb-1.5 ml-2">
                  Treatment Protocol
                </p>
                <p className="text-xs text-[var(--text-primary)] leading-relaxed font-medium ml-2">{post.treatment_plan}</p>

                {post.drugs_used.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-[var(--color-primary-200)]/50 ml-2">
                    <p className="text-[9px] font-bold text-[var(--color-primary-700)] uppercase tracking-wider mb-1.5">Pharmacology:</p>
                    <div className="flex flex-wrap gap-1.5">
                      {post.drugs_used.map((drug, i) => (
                        <span key={i} className="text-xs font-bold bg-white text-[var(--color-primary-700)] px-2.5 py-1 rounded-lg border border-[var(--color-primary-200)] shadow-sm">
                          {drug}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </div>

        {/* Expand / Collapse */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-xs font-bold text-[var(--color-primary-500)] hover:text-[var(--color-primary-700)] mb-4 transition-colors flex items-center gap-1"
        >
          {isExpanded ? "▲ Collapse" : "▼ Read Full Case"}
        </button>

        {/* Attachments */}
        {post.attachments?.length > 0 && (
          <div className="mb-4 flex gap-2 overflow-x-auto pb-1">
            {post.attachments.map(att => (
              <motion.div
                whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                key={att.id}
                onClick={() => setSelectedImage(att.file_url)}
                className="min-w-[120px] h-[90px] bg-[var(--surface-sunken)] rounded-xl border border-[var(--border-default)] overflow-hidden relative cursor-pointer group/img flex-shrink-0"
              >
                {att.file_type.includes("image") ? (
                  <img src={att.file_url} alt="Clinical" className="w-full h-full object-cover group-hover/img:scale-105 transition-transform duration-300" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-[var(--text-tertiary)]">
                    <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                )}
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/img:opacity-100 transition-opacity flex items-center justify-center">
                  <span className="text-white text-[10px] font-bold">View</span>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Action bar */}
      <div className="px-5 py-3 bg-[var(--surface-sunken)] border-t border-[var(--border-default)] flex items-center justify-between">
        <div className="flex items-center gap-5">
          {/* Like */}
          <motion.button
            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.9 }}
            onClick={onLike}
            className={`flex items-center gap-1.5 text-sm font-bold transition-all ${post.is_liked_by_me ? "text-[var(--color-primary-600)]" : "text-[var(--text-tertiary)] hover:text-[var(--color-primary-500)]"}`}
          >
            <motion.svg
              animate={post.is_liked_by_me ? { scale: [1, 1.4, 1] } : {}}
              className="w-5 h-5"
              fill={post.is_liked_by_me ? "currentColor" : "none"}
              viewBox="0 0 24 24" stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={post.is_liked_by_me ? 0 : 2}
                d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
            </motion.svg>
            <span>{post.likes_count}</span>
          </motion.button>

          {/* Comment */}
          <button
            onClick={() => setShowComments(!showComments)}
            className="flex items-center gap-1.5 text-sm font-bold text-[var(--text-tertiary)] hover:text-[var(--color-primary-500)] transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <span>{post.comments_count} peer reviews</span>
          </button>
        </div>

        {/* AI Knowledge badge */}
        <span className="text-[10px] font-bold text-violet-600 bg-violet-50 border border-violet-200 px-2 py-0.5 rounded-full flex items-center gap-1">
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 2a8 8 0 100 16A8 8 0 0010 2zm0 14a6 6 0 110-12 6 6 0 010 12zm-1-5a1 1 0 112 0v3a1 1 0 11-2 0v-3zm0-4a1 1 0 112 0 1 1 0 01-2 0z"/>
          </svg>
          AI Knowledge
        </span>
      </div>

      {/* Comments section */}
      <AnimatePresence>
        {showComments && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-[var(--border-default)] overflow-hidden"
          >
            <div className="p-4 space-y-3">
              {post.comments.map(c => (
                <div key={c.id} className="flex gap-2.5">
                  <div className={`w-7 h-7 bg-gradient-to-br ${getAvatarGradient(c.author_id)} rounded-full flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0`}>
                    {getInitials(c.author_id)}
                  </div>
                  <div className="bg-[var(--surface-sunken)] rounded-xl px-3 py-2 flex-1">
                    <p className="text-[10px] font-bold text-[var(--text-secondary)] mb-0.5">
                      Dr. {c.author_id.substring(0, 8)} · {timeAgo(c.created_at)}
                    </p>
                    <p className="text-xs text-[var(--text-primary)]">{c.content}</p>
                  </div>
                </div>
              ))}

              {post.comments_count > 3 && (
                <button className="text-xs font-bold text-[var(--color-primary-500)] hover:underline">
                  View all {post.comments_count} peer reviews →
                </button>
              )}

              <div className="flex gap-2 mt-2">
                <input
                  type="text"
                  value={commentText}
                  onChange={e => setCommentText(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && handleComment()}
                  placeholder="Add a peer review or clinical insight..."
                  className="flex-1 bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-full px-4 py-2 text-xs outline-none focus:ring-2 focus:ring-[var(--color-primary-400)] text-[var(--text-primary)]"
                />
                <button
                  onClick={handleComment}
                  disabled={!commentText.trim()}
                  className="px-4 py-2 bg-[var(--color-primary-500)] hover:bg-[var(--color-primary-600)] disabled:opacity-40 text-white text-xs font-bold rounded-full transition-all"
                >
                  Post
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.article>
  );
}

// ─── Story Ring Component ───────────────────────────────────────────────────────

function StoryRing({ post, onClick }: { post: DoctorPost; onClick: () => void }) {
  const gradient = getAvatarGradient(post.author_id);
  return (
    <motion.button
      whileHover={{ scale: 1.06 }}
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      className="flex flex-col items-center gap-1.5 min-w-[72px]"
    >
      <div className="p-0.5 rounded-full bg-gradient-to-tr from-[var(--color-primary-400)] via-[var(--color-info-400)] to-[var(--color-primary-600)]">
        <div className={`w-14 h-14 bg-gradient-to-br ${gradient} rounded-full flex items-center justify-center text-white font-bold text-sm border-2 border-white`}>
          {getInitials(post.author_id)}
        </div>
      </div>
      <span className="text-[9px] text-[var(--text-secondary)] font-bold max-w-[68px] truncate text-center">
        {post.disease_name.length > 12 ? post.disease_name.substring(0, 12) + "…" : post.disease_name}
      </span>
    </motion.button>
  );
}

// ─── Main Hub Page ─────────────────────────────────────────────────────────────

export default function KnowledgeHub() {
  const { user } = useAuth();
  const [posts, setPosts] = useState<DoctorPost[]>([]);
  const [stories, setStories] = useState<DoctorPost[]>([]);
  const [trending, setTrending] = useState<TrendingData | null>(null);
  const [suggestedDoctors, setSuggestedDoctors] = useState<DoctorProfile[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterSpecialty, setFilterSpecialty] = useState("");
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"recent" | "trending">("recent");
  const [isSearching, setIsSearching] = useState(false);
  const [loadingFeed, setLoadingFeed] = useState(true);

  // Case Creation State
  const [newPost, setNewPost] = useState({
    disease_name: "",
    specialty_tags: "",
    clinical_findings: "",
    diagnosis: "",
    treatment_plan: "",
    drugs_used: "",
  });
  const [files, setFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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

  const fetchPosts = useCallback(async (search?: string, specialty?: string, tab?: "recent" | "trending") => {
    setLoadingFeed(true);
    try {
      let url = search
        ? `/api/v1/hub/search?q=${encodeURIComponent(search)}`
        : `/api/v1/hub/feed?sort_by=${tab ?? activeTab}`;
      if (!search && specialty) url += `&specialty=${encodeURIComponent(specialty)}`;

      const res = await fetch(url, { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        setPosts(data);
      }
    } catch (error) {
      console.error("Failed to load feed", error);
    } finally {
      setLoadingFeed(false);
    }
  }, [activeTab]);

  const fetchStories = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/hub/stories", { headers: authHeaders() });
      if (res.ok) setStories(await res.json());
    } catch {}
  }, []);

  const fetchTrending = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/hub/trending", { headers: authHeaders() });
      if (res.ok) setTrending(await res.json());
    } catch {}
  }, []);

  const fetchExploreDoctors = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/hub/explore", { headers: authHeaders() });
      if (res.ok) setSuggestedDoctors(await res.json());
    } catch {}
  }, []);

  useEffect(() => {
    fetchPosts();
    fetchStories();
    fetchTrending();
    fetchExploreDoctors();

    // WebSocket for live updates
    const authToken = token();
    if (!authToken) return;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/v1/stream?token=${authToken}`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "hub_new_post") setPosts(prev => [msg.payload, ...prev]);
        if (msg.type === "hub_post_liked") {
          setPosts(prev => prev.map(p => p.id === msg.payload.post_id
            ? { ...p, likes_count: msg.payload.likes_count } : p));
        }
        if (msg.type === "hub_new_comment") {
          setPosts(prev => prev.map(p => p.id === msg.payload.post_id
            ? { ...p, comments_count: msg.payload.comments_count } : p));
        }
      } catch {}
    };

    return () => ws.close();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Search debounce
  useEffect(() => {
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    if (searchQuery.length >= 2) {
      setIsSearching(true);
      searchTimeoutRef.current = setTimeout(() => {
        fetchPosts(searchQuery);
        setIsSearching(false);
      }, 400);
    } else if (searchQuery.length === 0) {
      fetchPosts(undefined, filterSpecialty, activeTab);
    }
    return () => { if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery]);

  // Tab / specialty filter change
  useEffect(() => {
    if (!searchQuery) fetchPosts(undefined, filterSpecialty, activeTab);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, filterSpecialty]);

  const uploadFiles = async (): Promise<string[]> => {
    const attachmentIds: string[] = [];
    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("metadata", JSON.stringify({ category: "clinical_imaging" }));
      const res = await fetch("/api/v1/files/upload", {
        method: "POST",
        headers: authHeaders(),
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        attachmentIds.push(data.file_id);
      }
    }
    return attachmentIds;
  };

  const handlePostSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUploading(true);
    try {
      const attachmentIds = await uploadFiles();
      const payload = {
        ...newPost,
        drugs_used: newPost.drugs_used.split(",").map(d => d.trim()).filter(Boolean),
        specialty_tags: newPost.specialty_tags.split(",").map(s => s.trim()).filter(Boolean),
        attachment_ids: attachmentIds
      };
      const res = await fetch("/api/v1/hub/posts", {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setIsCreating(false);
        setNewPost({ disease_name: "", specialty_tags: "", clinical_findings: "", diagnosis: "", treatment_plan: "", drugs_used: "" });
        setFiles([]);
        fetchPosts();
      }
    } catch (error) {
      console.error("Failed to create post", error);
    } finally {
      setIsUploading(false);
    }
  };

  const toggleLike = async (postId: string, currentState: boolean) => {
    // Optimistic update
    setPosts(prev => prev.map(p => p.id === postId
      ? { ...p, is_liked_by_me: !currentState, likes_count: currentState ? p.likes_count - 1 : p.likes_count + 1 }
      : p
    ));
    try {
      await fetch(`/api/v1/hub/posts/${postId}/like`, {
        method: "POST", headers: authHeaders()
      });
    } catch {}
  };

  const toggleBookmark = async (postId: string, currentState: boolean) => {
    setPosts(prev => prev.map(p => p.id === postId ? { ...p, is_bookmarked_by_me: !currentState } : p));
    try {
      await fetch(`/api/v1/hub/posts/${postId}/bookmark`, {
        method: "POST", headers: authHeaders()
      });
    } catch {}
  };

  const addComment = async (postId: string, content: string) => {
    try {
      await fetch(`/api/v1/hub/posts/${postId}/comments`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ content })
      });
      fetchPosts();
    } catch {}
  };

  if (!user?.is_verified) {
    return (
      <div className="flex items-center justify-center h-full bg-[var(--surface-primary)]">
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="p-10 text-center bg-[var(--surface-secondary)] backdrop-blur-md rounded-2xl shadow-xl border border-[var(--border-default)] max-w-md">
          <div className="w-20 h-20 bg-gradient-to-tr from-[var(--color-danger-500)] to-[var(--color-warning-500)] text-white rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
            <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-3xl font-bold font-heading text-[var(--text-primary)] mb-3">Verification Required</h2>
          <p className="text-[var(--text-secondary)] text-lg leading-relaxed">
            The Clinical Hub is an exclusive peer network for verified physicians. Complete verification to access.
          </p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-[var(--surface-primary)]">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* ── 3-Column Layout ── */}
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr_280px] gap-6">

          {/* ── LEFT SIDEBAR ── */}
          <aside className="hidden lg:block space-y-5">
            {/* Profile Card */}
            <div className="bg-[var(--surface-secondary)] rounded-2xl border border-[var(--border-default)] overflow-hidden shadow-sm">
              <div className="h-16 bg-gradient-to-r from-[var(--color-primary-500)] to-[var(--color-primary-700)]" />
              <div className="px-4 pb-4 -mt-7">
                <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full border-3 border-white flex items-center justify-center text-white font-bold text-lg shadow-md mb-2">
                  {(user?.email?.[0] ?? "D").toUpperCase()}
                </div>
                <h3 className="font-bold text-[var(--text-primary)] text-sm">Dr. {user?.email?.split("@")[0] ?? "Physician"}</h3>
                <p className="text-xs text-[var(--text-tertiary)]">Verified Specialist</p>
                <div className="mt-3 flex justify-around text-center border-t border-[var(--border-default)] pt-3">
                  <div><p className="font-bold text-[var(--text-primary)] text-sm">{posts.filter(p => p.author_id === user?.id).length}</p><p className="text-[10px] text-[var(--text-tertiary)]">Posts</p></div>
                  <div><p className="font-bold text-[var(--text-primary)] text-sm">—</p><p className="text-[10px] text-[var(--text-tertiary)]">Followers</p></div>
                  <div><p className="font-bold text-[var(--text-primary)] text-sm">—</p><p className="text-[10px] text-[var(--text-tertiary)]">Following</p></div>
                </div>
              </div>
            </div>

            {/* Trending Tags */}
            {trending && (
              <div className="bg-[var(--surface-secondary)] rounded-2xl border border-[var(--border-default)] p-4 shadow-sm">
                <h3 className="font-bold text-[var(--text-primary)] text-sm mb-3 flex items-center gap-2">
                  <span className="text-orange-500">🔥</span> Trending This Week
                </h3>
                <div className="space-y-2">
                  {trending.trending_diseases.slice(0, 6).map((d, i) => (
                    <button
                      key={i}
                      onClick={() => setSearchQuery(d.name)}
                      className="w-full flex items-center justify-between group hover:bg-[var(--surface-sunken)] rounded-lg px-2 py-1.5 transition-colors"
                    >
                      <div className="text-left">
                        <p className="text-[11px] text-[var(--text-tertiary)] font-medium">#{i + 1} trending</p>
                        <p className="text-xs font-bold text-[var(--text-primary)] group-hover:text-[var(--color-primary-500)] transition-colors">{d.name}</p>
                      </div>
                      <span className="text-[10px] text-[var(--text-tertiary)]">{d.post_count} posts</span>
                    </button>
                  ))}
                </div>
                <div className="mt-3 pt-3 border-t border-[var(--border-default)]">
                  <p className="text-[10px] text-[var(--text-tertiary)] mb-2 font-bold uppercase tracking-wider">Specialty Tags</p>
                  <div className="flex flex-wrap gap-1.5">
                    {trending.trending_tags.slice(0, 8).map((t, i) => (
                      <button
                        key={i}
                        onClick={() => setFilterSpecialty(t.tag)}
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getSpecialtyColor(t.tag)} hover:opacity-80 transition-opacity`}
                      >
                        #{t.tag}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Specialty Filter */}
            <div className="bg-[var(--surface-secondary)] rounded-2xl border border-[var(--border-default)] p-4 shadow-sm">
              <h3 className="font-bold text-[var(--text-primary)] text-sm mb-3">Browse by Specialty</h3>
              <div className="space-y-1">
                <button
                  onClick={() => setFilterSpecialty("")}
                  className={`w-full text-left text-xs px-3 py-2 rounded-lg font-medium transition-all ${!filterSpecialty ? "bg-[var(--color-primary-500)] text-white" : "text-[var(--text-secondary)] hover:bg-[var(--surface-sunken)]"}`}
                >
                  All Specialties
                </button>
                {ALL_SPECIALTIES.map(spec => (
                  <button
                    key={spec}
                    onClick={() => setFilterSpecialty(spec === filterSpecialty ? "" : spec)}
                    className={`w-full text-left text-xs px-3 py-2 rounded-lg font-medium transition-all ${filterSpecialty === spec ? "bg-[var(--color-primary-500)] text-white" : "text-[var(--text-secondary)] hover:bg-[var(--surface-sunken)]"}`}
                  >
                    {spec}
                  </button>
                ))}
              </div>
            </div>
          </aside>

          {/* ── CENTER FEED ── */}
          <main className="min-w-0">
            {/* Sticky Header */}
            <div className="sticky top-0 z-20 bg-[var(--surface-primary)]/90 backdrop-blur-xl pb-4 mb-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h1 className="text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-[var(--color-primary-600)] to-[var(--color-primary-400)]">
                    Clinical Hub
                  </h1>
                  <p className="text-xs text-[var(--text-tertiary)]">
                    Peer knowledge • {trending?.posts_this_week ?? 0} cases this week
                  </p>
                </div>
                <motion.button
                  whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }}
                  onClick={() => setIsCreating(true)}
                  className="bg-gradient-to-r from-[var(--color-primary-500)] to-[var(--color-primary-600)] text-white px-5 py-2.5 rounded-full font-bold shadow-lg text-sm flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Share Case
                </motion.button>
              </div>

              {/* Search */}
              <div className="relative">
                <svg className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  placeholder="Search diseases, drugs, findings..."
                  className="w-full pl-10 pr-4 py-2.5 rounded-full border border-[var(--border-default)] bg-[var(--surface-secondary)] outline-none focus:ring-2 focus:ring-[var(--color-primary-400)] text-sm text-[var(--text-primary)]"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                />
                {isSearching && (
                  <div className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 border-2 border-[var(--color-primary-400)] border-t-transparent rounded-full animate-spin" />
                )}
              </div>

              {/* Tabs */}
              {!searchQuery && (
                <div className="flex gap-1 mt-3 border-b border-[var(--border-default)]">
                  {(["recent", "trending"] as const).map(tab => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`px-4 py-2 text-sm font-bold capitalize transition-all border-b-2 -mb-px ${activeTab === tab ? "border-[var(--color-primary-500)] text-[var(--color-primary-500)]" : "border-transparent text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"}`}
                    >
                      {tab === "recent" ? "🕐 Recent" : "🔥 Trending"}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Stories Row */}
            {stories.length > 0 && !searchQuery && (
              <div className="mb-5 bg-[var(--surface-secondary)] border border-[var(--border-default)] rounded-2xl p-4 shadow-sm">
                <p className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-wider mb-3">Top Cases Today</p>
                <div className="flex gap-4 overflow-x-auto pb-1 custom-scrollbar">
                  {stories.map(post => (
                    <StoryRing
                      key={post.id}
                      post={post}
                      onClick={() => setSearchQuery(post.disease_name)}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Create Post Modal */}
            <AnimatePresence>
              {isCreating && (
                <motion.div
                  initial={{ opacity: 0, y: -20, height: 0 }}
                  animate={{ opacity: 1, y: 0, height: "auto" }}
                  exit={{ opacity: 0, scale: 0.95, height: 0 }}
                  className="mb-6 bg-[var(--surface-secondary)] border border-[var(--border-default)] shadow-xl rounded-2xl overflow-hidden relative"
                >
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-[var(--color-primary-400)] via-[var(--color-info-400)] to-[var(--color-primary-600)]" />
                  <div className="p-6">
                    <div className="flex justify-between items-center mb-6">
                      <div>
                        <h3 className="text-xl font-bold text-[var(--text-primary)]">Document Clinical Case</h3>
                        <p className="text-xs text-[var(--text-secondary)] mt-0.5">Your case will be added to the AI knowledge base upon publishing</p>
                      </div>
                      <button onClick={() => setIsCreating(false)} className="w-8 h-8 rounded-full bg-[var(--surface-sunken)] flex items-center justify-center text-[var(--text-secondary)] hover:bg-[var(--border-default)] transition-colors">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                      </button>
                    </div>

                    <form onSubmit={handlePostSubmit} className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-xs font-bold text-[var(--text-secondary)] mb-1.5 uppercase tracking-wider">Primary Condition / Disease *</label>
                          <input required value={newPost.disease_name} onChange={e => setNewPost({ ...newPost, disease_name: e.target.value })} type="text"
                            className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-[var(--color-primary-400)] outline-none text-sm text-[var(--text-primary)]"
                            placeholder="e.g. Type 2 Diabetes Mellitus" />
                        </div>
                        <div>
                          <label className="block text-xs font-bold text-[var(--text-secondary)] mb-1.5 uppercase tracking-wider">Specialty Tags (comma separated) *</label>
                          <input required value={newPost.specialty_tags} onChange={e => setNewPost({ ...newPost, specialty_tags: e.target.value })} type="text"
                            className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-[var(--color-primary-400)] outline-none text-sm text-[var(--text-primary)]"
                            placeholder="e.g. Endocrinology, Internal Medicine" />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-xs font-bold text-[var(--text-secondary)] mb-1.5 uppercase tracking-wider">Clinical Findings *</label>
                          <textarea required value={newPost.clinical_findings} onChange={e => setNewPost({ ...newPost, clinical_findings: e.target.value })} rows={3}
                            className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-[var(--color-primary-400)] outline-none resize-none text-sm text-[var(--text-primary)]"
                            placeholder="Vitals, labs, presentation..." />
                        </div>
                        <div>
                          <label className="block text-xs font-bold text-[var(--text-secondary)] mb-1.5 uppercase tracking-wider">Diagnosis & Rationale *</label>
                          <textarea required value={newPost.diagnosis} onChange={e => setNewPost({ ...newPost, diagnosis: e.target.value })} rows={3}
                            className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-[var(--color-primary-400)] outline-none resize-none text-sm text-[var(--text-primary)]"
                            placeholder="Confirmed diagnosis and criteria..." />
                        </div>
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-[var(--text-secondary)] mb-1.5 uppercase tracking-wider">Treatment Plan *</label>
                        <textarea required value={newPost.treatment_plan} onChange={e => setNewPost({ ...newPost, treatment_plan: e.target.value })} rows={2}
                          className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-[var(--color-primary-400)] outline-none resize-none text-sm text-[var(--text-primary)]"
                          placeholder="Step-by-step protocol..." />
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-[var(--text-secondary)] mb-1.5 uppercase tracking-wider">Drugs Used (comma separated)</label>
                        <input value={newPost.drugs_used} onChange={e => setNewPost({ ...newPost, drugs_used: e.target.value })} type="text"
                          className="w-full bg-[var(--surface-sunken)] border border-[var(--border-default)] rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-[var(--color-primary-400)] outline-none text-sm text-[var(--text-primary)]"
                          placeholder="e.g. Metformin 500mg, Lisinopril 10mg" />
                      </div>

                      {/* File Upload */}
                      <div>
                        <label className="block text-xs font-bold text-[var(--text-secondary)] mb-1.5 uppercase tracking-wider">Clinical Imaging / Attachments</label>
                        <div
                          onClick={() => fileInputRef.current?.click()}
                          className="border-2 border-dashed border-[var(--border-strong)] rounded-xl p-5 text-center hover:border-[var(--color-primary-400)] hover:bg-[var(--color-primary-50)]/30 transition-colors cursor-pointer"
                        >
                          <input type="file" multiple className="hidden" ref={fileInputRef}
                            onChange={e => { if (e.target.files) setFiles(Array.from(e.target.files)); }} />
                          <svg className="w-8 h-8 text-[var(--text-tertiary)] mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          <p className="text-xs text-[var(--text-secondary)] font-medium">
                            {files.length > 0 ? `${files.length} file(s) selected` : "Click to upload DICOM, JPEG, PNG"}
                          </p>
                        </div>
                      </div>

                      <div className="flex justify-end gap-3 pt-2">
                        <button type="button" onClick={() => setIsCreating(false)} className="px-5 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-sunken)] rounded-xl font-bold transition-colors">Cancel</button>
                        <button type="submit" disabled={isUploading}
                          className="bg-gradient-to-r from-[var(--color-primary-500)] to-[var(--color-primary-600)] disabled:opacity-60 text-white px-6 py-2 rounded-xl text-sm font-bold shadow-lg transition-all flex items-center gap-2">
                          {isUploading ? (
                            <><svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>Publishing...</>
                          ) : "🧠 Publish & Train AI"}
                        </button>
                      </div>
                    </form>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Feed */}
            <div className="space-y-4 pb-12">
              {loadingFeed ? (
                <div className="flex items-center justify-center py-16">
                  <div className="w-8 h-8 border-3 border-[var(--color-primary-400)] border-t-transparent rounded-full animate-spin" />
                </div>
              ) : posts.length === 0 ? (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-16 bg-[var(--surface-secondary)] border border-[var(--border-default)] rounded-2xl">
                  <div className="w-16 h-16 bg-[var(--surface-sunken)] rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-[var(--text-tertiary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-bold text-[var(--text-primary)] mb-1">
                    {searchQuery ? `No results for "${searchQuery}"` : "No Cases Yet"}
                  </h3>
                  <p className="text-sm text-[var(--text-secondary)]">
                    {searchQuery ? "Try a different search term" : "Be the first to share a clinical case!"}
                  </p>
                </motion.div>
              ) : (
                posts.map((post, index) => (
                  <PostCard
                    key={post.id}
                    post={post}
                    onLike={() => toggleLike(post.id, post.is_liked_by_me)}
                    onBookmark={() => toggleBookmark(post.id, post.is_bookmarked_by_me)}
                    onComment={(text) => addComment(post.id, text)}
                    onExpand={() => {}}
                    selectedImage={selectedImage}
                    setSelectedImage={setSelectedImage}
                  />
                ))
              )}
            </div>
          </main>

          {/* ── RIGHT SIDEBAR ── */}
          <aside className="hidden lg:block space-y-5">
            {/* AI Knowledge Stats */}
            <div className="bg-gradient-to-br from-violet-50 to-indigo-50 border border-violet-200 rounded-2xl p-4 shadow-sm">
              <h3 className="font-bold text-violet-800 text-sm mb-3 flex items-center gap-2">
                🧠 AI Knowledge Base
              </h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-violet-700 font-medium">Community Cases</span>
                  <span className="text-xs font-bold text-violet-900">{posts.length} indexed</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-violet-700 font-medium">This Week</span>
                  <span className="text-xs font-bold text-violet-900">{trending?.posts_this_week ?? 0} new</span>
                </div>
                <div className="w-full bg-violet-200 rounded-full h-1.5 mt-2">
                  <div className="bg-violet-500 h-1.5 rounded-full transition-all" style={{ width: "72%" }} />
                </div>
                <p className="text-[10px] text-violet-600">Every post trains the AI diagnosis engine</p>
              </div>
            </div>

            {/* Suggested Doctors */}
            {suggestedDoctors.length > 0 && (
              <div className="bg-[var(--surface-secondary)] rounded-2xl border border-[var(--border-default)] p-4 shadow-sm">
                <h3 className="font-bold text-[var(--text-primary)] text-sm mb-3">Suggested Specialists</h3>
                <div className="space-y-3">
                  {suggestedDoctors.slice(0, 5).map(doc => (
                    <div key={doc.id} className="flex items-center gap-3">
                      <div className={`w-9 h-9 bg-gradient-to-br ${getAvatarGradient(doc.id)} rounded-full flex items-center justify-center text-white text-xs font-bold`}>
                        {doc.full_name?.[0] ?? "D"}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-bold text-[var(--text-primary)] truncate">{doc.full_name}</p>
                        <p className="text-[10px] text-[var(--text-tertiary)] truncate">{doc.specialization} · {doc.post_count} cases</p>
                      </div>
                      <button className="text-[10px] font-bold text-[var(--color-primary-500)] hover:text-[var(--color-primary-700)] border border-[var(--color-primary-300)] px-2 py-1 rounded-full hover:bg-[var(--color-primary-50)] transition-all">
                        Follow
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Live Activity */}
            <div className="bg-[var(--surface-secondary)] rounded-2xl border border-[var(--border-default)] p-4 shadow-sm">
              <h3 className="font-bold text-[var(--text-primary)] text-sm mb-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                Live Activity
              </h3>
              <div className="space-y-2">
                {posts.slice(0, 3).map((p, i) => (
                  <div key={i} className="text-xs text-[var(--text-secondary)] py-1 border-b border-[var(--border-default)] last:border-0">
                    <span className="font-bold text-[var(--color-primary-500)]">Dr. {p.author_id.substring(0, 6)}</span>
                    {" "}shared a case on{" "}
                    <span className="font-bold text-[var(--text-primary)]">{p.disease_name}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Stats */}
            {trending && (
              <div className="bg-[var(--surface-secondary)] rounded-2xl border border-[var(--border-default)] p-4 shadow-sm">
                <h3 className="font-bold text-[var(--text-primary)] text-sm mb-3">Hub Statistics</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-[var(--surface-sunken)] rounded-xl p-3 text-center">
                    <p className="text-xl font-extrabold text-[var(--color-primary-500)]">{trending.posts_this_week}</p>
                    <p className="text-[10px] text-[var(--text-tertiary)] font-medium">Cases This Week</p>
                  </div>
                  <div className="bg-[var(--surface-sunken)] rounded-xl p-3 text-center">
                    <p className="text-xl font-extrabold text-emerald-500">{trending.trending_diseases.length}</p>
                    <p className="text-[10px] text-[var(--text-tertiary)] font-medium">Trending Conditions</p>
                  </div>
                </div>
              </div>
            )}
          </aside>
        </div>
      </div>

      {/* Image Modal */}
      <AnimatePresence>
        {selectedImage && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 md:p-10"
            onClick={() => setSelectedImage(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }}
              className="relative max-w-5xl w-full max-h-full bg-[var(--surface-secondary)] rounded-2xl overflow-hidden shadow-2xl"
              onClick={e => e.stopPropagation()}
            >
              <button
                onClick={() => setSelectedImage(null)}
                className="absolute top-4 right-4 z-10 w-10 h-10 bg-black/60 hover:bg-black/80 text-white rounded-full flex items-center justify-center"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <div className="w-full h-full flex items-center justify-center bg-black min-h-[50vh]">
                <img src={selectedImage} alt="Clinical imaging" className="max-w-full max-h-[85vh] object-contain" />
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
