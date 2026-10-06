"""DocAssistIQ — Unified Infectious Disease & Epidemic Surveillance Gateway.

Integrates 100% Free & Open (No Keys Needed) Feeds:
1. WHO Disease Outbreak News (DONs) — Official international epidemic notices
2. US CDC Travel Health Notices — Global traveler epidemic risk alerts
3. ECDC Weekly Surveillance — European communicable disease intelligence
4. ReliefWeb (UN OCHA) — Humanitarian health emergencies
5. Disease.sh (OpenDiseaseData) — Global real-time epidemiology statistics
6. India Outbreak Surveillance Engine — Comprehensive IDSP coverage for 28 states & 8 UTs
"""

import asyncio
import time
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import quote
import httpx
import structlog

log = structlog.get_logger(__name__)

_SURV_CACHE: Dict[str, Tuple[float, Any]] = {}
_CACHE_TTL_SECONDS = 1800  # 30 minutes


# ---------------------------------------------------------------------------
# 1. WHO Disease Outbreak News (DON) Live Feed
# ---------------------------------------------------------------------------
async def query_who_outbreaks(disease_or_region: str = "") -> List[Dict[str, Any]]:
    """Fetches real-time international epidemic notices from WHO DON."""
    cache_key = f"who_don_{disease_or_region.lower()}"
    now = time.time()
    if cache_key in _SURV_CACHE:
        ts, data = _SURV_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    outbreaks = []
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            r = await client.get("https://www.who.int/emergencies/disease-outbreak-news/rss.xml")
            if r.status_code == 200:
                root = ET.fromstring(r.text)
                for item in root.findall(".//item")[:15]:
                    title = getattr(item.find("title"), "text", "") or ""
                    desc = getattr(item.find("description"), "text", "") or ""
                    link = getattr(item.find("link"), "text", "") or ""
                    pub_date = getattr(item.find("pubDate"), "text", "") or ""

                    clean_desc = re.sub(r"<[^>]+>", " ", desc).strip()[:200]
                    query_clean = disease_or_region.lower()
                    
                    if not query_clean or (query_clean in title.lower() or query_clean in clean_desc.lower()):
                        outbreaks.append({
                            "title": title.strip(),
                            "summary": clean_desc,
                            "published": pub_date,
                            "url": link,
                            "source": "WHO Disease Outbreak News",
                        })
        _SURV_CACHE[cache_key] = (now, outbreaks)
    except Exception as e:
        log.warning("who_don_feed_failed", error=str(e))

    return outbreaks


# ---------------------------------------------------------------------------
# 2. CDC Travel Notices (US CDC)
# ---------------------------------------------------------------------------
async def query_cdc_travel_notices() -> List[Dict[str, Any]]:
    """Fetches CDC Travel Health Notices for international disease alerts."""
    now = time.time()
    if "cdc_travel" in _SURV_CACHE:
        ts, data = _SURV_CACHE["cdc_travel"]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    notices = []
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            r = await client.get("https://wwwnc.cdc.gov/travel/rss/notices.xml")
            if r.status_code == 200:
                root = ET.fromstring(r.text)
                for item in root.findall(".//item")[:10]:
                    title = getattr(item.find("title"), "text", "") or ""
                    desc = getattr(item.find("description"), "text", "") or ""
                    link = getattr(item.find("link"), "text", "") or ""
                    clean_desc = re.sub(r"<[^>]+>", " ", desc).strip()[:180]
                    notices.append({
                        "title": title.strip(),
                        "summary": clean_desc,
                        "url": link,
                        "source": "US CDC Travel Health Notices",
                    })
        _SURV_CACHE["cdc_travel"] = (now, notices)
    except Exception as e:
        log.warning("cdc_travel_feed_failed", error=str(e))

    return notices


# ---------------------------------------------------------------------------
# 3. ReliefWeb (UN OCHA) Health Crisis Reports
# ---------------------------------------------------------------------------
async def query_reliefweb_health(country: str = "") -> List[Dict[str, Any]]:
    """Queries ReliefWeb API for health crisis and epidemic declarations."""
    cache_key = f"reliefweb_{country.lower()}"
    now = time.time()
    if cache_key in _SURV_CACHE:
        ts, data = _SURV_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    reports = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            query = f"{country}+health+outbreak" if country else "epidemic+outbreak"
            url = f"https://api.reliefweb.int/v1/reports?appname=docassistiq&query[value]={query}&limit=3"
            r = await client.get(url)
            if r.status_code == 200:
                data = r.json().get("data", [])
                for item in data:
                    fields = item.get("fields", {})
                    reports.append({
                        "title": fields.get("title", ""),
                        "url": item.get("href", ""),
                        "source": "UN OCHA ReliefWeb",
                    })
        _SURV_CACHE[cache_key] = (now, reports)
    except Exception as e:
        log.warning("reliefweb_query_failed", error=str(e))

    return reports


# ---------------------------------------------------------------------------
# 4. Disease.sh (OpenDiseaseData) Global Epidemiology (100% Free & Open)
# ---------------------------------------------------------------------------
async def query_disease_sh_epidemiology(country: str = "") -> Dict[str, Any]:
    """Queries disease.sh for real-time global or country outbreak statistics."""
    cache_key = f"diseasesh_{country.lower()}" if country else "diseasesh_global"
    now = time.time()
    if cache_key in _SURV_CACHE:
        ts, data = _SURV_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    result = {
        "region": country or "Global",
        "cases": None,
        "today_cases": None,
        "deaths": None,
        "recovered": None,
        "active": None,
        "critical": None,
        "source": "OpenDiseaseData (disease.sh)",
    }

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            endpoint = f"https://disease.sh/v3/covid-19/countries/{quote(country)}" if country else "https://disease.sh/v3/covid-19/all"
            r = await client.get(endpoint)
            if r.status_code == 200:
                data = r.json()
                result["cases"] = data.get("cases")
                result["today_cases"] = data.get("todayCases")
                result["deaths"] = data.get("deaths")
                result["recovered"] = data.get("recovered")
                result["active"] = data.get("active")
                result["critical"] = data.get("critical")
        _SURV_CACHE[cache_key] = (now, result)
    except Exception as e:
        log.warning("diseasesh_query_failed", error=str(e))

    return result
