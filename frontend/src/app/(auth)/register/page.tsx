"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { authRegister } from "@/lib/api";

interface FieldError {
  fullName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

function passwordStrength(pw: string): { score: number; label: string } {
  let score = 0;
  if (pw.length >= 8) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[a-z]/.test(pw)) score++;
  if (/\d/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  const labels = ["", "Weak", "Fair", "Good", "Strong", "Very strong"];
  return { score, label: labels[score] ?? "" };
}

export default function RegisterPage() {
  const router = useRouter();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldError>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const strength = password ? passwordStrength(password) : null;

  function validate(): boolean {
    const errors: FieldError = {};
    if (!fullName.trim() || fullName.trim().length < 2) errors.fullName = "Full name must be at least 2 characters";
    if (!email.trim()) errors.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = "Enter a valid email address";
    if (!password) errors.password = "Password is required";
    else if (password.length < 8) errors.password = "Password must be at least 8 characters";
    else if (!/[A-Z]/.test(password)) errors.password = "Password must contain at least one uppercase letter";
    else if (!/[a-z]/.test(password)) errors.password = "Password must contain at least one lowercase letter";
    else if (!/\d/.test(password)) errors.password = "Password must contain at least one digit";
    if (confirmPassword !== password) errors.confirmPassword = "Passwords do not match";
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setServerError(null);
    if (!validate()) return;

    setPending(true);
    try {
      const result = await authRegister({
        email: email.trim(),
        password,
        full_name: fullName.trim(),
      });
      if (result.ok) {
        router.push("/login?registered=1");
      } else if (result.statusCode === 409) {
        setFieldErrors((p) => ({ ...p, email: "An account with this email already exists" }));
      } else {
        setServerError(result.error.message ?? "Registration failed. Please try again.");
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
        <h1 className="auth-card-title">Create account</h1>
        <p className="auth-card-subtitle">Register your clinical workspace account</p>
      </div>

      {serverError && (
        <div className="auth-error-banner" role="alert" aria-live="assertive">
          {serverError}
        </div>
      )}

      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        {/* Full name */}
        <div className="auth-field">
          <label className="auth-label" htmlFor="reg-name">Full name</label>
          <input
            id="reg-name"
            className={`auth-input${fieldErrors.fullName ? " auth-input--error" : ""}`}
            type="text"
            autoComplete="name"
            value={fullName}
            onChange={(e) => { setFullName(e.target.value); setFieldErrors((p) => ({ ...p, fullName: undefined })); }}
            disabled={pending}
            aria-invalid={!!fieldErrors.fullName}
            aria-describedby={fieldErrors.fullName ? "reg-name-err" : undefined}
          />
          {fieldErrors.fullName && <span id="reg-name-err" className="auth-field-error">{fieldErrors.fullName}</span>}
        </div>

        {/* Email */}
        <div className="auth-field">
          <label className="auth-label" htmlFor="reg-email">Email address</label>
          <input
            id="reg-email"
            className={`auth-input${fieldErrors.email ? " auth-input--error" : ""}`}
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => { setEmail(e.target.value); setFieldErrors((p) => ({ ...p, email: undefined })); }}
            disabled={pending}
            aria-invalid={!!fieldErrors.email}
            aria-describedby={fieldErrors.email ? "reg-email-err" : undefined}
          />
          {fieldErrors.email && <span id="reg-email-err" className="auth-field-error">{fieldErrors.email}</span>}
        </div>

        {/* Password */}
        <div className="auth-field">
          <label className="auth-label" htmlFor="reg-password">Password</label>
          <input
            id="reg-password"
            className={`auth-input${fieldErrors.password ? " auth-input--error" : ""}`}
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => { setPassword(e.target.value); setFieldErrors((p) => ({ ...p, password: undefined })); }}
            disabled={pending}
            aria-invalid={!!fieldErrors.password}
            aria-describedby="reg-pw-hint reg-pw-strength"
          />
          <span id="reg-pw-hint" className="auth-field-hint">
            Min 8 characters with uppercase, lowercase, and digit
          </span>
          {strength && strength.score > 0 && (
            <div id="reg-pw-strength" className="auth-strength" aria-label={`Password strength: ${strength.label}`}>
              <div className="auth-strength-bars">
                {[1, 2, 3, 4, 5].map((n) => (
                  <div
                    key={n}
                    className={`auth-strength-bar auth-strength-bar--${n <= strength.score ? (strength.score <= 2 ? "weak" : strength.score <= 3 ? "fair" : "strong") : "empty"}`}
                  />
                ))}
              </div>
              <span className="auth-strength-label">{strength.label}</span>
            </div>
          )}
          {fieldErrors.password && <span className="auth-field-error">{fieldErrors.password}</span>}
        </div>

        {/* Confirm password */}
        <div className="auth-field">
          <label className="auth-label" htmlFor="reg-confirm">Confirm password</label>
          <input
            id="reg-confirm"
            className={`auth-input${fieldErrors.confirmPassword ? " auth-input--error" : ""}`}
            type="password"
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(e) => { setConfirmPassword(e.target.value); setFieldErrors((p) => ({ ...p, confirmPassword: undefined })); }}
            disabled={pending}
            aria-invalid={!!fieldErrors.confirmPassword}
            aria-describedby={fieldErrors.confirmPassword ? "reg-confirm-err" : undefined}
          />
          {fieldErrors.confirmPassword && <span id="reg-confirm-err" className="auth-field-error">{fieldErrors.confirmPassword}</span>}
        </div>

        <button id="register-submit" className="auth-submit" type="submit" disabled={pending} aria-busy={pending}>
          {pending ? <span className="auth-spinner" aria-hidden="true" /> : null}
          {pending ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="auth-redirect-hint">
        Already have an account?{" "}
        <Link href="/login" className="auth-link">Sign in</Link>
      </p>
    </div>
  );
}
