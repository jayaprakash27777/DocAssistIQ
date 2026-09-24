import os
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from scripts.generate_docx_report import (
    add_h1, add_h2, add_h3, add_p, add_bullet, add_callout, add_table,
    HEX_PRIMARY, HEX_SECONDARY, HEX_ACCENT, HEX_DARK, HEX_LIGHT_BG,
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_ACCENT, COLOR_DARK, COLOR_MUTED, COLOR_WARNING
)

def build_section7_existing_system(doc):
    """Section 7: Existing System."""
    add_h1(doc, "7. Existing System & Comparative Analysis")
    add_p(doc,
        "The current clinical computing ecosystem is characterized by fractured, siloed tools that fail to provide cohesive, real-time clinical support. "
        "Clinical practitioners rely predominantly on four legacy operational paradigms:"
    )
    add_bullet(doc,
        "Major enterprise EHR systems (e.g., Epic Systems, Oracle Cerner, MEDITECH) were architected around billing codes (ICD-10, CPT) and regulatory compliance. Clinicians are forced to navigate hundreds of nested forms, type structured notes manually, or copy-paste template macros ('dot phrases'). This results in clinical note bloat, repetitive data entry, and extreme post-clinic documentation backlogs.",
        "1. Manual Entry in Legacy Electronic Health Records (EHR):")
    add_bullet(doc,
        "Early diagnostic support software (e.g., DXplain, Isabel) relies on rigid probabilistic or rule-based models. These systems require doctors to manually re-type symptoms into a separate standalone web portal. Because they are completely disconnected from the live patient conversation and EHR workflow, their adoption in routine practice is near zero.",
        "2. Disconnected Standalone Expert Systems:")
    add_bullet(doc,
        "Systems such as Nuance DAX, 3M M*Modal, and Abridge capture ambient audio and generate encounter summaries using cloud-hosted models. However, these systems function merely as passive documentation scribes—they offer zero diagnostic reasoning, do not verify clinical safety, do not cross-reference incubation periods or travel history, and charge exorbitant recurring fees ($300–$800/month/doctor) while locking patient data into proprietary cloud silos.",
        "3. Proprietary Cloud-Hosted Ambient Scribes:")
    add_bullet(doc,
        "Increasingly, desperate clinicians copy-paste de-identified patient notes into consumer generative AI chatbots (e.g., ChatGPT, Claude) to seek diagnostic advice. This ad-hoc practice is fraught with peril: consumer LLMs hallucinate non-existent medical literature, exhibit sycophancy, lack deterministic safety checks, and expose healthcare organizations to severe legal liability and HIPAA violations.",
        "4. Unsanctioned Consumer LLM Prompting:")

    add_h2(doc, "7.1 Detailed Vulnerability & Limitation Analysis")
    add_p(doc, "The table below synthesizes the structural failure modes of existing clinical tools compared across critical operational dimensions:")

    fail_headers = ["Operational Dimension", "Legacy EHR / Manual", "First-Gen CDSS", "Commercial Cloud Scribes", "Consumer GenAI Chatbots"]
    fail_rows = [
        ["Documentation Latency", "Very High (Hours of typing)", "N/A (No documentation)", "Moderate (Minutes to hours)", "Fast (Seconds per prompt)"],
        ["Real-time Ambient Voice", "None (Manual / dictation)", "None (Form checklists)", "Yes (Proprietary cloud)", "None (Text prompt only)"],
        ["Diagnostic Inference", "None (Human physician only)", "Static Bayesian / Rules", "None (Passive scribe)", "Probabilistic / Hallucinatory"],
        ["Red-Flag Interception", "Basic EHR hard-stops", "Alert pop-ups (Ignored)", "None", "None (Soft guidelines only)"],
        ["Medication Safety", "Basic interaction checks", "Basic static database", "None", "High hallucination risk"],
        ["Evidence Grounding", "None", "Static textbook index", "None", "Fabricated / Fake citations"],
        ["Hospital Data Privacy", "Compliant but isolated", "Compliant standalone", "Third-party cloud risk", "Severe HIPAA violation risk"],
        ["Clinician Alert Fatigue", "Severe (>90% alert override)", "High (Interruptive popups)", "Low (No alerts)", "None (Unstructured chat)"],
        ["Deployment Flexibility", "On-premise / Hosted", "On-premise / Web", "Cloud-only vendor lock", "Public cloud API only"]
    ]
    add_table(doc, fail_headers, fail_rows, col_widths=[1.5, 1.2, 1.2, 1.3, 1.3])


