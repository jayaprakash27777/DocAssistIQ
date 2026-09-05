export default function Home() {
  return (
    <main
      className="flex min-h-screen items-center justify-center"
      style={{ backgroundColor: "var(--surface-primary)" }}
    >
      <div className="animate-entrance text-center">
        <h1
          className="text-heading-1"
          style={{ color: "var(--text-primary)", marginBottom: "var(--space-3)" }}
        >
          DocAssistIQ
        </h1>
        <p
          className="text-body"
          style={{ color: "var(--text-secondary)" }}
        >
          Clinical Decision Support Platform
        </p>
        <p
          className="text-caption"
          style={{ marginTop: "var(--space-6)" }}
        >
          Phase 0 — Repository Initialized
        </p>
      </div>
    </main>
  );
}
