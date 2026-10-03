import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, 'backend')
from app.services.realtime_prediction_service import realtime_prediction_service

note1 = """HPI: A 42-year-old male presents with a 4-day history of acute high-grade fever, severe debilitating headache, prominent retro-orbital pain, generalized arthralgias, and intense myalgias. He reports marked photophobia and nausea.
PMH: Hypertension on amlodipine 5mg daily. No prior surgical history.
Social / Travel History: Returned 6 days ago from an eco-tourism trip to the Peruvian Amazon and Iquitos region, Peru. Reports frequent midge and mosquito bites despite insect repellent.
Physical Exam: T 39.1C, HR 108, BP 118/74, SpO2 98% RA. Alert, oriented x 3, in moderate discomfort. Conjunctival injection bilaterally without discharge. Diffuse maculopapular rash on trunk and arms with scattered petechiae. No nuchal rigidity. Abdomen soft, non-tender.
Labs: WBC 3.2 (leukopenia), Platelets 94,000 (thrombocytopenia), ALT 68, AST 74."""

note2 = """CHIEF COMPLAINT: Acute altered mental status and high fever.
HISTORY OF PRESENT ILLNESS: A 38-year-old agricultural laborer from Malappuram / Kozhikode district, Kerala, India is brought to the emergency department with a 3-day history of rapidly worsening fever, profound drowsiness, and confusion. Over the past 12 hours, the family noted involuntary jerking movements of his upper extremities (segmental myoclonus) and progressive difficulty breathing. The patient frequently consumed raw date palm sap harvested locally.
PHYSICAL EXAMINATION: Temperature 39.8 C, Heart Rate 118 bpm, BP 142/88 mmHg, Respiratory Rate 28/min, SpO2 91% on room air. Neurological exam reveals GCS 9 (E2V3M4), brisk bilateral papilledema, marked neck stiffness, spontaneous myoclonic jerks of the right arm, and generalized hypo/areflexia in lower extremities. Coarse bilateral crackles on lung auscultation.
DIAGNOSTIC WORKUP: Non-contrast head CT shows subtle bilateral temporal hypodensities and cerebral edema. CSF opening pressure elevated at 230 mmH2O with lymphocytic pleocytosis (85 cells/uL, 90% lymphocytes), protein 120 mg/dL, normal glucose."""

for label, note in [("Long Note 1 (Peru Amazon Oropouche)", note1), ("Long Note 2 (Kerala Kozhikode Nipah)", note2)]:
    print(f"\n==========================================")
    print(f"EVALUATING: {label}")
    print(f"==========================================")
    res = realtime_prediction_service.predict(note)
    print("Status:", res.get("status"))
    print("Outbreak Detected:", res.get("outbreak_detected"))
    print("Outbreak Summary:", res.get("outbreak_summary"))
    print("Travel / Geo History:", res.get("travel_history"))
    print("Extracted Findings:", res.get("extracted_findings")[:8])
    print("Top Candidates:")
    for c in res.get("top_candidates", [])[:5]:
        print(f" - {c['disease']} ({c['score']}) [Outbreak: {c.get('is_outbreak_match')}] Badge: {c.get('outbreak_badge')}")
        print(f"   Immediate tests: {c.get('immediate_tests', [])[:2]}")
        print(f"   Medications: {c.get('recommended_medications', [])[:2]}")
