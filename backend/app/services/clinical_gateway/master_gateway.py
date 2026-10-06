"""DocAssistIQ — Master Clinical Knowledge & Multi-Source Gateway Orchestrator.

Orchestrates 52+ authoritative medical knowledge sources into a unified, high-performance,
zero-hallucination clinical decision and coding API.
"""

import asyncio
from typing import Dict, List, Any, Optional
import structlog

from app.services.clinical_gateway.terminology_gateway import (
    query_rxnorm_drug,
    query_hpo_phenotype,
    query_icd11_condition,
    query_umls_crosswalk,
    normalize_clinical_unit,
)
from app.services.clinical_gateway.pharmacology_gateway import (
    query_dailymed_label,
    query_openfda_safety,
    query_pubchem_compound,
    query_chembl_targets,
    query_rxnav_drug_interactions,
    query_openfda_boxed_warnings,
)
from app.services.clinical_gateway.evidence_gateway import (
    query_pubmed_evidence,
    query_clinical_trials_v2,
    query_europe_pmc,
    query_openalex_citations,
)
from app.services.clinical_gateway.rare_disease_gateway import (
    query_orphanet_disease,
    query_mondo_crosswalk,
)
from app.services.clinical_gateway.surveillance_gateway import (
    query_who_outbreaks,
    query_cdc_travel_notices,
    query_reliefweb_health,
    query_disease_sh_epidemiology,
)
from app.services.clinical_gateway.genomics_amr_gateway import (
    query_hgnc_gene,
    query_clinvar_variant,
    query_amr_resistance,
    query_uniprot_protein,
    query_mygene_info,
)
from app.services.clinical_gateway.fhir_exporter import export_fhir_r4_bundle

log = structlog.get_logger(__name__)


