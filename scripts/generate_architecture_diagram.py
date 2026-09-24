"""DocAssistIQ — High-Resolution Professional System Architecture Diagram Generator.

Generates an ultra-crisp, publication-grade system architecture diagram (PNG & SVG)
accurately reflecting the exact latest codebase, components, protocols, and data flows.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path

def draw_shadowed_box(ax, x, y, w, h, bg_color, border_color, border_width=1.5, rx=0.2, alpha=1.0):
    """Draw a rounded rectangular box with a soft drop shadow."""
    # Shadow
    shadow = patches.FancyBboxPatch(
        (x + 0.08, y - 0.08), w, h,
        boxstyle=f"round,pad=0,rounding_size={rx}",
        facecolor="#CBD5E1", edgecolor="none", alpha=0.45, zorder=2
    )
    ax.add_patch(shadow)
    
    # Main Box
    box = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={rx}",
        facecolor=bg_color, edgecolor=border_color,
        linewidth=border_width, alpha=alpha, zorder=3
    )
    ax.add_patch(box)
    return box

def draw_badge(ax, x, y, text, bg_color="#0D9488", text_color="#FFFFFF", fontsize=7.5, pad=0.15):
    """Draw a compact pill badge for tech stack tags or protocol labels."""
    badge = patches.FancyBboxPatch(
        (x, y), len(text) * 0.12 + pad * 2, 0.32,
        boxstyle="round,pad=0.08,rounding_size=0.1",
        facecolor=bg_color, edgecolor="none", zorder=6
    )
    ax.add_patch(badge)
    ax.text(x + (len(text) * 0.12 + pad * 2) / 2, y + 0.16, text,
            color=text_color, fontsize=fontsize, weight="bold",
            ha="center", va="center", zorder=7, fontfamily="sans-serif")

def draw_arrow(ax, x1, y1, x2, y2, label="", color="#475569", lw=1.6, ls="-", label_offset=(0, 0.18)):
    """Draw an arrow with an optional floating protocol label."""
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="->,head_width=0.35,head_length=0.45",
            color=color, lw=lw, ls=ls, shrinkA=4, shrinkB=4
        ),
        zorder=5
    )
    if label:
        mx = (x1 + x2) / 2 + label_offset[0]
        my = (y1 + y2) / 2 + label_offset[1]
        bbox_props = dict(boxstyle="round,pad=0.2", fc="#FFFFFF", ec=color, lw=0.8, alpha=0.92)
        ax.text(mx, my, label, color=color, fontsize=7.0, weight="bold",
                ha="center", va="center", bbox=bbox_props, zorder=6, fontfamily="sans-serif")

def generate_architecture_diagram(output_png="DocAssistIQ_System_Architecture_Diagram.png", output_svg=None):
    # Dimensions: 22 x 15 inches at 300 DPI -> 6600 x 4500 px
    fig, ax = plt.subplots(figsize=(22, 14.5), dpi=300)
    ax.set_xlim(0, 22)
    ax.set_ylim(0, 14.5)
    ax.axis("off")
    fig.patch.set_facecolor("#F8FAFC")  # Crisp slate background

    # -----------------------------------------------------------------------
    # HEADER BANNER
    # -----------------------------------------------------------------------
    header_box = patches.FancyBboxPatch(
        (0.6, 13.3), 20.8, 0.95,
        boxstyle="round,pad=0.08,rounding_size=0.15",
        facecolor="#0F2942", edgecolor="#0D9488", linewidth=2.0, zorder=3
    )
    ax.add_patch(header_box)
    ax.text(1.0, 13.9, "DocAssistIQ — Enterprise Clinical Decision Support & Ambient Intelligence Platform",
            color="#FFFFFF", fontsize=15.0, weight="bold", va="center", fontfamily="sans-serif")
    ax.text(1.0, 13.52, "LATEST CODEBASE ARCHITECTURAL TOPOLOGY (MODULAR MONOLITH + DETERMINISTIC REASONING + REALTIME ASR + LOCAL LLM)",
            color="#38BDF8", fontsize=8.5, weight="bold", va="center", fontfamily="sans-serif")
    
    # System Status Badges in Header
    draw_badge(ax, 17.0, 13.6, "FastAPI + Next.js 14", bg_color="#0284C7", text_color="#FFFFFF", fontsize=7.5)
    draw_badge(ax, 18.8, 13.6, "Production Architecture v3.4", bg_color="#0D9488", text_color="#FFFFFF", fontsize=7.5)

    # -----------------------------------------------------------------------
    # LAYER 1: CLIENT & PRESENTATION TIER (TOP)
    # -----------------------------------------------------------------------
    draw_shadowed_box(ax, 0.6, 10.9, 20.8, 2.15, "#FFFFFF", "#0284C7", border_width=1.8, rx=0.15)
    ax.text(0.9, 12.8, "1. CLIENT & PRESENTATION TIER (Next.js 14 App Router, React 19, TypeScript, TailwindCSS)",
            color="#0F2942", fontsize=10.5, weight="bold", fontfamily="sans-serif")

    # Client Component Sub-boxes
    # Box 1A: Audio Capture & WebSocket Streamer
    draw_shadowed_box(ax, 0.9, 11.1, 4.7, 1.45, "#F0F9FF", "#38BDF8", border_width=1.2, rx=0.1)
    ax.text(1.1, 12.35, "Browser Audio Capture & Streamer", color="#0369A1", fontsize=9.0, weight="bold")
    ax.text(1.1, 12.05, "• Web Audio API (16kHz Linear PCM)", color="#1E293B", fontsize=7.8)
    ax.text(1.1, 11.75, "• Binary Chunking (250ms Audio Frames)", color="#1E293B", fontsize=7.8)
    ax.text(1.1, 11.45, "• WSS Client (`/api/v1/ws/consultations/{id}`)", color="#1E293B", fontsize=7.8)
    ax.text(1.1, 11.2, "• Mandatory Patient Consent Interlock Gate", color="#DC2626", fontsize=7.5, weight="bold")

    # Box 1B: Real-time Transcript & Diarization Stream
    draw_shadowed_box(ax, 5.8, 11.1, 4.8, 1.45, "#F0FDF4", "#4ADE80", border_width=1.2, rx=0.1)
    ax.text(6.0, 12.35, "Live Consultation Room UI", color="#15803D", fontsize=9.0, weight="bold")
    ax.text(6.0, 12.05, "• Real-time Speaker Bubbles (Doctor vs Patient)", color="#1E293B", fontsize=7.8)
    ax.text(6.0, 11.75, "• Live VAD Activity & Waveform Visualizer", color="#1E293B", fontsize=7.8)
    ax.text(6.0, 11.45, "• In-flight Transcript Correction & Editing", color="#1E293B", fontsize=7.8)
    ax.text(6.0, 11.2, "• Path: `frontend/src/app/(shell)/consultations`", color="#64748B", fontsize=7.2)

    # Box 1C: Differential Diagnosis & Reasoning Card
    draw_shadowed_box(ax, 10.8, 11.1, 5.0, 1.45, "#FEF3C7", "#F59E0B", border_width=1.2, rx=0.1)
    ax.text(11.0, 12.35, "Diagnostic Decision Support Cards", color="#B45309", fontsize=9.0, weight="bold")
    ax.text(11.0, 12.05, "• Ranked Top-5 Candidate Disease Cards", color="#1E293B", fontsize=7.8)
    ax.text(11.0, 11.75, "• Transparent 'Why?' Justification & Missing Findings", color="#1E293B", fontsize=7.8)
    ax.text(11.0, 11.45, "• Master Red Flag Critical Emergency Banners", color="#DC2626", fontsize=7.8, weight="bold")
    ax.text(11.0, 11.2, "• Reference Meds ('CLINICIAN REVIEW REQUIRED')", color="#B45309", fontsize=7.2, weight="bold")

    # Box 1D: Interactive SOAP Editor & Hub
    draw_shadowed_box(ax, 16.0, 11.1, 5.1, 1.45, "#FAF5FF", "#A855F7", border_width=1.2, rx=0.1)
    ax.text(16.2, 12.35, "Interactive SOAP Note & Hub Portal", color="#7E22CE", fontsize=9.0, weight="bold")
    ax.text(16.2, 12.05, "• Subjective, Objective, Assessment, Plan", color="#1E293B", fontsize=7.8)
    ax.text(16.2, 11.75, "• Immutable Cryptographic Sign & Export", color="#1E293B", fontsize=7.8)
    ax.text(16.2, 11.45, "• Verified Doctor Knowledge Hub (`/hub`)", color="#1E293B", fontsize=7.8)
    ax.text(16.2, 11.2, "• Hospital Tenant & RBAC Role Switcher", color="#64748B", fontsize=7.2)

    # -----------------------------------------------------------------------
    # LAYER 2: API GATEWAY & REAL-TIME TRANSPORT LAYER
    # -----------------------------------------------------------------------
    draw_shadowed_box(ax, 0.6, 9.15, 20.8, 1.35, "#FFFFFF", "#0F2942", border_width=1.8, rx=0.15)
    ax.text(0.9, 10.25, "2. API GATEWAY, AUTHENTICATION & REAL-TIME WEBSOCKET TRANSPORT (FastAPI / ASGI Uvicorn)",
            color="#0F2942", fontsize=10.5, weight="bold", fontfamily="sans-serif")

    # Gateway components
    draw_shadowed_box(ax, 0.9, 9.3, 4.7, 0.75, "#F1F5F9", "#94A3B8", border_width=1.0, rx=0.08)
    ax.text(1.1, 9.8, "Auth, RBAC & Multi-Tenancy", color="#0F2942", fontsize=8.2, weight="bold")
    ax.text(1.1, 9.45, "JWT OAuth2, Tenant Scoping, Request ID Tracing", color="#475569", fontsize=7.5)

    draw_shadowed_box(ax, 5.8, 9.3, 4.8, 0.75, "#F1F5F9", "#94A3B8", border_width=1.0, rx=0.08)
    ax.text(6.0, 9.8, "Authenticated WebSocket (`ws.py`)", color="#0F2942", fontsize=8.2, weight="bold")
    ax.text(6.0, 9.45, "Binary Audio Buffer Aggregator & JSON Broadcaster", color="#475569", fontsize=7.5)

    draw_shadowed_box(ax, 10.8, 9.3, 5.0, 0.75, "#F1F5F9", "#94A3B8", border_width=1.0, rx=0.08)
    ax.text(11.0, 9.8, "Redis Pub/Sub Channel Broker", color="#0F2942", fontsize=8.2, weight="bold")
    ax.text(11.0, 9.45, "Multi-worker event bus & session state sync", color="#475569", fontsize=7.5)

    draw_shadowed_box(ax, 16.0, 9.3, 5.1, 0.75, "#F1F5F9", "#94A3B8", border_width=1.0, rx=0.08)
    ax.text(16.2, 9.8, "API Router V1 (`router.py`)", color="#0F2942", fontsize=8.2, weight="bold")
    ax.text(16.2, 9.45, "27 Thin REST Routers: /consultations, /patients, /hub...", color="#475569", fontsize=7.5)

    # Connectors Layer 1 to Layer 2
    draw_arrow(ax, 3.25, 11.1, 3.25, 10.05, label="WSS Binary Audio", color="#0284C7")
    draw_arrow(ax, 8.2, 10.5, 8.2, 11.1, label="JSON Transcript Deltas", color="#15803D")
    draw_arrow(ax, 13.3, 10.5, 13.3, 11.1, label="Top-5 Differential JSON", color="#B45309")
    draw_arrow(ax, 18.55, 11.1, 18.55, 10.05, label="HTTPS REST / Audit", color="#7E22CE")

    # -----------------------------------------------------------------------
    # LAYER 3: CORE APPLICATION & DOMAIN SERVICES LAYER (MODULAR MONOLITH)
    # -----------------------------------------------------------------------
    draw_shadowed_box(ax, 0.6, 3.75, 20.8, 5.05, "#FFFFFF", "#0D9488", border_width=2.0, rx=0.15)
    ax.text(0.9, 8.55, "3. CORE DOMAIN SERVICES & CLINICAL INTELLIGENCE ENGINES (Python 3.11 / Modular Monolith)",
            color="#0F2942", fontsize=11.0, weight="bold", fontfamily="sans-serif")
    ax.text(12.5, 8.55, "[ 57 Domain Services • Zero Uncontrolled Network Dependencies in Reasoning Core ]",
            color="#0D9488", fontsize=8.2, weight="bold", fontfamily="sans-serif")

    # Sub-Engine 3A: Speech & Audio Processing
    draw_shadowed_box(ax, 0.9, 4.0, 4.7, 4.25, "#F8FAFC", "#0D9488", border_width=1.2, rx=0.12)
    ax.text(1.1, 8.05, "A. Speech & Audio Processing", color="#0F2942", fontsize=9.2, weight="bold")
    draw_badge(ax, 1.1, 7.6, "ASR & Diarization", bg_color="#0D9488")
    
    ax.text(1.1, 7.25, "• Faster-Whisper Service (Large-v3)", color="#1E293B", fontsize=8.0, weight="bold")
    ax.text(1.3, 6.95, "- CTranslate2 GPU Acceleration", color="#475569", fontsize=7.5)
    ax.text(1.3, 6.70, "- Silero Voice Activity Detection (VAD)", color="#475569", fontsize=7.5)
    ax.text(1.3, 6.45, "- Streaming PCM chunk accumulation", color="#475569", fontsize=7.5)
    
    ax.text(1.1, 6.10, "• PyAnnote Audio 3.1 Pipeline", color="#1E293B", fontsize=8.0, weight="bold")
    ax.text(1.3, 5.80, "- Multi-speaker clustering & embeddings", color="#475569", fontsize=7.5)
    ax.text(1.3, 5.55, "- Clinician vs Patient role assignment", color="#475569", fontsize=7.5)
    ax.text(1.3, 5.30, "- Overlap speech detection", color="#475569", fontsize=7.5)
    
    ax.text(1.1, 4.95, "• Transcript Persistence Service", color="#1E293B", fontsize=8.0, weight="bold")
    ax.text(1.3, 4.65, "- Timestamped speaker segments", color="#475569", fontsize=7.5)
    ax.text(1.3, 4.40, "- Manual doctor correction audit trail", color="#475569", fontsize=7.5)
    ax.text(1.1, 4.15, "Source: `app/services/asr_service.py`, `diarization_service.py`", color="#64748B", fontsize=6.8)

    # Sub-Engine 3B: Clinical NLP & Concept Normalization
    draw_shadowed_box(ax, 5.8, 4.0, 4.8, 4.25, "#F8FAFC", "#0284C7", border_width=1.2, rx=0.12)
    ax.text(6.0, 8.05, "B. Clinical NLP & Normalization", color="#0F2942", fontsize=9.2, weight="bold")
    draw_badge(ax, 6.0, 7.6, "CNLP & Ontologies", bg_color="#0284C7")
    
    ax.text(6.0, 7.25, "• Clinical NLP & Note Parser", color="#1E293B", fontsize=8.0, weight="bold")
    ax.text(6.2, 6.95, "- Entity extraction (Symptoms, History, Vitals)", color="#475569", fontsize=7.5)
    ax.text(6.2, 6.70, "- NegEx Negation Detection Algorithm", color="#DC2626", fontsize=7.5, weight="bold")
    ax.text(6.2, 6.45, "- Temporal onset duration parsing (delta_t)", color="#475569", fontsize=7.5)
    
    ax.text(6.0, 6.10, "• Multi-Ontology Concept Normalizer", color="#1E293B", fontsize=8.0, weight="bold")
    ax.text(6.2, 5.80, "- SNOMED CT clinical findings mapping", color="#475569", fontsize=7.5)
    ax.text(6.2, 5.55, "- UMLS CUI semantic ground truth", color="#475569", fontsize=7.5)
    ax.text(6.2, 5.30, "- RxNorm drug identification (RxCUIs)", color="#475569", fontsize=7.5)
    
    ax.text(6.0, 4.95, "• Canonical Clinical Representation", color="#1E293B", fontsize=8.0, weight="bold")
    ax.text(6.2, 4.65, "- Structured Pydantic payload", color="#475569", fontsize=7.5)
    ax.text(6.2, 4.40, "- Feeds Reasoning & Safety Engines", color="#475569", fontsize=7.5)
    ax.text(6.0, 4.15, "Source: `app/services/clinical_nlp.py`, `concept_normalizer.py`", color="#64748B", fontsize=6.8)

    # Sub-Engine 3C: Deterministic Clinical Reasoning Core (GOD-LEVEL AI)
    draw_shadowed_box(ax, 10.8, 4.0, 5.0, 4.25, "#FFFBEB", "#F59E0B", border_width=1.5, rx=0.12)
    ax.text(11.0, 8.05, "C. Deterministic Clinical Reasoning", color="#92400E", fontsize=9.2, weight="bold")
    draw_badge(ax, 11.0, 7.6, "100% Offline • < 85ms", bg_color="#F59E0B")
    
    ax.text(11.0, 7.25, "• Multi-Factor Objective Scoring", color="#1E293B", fontsize=8.0, weight="bold")
    ax.text(11.2, 6.95, "- Jaccard symptom similarity score (w1=0.30)", color="#475569", fontsize=7.5)
    ax.text(11.2, 6.70, "- Cardinal pathognomonic match (w2=0.35)", color="#475569", fontsize=7.5)
    ax.text(11.2, 6.45, "- Incubation timeline fit math (w3=0.15)", color="#475569", fontsize=7.5)
    ax.text(11.2, 6.20, "- Geographic travel prior match (w4=0.10)", color="#475569", fontsize=7.5)
    ax.text(11.2, 5.95, "- Syndromic cluster bonus (w5=0.10)", color="#475569", fontsize=7.5)
    ax.text(11.2, 5.70, "- Negation penalty deduction (w6=0.25)", color="#DC2626", fontsize=7.5, weight="bold")
    
    ax.text(11.0, 5.35, "• Comprehensive Medical Knowledge KB", color="#1E293B", fontsize=8.0, weight="bold")
    ax.text(11.2, 5.05, "- 100+ Multi-Specialty Clinical Diseases", color="#475569", fontsize=7.5)
    ax.text(11.2, 4.80, "- Cardiology, Pulm, Neuro, ID, GI, Rheum", color="#475569", fontsize=7.5)
    ax.text(11.2, 4.55, "- Pre-computes 90% of Diagnostic Inference", color="#059669", fontsize=7.5, weight="bold")
    ax.text(11.0, 4.15, "Source: `app/services/clinical_reasoning_engine.py`, `offline_disease_kb.py`", color="#64748B", fontsize=6.8)

    # Sub-Engine 3D: Safety, RAG & Constrained LLM Explainer
    draw_shadowed_box(ax, 16.0, 4.0, 5.1, 4.25, "#FEF2F2", "#DC2626", border_width=1.5, rx=0.12)
    ax.text(16.2, 8.05, "D. Safety Guardrails & Local LLM", color="#991B1B", fontsize=9.2, weight="bold")
    draw_badge(ax, 16.2, 7.6, "Zero-Bypass Safety", bg_color="#DC2626")
    
    ax.text(16.2, 7.25, "• Master Red Flag Safety Engine", color="#DC2626", fontsize=8.0, weight="bold")
    ax.text(16.4, 6.95, "- RF-001 Severe Chest Pain (ACS/PE)", color="#7F1D1D", fontsize=7.5)
    ax.text(16.4, 6.70, "- RF-002 Severe Dyspnea (Airway/Hypoxia)", color="#7F1D1D", fontsize=7.5)
    ax.text(16.4, 6.45, "- RF-003 Stroke Signs (Facial droop/speech)", color="#7F1D1D", fontsize=7.5)
    ax.text(16.4, 6.20, "- RF-004 Anaphylaxis & RF-005 Altered Mental", color="#7F1D1D", fontsize=7.5)
    
    ax.text(16.2, 5.85, "• Dual-Mode Medication & RxNav DDI", color="#1E293B", fontsize=8.0, weight="bold")
    ax.text(16.4, 5.55, "- NIH RxNav live Drug-Drug Interaction", color="#475569", fontsize=7.5)
    ax.text(16.4, 5.30, "- Allergy contraindication cross-check", color="#475569", fontsize=7.5)
    
    ax.text(16.2, 4.95, "• Constrained Local LLM Narrator", color="#1E293B", fontsize=8.0, weight="bold")
    ax.text(16.4, 4.65, "- Llama-3.2-3B via Ollama (Local GPU)", color="#475569", fontsize=7.5)
    ax.text(16.4, 4.40, "- Explains pre-computed scores into 'Why?'", color="#059669", fontsize=7.5, weight="bold")
    ax.text(16.2, 4.15, "Source: `app/services/safety_engine.py`, `llm_service.py`, `medication_service.py`", color="#64748B", fontsize=6.8)

    # Inter-Service Connectors within Layer 3
    draw_arrow(ax, 5.6, 6.1, 5.8, 6.1, color="#0D9488")
    draw_arrow(ax, 10.6, 6.1, 10.8, 6.1, color="#0284C7")
    draw_arrow(ax, 15.8, 6.1, 16.0, 6.1, color="#F59E0B")

    # -----------------------------------------------------------------------
    # LAYER 4: ASYNCHRONOUS PROCESSING & WORKERS
    # -----------------------------------------------------------------------
    draw_shadowed_box(ax, 0.6, 2.3, 20.8, 1.25, "#FFFFFF", "#6366F1", border_width=1.8, rx=0.15)
    ax.text(0.9, 3.25, "4. ASYNCHRONOUS TASK WORKER & EVENT BROKER LAYER (Celery 5.3 + Redis 7)",
            color="#0F2942", fontsize=10.5, weight="bold", fontfamily="sans-serif")

    draw_shadowed_box(ax, 0.9, 2.45, 4.7, 0.65, "#EEF2FF", "#C7D2FE", border_width=1.0, rx=0.08)
    ax.text(1.1, 2.9, "Document OCR & Extraction", color="#3730A3", fontsize=8.0, weight="bold")
    ax.text(1.1, 2.6, "Tesseract / LayoutLM lab report parsing", color="#475569", fontsize=7.2)

    draw_shadowed_box(ax, 5.8, 2.45, 4.8, 0.65, "#EEF2FF", "#C7D2FE", border_width=1.0, rx=0.08)
    ax.text(6.0, 2.9, "Batch Vector Embedding Tasks", color="#3730A3", fontsize=8.0, weight="bold")
    ax.text(6.0, 2.6, "Sentence-Transformers indexing into pgvector", color="#475569", fontsize=7.2)

    draw_shadowed_box(ax, 10.8, 2.45, 5.0, 0.65, "#EEF2FF", "#C7D2FE", border_width=1.0, rx=0.08)
    ax.text(11.0, 2.9, "PubMed & Guideline Harvester", color="#3730A3", fontsize=8.0, weight="bold")
    ax.text(11.0, 2.6, "Scheduled medical evidence & outbreak updates", color="#475569", fontsize=7.2)

    draw_shadowed_box(ax, 16.0, 2.45, 5.1, 0.65, "#EEF2FF", "#C7D2FE", border_width=1.0, rx=0.08)
    ax.text(16.2, 2.9, "Audit Log Aggregator & Cleanup", color="#3730A3", fontsize=8.0, weight="bold")
    ax.text(16.2, 2.6, "SHA-256 cryptographic chaining & retention", color="#475569", fontsize=7.2)

    # -----------------------------------------------------------------------
    # LAYER 5: DATA PERSISTENCE & INFRASTRUCTURE TIER (BOTTOM)
    # -----------------------------------------------------------------------
    draw_shadowed_box(ax, 0.6, 0.35, 20.8, 1.75, "#FFFFFF", "#1E293B", border_width=2.0, rx=0.15)
    ax.text(0.9, 1.8, "5. DATA PERSISTENCE, VECTOR STORAGE & CLOUD INFRASTRUCTURE (Docker Compose Environment)",
            color="#0F2942", fontsize=10.5, weight="bold", fontfamily="sans-serif")

    # DB 1: PostgreSQL 16 + pgvector
    draw_shadowed_box(ax, 0.9, 0.5, 6.4, 1.1, "#F8FAFC", "#334155", border_width=1.2, rx=0.1)
    ax.text(1.1, 1.35, "PostgreSQL 16 + pgvector (`docassistiq_db`)", color="#0F2942", fontsize=8.5, weight="bold")
    ax.text(1.1, 1.10, "• Relational: users, doctors, patients, consultations, SOAP notes", color="#334155", fontsize=7.5)
    ax.text(1.1, 0.85, "• Vector Storage: 384-dim HNSW embeddings (medical_documents)", color="#334155", fontsize=7.5)
    ax.text(1.1, 0.60, "• Cryptographic Audit Trail: SHA-256 chained audit_logs", color="#15803D", fontsize=7.2, weight="bold")

    # DB 2: Redis 7
    draw_shadowed_box(ax, 7.5, 0.5, 4.8, 1.1, "#F8FAFC", "#DC2626", border_width=1.2, rx=0.1)
    ax.text(7.7, 1.35, "Redis 7.2 (`docassistiq_redis`)", color="#991B1B", fontsize=8.5, weight="bold")
    ax.text(7.7, 1.10, "• Port 6379 DB 0: Session cache & pub/sub", color="#334155", fontsize=7.5)
    ax.text(7.7, 0.85, "• Port 6379 DB 1: Celery task message broker", color="#334155", fontsize=7.5)
    ax.text(7.7, 0.60, "• Port 6379 DB 2: Celery task result backend", color="#334155", fontsize=7.5)

    # DB 3: MinIO S3 Object Storage
    draw_shadowed_box(ax, 12.5, 0.5, 4.5, 1.1, "#F8FAFC", "#B45309", border_width=1.2, rx=0.1)
    ax.text(12.7, 1.35, "MinIO S3 Storage (`docassistiq_minio`)", color="#B45309", fontsize=8.5, weight="bold")
    ax.text(12.7, 1.10, "• Ports 9010 (API) / 9011 (Console)", color="#334155", fontsize=7.5)
    ax.text(12.7, 0.85, "• Bucket: `docassistiq`", color="#334155", fontsize=7.5)
    ax.text(12.7, 0.60, "• Audio PCM recordings & lab PDF files", color="#334155", fontsize=7.5)

    # DB 4: Local Ollama / AI Provider
    draw_shadowed_box(ax, 17.2, 0.5, 3.9, 1.1, "#F8FAFC", "#4338CA", border_width=1.2, rx=0.1)
    ax.text(17.4, 1.35, "Local AI Runtime (`Ollama`)", color="#4338CA", fontsize=8.5, weight="bold")
    ax.text(17.4, 1.10, "• Model: Llama-3.2-3B Instruct", color="#334155", fontsize=7.5)
    ax.text(17.4, 0.85, "• Host: `localhost:11434`", color="#334155", fontsize=7.5)
    ax.text(17.4, 0.60, "• Zero cloud data leakage / Local GPU", color="#15803D", fontsize=7.2, weight="bold")

    # Connections between Layer 3, Layer 4, and Layer 5
    draw_arrow(ax, 4.1, 3.75, 4.1, 1.6, label="Asyncpg ORM", color="#334155")
    draw_arrow(ax, 9.9, 3.75, 9.9, 1.6, label="Redis Pub/Sub", color="#DC2626")
    draw_arrow(ax, 14.7, 3.75, 14.7, 1.6, label="S3 Object API", color="#B45309")
    draw_arrow(ax, 19.15, 4.0, 19.15, 1.6, label="HTTP Local API", color="#4338CA")

    # -----------------------------------------------------------------------
    # SAVE FILE
    # -----------------------------------------------------------------------
    plt.tight_layout()
    png_path = os.path.abspath(output_png)
    plt.savefig(png_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    print(f"Generated high-resolution architecture diagram (PNG): {png_path}")

    if output_svg:
        svg_path = os.path.abspath(output_svg)
        plt.savefig(svg_path, format="svg", facecolor=fig.get_facecolor(), edgecolor="none")
        print(f"Generated vector architecture diagram (SVG): {svg_path}")

    plt.close()
    return png_path

if __name__ == "__main__":
    generate_architecture_diagram("DocAssistIQ_System_Architecture_Diagram.png", "DocAssistIQ_System_Architecture_Diagram.svg")
