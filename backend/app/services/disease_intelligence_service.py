"""DocAssistIQ - Deep Disease Intelligence Service (v3 World-Class).

Generates comprehensive 20+ field clinical intelligence profiles using:
  - Wikipedia Medical API
  - ICD-11 Foundation API
  - PubMed/NCBI abstracts
  - WHO/CDC live context
  - Internal RAG (uploaded clinical documents)
  - OpenFDA drug database
  - Live outbreak scanner dynamic KB
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.disease_intelligence import (
    DiseaseIntelligenceResponse, EpidemiologyData, SpecialPopulationWarning
)
from app.schemas.rag import RAGQueryRequest
from app.services.rag_service import retrieve_evidence, retrieve_medical_context
from app.services.llm_service import llm_service
import structlog

log = structlog.get_logger(__name__)

DEEP_INTELLIGENCE_PROMPT = """You are a world-class Senior Consultant Physician and Clinical Epidemiologist at a top academic medical center.
Generate a COMPREHENSIVE, EVIDENCE-BASED clinical intelligence profile for the disease: {disease_name}

Use ALL provided multi-source context. This profile will be used by specialist physicians — it must be complete, accurate, and detailed.

## MANDATORY OUTPUT — Generate ALL fields:
1. summary: 4-6 sentences — etiology, pathogenesis, geographic distribution, typical clinical course, current WHO status.
2. pathophysiology: Detailed mechanism of disease (cellular/molecular/organ level). 4-8 sentences.
3. etiology: Causative agent(s), risk factors, transmission route.
4. icd11_code: The ICD-11 code for this disease (e.g., "1C11.0"). If uncertain, best estimate.
5. who_classification: WHO disease category.
6. disease_class: Simple class (e.g., "Viral Hemorrhagic Fever", "Bacterial Meningitis").
7. is_notifiable: true/false — is this WHO-notifiable or nationally reportable?
8. is_outbreak_active: true/false — is there an active outbreak anywhere globally?
9. cardinal_symptoms: 3-5 most pathognomonic/distinctive symptoms — what makes this diagnosis.
10. symptoms: ALL symptoms from early to late disease progression (comprehensive, 12-20 items).
11. signs_on_examination: Physical signs a doctor would find on examination (10-15 items).
12. red_flags: Danger signs requiring IMMEDIATE escalation (5-8 items).
13. incubation_period: Specific range (e.g., "2-21 days (mean 8-10 days)").
14. disease_stages: Named stages/phases with clinical description (e.g., ["Incubation phase", "Prodromal phase: fever, fatigue", "Acute phase: hemorrhage"]).
15. prognosis: Mortality rate, recovery timeline, long-term sequelae, factors affecting outcome.
16. complications: Specific complications with frequency if known (10-15 items).
17. first_line_treatment: Most important single treatment decision.
18. treatments: ALL treatment options — supportive, specific, procedural (10-15 items).
19. medications: Specific evidence-based pharmaceutical agents with exact names, dosing, routes, and clinical indications (e.g. ["Drug name dosage route indication", ...]).
20. monitoring_parameters: Lab/clinical parameters to track during treatment.
21. investigations: SPECIFIC test names with priority — confirmatory, staging, monitoring, differential-exclusion.
22. differential_diagnosis_clues: Key features that distinguish from similar diseases (5-8 clues).
23. epidemiology: Object with global_incidence, mortality_rate, affected_regions, outbreak_status, seasonal_pattern, high_risk_groups.
24. prevention: Specific preventive measures (vaccines, chemoprophylaxis, behavioral).
25. public_health_measures: Isolation, quarantine, reporting requirements.
26. special_populations: Array of objects for pregnancy, pediatric, immunocompromised, elderly — each with specific warning and recommendation.
27. data_sources: List the sources used.
## Multi-Source Context:
{context}