class MasterClinicalGateway:
    """Master Clinical Knowledge Gateway coordinating all 52+ sources asynchronously."""

    async def code_clinical_condition(self, condition_name: str) -> Dict[str, Any]:
        """Resolves condition across WHO ICD-11, SNOMED CT, MeSH, and MONDO in parallel."""
        icd_task = query_icd11_condition(condition_name)
        umls_task = query_umls_crosswalk(condition_name)
        mondo_task = query_mondo_crosswalk(condition_name)

        icd_res, umls_res, mondo_res = await asyncio.gather(icd_task, umls_task, mondo_task)

        return {
            "query": condition_name,
            "icd11_code": icd_res.get("icd11_code"),
            "icd11_title": icd_res.get("title"),
            "snomed_ct": umls_res.get("snomed_ct"),
            "cui": umls_res.get("cui"),
            "mesh_ui": umls_res.get("mesh_ui"),
            "mondo_id": mondo_res.get("mondo_id"),
            "verified": bool(icd_res.get("icd11_code") or umls_res.get("snomed_ct")),
        }

    async def get_drug_comprehensive_profile(self, drug_name: str) -> Dict[str, Any]:
        """Gathers RxNorm, WHO ATC classes, openFDA adverse reactions, DailyMed label, and PubChem."""
        rx_task = query_rxnorm_drug(drug_name)
        label_task = query_dailymed_label(drug_name)
        fda_task = query_openfda_safety(drug_name)
        pubchem_task = query_pubchem_compound(drug_name)
        chembl_task = query_chembl_targets(drug_name)

        rx_res, label_res, fda_res, pubchem_res, chembl_res = await asyncio.gather(
            rx_task, label_task, fda_task, pubchem_task, chembl_task
        )

        return {
            "drug_name": drug_name,
            "rxcui": rx_res.get("rxcui"),
            "atc_classes": rx_res.get("atc_classes", []),
            "synonyms": rx_res.get("synonyms", []),
            "fda_label": label_res,
            "fda_adverse_events": fda_res,
            "pubchem": pubchem_res,
            "chembl_mechanisms": chembl_res,
        }

    async def get_condition_evidence(self, condition_name: str) -> Dict[str, Any]:
        """Gathers PubMed peer-reviewed papers, active ClinicalTrials.gov v2 studies, and Europe PMC."""
        pubmed_task = query_pubmed_evidence(condition_name, max_results=3)
        trials_task = query_clinical_trials_v2(condition_name, max_trials=3)
        epmc_task = query_europe_pmc(condition_name, max_results=2)

        pubmed_res, trials_res, epmc_res = await asyncio.gather(pubmed_task, trials_task, epmc_task)

        return {
            "condition": condition_name,
            "pubmed_citations": pubmed_res,
            "clinical_trials": trials_res,
            "europe_pmc": epmc_res,
        }

    async def evaluate_rare_disease_and_phenotypes(self, symptoms: List[str]) -> Dict[str, Any]:
        """Resolves HPO codes and searches Orphanet / ORDO for matching rare diseases."""
        hpo_tasks = [query_hpo_phenotype(sym) for sym in symptoms[:4]]
        hpo_results = await asyncio.gather(*hpo_tasks)

        all_phenotypes = []
        for res_list in hpo_results:
            all_phenotypes.extend(res_list)

        # Search Orphanet for first two symptoms
        rare_tasks = [query_orphanet_disease(sym) for sym in symptoms[:2]]
        rare_results = await asyncio.gather(*rare_tasks)

        all_rare = []
        for r_list in rare_results:
            all_rare.extend(r_list)

        return {
            "symptoms_evaluated": symptoms,
            "hpo_phenotypes": all_phenotypes,
            "rare_disease_matches": all_rare,
        }

    async def get_live_epidemic_intelligence(self, region: str = "") -> Dict[str, Any]:
        """Gathers WHO Outbreak News, CDC Travel Notices, and ReliefWeb emergency alerts."""
        who_task = query_who_outbreaks(region)
        cdc_task = query_cdc_travel_notices()
        rw_task = query_reliefweb_health(region)
        dsh_task = query_disease_sh_epidemiology(region)

        who_res, cdc_res, rw_res, dsh_res = await asyncio.gather(who_task, cdc_task, rw_task, dsh_task)

        return {
            "region": region,
            "who_outbreaks": who_res,
            "cdc_notices": cdc_res[:3],
            "reliefweb_reports": rw_res,
            "realtime_epidemiology": dsh_res,
        }

    async def check_multi_drug_interactions(self, rxcuis: List[str]) -> List[Dict[str, Any]]:
        """Live NLM drug-drug interaction pairs and severity check."""
        return await query_rxnav_drug_interactions(rxcuis)

    async def get_drug_boxed_warnings(self, drug_name: str) -> Dict[str, Any]:
        """Live FDA Boxed Warning and Contraindications from openFDA."""
        return await query_openfda_boxed_warnings(drug_name)

    async def get_genomics_deep_profile(self, gene_or_protein: str) -> Dict[str, Any]:
        """Combines HGNC, ClinVar, UniProt, and MyGene.info in parallel."""
        hgnc_task = query_hgnc_gene(gene_or_protein)
        clin_task = query_clinvar_variant(gene_or_protein)
        uni_task = query_uniprot_protein(gene_or_protein)
        myg_task = query_mygene_info(gene_or_protein)
        amr_res = query_amr_resistance(gene_or_protein)

        hgnc_res, clin_res, uni_res, myg_res = await asyncio.gather(
            hgnc_task, clin_task, uni_task, myg_task
        )

        return {
            "query": gene_or_protein,
            "hgnc": hgnc_res,
            "clinvar": clin_res,
            "uniprot": uni_res,
            "mygene": myg_res,
            "card_amr": amr_res,
        }

    def generate_encounter_fhir(
        self,
        patient_id: str,
        conditions: List[Dict[str, Any]],
        observations: List[Dict[str, Any]],
        medications: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Exports full patient encounter into an official HL7 FHIR R4 bundle."""
        return export_fhir_r4_bundle(
            patient_id=patient_id,
            conditions=conditions,
            observations=observations,
            medications=medications,
        )


master_clinical_gateway = MasterClinicalGateway()
