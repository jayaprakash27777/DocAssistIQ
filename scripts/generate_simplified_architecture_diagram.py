"""DocAssistIQ — Simplified, High-Clarity Professional System Architecture Diagram Generator.

Creates a clean, elegant, highly scannable, and publication-ready architecture diagram
reflecting all technical components from the latest codebase without visual clutter.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_card(ax, x, y, w, h, title, subtitle, items, bg_color="#FFFFFF", border_color="#CBD5E1", 
              header_color="#0F2942", badge_text=None, badge_color="#0D9488", border_width=1.4):
    """Draw a clean modern card with rounded corners, header, and bullet points."""
    # Subtle drop shadow
    shadow = patches.FancyBboxPatch(
        (x + 0.05, y - 0.05), w, h,
        boxstyle="round,pad=0,rounding_size=0.12",
        facecolor="#E2E8F0", edgecolor="none", alpha=0.5, zorder=2
    )
    ax.add_patch(shadow)

    # Main Card Box
    card = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0,rounding_size=0.12",
        facecolor=bg_color, edgecolor=border_color,
        linewidth=border_width, zorder=3
    )
    ax.add_patch(card)

    # Title & Subtitle
    ax.text(x + 0.22, y + h - 0.32, title, color=header_color, fontsize=9.2, weight="bold", fontfamily="sans-serif", zorder=5)
    if subtitle:
        ax.text(x + 0.22, y + h - 0.54, subtitle, color="#64748B", fontsize=7.2, fontfamily="sans-serif", zorder=5)

    # Optional Pill Badge in top right of card
    if badge_text:
        badge_w = len(badge_text) * 0.095 + 0.22
        bx = x + w - badge_w - 0.15
        by = y + h - 0.42
        badge = patches.FancyBboxPatch(
            (bx, by), badge_w, 0.24,
            boxstyle="round,pad=0.04,rounding_size=0.08",
            facecolor=badge_color, edgecolor="none", zorder=6
        )
        ax.add_patch(badge)
        ax.text(bx + badge_w / 2, by + 0.12, badge_text, color="#FFFFFF", fontsize=6.5, weight="bold",
                ha="center", va="center", fontfamily="sans-serif", zorder=7)

    # Bullet items
    start_y = y + h - (0.82 if subtitle else 0.65)
    line_spacing = 0.24
    for idx, item in enumerate(items):
        item_y = start_y - (idx * line_spacing)
        if item.startswith("!"): # Warning / Highlight item
            ax.text(x + 0.22, item_y, "• " + item[1:], color="#DC2626", fontsize=7.5, weight="bold", fontfamily="sans-serif", zorder=5)
        elif item.startswith("*"): # Primary Highlight item
            ax.text(x + 0.22, item_y, "• " + item[1:], color="#0D9488", fontsize=7.5, weight="bold", fontfamily="sans-serif", zorder=5)
        else:
            ax.text(x + 0.22, item_y, "• " + item, color="#334155", fontsize=7.5, fontfamily="sans-serif", zorder=5)

def draw_step_box(ax, x, y, w, h, step_num, title, tech, points, bg_color="#FFFFFF", border_color="#0D9488"):
    """Draw a numbered pipeline step card for the clinical intelligence flow."""
    # Drop shadow
    shadow = patches.FancyBboxPatch(
        (x + 0.06, y - 0.06), w, h,
        boxstyle="round,pad=0,rounding_size=0.14",
        facecolor="#E2E8F0", edgecolor="none", alpha=0.5, zorder=2
    )
    ax.add_patch(shadow)

    # Main Card
    box = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0,rounding_size=0.14",
        facecolor=bg_color, edgecolor=border_color,
        linewidth=1.6, zorder=3
    )
    ax.add_patch(box)

    # Step Badge Circle
    circle = patches.Circle((x + 0.36, y + h - 0.38), 0.22, facecolor=border_color, edgecolor="none", zorder=5)
    ax.add_patch(circle)
    ax.text(x + 0.36, y + h - 0.38, str(step_num), color="#FFFFFF", fontsize=8.5, weight="bold",
            ha="center", va="center", fontfamily="sans-serif", zorder=6)

    # Title & Tech
    ax.text(x + 0.70, y + h - 0.28, title, color="#0F2942", fontsize=9.2, weight="bold", fontfamily="sans-serif", zorder=5)
    ax.text(x + 0.70, y + h - 0.50, tech, color="#64748B", fontsize=7.2, weight="bold", fontfamily="sans-serif", zorder=5)

    # Bullet items
    start_y = y + h - 0.78
    for idx, pt in enumerate(points):
        pt_y = start_y - (idx * 0.24)
        if pt.startswith("!"):
            ax.text(x + 0.22, pt_y, "• " + pt[1:], color="#DC2626", fontsize=7.4, weight="bold", fontfamily="sans-serif", zorder=5)
        elif pt.startswith("*"):
            ax.text(x + 0.22, pt_y, "• " + pt[1:], color="#0D9488", fontsize=7.4, weight="bold", fontfamily="sans-serif", zorder=5)
        else:
            ax.text(x + 0.22, pt_y, "• " + pt, color="#334155", fontsize=7.4, fontfamily="sans-serif", zorder=5)

def draw_flow_arrow(ax, x1, y1, x2, y2, label="", color="#475569", lw=1.8):
    """Draw a clean directional flow arrow with a neat floating badge."""
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="->,head_width=0.35,head_length=0.45",
            color=color, lw=lw, shrinkA=3, shrinkB=3
        ),
        zorder=6
    )
    if label:
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        bbox_props = dict(boxstyle="round,pad=0.2", fc="#FFFFFF", ec=color, lw=0.9, alpha=0.95)
        ax.text(mx, my, label, color=color, fontsize=7.0, weight="bold",
                ha="center", va="center", bbox=bbox_props, zorder=7, fontfamily="sans-serif")

def generate_simplified_architecture(output_png="DocAssistIQ_System_Architecture_Diagram.png", output_svg="DocAssistIQ_System_Architecture_Diagram.svg"):
    # Clean 21 x 13.5 inches at 300 DPI
    fig, ax = plt.subplots(figsize=(21, 13.5), dpi=300)
    ax.set_xlim(0, 21)
    ax.set_ylim(0, 13.5)
    ax.axis("off")
    fig.patch.set_facecolor("#F8FAFC")

    # -----------------------------------------------------------------------
    # HEADER
    # -----------------------------------------------------------------------
    header = patches.FancyBboxPatch(
        (0.6, 12.35), 19.8, 0.85,
        boxstyle="round,pad=0,rounding_size=0.12",
        facecolor="#0F2942", edgecolor="#0D9488", linewidth=1.8, zorder=3
    )
    ax.add_patch(header)
    ax.text(0.9, 12.88, "DocAssistIQ — Simplified System Architecture Blueprint",
            color="#FFFFFF", fontsize=14.0, weight="bold", fontfamily="sans-serif")
    ax.text(0.9, 12.55, "Evidence-Grounded Neuro-Symbolic Modular Monolith • Real-Time ASR • Deterministic Reasoning • Local LLM",
            color="#38BDF8", fontsize=8.2, weight="bold", fontfamily="sans-serif")

    # Header Badges
    bx = 16.5
    for btext, bcol in [("FastAPI 0.110+", "#0284C7"), ("Next.js 14", "#0D9488"), ("v3.4 Release", "#475569")]:
        bw = len(btext) * 0.11 + 0.25
        bpatch = patches.FancyBboxPatch((bx, 12.62), bw, 0.30, boxstyle="round,pad=0.04,rounding_size=0.08", facecolor=bcol, zorder=5)
        ax.add_patch(bpatch)
        ax.text(bx + bw / 2, 12.77, btext, color="#FFFFFF", fontsize=7.2, weight="bold", ha="center", va="center", zorder=6)
        bx += bw + 0.18

    # -----------------------------------------------------------------------
    # TIER 1: CLIENT PRESENTATION TIER (TOP)
    # -----------------------------------------------------------------------
    tier1_bg = patches.FancyBboxPatch(
        (0.6, 10.0), 19.8, 2.15,
        boxstyle="round,pad=0,rounding_size=0.12",
        facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidth=1.5, zorder=2
    )
    ax.add_patch(tier1_bg)
    ax.text(0.9, 11.85, "TIER 1: CLINICIAN PRESENTATION LAYER", color="#0F2942", fontsize=10.0, weight="bold", fontfamily="sans-serif")
    ax.text(6.0, 11.85, "Next.js 14 App Router • React 19 • TypeScript • TailwindCSS • Web Audio API", color="#64748B", fontsize=8.0, fontfamily="sans-serif")

    draw_card(ax, 0.9, 10.2, 4.4, 1.45,
              "Ambient Voice Capture", "Web Audio API Client",
              ["16kHz 16-bit mono linear PCM", "250ms binary audio chunks", "!Mandatory Consent Interlock Gate"],
              bg_color="#F0F9FF", border_color="#38BDF8", header_color="#0369A1", badge_text="WSS Client", badge_color="#0284C7")

    draw_card(ax, 5.7, 10.2, 4.5, 1.45,
              "Consultation Room UI", "Real-Time Interaction",
              ["Doctor vs Patient Diarized Streams", "Live Waveform & VAD Feedback", "*Real-time transcript editing"],
              bg_color="#F0FDF4", border_color="#4ADE80", header_color="#15803D", badge_text="Live Stream", badge_color="#15803D")

    draw_card(ax, 10.6, 10.2, 4.6, 1.45,
              "Diagnostic Decision Cards", "Real-Time Decision Support",
              ["Ranked Top-5 differential diagnoses", "Transparent 'Why?' evidence breakdown", "!Master Red-Flag Emergency Banner"],
              bg_color="#FFFBEB", border_color="#F59E0B", header_color="#B45309", badge_text="Top-5 CDS", badge_color="#D97706")

    draw_card(ax, 15.6, 10.2, 4.5, 1.45,
              "SOAP Editor & Hub Portal", "Clinician Control & Knowledge",
              ["Structured S-O-A-P note drafting", "*Immutable SHA-256 Provenance Sign", "Doctor Knowledge Hub (`/hub`)"],
              bg_color="#FAF5FF", border_color="#A855F7", header_color="#7E22CE", badge_text="Audit Sealed", badge_color="#7E22CE")

    # -----------------------------------------------------------------------
    # TIER 2: API GATEWAY & REAL-TIME TRANSPORT
    # -----------------------------------------------------------------------
    tier2_bg = patches.FancyBboxPatch(
        (0.6, 8.55), 19.8, 1.15,
        boxstyle="round,pad=0,rounding_size=0.12",
        facecolor="#F1F5F9", edgecolor="#94A3B8", linewidth=1.4, zorder=2
    )
    ax.add_patch(tier2_bg)
    ax.text(0.9, 9.40, "TIER 2: API GATEWAY & REAL-TIME TRANSPORT (FastAPI ASGI / Uvicorn)", color="#0F2942", fontsize=9.5, weight="bold")

    draw_card(ax, 0.9, 8.7, 4.4, 0.65, "Auth & Tenant RBAC", None, ["JWT Bearer • Tenant Scoping • Request ID"],
              bg_color="#FFFFFF", border_color="#CBD5E1", header_color="#0F2942")

    draw_card(ax, 5.7, 8.7, 4.5, 0.65, "WebSocket Server (`ws.py`)", None, ["Binary PCM Ingestion & JSON Deltas"],
              bg_color="#FFFFFF", border_color="#CBD5E1", header_color="#0F2942")

    draw_card(ax, 10.6, 8.7, 4.6, 0.65, "Redis Pub/Sub Bus", None, ["Cross-worker event synchronization"],
              bg_color="#FFFFFF", border_color="#CBD5E1", header_color="#0F2942")

    draw_card(ax, 15.6, 8.7, 4.5, 0.65, "REST Router V1 (`router.py`)", None, ["27 domain endpoints: /consultations, /rag..."],
              bg_color="#FFFFFF", border_color="#CBD5E1", header_color="#0F2942")

    # Connectors Tier 1 -> Tier 2
    draw_flow_arrow(ax, 3.1, 10.2, 3.1, 9.35, label="WSS Audio", color="#0284C7")
    draw_flow_arrow(ax, 7.95, 9.35, 7.95, 10.2, label="JSON Deltas", color="#15803D")
    draw_flow_arrow(ax, 12.9, 9.35, 12.9, 10.2, label="Top-5 CDS", color="#D97706")
    draw_flow_arrow(ax, 17.85, 10.2, 17.85, 9.35, label="HTTPS REST", color="#7E22CE")

    # -----------------------------------------------------------------------
    # TIER 3: CORE MEDICAL INTELLIGENCE PIPELINE (5 SEQUENTIAL STEPS)
    # -----------------------------------------------------------------------
    tier3_bg = patches.FancyBboxPatch(
        (0.6, 4.45), 19.8, 3.8,
        boxstyle="round,pad=0,rounding_size=0.14",
        facecolor="#FFFFFF", edgecolor="#0D9488", linewidth=1.8, zorder=2
    )
    ax.add_patch(tier3_bg)
    ax.text(0.9, 7.95, "TIER 3: CORE MEDICAL INTELLIGENCE PIPELINE (Modular Monolith / 57 Python Services)",
            color="#0F2942", fontsize=10.5, weight="bold", fontfamily="sans-serif")
    ax.text(12.2, 7.95, "Sequential Execution • 90% Deterministic Reasoning • Zero Hallucination Core",
            color="#0D9488", fontsize=8.0, weight="bold", fontfamily="sans-serif")

    # Step 1: Speech to Text & Diarization
    draw_step_box(ax, 0.9, 4.7, 3.5, 3.0, 1,
                  "Speech & Diarization", "Faster-Whisper + PyAnnote",
                  ["Faster-Whisper (Large-v3)", "CTranslate2 GPU Acceleration", "Silero Voice Activity Detect",
                   "PyAnnote 3.1 Speaker Cluster", "*Doctor vs Patient labeling"],
                  bg_color="#F8FAFC", border_color="#0284C7")

    # Step 2: Clinical NLP & Negation
    draw_step_box(ax, 4.8, 4.7, 3.5, 3.0, 2,
                  "Clinical NLP & Norm", "NegEx + Medical Ontologies",
                  ["Symptoms, Vitals, Meds extraction", "!NegEx: Excludes negative findings",
                   "SNOMED CT clinical findings", "UMLS CUI semantic mapping", "*RxNorm drug identifiers"],
                  bg_color="#F8FAFC", border_color="#0D9488")

    # Step 3: Deterministic Reasoning Engine (GOD-LEVEL AI)
    draw_step_box(ax, 8.7, 4.7, 3.7, 3.0, 3,
                  "Deterministic Reasoning", "100+ Disease KB (Offline)",
                  ["*Multi-Factor Objective Math:", "  - Jaccard similarity (w1=0.30)", "  - Cardinal symptoms (w2=0.35)",
                   "  - Incubation timeline (w3=0.15)", "  - Travel outbreak fit (w4=0.10)",
                   "!Negation penalty deduction", "*Sub-second latency (< 85ms)"],
                  bg_color="#FFFBEB", border_color="#D97706")

    # Step 4: Deterministic Safety Engine
    draw_step_box(ax, 12.8, 4.7, 3.4, 3.0, 4,
                  "Safety Guardrails", "Master Red Flags & RxNav",
                  ["!RF-001 Severe Chest Pain", "!RF-002 Severe Dyspnea", "!RF-003 Acute Stroke Signs",
                   "!RF-004 Anaphylaxis", "*NIH RxNav Live DDI Checks", "!Mandatory Clinician Review"],
                  bg_color="#FEF2F2", border_color="#DC2626")

    # Step 5: Constrained Local LLM
    draw_step_box(ax, 16.6, 4.7, 3.5, 3.0, 5,
                  "Neural Explainer", "Llama-3.2-3B via Ollama",
                  ["Local GPU inference", "*Constrained to evidence matrix", "Drafts 'Why?' justifications",
                   "Generates structured SOAP", "!Forbidden to guess diagnoses"],
                  bg_color="#FAF5FF", border_color="#7E22CE")

    # Flow arrows between steps in Tier 3
    draw_flow_arrow(ax, 4.4, 6.2, 4.8, 6.2, color="#0284C7")
    draw_flow_arrow(ax, 8.3, 6.2, 8.7, 6.2, color="#0D9488")
    draw_flow_arrow(ax, 12.4, 6.2, 12.8, 6.2, color="#D97706")
    draw_flow_arrow(ax, 16.2, 6.2, 16.6, 6.2, color="#DC2626")

    # Gateway to Intelligence Pipeline Arrow
    draw_flow_arrow(ax, 7.95, 8.7, 2.65, 7.7, label="PCM Stream", color="#0284C7")
    draw_flow_arrow(ax, 18.35, 7.7, 18.35, 8.7, label="Verified Output", color="#7E22CE")

    # -----------------------------------------------------------------------
    # TIER 4: ASYNC WORKERS & RAG PIPELINE
    # -----------------------------------------------------------------------
    tier4_bg = patches.FancyBboxPatch(
        (0.6, 2.75), 19.8, 1.45,
        boxstyle="round,pad=0,rounding_size=0.12",
        facecolor="#EEF2FF", edgecolor="#6366F1", linewidth=1.4, zorder=2
    )
    ax.add_patch(tier4_bg)
    ax.text(0.9, 3.90, "TIER 4: ASYNCHRONOUS TASK WORKERS & HYBRID RAG (Celery 5.3 + Redis 7)", color="#312E81", fontsize=9.5, weight="bold")

    draw_card(ax, 0.9, 2.9, 4.4, 0.85, "Document OCR & Parser", "Tesseract / LayoutLM",
              ["Lab PDF & diagnostic report ingestion"], bg_color="#FFFFFF", border_color="#C7D2FE", header_color="#3730A3")

    draw_card(ax, 5.7, 2.9, 4.5, 0.85, "Batch Vector Embeddings", "Sentence-Transformers",
              ["384-dim all-MiniLM-L6-v2 pgvector indexing"], bg_color="#FFFFFF", border_color="#C7D2FE", header_color="#3730A3")

    draw_card(ax, 10.6, 2.9, 4.6, 0.85, "PubMed Evidence Scanner", "Medical Literature Harvester",
              ["Verified clinical guideline RRF sync"], bg_color="#FFFFFF", border_color="#C7D2FE", header_color="#3730A3")

    draw_card(ax, 15.6, 2.9, 4.5, 0.85, "Audit Chainer & Archival", "SHA-256 Provenance Engine",
              ["Tamper-resistant append-only ledger"], bg_color="#FFFFFF", border_color="#C7D2FE", header_color="#3730A3")

    # -----------------------------------------------------------------------
    # TIER 5: PERSISTENCE, STORAGE & INFRASTRUCTURE (DOCKER)
    # -----------------------------------------------------------------------
    tier5_bg = patches.FancyBboxPatch(
        (0.6, 0.45), 19.8, 2.05,
        boxstyle="round,pad=0,rounding_size=0.12",
        facecolor="#FFFFFF", edgecolor="#334155", linewidth=1.6, zorder=2
    )
    ax.add_patch(tier5_bg)
    ax.text(0.9, 2.15, "TIER 5: PERSISTENCE, STORAGE & LOCAL INFRASTRUCTURE (Docker Compose Environment)",
            color="#0F2942", fontsize=10.0, weight="bold", fontfamily="sans-serif")

    draw_card(ax, 0.9, 0.65, 4.4, 1.35,
              "PostgreSQL 16 + pgvector", "Primary Database",
              ["Relational: Users, Consultations, SOAP", "Vector: 384-dim HNSW indexed embeddings", "*Immutable SHA-256 Audit Trail table"],
              bg_color="#F8FAFC", border_color="#475569", header_color="#0F2942", badge_text="pgvector", badge_color="#334155")

    draw_card(ax, 5.7, 0.65, 4.5, 1.35,
              "Redis 7.2 Alpine", "In-Memory Cache & Broker",
              ["Port 6379 DB 0: Session cache & Pub/Sub", "Port 6379 DB 1: Celery Task Broker", "Port 6379 DB 2: Celery Result Backend"],
              bg_color="#F8FAFC", border_color="#DC2626", header_color="#991B1B", badge_text="Redis 7", badge_color="#DC2626")

    draw_card(ax, 10.6, 0.65, 4.6, 1.35,
              "MinIO S3 Object Storage", "Document & Audio Store",
              ["Ports 9010 (API) / 9011 (Console)", "Bucket: `docassistiq`", "Raw 16kHz PCM audio & lab PDF reports"],
              bg_color="#F8FAFC", border_color="#D97706", header_color="#B45309", badge_text="S3 Storage", badge_color="#D97706")

    draw_card(ax, 15.6, 0.65, 4.5, 1.35,
              "Ollama Local AI Runtime", "Zero Cloud Data Leakage",
              ["Model: Llama-3.2-3B Instruct", "Local GPU execution (`localhost:11434`)", "*100% HIPAA On-Premise Data Privacy"],
              bg_color="#F8FAFC", border_color="#7E22CE", header_color="#581C87", badge_text="Local AI", badge_color="#7E22CE")

    # Connectors Tier 3 to Tier 5
    draw_flow_arrow(ax, 3.1, 4.7, 3.1, 2.0, label="Asyncpg / pgvector", color="#334155")
    draw_flow_arrow(ax, 10.5, 4.7, 7.95, 2.0, label="Pub/Sub", color="#DC2626")
    draw_flow_arrow(ax, 14.5, 4.7, 12.9, 2.0, label="S3 Blobs", color="#D97706")
    draw_flow_arrow(ax, 18.35, 4.7, 17.85, 2.0, label="Local LLM API", color="#7E22CE")

    # Save
    plt.tight_layout()
    png_path = os.path.abspath(output_png)
    plt.savefig(png_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    print(f"Generated simplified architecture diagram (PNG): {png_path}")

    if output_svg:
        svg_path = os.path.abspath(output_svg)
        plt.savefig(svg_path, format="svg", facecolor=fig.get_facecolor(), edgecolor="none")
        print(f"Generated simplified architecture diagram (SVG): {svg_path}")

    plt.close()
    return png_path

if __name__ == "__main__":
    generate_simplified_architecture("DocAssistIQ_System_Architecture_Diagram.png", "DocAssistIQ_System_Architecture_Diagram.svg")
