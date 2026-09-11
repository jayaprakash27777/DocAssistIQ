"use client";

import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/lib/auth-context";
import { motion, AnimatePresence } from "framer-motion";

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

export default function KnowledgeHub() {
  const { user } = useAuth();
  const [posts, setPosts] = useState<DoctorPost[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterSpecialty, setFilterSpecialty] = useState("");
  
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

  useEffect(() => {
    fetchPosts();

    // Setup Real-time WebSocket Connection
    const token = localStorage.getItem("access_token");
    if (!token) return;

    // Use wss:// in production, ws:// locally
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/v1/stream?token=${token}`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        
        // Handle New Posts
        if (msg.type === "hub_new_post") {
          setPosts(prev => [msg.payload, ...prev]);
        }
        
        // Handle Like Updates
        if (msg.type === "hub_post_liked") {
          setPosts(prev => prev.map(p => {
            if (p.id === msg.payload.post_id) {
              return { ...p, likes_count: msg.payload.likes_count };
            }
            return p;
          }));
        }
        
        // Handle Comment Updates
        if (msg.type === "hub_new_comment") {
          setPosts(prev => prev.map(p => {
            if (p.id === msg.payload.post_id) {
              return { ...p, comments_count: msg.payload.comments_count };
            }
            return p;
          }));
        }
      } catch (e) {
        console.error("WS Parse Error:", e);
      }
    };

    return () => {
      ws.close();
    };
  }, [searchQuery, filterSpecialty]);

  const fetchPosts = async () => {
    try {
      const token = localStorage.getItem("access_token");
      let url = "/api/v1/hub/feed?";
      if (searchQuery) url += `disease=${encodeURIComponent(searchQuery)}&`;
      if (filterSpecialty) url += `specialty=${encodeURIComponent(filterSpecialty)}&`;
      
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPosts(data);
      }
    } catch (error) {
      console.error("Failed to load feed", error);
    }
  };

  const uploadFiles = async (): Promise<string[]> => {
    const token = localStorage.getItem("access_token");
    const attachmentIds: string[] = [];
    
    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("metadata", JSON.stringify({ category: "clinical_imaging" }));
      
      const res = await fetch("/api/v1/files/upload", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
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
      const token = localStorage.getItem("access_token");
      const attachmentIds = await uploadFiles();
      
      const payload = {
        ...newPost,
        drugs_used: newPost.drugs_used.split(",").map(d => d.trim()).filter(Boolean),
        specialty_tags: newPost.specialty_tags.split(",").map(s => s.trim()).filter(Boolean),
        attachment_ids: attachmentIds
      };
      
      const res = await fetch("/api/v1/hub/posts", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        setIsCreating(false);
        setNewPost({
          disease_name: "", specialty_tags: "", clinical_findings: "",
          diagnosis: "", treatment_plan: "", drugs_used: ""
        });
        setFiles([]);
        fetchPosts();
      }
    } catch (error) {
      console.error("Failed to create post", error);
    } finally {
      setIsUploading(false);
    }
  };

  const toggleAction = async (postId: string, action: "like" | "bookmark", currentState: boolean) => {
    try {
      const token = localStorage.getItem("access_token");
      await fetch(`/api/v1/hub/posts/${postId}/${action}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setPosts(posts.map(p => {
        if (p.id === postId) {
          if (action === "like") {
            return { ...p, is_liked_by_me: !currentState, likes_count: currentState ? p.likes_count - 1 : p.likes_count + 1 };
          } else {
            return { ...p, is_bookmarked_by_me: !currentState };
          }
        }
        return p;
      }));
    } catch (error) {
      console.error(`Failed to toggle ${action}`, error);
    }
  };

  if (!user?.is_verified) {
    return (
      <div className="flex items-center justify-center h-full bg-slate-50">
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="p-10 text-center bg-white/80 backdrop-blur-md rounded-2xl shadow-xl border border-white/40">
          <div className="w-20 h-20 bg-gradient-to-tr from-red-500 to-rose-400 text-white rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg shadow-red-200">
            <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-3xl font-bold text-slate-900 mb-3 tracking-tight">Verification Required</h2>
          <p className="text-slate-600 max-w-md mx-auto text-lg leading-relaxed">
            The DocAssistIQ Knowledge Hub is an exclusive, clinical-grade network. Please complete your professional verification to access this peer-reviewed ecosystem.
          </p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 h-full overflow-y-auto custom-scrollbar">
      {/* Premium Header & Filters */}
      <div className="sticky top-0 z-20 bg-slate-50/80 backdrop-blur-xl pb-6 pt-2 border-b border-slate-200/60 mb-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-700 to-indigo-600 tracking-tight">Clinical Hub</h1>
            <p className="text-slate-500 mt-1 font-medium">Collaborate on complex cases with verified specialists.</p>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="relative">
              <svg className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input 
                type="text" 
                placeholder="Search diseases..." 
                className="pl-10 pr-4 py-2.5 rounded-full border border-slate-200 bg-white/50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all w-64 shadow-sm"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            
            <select 
              value={filterSpecialty} 
              onChange={(e) => setFilterSpecialty(e.target.value)}
              className="py-2.5 px-4 rounded-full border border-slate-200 bg-white/50 focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition-all text-slate-700 shadow-sm font-medium"
            >
              <option value="">All Specialties</option>
              <option value="Cardiology">Cardiology</option>
              <option value="Neurology">Neurology</option>
              <option value="Oncology">Oncology</option>
              <option value="Pediatrics">Pediatrics</option>
            </select>

            <motion.button 
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsCreating(true)}
              className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-6 py-2.5 rounded-full font-bold shadow-lg shadow-blue-500/30 transition-all flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Share Case
            </motion.button>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {isCreating && (
          <motion.div 
            initial={{ opacity: 0, y: -20, height: 0 }}
            animate={{ opacity: 1, y: 0, height: "auto" }}
            exit={{ opacity: 0, scale: 0.95, height: 0 }}
            className="mb-10 bg-white border border-slate-200 shadow-xl rounded-2xl overflow-hidden relative z-10"
          >
            <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500"></div>
            <div className="p-8">
              <div className="flex justify-between items-center mb-8">
                <div>
                  <h3 className="text-2xl font-bold text-slate-900">Document Clinical Case</h3>
                  <p className="text-slate-500 text-sm mt-1">Provide structured data to enrich the DocAssistIQ knowledge graph.</p>
                </div>
                <button onClick={() => setIsCreating(false)} className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 hover:bg-slate-200 transition-colors">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <form onSubmit={handlePostSubmit} className="space-y-6">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-2">Primary Condition / Disease</label>
                    <input required value={newPost.disease_name} onChange={e => setNewPost({...newPost, disease_name: e.target.value})} type="text" className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:bg-white outline-none transition-all" placeholder="e.g. Type 2 Diabetes Mellitus" />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-2">Specialty Tags (Comma separated)</label>
                    <input required value={newPost.specialty_tags} onChange={e => setNewPost({...newPost, specialty_tags: e.target.value})} type="text" className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:bg-white outline-none transition-all" placeholder="e.g. Endocrinology, Internal Medicine" />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-2">Clinical Findings (Presentation)</label>
                    <textarea required value={newPost.clinical_findings} onChange={e => setNewPost({...newPost, clinical_findings: e.target.value})} rows={4} className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:bg-white outline-none transition-all resize-none" placeholder="Detailed patient presentation, vitals, and lab irregularities..." />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-2">Diagnosis & Rationale</label>
                    <textarea required value={newPost.diagnosis} onChange={e => setNewPost({...newPost, diagnosis: e.target.value})} rows={4} className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:bg-white outline-none transition-all resize-none" placeholder="Confirmed diagnosis and diagnostic criteria met..." />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Treatment Plan</label>
                  <textarea required value={newPost.treatment_plan} onChange={e => setNewPost({...newPost, treatment_plan: e.target.value})} rows={3} className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:bg-white outline-none transition-all resize-none" placeholder="Step-by-step treatment methodology..." />
                </div>

                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Pharmacological Interventions (Comma separated)</label>
                  <input value={newPost.drugs_used} onChange={e => setNewPost({...newPost, drugs_used: e.target.value})} type="text" className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:bg-white outline-none transition-all" placeholder="e.g. Metformin 500mg, Lisinopril 10mg" />
                </div>

                {/* File Upload Zone */}
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Clinical Imaging / Attachments</label>
                  <div 
                    className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:bg-slate-50 hover:border-blue-400 transition-colors cursor-pointer group"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <input 
                      type="file" 
                      multiple 
                      className="hidden" 
                      ref={fileInputRef}
                      onChange={(e) => {
                        if (e.target.files) {
                          setFiles(Array.from(e.target.files));
                        }
                      }}
                    />
                    <div className="w-16 h-16 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <p className="font-semibold text-slate-700 mb-1">Click to upload Medical Imagery</p>
                    <p className="text-sm text-slate-500">Supports DICOM, JPEG, PNG (Max 50MB)</p>
                  </div>
                  
                  {files.length > 0 && (
                    <div className="mt-4 flex flex-wrap gap-3">
                      {files.map((f, i) => (
                        <div key={i} className="bg-blue-50 border border-blue-100 text-blue-800 text-sm px-4 py-2 rounded-lg flex items-center gap-2 font-medium">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                          </svg>
                          {f.name}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="pt-6 border-t border-slate-100 flex justify-end gap-4">
                  <button type="button" onClick={() => setIsCreating(false)} className="px-6 py-3 text-slate-600 hover:bg-slate-100 rounded-xl font-bold transition-colors">Cancel</button>
                  <button 
                    type="submit" 
                    disabled={isUploading}
                    className="bg-blue-600 hover:bg-blue-700 disabled:opacity-70 text-white px-8 py-3 rounded-xl font-bold shadow-lg shadow-blue-500/30 transition-all flex items-center gap-2"
                  >
                    {isUploading ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Processing...
                      </>
                    ) : 'Publish Clinical Case'}
                  </button>
                </div>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="space-y-8">
        {posts.length === 0 ? (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-20 bg-white/50 border border-slate-200/50 rounded-3xl backdrop-blur-sm">
            <div className="w-24 h-24 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-12 h-12 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-slate-700 mb-2">No Cases Found</h3>
            <p className="text-slate-500">Be the first to share a clinical case in this specialty.</p>
          </motion.div>
        ) : (
          posts.map((post, index) => (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              key={post.id} 
              className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 group"
            >
              <div className="p-7">
                <div className="flex items-start justify-between mb-6">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 bg-gradient-to-br from-indigo-100 to-blue-50 rounded-full flex items-center justify-center text-blue-700 font-extrabold text-xl border-2 border-white shadow-sm">
                      Dr
                    </div>
                    <div>
                      <h4 className="font-bold text-slate-900 text-lg">Dr. {post.author_id.substring(0, 8)}</h4>
                      <p className="text-sm text-slate-500 font-medium">Verified Specialist • {new Date(post.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                  
                  <button 
                    onClick={() => toggleAction(post.id, "bookmark", post.is_bookmarked_by_me)}
                    className={`p-2 rounded-full transition-all ${post.is_bookmarked_by_me ? 'bg-amber-50 text-amber-500' : 'text-slate-400 hover:bg-slate-100'}`}
                  >
                    <svg className="w-6 h-6" fill={post.is_bookmarked_by_me ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                    </svg>
                  </button>
                </div>

                <div className="mb-4 flex flex-wrap gap-2">
                  {post.specialty_tags.map((tag, i) => (
                    <span key={i} className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-100">
                      {tag}
                    </span>
                  ))}
                </div>

                <h2 className="text-2xl font-extrabold text-slate-900 mb-5 leading-tight">{post.disease_name}</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-6">
                  <div className="bg-slate-50/50 p-5 rounded-2xl border border-slate-100 shadow-inner">
                    <h5 className="flex items-center gap-2 text-xs font-black text-slate-400 uppercase tracking-widest mb-3">
                      <svg className="w-4 h-4 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                      </svg>
                      Clinical Findings
                    </h5>
                    <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">{post.clinical_findings}</p>
                  </div>
                  <div className="bg-slate-50/50 p-5 rounded-2xl border border-slate-100 shadow-inner">
                    <h5 className="flex items-center gap-2 text-xs font-black text-slate-400 uppercase tracking-widest mb-3">
                      <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Diagnosis & Rationale
                    </h5>
                    <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">{post.diagnosis}</p>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-blue-50 to-indigo-50/50 p-6 rounded-2xl border border-blue-100 mb-6 relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-1 h-full bg-blue-500"></div>
                  <h5 className="flex items-center gap-2 text-xs font-black text-blue-600 uppercase tracking-widest mb-3">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                    </svg>
                    Treatment Protocol
                  </h5>
                  <p className="text-sm text-slate-800 whitespace-pre-wrap leading-relaxed font-medium">{post.treatment_plan}</p>
                  
                  {post.drugs_used.length > 0 && (
                    <div className="mt-5 pt-5 border-t border-blue-200/50">
                      <p className="text-xs font-bold text-blue-800 mb-2">Pharmacology:</p>
                      <div className="flex flex-wrap gap-2">
                        {post.drugs_used.map((drug, i) => (
                          <span key={i} className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-white text-blue-700 shadow-sm border border-blue-100">
                            {drug}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Attachments Carousel */}
                {post.attachments && post.attachments.length > 0 && (
                  <div className="mb-6">
                    <h5 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3">Clinical Imaging</h5>
                    <div className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar">
                      {post.attachments.map((att) => (
                        <div key={att.id} className="min-w-[200px] h-[150px] bg-slate-100 rounded-xl border border-slate-200 overflow-hidden relative group/img cursor-pointer">
                           {att.file_type.includes('image') ? (
                             <img src={att.file_url} alt="Clinical image" className="w-full h-full object-cover" />
                           ) : (
                             <div className="w-full h-full flex flex-col items-center justify-center text-slate-400">
                               <svg className="w-10 h-10 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                               </svg>
                               <span className="text-xs font-semibold">Document</span>
                             </div>
                           )}
                           <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/img:opacity-100 transition-opacity flex items-center justify-center">
                              <span className="text-white font-semibold text-sm">View Full</span>
                           </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              
              <div className="px-7 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
                <div className="flex items-center gap-8">
                  <button 
                    onClick={() => toggleAction(post.id, "like", post.is_liked_by_me)}
                    className={`flex items-center gap-2.5 font-bold transition-all ${post.is_liked_by_me ? 'text-blue-600 scale-105' : 'text-slate-500 hover:text-slate-700'}`}
                  >
                    <svg className="w-6 h-6" fill={post.is_liked_by_me ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={post.is_liked_by_me ? 0 : 2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                    </svg>
                    <span>{post.likes_count} <span className="hidden sm:inline">Endorsements</span></span>
                  </button>
                  <button className="flex items-center gap-2.5 text-slate-500 hover:text-slate-700 font-bold transition-colors">
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    <span>{post.comments_count} <span className="hidden sm:inline">Peer Reviews</span></span>
                  </button>
                </div>
                <button className="text-sm font-bold text-slate-400 hover:text-blue-600 transition-colors">
                  Read Case Study →
                </button>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
