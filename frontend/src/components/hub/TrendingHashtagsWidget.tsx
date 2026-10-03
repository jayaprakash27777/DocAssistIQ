"use client";

import React, { useState, useEffect } from "react";

import { TrendingHashtag } from "@/types/social";
import { getStoredToken } from "@/lib/api";
import { getSharedRealtimeClient } from "@/lib/ws";

interface TrendingHashtagsWidgetProps {
  hashtags?: TrendingHashtag[];
  activeHashtag?: string | null;
  onSelectHashtag?: (tag: string) => void;
  onClearHashtag?: () => void;
}

export function TrendingHashtagsWidget({
  hashtags: initialHashtags,
  activeHashtag,
  onSelectHashtag,
  onClearHashtag,
}: TrendingHashtagsWidgetProps) {
  const [hashtags, setHashtags] = useState<TrendingHashtag[]>(initialHashtags || []);

  const loadHashtags = () => {
    const token = getStoredToken();
    fetch("/api/v1/hub/hashtags", {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        if (Array.isArray(data)) {
          setHashtags(data);
        }
      })
      .catch(() => {});
  };

  useEffect(() => {
    if (initialHashtags && initialHashtags.length > 0) {
      setHashtags(initialHashtags);
    } else {
      loadHashtags();
    }

    const token = getStoredToken();
    const ws = getSharedRealtimeClient(token);
    const unsub = ws.subscribeMessages((type) => {
      if (type === "hub_new_post") {
        loadHashtags();
      }
    });

    return () => {
      unsub();
    };
  }, [initialHashtags]);

  if (!hashtags || hashtags.length === 0) return null;

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-xs">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
          <h3 className="font-extrabold text-xs text-slate-900 uppercase tracking-wider">
            Trending Hashtags
          </h3>
        </div>
        {activeHashtag && onClearHashtag && (
          <button
            type="button"
            onClick={onClearHashtag}
            className="text-[10px] text-teal-600 hover:text-teal-800 font-bold hover:underline cursor-pointer"
          >
            Clear Filter
          </button>
        )}
      </div>

      <div className="space-y-1">
        {hashtags.slice(0, 8).map((h) => {
          const isSelected = activeHashtag === h.tag;
          return (
            <button
              key={h.tag}
              type="button"
              onClick={() => onSelectHashtag && onSelectHashtag(h.tag)}
              className={`w-full text-left px-3 py-2 rounded-xl text-xs font-semibold transition-all flex items-center justify-between cursor-pointer ${
                isSelected
                  ? "bg-teal-50 text-teal-900 font-bold border border-teal-200"
                  : "text-slate-700 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              <div className="flex items-center gap-1.5 truncate">
                <span className="text-teal-600 font-extrabold">{h.tag}</span>
                {h.has_urgent && (
                  <span className="inline-block w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping" title="Active emergency consult" />
                )}
              </div>
              <span className="text-[10px] font-mono text-slate-400 font-medium">
                {h.count} cases
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default TrendingHashtagsWidget;
