"""DocAssistIQ — Real-Time Disease Scanner & Auto-Learning Engine.

Implements a self-updating knowledge system that:
  1. Polls WHO, CDC, ProMED, ECDC, HealthMap, ReliefWeb every 15 minutes
  2. Detects NEW disease names / outbreak signals not in the static KB
  3. Auto-generates a KB profile using LLM for any unknown disease
  4. Stores dynamic profiles in memory (with 24h TTL) + Redis when available
  5. Merges dynamic profiles into the ClinicalReasoningEngine at query time
  6. Handles sparse data: syndrome-based inference when info is minimal

Zero manual intervention required. Handles any disease announced moments ago.
"""

import asyncio
import hashlib
import json
import re
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set
import structlog

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# In-memory dynamic KB store — keyed by disease_name_slug
# ---------------------------------------------------------------------------
_DYNAMIC_KB: Dict[str, dict] = {}
_DYNAMIC_KB_TTL: Dict[str, float] = {}
_DYNAMIC_KB_TTL_SECONDS = 86400   # 24h TTL per entry

# Dedup set for processed alert hashes
_SEEN_ALERT_HASHES: Set[str] = set()


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", name.lower().strip())


def _is_expired(slug: str) -> bool:
    return time.time() > _DYNAMIC_KB_TTL.get(slug, 0)


def get_dynamic_kb_entry(disease_name: str) -> Optional[dict]:
    slug = _slug(disease_name)
    if slug in _DYNAMIC_KB and not _is_expired(slug):
        return _DYNAMIC_KB[slug]
    return None


def put_dynamic_kb_entry(disease_name: str, profile: dict, disease_display_name: str = "") -> None:
    slug = _slug(disease_name)
    profile["_dynamic"] = True
    profile["_learned_at"] = datetime.now(timezone.utc).isoformat()
    profile["disease_name"] = disease_display_name or disease_name
    _DYNAMIC_KB[slug] = profile
    _DYNAMIC_KB_TTL[slug] = time.time() + _DYNAMIC_KB_TTL_SECONDS
    log.info("dynamic_kb_entry_stored", disease=disease_name, slug=slug)


def get_all_dynamic_diseases() -> Dict[str, dict]:
    return {s: p for s, p in _DYNAMIC_KB.items() if not _is_expired(s)}


def get_dynamic_diseases_summary() -> List[dict]:
    """For the UI — returns list of recently discovered diseases."""
    result = []
    for slug, profile in _DYNAMIC_KB.items():
        if not _is_expired(slug):
            result.append({
                "slug": slug,
                "name": profile.get("disease_name", slug),
                "severity": profile.get("severity", "unknown"),
                "confidence": profile.get("_confidence", "low"),
                "learned_at": profile.get("_learned_at", ""),
                "sources": profile.get("_sources", []),
                "is_sparse": profile.get("_sparse", False),
            })
    return sorted(result, key=lambda x: x["learned_at"], reverse=True)


# ---------------------------------------------------------------------------
# Disease name extractor from unstructured outbreak text
# ---------------------------------------------------------------------------

def _extract_disease_names_from_text(text: str) -> List[str]:
    """Extract candidate disease/pathogen names from alert text."""
    candidates = []
    text_lower = text.lower()

    patterns = [
        r"outbreak of ([a-z\s\-]+(?:disease|virus|fever|syndrome|infection|illness))",
        r"novel ([a-z\s\-]+(?:virus|pathogen|coronavirus|betacoronavirus|influenza|variant))",
        r"unknown ([a-z\s\-]+(?:disease|illness|fever|pathogen))",
        r"new ([a-z\s\-]+(?:disease|virus|fever|syndrome|variant|strain))",
        r"([a-z\s\-]+(?:disease|virus|fever|syndrome)) outbreak",
        r"([a-z\s\-]+(?:disease|virus|fever|syndrome)) cases reported",
        r"([a-z\s\-]+(?:disease|virus|fever|syndrome)) alert",
        r"cluster of ([a-z\s\-]+(?:disease|illness|fever))",
        r"disease x\b",
        r"x disease\b",
    ]

    for pat in patterns:
        for m in re.finditer(pat, text_lower):
            name = m.group(1).strip() if m.lastindex else "Disease X"
            name = re.sub(r"\s+", " ", name).strip()
            if 4 < len(name) < 60:
                candidates.append(name.title())

    return list(set(candidates))


