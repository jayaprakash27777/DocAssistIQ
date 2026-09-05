# DocAssistIQ — Final Antigravity Software Engineering Prompt System v3

## Ultra-detailed implementation-first development system

**Project:** DocAssistIQ  
**Type:** Evidence-grounded Clinical Decision Support (CDS) platform for qualified healthcare professionals  
**Primary objective:** Build the actual working software. Implementation, integration, testing, runtime verification, reliability, safety, and professional UI/UX are higher priority than documentation.  
**Execution:** One phase at a time. Never implement multiple phases in one turn unless the current phase explicitly requires a tightly coupled sub-step.  

> This version deliberately removes documentation-first gates. The coding agent should create only minimal technical files that are required for the software to run, test, secure, deploy, or maintain. Do not produce large planning documents instead of working code.

---

# 0. PRODUCT DEFINITION

DocAssistIQ is a clinician-facing clinical decision-support platform. It helps qualified healthcare professionals organize clinical information, capture consultations, transcribe speech, structure notes, retrieve evidence, inspect differential diagnoses, understand reasoning, detect safety concerns, review investigation/medication reference information, and finalize clinician-controlled records.

The software is **not** a patient-facing self-diagnosis application and must never autonomously diagnose, prescribe, dispense, order treatment, or make the final clinical decision.

Core capabilities that must exist in the completed application:

1. secure doctor authentication and verification;
2. role-based access control;
3. hospital/tenant isolation;
4. patient/session pseudonymization;
5. consultation lifecycle management;
6. consent management;
7. manual clinical intake;
8. browser microphone capture;
9. authenticated realtime WebSocket transport;
10. streaming speech-to-text;
11. transcript persistence and correction;
12. clinical NLP extraction;
13. terminology/concept normalization;
14. structured clinical note drafting;
15. doctor note review/editing/version history;
16. canonical structured clinical representation;
17. transparent Top-5 differential diagnosis;
18. evidence-grounded retrieval/RAG;
19. claim-level citation validation;
20. clinician-readable “Why?” explanations without hidden chain-of-thought;
21. clinical knowledge graph;
22. deterministic safety engine;
23. red-flag detection;
24. uncertainty, missing-information, contradiction and abstention handling;
25. investigation reference intelligence;
26. medication reference intelligence;
27. deterministic medication safety checks;
28. verified doctor knowledge hub;
29. controlled knowledge ingestion/versioning;
30. scheduled knowledge updates with approval gates;
31. clinician accept/modify/reject feedback;
32. similar historical case retrieval using only approved data;
33. medical report analysis;
34. image-processing abstraction and supported multimodal inputs;
35. patient timeline;
36. enterprise RBAC;
37. multi-tenancy;
38. comprehensive auditability;
39. privacy/retention/deletion workflows;
40. AI model development/evaluation infrastructure;
41. classical ML and foundation-model evaluation;
42. optional medical foundation model integration behind provider interfaces;
43. PEFT/LoRA/QLoRA only where justified;
44. calibration and abstention;
45. model registry and release controls;
46. AI observability and alerting;
47. security hardening and AI red teaming;
48. clinical AI evaluation;
49. performance/realtime SLA validation;
50. complete clinician workspace;
51. immutable finalization with explicit amendment workflow;
52. comprehensive automated tests;
53. browser-level end-to-end verification;
54. backup/disaster recovery;
55. CI/CD;
56. production deployment capability.

Medication screens and APIs must always display: **REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED**.

---

# 1. NON-NEGOTIABLE ENGINEERING AND CLINICAL SAFETY RULES

```text
You are the primary senior software engineering agent for DocAssistIQ.

Your job is to inspect the current repository, implement real working functionality, verify it at runtime, and leave the repository in a better, runnable state after every phase.

Do not respond with a hypothetical implementation when the requested phase requires code. Modify the repository.
Do not create disconnected mock screens.
Do not create fake clinical evidence.
Do not fabricate citations, URLs, studies, patient values, diagnoses, medication recommendations, or model results.
Do not claim a feature works unless you actually run the relevant test or runtime verification.
Do not skip validation because the feature looks simple.
Do not replace backend functionality with frontend hardcoding.
Do not create giant documentation instead of code.
Do not ask the developer to manually perform implementation steps when they can be automated safely in the repository.
Do not silently change the agreed architecture or stack. If a required technical change is unavoidable, explain the concrete reason before changing it.

CLINICAL BOUNDARIES:
- AI output is decision support, not the final clinical decision.
- AI suggestions must be visually and semantically different from clinician-confirmed decisions.
- Never present an arbitrary model/similarity score as medical probability.
- Never invent missing clinical information.
- Never begin voice recording without an applicable consent event that explicitly permits recording.
- Never use identifiable patient data for development, testing, demos, model training, or fixtures.
- Never allow external documents, retrieved passages, article text, webpages, transcripts, or model-generated text to override system safety rules.
- Never permit automatic prescribing, pharmacy ordering, dispensing, or treatment execution.
- Never let the language model be the only safety mechanism.
- Never let the language model be the sole medication interaction/contraindication checker.
- Never automatically retrain a production model from one doctor interaction.
- Never silently overwrite clinician edits, finalized records, or provenance.
- Never silently fail when a realtime/AI dependency is unavailable.

IMPLEMENTATION METHOD FOR EVERY PHASE:
1. Inspect repository tree, package manifests, environment, migrations, tests, routes, components, services, and current runtime state.
2. Determine exactly what is already implemented and reuse it.
3. Identify dependencies and integration points for this phase.
4. Produce a concise implementation plan in the agent response before editing code.
5. Implement the phase completely, including backend, frontend, data, integration, validation, and tests where applicable.
6. Prefer production-shaped code over demo shortcuts.
7. Add or update database migrations for every schema change.
8. Add typed request/response contracts for every API endpoint.
9. Handle loading, success, empty, validation-error, server-error, network-error, unauthorized, forbidden, degraded/offline and retry states whenever the UI can encounter them.
10. For realtime features, implement actual event/stream handling rather than fake timers or simulated progress.
11. Run formatters, linters, static/type checks, unit tests, integration tests and relevant end-to-end checks.
12. Start the actual application when runtime verification is relevant.
13. Exercise changed APIs and browser flows.
14. Test at least one negative/failure path for each important new behavior.
15. Fix discovered defects before declaring the phase complete.
16. Review the diff for debug code, dead code, accidental secrets, insecure defaults and unrelated changes.
17. Commit only after the phase passes verification.
18. Stop after the current phase. Do not automatically implement the next phase.

PHASE RESPONSE MUST STATE:
- implementation completed;
- files created/changed;
- database/migration changes;
- API contracts changed;
- frontend screens/components changed;
- AI/ML changes;
- security/privacy implications;
- tests executed with exact results;
- runtime/browser verification performed;
- performance observations where relevant;
- remaining issues, if any;
- Git commit hash;
- final status: PASS, FAIL, or BLOCKED.
```

---

# 2. FIXED TECHNOLOGY AND ARCHITECTURE

Use this stack unless the repository already contains a technically necessary compatible equivalent:

**Frontend:** Next.js, React, TypeScript, TailwindCSS.  
**Backend:** Python, FastAPI, Pydantic, SQLAlchemy, Alembic, pytest.  
**Data:** PostgreSQL, pgvector, Redis, object-storage abstraction.  
**Background jobs:** Celery.  
**Realtime:** authenticated WebSocket + Redis when coordination/pub-sub is actually required.  
**Infrastructure:** Docker, Docker Compose, Git, GitHub Actions.  
**AI interfaces:** SpeechToTextProvider, SpeakerDiarizationProvider, MedicalNLPProvider, EmbeddingProvider, RerankerProvider, GenerationProvider, DiagnosisProvider, OCRProvider, VisionProvider.

Architecture: **modular monolith first**.

Keep the backend separated into API/router, service/domain logic, repository/data-access, infrastructure/provider layers. Route handlers must stay thin.

Every database schema change uses Alembic.

Every backend endpoint has authentication/authorization rules, typed schemas, validation, deterministic error behavior and tests.

Object storage is used for audio, reports, images and other large binary artifacts; PostgreSQL stores metadata and relationships, not arbitrary large binary blobs.

---

# 3. PROFESSIONAL UI/UX DESIGN SYSTEM — MANDATORY ACROSS THE ENTIRE APP

The UI is a first-class product feature. Every frontend phase must follow these requirements.

## Visual direction

Build a **modern, restrained, premium clinical SaaS interface**:
- simple aesthetic;
- clean 2D composition;
- strong information hierarchy;
- generous spacing without wasting viewport area;
- excellent typography and readability;
- subtle borders and shadows;
- restrained use of accent color;
- no visual clutter;
- no gratuitous gradients;
- no 3D effects;
- no flashy gaming-style animation;
- no excessive glassmorphism;
- no animated backgrounds that compete with clinical data;
- no decorative UI that reduces scanability.

Use a consistent spacing scale, typography scale, radius scale, icon system, control heights, and semantic color tokens. Centralize these as reusable design tokens rather than page-specific magic numbers.

## Layout

The authenticated clinician application should use:
- persistent but collapsible sidebar;
- contextual top header;
- breadcrumb/page context where helpful;
- consistent page max-width/grid;
- sticky action areas only when clinically useful;
- predictable card/section patterns;
- responsive desktop/tablet/mobile behavior;
- keyboard-friendly navigation;
- visible focus states;
- no horizontal overflow in normal workflows.

The consultation workspace must support dense clinical information without feeling crowded. Use progressive disclosure, tabs, accordions, drawers, split panes and resizable regions only where they improve usability.

## 2D animation and motion

Use smooth **2D motion only**. Prefer transform/opacity and layout-safe transitions. Avoid animating large expensive surfaces or causing layout thrashing.

Motion rules:
- page/section entrance: subtle fade + 4–12 px translate;
- cards: 120–220 ms hover/focus transitions;
- modal/drawer: 160–240 ms enter/exit;
- dropdown/popover: 120–180 ms;
- toast/notification: 180–260 ms;
- tab/segmented control: 140–220 ms;
- live transcript updates: smooth insertion without distracting auto-scroll jumps;
- skeletons: low-contrast shimmer/pulse only while loading;
- success feedback: brief opacity/scale cue, not a large celebration;
- errors: gentle attention transition, never shaking the whole page;
- navigation: preserve continuity instead of full-screen theatrical transitions.

Respect `prefers-reduced-motion`. When reduced motion is enabled, remove nonessential movement while preserving state changes and focus visibility.

Do not use animation to disguise slow APIs. The UI must expose real loading/progress/failure states.

## Interaction quality

