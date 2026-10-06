"""DocAssistIQ — Master Clinical Knowledge & Terminology Gateway Package.

Consolidates 52+ global medical knowledge sources into high-performance,
zero-hallucination, asynchronous clinical APIs.
"""

from app.services.clinical_gateway.master_gateway import (
    MasterClinicalGateway,
    master_clinical_gateway,
)
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

__all__ = [
    "MasterClinicalGateway",
    "master_clinical_gateway",
    "query_rxnorm_drug",
    "query_hpo_phenotype",
    "query_icd11_condition",
    "query_umls_crosswalk",
    "normalize_clinical_unit",
    "query_dailymed_label",
    "query_openfda_safety",
    "query_pubchem_compound",
    "query_chembl_targets",
    "query_pubmed_evidence",
    "query_clinical_trials_v2",
    "query_europe_pmc",
    "query_openalex_citations",
    "query_orphanet_disease",
    "query_mondo_crosswalk",
    "query_who_outbreaks",
    "query_cdc_travel_notices",
    "query_reliefweb_health",
    "query_disease_sh_epidemiology",
    "query_hgnc_gene",
    "query_clinvar_variant",
    "query_amr_resistance",
    "query_uniprot_protein",
    "query_mygene_info",
    "query_rxnav_drug_interactions",
    "query_openfda_boxed_warnings",
    "export_fhir_r4_bundle",
]