def build_section8_proposed_system(doc):
    """Section 8: Proposed System."""
    add_h1(doc, "8. Proposed System: The DocAssistIQ Architecture")
    add_p(doc,
        "DocAssistIQ introduces a transformative neuro-symbolic clinical AI architecture designed from the ground up to eliminate the vulnerabilities of existing systems. "
        "The overarching paradigm of DocAssistIQ is: 'Deterministic Clinical Rigor Governs, Constrained Neural Language Explains'."
    )
    add_p(doc,
        "DocAssistIQ is structured around seven interconnected functional pillars that create a closed-loop, safe clinical environment:"
    )
    add_bullet(doc,
        "A low-latency, privacy-first audio streaming engine using the browser Web Audio API, authenticated WebSockets, and local Faster-Whisper ASR with PyAnnote speaker diarization, separating physician and patient speech in real time under mandatory patient consent.",
        "1. Ambient Multi-Speaker Listening:")
    add_bullet(doc,
        "A specialized clinical NLP pipeline that extracts symptoms, medical history, medications, allergies, and vitals while executing NegEx negation detection and standardizing concepts to UMLS, SNOMED CT, and RxNorm terminologies.",
        "2. Clinical Named Entity Extraction & Normalization:")
    add_bullet(doc,
        "A 100% offline, deterministic Clinical Reasoning Engine that computes diagnostic fit across 100+ conditions using Jaccard symptom overlap, cardinal symptom weights, geographic travel history, incubation period calculations, and syndromic clusters.",
        "3. Deterministic Clinical Reasoning Core:")
    add_bullet(doc,
        "A quantized local model (Llama-3.2-3B via Ollama) that accepts pre-computed candidate evidence matrices and drafts concise, clinician-friendly 'Why?' diagnostic justifications and structured SOAP notes without performing ungrounded reasoning.",
        "4. Constrained Local Neural Explainer:")
    add_bullet(doc,
        "A deterministic safety engine that evaluates clinical representations against hardcoded master red-flag rules (e.g., crushing chest pain, dyspnea, stroke signs, anaphylaxis, altered mental status) and screens medications via the NIH RxNav API, enforcing the mandatory clinician review banner.",
        "5. Dual-Layer Deterministic Safety Guardrails:")
    add_bullet(doc,
        "A hybrid search pipeline pairing PostgreSQL pgvector dense embeddings with BM25 full-text keyword search and Reciprocal Rank Fusion (RRF), fetching peer-reviewed medical evidence and PubMed literature with claim-level provenance.",
        "6. Evidence-Grounded Hybrid RAG & Live Scanner:")
    add_bullet(doc,
        "A modern, restrained clinical SaaS interface (Next.js 14, React 19, TailwindCSS) providing live transcript inspection, differential diagnosis cards with evidence breakdowns, an interactive SOAP editor, and immutable, cryptographically audited note finalization.",
        "7. Clinician-Controlled Interactive Workspace:")

    add_h2(doc, "8.1 Key Innovations and Systematic Advantages")
    add_p(doc, "The DocAssistIQ proposed system provides definitive advantages over prevailing commercial and academic solutions:")
    
    adv_headers = ["Key Innovation", "Technical Mechanism", "Clinical & Operational Impact"]
    adv_rows = [
        ["Deterministic Pre-Reasoning", "Offline KB, cardinal symptom weights, Jaccard overlap, incubation math", "Eliminates diagnostic hallucinations; 100% repeatable reasoning in < 85ms."],
        ["Constrained Local LLM", "Llama-3.2-3B used strictly as evidence narrator", "Runs on standard clinical workstations without transmitting PHI to external clouds."],
        ["Zero-Bypass Red Flags", "Hardcoded deterministic rule evaluation outside LLM context", "Guarantees 100% sensitivity for acute emergencies; immune to model prompt drift."],
        ["Dual-Mode Medication Engine", "Offline reference panels + Live NIH RxNav DDI screening", "Prevents lethal polypharmacy and drug interactions; enforces clinical review."],
        ["Consent-Gated Voice Capture", "WebSocket protocol enforces verified consent event before audio intake", "Complete regulatory compliance with medical ethics and wiretapping laws."],
        ["Immutable Cryptographic Audit", "SHA-256 hash chaining of all clinical edits and AI suggestions", "Full medico-legal traceability, provenance tracking, and tamper resistance."],
        ["Verified Doctor Knowledge Hub", "Peer collaboration portal with verified credentials and case discussions", "Enables rapid clinical knowledge dissemination and peer learning across hospital networks."]
    ]
    add_table(doc, adv_headers, adv_rows, col_widths=[1.8, 2.3, 2.4])