Every interactive control must have:
- clear label/icon semantics;
- hover/focus/pressed/disabled states;
- keyboard operation;
- visible focus ring;
- confirmation for destructive actions;
- disabled/loading behavior that prevents duplicate submissions;
- meaningful accessible name;
- error text connected to the relevant field where applicable.

Avoid tiny icon-only controls for critical clinical actions unless the icon has a tooltip and accessible label.

## Clinical visual hierarchy

AI suggestions, evidence, warnings and clinician decisions must have separate visual treatments.

Use explicit badges/labels such as:
- AI SUGGESTION
- CLINICIAN REVIEW REQUIRED
- VERIFIED EVIDENCE
- INSUFFICIENT EVIDENCE
- WARNING
- CRITICAL SAFETY FLAG
- FINAL CLINICIAN DECISION

A clinician decision must visually dominate an AI suggestion once confirmed.

## States every screen must support

Loading, skeleton, success, empty, partial-data, validation-error, network-error, server-error, unauthorized, forbidden, degraded/offline, retrying, stale-data, and action-in-progress states where relevant.

Never show a permanent spinner with no timeout or escape path.

## Accessibility baseline

Target WCAG 2.2 AA-quality behavior:
- semantic HTML;
- keyboard navigation;
- visible focus;
- adequate contrast;
- labels for inputs;
- accessible error messages;
- logical heading structure;
- screen-reader-friendly status announcements for important asynchronous changes;
- reduced-motion support;
- touch targets large enough for reliable interaction.

## Frontend architecture

Build reusable primitives first:
Button, IconButton, Input, Textarea, Select, MultiSelect, Checkbox, RadioGroup, Switch, Tabs, Modal, Drawer, Tooltip, Popover, Dropdown, Toast, Alert, Badge, Card, Table, Pagination, Skeleton, EmptyState, ErrorState, StatusIndicator, TimelineItem, EvidenceCard, SafetyBanner, ConfidenceIndicator, AudioControls, TranscriptSegment, ClinicalFindingCard, DifferentialCard, MedicationReferenceCard, InvestigationCard, SourceCitation, AuditEvent, FileUploader.

Do not duplicate nearly identical visual components across pages.

---

# 4. REALTIME CONTRACT

All realtime features must use actual event-driven communication. Define typed event contracts and maintain them as code, not prose.

Required transport behavior:
- authenticated connection establishment;
- consultation/tenant authorization on connect;
- connection ID;
- monotonically increasing sequence number per stream;
- event timestamp;
- event type;
- typed payload;
- optional ACK metadata;
- heartbeat/ping-pong;
- stale connection detection;
- duplicate detection/idempotency;
- ordered processing;
- reconnect with bounded retry;
- visible connection state;
- manual fallback.

Reference state machine:
CONNECTING → CONNECTED → RECONNECTING → CONNECTED
                                      ↘ UNAVAILABLE

Target behavior:
- partial transcript visible within 2 seconds of speech where hardware/provider permits;
- automatic reconnect attempt within 3 seconds after a dropped connection;
- after 2 failed reconnect attempts, show “Live capture unavailable — switch to manual entry”;
- never lose already persisted transcript/manual work because a socket failed;
- never duplicate a transcript segment after reconnect.

---

# 5. DATA, AI, PROVENANCE AND SAFETY CONTRACT

Every clinically meaningful generated or retrieved object must preserve provenance. At minimum, where applicable, retain source record, model/provider/version, knowledge version, evidence IDs, timestamps, and the originating input artifact.

Approved knowledge only: source registered, access/licensing understood, content validated, review status approved, version tracked.

RAG pipeline must be:
query → retrieval → metadata filtering → reranking → evidence selection → claim validation → clinician presentation.

If evidence is insufficient, return an explicit insufficient-evidence state. Do not guess.

Safety evaluation is deterministic and independent of the language model. It can block/abstain/warn.

Confidence terminology must distinguish ranking score, model score, calibrated confidence estimate and medical probability. Only use probability language after validated calibration.

---

# 6. MINIMAL-DOCUMENTATION RULE

Do NOT make documentation a project phase or a prerequisite for coding.

Create only what is operationally necessary, such as:
- README setup commands;
- `.env.example`;
- migration files;
- typed schemas/interfaces;
- source/config comments when necessary;
- CI/CD configuration;
- security/configuration files;
- machine-readable test fixtures and evaluation manifests.

Do not create large requirements reports, UX reports, phase reports, architectural essays, or planning documents unless a specific runtime/deployment/security mechanism requires the file.

The agent should report progress in chat, not generate document packs.

---

# 7. STANDARD EXECUTION HEADER — PREFIX EVERY PHASE PROMPT

```text
Continue DocAssistIQ from the repository's current state.

Use the permanent engineering rules in the project context and follow the current phase only.

Before changing anything:
1. Inspect the repository and current runtime state.
2. Identify what is already implemented and what must be added.
3. Identify all affected frontend, backend, database, AI, infrastructure, security, and test surfaces.
4. State a concise implementation plan.

Then implement this phase completely.

Do not stop at scaffolding if the phase requires working behavior.
Do not create fake data or fake AI results.
Do not leave visible controls unconnected to real behavior.
Do not silently ignore failures.
Do not move to another phase.

After coding:
- format/lint/type-check;
- run unit tests;
- run integration tests where relevant;
- run migration checks where relevant;
- start the actual app where relevant;
- exercise API/browser behavior where relevant;
- test negative/failure paths;
- fix failures;
- inspect the Git diff;
- commit the completed phase.

Only report PASS when the required implementation was actually verified.
```

---

# 8. PHASE-BY-PHASE IMPLEMENTATION PROMPTS

Each phase below is intentionally written as a **complete implementation directive**, not a one-line feature request. The agent must implement the full behavior described by the current phase, including integration, UI states, security, and tests, while preserving previously completed work.

## PHASE 0 — Repository Initialization

```text
Start DocAssistIQ from absolute zero.

Create the real repository structure:

frontend/
backend/
ml/
data/
tests/
scripts/
infra/
docs/
.github/

Initialize Next.js + React + TypeScript + TailwindCSS.
Initialize FastAPI + Pydantic + SQLAlchemy + Alembic + pytest.

Create:
- .gitignore;
- .env.example;
- README.md with only necessary setup instructions;
- PROJECT_CONTEXT.md containing the permanent engineering rules.

Do not create clinical functionality yet.
Do not create fabricated medical data.

Verify the repository is clean and runnable.

### Additional mandatory implementation detail
Convert this phase into an implementation-ready bootstrap. Establish frontend/backend separation, environment conventions, developer scripts, test commands, and the minimum design system. The repository must be runnable immediately after this phase.

The coding agent must verify:
- `frontend` builds successfully;
- `backend` imports and starts successfully;
- type checking succeeds;
- Python lint/test commands exist and run;
- frontend lint/test commands exist and run;
- no secret is committed;
- no hard-coded database password/API key is introduced;
- `.env.example` contains variable names only;
- the initial Git state is understandable.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 1 — Development Containers and Infrastructure

```text
Build the actual local development environment.

Docker Compose must run:
- frontend;
- backend;
- PostgreSQL with pgvector;
- Redis;
- Celery worker;
- MinIO or equivalent local object-storage service if required by the architecture.

Implement:
- health checks;
- service dependencies;
- persistent database storage;
- environment configuration;
- startup/shutdown handling;
- dependency connection tests.

Test cold startup from a clean environment.
Test behavior when PostgreSQL or Redis is unavailable.

### Additional mandatory implementation detail
Implement actual local infrastructure, not placeholder service names. PostgreSQL, pgvector, Redis, Celery and object storage must be addressable through the configured application services. Add health/readiness checks that distinguish liveness from dependency readiness.

Failure behavior is part of the feature:
- database unavailable → readiness fails clearly while liveness remains diagnostic;
- Redis unavailable → Redis-dependent features expose degraded behavior rather than hanging;
- worker unavailable → queued-job UI/API can expose pending/degraded state;
- object storage unavailable → uploads fail explicitly and do not create false success records.

Include clean-start verification from an empty local data volume and safe restart behavior with persistent data where intended.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 2 — Backend Core

```text
Implement the FastAPI application foundation.

Create:
- application factory;
- settings/configuration;
- environment validation;
- router registration;
- /api/v1 namespace;
- global exception handler;
- structured logging;
- correlation/request ID middleware;
- CORS configuration;
- health endpoint;
- readiness endpoint;
- dependency injection foundation.

GET /health must indicate application health.
GET /ready must verify required local dependencies without making liveness dependent on AI availability.

Write tests.

### Additional mandatory implementation detail
Implement a production-shaped FastAPI core with dependency injection, typed settings, request IDs/correlation IDs, structured errors and safe logging. Define a clear error envelope and make frontend consumption predictable.

Every request must be observable without logging passwords, tokens, unnecessary raw clinical text or sensitive payloads. Health endpoints must not perform expensive model operations.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 3 — Database Core

```text
Implement SQLAlchemy database infrastructure.

Create:
- engine;
- session factory;
- transaction management;
- repository base patterns where justified;
- Alembic configuration;
- test database strategy.

Enable pgvector.

Test:
- connection;
- commit;
- rollback;
- migration;
- pgvector availability.

### Additional mandatory implementation detail
Implement transaction-safe SQLAlchemy infrastructure and Alembic from the start. Create test isolation so tests do not corrupt developer data. Verify migrations in both upgrade and downgrade paths where safe. Add indexes/constraints only when supported by actual access patterns.

No endpoint may silently commit partial state when a multi-record transaction fails.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 4 — Authentication

```text
Implement secure authentication.

User fields:
- id;
- email;
- password_hash;
- full_name;
- is_active;
- is_verified;
- created_at;
- updated_at.

Implement:
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET /api/v1/auth/me

Use secure password hashing and a secure JWT/session design.
Never expose password hashes.
Never log credentials/tokens.

Implement duplicate-email handling, password validation, token expiration and logout/session invalidation.

Build real frontend login/register pages and protected routing.

Test valid, invalid, expired, revoked and unauthorized cases.

### Additional mandatory implementation detail
Implement secure authentication end to end.

Frontend requirements:
- polished login/register screens;
- inline validation;
- disabled submit while pending;
- accessible password fields;
- network/server error presentation;
- session restoration;
- logout handling;
- redirect back to the protected destination when appropriate;
- no token leakage into visible UI.

Backend requirements:
- password hashing using a modern approved password-hashing scheme;
- secure session/JWT strategy with expiration and revocation behavior;
- generic login failure responses to reduce account enumeration;
- rate limiting or abuse protection where feasible;
- audit events for authentication lifecycle.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 5 — Authorization Foundation

```text
Implement reusable role/permission authorization.

