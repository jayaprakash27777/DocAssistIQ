/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react/no-unescaped-entities */
"use client";

import React, { useState } from "react";
import { useToast } from "@/components/shell/ToastProvider";
import { ragQuery, type RAGResponse, type RAGQueryRequest } from "@/lib/api";

export default function RAGAssistant() {
  const { toast } = useToast();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RAGResponse | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setResult(null);

    const request: RAGQueryRequest = {
      query: query.trim(),
      top_k: 3,
      filters: {
        only_approved: true,
      }
    };

    const res = await ragQuery(request);
    setLoading(false);

    if (res.ok) {
      setResult(res.data);
    } else {
      toast.error(res.error?.message || "Failed to retrieve evidence");
    }
  };

  return (
    <div className="flex flex-col h-full bg-white border-l shadow-sm">
      <div className="p-4 border-b bg-gray-50 flex items-center justify-between">
        <h3 className="font-semibold text-gray-800 flex items-center gap-2">
          <span className="text-blue-600">✨</span> Clinical Knowledge Assistant
        </h3>
      </div>

      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        {result ? (
          <div className="space-y-4">
            <div className="p-3 bg-gray-50 rounded-lg text-sm text-gray-700 font-medium">
              Q: {result.query}
            </div>

            {result.insufficient_evidence ? (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-3">
                <span className="text-yellow-600 mt-0.5">⚠️</span>
                <div>
                  <h4 className="text-sm font-semibold text-yellow-800">Insufficient Evidence</h4>
                  <p className="text-sm text-yellow-700 mt-1">
                    There is not enough approved clinical evidence in the knowledge base to answer this query safely.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="prose prose-sm text-gray-800 whitespace-pre-wrap">
                  {result.answer}
                </div>
                
                {result.citations.length > 0 && (
                  <div className="pt-4 border-t">
                    <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Sources</h4>
                    <ul className="space-y-3">
                      {result.citations.map((cit, idx) => (
                        <li key={cit.evidence_id} className="bg-blue-50/50 p-3 rounded-md border border-blue-100 text-sm">
                          <div className="flex justify-between items-start mb-1">
                            <span className="font-medium text-blue-900">[{idx + 1}] {cit.source_name}</span>
                            {cit.evidence_grade && (
                              <span className="px-1.5 py-0.5 text-xs font-semibold bg-blue-100 text-blue-800 rounded">
                                Grade {cit.evidence_grade}
                              </span>
                            )}
                          </div>
                          <p className="text-gray-700 italic text-xs mb-1">"{cit.claim}"</p>
                          <div className="text-xs text-gray-500">Code: {cit.source_code} {cit.article_doi ? `| DOI: ${cit.article_doi}` : ""}</div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-gray-500">
            <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-4 text-xl">
              🔍
            </div>
            <p className="text-sm">Ask a clinical question to retrieve evidence from the approved knowledge base.</p>
          </div>
        )}
      </div>

      <div className="p-4 border-t bg-white">
        <form onSubmit={handleSearch} className="flex gap-2 items-end">
          <textarea
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (query.trim() && !loading) {
                  // create a synthetic event to pass to handleSearch
                  handleSearch(e as unknown as React.FormEvent);
                }
              }
            }}
            placeholder="Search guidelines, paste patient paragraphs, etc... (Shift+Enter for new line)"
            className="flex-1 px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y min-h-[40px] max-h-[200px]"
            rows={2}
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors h-[40px]"
          >
            {loading ? "Searching..." : "Ask"}
          </button>
        </form>
      </div>
    </div>
  );
}
