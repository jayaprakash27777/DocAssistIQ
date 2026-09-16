"""DocAssistIQ — Live Disease Intelligence API Endpoints."""

import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/intelligence", tags=["Live Intelligence"])


class DiseaseLookupRequest(BaseModel):
    disease_name: str
    context: Optional[str] = ""


@router.get("/outbreak-scanner/status", summary="Real-time outbreak scanner status")
async def get_scanner_status():
    """Returns scanner status, last scan time, and active dynamic disease list."""
    try:
        from app.services.live_disease_scanner import outbreak_scanner
        return outbreak_scanner.status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dynamic-kb", summary="Currently loaded dynamic disease profiles")
async def get_dynamic_kb():
    """Returns all dynamically-learned disease profiles from live feeds."""
    try:
        from app.services.live_disease_scanner import get_dynamic_diseases_summary
        return {"status": "ok", "dynamic_diseases": get_dynamic_diseases_summary()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lookup", summary="On-demand disease lookup — any disease, including brand new ones")
async def lookup_disease(req: DiseaseLookupRequest):
    """
    Instantly generates a clinical intelligence profile for ANY disease:
    1. Checks static KB (96+ diseases)
    2. Checks dynamic KB (live-learned)
    3. If not found, generates profile via LLM + WHO/CDC/PubMed/Wikipedia
    Works for diseases announced seconds ago.
    """
    if not req.disease_name or len(req.disease_name.strip()) < 2:
        raise HTTPException(status_code=422, detail="disease_name required")
    try:
        from app.services.live_disease_scanner import on_demand_lookup
        result = await on_demand_lookup(req.disease_name.strip(), req.context or "")
        if not result:
            return {"found": False, "disease": req.disease_name, "message": "Could not generate profile"}
        return {"found": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/live-alerts", summary="Latest WHO/CDC/ProMED outbreak alerts")
async def get_live_alerts():
    """Fetches current outbreak alerts directly from WHO, CDC, and ProMED-mail."""
    try:
        from app.services.intelligence_engine import (
            _fetch_who_outbreak_news, _fetch_cdc_travel_notices, _fetch_promedmail_feed
        )
        who, cdc, promed = await asyncio.gather(
            _fetch_who_outbreak_news(),
            _fetch_cdc_travel_notices(),
            _fetch_promedmail_feed(),
            return_exceptions=True,
        )
        return {
            "who_outbreak_news": who if not isinstance(who, Exception) else "",
            "cdc_travel_health": cdc if not isinstance(cdc, Exception) else "",
            "promed_mail": promed if not isinstance(promed, Exception) else "",
            "sources": ["WHO Disease Outbreak News", "CDC Travel Health Notices", "ProMED-mail"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kb-stats", summary="Knowledge base statistics")
async def get_kb_stats():
    """Returns total disease count (static + dynamic), cluster count, and coverage summary."""
    try:
        from app.services.live_disease_scanner import get_merged_disease_kb, get_all_dynamic_diseases
        from app.services.offline_disease_kb import DISEASE_KB, SYNDROMIC_CLUSTERS
        dynamic = get_all_dynamic_diseases()
        merged = get_merged_disease_kb()
        return {
            "static_diseases": len(DISEASE_KB),
            "dynamic_diseases": len(dynamic),
            "total_diseases": len(merged),
            "syndromic_clusters": len(SYNDROMIC_CLUSTERS),
            "specialties_covered": [
                "Infectious / Tropical", "Cardiovascular", "Neurological",
                "Gastrointestinal / Surgical", "Renal / Urological",
                "Respiratory", "Endocrine / Metabolic", "OB/GYN",
                "Autoimmune / Rheumatic", "Hematological", "Dermatological",
                "Toxicological / Psychiatric",
            ],
            "live_scan_enabled": True,
            "auto_learning": True,
            "data_sources": [
                "WHO Disease Outbreak News", "CDC Travel Health Notices",
                "ProMED-mail", "ECDC", "HealthMap", "PubMed/NCBI",
                "Wikipedia Medical", "ICD-11 Foundation API",
            ],
            "dynamic_entries": [
                {"name": p.get("disease_name", s), "confidence": p.get("_confidence","?"),
                 "severity": p.get("severity","?"), "learned_at": p.get("_learned_at","")}
                for s, p in dynamic.items()
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
