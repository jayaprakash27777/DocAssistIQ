"""DocAssistIQ — Extended Free Knowledge Sources (God-Level AI Upgrade).

8 additional free, no-key-required knowledge APIs:
1. ECDC (European Centre for Disease Prevention and Control)
2. ReliefWeb — humanitarian health crisis reports
3. OpenDiseaseData (disease.sh) — real-time epidemiology
4. MedlinePlus (NIH) — disease information
5. Healthmap RSS — live disease alerts
6. WHO AFRO — Africa-specific health alerts
7. Global Health Observatory (GHO) API — WHO statistics
8. OpenFDA — drug adverse events / outbreak reports

All free, no API keys, no rate limits (reasonable use).
All calls are fire-and-forget with 3s timeout — failures are silent.
"""

import asyncio
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from datetime import datetime, timezone
import structlog

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Source fetchers — each returns a string summary or empty string on failure
# ---------------------------------------------------------------------------

async def fetch_ecdc_surveillance(country_keywords: List[str]) -> str:
    """ECDC Weekly Epidemiological Report RSS — European disease surveillance."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(
                "https://www.ecdc.europa.eu/en/publications-data/rss",
                headers={"Accept": "application/rss+xml, application/xml, text/xml"},
                follow_redirects=True,
            )
            if r.status_code != 200:
                return ""
            root = ET.fromstring(r.text)
            items = []
            for item in root.findall(".//item")[:15]:
                title = (item.find("title") or _empty()).text or ""
                desc = (item.find("description") or _empty()).text or ""
                combined = f"{title} {desc}".lower()
                if any(kw.lower() in combined for kw in country_keywords + ["outbreak", "epidemic", "alert", "hemorrhagic"]):
                    items.append(f"[ECDC] {title.strip()}: {desc.strip()[:150]}")
            return "\n".join(items[:5]) if items else ""
    except Exception as e:
        log.debug("ecdc_fetch_failed", error=str(e))
        return ""


async def fetch_reliefweb_health(country_keywords: List[str]) -> str:
    """ReliefWeb API — Humanitarian health crisis reports (free, no key)."""
    try:
        import httpx
        search_terms = " OR ".join(country_keywords[:3]) if country_keywords else "outbreak"
        url = (
            f"https://api.reliefweb.int/v1/reports"
            f"?appname=docassistiq&query[value]={search_terms}+health+outbreak"
            f"&fields[include][]=title&fields[include][]=body-html"
            f"&sort[]=date:desc&limit=5"
            f"&filter[field]=primary_country.name&filter[value]=&filter[operator]=and"
        )
        async with httpx.AsyncClient(timeout=4.0) as client:
            r = await client.get(url)
            if r.status_code != 200:
                return ""
            data = r.json()
            items = []
            for report in data.get("data", [])[:5]:
                fields = report.get("fields", {})
                title = fields.get("title", "")
                body = fields.get("body-html", "")
                # Strip HTML
                body_clean = re.sub(r"<[^>]+>", " ", body)[:200]
                items.append(f"[ReliefWeb] {title}: {body_clean}")
            return "\n".join(items) if items else ""
    except Exception as e:
        log.debug("reliefweb_fetch_failed", error=str(e))
        return ""


async def fetch_open_disease_data(disease_name: str) -> str:
    """
    disease.sh API — Free, open, real-time disease/epidemiology data.
    Good for COVID-19 stats. Also has general information.
    """
    try:
        import httpx
        # Try to fetch country-level outbreak statistics
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(
                f"https://disease.sh/v3/covid-19/all",
                headers={"Accept": "application/json"},
            )
            if r.status_code == 200:
                data = r.json()
                if "covid" in disease_name.lower():
                    return (
                        f"[OpenDiseaseData] Global COVID-19: "
                        f"Active cases: {data.get('active', 'N/A'):,}, "
                        f"Deaths today: {data.get('todayDeaths', 'N/A'):,}"
                    )
            return ""
    except Exception as e:
        log.debug("opendiseasedata_fetch_failed", error=str(e))
        return ""


async def fetch_medlineplus(disease_name: str) -> str:
    """
    MedlinePlus Web Service (NIH) — Free, no key.
    Returns NIH's official description of a disease.
    """
    try:
        import httpx
        from urllib.parse import quote
        url = (
            f"https://wsearch.nlm.nih.gov/ws/query"
            f"?db=healthTopics&term={quote(disease_name)}&retmax=1"
        )
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(url)
            if r.status_code != 200:
                return ""
            root = ET.fromstring(r.text)
            # Extract FullSummary
            summaries = root.findall(".//content[@name='FullSummary']")
            if summaries and summaries[0].text:
                clean = re.sub(r"<[^>]+>", " ", summaries[0].text).strip()
                return f"[MedlinePlus/NIH] {disease_name}: {clean[:400]}"
            # Fallback: extract snippet
            snippets = root.findall(".//content[@name='snippet']")
            if snippets and snippets[0].text:
                clean = re.sub(r"<[^>]+>", " ", snippets[0].text).strip()
                return f"[MedlinePlus/NIH] {disease_name}: {clean[:300]}"
            return ""
    except Exception as e:
        log.debug("medlineplus_fetch_failed", error=str(e))
        return ""


async def fetch_who_afro(country_keywords: List[str]) -> str:
    """WHO AFRO (Africa Regional Office) RSS feed — Africa-specific health alerts."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(
                "https://www.afro.who.int/rss.xml",
                follow_redirects=True,
            )
            if r.status_code != 200:
                return ""
            root = ET.fromstring(r.text)
            items = []
            for item in root.findall(".//item")[:15]:
                title = (item.find("title") or _empty()).text or ""
                desc = (item.find("description") or _empty()).text or ""
                combined = f"{title} {desc}".lower()
                if any(kw.lower() in combined for kw in country_keywords + ["outbreak", "disease", "fever", "alert", "ebola", "hemorrhagic"]):
                    items.append(f"[WHO-AFRO] {title.strip()}: {desc.strip()[:150]}")
            return "\n".join(items[:5]) if items else ""
    except Exception as e:
        log.debug("who_afro_fetch_failed", error=str(e))
        return ""


