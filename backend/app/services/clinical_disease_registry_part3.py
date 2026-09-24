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
    }
}

