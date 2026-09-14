import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.disease_intelligence import DiseaseIntelligenceResponse
from app.services.rag_service import retrieve_medical_context, RAGQueryRequest, perform_rag_query
from app.infrastructure.ai.factory import get_llm_provider
import structlog

log = structlog.get_logger(__name__)

async def generate_disease_intelligence(db: AsyncSession, disease_name: str) -> DiseaseIntelligenceResponse:
    # 1. Query RAG for this disease
    rag_request = RAGQueryRequest(query=f"{disease_name} symptoms treatment investigations")
    rag_response = await perform_rag_query(db, rag_request)
    
    # 2. Extract context string and citations
    context_str = "\\n\\n".join([f"Source {i+1} ({c.source_type}): {c.preview_text}" for i, c in enumerate(rag_response.citations)])
    
    # NEW: Fetch live data from Wikipedia
    try:
        import httpx
        from urllib.parse import quote
        async with httpx.AsyncClient(timeout=3.0) as client:
            wiki_res = await client.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(disease_name)}")
            if wiki_res.status_code == 200:
                wiki_data = wiki_res.json()
                live_text = wiki_data.get("extract", "")
                if live_text:
                    context_str = f"LIVE WIKIPEDIA SUMMARY:\n{live_text}\n\nSTATIC RAG CONTEXT:\n{context_str}"
                    from app.schemas.rag import RAGCitation
                    from uuid import uuid4
                    rag_response.citations.insert(0, RAGCitation(
                        source_id=str(uuid4()),
                        source_type="wikipedia_live",
                        source_uri=wiki_data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                        preview_text=live_text,
                        score=1.0
                    ))
    except Exception as e:
        log.error("live_wikipedia_fetch_failed", error=str(e))

    # 3. Call LLM to parse into structured format
    llm = get_llm_provider("med_llm")
    
    system_prompt = f"""You are a clinical intelligence AI. Given the context about a disease, generate a structured profile.
    
Context:
{context_str}

Format your response exactly as JSON matching this schema:
{{
  "summary": "2-3 sentences describing the disease, its etiology, and typical presentation.",
  "symptoms": ["Symptom 1", "Symptom 2"],
  "treatments": ["Treatment 1", "Treatment 2"],
  "investigations": ["Investigation 1", "Investigation 2"]
}}
"""
    user_prompt = f"Generate the intelligence profile for: {disease_name}"
    
    try:
        response_text = await llm.generate_response(system_prompt, user_prompt, max_tokens=1000)
        
        # Clean potential markdown from response
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        data = json.loads(response_text)
        
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
        return DiseaseIntelligenceResponse(
            disease_name=disease_name,
            summary="Failed to generate disease intelligence due to an internal error.",
            symptoms=[],
            treatments=[],
            investigations=[],
            citations=rag_response.citations
        )