async def fetch_gho_api(indicator: str = "NCD_HYP_PREVALENCE_A") -> str:
    """
    WHO Global Health Observatory (GHO) API — free, no key.
    Returns WHO statistical context on health indicators.
    """
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(
                f"https://ghoapi.azureedge.net/api/{indicator}?$top=3",
                headers={"Accept": "application/json"},
            )
            if r.status_code == 200:
                data = r.json()
                values = data.get("value", [])
                if values:
                    return f"[WHO-GHO] {indicator}: {len(values)} data points available"
            return ""
    except Exception as e:
        log.debug("gho_api_fetch_failed", error=str(e))
        return ""


async def fetch_openfda_adverse_events(drug_name: str) -> str:
    """
    OpenFDA Drug Adverse Events API — completely free, no key.
    Useful for drug safety context.
    """
    try:
        import httpx
        from urllib.parse import quote
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(
                f"https://api.fda.gov/drug/event.json"
                f"?search=patient.drug.medicinalproduct:{quote(drug_name)}"
                f"&limit=1"
            )
            if r.status_code == 200:
                data = r.json()
                total = data.get("meta", {}).get("results", {}).get("total", 0)
                return f"[OpenFDA] Adverse event reports for {drug_name}: {total:,} total reports"
            return ""
    except Exception as e:
        log.debug("openfda_fetch_failed", error=str(e))
        return ""


async def fetch_healthmap_alerts(country_keywords: List[str]) -> str:
    """
    Healthmap / ProMED RSS — global disease alert network.
    Alternative to main ProMED feed for additional redundancy.
    """
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(
                "https://www.healthmap.org/promed/rss/",
                follow_redirects=True,
            )
            if r.status_code != 200:
                # Try ProMED direct
                r = await client.get("https://promedmail.org/promed-posts/feed/")
            if r.status_code != 200:
                return ""
            root = ET.fromstring(r.text)
            items = []
            for item in root.findall(".//item")[:20]:
                title = (item.find("title") or _empty()).text or ""
                desc = (item.find("description") or _empty()).text or ""
                combined = f"{title} {desc}".lower()
                if any(kw.lower() in combined for kw in country_keywords + ["hemorrhagic", "ebola", "outbreak"]):
                    items.append(f"[Healthmap/ProMED] {title.strip()}: {desc.strip()[:150]}")
            return "\n".join(items[:4]) if items else ""
    except Exception as e:
        log.debug("healthmap_fetch_failed", error=str(e))
        return ""


# ---------------------------------------------------------------------------
# Aggregated Fetch
# ---------------------------------------------------------------------------

async def fetch_all_free_sources(
    disease_name: str,
    country_keywords: List[str],
    timeout_sec: float = 5.0,
) -> Dict[str, str]:
    """
    Fetch all 8 free knowledge sources in parallel.
    Returns dict of source_name -> content (empty string if failed/irrelevant).
    Silent on all failures.
    """
    tasks = {
        "ecdc": fetch_ecdc_surveillance(country_keywords),
        "reliefweb": fetch_reliefweb_health(country_keywords),
        "opendiseasedata": fetch_open_disease_data(disease_name),
        "medlineplus": fetch_medlineplus(disease_name),
        "who_afro": fetch_who_afro(country_keywords),
        "gho": fetch_gho_api(),
        "openfda": asyncio.sleep(0, result=""),  # Only for drug queries
        "healthmap": fetch_healthmap_alerts(country_keywords),
    }

    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    output = {}
    for key, result in zip(tasks.keys(), results):
        if isinstance(result, Exception) or not result:
            output[key] = ""
        else:
            output[key] = str(result)

    return output


def build_free_sources_context(results: Dict[str, str], max_chars: int = 800) -> str:
    """
    Combines all free source results into a single context string (capped at max_chars).
    Prioritizes outbreak-relevant sources.
    """
    priority_order = ["who_afro", "healthmap", "ecdc", "medlineplus", "reliefweb", "opendiseasedata", "gho"]
    parts = []
    total = 0
    for key in priority_order:
        val = results.get(key, "")
        if val and total < max_chars:
            parts.append(val[:max_chars - total])
            total += len(val)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

class _empty:
    """Minimal placeholder for missing XML elements."""
    text = ""
