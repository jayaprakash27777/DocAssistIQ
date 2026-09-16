/* eslint-disable @typescript-eslint/no-unused-vars */
"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { authLogin, storeToken } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";

interface FieldError {
  email?: string;
  password?: string;
}

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextUrl = searchParams.get("next") ?? "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldError>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  function validate(): boolean {
    const errors: FieldError = {};
    if (!email.trim()) errors.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = "Enter a valid email address";
    if (!password) errors.password = "Password is required";
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setServerError(null);
    if (!validate()) return;

    setPending(true);
    try {
      const result = await authLogin({ email: email.trim(), password });
      if (result.ok) {
        storeToken(result.data.access_token);
        // Set lightweight session cookie for Next.js middleware route guarding
        document.cookie = "docassistiq_has_session=1; path=/; SameSite=Strict";
        router.push(nextUrl);
      } else {
        // Always generic — do not differentiate wrong email vs wrong password
        setServerError("Invalid email or password. Please try again.");
      }
    } catch {
      setServerError("Unable to connect to the server. Please try again.");
    } finally {
      setPending(false);
    }
  }

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.6, type: "spring", bounce: 0.4 }}
      className="auth-card relative overflow-hidden"
    >
      <div className="absolute top-0 right-0 -mr-20 -mt-20 w-64 h-64 rounded-full bg-[var(--color-primary-200)] opacity-20 blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-80 h-80 rounded-full bg-[var(--color-primary-100)] opacity-10 blur-3xl pointer-events-none" />

      <div className="auth-card-header text-center relative z-10 mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-[var(--text-primary)] mb-2">
          Welcome Back
        </h1>
        <p className="text-sm font-medium text-[var(--text-secondary)]">Sign in to your clinical workspace</p>
      </div>

      {serverError && (
        <div className="auth-error-banner" role="alert" aria-live="assertive">
          {serverError}
        </div>
      )}

      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <div className="auth-field">
          <label className="auth-label" htmlFor="login-email">
            Email address
          </label>
          <input
            id="login-email"
            className={`auth-input${fieldErrors.email ? " auth-input--error" : ""}`}
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (fieldErrors.email) setFieldErrors((p) => ({ ...p, email: undefined }));
            }}
            disabled={pending}
            aria-describedby={fieldErrors.email ? "login-email-err" : undefined}
            aria-invalid={!!fieldErrors.email}
          />
          {fieldErrors.email && (
            <span id="login-email-err" className="auth-field-error">
              {fieldErrors.email}
            </span>
          )}
        </div>

        <div className="auth-field">
          <div className="auth-label-row">
            <label className="auth-label" htmlFor="login-password">
              Password
            </label>
          </div>
          <input
            id="login-password"
            className={`auth-input${fieldErrors.password ? " auth-input--error" : ""}`}
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              if (fieldErrors.password) setFieldErrors((p) => ({ ...p, password: undefined }));
            }}
            disabled={pending}
            aria-describedby={fieldErrors.password ? "login-pw-err" : undefined}
            aria-invalid={!!fieldErrors.password}
          />
          {fieldErrors.password && (
            <span id="login-pw-err" className="auth-field-error">
              {fieldErrors.password}
            </span>
          )}
        </div>

        <Button
          id="login-submit"
          type="submit"
          isLoading={pending}
          className="w-full mt-2 h-11 text-base"
        >
          {pending ? "Signing in…" : "Sign in"}
        </Button>
      </form>

      <p className="auth-redirect-hint relative z-10 mt-8">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="auth-link font-bold text-[var(--color-primary-600)] hover:text-[var(--color-primary-700)] transition-colors">
          Create one
        </Link>
      </p>
    </motion.div>
  );
}

import { Suspense } from "react";

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="auth-card">Loading...</div>}>
      <LoginContent />
    </Suspense>
  );
}
