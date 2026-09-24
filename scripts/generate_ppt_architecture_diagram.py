"""DocAssistIQ — PowerPoint (16:9 Widescreen) Architecture Diagram Generator.

Generates a compact, high-legibility, slide-ready architecture diagram specifically designed
to look clean, bold, and easily readable inside a PowerPoint (PPT) presentation slide.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_ppt_card(ax, x, y, w, h, title, tech, points, bg_color="#FFFFFF", border_color="#CBD5E1", 
                  title_color="#0F2942", badge=None, badge_color="#0D9488"):
    """Draw a slide-optimized card with high-contrast text and clean spacing."""
    # Shadow
    shadow = patches.FancyBboxPatch(
        (x + 0.04, y - 0.04), w, h,
        boxstyle="round,pad=0,rounding_size=0.10",
        facecolor="#E2E8F0", edgecolor="none", alpha=0.55, zorder=2
    )
    ax.add_patch(shadow)

    # Main Card Box
    card = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0,rounding_size=0.10",
        facecolor=bg_color, edgecolor=border_color,
        linewidth=1.5, zorder=3
    )
    ax.add_patch(card)

    # Title & Tech Tag
    ax.text(x + 0.16, y + h - 0.28, title, color=title_color, fontsize=10.0, weight="bold", fontfamily="sans-serif", zorder=5)
    if tech:
        ax.text(x + 0.16, y + h - 0.50, tech, color="#64748B", fontsize=7.8, weight="bold", fontfamily="sans-serif", zorder=5)

    # Pill Badge (top right)
    if badge:
        bw = len(badge) * 0.10 + 0.22
        bx = x + w - bw - 0.14
        by = y + h - 0.38
        bp = patches.FancyBboxPatch(
            (bx, by), bw, 0.24,
            boxstyle="round,pad=0.03,rounding_size=0.08",
            facecolor=badge_color, edgecolor="none", zorder=6
        )
        ax.add_patch(bp)
        ax.text(bx + bw / 2, by + 0.12, badge, color="#FFFFFF", fontsize=6.8, weight="bold",
                ha="center", va="center", fontfamily="sans-serif", zorder=7)

    # Bullets
    start_y = y + h - (0.78 if tech else 0.60)
    line_sp = 0.23
    for idx, pt in enumerate(points):
        py = start_y - (idx * line_sp)
        if pt.startswith("!"):
            ax.text(x + 0.16, py, "• " + pt[1:], color="#DC2626", fontsize=8.0, weight="bold", fontfamily="sans-serif", zorder=5)
        elif pt.startswith("*"):
            ax.text(x + 0.16, py, "• " + pt[1:], color="#0D9488", fontsize=8.0, weight="bold", fontfamily="sans-serif", zorder=5)
        else:
            ax.text(x + 0.16, py, "• " + pt, color="#1E293B", fontsize=8.0, fontfamily="sans-serif", zorder=5)

def draw_pipeline_step(ax, x, y, w, h, step_num, title, tech, points, border_color="#0D9488", bg_color="#FFFFFF"):
    """Draw a numbered pipeline step in the central intelligence flow."""
    # Shadow
    shadow = patches.FancyBboxPatch(
        (x + 0.04, y - 0.04), w, h,
        boxstyle="round,pad=0,rounding_size=0.10",
        facecolor="#E2E8F0", edgecolor="none", alpha=0.55, zorder=2
    )
    ax.add_patch(shadow)

    # Card
    card = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0,rounding_size=0.10",
        facecolor=bg_color, edgecolor=border_color,
        linewidth=1.6, zorder=3
    )
    ax.add_patch(card)

    # Step Circle
    circle = patches.Circle((x + 0.28, y + h - 0.32), 0.18, facecolor=border_color, edgecolor="none", zorder=5)
    ax.add_patch(circle)
    ax.text(x + 0.28, y + h - 0.32, str(step_num), color="#FFFFFF", fontsize=8.5, weight="bold",
            ha="center", va="center", fontfamily="sans-serif", zorder=6)

    # Title & Tech
    ax.text(x + 0.54, y + h - 0.24, title, color="#0F2942", fontsize=9.5, weight="bold", fontfamily="sans-serif", zorder=5)
    ax.text(x + 0.54, y + h - 0.44, tech, color="#64748B", fontsize=7.4, weight="bold", fontfamily="sans-serif", zorder=5)

    # Bullets
    start_y = y + h - 0.70
    for idx, pt in enumerate(points):
        py = start_y - (idx * 0.22)
        if pt.startswith("!"):
            ax.text(x + 0.16, py, "• " + pt[1:], color="#DC2626", fontsize=7.8, weight="bold", fontfamily="sans-serif", zorder=5)
        elif pt.startswith("*"):
            ax.text(x + 0.16, py, "• " + pt[1:], color="#0D9488", fontsize=7.8, weight="bold", fontfamily="sans-serif", zorder=5)
        else:
            ax.text(x + 0.16, py, "• " + pt, color="#1E293B", fontsize=7.8, fontfamily="sans-serif", zorder=5)

def draw_ppt_arrow(ax, x1, y1, x2, y2, label="", color="#475569", lw=1.8):
    """Draw a clean presentation arrow with an optional label badge."""
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="->,head_width=0.32,head_length=0.40",
            color=color, lw=lw, shrinkA=3, shrinkB=3
        ),
        zorder=6
    )
    if label:
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        bbox_props = dict(boxstyle="round,pad=0.18", fc="#FFFFFF", ec=color, lw=0.8, alpha=0.95)
        ax.text(mx, my, label, color=color, fontsize=6.8, weight="bold",
                ha="center", va="center", bbox=bbox_props, zorder=7, fontfamily="sans-serif")

def generate_ppt_diagram(output_png="DocAssistIQ_Architecture_PPT_Slide.png", output_svg="DocAssistIQ_Architecture_PPT_Slide.svg"):
    # Standard 16:9 Widescreen aspect ratio (16 x 9 inches at 300 DPI = 4800 x 2700 px)
    fig, ax = plt.subplots(figsize=(16, 9), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")
    fig.patch.set_facecolor("#F8FAFC")

    # -----------------------------------------------------------------------
    # SLIDE TITLE HEADER (Compact & High Contrast)
    # -----------------------------------------------------------------------
    header = patches.FancyBboxPatch(
        (0.5, 8.15), 15.0, 0.65,
        boxstyle="round,pad=0,rounding_size=0.10",
        facecolor="#0F2942", edgecolor="#0D9488", linewidth=1.6, zorder=3
    )
    ax.add_patch(header)
    ax.text(0.75, 8.54, "DocAssistIQ: End-to-End System Architecture",
            color="#FFFFFF", fontsize=13.0, weight="bold", fontfamily="sans-serif")
    ax.text(0.75, 8.28, "Neuro-Symbolic Modular Monolith • Real-Time ASR • Deterministic Reasoning • Zero Cloud Data Leakage",
            color="#38BDF8", fontsize=7.8, weight="bold", fontfamily="sans-serif")

    # Status Badges in Title
    ax.text(12.5, 8.48, "[ Next.js 14 + FastAPI + PostgreSQL ]", color="#E2E8F0", fontsize=7.5, weight="bold", fontfamily="sans-serif")
    ax.text(12.5, 8.28, "[ Offline-First CDS Engine v3.4 ]", color="#34D399", fontsize=7.5, weight="bold", fontfamily="sans-serif")

    # -----------------------------------------------------------------------
    # ROW 1: PRESENTATION & API GATEWAY (Top Section: y = 6.45 to 7.95)
    # -----------------------------------------------------------------------
    # Client presentation container
    p_box = patches.FancyBboxPatch(
        (0.5, 6.45), 7.8, 1.55,
        boxstyle="round,pad=0,rounding_size=0.10",
        facecolor="#FFFFFF", edgecolor="#0284C7", linewidth=1.4, zorder=2
    )
    ax.add_patch(p_box)
    ax.text(0.7, 7.78, "CLINICIAN WORKSPACE (Next.js 14 / React 19)", color="#0369A1", fontsize=8.8, weight="bold")

    draw_ppt_card(ax, 0.7, 6.55, 3.6, 1.05,
                  "Ambient Voice Capture", "Web Audio API",
                  ["16kHz 16-bit Mono Linear PCM", "250ms Audio Chunk Streaming", "!Mandatory Patient Consent Gate"],
                  bg_color="#F0F9FF", border_color="#38BDF8", title_color="#0369A1")

    draw_ppt_card(ax, 4.5, 6.55, 3.6, 1.05,
                  "Clinical Workspace UI", "Consultation Room",
                  ["Doctor vs Patient Diarized Transcript", "Ranked Top-5 Diagnostic Cards", "*Interactive SOAP Note + Hub"],
                  bg_color="#F0FDF4", border_color="#4ADE80", title_color="#15803D")

    # API Gateway container
    g_box = patches.FancyBboxPatch(
        (8.6, 6.45), 6.9, 1.55,
        boxstyle="round,pad=0,rounding_size=0.10",
        facecolor="#FFFFFF", edgecolor="#0F2942", linewidth=1.4, zorder=2
    )
    ax.add_patch(g_box)
    ax.text(8.8, 7.78, "API GATEWAY & REAL-TIME TRANSPORT (FastAPI ASGI)", color="#0F2942", fontsize=8.8, weight="bold")

    draw_ppt_card(ax, 8.8, 6.55, 3.2, 1.05,
                  "Auth & WebSocket Gateway", "FastAPI (`ws.py`)",
                  ["JWT Bearer + Multi-Tenant RBAC", "Binary Audio Chunk Aggregator", "*Request ID Correlation Tracing"],
                  bg_color="#F1F5F9", border_color="#94A3B8", title_color="#0F2942")

    draw_ppt_card(ax, 12.2, 6.55, 3.1, 1.05,
                  "Real-Time Event Broker", "Redis 7 Pub/Sub",
                  ["Channel-based stream coordination", "Multi-worker session broadcast", "*27 Thin REST API Endpoints"],
                  bg_color="#F1F5F9", border_color="#94A3B8", title_color="#0F2942")

    # Connectors Row 1
    draw_ppt_arrow(ax, 8.3, 7.15, 8.6, 7.15, label="WSS Audio", color="#0284C7")
    draw_ppt_arrow(ax, 8.6, 6.85, 8.3, 6.85, label="JSON Output", color="#15803D")

    # -----------------------------------------------------------------------
    # ROW 2: CORE MEDICAL INTELLIGENCE PIPELINE (Middle Section: y = 3.2 to 6.25)
    # -----------------------------------------------------------------------
    pipe_box = patches.FancyBboxPatch(
        (0.5, 3.2), 15.0, 3.05,
        boxstyle="round,pad=0,rounding_size=0.12",
        facecolor="#FFFFFF", edgecolor="#0D9488", linewidth=1.8, zorder=2
    )
    ax.add_patch(pipe_box)
    ax.text(0.7, 6.02, "CORE MEDICAL INTELLIGENCE PIPELINE (5-Stage Sequential Flow • 90% Deterministic Core)",
            color="#0F2942", fontsize=9.5, weight="bold")
    ax.text(10.5, 6.02, "[ Executes 100% Offline • Zero Hallucinations ]", color="#0D9488", fontsize=7.8, weight="bold")

    # Step 1: Speech & Diarization
    draw_pipeline_step(ax, 0.7, 3.35, 2.7, 2.45, 1,
                       "Speech to Text", "Faster-Whisper + PyAnnote",
                       ["Faster-Whisper (Large-v3)", "CTranslate2 GPU Inference", "Silero Voice Activity Detect",
                        "PyAnnote 3.1 Diarization", "*Doctor vs Patient Split"],
                       border_color="#0284C7", bg_color="#F8FAFC")

    # Step 2: Clinical NLP & NegEx
    draw_pipeline_step(ax, 3.65, 3.35, 2.7, 2.45, 2,
                       "Clinical NLP & Norm", "NegEx + Ontologies",
                       ["Entity Extraction (Vitals/Meds)", "!NegEx Negation Filtering",
                        "SNOMED CT Clinical Findings", "UMLS CUI Semantic Grounding", "*RxNorm Drug Identifiers"],
                       border_color="#0D9488", bg_color="#F8FAFC")

    # Step 3: Deterministic Clinical Reasoning Core
    draw_pipeline_step(ax, 6.6, 3.35, 2.8, 2.45, 3,
                       "Reasoning Engine", "100+ Disease KB (Offline)",
                       ["*Multi-Factor Objective Math:", "  - Jaccard symptom match (w=0.30)",
                        "  - Cardinal findings (w=0.35)", "  - Incubation fit (w=0.15)",
                        "  - Travel outbreak fit (w=0.10)", "!Deterministic Latency < 85ms"],
                       border_color="#D97706", bg_color="#FFFBEB")

    # Step 4: Deterministic Safety Engine
    draw_pipeline_step(ax, 9.65, 3.35, 2.65, 2.45, 4,
                       "Safety Engine", "Master Red Flags + DDI",
                       ["!RF-001 Severe Chest Pain", "!RF-002 Severe Dyspnea", "!RF-003 Acute Stroke Signs",
                        "!RF-004 Anaphylaxis", "*NIH RxNav Live DDI Checks", "!Mandatory Clinician Review"],
                       border_color="#DC2626", bg_color="#FEF2F2")

    # Step 5: Constrained Local LLM
    draw_pipeline_step(ax, 12.55, 3.35, 2.75, 2.45, 5,
                       "Local LLM Explainer", "Llama-3.2-3B via Ollama",
                       ["Runs Locally on GPU Workstation", "*Strictly Constrained to Evidence",
                        "Generates 'Why?' Justification", "Drafts Structured SOAP Notes", "!Zero Ungrounded Diagnoses"],
                       border_color="#7E22CE", bg_color="#FAF5FF")

    # Arrows between 5 steps
    draw_ppt_arrow(ax, 3.40, 4.58, 3.65, 4.58, color="#0284C7")
    draw_ppt_arrow(ax, 6.35, 4.58, 6.60, 4.58, color="#0D9488")
    draw_ppt_arrow(ax, 9.40, 4.58, 9.65, 4.58, color="#D97706")
    draw_ppt_arrow(ax, 12.30, 4.58, 12.55, 4.58, color="#DC2626")

    # Connector from Gateway to Step 1 & Step 5 to Gateway
    draw_ppt_arrow(ax, 10.2, 6.45, 2.05, 5.80, label="PCM Audio", color="#0284C7")
    draw_ppt_arrow(ax, 13.9, 5.80, 13.9, 6.45, label="Verified SOAP", color="#7E22CE")

    # -----------------------------------------------------------------------
    # ROW 3: PERSISTENCE, STORAGE & WORKERS (Bottom Section: y = 0.5 to 2.95)
    # -----------------------------------------------------------------------
    stor_box = patches.FancyBboxPatch(
        (0.5, 0.5), 15.0, 2.45,
        boxstyle="round,pad=0,rounding_size=0.10",
        facecolor="#FFFFFF", edgecolor="#334155", linewidth=1.5, zorder=2
    )
    ax.add_patch(stor_box)
    ax.text(0.7, 2.70, "DATA PERSISTENCE, ASYNC WORKERS & INFRASTRUCTURE (Docker Compose Environment)",
            color="#0F2942", fontsize=8.8, weight="bold")

    draw_ppt_card(ax, 0.7, 0.65, 3.3, 1.85,
                  "PostgreSQL 16 + pgvector", "Relational & Vector DB",
                  ["Users, Doctors, Patients, Consults", "Clinical Representations (JSONB)", "384-dim HNSW Vector Embeddings",
                   "*SHA-256 Chained Immutable Audit Log", "Multi-Tenant Hospital Isolation"],
                  bg_color="#F8FAFC", border_color="#475569", title_color="#0F2942", badge="pgvector", badge_color="#334155")

    draw_ppt_card(ax, 4.2, 0.65, 2.5, 1.85,
                  "Redis 7.2 Alpine", "Cache & Celery Broker",
                  ["Port 6379 DB 0: Session cache", "Port 6379 DB 1: Celery Broker", "Port 6379 DB 2: Result Backend",
                   "*High-throughput In-Memory Bus"],
                  bg_color="#F8FAFC", border_color="#DC2626", title_color="#991B1B", badge="Redis 7", badge_color="#DC2626")

    draw_ppt_card(ax, 6.9, 0.65, 2.6, 1.85,
                  "MinIO S3 Storage", "Object Storage",
                  ["Bucket: `docassistiq`", "Raw 16kHz PCM Audio Recordings", "Diagnostic PDF Reports & OCR",
                   "*S3-Compatible Object Store"],
                  bg_color="#F8FAFC", border_color="#D97706", title_color="#B45309", badge="S3", badge_color="#D97706")

    draw_ppt_card(ax, 9.7, 0.65, 2.7, 1.85,
                  "Celery 5.3 Workers", "Async Task Engine",
                  ["Lab Report Document OCR", "Batch Vector Embeddings Tasks", "PubMed Literature Harvester",
                   "*Decoupled Heavy Workloads"],
                  bg_color="#F8FAFC", border_color="#6366F1", title_color="#3730A3", badge="Celery", badge_color="#6366F1")

    draw_ppt_card(ax, 12.6, 0.65, 2.7, 1.85,
                  "Ollama AI Runtime", "Local GPU Engine",
                  ["Model: Llama-3.2-3B Instruct", "Local Host: `localhost:11434`", "*Zero Cloud Data Transmission",
                   "!100% HIPAA Patient Data Privacy"],
                  bg_color="#F8FAFC", border_color="#7E22CE", title_color="#581C87", badge="Local AI", badge_color="#7E22CE")

    # Connectors to Bottom Row
    draw_ppt_arrow(ax, 2.35, 3.2, 2.35, 2.5, color="#334155")
    draw_ppt_arrow(ax, 5.45, 3.2, 5.45, 2.5, color="#DC2626")
    draw_ppt_arrow(ax, 8.20, 3.2, 8.20, 2.5, color="#D97706")
    draw_ppt_arrow(ax, 11.05, 3.2, 11.05, 2.5, color="#6366F1")
    draw_ppt_arrow(ax, 13.95, 3.2, 13.95, 2.5, color="#7E22CE")

    # Save PNG and SVG
    plt.tight_layout()
    png_path = os.path.abspath(output_png)
    plt.savefig(png_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    print(f"Generated PowerPoint 16:9 architecture slide (PNG): {png_path}")

    if output_svg:
        svg_path = os.path.abspath(output_svg)
        plt.savefig(svg_path, format="svg", facecolor=fig.get_facecolor(), edgecolor="none")
        print(f"Generated PowerPoint 16:9 architecture slide (SVG): {svg_path}")

    plt.close()
    return png_path

if __name__ == "__main__":
    generate_ppt_diagram("DocAssistIQ_Architecture_PPT_Slide.png", "DocAssistIQ_Architecture_PPT_Slide.svg")
