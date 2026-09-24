/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { getStoredToken } from "@/lib/api";

export default function DoctorProfile() {
  const { id } = useParams();
  const [posts, setPosts] = useState([]);
  
  useEffect(() => {
    const fetchProfilePosts = async () => {
      try {
        const token = getStoredToken() || (typeof window !== "undefined" ? (localStorage.getItem("access_token") || localStorage.getItem("token")) : null) || "";
        const res = await fetch(`/api/v1/hub/profiles/${id}/posts`, {
          headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) }
        });
        if (res.ok) {
          const data = await res.json();
          setPosts(data);
        }
      } catch (error) {
        console.error("Failed to load posts", error);
      }
    };

    fetchProfilePosts();
  }, [id]);

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 h-full overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-8 mb-8 text-center">
        <div className="w-24 h-24 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold text-3xl mx-auto mb-4 border-4 border-white shadow-md">
          Dr
        </div>
        <h1 className="text-2xl font-bold text-slate-900">Dr. {String(id).substring(0, 8)}</h1>
        <p className="text-slate-500 mt-1">Verified Medical Professional</p>
      </div>

      <h3 className="text-lg font-bold text-slate-800 mb-4">Clinical Cases Shared ({posts.length})</h3>

      <div className="space-y-6">
        {posts.length === 0 ? (
          <div className="text-center py-12 text-slate-500 bg-white border border-slate-200 rounded-xl">
            This doctor hasn&apos;t shared any clinical cases yet.
          </div>
        ) : (
          posts.map((post: any) => (
            <div key={post.id} className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
               <h2 className="text-xl font-bold text-slate-900 mb-2">{post.disease_name}</h2>
               <p className="text-sm text-slate-500 mb-4">{new Date(post.created_at).toLocaleDateString()}</p>
               <p className="text-sm text-slate-800 line-clamp-3">{post.clinical_findings}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
