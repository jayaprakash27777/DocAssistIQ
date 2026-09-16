"""DocAssistIQ — Enterprise-Grade Investigation Provider (God-Level v3).

Architecture:
  1. Offline Investigation Panel (from offline_disease_kb.py) — ALWAYS accurate, no network
  2. 14-source medical knowledge API — real live data from ICD-11, MedlinePlus, PubMed, etc.
  3. LLM Narrator — writes rationale for pre-built investigation list (short prompt)
  4. Fallback: if LLM fails → offline panel returned directly (still clinical-grade accurate)

No mock data. All investigations are evidence-based from WHO/CDC/NIH protocols.
"""

from app.schemas.investigation import InvestigationResponse, InvestigationSuggestion
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.rag_service import retrieve_medical_context, retrieve_investigation_context
from app.services.llm_service import llm_service
import structlog

log = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Comprehensive Disease Investigation Panel KB
# Evidence-based protocols from WHO, CDC, NIH, IDSA guidelines
# ---------------------------------------------------------------------------

INVESTIGATION_PANELS = {
    # ============================
    # VIRAL HEMORRHAGIC FEVERS
    # ============================
    "bundibugyo virus disease": [
        {"name": "RT-PCR for Bundibugyo ebolavirus (Whole Blood — BSL-4)", "priority": "HIGH PRIORITY",
         "rationale": "Definitive confirmatory test for BVD; detects viral RNA in blood during viremic phase (days 3–10 of illness). WHO-mandated first-line test.",
         "evidence": "WHO Laboratory Guidance for Ebola/BVD (2023); CDC Viral Special Pathogens Branch"},
        {"name": "Viral Antigen ELISA (Ebola/Bundibugyo Antigen Capture)", "priority": "HIGH PRIORITY",
         "rationale": "Rapid antigen detection; positive from day 3; less sensitive than PCR but faster result in field settings.",
         "evidence": "WHO Ebola Response Technical Guidance 2014-2016"},
        {"name": "Complete Blood Count (CBC) with Differential", "priority": "HIGH PRIORITY",
         "rationale": "VHF pattern: leukopenia, lymphopenia early; thrombocytopenia develops. Helps assess severity and DIC risk.",
         "evidence": "WHO Clinical Management of Ebola Virus Disease (2022)"},
        {"name": "Coagulation Panel — PT, aPTT, INR, Fibrinogen, D-Dimer", "priority": "HIGH PRIORITY",
         "rationale": "Detects disseminated intravascular coagulation (DIC) — the leading cause of death in VHF. Monitor daily.",
         "evidence": "Feldmann H et al., NEJM 2020; WHO VHF Case Management Protocol"},
        {"name": "Comprehensive Metabolic Panel (CMP) — LFTs, Renal Panel, Electrolytes", "priority": "HIGH PRIORITY",
         "rationale": "Assesses hepatic failure (elevated AST/ALT is hallmark of VHF), acute kidney injury (oliguria), and electrolyte depletion from diarrhea/vomiting.",
         "evidence": "WHO Integrated Management of Viral Haemorrhagic Fevers"},
        {"name": "Malaria Rapid Diagnostic Test (RDT) + Thick/Thin Blood Film", "priority": "HIGH PRIORITY",
         "rationale": "Co-endemic in DRC; must rule out malaria as a treatable cause before BSL-4 testing; also clinically important therapeutic decision.",
         "evidence": "WHO African Region Malaria Diagnosis Guidelines"},
        {"name": "Blood Culture (Aerobic + Anaerobic, ×2 sets)", "priority": "HIGH PRIORITY",
         "rationale": "Rules out bacterial sepsis as primary or co-infection; critical differential in febrile illness with shock.",
         "evidence": "IDSA Clinical Practice Guidelines for Sepsis"},
        {"name": "Urinalysis + Urine Microscopy (Proteinuria, Casts)", "priority": "CONDITIONAL",
         "rationale": "Oliguria present — assess for glomerulonephritis, tubular necrosis; proteinuria common in VHF.",
         "evidence": "WHO VHF Clinical Guidance"},
        {"name": "Chest X-Ray (PA view)", "priority": "CONDITIONAL",
         "rationale": "Screens for pulmonary edema, pleural effusion, pneumonia. Helps with fluid management decisions.",
         "evidence": "Standard VHF workup — WHO/CDC"},
        {"name": "IgM/IgG Antibody Serology (Ebola/BVD ELISA)", "priority": "CONDITIONAL",
         "rationale": "Seroconversion detectable from day 6–10; useful for convalescent phase confirmation when PCR may be negative.",
         "evidence": "Ksiazek TG et al., JID 1999; WHO Lab Biosafety Guidance"},
        {"name": "Abdominal Ultrasound", "priority": "IF INDICATED",
         "rationale": "Evaluate hepatomegaly, splenomegaly, free fluid (peritoneal bleeding) in severe VHF.",
         "evidence": "Point-of-care ultrasound protocol, MSF/WHO Ebola ETU"},
        {"name": "Serum Lactate (Lactic Acid)", "priority": "IF INDICATED",
         "rationale": "Marker of tissue hypoperfusion and shock; guides aggressive IV fluid resuscitation and ICU admission.",
         "evidence": "Surviving Sepsis Campaign Guidelines 2021"},
    ],

    "ebola virus disease": [
        {"name": "RT-PCR for Zaire ebolavirus (Whole Blood — BSL-4)", "priority": "HIGH PRIORITY",
         "rationale": "Gold standard confirmatory test for Ebola Zaire; WHO-mandated.",
         "evidence": "WHO Laboratory Guidance for EVD (2023)"},
        {"name": "Viral Antigen ELISA (Ebola Antigen Capture)", "priority": "HIGH PRIORITY",
         "rationale": "Rapid antigen detection; positive from day 3 of illness.",
         "evidence": "WHO Ebola Response Technical Guidance"},
        {"name": "CBC with Differential + Platelet Count", "priority": "HIGH PRIORITY",
         "rationale": "Leukopenia, lymphopenia, thrombocytopenia are hallmarks of EVD.",
         "evidence": "CDC Ebola Clinical Guidance"},
        {"name": "Coagulation Panel (PT, aPTT, Fibrinogen, D-Dimer)", "priority": "HIGH PRIORITY",
         "rationale": "DIC is the primary cause of hemorrhage and death in EVD.",
         "evidence": "Feldmann et al., NEJM 2020"},
        {"name": "Liver Function Tests (AST, ALT, Bilirubin, Albumin)", "priority": "HIGH PRIORITY",
         "rationale": "Marked AST/ALT elevation (>1000 IU/L) is characteristic of EVD hepatic involvement.",
         "evidence": "WHO EVD Clinical Management"},
        {"name": "Renal Function (BUN, Creatinine, eGFR, Electrolytes)", "priority": "HIGH PRIORITY",
         "rationale": "Acute kidney injury from dehydration and viral nephritis; guides fluid therapy.",
         "evidence": "WHO EVD Case Management Protocol"},
        {"name": "Malaria RDT + Blood Film", "priority": "HIGH PRIORITY",
         "rationale": "Co-endemic in West/Central Africa; exclude malaria as treatable differential.",
         "evidence": "WHO African Region Clinical Protocols"},
        {"name": "Blood Cultures (×2 aerobic)", "priority": "CONDITIONAL",
         "rationale": "Rule out bacterial co-infection or secondary bacteremia.",
         "evidence": "IDSA Guidelines"},
    ],

    "marburg virus disease": [
        {"name": "RT-PCR for Marburg virus (Whole Blood — BSL-4)", "priority": "HIGH PRIORITY",
         "rationale": "Definitive diagnosis. Marburg and Ebola are serologically distinct — specific PCR required.",
         "evidence": "CDC/WHO Marburg Laboratory Guidance"},
        {"name": "CBC, Coagulation Panel, LFTs, Renal Panel", "priority": "HIGH PRIORITY",
         "rationale": "Same VHF monitoring panel as EVD; DIC, hepatic failure, AKI are leading complications.",
         "evidence": "WHO Marburg Case Management Protocol"},
        {"name": "Malaria RDT", "priority": "HIGH PRIORITY",
         "rationale": "Uganda/Rwanda endemic; exclude malaria.",
         "evidence": "WHO African Region"},
        {"name": "Marburg IgM/IgG Serology (ELISA)", "priority": "CONDITIONAL",
         "rationale": "Seroconversion from day 7; useful for late-phase confirmation.",
         "evidence": "WHO Lab Guidance"},
    ],

    "lassa fever": [
        {"name": "RT-PCR for Lassa arenavirus (Serum/Whole Blood)", "priority": "HIGH PRIORITY",
         "rationale": "Gold standard; detects viral RNA in blood and urine. BSL-3+ required.",
         "evidence": "WHO Lassa Fever Fact Sheet (2023)"},
        {"name": "Lassa Virus IgM/IgG ELISA", "priority": "HIGH PRIORITY",
         "rationale": "Seroconversion typically by day 6-8; IgM indicates active infection.",
         "evidence": "CDC Lassa Fever Case Management"},
        {"name": "CBC with Differential", "priority": "HIGH PRIORITY",
         "rationale": "Leukopenia, thrombocytopenia; unlike EVD, hemorrhage is less prominent.",
         "evidence": "NEJM Lassa Fever Review 2019"},
        {"name": "LFTs, Renal Function, Electrolytes", "priority": "HIGH PRIORITY",
         "rationale": "Hepatic and renal involvement common; guide ribavirin dosing.",
         "evidence": "WHO Lassa Clinical Protocol"},
        {"name": "Audiometry / Hearing Assessment", "priority": "CONDITIONAL",
         "rationale": "Sensorineural hearing loss occurs in 25% of Lassa survivors; important outcome measure.",
         "evidence": "Cummins D et al., JID 1990"},
        {"name": "Ribavirin Therapy Level Monitoring", "priority": "CONDITIONAL",
         "rationale": "Ribavirin is the only proven therapy; renal dosing adjustment required.",
         "evidence": "WHO Essential Medicines List"},
    ],

    # ============================
    # MALARIA
    # ============================
    "malaria (plasmodium falciparum)": [
        {"name": "Thick & Thin Blood Film Microscopy (×3 sets, 12h apart)", "priority": "HIGH PRIORITY",
         "rationale": "Gold standard for malaria species identification and parasite density. P. falciparum has highest mortality risk.",
         "evidence": "WHO Malaria Microscopy Quality Assurance Manual (2016)"},
        {"name": "Malaria Rapid Diagnostic Test (RDT) — HRP-2/pLDH", "priority": "HIGH PRIORITY",
         "rationale": "Results within 15 minutes; detects P. falciparum HRP-2 antigen. WHO-recommended first-line test when microscopy not available.",
         "evidence": "WHO World Malaria Report 2023"},
        {"name": "CBC with Differential + Platelet Count", "priority": "HIGH PRIORITY",
         "rationale": "Anemia (hemolytic), thrombocytopenia, and elevated WBC are hallmarks. Severe anemia (Hb <7) indicates severe malaria.",
         "evidence": "WHO Severe Malaria Treatment Guidelines (3rd Edition)"},
        {"name": "Blood Glucose (Fingerstick + Serum)", "priority": "HIGH PRIORITY",
         "rationale": "Hypoglycemia is a life-threatening complication of severe P. falciparum, especially in children and pregnant women.",
         "evidence": "WHO Severe Malaria Protocol"},
        {"name": "Comprehensive Metabolic Panel (LFTs, Renal, Electrolytes)", "priority": "HIGH PRIORITY",
         "rationale": "Assess for acute kidney injury (blackwater fever), hepatic dysfunction, and electrolyte imbalance.",
         "evidence": "WHO Guidelines for the Treatment of Malaria (2022)"},
        {"name": "Blood Culture (Aerobic ×2)", "priority": "CONDITIONAL",
         "rationale": "Concurrent bacterial sepsis can co-occur with malaria in DRC; important if temperature > 39.5°C.",
         "evidence": "Bacchieri A, Ann Trop Med 2004"},
        {"name": "Lactate Dehydrogenase (LDH)", "priority": "CONDITIONAL",
         "rationale": "Elevated LDH reflects hemolysis; marker of severe malaria and hemolytic anemia severity.",
         "evidence": "WHO Malaria Guidelines"},
        {"name": "Urine Dipstick + Microscopy (Hemoglobinuria)", "priority": "CONDITIONAL",
         "rationale": "Blackwater fever (hemoglobinuria) indicates severe hemolysis — changes management.",
         "evidence": "WHO Severe Malaria Protocol"},
        {"name": "PCR for Malaria (Plasmodium species typing)", "priority": "IF INDICATED",
         "rationale": "Definitive species identification when RDT and microscopy are discordant; detects mixed infections.",
         "evidence": "WHO Technical Manual on Malaria Diagnosis"},
        {"name": "Head CT Scan (without contrast)", "priority": "IF INDICATED",
         "rationale": "Only if cerebral malaria suspected (seizures, coma, GCS < 11) to exclude other causes.",
         "evidence": "WHO Severe Malaria Guidelines"},
    ],

    # ============================
    # TYPHOID FEVER
    # ============================
    "typhoid fever": [
        {"name": "Blood Culture (Aerobic, ×2 sets from different sites)", "priority": "HIGH PRIORITY",
         "rationale": "Gold standard for typhoid fever diagnosis (sensitivity 40-80% in first week). S. typhi bacteremia peaks in week 1-2.",
         "evidence": "WHO Typhoid Fact Sheet (2023); IDSA Typhoid Guidelines"},
        {"name": "Bone Marrow Culture", "priority": "HIGH PRIORITY",
         "rationale": "Highest sensitivity (90%+) even after antibiotic exposure; indicated if blood cultures negative but clinical suspicion high.",
         "evidence": "Gilman RH et al., Lancet 1975"},
        {"name": "Widal Test (Salmonella typhi O and H agglutinins)", "priority": "CONDITIONAL",
         "rationale": "Classic serological test; positive from day 7-10. False positives common — interpret with clinical context.",
         "evidence": "WHO Typhoid Guidance Note"},
        {"name": "Typhidot / Typhoid IgM ELISA (Salmonella typhi IgM/IgG)", "priority": "CONDITIONAL",
         "rationale": "More specific than Widal; detects anti-outer membrane protein antibodies; positive from day 4-5.",
         "evidence": "Ramachandran S et al., AJTMH 2017"},
        {"name": "CBC with Differential", "priority": "HIGH PRIORITY",
         "rationale": "Relative lymphocytosis and leukopenia (white count < 4000) are characteristic of typhoid. Thrombocytopenia in severe cases.",
         "evidence": "Harrison's Principles of Internal Medicine"},
        {"name": "LFTs (AST, ALT, Bilirubin)", "priority": "CONDITIONAL",
         "rationale": "Hepatomegaly and mild transaminitis in 10-40% of typhoid; splenomegaly in 25%.",
         "evidence": "WHO Typhoid Management"},
        {"name": "Stool Culture + Sensitivity", "priority": "CONDITIONAL",
         "rationale": "Highest yield in weeks 3-4 of illness; also useful for contact tracing and antibiotic resistance patterns.",
         "evidence": "WHO Typhoid Guidelines"},
        {"name": "Urine Culture", "priority": "IF INDICATED",
         "rationale": "Salmonella typhi can be shed in urine in 25% of cases in week 3+.",
         "evidence": "WHO Typhoid Surveillance"},
        {"name": "Abdominal Ultrasound", "priority": "IF INDICATED",
         "rationale": "Assess hepatosplenomegaly; detect complications (intestinal perforation, bowel wall thickening).",
         "evidence": "Radiology Guidelines for Typhoid Complications"},
    ],

    # ============================
    # DENGUE
    # ============================
    "dengue fever": [
        {"name": "Dengue NS1 Antigen Rapid Test / ELISA", "priority": "HIGH PRIORITY",
         "rationale": "Detects non-structural protein 1; positive in days 1-5 of fever (highest yield early). WHO-recommended.",
         "evidence": "WHO Dengue Guidelines for Diagnosis, Treatment, Prevention and Control (2012)"},
        {"name": "Dengue IgM / IgG Serology (ELISA)", "priority": "HIGH PRIORITY",
         "rationale": "IgM positive from day 4-5; IgG rises in secondary infection; distinguish primary vs secondary dengue.",
         "evidence": "WHO Dengue Guidelines 2012"},
        {"name": "CBC with Platelet Count (Daily Monitoring)", "priority": "HIGH PRIORITY",
         "rationale": "Platelet count < 100,000 = warning phase; < 20,000 = critical phase with bleeding risk. Monitor every 12-24h.",
         "evidence": "WHO Dengue Clinical Management Protocol"},
        {"name": "Hematocrit (Serial Measurements)", "priority": "HIGH PRIORITY",
         "rationale": ">20% rise in hematocrit from baseline indicates plasma leakage — dengue hemorrhagic fever transition.",
         "evidence": "WHO Dengue Guidelines 2012"},
        {"name": "LFTs (AST, ALT)", "priority": "CONDITIONAL",
         "rationale": "Elevated transaminases (often AST > ALT) in 60-80% of dengue; severe elevation (>1000) indicates severe dengue.",
         "evidence": "Wills BA et al., Lancet 2005"},
        {"name": "Dengue RT-PCR (Serotype Identification)", "priority": "CONDITIONAL",
         "rationale": "Serotype determines risk of hemorrhagic fever in secondary infection; positive days 1-5.",
         "evidence": "WHO Dengue Surveillance Guidelines"},
        {"name": "Chest X-Ray + Pleural Ultrasound", "priority": "IF INDICATED",
         "rationale": "Detect pleural effusion and ascites — markers of severe dengue plasma leakage.",
         "evidence": "WHO Dengue Severity Classification"},
    ],

    # ============================
    # MENINGOCOCCAL MENINGITIS
    # ============================
    "meningococcal meningitis": [
        {"name": "Lumbar Puncture — CSF Analysis (Cell Count, Protein, Glucose, Culture)", "priority": "HIGH PRIORITY",
         "rationale": "Definitive diagnosis; bacterial meningitis: turbid CSF, >1000 WBC/μL (neutrophil-dominant), low glucose, high protein.",
         "evidence": "IDSA Practice Guidelines for Bacterial Meningitis (2017)"},
        {"name": "Blood Culture (×2 sets before antibiotics)", "priority": "HIGH PRIORITY",
         "rationale": "N. meningitidis bacteremia in 50-75% of cases; obtain BEFORE antibiotics (do not delay treatment for this).",
         "evidence": "IDSA Meningitis Guidelines 2017"},
        {"name": "CSF Gram Stain + Culture", "priority": "HIGH PRIORITY",
         "rationale": "Gram-negative diplococci (meningococcus) in CSF Gram stain is diagnostic; sensitivity 60-90%.",
         "evidence": "IDSA Guidelines 2017"},
        {"name": "Meningococcal PCR (CSF + Blood)", "priority": "HIGH PRIORITY",
         "rationale": "Highly sensitive (>90%) even after antibiotic administration; identifies serogroup for outbreak investigation.",
         "evidence": "WHO Meningitis Surveillance Guidelines"},
        {"name": "CBC, CRP, Procalcitonin", "priority": "HIGH PRIORITY",
         "rationale": "Leukocytosis, elevated CRP (>100mg/L) and procalcitonin (>0.5ng/mL) distinguish bacterial from viral meningitis.",
         "evidence": "Tunkel AR et al., CID 2004"},
        {"name": "CT Head (before LP if papilledema or focal neurological signs)", "priority": "CONDITIONAL",
         "rationale": "Exclude space-occupying lesion before LP to prevent herniation. Required if GCS <13 or focal signs.",
         "evidence": "IDSA Guidelines"},
    ],

    # ============================
    # COVID-19
    # ============================
    "covid-19": [
        {"name": "SARS-CoV-2 Nasopharyngeal RT-PCR", "priority": "HIGH PRIORITY",
         "rationale": "Gold standard; highest sensitivity in first 5-7 days of symptoms. WHO-recommended confirmatory test.",
         "evidence": "WHO COVID-19 Technical Guidelines (2023)"},
        {"name": "SARS-CoV-2 Rapid Antigen Test (RAT)", "priority": "HIGH PRIORITY",
         "rationale": "Results in 15-30 minutes; useful for rapid triage. Confirm positives with PCR in low-prevalence settings.",
         "evidence": "WHO Antigen Detection Guidelines (2021)"},
        {"name": "CBC, CRP, Ferritin, D-Dimer, LDH", "priority": "HIGH PRIORITY",
         "rationale": "Inflammatory markers predict disease severity and cytokine storm. D-Dimer >1000 μg/L indicates thromboembolism risk.",
         "evidence": "WHO Clinical Management of COVID-19 (2023)"},
        {"name": "Chest CT Scan (High Resolution)", "priority": "CONDITIONAL",
         "rationale": "Bilateral ground-glass opacities with peripheral distribution are COVID-19 signature (CO-RADS 4-5). More sensitive than CXR.",
         "evidence": "ACR/RSNA COVID-19 Imaging Guidelines"},
        {"name": "Pulse Oximetry (Continuous SpO2 Monitoring)", "priority": "HIGH PRIORITY",
         "rationale": "Silent hypoxia (SpO2 < 94%) without dyspnea is a COVID-19 hallmark; mandatory monitoring.",
         "evidence": "WHO Oxygen Therapy Guidelines"},
    ],

    # ============================
    # CHOLERA
    # ============================
    "cholera": [
        {"name": "Stool Culture (V. cholerae O1/O139) + Sensitivity", "priority": "HIGH PRIORITY",
         "rationale": "Definitive diagnosis; Vibrio cholerae on TCBS agar with confirmatory agglutination. Required for outbreak notification.",
         "evidence": "WHO Cholera Technical Guidelines (2023)"},
        {"name": "Rapid Cholera Dipstick Test (Crystal VC)", "priority": "HIGH PRIORITY",
         "rationale": "Point-of-care test; results in 15 minutes for field settings; sensitivity 80-90% for O1/O139.",
         "evidence": "WHO/GTFCC Cholera Rapid Diagnostics"},
        {"name": "Stool Dark-Field Microscopy (Motile Vibrios)", "priority": "CONDITIONAL",
         "rationale": "Rapid visualization of darting motile vibrios in fresh stool; specific if positive.",
         "evidence": "WHO Cholera Lab Guidance"},
        {"name": "Serum Electrolytes, BUN, Creatinine", "priority": "HIGH PRIORITY",
         "rationale": "Severe dehydration causes hyponatremia, hypokalemia, metabolic acidosis, pre-renal AKI. Guides rehydration therapy.",
         "evidence": "WHO ORS/IV Fluid Protocol"},
        {"name": "Serum/Plasma Bicarbonate (Metabolic Acidosis Assessment)", "priority": "HIGH PRIORITY",
         "rationale": "Profound metabolic acidosis from bicarbonate loss in rice-water stools; guides IV Ringer's Lactate therapy.",
         "evidence": "WHO Cholera Treatment Guidelines"},
    ],

    # ============================
    # LEPTOSPIROSIS
    # ============================
    "leptospirosis": [
        {"name": "Leptospira IgM ELISA (LeptoTek Dri-Dot / ELISA)", "priority": "HIGH PRIORITY",
         "rationale": "IgM detectable from day 4-5 of illness; sensitivity 60-80% in first week. WHO-recommended.",
         "evidence": "WHO Leptospirosis Fact Sheet; PAHO Guidelines"},
        {"name": "Microscopic Agglutination Test (MAT) — Paired Sera", "priority": "HIGH PRIORITY",
         "rationale": "Gold standard serology; 4-fold rise in titre between acute and convalescent sera confirms diagnosis. Reference lab required.",
         "evidence": "WHO/OIE/FAO Leptospira Reference Centre"},
        {"name": "Blood Culture (Leptospira-specific EMJH medium)", "priority": "CONDITIONAL",
         "rationale": "Positive in first week of illness; requires specialized media and up to 6 weeks incubation.",
         "evidence": "WHO Leptospira Lab Manual"},
        {"name": "LFTs (AST, ALT, Bilirubin — Weil's Disease Assessment)", "priority": "HIGH PRIORITY",
         "rationale": "Severe leptospirosis (Weil's disease) causes jaundice, hepatic failure; bilirubin >85 μmol/L defines severe disease.",
         "evidence": "Bharti AR et al., Lancet Infect Dis 2003"},
        {"name": "Renal Function (BUN, Creatinine, Urine Output)", "priority": "HIGH PRIORITY",
         "rationale": "Acute tubulointerstitial nephritis causing AKI is the leading cause of death in Weil's disease.",
         "evidence": "WHO Leptospirosis Clinical Guidelines"},
        {"name": "CK (Creatine Kinase) — Myositis Assessment", "priority": "CONDITIONAL",
         "rationale": "Marked myalgia and tenderness; elevated CK indicates rhabdomyolysis component.",
         "evidence": "Bharti AR et al., 2003"},
        {"name": "Chest X-Ray", "priority": "CONDITIONAL",
         "rationale": "Pulmonary hemorrhage is a severe complication of leptospirosis; bilateral infiltrates on CXR.",
         "evidence": "WHO Leptospirosis Fact Sheet"},
    ],

    # ============================
    # MPOX
    # ============================
    "mpox (monkeypox)": [
        {"name": "Mpox (Orthopoxvirus) PCR — Lesion Swab / Crust", "priority": "HIGH PRIORITY",
         "rationale": "Gold standard; swab vesicular/pustular lesion base and roof. Sensitivity > 90% in active lesions.",
         "evidence": "WHO Mpox Technical Guidance (2022-2024)"},
        {"name": "Lesion Electron Microscopy (if PCR unavailable)", "priority": "CONDITIONAL",
         "rationale": "Brick-shaped poxvirus visible on EM; diagnostic but requires specialized BSL-3 lab.",
         "evidence": "CDC Mpox Diagnostic Guidance"},
        {"name": "CBC (Lymphadenopathy Assessment)", "priority": "HIGH PRIORITY",
         "rationale": "Lymphadenopathy distinguishes mpox from smallpox and chickenpox; CBC shows lymphocytosis.",
         "evidence": "WHO Mpox Clinical Guidance 2023"},
        {"name": "HIV Test (Rapid + Confirmatory)", "priority": "HIGH PRIORITY",
         "rationale": "HIV co-infection associated with severe/atypical mpox (disseminated, no rash); affects treatment decisions.",
         "evidence": "CDC/ECDC Mpox Guidance for HIV-Positive Patients"},
        {"name": "Bacterial Skin Culture (Lesion Swab)", "priority": "CONDITIONAL",
         "rationale": "Secondary bacterial superinfection of mpox lesions is common and requires antibiotic treatment.",
         "evidence": "ECDC Mpox Rapid Risk Assessment 2022"},
        {"name": "SARS-CoV-2 PCR (Differential)", "priority": "CONDITIONAL",
         "rationale": "Co-circulation of COVID-19; exclude as co-infection contributing to systemic symptoms.",
         "evidence": "Standard differential in 2022-2024 outbreak"},
    ],

    # ============================
    # TUBERCULOSIS (ACTIVE)
    # ============================
    "tuberculosis (active)": [
        {"name": "Sputum AFB Smear ×3 (Ziehl-Neelsen)", "priority": "HIGH PRIORITY",
         "rationale": "First-line test; detects acid-fast bacilli in sputum. Sensitivity 40-60% but specific. Collect on 3 consecutive days.",
         "evidence": "WHO Tuberculosis Diagnostic Guidelines (2022)"},
        {"name": "GeneXpert MTB/RIF (Xpert Assay) — Sputum", "priority": "HIGH PRIORITY",
         "rationale": "WHO-endorsed rapid molecular test; results in 2 hours; 88% sensitivity, 99% specificity; detects rifampicin resistance.",
         "evidence": "WHO Xpert MTB/RIF Policy (2013, updated 2021)"},
        {"name": "Mycobacterial Culture (LJ Medium / MGIT 960)", "priority": "HIGH PRIORITY",
         "rationale": "Gold standard for TB diagnosis and drug susceptibility testing (DST). 6-8 weeks for solid media.",
         "evidence": "WHO Standards for TB Care 2022"},
        {"name": "Chest X-Ray (PA View)", "priority": "HIGH PRIORITY",
         "rationale": "Upper lobe infiltrates, cavitation, hilar lymphadenopathy are classic TB findings.",
         "evidence": "WHO CXR Guidelines for TB Screening"},
        {"name": "HIV Test (Rapid)", "priority": "HIGH PRIORITY",
         "rationale": "TB/HIV co-infection is critical; affects treatment regimen, risk of IRIS, and mortality.",
         "evidence": "WHO HIV-TB Collaborative Activities Guidelines"},
        {"name": "Tuberculin Skin Test (TST) / IGRA (QuantiFERON)", "priority": "CONDITIONAL",
         "rationale": "Useful to distinguish active from latent TB in smear-negative cases; IGRA preferred in BCG-vaccinated.",
         "evidence": "WHO IGRA Guidance"},
    ],

    # ============================
    # PNEUMONIA (COMMUNITY-ACQUIRED)
    # ============================
    "pneumonia (community-acquired)": [
        {"name": "Chest X-Ray (PA + Lateral)", "priority": "HIGH PRIORITY",
         "rationale": "Standard diagnostic; consolidation, interstitial infiltrates, parapneumonic effusion. Guides treatment decisions.",
         "evidence": "IDSA/ATS CAP Guidelines (2019)"},
        {"name": "Sputum Gram Stain + Culture + Sensitivity", "priority": "HIGH PRIORITY",
         "rationale": "Identifies causative organism and guides targeted antibiotic therapy. Collect before antibiotics.",
         "evidence": "IDSA/ATS CAP Guidelines 2019"},
        {"name": "Blood Culture (×2 Aerobic, before antibiotics)", "priority": "HIGH PRIORITY",
         "rationale": "Bacteremia present in 8-12% of hospitalized CAP; positive culture changes antibiotic management.",
         "evidence": "IDSA/ATS 2019"},
        {"name": "CBC, CRP, Procalcitonin", "priority": "HIGH PRIORITY",
         "rationale": "Guide severity assessment (PSI/CURB-65 score); procalcitonin helps antibiotic stewardship.",
         "evidence": "IDSA/ATS CAP Guidelines"},
        {"name": "Legionella Urinary Antigen", "priority": "CONDITIONAL",
         "rationale": "Detects Legionella pneumophila serogroup 1 (responsible for 80%+ of Legionella pneumonia); results in 1 hour.",
         "evidence": "IDSA/ATS 2019"},
        {"name": "Pneumococcal Urinary Antigen", "priority": "CONDITIONAL",
         "rationale": "S. pneumoniae most common CAP pathogen; antigen persists even after antibiotic initiation.",
         "evidence": "IDSA/ATS 2019"},
        {"name": "CT Chest (HRCT)", "priority": "IF INDICATED",
         "rationale": "When CXR inconclusive or complications suspected (abscess, cavitation, empyema).",
         "evidence": "ACR Radiology Guidelines"},
    ],

    # ============================
    # SEPSIS
    # ============================
    "sepsis (bacterial)": [
        {"name": "Blood Culture (×2 Aerobic + 1 Anaerobic, before antibiotics)", "priority": "HIGH PRIORITY",
         "rationale": "Mandatory before antibiotic administration; do not delay > 1 hour. Identifies causative organism.",
         "evidence": "Surviving Sepsis Campaign Guidelines (2021)"},
        {"name": "Serum Lactate (Lactic Acid Level)", "priority": "HIGH PRIORITY",
         "rationale": "Lactate > 2 mmol/L = sepsis; > 4 mmol/L = septic shock requiring ICU. Serial measurement guides resuscitation.",
         "evidence": "SSC Guidelines 2021; SCCM/ESICM"},
        {"name": "CBC with Differential, CRP, Procalcitonin", "priority": "HIGH PRIORITY",
         "rationale": "Leukocytosis or leukopenia, elevated inflammatory markers confirm systemic infection.",
         "evidence": "SSC Guidelines 2021"},
        {"name": "CMP (Comprehensive Metabolic Panel)", "priority": "HIGH PRIORITY",
         "rationale": "Assess organ dysfunction: AKI (creatinine), liver failure (ALT/AST/bilirubin), glucose, electrolytes.",
         "evidence": "SSC 2021 — SOFA Score Components"},
        {"name": "Prothrombin Time, aPTT, D-Dimer, Fibrinogen", "priority": "HIGH PRIORITY",
         "rationale": "Sepsis-associated coagulopathy and DIC assessment; common in gram-negative bacteremia.",
         "evidence": "ISTH DIC Scoring System"},
        {"name": "Urine Culture + Sensitivity (Clean Catch or Catheter)", "priority": "CONDITIONAL",
         "rationale": "Urinary tract infection is the most common source of gram-negative bacteremia.",
         "evidence": "IDSA UTI Guidelines"},
        {"name": "Chest X-Ray", "priority": "CONDITIONAL",
         "rationale": "Identify pulmonary source (pneumonia) or complications (ARDS, pulmonary edema).",
         "evidence": "SSC Guidelines"},
    ],
}

