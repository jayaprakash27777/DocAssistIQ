/* eslint-disable @typescript-eslint/no-unused-vars */
"use client";

import * as React from "react";
import { motion, HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";

interface ButtonProps extends HTMLMotionProps<"button"> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg" | "icon";
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      isLoading = false,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      "inline-flex items-center justify-center rounded-xl font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-[var(--surface-primary)] select-none";
    
    const variants = {
      primary:
        "bg-gradient-to-r from-[var(--color-primary-600)] to-[var(--color-primary-500)] text-white hover:from-[var(--color-primary-700)] hover:to-[var(--color-primary-600)] focus-visible:ring-[var(--color-primary-500)] shadow-[0_1px_3px_rgba(0,0,0,0.08),inset_0_1px_0_rgba(255,255,255,0.25)] hover:shadow-[0_4px_14px_rgba(75,170,160,0.35),inset_0_1px_0_rgba(255,255,255,0.35)] active:shadow-[inset_0_2px_4px_rgba(0,0,0,0.15)]",
      secondary:
        "bg-[var(--color-neutral-100)] text-[var(--color-neutral-900)] hover:bg-[var(--color-neutral-200)] focus-visible:ring-[var(--color-neutral-400)] shadow-[inset_0_1px_0_rgba(255,255,255,0.8),0_1px_2px_rgba(0,0,0,0.04)]",
      outline:
        "border border-[var(--color-neutral-200)] bg-white/70 hover:bg-white text-[var(--color-neutral-900)] focus-visible:ring-[var(--color-neutral-400)] shadow-sm backdrop-blur-md hover:border-[var(--color-neutral-300)]",
      ghost:
        "bg-transparent hover:bg-black/[0.04] text-[var(--color-neutral-700)] hover:text-[var(--color-neutral-900)] focus-visible:ring-[var(--color-neutral-400)]",
      danger:
        "bg-gradient-to-r from-[var(--color-danger-500)] to-[var(--color-danger-600)] text-white hover:from-[var(--color-danger-600)] hover:to-[var(--color-danger-700)] focus-visible:ring-[var(--color-danger-500)] shadow-[0_1px_3px_rgba(0,0,0,0.1),inset_0_1px_0_rgba(255,255,255,0.25)] hover:shadow-[0_4px_14px_rgba(244,63,94,0.35)]",
    };

    const sizes = {
      sm: "h-8 px-3 text-xs gap-1.5",
      md: "h-10 px-4 py-2 text-sm gap-2",
      lg: "h-12 px-8 text-base gap-2.5",
      icon: "h-10 w-10",
    };

    return (
      <motion.button
        ref={ref}
        whileHover={{ scale: disabled || isLoading ? 1 : 1.02, y: disabled || isLoading ? 0 : -1 }}
        whileTap={{ scale: disabled || isLoading ? 1 : 0.98, y: 0 }}
        transition={{ type: "spring", stiffness: 450, damping: 25 }}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && (
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
        )}
        {children as React.ReactNode}
      </motion.button>
    );
  }
);
Button.displayName = "Button";