Initial roles:
- doctor;
- admin.

Create reusable dependencies for:
- authenticated user;
- doctor;
- admin.

Do not implement complete enterprise RBAC yet.

Backend authorization must be enforced independently of frontend visibility.

Test direct API requests attempting unauthorized access.

### Additional mandatory implementation detail
Implement authorization as backend-enforced policy functions/dependencies. Build tests that directly call protected APIs with forged/insufficient roles and confirm denial even when a frontend control is hidden.

Create reusable authorization primitives that later phases can extend without rewriting route logic.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 6 — Core API Platform

```text
Implement the reusable API platform.

Include:
- request/response conventions;
- standard error responses;
- validation;
- pagination;
- safe filtering;
- whitelisted sorting;
- API versioning;
- correlation IDs;
- exception translation;
- OpenAPI summaries/descriptions;
- transaction conventions.

Every endpoint must use typed schemas.

Write integration tests.

### Additional mandatory implementation detail
Make the API platform predictable enough that every later frontend screen can consume it without special cases. Standardize pagination, filtering, sorting, validation and error structures. Include request IDs in errors so browser failures can be correlated with backend logs.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 7 — Frontend Application Shell

```text
Build the real authenticated application shell.

Create:
- authenticated layout;
- sidebar/navigation;
- top header;
- profile area;
- dashboard placeholder using real API state;
- centralized API client;
- auth state;
- loading states;
- error boundary;
- notifications;
- unauthorized/forbidden screens;
- responsive layout;
- accessibility foundation.

Do not use fake dashboard statistics.

### Additional mandatory implementation detail
Implement the visual system described in Section 3 and ensure every shell component is production-quality. Add responsive breakpoints, sidebar collapse/expand, header states, loading skeletons, error boundaries, toast notifications, keyboard support and reduced-motion behavior.

The dashboard must intentionally use real empty/loading states rather than fabricated metrics.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 8 — Walking Skeleton

```text
Build the first complete vertical slice.

Flow:
Register
→ Login
→ Dashboard
→ New Consultation
→ Manual text input
→ Analyze
→ Backend service
→ PostgreSQL
→ Response
→ UI

The analysis result is temporarily non-clinical and must be visibly marked:
PLACEHOLDER DEVELOPMENT RESPONSE — NOT CLINICAL

Also establish an authenticated WebSocket connection and show connection state:
LIVE / CONNECTING / RECONNECTING / UNAVAILABLE.

The placeholder must be removable without changing API architecture.

Verify the entire browser → API → DB → API → browser path.

### Additional mandatory implementation detail
Make this the first undeniable full-stack slice: a real browser action must hit a real API, persist real non-clinical development state, and return a typed response. The temporary analysis response may be non-clinical only and must be clearly labelled. Build the navigation and page transition experience as a real app, not a screenshot.

Verify refresh, direct route access, unauthorized access, backend failure, duplicate submission and WebSocket reconnect behavior.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 9 — Core Clinical Data Model

```text
Implement the production-oriented core domain schema.

Entities:
- Tenant placeholder/foundation;
- User;
- Role;
- Permission;
- Doctor;
- PatientSession;
- ConsentRecord;
- Consultation;
- ClinicalNote;
- ClinicalFinding;
- Symptom;
- Disease;
- Investigation;
- Medicine;
- Source;
- Evidence;
- Article;
- Feedback;
- AuditLog;
- FileObject;
- KnowledgeVersion.

Use relational modeling for relational data.
Use JSON only for genuinely semi-structured data.
Add indexes, foreign keys, unique constraints and status fields.

Add tenant/retention/provenance fields where required by later phases.

Create Alembic migrations.
Do not fabricate clinical evidence.

### Additional mandatory implementation detail
Design relationships carefully for future modules instead of creating a giant denormalized table. Include lifecycle/status fields, timestamps, tenant ownership, provenance and retention metadata where the entity needs them. Use explicit join tables for many-to-many clinical relationships.

Generate and test real migrations. Confirm foreign keys and uniqueness constraints prevent invalid state.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 10 — Doctor Profile and Verification

```text
Implement Doctor profiles.

Fields:
- user;
- medical credential reference;
- specialty;
- verification status;
- timestamps.

Statuses:
PENDING / VERIFIED / REJECTED

Admin can review verification.
Verified status must be enforceable by backend dependencies.

Test all states.

### Additional mandatory implementation detail
Build the doctor profile/verification workflow as a real admin-reviewed state machine. The doctor UI must show verification status and explain what is currently allowed or blocked. The backend must reject clinician-only operations from unverified users when the relevant feature requires verified status.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 11 — Secure File Storage

```text
Implement the FileObject abstraction.

Metadata:
- id;
- object key;
- filename;
- MIME type;
- size;
- checksum;
- owner;
- tenant;
- retention metadata;
- created_at;
- status.

Implement storage-provider interface.
Local development: MinIO or controlled local storage.

Support authorized upload/download/delete.
Validate type, size, filename and path traversal.
Never execute uploaded files.
Test unauthorized access and malformed uploads.

### Additional mandatory implementation detail
Implement secure file upload/download/delete as actual object-storage flows. Use generated object keys rather than user-controlled paths. Validate MIME type using server-side inspection where feasible, enforce size limits, checksum uploads, and verify authorization for every access.

Frontend uploader requirements: drag/drop plus browse, progress, cancellation where feasible, retry, validation errors, success state and clear degraded storage failure state.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 12 — Medical Source Registry

```text
Implement the Source registry.

Each source requires:
- organization;
- name;
- base URL/API;
- access mechanism;
- data type;
- license/access information;
- production suitability;
- last verification date;
- status.

Register appropriate real sources only after verifying current access/licensing requirements.

Examples to evaluate include:
PubMed/NCBI, PubMed Central, openFDA, RxNorm/RxNav, DailyMed, WHO resources,
ClinicalTrials.gov, Synthea, PhysioNet where authorized, and other appropriately licensed sources.

Do not hardcode access credentials.

### Additional mandatory implementation detail
Do not populate the knowledge base with invented content. Implement the source registry as the authority that later ingestion uses. Store provenance, access method, licensing/usage notes, verification date and active/deprecated state. Source adapters must be isolated so one source failure cannot corrupt other source jobs.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 13 — Knowledge Ingestion Framework

```text
Implement the general knowledge-ingestion framework.

Pipeline:
Source → Fetch → Parse → Validate → Normalize → Hash → Deduplicate → Version → Review Queue

Do not publish automatically.

Persist:
- raw artifact reference;
- source;
- source version;
- retrieval timestamp;
- content hash;
- validation result;
- review status.

Use Celery for background work.
Add retries with bounded backoff and explicit failure states.

### Additional mandatory implementation detail
Implement ingestion as idempotent background processing. A repeated fetch of unchanged content should not create duplicate active knowledge. Every stage must persist explicit success/failure/retry state. Use bounded retries and dead-letter/error visibility for persistent failure.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 14 — Knowledge Review and Publication

```text
Implement the controlled review workflow.

Statuses:
PENDING_REVIEW
APPROVED
REJECTED
SUPERSEDED
OUTDATED

Admin review endpoints:
- approve;
- reject;
- supersede;
- inspect provenance.

No knowledge may become production-active without the defined approval path.

Test duplicate, rejection, approval and rollback behavior.

### Additional mandatory implementation detail
Build the actual moderation/review UI and backend state transitions. Reviewers must see provenance, content, version, source metadata and validation results before approval. Rejecting or superseding content must not accidentally activate it.

Use optimistic UI only when it cannot create a false clinical state; otherwise wait for the confirmed server state.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 15 — Knowledge Quality and Versioning

```text
Implement knowledge-quality controls.

Track:
- publication date;
- retrieval date;
- effective date;
- version;
- content hash;
- credibility tier;
- evidence level;
- review state;
- superseded_by;
- outdated state.

Create knowledge snapshots/version IDs.

A later clinical result must identify the knowledge version used.

### Additional mandatory implementation detail
Implement immutable version identities for medical knowledge. A knowledge item that changes must create a new version or explicit supersession relationship rather than silently mutating the content used by historical clinical outputs.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 16 — AI Provider Abstraction

```text
Implement provider interfaces:
- SpeechToTextProvider;
- SpeakerDiarizationProvider;
- MedicalNLPProvider;
- EmbeddingProvider;
- RerankerProvider;
- GenerationProvider;
- DiagnosisProvider;
- OCRProvider;
- VisionProvider.

Each provider must expose typed contracts, configuration, model metadata, timeout and failure behavior.

Do not put model-specific code into business/domain services.

Implement only lightweight/local baseline providers where practical; do not download unnecessary large models.

### Additional mandatory implementation detail
Define stable provider interfaces and typed result/error contracts. Providers must expose model/provider metadata, capabilities, timeout handling and structured failure states. Business logic must depend on interfaces, not vendor SDK calls.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 17 — Dataset Registry and Governance

```text
Build a real dataset registry.

Dataset fields:
- name;
- source;
- license;
- version;
- hash;
- schema;
- record count;
- de-identification status;
- approval status;
- intended use;
- limitations.

Create data/raw, intermediate, processed, evaluation and synthetic directories.

Implement validation for:
- missing values;
- duplicates;
- malformed records;
- PII;
- label conflicts;
- leakage.

Only approved datasets can enter training/evaluation pipelines.

### Additional mandatory implementation detail
Implement dataset metadata and validation as executable code. PII detection must fail closed for data intended for ML. Dataset approvals are required before training/evaluation jobs consume the dataset.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 18 — Baseline Evaluation Harness

```text
Before tuning any large model, build the evaluation harness.

Support evaluation for:
- clinical information extraction;
- diagnosis ranking;
- retrieval;
- citation correctness;
- unsupported claims;
- hallucination;
- abstention;
- safety.

Create a fixed held-out evaluation set.
Prevent test leakage.

Do not invent metric results.

### Additional mandatory implementation detail
Build a repeatable evaluation runner with machine-readable results. Metrics must be computed from known ground truth or explicitly labeled as qualitative. No fabricated benchmark values. Keep a fixed held-out evaluation set separate from training data and make leakage checks executable.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 19 — Experiment Tracking Foundation

```text
Implement reproducible ML experiment metadata.

Every experiment records:
- experiment ID;
- code commit;
- dataset version/hash;
- preprocessing version;
- model/version;
- configuration;
- random seed;
- hardware;
- execution duration;
- metrics;
- artifact location.

Provide a reproducible CLI/script.

### Additional mandatory implementation detail
Make ML experiments reproducible from the CLI. Save run configuration and metadata automatically and make it possible to identify exactly which code/data/model produced an artifact.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 20 — Consultation Lifecycle

