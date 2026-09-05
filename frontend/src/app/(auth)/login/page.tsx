"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { authLogin, storeToken } from "@/lib/api";

interface FieldError {
  email?: string;
  password?: string;
}

export default function LoginPage() {
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
    <div className="auth-card">
      <div className="auth-card-header">
        <h1 className="auth-card-title">Sign in</h1>
        <p className="auth-card-subtitle">Access your clinical workspace</p>
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

        <button
          id="login-submit"
          className="auth-submit"
          type="submit"
          disabled={pending}
          aria-busy={pending}
        >
          {pending ? (
            <span className="auth-spinner" aria-hidden="true" />
          ) : null}
          {pending ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <p className="auth-redirect-hint">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="auth-link">
          Create one
        </Link>
      </p>
    </div>
  );
}
