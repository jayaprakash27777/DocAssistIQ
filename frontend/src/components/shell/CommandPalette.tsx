/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const router = useRouter();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const commands = [
    { id: "dash", name: "Dashboard", action: () => router.push("/dashboard") },
    { id: "cons", name: "Consultations", action: () => router.push("/consultations") },
    { id: "notes", name: "Clinical Notes", action: () => router.push("/notes") },
    { id: "files", name: "File Storage", action: () => router.push("/files") },
    { id: "hub", name: "Clinical Hub", action: () => router.push("/hub") },
    { id: "prof", name: "My Profile", action: () => router.push("/profile") },
  ];

  const filteredCommands = query === "" 
    ? commands 
    : commands.filter(c => c.name.toLowerCase().includes(query.toLowerCase()));

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setOpen(false)}
            className="fixed inset-0 z-50 bg-[var(--surface-overlay)] backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="fixed inset-x-0 top-[15%] z-50 mx-auto max-w-xl overflow-hidden rounded-2xl bg-[var(--glass-bg)] border border-[var(--glass-border)] shadow-[var(--glass-shadow)] backdrop-blur-[16px]"
          >
            <div className="p-4 border-b border-[var(--border-default)] flex items-center">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-[var(--text-tertiary)] mr-3">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
              <input
                type="text"
                autoFocus
                className="w-full bg-transparent text-[var(--text-primary)] placeholder-[var(--text-tertiary)] outline-none text-lg"
                placeholder="Search commands or navigate..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <div className="flex gap-1 ml-2">
                <kbd className="px-2 py-1 text-xs font-mono bg-[var(--surface-primary)] border border-[var(--border-default)] rounded text-[var(--text-secondary)]">ESC</kbd>
              </div>
            </div>
            
            <div className="max-h-80 overflow-y-auto p-2">
              {filteredCommands.length === 0 ? (
                <div className="p-4 text-center text-[var(--text-secondary)]">No results found.</div>
              ) : (
                <ul className="space-y-1">
                  {filteredCommands.map((command, idx) => (
                    <motion.li
                      key={command.id}
                      whileHover={{ scale: 0.98, backgroundColor: "var(--color-neutral-100)" }}
                      className="px-4 py-3 rounded-xl cursor-pointer text-[var(--text-primary)] flex items-center gap-3 transition-colors"
                      onClick={() => {
                        command.action();
                        setOpen(false);
                      }}
                    >
                      <span className="flex-1">{command.name}</span>
                      <span className="text-xs text-[var(--text-tertiary)]">Jump to</span>
                    </motion.li>
                  ))}
                </ul>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
