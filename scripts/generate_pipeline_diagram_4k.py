"""
Generates a 4K UHD (3840x2160) diagram of the DocAssistIQ Clinical Decision & Data Lifecycle.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_pipeline_chart():
    fig = plt.figure(figsize=(16, 9), dpi=240)
    fig.patch.set_facecolor('#0A192F') # Dark Navy background

    # Title & Subtitle
    fig.text(0.06, 0.92, "DocAssistIQ — End-to-End Clinical Intelligence Lifecycle", 
             fontsize=26, fontweight='bold', color='#FFFFFF', family='sans-serif')
    fig.text(0.06, 0.88, "Deterministic Multi-Stage Decision Pipeline from Point-of-Care Ingestion to Tamper-Evident Certification", 
             fontsize=14, color='#38BDF8', family='sans-serif')

    ax = fig.add_axes([0.05, 0.08, 0.90, 0.76])
    ax.set_facecolor('#0A192F')
    ax.axis('off')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    # 4 Main Horizontal Processing Bands / Phases
    phases = [
        ("STAGE 1: AMBIENT INGESTION & PARSING", 80, [
            ("Web Audio Stream\n(16kHz PCM Mono)", "Microphone Capture", "#0284C7"),
            ("Faster-Whisper + PyAnnote\n(Diarized Transcripts)", "Speech-to-Text", "#0284C7"),
            ("ClinicalNoteParser\n(Shorthand + Negation)", "Deterministic NLP", "#0D9488"),
            ("Vital Signs & Labs\n(Panic Value Detection)", "Safety Checks", "#0D9488")
        ]),
        ("STAGE 2: DETERMINISTIC REASONING (<30ms)", 55, [
            ("Emergency Red-Flag\nRegistry (<1ms)", "Critical Triage", "#E11D48"),
            ("Multi-Factor Scoring\n(Jaccard + Cardinal 3x)", "Bayesian Engine", "#8B5CF6"),
            ("India Outbreak Radar\n(28 States & 8 UTs)", "Geo Surveillance", "#F59E0B"),
            ("Discriminative Testing\n(KL-Tiebreakers)", "Lab Optimization", "#8B5CF6")
        ]),
        ("STAGE 3: KNOWLEDGE FUSION & LOCAL LLM", 30, [
            ("Open-Domain Engine\n(1,500+ Conditions)", "Rare Disease KB", "#10B981"),
            ("Live Fallback Pipeline\n(NLM & OpenFDA APIs)", "Zero-Hallucination", "#10B981"),
            ("Local Ollama Runtime\n(ii-medical:8b / temp 0.1)", "Clinical Narrator", "#6366F1"),
            ("Circuit Breaker Gate\n(10 fail / 30s fallback)", "Fault Tolerance", "#6366F1")
        ]),
        ("STAGE 4: PATIENT SAFETY & AUDITABLE DELIVERY", 5, [
            ("Polypharmacy Citadel\n(FDA Black Box DDIs)", "Lethal DDI Defense", "#E11D48"),
            ("Legal Watermark\n('Clinician Review Req')", "Regulatory Stamp", "#F59E0B"),
            ("SHA-256 Provenance\n(Canonical JSON Hash)", "Tamper-Evident", "#0D9488"),
            ("Public Portal & Export\n(PDF / DOCX / Next.js)", "Certified Sealing", "#0284C7")
        ])
    ]

    for p_title, y_base, steps in phases:
        # Phase Background Ribbon
        ax.add_patch(patches.Rectangle((0, y_base - 2), 100, 20, facecolor='#0F2942', edgecolor='#1E3A5F', linewidth=1.5, alpha=0.9))
        ax.text(2, y_base + 15, p_title, fontsize=12, fontweight='bold', color='#38BDF8', family='sans-serif')

        # 4 Step Boxes within this Phase
        box_w = 21.5
        box_gap = 3.0
        start_x = 2.0

        for idx, (step_title, sub, col) in enumerate(steps):
            bx = start_x + idx * (box_w + box_gap)
            by = y_base

            # Card
            ax.add_patch(patches.Rectangle((bx, by), box_w, 13, facecolor='#0A192F', edgecolor=col, linewidth=2.0))
            # Colored top indicator bar
            ax.add_patch(patches.Rectangle((bx, by + 11.5), box_w, 1.5, facecolor=col, edgecolor='none'))

            # Texts
            ax.text(bx + 1.0, by + 9.5, sub.upper(), fontsize=8, fontweight='bold', color=col, family='sans-serif')
            ax.text(bx + box_w/2., by + 5.0, step_title, fontsize=10, fontweight='bold', color='#FFFFFF', 
                    ha='center', va='center', family='sans-serif', multialignment='center')

            # Arrow between boxes
            if idx < 3:
                ax.annotate('', xy=(bx + box_w + box_gap - 0.5, by + 6.5), xytext=(bx + box_w + 0.5, by + 6.5),
                            arrowprops=dict(arrowstyle="-|>", color='#64748B', lw=1.5, mutation_scale=12))

    output_path = "clinical_pipeline_diagram_4k.png"
    plt.savefig(output_path, dpi=240, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close()
    print(f"SUCCESS: Generated 4K Pipeline Diagram at {output_path}")

if __name__ == "__main__":
    generate_pipeline_chart()
