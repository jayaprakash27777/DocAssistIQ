/**
 * Auth layout — minimal centred shell for login/register.
 * No navigation, just the DocAssistIQ mark and the form card.
 */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="auth-shell">
      <header className="auth-header">
        <span className="auth-logo-mark">DocAssistIQ</span>
        <span className="auth-logo-tagline">Clinical Decision Support</span>
      </header>
      <main className="auth-main">{children}</main>
      <footer className="auth-footer">
        <p>For use by qualified healthcare professionals only.</p>
      </footer>
    </div>
  );
}