def build_section9_system_architecture(doc):
    """Section 9: System Architecture & Engineering Blueprint."""
    add_h1(doc, "9. System Architecture")
    add_p(doc,
        "DocAssistIQ is engineered as an enterprise-grade modular monolith. "
        "A modular monolith architecture was chosen deliberately over fragmented microservices to maximize internal transactional integrity, eliminate inter-service network serialization overhead during real-time consultations, simplify HIPAA/GDPR compliance boundaries, and enable single-command Docker deployment on hospital infrastructure."
    )
    
    add_h2(doc, "9.1 Architectural Layer Decomposition")
    add_p(doc, "The platform is organized into nine discrete architectural tiers with unidirectional dependencies:")
    add_bullet(doc, "Built with Next.js 14 (App Router), React 19, TypeScript, and TailwindCSS. Captures browser microphone audio via Web Audio API (16kHz linear PCM), handles real-time WebSocket communication, renders the dual-pane clinician workspace, and strictly enforces WCAG 2.2 AA accessibility.", "1. Client & Presentation Layer:")
    add_bullet(doc, "Implemented using FastAPI on an asynchronous ASGI event loop (Uvicorn). Manages JWT authentication, Role-Based Access Control (RBAC), multi-tenant isolation, request correlation ID propagation, and thin route handlers.", "2. API Gateway & Transport Layer:")
    add_bullet(doc, "Authenticated WebSocket endpoints backed by Redis Pub/Sub. Ingests binary audio chunks, coordinates real-time transcription broadcasting, and synchronizes consultation workspace state across clinical devices.", "3. Real-Time Streaming & Event Layer:")
    add_bullet(doc, "Contains 57 specialized Python domain services encapsulating all business logic (ConsultationService, ClinicalNLP, ClinicalReasoningEngine, SafetyEngine, MedicationService, IngestionService, DoctorService, DiarizationService, etc.).", "4. Application & Domain Service Layer:")
    add_bullet(doc, "Contains the Offline Disease Knowledge Base (100+ conditions), Expanded Disease Catalog, Syndromic Cluster definitions, Incubation Period Evaluator, Master Red Flag Rules, and RxNav client. Zero network dependencies; executes in < 85ms.", "5. Deterministic Knowledge & Rule Core:")
    add_bullet(doc, "Integrates Faster-Whisper (ASR), PyAnnote Audio 3.1 (Speaker Diarization), Sentence-Transformers ('all-MiniLM-L6-v2' embeddings), and Llama-3.2-3B via Ollama. Exposes provider interfaces to allow seamless model swapping.", "6. Machine Learning & Natural Language Core:")
    add_bullet(doc, "PostgreSQL 16 with pgvector extension stores relational entities, clinical representations, differential diagnosis items, and 384-dimensional vector embeddings. MinIO S3-compatible object storage stores raw audio files and clinical reports. Redis 7 manages caching and session states.", "7. Persistence & Vector Storage Layer:")
    add_bullet(doc, "Distributed Celery workers backed by Redis broker queues. Asynchronously processes heavy background workloads including medical document OCR, PubMed literature scanning, batch clinical embedding generation, and audit report generation.", "8. Asynchronous Task Worker Layer:")
    add_bullet(doc, "Cryptographically chained audit logs (SHA-256), patient pseudonymization engine, retention/deletion lifecycle policies, and doctor credential verification pipelines.", "9. Governance, Security & Compliance Layer:")

    # High-Resolution System Architecture Diagram Image
    img_path = os.path.abspath("DocAssistIQ_System_Architecture_Diagram.png")
    if os.path.exists(img_path):
        add_h2(doc, "9.2 High-Resolution System Architecture Blueprint")
        doc.add_picture(img_path, width=Inches(6.5))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_before = Pt(4)
        cap.paragraph_format.space_after = Pt(10)
        crun = cap.add_run(
            "Figure 9.1: End-to-End Modular Monolith System Architecture Topology of DocAssistIQ "
            "(Client Presentation, API Gateway, Real-Time Audio & ASR, Deterministic Clinical Reasoning Core, "
            "Safety Guardrails, and Distributed Persistence Tier)."
        )
        crun.font.name = "Calibri"
        crun.font.size = Pt(8.5)
        crun.font.italic = True
        crun.font.color.rgb = COLOR_MUTED

    # Architecture Diagram as structured ASCII / Text Blueprint
    add_h2(doc, "9.3 System Architecture Interaction Topology (ASCII Specification)")
    add_p(doc, "The following schematic illustrates the end-to-end component topology and data flow across DocAssistIQ:")
    
    arch_ascii = (
        "+---------------------------------------------------------------------------------------------------+\n"
        "|                                     CLINICIAN BROWSER CLIENT (Next.js 14)                         |\n"
        "|  +---------------------+   +---------------------+   +---------------------+   +---------------+  |\n"
        "|  |  Consent & Intake   |   | Live Audio Capture  |   | Differential Cards  |   |  SOAP Editor  |  |\n"
        "|  +----------+----------+   +----------+----------+   +----------^----------+   +-------^-------+  |\n"
        "+-------------|-------------------------|-------------------------|----------------------|----------+\n"
        "              | HTTPS                   | WebSocket (Binary PCM)  | JSON Streaming       | HTTPS    \n"
        "+-------------v-------------------------v-------------------------v----------------------v----------+\n"
        "|                              API GATEWAY & ROUTING TIER (FastAPI / ASGI)                          |\n"
        "|  +---------------------------------------------------------------------------------------------+  |\n"
        "|  | JWT Authentication | RBAC Guardrails | Multi-Tenant Scoping | Request ID Tracing             |  |\n"
        "|  +---------------------------------------------------------------------------------------------+  |\n"
        "+---------------------------------------|-----------------------------------------------------------+\n"
        "                                        v                                                            \n"
        "+---------------------------------------------------------------------------------------------------+\n"
        "|                                    APPLICATION SERVICES LAYER                                     |\n"
        "|  +-------------------+   +--------------------+   +-----------------------+   +----------------+  |\n"
        "|  |  Streaming ASR    |-->| Clinical NLP &     |-->| Deterministic         |-->| Local LLM      |  |\n"
        "|  | (Faster-Whisper)  |   | Concept Normalizer |   | Reasoning Engine (KB) |   | (Llama-3.2-3B) |  |\n"
        "|  +-------------------+   +--------------------+   +-----------+-----------+   +--------+-------+  |\n"
        "|                                                               |                        |          |\n"
        "|  +-------------------+   +--------------------+               v                        v          |\n"
        "|  | PyAnnote Audio    |   | Hybrid RAG &       |   +-----------------------+   +----------------+  |\n"
        "|  | Diarization Engine|   | PubMed Scanner     |   | Deterministic Safety  |-->| Clinician Note |  |\n"
        "|  +-------------------+   +--------------------+   | Engine (Red Flags)    |   | Synthesis      |  |\n"
        "|                                                   +-----------------------+   +----------------+  |\n"
        "+---------------------------------------------------------------|-----------------------------------+\n"
        "                                                                v                                    \n"
        "+---------------------------------------------------------------------------------------------------+\n"
        "|                               DATA PERSISTENCE & ASYNC TASK TIER                                  |\n"
        "|  +------------------------+   +--------------------+   +-------------------+   +---------------+  |\n"
        "|  | PostgreSQL 16+pgvector |   | Redis 7 (Pub/Sub & |   | MinIO S3 Storage  |   | Celery Worker |  |\n"
        "|  | (Relational + Vectors) |   | Session Cache)     |   | (Audio & PDFs)    |   | (Async Tasks) |  |\n"
        "|  +------------------------+   +--------------------+   +-------------------+   +---------------+  |\n"
        "+---------------------------------------------------------------------------------------------------+"
    )
    add_callout(doc, arch_ascii, alert_type="NOTE", bold_title="SYSTEM ARCHITECTURE COMPONENT TOPOLOGY")