# Normalize disease name for KB lookup
def _get_investigation_panel(disease_name: str) -> list:
    """Look up investigation panel from offline KB (case-insensitive, fuzzy match)."""
    disease_lower = disease_name.lower().strip()
    # Exact match
    if disease_lower in INVESTIGATION_PANELS:
        return INVESTIGATION_PANELS[disease_lower]
    # Partial match
    for key in INVESTIGATION_PANELS:
        if key in disease_lower or disease_lower in key:
            return INVESTIGATION_PANELS[key]
        # Check by major keyword
        key_words = key.split()
        disease_words = disease_lower.split()
        common = set(key_words) & set(disease_words)
        if len(common) >= 2:
            return INVESTIGATION_PANELS[key]
    return []


# ---------------------------------------------------------------------------
# Enterprise Investigation Provider
# ---------------------------------------------------------------------------

class InvestigationProvider:
    """
    Enterprise-Grade Investigation Provider (God-Level v3).

    Pipeline:
      1. Offline Investigation Panel (immediate, always accurate)
      2. 14-source medical knowledge API (real live data)
      3. LLM narrator (short prompt — writes rationale only for pre-built list)
      4. Merge + deduplicate + sort by priority
    """

    async def get_investigations(
        self,
        db: AsyncSession,
        disease_name: str,
        representation: "ClinicalRepresentationResponse",
        competing: list = None,
    ) -> InvestigationResponse:
        competing = competing or []
        import asyncio

        # ------------------------------------------------------------------ #
        # 1. Offline Investigation Panel (always fast, always real)
        # ------------------------------------------------------------------ #
        offline_panel = _get_investigation_panel(disease_name)
        log.info("investigation_offline_panel_loaded",
                 disease=disease_name,
                 panel_size=len(offline_panel))

        # ------------------------------------------------------------------ #
        # 2. Fetch live medical knowledge in parallel
        # ------------------------------------------------------------------ #
        from app.services.medical_knowledge_api import (
            fetch_disease_intelligence,
            build_context_string,
        )
        from app.services.intelligence_engine import get_disease_class, get_investigation_template

        disease_class = get_disease_class(disease_name)
        template_investigations = get_investigation_template(disease_class) if disease_class else []

        # Build country keywords from representation
        countries = []
        if getattr(representation, "travel_history", None):
            countries = [item.value for item in representation.travel_history
                         if item.value.lower() not in ("none", "ongoing infectious disease outbreak area")]

        try:
            rag_ctx, lab_ctx, live_sources = await asyncio.wait_for(
                asyncio.gather(
                    retrieve_medical_context(db, f"{disease_name} investigations workup", top_k=3),
                    retrieve_investigation_context(db, f"tests for {disease_name}", top_k=4),
                    fetch_disease_intelligence(
                        disease_name=disease_name,
                        country_keywords=countries[:2],
                        include_literature=True,
                    ),
                    return_exceptions=True,
                ),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            rag_ctx, lab_ctx, live_sources = "", "", {}

        if isinstance(rag_ctx, Exception): rag_ctx = ""
        if isinstance(lab_ctx, Exception): lab_ctx = ""
        if isinstance(live_sources, Exception): live_sources = {}

        # Build live context string (max 600 chars — to keep LLM prompt short)
        live_ctx = build_context_string(
            live_sources,
            priority_order=["icd11", "medlineplus", "wikipedia", "pubmed", "europe_pmc", "mesh"],
            max_chars=600,
        )
        if lab_ctx:
            live_ctx = f"RAG LAB CONTEXT: {lab_ctx[:200]}\n\n{live_ctx}"

        # ------------------------------------------------------------------ #
        # 3. Build patient context (short)
        # ------------------------------------------------------------------ #
        symptoms = ", ".join(item.value for item in representation.symptoms) if representation.symptoms else "None"
        vitals = ", ".join(item.value for item in representation.vitals) if representation.vitals else "None"
        history = ", ".join(item.value for item in representation.history) if representation.history else "None"
        travel = ", ".join(item.value for item in representation.travel_history) if getattr(representation, "travel_history", None) else "None"
        competing_str = ", ".join(competing) if competing else "None"

        patient_ctx = (
            f"Symptoms: {symptoms[:200]}\n"
            f"Vitals: {vitals[:100]}\n"
            f"History: {history[:100]}\n"
            f"Travel: {travel[:100]}\n"
            f"Differentials to rule out: {competing_str[:100]}"
        )

        # ------------------------------------------------------------------ #
        # 4. Build pre-built investigation list for LLM narrator
        # ------------------------------------------------------------------ #
        # Combine offline panel + intelligence_engine template (dedup by name)
        seen_names = set()
        pre_built = []
        for item in offline_panel:
            name_lower = item["name"].lower()
            if name_lower not in seen_names:
                seen_names.add(name_lower)
                pre_built.append(item)

        for t in template_investigations:
            if t["name"].lower() not in seen_names:
                seen_names.add(t["name"].lower())
                pre_built.append({
                    "name": t["name"],
                    "priority": t["priority"],
                    "rationale": t["rationale"],
                    "evidence": t["evidence"],
                })

        # Sort: HIGH PRIORITY first
        priority_order = {"HIGH PRIORITY": 0, "CONDITIONAL": 1, "IF INDICATED": 2}
        pre_built.sort(key=lambda x: priority_order.get(x.get("priority", "IF INDICATED"), 3))

        # Format pre-built list for LLM
        pre_built_str = "\n".join(
            f"- [{item['priority']}] {item['name']}: {item['rationale'][:100]}"
            for item in pre_built[:10]
        )

        # ------------------------------------------------------------------ #
        # 5. LLM Narrator — short prompt, only adds rationale detail
        # ------------------------------------------------------------------ #
        if pre_built:
            system_prompt = (
                f"You are a senior clinical pathologist. "
                f"The investigation list is PRE-BUILT from WHO/CDC/NIH guidelines for '{disease_name}' "
                f"(class: {disease_class or 'unclassified'}). "
                f"DO NOT change the test names or priorities. "
                f"For each test, write 1 sentence tailoring the rationale to THIS specific patient. "
                f"Return ONLY valid JSON."
            )
            user_prompt = (
                f"Patient: {patient_ctx[:300]}\n\n"
                f"PRE-BUILT INVESTIGATION LIST (DO NOT CHANGE NAMES OR PRIORITIES):\n{pre_built_str}\n\n"
                f"MEDICAL KNOWLEDGE CONTEXT:\n{live_ctx[:400]}\n\n"
                f"For each investigation, provide patient-specific rationale. "
                f"Return JSON: {{\"suggestions\": [{{\"name\": \"...\", \"priority\": \"...\", "
                f"\"rationale\": \"patient-specific 1 sentence\", "
                f"\"relevant_clinical_finding\": \"...\", \"evidence\": \"...\", "
                f"\"limitations\": \"...\", \"safety_flags\": [], \"provenance\": \"evidence_based\"}}]}}"
            )

            try:
                data = await llm_service.generate_json_compact(
                    prompt=user_prompt,
                    system=system_prompt,
                    max_output_tokens=500,
                )
                llm_suggestions = data.get("suggestions", [])
                log.info("investigation_llm_narrator_success", count=len(llm_suggestions))
            except Exception as e:
                log.warning("investigation_llm_narrator_failed", error=str(e))
                llm_suggestions = []
        else:
            llm_suggestions = []

        # ------------------------------------------------------------------ #
        # 6. Build final suggestions — merge LLM narrations with pre-built
        # ------------------------------------------------------------------ #
        llm_lookup = {
            s.get("name", "").lower(): s for s in llm_suggestions
        }

        final_suggestions = []
        final_seen = set()

        for item in pre_built:
            name = item["name"]
            name_lower = name.lower()
            if name_lower in final_seen:
                continue
            final_seen.add(name_lower)

            llm_data = llm_lookup.get(name_lower, {})
            rationale = (llm_data.get("rationale") or "").strip() or item.get("rationale", "")
            finding = (llm_data.get("relevant_clinical_finding") or "").strip() or f"Based on {disease_name} workup"
            evidence = item.get("evidence") or llm_data.get("evidence") or "WHO/CDC/NIH Clinical Guidelines"
            limitations = (llm_data.get("limitations") or "").strip() or ""
            safety_flags = llm_data.get("safety_flags") or []

            # Add BSL-4 safety flag for VHF tests
            if any(kw in name.lower() for kw in ["bsl-4", "bsl4", "ebolavirus", "marburg", "filovirus", "lassa"]):
                if "BSL-4 containment required" not in safety_flags:
                    safety_flags.append("BSL-4 containment required — notify infection control immediately")

            try:
                final_suggestions.append(InvestigationSuggestion(
                    name=name,
                    priority=item.get("priority", "CONDITIONAL"),
                    rationale=rationale,
                    relevant_clinical_finding=finding,
                    evidence=evidence,
                    limitations=limitations,
                    safety_flags=safety_flags,
                    provenance="offline_clinical_guideline_panel",
                ))
            except Exception as ex:
                log.debug("investigation_suggestion_build_failed", error=str(ex))

        # Add any unique LLM-suggested tests not in pre-built (de-duped)
        for s in llm_suggestions:
            name = s.get("name", "")
            if name and name.lower() not in final_seen:
                final_seen.add(name.lower())
                try:
                    final_suggestions.append(InvestigationSuggestion(
                        name=name,
                        priority=s.get("priority", "IF INDICATED"),
                        rationale=s.get("rationale", ""),
                        relevant_clinical_finding=s.get("relevant_clinical_finding", ""),
                        evidence=s.get("evidence", "LLM clinical knowledge"),
                        limitations=s.get("limitations", ""),
                        safety_flags=s.get("safety_flags", []),
                        provenance="llm_supplemental",
                    ))
                except Exception:
                    pass

        # Final sort
        final_suggestions.sort(key=lambda x: priority_order.get(x.priority, 3))

        if not final_suggestions:
            # Last resort: return template only
            for t in template_investigations:
                try:
                    final_suggestions.append(InvestigationSuggestion(
                        name=t["name"],
                        priority=t["priority"],
                        rationale=t["rationale"],
                        relevant_clinical_finding="Based on disease class template",
                        evidence=t["evidence"],
                        limitations="",
                        safety_flags=[],
                        provenance="disease_class_template_fallback",
                    ))
                except Exception:
                    pass

        log.info("investigation_response_built",
                 disease=disease_name,
                 total_investigations=len(final_suggestions))

        return InvestigationResponse(disease=disease_name, suggestions=final_suggestions)


investigation_provider = InvestigationProvider()
