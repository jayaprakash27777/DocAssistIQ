import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.realtime_prediction_service import RealtimePredictionService

cases = [
    {
        "name": "Appendicitis",
        "input": "Right lower quadrant abdominal pain, anorexia, low-grade fever, nausea, McBurney sign tenderness",
        "expected": ["Appendicitis", "Acute Appendicitis"]
    },
    {
        "name": "STEMI",
        "input": "Crushing retrosternal chest pain radiating to left arm, diaphoresis, shortness of breath, ST elevation in anterior leads",
        "expected": ["Acute Myocardial Infarction (STEMI/NSTEMI)", "Acute Coronary Syndrome (STEMI/NSTEMI)", "Myocardial Infarction", "Coronary Artery Disease"]
    },
    {
        "name": "Meningitis",
        "input": "High fever, severe headache, nuchal rigidity, photophobia, positive Kernig and Brudzinski signs",
        "expected": ["Meningococcal Disease / Meningococcemia (with Meningitis)", "Bacterial Meningitis", "Meningitis"]
    },
    {
        "name": "Tension Pneumothorax",
        "input": "Sudden onset severe dyspnea, right-sided chest pain, absent breath sounds on right, tracheal deviation to left, hypotension",
        "expected": ["Tension Pneumothorax", "Pneumothorax"]
    },
    {
        "name": "DKA",
        "input": "Polyuria, polydipsia, fruity breath odor, Kussmaul respirations, nausea, vomiting, glucose 450",
        "expected": ["Diabetic Ketoacidosis (DKA)", "Diabetic Ketoacidosis", "Type 1 Diabetes Mellitus"]
    },
    {
        "name": "Pulmonary Embolism",
        "input": "Sudden onset pleuritic chest pain, tachypnea, tachycardia, hemoptysis, unilateral leg swelling",
        "expected": ["Pulmonary Embolism (PE)", "Pulmonary Embolism"]
    },
    {
        "name": "Dengue Fever",
        "input": "High fever, severe retro-orbital headache, severe myalgia, arthralgia, petechiae, positive tourniquet test",
        "expected": ["Dengue Fever", "Dengue Hemorrhagic Fever", "Dengue with Warning Signs / Impending Severe Dengue"]
    },
    {
        "name": "Acute Intermittent Porphyria",
        "input": "Severe colicky abdominal pain without peritoneal signs, port-wine dark reddish-brown urine, peripheral neuropathy, hyponatremia",
        "expected": ["Acute Intermittent Porphyria (AIP)", "Acute Porphyric Neurovisceral Crisis (AIP)", "Acute Intermittent Porphyria"]
    },
    {
        "name": "Guillain-Barré Syndrome",
        "input": "Ascending symmetrical muscle weakness starting in legs, absent deep tendon reflexes, antecedent diarrheal illness",
        "expected": ["Guillain-Barré Syndrome (AIDP / Miller Fisher)", "Guillain-Barré Syndrome", "Guillain-Barre Syndrome"]
    },
    {
        "name": "SLE",
        "input": "Malar rash sparing nasolabial folds, photosensitivity, symmetric polyarthritis, oral ulcers, positive ANA",
        "expected": ["Systemic Lupus Erythematosus (SLE)", "Systemic Lupus Erythematosus"]
    },
    {
        "name": "Iron Deficiency Anemia",
        "input": "Fatigue, pallor, brittle spoon nails, koilonychia, craving ice (pica), microcytic hypochromic red cells",
        "expected": ["Iron Deficiency Anemia"]
    },
    {
        "name": "Acute Angle-Closure Glaucoma",
        "input": "Severe right eye pain, headache, seeing halos around lights, nausea, fixed mid-dilated pupil, steamy cornea",
        "expected": ["Acute Angle-Closure Glaucoma"]
    },
    {
        "name": "COVID-19",
        "input": "Fever, dry persistent cough, sudden loss of smell and taste (anosmia and ageusia), fatigue",
        "expected": ["COVID-19", "Severe COVID-19 Pneumonia"]
    },
    {
        "name": "Graves Disease / Hyperthyroidism",
        "input": "Palpitations, heat intolerance, unintentional weight loss, fine hand tremor, exophthalmos (proptosis), diffuse goiter",
        "expected": ["Hyperthyroidism / Thyroid Storm", "Hyperthyroidism / Graves Disease", "Graves Disease", "Hyperthyroidism"]
    },
    {
        "name": "Gout",
        "input": "Sudden excruciating pain, swelling, erythema, and warmth in first metatarsophalangeal big toe joint (podagra)",
        "expected": ["Gout (Acute Gouty Arthritis)", "Gout"]
    },
    {
        "name": "Malaria",
        "input": ["paroxysmal shaking chills", "cyclic fever spikes every 48 hours", "travel to Nigeria", "splenomegaly", "hemolytic anemia"],
        "expected": ["Malaria (Plasmodium falciparum)", "Malaria (Plasmodium vivax)", "Severe Malaria / Cerebral Malaria"]
    },
    {
        "name": "Aortic Dissection",
        "input": "Sudden tearing chest pain radiating to back between shoulder blades, blood pressure discrepancy between arms, pulse deficit",
        "expected": ["Acute Aortic Dissection", "Aortic Dissection"]
    },
    {
        "name": "Preeclampsia",
        "input": "Pregnant at 34 weeks gestation, BP 170/110, severe persistent frontal headache, visual disturbances, 3+ proteinuria, hyperreflexia with clonus",
        "expected": ["Preeclampsia with Severe Features", "Preeclampsia with Severe Features / Impending Eclampsia", "Preeclampsia"]
    },
    {
        "name": "Testicular Torsion",
        "input": "Sudden severe unilateral testicular pain, scrotal swelling, absent cremasteric reflex, high-riding testicle, nausea",
        "expected": ["Testicular Torsion"]
    },
    {
        "name": "Cardiac Tamponade",
        "input": "Hypotension, jugular venous distension, muffled heart sounds, pulsus paradoxus",
        "expected": ["Cardiac Tamponade"]
    }
]

def main():
    svc = RealtimePredictionService()
    passed = 0
    top1_count = 0
    for idx, c in enumerate(cases, 1):
        res = svc.predict(c["input"], top_k=5)
        candidates = [cand.get("condition") or cand.get("disease") or cand.get("candidate") for cand in res.get("top_candidates", [])]
        matched = any(exp in candidates for exp in c["expected"])
        top1 = candidates[0] if candidates else "None"
        top1_match = any(exp == top1 for exp in c["expected"])
        if matched:
            passed += 1
            if top1_match:
                top1_count += 1
                status = "PASS (Top 1)"
            else:
                status = "PASS (In Top 5)"
        else:
            status = "FAIL"
        print(f"Case {idx:02d}: {c['name']:32s} -> {status} [Top 1: {top1}]")

    print(f"\nOverall Top-5 accuracy: {passed}/{len(cases)} ({passed/len(cases)*100:.1f}%)")
    print(f"Overall Top-1 accuracy: {top1_count}/{len(cases)} ({top1_count/len(cases)*100:.1f}%)")
    assert passed == len(cases), f"Expected 100% pass, got {passed}/{len(cases)}"

if __name__ == "__main__":
    main()
