"""DocAssistIQ — Master Clinical Knowledge & Terminology API Router.

Exposes live real-time endpoints for:
- Disease coding (WHO ICD-11, SNOMED CT, UMLS, MeSH)
- Drug safety & pharmacology (RxNorm, WHO ATC, openFDA, DailyMed, PubChem)
- Clinical evidence (PubMed, ClinicalTrials.gov v2, Europe PMC)
- Rare disease and phenotype matching (Monarch HPO, Orphanet)
- Outbreak intelligence (WHO DON, CDC, ReliefWeb)
- Genomics & AMR resistance (HGNC, ClinVar, CARD)
- HL7 FHIR R4 encounter bundle generation
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, Body, HTTPException
import structlog

from app.services.clinical_gateway import (
    master_clinical_gateway,
    query_rxnorm_drug,
    query_hpo_phenotype,
    query_icd11_condition,
    query_umls_crosswalk,
    query_openfda_safety,
    query_dailymed_label,
    query_pubmed_evidence,
    query_clinical_trials_v2,
    query_orphanet_disease,
    query_who_outbreaks,
    query_hgnc_gene,
    query_clinvar_variant,
    query_amr_resistance,
    export_fhir_r4_bundle,
)

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/clinical-knowledge", tags=["Clinical Knowledge Gateway"])


@router.get("/condition", summary="Code condition via ICD-11, SNOMED CT, UMLS, and MONDO")
async def get_condition_coding(q: str = Query(..., description="Condition or diagnosis name, e.g. 'Type 2 Diabetes'")):
    """Resolves condition across WHO ICD-11, SNOMED CT, UMLS CUI, and MONDO."""
    return await master_clinical_gateway.code_clinical_condition(q)


@router.get("/drug-safety", summary="Get comprehensive drug profile (RxNorm, ATC, openFDA, DailyMed)")
async def get_drug_safety(drug: str = Query(..., description="Medication generic or trade name, e.g. 'Warfarin'")):
    """Fetches RxCUI, WHO ATC classes, openFDA adverse events, FDA package inserts, and PubChem."""
    return await master_clinical_gateway.get_drug_comprehensive_profile(drug)


@router.get("/evidence", summary="Fetch PubMed literature and ClinicalTrials.gov studies")
async def get_condition_evidence(condition: str = Query(..., description="Disease or condition name, e.g. 'Pulmonary Embolism'")):
    """Fetches real PubMed citations, active clinical trials from ClinicalTrials.gov, and Europe PMC."""
    return await master_clinical_gateway.get_condition_evidence(condition)


@router.get("/phenotypes", summary="Match symptoms to HPO and Orphanet rare diseases")
async def get_phenotypes_and_rare_diseases(symptoms: str = Query(..., description="Comma-separated symptoms, e.g. 'ataxia, microcephaly'")):
    """Matches signs/symptoms against Monarch HPO and Orphanet rare disease registry."""
    symptom_list = [s.strip() for s in symptoms.split(",") if s.strip()]
    if not symptom_list:
        raise HTTPException(status_code=400, detail="At least one symptom is required")
    return await master_clinical_gateway.evaluate_rare_disease_and_phenotypes(symptom_list)


@router.get("/surveillance", summary="Real-time global and regional epidemic alerts")
async def get_epidemic_surveillance(region: Optional[str] = Query("", description="Country or region name, e.g. 'India' or 'Uganda'")):
    """Fetches WHO Outbreak News, CDC Travel Notices, and ReliefWeb emergency declarations."""
    return await master_clinical_gateway.get_live_epidemic_intelligence(region or "")


@router.get("/genomics-amr", summary="Genomics & Antibiotic Resistance Lookup")
async def get_genomics_and_amr(query: str = Query(..., description="Gene, variant, or resistance marker, e.g. 'BRCA1', 'blaKPC', 'mecA'")):
    """Fetches HGNC gene symbols, ClinVar variant pathogenicity, UniProt, MyGene, and CARD AMR."""
    return await master_clinical_gateway.get_genomics_deep_profile(query)


@router.get("/drug-interactions", summary="Live NLM Drug-Drug Interaction Checker")
async def get_drug_interactions(rxcuis: str = Query(..., description="Comma-separated RxCUIs, e.g. '11289,5640' (Warfarin + Ibuprofen)")):
    """Checks real documented NLM drug-drug interaction pairs and severity."""
    rxcui_list = [r.strip() for r in rxcuis.split(",") if r.strip()]
    if len(rxcui_list) < 2:
        raise HTTPException(status_code=400, detail="At least 2 RxCUIs are required to check interactions")
    return await master_clinical_gateway.check_multi_drug_interactions(rxcui_list)


@router.get("/boxed-warning", summary="FDA Boxed Warnings & Contraindications")
async def get_drug_boxed_warning(drug: str = Query(..., description="Medication name, e.g. 'Warfarin' or 'Ciprofloxacin'")):
    """Extracts official FDA Boxed Warning and Contraindications from openFDA."""
    return await master_clinical_gateway.get_drug_boxed_warnings(drug)


@router.get("/epidemiology-stats", summary="Real-time Outbreak & Case Statistics")
async def get_epidemiology_statistics(country: Optional[str] = Query("", description="Country name, e.g. 'India', 'US', or empty for Global")):
    """Queries real-time epidemiology statistics from disease.sh."""
    from app.services.clinical_gateway import query_disease_sh_epidemiology
    return await query_disease_sh_epidemiology(country or "")


@router.post("/export-fhir", summary="Export patient encounter as HL7 FHIR R4 Bundle")
async def export_patient_fhir(payload: Dict[str, Any] = Body(...)):
    """Exports patient data, conditions, observations, and medications into an official HL7 FHIR R4 Bundle."""
    patient_id = payload.get("patient_id", "anonymous")
    conditions = payload.get("conditions", [])
    observations = payload.get("observations", [])
    medications = payload.get("medications", [])
    return export_fhir_r4_bundle(
        patient_id=patient_id,
        conditions=conditions,
        observations=observations,
        medications=medications,
    )