def build_section10_methodology_workflow(doc):
    """Section 10: Methodology & Operational Workflow."""
    add_h1(doc, "10. Methodology & Operational Workflow")
    add_p(doc,
        "The operational lifecycle of DocAssistIQ is engineered as a deterministic, multi-stage state machine that mirrors the natural progression of an ambulatory or inpatient clinical consultation. "
        "The workflow comprises ten rigorous sequential stages:"
    )
    
    stages = [
        ("Stage 1: Patient Intake & Consent Verification",
         "The clinician logs in with two-factor JWT authentication. The patient is selected or registered under an automated pseudonymization scheme (generating a non-reversible cryptographic session token). "
         "CRITICAL GATE: The system prohibits microphone activation until a verified patient consent event (verbal consent documented or digital consent signed) is recorded in the immutable database state."),
        
        ("Stage 2: Browser Audio Capture & Binary Streaming",
         "Upon consent confirmation, the clinician initiates the consultation session. The client-side Web Audio API captures microphone input, resamples the stream to 16,000 Hz 16-bit mono linear PCM, "
         "and chunks audio into 250ms binary frames dispatched over an authenticated, TLS-encrypted WebSocket channel to the backend."),
        
        ("Stage 3: Streaming Speech-to-Text & Speaker Diarization",
         "The backend WebSocket handler streams incoming PCM buffers into the Faster-Whisper ASR engine with Voice Activity Detection (VAD) filtering. "
         "Simultaneously, the PyAnnote Audio diarization service processes speech segments to assign speaker labels ('Clinician' vs 'Patient'), emitting real-time transcript deltas to the UI."),
        
        ("Stage 4: Clinical NLP & Negation Detection",
         "As sentences complete, the Clinical NLP service analyzes the structured transcript. It identifies clinical entities across five categories: Chief Complaints, Active Symptoms, Medical/Surgical History, Current Medications, and Vital Signs. "
         "Crucially, it executes a regex-based NegEx negation detection parser (e.g., distinguishing 'patient reports chest pain' from 'patient denies chest pain') to prevent negative assertions from contaminating positive diagnostic sets."),
        
        ("Stage 5: Terminology Normalization & Concept Grounding",
         "Extracted clinical terms are passed to the Concept Normalizer, which resolves synonyms, colloquial expressions, and typos to standard clinical ontologies: "
         "Symptoms map to SNOMED CT concepts and UMLS Concept Unique Identifiers (CUIs); medications map to RxNorm RxCUIs; and diagnoses map to ICD-10-CM codes."),
        
        ("Stage 6: Deterministic Multi-Factor Diagnostic Reasoning",
         "The normalized clinical representation is fed to the deterministic Clinical Reasoning Engine. "
         "The engine evaluates candidate diseases across the knowledge base by calculating: (a) Jaccard symptom overlap; (b) Cardinal symptom weighting; (c) Geographic travel match; (d) Incubation timeline fit; (e) Syndromic cluster bonuses; and (f) Negation penalties. "
         "It outputs a pre-ranked Top-5 candidate list with complete mathematical score breakdowns."),
        
        ("Stage 7: Constrained Neural Narrative Synthesis",
         "The Top-5 pre-ranked candidates and their structured score breakdowns are supplied to the local Llama-3.2-3B language model via Ollama. "
         "Using strict system prompts that forbid ungrounded speculation, the model generates 1-2 sentence clinician-friendly narrative justifications explaining why each condition is supported, which expected findings are missing, and what contradicting evidence exists."),
        
        ("Stage 8: Deterministic Safety Evaluation & Red-Flag Interception",
         "Before any diagnostic suggestion reaches the clinician interface, the master SafetyEngine executes its hardcoded red-flag rules against the clinical representation. "
         "If critical emergencies (crushing chest pain, severe dyspnea, stroke symptoms, anaphylaxis, altered consciousness) are detected, the system immediately flags the session with a CRITICAL alert banner and recommends immediate emergency interventions."),
        
        ("Stage 9: Reference Intelligence & Medication Validation",
         "For the top diagnostic candidates, the Medication and Investigation services retrieve standard evidence-based clinical panels. "
         "Medication suggestions are automatically cross-referenced against patient-reported allergies and active medications via the NIH RxNav interaction API. "
         "Every medication card displays the mandatory warning: 'REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED'."),
        
        ("Stage 10: Clinician Review, Amendment, and Immutable Finalization",
         "The clinician reviews the real-time transcript, Top-5 differential diagnoses, safety alerts, and drafted SOAP note in the dual-pane workspace. "
         "The physician can freely edit any section of the note, confirm or reject diagnostic candidates, and sign the consultation. "
         "Upon signature, the consultation note is sealed as an immutable record with a SHA-256 cryptographic provenance hash, preventing retroactive tampering.")
    ]
    
    for title, desc in stages:
        add_h2(doc, title)
        add_p(doc, desc)

    # Workflow Sequence Table
    add_h2(doc, "10.1 Consultation Lifecycle State Transition Matrix")
    add_p(doc, "The formal state machine transitions governing the consultation lifecycle are summarized below:")
    
    wf_headers = ["Lifecycle Stage", "Input Trigger", "Processing Engine", "Output Artifact", "Failure / Fallback State"]
    wf_rows = [
        ["1. Intake & Consent", "Clinician selects patient", "Consent & Auth Service", "Verified Consent Event Token", "Session blocked; microphone disabled"],
        ["2. Audio Streaming", "Doctor clicks 'Start'", "Web Audio API / WebSocket", "16kHz Binary PCM stream", "WebSocket reconnect; local audio cache"],
        ["3. ASR & Diarization", "PCM Audio stream", "Faster-Whisper + PyAnnote", "Speaker-labeled transcript", "VAD fallback; single-speaker mode"],
        ["4. Clinical NLP", "Transcript text", "Clinical NLP (NegEx)", "Extracted entity & negation sets", "Rule-based fallback parser"],
        ["5. Normalization", "Raw entity strings", "Concept Normalizer", "UMLS CUI / SNOMED CT codes", "Literal string match fallback"],
        ["6. Reasoning Engine", "Normalized representation", "Clinical Reasoning Engine", "Ranked Top-5 candidate scores", "Deterministic common prevalence fallback"],
        ["7. LLM Narration", "Structured score matrix", "Llama-3.2-3B via Ollama", "Human-readable 'Why?' summaries", "Template-based heuristic explanation"],
        ["8. Safety Evaluation", "Representation + Candidates", "SafetyEngine (Red Flags)", "SafetyDecision (ALLOW/WARN/ABSTAIN)", "Fail-safe: Automatic WARN/ABSTAIN state"],
        ["9. Meds & Labs", "Top disease candidate", "Medication & RxNav Engine", "Evidence panels + DDI alerts", "Offline clinical panel fallback"],
        ["10. Finalization", "Doctor clicks 'Finalize'", "Consultation & Audit Service", "Immutable SHA-256 Signed Note", "Draft auto-save; amendment workflow"]
    ]
    add_table(doc, wf_headers, wf_rows, col_widths=[1.2, 1.2, 1.3, 1.4, 1.4])


