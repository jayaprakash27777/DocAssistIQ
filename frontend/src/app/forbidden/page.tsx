/* eslint-disable @typescript-eslint/no-unused-vars */
import Link from "next/link";

export const metadata = {
  title: "Access Denied — DocAssistIQ",
  description: "You do not have permission to access this page.",
};

export default function ForbiddenPage() {
  return (
    <div className="forbidden-shell">
      <div className="forbidden-card">
        {/* Icon */}
        <div className="forbidden-icon" aria-hidden="true">
          <svg
            width="56"
            height="56"
            viewBox="0 0 56 56"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <circle cx="28" cy="28" r="26" stroke="currentColor" strokeWidth="2.5" />
            <path
              d="M18 18L38 38M38 18L18 38"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
          </svg>
        </div>

        {/* Status code */}
        <p className="forbidden-code">403</p>

        {/* Heading */}
        <h1 className="forbidden-heading">Access Denied</h1>

        {/* Explanation */}
        <p className="forbidden-message">
          Your account does not have the required role to access this page.
          If you believe this is an error, please contact your system administrator.
        </p>

        {/* Clinical notice */}
        <div className="forbidden-notice" role="note">
          <span className="forbidden-notice-label">Security Notice</span>
          <span className="forbidden-notice-text">
            All access control is enforced server-side. This restriction cannot
            be bypassed by the browser.
          </span>
        </div>

        {/* Actions */}
        <div className="forbidden-actions">
          <Link href="/dashboard" className="forbidden-btn-primary">
            Go to Dashboard
          </Link>
          <Link href="/" className="forbidden-btn-secondary">
            Sign In as Different User
          </Link>
        </div>
      </div>
    </div>
  );
}
