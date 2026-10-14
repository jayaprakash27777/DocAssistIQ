import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

from app.services.clinical_note_parser import clinical_note_parser
from app.services.bayesian_diagnostic_engine import bayesian_diagnostic_engine
from app.services.global_disease_matrix_service import global_disease_matrix_service

case1 = """A 29-year-old woman presents with four months of fatigue, reduced exercise tolerance, intermittent headaches, and light-headedness when standing. She reports heavy menstrual bleeding lasting eight to nine days each cycle and occasionally craving ice. Examination shows conjunctival pallor, a pulse of 102/min, and no jaundice or splenomegaly. Hemoglobin is 8.7 g/dL, mean corpuscular volume is 68 fL, and the red-cell distribution width is elevated. She eats little meat and has no reported gastrointestinal bleeding."""

parsed = clinical_note_parser.parse(case1)
findings = parsed.get("positive_findings", [])
print("Findings:", findings)

diffs = bayesian_diagnostic_engine.rank_differentials(findings, top_k=10)
print("\n=== BAYESIAN ENGINE RESULTS ===")
for d in diffs:
    print(f"Disease: {d.disease_name} (ICD10: {d.icd10}) | Posterior: {d.posterior_probability:.3f} | Prior: {d.prior_prevalence:.4f} | LR+: {d.composite_likelihood_ratio:.2f} | Matched: {d.matched_manifestations}")
    if d.discriminative_tests:
        print(f"   Discriminative tests: {[t.test_name for t in d.discriminative_tests[:2]]}")

matrix_matches = global_disease_matrix_service.search_by_manifestations(findings, top_k=10)
print("\n=== GLOBAL MATRIX MATCHES ===")
for m in matrix_matches:
    print(f"Disease: {m.get('disease_name')} | Score: {m.get('match_score')} | Matched: {m.get('matched_manifestations')}")
