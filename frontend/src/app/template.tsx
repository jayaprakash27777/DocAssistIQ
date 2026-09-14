/* eslint-disable @typescript-eslint/no-unused-vars */
"use client";

import { motion } from "framer-motion";

export default function Template({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{
        type: "spring",
        stiffness: 260,
        damping: 20,
        duration: 0.4,
      }}
      className="flex flex-col min-h-screen"
    >
      {children}
    </motion.div>
  );
}
