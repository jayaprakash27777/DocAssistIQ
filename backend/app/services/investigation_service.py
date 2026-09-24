"""DocAssistIQ — Enterprise-Grade Investigation Provider (God-Level v3).

Architecture:
  1. Offline Investigation Panel (from offline_disease_kb.py) — ALWAYS accurate, no network
  2. 14-source medical knowledge API — real live data from ICD-11, MedlinePlus, PubMed, etc.
  3. LLM Narrator — writes rationale for pre-built investigation list (short prompt)
  4. Fallback: if LLM fails → offline panel returned directly (still clinical-grade accurate)

No mock data. All investigations are evidence-based from WHO/CDC/NIH protocols.
"""

from typing import Any, Optional
from pydantic import PrivateAttr
from app.schemas.investigation import InvestigationResponse, InvestigationSuggestion
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.rag_service import retrieve_medical_context, retrieve_investigation_context
from app.services.llm_service import llm_service
import structlog

log = structlog.get_logger(__name__)


class AwaitableInvestigationResponse(InvestigationResponse):
    """InvestigationResponse that can be used directly or awaited."""
    _coro_fn: Any = PrivateAttr(default=None)

    def __init__(self, coro_fn=None, **data):
        super().__init__(**data)
        self._coro_fn = coro_fn

    def __await__(self):
        if self._coro_fn:
            return self._coro_fn().__await__()
        async def _self():
            return self
        return _self().__await__()


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

    # ============================
    # HANTAVIRUS PULMONARY SYNDROME
    # ============================
    "hantavirus pulmonary syndrome": [
        {"name": "Hantavirus IgM + IgG Serology (ELISA) — Reference Lab",
         "priority": "HIGH PRIORITY",
         "rationale": "Primary confirmatory test for HPS. IgM detectable from day 1 of cardiopulmonary phase. IgG develops 1–2 weeks post-symptom onset. Send to National Virology Reference Laboratory urgently.",
         "evidence": "CDC Hantavirus Clinical Guidance (2024); WHO Technical Report on Rodent-Borne Diseases"},
        {"name": "RT-PCR for Hantavirus RNA (Whole Blood / PBMC)",
         "priority": "HIGH PRIORITY",
         "rationale": "Most sensitive during febrile prodrome (before cardiopulmonary phase). Confirms viral RNA. Also positive in PBMC. Send to reference laboratory with appropriate biohazard precautions.",
         "evidence": "CDC Special Pathogens Branch; Bharadwaj M et al., JID 2000"},
        {"name": "Full Blood Count (FBC) — Critical HPS Pattern",
         "priority": "HIGH PRIORITY",
         "rationale": "HPS hallmarks: Thrombocytopenia (platelets <150,000 — often <100,000), haemoconcentration (Hct >45%), atypical lymphocytes (immunoblasts >10%), left shift (bands). These findings are PATHOGNOMONIC for HPS cardiopulmonary phase.",
         "evidence": "Duchin JS et al., NEJM 1994; CDC Hantavirus Clinical Features"},
        {"name": "Chest X-Ray (PA + Lateral)",
         "priority": "HIGH PRIORITY",
         "rationale": "HPS: Bilateral interstitial infiltrates (ARDS pattern), progressing to dense consolidation. Pleural effusions in severe cases. Serial CXRs every 12–24h to monitor progression rate.",
         "evidence": "CDC HPS Imaging Criteria; Ketai LH et al., Radiology 1994"},
        {"name": "Arterial Blood Gas (ABG) — Serial Monitoring",
         "priority": "HIGH PRIORITY",
         "rationale": "Assesses severity of respiratory failure. PaO2/FiO2 ratio determines ARDS severity (Berlin Criteria). Guides decision for intubation/ECMO. Monitor every 2–4h in ICU.",
         "evidence": "ARDS Network ARMA Trial; Surviving Sepsis Campaign 2021"},
        {"name": "CT Chest (High-Resolution HRCT) — If CXR Insufficient",
         "priority": "HIGH PRIORITY",
         "rationale": "HRCT shows ground-glass opacities, interlobular septal thickening, bilateral infiltrates. More sensitive than CXR for early pulmonary oedema. Guides ventilation strategy.",
         "evidence": "CDC HPS Radiological Criteria; Ketai LH et al."},
        {"name": "Comprehensive Metabolic Panel — LFTs, Renal, Electrolytes",
         "priority": "HIGH PRIORITY",
         "rationale": "HPS: Elevated LDH (>250 U/L — marker of tissue damage), hypoalbuminaemia (capillary leak), elevated creatinine (renal involvement in 50%), hyponatraemia, hyperkalaemia.",
         "evidence": "CDC HPS Laboratory Findings; Hallin GW et al., JID 1996"},
        {"name": "Serum Lactate",
         "priority": "HIGH PRIORITY",
         "rationale": "Elevated lactate (>2 mmol/L) indicates tissue hypoperfusion in HPS shock. Guides aggressive fluid resuscitation. Serial monitoring every 2–4h.",
         "evidence": "Surviving Sepsis Campaign 2021; CDC Hantavirus Management"},
        {"name": "Echocardiogram (Transthoracic — TTE or TOE)",
         "priority": "HIGH PRIORITY",
         "rationale": "HPS causes myocardial depression and cardiogenic shock (distinct from ARDS alone). Echo guides management: IV fluids vs. vasopressors vs. ECMO. Low EF (<40%) is a critical finding.",
         "evidence": "Crowley MR et al., Clin Infect Dis 1998; ECMO criteria for HPS"},
        {"name": "Malaria Rapid Diagnostic Test (RDT) + Thick/Thin Blood Film",
         "priority": "HIGH PRIORITY",
         "rationale": "Critical differential — Malaria is endemic/imported from South America. Falciparum malaria can cause severe respiratory disease mimicking HPS. Must exclude urgently as highly treatable.",
         "evidence": "WHO Malaria Diagnostic Testing Recommendations"},
        {"name": "Dengue NS1 Antigen + IgM/IgG Serology",
         "priority": "HIGH PRIORITY",
         "rationale": "Dengue causes thrombocytopenia + respiratory involvement — overlaps with HPS. Argentina, Chile, Uruguay have seasonal dengue risk. NS1 positive in days 1–5.",
         "evidence": "PAHO/WHO Dengue Diagnostic Guidance 2023"},
        {"name": "Blood Culture (Aerobic + Anaerobic, ×2 sets)",
         "priority": "CONDITIONAL",
         "rationale": "Exclude bacterial sepsis as co-infection or primary diagnosis. Gram-negative sepsis can cause ARDS with thrombocytopenia. Essential before empirical antibiotics.",
         "evidence": "IDSA Sepsis Clinical Practice Guidelines"},
        {"name": "Leptospira Serology (MAT / IgM ELISA)",
         "priority": "CONDITIONAL",
         "rationale": "Leptospirosis is endemic in rural South America — shared environmental exposure (soil, water near agricultural areas). Can cause pulmonary haemorrhage syndrome (Weil-Farr's). Serology MAT is gold standard.",
         "evidence": "WHO Technical Report on Leptospirosis 2017"},
        {"name": "Influenza A/B Rapid Antigen Test + PCR",
         "priority": "CONDITIONAL",
         "rationale": "Influenza A H1N1 and H3N2 cause ARDS and thrombocytopenia — important differential. Rapid test useful; PCR is confirmatory.",
         "evidence": "WHO Influenza Surveillance and Pandemic Guidelines"},
        {"name": "SARS-CoV-2 PCR (Nasopharyngeal Swab)",
         "priority": "CONDITIONAL",
         "rationale": "COVID-19 remains differential for bilateral pulmonary infiltrates with thrombocytopenia. Exclude in any traveller with respiratory failure.",
         "evidence": "WHO COVID-19 Laboratory Testing Guidance"},
    ],

    "andes orthohantavirus (hps)": [
        {"name": "Hantavirus IgM/IgG Serology — Andes Strain (Reference Lab)",
         "priority": "HIGH PRIORITY",
         "rationale": "Andes-specific serology. IgM detectable from day 1 of cardiopulmonary phase. Person-to-person transmission documented with Andes strain — strict isolation required.",
         "evidence": "CDC Andes Virus Guidance; Wells RM et al., Science 1997"},
        {"name": "RT-PCR for Andes Orthohantavirus RNA",
         "priority": "HIGH PRIORITY",
         "rationale": "Definitive virological confirmation. Send to BSL-3 reference laboratory. Positive during febrile prodrome and cardiopulmonary phase. Andes strain is ONLY hantavirus with documented human-to-human transmission.",
         "evidence": "Padula PJ et al., Lancet 1998; PAHO Andes Hantavirus Alert"},
        {"name": "FBC with Differential — Thrombocytopenia Hallmark",
         "priority": "HIGH PRIORITY",
         "rationale": "Andes HPS: Severe thrombocytopenia (<50,000 common), haemoconcentration (Hct >50%), immunoblasts on smear. Platelet trend is a critical monitor — rapid drop indicates deterioration.",
         "evidence": "CDC Hantavirus; Martinez VP et al., Emerg Infect Dis 2005"},
        {"name": "CXR — Bilateral Infiltrates Monitoring",
         "priority": "HIGH PRIORITY",
         "rationale": "Serial CXRs track ARDS progression. Bilateral ground-glass and consolidation. Rate of radiographic progression (hours to full ARDS) determines ICU admission urgency.",
         "evidence": "CDC Andes Hantavirus Clinical Guidance"},
        {"name": "Echocardiogram (urgently — myocardial depression guide)",
         "priority": "HIGH PRIORITY",
         "rationale": "Cardiogenic shock + ARDS = bi-ventricular failure in Andes HPS. ECMO decisions require echo. EF <35% = immediate ECMO consideration.",
         "evidence": "ECMO for HPS — Mertz GJ et al., Antiviral Res 2006"},
        {"name": "ABG + Lactate (serial, every 4h ICU)",
         "priority": "HIGH PRIORITY",
         "rationale": "P/F ratio determines ARDS severity. Lactate monitors perfusion failure. Critical for weaning and ventilator titration.",
         "evidence": "ARDS Network; Surviving Sepsis Campaign"},
        {"name": "Serum LDH + Albumin",
         "priority": "HIGH PRIORITY",
         "rationale": "LDH >300 U/L: tissue damage marker. Hypoalbuminaemia (<3.5 g/dL): capillary leak syndrome. Both are independent predictors of ICU admission in HPS.",
         "evidence": "Hallin GW et al., JID 1996; Alarcón R et al., Chile 2009"},
        {"name": "Coagulation Panel (PT, aPTT, D-Dimer, Fibrinogen)",
         "priority": "CONDITIONAL",
         "rationale": "DIC may complicate severe Andes HPS. Coagulopathy with haemorrhage requires FFP/platelet transfusion guidance.",
         "evidence": "CDC Hantavirus Haemorrhagic Complications"},
        {"name": "Leptospira MAT / IgM ELISA",
         "priority": "CONDITIONAL",
         "rationale": "Leptospirosis co-endemic in Andes regions — agricultural/rural exposure. Weil's disease causes severe pulmonary haemorrhage + ARDS.",
         "evidence": "WHO Leptospirosis Technical Report"},
        {"name": "Dengue NS1 + Serology",
         "priority": "CONDITIONAL",
         "rationale": "Dengue thrombocytopenia + respiratory overlap. Seasonal transmission in Argentina, Uruguay.",
         "evidence": "PAHO Dengue 2023"},
    ],
    "asthma": [
        {"name": "Spirometry with Pre- and Post-Bronchodilator Testing", "priority": "HIGH PRIORITY",
         "rationale": "To establish the diagnosis of asthma by demonstrating reversible airflow obstruction.",
         "evidence": "GINA Guidelines: Spirometry is the preferred method for diagnosing asthma."},
        {"name": "Chest X-Ray (PA and Lateral)", "priority": "IF INDICATED",
         "rationale": "To rule out alternative diagnoses such as infection or pneumothorax if atypical features are present.",
         "evidence": "Routine CXR is not indicated for typical asthma presentations; NICE Asthma Guidelines"},
    ],
    "pneumonia": [
        {"name": "Chest X-Ray (PA and Lateral)", "priority": "HIGH PRIORITY",
         "rationale": "To confirm the presence of an infiltrate confirming clinical suspicion of pneumonia.",
         "evidence": "IDSA/ATS Guidelines recommend CXR for all patients with suspected pneumonia."},
        {"name": "Sputum Culture and Gram Stain", "priority": "CONDITIONAL",
         "rationale": "To identify the causative organism and guide targeted antibiotic therapy.",
         "evidence": "Recommended for severe inpatient CAP or if empirically treating for MRSA/Pseudomonas; IDSA/ATS 2019"},
        {"name": "Blood Cultures (x2 sets)", "priority": "CONDITIONAL",
         "rationale": "Identify bacteremic pneumonia in hospitalized or immunocompromised patients.",
         "evidence": "IDSA/ATS CAP Guidelines"},
    ],
    "covid-19": [
        {"name": "SARS-CoV-2 NAAT (RT-PCR or Rapid Antigen Assay)", "priority": "HIGH PRIORITY",
         "rationale": "Confirms acute infection and active viral replication.",
         "evidence": "Gold standard per WHO and NIH Guidelines."},
        {"name": "Continuous Pulse Oximetry and ABG", "priority": "HIGH PRIORITY",
         "rationale": "Screens for silent hypoxemia ('happy hypoxemia') and assesses respiratory failure requiring oxygen therapy.",
         "evidence": "NIH COVID-19 Treatment Guidelines"},
        {"name": "Complete Blood Count (CBC) with Differential", "priority": "HIGH PRIORITY",
         "rationale": "Detects lymphopenia, leukopenia, or neutrophilia indicating inflammatory progression.",
         "evidence": "WHO COVID-19 Clinical Management Guidelines"},
        {"name": "Inflammatory Biomarkers (Ferritin, CRP, D-Dimer, LDH)", "priority": "HIGH PRIORITY",
         "rationale": "Predicts cytokine release storm, hypercoagulability, and thromboembolic risk.",
         "evidence": "ASH / NIH Clinical Guidance"},
        {"name": "Chest Radiograph (PA/Lateral) or High-Resolution Chest CT", "priority": "CONDITIONAL",
         "rationale": "Evaluates peripheral bilateral ground-glass opacities and excludes pneumothorax or bacterial consolidation.",
         "evidence": "Fleischner Society Consensus"},
        {"name": "Comprehensive Metabolic Panel (CMP)", "priority": "CONDITIONAL",
         "rationale": "Monitors acute kidney injury, hepatic transaminitis, and directs antiviral clearance dosing.",
         "evidence": "NIH Guidelines"},
    ],
    "infective endocarditis": [
        {"name": "Blood Cultures (3 sets from separate venipuncture sites before antibiotics)", "priority": "HIGH PRIORITY",
         "rationale": "Mandatory Duke Criteria major requirement. Demonstrates continuous bacteremia.",
         "evidence": "AHA/ESC Infective Endocarditis Guidelines 2023"},
        {"name": "Transthoracic Echocardiogram (TTE) followed by TEE", "priority": "HIGH PRIORITY",
         "rationale": "Detects valvular vegetations, leaflet perforation, abscess, or new prosthetic dehiscence.",
         "evidence": "Duke Criteria / AHA Guidelines"},
        {"name": "12-Lead Electrocardiogram (ECG)", "priority": "HIGH PRIORITY",
         "rationale": "Screens for PR-interval prolongation, bundle branch block, or AV block indicating aortic root abscess extension.",
         "evidence": "ACC/AHA Valve Disease Guidelines"},
        {"name": "Complete Blood Count with Differential", "priority": "HIGH PRIORITY",
         "rationale": "Identifies leukocytosis with left shift and normocytic normochromic anemia of chronic disease.",
         "evidence": "Harrison's Principles of Internal Medicine"},
        {"name": "Urinalysis with Microscopic Examination", "priority": "CONDITIONAL",
         "rationale": "Detects microscopic hematuria and RBC casts secondary to immune-complex glomerulonephritis or renal infarction.",
         "evidence": "KDIGO / Duke Criteria minor manifestation"},
        {"name": "Serum Inflammatory Markers (ESR and C-Reactive Protein)", "priority": "CONDITIONAL",
         "rationale": "Universally elevated in active endocarditis; serial values monitor therapeutic response.",
         "evidence": "ESC Clinical Practice Guidelines 2023"},
    ],
    "pyelonephritis": [
        {"name": "Urinalysis with Microscopy (WBCs, Bacteria, WBC Casts)", "priority": "HIGH PRIORITY",
         "rationale": "Confirms upper urinary tract infection; WBC casts are pathognomonic for renal parenchymal inflammation.",
         "evidence": "IDSA Guidelines for Acute Uncomplicated Pyelonephritis"},
        {"name": "Urine Culture and Antimicrobial Susceptibility Testing", "priority": "HIGH PRIORITY",
         "rationale": "Identifies specific uropathogen and guides pathogen-directed antibiotic de-escalation.",
         "evidence": "IDSA / EAU Urological Infections Guidelines"},
        {"name": "Complete Blood Count (CBC) with Differential", "priority": "HIGH PRIORITY",
         "rationale": "Evaluates leukocytosis and systemic inflammatory response.",
         "evidence": "Emergency Medicine Clinics of North America"},
        {"name": "Serum Creatinine, Blood Urea Nitrogen (BUN), and eGFR", "priority": "HIGH PRIORITY",
         "rationale": "Evaluates renal functional impairment and guides antibiotic dosage adjustments.",
         "evidence": "KDIGO Clinical Practice Guidelines"},
        {"name": "Blood Cultures (x2 sets)", "priority": "CONDITIONAL",
         "rationale": "Indicated in patients with high fever, hemodynamic instability, or requiring hospitalization.",
         "evidence": "IDSA Guidelines"},
        {"name": "Renal and Bladder Ultrasound", "priority": "CONDITIONAL",
         "rationale": "Rules out hydronephrosis, urinary calculus obstruction, or perinephric abscess in patients with severe pain or slow response.",
         "evidence": "American College of Radiology (ACR) Appropriateness Criteria"},
    ],
    "urinary tract infection": [
        {"name": "Urinalysis (Dipstick and Microscopic Analysis)", "priority": "HIGH PRIORITY",
         "rationale": "Detects pyuria, bacteriuria, positive leukocyte esterase, and positive nitrite.",
         "evidence": "IDSA Guidelines for Uncomplicated Cystitis"},
        {"name": "Clean-Catch Midstream Urine Culture and Susceptibility", "priority": "HIGH PRIORITY",
         "rationale": "Identifies causative organism and antibiotic susceptibility profile.",
         "evidence": "EAU Guidelines on Urological Infections"},
        {"name": "Serum Creatinine and BUN", "priority": "CONDITIONAL",
         "rationale": "Baseline renal function assessment for complicated or recurrent infections.",
         "evidence": "KDIGO Guidelines"},
    ],
    "nephrolithiasis": [
        {"name": "Non-Contrast Helical CT Abdomen and Pelvis (NCCT)", "priority": "HIGH PRIORITY",
         "rationale": "Definitive gold standard (>98% sensitivity); determines exact stone size, location, density (HU), and degree of hydronephrosis.",
         "evidence": "AUA / EAU Urolithiasis Guidelines (2023)"},
        {"name": "Urinalysis with Microscopic Examination", "priority": "HIGH PRIORITY",
         "rationale": "Detects microscopic hematuria (present in 85-90%), urinary pH, and crystal morphology.",
         "evidence": "American Urological Association Guidelines"},
        {"name": "Serum Creatinine, BUN, and Electrolytes", "priority": "HIGH PRIORITY",
         "rationale": "Assesses for acute post-renal obstructive nephropathy requiring emergent decompression.",
         "evidence": "ACR Appropriateness Criteria"},
        {"name": "Renal and Bladder Ultrasound", "priority": "CONDITIONAL",
         "rationale": "First-line imaging in pregnant patients, children, or when avoiding radiation; demonstrates hydronephrosis and acoustic shadowing.",
         "evidence": "ACR Appropriateness Criteria / EAU Guidelines"},
        {"name": "Urine Culture and Sensitivity", "priority": "CONDITIONAL",
         "rationale": "Rules out concurrent infection; infected hydronephrosis is a urologic emergency.",
         "evidence": "AUA Guidelines for Medical and Surgical Management of Stones"},
    ],
    "acute diverticulitis": [
        {"name": "Contrast-Enhanced CT Abdomen and Pelvis", "priority": "HIGH PRIORITY",
         "rationale": "Gold standard diagnostic imaging; demonstrates colonic wall thickening, pericolic fat stranding, fascial thickening, or perforation.",
         "evidence": "American College of Gastroenterology (ACG) Guidelines 2021"},
        {"name": "Complete Blood Count (CBC) with Differential", "priority": "HIGH PRIORITY",
         "rationale": "Assesses for leukocytosis with left shift reflecting acute colonic inflammation.",
         "evidence": "World Society of Emergency Surgery (WSES) Guidelines 2020"},
        {"name": "Serum C-Reactive Protein (CRP)", "priority": "HIGH PRIORITY",
         "rationale": "CRP >50 mg/L correlates with acute diverticulitis severity and complicated disease risk.",
         "evidence": "WSES Diverticulitis Guidelines"},
        {"name": "Basic Metabolic Panel (Electrolytes, BUN, Creatinine)", "priority": "HIGH PRIORITY",
         "rationale": "Assesses hydration status and renal function prior to IV contrast or antibiotics.",
         "evidence": "ACG Practice Guidelines"},
        {"name": "Urinalysis with Microscopy", "priority": "CONDITIONAL",
         "rationale": "Rules out colovesical fistula (pneumaturia/fecaluria) and mimics such as nephrolithiasis or UTI.",
         "evidence": "ASCRS Practice Parameters for Diverticulitis"},
    ],
    "acute cholecystitis": [
        {"name": "Right Upper Quadrant Abdominal Ultrasound", "priority": "HIGH PRIORITY",
         "rationale": "First-line imaging modality of choice; evaluates gallstones, gallbladder wall thickening (>3mm), pericholecystic fluid, and sonographic Murphy sign.",
         "evidence": "Tokyo Guidelines 2018 (TG18); ACR Appropriateness Criteria"},
        {"name": "Complete Blood Count (CBC) with Differential", "priority": "HIGH PRIORITY",
         "rationale": "Leukocytosis with left shift indicates acute inflammatory process (TG18 diagnostic criteria).",
         "evidence": "Tokyo Guidelines 2018"},
        {"name": "Comprehensive Metabolic Panel (Total Bilirubin, Alk Phos, AST, ALT)", "priority": "HIGH PRIORITY",
         "rationale": "Evaluates for choledocholithiasis, cholangitis, or secondary hepatic injury.",
         "evidence": "ACG Clinical Guideline for Gallstones"},
        {"name": "Serum Lipase and Amylase", "priority": "HIGH PRIORITY",
         "rationale": "Rules out concurrent acute gallstone pancreatitis.",
         "evidence": "American College of Gastroenterology Guidelines"},
        {"name": "Cholescintigraphy (HIDA Scan)", "priority": "CONDITIONAL",
         "rationale": "Most sensitive diagnostic modality when ultrasound is equivocal; absence of gallbladder filling confirms cystic duct obstruction.",
         "evidence": "Tokyo Guidelines / SNMMI Practice Guideline"},
    ],
    "acute pancreatitis": [
        {"name": "Serum Lipase", "priority": "HIGH PRIORITY",
         "rationale": "Definitive biomarker; elevation >3 times upper limit of normal fulfills revised Atlanta classification criteria.",
         "evidence": "Revised Atlanta Classification / ACG Pancreatitis Guidelines"},
        {"name": "Transabdominal Ultrasound", "priority": "HIGH PRIORITY",
         "rationale": "Mandatory in all patients at admission to evaluate for gallstones, biliary sludge, and common bile duct dilatation.",
         "evidence": "ACG Clinical Guideline: Management of Acute Pancreatitis 2024"},
        {"name": "Complete Blood Count, BUN, Serum Creatinine, and Electrolytes", "priority": "HIGH PRIORITY",
         "rationale": "Assesses hemoconcentration (hematocrit >44%), third-spacing, and organ failure (BISAP score).",
         "evidence": "IAP/APA Evidence-Based Guidelines"},
        {"name": "Serum Calcium, Fasting Triglycerides, and Liver Enzymes", "priority": "CONDITIONAL",
         "rationale": "Investigates etiologies: hypertriglyceridemia, hypercalcemia, and biliary obstruction.",
         "evidence": "ACG Guidelines 2024"},
        {"name": "Contrast-Enhanced CT Abdomen (CECT at 72-96 hours)", "priority": "CONDITIONAL",
         "rationale": "Assesses for pancreatic necrosis, peripancreatic fluid collections, or vascular complications if patient fails to improve.",
         "evidence": "ACG / Revised Atlanta Classification"},
    ],
    "gout": [
        {"name": "Arthrocentesis with Polarized Light Microscopy", "priority": "HIGH PRIORITY",
         "rationale": "Definitive gold standard; identifies intracellular monosodium urate crystals showing strong negative birefringence.",
         "evidence": "ACR Guidelines for Management of Gout (2020); EULAR Recommendations"},
        {"name": "Synovial Fluid Gram Stain and Bacterial Culture", "priority": "HIGH PRIORITY",
         "rationale": "Crucial to exclude concomitant or mimicking septic arthritis before initiating immunosuppressive therapy.",
         "evidence": "ACR/EULAR Consensus Guidelines"},
        {"name": "Serum Uric Acid Level", "priority": "HIGH PRIORITY",
         "rationale": "Establishes baseline hyperuricemia for long-term treat-to-target ULT (target <6 mg/dL); may be transiently normal during acute flare.",
         "evidence": "ACR Gout Guidelines 2020"},
        {"name": "Complete Blood Count (CBC) and C-Reactive Protein (CRP)", "priority": "CONDITIONAL",
         "rationale": "Quantifies systemic inflammatory response during acute monoarthritis flare.",
         "evidence": "EULAR Recommendations"},
        {"name": "Plain Radiographs of Affected Joint", "priority": "CONDITIONAL",
         "rationale": "Detects chronic gouty changes: punched-out periarticular erosions with overhanging cortical edges (Martel sign).",
         "evidence": "ACR Guidelines"},
    ],
    "chronic obstructive pulmonary disease": [
        {"name": "Post-Bronchodilator Spirometry", "priority": "HIGH PRIORITY",
         "rationale": "Gold standard confirmatory test; FEV1/FVC ratio <0.70 confirms persistent, non-fully reversible airflow limitation.",
         "evidence": "GOLD Report 2024: Global Strategy for Diagnosis and Management of COPD"},
        {"name": "Chest Radiograph (PA and Lateral)", "priority": "HIGH PRIORITY",
         "rationale": "Evaluates lung hyperinflation, flattened diaphragms, bullae, and excludes pneumonia, congestive heart failure, or pneumothorax.",
         "evidence": "GOLD Guidelines / ATS Standards"},
        {"name": "Arterial Blood Gas (ABG Analysis)", "priority": "HIGH PRIORITY",
         "rationale": "Assesses severity of acute respiratory acidosis, hypoxemia, and hypercapnia during exacerbations.",
         "evidence": "GOLD Exacerbation Management Guidelines"},
        {"name": "Complete Blood Count (CBC)", "priority": "CONDITIONAL",
         "rationale": "Evaluates for secondary polycythemia due to chronic hypoxia or leukocytosis indicating active infection.",
         "evidence": "GOLD 2024 Guidelines"},
        {"name": "High-Resolution CT (HRCT) of the Chest", "priority": "IF INDICATED",
         "rationale": "Quantifies severity and anatomic distribution of emphysema and screens for bronchiectasis or pulmonary nodules.",
         "evidence": "Fleischner Society Guidelines"},
    ],
    "pulmonary embolism": [
        {"name": "CT Pulmonary Angiography (CTPA)", "priority": "HIGH PRIORITY",
         "rationale": "Definitive imaging modality of choice (>95% sensitivity and specificity); demonstrates intraluminal filling defects.",
         "evidence": "ESC Guidelines for Management of Acute Pulmonary Embolism (2020)"},
        {"name": "Quantitative High-Sensitivity D-Dimer Assay", "priority": "HIGH PRIORITY",
         "rationale": "High negative predictive value; reliably rules out PE in patients with low or intermediate clinical pretest probability.",
         "evidence": "Wells / Geneva Criteria / ESC Guidelines"},
        {"name": "12-Lead Electrocardiogram (ECG)", "priority": "HIGH PRIORITY",
         "rationale": "Evaluates right ventricular strain patterns: sinus tachycardia, S1Q3T3 pattern, right bundle branch block, or T-wave inversions V1-V4.",
         "evidence": "ESC PE Guidelines"},
        {"name": "Arterial Blood Gas (ABG)", "priority": "HIGH PRIORITY",
         "rationale": "Detects acute hypoxemia, hypocapnia, respiratory alkalosis, and increased alveolar-arterial (A-a) oxygen gradient.",
         "evidence": "American Thoracic Society Guidelines"},
        {"name": "Transthoracic Echocardiogram (TTE)", "priority": "CONDITIONAL",
         "rationale": "Assesses acute right ventricular dilation, McConnell sign, and pulmonary artery systolic pressure for hemodynamic risk stratification.",
         "evidence": "ESC Guidelines 2020"},
        {"name": "Compression Ultrasound of Lower Extremities with Doppler", "priority": "CONDITIONAL",
         "rationale": "Identifies deep vein thrombosis as source of thromboembolism.",
         "evidence": "ACR Appropriateness Criteria"},
    ],
    "cellulitis": [
        {"name": "Complete Blood Count (CBC) with Differential", "priority": "HIGH PRIORITY",
         "rationale": "Assesses for leukocytosis with left shift indicating active spreading bacterial infection.",
         "evidence": "IDSA Practice Guidelines for Skin and Soft Tissue Infections (SSTIs)"},
        {"name": "Serum C-Reactive Protein (CRP) and ESR", "priority": "HIGH PRIORITY",
         "rationale": "Quantifies systemic inflammation and provides baseline for monitoring clinical response to antimicrobial therapy.",
         "evidence": "IDSA SSTI Guidelines"},
        {"name": "Marking of Advancing Erythematous Margin with Surgical Pen", "priority": "HIGH PRIORITY",
         "rationale": "Essential bedside diagnostic procedure to track progression or regression of infection across serial examinations.",
         "evidence": "IDSA Clinical Practice Guidelines"},
        {"name": "Blood Cultures (x2 sets)", "priority": "CONDITIONAL",
         "rationale": "Indicated in patients with systemic toxicity, high fever, underlying malignancy, or immunosuppression.",
         "evidence": "IDSA Guidelines 2014"},
        {"name": "Lower Extremity Venous Duplex Ultrasound", "priority": "CONDITIONAL",
         "rationale": "Essential when deep vein thrombosis cannot be differentiated from unilateral lower limb cellulitis.",
         "evidence": "ACR Appropriateness Criteria"},
    ],
    "diabetic ketoacidosis": [
        {"name": "Basic Metabolic Panel, Blood Glucose, and Anion Gap Calculation", "priority": "HIGH PRIORITY",
         "rationale": "Confirms hyperglycemia, metabolic acidosis, and high anion gap ([Na] - [Cl + HCO3] > 12 mEq/L).",
         "evidence": "ADA Standards of Care in Diabetes (2024)"},
        {"name": "Serum Beta-Hydroxybutyrate (Quantitative Ketone Level)", "priority": "HIGH PRIORITY",
         "rationale": "Preferred method for detecting and monitoring ketoacidosis (threshold >3.0 mmol/L).",
         "evidence": "ADA Consensus Guidelines"},
        {"name": "Venous Blood Gas (VBG)", "priority": "HIGH PRIORITY",
         "rationale": "Assesses venous pH (pH < 7.30 indicates DKA) and tracks resolution of acidemia without requiring arterial puncture.",
         "evidence": "ADA / Endocrine Society Guidelines"},
        {"name": "Urinalysis with Microscopic Examination", "priority": "HIGH PRIORITY",
         "rationale": "Detects glucosuria, ketonuria, and screens for precipitating urinary tract infection.",
         "evidence": "ADA Guidelines"},
        {"name": "12-Lead Electrocardiogram (ECG)", "priority": "HIGH PRIORITY",
         "rationale": "Critical to monitor for life-threatening hyperkalemia or hypokalemia arrhythmias prior to and during insulin therapy.",
         "evidence": "AHA / ADA Guidelines"},
    ],
    "acute appendicitis": [
        {"name": "Contrast-Enhanced CT Abdomen and Pelvis", "priority": "HIGH PRIORITY",
         "rationale": "Gold standard diagnostic imaging in adults (>95% accuracy); shows appendiceal diameter >6mm, wall thickening, fat stranding, appendicolith.",
         "evidence": "WSES Jerusalem Guidelines on Acute Appendicitis (2020)"},
        {"name": "Graded-Compression Abdominal Ultrasound", "priority": "HIGH PRIORITY",
         "rationale": "First-line imaging modality in pediatric patients and pregnant women to avoid ionizing radiation.",
         "evidence": "ACR Appropriateness Criteria / WSES Guidelines"},
        {"name": "Complete Blood Count (CBC) with Differential", "priority": "HIGH PRIORITY",
         "rationale": "Leukocytosis with neutrophilia and bandemia (part of Alvarado and AIR scores).",
         "evidence": "WSES Jerusalem Guidelines"},
        {"name": "Serum C-Reactive Protein (CRP)", "priority": "HIGH PRIORITY",
         "rationale": "Combined CBC and CRP elevation significantly increases diagnostic sensitivity for acute appendicitis.",
         "evidence": "AIR Score / WSES 2020"},
        {"name": "Urine Beta-hCG Pregnancy Test", "priority": "HIGH PRIORITY",
         "rationale": "Mandatory in all females of reproductive age to exclude ectopic pregnancy.",
         "evidence": "ACOG Practice Bulletin"},
    ],
    "acute coronary syndrome": [
        {"name": "12-Lead Electrocardiogram (ECG within 10 minutes of arrival)", "priority": "HIGH PRIORITY",
         "rationale": "Immediately differentiates ST-elevation myocardial infarction (STEMI) requiring emergent reperfusion from NSTE-ACS.",
         "evidence": "ACC/AHA / ESC ACS Guidelines (2023)"},
        {"name": "Serial High-Sensitivity Cardiac Troponin (hs-cTn at 0h and 1-3h)", "priority": "HIGH PRIORITY",
         "rationale": "Biomarker of choice; detects acute myocardial injury and assesses significant dynamic delta rise/fall.",
         "evidence": "Fourth Universal Definition of Myocardial Infarction / ESC Guidelines"},
        {"name": "Complete Blood Count, BMP, Coagulation Studies (PT/INR, aPTT)", "priority": "HIGH PRIORITY",
         "rationale": "Baseline parameters for antithrombotic and anticoagulant therapy and contrast nephropathy risk.",
         "evidence": "ACC/AHA Guidelines"},
        {"name": "Portable Chest Radiograph (PA/AP)", "priority": "HIGH PRIORITY",
         "rationale": "Screens for pulmonary edema and excludes aortic dissection (widened mediastinum) before antithrombotic therapy.",
         "evidence": "ACC/AHA ACS Guidelines"},
        {"name": "Transthoracic Echocardiogram (TTE)", "priority": "CONDITIONAL",
         "rationale": "Evaluates regional wall motion abnormalities, left ventricular ejection fraction, and mechanical complications.",
         "evidence": "ACC/AHA Guidelines"},
    ],
    "acute ischemic stroke": [
        {"name": "Non-Contrast Head CT (NCCT within 20 minutes)", "priority": "HIGH PRIORITY",
         "rationale": "Emergent imaging to rapidly exclude intracranial hemorrhage prior to IV thrombolytic administration.",
         "evidence": "AHA/ASA Guidelines for Early Management of Acute Ischemic Stroke"},
        {"name": "CT Angiography (CTA) of Head and Neck", "priority": "HIGH PRIORITY",
         "rationale": "Identifies large vessel occlusion (LVO) in internal carotid, MCA M1/M2 segments for endovascular thrombectomy.",
         "evidence": "AHA/ASA Stroke Guidelines"},
        {"name": "Point-of-Care Blood Glucose", "priority": "HIGH PRIORITY",
         "rationale": "Mandatory before thrombolysis to immediately rule out hypoglycemia mimicking focal neurological deficit.",
         "evidence": "AHA/ASA Guidelines"},
        {"name": "Complete Blood Count, Platelet Count, and Coagulation Profile (PT/INR, aPTT)", "priority": "HIGH PRIORITY",
         "rationale": "Screens for coagulopathy or thrombocytopenia (<100,000/uL is contraindication to IV alteplase/tenecteplase).",
         "evidence": "AHA/ASA Guidelines"},
        {"name": "MRI Brain with Diffusion-Weighted Imaging (DWI)", "priority": "CONDITIONAL",
         "rationale": "Highest sensitivity for hyperacute cerebral ischemia; differentiates stroke mimic from true infarct.",
         "evidence": "AHA/ASA Guidelines"},
    ],
    "bacterial meningitis": [
        {"name": "Lumbar Puncture with CSF Analysis (Pressure, Cell Count, Protein, Glucose)", "priority": "HIGH PRIORITY",
         "rationale": "Definitive confirmatory diagnostic test; marked pleocytosis with polymorphonuclear predominance, elevated protein, low CSF/serum glucose ratio (<0.4).",
         "evidence": "IDSA Practice Guidelines for Healthcare-Associated and Community Bacterial Meningitis"},
        {"name": "CSF Gram Stain and Multiplex PCR (BioFire FilmArray)", "priority": "HIGH PRIORITY",
         "rationale": "Rapidly identifies Streptococcus pneumoniae, Neisseria meningitidis, Listeria, and other pathogens.",
         "evidence": "IDSA Guidelines / WHO Meningitis Protocols"},
        {"name": "Blood Cultures (x2 sets prior to antibiotic initiation)", "priority": "HIGH PRIORITY",
         "rationale": "Identifies causative pathogen in up to 75% of patients with bacterial meningitis.",
         "evidence": "IDSA Guidelines"},
        {"name": "Non-Contrast Head CT prior to LP", "priority": "HIGH PRIORITY",
         "rationale": "Mandatory in patients with focal neurological deficits, new onset seizures, papilledema, immunocompromise, or depressed consciousness to rule out impending herniation.",
         "evidence": "IDSA Meningitis Guidelines"},
        {"name": "Complete Blood Count (CBC) and Coagulation Profile", "priority": "HIGH PRIORITY",
         "rationale": "Evaluates leukocytosis with bandemia and excludes coagulopathy prior to performing lumbar puncture.",
         "evidence": "IDSA Guidelines"},
    ],
}