```text
Implement real consultation state management.

States:
CREATED
RECORDING
PROCESSING
DRAFT
UNDER_REVIEW
ANALYSIS_READY
FINALIZED
AMENDED

Implement APIs for create/start/pause/resume/end.

Enforce valid state transitions.
Reject invalid transitions.
Associate doctor, patient session and timestamps.
Add audit events.

### Additional mandatory implementation detail
Implement the consultation lifecycle as a validated state machine. Frontend buttons must be enabled only for legal transitions, while the backend independently rejects invalid transitions. Add idempotency where repeated start/end requests could otherwise duplicate actions.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 21 — Informed Consent

```text
Implement ConsentRecord.

Store:
- consultation;
- actor;
- actor relationship;
- consent text/version;
- purpose;
- timestamp;
- status;
- recording permission.

Voice recording must be impossible without an applicable consent record.
Manual entry remains available.

Build consent UI and backend enforcement.
Test direct API bypass attempts.

### Additional mandatory implementation detail
Treat consent as a first-class authorization artifact. Build clear clinician-facing consent status and recording permission state. The backend must verify consent at the moment recording starts, not only when the consultation was created.

Revocation must immediately prevent subsequent recording activity while preserving the previously recorded audit trail and explicitly defined retained artifacts.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 22 — Manual Clinical Intake

```text
Implement structured manual intake.

Fields:
- chief complaint;
- symptoms;
- duration;
- severity;
- onset;
- location;
- associated symptoms;
- aggravating factors;
- relieving factors;
- negations;
- past medical history;
- medications;
- allergies;
- family/social history;
- vitals;
- previous investigations.

Support draft/autosave/edit/delete.
Store structured findings separately from free text.
Never replace missing information with assumptions.

### Additional mandatory implementation detail
Build a clinically structured manual-intake form that is efficient for rapid typing. Use grouped sections, sensible defaults that do not invent facts, autosave indicators, draft recovery, validation, keyboard flow and unsaved-change protection.

Every structured finding must preserve whether it came from direct clinician input and must remain editable.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 23 — Realtime WebSocket Transport

```text
Harden the realtime channel.

Message envelope:
- type;
- connection ID;
- sequence number;
- timestamp;
- payload;
- acknowledgement metadata.

Support:
- authentication;
- heartbeat;
- disconnect;
- reconnect;
- duplicate detection;
- ordering;
- malformed-message rejection;
- stale connection handling.

Do not stream clinical audio yet.
Test all failure modes.

### Additional mandatory implementation detail
Implement one typed WebSocket event protocol used consistently across realtime features. Include authorization handshake, sequence numbers, heartbeat, ACK behavior, reconnect, duplicate suppression, ordered processing and explicit unavailable state.

Build a browser connection-status component that never lies about connection health.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 24 — Browser Audio Capture

```text
Implement microphone capture in the browser.

Support:
- permission request;
- start;
- pause;
- resume;
- stop;
- elapsed timer;
- device failure;
- device change.

Recording requires consent.
Do not lose captured text/manual work when recording fails.

### Additional mandatory implementation detail
Capture real browser audio with MediaRecorder or the appropriate browser API. Handle permission denial, unsupported formats, device removal, browser suspension, pause/resume, stop and cleanup. Do not retain microphone access after recording stops.

The UI must clearly distinguish idle, requesting permission, recording, paused, stopping, processing and unavailable states.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 25 — Streaming Speech-to-Text

```text
Implement actual realtime ASR.

Pipeline:
Browser microphone
→ audio chunks
→ authenticated WebSocket
→ backend realtime service
→ ASR provider
→ partial/final transcript
→ WebSocket
→ browser

Use a suitable self-hosted/open-source implementation such as faster-whisper where practical.

Implement:
- chunk sequencing;
- buffering;
- backpressure;
- timestamps;
- partial/final distinction;
- error state;
- reconnect;
- persistence.

Meet the established realtime p95 target where hardware permits.
If ASR fails, preserve work and immediately expose manual fallback.

### Additional mandatory implementation detail
Implement actual streaming ASR provider integration behind the abstraction. Chunk audio without loss, attach sequence/timestamp metadata, buffer out-of-order events, distinguish interim from final text, persist final segments, and recover from reconnects without duplicated text.

Meet the project latency target where hardware/provider permits and show measured latency. Never simulate “live” transcription using delayed fake strings.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 26 — Speaker Diarization

```text
Implement speaker-turn handling behind SpeakerDiarizationProvider.

If real diarization is unavailable:
- retain raw transcript;
- use clearly labeled heuristic turns only if needed;
- expose uncertainty.

Transcript segment fields:
- speaker;
- start;
- end;
- text;
- confidence;
- source.

Evaluate diarization separately.

### Additional mandatory implementation detail
Implement speaker attribution as a provider capability, not a hardcoded transcript transformation. If diarization confidence is low or unavailable, show that uncertainty and keep the raw transcript intact.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 27 — Transcript Management

```text
Implement transcript persistence and correction.

Maintain separately:
- raw ASR transcript;
- processed transcript;
- clinician-corrected transcript.

Support:
- timestamps;
- speaker labels;
- search;
- correction;
- versioning;
- audit.

Do not overwrite original ASR output.

### Additional mandatory implementation detail
Create a transcript editor where raw ASR output, processed output and clinician-corrected output are separate versions. Changes must be auditable. Search and navigation should jump to timestamps/speaker turns. Realtime updates must not overwrite text the clinician is currently editing.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 28 — Clinical NLP Extraction V1

```text
Implement deterministic clinical information extraction.

Extract:
- symptoms;
- signs;
- duration;
- severity;
- location;
- onset;
- associated symptoms;
- negation;
- temporality;
- medications;
- allergies;
- history;
- family/social factors;
- vitals;
- investigations.

Represent findings as:
concept, value, certainty, negated, temporality, source, confidence.

Do not infer missing information.
Create comprehensive tests including negation and temporality.

### Additional mandatory implementation detail
Build deterministic clinical extraction first. The extractor must represent negation, temporality, certainty and provenance explicitly. Avoid brittle regex-only behavior where a structured parser/tokenizer is more appropriate, while keeping the baseline explainable and testable.

Include adversarial tests such as “no fever”, “history of asthma”, “previous episode”, “denies chest pain”, ambiguous abbreviations and conflicting statements.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 29 — Clinical Concept Normalization

```text
Implement concept normalization.

Map:
- spelling variations;
- synonyms;
- abbreviations;
- common clinical phrasing

to canonical internal concepts where the mapping is verified.

Store raw value + canonical concept + mapping source + confidence.
Unknown/ambiguous concepts must remain explicit.
Prepare extension for licensed SNOMED/UMLS integration where permitted.

### Additional mandatory implementation detail
Normalize only verified mappings. Preserve raw user text and the canonical concept separately. Ambiguous mappings must remain unresolved rather than being force-mapped to a potentially wrong concept.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 30 — Clinical Note Generation

```text
Implement structured note drafting.

Sections:
- Chief Complaint;
- History of Present Illness;
- Past Medical History;
- Medication History;
- Allergies;
- Family History;
- Social History;
- Examination;
- Investigations;
- Assessment;
- Plan.

AI may draft factual sections from extracted information.
It must not invent facts, vitals or examination findings.
Assessment and Plan remain clinician-controlled.

Persist original draft, doctor edits and version history.

### Additional mandatory implementation detail
Generate only evidence-supported factual note sections from structured inputs. Clearly mark AI-drafted content. Assessment and Plan must remain explicitly clinician-controlled. Preserve version history and prevent background jobs from overwriting active clinician edits.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 31 — Note Review Workspace

```text
Build the doctor note-review interface.

Show:
- extracted facts;
- source segment where possible;
- confidence;
- AI draft;
- doctor-edited version.

Allow:
- edit;
- save;
- revert;
- accept section;
- reject section.

Background AI processing must not overwrite clinician edits.

### Additional mandatory implementation detail
Build a high-quality split-pane note review workspace. Support source-to-note traceability where available, section-level accept/reject, edit, undo/revert, autosave state and conflict protection.

Visual hierarchy: clinician-edited text must appear authoritative; AI draft must carry a persistent AI SUGGESTION label until accepted.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 32 — Structured Clinical Representation

```text
Create the canonical ClinicalRepresentation used by downstream intelligence.

Unify:
- patient context where permitted;
- symptoms;
- negations;
- duration;
- severity;
- history;
- medications;
- allergies;
- vitals;
- investigations;
- report findings.

Every finding must preserve provenance to manual input, transcript or report.
Missing information remains missing.

### Additional mandatory implementation detail
Create one canonical ClinicalRepresentation contract that downstream services consume. Version the representation schema and preserve per-field provenance. Do not let different pages calculate subtly different versions of the same clinical fact.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 33 — Baseline Differential Diagnosis

```text
Implement transparent differential ranking.

Pipeline:
ClinicalRepresentation
→ normalization
→ candidate generation
→ feature matching
→ scoring
→ ranking
→ missing information
→ contradictions

Use a transparent baseline such as weighted overlap/Jaccard/cosine matching using sourced disease/symptom data.

Return Top 5.

For each:
- disease;
- ranking/model score;
- supporting findings;
- missing expected findings;
- contradicting information;
- uncertainty;
- explanation reference.

Do not call the score a medical probability.

### Additional mandatory implementation detail
Implement the baseline differential algorithm transparently. Candidate generation, feature weighting and ranking must be inspectable in code and tied to sourced disease/symptom data. Return Top-5 plus supporting evidence, missing expected findings, contradictions and uncertainty.

The UI must not imply certainty. The ranking is a decision-support suggestion pending clinician review.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 34 — Diagnosis Provider Abstraction

```text
Create DiagnosisProvider interface.

Implement:
BaselineDiagnosisProvider

Prepare but do not require:
MLDiagnosisProvider
FoundationModelDiagnosisProvider

API contract must remain stable across provider replacement.
Add model/version metadata and error handling.

### Additional mandatory implementation detail
Lock the DiagnosisProvider contract before adding more advanced models. All providers must return the same domain-level result shape so the UI and safety layer do not depend on a specific model vendor.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 35 — Differential UI

```text
Build the Top-5 differential UI.

Display:
- rank;
- disease;
- model score/confidence estimate;
- supporting findings;
- contradicting findings;
- missing information;
- evidence availability;
- safety state.

Actions:
- select candidate;
- Why?;
- compare;
- review evidence.

Clearly label:
AI DIFFERENTIAL SUGGESTION

Doctor confirmation is separate.

