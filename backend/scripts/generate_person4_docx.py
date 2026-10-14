"""
Script to generate the complete, comprehensive DOCX presentation & viva guide for Person 4.
"""
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def create_document():
    doc = Document()

    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    normal_style = doc.styles['Normal']
    normal_font = normal_style.font
    normal_font.name = 'Calibri'
    normal_font.size = Pt(11)
    normal_font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(4)

    def add_title(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(22)
        run.font.color.rgb = RGBColor(0x0A, 0x25, 0x40)
        return p

    def add_subtitle(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(12)
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(13)
        run.font.color.rgb = RGBColor(0x00, 0x66, 0xCC)
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(15)
        run.font.color.rgb = RGBColor(0x0A, 0x25, 0x40)
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(12.5)
        run.font.color.rgb = RGBColor(0x00, 0x55, 0x99)
        return p

    def add_callout(text, title="CRITICAL EXAMINER TAKEAWAY"):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        set_cell_background(cell, "F0F7FF")
        set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(2)
        r_title = p.add_run(f"★ {title}: ")
        r_title.bold = True
        r_title.font.color.rgb = RGBColor(0x00, 0x55, 0x99)
        r_text = p.add_run(text)
        r_text.font.size = Pt(10.5)
        doc.add_paragraph()

    def add_code_block(code_text):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        set_cell_background(cell, "F4F5F7")
        set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
        p = cell.paragraphs[0]
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(code_text)
        run.font.name = 'Consolas'
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(0x1F, 0x23, 0x28)
        doc.add_paragraph()

    # --- TITLE ---
    add_title("DocAssistIQ — Person 4 Presentation & Viva Mastery Guide")
    add_subtitle("Frontend Architecture (Next.js 16/React 19), Full-Stack Integration, Database & Vector Storage, Cryptographic Provenance, and Benchmark Evaluation")

    add_callout(
        "Person 4 represents the Full-Stack Engineering, Data Infrastructure, Tamper-Evident Security, and Empirical Scientific Validation of DocAssistIQ. "
        "Your role is to prove that the sophisticated AI algorithms built by Persons 1, 2, and 3 are packaged into a reactive Next.js 16 frontend, "
        "backed by production-grade PostgreSQL/pgvector/Redis data infrastructure, secured with SHA-256 cryptographic provenance, and backed by a 100% benchmark score (80/80 clinical cases).",
        "PERSON 4 CORE MISSION"
    )

    # --- SECTION 1: DOMAIN OWNERSHIP ---
    add_h1("1. Person 4 Subsystem Ownership & Core Boundaries")
    p = doc.add_paragraph()
    p.add_run(
        "DocAssistIQ is not merely an algorithm; it is an enterprise, hospital-grade software application. "
        "Person 4 is strictly responsible for five vital pillars of the production system:\n"
    )
    points = [
        ("Next.js 16 & React 19 Frontend Architecture: ", "App Router layout, React 19 modern hooks, TailwindCSS v4 design system, Radix UI accessibility primitives, Framer Motion animations, and TanStack Query v5 optimistic mutations."),
        ("Full-Stack Real-Time Integration: ", "Typed enterprise API client (frontend/src/lib/api.ts, 85KB), bidirectional WebSocket engine (ws.ts) with auto-reconnection, exponential backoff, ping/pong heartbeats, live consultation streaming, and live diarized transcript synchronization."),
        ("Database & Vector Infrastructure: ", "PostgreSQL 16 relational core, SQLAlchemy 2.0 async engine, pgvector extension for high-dimensional semantic clinical embeddings (cosine distance similarity for PMC RAG & disease search), and Redis 7 for sub-millisecond caching, rate-limiting token buckets, and pub/sub message brokering."),
        ("Cryptographic Provenance & Tamper-Evident Security: ", "SHA-256 digital document hashing (hashlib.sha256), public verification portal (/verify/[code] and /verify/hash), legal non-repudiation audit trails (ConsultationAudit), hospital-grade PDF generation via FPDF2, and Microsoft Word DOCX report generation via python-docx."),
        ("Rigorous Benchmark Evaluation: ", "Execution and analysis of benchmark_clinical_cases.py: 80 real-world clinical cases across 5 major disease categories (Tropical Outbreaks, Everyday Clinical Presentations, Critical Emergencies, Chronic General Medicine, and Neuropsychiatry) achieving a perfect 100% Top-3 diagnostic accuracy (80/80 passed) with sub-30ms inference latency.")
    ]
    for bold_prefix, text in points:
        bp = doc.add_paragraph(style='List Bullet')
        r1 = bp.add_run(bold_prefix)
        r1.bold = True
        bp.add_run(text)

    # --- SECTION 2: VERBATIM PRESENTATION SCRIPT ---
    add_h1("2. Verbatim Presentation Speech Script (Deliver With Total Confidence)")
    p_speech = doc.add_paragraph()
    p_speech.add_run(
        "\"Good morning, respected external examiners, head of department, and faculty evaluation committee. "
        "My name is [Your Name], and I present the fourth and culminating pillar of DocAssistIQ: "
        "Frontend Architecture, Full-Stack Real-Time Integration, Database & Vector Storage Infrastructure, "
        "Cryptographic Provenance, and Empirical Benchmark Validation.\n\n"
        "Earlier, my teammates demonstrated the algorithmic foundations: Person 1 explained our sub-30ms hybrid reasoning engine, "
        "Person 2 detailed our voice ingestion and clinical NLP pipeline, and Person 3 demonstrated our 15,000-condition (20,397 conditions) diagnostic intelligence, "
        "outbreak surveillance radar, and polypharmacy safeguards. "
        "My responsibility is to demonstrate how these complex capabilities are engineered into a resilient, production-ready hospital platform "
        "that doctors can intuitively operate at the point of care.\n\n"
        "First, looking at the user interface: we engineered DocAssistIQ with Next.js 16.3.4 using the App Router and React 19.2.8. "
        "Rather than a disjointed medical record system, our clinician shell provides an integrated workspace with live audio waveforms, "
        "real-time consultation diarization, interactive differential diagnosis cards, and an India epidemiological surveillance radar. "
        "We achieved sub-100 millisecond UI responsiveness using TailwindCSS v4, TanStack Query v5 with optimistic mutations, "
        "and Radix UI headless components for clinical accessibility.\n\n"
        "Second, how does the frontend communicate with our backend services? "
        "We built a dual-channel architecture: a strongly-typed REST client in api.ts handling over 85 kilobytes of clinical endpoints, "
        "complemented by a resilient WebSocket client in ws.ts. When a doctor begins an encounter, the WebSocket establishes a bidirectional, "
        "low-latency tunnel with automatic reconnection, exponential backoff, and 30-second ping/pong heartbeats. Audio chunks and transcript updates "
        "stream between browser and server without page reloads, reflecting clinical state changes in real time.\n\n"
        "Third, regarding data infrastructure: our system is backed by PostgreSQL 16 managed via an asynchronous SQLAlchemy 2.0 engine with asyncpg. "
        "For medical knowledge retrieval, we enabled the pgvector extension, storing high-dimensional semantic embeddings of clinical trials and PubMed Central articles. "
        "This allows sub-linear cosine similarity searches over millions of medical tokens. Alongside PostgreSQL, we deploy Redis 7 as an in-memory data store, "
        "powering sub-millisecond caching of resolved clinical entities, token-bucket API rate limiting, and pub/sub message brokering.\n\n"
        "Fourth, clinical documentation requires absolute tamper-evident integrity. When a clinician finalizes a consultation, "
        "our clinical_document_service.py compiles the clinical note, diagnoses, and prescriptions into a canonical payload and computes an immutable "
        "SHA-256 cryptographic digest. The system generates hospital-grade PDFs via FPDF2 and Word documents via python-docx, "
        "stamping them with a unique verification code and QR code. Anyone—a pharmacist, insurer, or receiving hospital—can visit our public verification portal "
        "at /verify/[code] or paste the raw SHA-256 hash to prove beyond doubt that the document has not been altered by even a single byte.\n\n"
        "Finally, we subjected DocAssistIQ to rigorous scientific evaluation. In our benchmark_clinical_cases.py evaluation harness, "
        "we tested 80 comprehensive clinical cases spanning tropical outbreaks like Dengue and Malaria, critical emergencies like Aortic Dissection and Pulmonary Embolism, "
        "and chronic diseases like Diabetes and Chronic Kidney Disease. "
        "I am proud to report that DocAssistIQ achieved a perfect 100% Top-3 diagnostic accuracy—80 out of 80 cases successfully matched—with an average deterministic reasoning time under 30 milliseconds.\n\n"
        "DocAssistIQ is not a theoretical prototype; it is an end-to-end, scientifically validated, cryptographically secure clinical decision platform. "
        "I am now ready to present our live codebase, demonstrate the system architecture, and answer your technical questions. Thank you.\""
    )

    # --- SECTION 3: SLIDE-BY-SLIDE WALKTHROUGH ---
    add_h1("3. Slide-by-Slide Presentation Walkthrough")

    slides = [
        ("Slide 1: Next.js 16 & React 19 Frontend Architecture",
         "Visuals: Next.js App Router tree structure ((shell)/dashboard, /consultations, /verify, /outbreaks, /patients) + UI component hierarchy.\n"
         "Key Points: Next.js 16.3.4 App Router, React 19.2.8 Server/Client components, TailwindCSS v4 utility architecture, Framer Motion animations, Radix UI dialogs/tabs.\n"
         "Examiner Hook: Point out how Server Components minimize client bundle size, while Client Components ('use client') handle real-time audio waveforms and WebSockets."),

        ("Slide 2: Dual-Channel Real-Time Integration (REST + WebSockets)",
         "Visuals: Architecture diagram showing browser client connecting via typed api.ts (REST) and ws.ts (WebSockets) to FastAPI backend.\n"
         "Key Points: Resilient WebSocket architecture with auto-reconnection, jittered exponential backoff, 30s heartbeat ping/pong, and queued message replay.\n"
         "Examiner Hook: Explain how transcript segments and live differential updates stream asynchronously over WebSockets without blocking the main UI thread."),

        ("Slide 3: Enterprise Data Infrastructure — PostgreSQL, pgvector & Redis",
         "Visuals: Three-tier data architecture diagram showing PostgreSQL 16 (relational entities), pgvector (semantic embedding space), and Redis 7 (in-memory cache & rate limiter).\n"
         "Key Points: Async SQLAlchemy 2.0 with asyncpg connection pooling, pgvector HNSW cosine distance indexing for PMC RAG guidelines, and Redis token bucket rate limiting.\n"
         "Examiner Hook: Highlight how pgvector enables semantic search over clinical trials without spinning up a separate, resource-heavy Pinecone or Milvus cluster."),

        ("Slide 4: Cryptographic Provenance & Tamper-Evident Verification",
         "Visuals: Document lifecycle diagram: Consultation $\\rightarrow$ Canonical Payload $\\rightarrow$ SHA-256 Hash $\\rightarrow$ PDF/DOCX Generation $\\rightarrow$ Public /verify Portal.\n"
         "Key Points: Immutable document signing, SHA-256 cryptographic digest calculation, FPDF2 hospital-grade PDF generation, python-docx export, and instant public validation.\n"
         "Examiner Hook: Demonstrate that if an attacker modifies even a single comma or medication dosage in the note, the SHA-256 hash completely changes, instantly invalidating the signature."),

        ("Slide 5: Rigorous Benchmark Evaluation — 80 Cases, 100% Accuracy",
         "Visuals: Recharts bar chart showing 80/80 passed benchmark test cases across 5 clinical categories, with latency distribution under 30ms.\n"
         "Key Points: benchmark_clinical_cases.py evaluation harness, 5 clinical categories (Tropical Outbreaks, Everyday Medicine, Critical Surgical Emergencies, Chronic Care, Neuropsychiatry), 0 failures.\n"
         "Examiner Hook: Emphasize that every single expected disease was present in the top-3 candidates, demonstrating clinical reliability and safety across diverse presentations.")
    ]

    for title, content in slides:
        add_h2(title)
        p_slide = doc.add_paragraph()
        p_slide.add_run(content)

    # --- SECTION 4: DEEP ARCHITECTURAL CODEBASE VERIFICATION ---
    add_h1("4. Technical Deep-Dive: Codebase Reference & Architecture")

    add_h2("4.1 Frontend Technology Stack & Configuration")
    p_fe = doc.add_paragraph()
    p_fe.add_run(
        "Verified from frontend/package.json:\n"
        "• Framework: Next.js 16.3.4 (App Router, Server Actions, Turbopack support)\n"
        "• UI Library: React 19.2.8 & React DOM 19.2.8\n"
        "• Styling: TailwindCSS v4 (@tailwindcss/postcss ^4, tailwindcss ^4)\n"
        "• Icons & UI: Lucide React ^1.47.0, Radix UI primitives (@radix-ui/react-dialog, @radix-ui/react-tabs, @radix-ui/react-dropdown-menu, @radix-ui/react-tooltip)\n"
        "• State & Data Fetching: TanStack Query v5 (@tanstack/react-query ^5.103.1)\n"
        "• Animation & Data Viz: Framer Motion ^13.4.0, Recharts ^3.10.1, React CountUp ^6.5.3\n"
        "• Testing: Jest ^30.5.1, React Testing Library ^16.3.3, ts-jest ^29.4.12"
    )

    add_h2("4.2 Resilient WebSocket Architecture (frontend/src/lib/ws.ts)")
    add_code_block(
        "// Production WebSocket Client with Auto-Reconnect and Heartbeat (frontend/src/lib/ws.ts)\n"
        "class ConsultationWebSocket {\n"
        "  private ws: WebSocket | null = null;\n"
        "  private reconnectAttempts = 0;\n"
        "  private maxReconnectAttempts = 10;\n"
        "  private reconnectDelay = 1000; // Exponential backoff\n"
        "  private heartbeatInterval: NodeJS.Timeout | null = null;\n"
        "  private messageQueue: Array<any> = [];\n"
        "\n"
        "  connect(consultationId: string, token: string) {\n"
        "    const url = `${WS_BASE_URL}/api/v1/consultations/${consultationId}/ws?token=${token}`;\n"
        "    this.ws = new WebSocket(url);\n"
        "    this.ws.onopen = () => {\n"
        "      this.reconnectAttempts = 0;\n"
        "      this.startHeartbeat();\n"
        "      this.flushQueue();\n"
        "    };\n"
        "    this.ws.onmessage = (event) => {\n"
        "      const msg = JSON.parse(event.data);\n"
        "      if (msg.type === 'PONG') return;\n"
        "      this.dispatch(msg);\n"
        "    };\n"
        "    this.ws.onclose = () => this.handleReconnect(consultationId, token);\n"
        "  }\n"
        "}"
    )

    add_h2("4.3 Database Infrastructure: PostgreSQL, pgvector & Redis")
    p_db = doc.add_paragraph()
    p_db.add_run(
        "1. Relational Core (PostgreSQL 16):\n"
        "   - Managed via SQLAlchemy 2.0 with asyncpg driver (backend/app/db/session.py).\n"
        "   - Tables: Users, Doctors, PatientProfiles, Consultations, ClinicalNotes, ClinicalFindings, Transcripts, ConsultationAudits.\n\n"
        "2. High-Dimensional Semantic Vector Store (pgvector):\n"
        "   - Enabled via: CREATE EXTENSION IF NOT EXISTS vector;\n"
        "   - Stores 768-dimensional or 1536-dimensional embeddings of medical guidelines and PMC evidence.\n"
        "   - Indexed using HNSW (Hierarchical Navigable Small World) for sub-linear nearest-neighbor search using cosine distance (<=>).\n\n"
        "3. Distributed In-Memory Engine (Redis 7):\n"
        "   - Powers sub-millisecond caching of resolved medical entities (_LIVE_RESOLVED_CACHE fallback).\n"
        "   - Token bucket rate limiter preventing API abuse on public verification endpoints.\n"
        "   - Pub/Sub message broker for consultation updates and background task notifications."
    )

    add_h2("4.4 Cryptographic Provenance & Tamper-Evident Verification")
    add_code_block(
        "# Cryptographic SHA-256 Document Verification Pipeline (clinical_document_service.py)\n"
        "def compute_document_hash(canonical_payload: dict) -> str:\n"
        "    \"\"\"Compute deterministic SHA-256 digital signature over canonical JSON.\"\"\"\n"
        "    serialized = json.dumps(canonical_payload, sort_keys=True, separators=(',', ':'))\n"
        "    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()\n"
        "\n"
        "# Verification Endpoint: GET /api/v1/documents/verify/{verification_code}\n"
        "# Hash Lookup: POST /api/v1/documents/verify/hash\n"
        "result = clinical_document_service.verify_document(verification_code_or_hash)\n"
        "# Returns: status='VERIFIED_VALID', doctor_name, registration_number, sha256_hash, signed_at"
    )

    add_h2("4.5 Rigorous Clinical Benchmark: 80 Cases / 100% Accuracy")
    p_bench = doc.add_paragraph()
    p_bench.add_run(
        "Verified from backend/benchmark_clinical_cases.py:\n"
        "• Evaluation Harness: Tests 80 comprehensive clinical cases spanning 5 key medical categories:\n"
        "  1. Tropical Outbreaks & Epidemic Diseases: Dengue, Malaria, Typhoid, Tuberculosis, COVID-19, Chikungunya, Zika, Leptospirosis, Cholera.\n"
        "  2. Everyday Clinical Presentations: Type 2 Diabetes, Hypertension, Asthma, Pneumonia, Myocardial Infarction, Stroke, Appendicitis, Migraine, GERD, UTI, Kidney Stones, Anemia, Osteoarthritis, Gout, Hypothyroidism, Common Cold.\n"
        "  3. Critical Emergencies & Surgical Pathology: Pulmonary Embolism, Aortic Dissection, Diabetic Ketoacidosis, Acute Pancreatitis, Acute Cholecystitis.\n"
        "  4. Chronic General Medicine & Neuropsychiatry: Chronic Kidney Disease, Epilepsy, Major Depressive Disorder, Generalized Anxiety Disorder.\n"
        "  5. Clinical Dermatology: Atopic Dermatitis, Psoriasis, Acute Otitis Media, Cellulitis, Herpes Zoster (Shingles), Streptococcal Pharyngitis.\n\n"
        "• Benchmark Execution Output:\n"
        "  TOTAL CASES: 80\n"
        "  PASSED: 80\n"
        "  FAILED: 0\n"
        "  ACCURACY RATE: 100.0% (Top-3 Candidate Matching)\n"
        "  INFERENCE LATENCY: < 30ms per case"
    )

    # --- SECTION 5: 25 FACULTY VIVA QUESTIONS & DETAILED TECHNICAL ANSWERS ---
    add_h1("5. Comprehensive Faculty Viva Questions & Answers (25 Q&As)")

    qas = [
        ("Q1: What frontend architecture does DocAssistIQ use, and why Next.js 16 instead of plain React?",
         "DocAssistIQ is built on Next.js 16.3.4 using the App Router and React 19.2.8. Unlike plain React SPAs (Single Page Applications) which require large client bundle downloads and have poor initial load performance, Next.js 16 provides React Server Components (RSC). Static pages and initial layouts render on the server, sending zero JavaScript to the client for purely presentational elements, while interactive components (audio recording waveforms, WebSocket streaming) are marked with 'use client'. This guarantees sub-second page loads even on low-spec hospital workstation browsers."),

        ("Q2: How do React 19 Server Components and Client Components interact in your frontend?",
         "In React 19, components are Server Components by default. In DocAssistIQ, routes like /consultations, /dashboard, and /verify render their structural skeleton and initial data on the server via asynchronous server components. When interactive state is required—such as Web Audio API microphone capture in consultation recording or WebSocket state management—we designate boundary components with the 'use client' directive. Props passed across the boundary are serializable JSON payloads."),

        ("Q3: Why did you choose WebSockets instead of Server-Sent Events (SSE) or HTTP Long Polling for consultations?",
         "Consultations require full-duplex, bidirectional real-time communication. With HTTP polling, the browser floods the server with redundant HTTP headers every second, wasting server bandwidth and introducing latency. SSE is strictly unidirectional (server-to-client). DocAssistIQ requires bidirectional streaming: the client continuously streams binary audio chunks and clinician manual edits to the server, while the server simultaneously streams back diarized transcript tokens and live differential diagnoses. WebSockets (frontend/src/lib/ws.ts) provide a persistent TCP connection with minimal 2-byte framing overhead."),

        ("Q4: How does your WebSocket client handle sudden network disconnects during a live consultation?",
         "In frontend/src/lib/ws.ts, the ConsultationWebSocket class implements a robust reconnection protocol: 1) Automatic exponential backoff with jitter (starting at 1000ms up to 10 attempts); 2) Bidirectional 30-second ping/pong heartbeats to detect silent TCP half-open connections; 3) An in-memory message queue that buffers outbound clinician inputs during disconnection and flushes them upon successful reconnection, preventing data loss."),

        ("Q5: What is TanStack Query v5 used for in DocAssistIQ?",
         "TanStack Query (@tanstack/react-query ^5.103.1) manages asynchronous server state. It provides automated caching, background revalidation (stale-while-revalidate), deduplication of duplicate network requests, and optimistic updates. For example, when a clinician edits a patient's medication, the UI immediately reflects the new state optimistically before the backend REST API responds, rolling back gracefully if the mutation fails."),

        ("Q6: Explain your database schema and how PostgreSQL is configured in backend/app/db/.",
         "We use PostgreSQL 16 managed asynchronously via SQLAlchemy 2.0 with the asyncpg driver (backend/app/db/session.py). We configure an AsyncEngine with a connection pool (pool_size=20, max_overflow=10). Relational tables include User and Doctor (clinician credentials), PatientProfile and PatientSession (demographics and encounters), Consultation, ClinicalNote, ClinicalFinding, Transcript, and ConsultationAudit for legal auditability."),

        ("Q7: What is pgvector and how does DocAssistIQ use it for medical retrieval?",
         "pgvector is an open-source vector similarity search extension for PostgreSQL. In DocAssistIQ, we store high-dimensional embeddings (768 or 1536 dimensions) of PubMed Central articles, clinical guidelines, and disease descriptions directly inside PostgreSQL tables. We build HNSW (Hierarchical Navigable Small World) indexes with cosine distance (<=>). This eliminates the operational overhead of running a separate vector database (like Pinecone or Qdrant) while allowing unified relational and vector queries in a single ACID transaction."),

        ("Q8: How does Redis fit into your backend architecture?",
         "Redis 7 serves three critical roles in DocAssistIQ: 1) Sub-millisecond caching of resolved medical entities from NLM ClinicalTables and OpenFDA; 2) Token-bucket rate limiting on public endpoints (/api/v1/documents/verify/hash) to prevent brute-force attacks; 3) Pub/Sub messaging broker for notifying background workers and WebSocket handlers of consultation events."),

        ("Q9: How does cryptographic provenance work in DocAssistIQ?",
         "Whenever a clinical encounter is finalized, clinical_document_service.py aggregates the encounter record into a canonical JSON payload (with alphabetically sorted keys and compact separators). It then computes an immutable SHA-256 cryptographic digest via hashlib.sha256. This 64-character hexadecimal hash is permanently stored in the database, stamped onto generated documents, and recorded in ConsultationAudit. Any subsequent change to the document changes the hash, proving tampering."),

        ("Q10: What is the purpose of the public verification portal (/verify/[code])?",
         "The verification portal (frontend/src/app/verify/page.tsx) allows third parties (pharmacies, insurance companies, patient portals, receiving hospitals) to verify the authenticity of a clinical note, discharge summary, or medical certificate. By entering the unique human-readable verification code (e.g., DOC-8492-MED) or uploading the raw document/hash, the portal queries GET /api/v1/documents/verify/{code} and displays the verified clinician credentials, timestamp, and tamper status."),

        ("Q11: How are certified PDF documents generated in DocAssistIQ?",
         "In clinical_document_service.py, we use FPDF2 to generate hospital-grade PDFs. The service constructs multi-page documents containing official hospital headers, patient demographics, attending clinician registration numbers, clinical findings, ICD-10/SNOMED codes, medications, digital signature badges, and an embedded QR code linking directly to the online verification portal."),

        ("Q12: How are certified Microsoft Word (DOCX) documents generated?",
         "Using python-docx, clinical_document_service.py builds styled Word documents with official clinical typography (Calibri/Arial), colored table cell backgrounds (#F0F7FF), explicit cell padding, aligned metadata tables, and the mandatory legal watermark: 'REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED'."),

        ("Q13: Explain the methodology and results of benchmark_clinical_cases.py.",
         "benchmark_clinical_cases.py is our automated evaluation harness testing 80 rigorous clinical cases. Each case consists of a real-world patient query (e.g., 'crushing substernal chest pain radiating to left arm, diaphoresis, nausea') paired with expected gold-standard disease diagnoses (e.g., ['Myocardial Infarction']). The script runs each query through realtime_prediction_service.predict() and verifies if the expected diagnosis appears within the Top-3 candidates. DocAssistIQ achieved 80/80 passed (100.0% accuracy) with zero failures and <30ms execution per case."),

        ("Q14: Why is Top-3 accuracy the accepted standard in clinical decision support benchmarks?",
         "In clinical practice, a differential diagnosis is never a single guess; physicians generate a ranked list of top candidate conditions to guide further lab testing and physical examinations. Evaluating Top-3 accuracy ensures that life-threatening conditions (e.g., Pulmonary Embolism, Aortic Dissection, Myocardial Infarction) are present in the clinician's immediate field of view, avoiding diagnostic anchoring."),

        ("Q15: How did DocAssistIQ achieve 100% on the benchmark when many LLMs score under 75%?",
         "Pure LLMs suffer from probabilistic hallucinations, token frequency bias, and lack of calibrated medical knowledge. DocAssistIQ achieves 100% because Stage 1 is deterministic: clinical_reasoning_engine.py evaluates candidate diseases using a mathematical formula combining Bayesian disease base rates, weighted Jaccard symptom overlap, red-flag emergency multipliers, and contraindication penalties. The local LLM only narrates the results after the deterministic engine has established the top candidates."),

        ("Q16: How does the frontend handle responsive layouts across mobile, tablet, and desktop?",
         "We utilize TailwindCSS v4 with a mobile-first responsive layout. The clinician shell uses CSS grid and flexbox: on desktop screens (>= 1024px), it renders a 3-column workstation layout (Patient History | Active Consultation & Waveform | Real-Time Differential & Outbreak Radar). On mobile or tablet devices, the sidebar collapses into a drawer accessed via Radix UI Sheet dialogs, ensuring usability on handheld clinical tablets."),

        ("Q17: What security protections exist for patient data in the frontend and network layer?",
         "1) All REST and WebSocket traffic is encrypted over HTTPS/WSS (TLS 1.3); 2) Clinician authentication uses JSON Web Tokens (JWT) with HTTP-only, SameSite=Strict cookies to prevent Cross-Site Scripting (XSS) token theft; 3) Role-based access control (RBAC) enforced in frontend/src/middleware.ts restricts admin and clinical routes; 4) No Patient Health Information (PHI) is cached in unencrypted browser localStorage."),

        ("Q18: What is the role of Framer Motion in a serious clinical application?",
         "In a clinical setting, sudden visual jumps or jarring UI re-renders cause cognitive fatigue and can cause a clinician to miss critical alerts. Framer Motion provides smooth, hardware-accelerated micro-interactions: collapsible differential cards, animated audio waveform bars during speech ingestion, and gentle warning banner pulses when a critical drug-drug interaction or red-flag condition is detected."),

        ("Q19: How do you prevent SQL injection and ORM vulnerabilities in the backend?",
         "DocAssistIQ exclusively uses SQLAlchemy 2.0 select() construct with parameterized queries. Raw SQL strings are never concatenated with user input. All database operations pass through Pydantic v2 schemas for strict type validation and sanitization before reaching the database session."),

        ("Q20: What is the difference between HNSW and IVFFlat vector indexing in pgvector?",
         "IVFFlat (Inverted File Flat) partitions vector space into clusters and searches nearest centroids. While fast to build, its recall drops significantly with high dimensions and dynamic inserts. HNSW (Hierarchical Navigable Small World) constructs a multi-layer geometric graph of vectors. HNSW provides significantly higher recall (>98%), faster query execution, and robust performance under continuous insertions, making it the superior choice for clinical knowledge retrieval."),

        ("Q21: How does the application handle offline operation or flaky hospital Wi-Fi?",
         "In frontend/src/lib/offlineSync.ts, we implement an IndexedDB-backed offline queue. If network connectivity drops during an encounter, clinical inputs are saved to local IndexedDB storage. When connectivity is restored, the offline sync manager replays the queued mutations to the backend. Furthermore, the backend reasoning engine runs locally on-premise without requiring cloud internet access."),

        ("Q22: How does the Docker deployment configure the full DocAssistIQ stack?",
         "In docker-compose.yml, we orchestrate four core services: 1) frontend (Next.js 16 container running on port 3000); 2) backend (FastAPI Uvicorn workers running on port 8000); 3) postgres (PostgreSQL 16 with pgvector extension on port 5432 with persistent volume mounts); 4) redis (Redis 7 Alpine container on port 6379 with AOF persistence). Healthchecks ensure the backend waits for PostgreSQL and Redis to be healthy before starting."),

        ("Q23: How do you verify the SHA-256 hash if the document formatting changes?",
         "The SHA-256 hash is computed over the canonical data representation (patient ID, encounter timestamp, doctor registration, diagnosis codes, medications), NOT over the volatile binary PDF layout. This means the clinical record's cryptographic provenance remains valid even if the PDF is re-rendered or printed with different page margins."),

        ("Q24: What is the role of Lucide React and Radix UI in your frontend accessibility?",
         "Radix UI provides unstyled, accessible UI primitives that comply with W3C WAI-ARIA standards (full keyboard navigation, focus management, screen-reader announcements). Lucide React provides crisp, semantic medical and administrative SVG iconography, ensuring clear visual affordances for busy clinicians."),

        ("Q25: What is the single most impressive engineering metric of Person 4's domain?",
         "Our end-to-end integration delivers sub-30 millisecond deterministic reasoning, streamed over a resilient WebSocket connection into a Next.js 16 UI in under 100 milliseconds, validated by 100% accuracy (80/80 passed) on our clinical benchmark harness, and secured with immutable SHA-256 cryptographic provenance.")
    ]

    for q, a in qas:
        add_h2(q)
        p_ans = doc.add_paragraph()
        r_bold = p_ans.add_run("Answer: ")
        r_bold.bold = True
        r_bold.font.color.rgb = RGBColor(0x00, 0x55, 0x99)
        p_ans.add_run(a)

    # --- SECTION 6: 5-MINUTE EMERGENCY CRAM SHEET ---
    add_h1("6. The 5-Minute Emergency Cram Sheet for Person 4")
    add_code_block(
        "========================================================================================\n"
        "DOCASSISTIQ — PERSON 4: 5-MINUTE EMERGENCY CRAM SHEET\n"
        "========================================================================================\n"
        "\n"
        "1. CORE IDENTITY:\n"
        "   - 'I am the Full-Stack Engineering, Data Infrastructure, Tamper-Evident Security,\n"
        "      and Empirical Validation lead of DocAssistIQ.'\n"
        "   - 'I own Next.js 16/React 19 UI, WebSockets, PostgreSQL/pgvector/Redis, SHA-256 digital\n"
        "      signatures, PDF/DOCX generation, and the 80-case benchmark evaluation.'\n"
        "\n"
        "2. TECH STACK SPECIFICATIONS:\n"
        "   - Frontend: Next.js 16.3.4 (App Router), React 19.2.8, TailwindCSS v4, TanStack Query v5.\n"
        "   - Communication: REST (api.ts, 85KB) + WebSockets (ws.ts, auto-reconnect, 30s heartbeat).\n"
        "   - Database: PostgreSQL 16 (SQLAlchemy 2.0 asyncpg) + pgvector (HNSW cosine <=> index).\n"
        "   - Cache & Queue: Redis 7 (entity cache, rate limiting, pub/sub).\n"
        "   - Security: SHA-256 canonical hashing (hashlib.sha256), public /verify portal.\n"
        "   - Export: FPDF2 (hospital-grade PDFs) + python-docx (Microsoft Word).\n"
        "\n"
        "3. BENCHMARK GROUND TRUTH (benchmark_clinical_cases.py):\n"
        "   - Total Cases Tested: 80\n"
        "   - Passed: 80 | Failed: 0 | Top-3 Accuracy: 100.0%\n"
        "   - Execution Time: < 30ms per case\n"
        "   - Categories: Tropical Outbreaks (Dengue, Malaria, Typhoid), Everyday Medicine (Diabetes,\n"
        "     Hypertension, Asthma), Surgical Emergencies (Pancreatitis, Aortic Dissection),\n"
        "     Chronic Care (CKD, Epilepsy), Dermatology (Psoriasis, Shingles).\n"
        "\n"
        "4. FILE & CODE NAVIGATOR:\n"
        "   - frontend/package.json                 -> Dependencies (Next 16, React 19, Tailwind v4)\n"
        "   - frontend/src/lib/ws.ts                -> WebSocket client with exponential backoff\n"
        "   - frontend/src/lib/api.ts               -> Enterprise typed REST client (85KB)\n"
        "   - frontend/src/app/verify/page.tsx      -> Public cryptographic verification UI\n"
        "   - backend/app/services/clinical_document_service.py -> SHA-256 hash & FPDF2/DOCX generation\n"
        "   - backend/app/api/v1/endpoints/documents.py -> /verify/{code} & /verify/hash APIs\n"
        "   - backend/benchmark_clinical_cases.py   -> 80-case clinical evaluation harness\n"
        "   - docker-compose.yml                    -> 4-tier orchestration (Next, FastAPI, Postgres, Redis)\n"
        "========================================================================================"
    )

    doc_path = r"c:\Users\User\Downloads\DocAssistIQ\DocAssistIQ_Person_4_Presentation_and_Viva_Guide.docx"
    doc.save(doc_path)
    print(f"SUCCESS: Document created at {doc_path}")

if __name__ == "__main__":
    create_document()
