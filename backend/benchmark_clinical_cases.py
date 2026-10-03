from app.services.realtime_prediction_service import realtime_prediction_service

clinical_cases = [
    # 1. Classic Real-Time Outbreak & Tropical Diseases
    ("dengue", ["Dengue Fever", "Dengue"]),
    ("sudden high fever, severe retro-orbital headache, joint and bone pain, rash", ["Dengue Fever"]),
    ("malaria", ["Malaria"]),
    ("fever, chills, rigors, sweating, headache", ["Malaria"]),
    ("typhoid", ["Typhoid Fever"]),
    ("step-ladder fever, persistent abdominal pain, rose spots, relative bradycardia", ["Typhoid Fever"]),
    ("tuberculosis", ["Tuberculosis"]),
    ("chronic cough > 3 weeks, hemoptysis, night sweats, weight loss, fever", ["Tuberculosis"]),
    ("covid", ["COVID-19"]),
    ("fever, dry cough, loss of smell, loss of taste, fatigue", ["COVID-19"]),
    
    # 2. Classic Everyday Clinical Presentations
    ("type 2 diabetes", ["Type 2 Diabetes", "Diabetes"]),
    ("polyuria, polydipsia, excessive thirst, weight loss, fatigue", ["Type 2 Diabetes", "Diabetic Ketoacidosis"]),
    ("hypertension", ["Hypertension"]),
    ("persistent elevated blood pressure 160/100, morning headache, dizziness", ["Hypertension"]),
    ("asthma", ["Asthma"]),
    ("wheezing, episodic shortness of breath, chest tightness, nighttime cough", ["Asthma"]),
    ("pneumonia", ["Pneumonia"]),
    ("productive cough with purulent rust-colored sputum, high fever, pleuritic chest pain", ["Pneumonia"]),
    ("heart attack", ["Myocardial Infarction", "Acute Coronary Syndrome"]),
    ("crushing substernal chest pain radiating to left arm, diaphoresis, nausea", ["Myocardial Infarction"]),
    ("stroke", ["Stroke", "Ischemic Stroke"]),
    ("sudden onset right-sided facial droop, slurred speech, right arm weakness", ["Stroke", "Ischemic Stroke"]),
    ("appendicitis", ["Appendicitis"]),
    ("right lower quadrant abdominal pain, anorexia, low-grade fever, nausea", ["Appendicitis"]),
    ("migraine", ["Migraine"]),
    ("unilateral pulsating throbbing headache, photophobia, phonophobia, nausea", ["Migraine"]),
    ("gerd", ["GERD", "Gastroesophageal Reflux"]),
    ("burning retrosternal chest pain after eating, acid regurgitation, heartburn", ["GERD"]),
    ("urinary tract infection", ["Urinary Tract Infection", "UTI"]),
    ("dysuria, urinary frequency, suprapubic tenderness, cloudy urine", ["Urinary Tract Infection"]),
    ("kidney stones", ["Nephrolithiasis", "Kidney Stones"]),
    ("severe sudden colicky flank pain radiating to groin, hematuria", ["Nephrolithiasis"]),
    ("iron deficiency anemia", ["Iron Deficiency Anemia", "Anemia"]),
    ("chronic fatigue, pallor, brittle spoon nails, pica, shortness of breath on exertion", ["Anemia"]),
    ("osteoarthritis", ["Osteoarthritis"]),
    ("bilateral knee joint pain worsening with walking, morning stiffness < 30 minutes, crepitus", ["Osteoarthritis"]),
    ("gout", ["Gout"]),
    ("acute excruciating pain and swelling of first metatarsophalangeal big toe joint, podagra", ["Gout"]),
    ("hypothyroidism", ["Hypothyroidism"]),
    ("weight gain, cold intolerance, constipation, fatigue, dry coarse skin, bradycardia", ["Hypothyroidism"]),
    ("common cold", ["Common Cold", "Viral Upper Respiratory Infection"]),
    ("sneezing, nasal congestion, runny nose, scratchy sore throat, low-grade fever", ["Common Cold"]),

    # 3. Additional Tropical Outbreaks & Epidemic Conditions
    ("chikungunya", ["Chikungunya"]),
    ("high fever, severe debilitating bilateral joint pain, petechial rash, conjunctivitis", ["Chikungunya"]),
    ("zika", ["Zika Virus", "Zika"]),
    ("low-grade fever, pruritic maculopapular rash, non-purulent conjunctivitis, arthralgia", ["Zika Virus", "Zika"]),
    ("leptospirosis", ["Leptospirosis"]),
    ("fever, severe calf muscle tenderness, conjunctival suffusion, jaundice, dark urine", ["Leptospirosis"]),
    ("cholera", ["Cholera"]),
    ("sudden profuse painless watery rice-water diarrhea, severe dehydration, sunken eyes", ["Cholera"]),

    # 4. Critical Emergencies & Surgical Pathology
    ("pulmonary embolism", ["Pulmonary Embolism"]),
    ("sudden onset pleuritic chest pain, tachypnea, hemoptysis, unilateral leg swelling", ["Pulmonary Embolism"]),
    ("aortic dissection", ["Aortic Dissection"]),
    ("sudden tearing chest pain radiating to back between shoulder blades, blood pressure discrepancy", ["Aortic Dissection"]),
    ("diabetic ketoacidosis", ["Diabetic Ketoacidosis"]),
    ("kussmaul breathing, fruity acetone breath odor, vomiting, abdominal pain, high blood glucose", ["Diabetic Ketoacidosis"]),
    ("acute pancreatitis", ["Acute Pancreatitis", "Pancreatitis"]),
    ("severe constant epigastric pain radiating to back, relieved by leaning forward, vomiting, elevated serum lipase", ["Pancreatitis"]),
    ("acute cholecystitis", ["Acute Cholecystitis", "Cholecystitis"]),
    ("right upper quadrant abdominal pain after fatty meal, murphy sign, fever, leukocytosis", ["Cholecystitis"]),

    # 5. Chronic General Medicine, Neuropsychiatry & Dermatology
    ("chronic kidney disease", ["Chronic Kidney Disease", "CKD"]),
    ("bilateral leg edema, fatigue, anorexia, frothy foamy urine, elevated serum creatinine", ["Chronic Kidney Disease", "CKD"]),
    ("epilepsy", ["Epilepsy", "Seizure Disorder"]),
    ("generalized tonic-clonic seizure, post-ictal confusion, tongue biting, urinary incontinence", ["Epilepsy", "Seizure Disorder"]),
    ("depression", ["Major Depressive Disorder", "Depression"]),
    ("persistent sad mood > 2 weeks, anhedonia, insomnia, loss of appetite, fatigue, suicidal ideation", ["Major Depressive Disorder", "Depression"]),
    ("anxiety", ["Generalized Anxiety Disorder", "Anxiety"]),
    ("excessive uncontrollable worry > 6 months, restlessness, muscle tension, fatigue, irritability", ["Generalized Anxiety Disorder", "Anxiety"]),
    ("atopic dermatitis", ["Atopic Dermatitis", "Eczema"]),
    ("intense pruritus, erythematous dry scaly plaques on flexural creases, skin lichenification", ["Atopic Dermatitis", "Eczema"]),
    ("psoriasis", ["Psoriasis"]),
    ("well-demarcated erythematous plaques with silvery white scales on extensor surfaces of knees and elbows", ["Psoriasis"]),
    ("acute otitis media", ["Acute Otitis Media"]),
    ("severe otalgia, bulging erythematous tympanic membrane, fever, decreased hearing in child", ["Acute Otitis Media"]),
    ("cellulitis", ["Cellulitis"]),
    ("unilateral spreading erythema, warmth, local induration, tenderness on lower extremity", ["Cellulitis"]),
    ("shingles", ["Herpes Zoster", "Shingles"]),
    ("unilateral painful dermatomal vesicular rash, sharp burning nerve pain", ["Herpes Zoster", "Shingles"]),
    ("strep throat", ["Streptococcal Pharyngitis", "Strep Throat"]),
    ("severe sore throat, tonsillar exudate, tender anterior cervical lymphadenopathy, fever, absence of cough", ["Streptococcal Pharyngitis", "Strep Throat"]),
]

failures = []
successes = []

for query, expected_keywords in clinical_cases:
    res = realtime_prediction_service.predict(query)
    cands = res.get("top_candidates", [])
    top3_names = [c["disease"] for c in cands[:3]]
    
    # Check if any expected keyword is in any of top 3 candidate names
    matched = False
    for expected in expected_keywords:
        if any(expected.lower() in d.lower() for d in top3_names):
            matched = True
            break
            
    if matched:
        successes.append((query, top3_names))
    else:
        failures.append((query, expected_keywords, top3_names))

print(f"TOTAL CASES: {len(clinical_cases)}")
print(f"PASSED: {len(successes)}")
print(f"FAILED: {len(failures)}")
print("\n--- DETAILED FAILURES ---")
for query, expected, top3 in failures:
    print(f"QUERY: '{query}'")
    print(f"  EXPECTED ONE OF: {expected}")
    print(f"  ACTUAL TOP 3: {top3}\n")