### Additional mandatory implementation detail
Build polished differential cards with clear ranking, evidence state, support/contradiction sections, missing information, safety status and Why action. Use progressive disclosure so clinicians can scan Top-5 quickly and inspect detail on demand.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 36 — Embedding Infrastructure

```text
Implement EmbeddingProvider and pgvector storage.

Track:
- embedding model;
- dimensions;
- model version;
- generated_at;
- source record;
- content hash.

Support embeddings for evidence and future cases.
Do not add a separate vector database.

### Additional mandatory implementation detail
Use pgvector with explicit embedding model/version and content hash tracking. Add indexes appropriate for actual query patterns. Handle embedding generation failures without marking an evidence item searchable when no valid embedding exists.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 37 — RAG Retrieval

```text
Implement evidence-grounded RAG.

Pipeline:
Clinical query
→ query construction
→ embedding
→ pgvector retrieval
→ metadata filters
→ reranking
→ selected evidence
→ citation validation

Filter by:
- review status;
- credibility tier;
- evidence level;
- publication/recency where appropriate;
- current knowledge version.

Use Redis caching where clinically safe.

If evidence is insufficient, return insufficient_evidence=true rather than guessing.

### Additional mandatory implementation detail
Build hybrid-friendly retrieval that can later combine metadata filtering with vector retrieval and lexical search if justified. Never retrieve unpublished/rejected/superseded content. Cache only results that are safe to reuse for the same knowledge/model/version context.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 38 — Claim-Level Citation Verification

```text
Implement claim-to-evidence validation.

For each claim verify:
- evidence ID exists;
- source exists;
- source is approved;
- knowledge version is valid;
- evidence has not been superseded;
- referenced excerpt exists;
- association is appropriate.

Unsupported claims must not be presented as verified evidence.

Test fabricated IDs, missing sources, outdated evidence and mismatched claims.

### Additional mandatory implementation detail
Implement claim-level validation as a real service, not a UI badge. A citation can only appear as verified when the underlying source/evidence/version checks pass. Unsupported claims must be clearly labeled or removed from the verified-evidence presentation.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 39 — Clinical Explanation / Why?

```text
Implement the Why? service.

Return:
- supporting findings;
- contradicting findings;
- missing information;
- linked investigations;
- supporting evidence;
- evidence level/credibility;
- safety flags;
- model/knowledge versions.

Do not expose hidden chain-of-thought.
Provide concise, auditable, evidence-backed explanations.

Build the Why? UI.

### Additional mandatory implementation detail
The Why? feature must explain the decision-support output using auditable factors, evidence links and missing/contradicting findings. Do not expose hidden chain-of-thought, private reasoning traces or internal model deliberation.

Use expandable evidence sections and source links that open the exact relevant source record/excerpt.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 40 — Clinical Knowledge Graph

```text
Implement the evidence graph using PostgreSQL tables.

Relations:
Symptom → Disease
Disease → Investigation
Disease → Evidence
Disease → Medicine
Medicine → Contraindication
Medicine → Interaction
→ Evidence

Create graph service interface.

Implement real traversal for disease explanations.
No hardcoded explanation responses.

### Additional mandatory implementation detail
Implement knowledge-graph traversal from stored relationships, not static strings. The graph service must respect source status, version and tenant/authorization scope where applicable.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 41 — Safety Engine Foundation

```text
Implement a centralized deterministic SafetyEngine.

Input:
- clinical representation;
- AI suggestion;
- evidence;
- medication/reference context.

Check:
- red flags;
- missing critical information;
- contradictions;
- allergy conflicts;
- contraindications;
- interactions;
- evidence insufficiency;
- uncertainty.

Return:
ALLOW / WARN / ABSTAIN

Every SafetyFlag contains:
- rule ID;
- rule version;
- category;
- severity;
- message;
- source;
- related entity;
- timestamp.

### Additional mandatory implementation detail
Make SafetyEngine deterministic, versioned and independently testable. Safety must be able to return ALLOW/WARN/ABSTAIN independently of model availability. A critical safety result must dominate lower-priority suggestions in the UI.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 42 — Red-Flag Rules

```text
Create versioned red-flag detection rules for development/testing.

Examples may include patterns involving:
- severe breathing difficulty;
- stroke-like symptoms;
- severe chest pain;
- anaphylaxis-like symptoms;
- altered consciousness.

Do not claim complete emergency detection coverage.

Critical warnings must be prominently surfaced.

Test positive, negative, contradictory and borderline cases.

### Additional mandatory implementation detail
Implement red-flag rules as versioned machine-readable rules with unit tests. Keep the scope explicit: the rule set is not complete emergency medicine coverage. Avoid broad claims that a small ruleset can detect every emergency.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 43 — Uncertainty / Missing Information Gate

```text
Implement uncertainty handling.

Identify missing information relevant to downstream reasoning.

If the case lacks sufficient information:
- show missing information;
- reduce confidence where justified;
- warn;
- or abstain.

Never fill missing values by hallucination.

Test incomplete, contradictory and ambiguous consultations.

### Additional mandatory implementation detail
Create explicit missing-information and contradiction objects that downstream UI can render. The system should be able to state “insufficient information” rather than forcing a ranking when required inputs are absent.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 44 — Investigation Intelligence

```text
Implement clinician-facing investigation reference intelligence.

For selected diagnosis/candidate return:
HIGH PRIORITY
CONDITIONAL
IF INDICATED

Each investigation:
- name;
- rationale;
- relevant clinical finding;
- evidence;
- limitations;
- safety flags;
- provenance.

Never represent this as an automatically ordered test.

### Additional mandatory implementation detail
Investigation suggestions are reference intelligence only. Show why an investigation may be relevant, what is missing, evidence and limitations, but never issue an order. Use clinician-friendly grouping such as high priority/conditional/if indicated.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 45 — Medication Reference Intelligence

```text
Implement reference-only medication intelligence.

For supported medicines include:
- generic name;
- indication;
- formulation;
- route;
- standard reference dosing;
- contraindications;
- interactions;
- allergy considerations;
- renal considerations;
- hepatic considerations;
- pregnancy/lactation considerations;
- age considerations;
- monitoring/reference information;
- source/evidence.

If information is unavailable in approved sources, return unavailable.
Do not generate a dosage merely because the model knows one.

Every screen must state:
REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED

No prescribe/order workflow.

### Additional mandatory implementation detail
Medication reference pages must be sourced, versioned and visibly labeled “REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED”. If an approved source does not contain a requested field, show unavailable rather than generating a plausible value.

Do not include a prescription checkout/order/sending workflow.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 46 — Medication Safety Engine

```text
Implement independent deterministic medication safety checks.

Check:
- allergy;
- drug-drug interaction;
- drug-disease contraindication;
- duplicate therapy;
- renal context;
- hepatic context;
- pregnancy context;
- age context.

The LLM must not be the sole interaction/contraindication checker.

Safety checks must work even when the LLM is unavailable.

### Additional mandatory implementation detail
Implement deterministic medication-safety checks with explicit input assumptions and rule provenance. The safety engine must handle missing medication context conservatively and never claim “safe” merely because no rule matched.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 47 — Verified Doctor Knowledge Hub

```text
Implement doctor-authored knowledge.

Workflow:
Draft
→ Submitted
→ Under Review
→ Approved/Rejected
→ Published
→ Indexed

Only verified doctors can submit.
Doctors cannot approve their own articles.

Store:
- author;
- specialty;
- disease;
- title;
- content;
- references;
- version;
- reviewer;
- status;
- timestamps.

Doctor-authored material must remain distinguishable from authoritative evidence.

### Additional mandatory implementation detail
Build the full article authoring/moderation UI with draft autosave, validation, references, reviewer workflow, revision history and publishing status. Clearly distinguish doctor-authored material from authoritative external evidence everywhere it appears.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 48 — Continuous Knowledge Update

```text
Implement scheduled knowledge updates.

Pipeline:
Scheduler
→ approved source adapter
→ fetch
→ parse
→ validate
→ normalize
→ hash
→ deduplicate
→ version compare
→ review queue
→ approval
→ production
→ embedding

Support retries, timeouts, source outages, rollback and outdated content.

Never automatically publish fetched medical content.

### Additional mandatory implementation detail
Scheduled knowledge updates must be observable and idempotent. A source outage must not automatically mark previously approved knowledge as invalid without an explicit rule. New content enters review; it does not silently replace the production corpus.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 49 — Clinician Feedback Loop

```text
Implement Accept / Modify / Reject for:
- clinical note extraction;
- diagnosis;
- investigation;
- medication reference.

Store:
- suggestion ID;
- type;
- doctor;
- decision;
- reason;
- timestamp;
- model version;
- knowledge version.

Do not automatically retrain production from feedback.

Feedback is governed evaluation data.

### Additional mandatory implementation detail
Feedback must capture the exact suggestion version/context that the doctor accepted, changed or rejected. The workflow must make it easy for clinicians to give a reason without interrupting the consultation excessively. Feedback is evaluation data, not automatic production retraining.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 50 — Historical Case-Based Reasoning

```text
Implement similar-case retrieval.

Allowed data:
- synthetic;
- authorized de-identified;
- properly licensed.

Pipeline:
Current case
→ clinical representation
→ embedding
→ pgvector similarity
→ privacy filter
→ similar cases

Return only non-identifying information.

Label:
SIMILAR HISTORICAL CASE — NOT EVIDENCE OF CURRENT DIAGNOSIS

Test that identifying fields can never be returned.

### Additional mandatory implementation detail
Similar-case retrieval must apply privacy filtering before anything reaches the browser. Strip identifiers and never allow similarity retrieval to expose a patient’s identity or unrelated sensitive data. Display a persistent warning that historical similarity is not current diagnostic evidence.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 51 — Medical Report Analyzer

```text
Implement medical report processing.

Support initially:
- PDF;
- PNG;
- JPG.

Pipeline:
Upload
→ validation
→ secure storage
→ OCR/document parsing
→ structured extraction
→ reference range detection
→ potential abnormality flagging
→ clinician review.

Extract:
- test;
- value;
- unit;
- reference range;
- flag;
- source location.

Do not convert an abnormal result directly into a diagnosis.

### Additional mandatory implementation detail
Build secure report upload and extraction with page/region provenance. Reference-range and abnormality detection must distinguish a reported lab flag from clinical interpretation. The final UI should make “potentially abnormal” visibly different from “diagnosis”.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 52 — Medical Image Processing Abstraction

