"use client";

import { motion } from "framer-motion";

/**
 * Auth layout — minimal centred shell for login/register.
 * No navigation, just the DocAssistIQ mark and the form card.
 */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="auth-shell relative min-h-screen flex flex-col items-center justify-center overflow-hidden bg-[var(--surface-raised)]">
      {/* Background Animated Orbs */}
      <motion.div 
        animate={{ 
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.5, 0.3],
          rotate: [0, 90, 0]
        }}
        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        className="absolute top-[10%] left-[20%] w-[500px] h-[500px] rounded-full bg-[var(--color-primary-300)] opacity-30 blur-[100px] pointer-events-none"
      />
      <motion.div 
        animate={{ 
          scale: [1, 1.5, 1],
          opacity: [0.2, 0.4, 0.2],
          rotate: [0, -90, 0]
        }}
        transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
        className="absolute bottom-[10%] right-[20%] w-[600px] h-[600px] rounded-full bg-[var(--color-success-300)] opacity-20 blur-[120px] pointer-events-none"
      />

      <header className="auth-header relative z-10 text-center mb-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, type: "spring", bounce: 0.5 }}
          className="flex flex-col items-center"
        >
          <motion.span 
            className="auth-logo-mark text-3xl md:text-4xl font-black tracking-tight bg-clip-text text-transparent"
            animate={{ 
              backgroundImage: [
                "linear-gradient(to right, var(--color-primary-600), var(--color-primary-400))",
                "linear-gradient(to right, var(--color-primary-500), var(--color-primary-300))",
                "linear-gradient(to right, var(--color-primary-700), var(--color-primary-500))",
                "linear-gradient(to right, var(--color-primary-600), var(--color-primary-400))"
              ] 
            }}
            transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
            style={{ backgroundSize: '200% auto' }}
          >
            DocAssistIQ
          </motion.span>
          <span className="auth-logo-tagline text-sm text-[var(--text-secondary)] font-medium uppercase tracking-widest mt-2">Clinical Decision Support</span>
        </motion.div>
      </header>
      <main className="auth-main relative z-10 w-full max-w-md px-4">{children}</main>
      <footer className="auth-footer relative z-10 mt-12 text-center">
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="text-xs text-[var(--text-tertiary)] font-medium"
        >
          For use by qualified healthcare professionals only.
        </motion.p>
      </footer>
    </div>
  );
}
