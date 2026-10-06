"""DocAssistIQ — Unified Rare Disease & Phenotype Gateway.

Integrates 100% Free & Open (No Keys Needed) APIs:
1. Orphanet / ORDO (Orphadata API) — 6,000+ rare diseases, gene mappings
2. MONDO Unified Disease Ontology (Monarch / EBI OLS) — Multi-ontology bridging
3. Monarch Phenotype-to-Disease Association — HPO constellation matching
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import quote
import httpx
import structlog

log = structlog.get_logger(__name__)

_RARE_CACHE: Dict[str, Tuple[float, Any]] = {}
_CACHE_TTL_SECONDS = 7200  # 2 hours


# ---------------------------------------------------------------------------
# 1. Orphanet / ORDO Rare Disease Registry (100% Free & Open, Zero Keys)
# ---------------------------------------------------------------------------
async def query_orphanet_disease(rare_disease_name: str) -> List[Dict[str, Any]]:
    """Queries Orphadata / Monarch for rare disease classification and ORPHA codes."""
    cache_key = f"orpha_{rare_disease_name.lower()}"
    now = time.time()
    if cache_key in _RARE_CACHE:
        ts, data = _RARE_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    results = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Query Monarch OLS for Orphadata concepts
            url = f"https://api.monarchinitiative.org/v3/api/search?q={quote(rare_disease_name)}&category=biolink:Disease&limit=3"
            r = await client.get(url, headers={"Accept": "application/json"})
            if r.status_code == 200:
                items = r.json().get("items", [])
                for it in items:
                    entity_id = it.get("id", "")
                    if "ORPHA:" in entity_id or "MONDO:" in entity_id:
                        results.append({
                            "disease_id": entity_id,
                            "name": it.get("name"),
                            "description": it.get("description", ""),
                            "source": "Orphanet / MONDO (Monarch Initiative)",
                        })
        _RARE_CACHE[cache_key] = (now, results)
    except Exception as e:
        log.warning("orphanet_query_failed", disease=rare_disease_name, error=str(e))

    return results


# ---------------------------------------------------------------------------
# 2. MONDO Disease Ontology Bridge (100% Free & Open, Zero Keys)
# ---------------------------------------------------------------------------
async def query_mondo_crosswalk(disease_name: str) -> Dict[str, Any]:
    """Resolves MONDO ID and crosswalks to OMIM, ICD-10/11, and Orphanet."""
    cache_key = f"mondo_{disease_name.lower()}"
    now = time.time()
    if cache_key in _RARE_CACHE:
        ts, data = _RARE_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    result = {
        "disease_query": disease_name,
        "mondo_id": None,
        "name": None,
        "cross_references": [],
        "source": "MONDO Disease Ontology",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = f"https://www.ebi.ac.uk/ols4/api/search?q={quote(disease_name)}&ontology=mondo&rows=1"
            r = await client.get(url, headers={"Accept": "application/json"})
            if r.status_code == 200:
                docs = r.json().get("response", {}).get("docs", [])
                if docs:
                    doc = docs[0]
                    result["mondo_id"] = doc.get("obo_id")
                    result["name"] = doc.get("label")
                    xrefs = doc.get("obo_xref", [])
                    if isinstance(xrefs, list):
                        result["cross_references"] = xrefs[:8]
        _RARE_CACHE[cache_key] = (now, result)
    except Exception as e:
        log.warning("mondo_query_failed", disease=disease_name, error=str(e))

    return result
