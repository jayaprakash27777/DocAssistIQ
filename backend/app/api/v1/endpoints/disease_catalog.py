"""DocAssistIQ — Master Disease Catalog API Router (20,000+ Clinical Entities).

Exposes high-speed endpoints for:
  - Universal disease search with sub-30ms full-text SQLite FTS5 search
  - Comprehensive clinical monographs (ICD-10, ICD-11, OrphaCode, Hallmark symptoms, Confirmatory tests, First-line therapy)
  - Specialty filtering (Cardiology, Neurology, Rare Genetics, Pulmonology, etc.)
  - Real-time symptom-to-disease candidate matching
  - Global catalog metrics and epidemiological distributions
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Body
from pydantic import BaseModel
import structlog

from app.services.master_disease_catalog import master_disease_catalog

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/disease-catalog", tags=["Disease Catalog (15,000+ Entities)"])


class SymptomMatchRequest(BaseModel):
    symptoms: List[str]
    top_k: int = 10


@router.get(
    "/search",
    summary="Search 20,000+ Clinical Diseases & Rare Conditions",
    description="Sub-millisecond full-text and prefix search across 20,397+ conditions, ICD-10/11 codes, and synonyms."
)
async def search_disease_catalog(
    q: str = Query("", description="Search term, disease name, synonym, or ICD code"),
    category: Optional[str] = Query(None, description="Filter by medical specialty/category"),
    severity: Optional[str] = Query(None, description="Filter by severity ('critical', 'high', 'moderate', 'low')"),
    triage: Optional[str] = Query(None, description="Filter by triage priority ('EMERGENT', 'URGENT', 'ROUTINE')"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> Dict[str, Any]:
    return master_disease_catalog.search_diseases(
        query=q,
        category=category,
        severity=severity,
        triage=triage,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/disease/{disease_name}",
    summary="Get Detailed Clinical Monograph",
    description="Returns full clinical monograph for any of the 20,397+ diseases including hallmarks, tests, and treatment."
)
async def get_disease_monograph(disease_name: str) -> Dict[str, Any]:
    disease = master_disease_catalog.get_disease_by_name(disease_name)
    if not disease:
        # Try search for best match
        search_res = master_disease_catalog.search_diseases(query=disease_name, limit=1)
        if search_res["results"]:
            disease = search_res["results"][0]
        else:
            raise HTTPException(status_code=404, detail=f"Disease '{disease_name}' not found in master catalog.")
    return disease


@router.get(
    "/code/{code}",
    summary="Lookup Disease by ICD-10, ICD-11, or OrphaCode",
    description="Resolves conditions matching a given ICD-10 code, ICD-11 linearization, or Orphanet ORPHA-code."
)
async def get_disease_by_code(code: str) -> List[Dict[str, Any]]:
    results = master_disease_catalog.get_disease_by_code(code)
    if not results:
        raise HTTPException(status_code=404, detail=f"No disease found matching code '{code}'.")
    return results


@router.get(
    "/stats",
    summary="Master Catalog Statistics & Metrics",
    description="Returns total condition counts, specialty breakdown, and ICD coverage."
)
async def get_catalog_statistics() -> Dict[str, Any]:
    return master_disease_catalog.get_stats()


@router.get(
    "/categories",
    summary="List Medical Specialties & Categories",
    description="Returns all 48+ medical specialties with entity distribution counts."
)
async def get_catalog_categories() -> List[Dict[str, Any]]:
    return master_disease_catalog.get_categories()


@router.post(
    "/symptom-match",
    summary="Match Symptoms to Disease Candidates",
    description="Ranks top candidate conditions across the 20,397+ disease catalogue based on patient symptoms."
)
async def match_catalog_symptoms(payload: SymptomMatchRequest) -> List[Dict[str, Any]]:
    return master_disease_catalog.match_symptoms(payload.symptoms, top_k=payload.top_k)


@router.get(
    "/investigations/search",
    summary="Search Standardized Clinical Investigations Catalog",
    description="Sub-millisecond full-text search across LOINC laboratory tests, blood gases, cultures, and bedside imaging."
)
async def search_clinical_investigations(
    q: str = Query(..., description="Investigation name, LOINC code, or clinical condition"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return")
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_clinical_investigations(query=q, limit=limit)


@router.get(
    "/investigations/workup/{disease_name}",
    summary="Get Disease Diagnostic Workup",
    description="Returns immediate bedside tests, priority confirmatory tests, and gold standard for any disease."
)
async def get_disease_diagnostic_workup(disease_name: str) -> Dict[str, Any]:
    from app.services.offline_data_service import offline_data_service
    workup = offline_data_service.get_investigations_for_disease(disease_name)
    if not workup:
        raise HTTPException(status_code=404, detail=f"Diagnostic workup not found for '{disease_name}'.")
    return workup


@router.get(
    "/discriminative-test",
    summary="Get Discriminative 'Next Best Test' for Competing Differential Candidates",
    description="Evaluates two competing differential diagnoses and returns the maximum information-gain test."
)
async def get_discriminative_test(
    candidate_1: str = Query(..., description="Primary candidate disease"),
    candidate_2: str = Query(..., description="Secondary candidate disease")
) -> Dict[str, Any]:
    from app.services.discriminative_test_engine import discriminative_test_engine
    recommendation = discriminative_test_engine.recommend(candidate_1, candidate_2)
    if not recommendation:
        raise HTTPException(status_code=404, detail="Could not derive differentiating recommendation.")
    return recommendation


@router.get(
    "/rare-diseases/phenotype-match",
    summary="Match Rare Syndromes by Phenotypic Features (HPO & Orphanet)",
    description="Searches 12,880 rare syndromes and 285,918 annotations from the Human Phenotype Ontology."
)
async def match_rare_diseases_by_phenotype(
    phenotypes: str = Query(..., description="Comma-separated clinical signs, symptoms, or phenotypic terms"),
    top_k: int = Query(5, ge=1, le=20, description="Maximum results to return")
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    pheno_list = [p.strip() for p in phenotypes.split(",") if p.strip()]
    return offline_data_service.match_rare_disease_by_phenotype(pheno_list, top_k=top_k)


@router.get(
    "/guidelines",
    summary="Get Evidence-Based Clinical Practice Guidelines",
    description="Retrieves official clinical guidelines (AHA/ACC, GOLD, GINA, KDIGO, SSC, ACG, ADA)."
)
async def get_clinical_guidelines(condition: str = Query(..., description="Medical condition or specialty")) -> Dict[str, Any]:
    from app.services.offline_data_service import offline_data_service
    g = offline_data_service.get_clinical_guideline(condition)
    if not g:
        raise HTTPException(status_code=404, detail=f"No guideline found for '{condition}'.")
    return g


@router.get(
    "/calculators",
    summary="Get Clinical Risk Scoring Calculator",
    description="Retrieves criteria for Wells, HEART, CHA2DS2-VASc, CURB-65, MELD-Na."
)
async def get_clinical_calculator(score_name: str = Query(..., description="Score name, ID, or target condition")) -> Dict[str, Any]:
    from app.services.offline_data_service import offline_data_service
    c = offline_data_service.get_clinical_calculator(score_name)
    if not c:
        raise HTTPException(status_code=404, detail=f"Calculator not found for '{score_name}'.")
    return c


@router.get(
    "/resuscitation",
    summary="Get Emergency Resuscitation & Life Support Protocol",
    description="Retrieves ACLS, Anaphylaxis, Status Epilepticus, or MTP life-support protocol."
)
async def get_resuscitation_protocol(condition: str = Query(..., description="Clinical condition or arrest rhythm")) -> Dict[str, Any]:
    from app.services.offline_data_service import offline_data_service
    p = offline_data_service.get_emergency_resuscitation_protocol(condition)
    if not p:
        raise HTTPException(status_code=404, detail=f"Resuscitation protocol not found for '{condition}'.")
    return p


@router.get(
    "/toxicology",
    summary="Get Toxicology Antidote Protocol",
    description="Retrieves toxidrome features, specific antidote, and dosing protocol."
)
async def get_toxicology_protocol(substance: str = Query(..., description="Toxin, poison, or drug class")) -> Dict[str, Any]:
    from app.services.offline_data_service import offline_data_service
    t = offline_data_service.get_toxicology_antidote(substance)
    if not t:
        raise HTTPException(status_code=404, detail=f"Toxicology protocol not found for '{substance}'.")
    return t


@router.get(
    "/pharmacogenomics",
    summary="Check Pharmacogenomics & CPIC Safety",
    description="Retrieves high-risk gene-drug warnings (CYP2C19, HLA-B*5701, DPYD, TPMT)."
)
async def check_pharmacogenomics(drug: str = Query(..., description="Prescribed medication or gene symbol")) -> Dict[str, Any]:
    from app.services.offline_data_service import offline_data_service
    pgx = offline_data_service.check_pharmacogenomics_warning(drug)
    if not pgx:
        raise HTTPException(status_code=404, detail=f"No high-risk CPIC pharmacogenomic warning for '{drug}'.")
    return pgx


@router.get(
    "/antimicrobials",
    summary="Get Empiric Antimicrobial Stewardship Regimen",
    description="Retrieves first-line and alternative empiric antibiotic regimens."
)
async def get_antimicrobial_regimen(syndrome: str = Query(..., description="Infectious syndrome or pathogen")) -> Dict[str, Any]:
    from app.services.offline_data_service import offline_data_service
    abx = offline_data_service.get_empiric_antimicrobial_regimen(syndrome)
    if not abx:
        raise HTTPException(status_code=404, detail=f"Antimicrobial regimen not found for '{syndrome}'.")
    return abx


@router.get(
    "/wikidoc/search",
    summary="Search WikiDoc Peer-Reviewed Clinical Medicine",
    description="Searches 10,000 peer-reviewed clinical summaries from WikiDoc."
)
async def search_wikidoc_knowledge(
    q: str = Query(..., description="Clinical question, symptom, or disease"),
    limit: int = Query(3, ge=1, le=10)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_wikidoc(q, limit=limit)


@router.get(
    "/flashcards/search",
    summary="Search Medical Diagnostic Flashcards & Concepts",
    description="Searches 33,955 clinical diagnostic questions and high-yield concepts."
)
async def search_medical_flashcards_knowledge(
    q: str = Query(..., description="Medical topic or concept"),
    limit: int = Query(3, ge=1, le=10)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_medical_flashcards(q, limit=limit)


@router.get(
    "/healthcaremagic/search",
    summary="Search HealthCareMagic 100k Clinical Consultations",
    description="Searches 112,165 real physician consultations with clinical advice and triage urgency."
)
async def search_healthcaremagic_consultations(
    q: str = Query(..., description="Patient query or symptoms"),
    limit: int = Query(3, ge=1, le=10)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_healthcaremagic(q, limit=limit)


@router.get(
    "/medical-o1/search",
    summary="Search Medical-O1 Complex Clinical Reasoning Traces",
    description="Searches 19,704 step-by-step diagnostic reasoning chain-of-thought traces."
)
async def search_medical_o1_traces(
    q: str = Query(..., description="Clinical scenario or diagnostic dilemma"),
    limit: int = Query(3, ge=1, le=10)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_medical_o1_reasoning(q, limit=limit)


@router.get(
    "/medmcqa/search",
    summary="Search MedMCQA Specialty Board Clinical Questions",
    description="Searches 182,822 questions and clinical reasoning explanations across 21 medical specialties."
)
async def search_medmcqa_questions(
    q: str = Query(..., description="Clinical topic, disease, or medical question"),
    subject: Optional[str] = Query(None, description="Filter by medical subject (e.g., Surgery, Pathology, Pediatrics)"),
    limit: int = Query(3, ge=1, le=10)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_medmcqa(q, subject=subject, limit=limit)


@router.get(
    "/dialogues/search",
    summary="Search AI Medical Chatbot Real Clinical Dialogues",
    description="Searches 256,916 real patient-doctor dialogues."
)
async def search_clinical_dialogues(
    q: str = Query(..., description="Patient concern or symptoms"),
    limit: int = Query(3, ge=1, le=10)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_ai_medical_dialogues(q, limit=limit)


@router.get(
    "/triage/search",
    summary="Search Health Advice & Clinician Triage Guidance",
    description="Searches 8,676 clinician-verified triage guidance and health advice entries."
)
async def search_health_advice_triage(
    q: str = Query(..., description="Symptom or triage inquiry"),
    limit: int = Query(3, ge=1, le=10)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_health_advice(q, limit=limit)


@router.get(
    "/causal/search",
    summary="Search PubMed Causal Pathophysiology Mechanisms",
    description="Searches 2,446 biomedical causal pathophysiology relationships."
)
async def search_causal_mechanisms(
    q: str = Query(..., description="Clinical finding, biomarker, or condition"),
    limit: int = Query(3, ge=1, le=10)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_pubmed_causal(q, limit=limit)


@router.get(
    "/soap-templates/search",
    summary="Search MTS-Dialog Structured Clinical SOAP Notes",
    description="Searches doctor-patient dialogue paired with structured SOAP note sections."
)
async def search_soap_documentation_templates(
    q: str = Query(..., description="Clinical finding or complaint"),
    section: Optional[str] = Query(None, description="Filter by section (e.g., History, Assessment, Plan)"),
    limit: int = Query(3, ge=1, le=10)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_mts_dialog_notes(q, section=section, limit=limit)


@router.get(
    "/vignettes/search",
    summary="Search MedText Internal Medicine Clinical Vignettes",
    description="Searches curated internal medicine clinical case vignettes and diagnostic workups."
)
async def search_clinical_vignettes(
    q: str = Query(..., description="Patient clinical presentation"),
    limit: int = Query(3, ge=1, le=10)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_medtext_vignettes(q, limit=limit)


@router.get(
    "/asclepius/search",
    summary="Search Asclepius Hospital Discharge Summaries & Inpatient Notes",
    description="Searches hospital discharge summaries, clinical reasoning, and hospital courses."
)
async def search_hospital_discharge_notes(
    q: str = Query(..., description="Clinical topic or inpatient condition"),
    limit: int = Query(3, ge=1, le=10)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_asclepius_notes(q, limit=limit)


@router.get(
    "/ddxplus/search",
    summary="Search DDXPlus Differential Diagnosis Simulator (132k cases)",
    description="Instant sub-millisecond FTS5 search across 132,448 synthetic clinical simulator cases with real differential probabilities."
)
async def search_ddxplus_cases(
    q: str = Query(..., description="Pathology or presenting symptoms"),
    limit: int = Query(3, ge=1, le=20)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_ddxplus_differential_cases(q, limit=limit)


@router.get(
    "/diagnosis-encounters/search",
    summary="Search Sajjad Hadi Clinical Diagnosis Encounters (469k records)",
    description="Searches 469,195 symptom-based clinical encounters with instant SQLite FTS5 matching."
)
async def search_diagnosis_encounters(
    q: str = Query(..., description="Symptom text or target diagnosis"),
    limit: int = Query(3, ge=1, le=20)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_clinical_diagnosis_encounters(q, limit=limit)


@router.get(
    "/mayo-clinic/search",
    summary="Search Mayo Clinic Gold-Standard Disease & Symptom Library",
    description="Searches peer-reviewed Mayo Clinic disease monographs, symptoms, causes, and complications."
)
async def search_mayo_clinic_library(
    q: str = Query(..., description="Disease name or symptoms"),
    limit: int = Query(3, ge=1, le=20)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_mayo_clinic_diseases(q, limit=limit)


@router.get(
    "/differential-scenarios/search",
    summary="Search Medical Differential Diagnosis Scenarios",
    description="Searches 1,871 clinical differential diagnosis problem-solving cases with step-by-step reasoning."
)
async def search_differential_scenarios(
    q: str = Query(..., description="Patient clinical presentation"),
    limit: int = Query(3, ge=1, le=20)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_medical_diff_dx_cases(q, limit=limit)


@router.get(
    "/disease-encyclopedia/search",
    summary="Search Shaheer Comprehensive Disease Encyclopedia (253k profiles)",
    description="Searches 253,851 disease profiles with overview, symptoms, when to see doctor, causes, and complications."
)
async def search_disease_encyclopedia(
    q: str = Query(..., description="Disease or presenting symptom"),
    limit: int = Query(3, ge=1, le=20)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_shaheer_disease_encyclopedia(q, limit=limit)


@router.get(
    "/jainam-predictions/search",
    summary="Search Jainam Confidence-Ranked Disease Predictions",
    description="Searches multi-symptom clinical prompt records predicting diseases grouped by confidence levels."
)
async def search_jainam_predictions(
    q: str = Query(..., description="Symptom query"),
    limit: int = Query(3, ge=1, le=20)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_jainam_predictions(q, limit=limit)


@router.get(
    "/open-vignettes/search",
    summary="Search Open Clinical Vignettes Corpus (100k)",
    description="Searches 100,000 peer-reviewed English clinical vignettes with educational diagnostic scores."
)
async def search_open_vignettes(
    q: str = Query(..., description="Clinical case details or findings"),
    limit: int = Query(3, ge=1, le=20)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_open_clinical_vignettes(q, limit=limit)


@router.get(
    "/clinical-scenarios/search",
    summary="Search Clinical DDx Scenarios Benchmark",
    description="Searches Shuyue J clinical differential diagnosis scenarios with diagnostic ranking outputs."
)
async def search_clinical_ddx_scenarios(
    q: str = Query(..., description="Clinical presentation or symptom constellation"),
    limit: int = Query(3, ge=1, le=20)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_differential_scenarios(q, limit=limit)


@router.get(
    "/medical-diagnosis-20k/search",
    summary="Search Medical Diagnosis 20K Encounters",
    description="Searches 20,000 real medical diagnosis encounters linking patient presentations to confirmed conditions."
)
async def search_medical_diagnosis_20k_encounters(
    q: str = Query(..., description="Patient clinical query or diagnosis"),
    limit: int = Query(3, ge=1, le=20)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_medical_diagnosis_20k(q, limit=limit)


@router.get(
    "/diagnostic-cot/search",
    summary="Search Chain-of-Thought Diagnostic Reasoning",
    description="Searches step-by-step diagnostic reasoning trajectories dissecting clinical signs."
)
async def search_diagnostic_cot_traces(
    q: str = Query(..., description="Diagnostic problem or symptom query"),
    limit: int = Query(3, ge=1, le=20)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_medical_diagnosis_cot(q, limit=limit)


@router.get(
    "/chronic-organ-risk/search",
    summary="Search Chronic Organ-Specific Disease Risk Predictors",
    description="Searches across 100k diabetes presentations, stroke incidence risk, and chronic kidney disease predictions."
)
async def search_chronic_organ_risk_predictions(
    q: str = Query(..., description="Risk factors, biomarkers, or conditions"),
    limit: int = Query(3, ge=1, le=20)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_chronic_organ_risk(q, limit=limit)


@router.get(
    "/universal-warehouse/search",
    summary="Universal Search Across All 76 Offline Datasets",
    description="Search any offline dataset in D:\\OFFLINE DATA by its directory name using SQLite FTS5."
)
async def search_universal_warehouse_dataset(
    dataset: str = Query(..., description="Dataset directory name (e.g. 'diabetes_clinical_risk_prediction', 'rare_diseases_hpo')"),
    q: str = Query(..., description="Search query keywords"),
    limit: int = Query(5, ge=1, le=50)
) -> List[Dict[str, Any]]:
    from app.services.offline_data_service import offline_data_service
    return offline_data_service.search_universal_warehouse(dataset, q, limit=limit)





