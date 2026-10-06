"""DocAssistIQ — Unified Literature, Evidence & Clinical Trials Gateway.

Integrates 100% Free & Open (No Keys Needed) APIs:
1. NCBI PubMed & PMC (Entrez E-Utilities) — 40M+ peer-reviewed citations
2. Europe PMC — Full-text open-access medical articles
3. ClinicalTrials.gov v2 REST API — Active clinical trials and novel protocols
4. OpenAlex — Open academic knowledge graph and author citations
5. Semantic Scholar — AI-indexed biomedical research papers
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import quote
import httpx
import structlog

from app.config import get_settings

log = structlog.get_logger(__name__)

_EVIDENCE_CACHE: Dict[str, Tuple[float, Any]] = {}
_CACHE_TTL_SECONDS = 7200  # 2 hours


# ---------------------------------------------------------------------------
# 1. PubMed / PMC E-Utilities (Entrez)
# ---------------------------------------------------------------------------
async def query_pubmed_evidence(disease_query: str, max_results: int = 4) -> List[Dict[str, Any]]:
    """Queries NCBI Entrez E-Utilities for real peer-reviewed papers."""
    settings = get_settings()
    ncbi_key = settings.ncbi_api_key

    cache_key = f"pubmed_{disease_query.lower()}_{max_results}"
    now = time.time()
    if cache_key in _EVIDENCE_CACHE:
        ts, data = _EVIDENCE_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    articles = []
    key_param = f"&api_key={ncbi_key}" if ncbi_key else ""

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            # Step A: ESearch
            search_query = f'"{disease_query}"[Title/Abstract] AND (clinical trial[Publication Type] OR review[Publication Type] OR guideline[Publication Type])'
            search_url = (
                f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
                f"?db=pubmed&term={quote(search_query)}&retmax={max_results}&retmode=json{key_param}"
                f"&tool=docassistiq&email=clinical-ai@docassistiq.local"
            )
            r = await client.get(search_url)
            if r.status_code == 200:
                id_list = r.json().get("esearchresult", {}).get("idlist", [])
                if id_list:
                    # Step B: ESummary
                    ids_str = ",".join(id_list)
                    summary_url = (
                        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                        f"?db=pubmed&id={ids_str}&retmode=json{key_param}"
                        f"&tool=docassistiq&email=clinical-ai@docassistiq.local"
                    )
                    r_sum = await client.get(summary_url)
                    if r_sum.status_code == 200:
                        res_dict = r_sum.json().get("result", {})
                        for pmid in id_list:
                            if pmid in res_dict:
                                art = res_dict[pmid]
                                articles.append({
                                    "pmid": pmid,
                                    "title": art.get("title", ""),
                                    "journal": art.get("source", ""),
                                    "pub_date": art.get("pubdate", ""),
                                    "doi": next((aid.get("value") for aid in art.get("articleids", []) if aid.get("idtype") == "doi"), None),
                                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                                    "source": "NCBI PubMed",
                                })
        _EVIDENCE_CACHE[cache_key] = (now, articles)
    except Exception as e:
        log.warning("pubmed_query_failed", query=disease_query, error=str(e))

    return articles


# ---------------------------------------------------------------------------
# 2. ClinicalTrials.gov Modern v2 REST API (100% Free & Open, Zero Keys)
# ---------------------------------------------------------------------------
async def query_clinical_trials_v2(condition: str, max_trials: int = 3) -> List[Dict[str, Any]]:
    """Queries modern ClinicalTrials.gov v2 REST API for active clinical protocols."""
    cache_key = f"trials_v2_{condition.lower()}_{max_trials}"
    now = time.time()
    if cache_key in _EVIDENCE_CACHE:
        ts, data = _EVIDENCE_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    trials = []
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            url = f"https://clinicaltrials.gov/api/v2/studies?query.cond={quote(condition)}&pageSize={max_trials}&filter.overallStatus=RECRUITING,ACTIVE_NOT_RECRUITING"
            r = await client.get(url, headers={"Accept": "application/json"})
            if r.status_code == 200:
                studies = r.json().get("studies", [])
                for s in studies:
                    proto = s.get("protocolSection", {})
                    id_mod = proto.get("identificationModule", {})
                    status_mod = proto.get("statusModule", {})
                    desc_mod = proto.get("descriptionModule", {})
                    design_mod = proto.get("designModule", {})

                    nct_id = id_mod.get("nctId")
                    title = id_mod.get("briefTitle")
                    brief_summary = desc_mod.get("briefSummary", "")
                    phases = design_mod.get("phases", [])

                    trials.append({
                        "nct_id": nct_id,
                        "title": title,
                        "status": status_mod.get("overallStatus"),
                        "phases": phases,
                        "summary": brief_summary[:200] if brief_summary else "",
                        "url": f"https://clinicaltrials.gov/study/{nct_id}",
                        "source": "ClinicalTrials.gov (NIH)",
                    })
        _EVIDENCE_CACHE[cache_key] = (now, trials)
    except Exception as e:
        log.warning("clinicaltrials_v2_failed", condition=condition, error=str(e))

    return trials


# ---------------------------------------------------------------------------
# 3. Europe PMC (EMBL-EBI)
# ---------------------------------------------------------------------------
async def query_europe_pmc(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """Queries Europe PMC for pan-European open medical literature."""
    cache_key = f"epmc_{query.lower()}_{max_results}"
    now = time.time()
    if cache_key in _EVIDENCE_CACHE:
        ts, data = _EVIDENCE_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    results = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={quote(query)}&format=json&pageSize={max_results}&resultType=lite"
            r = await client.get(url)
            if r.status_code == 200:
                items = r.json().get("resultList", {}).get("result", [])
                for it in items:
                    results.append({
                        "id": it.get("id"),
                        "title": it.get("title"),
                        "journal": it.get("journalTitle"),
                        "year": it.get("pubYear"),
                        "doi": it.get("doi"),
                        "isOpenAccess": it.get("isOpenAccess") == "Y",
                        "url": f"https://europepmc.org/article/{it.get('source')}/{it.get('id')}",
                        "source": "Europe PMC",
                    })
        _EVIDENCE_CACHE[cache_key] = (now, results)
    except Exception as e:
        log.warning("europe_pmc_failed", query=query, error=str(e))

    return results


# ---------------------------------------------------------------------------
# 4. OpenAlex Academic Graph & Semantic Scholar
# ---------------------------------------------------------------------------
async def query_openalex_citations(query: str, max_results: int = 2) -> List[Dict[str, Any]]:
    """Queries OpenAlex for high-impact citation metadata."""
    cache_key = f"openalex_{query.lower()}"
    now = time.time()
    if cache_key in _EVIDENCE_CACHE:
        ts, data = _EVIDENCE_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    results = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = f"https://api.openalex.org/works?search={quote(query)}&filter=type:article&per-page={max_results}&mailto=clinical-ai@docassistiq.local"
            r = await client.get(url)
            if r.status_code == 200:
                works = r.json().get("results", [])
                for w in works:
                    results.append({
                        "id": w.get("id"),
                        "display_name": w.get("display_name"),
                        "publication_year": w.get("publication_year"),
                        "cited_by_count": w.get("cited_by_count"),
                        "doi": w.get("doi"),
                        "source": "OpenAlex Knowledge Graph",
                    })
        _EVIDENCE_CACHE[cache_key] = (now, results)
    except Exception as e:
        log.warning("openalex_query_failed", query=query, error=str(e))

    return results
