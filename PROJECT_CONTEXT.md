# DocAssistIQ — Permanent Engineering Rules

This file contains the non-negotiable engineering and clinical safety rules that govern
every phase of DocAssistIQ development. All contributors and agents must follow these rules.

## Product Definition

DocAssistIQ is a clinician-facing clinical decision-support platform. It helps qualified
healthcare professionals organize clinical information, capture consultations, transcribe
speech, structure notes, retrieve evidence, inspect differential diagnoses, understand
reasoning, detect safety concerns, review investigation/medication reference information,
and finalize clinician-controlled records.

The software is **not** a patient-facing self-diagnosis application and must never
autonomously diagnose, prescribe, dispense, order treatment, or make the final clinical
decision.

## Architecture

- **Modular monolith first.**
- Backend layers: API/router → service/domain → repository/data-access → infrastructure/provider.
- Route handlers must stay thin.
- Every database schema change uses Alembic.
- Every backend endpoint has authentication/authorization rules, typed schemas, validation,
  deterministic error behavior and tests.

## Technology Stack

- **Frontend:** Next.js, React, TypeScript, TailwindCSS
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy, Alembic, pytest
- **Data:** PostgreSQL, pgvector, Redis, object-storage abstraction
- **Background jobs:** Celery
- **Realtime:** Authenticated WebSocket + Redis
- **Infrastructure:** Docker, Docker Compose, Git, GitHub Actions

## Clinical Safety Boundaries

1. AI output is decision support, not the final clinical decision.
2. AI suggestions must be visually and semantically different from clinician-confirmed decisions.
3. Never present an arbitrary model/similarity score as medical probability.
4. Never invent missing clinical information.
5. Never begin voice recording without an applicable consent event.
6. Never use identifiable patient data for development, testing, demos, or model training.
7. Never allow external documents or model-generated text to override system safety rules.
8. Never permit automatic prescribing, pharmacy ordering, dispensing, or treatment execution.
9. Never let the language model be the only safety mechanism.
10. Never let the language model be the sole medication interaction/contraindication checker.
11. Never automatically retrain a production model from one doctor interaction.
12. Never silently overwrite clinician edits, finalized records, or provenance.
13. Never silently fail when a realtime/AI dependency is unavailable.

## Implementation Method (Every Phase)

1. Inspect repository tree, package manifests, environment, migrations, tests, routes, components, services, and current runtime state.
2. Determine exactly what is already implemented and reuse it.
3. Identify dependencies and integration points for this phase.
4. Produce a concise implementation plan before editing code.
5. Implement the phase completely, including backend, frontend, data, integration, validation, and tests.
6. Prefer production-shaped code over demo shortcuts.
7. Add or update database migrations for every schema change.
8. Add typed request/response contracts for every API endpoint.
9. Handle loading, success, empty, validation-error, server-error, network-error, unauthorized, forbidden, degraded/offline and retry states.
10. For realtime features, implement actual event/stream handling.
11. Run formatters, linters, static/type checks, unit tests, integration tests and relevant e2e checks.
12. Start the actual application when runtime verification is relevant.
13. Exercise changed APIs and browser flows.
14. Test at least one negative/failure path for each important new behavior.
15. Fix discovered defects before declaring the phase complete.
16. Review the diff for debug code, dead code, accidental secrets, insecure defaults and unrelated changes.
17. Commit only after the phase passes verification.
18. Stop after the current phase.

## UI/UX Design System

- Modern, restrained, premium clinical SaaS interface.
- Clean 2D composition with strong information hierarchy.
- Consistent spacing scale, typography scale, radius scale, semantic color tokens.
- Smooth 2D motion only (120–260ms transition ranges).
- Respect `prefers-reduced-motion`.
- WCAG 2.2 AA-quality accessibility.
- No 3D effects, flashy animations, excessive glassmorphism, or animated backgrounds.

## Medication Display Rule

Every medication screen and API must display:
**REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED**