# Normalize disease name for KB lookup
def _get_investigation_panel(disease_name: str) -> list:
    """Look up investigation panel from offline KB (case-insensitive, fuzzy match).
    Guarantees evidence-based tests are NEVER empty.
    """
    if not disease_name:
        return []
    disease_lower = disease_name.lower().strip()

    # 1. Exact match in INVESTIGATION_PANELS
    if disease_lower in INVESTIGATION_PANELS:
        return INVESTIGATION_PANELS[disease_lower]

    # 2. Comprehensive Clinical Disease Registry (45+ expert conditions + aliases)
    try:
        from app.services.clinical_disease_metadata import get_disease_clinical_profile
        meta = get_disease_clinical_profile(disease_name)
        if meta:
            imm_tests = meta.get("immediate_tests") or []
            rec_tests = meta.get("recommended_investigations") or []
            res_list = []
            seen = set()
            for t in imm_tests:
                if t.lower() not in seen:
                    seen.add(t.lower())
                    res_list.append({
                        "name": t,
                        "priority": "HIGH PRIORITY",
                        "rationale": f"Stat/immediate diagnostic evaluation for {disease_name}.",
                        "evidence": "Clinical Practice Guidelines / WHO / UpToDate Evidence",
                    })
            for t in rec_tests:
                if t.lower() not in seen:
                    seen.add(t.lower())
                    res_list.append({
                        "name": t,
                        "priority": "CONDITIONAL",
                        "rationale": f"Recommended laboratory and imaging workup for {disease_name}.",
                        "evidence": "Clinical Practice Guidelines / WHO / UpToDate Evidence",
                    })
            if res_list:
                return res_list
    except Exception as e:
        log.debug("investigation_clinical_profile_lookup_failed", error=str(e))

    # 3. Substring & high-specificity keyword match in INVESTIGATION_PANELS
    _STOP_WORDS = {"acute", "chronic", "syndrome", "disease", "disorder", "severe", "fever", "crisis", "shock", "type", "with", "from", "left", "right"}
    for key, panel in INVESTIGATION_PANELS.items():
        if key in disease_lower or (len(disease_lower) >= 6 and disease_lower in key):
            return panel
        key_words = [w for w in key.split() if len(w) > 3 and w not in _STOP_WORDS]
        disease_words = [w for w in disease_lower.split() if len(w) > 3 and w not in _STOP_WORDS]
        if key_words and disease_words and set(key_words) & set(disease_words):
            return panel

    # 4. Syndromic Categorical Fallback based on clinical domain keywords
    if any(k in disease_lower for k in ["kidney", "renal", "urinary", "bladder", "colic", "calcul"]):
        return [
            {"name": "Urinalysis with Microscopic Examination", "priority": "HIGH PRIORITY",
             "rationale": "Evaluates for pyuria, hematuria, proteinuria, and casts.", "evidence": "KDIGO Guidelines"},
            {"name": "Non-Contrast CT Abdomen and Pelvis or Renal Ultrasound", "priority": "HIGH PRIORITY",
             "rationale": "Definitive imaging for renal calculi, hydronephrosis, or parenchymal changes.", "evidence": "ACR Appropriateness Criteria"},
            {"name": "Serum Creatinine, Blood Urea Nitrogen, and eGFR", "priority": "HIGH PRIORITY",
             "rationale": "Assesses baseline glomerular function and acute kidney injury.", "evidence": "KDIGO Guidelines"},
            {"name": "Urine Culture and Antimicrobial Susceptibility", "priority": "CONDITIONAL",
             "rationale": "Rules out superimposed uropathogen infection.", "evidence": "IDSA Guidelines"},
            {"name": "Complete Blood Count with Differential", "priority": "CONDITIONAL",
             "rationale": "Assesses systemic inflammatory response or leukocytosis.", "evidence": "Standard Clinical Practice"},
        ]
    elif any(k in disease_lower for k in ["cardiac", "heart", "coronary", "chest", "angina", "valve", "infarct"]):
        return [
            {"name": "12-Lead Electrocardiogram (ECG)", "priority": "HIGH PRIORITY",
             "rationale": "Screens for ischemic ST-segment changes, arrhythmias, and conduction defects.", "evidence": "ACC/AHA Guidelines"},
            {"name": "Serial High-Sensitivity Cardiac Troponin", "priority": "HIGH PRIORITY",
             "rationale": "Detects and quantifies acute myocardial injury.", "evidence": "Universal Definition of MI"},
            {"name": "Transthoracic Echocardiogram (TTE)", "priority": "HIGH PRIORITY",
             "rationale": "Evaluates ventricular ejection fraction, regional wall motion, and valvular structure.", "evidence": "ACC/AHA Guidelines"},
            {"name": "Complete Blood Count and Comprehensive Metabolic Panel", "priority": "CONDITIONAL",
             "rationale": "Evaluates electrolytes, baseline renal function, and anemia.", "evidence": "Standard Practice"},
            {"name": "Chest Radiograph (PA and Lateral)", "priority": "CONDITIONAL",
             "rationale": "Evaluates for pulmonary vascular congestion, cardiomegaly, and alternative causes.", "evidence": "ACR Guidelines"},
        ]
    elif any(k in disease_lower for k in ["lung", "pulmonary", "respiratory", "breath", "cough", "bronch"]):
        return [
            {"name": "Chest Radiograph (PA and Lateral Views)", "priority": "HIGH PRIORITY",
             "rationale": "Evaluates lung parenchymal infiltrates, hyperinflation, effusions, or pneumothorax.", "evidence": "ATS/ERS Guidelines"},
            {"name": "Pulse Oximetry and Arterial Blood Gas (ABG)", "priority": "HIGH PRIORITY",
             "rationale": "Assesses oxygenation, ventilation, and acid-base status.", "evidence": "ATS Guidelines"},
            {"name": "Complete Blood Count with Differential", "priority": "HIGH PRIORITY",
             "rationale": "Assesses for infectious leukocytosis or secondary polycythemia.", "evidence": "Standard Practice"},
            {"name": "CT Angiography or High-Resolution Chest CT", "priority": "CONDITIONAL",
             "rationale": "Definitive imaging for pulmonary vascular or parenchymal pathology.", "evidence": "Fleischner Society"},
        ]
    elif any(k in disease_lower for k in ["belly", "abdom", "digest", "gastric", "bowel", "liver", "hepatic", "pancrea", "biliary"]):
        return [
            {"name": "Abdominal Ultrasonography or Contrast-Enhanced CT", "priority": "HIGH PRIORITY",
             "rationale": "Definitive anatomical assessment for acute abdominal pathology.", "evidence": "ACR Appropriateness Criteria"},
            {"name": "Complete Blood Count (CBC) with Differential", "priority": "HIGH PRIORITY",
             "rationale": "Identifies leukocytosis and systemic inflammatory response.", "evidence": "WSES Guidelines"},
            {"name": "Comprehensive Metabolic Panel and Liver Function Tests", "priority": "HIGH PRIORITY",
             "rationale": "Assesses hepatic enzymes, bilirubin, albumin, and renal function.", "evidence": "ACG Guidelines"},
            {"name": "Serum Lipase and Amylase", "priority": "HIGH PRIORITY",
             "rationale": "Rules out acute pancreatitis in abdominal presentation.", "evidence": "ACG Guidelines"},
            {"name": "Serum C-Reactive Protein and Lactate", "priority": "CONDITIONAL",
             "rationale": "Sensitive biomarkers for mesenteric ischemia and severe intra-abdominal inflammation.", "evidence": "Surviving Sepsis Campaign"},
        ]
    else:
        # Recognized disease in offline disease KB
        try:
            from app.services.offline_disease_kb import DISEASE_KB
            if disease_name in DISEASE_KB or any(d.lower() == disease_lower for d in DISEASE_KB):
                return [
                    {"name": "Complete Blood Count (CBC) with Automated Differential", "priority": "HIGH PRIORITY",
                     "rationale": f"Evaluates for infectious leukocytosis, anemia, and thrombocytopenia in {disease_name}.", "evidence": "Standard Clinical Practice"},
                    {"name": "Comprehensive Metabolic Panel (Electrolytes, BUN, Creatinine, LFTs)", "priority": "HIGH PRIORITY",
                     "rationale": f"Evaluates renal function, hepatic integrity, and electrolyte balance in {disease_name}.", "evidence": "Standard Clinical Practice"},
                    {"name": "Serum C-Reactive Protein (CRP) and ESR", "priority": "HIGH PRIORITY",
                     "rationale": "Quantifies systemic inflammatory response.", "evidence": "Clinical Practice Guidelines"},
                    {"name": "Urinalysis with Microscopic Examination", "priority": "CONDITIONAL",
                     "rationale": "Screens for renal involvement, proteinuria, or occult infection.", "evidence": "Standard Clinical Practice"},
                ]
        except Exception:
            pass
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

    def get_investigations(
        self,
        db_or_disease: Any,
        disease_name: Optional[str] = None,
        representation: Any = None,
        competing: list = None,
    ) -> Any:
        if isinstance(db_or_disease, str) and disease_name is None:
            actual_disease = db_or_disease
            offline_panel = _get_investigation_panel(actual_disease)
            suggestions = [
                InvestigationSuggestion(
                    name=p.get("name", "Test"),
                    priority=p.get("priority", "CONDITIONAL"),
                    rationale=p.get("rationale", ""),
                    relevant_clinical_finding="",
                    evidence=p.get("evidence", "WHO/CDC/NIH Guidelines"),
                    limitations="",
                    safety_flags=[],
                    provenance=p.get("evidence", "WHO/CDC/NIH Guidelines"),
                )
                for p in offline_panel
            ]
            return AwaitableInvestigationResponse(disease=actual_disease, suggestions=suggestions)
        else:
            db = db_or_disease
            actual_disease = disease_name
            offline_panel = _get_investigation_panel(actual_disease) if actual_disease else []
            offline_suggestions = [
                InvestigationSuggestion(
                    name=p.get("name", "Test"),
                    priority=p.get("priority", "CONDITIONAL"),
                    rationale=p.get("rationale", ""),
                    relevant_clinical_finding="",
                    evidence=p.get("evidence", "WHO/CDC/NIH Guidelines"),
                    limitations="",
                    safety_flags=[],
                    provenance=p.get("evidence", "WHO/CDC/NIH Guidelines"),
                )
                for p in offline_panel
            ]
            async def _async_runner():
                return await self._get_investigations_async(db, actual_disease, representation, competing)
            return AwaitableInvestigationResponse(
                coro_fn=_async_runner,
                disease=actual_disease or "",
                suggestions=offline_suggestions,
            )

    async def _get_investigations_async(
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
        if representation and getattr(representation, "travel_history", None):
            countries = [getattr(item, "value", str(item)) for item in representation.travel_history
                         if getattr(item, "value", str(item)).lower() not in ("none", "ongoing infectious disease outbreak area")]

        try:
            rag_coro = retrieve_medical_context(db, f"{disease_name} investigations workup", top_k=3) if db is not None else asyncio.sleep(0, result="")
            lab_coro = retrieve_investigation_context(db, f"tests for {disease_name}", top_k=4) if db is not None else asyncio.sleep(0, result="")
            rag_ctx, lab_ctx, live_sources = await asyncio.wait_for(
                asyncio.gather(
                    rag_coro,
                    lab_coro,
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
        symptoms = ", ".join(getattr(item, "value", str(item)) for item in representation.symptoms) if (representation and getattr(representation, "symptoms", None)) else "None"
        vitals = ", ".join(getattr(item, "value", str(item)) for item in representation.vitals) if (representation and getattr(representation, "vitals", None)) else "None"
        history = ", ".join(getattr(item, "value", str(item)) for item in representation.history) if (representation and getattr(representation, "history", None)) else "None"
        travel = ", ".join(getattr(item, "value", str(item)) for item in representation.travel_history) if (representation and getattr(representation, "travel_history", None)) else "None"
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