```text
Create a separate VisionProvider pipeline for actual image processing.

Do not use OCR as the medical image interpretation mechanism.

Pipeline:
Image
→ validation
→ preprocessing
→ vision provider
→ structured findings
→ evidence
→ safety
→ clinician review.

If no validated vision model is available, expose unavailable state rather than inventing findings.

### Additional mandatory implementation detail
Keep image processing architecturally separate from document OCR. Implement validation, size/type checks, preprocessing metadata, provider result contracts and explicit unavailable state. Never fabricate image findings when a validated vision provider is absent.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 53 — Multimodal Fusion

```text
Combine available modalities:
- manual text;
- transcript;
- structured findings;
- report findings;
- image findings where supported.

Use structured clinical outputs rather than blindly concatenating embeddings.

Track modalities_used and per-finding provenance.

Test:
- text only;
- voice + text;
- text + report;
- voice + report;
- image-supported flow;
- one modality failure.

Text-only mode must remain unchanged.

### Additional mandatory implementation detail
Fuse modalities through canonical structured findings with provenance. A failed image/report/voice modality must not invalidate successfully captured modalities. The UI should identify which modalities contributed to each downstream result.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 54 — Patient Timeline

```text
Implement chronological clinical timeline.

Include:
- consultations;
- notes;
- doctor decisions;
- investigations;
- reports;
- medication references;
- amendments.

Support:
- chronology;
- filters;
- expandable entries;
- permission checks;
- tenant isolation;
- auditing.

### Additional mandatory implementation detail
Build the patient timeline as a fast, filterable chronological view that reuses real domain events. Every item must obey tenant and authorization checks. Provide expandable detail without overwhelming the primary consultation experience.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 55 — Enterprise RBAC

```text
Implement full roles:
- SUPER_ADMIN
- HOSPITAL_ADMIN
- DOCTOR
- NURSE
- LAB_TECHNICIAN
- AUDITOR

Implement real permission matrix.

Examples:
Doctor: clinical workflow and decision-support review.
Nurse: intake and note assistance within permissions.
Lab Technician: report management.
Auditor: read-only audit/evaluation.
Hospital Admin: hospital administration.
Super Admin: system-level administration.

Backend authorization is mandatory.
Frontend hiding is only a UX feature, never a security boundary.

### Additional mandatory implementation detail
Implement the permission matrix as code, not a spreadsheet. Test each high-risk permission both positively and negatively. Roles must be combinable with resource/tenant restrictions rather than being treated as unconditional global access.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 56 — Multi-Tenancy

```text
Implement hospital/tenant isolation.

Relevant records require tenant scope.

Every repository query must enforce:
User identity
→ Role
→ Permission
→ Tenant
→ Resource
→ Action

Test:
- cross-tenant reads;
- cross-tenant updates;
- cross-tenant file downloads;
- timeline leakage;
- IDOR;
- privileged user without explicit cross-tenant permission.

### Additional mandatory implementation detail
Implement tenant scoping at the repository/service layer so developers cannot accidentally forget tenant filters in a single endpoint. Add automated cross-tenant security tests for every sensitive resource family.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 57 — Audit System

```text
Implement comprehensive audit logging.

Audit events include:
- authentication;
- consultation access;
- note modification;
- AI generation;
- diagnosis execution;
- evidence access;
- doctor decision;
- feedback;
- article moderation;
- knowledge approval;
- role changes;
- finalization;
- amendment;
- deletion;
- report access.

Avoid storing unnecessary sensitive clinical content in the audit record.

### Additional mandatory implementation detail
Audit events must be immutable from application code paths accessible to normal users. Store actor, action, target, tenant, timestamp, correlation ID and safe metadata without logging unnecessary clinical payloads.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 58 — Privacy, Retention and Deletion

```text
Implement configurable retention policies.

Support retention for:
- consultations;
- transcripts;
- audio;
- reports;
- patient-linked records;
- audit data;
- knowledge artifacts;
- embeddings;
- derived clinical representations.

Implement:
- scheduled purge;
- deletion request;
- object-storage deletion;
- database deletion;
- derived-data deletion;
- embedding deletion;
- audit tombstone.

The deletion workflow must be explicit and auditable.
Do not claim legal compliance automatically.

### Additional mandatory implementation detail
Deletion/retention must account for primary records, derived representations, embeddings and object storage. Use explicit deletion jobs and auditable tombstones where an audit trail must survive the deletion of clinical content.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 59 — AI Model Development Environment

```text
Create the actual ML development environment.

Structure:
ml/
├── configs/
├── preprocessing/
├── features/
├── training/
├── evaluation/
├── inference/
└── experiments/

Provide reproducible command-line workflows.
Detect:
- CPU;
- GPU;
- VRAM;
- CUDA/PyTorch compatibility.

If hardware is insufficient for a requested experiment, fail clearly and provide a supported execution configuration rather than pretending training succeeded.

### Additional mandatory implementation detail
Make ML development reproducible and resource-aware. Detect hardware capabilities before launching heavy work. Fail clearly if the requested experiment cannot run on the available environment.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 60 — Classical ML Diagnosis Baseline

```text
Build a measurable classical ML diagnosis baseline where the approved dataset supports it.

Potential approaches:
- logistic regression;
- random forest;
- gradient boosting/XGBoost;
- transparent similarity baseline.

Compare against the feature-overlap baseline.

Evaluate:
- Top-1;
- Top-3;
- Top-5 recall;
- class-wise performance;
- abstention;
- latency.

Store experiment metadata.

### Additional mandatory implementation detail
Compare classical models against the transparent baseline on the same held-out evaluation split. Save prediction artifacts/metrics and latency. Do not promote a model simply because one aggregate metric improves; review class-wise and safety/abstention behavior.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 61 — Foundation Model Evaluation

```text
Evaluate suitable pretrained models before fine-tuning.

Compare:
- deterministic baseline;
- biomedical/pretrained model;
- foundation model with structured prompting;
- medical foundation model;
- model + RAG.

Measure:
- quality;
- latency;
- memory;
- evidence grounding;
- hallucination;
- safety;
- abstention;
- resource requirements.

Do not select a model merely because it is large or popular.

### Additional mandatory implementation detail
Evaluate model quality as a multidimensional engineering decision: quality, grounding, safety, latency, memory, reliability and cost/resource needs. Keep model adapters isolated so experiments cannot break the production baseline.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 62 — Medical Foundation Model / MedGemma Integration

```text
Evaluate a suitable medical foundation model such as MedGemma if its current access terms, intended use, licensing and hardware requirements permit.

Implement it behind GenerationProvider/DiagnosisProvider/MedicalNLPProvider interfaces as appropriate.

Record:
- model name;
- model version;
- source;
- configuration;
- runtime resources;
- inference latency.

Do not yet replace the baseline in production.

Use the model only inside controlled research/evaluation paths until it passes evaluation and safety review.

### Additional mandatory implementation detail
Only integrate a medical foundation model after verifying current access terms, licensing, intended use and runtime requirements. Put it behind the provider abstraction and keep it in controlled evaluation/research mode until the project’s evaluation and safety gates pass.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 63 — PEFT / LoRA / QLoRA Training

```text
If Phase 63 shows a justified need for tuning, implement parameter-efficient fine-tuning.

Never train from scratch.
Never train on identifiable patient data.

Pipeline:
Approved dataset
→ validation
→ deduplication
→ leakage detection
→ train/validation/test
→ tokenizer
→ base model
→ LoRA/QLoRA
→ validation
→ safety evaluation
→ benchmark comparison
→ model registry.

Record:
- base model;
- adapter;
- dataset version;
- preprocessing version;
- hyperparameters;
- hardware;
- random seed;
- code commit;
- training run;
- metrics.

Never overwrite the base model.

### Additional mandatory implementation detail
PEFT/LoRA/QLoRA jobs must have explicit dataset/version/config provenance, checkpoint handling, resumability where practical, evaluation before release and clean separation from production artifacts. Never overwrite the base model.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 64 — Model Calibration and Abstention

```text
Implement calibration only where the evaluation labels support it.

Pipeline:
Raw score
→ calibration
→ confidence estimate
→ uncertainty
→ threshold
→ suggest or abstain.

Evaluate:
- Expected Calibration Error;
- Brier score;
- calibration curve;
- confidence vs accuracy;
- selective risk;
- abstention coverage.

Do not display probabilities without validated calibration.

### Additional mandatory implementation detail
Calibration is evidence-driven. Do not add a calibration layer when the dataset does not support it. Where supported, evaluate calibration stability on held-out data and expose confidence terminology accurately in the UI.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 65 — Model Registry and Release Management

```text
Create model registry.

Lifecycle:
EXPERIMENTAL
→ EVALUATED
→ CANDIDATE
→ SAFETY_REVIEW
→ APPROVED
→ STAGING
→ PRODUCTION
→ RETIRED

Store:
- model ID/version;
- base model;
- adapter;
- dataset version;
- evaluation version;
- safety results;
- artifact hash/location;
- deployment date;
- rollback version.

Historical AI outputs must retain the model version that generated them.

### Additional mandatory implementation detail
The model registry must prevent a model from entering production merely because an artifact exists. Require evaluation metadata, safety review status and deployment approval. Historical clinical outputs retain their generating model/knowledge context.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 66 — AI Observability

```text
Instrument:
- AI inference latency;
- ASR latency;
- embedding latency;
- retrieval latency;
- reranking latency;
- model errors;
- timeout rate;
- evidence failure;
- citation failure;
- safety flags;
- abstention.

Use correlation IDs.
Do not log raw clinical text by default.

### Additional mandatory implementation detail
Instrument AI and realtime latency using server-side timings plus request/trace IDs. Build dashboards/metrics that distinguish provider latency from queueing, serialization, database, retrieval and browser-delivery latency.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 67 — Alerting

```text
Implement operational alerting for:
- API error spikes;
- database failures;
- Redis failures;
- worker failures;
- WebSocket failures;
- realtime latency breaches;
- model failures;
- RAG failures;
- knowledge-ingestion failures.

Document actionable thresholds and operator response.

### Additional mandatory implementation detail
Alerts must be actionable and low-noise. Define severity, trigger, cooldown/deduplication and operational context. A latency alert should identify which stage breached the target rather than merely stating “AI slow”.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 68 — Security Hardening

```text
Perform application security hardening.

Check:
- password security;
- JWT/session security;
- rate limiting;
- secure headers;
- CORS;
- input validation;
- SQL injection defenses;
- XSS defenses;
- CSRF strategy where applicable;
- file validation;
- object-storage permissions;
- secret management;
- TLS;
- sensitive logging;
- authorization;
- tenant isolation.

Fix high-risk issues before deployment.

### Additional mandatory implementation detail
Run a security-hardening pass against the real deployed configuration, not only source code. Review authentication, authorization, CORS, headers, cookies/tokens, uploads, rate limits, secrets, SQL access, dependency risks, WebSocket authorization and tenant boundaries.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 69 — Threat Modeling and AI Red Team

```text
Threat-model:
- browser;
- REST API;
- WebSocket;
- authentication;
- uploads;
- object storage;
- database;
- Redis;
- Celery;
- LLM prompts;
- RAG documents;
- doctor-authored articles;
- tenant boundaries;
- administration.

