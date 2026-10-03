"use client";

import React, { useState, useEffect } from "react";
import { Folder, FolderPlus, X, Check } from "lucide-react";
import { getStoredToken } from "@/lib/api";

interface BookmarkFolderModalProps {
  postId: string;
  currentFolder?: string;
  availableFolders?: string[];
  onClose: () => void;
  onFolderUpdated: (folder: string) => void;
}

export function BookmarkFolderModal({
  postId,
  currentFolder = "General",
  availableFolders = ["General"],
  onClose,
  onFolderUpdated,
}: BookmarkFolderModalProps) {
  const [selectedFolder, setSelectedFolder] = useState(currentFolder);
  const [newFolderName, setNewFolderName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [foldersList, setFoldersList] = useState<string[]>(availableFolders);

  useEffect(() => {
    const token = getStoredToken();
    fetch("/api/v1/hub/bookmarks/folders", {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setFoldersList(Array.from(new Set(["General", ...data])));
        }
      })
      .catch(() => {});
  }, []);

  const handleSave = async (folderToSave: string) => {
    setIsSubmitting(true);
    try {
      const token = getStoredToken();
      const res = await fetch(`/api/v1/hub/posts/${postId}/bookmark/folder`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ folder_name: folderToSave }),
      });
      if (res.ok) {
        onFolderUpdated(folderToSave);
        onClose();
      }
    } catch (err) {
      console.error("Failed to update bookmark folder", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAddNew = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFolderName.trim()) return;
    handleSave(newFolderName.trim());
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-sm w-full p-5 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center font-bold">
              <Folder className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-black text-slate-900">Organize Saved Case</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-700 rounded-lg"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Existing Folders Selection */}
        <div className="space-y-1.5 max-h-48 overflow-y-auto">
          {foldersList.map((f) => (
            <button
              key={f}
              onClick={() => handleSave(f)}
              disabled={isSubmitting}
              className={`w-full text-left px-3.5 py-2.5 rounded-xl text-xs font-bold transition flex items-center justify-between cursor-pointer ${
                selectedFolder === f
                  ? "bg-amber-50 text-amber-900 border border-amber-200"
                  : "bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200"
              }`}
            >
              <div className="flex items-center gap-2">
                <Folder className="w-3.5 h-3.5 text-amber-600" />
                <span>{f}</span>
              </div>
              {selectedFolder === f && <Check className="w-4 h-4 text-amber-700" />}
            </button>
          ))}
        </div>

        {/* Create New Folder Form */}
        <form onSubmit={handleAddNew} className="pt-2 border-t border-slate-100 space-y-2">
          <label className="block text-[11px] font-bold text-slate-600">
            Or create a new case folder:
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              required
              placeholder="e.g. Pediatric Shock, Cath Lab..."
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              className="flex-1 px-3 py-1.5 rounded-xl border border-slate-300 text-xs text-slate-900 bg-white outline-none focus:border-amber-600"
            />
            <button
              type="submit"
              disabled={isSubmitting || !newFolderName.trim()}
              className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs rounded-xl shadow-xs transition flex items-center gap-1 cursor-pointer disabled:opacity-50"
            >
              <FolderPlus className="w-3.5 h-3.5" />
              <span>Add</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default BookmarkFolderModal;