## OUTPUT — Valid JSON ONLY (no markdown, no preamble):
{{
  "summary": "",
  "pathophysiology": "",
  "etiology": "",
  "icd11_code": "",
  "who_classification": "",
  "disease_class": "",
  "is_notifiable": false,
  "is_outbreak_active": false,
  "cardinal_symptoms": [],
  "symptoms": [],
  "signs_on_examination": [],
  "red_flags": [],
  "incubation_period": "",
  "disease_stages": [],
  "prognosis": "",
  "complications": [],
  "first_line_treatment": "",
  "treatments": [],
  "medications": [],
  "monitoring_parameters": [],
  "investigations": [],
  "differential_diagnosis_clues": [],
  "epidemiology": {{
    "global_incidence": "",
    "mortality_rate": "",
    "affected_regions": [],
    "outbreak_status": "",
    "seasonal_pattern": "",
    "high_risk_groups": []
  }},
  "prevention": [],
  "public_health_measures": [],
  "special_populations": [
    {"population": "Pregnancy", "warning": "", "recommendation": ""},
    {"population": "Pediatric", "warning": "", "recommendation": ""},
    {"population": "Immunocompromised", "warning": "", "recommendation": ""}
  ]
}}"""

# ---------------------------------------------------------------------------
# STATIC KB FALLBACK — Complete clinical profiles without LLM
# Covers the most critical infectious diseases, especially VHFs
# Used when LLM is unavailable, timed out, or circuit-breaker tripped
# ---------------------------------------------------------------------------

_VHF_INVESTIGATIONS = [
    "URGENT BSL-3/4 PCR: Ebola/Marburg/Sudan virus RT-PCR (Specialist Lab ONLY)",
    "Malaria thick/thin blood film + RDT (must exclude as co-infection)",
    "FBC with differential — thrombocytopenia, leukopenia expected in VHF",
    "Coagulation profile: PT, APTT, fibrinogen, D-dimer — DIC assessment",
    "Metabolic panel: U&E, creatinine, LFTs (ALT, AST, bilirubin)",
    "Blood cultures (aerobic + anaerobic) × 2 sets — exclude bacterial sepsis",
    "Serum lactate — sepsis / shock marker",
    "CXR (portable if infection-control isolation required)",
    "Urinalysis + microscopy",
    "CRP, ESR, Procalcitonin",
    "HIV rapid test",
    "Dengue NS1 Ag + IgM/IgG",
    "Typhoid (Widal + blood culture)",
    "Viral hepatitis panel: HBsAg, anti-HCV, anti-HAV IgM",
    "Serum electrolytes — hyponatraemia common in VHF",
    "ABG / venous blood gas — metabolic acidosis",
    "12-lead ECG",
]

_EBOLA_STATIC_PROFILE = {
    "summary": (
        "Ebola Virus Disease (EVD) is a severe and often fatal viral hemorrhagic fever caused by "
        "Ebolavirus (genus Ebolavirus, family Filoviridae). Four species cause disease in humans: "
        "Zaire (EBOV), Sudan (SUDV), Bundibugyo (BDBV), and Taï Forest (TAFV). EBOV (Zaire) is "
        "the most lethal with case fatality rates of 25–90%. The disease is endemic to sub-Saharan "
        "Africa, particularly the Democratic Republic of Congo (DRC), Uganda, and Republic of Congo. "
        "Transmission is via direct contact with blood, secretions, or organs of infected humans or animals. "
        "No licensed oral treatment exists; supportive care with IV fluids and electrolyte management "
        "is the cornerstone of treatment. REGEN-EB3 (atoltivimab+maftivimab+odesivimab) and Inmazeb "
        "are FDA-approved for Zaire EBOV. The rVSV-ZEBOV (Ervebo) vaccine is approved for prevention. "
        "Immediate high-level isolation (BSL-4 precautions) and public health notification are mandatory."
    ),
    "pathophysiology": (
        "EBOV enters via mucosal surfaces or skin breaks and initially infects monocytes, macrophages, "
        "and dendritic cells — impairing innate immune responses. The virus replicates systemically, "
        "triggering a massive cytokine storm (TNF-α, IL-6, IL-8). Endothelial dysfunction leads to "
        "vascular leak, disseminated intravascular coagulation (DIC), and multi-organ failure. "
        "Liver involvement causes hepatocyte necrosis (elevated transaminases). Impaired coagulation "
        "factors + thrombocytopenia → hemorrhagic manifestations. Viral load peaks at 5–7 days of illness."
    ),
    "etiology": (
        "Zoonotic origin — natural reservoir believed to be fruit bats (Pteropodidae). "
        "Human-to-human transmission via direct contact with blood/body fluids/secretions of symptomatic or "
        "deceased EVD patients. No airborne transmission. Healthcare worker exposure via needlestick or PPE breach. "
        "Incubation 2–21 days (mean 8–12 days). Infectious only when symptomatic. "
        "Virus can persist in semen for up to 18 months post-recovery."
    ),
    "icd11_code": "1D60.0",
    "who_classification": "WHO Priority Pathogen — Viral Hemorrhagic Fever",
    "disease_class": "Viral Hemorrhagic Fever (VHF) — Filovirus",
    "is_notifiable": True,
    "is_outbreak_active": True,
    "incubation_period": "2–21 days (mean 8–12 days)",
    "cardinal_symptoms": [
        "Sudden high fever (>38.6°C)",
        "Profound weakness and fatigue",
        "Severe headache",
        "Myalgia and arthralgia",
        "Watery diarrhoea",
        "Vomiting",
        "Abdominal pain",
        "Sore throat"
    ],
    "symptoms": [
        "Sudden fever onset", "Fatigue and weakness", "Severe headache",
        "Muscle pain (myalgia)", "Joint pain (arthralgia)", "Sore throat",
        "Watery diarrhoea", "Vomiting", "Nausea", "Abdominal pain",
        "Loss of appetite (anorexia)", "Dehydration", "Oliguria (reduced urine output)",
        "Conjunctival injection (red eyes)", "Hiccups", "Dysphagia",
        "Confusion and altered mental status", "Somnolence",
        "Haemorrhagic manifestations: gum bleeding, bloody vomit, petechiae",
        "Rash (maculopapular — appears day 5–7)", "Chest pain", "Dyspnoea"
    ],
    "signs_on_examination": [
        "High-grade fever (>39°C)", "Hypotension (late sign — circulatory shock)",
        "Tachycardia", "Dehydration (decreased skin turgor, dry mucosae)",
        "Conjunctival redness / injection", "Generalised tenderness on abdominal palpation",
        "Altered consciousness (GCS reduction)", "Petechiae / ecchymoses",
        "Active haemorrhage from puncture sites, gums, GI tract",
        "Maculopapular rash (trunk — not always present)"
    ],
    "red_flags": [
        "Active haemorrhage from any site — DIC",
        "Haemorrhagic shock — systolic BP < 90 mmHg",
        "Altered consciousness / encephalopathy — GCS < 14",
        "Oliguria / anuria → acute kidney injury",
        "Respiratory distress",
        "Rapidly rising transaminases (ALT/AST > 10× ULN)",
        "Viral load > 10⁷ copies/mL",
        "Seizures"
    ],
    "disease_stages": [
        "Stage 1 (Days 1–3): Dry phase — fever, myalgia, headache, fatigue, sore throat",
        "Stage 2 (Days 4–6): GI phase — vomiting, diarrhoea, abdominal pain; severe dehydration",
        "Stage 3 (Days 7–10): Wet phase — multi-organ failure, haemorrhage, shock; high mortality window",
        "Stage 4 (Days 10–14+): Either recovery (fever breaks, viral load declines) or death"
    ],
    "prognosis": (
        "Case fatality rate 25–90% depending on species and healthcare access. "
        "Zaire EBOV (DRC): ~65% CFR in community settings. With optimal IV fluid resuscitation and "
        "monoclonal antibody therapy (REGEN-EB3), CFR may fall to 30–40%. Survivors may experience "
        "Post-Ebola Syndrome: fatigue, arthralgia, ocular disease (uveitis), hearing loss. "
        "Early presentation, younger age, lower viral load, and access to intensive supportive care "
        "are associated with improved survival."
    ),
    "complications": [
        "Disseminated Intravascular Coagulation (DIC)",
        "Hypovolaemic / septic shock",
        "Acute Kidney Injury (AKI)",
        "Acute Respiratory Failure / ARDS",
        "Hepatic failure (elevated transaminases, coagulopathy)",
        "Electrolyte disturbances (hyponatraemia, hypokalaemia, hypocalcaemia)",
        "Secondary bacterial infections / nosocomial pneumonia",
        "Neurological complications (encephalitis, cerebral oedema)",
        "Post-Ebola Syndrome (long-term sequelae in survivors)"
    ],
    "first_line_treatment": (
        "Immediate HIGH-LEVEL ISOLATION (BSL-4 precautions). "
        "Aggressive IV fluid resuscitation (1–2L normal saline/hr if shocked). "
        "Monoclonal antibody therapy: REGEN-EB3 (Inmazeb) — atoltivimab + maftivimab + odesivimab — "
        "single IV infusion. Symptomatic management of fever (paracetamol), antiemetics, antidiarrhoeals."
    ),
    "treatments": [
        "IMMEDIATE: Activate hospital infection-control protocol — full PPE (gloves × 2, gown, N95, face shield, boot covers)",
        "Notify public health authorities and WHO immediately",
        "IV access × 2 large bore + aggressive fluid resuscitation: Normal Saline 1000–2000 mL bolus, then titrate to UO",
        "Monoclonal Ab: REGEN-EB3 (Inmazeb) — Zaire EBOV only — single dose IV infusion (requires specialist approval + compassionate use pathway)",
        "Antiviral: Remdesivir — investigational for EVD (not standard of care)",
        "Symptomatic: Paracetamol 1g IV/PO q6h (avoid NSAIDs/aspirin — platelet effect)",
        "Antiemetic: Ondansetron 4–8mg IV q8h",
        "Electrolyte replacement: Potassium, Calcium, Magnesium supplementation",
        "Oral Rehydration Salts (ORS) if tolerated — electrolyte-rich",
        "If DIC: FFP, cryoprecipitate, platelets per haematology guidance",
        "Vasopressors (Noradrenaline) if refractory hypotension in ICU setting",
        "Avoid unnecessary invasive procedures — minimise puncture site bleeding risk",
        "rVSV-ZEBOV (Ervebo) vaccine for ring vaccination of contacts — coordinate with WHO/CDC"
    ],
    "monitoring_parameters": [
        "Vital signs every 30–60 min (HR, BP, RR, SpO2, Temp)",
        "Strict fluid balance — urine output target > 0.5 mL/kg/hr",
        "Daily FBC — platelet nadir < 50 is high-risk for haemorrhage",
        "Coagulation: PT, APTT, fibrinogen — DIC monitoring",
        "LFTs daily (ALT, AST, bilirubin — hepatic involvement)",
        "U&E, creatinine — AKI monitoring",
        "Blood glucose (hypoglycaemia can occur)",
        "Viral load: RT-PCR q48h — predictor of outcome",
        "GCS every 4 hours — neurological decline",
        "Skin integrity — haemorrhagic rash progression"
    ],
    "investigations": _VHF_INVESTIGATIONS,
    "differential_diagnosis_clues": [
        "Malaria: most common DRC travel fever — must EXCLUDE first with film + RDT; no haemorrhage in uncomplicated malaria",
        "Typhoid: rose spots, relative bradycardia, positive Widal/blood culture — less acute onset",
        "Leptospirosis: water/soil exposure, jaundice, conjunctival suffusion, myalgia — Weil's disease",
        "Marburg Virus: identical presentation; Marburg also in DRC/Uganda — differentiate only by PCR",
        "CCHF (Crimean-Congo Haemorrhagic Fever): tick exposure history; haemorrhage more prominent early",
        "Dengue: thrombocytopenia, positive tourniquet test, dengue PCR/NS1 — no DRC transmission",
        "Meningococcal sepsis: purpuric rash, meningism, rapid deterioration — no GI prodrome",
        "Mpox (Monkeypox): skin vesicles/pustules, less severe haemorrhage, also DRC endemic"
    ],
    "epidemiology": {
        "global_incidence": "Sporadic outbreaks; > 30 outbreaks since 1976",
        "mortality_rate": "25–90% (species and care-dependent); Zaire EBOV ~65% community CFR",
        "affected_regions": ["Democratic Republic of Congo", "Uganda", "Republic of Congo", "Gabon", "South Sudan", "Sierra Leone (2014)", "Guinea (2014)", "Liberia (2014)"],
        "outbreak_status": "Ongoing DRC outbreaks (2022-present); sporadic detection every 1-2 years",
        "seasonal_pattern": "No strong seasonal pattern; linked to contact with infected wildlife or humans",
        "high_risk_groups": ["Healthcare workers (PPE breach)", "Family members of cases (home care)", "Traditional burial ceremony participants", "Hunters/bushmeat handlers", "Laboratory workers (accidental exposure)"]
    },
    "prevention": [
        "rVSV-ZEBOV (Ervebo) vaccine — WHO pre-qualified, ring vaccination strategy",
        "Ad26.ZEBOV/MVA-BN-Filo (Zabdeno+Mvabea) — 2-dose regimen for broader protection",
        "Strict contact and droplet precautions — full BSL-4 PPE in healthcare settings",
        "No bushmeat consumption in endemic areas",
        "Safe burial practices — trained burial teams with PPE",
        "Isolation of cases and quarantine of contacts for 21 days (max incubation)",
        "Traveller health advisory for DRC/Uganda — pre-travel counselling"
    ],
    "public_health_measures": [
        "IMMEDIATELY notify national public health authority (ICMR/NCDC in India) + WHO",
        "Contact tracing — all contacts from symptom onset; 21-day quarantine monitoring",
        "Ring vaccination of identified contacts",
        "Hospital infection control: dedicated isolation room, negative pressure if available",
        "Full PPE donning/doffing training for all treating staff",
        "Sample transport: Triple-packaging per IATA P650; specialist lab (BSL-3 minimum for PCR)",
        "Airport health screening if index case travelled by air — notify port health",
        "Media and community communication — prevent panic; address misinformation"
    ],
    "special_populations": [
        {"population": "Pregnancy", "warning": "EVD in pregnancy has near-universal maternal and fetal mortality. Placental infection and fetal viraemia. Risk of obstetric haemorrhage is extreme.", "recommendation": "Immediate specialist obstetrics + infection control consultation. Fetal/placental tissue is highly infectious. Obstetric interventions require BSL-4 precautions."},
        {"population": "Paediatric", "warning": "Children < 5 years have higher CFR. Fluid resuscitation volumes require careful weight-based calculation.", "recommendation": "Paediatric infectious disease specialist involvement. Oral rehydration preferred if tolerated."},
        {"population": "Immunocompromised", "warning": "Impaired viral clearance. Higher viraemia. Less typical presentation may delay diagnosis.", "recommendation": "Lower threshold for testing. Monoclonal Ab therapy essential if available."},
        {"population": "Healthcare Workers", "warning": "High-risk exposure group. Must have correct PPE and donning/doffing supervision.", "recommendation": "Occupational health assessment post-exposure. Post-exposure prophylaxis: Ervebo vaccine within 24h of exposure."}
    ],
    "data_sources": ["WHO", "CDC", "UpToDate", "Harrison's Principles 21st Ed", "Lancet Infectious Diseases", "NEJM", "BMJ"],
}

_DISEASE_STATIC_PROFILES: dict = {
    "ebola": _EBOLA_STATIC_PROFILE,
    "ebola virus disease": _EBOLA_STATIC_PROFILE,
    "ebola virus disease (zaire)": _EBOLA_STATIC_PROFILE,
    "zaire ebolavirus": _EBOLA_STATIC_PROFILE,
    "viral hemorrhagic fever": _EBOLA_STATIC_PROFILE,
    "viral haemorrhagic fever": _EBOLA_STATIC_PROFILE,
    "bundibugyo virus disease": {**_EBOLA_STATIC_PROFILE, "icd11_code": "1D60.1", "disease_class": "Viral Hemorrhagic Fever — Bundibugyo Ebolavirus"},
    "bundibugyo virus disease (bvd)": {**_EBOLA_STATIC_PROFILE, "icd11_code": "1D60.1"},
    "marburg virus disease": {
        **_EBOLA_STATIC_PROFILE,
        "icd11_code": "1D61",
        "disease_class": "Viral Hemorrhagic Fever — Marburg Virus (Filoviridae)",
        "summary": "Marburg Virus Disease (MVD) is caused by Marburg virus (MARV), a filovirus closely related to Ebola. First recognized in 1967 (Marburg, Germany). Endemic in Africa; reservoir: Egyptian fruit bats (Rousettus aegyptiacus). CFR 24–88%. No licensed vaccine. Treatment is supportive; MR-191 (monoclonal antibody) under compassionate use. Clinical presentation identical to Ebola. Must differentiate by RT-PCR.",
        "epidemiology": {"affected_regions": ["Uganda", "Kenya", "Democratic Republic of Congo", "Angola", "Guinea", "Rwanda"], "mortality_rate": "24–88%", "outbreak_status": "Sporadic outbreaks — Rwanda 2024", "high_risk_groups": ["Cave/mine workers", "Healthcare workers", "Contact with bats"], "global_incidence": "Sporadic; < 500 total confirmed cases historically", "seasonal_pattern": "No seasonal pattern"},
    },
    "lassa fever": {
        "icd11_code": "1D64",
        "disease_class": "Viral Hemorrhagic Fever — Arenavirus",
        "summary": "Lassa fever is caused by Lassa mammarenavirus, endemic to West Africa (Nigeria, Sierra Leone, Guinea, Liberia). Transmitted via contact with infected Mastomys rats or their excreta. CFR ~1% overall, 15–25% in hospitalised patients. Treatment: Ribavirin IV (most effective if started within 6 days).",
        "cardinal_symptoms": ["fever", "sore throat", "retrosternal chest pain", "hearing loss", "facial swelling"],
        "symptoms": ["fever", "weakness", "headache", "sore throat", "chest pain", "hearing loss", "cough", "abdominal pain", "vomiting", "diarrhoea", "conjunctivitis", "skin rash", "haemorrhage (minority)"],
        "investigations": _VHF_INVESTIGATIONS,
        "first_line_treatment": "Ribavirin IV: 30 mg/kg loading dose, then 16 mg/kg q6h × 4 days, then 8 mg/kg q8h × 6 days. Supportive care.",
        "treatments": ["Ribavirin IV (within 6 days of onset)", "IV fluids", "Electrolyte management", "Isolation precautions"],
        "red_flags": ["Facial oedema", "Haemorrhage", "Respiratory distress", "Encephalopathy", "Hearing loss (poor prognosis)"],
        "epidemiology": {"affected_regions": ["Nigeria", "Sierra Leone", "Guinea", "Liberia"], "mortality_rate": "15–25% hospitalised", "high_risk_groups": ["Healthcare workers", "Rural West Africa residents", "Rat-infested environments"]},
        "is_notifiable": True,
        "is_outbreak_active": False,
        "data_sources": ["WHO", "CDC", "UpToDate"],
    },

    # ===========================
    # HANTAVIRUS PULMONARY SYNDROME
    # ===========================
    "hantavirus pulmonary syndrome": {
        "disease_name": "Hantavirus Pulmonary Syndrome",
        "icd11_code": "1D82",
        "disease_class": "Zoonotic Viral Disease — Hantavirus (Bunyaviridae)",
        "who_classification": "Priority Pathogen — Rodent-Borne Zoonosis",
        "is_notifiable": True,
        "is_outbreak_active": False,
        "summary": (
            "Hantavirus Pulmonary Syndrome (HPS) is a severe, often fatal rodent-borne zoonosis caused by "
            "New World hantaviruses (Sin Nombre, Andes, Bayou, Black Creek Canal viruses). Humans are "
            "infected via inhalation of aerosols from infected rodent excreta (urine, faeces, saliva). "
            "CFR: 30–40% without ECMO; reduced to ~20% with ECMO. No specific antiviral exists. "
            "In South America, Andes Orthohantavirus is the predominant strain — uniquely capable of "
            "human-to-human transmission. Incubation: 1–5 weeks (typically 2–3 weeks). "
            "Two-phase illness: (1) GI prodrome — fever, myalgia, nausea, abdominal pain; "
            "(2) Rapid-onset cardiopulmonary collapse with non-cardiogenic pulmonary oedema and shock."
        ),
        "pathophysiology": (
            "Hantaviruses infect pulmonary endothelial cells via β3-integrin receptor. "
            "This triggers massive immune-mediated cytokine release (TNF-α, IL-6, IL-10) causing "
            "capillary leak syndrome — plasma shifts from vascular to interstitial/alveolar compartments. "
            "Result: non-cardiogenic pulmonary oedema, haemoconcentration (haematocrit rise), "
            "thrombocytopenia (immune destruction + consumption), and biventricular myocardial depression. "
            "Cardiac output falls precipitously — cardiogenic shock superimposed on ARDS. "
            "This dual mechanism (ARDS + cardiogenic shock) distinguishes HPS from other ARDS causes."
        ),
        "etiology": (
            "Sin Nombre virus (North America: SW USA, Canada) — reservoir: Deer Mouse (Peromyscus maniculatus). "
            "Andes Orthohantavirus (Argentina, Chile, Uruguay, Bolivia, Paraguay) — reservoir: Long-tailed Pygmy Rice Rat (Oligoryzomys longicaudatus). "
            "Bayou virus (Louisiana, Texas) — reservoir: Rice Rat. "
            "Black Creek Canal virus (Florida) — reservoir: Cotton Rat. "
            "Transmission: inhalation of aerosolised rodent excreta. Rural, agricultural, or forested environments. "
            "Andes strain: additionally transmitted person-to-person (only hantavirus with documented human-to-human spread — Wells RM, Science 1997)."
        ),
        "incubation_period": "9–35 days (typically 14–21 days)",
        "disease_stages": [
            "Phase 1 — Febrile/GI Prodrome (Days 1–5): Sudden fever (38–40°C), rigors, severe myalgia, headache, nausea, vomiting, abdominal pain, diarrhoea. No respiratory symptoms yet.",
            "Phase 2 — Cardiopulmonary (Days 5–10): Abrupt onset dyspnoea, hypoxia, non-cardiogenic pulmonary oedema. Haemoconcentration (Hct rises >5%). Thrombocytopenia nadir. Cardiogenic shock.",
            "Phase 3 — Diuretic Recovery (Days 10+): Survivors enter a brisk diuretic phase. Pulmonary infiltrates clear. Platelets normalise. Full recovery takes weeks–months.",
        ],
        "cardinal_symptoms": [
            "Fever + severe myalgia (prodrome)",
            "Abdominal pain + GI symptoms before respiratory onset",
            "Sudden dyspnoea and hypoxia (cardiopulmonary phase onset)",
            "Haemoconcentration (rising haematocrit >45%)",
            "Thrombocytopenia (platelets <150,000)",
            "Immunoblasts (atypical lymphocytes >10%) on blood film",
            "Bilateral interstitial infiltrates on CXR",
            "Cardiogenic shock + pulmonary oedema",
        ],
        "symptoms": [
            "Fever (38–40°C)", "Chills/rigors", "Severe myalgia", "Intense headache",
            "Nausea", "Vomiting", "Abdominal pain", "Diarrhoea", "Malaise", "Profound weakness",
            "Dizziness", "Cough (dry, non-productive)", "Dyspnoea", "Chest tightness",
            "Tachypnoea", "Hypoxia", "Low blood pressure", "Diaphoresis",
        ],
        "signs_on_examination": [
            "Fever (38–40°C)", "Tachycardia", "Tachypnoea (>30/min in cardiopulmonary phase)",
            "Hypotension/shock (SBP <90 mmHg)", "Hypoxia (SpO2 <90% on room air)",
            "Bilateral crackles on auscultation", "Signs of pulmonary oedema",
            "Haemoconcentration on FBC", "Thrombocytopenia on FBC",
            "Immunoblasts/atypical lymphocytes on peripheral smear",
            "Rising haematocrit (hallmark of vascular leak)",
            "Reduced urine output (oliguria in severe cases)",
        ],
        "red_flags": [
            "SpO2 <92% on room air — ICU transfer immediately",
            "Haematocrit >50% — severe haemoconcentration, imminent deterioration",
            "Platelets <80,000 with respiratory symptoms — high mortality risk",
            "SBP <90 mmHg — cardiogenic shock onset",
            "CXR bilateral infiltrates — ARDS established",
            "LDH >500 U/L — severe tissue damage",
            "Immunoblasts >10% on blood film — PATHOGNOMONIC for cardiopulmonary phase",
            "Metabolic acidosis on ABG",
            "Rate of haemoconcentration > 5 points/hour — emergency",
        ],
        "prognosis": (
            "CFR: 30–40% overall. With aggressive ICU support and ECMO: ~20%. "
            "Andes virus has higher CFR than Sin Nombre. Mortality highest in cardiopulmonary phase. "
            "Survivors typically recover fully with normal pulmonary function at 6–12 months. "
            "Predictors of death: haematocrit >50%, platelets <50,000, PaO2/FiO2 <100, EF <45%."
        ),
        "complications": [
            "ARDS (bilateral pulmonary infiltrates, P/F ratio <200)",
            "Cardiogenic shock (EF <40%)",
            "Disseminated Intravascular Coagulation (DIC)",
            "Acute Kidney Injury (50% of cases)",
            "Secondary bacterial pneumonia",
            "Pulmonary haemorrhage (Andes strain)",
            "Multi-organ failure",
            "Death (30–40% without ECMO)",
        ],
        "investigations": [
            "Hantavirus IgM + IgG Serology (ELISA) — Reference Lab (PATHOGNOMONIC — HIGH PRIORITY)",
            "RT-PCR for Hantavirus RNA (Whole Blood/PBMC) — HIGH PRIORITY",
            "FBC with Differential — Thrombocytopenia + Haemoconcentration + Immunoblasts (HALLMARK)",
            "Chest X-Ray (PA + Lateral) — Bilateral infiltrates (HIGH PRIORITY)",
            "Arterial Blood Gas (ABG) — P/F ratio, ventilation guidance (HIGH PRIORITY)",
            "Echocardiogram — ECMO decision (EF <40% = ECMO) (HIGH PRIORITY)",
            "Serum LDH + Albumin — Severity markers",
            "Comprehensive Metabolic Panel (LFTs, Renal, Electrolytes)",
            "Serum Lactate — Perfusion marker",
            "Malaria RDT + Blood Film (critical differential)",
            "Dengue NS1 + Serology (co-endemic differential)",
            "Blood Culture ×2 (exclude bacterial sepsis)",
            "Leptospira Serology MAT/ELISA (rural South America — overlap exposure)",
        ],
        "first_line_treatment": (
            "SUPPORTIVE CARE IS THE MAINSTAY — No specific antiviral approved for HPS. "
            "1. ICU admission at first sign of cardiopulmonary phase. "
            "2. Mechanical ventilation: Low tidal volume 6 mL/kg IBW (ARDS Net protocol). "
            "3. Vasopressors: Noradrenaline first-line for shock. "
            "4. ECMO (VV or VA): Consider if EF <40% or P/F <100 despite optimal ventilation. "
            "5. Judicious fluids — avoid aggressive resuscitation (worsens pulmonary oedema). "
            "6. Ribavirin: NOT recommended for HPS (trials showed no benefit — Mertz GJ 2004). "
            "7. CONTACT AND DROPLET ISOLATION for Andes strain (person-to-person transmission)."
        ),
        "treatments": [
            "ICU admission with continuous monitoring",
            "Mechanical ventilation — Low tidal volume 6 mL/kg IBW (ARDS Net)",
            "PEEP titration for oxygenation (target SpO2 >92%)",
            "Vasopressors — Noradrenaline first-line for shock (target MAP >65)",
            "ECMO (VA-ECMO) — if cardiogenic shock + ARDS (EF <40%)",
            "Conservative fluid strategy — aggressive fluids worsen oedema",
            "Platelet transfusion if <20,000 or active bleeding",
            "Dialysis if acute kidney injury (oliguria + creatinine rise)",
            "Strict isolation (droplet + contact) — especially for Andes strain",
            "Close monitoring of haematocrit (q2–4h — falling Hct = diuretic phase)",
            "Prone positioning (if P/F <150 on CMV — PROSEVA criteria)",
        ],
        "monitoring_parameters": [
            "Haematocrit (serial q2–4h — rising Hct = haemoconcentration = deterioration)",
            "Platelet count (daily minimum — q12h in ICU)",
            "ABG (q4h in ICU — PaO2/FiO2 ratio trend)",
            "Echocardiogram (EF trend — ECMO decision threshold EF <40%)",
            "Lactate (q4h — perfusion adequacy)",
            "Urine output (target >0.5 mL/kg/h)",
            "Chest X-Ray daily (infiltrate progression rate)",
            "LDH, CRP (severity and trajectory)",
            "Renal function daily",
        ],
        "differential_diagnosis_clues": [
            "Key distinguisher: GI prodrome → respiratory collapse pattern (vs. influenza which begins respiratory)",
            "Haemoconcentration + thrombocytopenia + immunoblasts = PATHOGNOMONIC triad for HPS",
            "Travel to rural Americas (Argentina, Chile, Uruguay, SW USA) + rodent exposure = HPS until proven otherwise",
            "No lymphadenopathy, no rash (distinguishes from dengue, rickettsial diseases)",
            "CXR bilateral infiltrates WITHOUT cardiomegaly (unlike cardiogenic pulmonary oedema)",
            "Echocardiogram: Low EF with normal valve function (distinguishes from bacterial endocarditis)",
            "Dengue: rash + retro-orbital pain + positive NS1; HPS: no rash",
            "Malaria: ring forms on blood film; HPS: immunoblasts on blood film",
            "Leptospirosis: jaundice + conjunctival suffusion + renal failure prominent; HPS: pulmonary dominant",
        ],
        "epidemiology": {
            "global_incidence": "Americas only: ~200–300 confirmed cases/year (USA ~30/year; Argentina/Chile ~100/year combined)",
            "mortality_rate": "30–40% (without ECMO); ~20% (with ECMO)",
            "affected_regions": [
                "Argentina (Andes/Patagonia — highest incidence globally)",
                "Chile (Andes regions)",
                "Uruguay", "Brazil", "Bolivia", "Paraguay",
                "United States (SW states: New Mexico, Colorado, Arizona, Utah)",
                "Canada (Saskatchewan, Manitoba)",
            ],
            "high_risk_groups": [
                "Farmers and agricultural workers",
                "Rural residents near rodent habitats",
                "Campers and hikers in endemic areas",
                "Military personnel in training exercises",
                "Construction workers disturbing rodent burrows",
                "Travel returnees from rural South America",
            ],
            "seasonal_pattern": "Spring-summer peak (rodent activity highest; human outdoor exposure)",
            "outbreak_status": "Endemic — seasonal cases in Americas. No person-to-person epidemic risk except Andes strain.",
        },
        "prevention": [
            "Avoid rodent habitats — seal holes, use rodent-proof storage",
            "Use N95 respirator when cleaning rodent-infested areas",
            "Wet-clean contaminated areas with bleach (do NOT dry sweep — aerosolises virus)",
            "Wear gloves when handling potentially contaminated materials",
            "No approved vaccine (IHNV and other candidates in trials)",
            "Rodent control programmes in endemic rural communities",
            "Pre-travel briefing for visitors to endemic rural areas",
        ],
        "public_health_measures": [
            "Mandatory notifiable disease — report to state/national public health authority within 24h",
            "Contact trace for Andes strain (person-to-person transmission documented)",
            "Strict droplet + contact isolation for Andes strain cases",
            "Public health alert if cluster cases identified (possible person-to-person cluster)",
            "Environmental investigation — identify rodent species and exposure source",
            "Community rodent control programme in affected area",
        ],
        "special_populations": [
            {
                "population": "Pregnant Women",
                "warning": "Limited data. Case reports of maternal death and fetal loss. Mechanical ventilation and ECMO feasible but high risk.",
                "recommendation": "Multidisciplinary team: Infectious Disease + Obstetrics + Pulmonology/Critical Care. Early ECMO consideration."
            },
            {
                "population": "Immunocompromised",
                "warning": "Higher viral loads, atypical presentation, reduced antibody response (serology may be falsely negative).",
                "recommendation": "Lower threshold for PCR testing. Rely on PCR not serology. Early aggressive supportive care."
            },
            {
                "population": "Elderly (>65y)",
                "warning": "Pre-existing cardiopulmonary disease worsens prognosis significantly. ECMO risk-benefit must be carefully assessed.",
                "recommendation": "Early ICU and cardiology involvement. Echo-guided ECMO decision."
            },
            {
                "population": "International Travellers",
                "warning": "May present to non-endemic regions where HPS is not on the differential. Travel history is the KEY diagnostic clue.",
                "recommendation": "Ask specifically about rural/agricultural exposure in the Americas. Notify infectious disease consultant immediately."
            },
        ],
        "citations": [],
        "data_sources": [
            "CDC — Hantavirus Pulmonary Syndrome Clinical Guidance (2024)",
            "Duchin JS et al., NEJM 1994 — Original HPS description",
            "Wells RM et al., Science 1997 — Andes person-to-person transmission",
            "Mertz GJ et al., JID 2004 — Ribavirin no benefit trial",
            "ARDS Network — Low tidal volume ventilation trial",
            "WHO — Technical Report on Rodent-Borne Diseases",
            "PAHO — Andes Hantavirus regional guidance",
        ],
    },

    "andes orthohantavirus (hps)": None,  # Resolved below
    "andes hantavirus": None,

    # ─── WEST NILE NEUROINVASIVE DISEASE ─────────────────────────────────────
    "west nile neuroinvasive disease": {
        "disease_name": "West Nile Neuroinvasive Disease (WNND)",
        "disease_class": "Viral Neuroinvasive Disease — Flavivirus (West Nile Virus, Lineage 1 & 2)",
        "icd11_code": "1D2A",
        "who_classification": "Arboviral Neurological Disease — Notifiable",
        "is_notifiable": True,
        "is_outbreak_active": True,
        "incubation_period": "2–14 days (typically 5–10 days)",
        "summary": (
            "West Nile Neuroinvasive Disease (WNND) is the most severe manifestation of West Nile Virus (WNV) infection, "
            "occurring in approximately 1% of infected individuals. WNV is a flavivirus (family Flaviviridae) transmitted "
            "by Culex mosquitoes, with birds as the amplifying host reservoir. WNND encompasses three syndromes: "
            "West Nile meningitis, West Nile encephalitis (most severe), and West Nile acute flaccid paralysis. "
            "The virus is endemic across Africa, Europe, the Middle East, Central Asia, and the Americas. "
            "Europe has experienced significant outbreaks since 2018 — particularly Italy, Greece, Serbia, Croatia, "
            "France, and the Balkans — predominantly due to Lineage 2 strains. "
            "Risk factors for neuroinvasive disease include age ≥50, immunocompromise, diabetes, hypertension, and male sex. "
            "There is no licensed specific antiviral; treatment is supportive. Mortality in WNND: 10–15%; "
            "50–75% of survivors experience persistent neurological deficits. "
            "THIS IS A NOTIFIABLE DISEASE — report to public health immediately upon clinical suspicion."
        ),
        "pathophysiology": (
            "WNV enters via Culex mosquito bite; initial replication occurs in dermal dendritic cells and skin Langerhans cells. "
            "Virus drains to regional lymph nodes → primary viraemia → spread to visceral organs (liver, spleen, kidney). "
            "Secondary viraemia occurs 2–5 days post-infection. CNS invasion occurs via: (1) blood-brain barrier (BBB) transcytosis "
            "across endothelium; (2) retrograde axonal transport along olfactory neurones and peripheral nerves; "
            "(3) BBB disruption by WNV-induced neuroinflammation (TNF-α, IL-6, IL-1β). "
            "In the CNS: WNV preferentially infects neurons (particularly in brainstem, deep grey matter, anterior horn cells), "
            "causing direct viral cytopathic effect + T-cell-mediated immunopathology. "
            "Anterior horn cell tropism → flaccid paralysis (WN poliomyelitis-like syndrome). "
            "Thalamus, basal ganglia, brainstem are the most commonly affected regions on MRI."
        ),
        "etiology": (
            "West Nile Virus (Flaviviridae, Flavivirus). "
            "Principal vector: Culex mosquitoes (Cx. pipiens, Cx. modestus, Cx. quinquefasciatus). "
            "Amplifying host: birds (corvids — crows/jays are sentinel species). "
            "Dead-end hosts: humans, horses, other mammals. "
            "Endemic in Europe: Italy (Po Valley), Greece, Balkans, France (Camargue), Spain, Portugal, Romania, Hungary, Serbia, Croatia. "
            "Seasonal: peak transmission July–October (Northern Hemisphere). "
            "Lineage 2 now dominant in Europe — as neurovirulent as Lineage 1. "
            "Blood transfusion, organ transplantation, breastfeeding, and transplacental transmission are rare routes."
        ),
        "cardinal_symptoms": [
            "Abrupt high fever with severe headache",
            "Neck stiffness (meningismus) — hallmark of CNS involvement",
            "Altered consciousness / confusion (encephalopathy)",
            "Neurological deficits: tremor, ataxia, extrapyramidal signs",
            "Acute flaccid paralysis (anterior horn cell involvement)",
            "Photophobia / phonophobia",
        ],
        "symptoms": [
            "Abrupt fever (typically >38.5°C)",
            "Severe frontal/occipital headache",
            "Profound fatigue and malaise",
            "Generalised myalgia",
            "Nausea and vomiting",
            "Loss of appetite",
            "Neck stiffness (nuchal rigidity)",
            "Photophobia and phonophobia",
            "Confusion and disorientation",
            "Altered level of consciousness (drowsiness → stupor → coma)",
            "Tremor and movement disorder (extrapyramidal signs — basal ganglia involvement)",
            "Ataxia and gait disturbance",
            "Focal neurological deficits",
            "Acute flaccid paralysis (WN poliomyelitis — asymmetric, areflexic)",
            "Cranial nerve palsies (VII, IX, X involvement — brainstem encephalitis)",
            "Seizures (in severe encephalitis)",
            "Diplopia or visual disturbance",
            "Dysphagia / dysarthria (brainstem involvement)",
            "Maculopapular rash (30–50% — trunk and extremities; spares palms/soles)",
            "Lymphadenopathy",
        ],
        "signs_on_examination": [
            "High fever (38–40°C)",
            "Nuchal rigidity — positive Kernig's and Brudzinski's signs",
            "Altered GCS (confusion, drowsiness)",
            "Extrapyramidal signs: cogwheel rigidity, bradykinesia, rest tremor",
            "Cerebellar ataxia — finger-nose dysmetria, tandem gait failure",
            "Acute flaccid paralysis (asymmetric, pure motor, areflexic) — mimics Guillain-Barré",
            "Cranial nerve palsies",
            "Maculopapular rash (trunk-predominant, non-pruritic)",
            "Relative bradycardia (characteristic for arboviral encephalitis)",
            "Lymphadenopathy (cervical, inguinal)",
            "Papilloedema (raised ICP — in severe encephalitis)",
        ],
        "red_flags": [
            "GCS <13 — acute encephalitis requiring ICU admission",
            "Seizures (new-onset in febrile encephalitis)",
            "Acute flaccid paralysis — rapid respiratory muscle involvement possible",
            "Progressive deterioration within 24–48 hours despite supportive care",
            "Respiratory failure (respiratory muscle or brainstem involvement)",
            "Status epilepticus",
            "Signs of raised intracranial pressure: papilloedema, Cushing's triad",
            "Immunocompromised patient — higher risk of fulminant disease",
        ],
        "disease_stages": [
            "Stage 1 — Viraemic phase (Days 1–5): Fever, headache, myalgia, fatigue, rash. Non-specific febrile illness. Most patients recover here.",
            "Stage 2 — Neuroinvasion phase (Days 5–10): CNS involvement begins — meningismus, photophobia, confusion. Encephalitis or meningitis syndrome.",
            "Stage 3 — Neurological plateau (Days 7–14): Maximal neurological deficit. Encephalitis, flaccid paralysis, movement disorder, coma in severe cases.",
            "Stage 4 — Recovery or deterioration (Weeks 2–6): Slow recovery (weeks–months). Sequelae: memory impairment, fatigue, depression, motor deficits in 50–75%.",
        ],
        "prognosis": (
            "WNND case fatality rate: 10–15% overall; higher in immunocompromised (up to 30–40%) and elderly. "
            "50–75% of WNND survivors have persistent neurological deficits at 1 year: fatigue, memory impairment, "
            "depression, tremor, gait disturbance. "
            "Acute flaccid paralysis (WN poliomyelitis) — poor recovery; most patients have permanent limb weakness. "
            "Younger, immunocompetent patients with WN meningitis alone have better prognosis. "
            "Recovery from encephalitis is slow — months to years. "
            "Prognostic factors: age >50, high viral load, acute flaccid paralysis, diabetes, immunosuppression predict poor outcome."
        ),
        "complications": [
            "Acute flaccid paralysis (WN poliomyelitis) — permanent in most cases",
            "Prolonged encephalopathy — cognitive decline",
            "Memory impairment and executive dysfunction (frontal lobe involvement)",
            "Movement disorder — parkinsonism-like (basal ganglia)",
            "Post-WNV fatigue syndrome (months to years)",
            "Aspiration pneumonia (dysphagia from cranial nerve involvement)",
            "Ventilator-dependent respiratory failure (respiratory muscle paralysis)",
            "Status epilepticus",
            "Raised intracranial pressure — cerebral herniation",
            "Secondary bacterial meningitis (super-infection)",
            "Depression and PTSD (post-encephalitis psychiatric sequelae)",
            "Myocarditis (rare)",
            "Hepatitis (rare)",
            "Rhabdomyolysis",
        ],
        "investigations": [
            "URGENT: WNV IgM antibody in CSF — diagnostic of WNV neuroinvasive disease (most sensitive test; positive from day 7–8 of symptoms)",
            "URGENT: WNV IgM + IgG serology (serum) — paired acute/convalescent samples (PRNT confirmation)",
            "URGENT: WNV RT-PCR (serum + CSF) — highest yield in first 7 days of illness (often negative after day 8)",
            "URGENT: CSF analysis: lymphocytic pleocytosis (10–500 WBC/μL, predominantly lymphocytes), elevated protein (0.5–2 g/L), normal glucose — aseptic meningitis pattern",
            "URGENT: MRI brain with contrast — characteristic signal in thalami, basal ganglia, brainstem, anterior horn cells (FLAIR/T2 hyperintensity)",
            "CT brain (non-contrast FIRST if MRI unavailable or to exclude mass lesion before LP)",
            "FBC: lymphopaenia + thrombocytopaenia (common in WNV)",
            "Metabolic panel: LFTs (transaminitis common), U&E, creatinine",
            "CRP, ESR, Procalcitonin (usually mildly elevated; high procalcitonin raises bacterial co-infection concern)",
            "Blood cultures × 2 (exclude bacterial meningitis/sepsis)",
            "Malaria thick/thin film + RDT (exclude malaria in returning traveller with fever and neurological symptoms)",
            "Dengue NS1 Ag + IgM/IgG (travel history — southern Europe dengue cases increasing since 2023)",
            "Viral meningitis PCR panel (CSF): HSV-1/2, EBV, CMV, Enterovirus (exclude other viral encephalitides)",
            "Anti-NMDAR antibody panel (CSF + serum) — exclude autoimmune encephalitis",
            "EEG: diffuse slowing (encephalitis); focal slow-wave activity or seizure activity",
            "EMG/NCS: if acute flaccid paralysis — confirm anterior horn cell vs Guillain-Barré pattern",
            "Urinalysis + microscopy (viral nephropathy)",
            "Chest X-ray (aspiration pneumonia surveillance)",
            "12-lead ECG (myocarditis screen)",
            "Mosquito exposure documentation and entomological report (public health)",
        ],
        "differential_diagnosis_clues": [
            "Travel to southern Europe + mosquito exposure + neurological fever → WNV/Toscana/TBE before HSV",
            "Extrapyramidal signs (tremor, rigidity) in arboviral encephalitis = STRONG WNV clue (basal ganglia/thalamic tropism)",
            "Acute flaccid areflexic paralysis in WNV = anterior horn cell (not GBS — pure motor, proximal, asymmetric)",
            "CSF lymphocytic pleocytosis + elevated protein + normal glucose = aseptic meningoencephalitis (viral not bacterial)",
            "Toscana virus (Tuscany, Italy): CSF identical but summer sandfly exposure (not mosquito); self-limiting",
            "TBE: tick bite history; biphasic illness (flu-like then neurological); Central/Eastern Europe, Scandinavia",
            "HSV encephalitis: temporal lobe predilection on MRI, rapid deterioration, cowdry bodies, fever + behaviour change",
            "Bacterial meningitis: very high neutrophilic pleocytosis, low CSF glucose, high protein, positive Gram stain",
            "Autoimmune encephalitis (anti-NMDAR): subacute onset, psychiatric prodrome, young females, CSF often mild",
        ],
        "first_line_treatment": (
            "No licensed specific antiviral exists. Supportive care is the cornerstone. "
            "Immediate ICU or high-dependency admission for WNND. "
            "IV fluid resuscitation, electrolyte correction, antipyretics. "
            "Anti-seizure medication for seizures. Physiotherapy for motor rehabilitation."
        ),
        "treatments": [
            "ICU/HDU admission — WNND requires close monitoring for neurological deterioration",
            "Supportive IV fluid therapy — maintain adequate hydration and electrolyte balance",
            "Antipyretics: paracetamol IV/oral (avoid NSAIDs in thrombocytopaenia)",
            "Anti-seizure drugs: levetiracetam IV (first-line) or phenytoin if seizures occur",
            "NO proven specific antiviral: ribavirin, interferon-α, IVIG — studied, not shown to improve outcomes",
            "IVIG (intravenous immunoglobulin): considered in immunocompromised with severe WNND (case series evidence only)",
            "WNV-specific IVIG (Omr-IgG-am): compassionate use in Israel — some case reports of benefit",
            "Dexamethasone: NO evidence of benefit; not routinely recommended for WNV encephalitis",
            "Anticoagulation: DVT prophylaxis in immobile patients",
            "Ventilatory support: non-invasive then invasive ventilation for respiratory muscle paralysis",
            "Nasogastric/PEG feeding: for prolonged encephalopathy or dysphagia",
            "Physiotherapy + occupational therapy: early mobilisation and rehabilitation",
            "Neuropsychological support: for cognitive sequelae in recovery phase",
            "Notifiable disease — report to state health department/IDSP/WHO",
        ],
        "monitoring_parameters": [
            "GCS hourly initially — any deterioration triggers ICU escalation",
            "Pupillary responses — signs of raised ICP",
            "Vital signs 4-hourly: temperature, HR, BP, RR, SpO2",
            "CSF analysis: repeat LP if clinical deterioration (consider bacterial superinfection)",
            "Serial FBC: lymphopaenia, thrombocytopaenia",
            "Metabolic panel: LFTs, electrolytes, creatinine",
            "WNV IgG titres: rising IgG confirms seroconversion (convalescent sample at 2–4 weeks)",
            "EEG monitoring for subclinical seizures in encephalopathic patients",
            "Respiratory function: peak flow, spirometry — if peripheral muscle weakness",
            "Bladder function (urinary retention common in WN poliomyelitis)",
        ],
        "prevention": [
            "No licensed human WNV vaccine (equine vaccine exists — Recombitek)",
            "Mosquito bite prevention: DEET-based repellents (≥20% DEET), permethrin-treated clothing",
            "Wear long sleeves/trousers outdoors from dusk to dawn in endemic regions",
            "Use bed nets in highly endemic areas",
            "Blood donation deferral: 28 days after travel to WNV-endemic areas",
            "Blood supply screening for WNV by RT-PCR in endemic countries",
            "Organ transplant screening: WNV RT-PCR prior to procurement in endemic seasons",
            "Public health: mosquito larviciding, surveillance of sentinel birds (crow die-offs)",
        ],
        "public_health_measures": [
            "MANDATORY NOTIFICATION to state public health authority (IDSP in India / ECDC in Europe) within 24 hours",
            "Blood and organ donation contraindicated for at least 28 days after illness",
            "Healthcare worker PPE: standard precautions only (no person-to-person transmission via normal contact)",
            "Entomological investigation: identify Culex breeding sites near exposure location",
            "Case report to WHO via national authorities",
            "Contact tracing: identify other travellers from same group (epidemiological cluster)",
        ],
        "epidemiology": {
            "global_incidence": "~7,000 neuroinvasive cases per year globally (likely significant underreporting). Europe: 1,000–3,000 cases/year during outbreak years",
            "mortality_rate": "10–15% in WNND; up to 30–40% in elderly/immunocompromised with encephalitis",
            "affected_regions": ["Europe (Italy, Greece, Balkans, France, Romania, Hungary, Serbia, Spain, Portugal)", "USA (all states)", "Middle East", "Africa", "Central Asia", "Australia (Kunjin lineage)"],
            "outbreak_status": "ACTIVE — Increased WNV neuroinvasive cases in southern Europe (Italy, Greece, Balkans) from 2018 onwards, with transmission season extending due to climate change",
            "seasonal_pattern": "Summer–early autumn (July–October in Northern Hemisphere). Peaks during warm, wet periods with high Culex mosquito density.",
            "high_risk_groups": ["Age >50 years", "Immunocompromised (HIV, transplant, chemotherapy)", "Diabetes mellitus", "Hypertension", "Male sex", "Occupational outdoor exposure", "Blood/organ transplant recipients"],
        },
        "special_populations": [
            {
                "population": "Immunocompromised",
                "warning": "Significantly higher risk of WNND (30–40× increased risk). Higher viral load. Serology may be negative (impaired antibody production — check WNV PCR in blood and CSF). Mortality up to 30–40%.",
                "recommendation": "Lower threshold for LP and neuroimaging. Check WNV RT-PCR (not just serology). Consider IVIG compassionate use. Involve infectious disease and transplant teams early.",
            },
            {
                "population": "Elderly (>65 years)",
                "warning": "Disproportionate risk of severe WNND and death. Neurological recovery is slower and less complete. Higher rate of persistent cognitive deficits.",
                "recommendation": "Early ICU admission, aggressive supportive care, and early involvement of neurology/geriatrics.",
            },
            {
                "population": "Pregnancy",
                "warning": "WNV can cross the placenta causing fetal infection. Reports of fetal brain injury and neonatal WNV. Vertical transmission rate unknown but documented.",
                "recommendation": "Urgent maternal-fetal medicine consultation. Fetal ultrasound for CNS anomalies. Neonatal WNV serology and CSF PCR if maternal WNND confirmed.",
            },
            {
                "population": "Pediatric",
                "warning": "Children more likely to have WN fever than WNND. When encephalitis occurs, extrapyramidal features and flaccid paralysis may be presenting signs.",
                "recommendation": "Paediatric infectious disease and neurology consultation. CSF analysis, MRI, and EEG.",
            },
        ],
        "data_sources": [
            "CDC — West Nile Virus Neuroinvasive Disease Surveillance and Clinical Guidance (2024)",
            "ECDC — West Nile Virus Season 2023–2024 Epidemiological Update",
            "WHO — West Nile Virus Fact Sheet (2023)",
            "Tyler KL, NEJM 2009 — West Nile Virus and other arboviral encephalitides (review)",
            "Sejvar JJ et al., Ann Neurol 2003 — WNV neurological disease spectrum",
            "Cho H & Diamond MS, Viruses 2012 — Mechanisms of WNV pathogenesis",
            "ICD-11 Foundation — 1D2A West Nile Fever with neurological complications",
        ],
    },

    # ─── TOSCANA VIRUS MENINGOENCEPHALITIS ───────────────────────────────────
    "toscana virus": {
        "disease_name": "Toscana Virus Meningoencephalitis",
        "disease_class": "Arboviral Neurological Disease — Phlebovirus (Sandfly-borne)",
        "icd11_code": "1D2F",
        "who_classification": "Sandfly-borne Neurological Disease — Southern Europe",
        "is_notifiable": True,
        "is_outbreak_active": False,
        "incubation_period": "3–7 days",
        "summary": (
            "Toscana Virus (TOSV) is a Phlebovirus (family Phenuiviridae) transmitted by Phlebotomus sandflies "
            "in Mediterranean Europe — particularly central Italy (Tuscany, Umbria, Lazio), Spain, Portugal, France, "
            "and the Balkans. TOSV is a LEADING cause of aseptic meningitis and meningoencephalitis in southern Europe "
            "during the warm season (May–October), accounting for up to 80% of viral CNS infections in some Italian series. "
            "Unlike West Nile Virus (mosquito-borne), TOSV is transmitted by sandfly bites — patients may not recall a "
            "prominent insect bite but will have been outdoors in hot, dry, rural/agricultural areas at dusk. "
            "Most cases are self-limiting (10–14 days) but 5–10% develop encephalitis requiring ICU care. "
            "No specific antiviral; supportive treatment."
        ),
        "pathophysiology": (
            "TOSV enters via sandfly (Phlebotomus perniciosus, P. perfiliewi) saliva injection. "
            "Initial replication in dermis and regional lymph nodes. Viraemia allows CNS penetration. "
            "CNS tropism: leptomeninges and brain parenchyma — causing lymphocytic meningitis and encephalitis. "
            "Immune response: CSF lymphocytosis (100–1000 cells/μL), elevated protein. "
            "Most patients clear infection within 2 weeks without specific treatment."
        ),
        "etiology": (
            "Toscana Virus (Phlebovirus, Phenuiviridae). "
            "Vector: Phlebotomus sandflies — most active at dusk/night; stay low to ground. "
            "Endemic regions: Italy (Tuscany, Umbria, Lazio, Emilia-Romagna), Spain (Andalusia, Catalonia), "
            "Portugal, France (Provence), Greece, Cyprus, Croatia, Turkey, North Africa. "
            "Season: May–October (sandfly season). No reservoir animal host — sandfly is both vector and reservoir. "
            "Key exposure: rural areas, stone walls, rocky terrain (sandfly habitat), outdoor evenings in summer."
        ),
        "cardinal_symptoms": [
            "Acute fever (38–40°C) — abrupt onset",
            "Severe headache (frontal/occipital)",
            "Neck stiffness (meningismus)",
            "Photophobia and phonophobia",
            "Profound fatigue and malaise",
        ],
        "symptoms": [
            "Abrupt fever (38–40°C)", "Severe headache", "Neck stiffness (nuchal rigidity)",
            "Photophobia", "Phonophobia", "Profound fatigue",
            "Nausea and vomiting", "Myalgia", "Arthralgia",
            "Confusion (in encephalitis cases)", "Cerebellar ataxia (encephalitis)",
            "Cranial nerve palsies (rare)", "Seizures (rare, in encephalitis)",
            "Altered consciousness (encephalitis — 5–10%)",
            "Retroorbital pain", "Anorexia",
        ],
        "signs_on_examination": [
            "Fever", "Nuchal rigidity", "Positive Kernig's sign", "Positive Brudzinski's sign",
            "Photophobia (bright light sensitivity)", "Altered GCS (in encephalitis cases)",
            "Cerebellar signs (ataxia, nystagmus) — if encephalitis", "Generally preserved consciousness in most",
        ],
        "red_flags": [
            "Altered consciousness / GCS <14 (encephalitis, not meningitis)",
            "Seizures",
            "Focal neurological deficits",
            "Failure to improve after 5–7 days",
            "Immunocompromised patient (may have severe prolonged disease)",
        ],
        "investigations": [
            "TOSV-specific IgM/IgG serology (ELISA) — available at reference laboratories; positive from ~day 5–7",
            "TOSV RT-PCR (CSF and/or serum) — highest yield in first 5 days",
            "CSF analysis: lymphocytic pleocytosis (100–500 cells, predominantly lymphocytes), elevated protein, normal glucose",
            "MRI brain: usually normal in meningitis; focal signal changes in encephalitis cases (frontal/temporal)",
            "WNV IgM/IgG serology — must co-test (same season, same region, different vector)",
            "FBC: leucocyte count usually normal or mildly elevated; lymphopaenia early",
            "Metabolic panel: LFTs, U&E",
            "HSV-1/2 PCR (CSF) — most important differential (clinically indistinguishable)",
            "Enterovirus PCR (CSF) — exclude enteroviral meningitis",
            "Blood cultures × 2 (exclude bacterial meningitis)",
            "Dengue serology (returning travellers)",
            "EEG (if encephalitis suspected)",
            "CT head prior to LP (mass lesion exclusion)",
        ],
        "first_line_treatment": "Supportive care. Hospitalise for pain management, IV fluids, and close neurological monitoring. Usually self-limiting in 10–14 days.",
        "treatments": [
            "Supportive: IV fluid therapy, antipyretics (paracetamol), analgesia",
            "Analgesics for headache (paracetamol ± low-dose opiate)",
            "Anti-emetics for nausea (ondansetron, metoclopramide)",
            "Bed rest in dark, quiet environment (photophobia management)",
            "No proven specific antiviral (ribavirin has in-vitro activity but no clinical evidence for TOSV)",
            "Anti-seizure drugs if seizures occur (levetiracetam preferred)",
            "Dexamethasone: NOT recommended (no evidence for viral meningitis)",
            "ICU for encephalitis cases",
        ],
        "prognosis": (
            "Excellent for isolated viral meningitis: full recovery in 10–14 days in >90% of cases. "
            "Persistent headache and fatigue may last 4–6 weeks. "
            "Encephalitis cases (5–10%): slower recovery, occasional persistent neurological deficits. "
            "Very rare fatalities (<0.5%). Immunocompromised patients have more severe/prolonged course."
        ),
        "differential_diagnosis_clues": [
            "Travel to SOUTHERN EUROPE in summer + outdoor evening exposure + meningoencephalitis → TOSV is most likely diagnosis before HSV",
            "TOSV is leading cause of viral meningitis in Mediterranean summer — outranks enteroviruses in some series",
            "CSF: lymphocytic meningitis with normal glucose — TOSV, WNV, HSV, enterovirus, TBE are all possible",
            "No rash (unlike dengue, enteroviruses); no haemorrhagic features (unlike WNV occasionally)",
            "WNV: more likely extrapyramidal signs, flaccid paralysis, more severe encephalitis",
            "TBE: tick bite (not sandfly), biphasic illness, Central/Eastern European travel",
        ],
        "epidemiology": {
            "global_incidence": "Estimated thousands of cases annually in Mediterranean Europe (significant underdiagnosis due to limited testing)",
            "mortality_rate": "<1% in immunocompetent; higher in encephalitis and immunocompromised",
            "affected_regions": ["Italy (Tuscany, Umbria, Lazio, Emilia-Romagna)", "Spain", "Portugal", "France (Provence)", "Greece", "Cyprus", "Croatia", "Turkey", "North Africa"],
            "outbreak_status": "Endemic seasonal pattern — peak cases May–October annually",
            "seasonal_pattern": "May–October — correlates with sandfly (Phlebotomus) activity",
            "high_risk_groups": ["Travellers to rural Mediterranean areas in summer", "Outdoor workers", "Campers/hikers in southern Europe", "Immunocompromised"],
        },
        "prevention": [
            "Fine-mesh sandfly nets (mesh size <1mm — smaller than mosquito nets required)",
            "DEET repellents (>20% DEET) — effective against sandflies",
            "Avoid outdoor activity at dusk in sandy/rocky terrain",
            "Light-coloured clothing covering limbs at dawn/dusk",
            "Environmental control: permethrin spraying in endemic areas",
            "No vaccine available",
        ],
        "public_health_measures": [
            "Report to public health as part of viral encephalitis/meningitis surveillance",
            "Travel medicine alert for Mediterranean travellers in summer months",
            "Entomological investigation to confirm sandfly exposure",
        ],
        "data_sources": [
            "Charrel RN et al., Clin Infect Dis 2012 — Toscana virus: emerging threat in Mediterranean Europe",
            "Valassina M et al., Emerg Infect Dis 2003 — TOSV as leading cause of aseptic meningitis in Italy",
            "Baldelli F et al., Eur J Epidemiol 2004 — Seroprevalence of TOSV in central Italy",
            "ECDC — Toscana Virus Disease Factsheet",
            "WHO Mediterranean Communicable Disease Surveillance Network",
        ],
    },

    # ─── TICK-BORNE ENCEPHALITIS (TBE) ────────────────────────────────────────
    "tick-borne encephalitis": {
        "disease_name": "Tick-Borne Encephalitis (TBE)",
        "disease_class": "Arboviral Neurological Disease — Flavivirus (TBE Virus, 3 subtypes)",
        "icd11_code": "1D2B",
        "who_classification": "Arthropod-borne Viral Encephalitis — Notifiable (Endemic Europe/Asia)",
        "is_notifiable": True,
        "is_outbreak_active": False,
        "incubation_period": "7–14 days (range 4–28 days)",
        "summary": (
            "Tick-Borne Encephalitis (TBE) is caused by TBE Virus (TBEV, Flaviviridae), transmitted by Ixodes ticks "
            "(I. ricinus in Europe; I. persulcatus in Russia/Asia). Three subtypes: European (least severe), "
            "Siberian, and Far Eastern (most severe). TBE is ENDEMIC across Central and Eastern Europe, Scandinavia, "
            "Russia, and parts of Asia — with approximately 10,000–12,000 confirmed cases annually (significant underreporting). "
            "HALLMARK: BIPHASIC ILLNESS — Phase 1: flu-like illness (4–7 days) → remission (1–20 days) → "
            "Phase 2: neurological illness (meningitis, encephalitis, myelitis) in ~35% of symptomatic patients. "
            "An effective vaccine exists (FSME-Immun/Encepur). Early tick removal reduces risk."
        ),
        "pathophysiology": (
            "TBEV is injected via Ixodes tick saliva during blood meal (transmission occurs within hours of tick attachment). "
            "Initial replication in skin and subcutaneous tissue. Phase 1: viraemia → systemic symptoms. "
            "Phase 2: CNS invasion via blood-brain barrier (BBB) transcytosis and direct neuronal infection. "
            "CNS: predilection for cerebellum, brainstem, basal ganglia, spinal anterior horn cells. "
            "Pathological findings: lymphocytic perivascular infiltration, neuronophagia, gliosis. "
            "Immune pathology contributes to neuronal damage alongside direct cytopathic effect."
        ),
        "etiology": (
            "TBE Virus (TBEV), Flavivirus. Vector: Ixodes ricinus (Europe), I. persulcatus (Russia, Asia). "
            "Endemic regions: Central Europe (Austria, Germany, Switzerland, Czech Republic, Slovakia, Hungary), "
            "Baltic States, Scandinavia (Sweden, Finland), Russia, Eastern Europe (Poland, Romania, Slovenia, Croatia). "
            "In southern Europe: foci in northern Italy, Balkans, Croatia, Slovenia. "
            "Season: April–November (tick season). Rare transmission via unpasteurised milk (goat, cow). "
            "Not all tick bites transmit TBE; infection rate varies by endemic area."
        ),
        "cardinal_symptoms": [
            "BIPHASIC illness — distinguishing feature",
            "Phase 1: flu-like (fever, headache, myalgia) followed by apparent recovery",
            "Phase 2: meningitis/encephalitis symptoms (neck stiffness, confusion, ataxia)",
            "Cerebellar ataxia (prominent in TBE encephalitis)",
            "Flaccid paralysis (spinal cord involvement — cervical predilection)",
        ],
        "symptoms": [
            "Phase 1: fever (38–40°C), headache, myalgia, fatigue, malaise, anorexia",
            "Phase 1: nausea, vomiting, photophobia",
            "Apparent remission (1–20 days, mean 8 days) — asymptomatic interval",
            "Phase 2 onset: fever recurrence, severe headache",
            "Neck stiffness (nuchal rigidity)", "Photophobia", "Phonophobia",
            "Cerebellar ataxia (tremor, dysmetria, gait instability) — hallmark",
            "Confusion and cognitive impairment", "Altered consciousness",
            "Upper limb flaccid paralysis (C-type TBE, cervical cord)",
            "Paralysis of shoulder girdle / arm elevation (brachial amyotrophy)",
            "Cranial nerve palsies (VII, XII — dysarthria, dysphagia)",
            "Seizures (in severe encephalitis)",
            "Tremor (intention tremor)", "Nystagmus",
        ],
        "signs_on_examination": [
            "Fever (Phase 2 — second temperature spike)",
            "Nuchal rigidity", "Kernig's and Brudzinski's positive",
            "Cerebellar signs: dysmetria, dysdiadochokinesia, tandem gait failure, truncal ataxia",
            "Flaccid upper limb weakness (anterior horn cell — cervical cord predilection)",
            "Nystagmus", "Intention tremor", "Dysarthria (slurred speech)",
            "Cranial nerve palsies", "Altered GCS in encephalitis",
        ],
        "red_flags": [
            "Rapid deterioration during Phase 2", "GCS <14",
            "Respiratory muscle weakness / diaphragm involvement",
            "Swallowing difficulty (brainstem/cranial nerve involvement — aspiration risk)",
            "Status epilepticus", "Flaccid paralysis progressing to respiratory muscles",
            "Far Eastern subtype: higher mortality, rapid encephalitis without biphasic pattern",
        ],
        "investigations": [
            "TBEV-specific IgM + IgG serology (serum) — positive by Phase 2 onset in >95%; IgM confirms acute infection",
            "TBEV IgM in CSF (reference lab) — if serology equivocal",
            "TBEV RT-PCR (serum) — only positive during Phase 1 viraemia; usually negative by Phase 2",
            "CSF analysis: lymphocytic pleocytosis (50–1000 cells), elevated protein, normal glucose",
            "MRI brain: bilateral thalamic, basal ganglia, cerebellar, brainstem, spinal cord signal changes (FLAIR/T2)",
            "CT brain (mass lesion exclusion before LP)",
            "FBC: leucocytosis (Phase 2); leucopaenia + thrombocytopaenia (Phase 1)",
            "Metabolic panel: LFTs, U&E",
            "WNV serology (co-test — flavivirus cross-reactivity; use PRNT for confirmation)",
            "HSV PCR (CSF) — most important rapidly fatal differential",
            "EEG: diffuse slowing, focal changes in encephalitis",
            "EMG/NCS: anterior horn cell pattern if flaccid paralysis (differentiate from GBS)",
            "Vaccination history: Has patient received TBE vaccine? (reduces severity, may alter serology)",
        ],
        "first_line_treatment": "No specific antiviral. Supportive care. Vaccination (post-exposure of unimmunised contacts with tick bite in endemic area — passive immunisation with FSME-Bulin HYPERIMMUN within 72–96h of tick bite).",
        "treatments": [
            "Supportive: IV fluids, antipyretics, analgesia",
            "Anti-seizure drugs for seizures (levetiracetam first-line)",
            "ICU for encephalitis/respiratory compromise",
            "TBE-specific hyperimmune immunoglobulin (TBE-HIIG/FSME-Bulin): only for post-exposure prophylaxis within 96h of tick bite — NOT beneficial once neurological phase established",
            "Mechanical ventilation for respiratory muscle paralysis",
            "Physiotherapy and rehabilitation — extensive, prolonged",
            "Corticosteroids: NOT recommended (may worsen outcome)",
            "Prevention: TBE vaccine (FSME-Immun, Encepur) — 3-dose primary course; highly effective (>95%)",
        ],
        "prognosis": (
            "European subtype: mortality <2%; sequelae in 30–50% (fatigue, headache, cognitive impairment, "
            "psychiatric symptoms, cerebellar dysfunction). "
            "Far Eastern subtype: mortality 5–20%; higher rate of severe encephalitis. "
            "Siberian subtype: chronic progressive encephalitis (rare). "
            "Cervical myelitis with flaccid arm paralysis: poor recovery (permanent in many). "
            "Recovery from encephalitis: months to years; elderly have poorer prognosis."
        ),
        "differential_diagnosis_clues": [
            "BIPHASIC illness with flu-like Phase 1 → apparent recovery → neurological Phase 2 = PATHOGNOMONIC for TBE",
            "Tick bite history (Central/Eastern Europe, Scandinavia, Russia, northern Italy, Croatia) + neurological fever",
            "Cerebellar ataxia is more prominent in TBE than WNV",
            "Flaccid upper limb paralysis with cervical cord involvement is characteristic of TBE (C-type)",
            "WNV: mosquito-borne, no biphasic pattern, basal ganglia/thalamic MRI changes, Mediterranean/Balkans focus",
            "TOSV: sandfly-borne, no biphasic pattern, usually milder, self-limiting, southern Europe (Italy, Spain)",
        ],
        "epidemiology": {
            "global_incidence": "~10,000–12,000 confirmed cases/year globally (significant underdiagnosis estimated 10–100× higher)",
            "mortality_rate": "<2% (European subtype); 5–20% (Far Eastern subtype)",
            "affected_regions": ["Central Europe (Austria, Germany, Switzerland, Czech Republic)", "Baltic States (Latvia, Estonia, Lithuania)", "Scandinavia (Sweden, Finland)", "Eastern Europe (Poland, Slovenia, Croatia, Hungary)", "Russia", "China", "Japan", "Northern Italy"],
            "outbreak_status": "Increasing cases in Central/Northern Europe due to climate change extending tick season and distribution",
            "seasonal_pattern": "April–November (tick season). Peaks in June–July and September–October (bimodal with human outdoor activity).",
            "high_risk_groups": ["Unvaccinated travellers to endemic areas", "Outdoor workers (farmers, forestry)", "Hikers, campers in endemic areas", "Elderly (more severe disease)", "Children (usually milder)"],
        },
        "prevention": [
            "TBE VACCINE — primary prevention (3-dose schedule: FSME-Immun or Encepur; booster every 3–5 years)",
            "Tick bite prevention: DEET repellents, permethrin clothing treatment",
            "Tick checks after outdoor activity (early removal reduces risk — transmission usually requires >12–24h attachment)",
            "Remove attached tick with fine forceps — twist and pull, no petroleum jelly",
            "Avoid unpasteurised milk in endemic areas",
            "Post-exposure prophylaxis: TBE hyperimmune Ig within 96h of tick bite (unvaccinated)",
        ],
        "public_health_measures": [
            "Notifiable disease in most European countries",
            "Report to ECDC/national surveillance system",
            "Entomological investigation in cluster cases",
            "Vaccination campaign for endemic area residents and travellers",
        ],
        "data_sources": [
            "ECDC — Tick-Borne Encephalitis Disease Fact Sheet (2024)",
            "WHO — Tick-Borne Encephalitis Fact Sheet (2022)",
            "Gritsun TS et al., Antiviral Res 2003 — TBE virus biology",
            "Kaiser R, J Neurol 2008 — Clinical course of TBE (500-patient series)",
            "Bogovic P & Strle F, World J Clin Cases 2015 — TBE clinical review",
            "ICD-11 Foundation — 1D2B Tick-borne encephalitis",
        ],
    },
}

# Wire aliases for all European neurotropic arboviruses
_DISEASE_STATIC_PROFILES["west nile encephalitis"] = _DISEASE_STATIC_PROFILES["west nile neuroinvasive disease"]
_DISEASE_STATIC_PROFILES["west nile virus neuroinvasive"] = _DISEASE_STATIC_PROFILES["west nile neuroinvasive disease"]
_DISEASE_STATIC_PROFILES["west nile fever"] = _DISEASE_STATIC_PROFILES["west nile neuroinvasive disease"]
_DISEASE_STATIC_PROFILES["west nile virus"] = _DISEASE_STATIC_PROFILES["west nile neuroinvasive disease"]
_DISEASE_STATIC_PROFILES["wnnd"] = _DISEASE_STATIC_PROFILES["west nile neuroinvasive disease"]
_DISEASE_STATIC_PROFILES["wnv encephalitis"] = _DISEASE_STATIC_PROFILES["west nile neuroinvasive disease"]
_DISEASE_STATIC_PROFILES["toscana virus meningoencephalitis"] = _DISEASE_STATIC_PROFILES["toscana virus"]
_DISEASE_STATIC_PROFILES["toscana"] = _DISEASE_STATIC_PROFILES["toscana virus"]
_DISEASE_STATIC_PROFILES["tosv"] = _DISEASE_STATIC_PROFILES["toscana virus"]
_DISEASE_STATIC_PROFILES["sandfly fever"] = _DISEASE_STATIC_PROFILES["toscana virus"]
_DISEASE_STATIC_PROFILES["tbe"] = _DISEASE_STATIC_PROFILES["tick-borne encephalitis"]
_DISEASE_STATIC_PROFILES["tick borne encephalitis"] = _DISEASE_STATIC_PROFILES["tick-borne encephalitis"]
_DISEASE_STATIC_PROFILES["central european encephalitis"] = _DISEASE_STATIC_PROFILES["tick-borne encephalitis"]


# Wire Andes strain to the same profile (with strain-specific override)
_HPS_ANDES_PROFILE = dict(_DISEASE_STATIC_PROFILES["hantavirus pulmonary syndrome"])
_HPS_ANDES_PROFILE.update({
    "disease_name": "Andes Orthohantavirus (HPS)",
    "disease_class": "Zoonotic Viral Disease — Andes Orthohantavirus (ANDV) — South America",
    "summary": (
        "Andes Orthohantavirus (ANDV) is the predominant hantavirus in South America (Argentina, Chile, Uruguay, Bolivia, Paraguay). "
        "It is the ONLY hantavirus species with documented human-to-human transmission (Wells RM, Science 1997; Padula PJ, Lancet 1998). "
        "CFR: 35–50% without ECMO. Clinical presentation: GI prodrome → cardiopulmonary collapse (ARDS + cardiogenic shock). "
        "Reservoir: Long-tailed Pygmy Rice Rat (Oligoryzomys longicaudatus) in Andes/Patagonia regions. "
        "STRICT DROPLET + CONTACT ISOLATION required. Early ECMO is the only intervention shown to improve survival."
    ),
    "etiology": (
        "Andes Orthohantavirus (ANDV). Reservoir: Oligoryzomys longicaudatus (Patagonian and Andean rodent). "
        "Endemic zones: Argentina (Patagonia, Mendoza, Neuquén, Río Negro provinces), Chile (Aysén, Araucanía), "
        "Uruguay, Bolivia, Paraguay. Transmission: rodent excreta aerosol inhalation AND person-to-person (unique among hantaviruses). "
        "Human-to-human: close contact with symptomatic case during cardiopulmonary phase."
    ),
    "public_health_measures": [
        "MANDATORY ISOLATION: Droplet + Contact precautions (unlike Sin Nombre virus — Andes can spread person-to-person)",
        "Report immediately to public health authority — notifiable in Argentina, Chile, Uruguay, Brazil",
        "Contact trace ALL close contacts of confirmed Andes HPS case — 35-day follow-up",
        "Healthcare workers: N95 + face shield + gown + gloves when caring for Andes HPS patients",
        "Environmental investigation: identify rodent species and exposure site",
        "Community rodent control in affected area",
    ],
})
_DISEASE_STATIC_PROFILES["andes orthohantavirus (hps)"] = _HPS_ANDES_PROFILE
_DISEASE_STATIC_PROFILES["andes hantavirus"] = _HPS_ANDES_PROFILE
_DISEASE_STATIC_PROFILES["andes virus disease"] = _HPS_ANDES_PROFILE


def _build_static_fallback(
    disease_name: str,
    dynamic_profile: dict | None = None,
    template_invs: list | None = None,
    incubation_data: tuple | None = None,
    disease_class: str = "",
) -> dict:
    """
    Build a comprehensive clinical intelligence response using ONLY static data.
    Used when LLM is unavailable, timed out, or circuit-breaker tripped.
    Priority: 1) get_disease_clinical_profile → 2) _DISEASE_STATIC_PROFILES → 3) DISEASE_KB → 4) dynamic_profile → 5) template
    """
    dn_lower = disease_name.lower().strip()

    # Priority 0: Comprehensive Clinical Disease Registry (44+ expert conditions + aliases)
    try:
        from app.services.clinical_disease_metadata import get_disease_clinical_profile
        reg_profile = get_disease_clinical_profile(disease_name)
        if reg_profile:
            p_dict = dict(reg_profile)
            d_intel = reg_profile.get("disease_intelligence") or {}

            # Map summary
            summary = (
                p_dict.get("summary")
                or d_intel.get("summary")
                or p_dict.get("treatment_summary")
                or p_dict.get("pearl")
                or d_intel.get("clinical_pearl")
                or f"{disease_name} — Comprehensive evidence-based clinical intelligence profile and diagnostic management protocol."
            )
            p_dict["summary"] = summary

            if not p_dict.get("pathophysiology"):
                p_dict["pathophysiology"] = d_intel.get("pathophysiology")
            if not p_dict.get("etiology"):
                p_dict["etiology"] = d_intel.get("etiology") or d_intel.get("transmission")
            if not p_dict.get("icd11_code"):
                p_dict["icd11_code"] = d_intel.get("icd11_code") or reg_profile.get("icd11")
            if not p_dict.get("cardinal_symptoms"):
                p_dict["cardinal_symptoms"] = d_intel.get("cardinal_symptoms") or []
            if not p_dict.get("symptoms"):
                p_dict["symptoms"] = d_intel.get("cardinal_symptoms") or []
            if not p_dict.get("red_flags"):
                p_dict["red_flags"] = d_intel.get("red_flags") or []
            if not p_dict.get("incubation_period"):
                p_dict["incubation_period"] = d_intel.get("incubation_period")
            if not p_dict.get("prognosis"):
                p_dict["prognosis"] = d_intel.get("clinical_pearl") or p_dict.get("pearl")
            if not p_dict.get("disease_class"):
                p_dict["disease_class"] = reg_profile.get("category") or disease_class

            # Map treatments
            if not p_dict.get("first_line_treatment"):
                p_dict["first_line_treatment"] = (
                    reg_profile.get("first_line_treatment")
                    or reg_profile.get("treatment_summary")
                    or (reg_profile.get("recommended_medications", [])[0] if reg_profile.get("recommended_medications") else "Guideline-directed clinical therapy")
                )

            if not p_dict.get("treatments"):
                txs = []
                if reg_profile.get("first_line_treatment"):
                    txs.append(reg_profile["first_line_treatment"])
                if reg_profile.get("treatment_summary"):
                    txs.append(reg_profile["treatment_summary"])
                if reg_profile.get("recommended_medications"):
                    txs.extend(reg_profile["recommended_medications"][:3])
                p_dict["treatments"] = txs or ["Supportive medical care and specialist evaluation"]

            if not p_dict.get("investigations"):
                p_dict["investigations"] = p_dict.get("recommended_investigations") or p_dict.get("immediate_tests") or []
            if not p_dict.get("medications"):
                p_dict["medications"] = p_dict.get("recommended_medications") or []
            return p_dict
    except Exception as e:
        log.warning("clinical_profile_registry_lookup_failed", error=str(e), disease=disease_name)

    # Priority 1: Expert-curated static profiles (Ebola, Marburg, Lassa, etc.)
    for key, profile in _DISEASE_STATIC_PROFILES.items():
        if key in dn_lower or dn_lower in key:
            p_dict = dict(profile)
            if not p_dict.get("first_line_treatment"):
                p_dict["first_line_treatment"] = (
                    p_dict.get("first_line_treatment")
                    or (p_dict.get("treatments", [])[0] if p_dict.get("treatments") else "Immediate supportive care and specialist evaluation")
                )
            if not p_dict.get("medications"):
                from app.services.medication_service import _get_offline_medications
                med_objs = _get_offline_medications(key)
                p_dict["medications"] = [f"{m.generic_name} ({m.standard_reference_dosing})" if getattr(m, 'standard_reference_dosing', None) else m.generic_name for m in med_objs]
            return p_dict

    # Priority 2: DISEASE_KB lookup
    from app.services.offline_disease_kb import DISEASE_KB
    kb_match = None
    for kb_name, kb_data in DISEASE_KB.items():
        if dn_lower in kb_name.lower() or kb_name.lower() in dn_lower:
            kb_match = kb_data
            break

    if kb_match:
        inv_base = [t.get("name", t) if isinstance(t, dict) else t for t in template_invs[:10]]
        if not inv_base:
            if kb_match.get("hemorrhagic"):
                inv_base = _VHF_INVESTIGATIONS[:8]
            else:
                inv_base = [
                    "Complete Blood Count (CBC) with Automated Differential",
                    "Comprehensive Metabolic Panel (Electrolytes, Renal & Liver Function)",
                    "Serum C-Reactive Protein (CRP) and ESR",
                    "Urinalysis with Microscopic Examination",
                    "Chest Radiograph (PA and Lateral Views)",
                    "12-Lead Electrocardiogram (ECG)",
                ]
        inc_min = kb_match.get("incubation_min", "?")
        inc_max = kb_match.get("incubation_max", "?")

        from app.services.medication_service import _get_offline_medications
        med_objs = _get_offline_medications(disease_name)
        med_strs = [f"{m.generic_name} ({m.standard_reference_dosing})" if getattr(m, 'standard_reference_dosing', None) else m.generic_name for m in med_objs]
        if not med_strs:
            med_strs = [f"Guideline-directed medical therapy for {disease_name}"]

        return {
            "summary": (
                f"{disease_name} — Clinical intelligence sourced from curated medical knowledge base. "
                f"Severity: {kb_match.get('severity', 'unknown')}. "
                f"Geographic distribution: {', '.join(kb_match.get('geographic_zones', ['worldwide']))}. "
                f"Incubation: {inc_min}–{inc_max} days."
            ),
            "pathophysiology": f"Classified as: {disease_class or kb_match.get('clusters', ['infectious disease'])[0]}",
            "etiology": f"Geographic exposure: {', '.join(kb_match.get('geographic_zones', ['worldwide']))}",
            "icd11_code": "",
            "who_classification": "",
            "disease_class": disease_class or ", ".join(kb_match.get("clusters", [])),
            "is_notifiable": kb_match.get("severity") == "critical",
            "is_outbreak_active": kb_match.get("is_outbreak_active", False),
            "incubation_period": f"{inc_min}–{inc_max} days",
            "cardinal_symptoms": kb_match.get("cardinal_symptoms", []),
            "symptoms": kb_match.get("symptoms", []),
            "signs_on_examination": [],
            "red_flags": ["Clinical deterioration", "Organ dysfunction", "Haemorrhage", "Altered consciousness"] if kb_match.get("hemorrhagic") else ["Rapid deterioration", "Signs of sepsis"],
            "disease_stages": [],
            "prognosis": f"Severity rating: {kb_match.get('severity', 'unknown')}. Consult specialist.",
            "complications": [],
            "first_line_treatment": "Consult specialist immediately. Supportive care and targeted pharmacotherapy.",
            "treatments": ["Specialist consultation", "Supportive care", "Isolation if indicated"],
            "medications": med_strs,
            "monitoring_parameters": ["Vital signs", "Fluid balance", "FBC", "Metabolic panel"],
            "investigations": inv_base,
            "differential_diagnosis_clues": [f"Distinguish from other conditions in: {', '.join(kb_match.get('clusters', ['febrile illness']))}"],
            "epidemiology": {
                "affected_regions": kb_match.get("geographic_zones", []),
                "high_risk_groups": [],
                "outbreak_status": "Unknown — check WHO/CDC for current status",
                "global_incidence": "Unknown",
                "mortality_rate": "Unknown",
                "seasonal_pattern": "Unknown",
            },
            "prevention": ["Standard infection control", "Travel precautions in endemic areas"],
            "public_health_measures": ["Notify public health if notifiable disease suspected"],
            "special_populations": [],
            "data_sources": ["DocAssistIQ Static KB", "WHO", "CDC"],
        }

    # Priority 3: dynamic profile
    if dynamic_profile and dynamic_profile.get("symptoms"):
        from app.services.medication_service import _get_offline_medications
        med_objs = _get_offline_medications(disease_name)
        med_strs = [f"{m.generic_name} ({m.standard_reference_dosing})" if getattr(m, 'standard_reference_dosing', None) else m.generic_name for m in med_objs]
        return {
            "summary": f"Clinical intelligence for {disease_name}. Compiled from dynamic medical knowledge.",
            "cardinal_symptoms": dynamic_profile.get("cardinal_symptoms", []),
            "symptoms": dynamic_profile.get("symptoms", []),
            "investigations": [t.get("name", t) if isinstance(t, dict) else t for t in template_invs[:10]] or [
                "Complete Blood Count (CBC) with Differential",
                "Comprehensive Metabolic Panel (CMP)",
                "Serum C-Reactive Protein (CRP)",
                "Urinalysis",
            ],
            "first_line_treatment": dynamic_profile.get("_treatment_summary", "Consult specialist."),
            "treatments": [dynamic_profile.get("_treatment_summary", "Supportive care.")],
            "medications": med_strs or [f"Guideline-directed therapy for {disease_name}"],
            "red_flags": ["Rapid deterioration", "Organ dysfunction"],
            "epidemiology": {"affected_regions": dynamic_profile.get("geographic_zones", []), "high_risk_groups": []},
            "is_notifiable": False, "is_outbreak_active": False,
            "data_sources": ["DocAssistIQ Dynamic KB"],
        }

    # Priority 4: minimal template with safe general investigations (NOT VHF tests!)
    from app.services.medication_service import _get_offline_medications
    med_objs = _get_offline_medications(disease_name)
    med_strs = [f"{m.generic_name} ({m.standard_reference_dosing})" if getattr(m, 'standard_reference_dosing', None) else m.generic_name for m in med_objs]
    return {
        "summary": f"Clinical intelligence for {disease_name}. Evidence-based diagnostic evaluation and supportive management.",
        "investigations": [t.get("name", t) if isinstance(t, dict) else t for t in template_invs[:10]] or [
            "Complete Blood Count (CBC) with Automated Differential",
            "Comprehensive Metabolic Panel (Electrolytes, Renal & Liver Function)",
            "Serum C-Reactive Protein (CRP) and ESR",
            "Urinalysis with Microscopic Examination",
            "12-Lead Electrocardiogram (ECG)",
        ],
        "cardinal_symptoms": [],
        "symptoms": [],
        "red_flags": ["Clinical deterioration", "Organ dysfunction", "Altered mental status"],
        "first_line_treatment": "Guideline-directed clinical therapy. Supportive care and specialist evaluation.",
        "treatments": ["Supportive medical care", "Specialist evaluation and targeted therapy"],
        "medications": med_strs or [f"Standard-of-care pharmacotherapy tailored to {disease_name}"],
        "epidemiology": {"affected_regions": [], "high_risk_groups": []},
        "is_notifiable": False, "is_outbreak_active": False,
        "data_sources": ["DocAssistIQ Clinical Guidelines"],
    }


async def generate_disease_intelligence(db: AsyncSession, disease_name: str) -> DiseaseIntelligenceResponse:
    """
    World-class disease intelligence generator (v3).
    Uses all available sources: RAG + Wikipedia + ICD-11 + PubMed + WHO/CDC + dynamic KB + Clinical Registry.
    Returns a comprehensive 20+ field profile suitable for specialist physicians with complete investigations & medications.
    """
    log.info("disease_intelligence_start", disease=disease_name)

    # 1. Run all data fetches in parallel with resilient timeouts
    from app.services.intelligence_engine import (
        intelligence_engine, INCUBATION_PERIODS, get_disease_class, get_investigation_template
    )
    from app.services.live_disease_scanner import on_demand_lookup

    rag_request = RAGQueryRequest(query=f"{disease_name} symptoms treatment pathophysiology epidemiology prognosis")

    async def _safe_fetch(coro, timeout_sec=2.0, default=None):
        try:
            return await asyncio.wait_for(coro, timeout=timeout_sec)
        except Exception as ex:
            log.debug("disease_intelligence_fetch_skipped", error=str(ex))
            return default

    # RAG tasks depend on DB; safe 1.5s timeout prevents blocking when DB is slow/offline
    intel_task = _safe_fetch(intelligence_engine.get_disease_intelligence_context(disease_name), timeout_sec=5.0, default={})
    rag_evidence_task = _safe_fetch(retrieve_evidence(db, rag_request), timeout_sec=1.5, default=None)
    rag_context_task = _safe_fetch(retrieve_medical_context(db, f"{disease_name} clinical features management", top_k=3), timeout_sec=1.5, default="")
    dynamic_kb_task = _safe_fetch(on_demand_lookup(disease_name, f"clinical profile for {disease_name}"), timeout_sec=2.0, default={})

    results = await asyncio.gather(
        intel_task, rag_evidence_task, rag_context_task, dynamic_kb_task,
        return_exceptions=True
    )

    intel_ctx = results[0] if not isinstance(results[0], Exception) and isinstance(results[0], dict) else {}
    rag_response = results[1] if not isinstance(results[1], Exception) else None
    rag_context_str = results[2] if not isinstance(results[2], Exception) and isinstance(results[2], str) else ""
    dynamic_profile = results[3] if not isinstance(results[3], Exception) and isinstance(results[3], dict) else {}

    # 2. Extract all context components
    wiki_ctx = intel_ctx.get("wikipedia_context", "") if isinstance(intel_ctx, dict) else ""
    pubmed_ctx = intel_ctx.get("pubmed_context", "") if isinstance(intel_ctx, dict) else ""
    icd_ctx = intel_ctx.get("icd_context", "") if isinstance(intel_ctx, dict) else ""
    who_cdc_ctx = intel_ctx.get("who_context", "") if isinstance(intel_ctx, dict) else ""
    disease_class = intel_ctx.get("disease_class") if isinstance(intel_ctx, dict) else get_disease_class(disease_name)
    incubation_data = INCUBATION_PERIODS.get(disease_name.lower())

    # 3. Build combined context for LLM
    context_parts = []

    if icd_ctx:
        context_parts.append(f"=== ICD-11 CLASSIFICATION ===\n{icd_ctx}")
    if wiki_ctx:
        context_parts.append(f"=== WIKIPEDIA MEDICAL ===\n{wiki_ctx[:3000]}")
    if pubmed_ctx:
        context_parts.append(f"=== PUBMED / NCBI ===\n{pubmed_ctx[:2000]}")

    if who_cdc_ctx:
        relevant = [l for l in who_cdc_ctx.split("\n")
                    if disease_name.lower() in l.lower() or len(l) > 20]
        if relevant:
            context_parts.append("=== WHO/CDC ALERTS ===\n" + "\n".join(relevant[:8]))

    if rag_context_str:
        context_parts.append(f"=== INTERNAL KNOWLEDGE BASE (RAG) ===\n{rag_context_str}")

    if rag_response and not isinstance(rag_response, Exception) and rag_response.citations:
        cit_str = "\n".join([
            f"[{c.source_type}]: {c.preview_text[:300]}"
            for c in rag_response.citations[:4]
        ])
        context_parts.append(f"=== RAG CITATIONS ===\n{cit_str}")

    if incubation_data:
        context_parts.append(
            f"=== EVIDENCE-BASED INCUBATION DATA ===\n"
            f"Min: {incubation_data['min_days']}d | Max: {incubation_data['max_days']}d | "
            f"Typical: {incubation_data['typical_days']}d | Class: {incubation_data['disease_class']}"
        )

    if dynamic_profile and dynamic_profile.get("found"):
        sym = dynamic_profile.get("symptoms", [])
        if sym:
            context_parts.append(f"=== DYNAMIC KB (LIVE-LEARNED) ===\nSymptoms: {', '.join(sym[:15])}")

    # Template investigations from static KB
    template_invs = get_investigation_template(disease_class) if disease_class else []
    if template_invs:
        inv_names = [t["name"] for t in template_invs[:8]]
        context_parts.append(f"=== KNOWN KEY INVESTIGATIONS ({disease_class}) ===\n" + "; ".join(inv_names))

    combined_context = "\n\n".join(context_parts) if context_parts else f"No external context found for {disease_name}. Use your training data."

    # 4. Call LLM with extended context budget — hard 25s timeout prevents UI hangs
    user_prompt = f"Generate the comprehensive clinical intelligence profile for: {disease_name}\n\n{combined_context[:6000]}"

    data = {}
    try:
        llm_coro = llm_service.generate_json_large(
            user_prompt, system=DEEP_INTELLIGENCE_PROMPT.split("## Multi-Source Context:")[0]
        )
        data = await asyncio.wait_for(llm_coro, timeout=25.0)
        if data:
            log.info("disease_intelligence_llm_ok", disease=disease_name, fields=len(data))
        else:
            log.warning("disease_intelligence_llm_empty", disease=disease_name)

    except asyncio.TimeoutError:
        log.warning("disease_intelligence_llm_timeout", disease=disease_name)
        data = _build_static_fallback(disease_name, dynamic_profile, template_invs, incubation_data, disease_class)
    except Exception as e:
        log.error("disease_intelligence_llm_failed", error=str(e), disease=disease_name)
        data = _build_static_fallback(disease_name, dynamic_profile, template_invs, incubation_data, disease_class)

    # Also use static fallback if LLM returned empty dict
    if not data:
        log.info("disease_intelligence_using_static_fallback", disease=disease_name)
        data = _build_static_fallback(disease_name, dynamic_profile, template_invs, incubation_data, disease_class)

    # 4b. Clinical Registry Enrichment: Ensure high-accuracy investigations and medications are NEVER missing
    try:
        from app.services.clinical_disease_metadata import get_disease_clinical_profile
        clinical_profile = get_disease_clinical_profile(disease_name)
        if clinical_profile:
            # If investigations are missing or sparse, enrich from clinical registry
            existing_invs = data.get("investigations") or []
            if len(existing_invs) < 3:
                rec_tests = clinical_profile.get("recommended_investigations", [])
                imm_tests = clinical_profile.get("immediate_tests", [])
                combined_tests = list(dict.fromkeys(imm_tests + rec_tests + existing_invs))
                if combined_tests:
                    data["investigations"] = combined_tests

            # If medications are missing or sparse, enrich from clinical registry
            existing_meds = data.get("medications") or []
            if len(existing_meds) < 1:
                rec_meds = clinical_profile.get("recommended_medications", [])
                if rec_meds:
                    data["medications"] = rec_meds

            # Ensure first line treatment is present
            if not data.get("first_line_treatment") and clinical_profile.get("first_line_treatment"):
                data["first_line_treatment"] = clinical_profile.get("first_line_treatment")

            # Ensure red flags are present
            if not data.get("red_flags") and clinical_profile.get("red_flags"):
                data["red_flags"] = clinical_profile.get("red_flags")

            # Ensure cardinal symptoms are present
            if not data.get("cardinal_symptoms") and clinical_profile.get("cardinal_symptoms"):
                data["cardinal_symptoms"] = clinical_profile.get("cardinal_symptoms")
    except Exception as ex:
        log.debug("clinical_registry_enrichment_skipped", error=str(ex))

    # Ensure medications, investigations, and first_line_treatment are NEVER empty
    if not data.get("medications"):
        try:
            from app.services.medication_service import _get_offline_medications
            med_objs = _get_offline_medications(disease_name)
            if med_objs:
                data["medications"] = [
                    f"{m.generic_name} ({m.standard_reference_dosing})" if getattr(m, 'standard_reference_dosing', None) else m.generic_name
                    for m in med_objs
                ]
        except Exception:
            pass

    if not data.get("investigations"):
        try:
            from app.services.investigation_service import _get_investigation_panel
            inv_panel = _get_investigation_panel(disease_name)
            if inv_panel:
                data["investigations"] = [p.get("name", p) if isinstance(p, dict) else p for p in inv_panel]
        except Exception:
            pass

    if not data.get("first_line_treatment"):
        data["first_line_treatment"] = (
            data.get("treatments", [])[0]
            if data.get("treatments")
            else (data.get("medications", [])[0] if data.get("medications") else "Guideline-directed clinical therapy")
        )

    # 5. Build structured response
    citations = []
    if rag_response and not isinstance(rag_response, Exception):
        citations = rag_response.citations or []

    # Add Wikipedia citation
    if wiki_ctx:
        from app.schemas.rag import RAGCitation
        from uuid import uuid4
        citations.insert(0, RAGCitation(
            source_id=str(uuid4()),
            source_type="wikipedia_medical",
            source_uri=f"https://en.wikipedia.org/wiki/{disease_name.replace(' ', '_')}",
            preview_text=wiki_ctx[:400],
            score=1.0
        ))

    # Add PubMed citation
    if pubmed_ctx:
        from app.schemas.rag import RAGCitation
        from uuid import uuid4
        citations.append(RAGCitation(
            source_id=str(uuid4()),
            source_type="pubmed_ncbi",
            source_uri="https://pubmed.ncbi.nlm.nih.gov/",
            preview_text=pubmed_ctx[:400],
            score=0.95
        ))

    # Build epidemiology object
    epi_data = data.get("epidemiology", {})
    epidemiology = None
    if isinstance(epi_data, dict):
        epidemiology = EpidemiologyData(
            global_incidence=epi_data.get("global_incidence"),
            mortality_rate=epi_data.get("mortality_rate"),
            affected_regions=epi_data.get("affected_regions", []),
            outbreak_status=epi_data.get("outbreak_status"),
            seasonal_pattern=epi_data.get("seasonal_pattern"),
            high_risk_groups=epi_data.get("high_risk_groups", []),
        )

    # Build special populations
    special_pops = []
    for sp in data.get("special_populations", []):
        if isinstance(sp, dict) and sp.get("population"):
            special_pops.append(SpecialPopulationWarning(
                population=sp["population"],
                warning=sp.get("warning", ""),
                recommendation=sp.get("recommendation", ""),
            ))

    return DiseaseIntelligenceResponse(
        disease_name=disease_name,
        summary=data.get("summary", "No summary available."),
        pathophysiology=data.get("pathophysiology"),
        etiology=data.get("etiology"),
        icd11_code=data.get("icd11_code"),
        who_classification=data.get("who_classification"),
        disease_class=data.get("disease_class", disease_class),
        is_notifiable=bool(data.get("is_notifiable", False)),
        is_outbreak_active=bool(data.get("is_outbreak_active", False)),
        symptoms=data.get("symptoms", []),
        cardinal_symptoms=data.get("cardinal_symptoms", []),
        signs_on_examination=data.get("signs_on_examination", []),
        red_flags=data.get("red_flags", []),
        incubation_period=data.get("incubation_period"),
        disease_stages=data.get("disease_stages", []),
        prognosis=data.get("prognosis"),
        complications=data.get("complications", []),
        first_line_treatment=data.get("first_line_treatment"),
        treatments=data.get("treatments", []),
        medications=data.get("medications", []),
        monitoring_parameters=data.get("monitoring_parameters", []),
        investigations=data.get("investigations", []),
        differential_diagnosis_clues=data.get("differential_diagnosis_clues", []),
        epidemiology=epidemiology,
        prevention=data.get("prevention", []),
        public_health_measures=data.get("public_health_measures", []),
        special_populations=special_pops,
        citations=citations,
        data_sources=data.get("data_sources") or ["Wikipedia Medical", "ICD-11 Foundation", "PubMed/NCBI", "WHO/CDC", "Clinical Disease Registry"],
        last_updated=datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC"),
    )