Test:
- spoofing;
- tampering;
- repudiation;
- information disclosure;
- denial of service;
- privilege escalation;
- prompt injection;
- retrieval poisoning;
- document injection;
- data exfiltration.

External content must always be treated as untrusted data.

### Additional mandatory implementation detail
Execute adversarial tests against both ordinary application security and AI-specific attack paths. Treat external content as hostile input. Test prompt injection in retrieved documents, data exfiltration attempts, malicious uploads, forged WebSocket messages and cross-tenant references.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 70 — Clinical AI Evaluation Platform

```text
Build the production evaluation pipeline.

Measure:
NLP:
- precision;
- recall;
- F1;
- negation;
- temporality.

Diagnosis:
- Top-1;
- Top-3;
- Top-5 recall;
- MRR;
- calibration;
- abstention/selective risk.

RAG:
- precision@K;
- recall@K;
- MRR;
- relevance;
- citation validity.

Generation:
- unsupported claim rate;
- hallucination rate.

Safety:
- red-flag sensitivity;
- false negatives;
- false positives;
- abstention.

Human:
- accept;
- modify;
- reject.

Store dated results by model/version.

### Additional mandatory implementation detail
Make clinical AI evaluation executable on demand and in CI where practical. Track metrics by model/version/dataset/version and do not overwrite previous results. Include safety and abstention, not only accuracy.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 71 — Performance and Realtime SLA Validation

```text
Measure real system performance against the established NFR targets.

Collect:
- API p50/p95/p99;
- DB latency;
- pgvector latency;
- embedding latency;
- reranker latency;
- LLM latency;
- ASR latency;
- WebSocket delay;
- reconnect time;
- Celery queue time;
- CPU;
- RAM;
- GPU;
- concurrent consultations.

Load-test at least the agreed baseline concurrency.
Optimize only after measuring the bottleneck.

### Additional mandatory implementation detail
Measure the actual end-to-end user experience, not just isolated function durations. Load-test realistic concurrent consultations, realtime streams, retrieval, note autosave and background processing. Optimize only after identifying the measured bottleneck.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 72 — Complete Clinical Workspace

```text
Assemble the complete doctor consultation workspace.

Sections:
- consultation header;
- consent state;
- live transcript;
- manual input;
- extracted clinical facts;
- clinical note;
- Top-5 differential;
- Why?;
- evidence;
- safety;
- investigations;
- medication reference;
- similar cases;
- reports;
- doctor feedback;
- doctor decision;
- finalize.

AI suggestion and doctor decision must be visually distinct.
No hidden/manual API actions should be required from the doctor.

### Additional mandatory implementation detail
Now assemble all previously implemented features into one coherent clinician workspace. Remove any need for the doctor to manually call APIs or navigate fragmented admin-style screens for the primary consultation workflow.

Use a clear visual rhythm: patient/session context → capture/input → extracted facts → note → differential → evidence/Why → safety → references → historical context → final clinician action.

Use resizable/split panes only where they improve comparison. Preserve work when navigating between sections.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 73 — Clinical Finalization and Immutable Record

```text
Implement finalization.

Workflow:
DRAFT
→ DOCTOR_REVIEW
→ DOCTOR_DECISION
→ FINALIZED

Final record must contain:
- transcript reference;
- clinical note;
- doctor edits;
- accepted diagnosis;
- accepted investigations;
- accepted medication references;
- evidence references;
- model version;
- knowledge version;
- approval timestamp;
- audit trail.

After finalization:
- no silent edits;
- explicit amendment only;
- original preserved;
- amendment reason;
- actor and timestamp;
- version history.

Generate a professional PDF.

### Additional mandatory implementation detail
Finalization must be explicit, reviewable and irreversible except through an amendment process. Present a final review summary before confirmation. Prevent duplicate finalization and preserve a complete version chain.

Generate the final PDF from stored final state, not from arbitrary current browser DOM.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 74 — Complete Automated Test Suite

```text
Run a complete regression suite.

Backend:
- unit;
- integration;
- API;
- database;
- auth;
- authorization;
- tenant isolation;
- safety;
- RAG;
- knowledge ingestion;
- file handling;
- model contract.

Frontend:
- component;
- interaction;
- accessibility;
- browser workflows.

ML:
- dataset validation;
- benchmark;
- regression;
- calibration;
- adversarial.

Security:
- auth abuse;
- IDOR;
- privilege bypass;
- malicious uploads;
- prompt injection;
- rate limiting.

Fix failures, then rerun the complete suite.

### Additional mandatory implementation detail
Treat the test suite as release infrastructure. Add regression tests for every major defect found in earlier phases. Cover permission boundaries, safety, failure recovery and browser workflows in addition to happy paths.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 75 — End-to-End Doctor Verification

```text
Perform the complete browser workflow:

Register
→ Login
→ Doctor verification
→ Dashboard
→ New Consultation
→ Consent
→ Manual/Voice input
→ Live transcript
→ Clinical extraction
→ Note review
→ Note edit
→ Differential
→ Top-5
→ Why?
→ Evidence
→ Safety
→ Investigations
→ Medication reference
→ Similar cases
→ Reports
→ Feedback
→ Doctor decision
→ Finalize
→ PDF

Also run failure cases:
- no consent;
- ASR unavailable;
- WebSocket failure;
- RAG unavailable;
- low information;
- red flag;
- medication conflict;
- unauthorized role;
- wrong tenant;
- malicious upload.

Record actual results. Fix failures.

### Additional mandatory implementation detail
Run the complete doctor journey in a clean browser session and from a clean backend state. Capture exact failures, fix them, rerun, then verify that a refresh or reconnect does not destroy state.

Do not mark PASS based only on API tests if the phase includes visible user workflows.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 76 — Backup and Disaster Recovery

```text
Implement backup/restore procedures.

Define:
- RPO;
- RTO;
- PostgreSQL backup;
- object-storage backup;
- retention;
- encryption;
- restore procedure;
- rollback procedure.

Perform an actual restore drill into a clean environment.
Verify recovered application behavior and data integrity.

### Additional mandatory implementation detail
Perform an actual backup and restore drill. Restore into an isolated environment, run migrations as appropriate, start the application, and verify that representative consultations, evidence references and file metadata remain internally consistent.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 77 — CI/CD

```text
Implement GitHub Actions.

Pull Request:
- lint;
- format check;
- type check;
- unit tests;
- integration tests;
- security checks;
- build.

Main:
- complete tests;
- build images;
- image/security scan;
- staging deployment;
- smoke tests;
- manual production approval;
- production deployment.

Never store secrets in Git.

### Additional mandatory implementation detail
CI must block merges when formatting, types, tests, migrations or security checks fail. Keep secrets out of CI logs. Add build artifacts and smoke verification for the application images.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 78 — Production Deployment

```text
Prepare production deployment.

Implement/configure:
- production Dockerfiles;
- production Compose or deployment manifests;
- reverse proxy;
- TLS;
- environment separation;
- secrets;
- PostgreSQL;
- Redis;
- Celery;
- object storage;
- monitoring;
- alerting;
- backups;
- rollback.

Verify production-like startup from a clean environment.

### Additional mandatory implementation detail
Production deployment must use environment separation, secret management, TLS termination, backups, health checks, graceful restarts, logging/metrics, alerting and rollback. Verify deployment from a clean environment rather than relying on a developer laptop state.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 79 — Final System Audit

```text
Do not add new functionality unless needed to fix an audit failure.

Audit:
- requirements;
- architecture;
- code quality;
- database;
- migrations;
- API;
- frontend;
- authentication;
- authorization;
- tenant isolation;
- privacy;
- file security;
- AI model/versioning;
- training/evaluation;
- RAG;
- citation verification;
- knowledge graph;
- safety engine;
- realtime;
- observability;
- backup/DR;
- deployment;
- testing.

Classify all issues:
CRITICAL / HIGH / MEDIUM / LOW / INFORMATIONAL

Fix all Critical and High issues before final completion.

Verify the full doctor workflow again after fixes.

### Additional mandatory implementation detail
Perform a final implementation audit against the actual repository, not against the plan text. Search for unfinished TODOs, fake/mocked clinical outputs, dead routes, unreachable components, unauthorized endpoints, missing tenant filters, undocumented environment assumptions, untested error branches, unsafe logging, hidden spinners and controls with no backend action.

Re-run the complete end-to-end clinical workflow after every high-severity fix. The final result must be a coherent product, not a collection of completed tickets.


MANDATORY PHASE COMPLETION CHECKLIST
- Implement all behavior described above, not only the first bullet or API endpoint.
- Connect backend state to the real frontend where this phase affects user-visible behavior.
- Add loading, success, empty, validation, error, unauthorized/forbidden and degraded states relevant to this phase.
- Apply the global professional UI/UX system: clean 2D visual design, subtle smooth transitions, responsive layout, keyboard accessibility and reduced-motion support.
- Keep AI suggestion state separate from clinician-confirmed state.
- Preserve provenance, auditability and versioning wherever the feature produces or changes clinical/AI knowledge.
- Add regression tests for important edge cases and failure paths.
- Do not use fake clinical results or hardcoded “magic” output to make the screen look finished.
- Verify the actual runtime behavior before reporting PASS.
```

## PHASE 80 — Product Polish, Reliability and Release Gate

```text
This is the final implementation gate. Do not create a documentation pack. Inspect and harden the actual application.

OBJECTIVE
Deliver a coherent, professional, clinically safe, production-shaped DocAssistIQ application in which the primary doctor workflow works from browser to database to AI/retrieval/safety services and back to the browser.

1. PRODUCT-WIDE FUNCTIONAL VERIFICATION
Run the full flow:
login → doctor verification → dashboard → consultation → consent → manual/voice capture → realtime transcript → clinical extraction → note drafting → note editing → differential → Why? → evidence/RAG → citation validation → safety → investigations → medication reference → similar cases → reports → feedback → doctor decision → finalization → PDF → patient timeline.

2. CROSS-FEATURE CONSISTENCY
Verify that:
- every shared entity uses one canonical contract;
- status labels mean the same thing throughout the UI;
- model/knowledge versions are retained consistently;
- AI suggestions never visually become confirmed decisions without explicit clinician action;
- tenant scope is enforced uniformly;
- audit records line up with user-visible actions;
- deleted/retained data follows the same rules across primary and derived storage.

