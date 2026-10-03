"""DocAssistIQ — Comprehensive Clinical Disease Registry (Part 3: Complete Coverage).

Covers Guillain-Barre, Anaphylaxis, Gout, Pyelonephritis, Nephrolithiasis,
Cholecystitis, Diverticulitis, Cellulitis, Meningitis, Sepsis, Typhus,
Scrub Typhus, Pre-eclampsia, Sickle Cell, GI Bleed, Tetanus, Rabies, etc.
"""

from typing import Dict, Any

CLINICAL_DISEASE_REGISTRY_PART3: Dict[str, Dict[str, Any]] = {
    "Guillain-Barré Syndrome": {
        "icd10": "G61.0", "icd11": "8C01.0", "category": "Emergency Neurology / Peripheral Nerve", "triage": "EMERGENT",
        "immediate_tests": [
            "Bedside Pulmonary Function (Forced Vital Capacity [FVC] <20 mL/kg, Negative Inspiratory Force [NIF] < -30 cmH2O warns of impending intubation)",
            "Lumbar Puncture with CSF Analysis (Classic: Albuminocytologic dissociation — elevated protein >100 mg/dL with normal WBC <5-10/mcL after day 7)",
            "Neurological Reflex Exam (generalized areflexia / hyporeflexia with symmetric ascending motor weakness)",
            "Continuous Cardiac Telemetry and Blood Pressure Monitoring (autonomic instability: labile BP and fatal dysrhythmias)",
            "Complete Blood Count and Comprehensive Metabolic Panel (electrolytes, SIADH monitoring)"
        ],
        "recommended_investigations": [
            "Lumbar Puncture (CSF protein and cell count; repeated if normal in first 48-72 hours)",
            "Nerve Conduction Studies (NCS) and Electromyography (EMG: marked slowing of conduction velocity, prolonged distal latencies, conduction blocks)",
            "Anti-Ganglioside Antibodies: Anti-GM1, Anti-GD1a (AIDP/AMAN); Anti-GQ1b (Miller Fisher syndrome triad: ophthalmoplegia, ataxia, areflexia)",
            "Antecedent Infection Serology: Campylobacter jejuni, CMV, EBV, Mycoplasma, Zika, SARS-CoV-2",
            "Spine MRI with contrast (demonstrates prominent anterior spinal root enhancement)"
        ],
        "recommended_medications": [
            "First-Line Immunotherapy (Intravenous Immunoglobulin): IVIG 0.4 g/kg/day IV for 5 consecutive days (total 2 g/kg)",
            "Alternative First-Line (Plasma Exchange): Plasmapheresis 200-250 mL/kg total plasma volume exchanged over 4-5 sessions over 7-14 days",
            "Severe Autonomic Instability: Short-acting IV agents (Esmolol for severe tachycardia/HTN; pacing/atropine for bradycardia)",
            "VTE Prophylaxis: Enoxaparin 40 mg SC daily + pneumatic compression boots (paralyzed patients at high PE risk)",
            "Neuropathic Pain: Gabapentin 300 mg PO TID or Pregabalin 75 mg PO BID",
            "Strict Contraindication: Corticosteroids (Prednisone/Methylprednisolone) are INEFFECTIVE and may delay recovery"
        ],
        "first_line_treatment": "Intravenous Immunoglobulin (IVIG 2 g/kg over 5 days) or Plasmapheresis, combined with ICU admission and serial FVC/NIF bedside respiratory monitoring ('20/30/40 rule').",
        "treatment_summary": "Ascending symmetric flaccid paralysis with areflexia following a GI (Campylobacter) or respiratory infection. Corticosteroids are contraindicated. Intubate electively if FVC <15-20 mL/kg.",
        "disease_intelligence": {
            "disease_name": "Guillain-Barré Syndrome (Acute Inflammatory Demyelinating Polyradiculoneuropathy)",
            "etiology": "Post-infectious autoimmune molecular mimicry triggered by Campylobacter jejuni enteritis (30-40%), CMV, EBV, Mycoplasma pneumoniae, or viral infections.",
            "icd10_code": "G61.0", "icd11_code": "8C01.0",
            "cardinal_symptoms": ["Symmetric, progressive, ascending flaccid muscle weakness (starts in legs and ascends to arms and face)", "Generalized loss of deep tendon reflexes (areflexia)", "Distal paresthesias ('glove-and-stocking' numbness and tingling)", "Bilateral facial weakness (diplegia) and bulbar palsy (dysphagia, dysarthria)", "Autonomic dysfunction: fluctuating blood pressure, orthostatic hypotension, cardiac arrhythmias"],
            "red_flags": ["Acute neuromuscular respiratory failure (requiring mechanical ventilation in 25-30% of patients; FVC <15 mL/kg)", "Life-threatening cardiac arrhythmias from autonomic storms (sustained sinus tachycardia, asystole)", "Aspiration pneumonia secondary to bulbar paralysis"],
            "pathophysiology": "Antibodies raised against microbial antigens (e.g. Campylobacter lipooligosaccharides) cross-react with structurally identical GM1/GD1a gangliosides on peripheral nerve axolemma and myelin sheaths (molecular mimicry), activating complement and causing macrophage-mediated demyelination.",
            "clinical_pearl": "The '20/30/40 rule' indicates impending respiratory arrest and need for elective mechanical ventilation: FVC <20 mL/kg, NIF < -30 cmH2O, or Peak Expiratory Flow <40% predicted. Never wait for hypoxemia to intubate!"
        },
        "pearl": "Campylobacter prodrome -> ascending flaccid paralysis + areflexia. Albuminocytologic dissociation on LP. IVIG 2 g/kg or Plasmapheresis. Serial FVC/NIF monitoring. Corticosteroids contraindicated."
    },

    "Anaphylaxis": {
        "icd10": "T78.2", "icd11": "4A84", "category": "Emergency Allergy / Immunology", "triage": "EMERGENT",
        "immediate_tests": [
            "Clinical Diagnosis STAT (DO NOT delay treatment for any lab test: acute onset skin/mucosal symptoms + airway/breathing compromise or hypotension)",
            "Continuous Vital Signs Monitoring (BP, SpO2, HR every 2-5 minutes)",
            "Total Serum Tryptase (STAT within 1-2 hours of symptom onset; baseline repeat at 24 hours confirms mast cell degranulation)",
            "12-Lead Electrocardiogram (evaluates Kounis syndrome: allergic angina / coronary vasospasm)"
        ],
        "recommended_investigations": [
            "Serum Tryptase Level (peak at 60-90 minutes post-exposure, normalizes by 24h)",
            "Follow-up Outpatient Allergy Testing (Skin prick and serum specific IgE after 4-6 weeks to identify trigger: venom, food, penicillin, latex)",
            "12-Lead ECG and Troponin (if chest pain or hemodynamic collapse present)"
        ],
        "recommended_medications": [
            "First-Line Drug of Choice (ADMINISTER IMMEDIATELY): Intramuscular Epinephrine (1:1,000, 1 mg/mL) 0.3-0.5 mg (0.01 mg/kg in children, max 0.3 mg) IM into anterolateral mid-thigh STAT",
            "Repeat Epinephrine: Repeat 0.3-0.5 mg IM every 5 to 15 minutes if symptoms persist or progress",
            "IV Fluid Bolus for Hypotension: IV Normal Saline (0.9% NaCl) 1000-2000 mL rapid bolus (20 mL/kg in children) through large-bore IVs",
            "Secondary Adjunctive Antihistamines: Diphenhydramine 25-50 mg IV/PO (H1 blocker) PLUS Famotidine 20 mg IV/PO (H2 blocker)",
            "Secondary Adjunctive Corticosteroid: Methylprednisolone 125 mg IV (or oral Prednisone 50 mg) — prevents delayed biphasic reactions",
            "Refractory Bronchospasm: Inhaled Albuterol 2.5-5 mg nebulized with oxygen",
            "Refractory Shock on Beta-Blockers: IV Glucagon 1-5 mg slow IV over 5 min, then 5-15 mcg/min infusion (bypasses beta-receptors)"
        ],
        "first_line_treatment": "Intramuscular Epinephrine (1:1000) 0.3-0.5mg injected immediately into the anterolateral mid-thigh. Never delay Epinephrine for antihistamines or steroids.",
        "treatment_summary": "Epinephrine is the ONLY medication that prevents death from anaphylaxis. Inject anterolateral thigh immediately. Keep patient supine with legs elevated (fatal 'empty heart syndrome' if stood up).",
        "disease_intelligence": {
            "disease_name": "Anaphylaxis",
            "etiology": "IgE-mediated mast cell/basophil degranulation triggered by foods (peanuts, tree nuts, shellfish), insect stings (Hymenoptera: wasps, bees), medications (beta-lactam antibiotics, NSAIDs), radiocontrast media, or latex.",
            "icd10_code": "T78.2", "icd11_code": "4A84",
            "cardinal_symptoms": ["Acute generalized urticaria (hives), intense pruritus, and flushing", "Angioedema of lips, tongue, uvula, and soft palate", "Inspiratory stridor, hoarseness, and sensation of throat closure", "Expiratory wheezing, bronchospasm, and dyspnea", "Hypotension (SBP <90 or >30% drop from baseline), dizziness, syncope, and cardiovascular collapse"],
            "red_flags": ["Upper Airway Angioedema with Stridor (requires immediate awake fiberoptic intubation before complete glottic closure)", "Biphasic Anaphylaxis (recurrence of severe symptoms 4 to 12 hours later in up to 20% of patients)", "Refractory distributive shock in patients on chronic beta-blockers"],
            "pathophysiology": "Cross-linking of allergen to allergen-specific IgE bound to high-affinity FceRI receptors on mast cells and basophils triggers immediate degranulation, releasing massive preformed histamine, tryptase, leukotrienes (LTC4, LTD4), and platelet-activating factor, driving profound vasodilation and capillary leakage.",
            "clinical_pearl": "Never allow an anaphylactic patient to suddenly sit up or stand! Rapid elevation of the head can cause sudden venous pooling in massively dilated splanchnic and peripheral vessels, resulting in catastrophic loss of cardiac preload ('empty heart syndrome') and immediate PEA cardiac arrest. Keep supine with legs elevated."
        },
        "pearl": "IM Epinephrine 0.3-0.5mg in anterolateral thigh STAT. Repeat q5-15m PRN. 1-2L Normal Saline bolus. Keep supine! Antihistamines and steroids are secondary and NEVER substitute for Epinephrine."
    },

    "Pre-eclampsia / Eclampsia": {
        "icd10": "O14.90", "icd11": "JA24", "category": "Obstetrics / Emergency", "triage": "EMERGENT",
        "immediate_tests": [
            "Blood Pressure Measurement (SBP >=140 or DBP >=90 on 2 occasions >=4h apart after 20 weeks; SBP >=160 or DBP >=110 indicates Severe Features)",
            "Urinalysis (dipstick >=2+ protein) and Urine Protein-to-Creatinine Ratio (UPCR >=0.3 mg/mg or 24h urine protein >=300 mg)",
            "Complete Blood Count with Platelets (thrombocytopenia <100,000/mcL)",
            "Comprehensive Metabolic Panel (Liver enzymes: AST/ALT >=2x upper limit of normal; Serum Creatinine >1.1 mg/dL)",
            "Fetal Heart Rate Tracing and Bedside Obstetric Ultrasound (fetal well-being, biophysical profile, amniotic fluid index)"
        ],
        "recommended_investigations": [
            "Urine Protein/Creatinine Ratio (UPCR >=0.3 confirms significant proteinuria; can diagnose without proteinuria if other end-organ damage present)",
            "Peripheral Blood Smear (schistocytes, burr cells indicating microangiopathic hemolytic anemia in HELLP syndrome)",
            "Serum Lactate Dehydrogenase (LDH >600 IU/L in HELLP syndrome)",
            "Coagulation Profile (PT/INR, aPTT, Fibrinogen — screening for DIC)",
            "Uric Acid (elevated >5.5-6.0 mg/dL aids diagnostic confirmation)"
        ],
        "recommended_medications": [
            "First-Line Seizure Prophylaxis / Eclampsia Treatment: Magnesium Sulfate 4-6 g IV loading dose in 100 mL over 15-20 minutes, followed by 1-2 g/h continuous IV maintenance infusion (continue for 24h postpartum)",
            "Antidote for Magnesium Toxicity: Calcium Gluconate 10% (1 g IV over 3-5 minutes) for loss of deep tendon reflexes or respiratory depression",
            "Emergency Antihypertensive (Severe BP >=160/110 mmHg within 30-60 min): IV Labetalol 20 mg slow push, repeated 40-80 mg q10min (max 300 mg) OR IV Hydralazine 5-10 mg slow push q20min (max 20 mg) OR Oral Nifedipine extended-release 30-60 mg PO (or immediate-release 10-20 mg PO)",
            "Fetal Lung Maturity (Gestation <34-37 weeks): Betamethasone 12 mg IM q24h for 2 doses",
            "Definitive Cure: Timely delivery of the fetus and placenta (immediate if >=34 weeks with severe features or eclampsia)"
        ],
        "first_line_treatment": "Magnesium Sulfate IV infusion (seizure prophylaxis) + IV Labetalol or Hydralazine (BP control target <160/110) + prompt delivery of the fetus and placenta.",
        "treatment_summary": "Delivery is the only definitive cure. Severe features: SBP >=160 or DBP >=110, platelets <100k, AST/ALT 2x ULN, Cr >1.1, pulmonary edema, new visual/cerebral symptoms. Eclampsia = new onset grand mal seizures.",
        "disease_intelligence": {
            "disease_name": "Pre-eclampsia with Severe Features & Eclampsia",
            "etiology": "Defective maternal spiral artery remodeling by cytotrophoblasts, causing placental ischemia, release of anti-angiogenic factors (sFlt-1, soluble endoglin), and systemic maternal endothelial dysfunction.",
            "icd10_code": "O14.90", "icd11_code": "JA24",
            "cardinal_symptoms": ["New-onset hypertension (BP >=140/90 after 20 weeks gestation)", "Persistent throbbing frontal headache refractory to analgesics", "Visual scotomas, blurred vision, or photopsia (cerebral vasospasm)", "Right upper quadrant or epigastric pain (hepatic capsule stretch / microvascular ischemia)", "Generalized facial and hand edema with brisk hyperreflexia / clonus"],
            "red_flags": ["Eclamptic Convulsions (generalized tonic-clonic seizures — requires immediate Magnesium Sulfate bolus)", "HELLP Syndrome (Hemolysis, Elevated Liver enzymes, Low Platelets)", "Placental Abruption (painful vaginal bleeding, hypertonic uterus)", "Intracranial Hemorrhage / stroke (leading cause of maternal mortality)"],
            "pathophysiology": "Impaired trophoblastic invasion leads to high-resistance uteroplacental bed, hypoperfusion, oxidative stress, and shedding of anti-angiogenic sFlt-1 (which binds and neutralizes VEGF and PlGF), resulting in widespread systemic vascular endothelial damage, capillary leak, hypertension, and microvascular thrombosis.",
            "clinical_pearl": "Magnesium Sulfate is significantly superior to Phenytoin, Diazepam, or Levetiracetam for both the prevention and treatment of eclamptic seizures. Monitor deep tendon reflexes (patellar reflex loss occurs before respiratory depression)."
        },
        "pearl": "BP >=160/110 or organ damage after 20 weeks. Magnesium Sulfate 4-6g IV bolus + 1-2g/h for seizure prophylaxis. IV Labetalol or Hydralazine for BP. Delivery is the only definitive cure."
    },

    "Sickle Cell Crisis (Vaso-occlusive)": {
        "icd10": "D57.00", "icd11": "4A51.0", "category": "Hematology / Emergency", "triage": "URGENT",
        "immediate_tests": [
            "Complete Blood Count with Reticulocyte Count (STAT: baseline hemoglobin/hematocrit drop, reticulocytes >3-10% indicates active hemolysis; reticulocytopenia <1% indicates aplastic crisis)",
            "Peripheral Blood Smear (sickle erythrocytes [drepanocytes], Howell-Jolly bodies, target cells, nucleated RBCs)",
            "Comprehensive Metabolic Panel (Total/indirect bilirubin and LDH markedly elevated; Creatinine for nephropathy)",
            "Pulse Oximetry and Chest Radiograph (STAT if fever, cough, chest pain, or tachypnea -> screen for Acute Chest Syndrome)",
            "Blood Cultures and Urinalysis (fever in sickle cell is an emergency due to functional asplenia)"
        ],
        "recommended_investigations": [
            "Hemoglobin Electrophoresis / High-Performance Liquid Chromatography (HPLC: confirms HbSS vs HbSC vs HbS-beta-thalassemia)",
            "Chest X-Ray (new pulmonary infiltrate confirms Acute Chest Syndrome)",
            "Type and Screen with Extended Phenotypic Red Cell Crossmatch (evaluates for alloantibodies prior to simple/exchange transfusion)",
            "Transcranial Doppler (TCD: pediatric stroke risk screening)"
        ],
        "recommended_medications": [
            "Rapid First-Line Opioid Analgesia (Administer within 30-60 minutes): IV Morphine 0.1 mg/kg (or IV Hydromorphone 0.015-0.02 mg/kg) repeated q15-30min until pain controlled, then PCA (patient-controlled analgesia)",
            "Adjunctive NSAID: IV Ketorolac 15-30 mg q6h for 48-72 hours (or oral Ibuprofen) if renal function preserved",
            "Intravenous Hydration: D5 0.45% Normal Saline at maintenance rate (avoid over-hydration which triggers pulmonary edema and Acute Chest Syndrome)",
            "Supplemental Oxygen: Indicated ONLY if SpO2 <95% on room air (hyperoxia suppresses erythropoiesis)",
            "Empiric Antibiotics (if Febrile >=38.5°C): IV Ceftriaxone 2g daily (covers encapsulated Streptococcus pneumoniae and Salmonella osteomyelitis)",
            "Acute Chest Syndrome / Stroke Protocol: Simple or Automated Red Cell Exchange Transfusion (target Hb 10 g/dL, HbS <30%)"
        ],
        "first_line_treatment": "Aggressive, rapid parenteral opioid analgesia within 30-60 minutes of arrival + maintenance IV hydration with D5 0.45% Saline + empiric Ceftriaxone if febrile.",
        "treatment_summary": "Do not undertreat acute vaso-occlusive bone pain. Watch closely for Acute Chest Syndrome (new CXR infiltrate + fever/chest pain/hypoxemia = leading cause of mortality).",
        "disease_intelligence": {
            "disease_name": "Sickle Cell Vaso-Occlusive Pain Crisis (VOC)",
            "etiology": "Homozygous point mutation in beta-globin gene (Glu6Val) producing Hemoglobin S (HbS); triggered by hypoxia, dehydration, acidosis, cold exposure, infection, or stress.",
            "icd10_code": "D57.00", "icd11_code": "4A51.0",
            "cardinal_symptoms": ["Excruciating, deep, throbbing bone and joint pain (lumbar spine, femur, ribs, humerus)", "Dactylitis ('hand-foot syndrome' in infants: painful dactyl swelling)", "Low-grade fever and tachycardia", "Scleral icterus and mucosal pallor"],
            "red_flags": ["Acute Chest Syndrome (new infiltrate on CXR + fever, chest pain, wheeze, or drop in SpO2 — major cause of mortality)", "Splenic Sequestration Crisis (rapid pooling of blood in spleen: massive tender splenomegaly and severe acute shock/anemia)", "Aplastic Crisis (Parvovirus B19 infection: cessation of erythropoiesis with reticulocytes <0.5%)", "Acute Ischemic Stroke (transient ischemic attack, focal deficit)"],
            "pathophysiology": "Under low oxygen tension, deoxygenated HbS molecules polymerize into rigid, insoluble fibers, distorting red blood cells into stiff, crescent/sickle shapes; these adhere to vascular endothelium, obstruct microcirculation, trigger tissue ischemia, severe inflammation, and bone infarction.",
            "clinical_pearl": "All adult sickle cell patients are functionally asplenic due to repetitive splenic micro-infarctions (autosplenectomy) by age 5-6. Any fever (>=38.5°C) is a life-threatening medical emergency requiring immediate empiric IV Ceftriaxone for encapsulated organisms."
        },
        "pearl": "Excruciating bone pain crisis. Rapid IV Opioids within 30-60 min + maintenance IV fluids. If febrile, give IV Ceftriaxone STAT (functional asplenia). Watch for Acute Chest Syndrome (CXR infiltrate)."
    },

    "COVID-19": {
        "icd10": "U07.1", "icd11": "RA01", "category": "Infectious Disease / Respiratory Viral", "triage": "URGENT",
        "immediate_tests": [
            "SARS-CoV-2 NAAT (RT-PCR or Rapid Antigen Assay)",
            "Continuous Pulse Oximetry and Arterial Blood Gas (ABG if SpO2 <92% or respiratory distress)",
            "Complete Blood Count with Differential (lymphopenia, absolute lymphocyte count <1000/mcL)",
            "Inflammatory Biomarkers: Serum Ferritin, C-Reactive Protein, D-Dimer, and LDH",
            "12-Lead Electrocardiogram (evaluates myocarditis, arrhythmia, or baseline QTc prior to therapies)"
        ],
        "recommended_investigations": [
            "Chest Radiograph (PA and lateral views) or High-Resolution Chest CT (bilateral peripheral ground-glass opacities)",
            "Comprehensive Metabolic Panel (serum creatinine, BUN, ALT/AST, electrolytes)",
            "Cardiac Troponin and NT-proBNP (screens for COVID-19 associated myocarditis or right ventricular strain)",
            "Coagulation Panel: PT/INR, aPTT, Fibrinogen (monitors COVID-19 associated coagulopathy [CAC])",
            "Respiratory Viral Multiplex PCR (rules out Influenza A/B, RSV, and bacterial superinfection)"
        ],
        "recommended_medications": [
            "Severe Hypoxemic Disease (SpO2 <94% on room air): Dexamethasone 6 mg IV or PO once daily for up to 10 days (or until discharge)",
            "Early Antiviral Therapy (within 5-7 days of onset in hospitalized requiring supplemental O2): IV Remdesivir 200 mg loading dose on Day 1, followed by 100 mg IV once daily for 5 days",
            "Rapid Inflammatory Progression (Within 24-48h of ICU/high-flow O2 + CRP >=75 mg/L): Baricitinib 4 mg PO daily x14 days OR IV Tocilizumab 8 mg/kg (max 800 mg) single infusion",
            "Standard Thromboprophylaxis: Prophylactic Enoxaparin 40 mg SC once daily (or Heparin 5,000 units SC q8-12h) unless active bleeding or platelets <25k",
            "Mild/Moderate Outpatient High-Risk: Nirmatrelvir/Ritonavir (Paxlovid) 300 mg/100 mg PO BID x5 days (initiated within 5 days of symptom onset; check renal function and CYP3A interactions)"
        ],
        "first_line_treatment": "Supplemental oxygen to maintain SpO2 >=92-96% + Dexamethasone 6 mg daily (if supplemental O2 required) + IV Remdesivir (within 5-7 days) + prophylactic anticoagulation.",
        "treatment_summary": "Supplemental oxygen + Dexamethasone 6mg daily for hypoxemia (RECOVERY trial). Remdesivir for early viral replication. Prophylactic anticoagulation for COVID-associated coagulopathy.",
        "disease_intelligence": {
            "disease_name": "COVID-19 (SARS-CoV-2 Acute Respiratory Disease)",
            "etiology": "Infection by severe acute respiratory syndrome coronavirus 2 (SARS-CoV-2), a positive-sense single-stranded RNA betacoronavirus transmitted via respiratory droplets, aerosols, and contact.",
            "icd10_code": "U07.1", "icd11_code": "RA01",
            "cardinal_symptoms": ["Fever, chills, and rigors", "Dry or productive cough and dyspnea", "Fatigue, generalized myalgias, and headache", "Sudden anosmia (loss of smell) and ageusia (loss of taste)", "Sore throat, nasal congestion, and gastrointestinal symptoms (nausea, diarrhea)"],
            "red_flags": ["Silent / 'Happy' Hypoxemia (severe desaturation SpO2 <88% without proportional dyspnea)", "Rapid respiratory failure and ARDS requiring mechanical ventilation or ECMO", "COVID-19 Associated Coagulopathy (pulmonary embolism, deep vein thrombosis, arterial stroke)", "Multisystem Inflammatory Syndrome (MIS) or Cytokine Release Storm"],
            "pathophysiology": "SARS-CoV-2 spike protein binds host ACE2 receptors via TMPRSS2 priming, infecting alveolar type II pneumocytes and vascular endothelial cells, initiating immune hyperactivation, microvascular endothelialitis, microthrombi formation, and acute lung injury.",
            "clinical_pearl": "Dexamethasone provides a significant mortality benefit ONLY in patients requiring supplemental oxygen or mechanical ventilation; in mild patients not requiring oxygen, corticosteroids may increase mortality by impairing viral clearance."
        },
        "pearl": "SpO2 <94% -> Dexamethasone 6mg daily x10d + Remdesivir x5d + prophylactic Enoxaparin. Watch for silent hypoxemia and thromboembolism. Steroids contraindicated if no O2 required."
    },

    "Type 2 Diabetes Mellitus": {
        "icd10": "E11.9", "icd11": "5A11", "category": "Endocrinology / Metabolic", "triage": "ROUTINE",
        "immediate_tests": [
            "Fasting Plasma Glucose (FPG >= 126 mg/dL / 7.0 mmol/L confirms diagnosis)",
            "Hemoglobin A1c (HbA1c >= 6.5% / 48 mmol/mol confirms diagnosis)",
            "Comprehensive Metabolic Panel (serum creatinine, eGFR, BUN, electrolytes)",
            "Urinalysis with microalbuminuria / UACR",
            "Lipid Panel (fasting total cholesterol, HDL, LDL, triglycerides)"
        ],
        "recommended_investigations": [
            "Serial HbA1c every 3 months until target (<7.0%) met, then twice yearly",
            "Annual Urine Albumin-to-Creatinine Ratio (UACR: early diabetic nephropathy)",
            "Annual comprehensive dilated eye examination by ophthalmologist (diabetic retinopathy)",
            "Annual comprehensive foot examination with 10g monofilament (diabetic peripheral neuropathy)",
            "12-Lead Electrocardiogram (cardiovascular risk screening in asymptomatic diabetics)"
        ],
        "recommended_medications": [
            "First-Line Cornerstone Pharmacotherapy: Metformin 500 mg PO daily with meals, titrated weekly to 1000 mg PO BID (monitor eGFR; dose reduce if eGFR <45, stop if eGFR <30)",
            "Cardiovascular & Renal Protection: SGLT2 Inhibitor (Empagliflozin 10-25 mg PO daily or Dapagliflozin 10 mg PO daily) if established ASCVD, Heart Failure, or CKD (UACR >=30)",
            "GLP-1 Receptor Agonist (Preferred for ASCVD / Weight Loss): Semaglutide 0.25 mg SC weekly titrated to 0.5-2.0 mg weekly OR Dulaglutide 0.75-4.5 mg weekly",
            "Second-Line Oral Add-On: DPP-4 Inhibitor (Sitagliptin 100 mg PO daily) or Sulfonylurea (Glimepiride 1-4 mg PO daily with morning meal)",
            "Basal Insulin (if severe symptomatic hyperglycemia or HbA1c >10%): Insulin Glargine or Degludec 10 units SC at bedtime"
        ],
        "first_line_treatment": "Lifestyle modification (medical nutrition therapy + 150 min/week exercise) + Metformin (500-1000 mg BID) + SGLT2 inhibitor / GLP-1 RA if cardiorenal risk present.",
        "treatment_summary": "Comprehensive glycemic control targeting HbA1c <7.0%. Metformin first-line unless contraindicated. SGLT2i/GLP-1RA mandatory if cardiovascular disease, heart failure, or albuminuric kidney disease. Annual screening for retinopathy, nephropathy, and neuropathy.",
        "disease_intelligence": {
            "disease_name": "Type 2 Diabetes Mellitus (T2DM)",
            "etiology": "Progressive defect in pancreatic beta-cell insulin secretion on the background of tissue insulin resistance in skeletal muscle, liver, and adipose tissue.",
            "icd10_code": "E11.9", "icd11_code": "5A11",
            "cardinal_symptoms": ["Polyuria (osmotic diuresis from glucosuria)", "Polydipsia (excessive thirst secondary to dehydration)", "Polyphagia and unexpected weight loss", "Fatigue and generalized malaise", "Blurred vision (hyperosmolar refractive lens changes)", "Delayed wound healing and recurrent candidal/fungal infections"],
            "red_flags": ["Hyperosmolar Hyperglycemic State (HHS: glucose >600 mg/dL, severe dehydration, plasma osmolality >320 mOsm/kg, altered sensorium/coma)", "Diabetic Ketoacidosis (DKA: anion gap metabolic acidosis, vomiting, tachypnea, ketones)", "Critical Limb Ischemia or Infected Diabetic Foot Ulcer (osteomyelitis risk)"],
            "pathophysiology": "Genetic predisposition coupled with obesity and physical inactivity leads to peripheral insulin resistance. Beta-cells initially hypersecrete insulin (compensatory hyperinsulinemia), but eventually undergo exhaustion and apoptosis, resulting in relative insulin deficiency, unsuppressed hepatic gluconeogenesis, and sustained hyperglycemia.",
            "clinical_pearl": "SGLT2 inhibitors and GLP-1 receptor agonists provide major cardiovascular and renal benefits that are INDEPENDENT of their glucose-lowering effects. In diabetic patients with heart failure or CKD, an SGLT2 inhibitor should be initiated regardless of baseline HbA1c."
        },
        "pearl": "HbA1c >=6.5% or FPG >=126. Metformin first line. Add SGLT2i or GLP-1RA if ASCVD, HF, or CKD. Target HbA1c <7.0%. Annual foot, eye, and renal microalbumin screening."
    },

    "Essential Hypertension": {
        "icd10": "I10", "icd11": "BA00", "category": "Cardiology / Vascular", "triage": "ROUTINE",
        "immediate_tests": [
            "Serial standardized clinic BP measurements (>=130/80 mmHg confirms hypertension; measure both arms)",
            "Basic Metabolic Panel (serum sodium, potassium, BUN, serum creatinine, eGFR)",
            "Urinalysis (dipstick for proteinuria and microscopic hematuria)",
            "12-Lead Electrocardiogram (evaluates left ventricular hypertrophy / Cornell voltage criteria)",
            "Fasting Blood Glucose and Lipid Profile (global cardiovascular risk evaluation)"
        ],
        "recommended_investigations": [
            "24-Hour Ambulatory Blood Pressure Monitoring (ABPM: rules out white-coat and masked hypertension)",
            "Transthoracic Echocardiogram (evaluates LV wall thickness, diastolic dysfunction, and ejection fraction)",
            "Urine Albumin-to-Creatinine Ratio (UACR: screens for early microvascular hypertensive nephrosclerosis)",
            "Screening for Secondary Hypertension (Plasma aldosterone-to-renin ratio for Conn syndrome; sleep study for OSA; renal artery ultrasound for renal artery stenosis)"
        ],
        "recommended_medications": [
            "First-Line Monotherapy (Non-Black Patients): ACE Inhibitor (Lisinopril 10-40 mg PO daily) OR ARB (Losartan 50-100 mg PO daily)",
            "First-Line Monotherapy (Black Patients / Elderly): Dihydropyridine Calcium Channel Blocker (Amlodipine 5-10 mg PO daily) OR Thiazide Diuretic (Chlorthalidone 12.5-25 mg PO daily)",
            "First-Line Dual Combination (Stage 2 HTN: BP >20/10 mmHg over target): ACEi or ARB PLUS Dihydropyridine CCB (e.g. Lisinopril + Amlodipine)",
            "Target Organ Protection (CKD / Proteinuria): ACEi (Lisinopril) or ARB (Losartan) mandatory to preserve glomerular capillary pressure",
            "Resistant Hypertension (Uncontrolled on 3 agents including a diuretic): Add Spironolactone 25-50 mg PO daily"
        ],
        "first_line_treatment": "DASH diet (<1.5g sodium/day, weight loss) + First-line pharmacotherapy (ACEi/ARB, Dihydropyridine CCB, or Thiazide diuretic). Target BP <130/80 mmHg.",
        "treatment_summary": "First-line antihypertensive therapy using ACEi/ARB, CCB, or thiazide-like diuretic (Chlorthalidone). In Stage 2 HTN, start initial dual therapy. Target BP <130/80 mmHg in all patients.",
        "disease_intelligence": {
            "disease_name": "Essential (Primary) Hypertension",
            "etiology": "Multifactorial disorder involving complex interactions between genetic predisposition, renal sodium handling, renin-angiotensin-aldosterone axis hyperactivity, sympathetic tone, and endothelial dysfunction.",
            "icd10_code": "I10", "icd11_code": "BA00",
            "cardinal_symptoms": ["Elevated blood pressure (>=130/80 mmHg on repeated readings)", "Frequently completely asymptomatic ('The Silent Killer')", "Suboccipital morning headache (severe or long-standing cases)", "Dizziness, lightheadedness, and exertional dyspnea", "Epistaxis, blurry vision, or tinnitus"],
            "red_flags": ["Hypertensive Emergency (BP >180/120 mmHg WITH acute target organ damage: encephalopathy, stroke, acute pulmonary edema, aortic dissection, acute kidney injury)", "Papilledema on fundoscopic exam", "New-onset chest pain or tearing back pain"],
            "pathophysiology": "Chronic sustained elevation in total peripheral vascular resistance driven by arteriolar vasoconstriction, arterial stiffness, and microvascular remodeling. Leads to concentric left ventricular hypertrophy, accelerated coronary atherosclerosis, nephrosclerosis, and cerebrovascular accidents.",
            "clinical_pearl": "Chlorthalidone and Indapamide are superior to Hydrochlorothiazide (HCTZ) due to longer half-lives and proven 24-hour ambulatory blood pressure reduction and cardiovascular event prevention."
        },
        "pearl": "BP >=130/80 mmHg. ACEi/ARB + CCB + Thiazide. Target <130/80 mmHg. Screen for end-organ damage (ECG, creatinine, UACR, eye exam). Rule out secondary causes in refractory cases."
    },

    "Iron Deficiency Anemia": {
        "icd10": "D50.9", "icd11": "3A00", "category": "Hematology", "triage": "ROUTINE",
        "immediate_tests": [
            "Complete Blood Count with Peripheral Blood Smear (low Hb, low MCV <80 fL microcytic, low MCH <27 pg hypochromic, elevated RDW >15%)",
            "Serum Ferritin (gold standard biomarker: <30 ng/mL diagnostic of iron deficiency; <15 ng/mL pathognomonic)",
            "Iron Panel (low serum iron <50 mcg/dL, elevated TIBC >400 mcg/dL, transferrin saturation <16%)",
            "Reticulocyte Count and Reticulocyte Hemoglobin Content (Ret-He <29 pg indicates functional iron deficiency)",
            "Serum Creatinine and eGFR (exclude anemia of chronic kidney disease)"
        ],
        "recommended_investigations": [
            "Gastrointestinal Endoscopy (Esophagogastroduodenoscopy [EGD] and Colonoscopy: mandatory in all men and postmenopausal women to identify source of occult GI bleeding)",
            "Celiac Disease Serology (Anti-tissue transglutaminase IgA [anti-tTG] + total serum IgA: rules out duodenal iron malabsorption)",
            "Urinalysis (rules out hemoglobinuria / hematuria)",
            "Helicobacter pylori stool antigen or breath test (H. pylori causes refractory iron deficiency)",
            "Pelvic Ultrasound (in premenopausal women with heavy menstrual bleeding / uterine fibroids)"
        ],
        "recommended_medications": [
            "First-Line Oral Iron Replacement: Ferrous Sulfate 325 mg (65 mg elemental iron) OR Ferrous Fumarate 200 mg PO daily or on ALTERNATE DAYS with Vitamin C 250-500 mg (alternate-day dosing minimizes hepcidin spike and maximizes absorption)",
            "Tolerability Formulation: Ferrous Gluconate 325 mg (36 mg elemental iron) PO daily (fewer GI side effects)",
            "Intravenous Iron Therapy (Indicated if oral iron intolerance, malabsorption, active inflammatory bowel disease, 2nd/3rd trimester pregnancy, or severe anemia Hb <7-8): Ferric Carboxymaltose (Injectafer) 750-1000 mg IV single infusion OR Iron Sucrose (Venofer) 200 mg IV weekly",
            "Dietary Counseling: Increase heme iron intake (red meat, poultry, fish); avoid tea, coffee, and calcium supplements with iron doses"
        ],
        "first_line_treatment": "Oral ferrous iron (65-100 mg elemental iron every other day) + Vitamin C, combined with diagnostic workup to identify and treat the source of iron loss (GI endoscopy in adult males/postmenopausal females).",
        "treatment_summary": "Identify etiology of blood loss/malabsorption. Oral iron on alternate days maximizes absorption by preventing hepcidin peaks. IV iron for malabsorption, intolerance, or CKD. Treat underlying source.",
        "disease_intelligence": {
            "disease_name": "Iron Deficiency Anemia (IDA)",
            "etiology": "Inadequate total body iron stores caused by chronic occult blood loss (gastrointestinal bleeding, heavy menstrual bleeding), impaired intestinal absorption (celiac disease, post-gastrectomy), or increased physiological demand (pregnancy, rapid growth).",
            "icd10_code": "D50.9", "icd11_code": "3A00",
            "cardinal_symptoms": ["Profound chronic fatigue, lassitude, and general weakness", "Mucosal and cutaneous pallor (pale conjunctivae, palmar creases)", "Exertional dyspnea and compensatory sinus tachycardia", "Pica (compulsive craving and consumption of non-nutritive substances: pagophagia/ice, chalk, dirt)", "Koilonychia ('spoon nails': thin, brittle, spoon-shaped concave nails)", "Atrophic glossitis (smooth, erythematous, burning tongue) and angular cheilitis"],
            "red_flags": ["Severe symptomatic anemia (angina pectoris, syncope, hemodynamic instability)", "Gross gastrointestinal hemorrhage (melena, hematochezia)", "Underlying occult GI malignancy (colorectal adenocarcinoma) in patients >50yo"],
            "pathophysiology": "Depletion of iron stores leads to insufficient heme synthesis within developing erythroblasts. Resulting red blood cells are small (microcytic) and poorly hemoglobinized (hypochromic). Tissue iron deficiency also impairs mitochondrial cytochrome enzymes and myoglobin, causing severe muscle fatigue and cellular dysfunction.",
            "clinical_pearl": "Serum ferritin is an acute-phase reactant and may be falsely normal or elevated in active infection, malignancy, or liver disease. In inflammatory states, transferrin saturation <20% and soluble transferrin receptor (sTfR) indicate true concurrent iron deficiency."
        },
        "pearl": "Ferritin <30 ng/mL confirms IDA. Oral iron on alternate days optimizes absorption. Mandatory EGD/Colonoscopy in men and postmenopausal women to rule out occult GI cancer."
    },

    "Osteoarthritis": {
        "icd10": "M19.9", "icd11": "FA00", "category": "Rheumatology / Musculoskeletal", "triage": "ROUTINE",
        "immediate_tests": [
            "Targeted Musculoskeletal Physical Exam (crepitus, bony enlargement, joint line tenderness, restricted range of motion)",
            "Weight-Bearing Plain Radiographs of affected joint (AP, lateral, and skyline views for knee; AP pelvis for hip)",
            "Inflammatory Markers: ESR and CRP (normal, cleanly distinguishes from inflammatory / rheumatoid arthritis)",
            "Arthrocentesis with Synovial Fluid Analysis (non-inflammatory: clear yellow, WBC <2,000/mcL, negative crystal exam and culture)"
        ],
        "recommended_investigations": [
            "Serial Weight-Bearing Plain Radiographs (assesses progression of joint space narrowing and Kellgren-Lawrence grade 1-4)",
            "Synovial Fluid Polarized Light Microscopy (excludes concurrent gout or calcium pyrophosphate / pseudogout crystals)",
            "Magnetic Resonance Imaging (MRI: only indicated if clinical suspicion of acute meniscal tear, avascular necrosis, or subchondral insufficiency fracture)"
        ],
        "recommended_medications": [
            "First-Line Topical Therapy (Knee & Hand OA): Topical Diclofenac 1% gel (Voltaren) 2-4g applied QID (excellent efficacy with minimal systemic GI/cardiovascular toxicity)",
            "First-Line Oral Pharmacotherapy: Oral NSAIDs (Naproxen 500 mg PO BID or Celecoxib 100-200 mg PO daily) with a Proton Pump Inhibitor (Omeprazole 20 mg daily) for gastroprotection",
            "Acetaminophen / Paracetamol (Adjunctive): Paracetamol 500-1000 mg PO TID-QID (max 3g/day; safe alternative if NSAIDs contraindicated)",
            "Intra-Articular Corticosteroid Injection: Triamcinolone acetonide 40 mg intra-articular injection (rapid relief for acute knee/hip inflammatory flares; limit to once every 3-4 months)",
            "Severe Refractory Pain: Duloxetine 30-60 mg PO once daily (dual action on chronic musculoskeletal neuropathic/nociceptive pain)"
        ],
        "first_line_treatment": "Patient education + structured weight loss (>5-10% body weight) + low-impact physical exercise (quadriceps strengthening) + Topical Diclofenac gel first-line.",
        "treatment_summary": "Non-pharmacological cornerstone: exercise and weight loss. Topical NSAIDs first-line for knees/hands. Oral NSAIDs + PPI for refractory pain. Intra-articular steroid injections for acute flares. Total joint arthroplasty for end-stage disease.",
        "disease_intelligence": {
            "disease_name": "Osteoarthritis (Degenerative Joint Disease)",
            "etiology": "Biomechanical failure of the synovial joint driven by cellular stress, microtrauma, low-grade innate immune inflammation, and breakdown of articular cartilage and underlying subchondral bone.",
            "icd10_code": "M19.9", "icd11_code": "FA00",
            "cardinal_symptoms": ["Joint pain exacerbated by weight-bearing and activity, relieved by rest", "Morning joint stiffness lasting <30 minutes ('gelling' phenomenon)", "Coarse joint crepitus on passive and active motion", "Bony joint enlargement and joint line tenderness (Heberden nodes at DIPs, Bouchard nodes at PIPs)", "Progressive reduction in joint range of motion and joint instability"],
            "red_flags": ["Rapid unilateral joint swelling with erythema and intense warmth (suspect Septic Arthritis or crystal arthropathy)", "Sudden inability to bear weight (subchondral insufficiency fracture / meniscal tear)", "Constitutional symptoms (fever, weight loss suggest systemic autoimmune disease)"],
            "pathophysiology": "Chondrocyte senescence and phenotypic shift lead to matrix metalloproteinase (MMP) release, breakdown of type II collagen and aggrecan, loss of articular cartilage, subchondral bone sclerosis, microfractures, subchondral cysts, and compensatory marginal osteophyte formation.",
            "clinical_pearl": "Radiographic findings of osteoarthritis correlate poorly with patient-reported pain severity. A patient with severe joint space loss on X-ray may experience minimal discomfort, while another with mild radiographic disease may report incapacitating pain."
        },
        "pearl": "Activity-related joint pain + morning stiffness <30 min + crepitus. Normal ESR/CRP. Weight-bearing X-ray: joint space narrowing, subchondral sclerosis, osteophytes. Topical Diclofenac first line."
    },

    "Septic Shock / Severe Sepsis": {
        "icd10": "R65.21", "icd11": "MG42.1", "category": "Critical Care / Emergency Medicine", "triage": "EMERGENT",
        "immediate_tests": [
            "Venous / Arterial Blood Gas with STAT Lactate (hyperlactatemia > 2.0 mmol/L indicates cellular hypoperfusion; >=4.0 mmol/L denotes severe shock)",
            "Blood Cultures x 2 distinct anatomical sites (aerobic and anaerobic sets drawn PRIOR to antimicrobial initiation)",
            "Continuous Invasive Blood Pressure / Telemetry (target Mean Arterial Pressure [MAP] >= 65 mmHg)",
            "Complete Blood Count with differential (marked leukocytosis >12,000 or leukopenia <4,000, immature bands >10%, thrombocytopenia)",
            "Comprehensive Metabolic Panel (serum creatinine elevation, acute hepatic dysfunction with hyperbilirubinemia, electrolyte derangements)"
        ],
        "recommended_investigations": [
            "Serial Serum Lactate at 2 to 4 hours (guides resuscitation; goal is >20% clearance every 2 hours)",
            "Urinalysis and Urine Culture with Antimicrobial Susceptibilities (screens for genitourinary sepsis source)",
            "Portable Chest Radiograph (PA/AP: detects lobar consolidation, bilateral alveolar infiltrates of ARDS, or occult pneumonia)",
            "Coagulation Panel: PT/INR, aPTT, D-Dimer, Fibrinogen (surveillance for Disseminated Intravascular Coagulation [DIC])",
            "Serum Procalcitonin (PCT >= 0.5-2.0 mcg/L supports bacterial etiology and aids antimicrobial de-escalation)",
            "Point-of-Care Echocardiography (POCUS: assesses IVC collapsibility, left ventricular systolic function, and rules out pericardial tamponade)"
        ],
        "recommended_medications": [
            "First-Line Vasopressor of Choice: Norepinephrine Bitartrate 0.02-1.0 mcg/kg/min continuous IV infusion titrated to target MAP >= 65 mmHg",
            "Immediate Empirical Antimicrobial Coverage (within 1 Hour): Piperacillin-Tazobactam 4.5 g IV q8h (extended 4-hour infusion) PLUS Vancomycin 25-30 mg/kg IV loading dose",
            "Second-Line Vasopressor for Refractory Shock: Vasopressin 0.03 units/min fixed-rate continuous IV infusion (added when norepinephrine exceeds 0.25 mcg/kg/min)",
            "Aggressive Crystalloid Resuscitation: Balanced Crystalloids (Lactated Ringer's / Plasmalyte) 30 mL/kg IV within the first 3 hours",
            "Refractory Septic Shock Corticosteroid: IV Hydrocortisone 200 mg/day (administered as 50 mg IV q6h or continuous infusion)"
        ],
        "first_line_treatment": "Surviving Sepsis Campaign 1-Hour Bundle: Measure lactate, obtain blood cultures, administer broad-spectrum IV antibiotics within 1 hour, infuse 30 mL/kg balanced crystalloids for hypotension/lactate >=4, and initiate Norepinephrine to maintain MAP >= 65 mmHg.",
        "treatment_summary": "Medical emergency with high mortality (>30-40%). Sepsis-3 definition: life-threatening organ dysfunction caused by a dysregulated host response to infection (SOFA score increase >=2). Septic shock: persistent hypotension requiring vasopressors to maintain MAP >=65 and lactate >2 despite fluid resuscitation.",
        "disease_intelligence": {
            "disease_name": "Septic Shock and Severe Sepsis",
            "etiology": "Infection-induced systemic inflammatory response syndrome triggered most commonly by pneumonia, urinary tract infections, intra-abdominal infections, and bloodstream infections (Gram-negative bacilli: E. coli, Klebsiella, Pseudomonas; Gram-positive cocci: S. aureus, S. pneumoniae).",
            "icd10_code": "R65.21", "icd11_code": "MG42.1",
            "diagnostic_criteria": "Sepsis-3 International Consensus Criteria: Suspected infection + acute increase in Sequential Organ Failure Assessment (SOFA) score >= 2 points. Septic Shock: Sepsis with persistent hypotension requiring vasopressors to maintain MAP >= 65 mmHg AND serum lactate > 2.0 mmol/L despite adequate fluid volume resuscitation.",
            "cardinal_symptoms": ["Profound hypotension (SBP < 90 mmHg or MAP < 65 mmHg refractory to initial fluid challenge)", "Hyperthermia (>38.3°C) or hypothermia (<36.0°C denotes poor prognosis)", "Tachypnea (respiratory rate > 22-26/min, early sign of metabolic acidosis compensation)", "Tachycardia (heart rate > 100-120 bpm)", "Altered mental status (encephalopathy, acute delirium, lethargy)", "Oliguria (urine output < 0.5 mL/kg/hr for >2 hours)", "Peripheral mottling, delayed capillary refill (>3 sec), cold clammy extremities"],
            "red_flags": ["Serum Lactate >= 4.0 mmol/L (heralds severe tissue hypoperfusion and impending cardiovascular collapse)", "Acute Respiratory Distress Syndrome (ARDS: PaO2/FiO2 ratio <= 300 with bilateral ground-glass infiltrates)", "Disseminated Intravascular Coagulation (DIC: spontaneous oozing from catheter sites, purpura fulminans, profound thrombocytopenia)", "Refractory distributive vasoplegia despite dual vasopressors"],
            "pathophysiology": "Pathogen-associated molecular patterns (PAMPs) activate toll-like receptors on immune cells, triggering an uncontrolled cascade of proinflammatory cytokines (TNF-alpha, IL-1, IL-6), inducible nitric oxide synthase (iNOS) overactivation, profound systemic arteriolar vasodilation, widespread endothelial glycocalyx degradation, microvascular thrombosis, and diffuse capillary leakage leading to cellular dysoxia and multi-organ failure.",
            "clinical_pearl": "Administering broad-spectrum antimicrobials within the first hour of recognition reduces mortality by 7.6% per hour of delay. Never withhold or delay antibiotic administration if blood cultures cannot be rapidly obtained!"
        },
        "pearl": "Sepsis-3: Infection + SOFA >=2. Shock = vasopressor for MAP >=65 + lactate >2 despite 30 mL/kg fluids. Broad-spectrum IV antibiotics within 1 hour. Norepinephrine first line. Re-check lactate q2h."
    },

    "Bacterial Meningitis": {
        "icd10": "G00.9", "icd11": "1D01.0", "category": "Emergency Neurology / Infectious Diseases", "triage": "EMERGENT",
        "immediate_tests": [
            "Lumbar Puncture (STAT CSF analysis: opening pressure >200-300 mmH2O, WBC count >1,000-5,000/mcL with >80% neutrophils, elevated protein >100-500 mg/dL, low glucose <40 mg/dL or CSF:serum glucose ratio <0.40)",
            "CSF Gram Stain, Bacterial Culture, and Multiplex FilmArray PCR (STAT identification of S. pneumoniae, N. meningitidis, H. influenzae, Listeria)",
            "Blood Cultures x 2 sets drawn STAT prior to antimicrobial initiation",
            "Screening for Increased Intracranial Pressure (STAT head CT prior to LP indicated ONLY if new focal neurological deficit, new seizures, papilledema, immunocompromised state, or GCS <10)",
            "Complete Blood Count and Coagulation Panel (PT/INR, aPTT, platelets to rule out coagulopathy prior to spinal tap)"
        ],
        "recommended_investigations": [
            "Multiplex CSF BioFire Meningitis/Encephalitis PCR Panel (rapid 1-hour pathogen identification)",
            "CSF Latex Agglutination / Antigen Panel (helpful if antibiotics were administered prior to lumbar puncture)",
            "Non-Contrast Head CT (excludes intracranial mass effect, acute hydrocephalus, or cerebral herniation risk)",
            "Serum Electrolytes (surveillance for Syndrome of Inappropriate Antidiuretic Hormone secretion [SIADH])",
            "Audiometry / Hearing Evaluation during recovery (evaluates sensorineural cochlear damage)"
        ],
        "recommended_medications": [
            "First-Line Empirical Antimicrobial Regimen: Ceftriaxone 2 g IV every 12 hours (double meningitic dose) PLUS Vancomycin 15-20 mg/kg IV every 8-12 hours (target trough 15-20 mcg/mL)",
            "Mandatory Listeria Coverage (Age >= 50, Pregnancy, Immunocompromise): Add IV Ampicillin 2 g every 4 hours",
            "Adjunctive Anti-Inflammatory Corticosteroid: Dexamethasone 10 mg IV administered 15 to 20 minutes BEFORE or CONCURRENTLY WITH the first dose of antibiotics, repeated every 6 hours for 4 days",
            "Severe Cephalosporin/Beta-Lactam Allergy Alternative: Chloramphenicol 25 mg/kg IV q6h OR Moxifloxacin 400 mg IV daily PLUS Vancomycin",
            "Close Contact Chemoprophylaxis (for Neisseria meningitidis): Rifampin 600 mg PO BID x 2 days OR Ciprofloxacin 500 mg PO single dose OR Ceftriaxone 250 mg IM single dose"
        ],
        "first_line_treatment": "Immediate high-dose IV Ceftriaxone (2g q12h) + Vancomycin + IV Dexamethasone (10mg) prior to or with antibiotics. Add Ampicillin (2g q4h) if age >=50 or immunocompromised. NEVER delay antibiotics for a CT scan!",
        "treatment_summary": "Neurological emergency with high fatality and neurological sequelae. Triad of fever, altered mental status, and neck stiffness. If head CT is required before LP, DRAW BLOOD CULTURES AND START ANTIBIOTICS + DEXAMETHASONE IMMEDIATELY before sending to CT.",
        "disease_intelligence": {
            "disease_name": "Acute Bacterial Meningitis",
            "etiology": "Suppurative infection of the leptomeninges and subarachnoid space primarily caused by Streptococcus pneumoniae (50%), Neisseria meningitidis (25%), Listeria monocytogenes (10% in elderly/immunocompromised/neonates), and Group B Streptococcus.",
            "icd10_code": "G00.9", "icd11_code": "1D01.0",
            "diagnostic_criteria": "Definitive diagnosis via Lumbar Puncture CSF findings: Pleocytosis (>1,000 WBC/mcL, >80% polymorphonuclear leukocytes), elevated opening pressure (>200 mmH2O), CSF protein >100-500 mg/dL, and CSF:serum glucose ratio < 0.40 (or absolute CSF glucose < 40 mg/dL) with positive CSF Gram stain, PCR, or culture.",
            "cardinal_symptoms": ["Classic Clinical Triad (present in 44% of patients): Fever, altered mental status, and nuchal rigidity (stiff neck)", "Almost all patients (>95%) present with at least two of four symptoms: headache, fever, neck stiffness, and altered consciousness", "Severe, intractable, generalized holocephalic headache", "Marked photophobia and phonophobia", "Positive Kernig sign (resistance and pain on passive knee extension with hip flexed 90 degrees)", "Positive Brudzinski sign (passive neck flexion induces spontaneous involuntary flexion of hips and knees)", "Jolt Accentuation of Headache (worsening of baseline headache by rotating head horizontally at 2-3 turns per second)"],
            "red_flags": ["Petechial or Non-Blanching Purpuric Rash (pathognomonic for Neisseria meningitidis bacteremia / meningococcemia)", "Purpura Fulminans and Waterhouse-Friderichsen Syndrome (bilateral adrenal hemorrhage leading to acute adrenal collapse and catastrophic septic shock)", "Rapid decline in Glasgow Coma Scale (GCS <= 8 heralds herniation)", "Focal neurological deficits (cranial nerve palsies III, IV, VI, VII or hemiparesis)"],
            "pathophysiology": "Pathogens colonize the nasopharynx, invade mucosal microvasculature, survive bacteremia via protective polysaccharide capsules, cross the blood-brain barrier via receptor-mediated transcytosis into the subarachnoid space, and release endotoxins/peptidoglycans that incite intense subarachnoid inflammation, neutrophilic recruitment, purulent exudate accumulation, cerebral edema, elevated ICP, and cortical thrombophlebitis.",
            "clinical_pearl": "Dexamethasone MUST be administered prior to or concurrently with the first dose of antibiotics; giving steroids after antibiotics is of NO proven benefit because the initial lysis of bacteria has already triggered the inflammatory cytokine surge. Discontinue dexamethasone if pneumococcus is ruled out."
        },
        "pearl": "Fever + headache + neck stiffness + altered mental status. Dexamethasone 10mg IV STAT + Ceftriaxone 2g q12h + Vancomycin (add Ampicillin if >=50yo). Do NOT delay antibiotics for CT! LP: neutrophils, protein >100, glucose ratio <0.4."
    },

    "Status Epilepticus": {
        "icd10": "G40.901", "icd11": "8A68.0", "category": "Emergency Neurology / Neurocritical Care", "triage": "EMERGENT",
        "immediate_tests": [
            "STAT Point-of-Care Capillary Blood Glucose (immediately rules out or identifies severe hypoglycemia as reversible trigger)",
            "Continuous Pulse Oximetry and End-Tidal CO2 Monitoring (respiratory failure, hypoventilation from seizure or benzodiazepines)",
            "Basic Metabolic Panel with Ionized Calcium and Magnesium (evaluates hyponatremia, hypocalcemia, hypomagnesemia, and renal failure)",
            "Antiepileptic Drug (AED) Serum Trough Levels (detects non-compliance or subtherapeutic medication levels in known epileptic patients)",
            "Urine and Serum Toxicology Screen (detects sympathomimetics, cocaine, amphetamines, tricyclic antidepressants, synthetic cannabinoids)"
        ],
        "recommended_investigations": [
            "Continuous Video Electroencephalography (cEEG: mandatory within 1-2 hours to identify non-convulsive status epilepticus [NCSE] in patients who fail to regain consciousness)",
            "Emergent Non-Contrast Head CT (identifies acute intracranial hemorrhage, massive stroke, cerebral edema, or structural mass lesion)",
            "Lumbar Puncture with CSF Analysis (indicated once airway secured and CT completed if CNS infection / encephalitis suspected)",
            "Serum Lactate and Creatine Kinase (CK: detects post-ictal severe metabolic lactic acidosis and rhabdomyolysis)"
        ],
        "recommended_medications": [
            "Phase 1 First-Line Emergency Benzodiazepine (0-5 minutes): Lorazepam 0.1 mg/kg IV (typically 4 mg slow IV push over 2 min; repeat once at 5-10 min if seizing persists) OR Midazolam 10 mg IM (if no IV access)",
            "Phase 2 First-Line Urgent Antiepileptic (5-20 minutes): Levetiracetam (Keppra) 60 mg/kg IV (max 4,500 mg) infused over 10 minutes",
            "Alternative Phase 2 Urgent Antiepileptic: Fosphenytoin 20 mg PE/kg IV (max 1,500 mg PE) infused at up to 150 mg PE/min with ECG telemetry OR Valproate Sodium 40 mg/kg IV (max 3,000 mg)",
            "Phase 3 Refractory Status Epilepticus (20-60 minutes): Rapid Sequence Intubation (RSI) with continuous IV anesthetic infusion: Propofol (2-5 mg/kg bolus, then 2-10 mg/kg/hr) OR Midazolam (0.2 mg/kg bolus, then 0.05-2 mg/kg/hr)",
            "Reversible Trigger Antidote: 50% Dextrose (50 mL IV push) + Thiamine 100 mg IV (if hypoglycemic or alcohol-dependent to prevent Wernicke encephalopathy)"
        ],
        "first_line_treatment": "Lorazepam 4 mg IV (or Midazolam 10 mg IM) immediately at 5 minutes. If seizures persist beyond 10-15 minutes, infuse IV Levetiracetam 60 mg/kg (or Fosphenytoin 20 mg PE/kg). If refractory past 30 min, intubate and start continuous Propofol or Midazolam infusion with cEEG monitoring.",
        "treatment_summary": "Life-threatening neurological emergency. Operational definition (AES): convulsive seizure lasting >= 5 minutes (T1) warrants immediate treatment; at >= 30 minutes (T2), irreversible neuronal death and pharmacoresistance ensue. The longer status epilepticus persists, the less responsive GABA receptors become.",
        "disease_intelligence": {
            "disease_name": "Status Epilepticus (Generalized Convulsive)",
            "etiology": "Acute structural, metabolic, infectious, or toxic insult to the central nervous system (acute ischemic/hemorrhagic stroke, CNS infection, traumatic brain injury, anoxia), antiepileptic drug withdrawal in known epilepsy, toxic ingestions, or severe electrolyte derangements.",
            "icd10_code": "G40.901", "icd11_code": "8A68.0",
            "diagnostic_criteria": "American Epilepsy Society (AES) Operational Criteria: Continuous, unremitting generalized convulsive seizure activity lasting >= 5 minutes, OR two or more discrete seizures without complete interictal recovery of baseline consciousness between episodes.",
            "cardinal_symptoms": ["Continuous, rhythmic bilateral tonic-clonic motor convulsions of extremities lasting >= 5 minutes", "Persistent loss of consciousness and unresponsiveness", "Cyanosis, shallow irregular respirations, or apnea with stertorous breathing", "Tongue biting (lateral border lacerations pathognomonic)", "Urinary or fecal incontinence", "Excessive salivation and oral frothing", "Post-ictal profound coma or subtle rhythmic twitching (nystagmus, eyelid myoclonus in subtle/non-convulsive status)"],
            "red_flags": ["Hyperthermia (core body temperature > 40°C due to sustained violent muscular contraction)", "Severe Lactic Acidosis (lactate frequently >10-15 mmol/L from anaerobic muscular metabolism)", "Rhabdomyolysis and Myoglobinuric Acute Renal Failure", "Neurogenic Pulmonary Edema and Cardiac Dysrhythmias", "Transformation into Subtle or Non-Convulsive Status Epilepticus (motor movements cease but brain remains in continuous seizure)"],
            "pathophysiology": "Failure of endogenous GABA-mediated inhibitory mechanisms combined with sustained NMDA-mediated glutamatergic excitatory transmission. Over time, synaptic GABAA receptors undergo clathrin-dependent endocytosis and internalization, while excitatory NMDA receptors migrate to the synaptic cleft, causing progressive loss of benzodiazepine responsiveness ('pharmacoresistance') and excitotoxic calcium-mediated neuronal apoptosis.",
            "clinical_pearl": "Do NOT wait 30 minutes to initiate treatment! Brain damage and pharmacoresistance begin at 5 minutes. If a patient stops convulsing but fails to awaken within 20-30 minutes, assume Non-Convulsive Status Epilepticus (NCSE) until proven otherwise by emergent continuous EEG."
        },
        "pearl": "Seizure >=5 min = Status Epilepticus. Lorazepam 4mg IV (or Midazolam 10mg IM) STAT at 5 min. If persisting at 10 min, Levetiracetam 60mg/kg IV (max 4.5g). If refractory >30 min, intubate + Propofol. Check glucose STAT."
    },

    "Acute Upper Gastrointestinal Bleeding": {
        "icd10": "K92.0", "icd11": "MD30", "category": "Emergency Gastroenterology", "triage": "EMERGENT",
        "immediate_tests": [
            "Two Large-Bore Peripheral IV Lines (16- or 18-gauge) or Rapid Infuser Catheter for aggressive crystalloid/blood resuscitation",
            "STAT Type and Screen with Crossmatch for 4 to 6 units Packed Red Blood Cells (PRBCs) and Plasma",
            "Complete Blood Count with Platelets (initial hematocrit may be falsely normal before volume equilibration)",
            "Coagulation Studies: PT/INR, aPTT, Fibrinogen (critical in cirrhotic patients and those on anticoagulants)",
            "Comprehensive Metabolic Panel with BUN:Creatinine Ratio (BUN:Cr ratio > 30:1 strongly indicates upper GI source due to digestion and resorption of blood proteins)"
        ],
        "recommended_investigations": [
            "Urgent Esophagogastroduodenoscopy (EGD: within 24 hours of presentation, or within 12 hours if hemodynamically unstable or suspected varices)",
            "Serial Hemoglobin / Hematocrit every 4 to 6 hours to assess ongoing hemorrhage",
            "Glasgow-Blatchford Score (GBS: clinical risk stratification; score <=1 predicts safe outpatient management; score >=6 indicates high risk of intervention)",
            "Rockall Score or AIMS65 Score (predicts mortality and rebleeding risk)",
            "Abdominal Ultrasound with Doppler (in patients with chronic liver disease to evaluate portal vein thrombosis and ascites)"
        ],
        "recommended_medications": [
            "High-Dose Intravenous Proton Pump Inhibitor: Pantoprazole 80 mg IV bolus STAT, followed by continuous infusion of 8 mg/hr for 72 hours (or 40 mg IV BID)",
            "Suspected Variceal Hemorrhage (Cirrhosis / Portal Hypertension): Octreotide 50 mcg IV bolus STAT, followed by continuous IV infusion of 50 mcg/hr for 2 to 5 days",
            "Prophylactic Antibiotic for Cirrhotic Patients: Ceftriaxone 1 g IV every 24 hours for 7 days (reduces bacterial infections and rebleeding mortality)",
            "Prokinetic Agent Prior to Endoscopy: Erythromycin 250 mg IV infusion 30-90 minutes prior to EGD (clears clots from stomach and improves visualization)",
            "Reversal of Anticoagulation (if life-threatening hemorrhage): 4-Factor Prothrombin Complex Concentrate (Kcentra) + IV Vitamin K 10 mg for Warfarin; Andexanet alfa or Idarucizumab for DOACs"
        ],
        "first_line_treatment": "Two large-bore IVs + restrictive PRBC transfusion (transfuse at Hb <7 g/dL, target 7-9 g/dL) + IV Pantoprazole 80mg bolus + 8mg/h infusion + IV Octreotide (if variceal) + urgent EGD within 24 hours.",
        "treatment_summary": "Common gastrointestinal emergency. Hemodynamic resuscitation takes precedence over endoscopy. Restrictive transfusion strategy (threshold <7 g/dL) significantly improves survival compared to liberal transfusion (TRICC / Villanueva trials).",
        "disease_intelligence": {
            "disease_name": "Acute Upper Gastrointestinal Bleeding",
            "etiology": "Bleeding originating proximal to the ligament of Treitz. Causes: Peptic Ulcer Disease (gastric/duodenal ulcers, 50%), Gastroesophageal Varices (portal hypertension, 15-20%), Mallory-Weiss tears (5-10%), Erosive Gastritis/Duodenitis, Angiodysplasia, Dieulafoy lesions, and gastric malignancy.",
            "icd10_code": "K92.0", "icd11_code": "MD30",
            "diagnostic_criteria": "Clinical presentation of hematemesis, coffee-ground emesis, or melena confirmed by diagnostic upper endoscopy (EGD) demonstrating the bleeding source and Forrest classification (Forrest Ia: spurting; Ib: oozing; IIa: non-bleeding visible vessel; IIb: adherent clot; IIc: flat pigmented spot; III: clean base).",
            "cardinal_symptoms": ["Hematemesis (vomiting of frank bright red blood or dark clots)", "Coffee-ground emesis (vomiting of dark, granular, digested blood altered by gastric acid)", "Melena (passage of black, tarry, foul-smelling, sticky stools caused by hemoglobin oxidation by gut bacteria)", "Hematochezia (passage of bright red blood per rectum: typically lower GI, but occurs in 10-15% of massive, brisk upper GI hemorrhages with shock)", "Orthostatic dizziness, presyncope, and syncope", "Tachycardia and postural hypotension"],
            "red_flags": ["Hemodynamic Shock (SBP < 90 mmHg, HR > 110 bpm, cold clammy extremities denotes massive blood loss >30-40% circulating volume)", "Hematochezia with Hypotension (indicates catastrophic, torrential upper GI bleed)", "Cirrhosis with Acute Variceal Rupture (50% risk of early rebleeding and 20% 6-week mortality)", "Active arterial spurting on endoscopy (Forrest Ia carries 90% rebleeding risk without endoscopic hemostasis)"],
            "pathophysiology": "Erosion into submucosal arteries or rupture of dilated submucosal esophageal/gastric varices under elevated hydrostatic portal pressure (>12 mmHg). Gastric acid and pepsin break down newly formed platelet plugs and dissolve fibrin clots when intragastric pH is acidic (<6.0); maintaining neutral intragastric pH (>6.0) with high-dose PPIs is required for stable clot architecture.",
            "clinical_pearl": "Transfuse conservatively! The landmark Villanueva trial showed that a restrictive transfusion threshold (transfusing when Hb < 7 g/dL targeting 7-9 g/dL) resulted in significantly higher survival and lower rebleeding rates compared to liberal transfusion (threshold < 9 g/dL), because over-transfusion increases central venous and portal pressures, blowing off newly formed clots."
        },
        "pearl": "Hematemesis or melena. Restrictive transfusion (target Hb 7-9 g/dL). IV Pantoprazole 80mg bolus + 8mg/h. If cirrhotic, add IV Octreotide + Ceftriaxone STAT. Urgent EGD within 24 hours. BUN:Cr >30 indicates upper GI source."
    },

    "Refsum Disease": {
        "icd10": "G60.1", "icd11": "8C00.1", "category": "Metabolic Neurology / Peroxisomal Lipidosis", "triage": "URGENT",
        "immediate_tests": [
            "Fasting Plasma Phytanic Acid and Pristanic Acid Quantification (confirmatory: marked phytanic acid elevation >200-2000 umol/L; normal <10-30 umol/L)",
            "Plasma Very-Long-Chain Fatty Acids (VLCFAs: C26:0, C24/C22, C26/C22 ratios — strictly NORMAL, excludes Zellweger spectrum / infantile Refsum)",
            "12-Lead Electrocardiogram and Continuous Cardiac Telemetry (detects QT prolongation, AV conduction blocks, and intermittent atrial arrhythmias)",
            "Ophthalmologic Electroretinography (ERG) & Dilated Funduscopy (pigmentary retinal degeneration with severely reduced/extinguished rod responses)",
            "Nerve Conduction Studies (NCS: marked demyelinating polyneuropathy with slowed conduction velocities and prolonged distal latencies)"
        ],
        "recommended_investigations": [
            "Molecular Genetic Sequencing of PHYH (phytanoyl-CoA hydroxylase, 10p13, ~90%) and PEX7 (peroxin-7, 6q23.3, ~10%)",
            "Pure Tone Audiometry (quantifies bilateral progressive sensorineural hearing loss)",
            "Transthoracic Echocardiogram (evaluates cardiomyopathy and left ventricular function)",
            "Automated Visual Field Perimetry (evaluates concentric peripheral visual field constriction / tunnel vision)",
            "Comprehensive Metabolic Panel with Blood Glucose (rule out secondary metabolic or diabetic neuropathies)"
        ],
        "recommended_medications": [
            "Strict Dietary Elimination: Restrict dietary phytanic acid to <10 mg/day (eliminate ruminant meat, beef, lamb, dairy fat, butter, cheese, and farmed fish)",
            "High-Caloric Maintenance Regimen (prevent catabolism): High-carbohydrate nutrition (>=2000-2500 kcal/day) or IV 10% Dextrose during acute illness/surgery to prevent adipose tissue lipolysis",
            "Therapeutic Plasma Exchange (Plasmapheresis): 1-2 plasma volumes exchanged every 1-2 weeks for acute toxic exacerbations (>1000 umol/L), progressive neuropathy, or arrhythmias",
            "Topical Keratolytics: Urea 10-20% or Ammonium Lactate 12% lotion daily for dry scaly skin / ichthyosis",
            "Antiarrhythmic / Pacing Management: Cardiology consultation for antiarrhythmics or permanent pacemaker implantation if high-grade AV block occurs",
            "Absolute Safety Contraindication: STRICTLY AVOID FASTING, hypocaloric diets, or rapid weight loss; lipolysis floods circulation with phytanic acid, provoking fatal arrhythmias"
        ],
        "first_line_treatment": "Lifelong strict dietary phytanic acid restriction (<10 mg/day) + avoidance of fasting/catabolism + therapeutic plasma exchange for acute neuro-cardiac decompensation.",
        "treatment_summary": "Classic Adult Refsum Disease (Heredopathia Atactica Polyneuritiformis) caused by autosomal recessive PHYH/PEX7 mutations impairing peroxisomal alpha-oxidation. Cardinal pentad: Retinitis pigmentosa (nyctalopia), sensorimotor polyneuropathy, cerebellar ataxia, anosmia, and sensorineural deafness. Normal VLCFAs distinguishes it from Zellweger spectrum disorders.",
        "disease_intelligence": {
            "disease_name": "Refsum Disease (Classic Adult Refsum Disease / Heredopathia Atactica Polyneuritiformis)",
            "etiology": "Autosomal recessive peroxisomal alpha-oxidation disorder caused by biallelic mutations in PHYH (encoding phytanoyl-CoA 2-hydroxylase, 10p13, ~90%) or PEX7 (encoding peroxin-7 / PTS2 receptor, 6q23.3, ~10%).",
            "icd10_code": "G60.1", "icd11_code": "8C00.1",
            "cardinal_symptoms": ["Night blindness (nyctalopia) and retinitis pigmentosa", "Symmetric sensorimotor peripheral polyneuropathy (distal sensory loss, absent ankle reflexes, weakness)", "Cerebellar gait ataxia", "Anosmia / hyposmia (present in virtually 100% of classic patients)", "Sensorineural hearing loss", "Dry, scaly skin (ichthyosis)", "Intermittent cardiac arrhythmias and conduction defects"],
            "red_flags": ["Acute cardiac arrhythmias / heart block / sudden cardiac death", "Fulminant neurotoxicity triggered by acute fasting, infection, or rapid weight loss (uncontrolled lipolysis)", "Rapidly progressive tetraplegia and respiratory muscle weakness"],
            "pathophysiology": "Phytanic acid (3,7,11,15-tetramethylhexadecanoic acid) is a branched-chain fatty acid derived exclusively from dietary chlorophyll/phytol (ruminant fats, dairy). Because of the 3-methyl group, it cannot undergo direct beta-oxidation and requires initial alpha-oxidation by phytanoyl-CoA hydroxylase to remove one carbon and form pristanic acid. Enzyme deficiency leads to progressive toxic accumulation in lipid-rich neural tissues, myelin, and myocardium, causing demyelination, pigmentary retinopathy, ataxia, and conduction system fibrosis.",
            "clinical_pearl": "Normal very-long-chain fatty acids (VLCFAs) is the pathognomonic biochemical clue distinguishing Adult Refsum disease (isolated alpha-oxidation defect) from Zellweger spectrum disorders and infantile Refsum disease (generalized peroxisomal assembly defects with elevated VLCFAs and severe neonatal/infantile onset)."
        },
        "pearl": "Adult Refsum: Retinitis pigmentosa + ataxia + polyneuropathy + anosmia + elevated phytanic acid + NORMAL VLCFAs. Autosomal recessive PHYH/PEX7. Diet <10mg phytanic acid/day. Never allow fasting/rapid weight loss!"
    }
}


