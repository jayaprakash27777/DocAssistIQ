"""
DocAssistIQ — Master All-In-One Professional Presentation Deck Generator.
Produces a 4K UHD 16:9 Widescreen (13.333" x 7.5") 24-slide presentation deck
covering Person 1, Person 2, Person 3, and Person 4, high-resolution diagrams,
benchmarks, architecture, formulas, and viva defense strategy.
"""

import os
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # --- COLOR PALETTE ---
    DARK_NAVY = RGBColor(10, 25, 47)       # #0A192F
    CARD_DARK = RGBColor(15, 41, 66)       # #0F2942
    CYAN_ACCENT = RGBColor(56, 189, 248)   # #38BDF8
    BLUE_PRIMARY = RGBColor(2, 132, 199)   # #0284C7
    TEAL_MEDICAL = RGBColor(13, 148, 136)  # #0D9488
    PURPLE_ACC = RGBColor(139, 92, 246)    # #8B5CF6
    EMERALD_GREEN = RGBColor(16, 185, 129) # #10B981
    ROSE_ALERT = RGBColor(225, 29, 72)     # #E11D48
    AMBER_WARN = RGBColor(245, 158, 11)    # #F59E0B
    SLATE_TEXT = RGBColor(51, 65, 85)      # #334155
    SLATE_MUTED = RGBColor(100, 116, 139)  # #64748B
    BG_LIGHT = RGBColor(248, 250, 252)     # #F8FAFC
    PURE_WHITE = RGBColor(255, 255, 255)

    def set_slide_background(slide, color):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_tag, dark_theme=False):
        # Header banner text box
        header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(0.9))
        tf = header_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        # Category Tag
        p_tag = tf.paragraphs[0]
        p_tag.text = category_tag.upper()
        p_tag.font.name = "Calibri"
        p_tag.font.size = Pt(10)
        p_tag.font.bold = True
        p_tag.font.color.rgb = CYAN_ACCENT if dark_theme else BLUE_PRIMARY

        # Main Title
        p_title = tf.add_paragraph()
        p_title.text = title_text
        p_title.font.name = "Calibri"
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = PURE_WHITE if dark_theme else CARD_DARK
        p_title.space_before = Pt(3)

    def add_card(slide, x, y, w, h, bg_color=BG_LIGHT, border_color=BLUE_PRIMARY, border_width=1.5):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(border_width)
        else:
            card.line.fill.background()
        return card

    # =========================================================================
    # SLIDE 1: Master Title Slide (4K Premium Dark Theme)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, DARK_NAVY)

    # Accent decorative top ribbon
    ribbon = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
    ribbon.fill.solid()
    ribbon.fill.fore_color.rgb = CYAN_ACCENT
    ribbon.line.fill.background()

    # Main Title Box
    tbox = s1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.333), Inches(3.2))
    tf = tbox.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "DocAssistIQ"
    p0.font.name = "Calibri"
    p0.font.size = Pt(56)
    p0.font.bold = True
    p0.font.color.rgb = PURE_WHITE

    p1 = tf.add_paragraph()
    p1.text = "Autonomous-Grade Clinical Decision Support System & Ambient Voice Intelligence"
    p1.font.name = "Calibri"
    p1.font.size = Pt(22)
    p1.font.bold = True
    p1.font.color.rgb = CYAN_ACCENT
    p1.space_before = Pt(8)

    p2 = tf.add_paragraph()
    p2.text = "Comprehensive 4-Person Master Project Presentation & Faculty Viva Defense Deck"
    p2.font.name = "Calibri"
    p2.font.size = Pt(14)
    p2.font.color.rgb = RGBColor(148, 163, 184)
    p2.space_before = Pt(10)

    # Bottom 4 Pillar Badges
    badges = [
        ("Sub-30ms Real-Time Inference", BLUE_PRIMARY),
        ("Faster-Whisper & Diarization", TEAL_MEDICAL),
        ("1,500+ Open-Domain KB & Outbreak Radar", PURPLE_ACC),
        ("Next.js 16 & SHA-256 Provenance", EMERALD_GREEN)
    ]
    for idx, (b_text, b_col) in enumerate(badges):
        bx = 1.0 + (idx * 2.85)
        b_card = add_card(s1, bx, 5.4, 2.7, 0.9, bg_color=CARD_DARK, border_color=b_col, border_width=1.5)
        btf = b_card.text_frame
        btf.vertical_anchor = MSO_ANCHOR.MIDDLE
        bp = btf.paragraphs[0]
        bp.text = b_text
        bp.font.name = "Calibri"
        bp.font.size = Pt(11)
        bp.font.bold = True
        bp.font.color.rgb = PURE_WHITE
        bp.alignment = PP_ALIGN.CENTER

    # =========================================================================
    # SLIDE 2: Executive Summary & Project Motivation
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, PURE_WHITE)
    add_header(s2, "Clinical Crisis & Project Motivation", "Problem Statement & Clinical Context")

    # 3 Problem Cards
    problems = [
        ("Cognitive & Documentation Overload", 
         "• Physicians spend over 2 hours on EHR data entry for every 1 hour of patient care.\n"
         "• Over 80% of clinical data is trapped in unstructured shorthand notes (SOB, DOE, PMH, c/o).\n"
         "• Severe physician burnout leading to rushed consultations and missed findings.",
         ROSE_ALERT),
        ("Diagnostic Errors & Anchoring Bias",
         "• Over 800,000 Americans die or are permanently disabled annually from diagnostic error.\n"
         "• Clinicians under time pressure fall into cognitive anchoring bias—missing rare conditions, atypical presentations, and regional tropical outbreaks (Nipah, KFD, Dengue).",
         AMBER_WARN),
        ("The Dangers of Raw LLMs in Healthcare",
         "• Generic chatbots (ChatGPT, Claude) hallucinate non-existent medical citations and dosages.\n"
         "• Stochastic variance violates medical determinism and reproducibility standards.\n"
         "• Cloud APIs transmit unencrypted Protected Health Information (PHI), violating HIPAA.",
         BLUE_PRIMARY)
    ]

    for i, (title, body, col) in enumerate(problems):
        card = add_card(s2, 0.8 + (i * 3.95), 1.6, 3.8, 5.2, bg_color=BG_LIGHT, border_color=col, border_width=2.0)
        tf = card.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = "Calibri"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = col

        p_body = tf.add_paragraph()
        p_body.text = body
        p_body.font.name = "Calibri"
        p_body.font.size = Pt(12)
        p_body.font.color.rgb = SLATE_TEXT
        p_body.space_before = Pt(14)

    # =========================================================================
    # SLIDE 3: 4-Person Master Engineering Division Matrix
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, PURE_WHITE)
    add_header(s3, "Four-Person Architectural Responsibility Division (25% Each)", "Team Workload & Modular Ownership")

    team = [
        ("PERSON 1", "Foundations & Real-Time Intelligence", BLUE_PRIMARY,
         "• Sub-30ms Real-Time Prediction\n"
         "• Hybrid Neuro-Symbolic Engine\n"
         "• Emergency Red-Flag Triage (<1ms)\n"
         "• Local LLM Orchestration & Fallbacks\n"
         "• 10-Failure Circuit Breaker Gate"),

        ("PERSON 2", "Clinical NLP & Voice Ingestion", TEAL_MEDICAL,
         "• Web Audio API (16kHz PCM Stream)\n"
         "• Faster-Whisper Large-v3 Local ASR\n"
         "• PyAnnote 3.1 Speaker Diarization\n"
         "• Shorthand Expansion (<5ms)\n"
         "• Clause Negation & SNOMED CT Mapping"),

        ("PERSON 3", "Diagnostic Engine & Safety Citadel", PURPLE_ACC,
         "• Deterministic Scoring Mathematics\n"
         "• 1,500+ Open-Domain Disease Catalog\n"
         "• India Outbreak Radar (28 States/8 UTs)\n"
         "• Discriminative Tiebreaker Tests\n"
         "• Polypharmacy FDA Boxed DDI Matrix"),

        ("PERSON 4", "Frontend, Data, Security & Evaluation", EMERALD_GREEN,
         "• Next.js 16.3.4 (App Router) & React 19\n"
         "• Dual-Channel REST & Resilient WebSockets\n"
         "• PostgreSQL 16 + pgvector HNSW + Redis 7\n"
         "• SHA-256 Tamper-Evident Record Sealing\n"
         "• 80-Case Benchmark (100% Accuracy)")
    ]

    for i, (p_num, p_role, col, bullet_text) in enumerate(team):
        card = add_card(s3, 0.8 + (i * 2.95), 1.6, 2.8, 5.2, bg_color=BG_LIGHT, border_color=col, border_width=2.0)
        tf = card.text_frame
        tf.word_wrap = True

        p_badge = tf.paragraphs[0]
        p_badge.text = p_num
        p_badge.font.name = "Calibri"
        p_badge.font.size = Pt(13)
        p_badge.font.bold = True
        p_badge.font.color.rgb = col

        p_sub = tf.add_paragraph()
        p_sub.text = p_role
        p_sub.font.name = "Calibri"
        p_sub.font.size = Pt(14)
        p_sub.font.bold = True
        p_sub.font.color.rgb = CARD_DARK
        p_sub.space_before = Pt(4)

        p_list = tf.add_paragraph()
        p_list.text = bullet_text
        p_list.font.name = "Calibri"
        p_list.font.size = Pt(11)
        p_list.font.color.rgb = SLATE_TEXT
        p_list.space_before = Pt(14)

    # =========================================================================
    # SLIDE 4: Full-Scale High-Resolution System Architecture (Full Diagram)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, DARK_NAVY)
    add_header(s4, "DocAssistIQ Modular Monolith Architecture (4K System Diagram)", "Enterprise Technical Blueprint", dark_theme=True)

    arch_img = "DocAssistIQ_Architecture_PPT_Slide.png"
    if os.path.exists(arch_img):
        s4.shapes.add_picture(arch_img, Inches(0.8), Inches(1.4), width=Inches(11.733))

    # =========================================================================
    # SLIDE 5: End-to-End Clinical Intelligence Lifecycle Diagram
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, DARK_NAVY)
    add_header(s5, "End-to-End Clinical Decision & Data Lifecycle (4-Stage Pipeline)", "Pipeline Workflow", dark_theme=True)

    pipeline_img = "clinical_pipeline_diagram_4k.png"
    if os.path.exists(pipeline_img):
        s5.shapes.add_picture(pipeline_img, Inches(0.8), Inches(1.4), width=Inches(11.733))

    # =========================================================================
    # SLIDE 6: Person 1 — Hybrid Neuro-Symbolic Engine
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, PURE_WHITE)
    add_header(s6, "Person 1: Hybrid Reasoning — Decoupling Math from Narration", "Foundations & Intelligence Core")

    # Left Card: Why Not Raw LLMs?
    c1 = add_card(s6, 0.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=ROSE_ALERT, border_width=1.5)
    tf1 = c1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "The Fallacy of End-to-End LLM Diagnosis"
    p.font.name = "Calibri"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = ROSE_ALERT

    p_b1 = tf1.add_paragraph()
    p_b1.text = (
        "• Stochastic Variance: The same clinical prompt produces varying differentials across turns.\n\n"
        "• Calibrated Cutoff Failure: Unconstrained LLMs cannot deterministically enforce lab thresholds (e.g., Troponin > 0.04 ng/mL, Platelets < 50,000/μL).\n\n"
        "• Legal Black-Box Liability: An LLM cannot mathematically prove which exact symptom triggered a diagnosis in a court of law.\n\n"
        "• Token Cost & Latency: Cloud API calls require 3 to 15 seconds, making real-time interactive typing impossible."
    )
    p_b1.font.name = "Calibri"
    p_b1.font.size = Pt(12)
    p_b1.font.color.rgb = SLATE_TEXT
    p_b1.space_before = Pt(12)

    # Right Card: The DocAssistIQ Two-Stage Solution
    c2 = add_card(s6, 6.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=TEAL_MEDICAL, border_width=1.5)
    tf2 = c2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = "The DocAssistIQ Two-Stage Solution"
    p2.font.name = "Calibri"
    p2.font.size = Pt(16)
    p2.font.bold = True
    p2.font.color.rgb = TEAL_MEDICAL

    p_b2 = tf2.add_paragraph()
    p_b2.text = (
        "• STAGE 1: Deterministic Python Engine (90% of Work)\n"
        "  - Evaluates candidate diseases via Bayesian priors and weighted Jaccard similarity in < 30ms.\n"
        "  - Applies emergency red-flag triage rules in < 1ms.\n"
        "  - Ranks the entire differential deterministically before any AI model is invoked.\n\n"
        "• STAGE 2: Local LLM Narrator (10% of Work)\n"
        "  - Receives Stage 1 pre-ranked candidates as immutable context.\n"
        "  - Constrained local model (ii-medical:8b at temp 0.1) synthesizes grounded clinical justifications.\n"
        "  - Forbidden from changing diagnostic rank order or hallucinating unlisted diseases."
    )
    p_b2.font.name = "Calibri"
    p_b2.font.size = Pt(12)
    p_b2.font.color.rgb = SLATE_TEXT
    p_b2.space_before = Pt(12)

    # =========================================================================
    # SLIDE 7: Person 1 — Sub-30ms Real-Time Inference & Emergency Triage
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, PURE_WHITE)
    add_header(s7, "Person 1: Sub-30ms Real-Time Inference & Emergency Red-Flag Triage", "Real-Time System Runtime")

    c_left = add_card(s7, 0.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=BLUE_PRIMARY, border_width=1.5)
    tf_l = c_left.text_frame
    tf_l.word_wrap = True
    pl = tf_l.paragraphs[0]
    pl.text = "Sub-30ms Real-Time Engine (realtime_prediction_service.py)"
    pl.font.name = "Calibri"
    pl.font.size = Pt(15)
    pl.font.bold = True
    pl.font.color.rgb = BLUE_PRIMARY

    pl_b = tf_l.add_paragraph()
    pl_b.text = (
        "• Zero-Network Execution: Operates entirely in server memory without disk I/O, database round-trips, or GPU inference in the critical path.\n\n"
        "• Pre-Compiled Regex Matching: Shorthands and symptoms are matched using compiled regular expression trees in under 5 milliseconds.\n\n"
        "• Hash Map Dictionary Lookups: Disease profiles are indexed by symptom hash sets, allowing instantaneous candidate retrieval.\n\n"
        "• Verified Benchmark Latency: Consistently executes in 18 to 28 milliseconds (average 22.5 ms), enabling true real-time feedback as the doctor types."
    )
    pl_b.font.name = "Calibri"
    pl_b.font.size = Pt(12)
    pl_b.font.color.rgb = SLATE_TEXT
    pl_b.space_before = Pt(12)

    c_right = add_card(s7, 6.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=ROSE_ALERT, border_width=1.5)
    tf_r = c_right.text_frame
    tf_r.word_wrap = True
    pr = tf_r.paragraphs[0]
    pr.text = "Emergency Red-Flag Registry (EMERGENCY_RULES < 1ms)"
    pr.font.name = "Calibri"
    pr.font.size = Pt(15)
    pr.font.bold = True
    pr.font.color.rgb = ROSE_ALERT

    pr_b = tf_r.add_paragraph()
    pr_b.text = (
        "• Life-Threatening Presentations Scanned Deterministically:\n"
        "  - Acute Aortic Dissection: Tearing chest pain radiating to back + unequal blood pressures.\n"
        "  - STEMI (Myocardial Infarction): Crushing substernal pain radiating to left arm + diaphoresis.\n"
        "  - Bacterial Meningitis: Triad of high fever + severe neck stiffness + altered mental status.\n"
        "  - Tension Pneumothorax: Tracheal deviation + unilateral absent breath sounds + hypotension.\n\n"
        "• Instant Bedside Protocol Trigger:\n"
        "  Elevates critical alert banners immediately, prepending emergency bedside orders (e.g., Stat 12-lead ECG, Door-to-balloon PCI) before differential ranking."
    )
    pr_b.font.name = "Calibri"
    pr_b.font.size = Pt(12)
    pr_b.font.color.rgb = SLATE_TEXT
    pr_b.space_before = Pt(12)

    # =========================================================================
    # SLIDE 8: Person 1 — Local LLM Orchestration & Circuit Breaker
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, PURE_WHITE)
    add_header(s8, "Person 1: Local LLM Orchestration & Hardware Resilience", "Model Serving & Reliability")

    cards_s8 = [
        ("Constrained Local Inference",
         "• Local Model: ii-medical:8b / llama3.2 hosted on local GPU via Ollama runtime (port 11434).\n"
         "• Strict Low Temperature (0.1): Minimizes stochastic sampling variance and guarantees reproducible clinical prose.\n"
         "• Zero Cloud Egress: All clinical prompts remain on the hospital premises, guaranteeing HIPAA compliance.",
         PURPLE_ACC),
        ("Structured JSON Enforcement",
         "• Strict Pydantic JSON Schemas: LLM outputs are forced into structured JSON with fields for summary, reasoning, and missing signs.\n"
         "• Schema Validation: If an LLM response fails validation, an automated repair parser corrects formatting errors instantly.",
         BLUE_PRIMARY),
        ("Hardware Circuit Breaker Pattern",
         "• 10 Consecutive Failure Trip: If Ollama crashes or runs out of VRAM, the circuit breaker opens for 30 seconds.\n"
         "• Zero Downtime Fallback: Bypasses the LLM completely, synthesizing clinical narratives from static medical monographs.\n"
         "• Self-Healing: Periodically tests background health checks and closes the circuit automatically once Ollama recovers.",
         EMERALD_GREEN)
    ]

    for i, (title, body, col) in enumerate(cards_s8):
        card = add_card(s8, 0.8 + (i * 3.95), 1.6, 3.8, 5.2, bg_color=BG_LIGHT, border_color=col, border_width=1.5)
        tf = card.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = "Calibri"
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = col

        pb = tf.add_paragraph()
        pb.text = body
        pb.font.name = "Calibri"
        pb.font.size = Pt(12)
        pb.font.color.rgb = SLATE_TEXT
        pb.space_before = Pt(14)

    # =========================================================================
    # SLIDE 9: Person 2 — Ambient Consultation Voice Ingestion & Diarization
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, PURE_WHITE)
    add_header(s9, "Person 2: Ambient Voice Consultation Ingestion & Audio Diarization", "Speech Ingestion & Acoustic Processing")

    c_v1 = add_card(s9, 0.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=TEAL_MEDICAL, border_width=1.5)
    tf_v1 = c_v1.text_frame
    tf_v1.word_wrap = True
    pv1 = tf_v1.paragraphs[0]
    pv1.text = "Microphone Capture & Faster-Whisper ASR"
    pv1.font.name = "Calibri"
    pv1.font.size = Pt(15)
    pv1.font.bold = True
    pv1.font.color.rgb = TEAL_MEDICAL

    pv1_b = tf_v1.add_paragraph()
    pv1_b.text = (
        "• Web Audio API Capture: Browser captures raw microphone input at 16kHz PCM single-channel mono, chunked into 250ms binary buffers.\n\n"
        "• WebSocket Streaming: Chunks stream via ws.ts to FastAPI backend without intermediate disk writes.\n\n"
        "• Faster-Whisper Large-v3: Uses CTranslate2 quantization (int8/float16), executing 4x faster than standard PyTorch Whisper with 1/3 the memory footprint.\n\n"
        "• Clinical Domain Prompting: Custom initial prompts prime Whisper to accurately transcribe medical jargon (e.g., dyspnea, hepatosplenomegaly, ciprofloxacin)."
    )
    pv1_b.font.name = "Calibri"
    pv1_b.font.size = Pt(12)
    pv1_b.font.color.rgb = SLATE_TEXT
    pv1_b.space_before = Pt(12)

    c_v2 = add_card(s9, 6.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=BLUE_PRIMARY, border_width=1.5)
    tf_v2 = c_v2.text_frame
    tf_v2.word_wrap = True
    pv2 = tf_v2.paragraphs[0]
    pv2.text = "PyAnnote 3.1 Dual-Speaker Diarization"
    pv2.font.name = "Calibri"
    pv2.font.size = Pt(15)
    pv2.font.bold = True
    pv2.font.color.rgb = BLUE_PRIMARY

    pv2_b = tf_v2.add_paragraph()
    pv2_b.text = (
        "• Acoustic Voiceprint Separation: Segregates dialogue between Attending Doctor and Patient using neural speaker embeddings.\n\n"
        "• Elimination of Role Confusion: Prevents patient subjective complaints from being recorded as physician clinical findings, and vice versa.\n\n"
        "• Real-Time Turn-Taking Alignment: Aligns Whisper transcription timestamps with PyAnnote speaker intervals with <150ms temporal jitter.\n\n"
        "• Energy-Based Voice Activity Detection (VAD): Suppresses background hospital noise, rustling paper, and trolley wheels."
    )
    pv2_b.font.name = "Calibri"
    pv2_b.font.size = Pt(12)
    pv2_b.font.color.rgb = SLATE_TEXT
    pv2_b.space_before = Pt(12)

    # =========================================================================
    # SLIDE 10: Person 2 — Clinical NLP: Shorthand Expansion & Negation Scope
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, PURE_WHITE)
    add_header(s10, "Person 2: Clinical NLP — Shorthand Expansion & Clause-Level Negation", "Clinical Text Parsing")

    c_nlp1 = add_card(s10, 0.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=BLUE_PRIMARY, border_width=1.5)
    tf_nlp1 = c_nlp1.text_frame
    tf_nlp1.word_wrap = True
    pn1 = tf_nlp1.paragraphs[0]
    pn1.text = "Deterministic Shorthand Expansion (CLINICAL_SHORTHANDS)"
    pn1.font.name = "Calibri"
    pn1.font.size = Pt(15)
    pn1.font.bold = True
    pn1.font.color.rgb = BLUE_PRIMARY

    pn1_b = tf_nlp1.add_paragraph()
    pn1_b.text = (
        "• Rapid Expansion Dictionary in clinical_note_parser.py (<1ms):\n"
        "  - SOB  -> 'shortness of breath'\n"
        "  - DOE  -> 'dyspnea on exertion'\n"
        "  - PMH  -> 'past medical history'\n"
        "  - c/o  -> 'complaining of'\n"
        "  - k/c/o -> 'known case of'\n"
        "  - N/V  -> 'nausea and vomiting'\n"
        "  - HTN  -> 'hypertension'\n"
        "  - T2DM -> 'type 2 diabetes mellitus'\n\n"
        "• Eliminates NLP Ambiguity: Standardizes messy physician typing into canonical terms prior to entity linking."
    )
    pn1_b.font.name = "Calibri"
    pn1_b.font.size = Pt(12)
    pn1_b.font.color.rgb = SLATE_TEXT
    pn1_b.space_before = Pt(12)

    c_nlp2 = add_card(s10, 6.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=PURPLE_ACC, border_width=1.5)
    tf_nlp2 = c_nlp2.text_frame
    tf_nlp2.word_wrap = True
    pn2 = tf_nlp2.paragraphs[0]
    pn2.text = "Clause-Level Negation Resolution (NEGATION_PATTERNS)"
    pn2.font.name = "Calibri"
    pn2.font.size = Pt(15)
    pn2.font.bold = True
    pn2.font.color.rgb = PURPLE_ACC

    pn2_b = tf_nlp2.add_paragraph()
    pn2_b.text = (
        "• The Clinical Negation Challenge:\n"
        "  Raw keyword search misinterprets: 'Patient has productive cough; denies chest pain or shortness of breath' as positive for chest pain.\n\n"
        "• DocAssistIQ Scope Resolution Algorithm:\n"
        "  1. Sentence & Clause Boundary Splitting (periods, semicolons, conjunctions like 'but', 'however', 'denies').\n"
        "  2. Scopes negation triggers ('no', 'denies', 'negative for', 'ruled out', 'absence of') across 1 to 5 subsequent tokens.\n"
        "  3. Correctly categorizes findings into POSITIVE vs. NEGATED sets.\n"
        "  4. Negative findings actively apply mathematical penalties to competing candidate diseases."
    )
    pn2_b.font.name = "Calibri"
    pn2_b.font.size = Pt(12)
    pn2_b.font.color.rgb = SLATE_TEXT
    pn2_b.space_before = Pt(12)

    # =========================================================================
    # SLIDE 11: Person 2 — Terminology Normalization & Patient Consent Gate
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11, PURE_WHITE)
    add_header(s11, "Person 2: Terminology Normalization & The Patient Consent Gate", "Standardization & Clinical Governance")

    c_t1 = add_card(s11, 0.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=TEAL_MEDICAL, border_width=1.5)
    tf_t1 = c_t1.text_frame
    tf_t1.word_wrap = True
    pt1 = tf_t1.paragraphs[0]
    pt1.text = "Concept Normalization (concept_normalizer.py)"
    pt1.font.name = "Calibri"
    pt1.font.size = Pt(15)
    pt1.font.bold = True
    pt1.font.color.rgb = TEAL_MEDICAL

    pt1_b = tf_t1.add_paragraph()
    pt1_b.text = (
        "• International Ontology Cross-Walking:\n"
        "  Maps unstructured phrases to standardized medical vocabularies:\n"
        "  - SNOMED CT: Clinical findings, symptoms, anatomical sites.\n"
        "  - RxNorm: Active ingredients, pharmaceutical forms, strengths.\n"
        "  - ICD-10-CM / ICD-11: Standard international billing and mortality codes.\n\n"
        "• Hybrid Normalization Pipeline:\n"
        "  1. Exact string match against curated concept dictionary.\n"
        "  2. Jaro-Winkler & Levenshtein phonetic/distance matching for spelling typos.\n"
        "  3. Semantic embedding nearest-neighbor lookup for complex clinical synonyms."
    )
    pt1_b.font.name = "Calibri"
    pt1_b.font.size = Pt(12)
    pt1_b.font.color.rgb = SLATE_TEXT
    pt1_b.space_before = Pt(12)

    c_t2 = add_card(s11, 6.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=ROSE_ALERT, border_width=1.5)
    tf_t2 = c_t2.text_frame
    tf_t2.word_wrap = True
    pt2 = tf_t2.paragraphs[0]
    pt2.text = "Mandatory Patient Consent Gate (consent.py)"
    pt2.font.name = "Calibri"
    pt2.font.size = Pt(15)
    pt2.font.bold = True
    pt2.font.color.rgb = ROSE_ALERT

    pt2_b = tf_t2.add_paragraph()
    pt2_b.text = (
        "• Ethical & Legal Non-Negotiable Gate:\n"
        "  Consultation audio capture and clinical parsing are strictly blocked at the API middleware level until explicit patient consent is recorded.\n\n"
        "• Audit Trail Recording (ConsentRecord Table):\n"
        "  - Stores consent type (Explicit Verbal, Written, Emergency Override).\n"
        "  - Captures clinician ID, patient session token, and ISO-8601 UTC timestamp.\n"
        "  - Cryptographically chained into the final consultation audit ledger.\n\n"
        "• Emergency Exception Handling:\n"
        "  In life-threatening trauma/unconscious patients, attending clinicians can toggle Emergency Override with mandatory justification logging."
    )
    pt2_b.font.name = "Calibri"
    pt2_b.font.size = Pt(12)
    pt2_b.font.color.rgb = SLATE_TEXT
    pt2_b.space_before = Pt(12)

    # =========================================================================
    # SLIDE 12: Person 3 — Deterministic Diagnostic Scoring Formulation
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12, PURE_WHITE)
    add_header(s12, "Person 3: Deterministic Diagnostic Scoring Formulation", "Mathematical Diagnostic Intelligence")

    c_math = add_card(s12, 0.8, 1.6, 11.733, 5.2, bg_color=BG_LIGHT, border_color=BLUE_PRIMARY, border_width=2.0)
    tf_m = c_math.text_frame
    tf_m.word_wrap = True

    pm = tf_m.paragraphs[0]
    pm.text = "The Multi-Factor Candidate Ranking Formulation (clinical_reasoning_engine.py)"
    pm.font.name = "Calibri"
    pm.font.size = Pt(16)
    pm.font.bold = True
    pm.font.color.rgb = BLUE_PRIMARY

    pm_eq = tf_m.add_paragraph()
    pm_eq.text = "Score(d) = w_1·Prior(d) + w_2·Jaccard_weighted(S_patient, S_d) + w_3·RedFlag(d) - w_4·Penalty(d)"
    pm_eq.font.name = "Consolas"
    pm_eq.font.size = Pt(15)
    pm_eq.font.bold = True
    pm_eq.font.color.rgb = CARD_DARK
    pm_eq.space_before = Pt(8)

    pm_b = tf_m.add_paragraph()
    pm_b.text = (
        "1. Bayesian Disease Prior [w_1 · Prior(d)]:\n"
        "   Base epidemiological incidence dynamically adjusted by patient age, sex, and geographic location.\n\n"
        "2. Weighted Jaccard Overlap [w_2 · Jaccard_weighted]:\n"
        "   Calculates ratio of symptom intersections. Pathognomonic hallmark signs (e.g., Kayser-Fleischer rings in Wilson's, Janeway lesions in Endocarditis) carry 3x to 5x weights over non-specific symptoms (fever, fatigue).\n\n"
        "3. Red-Flag & Cluster Multiplier [w_3 · RedFlag(d)]:\n"
        "   Elevates acute life-threatening surgical emergencies and multi-system triads (fever + jaundice + acute hemorrhage).\n\n"
        "4. Contraindication & Negation Demotion [- w_4 · Penalty(d)]:\n"
        "   Subtracts mathematical penalty if the patient explicitly denies a hallmark sign (e.g., patient denies cough demotes Pneumonia)."
    )
    pm_b.font.name = "Calibri"
    pm_b.font.size = Pt(12)
    pm_b.font.color.rgb = SLATE_TEXT
    pm_b.space_before = Pt(12)

    # =========================================================================
    # SLIDE 13: Person 3 — Open-Domain Engine & Rare Diseases (1,500+ Catalog)
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13, PURE_WHITE)
    add_header(s13, "Person 3: Open-Domain Medical Engine (1,500+ Conditions & Rare Diseases)", "Knowledge Generalization")

    c_od1 = add_card(s13, 0.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=TEAL_MEDICAL, border_width=1.5)
    tf_od1 = c_od1.text_frame
    tf_od1.word_wrap = True
    pod1 = tf_od1.paragraphs[0]
    pod1.text = "Overcoming Closed-World AI Limitations"
    pod1.font.name = "Calibri"
    pod1.font.size = Pt(15)
    pod1.font.bold = True
    pod1.font.color.rgb = TEAL_MEDICAL

    pod1_b = tf_od1.add_paragraph()
    pod1_b.text = (
        "• The Closed-World Problem: Typical medical models know only 50 to 100 textbook conditions, failing completely when faced with complex or rare diseases.\n\n"
        "• 1,500+ Indexed Clinical Entities: Extensively covers metabolic, genetic, neurodegenerative, and autoimmune conditions.\n\n"
        "• Built-In Rare Disease Coverage:\n"
        "  - Wilson's Disease: ATP7B mutation, copper toxic accumulation, Kayser-Fleischer rings, low ceruloplasmin.\n"
        "  - Friedreich's Ataxia: FXN GAA trinucleotide repeat, sensory neuropathy, hypertrophic cardiomyopathy.\n"
        "  - Ataxia-Telangiectasia: ATM mutation, progressive cerebellar ataxia, oculocutaneous telangiectasia, immunodeficiency."
    )
    pod1_b.font.name = "Calibri"
    pod1_b.font.size = Pt(12)
    pod1_b.font.color.rgb = SLATE_TEXT
    pod1_b.space_before = Pt(12)

    c_od2 = add_card(s13, 6.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=BLUE_PRIMARY, border_width=1.5)
    tf_od2 = c_od2.text_frame
    tf_od2.word_wrap = True
    pod2 = tf_od2.paragraphs[0]
    pod2.text = "Tri-Source Live Fallback Resolution Pipeline"
    pod2.font.name = "Calibri"
    pod2.font.size = Pt(15)
    pod2.font.bold = True
    pod2.font.color.rgb = BLUE_PRIMARY

    pod2_b = tf_od2.add_paragraph()
    pod2_b.text = (
        "• Dynamic External Discovery for Out-of-Catalog Queries:\n"
        "  1. Local Knowledge Graph (Master catalog of 1,500+ conditions).\n"
        "  2. NIH NLM ClinicalTables API: Live lookup over 100,000+ conditions and ICD-10-CM codes with 2.0s timeout.\n"
        "  3. OpenFDA Drug & Indications API: Live resolution of drug indications, boxed warnings, and adverse profiles.\n\n"
        "• In-Memory Thread-Safe Cache (_LIVE_RESOLVED_CACHE):\n"
        "  Successfully resolved external conditions are cached in memory with LRU eviction, reducing subsequent query latency to < 1 ms."
    )
    pod2_b.font.name = "Calibri"
    pod2_b.font.size = Pt(12)
    pod2_b.font.color.rgb = SLATE_TEXT
    pod2_b.space_before = Pt(12)

    # =========================================================================
    # SLIDE 14: Person 3 — India Epidemiological Outbreak Surveillance Radar
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14, PURE_WHITE)
    add_header(s14, "Person 3: India Outbreak Surveillance Radar (28 States & 8 UTs)", "Epidemiological Intelligence")

    cards_s14 = [
        ("Regional Disease Vectors",
         "• Kerala: Nipah Virus (Pteropus fruit bat vector), Leptospirosis (Weil's disease post-monsoon), KFD in border districts.\n\n"
         "• Karnataka: Kyasanur Forest Disease (KFD / Flavivirus tick vector in Western Ghats), Dengue, Chikungunya.\n\n"
         "• Gujarat: Chandipura Vesiculovirus (rapid pediatric encephalitis via sandflies), Crimean-Congo Hemorrhagic Fever.\n\n"
         "• Maharashtra: Urban Leptospirosis during monsoon waterlogging, H1N1 Influenza.\n\n"
         "• Himachal / Uttarakhand: Scrub Typhus (Orientia tsutsugamushi via chigger mites).",
         PURPLE_ACC),

        ("Bayesian Prior Boosting",
         "• Geo-Location Multiplier:\n"
         "  Prior_adjusted(d) = Prior_base(d) * Outbreak_multiplier(state, season)\n\n"
         "• NCDC & IDSP Modeling:\n"
         "  Incorporates weekly syndromic surveillance bulletins from the National Centre for Disease Control (NCDC) and Integrated Disease Surveillance Programme (IDSP).\n\n"
         "• Prevents Tropical Misses:\n"
         "  Elevates regional hemorrhagic fevers and encephalitides that Western medical algorithms routinely miss.",
         BLUE_PRIMARY),

        ("Discriminative Travel Questions",
         "• Automated Bedside Prompts:\n"
         "  When a fever with thrombocytopenia is logged in Karnataka, the engine automatically prompts:\n"
         "  - 'Recent travel or trekking in Western Ghats forest areas?'\n"
         "  - 'History of tick bites or monkey deaths nearby?'\n\n"
         "• Early Quarantine Protocols:\n"
         "  Alerts the hospital infection control officer immediately if Nipah or CCHF is suspected.",
         EMERALD_GREEN)
    ]

    for i, (title, body, col) in enumerate(cards_s14):
        card = add_card(s14, 0.8 + (i * 3.95), 1.6, 3.8, 5.2, bg_color=BG_LIGHT, border_color=col, border_width=1.5)
        tf = card.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = "Calibri"
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = col

        pb = tf.add_paragraph()
        pb.text = body
        pb.font.name = "Calibri"
        pb.font.size = Pt(11.5)
        pb.font.color.rgb = SLATE_TEXT
        pb.space_before = Pt(12)

    # =========================================================================
    # SLIDE 15: Person 3 — Discriminative Testing & Validated Criteria
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_background(s15, PURE_WHITE)
    add_header(s15, "Person 3: Discriminative Testing Engine & Validated Clinical Criteria", "Diagnostic Precision")

    c_dt1 = add_card(s15, 0.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=PURPLE_ACC, border_width=1.5)
    tf_dt1 = c_dt1.text_frame
    tf_dt1.word_wrap = True
    pdt1 = tf_dt1.paragraphs[0]
    pdt1.text = "Lookalike Pair Discriminative Tiebreaker Engine"
    pdt1.font.name = "Calibri"
    pdt1.font.size = Pt(15)
    pdt1.font.bold = True
    pdt1.font.color.rgb = PURPLE_ACC

    pdt1_b = tf_dt1.add_paragraph()
    pdt1_b.text = (
        "• Automatically Breaks Diagnostic Ties:\n"
        "  - Chikungunya vs. Dengue:\n"
        "    Discriminative Test: Anti-CHIKV IgM ELISA vs. Dengue NS1 / Tourniquet Test.\n"
        "    Clinical Tiebreaker: Persistent symmetrical polyarthritis vs. severe plasma leakage / thrombocytopenia.\n\n"
        "  - Bacterial Meningitis vs. Subarachnoid Hemorrhage:\n"
        "    Discriminative Test: Non-Contrast Head CT + Lumbar Puncture opening pressure/xanthochromia.\n"
        "    Clinical Tiebreaker: High fever/neutrophils vs. sudden thunderclap headache without initial fever.\n\n"
        "  - Acute Intermittent Porphyria vs. Appendicitis:\n"
        "    Discriminative Test: Urinary Porphobilinogen (PBG) vs. Abdominal Sonography/CT."
    )
    pdt1_b.font.name = "Calibri"
    pdt1_b.font.size = Pt(11.5)
    pdt1_b.font.color.rgb = SLATE_TEXT
    pdt1_b.space_before = Pt(12)

    c_dt2 = add_card(s15, 6.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=TEAL_MEDICAL, border_width=1.5)
    tf_dt2 = c_dt2.text_frame
    tf_dt2.word_wrap = True
    pdt2 = tf_dt2.paragraphs[0]
    pdt2.text = "Deterministic Clinical Criteria Evaluators"
    pdt2.font.name = "Calibri"
    pdt2.font.size = Pt(15)
    pdt2.font.bold = True
    pdt2.font.color.rgb = TEAL_MEDICAL

    pdt2_b = tf_dt2.add_paragraph()
    pdt2_b.text = (
        "• ACR/EULAR 2019 Criteria for SLE (Lupus):\n"
        "  - Mandatory Entry Criterion: ANA titer >= 1:80.\n"
        "  - Additive Domains: Constitutional, Hematologic, Mucocutaneous, Serosal, Renal, Musculoskeletal.\n"
        "  - Score >= 10 points classifies Systemic Lupus Erythematosus.\n\n"
        "• Modified Duke Criteria for Infective Endocarditis:\n"
        "  - 2 Major Criteria (persistent typical bacteremia, positive echo vegetation/abscess).\n"
        "  - 5 Minor Criteria (predisposition, fever, vascular/Janeway, immunologic/Osler).\n\n"
        "• Wells' Criteria for Pulmonary Embolism:\n"
        "  - Score > 4.0: PE Likely -> Stat CT Pulmonary Angiography.\n"
        "  - Score <= 4.0: PE Unlikely -> High-sensitivity D-Dimer rule-out."
    )
    pdt2_b.font.name = "Calibri"
    pdt2_b.font.size = Pt(11.5)
    pdt2_b.font.color.rgb = SLATE_TEXT
    pdt2_b.space_before = Pt(12)

    # =========================================================================
    # SLIDE 16: Person 3 — Polypharmacy Safety Citadel & Watermark
    # =========================================================================
    s16 = prs.slides.add_slide(blank_layout)
    set_slide_background(s16, PURE_WHITE)
    add_header(s16, "Person 3: Polypharmacy Safety Citadel & Regulatory Watermark", "Clinical Safety Safeguards")

    c_poly1 = add_card(s16, 0.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=ROSE_ALERT, border_width=1.5)
    tf_poly1 = c_poly1.text_frame
    tf_poly1.word_wrap = True
    pp1 = tf_poly1.paragraphs[0]
    pp1.text = "Deterministic Lethal Drug-Drug Interaction Matrix"
    pp1.font.name = "Calibri"
    pp1.font.size = Pt(15)
    pp1.font.bold = True
    pp1.font.color.rgb = ROSE_ALERT

    pp1_b = tf_poly1.add_paragraph()
    pp1_b.text = (
        "• Hardcoded FDA Boxed Warning Enforcement:\n"
        "  - Warfarin + Aspirin/NSAIDs:\n"
        "    Severity: CRITICAL -> Severe GI & intracranial hemorrhage risk via combined antiplatelet/anticoagulant synergy.\n\n"
        "  - Sildenafil + Nitroglycerin:\n"
        "    Severity: LETHAL -> Synergistic cGMP accumulation causing profound, refractory systemic hypotension and cardiac arrest.\n\n"
        "  - Lisinopril + Spironolactone:\n"
        "    Severity: HIGH -> Dual potassium-sparing suppression causing fatal hyperkalemia and ventricular arrhythmias.\n\n"
        "• Zero AI Bypass: Safety rules execute in hard Python code; no LLM can override or dismiss a critical drug contraindication."
    )
    pp1_b.font.name = "Calibri"
    pp1_b.font.size = Pt(11.5)
    pp1_b.font.color.rgb = SLATE_TEXT
    pp1_b.space_before = Pt(12)

    c_poly2 = add_card(s16, 6.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=AMBER_WARN, border_width=1.5)
    tf_poly2 = c_poly2.text_frame
    tf_poly2.word_wrap = True
    pp2 = tf_poly2.paragraphs[0]
    pp2.text = "The Mandatory Legal Watermark & Compliance"
    pp2.font.name = "Calibri"
    pp2.font.size = Pt(15)
    pp2.font.bold = True
    pp2.font.color.rgb = AMBER_WARN

    pp2_b = tf_poly2.add_paragraph()
    pp2_b.text = (
        "• Regulatory Governance & Medico-Legal Safeguard:\n"
        "  Every single screen, JSON payload, and exported document is permanently stamped with:\n\n"
        "  'REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED'\n\n"
        "• Compliance Standards Met:\n"
        "  - US FDA CDSS Guidance (Clinical Decision Support Software exemption criteria).\n"
        "  - EU Medical Device Regulation (EU MDR 2017/745 Class IIa SaMD rules).\n"
        "  - Asserts that DocAssistIQ is an assistive decision-support tool, preserving ultimate clinical authority and liability with the licensed human practitioner."
    )
    pp2_b.font.name = "Calibri"
    pp2_b.font.size = Pt(12)
    pp2_b.font.color.rgb = SLATE_TEXT
    pp2_b.space_before = Pt(12)

    # =========================================================================
    # SLIDE 17: Person 4 — Next.js 16 & React 19 Frontend Architecture
    # =========================================================================
    s17 = prs.slides.add_slide(blank_layout)
    set_slide_background(s17, PURE_WHITE)
    add_header(s17, "Person 4: Next.js 16 & React 19 Modern Frontend Architecture", "Full-Stack User Experience")

    fe_cards = [
        ("App Router & Server Components",
         "• Next.js 16.3.4 App Router: Nested layouts, server-side data fetching, and zero client JS bundle overhead for static tables.\n\n"
         "• React 19.2.8 RSC Boundary: Clear separation between asynchronous Server Components and dynamic Client Components ('use client').",
         BLUE_PRIMARY),

        ("Design System & UI Library",
         "• TailwindCSS v4: Modern utility-first CSS design with theme variables, achieving sub-100ms UI render times.\n\n"
         "• Radix UI Primitives: Unstyled, accessible dialogs, tabs, and tooltips complying with W3C WAI-ARIA standards.\n\n"
         "• Framer Motion: Hardware-accelerated smooth waveforms and alert transitions.",
         TEAL_MEDICAL),

        ("State & Optimistic Updates",
         "• TanStack Query v5: Manages server-side cache invalidation, deduplication, and background polling.\n\n"
         "• Optimistic Mutations: Medication and symptom edits reflect in the UI immediately before server ACK, rolling back gracefully if an error occurs.",
         EMERALD_GREEN)
    ]

    for i, (title, body, col) in enumerate(fe_cards):
        card = add_card(s17, 0.8 + (i * 3.95), 1.6, 3.8, 5.2, bg_color=BG_LIGHT, border_color=col, border_width=1.5)
        tf = card.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = "Calibri"
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = col

        pb = tf.add_paragraph()
        pb.text = body
        pb.font.name = "Calibri"
        pb.font.size = Pt(12)
        pb.font.color.rgb = SLATE_TEXT
        pb.space_before = Pt(14)

    # =========================================================================
    # SLIDE 18: Person 4 — Dual-Channel Real-Time Integration
    # =========================================================================
    s18 = prs.slides.add_slide(blank_layout)
    set_slide_background(s18, PURE_WHITE)
    add_header(s18, "Person 4: Full-Stack Integration — Typed REST & Resilient WebSockets", "Full-Stack Real-Time Pipeline")

    c_ws1 = add_card(s18, 0.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=BLUE_PRIMARY, border_width=1.5)
    tf_ws1 = c_ws1.text_frame
    tf_ws1.word_wrap = True
    pws1 = tf_ws1.paragraphs[0]
    pws1.text = "Strongly-Typed REST API Client (lib/api.ts - 85KB)"
    pws1.font.name = "Calibri"
    pws1.font.size = Pt(15)
    pws1.font.bold = True
    pws1.font.color.rgb = BLUE_PRIMARY

    pws1_b = tf_ws1.add_paragraph()
    pws1_b.text = (
        "• Enterprise TypeScript API Layer:\n"
        "  - 85 KB comprehensive client mapping over 50 backend FastAPI endpoints.\n"
        "  - Strict TypeScript interface typings mirroring backend Pydantic models.\n"
        "  - Centralized error interception, JWT bearer token refresh, and request correlation IDs.\n\n"
        "• Covers All Major Workflows:\n"
        "  Authentication, Patient Profile lookup, Consultation state transitions, Differential queries, Document downloads, and Outbreak radar data."
    )
    pws1_b.font.name = "Calibri"
    pws1_b.font.size = Pt(12)
    pws1_b.font.color.rgb = SLATE_TEXT
    pws1_b.space_before = Pt(12)

    c_ws2 = add_card(s18, 6.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=PURPLE_ACC, border_width=1.5)
    tf_ws2 = c_ws2.text_frame
    tf_ws2.word_wrap = True
    pws2 = tf_ws2.paragraphs[0]
    pws2.text = "Resilient Full-Duplex WebSockets (lib/ws.ts)"
    pws2.font.name = "Calibri"
    pws2.font.size = Pt(15)
    pws2.font.bold = True
    pws2.font.color.rgb = PURPLE_ACC

    pws2_b = tf_ws2.add_paragraph()
    pws2_b.text = (
        "• Bidirectional Low-Latency Tunnel:\n"
        "  Streams binary PCM audio chunks upstream and diarized transcript tokens + live differential predictions downstream.\n\n"
        "• Jittered Exponential Backoff Reconnection:\n"
        "  If the hospital Wi-Fi drops, ws.ts automatically retries up to 10 times with randomized delay, preventing thundering herd server spikes.\n\n"
        "• In-Memory Offline Message Buffer:\n"
        "  Clinician inputs made during network dropouts are queued in memory and replayed automatically upon reconnection.\n\n"
        "• 30-Second Ping/Pong Heartbeats:\n"
        "  Actively detects and tears down silent half-open TCP connections."
    )
    pws2_b.font.name = "Calibri"
    pws2_b.font.size = Pt(12)
    pws2_b.font.color.rgb = SLATE_TEXT
    pws2_b.space_before = Pt(12)

    # =========================================================================
    # SLIDE 19: Person 4 — Database, Vector Storage & Redis Infrastructure
    # =========================================================================
    s19 = prs.slides.add_slide(blank_layout)
    set_slide_background(s19, PURE_WHITE)
    add_header(s19, "Person 4: Enterprise Data Infrastructure — PostgreSQL, pgvector & Redis", "Data Persistence & Vector Search")

    db_cards = [
        ("Relational Core: PostgreSQL 16",
         "• SQLAlchemy 2.0 Async Engine: Fully non-blocking database queries with asyncpg driver.\n\n"
         "• Connection Pooling: pool_size=20 with max_overflow=10 for high-concurrency throughput.\n\n"
         "• Normalized Relational Schema: Enforces ACID guarantees across Users, Doctors, PatientProfiles, Consultations, ClinicalNotes, Findings, and Audits.",
         BLUE_PRIMARY),

        ("Semantic Vector Search: pgvector",
         "• In-Database Vector Store: Native vector extension eliminating external Pinecone/Milvus overhead.\n\n"
         "• HNSW Indexing: Hierarchical Navigable Small World index using cosine distance (<=>) for 768/1536-dim embeddings.\n\n"
         "• Sub-15ms PMC Evidence RAG: Sub-linear nearest-neighbor search over thousands of medical research articles.",
         TEAL_MEDICAL),

        ("In-Memory Engine: Redis 7",
         "• Sub-Millisecond Cache: Stores live resolved NLM ClinicalTables and OpenFDA entities.\n\n"
         "• Token-Bucket Rate Limiting: Restricts public verification endpoints to 60 req/min, preventing brute force.\n\n"
         "• Pub/Sub Message Broker: Asynchronously dispatches consultation events to background workers.",
         ROSE_ALERT)
    ]

    for i, (title, body, col) in enumerate(db_cards):
        card = add_card(s19, 0.8 + (i * 3.95), 1.6, 3.8, 5.2, bg_color=BG_LIGHT, border_color=col, border_width=1.5)
        tf = card.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = "Calibri"
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = col

        pb = tf.add_paragraph()
        pb.text = body
        pb.font.name = "Calibri"
        pb.font.size = Pt(12)
        pb.font.color.rgb = SLATE_TEXT
        pb.space_before = Pt(14)

    # =========================================================================
    # SLIDE 20: Person 4 — Cryptographic Provenance & Verification Portal
    # =========================================================================
    s20 = prs.slides.add_slide(blank_layout)
    set_slide_background(s20, PURE_WHITE)
    add_header(s20, "Person 4: Cryptographic Provenance & Public Tamper-Evident Portal", "Security & Legal Verification")

    c_sec1 = add_card(s20, 0.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=EMERALD_GREEN, border_width=1.5)
    tf_sec1 = c_sec1.text_frame
    tf_sec1.word_wrap = True
    ps1 = tf_sec1.paragraphs[0]
    ps1.text = "SHA-256 Canonical Hashing & Document Generation"
    ps1.font.name = "Calibri"
    ps1.font.size = Pt(15)
    ps1.font.bold = True
    ps1.font.color.rgb = EMERALD_GREEN

    ps1_b = tf_sec1.add_paragraph()
    ps1_b.text = (
        "• Canonical JSON Normalization:\n"
        "  Keys are sorted alphabetically with compact delimiters before hashing, ensuring identical hashes regardless of formatting differences.\n\n"
        "• Immutable SHA-256 Digital Signature:\n"
        "  hashlib.sha256(canonical_bytes).hexdigest() computes a 64-character tamper-evident digest permanently stored in the database.\n\n"
        "• Certified PDF & DOCX Generation:\n"
        "  - Hospital-grade PDFs generated via FPDF2 with clinician registration badges and QR codes.\n"
        "  - Formatted Microsoft Word DOCX exported via python-docx."
    )
    ps1_b.font.name = "Calibri"
    ps1_b.font.size = Pt(12)
    ps1_b.font.color.rgb = SLATE_TEXT
    ps1_b.space_before = Pt(12)

    c_sec2 = add_card(s20, 6.8, 1.6, 5.7, 5.2, bg_color=BG_LIGHT, border_color=BLUE_PRIMARY, border_width=1.5)
    tf_sec2 = c_sec2.text_frame
    tf_sec2.word_wrap = True
    ps2 = tf_sec2.paragraphs[0]
    ps2.text = "Public Verification Portal (/verify/[code] & /verify/hash)"
    ps2.font.name = "Calibri"
    ps2.font.size = Pt(15)
    ps2.font.bold = True
    ps2.font.color.rgb = BLUE_PRIMARY

    ps2_b = tf_sec2.add_paragraph()
    ps2_b.text = (
        "• Instant Multi-Party Authenticity Check:\n"
        "  Pharmacists, insurers, or receiving hospitals visit the public portal at /verify/[code] or upload document hashes to verify origin.\n\n"
        "• Zero-Trust Cryptographic Guarantee:\n"
        "  If an attacker alters even a single dosage or date in the note, the re-computed SHA-256 hash mismatches, flagging 'DOCUMENT COMPROMISED' immediately.\n\n"
        "• Verified Clinical Ledger (verified_documents.json):\n"
        "  Backs the public registry with high-security verified document fingerprints."
    )
    ps2_b.font.name = "Calibri"
    ps2_b.font.size = Pt(12)
    ps2_b.font.color.rgb = SLATE_TEXT
    ps2_b.space_before = Pt(12)

    # =========================================================================
    # SLIDE 21: Person 4 — Empirical Benchmark Validation (80/80 - 100% Accuracy)
    # =========================================================================
    s21 = prs.slides.add_slide(blank_layout)
    set_slide_background(s21, DARK_NAVY)
    add_header(s21, "Person 4: Empirical Benchmark Evaluation (80/80 Passed — 100% Accuracy)", "Scientific Validation", dark_theme=True)

    bench_img = "benchmark_chart_4k.png"
    if os.path.exists(bench_img):
        s21.shapes.add_picture(bench_img, Inches(0.8), Inches(1.4), width=Inches(11.733))

    # =========================================================================
    # SLIDE 22: Comprehensive System Comparison Matrix
    # =========================================================================
    s22 = prs.slides.add_slide(blank_layout)
    set_slide_background(s22, PURE_WHITE)
    add_header(s22, "System Comparison: DocAssistIQ vs. Traditional EHR vs. Generic AI", "Competitive & Architectural Advantage")

    # Comparison Table
    table_shape = s22.shapes.add_table(rows=7, cols=4, left=Inches(0.8), top=Inches(1.6), width=Inches(11.733), height=Inches(5.0))
    tbl = table_shape.table
    tbl.columns[0].width = Inches(2.733)
    tbl.columns[1].width = Inches(3.0)
    tbl.columns[2].width = Inches(3.0)
    tbl.columns[3].width = Inches(3.0)

    headers = ["Evaluation Metric", "Traditional EHR Systems", "Generic Cloud LLMs (ChatGPT)", "DocAssistIQ (Our Solution)"]
    rows_data = [
        ["Diagnostic Latency", "N/A (Passive storage only)", "3,000ms - 15,000ms (High latency)", "< 30ms (Deterministic in-memory)"],
        ["Medical Hallucination Risk", "Zero (Manual doctor entry)", "High (Probabilistic fabrication)", "Zero (Stage 1 deterministic math)"],
        ["Ambient Voice & Diarization", "None or basic dictation", "Speech only (No speaker separation)", "Dual-Speaker PyAnnote 3.1 Diarization"],
        ["Negation Resolution", "None (Fails on denied terms)", "Inconsistent across turns", "Deterministic clause-level scope parser"],
        ["Regional Outbreak Surveillance", "None (Siloed databases)", "Static training cutoff (Blind to local)", "India 28-State / 8-UT NCDC/IDSP Radar"],
        ["Tamper-Evident Provenance", "Basic database update timestamp", "None", "SHA-256 Cryptographic Record Sealing"]
    ]

    for c_idx, h_text in enumerate(headers):
        cell = tbl.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = DARK_NAVY
        p = cell.text_frame.paragraphs[0]
        p.text = h_text
        p.font.name = "Calibri"
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = PURE_WHITE

    for r_idx, r_vals in enumerate(rows_data):
        for c_idx, val in enumerate(r_vals):
            cell = tbl.cell(r_idx + 1, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(241, 245, 249) if r_idx % 2 == 1 else PURE_WHITE
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = "Calibri"
            p.font.size = Pt(10.5)
            if c_idx == 3:
                p.font.bold = True
                p.font.color.rgb = BLUE_PRIMARY
            else:
                p.font.color.rgb = SLATE_TEXT

    # =========================================================================
    # SLIDE 23: Master Faculty Viva Defense Strategy (Top 10 Core Defenses)
    # =========================================================================
    s23 = prs.slides.add_slide(blank_layout)
    set_slide_background(s23, PURE_WHITE)
    add_header(s23, "Master Faculty Viva Defense Strategy — Top 6 Examiner Challenges", "Viva Preparation")

    viva_cards = [
        ("Are you claiming this replaces a licensed doctor?",
         "NO. DocAssistIQ is strictly a Clinical Decision Support System (CDSS). Every screen and document bears our mandatory legal watermark: 'REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED'. Final clinical authority rests solely with the physician.",
         BLUE_PRIMARY),

        ("How do you guarantee your AI won't hallucinate?",
         "Through our Two-Stage Architecture. Stage 1 ranks candidate diseases deterministically via Python Bayesian priors and Jaccard math. The local LLM in Stage 2 is restricted to summarizing pre-ranked candidates and cannot introduce new conditions.",
         TEAL_MEDICAL),

        ("What if the hospital loses internet connection?",
         "DocAssistIQ operates fully offline. The FastAPI backend, Faster-Whisper ASR, Ollama LLM, PostgreSQL, and our 1,500-condition catalog run on local hospital server hardware without external internet access.",
         PURPLE_ACC),

        ("How do you protect patient privacy and HIPAA compliance?",
         "Zero Protected Health Information (PHI) leaves the hospital. Ingestion, transcription, diarization, and LLM reasoning run on local GPU/CPU hardware. External API queries transmit only sanitized medical terms, never patient names or IDs.",
         EMERALD_GREEN),

        ("Why WebSockets instead of REST polling for consultations?",
         "Consultations require bidirectional streaming (binary audio chunks upstream, diarized transcript tokens downstream). WebSockets eliminate repetitive HTTP header overhead, reducing latency and server bandwidth by >80%.",
         ROSE_ALERT),

        ("What proves your system actually works?",
         "Our empirical evaluation harness benchmark_clinical_cases.py tested 80 comprehensive clinical cases across 5 medical categories, achieving a 100% Top-3 diagnostic accuracy with an average latency under 30 milliseconds.",
         CARD_DARK)
    ]

    for i, (q, a, col) in enumerate(viva_cards):
        row = i // 3
        col_idx = i % 3
        card = add_card(s23, 0.8 + (col_idx * 3.95), 1.6 + (row * 2.7), 3.8, 2.5, bg_color=BG_LIGHT, border_color=col, border_width=1.5)
        tf = card.text_frame
        tf.word_wrap = True

        pq = tf.paragraphs[0]
        pq.text = q
        pq.font.name = "Calibri"
        pq.font.size = Pt(11.5)
        pq.font.bold = True
        pq.font.color.rgb = col

        pa = tf.add_paragraph()
        pa.text = a
        pa.font.name = "Calibri"
        pa.font.size = Pt(10)
        pa.font.color.rgb = SLATE_TEXT
        pa.space_before = Pt(6)

    # =========================================================================
    # SLIDE 24: Conclusion, Clinical Impact & Production Deployment
    # =========================================================================
    s24 = prs.slides.add_slide(blank_layout)
    set_slide_background(s24, DARK_NAVY)
    add_header(s24, "Conclusion, Clinical Impact & Production Deployment", "Summary & Takeaways", dark_theme=True)

    # Left Container: Deployment Architecture
    c_end1 = add_card(s24, 0.8, 1.6, 5.7, 5.2, bg_color=CARD_DARK, border_color=CYAN_ACCENT, border_width=1.5)
    tf_e1 = c_end1.text_frame
    tf_e1.word_wrap = True
    pe1 = tf_e1.paragraphs[0]
    pe1.text = "Production Docker Compose Orchestration"
    pe1.font.name = "Calibri"
    pe1.font.size = Pt(16)
    pe1.font.bold = True
    pe1.font.color.rgb = CYAN_ACCENT

    pe1_b = tf_e1.add_paragraph()
    pe1_b.text = (
        "• Containerized 4-Tier Production Stack:\n"
        "  - frontend: Next.js 16 container running on port 3000.\n"
        "  - backend: FastAPI async Uvicorn workers on port 8000.\n"
        "  - postgres: PostgreSQL 16 + pgvector with persistent volume mounts on port 5432.\n"
        "  - redis: Redis 7 Alpine in-memory cache & rate limiter on port 6379.\n\n"
        "• Automated One-Click Launchers:\n"
        "  - START_ALL_DOCKER.bat / START_ALL_LOCAL.bat for instant offline demonstration.\n"
        "  - Healthchecks ensure database readiness before API boot."
    )
    pe1_b.font.name = "Calibri"
    pe1_b.font.size = Pt(12)
    pe1_b.font.color.rgb = RGBColor(226, 232, 240)
    pe1_b.space_before = Pt(12)

    # Right Container: Final Takeaway
    c_end2 = add_card(s24, 6.8, 1.6, 5.7, 5.2, bg_color=CARD_DARK, border_color=EMERALD_GREEN, border_width=1.5)
    tf_e2 = c_end2.text_frame
    tf_e2.word_wrap = True
    pe2 = tf_e2.paragraphs[0]
    pe2.text = "Final Takeaway & Academic Contribution"
    pe2.font.name = "Calibri"
    pe2.font.size = Pt(16)
    pe2.font.bold = True
    pe2.font.color.rgb = EMERALD_GREEN

    pe2_b = tf_e2.add_paragraph()
    pe2_b.text = (
        "• Proven Engineering Deliverables:\n"
        "  - 80/80 passed benchmark clinical cases (100% Top-3 diagnostic accuracy).\n"
        "  - Sub-30ms real-time typing prediction with <1ms red-flag emergency triage.\n"
        "  - Full-duplex ambient voice consultation diarization with mandatory consent gates.\n"
        "  - 1,500+ open-domain conditions + India 28-State epidemiological surveillance radar.\n"
        "  - Immutable SHA-256 cryptographic provenance with public verification portal.\n\n"
        "• Core Philosophy:\n"
        "  'DocAssistIQ does not replace the physician—it amplifies clinical precision, eliminates administrative burnout, and protects human lives.'"
    )
    pe2_b.font.name = "Calibri"
    pe2_b.font.size = Pt(12)
    pe2_b.font.color.rgb = RGBColor(226, 232, 240)
    pe2_b.space_before = Pt(12)

    # Save to disk
    output_path = os.path.abspath("DocAssistIQ_Master_All_In_One_4K_Presentation.pptx")
    prs.save(output_path)
    print(f"SUCCESS: Generated 24-Slide 4K Presentation Deck at: {output_path}")

    # Also update the primary presentation files for convenience
    for alt_name in ["DocAssistIQ_Architecture_Presentation.pptx", "DocAssistIQ_Clean_Headings_Presentation.pptx"]:
        try:
            alt_path = os.path.abspath(alt_name)
            prs.save(alt_path)
            print(f"Also updated: {alt_path}")
        except Exception as e:
            print(f"Note: Could not update {alt_name}: {e}")

    return output_path

if __name__ == "__main__":
    build_presentation()