3. PROFESSIONAL UI/UX POLISH
Review every major screen for:
- spacing consistency;
- visual hierarchy;
- typography;
- keyboard navigation;
- focus states;
- loading skeleton quality;
- empty states;
- useful error messages;
- responsive layout;
- subtle 2D transitions;
- reduced-motion behavior;
- consistent icons;
- no layout jumps during realtime updates;
- no accidental scroll traps;
- no buttons without real actions;
- no debug labels or placeholder styling.

Animation must remain calm and clinical. Remove any animation that distracts from reading, typing, reviewing evidence or acknowledging safety warnings.

4. REALTIME RELIABILITY
Test dropped WebSocket connection, reconnect, duplicate events, out-of-order messages, provider timeout, browser tab suspension, microphone denial, ASR outage, manual fallback and recovery. Confirm no duplicate transcript segments and no lost persisted work.

5. AI/CLINICAL SAFETY
Test insufficient evidence, contradictory findings, missing critical fields, red flags, medication conflict, outdated evidence, unavailable model, malformed retrieved content and unsupported claims. Confirm the system warns/abstains rather than fabricates.

6. SECURITY
Re-run authentication abuse, authorization bypass, IDOR, cross-tenant access, malicious upload, prompt injection, retrieval poisoning, WebSocket forgery, unsafe logging and secret leakage checks.

7. PERFORMANCE
Measure the established realtime targets and identify the actual bottlenecks. Do not use animation or caching to conceal slow behavior.

8. FAILURE CLEANUP
Search for TODO/FIXME markers, temporary bypasses, `any`-heavy type escapes, ignored exceptions, debug prints, disabled tests, mocked clinical outputs, fake timers standing in for realtime behavior, unsafe CORS, development credentials and dead code. Fix every release-blocking problem.

9. BUILD AND DEPLOYMENT
Perform a clean install/build/test/start cycle from a fresh environment. Verify database migration startup, worker startup, frontend startup and health/readiness behavior.

10. FINAL STATUS
Declare PASS only if the actual software passes the release gate. Otherwise declare FAIL or BLOCKED and list the exact technical blockers. Never claim completeness without runtime evidence.
```


# 9. FINAL RUNTIME ARCHITECTURE

```text
DOCTOR
  │
  ▼
DOCASSISTIQ FRONTEND
  │
  ├── REST API ───────────────────────────────────────┐
  └── Authenticated WebSocket ───────────────────────┐│
                                                      ▼▼
                                                FASTAPI BACKEND
                                                      │
                       ┌──────────────────────────────┼───────────────────────────┐
                       │                              │                           │
                       ▼                              ▼                           ▼
                 DOMAIN SERVICES                REALTIME LAYER              BACKGROUND JOBS
                       │                              │                           │
                       ▼                              ▼                           ▼
              PostgreSQL + pgvector                 Redis                     Celery
                       │                              │                           │
                       └───────────────┬──────────────┴───────────────┬───────────┘
                                       │                              │
                                       ▼                              ▼
                                 OBJECT STORAGE                 AI PROVIDERS
                                       │                  ┌─────────┬─────────────┐
                                       │                  │         │             │
                                       ▼                  ▼         ▼             ▼
                              audio / reports /       ASR / NLP / EMBEDDING /  GENERATION /
                              images / PDFs           RERANKER / DIAGNOSIS / OCR / VISION
                                       │
                                       └──────────────────────┬───────────────────┘
                                                              ▼
                                                     CLINICAL WORKFLOW
                                                              │
                               ┌──────────────────────────────┼────────────────────────────┐
                               ▼                              ▼                            ▼
                         MANUAL INPUT                     VOICE                        REPORT/IMAGE
                               │                              │                            │
                               │                             ASR                       OCR/VISION
                               └──────────────────────────────┼────────────────────────────┘
                                                              ▼
                                                     CLINICAL NLP
                                                              ▼
                                                STRUCTURED CLINICAL STATE
                                                              │
                                  ┌────────────────────────────┼───────────────────────────┐
                                  ▼                            ▼                           ▼
                             DIFFERENTIAL                    RAG                       SAFETY ENGINE
                                  │                            │                           │
                                  ▼                            ▼                           ▼
                             TOP-5 RANKING                EVIDENCE                 WARN / ABSTAIN / ALLOW
                                  └──────────────┬─────────────┴───────────────────────────┘
                                                 ▼
                                           WHY? / EXPLANATION
                                                 ▼
                                           DOCTOR REVIEW
                                                 ▼
                                      ACCEPT / MODIFY / REJECT
                                                 ▼
                                      FINAL CLINICIAN DECISION
                                                 ▼
                                            FINALIZE
                                                 ▼
                                  IMMUTABLE FINAL RECORD + PDF
```

The browser is never the source of truth for clinical state. The backend is authoritative, APIs are typed, database transactions are explicit, and every AI/knowledge result carries enough provenance to reconstruct how it was produced.

---

# 10. PRIMARY DOCTOR WORKSPACE INFORMATION ARCHITECTURE

The core consultation page should feel like one coherent workspace rather than 15 unrelated pages.

Recommended structure:

**Header:** patient/session pseudonym, consultation status, consent state, connection state, save state, primary action.  
**Left/input region:** manual intake + live transcript + audio controls.  
**Center/primary region:** clinical findings + note + doctor edits.  
**Right/intelligence region:** Top-5 differential + Why? + evidence + safety + investigation/medication references.  
**Secondary views:** reports, similar cases, timeline, audit/detail drawers.  
**Footer/action zone:** clinician review, feedback, final decision, finalize.

The exact arrangement may adapt responsively, but the information hierarchy must remain consistent.

Important UI principles:
- the clinician should always know what is current;
- the clinician should know whether a value is AI-generated, imported, manually entered, or clinician-confirmed;
- a failed service must have a visible explanation and next action;
- the most safety-critical information must not be buried in secondary UI;
- editing a section must not cause background refresh to overwrite it;
- realtime updates should feel alive but remain calm and readable.

---

# 11. PERFORMANCE TARGETS

Use these targets consistently and measure them in the actual system:

- partial live transcript visible within 2 seconds of speech;
- WebSocket reconnect within 3 seconds, then visible manual fallback after 2 failed retries;
- manual note save within 500 ms under normal development conditions;
- Top-5 differential generated within 3 seconds of trigger where provider hardware permits;
- evidence/RAG retrieval within 2.5 seconds cold and 400 ms cached where caching is applicable;
- Why? explanation/graph traversal within 1.5 seconds;
- investigation/medication lookups within 2 seconds;
- safety-engine overhead under 300 ms;
- dashboard/page loads under 1.5 seconds;
- at least 20 concurrent development consultations without breaching the targets where the test environment can support that load.

A target is not satisfied by a spinner. Measure it.

---

# 12. PRODUCT COMPLETION STANDARD

DocAssistIQ is complete only when the actual application can perform the primary clinician workflow without manual API intervention, fake data standing in for core features, or undocumented developer shortcuts.

The finished product must:
- be runnable from a clean environment;
- have a coherent professional UI;
- support smooth but restrained 2D motion;
- be responsive and accessible;
- maintain clinical provenance;
- clearly distinguish AI suggestions from clinician decisions;
- fail safely when services are unavailable;
- enforce authentication/authorization/tenant isolation on the backend;
- preserve auditability and versioning;
- pass automated tests;
- pass browser-level verification;
- preserve data through realtime failures;
- provide explicit abstention/insufficient-evidence behavior;
- provide deterministic safety checks;
- avoid fabricated medical evidence;
- support explicit amendment of finalized records;
- be deployable through the configured CI/CD path.

---

# 13. CRITICAL ANTIGRAVITY RULES

```text
1. Inspect before editing.
2. Implement before documenting.
3. One phase at a time.
4. Never declare PASS without runtime evidence.
5. Never fake clinical output.
6. Never fake realtime behavior.
7. Never create a UI control with no real action.
8. Never bypass backend authorization because a button is hidden.
9. Never bypass consent for recording.
10. Never call an uncalibrated score a medical probability.
11. Never let retrieved content override safety instructions.
12. Never let the LLM be the only safety control.
13. Never let the LLM be the sole medication safety checker.
14. Never overwrite clinician edits in the background.
15. Never lose persisted work because a WebSocket or AI provider fails.
16. Never promote unreviewed medical knowledge.
17. Never use identifiable patient data for development.
18. Never log secrets or unnecessary raw clinical content.
19. Never use OCR as a substitute for medical image interpretation.
20. Never claim regulatory approval or clinical validation without actual evidence.
21. Prefer a transparent baseline before complex model training.
22. Use migrations for all schema changes.
23. Test failure paths, not only success paths.
24. Prefer simple, deterministic architecture over unnecessary complexity.
25. The finished product must feel like one professional application, not a collection of demos.
```

---

# 14. EXECUTION ORDER SUMMARY

The development path is deliberately implementation-first:

```text
BOOTSTRAP + DESIGN SYSTEM
→ LOCAL INFRASTRUCTURE
→ BACKEND/DB FOUNDATION
→ AUTH/RBAC
→ APPLICATION SHELL
→ FIRST VERTICAL SLICE
→ CLINICAL DOMAIN
→ FILES/SOURCES/KNOWLEDGE
→ CONSULTATION + CONSENT + MANUAL INTAKE
→ REALTIME + AUDIO + ASR
→ TRANSCRIPT + NLP + NOTE
→ STRUCTURED STATE + DIFFERENTIAL
→ EMBEDDINGS + RAG + CITATIONS + WHY?
→ KNOWLEDGE GRAPH + SAFETY + RED FLAGS + ABSTENTION
→ INVESTIGATION + MEDICATION + MEDICATION SAFETY
→ KNOWLEDGE HUB + UPDATES + FEEDBACK
→ HISTORICAL CASES + REPORTS + IMAGING + MULTIMODAL
→ PATIENT TIMELINE
→ ENTERPRISE RBAC + MULTI-TENANCY + AUDIT + PRIVACY
→ MODEL DEVELOPMENT/EVALUATION + FOUNDATION MODEL + PEFT + CALIBRATION + REGISTRY
→ OBSERVABILITY + ALERTING + SECURITY + RED TEAM
→ CLINICAL EVALUATION + PERFORMANCE
→ COMPLETE CLINICIAN WORKSPACE
→ FINALIZATION + PDF
→ TESTING + E2E + BACKUP/DR + CI/CD + DEPLOYMENT
→ FINAL PRODUCT POLISH + RELEASE GATE
```

Use the shortest dependency-safe path to a real usable application, and keep every later feature integrated with the actual domain model rather than building disconnected prototypes.
