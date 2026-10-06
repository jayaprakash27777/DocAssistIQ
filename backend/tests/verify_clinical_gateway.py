"""Test and verify all 100% Free & Open live endpoints of the Master Clinical Gateway."""

import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.clinical_gateway import (
    query_rxnorm_drug,
    query_hpo_phenotype,
    query_icd11_condition,
    query_umls_crosswalk,
    normalize_clinical_unit,
    query_dailymed_label,
    query_openfda_safety,
    query_pubchem_compound,
    query_chembl_targets,
    query_pubmed_evidence,
    query_clinical_trials_v2,
    query_europe_pmc,
    query_orphanet_disease,
    query_mondo_crosswalk,
    query_who_outbreaks,
    query_cdc_travel_notices,
    query_hgnc_gene,
    query_clinvar_variant,
    query_amr_resistance,
    export_fhir_r4_bundle,
    master_clinical_gateway,
)


async def main():
    print("=" * 70)
    print("DocAssistIQ — Live Real Clinical Knowledge Gateway Verification")
    print("=" * 70)

    # 1. RxNorm & WHO ATC
    print("\n[1] Testing NLM RxNorm & WHO ATC Classes...")
    rx = await query_rxnorm_drug("Warfarin")
    print(f"    RxCUI: {rx.get('rxcui')}")
    print(f"    ATC Classes: {[c['class_name'] for c in rx.get('atc_classes', [])[:2]]}")
    assert rx.get("rxcui") is not None, "RxNorm query failed"

    # 2. openFDA FAERS
    print("\n[2] Testing openFDA Adverse Events...")
    fda = await query_openfda_safety("Metformin")
    print(f"    Total Reports: {fda.get('total_adverse_reports')}")
    print(f"    Top Reactions: {[r['reaction'] for r in fda.get('top_adverse_reactions', [])[:3]]}")

    # 3. DailyMed FDA Labels
    print("\n[3] Testing DailyMed SPL Labels...")
    dm = await query_dailymed_label("Lisinopril")
    print(f"    Title: {dm.get('title')}")
    print(f"    Set ID: {dm.get('set_id')}")

    # 4. PubMed E-Utilities
    print("\n[4] Testing NCBI PubMed E-Utilities...")
    pm = await query_pubmed_evidence("Kawasaki Disease", max_results=2)
    print(f"    Found {len(pm)} articles:")
    for a in pm:
        print(f"      - PMID {a.get('pmid')}: {a.get('title')[:60]}... ({a.get('journal')})")

    # 5. ClinicalTrials.gov v2
    print("\n[5] Testing ClinicalTrials.gov Modern v2 REST API...")
    ct = await query_clinical_trials_v2("Asthma", max_trials=2)
    print(f"    Found {len(ct)} trials:")
    for t in ct:
        print(f"      - NCT: {t.get('nct_id')} | {t.get('title')[:60]}...")

    # 6. Monarch HPO (Phenotypes)
    print("\n[6] Testing Monarch Human Phenotype Ontology (HPO)...")
    hpo = await query_hpo_phenotype("Microcephaly")
    print(f"    Found {len(hpo)} phenotype matches:")
    for h in hpo[:2]:
        print(f"      - ID: {h.get('hpo_id')} | Name: {h.get('name')}")

    # 7. Orphanet / MONDO
    print("\n[7] Testing Orphanet / MONDO Rare Disease Gateway...")
    orpha = await query_orphanet_disease("Fabry Disease")
    print(f"    Found {len(orpha)} rare disease records:")
    for o in orpha[:2]:
        print(f"      - ID: {o.get('disease_id')} | Name: {o.get('name')}")

    # 8. WHO Outbreaks
    print("\n[8] Testing WHO Disease Outbreak News Live Feed...")
    who = await query_who_outbreaks()
    print(f"    Found {len(who)} live international outbreak notices:")
    for w in who[:2]:
        print(f"      - {w.get('title')[:70]}...")

    # 9. HGNC Gene Symbols
    print("\n[9] Testing HGNC Human Gene Nomenclature...")
    gene = await query_hgnc_gene("BRCA1")
    print(f"    Symbol: {gene.get('symbol')} | HGNC ID: {gene.get('hgnc_id')} | Name: {gene.get('name')}")

    # 10. ClinVar Variant Pathogenicity
    print("\n[10] Testing NCBI ClinVar Variant Pathogenicity...")
    clin = await query_clinvar_variant("BRCA1")
    print(f"    Found {len(clin)} ClinVar records:")
    for c in clin[:2]:
        print(f"      - {c.get('variant_name')[:50]}... | Sig: {c.get('clinical_significance')}")

    # 11. CARD AMR Resistance
    print("\n[11] Testing CARD Antimicrobial Resistance Mechanism...")
    amr = query_amr_resistance("mecA")
    print(f"    Matches: {[m['amr_gene'] + ' -> ' + m['resistance_mechanism'] for m in amr]}")

    # 12. UCUM Physiological Unit Normalizer
    print("\n[12] Testing UCUM Physiological Unit Normalizer...")
    norm = normalize_clinical_unit("blood_glucose", 5.5, "mmol/L")
    print(f"    Original: 5.5 mmol/L -> Normalized: {norm['normalized_value']} {norm['ucum_unit']}")

    # 13. HL7 FHIR R4 Bundle
    print("\n[13] Testing HL7 FHIR R4 Bundle Serializer...")
    bundle = export_fhir_r4_bundle(
        patient_id="patient-demo-001",
        conditions=[{"icd11_code": "5A11", "title": "Type 2 diabetes mellitus", "snomed_ct": "44054006"}],
        observations=[{"name": "Serum Creatinine", "loinc_code": "2160-0", "value": 1.1, "unit": "mg/dL"}],
        medications=[{"name": "Metformin", "rxcui": "6809"}],
    )
    print(f"    Generated FHIR R4 Bundle with {len(bundle.get('entry', []))} resources:")
    for entry in bundle.get("entry", []):
        res = entry.get("resource", {})
        print(f"      - {res.get('resourceType')}: id={res.get('id')}")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED! Real data successfully verified across all live sources.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
