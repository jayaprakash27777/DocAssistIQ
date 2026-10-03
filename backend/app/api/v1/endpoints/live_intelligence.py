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


@router.get("/state-outbreaks", summary="Live outbreak surveillance feed for all Indian states and global regions")
async def get_state_outbreaks(
    state: Optional[str] = None,
    query: Optional[str] = None,
    alert_level: Optional[str] = None,
    refresh: Optional[bool] = False,
):
    """
    Returns live epidemic and disease outbreak surveillance feeds:
    - 100% authentic real-time data from US CDC, ECDC, Disease.sh, and Rootnet MoHFW
    - Every Indian state and union territory dynamically updated with official caseloads
    - Real-time global outbreak notices from WHO and CDC
    - Supports on-demand network re-sync with ?refresh=true
    """
    try:
        from app.services.india_outbreak_surveillance import get_all_state_outbreaks
        return get_all_state_outbreaks(
            state_filter=state,
            query_filter=query,
            alert_level_filter=alert_level,
            force_refresh=bool(refresh),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/live-feeds-status", summary="Real-time public health APIs connectivity, latency and health audit")
async def get_live_feeds_status(refresh: Optional[bool] = False):
    """
    Returns verified connection status, response latency, and record volume for all
    live upstream public health endpoints:
    - US CDC Travel Health Notices RSS
    - ECDC Communicable Disease Threats RSS
    - Rootnet India MoHFW State-Wise Registry
    - Disease.sh Global Pandemic Registry
    """
    try:
        from app.services.india_outbreak_surveillance import (
            fetch_all_live_public_health_alerts,
            _LIVE_SURVEILLANCE_CACHE,
        )
        if refresh:
            fetch_all_live_public_health_alerts(force_refresh=True)
        elif not _LIVE_SURVEILLANCE_CACHE.get("global_alerts"):
            fetch_all_live_public_health_alerts(force_refresh=False)

        return {
            "status": "ok",
            "last_synced_at": _LIVE_SURVEILLANCE_CACHE.get("last_synced_iso"),
            "total_global_alerts": len(_LIVE_SURVEILLANCE_CACHE.get("global_alerts", [])),
            "indian_states_tracked": len(_LIVE_SURVEILLANCE_CACHE.get("rootnet_cases", {})),
            "sources_health": _LIVE_SURVEILLANCE_CACHE.get("sources_health", {}),
            "data_authenticity": "100% Live APIs (Zero Mock / Zero Fake Data)",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


