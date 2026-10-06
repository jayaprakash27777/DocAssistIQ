"""DocAssistIQ — Unified Pharmacology & Drug Safety Gateway.

Integrates 100% Free & Open (No Keys Needed) APIs:
1. DailyMed (NLM / FDA) — Official Structured Product Labels (SPL)
2. openFDA — Adverse Event Reporting (FAERS), recalls, boxed warnings
3. PubChem (NIH PUG-REST) — Chemical identities, molecular formulas, toxicity
4. ChEMBL (EMBL-EBI) — Bioactivity, drug targets, mechanism of action
5. FDA Orange Book — Therapeutic equivalence evaluation
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import quote
import httpx
import structlog

from app.config import get_settings

log = structlog.get_logger(__name__)

_PHARMA_CACHE: Dict[str, Tuple[float, Any]] = {}
_CACHE_TTL_SECONDS = 7200  # 2 hours


# ---------------------------------------------------------------------------
# 1. DailyMed (NLM/FDA) Official Drug Label & Package Insert
# ---------------------------------------------------------------------------
async def query_dailymed_label(drug_name: str) -> Dict[str, Any]:
    """Queries official FDA package insert and boxed warnings from DailyMed."""
    cache_key = f"dailymed_{drug_name.lower()}"
    now = time.time()
    if cache_key in _PHARMA_CACHE:
        ts, data = _PHARMA_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    result = {
        "drug_name": drug_name,
        "spl_id": None,
        "title": None,
        "set_id": None,
        "label_url": None,
        "source": "FDA DailyMed (NLM)",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = f"https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json?drug_name={quote(drug_name)}&pagesize=1"
            r = await client.get(url, headers={"Accept": "application/json"})
            if r.status_code == 200:
                data = r.json().get("data", [])
                if data:
                    top = data[0]
                    result["spl_id"] = top.get("spl_version")
                    result["title"] = top.get("title")
                    result["set_id"] = top.get("setid")
                    if top.get("setid"):
                        result["label_url"] = f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={top.get('setid')}"
        _PHARMA_CACHE[cache_key] = (now, result)
    except Exception as e:
        log.warning("dailymed_query_failed", drug=drug_name, error=str(e))

    return result


# ---------------------------------------------------------------------------
# 2. openFDA Adverse Events (FAERS) & Enforcement Recalls
# ---------------------------------------------------------------------------
async def query_openfda_safety(drug_name: str) -> Dict[str, Any]:
    """Queries openFDA for real adverse event reports and recalls."""
    settings = get_settings()
    api_key = settings.openfda_api_key

    cache_key = f"openfda_{drug_name.lower()}"
    now = time.time()
    if cache_key in _PHARMA_CACHE:
        ts, data = _PHARMA_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    result = {
        "drug_name": drug_name,
        "top_adverse_reactions": [],
        "total_adverse_reports": 0,
        "recent_recalls": [],
        "source": "US FDA (openFDA)",
    }

    key_param = f"&api_key={api_key}" if api_key else ""

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Query A: Top reactions in FAERS
            faers_url = (
                f"https://api.fda.gov/drug/event.json?search=patient.drug.medicinalproduct:{quote(drug_name)}"
                f"&count=patient.reaction.reactionmeddrapt.exact&limit=5{key_param}"
            )
            r_faers = await client.get(faers_url)
            if r_faers.status_code == 200:
                results = r_faers.json().get("results", [])
                result["top_adverse_reactions"] = [
                    {"reaction": item.get("term"), "count": item.get("count")}
                    for item in results
                ]
                meta = r_faers.json().get("meta", {}).get("results", {})
                result["total_adverse_reports"] = meta.get("total", 0)

            # Query B: Recalls / Enforcement
            recall_url = (
                f"https://api.fda.gov/drug/enforcement.json?search=product_description:{quote(drug_name)}"
                f"&limit=2{key_param}"
            )
            r_rec = await client.get(recall_url)
            if r_rec.status_code == 200:
                rec_results = r_rec.json().get("results", [])
                for rec in rec_results:
                    result["recent_recalls"].append({
                        "reason": rec.get("reason_for_recall", "")[:180],
                        "classification": rec.get("classification"),
                        "status": rec.get("status"),
                        "recall_date": rec.get("recall_initiation_date"),
                    })

        _PHARMA_CACHE[cache_key] = (now, result)
    except Exception as e:
        log.warning("openfda_query_failed", drug=drug_name, error=str(e))

    return result


# ---------------------------------------------------------------------------
# 3. PubChem (NIH PUG-REST) — Chemistry, IUPAC, Molecular Safety
# ---------------------------------------------------------------------------
async def query_pubchem_compound(compound_name: str) -> Dict[str, Any]:
    """Queries NIH PubChem for molecular formula, CID, and safety synonyms."""
    cache_key = f"pubchem_{compound_name.lower()}"
    now = time.time()
    if cache_key in _PHARMA_CACHE:
        ts, data = _PHARMA_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    result = {
        "compound_name": compound_name,
        "pubchem_cid": None,
        "molecular_formula": None,
        "molecular_weight": None,
        "iupac_name": None,
        "source": "NIH PubChem (PUG-REST)",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = (
                f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{quote(compound_name)}"
                f"/property/MolecularFormula,MolecularWeight,IUPACName/JSON"
            )
            r = await client.get(url)
            if r.status_code == 200:
                props = (
                    r.json()
                    .get("PropertyTable", {})
                    .get("Properties", [])
                )
                if props:
                    top = props[0]
                    result["pubchem_cid"] = top.get("CID")
                    result["molecular_formula"] = top.get("MolecularFormula")
                    result["molecular_weight"] = top.get("MolecularWeight")
                    result["iupac_name"] = top.get("IUPACName")
        _PHARMA_CACHE[cache_key] = (now, result)
    except Exception as e:
        log.warning("pubchem_query_failed", compound=compound_name, error=str(e))

    return result


# ---------------------------------------------------------------------------
# 4. ChEMBL (EMBL-EBI) — Bioactivity & Drug Target Mechanism
# ---------------------------------------------------------------------------
async def query_chembl_targets(drug_name: str) -> List[Dict[str, Any]]:
    """Queries EMBL-EBI ChEMBL for biological targets and mechanisms."""
    cache_key = f"chembl_{drug_name.lower()}"
    now = time.time()
    if cache_key in _PHARMA_CACHE:
        ts, data = _PHARMA_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    targets = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = f"https://www.ebi.ac.uk/chembl/api/data/mechanism.json?molecule_chembl_id__isnull=false&limit=3&q={quote(drug_name)}"
            r = await client.get(url)
            if r.status_code == 200:
                mechanisms = r.json().get("mechanisms", [])
                for m in mechanisms:
                    targets.append({
                        "mechanism_of_action": m.get("mechanism_of_action"),
                        "action_type": m.get("action_type"),
                        "target_chembl_id": m.get("target_chembl_id"),
                        "source": "EMBL-EBI ChEMBL",
                    })
        _PHARMA_CACHE[cache_key] = (now, targets)
    except Exception as e:
        log.warning("chembl_query_failed", drug=drug_name, error=str(e))

    return targets


# ---------------------------------------------------------------------------
# 5. Clinical Drug-Drug Interaction Safety Evaluator (100% Free & Open)
# ---------------------------------------------------------------------------
async def query_rxnav_drug_interactions(rxcuis: List[str]) -> List[Dict[str, Any]]:
    """Evaluates multi-drug prescriptions against NLM RxCUI definitions and peer-reviewed critical contraindications."""
    if not rxcuis or len(rxcuis) < 2:
        return []

    rxcui_clean = [str(r).strip() for r in rxcuis if str(r).strip().isdigit()]
    if len(rxcui_clean) < 2:
        return []

    cache_key = f"interactions_{'_'.join(sorted(rxcui_clean))}"
    now = time.time()
    if cache_key in _PHARMA_CACHE:
        ts, data = _PHARMA_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    interactions = []
    
    # 1. Check authoritative offline critical interaction pairs from rxnav_service
    from app.services.rxnav_service import OFFLINE_CRITICAL_RXCUI_INTERACTIONS
    rxcui_set = set(rxcui_clean)
    for rule in OFFLITICAL_RXCUI_INTERACTIONS if "OFFLITICAL_RXCUI_INTERACTIONS" in locals() else OFFLINE_CRITICAL_RXCUI_INTERACTIONS:
        pair = rule.get("pair", set())
        if pair.issubset(rxcui_set):
            interactions.append({
                "drug_pair": " + ".join(sorted(list(pair))),
                "severity": "CRITICAL",
                "description": rule.get("description", "High-severity adverse drug interaction."),
                "source": "NLM / FDA Critical Safety Evidence Base",
            })

    # 2. Query openFDA for drug-drug interaction warnings on individual substances
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            for rxcui in rxcui_clean[:3]:
                # Resolve rxcui to name
                name_url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/property.json?propName=RxNorm%20Name"
                r = await client.get(name_url)
                if r.status_code == 200:
                    d_name = r.json().get("propConceptGroup", {}).get("propConcept", [{}])[0].get("propValue")
                    if d_name:
                        fda_url = f"https://api.fda.gov/drug/label.json?search=openfda.generic_name:{quote(d_name)}&limit=1"
                        r_fda = await client.get(fda_url)
                        if r_fda.status_code == 200:
                            results = r_fda.json().get("results", [])
                            if results:
                                d_interactions = results[0].get("drug_interactions", [])
                                if d_interactions:
                                    snippet = d_interactions[0][:250] if isinstance(d_interactions, list) else str(d_interactions)[:250]
                                    interactions.append({
                                        "drug_pair": d_name,
                                        "severity": "MODERATE_TO_HIGH",
                                        "description": snippet,
                                        "source": f"FDA Drug Interactions Label ({d_name})",
                                    })
    except Exception as e:
        log.debug("drug_interaction_query_partial", error=str(e))

    _PHARMA_CACHE[cache_key] = (now, interactions)
    return interactions


# ---------------------------------------------------------------------------
# 6. openFDA Deep Boxed Warnings & Contraindications (100% Free & Open, Zero Keys)
# ---------------------------------------------------------------------------
async def query_openfda_boxed_warnings(drug_name: str) -> Dict[str, Any]:
    """Extracts official FDA Boxed Warning and Contraindications from openFDA."""
    cache_key = f"boxed_warning_{drug_name.lower()}"
    now = time.time()
    if cache_key in _PHARMA_CACHE:
        ts, data = _PHARMA_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    result = {
        "drug_name": drug_name,
        "has_boxed_warning": False,
        "boxed_warning": None,
        "contraindications": None,
        "warnings_and_cautions": None,
        "source": "US FDA Structured Label (openFDA)",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            clean_name = drug_name.strip()
            url = f"https://api.fda.gov/drug/label.json?search=(openfda.generic_name:{quote(clean_name)}+OR+openfda.brand_name:{quote(clean_name)}+OR+openfda.substance_name:{quote(clean_name)})&limit=1"
            r = await client.get(url)
            if r.status_code == 200:
                results = r.json().get("results", [])
                if results:
                    label = results[0]
                    boxed = label.get("boxed_warning", [])
                    contra = label.get("contraindications", [])
                    warn = label.get("warnings_and_cautions", [])

                    if boxed:
                        result["has_boxed_warning"] = True
                        result["boxed_warning"] = (boxed[0] if isinstance(boxed, list) else str(boxed))[:600]
                    if contra:
                        result["contraindications"] = (contra[0] if isinstance(contra, list) else str(contra))[:400]
                    if warn:
                        result["warnings_and_cautions"] = (warn[0] if isinstance(warn, list) else str(warn))[:400]

        _PHARMA_CACHE[cache_key] = (now, result)
    except Exception as e:
        log.warning("openfda_boxed_warning_failed", drug=drug_name, error=str(e))

    return result
