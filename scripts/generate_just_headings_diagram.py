"""DocAssistIQ — Minimalist 'Just Headings' Architecture Diagram Generator.

Creates a clean, bold, executive-level architecture diagram featuring ONLY high-level
headings, key technology names, and clean directional flows. Zero clutter, zero bullet points.
Perfect for clear PowerPoint presentations.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_heading_card(ax, x, y, w, h, title, subtitle, accent_color, bg_color="#FFFFFF", border_color="#CBD5E1"):
    """Draw a minimalist modern card with a bold heading, single subtitle, and colored top accent bar."""
    # Subtle modern drop shadow
    shadow = patches.FancyBboxPatch(
        (x + 0.05, y - 0.05), w, h,
        boxstyle="round,pad=0,rounding_size=0.14",
        facecolor="#E2E8F0", edgecolor="none", alpha=0.6, zorder=2
    )
    ax.add_patch(shadow)

    # Main Card Body
    card = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0,rounding_size=0.14",
        facecolor=bg_color, edgecolor=border_color,
        linewidth=1.6, zorder=3
    )
    ax.add_patch(card)

    # Colored Top Accent Bar
    bar_h = 0.14
    accent_bar = patches.FancyBboxPatch(
        (x, y + h - bar_h), w, bar_h,
        boxstyle="round,pad=0,rounding_size=0.06",
        facecolor=accent_color, edgecolor="none", zorder=4
    )
    ax.add_patch(accent_bar)

    # Big Bold Heading
    ax.text(
        x + w / 2, y + (h / 2) + 0.16, title,
        color="#0F2942", fontsize=11.5, weight="bold",
        ha="center", va="center", fontfamily="sans-serif", zorder=5
    )

    # Clean Crisp Subtitle
    if subtitle:
        ax.text(
            x + w / 2, y + (h / 2) - 0.22, subtitle,
            color="#475569", fontsize=8.5, weight="bold",
            ha="center", va="center", fontfamily="sans-serif", zorder=5
        )

def draw_clean_arrow(ax, x1, y1, x2, y2, label="", color="#334155", lw=2.0):
    """Draw a bold clean arrow with an uncluttered label."""
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="->,head_width=0.38,head_length=0.48",
            color=color, lw=lw, shrinkA=3, shrinkB=3
        ),
        zorder=6
    )
    if label:
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        bbox_props = dict(boxstyle="round,pad=0.22", fc="#FFFFFF", ec=color, lw=1.0, alpha=0.98)
        ax.text(mx, my, label, color=color, fontsize=7.8, weight="bold",
                ha="center", va="center", bbox=bbox_props, zorder=7, fontfamily="sans-serif")

def generate_just_headings_diagram(output_png="DocAssistIQ_Architecture_PPT_Slide.png", 
                                    output_svg="DocAssistIQ_Architecture_PPT_Slide.svg"):
    # Standard 16:9 Widescreen aspect ratio (16 x 9 inches at 300 DPI)
    fig, ax = plt.subplots(figsize=(16, 9), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")
    fig.patch.set_facecolor("#F8FAFC")

    # -----------------------------------------------------------------------
    # SLIDE TITLE HEADER
    # -----------------------------------------------------------------------
    header = patches.FancyBboxPatch(
        (0.6, 8.15), 14.8, 0.65,
        boxstyle="round,pad=0,rounding_size=0.10",
        facecolor="#0F2942", edgecolor="#0D9488", linewidth=1.8, zorder=3
    )
    ax.add_patch(header)
    ax.text(0.9, 8.54, "DocAssistIQ — High-Level System Architecture",
            color="#FFFFFF", fontsize=14.0, weight="bold", fontfamily="sans-serif")
    ax.text(0.9, 8.28, "Neuro-Symbolic Architecture • Real-Time Speech • Deterministic Medical Reasoning • Local AI",
            color="#38BDF8", fontsize=8.2, weight="bold", fontfamily="sans-serif")

    # Clean Tech Pills in Header
    ax.text(14.8, 8.48, "Next.js 14 • FastAPI", color="#E2E8F0", fontsize=8.0, weight="bold", ha="right", fontfamily="sans-serif")
    ax.text(14.8, 8.28, "PostgreSQL 16 • Docker", color="#34D399", fontsize=8.0, weight="bold", ha="right", fontfamily="sans-serif")

    # -----------------------------------------------------------------------
    # TIER 1: FRONTEND & API GATEWAY (Top Row)
    # -----------------------------------------------------------------------
    # Section Label
    ax.text(0.7, 7.82, "1. USER INTERACTION & REAL-TIME API GATEWAY", color="#0F2942", fontsize=9.2, weight="bold")

    # Card 1: Web Client
    draw_heading_card(ax, 0.7, 6.45, 6.7, 1.25,
                      "Clinician Workspace (Frontend)",
                      "Next.js 14 • React 19 • Web Audio API • TailwindCSS",
                      accent_color="#0284C7", border_color="#38BDF8")

    # Card 2: API Gateway
    draw_heading_card(ax, 8.6, 6.45, 6.7, 1.25,
                      "API Gateway & WebSocket Server",
                      "FastAPI ASGI • Redis Pub/Sub • JWT & Multi-Tenancy",
                      accent_color="#0F2942", border_color="#64748B")

    # Connector between Client and Gateway
    draw_clean_arrow(ax, 7.45, 7.08, 8.55, 7.08, label="WSS Audio / REST", color="#0284C7")

    # -----------------------------------------------------------------------
    # TIER 2: CORE MEDICAL INTELLIGENCE PIPELINE (Middle Flow: 5 Steps)
    # -----------------------------------------------------------------------
    # Background Container for Pipeline
    pipe_bg = patches.FancyBboxPatch(
        (0.6, 3.4), 14.8, 2.65,
        boxstyle="round,pad=0,rounding_size=0.12",
        facecolor="#FFFFFF", edgecolor="#0D9488", linewidth=1.8, zorder=2
    )
    ax.add_patch(pipe_bg)
    ax.text(0.9, 5.75, "2. CORE MEDICAL INTELLIGENCE PIPELINE (Modular Monolith Services)",
            color="#0F2942", fontsize=9.5, weight="bold")
    ax.text(14.8, 5.75, "[ 90% Deterministic Inference • Zero Hallucination Core ]",
            color="#0D9488", fontsize=8.0, weight="bold", ha="right")

    # 5 Big Clean Heading Cards
    step_w = 2.6
    step_h = 1.85
    step_y = 3.65

    # Step 1: Speech to Text
    draw_heading_card(ax, 0.9, step_y, step_w, step_h,
                      "Speech-to-Text\n& Diarization",
                      "Faster-Whisper (Large-v3)\n+ PyAnnote Audio 3.1",
                      accent_color="#0284C7", border_color="#38BDF8")

    # Step 2: Clinical NLP
    draw_heading_card(ax, 3.85, step_y, step_w, step_h,
                      "Clinical NLP &\nConcept Normalizer",
                      "NegEx Negation Parser\nUMLS • SNOMED • RxNorm",
                      accent_color="#0D9488", border_color="#2DD4BF")

    # Step 3: Deterministic Reasoning Engine
    draw_heading_card(ax, 6.8, step_y, step_w, step_h,
                      "Deterministic\nReasoning Engine",
                      "100+ Disease KB (Offline)\nMulti-Factor Scoring Math",
                      accent_color="#D97706", border_color="#F59E0B")

    # Step 4: Safety Engine
    draw_heading_card(ax, 9.75, step_y, step_w, step_h,
                      "Deterministic\nSafety Engine",
                      "Master Red Flags (RF-001–005)\nNIH RxNav DDI Screening",
                      accent_color="#DC2626", border_color="#F87171")

    # Step 5: Local LLM
    draw_heading_card(ax, 12.65, step_y, step_w, step_h,
                      "Constrained\nLocal LLM",
                      "Llama-3.2-3B via Ollama\n'Why?' Explanations & SOAP",
                      accent_color="#7C3AED", border_color="#C084FC")

    # Flow arrows between 5 steps
    draw_clean_arrow(ax, 3.52, 4.58, 3.82, 4.58, color="#0284C7")
    draw_clean_arrow(ax, 6.47, 4.58, 6.77, 4.58, color="#0D9488")
    draw_clean_arrow(ax, 9.42, 4.58, 9.72, 4.58, color="#D97706")
    draw_clean_arrow(ax, 12.37, 4.58, 12.62, 4.58, color="#DC2626")

    # Top to Pipeline Arrow & Pipeline to Top Arrow
    draw_clean_arrow(ax, 11.95, 6.45, 2.2, 5.55, label="PCM Audio Stream", color="#0284C7")
    draw_clean_arrow(ax, 13.95, 5.55, 11.95, 6.45, label="Verified Decisions", color="#7C3AED")

    # -----------------------------------------------------------------------
    # TIER 3: PERSISTENCE, STORAGE & WORKERS (Bottom Row)
    # -----------------------------------------------------------------------
    ax.text(0.7, 2.95, "3. DATA PERSISTENCE, ASYNC WORKERS & INFRASTRUCTURE (Docker Environment)",
            color="#0F2942", fontsize=9.2, weight="bold")

    bot_w = 3.3
    bot_h = 1.35
    bot_y = 1.25

    # Storage 1: PostgreSQL + pgvector
    draw_heading_card(ax, 0.7, bot_y, bot_w, bot_h,
                      "PostgreSQL 16 + pgvector",
                      "Relational DB • 384-dim Embeddings\nSHA-256 Chained Audit Trail",
                      accent_color="#334155", border_color="#64748B")

    # Storage 2: Redis 7
    draw_heading_card(ax, 4.4, bot_y, bot_w, bot_h,
                      "Redis 7.2 Cache & Bus",
                      "In-Memory Session Cache\nCelery Task Broker & Pub/Sub",
                      accent_color="#DC2626", border_color="#F87171")

    # Storage 3: MinIO S3
    draw_heading_card(ax, 8.1, bot_y, bot_w, bot_h,
                      "MinIO S3 Storage",
                      "Bucket: 'docassistiq'\nRaw PCM Audio & Clinical PDFs",
                      accent_color="#D97706", border_color="#F59E0B")

    # Storage 4: Celery + Ollama
    draw_heading_card(ax, 11.8, bot_y, bot_w, bot_h,
                      "Celery & Local Ollama",
                      "Async OCR & RAG Indexing Tasks\nLlama-3.2 GPU Local AI Runtime",
                      accent_color="#7C3AED", border_color="#C084FC")

    # Connectors between Pipeline and Infrastructure
    draw_clean_arrow(ax, 2.35, 3.65, 2.35, 2.65, color="#334155")
    draw_clean_arrow(ax, 6.05, 3.65, 6.05, 2.65, color="#DC2626")
    draw_clean_arrow(ax, 9.75, 3.65, 9.75, 2.65, color="#D97706")
    draw_clean_arrow(ax, 13.45, 3.65, 13.45, 2.65, color="#7C3AED")

    # -----------------------------------------------------------------------
    # SAVE PNG AND SVG
    # -----------------------------------------------------------------------
    plt.tight_layout()
    png_path = os.path.abspath(output_png)
    plt.savefig(png_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    print(f"Generated clean 'Just Headings' architecture diagram (PNG): {png_path}")

    if output_svg:
        svg_path = os.path.abspath(output_svg)
        plt.savefig(svg_path, format="svg", facecolor=fig.get_facecolor(), edgecolor="none")
        print(f"Generated clean 'Just Headings' architecture diagram (SVG): {svg_path}")

    plt.close()
    return png_path

if __name__ == "__main__":
    generate_just_headings_diagram("DocAssistIQ_Architecture_PPT_Slide.png", "DocAssistIQ_Architecture_PPT_Slide.svg")