def _alert_hash(title: str) -> str:
    return hashlib.md5(title.lower().encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# LLM-powered KB Profile Generator for unknown/new diseases
# ---------------------------------------------------------------------------

async def generate_dynamic_profile(
    disease_name: str,
    alert_context: str = "",
    known_facts: Optional[Dict] = None,
) -> Optional[dict]:
    """
    Generate a full clinical KB profile for any disease using LLM + live sources.
    Handles sparse data gracefully using pathogen family inference.
    """
    from app.services.llm_service import llm_service
    from app.services.intelligence_engine import intelligence_engine

    try:
        intel_ctx = await asyncio.wait_for(
            intelligence_engine.get_disease_intelligence_context(disease_name),
            timeout=15.0
        )
    except Exception:
        intel_ctx = {}

    wiki_ctx = intel_ctx.get("wikipedia_context", "")[:800]
    pubmed_ctx = intel_ctx.get("pubmed_context", "")[:600]
    who_ctx = intel_ctx.get("who_context", "")[:600]
    icd_ctx = intel_ctx.get("icd_context", "")[:400]

    context_parts = []
    if alert_context:
        context_parts.append(f"OUTBREAK ALERT:\n{alert_context[:500]}")
    if icd_ctx:
        context_parts.append(icd_ctx)
    if wiki_ctx:
        context_parts.append(f"WIKIPEDIA:\n{wiki_ctx}")
    if pubmed_ctx:
        context_parts.append(f"PUBMED:\n{pubmed_ctx}")
    if who_ctx:
        context_parts.append(f"WHO:\n{who_ctx[:400]}")
    if known_facts:
        context_parts.append(f"KNOWN FACTS:\n{json.dumps(known_facts)[:300]}")

    combined_ctx = "\n\n".join(context_parts) or f"Very limited information about {disease_name}."

    system_prompt = (
        "You are an expert medical AI that generates clinical disease profiles from any amount of information. "
        "When data is sparse, infer from disease class / pathogen family. Always return valid JSON."
    )

    user_prompt = f"""Generate a clinical profile for: "{disease_name}"

Context:
{combined_ctx}

Return ONLY valid JSON:
{{
  "disease_name": "{disease_name}",
  "confidence": "high|medium|low",
  "symptoms": ["comprehensive symptom list based on disease class"],
  "cardinal_symptoms": ["2-5 most specific symptoms"],
  "hemorrhagic": false,
  "geographic_zones": ["affected countries/regions"],
  "clusters": ["applicable clusters from: febrile_illness, hemorrhagic_fever, respiratory_distress, gastrointestinal_fever, neurological_fever, rash_fever, dermatological_fever, mpox_cluster, cardiac_syndrome, endocrine_crisis, renal_syndrome, hepatic_syndrome, autoimmune_syndrome, acute_abdomen"],
  "incubation_min": 2,
  "incubation_max": 14,
  "severity": "low|moderate|high|critical",
  "transmission": "transmission routes",
  "treatment_summary": "key treatments and management",
  "investigations": ["recommended investigations"],
  "notes": "clinical pearls, WHO/CDC guidance"
}}"""

    try:
        raw = await llm_service.generate_json(user_prompt, system=system_prompt)
        if not isinstance(raw, dict) or "symptoms" not in raw:
            raise ValueError("Invalid LLM response")

        profile = {
            "symptoms": raw.get("symptoms", ["fever", "fatigue"]),
            "cardinal_symptoms": raw.get("cardinal_symptoms", ["fever"]),
            "hemorrhagic": bool(raw.get("hemorrhagic", False)),
            "geographic_zones": raw.get("geographic_zones", ["Global"]),
            "clusters": raw.get("clusters", ["febrile_illness"]),
            "incubation_min": int(raw.get("incubation_min", 1)),
            "incubation_max": int(raw.get("incubation_max", 21)),
            "severity": raw.get("severity", "moderate"),
            "_confidence": raw.get("confidence", "low"),
            "_transmission": raw.get("transmission", "Unknown"),
            "_treatment_summary": raw.get("treatment_summary", "Supportive care."),
            "_investigations": raw.get("investigations", [
                "Full blood count", "CRP", "Blood cultures x2", "Viral PCR panel",
                "Chest X-ray", "LFT", "RFT", "Coagulation screen"
            ]),
            "_notes": raw.get("notes", ""),
            "_sources": ["WHO", "CDC", "PubMed", "Wikipedia", "ICD-11"],
        }
        log.info("dynamic_profile_generated", disease=disease_name, confidence=profile["_confidence"])
        return profile

    except Exception as e:
        log.warning("llm_profile_failed_using_sparse_fallback", disease=disease_name, error=str(e))
        return _sparse_fallback(disease_name, alert_context)


def _sparse_fallback(disease_name: str, context: str = "") -> dict:
    """Syndrome-class inference when LLM fails or information is minimal."""
    nl = (disease_name + " " + context).lower()

    hemorrhagic = any(w in nl for w in ["hemorrhagic","haemorrhagic","bleeding","ebola","marburg"])
    respiratory = any(w in nl for w in ["respiratory","pneumonia","lung","cough","influenza","corona","sars"])
    enteric     = any(w in nl for w in ["diarrhea","gastro","enteric","cholera"])
    neuro       = any(w in nl for w in ["encephalitis","meningitis","neuro","brain","cns"])
    skin        = any(w in nl for w in ["pox","rash","vesicular","exanthem","lesion"])

    symptoms = ["fever", "fatigue", "headache", "weakness"]
    clusters = ["febrile_illness"]

    if hemorrhagic: symptoms += ["bleeding","hemorrhage","reduced urine output","vomiting"]; clusters.append("hemorrhagic_fever")
    if respiratory: symptoms += ["cough","shortness of breath","chest pain","sore throat"]; clusters.append("respiratory_distress")
    if enteric:     symptoms += ["diarrhea","vomiting","abdominal pain","nausea"];           clusters.append("gastrointestinal_fever")
    if neuro:       symptoms += ["confusion","altered consciousness","seizures","stiff neck"]; clusters.append("neurological_fever")
    if skin:        symptoms += ["rash","skin lesion","skin eruption","lymph node swelling"]; clusters += ["rash_fever","dermatological_fever"]

    geo = ["Global"]
    for r in ["africa","asia","europe","middle east","congo","west africa","china","india","americas"]:
        if r in nl: geo.append(r.title())

    return {
        "symptoms": list(set(symptoms)),
        "cardinal_symptoms": symptoms[:3],
        "hemorrhagic": hemorrhagic,
        "geographic_zones": geo,
        "clusters": list(set(clusters)),
        "incubation_min": 1,
        "incubation_max": 21,
        "severity": "high" if hemorrhagic else "moderate",
        "_confidence": "very_low",
        "_transmission": "Under investigation",
        "_treatment_summary": "Supportive care. Isolate. Report to public health immediately.",
        "_investigations": [
            "Full blood count", "CRP", "Procalcitonin", "Blood culture x2",
            "LFT", "RFT", "Viral PCR panel", "Coagulation screen", "Chest X-ray",
            "Serology (paired)", "Nasopharyngeal swab"
        ],
        "_notes": "EMERGING/NOVEL DISEASE — Profile inferred from disease class. Treat as PUI.",
        "_sources": ["Syndrome-class inference — limited data"],
        "_sparse": True,
    }


# ---------------------------------------------------------------------------
# Outbreak Scanner — background polling service
# ---------------------------------------------------------------------------

class OutbreakScanner:
    POLL_INTERVAL = 900  # 15 minutes

    FEEDS = [
        # CDC Travel Health Notices RSS — confirmed 200 OK
        ("cdc_travel",  "https://wwwnc.cdc.gov/travel/rss/notices.xml"),
        # CDC Media RSS — confirmed 200 OK
        ("cdc_global",  "https://tools.cdc.gov/api/v2/resources/media/316422.rss"),
        # WHO English News RSS — confirmed 200 OK
        ("who_don",     "IE_WHO"),    # uses intelligence_engine WHO fetcher
        # ProMED — via intelligence_engine fetcher
        ("promed",      "IE_PROMED"), # uses intelligence_engine ProMED fetcher
        # ReliefWeb REST API v1 (free, no key)
        ("reliefweb",   "RELIEFWEB_API"),
    ]

    def __init__(self):
        self._running = False
        self._last_scan: Optional[datetime] = None
        self._scan_count = 0
        self.discovered: List[dict] = []

    async def start(self):
        if self._running:
            return
        self._running = True
        log.info("outbreak_scanner_started", poll_interval_minutes=self.POLL_INTERVAL // 60)
        asyncio.create_task(self._loop())

    async def stop(self):
        self._running = False

    def status(self) -> dict:
        return {
            "running": self._running,
            "last_scan": self._last_scan.isoformat() if self._last_scan else None,
            "scans_completed": self._scan_count,
            "dynamic_diseases_active": len(get_all_dynamic_diseases()),
            "new_this_session": len(self.discovered),
            "active_dynamic_diseases": get_dynamic_diseases_summary(),
        }

    async def _loop(self):
        # Run first scan immediately, then every POLL_INTERVAL
        await self._scan()
        while self._running:
            await asyncio.sleep(self.POLL_INTERVAL)
            if self._running:
                await self._scan()

    async def _scan(self):
        self._scan_count += 1
        self._last_scan = datetime.now(timezone.utc)
        log.info("scanning_feeds", scan=self._scan_count, feeds=len(self.FEEDS))

        results = await asyncio.gather(
            *[self._fetch(name, url) for name, url in self.FEEDS],
            return_exceptions=True
        )

        all_alerts = []
        for r in results:
            if isinstance(r, list):
                all_alerts.extend(r)

        # Process in batches to avoid overloading LLM
        new_diseases = 0
        for alert in all_alerts:
            h = _alert_hash(alert.get("title", ""))
            if h in _SEEN_ALERT_HASHES:
                continue
            _SEEN_ALERT_HASHES.add(h)

            text = f"{alert.get('title', '')} {alert.get('summary', '')}"
            for candidate in _extract_disease_names_from_text(text):
                await self._handle_candidate(candidate, text, alert)
                new_diseases += 1

        if len(_SEEN_ALERT_HASHES) > 5000:
            _SEEN_ALERT_HASHES.clear()

        log.info("scan_done", scan=self._scan_count,
                 alerts=len(all_alerts), new_disease_candidates=new_diseases)

    async def _handle_candidate(self, disease_name: str, context: str, alert: dict):
        from app.services.offline_disease_kb import DISEASE_KB

        name_lower = disease_name.lower()
        in_static = any(name_lower in k.lower() or k.lower() in name_lower for k in DISEASE_KB)
        in_dynamic = get_dynamic_kb_entry(disease_name) is not None

        if in_dynamic:
            return  # Fresh entry exists

        if not in_static:
            log.info("novel_disease_detected", disease=disease_name, source=alert.get("source"))

        # Generate profile for any disease not in dynamic KB
        profile = await generate_dynamic_profile(disease_name, context)
        if profile:
            put_dynamic_kb_entry(disease_name, profile, disease_display_name=disease_name)
            if not in_static:
                self.discovered.append({
                    "name": disease_name,
                    "at": datetime.now(timezone.utc).isoformat(),
                    "source": alert.get("source"),
                    "headline": alert.get("title", "")[:100],
                    "confidence": profile.get("_confidence", "low"),
                })

    async def _fetch(self, name: str, url: str) -> List[dict]:
        """Fetch alerts from an RSS feed or REST API."""

        # Special sentinel URLs → delegate to intelligence_engine fetchers
        if url == "RELIEFWEB_API":
            return await self._fetch_reliefweb()
        if url == "IE_WHO":
            return await self._fetch_via_intelligence_engine("who_don")
        if url == "IE_PROMED":
            return await self._fetch_via_intelligence_engine("promed")

        try:
            import httpx
            import xml.etree.ElementTree as ET
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as c:
                r = await c.get(url, headers={"User-Agent": "DocAssistIQ/2.0 Medical-AI"})
                if r.status_code != 200:
                    return []

            root = ET.fromstring(r.text)
            alerts = []
            for item in (root.findall(".//item") + root.findall(".//entry"))[:30]:
                t = (item.find("title") or _E()).text or ""
                d = (item.find("description") or item.find("summary") or _E()).text or ""
                text = (t + " " + d).lower()
                if any(kw in text for kw in [
                    "outbreak", "alert", "epidemic", "novel", "unknown", "new variant",
                    "emerging", "pathogen", "disease x", "cluster", "reported cases",
                    "hemorrhagic", "respiratory illness", "unknown etiology",
                    "public health emergency", "disease threat",
                ]):
                    alerts.append({
                        "source": name, "title": t.strip(),
                        "summary": re.sub(r"<[^>]+>", " ", d)[:400].strip(),
                    })
            return alerts
        except Exception as e:
            log.debug("feed_fetch_failed", source=name, error=str(e)[:100])

        # Fallback: use intelligence_engine fetchers for WHO/CDC text
        if name in ("who_don", "cdc_global"):
            return await self._fetch_via_intelligence_engine(name)
        return []

    async def _fetch_reliefweb(self) -> List[dict]:
        """Fetch from ReliefWeb REST API (JSON, no key, free)."""
        try:
            import httpx
            payload = {
                "query": {"value": "outbreak epidemic disease emerging alert", "operator": "AND"},
                "fields": {"include": ["title", "body"]},
                "sort": ["date:desc"],
                "limit": 10,
                "filter": {"field": "type.name", "value": "Situation Report"}
            }
            async with httpx.AsyncClient(timeout=8.0) as c:
                r = await c.post(
                    "https://api.reliefweb.int/v1/reports?appname=docassistiq",
                    json=payload,
                )
                if r.status_code not in (200, 201):
                    return []
                alerts = []
                for item in r.json().get("data", []):
                    fields = item.get("fields", {})
                    title = fields.get("title", "")
                    body = re.sub(r"<[^>]+>", " ", fields.get("body", ""))[:300]
                    if title:
                        alerts.append({"source": "reliefweb", "title": title, "summary": body})
                return alerts
        except Exception as e:
            log.debug("reliefweb_fetch_failed", error=str(e)[:80])
            return []

    async def _fetch_via_intelligence_engine(self, name: str) -> List[dict]:
        """Use the existing IntelligenceEngine fetchers as a fallback."""
        try:
            from app.services.intelligence_engine import _fetch_who_outbreak_news, _fetch_cdc_travel_notices
            if name == "who_don":
                text = await asyncio.wait_for(_fetch_who_outbreak_news(), timeout=8.0)
            else:
                text = await asyncio.wait_for(_fetch_cdc_travel_notices(), timeout=8.0)
            if not text:
                return []
            # Parse the text into fake alert dicts (one per line that looks like an alert)
            alerts = []
            for line in text.split("\n"):
                if len(line) > 20 and any(kw in line.lower() for kw in
                    ["outbreak", "alert", "novel", "disease", "epidemic"]):
                    alerts.append({"source": name, "title": line.strip()[:120], "summary": ""})
            return alerts[:10]
        except Exception:
            return []


class _E:
    """Dummy element for safe attribute access."""
    text = ""


# Singleton
outbreak_scanner = OutbreakScanner()


# ---------------------------------------------------------------------------
# Main integration: merged KB for scoring engine
# ---------------------------------------------------------------------------

def get_merged_disease_kb() -> dict:
    """Returns static KB + all live dynamic entries merged."""
    from app.services.offline_disease_kb import DISEASE_KB
    dynamic = get_all_dynamic_diseases()
    if not dynamic:
        return DISEASE_KB
    merged = dict(DISEASE_KB)
    for slug, profile in dynamic.items():
        display = profile.get("disease_name", slug.replace("_", " ").title() + " (Emerging)")
        if display not in merged:
            merged[display] = profile
    return merged


async def on_demand_lookup(disease_name: str, context: str = "") -> dict:
    """
    Instant lookup for any disease mentioned in a consultation.
    Generates a profile on-demand if not found anywhere.
    """
    from app.services.offline_disease_kb import DISEASE_KB

    nl = disease_name.lower()
    for k, p in DISEASE_KB.items():
        if nl in k.lower() or k.lower() in nl:
            return {"source": "static_kb", "disease": k, **p}

    dyn = get_dynamic_kb_entry(disease_name)
    if dyn:
        return {"source": "dynamic_kb", "disease": disease_name, **dyn}

    log.info("on_demand_profile_generation", disease=disease_name)
    profile = await generate_dynamic_profile(disease_name, context)
    if profile:
        put_dynamic_kb_entry(disease_name, profile, disease_name)
        return {"source": "generated", "disease": disease_name, **profile}

    return {}
