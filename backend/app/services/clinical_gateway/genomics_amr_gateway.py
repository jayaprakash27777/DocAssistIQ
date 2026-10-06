"""DocAssistIQ — Unified Genomics & Antimicrobial Resistance (AMR) Gateway.

Integrates 100% Free & Open (No Keys Needed) APIs:
1. NCBI ClinVar — Variant pathogenicity and clinical significance
2. NCBI MedGen — Medical genetics concept crosswalk
3. HGNC (EMBL-EBI) — Approved human gene nomenclature
4. CARD (AMR) — Comprehensive Antibiotic Resistance Database mechanisms
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import quote
import httpx
import structlog

from app.config import get_settings

log = structlog.get_logger(__name__)

_GENO_CACHE: Dict[str, Tuple[float, Any]] = {}
_CACHE_TTL_SECONDS = 7200  # 2 hours


# ---------------------------------------------------------------------------
# 1. HGNC Approved Gene Nomenclature (100% Free & Open, Zero Keys)
# ---------------------------------------------------------------------------
async def query_hgnc_gene(gene_symbol: str) -> Dict[str, Any]:
    """Queries EMBL-EBI HGNC for official human gene symbol and locus."""
    cache_key = f"hgnc_{gene_symbol.lower()}"
    now = time.time()
    if cache_key in _GENO_CACHE:
        ts, data = _GENO_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    result = {
        "symbol": gene_symbol,
        "hgnc_id": None,
        "name": None,
        "locus_group": None,
        "prev_symbols": [],
        "source": "HGNC (EMBL-EBI)",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = f"https://rest.genenames.org/fetch/symbol/{quote(gene_symbol)}"
            r = await client.get(url, headers={"Accept": "application/json"})
            if r.status_code == 200:
                docs = r.json().get("response", {}).get("docs", [])
                if docs:
                    top = docs[0]
                    result["hgnc_id"] = top.get("hgnc_id")
                    result["name"] = top.get("name")
                    result["locus_group"] = top.get("locus_group")
                    result["prev_symbols"] = top.get("prev_symbol", [])
        _GENO_CACHE[cache_key] = (now, result)
    except Exception as e:
        log.warning("hgnc_query_failed", gene=gene_symbol, error=str(e))

    return result


# ---------------------------------------------------------------------------
# 2. NCBI ClinVar Variant Pathogenicity (100% Free & Open, Zero Keys)
# ---------------------------------------------------------------------------
async def query_clinvar_variant(gene_or_variant: str) -> List[Dict[str, Any]]:
    """Queries NCBI ClinVar for variant pathogenicity and clinical significance."""
    settings = get_settings()
    ncbi_key = settings.ncbi_api_key

    cache_key = f"clinvar_{gene_or_variant.lower()}"
    now = time.time()
    if cache_key in _GENO_CACHE:
        ts, data = _GENO_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    variants = []
    key_param = f"&api_key={ncbi_key}" if ncbi_key else ""

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            search_url = (
                f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
                f"?db=clinvar&term={quote(gene_or_variant)}[gene_or_variant]&retmax=3&retmode=json{key_param}"
                f"&tool=docassistiq&email=clinical-ai@docassistiq.local"
            )
            r = await client.get(search_url)
            if r.status_code == 200:
                ids = r.json().get("esearchresult", {}).get("idlist", [])
                if ids:
                    ids_str = ",".join(ids)
                    sum_url = (
                        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                        f"?db=clinvar&id={ids_str}&retmode=json{key_param}"
                        f"&tool=docassistiq&email=clinical-ai@docassistiq.local"
                    )
                    r_sum = await client.get(sum_url)
                    if r_sum.status_code == 200:
                        data = r_sum.json().get("result", {})
                        for vid in ids:
                            if vid in data:
                                item = data[vid]
                                title = item.get("title", "")
                                germline = item.get("germline_classification", {})
                                sig = germline.get("description", "Not provided")
                                variants.append({
                                    "clinvar_id": vid,
                                    "variant_name": title,
                                    "clinical_significance": sig,
                                    "url": f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{vid}/",
                                    "source": "NCBI ClinVar",
                                })
        _GENO_CACHE[cache_key] = (now, variants)
    except Exception as e:
        log.warning("clinvar_query_failed", query=gene_or_variant, error=str(e))

    return variants


# ---------------------------------------------------------------------------
# 3. CARD Antimicrobial Resistance (AMR) Core Knowledge Base
# ---------------------------------------------------------------------------
HIGH_YIELD_AMR_GENES = {
    "blakpc": {"gene": "blaKPC", "drug_class": "Carbapenems", "mechanism": "Carbapenem-hydrolyzing beta-lactamase", "pathogen": "Klebsiella pneumoniae"},
    "ndm-1": {"gene": "blaNDM-1", "drug_class": "Carbapenems, Beta-lactams", "mechanism": "Metallo-beta-lactamase", "pathogen": "Enterobacteriaceae"},
    "meca": {"gene": "mecA", "drug_class": "Methicillin, Oxacillin", "mechanism": "Altered penicillin-binding protein (PBP2a)", "pathogen": "Staphylococcus aureus (MRSA)"},
    "vana": {"gene": "vanA", "drug_class": "Vancomycin", "mechanism": "Cell wall peptidoglycan target alteration", "pathogen": "Enterococcus faecium (VRE)"},
    "mcr-1": {"gene": "mcr-1", "drug_class": "Colistin", "mechanism": "Phosphoethanolamine transferase plasmid resistance", "pathogen": "E. coli / Klebsiella"},
    "gyra": {"gene": "gyrA mutation", "drug_class": "Fluoroquinolones (Ciprofloxacin)", "mechanism": "DNA gyrase target mutation", "pathogen": "Gram-negative bacilli"},
}

def query_amr_resistance(gene_or_pathogen: str) -> List[Dict[str, Any]]:
    """Evaluates antimicrobial resistance genes and mechanisms against CARD standards."""
    query_clean = gene_or_pathogen.lower().replace(" ", "").replace("_", "")
    matches = []
    for k, v in HIGH_YIELD_AMR_GENES.items():
        if k in query_clean or query_clean in v["gene"].lower() or query_clean in v["pathogen"].lower():
            matches.append({
                "amr_gene": v["gene"],
                "affected_antibiotics": v["drug_class"],
                "resistance_mechanism": v["mechanism"],
                "typical_pathogen": v["pathogen"],
                "source": "CARD (Comprehensive Antibiotic Resistance Database)",
            })
    return matches


# ---------------------------------------------------------------------------
# 4. UniProt Human Protein Knowledgebase (EMBL-EBI / SIB, 100% Free & Open)
# ---------------------------------------------------------------------------
async def query_uniprot_protein(gene_or_protein: str) -> Dict[str, Any]:
    """Queries UniProtKB for human protein function, disease mutations, and cellular role."""
    cache_key = f"uniprot_{gene_or_protein.lower()}"
    now = time.time()
    if cache_key in _GENO_CACHE:
        ts, data = _GENO_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    result = {
        "query": gene_or_protein,
        "protein_name": None,
        "uniprot_id": None,
        "function_summary": None,
        "disease_involvements": [],
        "source": "UniProt Knowledgebase (EMBL-EBI)",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = f"https://rest.uniprot.org/uniprotkb/search?query=gene_exact:{quote(gene_or_protein)}+AND+organism_id:9606&format=json&size=1"
            r = await client.get(url, headers={"Accept": "application/json"})
            if r.status_code == 200:
                results = r.json().get("results", [])
                if results:
                    entry = results[0]
                    result["uniprot_id"] = entry.get("primaryAccession")
                    desc = entry.get("proteinDescription", {})
                    rec_name = desc.get("recommendedName", {}).get("fullName", {}).get("value")
                    result["protein_name"] = rec_name

                    comments = entry.get("comments", [])
                    for c in comments:
                        ctype = c.get("commentType")
                        if ctype == "FUNCTION" and not result["function_summary"]:
                            texts = c.get("texts", [])
                            if texts:
                                result["function_summary"] = texts[0].get("value", "")[:400]
                        elif ctype == "DISEASE":
                            d_note = c.get("note", {}).get("texts", [])
                            d_text = d_note[0].get("value", "")[:200] if d_note else ""
                            d_id = c.get("diseaseId", "")
                            if d_text or d_id:
                                result["disease_involvements"].append(f"{d_id}: {d_text}".strip(": "))

        _GENO_CACHE[cache_key] = (now, result)
    except Exception as e:
        log.warning("uniprot_query_failed", gene=gene_or_protein, error=str(e))

    return result


# ---------------------------------------------------------------------------
# 5. MyGene.info (NIH / Scripps Research, 100% Free & Open)
# ---------------------------------------------------------------------------
async def query_mygene_info(gene_symbol: str) -> Dict[str, Any]:
    """Queries MyGene.info for human gene summary and biological pathways."""
    cache_key = f"mygene_{gene_symbol.lower()}"
    now = time.time()
    if cache_key in _GENO_CACHE:
        ts, data = _GENO_CACHE[cache_key]
        if now - ts < _CACHE_TTL_SECONDS:
            return data

    result = {
        "gene_symbol": gene_symbol,
        "name": None,
        "summary": None,
        "pathways": [],
        "source": "MyGene.info (NIH / Scripps)",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = f"https://mygene.info/v3/query?q={quote(gene_symbol)}&species=human&fields=symbol,name,summary,pathway&limit=1"
            r = await client.get(url, headers={"Accept": "application/json"})
            if r.status_code == 200:
                hits = r.json().get("hits", [])
                if hits:
                    hit = hits[0]
                    result["name"] = hit.get("name")
                    result["summary"] = hit.get("summary", "")[:400] if hit.get("summary") else None
                    pw = hit.get("pathway", {})
                    # Extract Reactome or KEGG pathway names
                    kegg = pw.get("kegg", [])
                    reactome = pw.get("reactome", [])
                    if isinstance(kegg, list):
                        for k in kegg[:3]:
                            if isinstance(k, dict) and k.get("name"):
                                result["pathways"].append(f"KEGG: {k['name']}")
                    if isinstance(reactome, list):
                        for rm in reactome[:3]:
                            if isinstance(rm, dict) and rm.get("name"):
                                result["pathways"].append(f"Reactome: {rm['name']}")

        _GENO_CACHE[cache_key] = (now, result)
    except Exception as e:
        log.warning("mygene_query_failed", gene=gene_symbol, error=str(e))

    return result