def build_section11_technologies_used(doc):
    """Section 11: Technologies Used."""
    add_h1(doc, "11. Technologies Used & Architectural Justifications")
    add_p(doc,
        "Every component in the DocAssistIQ technology stack was chosen through rigorous architectural evaluation, prioritizing local execution capability, deterministic safety, high throughput, and long-term enterprise maintainability."
    )
    
    tech_headers = ["Layer / Domain", "Technology & Version", "Architectural Role", "Selection Justification & Tradeoff Rationale"]
    tech_rows = [
        ["Frontend Framework", "Next.js 14.2 / React 19", "User Interface & App Router", "Server-side rendering, strict routing, superior type safety with TypeScript, fast hydration."],
        ["Styling System", "TailwindCSS 3.4", "Design System & UI Tokens", "Restrained clinical design tokens, WCAG 2.2 AA accessibility, zero runtime CSS overhead."],
        ["Client Audio API", "Web Audio API (Browser)", "Microphone Capture & PCM Resampling", "Native browser standard; resamples to 16kHz mono without external browser plugins."],
        ["Backend Core", "Python 3.11 / FastAPI", "API Gateway & Async Web Services", "High-performance async ASGI event loop, native Pydantic validation, Python AI ecosystem."],
        ["Data Validation", "Pydantic v2.6", "Request/Response Typing & Schemas", "Rust-based serialization engine; 10x faster validation than v1; strict typed contracts."],
        ["Database & ORM", "PostgreSQL 16 + SQLAlchemy 2", "Relational Storage & Async ORM", "Rock-solid enterprise ACID compliance, asyncpg driver, robust JSONB support."],
        ["Vector Search", "pgvector extension (0.6+)", "Semantic Embeddings & RAG", "Eliminates need for separate vector DB; maintains relational joins with medical documents."],
        ["Cache & Pub/Sub", "Redis 7.2 Alpine", "Session Cache & WebSocket Broker", "Ultra-low latency in-memory data store; coordinates multi-user WebSocket events."],
        ["Asynchronous Jobs", "Celery 5.3 + Redis broker", "Background Heavy Task Execution", "Decouples heavy OCR, batch embedding, and document ingestion from the API event loop."],
        ["Object Storage", "MinIO S3-Compatible", "Binary Audio & Report Storage", "S3-compatible, self-hosted, enterprise-grade object storage; keeps blobs out of PostgreSQL."],
        ["Speech-to-Text", "Faster-Whisper (Large-v3)", "Automatic Speech Recognition", "CTranslate2 implementation of Whisper; 4x faster inference with 50% less VRAM usage."],
        ["Speaker Diarization", "PyAnnote Audio 3.1", "Speaker Segmentation & Labeling", "State-of-the-art diarization neural pipeline; separates doctor and patient voices."],
        ["Embeddings", "Sentence-Transformers", "Dense Vector Representation", "Pretrained 'all-MiniLM-L6-v2' generating 384-dimensional dense semantic vectors."],
        ["Local LLM", "Llama-3.2-3B via Ollama", "Constrained Narrative Generation", "Compact 3-billion parameter model; runs locally on standard GPUs; zero cloud data leakage."],
        ["Testing & Quality", "Pytest, Ruff, Mypy, ESLint", "Code Quality & Static Analysis", "Enforces 100% type safety, zero lint regressions, and automated CI/CD verification."]
    ]
    add_table(doc, tech_headers, tech_rows, col_widths=[1.1, 1.4, 1.5, 2.5])


