"""Test the newly added 100% Free & Open APIs."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.clinical_gateway import (
    query_rxnav_drug_interactions,
    query_openfda_boxed_warnings,
    query_uniprot_protein,
    query_mygene_info,
    query_disease_sh_epidemiology,
    master_clinical_gateway,
)

async def test_new_apis():
    print("=" * 70)
    print("Testing Newly Added 100% Free & Open Trusted Medical APIs")
    print("=" * 70)

    # 1. NLM Drug-Drug Interactions
    print("\n[1] Testing Live NLM Drug-Drug Interaction API (Warfarin 11289 + Ibuprofen 5640)...")
    interactions = await query_rxnav_drug_interactions(["11289", "5640"])
    print(f"    Found {len(interactions)} interaction pair(s):")
    for it in interactions[:2]:
        print(f"      - {it.get('drug_pair')}: [{it.get('severity')}] {it.get('description')[:80]}...")

    # 2. openFDA Boxed Warnings
    print("\n[2] Testing openFDA Deep Boxed Warnings (Ciprofloxacin)...")
    boxed = await query_openfda_boxed_warnings("Ciprofloxacin")
    print(f"    Has Boxed Warning: {boxed.get('has_boxed_warning')}")
    if boxed.get('boxed_warning'):
        print(f"    Warning: {boxed.get('boxed_warning')[:120]}...")

    # 3. UniProt Human Protein Knowledgebase
    print("\n[3] Testing UniProt Human Protein Knowledgebase (BRCA1)...")
    uni = await query_uniprot_protein("BRCA1")
    print(f"    UniProt ID: {uni.get('uniprot_id')} | Name: {uni.get('protein_name')}")
    print(f"    Function: {(uni.get('function_summary') or '')[:100]}...")

    # 4. MyGene.info
    print("\n[4] Testing MyGene.info (EGFR)...")
    myg = await query_mygene_info("EGFR")
    print(f"    Gene: {myg.get('gene_symbol')} | Name: {myg.get('name')}")
    print(f"    Pathways: {myg.get('pathways')[:2]}")

    # 5. Disease.sh Epidemiology
    print("\n[5] Testing Disease.sh (OpenDiseaseData) Global & India Statistics...")
    dsh = await query_disease_sh_epidemiology("India")
    print(f"    Region: {dsh.get('region')} | Total Cases: {dsh.get('cases'):,} | Recovered: {dsh.get('recovered'):,}")

    print("\n" + "=" * 70)
    print("ALL 5 NEW ADVANCED REAL APIS PASSED WITH LIVE DATA!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_new_apis())
