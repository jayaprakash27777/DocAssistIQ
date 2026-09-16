import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.disease_intelligence import DiseaseIntelligenceResponse
from app.services.rag_service import retrieve_medical_context, RAGQueryRequest, perform_rag_query
from app.infrastructure.ai.factory import get_llm_provider
import structlog

log = structlog.get_logger(__name__)

async def generate_disease_intelligence(db: AsyncSession, disease_name: str) -> DiseaseIntelligenceResponse:
    """
    Massively upgraded disease intelligence generator (AI v2).
    - Multi-source context: Wikipedia + ICD-11 + PubMed + WHO/CDC + RAG
    - Uses IntelligenceEngine for live outbreak context
    - Includes incubation period data and investigation templates
    """
    # 1. Query RAG for this disease
    rag_request = RAGQueryRequest(query=f"{disease_name} symptoms treatment investigations")
    rag_response = await perform_rag_query(db, rag_request)

    # 2. Fetch all sources in parallel using intelligence_engine
    from app.services.intelligence_engine import intelligence_engine, INCUBATION_PERIODS, get_disease_class, get_investigation_template
    import asyncio

    intel_task = intelligence_engine.get_disease_intelligence_context(disease_name)
    rag_context_task = retrieve_medical_context(db, f"{disease_name} symptoms treatment etiology", top_k=3)

    intel_ctx, rag_context_str = await asyncio.gather(
        intel_task, rag_context_task, return_exceptions=True
    )

    if isinstance(intel_ctx, Exception):
        log.error("intelligence_engine_failed", error=str(intel_ctx))
        intel_ctx = {}
    if isinstance(rag_context_str, Exception):
        rag_context_str = ""

    # 3. Extract multi-source context
    wiki_ctx = intel_ctx.get("wikipedia_context", "") if isinstance(intel_ctx, dict) else ""
    pubmed_ctx = intel_ctx.get("pubmed_context", "") if isinstance(intel_ctx, dict) else ""
    icd_ctx = intel_ctx.get("icd_context", "") if isinstance(intel_ctx, dict) else ""
    who_cdc_ctx = intel_ctx.get("who_context", "") if isinstance(intel_ctx, dict) else ""
    disease_class = intel_ctx.get("disease_class") if isinstance(intel_ctx, dict) else get_disease_class(disease_name)
    incubation_data = INCUBATION_PERIODS.get(disease_name.lower())

    # 4. Build RAG citations string
    rag_citations_str = "\n\n".join([
        f"Source {i+1} ({c.source_type}): {c.preview_text}"
        for i, c in enumerate(rag_response.citations)
    ]) if rag_response.citations else ""

    # 5. Build rich combined context for LLM
    context_parts = []
    if icd_ctx:
        context_parts.append(icd_ctx)
    if wiki_ctx:
        context_parts.append(wiki_ctx)
    if pubmed_ctx:
        context_parts.append(pubmed_ctx)
    if who_cdc_ctx:
        # Filter WHO/CDC to relevant parts
        relevant_lines = [
            line for line in who_cdc_ctx.split("\n")
            if disease_name.lower() in line.lower() or any(
                syn in line.lower() for syn in [disease_name.lower().split()[0]]
            )
        ]
        if relevant_lines:
            context_parts.append("WHO/CDC RELEVANT NOTICES:\n" + "\n".join(relevant_lines[:5]))
    if rag_context_str:
        context_parts.append(f"STATIC RAG CONTEXT:\n{rag_context_str}")
    if rag_citations_str:
        context_parts.append(f"RAG CITATIONS:\n{rag_citations_str[:1000]}")

    # Add incubation data
    if incubation_data:
        context_parts.append(
            f"INCUBATION PERIOD DATA (Evidence-Based):\n"
            f"  Min: {incubation_data['min_days']} days\n"
            f"  Max: {incubation_data['max_days']} days\n"
            f"  Typical: {incubation_data['typical_days']} days\n"
            f"  Disease Class: {incubation_data['disease_class']}"
        )

    context_str = "\n\n".join(filter(None, context_parts))

    # 6. Build investigation template hints
    template_investigations = get_investigation_template(disease_class) if disease_class else []
    template_names = [t["name"] for t in template_investigations[:5]]
    template_hint = ""
    if template_names:
        template_hint = f"\n\nKNOWN KEY INVESTIGATIONS FOR {disease_class}: " + "; ".join(template_names)

    # 7. Call LLM with multi-source context
    llm = get_llm_provider("med_llm")

    system_prompt = f"""You are a world-class Clinical Intelligence AI specializing in infectious disease profiles.
Given the comprehensive multi-source context below about '{disease_name}', generate a highly accurate structured clinical profile.

## CRITICAL INSTRUCTIONS:
1. Use ALL provided sources (Wikipedia, ICD-11, PubMed, WHO/CDC, RAG) to form a complete answer.
2. For the summary: include etiology, pathophysiology, geographic distribution, and current outbreak status if relevant.
3. For symptoms: list ALL known symptoms from early to late disease progression (comprehensive list, 10-20 items).
4. For treatments: include supportive care, specific antivirals/antibiotics, experimental treatments, and WHO protocols.
5. For investigations: use SPECIFIC medical test names (not generic terms). Include confirmatory tests, monitoring tests, and differential-exclusion tests.
6. If incubation data is provided, include it in the summary.
{template_hint}

## Multi-Source Clinical Context:
{context_str}

Format your response EXACTLY as JSON matching this schema:
{{
  "summary": "3-4 comprehensive sentences describing the disease, etiology, geographic distribution, current outbreak context, incubation period, and typical clinical course.",
  "symptoms": ["Symptom 1 (early)", "Symptom 2", "...", "Symptom N (late/severe)"],
  "treatments": ["Treatment 1 (supportive)", "Treatment 2 (specific)", "Treatment 3 (experimental/WHO protocol)"],
  "investigations": ["Investigation 1 (HIGH PRIORITY - confirmatory)", "Investigation 2 (organ monitoring)", "Investigation 3 (differential exclusion)"]
}}
"""
    user_prompt = f"Generate the comprehensive clinical intelligence profile for: {disease_name}"

    try:
        response_text = await llm.generate_response(system_prompt, user_prompt, max_tokens=1500)

        # Clean potential markdown from response
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        data = json.loads(response_text.strip())

        # Add Wikipedia citation to RAG citations if available
        if wiki_ctx:
            from app.schemas.rag import RAGCitation
            from uuid import uuid4
            rag_response.citations.insert(0, RAGCitation(
                source_id=str(uuid4()),
                source_type="wikipedia_live",
                source_uri=f"https://en.wikipedia.org/wiki/{disease_name.replace(' ', '_')}",
                preview_text=wiki_ctx[:500],
                score=1.0
            ))

        # Add PubMed citation if available
        if pubmed_ctx:
            from app.schemas.rag import RAGCitation
            from uuid import uuid4
            rag_response.citations.append(RAGCitation(
                source_id=str(uuid4()),
                source_type="pubmed_live",
                source_uri="https://pubmed.ncbi.nlm.nih.gov/",
                preview_text=pubmed_ctx[:500],
                score=0.95
            ))

        return DiseaseIntelligenceResponse(
            disease_name=disease_name,
            summary=data.get("summary", "No summary available."),
            symptoms=data.get("symptoms", []),
            treatments=data.get("treatments", []),
            investigations=data.get("investigations", []),
            citations=rag_response.citations
        )

    except Exception as e:
        log.error("disease_intelligence_generation_failed", error=str(e), disease=disease_name)

        # Fallback: Return data from multi-source context without LLM
        fallback_investigations = template_names if template_names else []
        return DiseaseIntelligenceResponse(
            disease_name=disease_name,
            summary=f"Intelligence data from multiple sources: {wiki_ctx[:400] if wiki_ctx else 'See citations.'}",
            symptoms=[],
            treatments=[],
            investigations=fallback_investigations,
            citations=rag_response.citations
        )