def build_section12_modules(doc):
    """Section 12: Modules & Functional Decomposition."""
    add_h1(doc, "12. Modules & Functional Decomposition")
    add_p(doc,
        "DocAssistIQ is architected into ten core functional modules, each possessing strictly defined interface boundaries, domain models, and service contracts:"
    )
    
    modules = [
        ("Module 1: Enterprise Authentication, RBAC & Multi-Tenancy",
         "Manages user authentication via PBKDF2-SHA256 password hashing, OAuth2 Bearer JWT access/refresh tokens, and multi-tenant hospital partitioning. "
         "Implements Role-Based Access Control (RBAC) across four roles: CLINICIAN, NURSE, AUDITOR, and SYSTEM_ADMIN. Enforces strict hospital tenant scoping across all SQL queries."),
        
        ("Module 2: Patient Intake, Consent & Pseudonymization",
         "Governs patient registration, historical medical profiles, and privacy compliance. Automatically assigns an opaque, non-reversible UUID to patient consultation sessions. "
         "Maintains an append-only consent registry that records the consent type (Verbal, Signed Digital), timestamp, and clinician ID before voice capture is unlocked."),
        
        ("Module 3: Ambient Consultation & Real-Time Audio Streaming",
         "Contains the authenticated WebSocket endpoint (`/api/v1/ws/consultations/{id}`), audio buffer aggregator, Faster-Whisper ASR pipeline, and PyAnnote diarizer. "
         "Handles real-time chunking, Voice Activity Detection, and JSON broadcasting of live transcription events to connected clinician workstations."),
        
        ("Module 4: Clinical NLP, Negation & Terminology Normalization",
         "Analyzes consultation transcripts using specialized entity extraction patterns and NegEx negation boundary evaluators. "
         "Maps extracted concepts to standardized vocabularies: UMLS CUIs, SNOMED CT concept identifiers, and RxNorm RxCUIs, producing a validated `ClinicalRepresentation` object."),
        
        ("Module 5: Deterministic Clinical Reasoning & Top-5 Differential Engine",
         "The core intelligence engine. Evaluates patient clinical representations against an extensive multi-specialty knowledge catalog (100+ conditions). "
         "Executes multi-factor scoring combining symptom Jaccard similarity, cardinal symptom matches, geographic travel risk, incubation timeline fit, and syndromic clusters."),
        
        ("Module 6: Deterministic Safety & Red-Flag Enforcement Engine",
         "The non-negotiable clinical safety guardian. Evaluates patient findings against versioned Master Red Flag rules (RF-001 Severe Chest Pain, RF-002 Severe Dyspnea, RF-003 Stroke Signs, RF-004 Anaphylaxis, RF-005 Altered Consciousness). "
         "Enforces safety decisions (ALLOW, WARN, ABSTAIN) and blocks AI-generated suggestions if critical contraindications are detected."),
        
        ("Module 7: Evidence-Grounded Hybrid RAG & Verification Module",
         "Performs hybrid vector-lexical document retrieval across clinical practice guidelines, hospital formulary documents, and PubMed abstracts. "
         "Uses Reciprocal Rank Fusion (RRF) to merge pgvector cosine distance rankings with PostgreSQL `tsvector` BM25 keyword rankings, attaching claim-level citations to clinical summaries."),
        
        ("Module 8: Medication, Investigation & Polypharmacy Reference Module",
         "Supplies standardized evidence-based medication panels, dosing guidelines, and recommended diagnostic investigations. "
         "Integrates live NIH RxNav API interaction checking with local offline fallback, alerting clinicians to adverse drug-drug interactions and patient allergy conflicts."),
        
        ("Module 9: Verified Doctor Knowledge Hub & Collaboration Module",
         "An enterprise clinical networking portal where verified physicians can publish anonymized case studies, discuss complex differential diagnoses, and vote on clinical guidelines. "
         "Includes peer credential verification, discussion threads, and clinical feedback loops to continually refine platform knowledge."),
        
        ("Module 10: Audit Trail, Provenance Tracking & Compliance Module",
         "Maintains an immutable, cryptographically chained audit log for every clinical interaction. "
         "Each log entry records user ID, action, timestamp, client IP, request correlation ID, and a SHA-256 hash of the payload linked to the previous entry, ensuring complete evidentiary integrity for medical-legal compliance.")
    ]
    
    for mod_title, mod_desc in modules:
        add_h2(doc, mod_title)
        add_p(doc, mod_desc)

print("Report Part 2 (Sections 7 to 12) module loaded successfully.")
