"""DocAssistIQ — Comprehensive Clinical Disease Registry (Part 2: Expanded Specialties).

Covers emergency medicine, cardiology, pulmonology, gastroenterology, nephrology,
neurology, rheumatology, and infectious diseases.
"""

from typing import Dict, Any

CLINICAL_DISEASE_REGISTRY_PART2: Dict[str, Dict[str, Any]] = {
    "Acute Angle-Closure Glaucoma": {
        "icd10": "H40.20", "icd11": "9C61.2", "category": "Ophthalmology / Emergency", "triage": "EMERGENT",
        "immediate_tests": [
            "Tonometry (STAT measurement of Intraocular Pressure: IOP typically >40-60 mmHg; normal 10-21)",
            "Slit Lamp Biomicroscopy (shallow anterior chamber, corneal steamy edema, fixed mid-dilated pupil)",
            "Gonioscopy (Gold standard: confirms complete 360-degree closed iridocorneal angle in both eyes)",
            "Visual Acuity Assessment (marked visual reduction / halo visualization around lights)"
        ],
        "recommended_investigations": [
            "Applanation Tonometry (serial monitoring of IOP response every 30-60 min)",
            "Gonioscopy of bilateral eyes (fellow eye is anatomically predisposed)",
            "Central Corneal Pachymetry and Visual Field Perimetry (post-acute evaluation)"
        ],
        "recommended_medications": [
            "Topical Beta-Blocker: Timolol 0.5% ophthalmic solution 1 drop STAT (reduces aqueous production)",
            "Topical Alpha-2 Agonist: Apraclonidine 1% (or Brimonidine 0.2%) ophthalmic solution 1 drop STAT",
            "Topical Miotic Agent: Pilocarpine 1% or 2% ophthalmic solution 1 drop (administer once IOP <30 mmHg to pull peripheral iris away from trabecular meshwork)",
            "Systemic Carbonic Anhydrase Inhibitor: Acetazolamide 500 mg IV (or PO) STAT, then 250 mg q6h",
            "Osmotic Diuretic (Refractory IOP >50): IV Mannitol 1.0-2.0 g/kg IV infusion over 30-45 minutes"
        ],
        "first_line_treatment": "Immediate medical IOP reduction with topical Timolol, Apraclonidine, Pilocarpine, and IV Acetazolamide, followed by definitive Bilateral Laser Peripheral Iridotomy (LPI).",
        "treatment_summary": "Ophthalmic emergency; permanent vision loss can occur within hours. Lower IOP medically immediately, then urgent ophthalmology consultation for bilateral laser iridotomy.",
        "disease_intelligence": {
            "disease_name": "Acute Angle-Closure Glaucoma (AACG)",
            "etiology": "Pupillary block in anatomically predisposed eyes with shallow anterior chambers; triggered by mydriasis (dim lighting, anticholinergics, sympathomimetics).",
            "icd10_code": "H40.20", "icd11_code": "9C61.2",
            "cardinal_symptoms": ["Severe, agonizing unilateral eye and periorbital pain", "Marked blurring of vision with colored rainbow halos around lights", "Nausea and profuse vomiting (frequently misdiagnosed as acute abdomen or migraine)", "Ciliary flush / deep conjunctival injection", "Fixed, mid-dilated, non-reactive pupil with cloudy steamy cornea"],
            "red_flags": ["Complete irreversible optic nerve ischemia and permanent blindness within 24-48 hours", "Extreme IOP >60-80 mmHg with central retinal artery occlusion"],
            "pathophysiology": "Pupillary margin contacts anterior lens capsule, obstructing aqueous humor flow from posterior to anterior chamber; relative pressure builds behind the iris, bowing it forward (iris bombe) to mechanically block the trabecular meshwork.",
            "clinical_pearl": "Patients frequently present to the ED with headache, nausea, and severe vomiting and are misdiagnosed with food poisoning, migraine, or acute gastroenteritis. Always check the pupils and palpate eye firmness!"
        },
        "pearl": "Severe unilateral eye pain + nausea + cloudy cornea + mid-dilated fixed pupil + IOP >40. Medical cocktail: Timolol + Apraclonidine + IV Acetazolamide -> urgent Bilateral Laser Iridotomy."
    },

    "Acute Pericarditis": {
        "icd10": "I30.9", "icd11": "BB20", "category": "Cardiology / Emergency", "triage": "URGENT",
        "immediate_tests": [
            "12-Lead Electrocardiogram (Classic: widespread concave-upward ST elevation in almost all leads with reciprocal ST depression and PR depression in aVR)",
            "High-Sensitivity Cardiac Troponin (elevated in 30-50% indicating myopericarditis)",
            "Echocardiogram (transthoracic: evaluates pericardial effusion and rules out cardiac tamponade)",
            "Inflammatory Biomarkers: C-Reactive Protein (CRP) and ESR (markedly elevated; tracks treatment response)",
            "Complete Blood Count and Basic Metabolic Panel (excludes uremia)"
        ],
        "recommended_investigations": [
            "12-Lead ECG (Stage 1: diffuse ST elevation / PR depression; Stage 2: normalization; Stage 3: inverted T waves; Stage 4: resolution)",
            "Transthoracic Echocardiogram (confirms or excludes effusion and evaluates RV diastolic collapse)",
            "Serial CRP levels (guides duration of anti-inflammatory therapy until normalized)",
            "Chest Radiograph (usually normal unless large effusion or underlying lung pathology)",
            "Viral Serology / Autoimmune panel (ANA, RF) in refractory or recurrent cases"
        ],
        "recommended_medications": [
            "First-Line High-Dose NSAID: Ibuprofen 600-800 mg PO TID with meals for 1-2 weeks (OR Indomethacin 50 mg PO TID) tapered weekly",
            "Synergistic Anti-Recurrence Agent: Colchicine 0.5-0.6 mg PO daily (if <70 kg) or BID (if >=70 kg) for 3 months (reduces recurrence rate by >50%)",
            "Gastroprotection: Omeprazole 20-40 mg PO daily for gastric ulcer prophylaxis during high-dose NSAIDs",
            "Post-MI Pericarditis (Dressler syndrome): Aspirin 650-1000 mg PO q6-8h instead of other NSAIDs (which may impair myocardial scar healing)",
            "Glucocorticoids (Restricted): Prednisone 0.25-0.5 mg/kg/day ONLY if contraindication/failure to NSAIDs + Colchicine (steroids increase recurrence risk)"
        ],
        "first_line_treatment": "High-dose NSAID (Ibuprofen 600-800mg TID) PLUS Colchicine 0.5-0.6mg daily for 3 months; avoid systemic steroids unless autoimmune etiology.",
        "treatment_summary": "Diagnosis requires 2 of 4: pleuritic chest pain relieved by leaning forward, pericardial friction rub, typical ECG changes, new/worsening pericardial effusion. Colchicine prevents debilitating recurrences.",
        "disease_intelligence": {
            "disease_name": "Acute Pericarditis",
            "etiology": "Viral infection (Coxsackievirus, Echovirus, Adenovirus, SARS-CoV-2), idiopathic (85%), post-MI (Dressler syndrome), uremia, autoimmune (SLE, RA), neoplastic.",
            "icd10_code": "I30.9", "icd11_code": "BB20",
            "cardinal_symptoms": ["Sharp, pleuritic, retrosternal chest pain radiating to the left trapezius ridge", "Pain worsens when lying supine or coughing and improves significantly when sitting up and leaning forward", "Pericardial friction rub on auscultation (high-pitched, scratching sound heard best at left lower sternal border with patient leaning forward)", "Low-grade fever and tachycardia"],
            "red_flags": ["Cardiac Tamponade (hypotension, JVD, pulsus paradoxus >10 mmHg)", "Myopericarditis with acute heart failure or severe ventricular arrhythmias", "Large pericardial effusion (>20mm on echo)"],
            "pathophysiology": "Inflammation of the visceral and parietal layers of the pericardium results in fibrinous exudate, rubbing of inflamed serosal surfaces, and fluid accumulation within the pericardial space.",
            "clinical_pearl": "Pain radiating to the bilateral trapezius ridge is virtually pathognomonic for pericarditis because the phrenic nerve innervates both the pericardium and the trapezius dermatome (C3-C5)."
        },
        "pearl": "Sharp chest pain relieved by leaning forward + friction rub + diffuse ST elevation with PR depression. Ibuprofen 800mg TID + Colchicine for 3 months (prevents recurrences). Avoid steroids."
    },

    "Asthma Exacerbation": {
        "icd10": "J45.901", "icd11": "CA23.0", "category": "Pulmonology / Emergency", "triage": "EMERGENT",
        "immediate_tests": [
            "Peak Expiratory Flow Rate (PEFR / FEV1: <50% predicted indicates severe exacerbation; 50-70% moderate)",
            "Continuous Pulse Oximetry (target SpO2 93-95% in adults; 94-98% in children)",
            "Arterial or Venous Blood Gas (STAT in severe exacerbation: normal or rising PaCO2 >=40-45 mmHg warns of respiratory muscle fatigue and impending respiratory arrest)",
            "12-Lead Electrocardiogram (sinus tachycardia, right axis deviation in severe strain)",
            "Chest Radiograph (PA/Lateral: indicated if pneumothorax, pneumomediastinum, or pneumonia suspected)"
        ],
        "recommended_investigations": [
            "Serial PEFR measurements pre- and post-bronchodilator therapy (every 30-60 min)",
            "Arterial Blood Gas (monitoring ventilation; hypocarbia PaCO2 <35 is expected early; normocarbia is a RED FLAG)",
            "Complete Blood Count (eosinophilia, leukocytosis)",
            "Serum Potassium (beta-agonist therapy causes transient hypokalemia)"
        ],
        "recommended_medications": [
            "Short-Acting Beta-2 Agonist (SABA): Inhaled Albuterol 2.5-5.0 mg via nebulizer q20min for 3 doses, then 2.5-5 mg q1-4h (or 4-8 puffs via MDI with spacer)",
            "Short-Acting Muscarinic Antagonist (SAMA): Inhaled Ipratropium bromide 0.5 mg nebulized with Albuterol q20min for 3 doses (combining SAMA + SABA significantly reduces hospital admissions)",
            "Systemic Corticosteroids (Administer within 1 hour): Oral Prednisone 40-50 mg daily for 5-7 days (OR IV Methylprednisolone 60-125 mg IV if severe/vomiting)",
            "IV Magnesium Sulfate (Severe / Refractory Exacerbation): Magnesium Sulfate 2.0 g IV infusion in 100 mL saline over 20 minutes (potent bronchodilator for FEV1 <40%)",
            "Supplemental Oxygen: Titrated via nasal cannula or mask to maintain SpO2 93-95%"
        ],
        "first_line_treatment": "Inhaled Albuterol + Ipratropium nebulizations q20min x3 doses + systemic oral Prednisone 40-50mg + supplemental oxygen; add IV Magnesium Sulfate 2g if PEFR <40-50%.",
        "treatment_summary": "Early administration of systemic corticosteroids accelerates resolution and prevents relapse. In severe exacerbations, a 'silent chest' or normal PaCO2 indicates respiratory muscle exhaustion requiring ICU admission.",
        "disease_intelligence": {
            "disease_name": "Acute Asthma Exacerbation (Status Asthmaticus)",
            "etiology": "Viral upper respiratory infections (rhinovirus 80%), allergen exposure, cold air, exercise, NSAID/aspirin ingestion, medication non-adherence.",
            "icd10_code": "J45.901", "icd11_code": "CA23.0",
            "cardinal_symptoms": ["Severe expiratory wheezing and prolonged expiratory phase", "Acute shortness of breath, chest tightness, and intractable dry cough", "Accessory muscle use (sternocleidomastoid, intercostal indrawing)", "Tachypnea (RR >25-30 bpm) and inability to speak in complete sentences ('words between breaths')", "Pulsus paradoxus >12-15 mmHg"],
            "red_flags": ["'Silent Chest' (severe bronchospasm with airflow too low to generate audible wheezing — impending asphyxiation)", "Normal or Elevated PaCO2 on ABG (indicates exhausted ventilatory pump)", "Altered mental status / drowsy / cyanosis", "Pneumothorax / pneumomediastinum"],
            "pathophysiology": "Acute contraction of bronchial smooth muscle, hypersecretion of thick tenacious mucus plugs, and airway mucosal edema and eosinophilic infiltration, resulting in air trapping and dynamic hyperinflation.",
            "clinical_pearl": "A 'normal' PaCO2 (40 mmHg) in an acutely tachypneic asthmatic is NOT reassuring — it is an ominous sign of impending respiratory arrest. The patient should be blowing off CO2 (PaCO2 <30); normocarbia means they are tiring out."
        },
        "pearl": "Albuterol + Ipratropium nebs q20m x3 + oral Prednisone 50mg STAT + O2 target 93-95%. A 'normal' PaCO2 on ABG or a 'silent chest' warns of imminent respiratory arrest -> IV Magnesium 2g."
    },

    "Deep Vein Thrombosis (DVT)": {
        "icd10": "I82.40", "icd11": "BD71", "category": "Vascular / Hematology", "triage": "URGENT",
        "immediate_tests": [
            "Wells Clinical Score for DVT (risk stratification: low, moderate, high probability)",
            "Venous Duplex Compression Ultrasound of Lower Extremity (Gold Standard: non-compressible femoral/popliteal vein with absent color flow)",
            "High-Sensitivity D-Dimer Assay (highly sensitive: D-Dimer <500 ng/mL effectively rules out DVT in low/moderate Wells score)",
            "Complete Blood Count (baseline platelets before anticoagulation)",
            "Basic Metabolic Panel (Serum Creatinine and eGFR — essential for DOAC selection and dosing)"
        ],
        "recommended_investigations": [
            "Complete Venous Duplex Ultrasound (common femoral, deep femoral, popliteal, calf veins)",
            "Coagulation Studies (PT/INR, aPTT, baseline prior to therapy)",
            "Screening for Pulmonary Embolism (Chest CTPA if dyspnea, pleuritic pain, or tachycardia present)",
            "Thrombophilia Evaluation (Factor V Leiden, Prothrombin G20210A, Antiphospholipid antibodies — test >=6 weeks AFTER acute event)",
            "Age-Appropriate Malignancy Screening (occult cancer present in 10% of unprovoked DVTs)"
        ],
        "recommended_medications": [
            "First-Line Direct Oral Anticoagulant (DOAC): Apixaban (Eliquis) 10 mg PO BID for 7 days, followed by 5 mg PO BID for minimum 3-6 months",
            "Alternative DOAC: Rivaroxaban (Xarelto) 15 mg PO BID with food for 21 days, followed by 20 mg PO daily with food",
            "Parenteral Lead-In DOAC Regimen: Enoxaparin 1 mg/kg SC q12h (or Fondaparinux) for 5-10 days followed by Dabigatran 150 mg BID (or Edoxaban 60 mg daily)",
            "Severe Renal Impairment (CrCl <15-30 mL/min): Unfractionated Heparin infusion bridged to Warfarin (target INR 2.0-3.0)",
            "Phlegmasia Cerulea Dolens: Catheter-directed thrombolysis or surgical thrombectomy for limb-threatening venous gangrene"
        ],
        "first_line_treatment": "Direct Oral Anticoagulant (DOAC: oral Apixaban 10mg BID x7d then 5mg BID) initiated immediately without requiring heparin lead-in, for a minimum duration of 3 to 6 months.",
        "treatment_summary": "DOACs are preferred over Warfarin due to superior safety, lower intracranial hemorrhage risk, and no requirement for routine INR monitoring. Compression stockings aid post-thrombotic syndrome.",
        "disease_intelligence": {
            "disease_name": "Deep Vein Thrombosis (Lower Extremity DVT)",
            "etiology": "Virchow's Triad: Venous stasis (prolonged travel, immobilization, surgery), Endothelial injury (trauma, catheters), and Hypercoagulability (malignancy, factor V Leiden, oral contraceptives, pregnancy).",
            "icd10_code": "I82.40", "icd11_code": "BD71",
            "cardinal_symptoms": ["Unilateral lower extremity swelling (calf circumference discrepancy >3 cm)", "Dull, aching pain and calf tenderness on palpation", "Erythema, warmth, and dilated superficial collateral veins", "Prominent pitting edema restricted to the affected leg"],
            "red_flags": ["Phlegmasia Cerulea Dolens (massive iliofemoral thrombosis causing cyanosis, severe pain, arterial compromise, and limb gangrene)", "Signs of concurrent Pulmonary Embolism (sudden dyspnea, pleuritic chest pain, syncope)"],
            "pathophysiology": "Thrombus formation in deep veins of legs, typically originating in valve cusps where flow is sluggish, propagating proximally into popliteal, femoral, and iliac veins; embolization carries clot to pulmonary arterial bed.",
            "clinical_pearl": "Homan's sign (calf pain on dorsiflexion of the foot) is notoriously unreliable (sensitivity <50%, specificity <50%) and should never be used to rule in or rule out DVT. Ultrasound is the standard of care."
        },
        "pearl": "Unilateral calf swelling (>3cm difference) + warmth. Ultrasound confirms. First-line: Apixaban 10mg BID x7d -> 5mg BID for 3-6 months. No routine heparin lead-in required for Apixaban/Rivaroxaban."
    },

    "Pulmonary Embolism": {
        "icd10": "I26.99", "icd11": "BD70", "category": "Emergency Pulmonology / Vascular", "triage": "EMERGENT",
        "immediate_tests": [
            "CT Pulmonary Angiography (CTPA — Gold Standard: intraluminal filling defect in pulmonary arterial tree)",
            "Wells and Geneva Clinical Probability Scores for PE",
            "High-Sensitivity D-Dimer (rules out PE if low/intermediate pre-test probability)",
            "12-Lead Electrocardiogram (sinus tachycardia [most common], S1Q3T3 pattern, right bundle branch block, T-wave inversions V1-V4)",
            "Bedside Transthoracic Echocardiogram (evaluates right ventricular strain, RV dilation, McConnell sign)"
        ],
        "recommended_investigations": [
            "CT Pulmonary Angiography (CTPA with IV contrast)",
            "Ventilation-Perfusion (V/Q) Lung Scan (indicated when CTPA contraindicated: severe renal failure or IV contrast anaphylaxis)",
            "Serum Troponin and BNP / NT-proBNP (biomarkers of RV micro-infarction and strain; stratifies Submassive/Intermediate PE)",
            "Bilateral Lower Extremity Compression Ultrasound (identifies DVT source)",
            "Arterial Blood Gas (hypoxemia, hypocapnia, widened alveolar-arterial oxygen gradient)"
        ],
        "recommended_medications": [
            "Stable Non-High-Risk PE (DOAC First-Line): Apixaban 10 mg PO BID for 7 days, then 5 mg PO BID OR Rivaroxaban 15 mg BID for 21 days, then 20 mg PO daily with food",
            "Intermediate-High Risk Inpatient: Enoxaparin 1 mg/kg SC q12h (or therapeutic Unfractionated Heparin infusion)",
            "Massive / High-Risk PE with Hemodynamic Instability (Shock / SBP <90): Systemic Thrombolysis with IV Alteplase (tPA) 100 mg IV infusion over 2 hours (or Tenecteplase)",
            "Catheter-Directed Therapy: Ultrasound-assisted catheter-directed thrombolysis (EKOS) or mechanical suction thrombectomy",
            "Inferior Vena Cava (IVC) Filter: Indicated ONLY if absolute contraindication to anticoagulation or recurrent PE despite therapeutic anticoagulation"
        ],
        "first_line_treatment": "Immediate therapeutic anticoagulation with DOAC (Apixaban/Rivaroxaban) for hemodynamically stable PE; immediate systemic thrombolysis (IV Alteplase 100mg) for massive PE with shock.",
        "treatment_summary": "Massive PE (hypotension SBP <90) requires emergent reperfusion (thrombolysis or thrombectomy). Submassive PE has normal BP but positive troponin/BNP and RV strain, requiring close ICU monitoring.",
        "disease_intelligence": {
            "disease_name": "Acute Pulmonary Embolism (PE)",
            "etiology": "Thromboembolism dislodged from deep veins of lower extremities or pelvis (90%), fat embolism (long bone fracture), amniotic fluid, or air embolism.",
            "icd10_code": "I26.99", "icd11_code": "BD70",
            "cardinal_symptoms": ["Sudden onset of unexplained dyspnea (most common symptom)", "Pleuritic chest pain (worse with inspiration)", "Tachypnea (RR >20) and Tachycardia (HR >100 bpm)", "Hemoptysis (indicates pulmonary infarction)", "Lightheadedness, syncope, or near-syncope (sign of massive central saddle embolus)"],
            "red_flags": ["Massive PE / Obstructive Shock: SBP <90 mmHg, cardiac arrest (PEA), profound cyanosis", "Submassive PE: Normotensive but with RV enlargement (RV/LV ratio >0.9) and elevated troponin/BNP (high risk of rapid decompensation)"],
            "pathophysiology": "Thrombus occludes pulmonary arterial circulation, increasing pulmonary vascular resistance, causing acute right ventricular strain/dilation, shifting the interventricular septum leftward, impairing left ventricular filling, and precipitating cardiogenic/obstructive shock.",
            "clinical_pearl": "Sinus tachycardia is the single most common ECG abnormality in PE (found in >40% of cases). The classic S1Q3T3 pattern (McGinn-White sign) is specific for acute cor pulmonale but present in only 15-20%."
        },
        "pearl": "Sudden dyspnea + pleuritic pain + tachycardia. CTPA confirms. If SBP <90: Systemic thrombolysis with Alteplase 100mg. If stable: Apixaban 10mg BID x7d -> 5mg BID for >=3-6 months."
    },

    "Hypertensive Emergency": {
        "icd10": "I16.1", "icd11": "BA04", "category": "Emergency Cardiology / Vascular", "triage": "EMERGENT",
        "immediate_tests": [
            "Serial Blood Pressure Measurement (confirm SBP >180 mmHg and/or DBP >120 mmHg with target organ damage)",
            "Fundoscopic Examination (bilateral flame hemorrhages, cotton-wool spots, or papilledema / optic disc swelling)",
            "12-Lead Electrocardiogram (STAT: screens for acute ST-T ischemia, LV strain, infarction)",
            "High-Sensitivity Troponin and Basic Metabolic Panel (acute kidney injury: rising serum creatinine, BUN)",
            "Urinalysis (STAT: dipstick and microscopy for proteinuria, hematuria, red cell casts)"
        ],
        "recommended_investigations": [
            "Non-Contrast Head CT (mandatory if encephalopathy, severe headache, confusion, or focal deficits)",
            "CT Angiography of Chest and Abdomen (STAT if tearing chest/back pain, pulse asymmetry -> aortic dissection)",
            "Chest Radiograph (cardiomegaly, pulmonary edema)",
            "Transthoracic Echocardiogram (evaluates left ventricular hypertrophy and systolic/diastolic dysfunction)",
            "Coagulation Panel and Peripheral Blood Smear (evaluates microangiopathic hemolytic anemia in malignant hypertension)"
        ],
        "recommended_medications": [
            "First-Line IV Dihydropyridine Calcium Channel Blocker: IV Nicardipine infusion 5 mg/h, titrated by 2.5 mg/h q5-15min (max 15 mg/h) until target BP achieved",
            "First-Line Combined Alpha/Beta-Blocker: IV Labetalol 10-20 mg slow IV push over 2 min, repeated 20-80 mg q10min (or IV infusion 0.5-2 mg/min)",
            "Target Rule: Lower Mean Arterial Pressure (MAP) by no more than 20-25% in the first hour, then to 160/100 mmHg over next 2-6 hours (prevents watershed cerebral/coronary ischemia)",
            "Exception 1 (Aortic Dissection): Rapidly reduce SBP <120 mmHg and HR <60 bpm within 20 minutes (IV Esmolol + IV Nitroprusside/Nicardipine)",
            "Exception 2 (Acute Ischemic Stroke): Lower BP ONLY if >220/120 mmHg (or >185/110 if eligible for IV thrombolysis)"
        ],
        "first_line_treatment": "IV Nicardipine or IV Labetalol infusion titrated to reduce Mean Arterial Pressure by maximum 20-25% over the first hour; avoid excessive precipitous drops.",
        "treatment_summary": "Hypertensive emergency is defined by acute target organ damage (brain, retina, heart, kidney, aorta), NOT just blood pressure number. Admit to ICU for continuous arterial line monitoring.",
        "disease_intelligence": {
            "disease_name": "Hypertensive Emergency (Malignant Hypertension)",
            "etiology": "Medication non-adherence, renovascular hypertension, acute glomerulonephritis, pheochromocytoma, pre-eclampsia, sympathomimetic drugs (cocaine, methamphetamine), acute stroke.",
            "icd10_code": "I16.1", "icd11_code": "BA04",
            "cardinal_symptoms": ["Severe occipital headache", "Visual disturbances (blurring, scotomas, visual loss)", "Chest pain, dyspnea, and orthopnea (acute pulmonary edema)", "Confusion, somnolence, seizures (hypertensive encephalopathy)", "Oliguria and tea-colored urine (acute renal failure)"],
            "red_flags": ["Aortic Dissection (tearing chest pain radiating to back with unequal pulses)", "Hypertensive Encephalopathy (seizures, coma, papilledema)", "Acute Myocardial Infarction / Flash Pulmonary Edema", "Acute Renal Failure (rapidly rising creatinine, hematuria)"],
            "pathophysiology": "Abrupt surge in systemic vascular resistance overwhelms endothelial autoregulation, leading to vascular endothelial injury, fibrinoid necrosis of arterioles, platelet/fibrin deposition, microangiopathy, and ischemic target organ failure.",
            "clinical_pearl": "Never lower blood pressure precipitously to 'normal' in hypertensive emergency. Dropping MAP by >25% in the first hour can trigger catastrophic ischemic stroke or acute coronary thrombosis due to shifted cerebral autoregulation curves."
        },
        "pearl": "BP >180/120 with acute organ damage. Reduce MAP by MAX 20-25% in hour 1 using IV Nicardipine or Labetalol. Exception: Aortic Dissection demands SBP <120 and HR <60 within 20 minutes."
    },

    "Thyroid Storm": {
        "icd10": "E05.91", "icd11": "5A00.1", "category": "Emergency Endocrinology / Metabolic", "triage": "EMERGENT",
        "immediate_tests": [
            "Free T4 and Free T3 (STAT: markedly elevated) and TSH (suppressed <0.01 mIU/L)",
            "Burch-Wartofsky Point Scale (BWPS) Calculation (score >=45 highly suggestive of thyroid storm)",
            "12-Lead Electrocardiogram (sinus tachycardia [typically HR >140 bpm], atrial fibrillation with RVR)",
            "Complete Blood Count and Comprehensive Metabolic Panel (leukocytosis, hypercalcemia, transaminitis, hyperbilirubinemia)",
            "Precipitant Workup: Blood and urine cultures, Chest X-ray, Troponin"
        ],
        "recommended_investigations": [
            "Thyroid Function Tests (Free T4, Free T3, TSH)",
            "Thyrotropin Receptor Antibodies (TRAb / TSI: confirms Graves disease etiology)",
            "Burch-Wartofsky Point Scale calculation (evaluates thermoregulatory, CNS, GI, CV, and heart failure dysfunction)",
            "Bedside Echocardiogram (evaluates high-output heart failure and LVEF)"
        ],
        "recommended_medications": [
            "Step 1 — Beta-Blockade: Propranolol 60-80 mg PO q4h (or IV 1-2 mg slow push q10-15min) — controls adrenergic symptoms and inhibits peripheral T4-to-T3 conversion",
            "Step 2 — Inhibit Hormone Synthesis (Thionamide): Propylthiouracil (PTU) 500-1000 mg PO loading dose, then 250 mg PO q4h (preferred over Methimazole in storm due to T4-T3 conversion block)",
            "Step 3 — Inhibit Hormone Release (Iodide): Saturated Solution of Potassium Iodide (SSKI) 5 drops PO q6h (or Lugols iodine 10 drops q8h) — MUST ADMINISTER AT LEAST 1 HOUR AFTER THIONAMIDE",
            "Step 4 — Inhibit Peripheral Conversion & Adrenal Support: IV Hydrocortisone 100 mg IV q8h (or Dexamethasone 2 mg q6h)",
            "Step 5 — Aggressive Cooling: Acetaminophen and cooling blankets (Strictly avoid Aspirin, which displaces thyroid hormone from thyroxine-binding globulin)"
        ],
        "first_line_treatment": "Multimodal 4-step therapy in strict sequence: 1) Beta-blocker (Propranolol), 2) PTU, 3) wait 1 hour then give Potassium Iodide, 4) IV Hydrocortisone + active cooling with Acetaminophen.",
        "treatment_summary": "Life-threatening thyrotoxicosis with multi-organ decompensation (20-30% mortality). Sequence is vital: NEVER give iodine before PTU (giving iodine first fuels further thyroid hormone synthesis). Never give Aspirin.",
        "disease_intelligence": {
            "disease_name": "Thyroid Storm (Thyrotoxic Crisis)",
            "etiology": "Graves disease, toxic multinodular goiter, triggered by acute infection, trauma, surgery, radioactive iodine therapy, iodinated contrast, or medication non-compliance.",
            "icd10_code": "E05.91", "icd11_code": "5A00.1",
            "cardinal_symptoms": ["Extreme high-grade hyperpyrexia (fever 39-41°C / 102-106°F) with profuse diaphoresis", "Marked sinus tachycardia (HR >140 bpm) or Atrial Fibrillation with RVR", "Severe agitation, delirium, emotional lability, psychosis, or coma", "Nausea, persistent vomiting, diarrhea, jaundice, and abdominal pain", "High-output congestive heart failure and wide pulse pressure"],
            "red_flags": ["Cardiovascular collapse / cardiogenic shock from tachyarrhythmias", "Coma and status epilepticus", "Hepatic necrosis with deep jaundice (Bilirubin >3 mg/dL predicts high mortality)"],
            "pathophysiology": "Sudden massive surge in free T4/T3 availability and increased tissue sensitivity to catecholamines via up-regulated adrenergic receptors, inducing profound hypermetabolism and uncoupled oxidative phosphorylation.",
            "clinical_pearl": "Never administer Aspirin for fever in thyroid storm! Aspirin displaces T4 and T3 from thyroxine-binding globulin (TBG), dramatically increasing free active hormone levels and worsening the crisis. Use Acetaminophen."
        },
        "pearl": "Extreme fever + HR >140 + delirium + AFib. Burch-Wartofsky >=45. 4-step cocktail: 1) Propranolol, 2) PTU, 3) WAIT 1 HOUR -> Potassium Iodide, 4) IV Hydrocortisone. NEVER give Aspirin."
    },

    "Subarachnoid Hemorrhage": {
        "icd10": "I60.9", "icd11": "8B00", "category": "Emergency Neurology / Neurosurgery", "triage": "EMERGENT",
        "immediate_tests": [
            "Non-Contrast CT Head (STAT within 6 hours of onset: >99% sensitive for hyperdense blood in basal cisterns, sylvian fissures, and sulci)",
            "Lumbar Puncture with CSF Analysis (MANDATORY if head CT is negative or equivocal >6h from headache onset: evaluates xanthochromia via spectrophotometry and persistent RBCs in tubes 1-4)",
            "CT Angiography (CTA) of Head and Neck (STAT: detects intracranial aneurysm, location, size, and vasospasm)",
            "Complete Blood Count and Coagulation Profile (PT/INR, aPTT, Platelets)",
            "Basic Metabolic Panel (Serum Sodium: cerebral salt wasting vs SIADH monitoring)"
        ],
        "recommended_investigations": [
            "Non-Contrast Head CT followed immediately by CTA of intracranial vessels",
            "Lumbar Puncture (xanthochromia confirms subarachnoid blood degradation products)",
            "Digital Subtraction Angiography (DSA / Catheter cerebral angiogram — definitive gold standard for aneurysm planning)",
            "Hunt and Hess / Fisher Score calculations (clinical severity and vasospasm risk)",
            "Transcranial Doppler (TCD: daily surveillance for delayed cerebral vasospasm days 4-14)"
        ],
        "recommended_medications": [
            "Vasospasm Neuro-Protection: Oral Nimodipine 60 mg PO/NG q4h for 21 consecutive days (reduces poor neurological outcomes and cerebral infarction)",
            "Strict Blood Pressure Control (Prior to Aneurysm Securing): IV Nicardipine infusion (or IV Labetalol) to maintain SBP <140 mmHg (or MAP <110)",
            "Anticonvulsant Seizure Prophylaxis: IV Levetiracetam (Keppra) 500-1000 mg IV q12h",
            "Reversal of Anticoagulation (if on warfarin/DOAC): 4-Factor Prothrombin Complex Concentrate (PCC) + Vitamin K (or Idarucizumab / Andexanet alfa)",
            "Stool Softener and Analgesia: Docusate sodium + IV Fentanyl (prevent Valsalva-induced aneurysm re-rupture)"
        ],
        "first_line_treatment": "Emergency neurosurgical/endovascular consultation for aneurysm securing (endovascular coiling or surgical clipping within 24 hours) + oral Nimodipine 60mg q4h + SBP control <140.",
        "treatment_summary": "Sudden 'thunderclap' headache reaching peak intensity in <1 minute ('worst headache of my life'). Non-contrast CT STAT; if negative, lumbar puncture is mandatory. Prevent rebleeding and delayed vasospasm.",
        "disease_intelligence": {
            "disease_name": "Aneurysmal Subarachnoid Hemorrhage (aSAH)",
            "etiology": "Rupture of an intracranial saccular (berry) aneurysm (85%, most common at anterior communicating, posterior communicating, or MCA bifurcation), AVM, trauma.",
            "icd10_code": "I60.9", "icd11_code": "8B00",
            "cardinal_symptoms": ["Sudden-onset, explosive 'thunderclap' headache reaching peak intensity in seconds", "'Worst headache of my life' (distinct from any prior headache)", "Neck stiffness / meningismus (Kernig and Brudzinski signs positive)", "Transient or persistent loss of consciousness at ictus", "Photophobia, nausea, and vomiting", "Pupillary asymmetry / third nerve palsy (PCoA aneurysm)"],
            "red_flags": ["Aneurysmal Re-rupture (highest in first 24h, 70% mortality — maintain SBP <140)", "Delayed Cerebral Ischemia / Vasospasm (peak days 4 to 14 post-bleed)", "Acute obstructive hydrocephalus (requires emergency external ventricular drain [EVD])"],
            "pathophysiology": "High-pressure arterial blood extravasates into subarachnoid space under intracranial pressure, causing sudden intracranial hypertension, meningeal irritation, blood degradation into oxyhemoglobin, and delayed cerebral vasoconstriction.",
            "clinical_pearl": "Nimodipine does NOT prevent cerebral vasospasm itself — rather, it is neuroprotective against delayed cerebral ischemic injury. Never withhold Nimodipine unless profound hypotension refractory to vasopressors occurs."
        },
        "pearl": "Sudden 'thunderclap' headache ('worst of life'). Non-contrast CT STAT; if negative, LP for xanthochromia. Nimodipine 60mg q4h for 21d + SBP <140 -> emergent endovascular coiling <24h."
    }
}
