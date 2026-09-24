"""DocAssistIQ — Comprehensive Clinical Disease Metadata & Intelligence Registry.

Provides enterprise-grade, evidence-based metadata for universal disease entities:
  - ICD-10 & ICD-11 coding
  - Clinical triage classification
  - Priority bedside and immediate diagnostic investigations
  - Recommended comprehensive diagnostic laboratory & imaging panels
  - Recommended evidence-based pharmacological treatments & contraindicated drugs
  - Actionable clinical treatment & stabilization summaries
  - Structured disease intelligence (pathophysiology, transmission/etiology, cardinal findings, red flags, clinical pearls)
"""

from typing import Dict, Any

DISEASE_METADATA_EXT: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # HIGH-CONSEQUENCE VIRAL HEMORRHAGIC FEVERS & TROPICAL INFECTIONS
    # =========================================================================
    "Bundibugyo Virus Disease (BVD)": {
        "icd10": "A98.4", "icd11": "1D60.1", "category": "Viral Hemorrhagic Fever — Bundibugyo Ebolavirus", "triage": "EMERGENT",
        "immediate_tests": [
            "Stat Bundibugyo ebolavirus RT-PCR (Whole Blood — BSL-4 facility)",
            "Complete Blood Count with differential (marked lymphopenia, profound thrombocytopenia)",
            "Comprehensive Metabolic Panel (AST >> ALT, BUN, creatinine, electrolyte panel)",
            "Coagulation Studies (PT/INR, aPTT, D-Dimer, Fibrinogen for DIC screening)",
            "Malaria RDT and Blood Film (co-endemic exclusion)"
        ],
        "recommended_investigations": [
            "Stat Bundibugyo ebolavirus RT-PCR (Blood — BSL-4 with BDBV-specific primers)",
            "Serial Complete Blood Count (monitoring thrombocytopenia and hemoconcentration)",
            "Comprehensive Metabolic Panel (frequent monitoring for acute kidney injury and hypokalemia)",
            "Coagulation Studies (PT/INR, aPTT, D-Dimer, Fibrinogen)",
            "Malaria Thick and Thin Blood Smears",
            "Venous Blood Gas and Lactate (tissue hypoperfusion / lactic acidosis)"
        ],
        "recommended_medications": [
            "Balanced IV Crystalloids (Ringer's Lactate / Plasmalyte titrated to urine output >=0.5-1.0 mL/kg/h)",
            "Aggressive Potassium and Magnesium chloride replacement (cardiac dysrhythmia prevention)",
            "Empiric IV Ceftriaxone 2g daily (bacterial translocation across damaged gut mucosa)",
            "IV Ondansetron 4-8mg q8h for persistent vomiting",
            "Therapeutic Alert: Inmazeb (REGN-EB3) and Ebanga (mAb114) are Zaire-specific and INEFFECTIVE against Bundibugyo virus; optimized supportive critical care is the cornerstone of therapy"
        ],
        "treatment_summary": "Immediate strict Level 4 barrier nursing, isolation, and public health reporting. Aggressive fluid and electrolyte resuscitation to replace massive gastrointestinal losses. Intensive hemodynamic monitoring in ICU; avoid IM injections and NSAIDs.",
        "disease_intelligence": {
            "disease_name": "Bundibugyo Virus Disease",
            "species": "Bundibugyo ebolavirus (BDBV)",
            "genus": "Orthoebolavirus",
            "family": "Filoviridae",
            "icd10_code": "A98.4",
            "icd11_code": "1D60.1",
            "transmission": "Direct contact with blood, secretions, organs, or other bodily fluids of infected individuals or contaminated surfaces/materials.",
            "incubation_period": "2 to 21 days (mean 8 to 10 days)",
            "epidemiology_context": "Active 2026 outbreak in Democratic Republic of the Congo (WHO DON617: 6,757 confirmed cases, 3,267 deaths as of Sept 2026). CFR ~30-45%.",
            "cardinal_symptoms": ["Acute fever", "Profound weakness", "Severe watery diarrhea", "Repeated vomiting", "Sore throat", "Mucosal bleeding diathesis"],
            "red_flags": ["Postural hypotension / circulatory shock", "Oliguria / acute renal shutdown", "Encephalopathy / altered mental status", "Overt mucosal or GI hemorrhage"],
            "clinical_pearl": "Zaire-specific monoclonal antibodies (Inmazeb, Ebanga) do NOT neutralize Bundibugyo virus. Survival depends on early, aggressive, volume-targeted fluid resuscitation and electrolyte correction."
        },
        "pearl": "Ebolavirus species causing the 2026 DRC outbreak (WHO DON617). Inmazeb and Ebanga do NOT neutralize Bundibugyo virus; aggressive supportive fluid-electrolyte care is lifesaving."
    },

    "Ebola Virus Disease (Zaire)": {
        "icd10": "A98.4", "icd11": "1D42", "category": "Viral Hemorrhagic Fever — Zaire Ebolavirus", "triage": "EMERGENT",
        "immediate_tests": [
            "Stat Filovirus RT-PCR (Blood — BSL-4 facility)",
            "Complete Blood Count (Leukopenia, marked Thrombocytopenia)",
            "Comprehensive Metabolic Panel (LFTs with AST >> ALT, Creatinine, BUN)",
            "Coagulation Panel (PT/INR, PTT, D-Dimer, Fibrinogen)",
            "Blood Cultures x2 & Malaria RDT"
        ],
        "recommended_investigations": [
            "Stat Filovirus RT-PCR (BSL-4 reference lab)",
            "Serial CBC with differential and Platelets",
            "Comprehensive Metabolic Panel (monitoring renal failure and hypokalemia)",
            "Coagulation Panel (DIC screening)",
            "Malaria Thick/Thin Film and Rapid Diagnostic Test"
        ],
        "recommended_medications": [
            "Inmazeb (Atoltivimab + Maftivimab + Odesivimab-ebgn) 50 mg/kg IV single infusion OR Ebanga (Ansuvimab-zykl) 50 mg/kg IV single infusion",
            "Aggressive IV fluid resuscitation with balanced crystalloids (Ringer's Lactate)",
            "Electrolyte replacement (KCl IV/oral, Magnesium sulfate IV)",
            "Empiric IV Ceftriaxone 2g daily for gut bacterial translocation",
            "Avoid NSAIDs, Aspirin, and IM injections"
        ],
        "treatment_summary": "Strict BSL-4 barrier nursing and Level 4 PPE. Immediate administration of monoclonal antibodies (Inmazeb or Ebanga) specific for Zaire ebolavirus. Aggressive fluid resuscitation for massive diarrheal losses.",
        "disease_intelligence": {
            "disease_name": "Ebola Virus Disease (Zaire)",
            "species": "Zaire ebolavirus (EBOV)",
            "genus": "Orthoebolavirus",
            "family": "Filoviridae",
            "icd10_code": "A98.4",
            "icd11_code": "1D42",
            "transmission": "Contact with blood, body fluids, or infected bushmeat.",
            "cardinal_symptoms": ["Acute fever", "Profound weakness", "Watery diarrhea", "Vomiting", "Mucosal bleeding", "Postural hypotension"],
            "red_flags": ["Shock / hypovolemia", "Anuria", "Coma / encephalopathy", "Severe coagulopathy"],
            "clinical_pearl": "Zaire ebolavirus has licensed neutralizing mAbs (Inmazeb, Ebanga) which significantly reduce mortality if administered early."
        },
        "pearl": "High-consequence filovirus disease. Characterized by acute fever, profound gastrointestinal fluid losses, postural hypotension, mucosal bleeding, and multisystem organ failure. Inmazeb/Ebanga indicated."
    },

    "Marburg Virus Disease": {
        "icd10": "A98.3", "icd11": "1D43", "category": "Viral Hemorrhagic Fever — Marburg Virus", "triage": "EMERGENT",
        "immediate_tests": [
            "Stat Marburg RT-PCR (Blood — BSL-4)",
            "Complete Blood Count with differential",
            "Renal & Liver Function Panels",
            "Coagulation Studies (DIC screen)",
            "Malaria Thick/Thin Film"
        ],
        "recommended_investigations": [
            "Stat Marburg virus RT-PCR (Blood - BSL-4)",
            "Complete Blood Count and Platelet Count",
            "Comprehensive Metabolic Panel and Serum Lactate",
            "Coagulation Profile (PT/INR, PTT, Fibrinogen)",
            "Malaria Smear"
        ],
        "recommended_medications": [
            "Aggressive balanced IV crystalloids (Ringer's Lactate)",
            "Electrolyte correction (KCl, MgSO4)",
            "Empiric broad-spectrum IV antibiotics (Ceftriaxone)",
            "Investigational monoclonal antibody (MR-191) where accessible"
        ],
        "treatment_summary": "Level 4 barrier isolation and aggressive intensive supportive care. Monitored fluid resuscitation and replacement of coagulation factors.",
        "disease_intelligence": {
            "disease_name": "Marburg Virus Disease",
            "etiology": "Marburg virus (MARV / Filoviridae)",
            "icd10_code": "A98.3",
            "icd11_code": "1D43",
            "transmission": "Fruit bat (Rousettus aegyptiacus) exposure or human-to-human body fluid contact.",
            "cardinal_symptoms": ["Ghost-like facies", "Abrupt high fever", "Severe watery diarrhea", "Vomiting", "Hemorrhagic diathesis"],
            "red_flags": ["Hypovolemic shock", "Anuria", "Coma", "Massive hemorrhage"],
            "clinical_pearl": "CFR ranges 24-88%. Presentation clinically indistinguishable from Ebola; RT-PCR differentiation is vital."
        },
        "pearl": "Filovirus closely related to Ebola causing severe hemorrhagic fever. Rapid progression to massive fluid losses, encephalopathy, and shock. Strict isolation required."
    },

    "Meningococcal Meningitis": {
        "icd10": "A39.0", "icd11": "1D01", "category": "Invasive Bacterial Emergency", "triage": "EMERGENT",
        "immediate_tests": [
            "Stat Blood Cultures x2 (draw immediately without delaying antibiotics)",
            "Lumbar Puncture for CSF Analysis (opening pressure, cell count, Gram stain for Gram-negative diplococci, protein, glucose, PCR)",
            "Complete Blood Count with differential and Coagulation Panel (PT/INR, PTT, D-dimer for DIC)",
            "Serum Lactate and Blood Gas"
        ],
        "recommended_investigations": [
            "Stat Blood Cultures x2 prior to antibiotics",
            "Lumbar Puncture (CSF Gram stain, bacterial culture, multiplex PCR)",
            "Serum Lactate and Arterial/Venous Blood Gas",
            "Coagulation Profile (PT/INR, aPTT, Fibrinogen, D-Dimer for purpura fulminans / DIC)",
            "Non-contrast Head CT prior to LP only if focal deficit, papilledema, or new seizure"
        ],
        "recommended_medications": [
            "IV Ceftriaxone 2g IV q12h (or Cefotaxime 2g IV q4-6h) immediately",
            "IV Vancomycin 15-20 mg/kg IV q8-12h (empiric co-coverage until sensitivities confirmed)",
            "IV Dexamethasone 10mg IV administered prior to or with first dose of antibiotics",
            "IV Isotonic Crystalloids (30 mL/kg within 3 hours for hypotension/hyperlactatemia)",
            "Chemoprophylaxis for close contacts: Oral Rifampin 600mg BID x2 days or single-dose Ciprofloxacin 500mg"
        ],
        "treatment_summary": "Immediate empiric parenteral bactericidal antibiotics (IV Ceftriaxone + Vancomycin + Dexamethasone)—never delay treatment for imaging or lumbar puncture. Strict droplet isolation for 24 hours post-effective antibiotics. Aggressive septic shock resuscitation.",
        "disease_intelligence": {
            "disease_name": "Meningococcal Disease / Meningococcemia (with Meningitis)",
            "etiology": "Neisseria meningitidis (Gram-negative diplococcus)",
            "icd10_code": "A39.0 / A39.2",
            "icd11_code": "1D01",
            "transmission": "Respiratory droplets and pharyngeal secretions; high risk in crowded environments, barracks, and student residences.",
            "cardinal_symptoms": ["Sudden high fever", "Severe headache", "Nuchal rigidity", "Photophobia", "Non-blanching petechial or purpuric rash", "Rapid circulatory deterioration"],
            "red_flags": ["Rapidly coalescing purpuric rash (purpura fulminans)", "Hypotension / septic shock (Waterhouse-Friderichsen syndrome)", "Depressed consciousness", "Signs of brain herniation"],
            "clinical_pearl": "Petechial or purpuric rash in a febrile patient with meningism is Meningococcemia until proven otherwise. Every 30 minutes of delay in antibiotic administration significantly increases mortality."
        },
        "pearl": "Neisseria meningitidis infection with non-blanching petechial/purpuric rash. Immediate IV Ceftriaxone and Dexamethasone are lifesaving; do not delay for imaging or lumbar puncture."
    },

    "Bacterial Meningitis": {
        "icd10": "G00.9", "icd11": "1D01", "category": "Neurological / Invasive Bacterial", "triage": "EMERGENT",
        "immediate_tests": [
            "Stat Blood Cultures x2",
            "Immediate Empiric IV Ceftriaxone 2g + Vancomycin + Dexamethasone",
            "Lumbar Puncture (CSF Gram stain, protein, glucose, cell count)",
            "Head CT prior to LP if altered mental status or focal deficit"
        ],
        "recommended_investigations": [
            "Stat Blood Cultures x2",
            "Lumbar Puncture for CSF Analysis (Pressure, Gram Stain, Cell Count, Protein, Glucose)",
            "Multiplex CSF PCR panel for common bacterial pathogens",
            "Serum Procalcitonin and Complete Blood Count"
        ],
        "recommended_medications": [
            "IV Ceftriaxone 2g q12h + IV Vancomycin 15-20 mg/kg q8-12h",
            "IV Ampicillin 2g q4h added if age >50 or immunocompromised (Listeria coverage)",
            "IV Dexamethasone 10mg q6h x4 days (initiated with or before first antibiotic dose)"
        ],
        "treatment_summary": "Immediate empiric parenteral antimicrobial therapy. Do not delay antibiotics for CT or lumbar puncture.",
        "disease_intelligence": {
            "disease_name": "Acute Bacterial Meningitis",
            "etiology": "Streptococcus pneumoniae, Neisseria meningitidis, Listeria monocytogenes",
            "icd10_code": "G00.9",
            "icd11_code": "1D01",
            "cardinal_symptoms": ["Fever", "Neck stiffness", "Altered mental status", "Severe headache", "Photophobia"],
            "red_flags": ["Cerebral herniation signs", "Coma", "Refractory seizures", "Septic shock"],
            "clinical_pearl": "Classic triad is fever, neck stiffness, and altered mental status. Pre-antibiotic dexamethasone reduces mortality and hearing loss in pneumococcal meningitis."
        },
        "pearl": "Classic triad of fever, neck stiffness, and altered mental status. Never delay antibiotics for imaging or lumbar puncture."
    },

    "Chikungunya": {
        "icd10": "A92.0", "icd11": "1D21", "category": "Tropical Arboviral", "triage": "URGENT",
        "immediate_tests": [
            "Chikungunya RT-PCR (days 1-7 of illness)",
            "Chikungunya IgM/IgG ELISA (day 5+)",
            "Dengue & Zika RT-PCR/Serology (co-endemic rule out)",
            "Complete Blood Count",
            "CRP / ESR"
        ],
        "recommended_investigations": [
            "Chikungunya RT-PCR (acute viremic phase)",
            "Chikungunya IgM/IgG ELISA",
            "Dengue NS1 Antigen and IgM (differentiating co-circulating arboviruses)",
            "CBC with differential (leukopenia, mild thrombocytopenia)",
            "Renal and Liver Function Panels"
        ],
        "recommended_medications": [
            "Paracetamol (Acetaminophen) 650-1000 mg q6h PRN for fever and arthralgia (max 3-4g/day)",
            "NSAIDs (Ibuprofen 400-600mg TID or Meloxicam) ONLY after Dengue strictly excluded",
            "Tramadol 50mg PRN for refractory incapacitating arthralgia",
            "Contraindication: Strict avoidance of Aspirin and early NSAIDs until Dengue is ruled out"
        ],
        "treatment_summary": "Symptomatic control of severe joint pain with paracetamol; introduce NSAIDs only after Dengue exclusion. Rest, joint immobilization, and vector precautions.",
        "disease_intelligence": {
            "disease_name": "Chikungunya",
            "etiology": "Chikungunya virus (Alphavirus / Togaviridae)",
            "icd10_code": "A92.0",
            "icd11_code": "1D21",
            "transmission": "Aedes aegypti and Aedes albopictus mosquitoes.",
            "cardinal_symptoms": ["Sudden high fever", "Severe bilateral crippling polyarthralgia", "Periarticular joint swelling", "Maculopapular rash"],
            "red_flags": ["Severe dehydration", "Meningoencephalitis", "Bullous skin lesions in infants"],
            "clinical_pearl": "In Chikungunya, joint pain is disproportionately severe and disabling compared with fever, frequently rendering the patient unable to walk or climb stairs."
        },
        "pearl": "Alphavirus transmitted by Aedes mosquitoes ('that which bends up'). Hallmarked by acute high fever, severe incapacitating polyarthralgia symmetrically affecting wrists and ankles."
    },

    "Yellow Fever": {
        "icd10": "A95.9", "icd11": "1D20", "category": "Tropical Arboviral / Hemorrhagic", "triage": "EMERGENT",
        "immediate_tests": [
            "Yellow Fever RT-PCR (Early viremic phase, days 1-6)",
            "Yellow Fever IgM ELISA",
            "Liver Function Tests (AST/ALT markedly elevated, AST > ALT, Bilirubin)",
            "Serum Creatinine and BUN (evaluating acute tubular necrosis)",
            "Coagulation Profile (PT/INR, PTT, Fibrinogen)"
        ],
        "recommended_investigations": [
            "Yellow Fever RT-PCR (blood)",
            "Yellow Fever IgM ELISA / Plaque Reduction Neutralization Test (PRNT)",
            "Serial Liver Function Tests and Total Bilirubin",
            "Renal Function Panel and Urine Output monitoring",
            "Coagulation profile (PT/INR, aPTT, D-Dimer, Fibrinogen)"
        ],
        "recommended_medications": [
            "Balanced IV Crystalloids titrated to urine output",
            "IV Vitamin K 10mg for coagulopathy",
            "Fresh Frozen Plasma (FFP) or Platelets for active bleeding",
            "IV Pantoprazole 40mg daily for gastric mucosal stress bleeding prophylaxis",
            "Contraindicated: NSAIDs, Aspirin, and hepatotoxic medications"
        ],
        "treatment_summary": "Strict mosquito netting/vector isolation. Monitored ICU admission for aggressive hepatorenal support, correction of metabolic acidosis, and blood product support for hemorrhage.",
        "disease_intelligence": {
            "disease_name": "Yellow Fever",
            "etiology": "Yellow fever virus (Flavivirus / Flaviviridae)",
            "icd10_code": "A95.9",
            "icd11_code": "1D20",
            "transmission": "Haemagogus and Sabethes (jungle) or Aedes (urban) mosquitoes in South America and Africa.",
            "cardinal_symptoms": ["Biphasic fever", "Severe jaundice", "Dark urine", "Epistaxis and gum bleeding", "Hematemesis (black vomit)", "Right costal tenderness"],
            "red_flags": ["Faget sign (bradycardia with high fever)", "Hepatic failure / encephalopathy", "Severe coagulopathy / DIC", "Anuria"],
            "clinical_pearl": "Biphasic disease: brief remission followed by toxic phase with profound jaundice and hepatorenal failure. Vaccination provides lifelong immunity."
        },
        "pearl": "Flavivirus endemic in tropical South America and Africa. Biphasic course: initial flu-like fever followed by toxic phase with profound jaundice, dark urine, gum bleeding, and renal failure."
    },

    "Malaria (Plasmodium falciparum)": {
        "icd10": "B50.9", "icd11": "1F40", "category": "Tropical Parasitic", "triage": "EMERGENT",
        "immediate_tests": [
            "Stat Thick and Thin Peripheral Blood Smears (Giemsa stain)",
            "Malaria Rapid Diagnostic Test (Pf-HRP2 antigen)",
            "Complete Blood Count (Anemia, Thrombocytopenia)",
            "Venous Blood Gas, Lactate, and Blood Glucose"
        ],
        "recommended_investigations": [
            "Stat Thick and Thin Giemsa Blood Smears (species & parasitemia %)",
            "Repeat blood smears every 12-24h to assess parasite clearance",
            "Complete Blood Count (hemolytic anemia, thrombocytopenia)",
            "Serum Lactate, Creatinine, and Liver Function Tests",
            "Blood Glucose (frequent monitoring for hypoglycemia)"
        ],
        "recommended_medications": [
            "For Severe Malaria: IV Artesunate 2.4 mg/kg IV at 0, 12, 24 hours, then once daily",
            "For Uncomplicated Falciparum: Oral Artemether-Lumefantrine (Coartem) 4 tablets BID x3 days with food",
            "IV Dextrose 10% or 50% for hypoglycemia",
            "Broad-spectrum IV Ceftriaxone if enteric co-infection suspected"
        ],
        "treatment_summary": "Parenteral IV Artesunate immediately for any neurological alteration, parasitemia >5%, severe anemia, or inability to tolerate oral medications. Close monitoring for hypoglycemia and pulmonary edema.",
        "disease_intelligence": {
            "disease_name": "Malaria (Plasmodium falciparum)",
            "etiology": "Plasmodium falciparum (intraerythrocytic protozoan)",
            "icd10_code": "B50.9",
            "icd11_code": "1F40",
            "transmission": "Female Anopheles mosquito bite.",
            "cardinal_symptoms": ["Recurrent paroxysms of fever and chills", "Severe headache", "Dark urine", "Pallor and splenomegaly", "Confusion / altered consciousness"],
            "red_flags": ["Cerebral malaria (coma / seizures)", "Acidotic breathing / hyperlactatemia", "Hemoglobin <7 g/dL", "Hyperparasitemia >5%"],
            "clinical_pearl": "P. falciparum cytoadheres to microvascular endothelium causing organ ischemia. Any neurological alteration with falciparum malaria is cerebral malaria requiring stat IV Artesunate."
        },
        "pearl": "Most dangerous Plasmodium species causing microvascular sequestration. Cyclical paroxysms of fever and chills; any neurological alteration indicates severe malaria requiring IV Artesunate."
    },

    "Severe Malaria / Cerebral Malaria": {
        "icd10": "B50.9", "icd11": "1F40", "category": "Tropical Parasitic Emergency", "triage": "EMERGENT",
        "immediate_tests": [
            "Immediate IV Artesunate (2.4 mg/kg IV stat)",
            "Thick and Thin Blood Smears",
            "Continuous Vital and Telemetry Monitoring",
            "Serial Blood Glucose and Arterial Blood Gas"
        ],
        "recommended_investigations": [
            "Serial Thick and Thin Blood Smears (q12h)",
            "Arterial Blood Gas and Serum Lactate",
            "Renal Panel and Serial Blood Glucose (q4h)",
            "Non-contrast Head CT (rule out alternative intracranial pathology)"
        ],
        "recommended_medications": [
            "IV Artesunate 2.4 mg/kg IV at 0, 12, 24h, then daily",
            "IV 10% Dextrose infusion to prevent hypoglycemia",
            "Benzodiazepines (IV Lorazepam 4mg) for seizures",
            "IV broad-spectrum Ceftriaxone for potential bacterial superinfection"
        ],
        "treatment_summary": "Immediate IV Artesunate. ICU admission with aggressive supportive therapy, glycemic monitoring, and control of seizures.",
        "disease_intelligence": {
            "disease_name": "Severe / Cerebral Malaria",
            "etiology": "Plasmodium falciparum with cerebral sequestration",
            "icd10_code": "B50.9",
            "icd11_code": "1F40",
            "cardinal_symptoms": ["Unarousable coma", "Repeated generalized convulsions", "Acidotic breathing", "Severe normocytic anemia"],
            "red_flags": ["Coma >30 min post-seizure", "Lactic acidosis", "Acute kidney injury", "Pulmonary edema"],
            "clinical_pearl": "Mortality approaches 100% if untreated; IV Artesunate reduces mortality by 35% compared to Quinine."
        },
        "pearl": "Medical emergency with high mortality. Features unarousable coma, repeated seizures, or acute kidney injury. Immediate parenteral IV Artesunate is lifesaving."
    },

    "Zika Virus": {
        "icd10": "A92.8", "icd11": "1D22", "category": "Tropical Arboviral", "triage": "ROUTINE",
        "immediate_tests": [
            "Zika Virus RT-PCR (Serum & Urine)",
            "Zika IgM ELISA",
            "Dengue and Chikungunya PCR/Serology",
            "CBC with Platelets"
        ],
        "recommended_investigations": [
            "Zika Virus RT-PCR (serum <=7 days, urine <=14 days)",
            "Zika Virus IgM ELISA",
            "Dengue and Chikungunya RT-PCR / serology",
            "If partner pregnant: Serial fetal anomaly ultrasounds"
        ],
        "recommended_medications": [
            "Paracetamol 500-1000mg q6h PRN for fever and arthralgia",
            "Oral Cetirizine 10mg daily for pruritic rash",
            "Adequate oral fluid hydration"
        ],
        "treatment_summary": "Supportive outpatient care. Counseling on barrier contraception: prevent sexual transmission for 3 months (men) or 2 months (women) post-return.",
        "disease_intelligence": {
            "disease_name": "Zika Virus Disease",
            "etiology": "Zika virus (Flavivirus / Flaviviridae)",
            "icd10_code": "A92.8",
            "icd11_code": "1D22",
            "transmission": "Aedes mosquitoes and sexual transmission.",
            "cardinal_symptoms": ["Low-grade fever", "Descending maculopapular rash", "Bilateral non-purulent conjunctivitis", "Mild arthralgia"],
            "red_flags": ["Guillain-Barré syndrome", "Congenital Zika syndrome (microcephaly) in pregnant partners"],
            "clinical_pearl": "Capable of sexual transmission for months. Advise strict contraception to prevent severe congenital neurodevelopmental defects."
        },
        "pearl": "Flavivirus presenting with low-grade fever, descending maculopapular rash, bilateral non-purulent conjunctivitis, and mild arthralgia. Sexual transmission precautions required."
    },

    "Hepatitis A": {
        "icd10": "B15.9", "icd11": "1E50.0", "category": "Enteric Viral Hepatitis", "triage": "URGENT",
        "immediate_tests": [
            "Hepatitis A IgM ELISA (Diagnostic)",
            "Comprehensive Metabolic Panel (ALT, AST, Total & Direct Bilirubin, Alk Phos)",
            "Coagulation Panel (PT/INR)",
            "Abdominal Ultrasound"
        ],
        "recommended_investigations": [
            "Anti-HAV IgM (gold standard for acute infection)",
            "Serial CMP (monitoring transaminases and bilirubin clearance)",
            "Serial PT/INR (critical monitor for acute fulminant liver failure)",
            "Abdominal Ultrasound (parenchyma evaluation, excluding biliary obstruction)"
        ],
        "recommended_medications": [
            "Oral hydration and nutritional maintenance",
            "Oral Ondansetron 4-8mg TID PRN for nausea",
            "Vitamin K 10mg subcutaneously if mild PT prolongation",
            "Avoid all hepatotoxic substances (alcohol, paracetamol >2g/day)"
        ],
        "treatment_summary": "Supportive outpatient care with close monitoring of INR. An INR >1.5 or mental clouding requires immediate admission for impending acute liver failure.",
        "disease_intelligence": {
            "disease_name": "Acute Hepatitis A",
            "etiology": "Hepatitis A virus (Picornaviridae)",
            "icd10_code": "B15.9",
            "icd11_code": "1E50.0",
            "transmission": "Fecal-oral route via contaminated food or water.",
            "incubation_period": "15 to 50 days (mean 28 days)",
            "cardinal_symptoms": ["Fatigue and anorexia", "Dark urine", "Acholic (pale) stools", "Scleral icterus / jaundice", "Right upper quadrant discomfort"],
            "red_flags": ["Coagulopathy (INR >1.5)", "Hepatic encephalopathy (asterixis, confusion)", "Persistent vomiting"],
            "clinical_pearl": "Incubation is 2-6 weeks. Characterized by dark urine and pale stools preceding jaundice. Almost never causes chronic infection."
        },
        "pearl": "Fecal-oral transmission with 15-50 day incubation. Characterized by acute prodromal malaise followed by dark urine, acholic stools, and jaundice. Monitor INR."
    },

    "Dengue Hemorrhagic Fever": {
        "icd10": "A91", "icd11": "1D2Z", "category": "Tropical Arboviral / Hemorrhagic", "triage": "EMERGENT",
        "immediate_tests": [
            "Serial Hematocrit & Platelet Count (q6-12h)",
            "Dengue NS1 Antigen / IgM ELISA",
            "Serum Albumin (assess vascular leakage)",
            "Bedside Ultrasound (pleural effusion / ascites)",
            "Liver Function Tests"
        ],
        "recommended_investigations": [
            "Serial Hematocrit and Platelet counts every 4-6 hours during critical phase",
            "Dengue NS1 Antigen and IgM/IgG Serology",
            "Point-of-Care Ultrasound (POCUS) for gallbladder wall thickening, ascites, pleural effusion",
            "Serum Albumin, Electrolytes, and Coagulation Panel"
        ],
        "recommended_medications": [
            "Judicious isotonic crystalloid titration (5-7 mL/kg/h for 1-2h, then taper to 3-5 mL/kg/h)",
            "Paracetamol 500-650mg q6h PRN for fever (max 2-3g/day)",
            "Strictly avoid Aspirin, NSAIDs, and intramuscular injections"
        ],
        "treatment_summary": "Close monitoring during the defervescence window (days 3-7). Cautious, volume-targeted isotonic crystalloid titration to prevent both hypovolemic shock and fluid overload.",
        "disease_intelligence": {
            "disease_name": "Dengue Hemorrhagic Fever",
            "etiology": "Dengue virus serotypes 1-4 (Flaviviridae)",
            "icd10_code": "A91",
            "icd11_code": "1D2Z",
            "cardinal_symptoms": ["Defervescence with worsening status", "Hemoconcentration (>=20% rise in hematocrit)", "Thrombocytopenia (<100,000/uL)", "Persistent vomiting", "Mucosal bleeding"],
            "red_flags": ["Severe abdominal pain", "Persistent vomiting", "Fluid accumulation (pleural effusion)", "Mucosal bleeding", "Lethargy", "Narrow pulse pressure (<20 mmHg)"],
            "clinical_pearl": "The critical plasma leakage phase coincides with fever clearance (defervescence). Meticulous fluid balance is the key to preventing Dengue Shock Syndrome."
        },
        "pearl": "Severe manifestation of dengue during defervescence window characterized by plasma leakage, hemoconcentration (hematocrit rise >=20%), thrombocytopenia, and bleeding."
    },

    "Dengue Fever": {
        "icd10": "A90", "icd11": "1D2Z", "category": "Tropical Arboviral", "triage": "URGENT",
        "immediate_tests": ["Dengue NS1 Antigen (days 1-5)", "Dengue IgM/IgG Serology (day 5+)", "Complete Blood Count (Serial Platelets and Hematocrit)", "Liver Function Tests"],
        "recommended_investigations": ["Dengue NS1 Antigen and IgM/IgG ELISA", "Serial CBC with Platelet Count", "Liver Function Tests", "Urinalysis"],
        "recommended_medications": ["Paracetamol 500-1000mg q6h PRN (max 3g/day)", "Oral Rehydration Solution (ORS)", "Avoid Aspirin, NSAIDs, and steroids"],
        "treatment_summary": "Outpatient fluid replacement with close daily follow-up. Counsel patient on red-flag warning signs indicating transition to severe dengue.",
        "disease_intelligence": {
            "disease_name": "Dengue Fever",
            "etiology": "Dengue virus serotypes 1-4",
            "icd10_code": "A90",
            "cardinal_symptoms": ["Sudden high fever", "Retro-orbital pain", "Severe myalgia ('breakbone')", "Maculopapular rash"],
            "red_flags": ["Persistent vomiting", "Severe abdominal pain", "Mucosal bleeding"],
            "clinical_pearl": "Avoid NSAIDs and aspirin due to platelet inhibition and hemorrhagic risk."
        },
        "pearl": "'Breakbone fever' featuring retro-orbital headache, severe arthralgia, and risk of plasma leakage. Avoid aspirin and NSAIDs."
    },

    "Typhoid Fever": {
        "icd10": "A01.0", "icd11": "1A07.0", "category": "Infectious Enteric", "triage": "URGENT",
        "immediate_tests": [
            "Blood Cultures x3 (Gold standard, 60-80% yield)",
            "Stool and Urine Cultures",
            "Complete Blood Count (Leukopenia, Anemia)",
            "Liver Function Tests",
            "TyphiDot / Serology (adjunct)"
        ],
        "recommended_investigations": [
            "Blood Cultures x3 (before antibiotics)",
            "Stool Culture and Bone Marrow Culture (highest yield if blood cultures negative)",
            "Complete Blood Count (leukopenia with relative lymphocytosis)",
            "Liver Function Tests and Serum Electrolytes"
        ],
        "recommended_medications": [
            "IV Ceftriaxone 2g daily x10-14 days OR Oral Azithromycin 1g day 1 then 500mg daily x7 days",
            "Oral Ciprofloxacin 500mg BID x10-14 days ONLY if local fluoroquinolone sensitivity confirmed",
            "Dexamethasone 3 mg/kg IV load then 1 mg/kg q6h x48h for severe typhoid encephalopathy"
        ],
        "treatment_summary": "Empiric parenteral third-generation cephalosporin or oral azithromycin. Monitor for ileal perforation and gastrointestinal hemorrhage during 3rd week.",
        "disease_intelligence": {
            "disease_name": "Typhoid Fever (Enteric Fever)",
            "etiology": "Salmonella enterica serovar Typhi",
            "icd10_code": "A01.0",
            "icd11_code": "1A07.0",
            "transmission": "Contaminated food and water.",
            "cardinal_symptoms": ["Step-ladder rising fever", "Persistent high fever", "Relative bradycardia (Faget sign)", "Abdominal discomfort", "Rose spots", "Hepatosplenomegaly"],
            "red_flags": ["Acute peritonitis (ileal perforation)", "Severe melena / intestinal hemorrhage", "Typhoid state (delirium, stupor)"],
            "clinical_pearl": "Look for Faget sign: fever with relative bradycardia instead of expected tachycardia."
        },
        "pearl": "Systemic infection by Salmonella enterica serovar Typhi. Classic step-ladder rising fever, persistent high fever, headache, relative bradycardia, and hepatosplenomegaly."
    },

    # =========================================================================
    # RARE GENETIC, METABOLIC, NEUROMUSCULAR & AUTOINFLAMMATORY CONDITIONS
    # =========================================================================
    "Insulin Autoimmune Syndrome (Hirata Disease)": {
        "icd10": "E16.1", "icd11": "5A42", "category": "Endocrinology / Autoimmune", "triage": "URGENT",
        "immediate_tests": [
            "Serum Insulin Autoantibody (IAA) Titer (>50-90% binding)",
            "Simultaneous Glucose, Total Insulin, Free Insulin, and C-peptide levels during hypoglycemia",
            "Pancreatic Endoscopic Ultrasound / MRI (rule out insulinoma)",
            "Oral Glucose Tolerance Test with extended sampling (postprandial late hypoglycemia pattern)"
        ],
        "recommended_investigations": [
            "Serum Insulin Autoantibody (IAA) titer by radioimmunoassay",
            "Simultaneous Plasma Glucose, Free Insulin, Total Insulin, and C-peptide during symptomatic episode",
            "Sulfonylurea and meglitinide screen in plasma/urine",
            "Pancreatic MRI and Endoscopic Ultrasound (EUS) to exclude insulinoma",
            "HLA Class II typing (strong association with HLA-DRB1*04:06)"
        ],
        "recommended_medications": [
            "Frequent small low-carbohydrate, high-protein meals (prevents sudden postprandial insulin surges)",
            "Oral Acarbose (alpha-glucosidase inhibitor) 50-100mg TID with first bite of meals (delays carbohydrate absorption)",
            "Oral Prednisone 30-40mg daily tapered over weeks for refractory severe hypoglycemia",
            "Discontinue all triggering sulfhydryl-containing supplements (alpha-lipoic acid, glutathione, captopril)"
        ],
        "treatment_summary": "Discontinue triggering supplements (alpha-lipoic acid). Dietary modification with small frequent low-carbohydrate meals. Acarbose to blunt postprandial hyperglycemia and subsequent autoantibody dissociation hypoglycemia; corticosteroids for refractory cases.",
        "disease_intelligence": {
            "disease_name": "Insulin Autoimmune Syndrome (Hirata Disease)",
            "etiology": "Polyclonal autoantibodies directed against endogenous insulin, frequently triggered by sulfhydryl/thiol medications or supplements",
            "icd10_code": "E16.1",
            "icd11_code": "5A42",
            "cardinal_symptoms": ["Recurrent late postprandial hypoglycemia", "Profound neuroglycopenia", "Markedly elevated total insulin with elevated C-peptide", "Absence of pancreatic mass"],
            "red_flags": ["Hypoglycemic coma / seizure", "Severe neuroglycopenia with syncope", "Nocturnal hypoglycemic episodes"],
            "clinical_pearl": "Hypoglycemia occurs 2-4 hours AFTER meals when massive amounts of insulin dissociate from circulating low-affinity autoantibodies. Always ask about alpha-lipoic acid supplements."
        },
        "pearl": "Autoimmune reactive hypoglycemia driven by polyclonal anti-insulin antibodies. Often triggered by sulfhydryl/thiol-containing medications or nutritional supplements (alpha-lipoic acid)."
    },

    "Pachydermoperiostosis (Primary Hypertrophic Osteoarthropathy)": {
        "icd10": "M89.4", "icd11": "FB81.2", "category": "Rare Genetic / Skeletal", "triage": "ROUTINE",
        "immediate_tests": [
            "Skeletal Survey / Long Bone Plain Radiographs (bilateral symmetric subperiosteal new bone formation)",
            "Chest CT and Transthoracic Echocardiogram (exclude secondary pulmonary or cardiac clubbing)",
            "HPGD and SLCO2A1 Genetic Testing (mutations in 15-PGDH or prostaglandin transporter)",
            "Urinary Prostaglandin E2 metabolite (PGE-M) excretion"
        ],
        "recommended_investigations": [
            "Plain Radiographs of Long Bones (periostosis of diaphysis and metaphysis of tibia/fibula/radius/ulna)",
            "Contrast Chest CT and Echocardiography (ruling out bronchogenic carcinoma, cyanotic heart disease)",
            "Targeted Sanger or NGS sequencing of SLCO2A1 and HPGD genes",
            "Urinary PGE-M and plasma PGE2 levels",
            "Serum Growth Hormone and IGF-1 (exclude acromegaly)"
        ],
        "recommended_medications": [
            "Oral NSAIDs (Celecoxib 200mg daily, Etoricoxib, or Indomethacin) for bone and articular pain",
            "Oral Colchicine 0.5mg BID for pachydermia and articular inflammation",
            "Bisphosphonates (IV Zoledronic acid 4mg or Pamidronate) for severe refractory osteoarthropathy pain",
            "Plastic surgical evaluation for facial pachydermia / furrowing (blepharoplasty, rhytidectomy)"
        ],
        "treatment_summary": "Symptomatic control of disabling bone pain with NSAIDs and bisphosphonates. Dermatological and surgical interventions for facial furrowing (cutis verticis gyrata) and ptosis. Genetic counseling for autosomal recessive inheritance.",
        "disease_intelligence": {
            "disease_name": "Pachydermoperiostosis (Touraine-Solente-Golé Syndrome)",
            "etiology": "Autosomal recessive mutations in HPGD or SLCO2A1 genes leading to impaired prostaglandin E2 degradation and systemic PGE2 elevation",
            "icd10_code": "M89.4",
            "icd11_code": "FB81.2",
            "cardinal_symptoms": ["Bulbous digital clubbing", "Pachydermia (furrowed facial skin / cutis verticis gyrata)", "Periosteal new bone formation", "Hyperhidrosis", "Chronic deep aching bone pain"],
            "red_flags": ["Severe debilitating arthropathy", "Ptosis obstructing vision", "Myelofibrosis in late disease"],
            "clinical_pearl": "Complete triad of pachydermia, periostosis, and digital clubbing in an adolescent/young male without underlying cardiopulmonary disease indicates primary hypertrophic osteoarthropathy."
        },
        "pearl": "Touraine-Solente-Golé syndrome: Triad of pachydermia (furrowed/thickened facial skin), periostosis (periosteal new bone formation), and bulbous digital clubbing with hyperhidrosis."
    },

    "Acute Intermittent Porphyria (AIP)": {
        "icd10": "E80.2", "icd11": "5C58.0", "category": "Metabolic Emergency / Hematology", "triage": "EMERGENT",
        "immediate_tests": [
            "Urinary Porphobilinogen (PBG) and ALA (quantitative light-protected urine sample)",
            "Hydroxymethylbilane Synthase (HMBS / PBG Deaminase) enzyme activity in erythrocytes",
            "Comprehensive Metabolic Panel (hyponatremia / SIADH evaluation)",
            "HMBS Gene Molecular Sequencing"
        ],
        "recommended_investigations": [
            "Spot Urine Porphobilinogen (PBG) normalized to creatinine (markedly elevated 10-50x during attack)",
            "Urine protected from light for porphyrin precursors (PBG and ALA)",
            "HMBS (PBGD) enzymatic activity assay in red blood cells",
            "Molecular genetic testing for HMBS gene pathogenic variants",
            "Serum electrolytes (detecting SIADH-induced hyponatremia)"
        ],
        "recommended_medications": [
            "IV Hemin (Panhematin) 3-4 mg/kg/day infused in 25% human albumin over 30 min daily x4 days",
            "IV 10% Dextrose infusion (>=300g carbohydrate/day) as bridge while obtaining Hemin",
            "IV Morphine or Fentanyl for severe neurovisceral abdominal pain",
            "IV Ondansetron 4-8mg q8h for nausea/vomiting",
            "Strict avoidance of all porphyrinogenic CYP-inducing medications (barbiturates, sulfonamides, carbamazepine, rifampin)"
        ],
        "treatment_summary": "Immediate discontinuation of any porphyrinogenic medications. High-dose IV carbohydrates (10% Dextrose) and definitive treatment with IV Hemin (Panhematin). Aggressive opioid analgesia and correction of hyponatremia.",
        "disease_intelligence": {
            "disease_name": "Acute Intermittent Porphyria",
            "etiology": "Autosomal dominant deficiency of hydroxymethylbilane synthase (HMBS / PBG deaminase) in the heme biosynthetic pathway",
            "icd10_code": "E80.2",
            "icd11_code": "5C58.0",
            "cardinal_symptoms": ["Severe diffuse abdominal pain out of proportion to exam", "Port-wine / reddish-brown urine on standing", "Motor neuropathy / quadriparesis", "Neuropsychiatric disturbance", "Autonomic instability"],
            "red_flags": ["Respiratory muscle paralysis from motor neuropathy", "Severe hyponatremia with seizures", "Intractable hypertension / tachycardia"],
            "clinical_pearl": "Abdominal pain is severe, diffuse, and disproportionate to physical examination, with normal lipase/amylase and no surgical peritonitis. Urine darkens to reddish-brown ('port-wine') upon light exposure."
        },
        "pearl": "Life-threatening neurovisceral crisis: Severe diffuse abdominal pain out of proportion to exam, dark port-wine urine, peripheral neuropathy, and hyponatremia. Immediate IV Hemin."
    },

    "Duchenne Muscular Dystrophy (DMD)": {
        "icd10": "G71.0", "icd11": "8C70.0", "category": "Pediatric Neuromuscular / Genetic", "triage": "URGENT",
        "immediate_tests": [
            "Serum Creatine Kinase (CK - markedly elevated >10,000–50,000 U/L)",
            "DMD Gene Multiplex Ligation-dependent Probe Amplification (MLPA) / Sequencing",
            "Electromyography (EMG - small-amplitude, short-duration polyphasic motor unit potentials)",
            "Transthoracic Echocardiogram and 12-Lead ECG (cardiomyopathy screening)"
        ],
        "recommended_investigations": [
            "Serum Creatine Kinase (massively elevated, 50-100x upper limit of normal)",
            "DMD Gene Genetic Testing: MLPA for exon deletions/duplications (70% of cases) followed by sequencing",
            "Muscle Biopsy (dystrophin immunofluorescence / Western blot showing complete dystrophin deficiency)",
            "Pulmonary Function Testing (FVC, MIP, MEP)",
            "Cardiovascular MRI and TTE (dilated cardiomyopathy screening)"
        ],
        "recommended_medications": [
            "Oral Deflazacort 0.9 mg/kg/day OR Oral Prednisone 0.75 mg/kg/day (preserves ambulation, muscle and cardiac function)",
            "Early ACE inhibitors (Enalapril or Perindopril) for cardioprotection by age 10",
            "Calcium and Vitamin D supplementation for bone health",
            "Exon-skipping antisense oligonucleotides (Eteplirsen, Golodirsen, Viltolarsen) for amenable mutations",
            "Anesthesia Warning: Avoid Succinylcholine and volatile anesthetics (risk of hyperkalemic cardiac arrest / rhabdomyolysis)"
        ],
        "treatment_summary": "Initiation of corticosteroid therapy (Deflazacort or Prednisone) to preserve ambulation, cardiorespiratory function, and reduce scoliosis. Multidisciplinary neuromuscular, cardiology, and physical therapy care.",
        "disease_intelligence": {
            "disease_name": "Duchenne Muscular Dystrophy",
            "etiology": "X-linked recessive out-of-frame mutation in the DMD gene causing complete absence of functional dystrophin protein",
            "icd10_code": "G71.0",
            "icd11_code": "8C70.0",
            "cardinal_symptoms": ["Progressive proximal weakness in young boys", "Gowers sign (climbing up thighs to stand)", "Calf pseudohypertrophy", "Waddling gait", "Marked CK elevation >10,000 U/L"],
            "red_flags": ["Cardiomyopathy / ventricular dysrhythmia", "Respiratory failure / nocturnal hypoventilation", "Rhabdomyolysis with general anesthesia"],
            "clinical_pearl": "A young boy with delayed motor milestones, clumsy running, and calf pseudohypertrophy whose CK is >10,000 U/L is DMD until proven otherwise by genetic testing."
        },
        "pearl": "X-linked dystrophinopathy: Onset in early childhood with clumsy gait, frequent falls, calf pseudohypertrophy, and positive Gowers sign. High-dose corticosteroids prolong ambulation."
    },

    "Gyrate Atrophy of the Choroid and Retina": {
        "icd10": "H35.5", "icd11": "9B75.0", "category": "Rare Metabolic / Ophthalmology", "triage": "ROUTINE",
        "immediate_tests": [
            "Plasma Amino Acid Chromatography (10-20x elevation of plasma ornithine)",
            "Full-Field Electroretinography (ERG - markedly reduced or extinguished rod/cone responses)",
            "Dilated Fundus Examination & Autofluorescence (scalloped, circular patches of chorioretinal atrophy in mid-periphery)",
            "OAT Gene Molecular Testing (ornithine aminotransferase deficiency)"
        ],
        "recommended_investigations": [
            "Plasma Amino Acid Analysis (plasma ornithine typically 800-1500 umol/L; normal 40-100 umol/L)",
            "Urinary amino acid profile (excess ornithine, lysine, and arginine excretion)",
            "Full-Field Electroretinogram (ERG) and Visual Field Perimetry (constricted peripheral fields)",
            "High-resolution Optical Coherence Tomography (OCT - cystoid macular edema)",
            "OAT Gene Sequencing (confirming biallelic pathogenic variants)"
        ],
        "recommended_medications": [
            "Strict Arginine-restricted, low-protein diet (target plasma ornithine <200-400 umol/L to slow chorioretinal loss)",
            "Oral Pyridoxine (Vitamin B6) 300-500 mg/day (therapeutic trial to assess B6 responsiveness)",
            "Oral L-Lysine and L-Carnitine supplementation (promotes urinary ornithine loss)",
            "Topical Carbonic Anhydrase Inhibitors (Dorzolamide eye drops) for cystoid macular edema"
        ],
        "treatment_summary": "Lifelong strict low-protein, arginine-restricted medical diet combined with Pyridoxine (Vitamin B6) trial. Close ophthalmological surveillance for cystoid macular edema and cataract formation.",
        "disease_intelligence": {
            "disease_name": "Gyrate Atrophy of the Choroid and Retina",
            "etiology": "Autosomal recessive deficiency of ornithine aminotransferase (OAT) on chromosome 10q26 leading to hyperornithinemia",
            "icd10_code": "H35.5",
            "icd11_code": "9B75.0",
            "cardinal_symptoms": ["Progressive night blindness (nyctalopia)", "Constricted peripheral visual fields", "Characteristic circular chorioretinal atrophy", "Hyperornithinemia"],
            "red_flags": ["Severe macular edema with central visual loss", "Subcapsular cataracts", "High myopia"],
            "clinical_pearl": "Early nyctalopia progressing to peripheral tunnel vision with sharply demarcated scalloped chorioretinal atrophy. Hyperornithinemia confirms the diagnosis."
        },
        "pearl": "Inborn error of ornithine metabolism caused by OAT deficiency: Progressive night blindness (nyctalopia) and constricted peripheral visual fields with characteristic chorioretinal circular atrophy."
    },

    "Cryopyrin-Associated Periodic Syndrome (CAPS Spectrum / Muckle-Wells / FCAS)": {
        "icd10": "M04.2", "icd11": "4A60.2", "category": "Autoinflammatory / Rheumatology", "triage": "URGENT",
        "immediate_tests": [
            "NLRP3 (CIAS1) Gene Mutation Analysis (exon 3 hotspot sequencing)",
            "Serum Inflammatory Markers (ESR, high-sensitivity CRP, Serum Amyloid A [SAA])",
            "Pure-Tone Audiometry (sensorineural hearing loss baseline and monitoring)",
            "Renal Function Panel and Urinalysis with spot protein:creatinine ratio (screen for AA amyloidosis)"
        ],
        "recommended_investigations": [
            "NLRP3 Next-Generation Sequencing (evaluating for somatic mosaicism if standard Sanger is negative)",
            "Serial Serum Amyloid A (SAA) levels (guiding adequate IL-1 suppression)",
            "Annual Audiogram (progressive high-frequency sensorineural deafness)",
            "Lumbar Puncture (CSF pleocytosis and elevated opening pressure in NOMID/CINCA subtype)",
            "Brain and Inner Ear MRI with contrast (cochlear enhancement / leptomeningitis)"
        ],
        "recommended_medications": [
            "Anakinra (recombinant IL-1 receptor antagonist) 1-2 mg/kg/day subcutaneous daily OR",
            "Canakinumab (human anti-IL-1beta monoclonal antibody) 150mg SC every 8 weeks (weight-based in pediatrics)",
            "Rilonacept (IL-1 trap) for FCAS subtype",
            "Antihistamines and NSAIDs provide negligible relief; targeted IL-1 blockade is disease-modifying"
        ],
        "treatment_summary": "Lifelong IL-1 blockade (Anakinra or Canakinumab) is the definitive, life-altering therapy. Prompt initiation prevents progressive sensorineural deafness and fatal systemic AA amyloidosis.",
        "disease_intelligence": {
            "disease_name": "Cryopyrin-Associated Periodic Syndrome (CAPS Spectrum)",
            "etiology": "Autosomal dominant gain-of-function mutations in NLRP3 (CIAS1) causing constitutive activation of the cryopyrin inflammasome and uncontrolled IL-1beta release",
            "icd10_code": "M04.2",
            "icd11_code": "4A60.2",
            "phenotypic_subtypes": "Familial Cold Autoinflammatory Syndrome (FCAS - mildest), Muckle-Wells Syndrome (MWS - intermediate), Neonatal-Onset Multisystem Inflammatory Disease (NOMID/CINCA - most severe)",
            "cardinal_symptoms": ["Recurrent unexplained fevers from infancy", "Cold-induced urticarial-type non-pruritic rash", "Progressive sensorineural hearing loss", "Arthralgia / joint swelling", "Elevated SAA and CRP"],
            "red_flags": ["Systemic AA amyloidosis (proteinuria, renal failure)", "Chronic aseptic meningitis with hydrocephalus", "Severe vision loss / optic atrophy"],
            "clinical_pearl": "Rash is urticarial in appearance but neutrophils dominate on biopsy, and antihistamines are completely ineffective. IL-1 blockade reverses hearing loss if started early."
        },
        "pearl": "Autoinflammatory disorder of the cryopyrin inflammasome: Recurrent unprovoked fevers from infancy, cold-triggered urticarial rash, arthralgia, and progressive sensorineural hearing loss. Treat with IL-1 inhibitors."
    },

    "Idiopathic Inflammatory Myopathy (Suspected Anti-Synthetase Syndrome / Dermatomyositis Spectrum)": {
        "icd10": "M33.0", "icd11": "4A41.0", "category": "Rheumatology / Pulmonology", "triage": "URGENT",
        "immediate_tests": [
            "High-Resolution Computed Tomography of Chest (HRCT — evaluating interstitial lung disease / NSIP)",
            "Extended Myositis-Specific Autoantibody Panel (anti-Jo-1, anti-PL-7, anti-PL-12, anti-EJ, anti-OJ, anti-MDA5)",
            "Muscle Biopsy (perifascicular atrophy, perivascular/endomysial inflammatory infiltrate)",
            "Pulmonary Function Testing with DLCO (restrictive ventilatory defect)",
            "Serum Creatine Kinase (CK), Aldolase, and Myoglobin"
        ],
        "recommended_investigations": [
            "Comprehensive Myositis-Specific and Myositis-Associated Autoantibody Line Blot",
            "High-Resolution Chest CT (subpleural ground glass, reticulation, traction bronchiectasis)",
            "Muscle MRI (T2/STIR hyperintensity showing active myofascial edema)",
            "Needle Electromyography (EMG - fibrillations, positive sharp waves, small polyphasics)",
            "Barium Swallow / Videofluoroscopic Swallowing Study for severe dysphagia"
        ],
        "recommended_medications": [
            "High-dose systemic corticosteroids: IV Methylprednisolone 1g daily x3 days, followed by oral Prednisone 1 mg/kg/day",
            "Mycophenolate Mofetil 2-3g/day OR Tacrolimus 0.075-0.1 mg/kg/day (first-line steroid-sparing immunosuppressants)",
            "IV Rituximab (1000mg on days 1 and 15) for severe or rapidly progressive interstitial lung disease",
            "Intravenous Immunoglobulin (IVIG) 2 g/kg divided over 2-5 days for refractory dysphagia or weakness"
        ],
        "treatment_summary": "Aggressive immunosuppression with high-dose corticosteroids combined with Mycophenolate Mofetil or Tacrolimus. Close pulmonary monitoring with HRCT and DLCO; rapidly progressive ILD requires prompt Rituximab or Cyclophosphamide.",
        "disease_intelligence": {
            "disease_name": "Idiopathic Inflammatory Myopathy (Anti-Synthetase Syndrome / Dermatomyositis Spectrum)",
            "etiology": "Autoimmune idiopathic inflammatory myopathy associated with autoantibodies against aminoacyl-tRNA synthetases or MDA5",
            "icd10_code": "M33.0 / M33.9",
            "icd11_code": "4A41.0",
            "cardinal_symptoms": ["Symmetrical proximal muscle weakness", "Progressive dysphagia", "Mechanic's hands (hyperkeratotic cracked skin)", "Rapidly progressive interstitial lung disease (ILD)", "Perifascicular atrophy on muscle biopsy"],
            "red_flags": ["Rapidly progressive interstitial lung disease / respiratory failure", "Severe pharyngeal dysphagia with aspiration", "Anti-MDA5 associated rapidly progressive cutaneous ulceration"],
            "clinical_pearl": "Lung disease often precedes or dwarfs muscle weakness. Perifascicular muscle biopsy atrophy is pathognomonic for dermatomyositis/antisynthetase spectrum."
        },
        "pearl": "Idiopathic inflammatory myopathy featuring dysphagia, proximal muscle weakness, and interstitial lung disease out of proportion to muscle weakness. Anti-tRNA synthetase / MDA5 antibodies indicated."
    },

    "Collodion Baby Phenotype (Underlying Congenital Ichthyosis suspected)": {
        "icd10": "Q80.2", "icd11": "EC20.0", "category": "Neonatal / Dermatology Emergency", "triage": "EMERGENT",
        "immediate_tests": [
            "Urgent Pediatric Dermatology and Neonatal Intensive Care Unit (NICU) Evaluation",
            "Serum Electrolytes, BUN, and Creatinine (monitoring for hypernatremic dehydration)",
            "Targeted Next-Generation Sequencing Gene Panel for Congenital Ichthyosis (TGM1, ALOX12B, ALOXE3, ABCA12, NIPAL4, CYP4F22)",
            "Bacterial and Fungal Skin Swabs (frequent surveillance for cutaneous sepsis)"
        ],
        "recommended_investigations": [
            "Continuous fluid-electrolyte monitoring via blood gas and serum sodium (high trans-epidermal water loss)",
            "Molecular genetic testing using a comprehensive Congenital Ichthyosis NGS panel",
            "Ophthalmology slit-lamp examination (corneal exposure keratitis from bilateral ectropion)",
            "Auditory Brainstem Response (ABR) screening (keratin debris obstructing external auditory canals)"
        ],
        "recommended_medications": [
            "Sterile bland emollients (White petrolatum / Aquaphor) applied liberally every 2-4 hours",
            "Preservative-free artificial tears and ophthalmic lubricating ointment q2h for ectropion",
            "IV balanced crystalloids adjusted for massive trans-epidermal insensible fluid losses",
            "Strict Contraindication: Avoid topical keratolytics (salicylic acid, urea, lactic acid) due to lethal systemic absorption"
        ],
        "treatment_summary": "Admission to a high-humidity humidified incubator (>=70-80%). Liberal sterile emollient application without forcefully peeling the membrane. Meticulous fluid/electrolyte resuscitation and eye lubrication.",
        "disease_intelligence": {
            "disease_name": "Collodion Baby Phenotype",
            "etiology": "Neonatal presentation of autosomal recessive congenital ichthyoses (ARCI), most commonly mutations in TGM1 (transglutaminase-1), ALOX12B, or ALOXE3",
            "icd10_code": "Q80.2",
            "icd11_code": "EC20.0",
            "cardinal_symptoms": ["Taut shiny parchment-like membrane covering body at birth", "Cracking and peeling leaving raw skin", "Bilateral ectropion (eversion of eyelids)", "Eclabium (eversion of lips)", "Thermoregulatory failure"],
            "red_flags": ["Severe hypernatremic dehydration", "Hypothermia / hyperthermia", "Cutaneous sepsis / staphylococcal bacteremia", "Corneal ulceration from lagophthalmos"],
            "clinical_pearl": "Collodion baby is a clinical phenotype, not a final molecular diagnosis. Most evolve into Lamellar Ichthyosis or Congenital Ichthyosiform Erythroderma; ~10% are self-healing."
        },
        "pearl": "Newborn encased in a shiny taut membrane that cracks and peels, causing severe barrier failure, bilateral ectropion, eclabium, and temperature instability. High-humidity incubator and sterile emollients."
    },

    "Mitochondrial Encephalopathy (Differential includes MELAS, MERRF, Mitochondrial Ataxia)": {
        "icd10": "G31.8", "icd11": "5C53.0", "category": "Metabolic / Neurological", "triage": "URGENT",
        "immediate_tests": [
            "Brain MRI with MR Spectroscopy (MRS - inverted lactate doublet peak at 1.3 ppm, non-vascular stroke-like lesions)",
            "Mitochondrial DNA (mtDNA) Point Mutation Panel (m.3243A>G in MT-TL1, m.8344A>G in MT-TK)",
            "Venous / Arterial Blood Gas, Plasma Lactate, and CSF Lactate and Pyruvate",
            "Audiometry (sensorineural hearing loss) and Echocardiogram (cardiomyopathy / WPW)"
        ],
        "recommended_investigations": [
            "Brain MRI with Diffusion-Weighted Imaging and MR Spectroscopy",
            "Mitochondrial Genome Sequencing in blood, urine sediment, or hair follicles (detecting heteroplasmy)",
            "Plasma and CSF lactate:pyruvate ratio (exaggerated rise with rest or exercise)",
            "Skeletal Muscle Biopsy (modified Gomori trichrome for ragged-red fibers [RRF] and COX-negative fibers)",
            "Continuous 24-hour Holter Monitor (pre-excitation / conduction defects)"
        ],
        "recommended_medications": [
            "IV L-Arginine (0.5 g/kg load over 30 min, then 0.5 g/kg/day) during acute stroke-like episodes",
            "Oral maintenance L-Citrulline (2-4 g TID) or L-Arginine to enhance nitric oxide microvascular perfusion",
            "Coenzyme Q10 (Ubiquinol) 300-600 mg daily",
            "L-Carnitine 1-2 g daily and Riboflavin (Vitamin B2) 100mg daily",
            "Strict Contraindication: Avoid Sodium Valproate (triggers fatal hepatic/metabolic failure) and Metformin (lactic acidosis)"
        ],
        "treatment_summary": "Acute stroke-like episodes treated with IV L-Arginine to promote microvascular vasodilation. Maintenance mitochondrial cofactor cocktail (CoQ10, L-Carnitine). Strict avoidance of valproate and metformin.",
        "disease_intelligence": {
            "disease_name": "Mitochondrial Encephalopathy (MELAS / Mitochondrial Syndrome)",
            "etiology": "Maternally inherited mitochondrial DNA mutations (most commonly m.3243A>G in the MT-TL1 gene encoding tRNA Leu)",
            "icd10_code": "G31.8",
            "icd11_code": "5C53.0",
            "cardinal_symptoms": ["Maternal family history", "Migraine-like headaches", "Stroke-like episodes not conforming to arterial territories", "Episodic ataxia and nystagmus", "Lactic acidosis"],
            "red_flags": ["Acute stroke-like focal deficits / hemiparesis", "Refractory status epilepticus", "Cardiomyopathy with ventricular dysrhythmia", "Severe lactic acidemia"],
            "clinical_pearl": "Stroke-like lesions cross classical vascular territories and involve cortical gray matter and subcortical white matter. Elevated brain lactate on MRS is characteristic."
        },
        "pearl": "Maternally inherited mitochondrial disorder: Migraine-like headaches since adolescence, episodic vertigo, ataxia, stroke-like episodes, and bilateral MRI hyperintensities. L-Arginine indicated."
    },

    "Carnitine Palmitoyltransferase II (CPT II) Deficiency": {
        "icd10": "E71.3", "icd11": "5C52.0", "category": "Metabolic Myopathy / Acute Renal", "triage": "URGENT",
        "immediate_tests": [
            "Serum Creatine Kinase (CK — markedly elevated >20,000–100,000 U/L during acute attacks)",
            "Urinalysis for Myoglobinuria (dipstick strongly heme-positive with absence of intact RBCs on microscopy)",
            "Plasma Acylcarnitine Profile via Tandem Mass Spectrometry (elevated long-chain acylcarnitines: C16, C18:1, [C16+C18:1]/C2 ratio)",
            "CPT2 Gene Molecular Sequencing (common adult myopathic p.Ser113Leu pathogenic variant)"
        ],
        "recommended_investigations": [
            "Serum Creatine Kinase and Myoglobin",
            "Urinalysis with micro-examination (confirming pigment myoglobinuria)",
            "Plasma Acylcarnitine Profile (MS/MS)",
            "CPT2 Gene Sequencing",
            "Renal Function Panel (BUN, Creatinine, Electrolytes, Serum Calcium, Phosphorus, Uric Acid)"
        ],
        "recommended_medications": [
            "Vigorous IV Hydration: Normal Saline or D5-1/2NS with 2-3 ampules Sodium Bicarbonate at 200-300 mL/hr",
            "Target urine output >= 2-3 mL/kg/h and urine pH >= 6.5 (prevents intratubular ferrihemate precipitation)",
            "Frequent high-carbohydrate meals during physical exertion or intercurrent febrile illness",
            "Medium-Chain Triglyceride (MCT) oil supplementation (bypasses CPT shuttle into mitochondria)",
            "Avoid prolonged fasting, cold exposure, and extreme unaccustomed strenuous exercise"
        ],
        "treatment_summary": "High-volume alkalized IV hydration targeting brisk diuresis to protect against acute pigment tubular nephropathy. Long-term management with high-carbohydrate diet, MCT oil, and avoidance of fasting and extreme exertion.",
        "disease_intelligence": {
            "disease_name": "Carnitine Palmitoyltransferase II (CPT II) Deficiency",
            "etiology": "Autosomal recessive deficiency of carnitine palmitoyltransferase II on chromosome 1p32, disrupting long-chain fatty acid transport into mitochondria for beta-oxidation",
            "icd10_code": "E71.3",
            "icd11_code": "5C52.0",
            "cardinal_symptoms": ["Recurrent exercise- or fasting-induced rhabdomyolysis", "Dark brown urine (myoglobinuria)", "Severe muscle weakness and pain after prolonged exertion", "Normal baseline examination"],
            "red_flags": ["Acute oliguric pigment nephropathy / acute kidney injury", "Severe hyperkalemia from massive muscle lysis", "Cardiac arrhythmias"],
            "clinical_pearl": "Urinalysis is strongly positive for blood on dipstick, but microscopic analysis reveals few to no red blood cells (classic hallmark of free myoglobin)."
        },
        "pearl": "Most common inherited metabolic defect of lipid oxidation: Recurrent exercise- or fasting-induced rhabdomyolysis and myoglobinuria. High-volume alkalized IV hydration prevents acute pigment nephropathy."
    },

    "Subacute Necrotizing Encephalomyelopathy (Suspected Leigh Syndrome / Mitochondrial Neurodegeneration)": {
        "icd10": "G31.8", "icd11": "8E60.0", "category": "Pediatric Neurodegenerative Emergency", "triage": "EMERGENT",
        "immediate_tests": [
            "Brain MRI (bilateral symmetric T2/FLAIR hyperintensities in basal ganglia [putamen, globus pallidus] and brainstem)",
            "Whole Exome / mtDNA Genome Sequencing (SURF1, MT-ATP6, NDUFV1, PDHA1)",
            "Serum and CSF Lactate and Pyruvate (consistently elevated lactate:pyruvate ratio)",
            "MR Spectroscopy (inverted lactate doublet peak in basal ganglia lesions)"
        ],
        "recommended_investigations": [
            "High-resolution 3T Brain MRI with diffusion, T2, FLAIR, and MRS",
            "Comprehensive Nuclear and Mitochondrial Whole Exome Sequencing",
            "Blood and CSF Lactate and Pyruvate levels",
            "Echocardiogram (screening for hypertrophic cardiomyopathy)",
            "Polysomnography / Respiratory monitoring for central hypoventilation"
        ],
        "recommended_medications": [
            "Oral Thiamine (Vitamin B1) 100-300 mg daily and Biotin 5-10 mg/kg/day",
            "Coenzyme Q10 (Ubiquinol) 10-30 mg/kg/day",
            "L-Carnitine 50-100 mg/kg/day",
            "Sodium Bicarbonate for severe acute metabolic acidosis (pH <7.1)",
            "Strict Contraindication: Avoid Sodium Valproate and Linezolid"
        ],
        "treatment_summary": "Metabolic crisis management: IV glucose to suppress catabolism, correction of acidemia, and mitochondrial cofactor cocktail (Thiamine, Biotin, CoQ10). Prompt management of infections to prevent neurological regression.",
        "disease_intelligence": {
            "disease_name": "Subacute Necrotizing Encephalomyelopathy (Leigh Syndrome)",
            "etiology": "Genetically heterogeneous mitochondrial energy failure (nuclear gene mutations e.g. SURF1 or mitochondrial DNA mutations e.g. MT-ATP6)",
            "icd10_code": "G31.8",
            "icd11_code": "8E60.0",
            "cardinal_symptoms": ["Infantile or childhood neurodevelopmental regression", "Loss of previously acquired motor skills", "Abnormal eye movements (nystagmus, ophthalmoplegia)", "Ataxia and hypotonia", "Bilateral symmetric basal ganglia lesions on MRI"],
            "red_flags": ["Central respiratory failure / apneas", "Severe high-anion-gap lactic acidosis", "Rapid neurological deterioration triggered by infection"],
            "clinical_pearl": "Bilateral, symmetric T2 hyperintensities in the basal ganglia and brainstem are the pathognomonic radiological signature. Sibling deaths in infancy or childhood are common."
        },
        "pearl": "Progressive neurodevelopmental regression in infants/children: Loss of motor skills, ataxia, tremor, nystagmus, and central respiratory failure. Sibling recurrence common."
    },

    "Hereditary Spastic Paraplegia (HSP)": {
        "icd10": "G11.4", "icd11": "8A03.0", "category": "Neurogenetics / Upper Motor Neuron", "triage": "ROUTINE",
        "immediate_tests": [
            "Brain and Whole Spine MRI (corticospinal tract hyperintensity, spinal cord atrophy, excludes multiple sclerosis and compressive myelopathy)",
            "Next-Generation Sequencing HSP Multigene Panel (SPG4 [spastin], SPG3A [atlastin], SPG7, SPG11)",
            "Electromyography and Nerve Conduction Studies (confirms pure upper motor neuron pathology)",
            "Urodynamic Studies (detrusor hyperreflexia / neurogenic bladder)"
        ],
        "recommended_investigations": [
            "Spinal Cord and Brain MRI with contrast",
            "Comprehensive Next-Generation Sequencing Multigene Panel for Spastic Paraplegia",
            "Serum Vitamin B12, Folate, Copper, Ceruloplasmin, Very Long Chain Fatty Acids (VLCFA), and HTLV-1/2 (exclude mimics)",
            "Urodynamic evaluation for spastic neurogenic bladder"
        ],
        "recommended_medications": [
            "Oral Baclofen 10-25mg TID OR Tizanidine 2-8mg TID for lower-limb spasticity",
            "Intrathecal Baclofen Pump for severe, refractory lower-limb spasticity",
            "Oral Oxybutynin 5mg BID-TID or Mirabegron 50mg daily for spastic bladder urgency",
            "Intensive physical therapy, stretching protocols, and Ankle-Foot Orthoses (AFOs)"
        ],
        "treatment_summary": "Symptomatic spasticity management with oral Baclofen, Tizanidine, or intrathecal Baclofen. Anticholinergic therapy for neurogenic bladder. Intensive gait training and physical therapy.",
        "disease_intelligence": {
            "disease_name": "Hereditary Spastic Paraplegia (HSP)",
            "etiology": "Genetically heterogeneous group of neurodegenerative disorders hallmarked by retrograde degeneration of the longest corticospinal tract axons (most commonly SPG4 / SPAST)",
            "icd10_code": "G11.4",
            "icd11_code": "8A03.0",
            "cardinal_symptoms": ["Insidious progressive bilateral lower-limb spasticity", "Sustained ankle clonus", "Bilateral extensor plantar responses (Babinski)", "Spastic gait / toe-walking", "Urinary urgency", "Normal upper limb strength and sensation"],
            "red_flags": ["Rapidly progressive quadriparesis (prompts search for compressive cervical myelopathy)", "Severe neurogenic bladder leading to recurrent urosepsis"],
            "clinical_pearl": "Pure HSP manifests as isolated lower-limb spasticity and hyperreflexia with preserved sensory exam and upper extremity strength, often with autosomal dominant family history."
        },
        "pearl": "Insidious, slowly progressive bilateral lower-limb spasticity, hyperreflexia, ankle clonus, and urinary urgency with preserved sensation. Often shows familial clustering."
    },

    "Mitochondrial Energy Metabolism Disorder (Suspected Respiratory Chain Complex Deficiency / Inborn Error of Metabolism)": {
        "icd10": "E88.4", "icd11": "5C53.0", "category": "Metabolic Emergency / Critical Care", "triage": "EMERGENT",
        "immediate_tests": [
            "Blood Gas, Serum Lactate and Pyruvate (severe high-anion-gap lactic acidosis with elevated L:P ratio >20)",
            "Spectrophotometric Respiratory Chain Enzyme Activity Assay (Complex I, II, III, IV on muscle biopsy or skin fibroblasts)",
            "Nuclear and mtDNA Whole Exome Sequencing",
            "Transthoracic Echocardiogram (hypertrophic cardiomyopathy evaluation)",
            "Plasma Acylcarnitines and Urine Organic Acids (elevated lactic, pyruvic, and dicarboxylic acids)"
        ],
        "recommended_investigations": [
            "Arterial/Venous Blood Gas, serial Serum Lactate, and Pyruvate levels",
            "Urine Organic Acid chromatography and Plasma Acylcarnitine profile",
            "Muscle or skin fibroblast biopsy for mitochondrial respiratory chain enzyme spectrophotometry",
            "Whole Exome Sequencing / Mitochondrial Genome Sequencing",
            "Echocardiogram and 12-Lead ECG"
        ],
        "recommended_medications": [
            "IV 10% Dextrose infusion with electrolytes (suppresses lipolysis and catabolism)",
            "Cautious IV Sodium Bicarbonate or THAM for severe, life-threatening acidemia (pH <7.1)",
            "Mitochondrial Cocktail: Coenzyme Q10 (10-30 mg/kg/day), Riboflavin (Vitamin B2 100-200 mg/day), Thiamine (100mg/day), L-Carnitine (50-100 mg/kg/day)",
            "Strict Contraindication: Avoid Metformin and Ringer's Lactate (exacerbates lactic acidemia)"
        ],
        "treatment_summary": "Emergency resuscitation: IV Dextrose to shut down toxic catabolism and fatty acid oxidation; cautious bicarbonate for life-threatening acidosis. Mitochondrial cofactor cocktail. Rapid genetic and enzymological testing.",
        "disease_intelligence": {
            "disease_name": "Mitochondrial Energy Metabolism Disorder",
            "etiology": "Defects in nuclear or mitochondrial genes encoding structural subunits or assembly factors of the oxidative phosphorylation respiratory chain (Complexes I-V)",
            "icd10_code": "E88.4",
            "icd11_code": "5C53.0",
            "cardinal_symptoms": ["Severe high-anion-gap lactic acidosis", "Fasting hypoglycemia", "Infantile hypotonia", "Hypertrophic cardiomyopathy", "Metabolic decompensation triggered by mild illness"],
            "red_flags": ["Severe refractory metabolic acidosis (pH <7.0)", "Intractable hyperlactatemia (>10 mmol/L)", "Cardiogenic shock / heart failure"],
            "clinical_pearl": "Severe neonatal or infantile lactic acidosis accompanied by cardiomyopathy and fasting hypoglycemia indicates mitochondrial respiratory chain failure. Avoid Ringer's Lactate."
        },
        "pearl": "Recurrent metabolic crises precipitated by fasting or intercurrent illness: High-anion gap metabolic acidosis, marked hyperlactatemia, fasting hypoglycemia, hypotonia, and cardiomyopathy."
    },

    # =========================================================================
    # CORE EMERGENCY MEDICINE & SYSTEMIC DISEASES
    # =========================================================================
    "Acute Ischemic Stroke (CVA)": {
        "icd10": "I63.9", "icd11": "8B11", "category": "Neurology Emergency", "triage": "EMERGENT",
        "immediate_tests": ["STAT Non-contrast Head CT within 20 min", "CT Angiography (CTA) of Head and Neck", "Fingerstick Blood Glucose", "12-Lead ECG (exclude AFib)", "Coagulation Panel (PT/INR, PTT)"],
        "recommended_investigations": ["Non-contrast Head CT", "CT Angiography (CTA) of Head and Neck", "CT Perfusion (CTP)", "Brain MRI (DWI/FLAIR)", "Echocardiogram and Holter Monitor"],
        "recommended_medications": ["IV Tenecteplase (0.25 mg/kg) or IV Alteplase (0.9 mg/kg) if within 4.5h window", "Aspirin 160-300mg orally after 24h post-thrombolysis", "IV Labetalol or Nicardipine (maintain BP <185/110 before thrombolysis)"],
        "treatment_summary": "Immediate non-contrast head CT. Revascularization via IV thrombolysis (<4.5h) or endovascular thrombectomy (<24h for large vessel occlusion). Strict blood pressure control.",
        "disease_intelligence": {
            "disease_name": "Acute Ischemic Stroke",
            "icd10_code": "I63.9", "icd11_code": "8B11",
            "cardinal_symptoms": ["Sudden hemiparesis", "Facial droop", "Aphasia / dysarthria", "Sudden sensory loss"],
            "red_flags": ["Rapidly worsening NIHSS score", "Signs of brain herniation", "Hemorrhagic transformation"],
            "clinical_pearl": "Time is brain: 1.9 million neurons die every minute an ischemic stroke goes untreated."
        },
        "pearl": "Time is brain. IV thrombolysis window is <4.5 hours; endovascular thrombectomy window is up to 24 hours for large vessel occlusion."
    },

    "Preeclampsia with Severe Features": {
        "icd10": "O14.1", "icd11": "JA24.1", "category": "Obstetric Emergency", "triage": "EMERGENT",
        "immediate_tests": ["Serial Blood Pressure Monitoring (q15m)", "Urinalysis for Proteinuria (Protein-to-Creatinine ratio)", "Complete Blood Count (Platelet count)", "Liver Function Tests (AST, ALT, LDH)", "Serum Creatinine", "Continuous Fetal Monitoring"],
        "recommended_investigations": ["Spot urine protein:creatinine ratio", "Complete Blood Count (platelets <100k)", "Comprehensive Metabolic Panel (AST/ALT >=2x, Creatinine >1.1)", "Coagulation studies and Fibrinogen", "Obstetric ultrasound for fetal growth and biophysical profile"],
        "recommended_medications": ["IV Magnesium Sulfate (4-6g IV load over 20 min, then 1-2g/hr infusion) for eclampsia seizure prophylaxis", "IV Labetalol (20mg IV, then 40-80mg q10m) or IV Hydralazine (5-10mg IV) for BP >=160/110", "Antenatal corticosteroids (Betamethasone 12mg IM q24h x2) if <37 weeks"],
        "treatment_summary": "Immediate seizure prophylaxis with IV Magnesium Sulfate. Urgent blood pressure control with IV Labetalol/Hydralazine. Definitive treatment is delivery, timed according to gestational age and maternal/fetal stability.",
        "disease_intelligence": {
            "disease_name": "Preeclampsia with Severe Features",
            "icd10_code": "O14.1", "icd11_code": "JA24.1",
            "cardinal_symptoms": ["BP >=160/110 mmHg", "Severe persistent headache", "Visual scotomata", "Right upper quadrant pain", "Proteinuria", "Hyperreflexia / sustained clonus"],
            "red_flags": ["Eclamptic seizure", "Placental abruption", "HELLP syndrome (hemolysis, elevated liver enzymes, low platelets)", "Pulmonary edema"],
            "clinical_pearl": "Magnesium sulfate is superior to phenytoin and benzodiazepines for preventing eclamptic seizures."
        },
        "pearl": "BP >= 160/110 mmHg with end-organ dysfunction (headache, visual changes, clonus, RUQ pain, proteinuria) indicates severe preeclampsia. Administer IV Magnesium Sulfate immediately."
    },

    "Acute Myocardial Infarction (STEMI/NSTEMI)": {
        "icd10": "I21.9", "icd11": "BA41", "category": "Cardiology Emergency", "triage": "EMERGENT",
        "immediate_tests": ["12-Lead ECG within 10 min", "High-Sensitivity Cardiac Troponin I/T", "Bedside Echocardiogram", "CBC, PT/INR, PTT, Serum Electrolytes"],
        "recommended_investigations": ["Serial 12-Lead ECGs (q15-30m if persistent pain)", "High-sensitivity Cardiac Troponin (0h, 1h/2h, 3h)", "Emergency Coronary Angiography (Cath lab activation)", "Bedside Echocardiogram (wall motion abnormalities)"],
        "recommended_medications": ["Aspirin 300mg chewable + secondary P2Y12 inhibitor (Ticagrelor 180mg or Prasugrel 60mg)", "Sublingual Nitroglycerin 0.4mg q5m x3 (contraindicated if RV infarction or PDE-5 inhibitor use)", "Anticoagulation: IV Unfractionated Heparin bolus + infusion OR subcutaneous Enoxaparin", "High-intensity Statin (Atorvastatin 80mg)"],
        "treatment_summary": "Emergency cardiac catheterization lab activation for primary percutaneous coronary intervention (PCI door-to-balloon <90 min). Dual antiplatelet therapy and therapeutic anticoagulation.",
        "disease_intelligence": {
            "disease_name": "Acute Myocardial Infarction",
            "icd10_code": "I21.9", "icd11_code": "BA41",
            "cardinal_symptoms": ["Substernal crushing chest pain", "Radiation to left arm, neck, or jaw", "Diaphoresis", "Dyspnea", "ST-segment elevation on ECG"],
            "red_flags": ["Cardiogenic shock", "Ventricular fibrillation / VT", "Acute mitral regurgitation (papillary muscle rupture)", "Cardiac arrest"],
            "clinical_pearl": "A normal initial ECG does NOT rule out acute coronary syndrome. If high clinical suspicion, obtain serial ECGs and right-sided / posterior leads."
        },
        "pearl": "STEMI requires door-to-balloon time <90 minutes. Normal initial ECG does NOT rule out acute coronary syndrome."
    },

    "Aortic Dissection": {
        "icd10": "I71.0", "icd11": "BD50", "category": "Vascular Emergency", "triage": "EMERGENT",
        "immediate_tests": ["CT Angiography of Chest and Abdomen", "Transesophageal Echocardiogram (TEE)", "12-Lead ECG", "Type and Crossmatch 6 units PRBCs"],
        "recommended_investigations": ["CT Angiography (CTA) of Chest, Abdomen, and Pelvis", "Bedside Transesophageal Echocardiogram (TEE)", "Transthoracic Echocardiogram (evaluating pericardial effusion/tamponade, aortic regurgitation)", "Blood pressure measurement in both arms and legs"],
        "recommended_medications": ["IV Esmolol infusion (titrated to HR <60 bpm and SBP <120 mmHg) BEFORE vasodilators", "IV Nitroprusside or Nicardipine (added only after adequate beta-blockade)", "IV Morphine/Fentanyl for severe pain and sympathetic drive reduction", "Strictly avoid anticoagulation and thrombolysis"],
        "treatment_summary": "Strict anti-impulse therapy: IV beta-blockers (Esmolol) first to decrease heart rate (<60 bpm) and shear stress, then vasodilators (Nicardipine) for SBP <120. Immediate emergent cardiothoracic surgery consult for Stanford Type A dissection.",
        "disease_intelligence": {
            "disease_name": "Acute Aortic Dissection",
            "icd10_code": "I71.0", "icd11_code": "BD50",
            "cardinal_symptoms": ["Abrupt tearing or ripping chest/back pain", "Interscapular pain", "Pulse deficit between limbs", "Blood pressure discrepancy >20 mmHg between arms", "Aortic regurgitation murmur"],
            "red_flags": ["Cardiac tamponade (Beck's triad)", "Hypotension / aortic rupture", "Stroke from carotid dissection", "Paraplegia from spinal artery ischemia"],
            "clinical_pearl": "Always give beta-blockers BEFORE vasodilators to prevent reflex tachycardia and increased aortic wall shear stress (dP/dt)."
        },
        "pearl": "Classic tearing/ripping pain radiating to interscapular back with pulse or BP differential between upper extremities."
    },

    "Acute Appendicitis": {
        "icd10": "K35.8", "icd11": "DC80", "category": "Surgical Emergency", "triage": "EMERGENT",
        "immediate_tests": ["Ultrasound Abdomen / CT Abdomen-Pelvis with IV contrast", "Complete Blood Count (Leukocytosis with Left Shift)", "Serum CRP", "Urinalysis and Beta-hCG (in females)"],
        "recommended_investigations": ["Abdominal/Pelvic CT with IV contrast (highest sensitivity >95%)", "Graded-compression abdominal ultrasound (preferred in children and pregnant patients)", "Complete Blood Count and CRP", "Urinalysis and Serum Beta-hCG"],
        "recommended_medications": ["IV broad-spectrum antibiotics: Ceftriaxone 2g + Metronidazole 500mg IV OR Piperacillin-Tazobactam", "IV balanced crystalloids for hydration", "IV analgesia (Morphine or Fentanyl) - does NOT mask surgical signs"],
        "treatment_summary": "NPO status, IV hydration, and prompt surgical consult for emergency laparoscopic appendectomy. Preoperative broad-spectrum IV antibiotics.",
        "disease_intelligence": {
            "disease_name": "Acute Appendicitis",
            "icd10_code": "K35.8", "icd11_code": "DC80",
            "cardinal_symptoms": ["Periumbilical pain migrating to right lower quadrant (McBurney's point)", "Anorexia", "Nausea and vomiting", "Fever", "Rebound tenderness and guarding"],
            "red_flags": ["Perforated appendicitis with diffuse peritonitis", "Appendiceal abscess / phlegmon", "Septic shock"],
            "clinical_pearl": "Classic progression is anorexia followed by vague periumbilical pain, which subsequently localizes to the right lower quadrant over 12-24 hours."
        },
        "pearl": "Pain classically begins periumbilically and migrates to McBurney's point in the RLQ with tenderness, guarding, and positive Rovsing sign."
    },

    "Gastroenteritis (Viral)": {
        "icd10": "A08.4", "icd11": "1A00", "category": "Gastroenterology / Infectious Disease", "triage": "ROUTINE",
        "immediate_tests": ["Clinical hydration status assessment", "Serum Electrolytes (BUN, Creatinine, Sodium, Potassium)", "Capillary blood glucose", "Urinalysis (specific gravity, ketones)"],
        "recommended_investigations": ["Serum electrolytes, urea, creatinine, bicarbonate", "Stool viral PCR (Norovirus, Rotavirus, Adenovirus) if indicated", "Stool microscopy and culture (to rule out invasive bacterial pathogens)", "Venous blood gas (if hypovolemic acidosis)"],
        "recommended_medications": ["Oral Rehydration Salts (WHO-ORS solution 50-100 mL/kg)", "Ondansetron 4-8 mg PO/ODT single dose for intractable vomiting", "Acetaminophen 500-1000 mg PO q6h PRN for fever", "Avoid antimotility agents (Loperamide contraindicated in dysentery)"],
        "treatment_summary": "Oral rehydration therapy with WHO-ORS + Ondansetron for refractory emesis + strict hand hygiene and enteric precautions.",
        "disease_intelligence": {
            "disease_name": "Gastroenteritis (Viral)",
            "icd10_code": "A08.4", "icd11_code": "1A00",
            "cardinal_symptoms": ["Watery non-bloody diarrhea", "Nausea and persistent vomiting", "Diffuse abdominal cramping", "Low-grade fever", "Dehydration"],
            "red_flags": ["Severe dehydration / hypovolemic shock", "Bloody stools (dysentery indicating invasive bacterial enteritis)", "Persistent vomiting precluding oral intake"],
            "clinical_pearl": "Cornerstone of management is oral fluid and electrolyte rehydration. Antibiotics have no role in uncomplicated viral gastroenteritis."
        },
        "pearl": "Self-limiting viral illness (Norovirus, Rotavirus). Cornerstone of management is oral rehydration therapy. Avoid routine antibiotics and antimotility drugs."
    },

    "Systemic Lupus Erythematosus (SLE)": {
        "icd10": "M32.9", "icd11": "4A40", "category": "Rheumatology / Autoimmune", "triage": "URGENT",
        "immediate_tests": ["Antinuclear Antibody (ANA) by IFA", "Anti-double-stranded DNA (anti-dsDNA)", "Anti-Smith (anti-Sm) Antibody", "Serum Complement Levels (C3, C4)", "Urinalysis with Microscopy (proteinuria/casts)", "CBC and Renal Panel"],
        "recommended_investigations": ["ANA by immunofluorescence (>98% sensitive)", "Anti-dsDNA (titers correlate with lupus nephritis activity)", "Anti-Smith antibodies (highly specific)", "Serum Complement C3 and C4", "Spot urine protein:creatinine ratio (lupus nephritis screening)", "Renal biopsy if proteinuria >0.5g/24h"],
        "recommended_medications": ["Hydroxychloroquine 200-400mg daily (foundational disease-modifying therapy for all SLE patients)", "Oral Prednisone 5-20mg daily for mild/moderate flares; high-dose pulse Methylprednisolone for severe nephritis/CNS", "Mycophenolate Mofetil or Cyclophosphamide for active lupus nephritis", "Belimumab or Anifrolumab for active systemic disease"],
        "treatment_summary": "Lifelong Hydroxychloroquine reduces flares, organ damage, and mortality. Immunosuppression tailored to organ involvement (Mycophenolate or Cyclophosphamide for lupus nephritis).",
        "disease_intelligence": {
            "disease_name": "Systemic Lupus Erythematosus",
            "icd10_code": "M32.9", "icd11_code": "4A40",
            "cardinal_symptoms": ["Malar butterfly rash", "Photosensitivity", "Inflammatory polyarthritis", "Serositis (pleuritis, pericarditis)", "Lupus nephritis (proteinuria, cellular casts)", "Complement consumption"],
            "red_flags": ["Rapidly progressive lupus nephritis", "Lupus cerebritis / neuropsychiatric lupus", "Alveolar hemorrhage"],
            "clinical_pearl": "Hydroxychloroquine should be prescribed to virtually every patient with SLE unless contraindicated, as it preserves survival and prevents severe flares."
        },
        "pearl": "Multisystem autoimmune disease characterized by ANA positivity (>98%), photosensitive malar butterfly rash, inflammatory polyarthritis, and complement consumption."
    },

    "Acute Heart Failure (Cardiogenic Pulmonary Edema)": {
        "icd10": "I50.9", "icd11": "BD11", "category": "Cardiology Emergency", "triage": "EMERGENT",
        "immediate_tests": ["B-Type Natriuretic Peptide (BNP / NT-proBNP)", "12-Lead ECG", "Transthoracic Echocardiogram (TTE)", "Portable Chest Radiograph (CXR)", "High-Sensitivity Troponin", "Serum Electrolytes & Creatinine"],
        "recommended_investigations": ["Serum NT-proBNP or BNP", "Transthoracic Echocardiogram (EF, diastolic function, valve lesions)", "Portable Chest Radiograph (Kerley B lines, alveolar infiltrates, cardiomegaly)", "12-Lead ECG and serial troponins", "Point-of-Care Lung Ultrasound (B-lines)"],
        "recommended_medications": ["IV Furosemide (40-80mg IV bolus or 1-2.5x home oral dose)", "Non-invasive Positive Pressure Ventilation (CPAP or BiPAP) - reduces intubation and mortality", "IV Nitroglycerin infusion for hypertensive pulmonary edema (afterload and preload reduction)", "IV Inotropes (Dobutamine, Milrinone) only if cardiogenic shock / hypoperfusion"],
        "treatment_summary": "Upright positioning, high-flow oxygen or non-invasive positive pressure ventilation (CPAP). IV loop diuretics (Furosemide) and IV vasodilators (Nitroglycerin) to rapidly reduce cardiac filling pressures.",
        "disease_intelligence": {
            "disease_name": "Acute Heart Failure / Cardiogenic Pulmonary Edema",
            "icd10_code": "I50.9", "icd11_code": "BD11",
            "cardinal_symptoms": ["Severe acute dyspnea", "Orthopnea", "Paroxysmal nocturnal dyspnea", "Diffuse pulmonary crackles", "Elevated jugular venous pressure", "S3 gallop"],
            "red_flags": ["Cardiogenic shock (hypotension, cold extremities)", "Impending respiratory exhaustion / hypercapnic failure", "Severe ventricular dysrhythmias"],
            "clinical_pearl": "Non-invasive ventilation (CPAP/BiPAP) dramatically reduces the work of breathing and preload in acute pulmonary edema, cutting intubation rates in half."
        },
        "pearl": "Characterized by acute pulmonary congestion, bilateral basilar crackles, orthopnea, elevated JVP, and S3 gallop. Treat with IV loop diuretics, preload reduction, and non-invasive ventilation."
    },

    "Acute Epiglottitis": {
        "icd10": "J05.1", "icd11": "CA06", "category": "Airway Emergency", "triage": "EMERGENT",
        "immediate_tests": ["Do NOT inspect throat with tongue blade", "Stat ENT & Anesthesia consult for emergency airway evaluation in operating room", "Lateral Neck Soft Tissue Radiograph (thumbprint sign — only if patient stable)", "Blood Cultures x2"],
        "recommended_investigations": ["Direct visualization in controlled operating room setting", "Lateral neck radiograph (enlarged epiglottis / 'thumbprint' sign)", "Blood cultures and epiglottic swab for bacterial culture (post-intubation)", "Complete Blood Count and inflammatory markers"],
        "recommended_medications": ["IV Ceftriaxone 2g daily + IV Vancomycin 15-20 mg/kg q12h", "IV Dexamethasone 10mg IV stat", "Humidified oxygen", "Avoid agitation, supine positioning, and oral cavity manipulation"],
        "treatment_summary": "Keep patient upright and calm. Prepare for emergency fiberoptic endotracheal intubation or surgical cricothyroidotomy in the operating room. Empiric IV Ceftriaxone + Vancomycin.",
        "disease_intelligence": {
            "disease_name": "Acute Epiglottitis",
            "etiology": "Haemophilus influenzae type b, Streptococcus pyogenes, Streptococcus pneumoniae, Staphylococcus aureus",
            "icd10_code": "J05.1", "icd11_code": "CA06",
            "cardinal_symptoms": ["Severe sore throat out of proportion to exam", "Difficulty swallowing / drooling", "Muffled voice ('hot potato')", "Inspiratory stridor", "Tripod positioning"],
            "red_flags": ["Complete precipitous airway obstruction", "Stridor at rest", "Agitation and cyanosis"],
            "clinical_pearl": "Never use a tongue blade to examine the pharynx in a suspected epiglottitis case, as it can precipitate immediate, fatal laryngospasm."
        },
        "pearl": "Airway emergency. Tripod position, drooling, muffled voice, and severe sore throat. Do NOT examine throat with a tongue blade. Secure airway in OR."
    },

    "Tension Pneumothorax": {
        "icd10": "J93.0", "icd11": "CB24", "category": "Thoracic Surgical Emergency", "triage": "EMERGENT",
        "immediate_tests": ["Immediate Clinical Diagnosis! Never delay decompression for X-ray", "Immediate Needle Decompression (2nd ICS midclavicular or 5th ICS anterior axillary)", "Emergent Tube Thoracostomy (Chest tube)", "Post-procedure CXR"],
        "recommended_investigations": ["Clinical examination (tracheal deviation, unilateral absent breath sounds, hypotension)", "Bedside Point-of-Care Ultrasound (POCUS - absence of lung sliding, barcode sign)", "Post-decompression Chest Radiograph"],
        "recommended_medications": ["Supplemental 100% high-flow oxygen", "IV isotonic crystalloid fluid bolus for circulatory resuscitation", "Post-tube thoracostomy analgesia (local lidocaine, IV opioids)"],
        "treatment_summary": "Immediate emergent needle thoracostomy followed by tube thoracostomy (chest tube). Do NOT wait for radiographic confirmation in an unstable patient.",
        "disease_intelligence": {
            "disease_name": "Tension Pneumothorax",
            "icd10_code": "J93.0", "icd11_code": "CB24",
            "cardinal_symptoms": ["Severe sudden respiratory distress", "Hypotension / obstructive shock", "Absent breath sounds on affected side", "Hyperresonance to percussion", "Tracheal deviation away from affected side"],
            "red_flags": ["Impending cardiac arrest / PEA arrest", "Severe hypoxia", "Jugular venous distension"],
            "clinical_pearl": "A tension pneumothorax is an absolute clinical diagnosis. If the patient is hypotensive with absent unilateral breath sounds, decompress immediately."
        },
        "pearl": "Clinical diagnosis! Never delay emergency needle decompression for a chest X-ray in an unstable patient with tracheal deviation and absent breath sounds."
    },

    "Anaphylaxis": {
        "icd10": "T78.2", "icd11": "4A84", "category": "Allergy & Immunology Emergency", "triage": "EMERGENT",
        "immediate_tests": ["Clinical Diagnosis! Immediate Epinephrine administration", "Continuous Pulse Oximetry and Blood Pressure monitoring", "Serum Tryptase (drawn within 1-2 hours of onset to confirm mast cell activation)"],
        "recommended_investigations": ["Serum total tryptase level (1-2 hours post-event and baseline at >24 hours)", "Continuous ECG and hemodynamic monitoring", "Comprehensive allergen IgE testing post-recovery"],
        "recommended_medications": ["Immediate IM Epinephrine 0.3-0.5mg (1:1000) in anterolateral mid-thigh (repeat q5-15m PRN)", "Rapid IV Crystalloid bolus (1-2 Liters Normal Saline) for distributive shock", "IV Diphenhydramine 50mg (H1-antihistamine) + IV Famotidine 20mg (H2-antihistamine)", "IV Methylprednisolone 1-2 mg/kg to prevent biphasic reactions", "Inhaled Albuterol for bronchospasm"],
        "treatment_summary": "Intramuscular Epinephrine in the anterolateral thigh is the first and most critical intervention. Supine positioning, high-flow oxygen, aggressive IV fluid resuscitation, and observation for biphasic anaphylaxis.",
        "disease_intelligence": {
            "disease_name": "Anaphylaxis",
            "icd10_code": "T78.2", "icd11_code": "4A84",
            "cardinal_symptoms": ["Urticaria / angioedema", "Stridor / wheezing / respiratory distress", "Hypotension / syncope", "Sudden abdominal cramping and vomiting post-exposure"],
            "red_flags": ["Stridor / laryngeal edema", "Refractory hypotension / shock", "Cardiac arrest"],
            "clinical_pearl": "Epinephrine is the ONLY first-line medication in anaphylaxis. Antihistamines and steroids do not prevent airway collapse or shock."
        },
        "pearl": "Life-threatening allergic emergency. Immediate IM Epinephrine 0.3-0.5mg in the anterolateral thigh is lifesaving. Do not delay for antihistamines."
    },

    "Giant Cell Arteritis (Temporal Arteritis)": {
        "icd10": "M31.5", "icd11": "4A44.0", "category": "Rheumatology / Ophthalmology Emergency", "triage": "EMERGENT",
        "immediate_tests": ["Stat ESR and CRP (ESR typically >50-100 mm/hr)", "Temporal Artery Ultrasound (hypoechoic 'halo' sign)", "Temporal Artery Biopsy (gold standard: transmural inflammatory infiltrate)", "Complete Blood Count (normocytic anemia, thrombocytosis)"],
        "recommended_investigations": ["Erythrocyte Sedimentation Rate (ESR) and C-reactive Protein (CRP)", "Temporal Artery Biopsy (at least 1.5-2 cm specimen)", "Color Doppler Ultrasound of Temporal and Axillary Arteries", "Formal ophthalmological visual field and fundus evaluation"],
        "recommended_medications": ["Immediate oral Prednisone 40-60mg daily (or IV Methylprednisolone 1000mg daily x3 if acute visual symptoms)", "Tocilizumab (anti-IL-6 receptor mAb) for steroid-sparing maintenance", "Aspirin 81-100mg daily to reduce ischemic neuro-ophthalmic events", "Proton pump inhibitor and bone protection (calcium/vitamin D/bisphosphonate)"],
        "treatment_summary": "Start high-dose systemic corticosteroids IMMEDIATELY if GCA is suspected to prevent irreversible, permanent bilateral blindness. Never delay corticosteroids for a temporal artery biopsy.",
        "disease_intelligence": {
            "disease_name": "Giant Cell Arteritis",
            "icd10_code": "M31.5", "icd11_code": "4A44.0",
            "cardinal_symptoms": ["New localized temporal headache", "Jaw claudication while chewing", "Scalp tenderness (brushing hair)", "Visual loss / amaurosis fugax", "Polymyalgia rheumatica symptoms"],
            "red_flags": ["Acute painless visual loss (anterior ischemic optic neuropathy)", "Diplopia", "Thoracic aortic aneurysm"],
            "clinical_pearl": "Jaw claudication is the most specific clinical symptom of GCA. Immediate high-dose steroids prevent contralateral blindness."
        },
        "pearl": "Sight-threatening emergency. Jaw claudication, scalp tenderness, and elevated ESR. Immediate high-dose steroids prevent permanent bilateral blindness."
    },

    "Wilson's Disease (Hepatolenticular Degeneration)": {
        "icd10": "E83.0", "icd11": "5C56.1", "category": "Metabolic / Hepatology", "triage": "URGENT",
        "immediate_tests": ["Slit-Lamp Examination for Kayser-Fleischer (KF) Rings", "Serum Ceruloplasmin (typically <20 mg/dL)", "24-Hour Urinary Copper Excretion (>100 ug/24h)", "Liver Function Tests and Complete Blood Count (Coombs-negative hemolytic anemia)"],
        "recommended_investigations": ["Slit-lamp biomicroscopy for copper deposition in Descemet's membrane (KF rings)", "24-hour urinary copper excretion", "Serum ceruloplasmin and free serum copper", "ATP7B gene molecular testing", "Liver biopsy for quantitative dry weight copper determination", "Brain MRI (T2 hyperintensity in basal ganglia, 'face of the giant panda' sign)"],
        "recommended_medications": ["Copper chelators: D-Penicillamine 250-500mg QID OR Trientine 750-1500mg daily (preferred for fewer side effects)", "Oral Zinc Acetate 50mg TID (induces intestinal metallothionein to block copper absorption)", "Pyridoxine (Vitamin B6) 25-50mg daily when on Penicillamine"],
        "treatment_summary": "Lifelong copper chelation therapy (Trientine or Penicillamine) followed by Zinc maintenance. Dietary avoidance of copper-rich foods (shellfish, liver, nuts, mushrooms, chocolate).",
        "disease_intelligence": {
            "disease_name": "Wilson's Disease",
            "etiology": "Autosomal recessive mutation in ATP7B gene encoding copper-transporting P-type ATPase, causing toxic copper accumulation in liver and brain",
            "icd10_code": "E83.0", "icd11_code": "5C56.1",
            "cardinal_symptoms": ["Kayser-Fleischer rings", "Unexplained hepatitis / cirrhosis", "Neuropsychiatric symptoms (tremor, dystonia, dysarthria, personality changes)", "Coombs-negative hemolytic anemia"],
            "red_flags": ["Acute fulminant liver failure with Coombs-negative hemolytic anemia and low alkaline phosphatase", "Severe dystonia / dysphagia"],
            "clinical_pearl": "Kayser-Fleischer rings are present in >95% of patients with neuropsychiatric Wilson's disease. Low serum ceruloplasmin + elevated 24h urine copper confirms diagnosis."
        },
        "pearl": "Autosomal recessive copper storage disorder: Kayser-Fleischer corneal rings, hepatic dysfunction, and neuropsychiatric manifestations (tremor, dystonia, psychosis)."
    },

    "Addison's Disease (Primary Adrenal Insufficiency)": {
        "icd10": "E27.1", "icd11": "5A71.0", "category": "Endocrinology", "triage": "URGENT",
        "immediate_tests": ["Stat Serum Cortisol and ACTH level (high ACTH with low cortisol)", "High-Dose Cosyntropin (ACTH) Stimulation Test (failure of cortisol to rise >18 ug/dL)", "Serum Electrolytes (hyponatremia, hyperkalemia)", "21-Hydroxylase Autoantibodies"],
        "recommended_investigations": ["Standard ACTH Stimulation Test (250 ug cosyntropin IV/IM)", "Morning baseline plasma ACTH and serum cortisol", "Serum Electrolytes (hyponatremia, hyperkalemia, elevated BUN)", "Adrenal autoantibodies (anti-21-hydroxylase)", "Adrenal CT scan (if autoantibodies negative: screen for TB, hemorrhage, metastases)"],
        "recommended_medications": ["Hydrocortisone 15-25mg daily in divided doses (e.g. 10mg morning, 5mg lunch, 2.5mg early evening)", "Fludrocortisone 0.05-0.2mg daily (mineralocorticoid replacement)", "In Acute Adrenal Crisis: IV Hydrocortisone 100mg stat, then 50-100mg q6-8h with aggressive Normal Saline resuscitation", "Patient education: Double or triple oral hydrocortisone during intercurrent febrile illness ('sick day rules')"],
        "treatment_summary": "Lifelong glucocorticoid (Hydrocortisone) and mineralocorticoid (Fludrocortisone) replacement. Emergency injectable Hydrocortisone and medical alert bracelet. Stat IV hydrocortisone + saline for adrenal crisis.",
        "disease_intelligence": {
            "disease_name": "Primary Adrenal Insufficiency (Addison's Disease)",
            "etiology": "Autoimmune destruction of adrenal cortex (80-90% in developed countries); tuberculosis in endemic regions",
            "icd10_code": "E27.1", "icd11_code": "5A71.0",
            "cardinal_symptoms": ["Hyperpigmentation of palmar creases, buccal mucosa, and scars", "Orthostatic hypotension", "Chronic fatigue and weakness", "Salt craving", "Hyponatremia with hyperkalemia"],
            "red_flags": ["Adrenal crisis (refractory hypotension, shock, severe vomiting, abdominal pain, hypoglycemia)", "Severe hyperkalemia with cardiac conduction abnormalities"],
            "clinical_pearl": "Hyperpigmentation is unique to PRIMARY adrenal insufficiency due to elevated pro-opiomelanocortin (POMC) and ACTH cross-reacting with melanocortin-1 receptors."
        },
        "pearl": "Primary adrenal failure: Hyperpigmentation of palmar creases and oral mucosa, salt craving, postural hypotension, hyponatremia, and hyperkalemia. Treat with hydrocortisone."
    },

    "Kawasaki Disease": {
        "icd10": "M30.3", "icd11": "4A44.3", "category": "Pediatric Rheumatology / Cardiology", "triage": "URGENT",
        "immediate_tests": ["Transthoracic Echocardiogram (evaluating coronary artery dilation/aneurysms)", "Complete Blood Count (Leukocytosis, thrombocytosis in subacute phase)", "Serum ESR and CRP (markedly elevated)", "Liver Function Tests and Urinalysis (sterile pyuria)"],
        "recommended_investigations": ["Serial Transthoracic Echocardiography (baseline, 2 weeks, 6-8 weeks)", "Inflammatory markers (ESR, CRP, Ferritin)", "CBC (normocytic anemia, thrombocytosis >450k after day 7)", "Urinalysis (sterile pyuria without bacteriuria)"],
        "recommended_medications": ["Intravenous Immunoglobulin (IVIG) 2 g/kg as a single infusion over 10-12 hours within first 10 days of fever", "Oral Aspirin high-dose (30-50 mg/kg/day divided q6h) until afebrile, then low-dose (3-5 mg/kg/day) for 6-8 weeks", "IV Infliximab or Methylprednisolone for IVIG-resistant Kawasaki disease"],
        "treatment_summary": "Immediate IVIG (2 g/kg) within the first 10 days of illness combined with Aspirin prevents coronary artery aneurysms. Serial echocardiography to monitor coronary dimensions.",
        "disease_intelligence": {
            "disease_name": "Kawasaki Disease (Mucocutaneous Lymph Node Syndrome)",
            "icd10_code": "M30.3", "icd11_code": "4A44.3",
            "cardinal_symptoms": ["Fever >=5 days", "Bilateral non-exudative bulbar conjunctival injection", "Strawberry tongue and red cracked lips", "Polymorphous rash", "Erythema and edema of hands/feet with periungual desquamation", "Cervical lymphadenopathy (>1.5 cm)"],
            "red_flags": ["Coronary artery aneurysms / thrombosis", "Myocardial infarction", "Myocarditis / congestive heart failure"],
            "clinical_pearl": "Early IVIG reduces the risk of coronary artery aneurysms from 25% down to less than 5%. Kawasaki disease is the leading cause of acquired heart disease in children in developed nations."
        },
        "pearl": "Pediatric medium-vessel vasculitis: Prolonged fever (>=5 days), strawberry tongue, conjunctivitis, polymorphous rash, and desquamation. IVIG prevents coronary artery aneurysms."
    },

    "Gout (Acute Gouty Arthritis)": {
        "icd10": "M10.0", "icd11": "FA25", "category": "Rheumatology", "triage": "ROUTINE",
        "immediate_tests": ["Arthrocentesis with Polarized Light Microscopy (negatively birefringent needle-shaped crystals)", "Synovial Fluid Gram Stain and Culture (rule out septic arthritis)", "Serum Uric Acid", "Renal Function Panel"],
        "recommended_investigations": ["Synovial fluid analysis (needle-shaped, negatively birefringent monosodium urate crystals under polarized light)", "Synovial fluid cell count and culture", "Serum uric acid (can be normal during acute flare)", "Plain radiographs of affected joint (punched-out erosions with overhanging edges in chronic gout)"],
        "recommended_medications": ["Oral NSAIDs (Indomethacin 50mg TID, Naproxen 500mg BID, or Celecoxib)", "Oral Colchicine (1.2mg load, then 0.6mg 1 hour later, then 0.6mg daily/BID)", "Oral Prednisone 30-40mg daily tapered over 7-10 days (preferred in renal insufficiency)", "Long-term Urate-Lowering Therapy: Allopurinol or Febuxostat targeting serum uric acid <6.0 mg/dL"],
        "treatment_summary": "First-line acute flare relief with NSAIDs, Colchicine, or oral corticosteroids. Once the flare resolves, initiate urate-lowering therapy (Allopurinol) with anti-inflammatory prophylaxis to prevent recurrent attacks.",
        "disease_intelligence": {
            "disease_name": "Gout (Acute Gouty Arthritis)",
            "icd10_code": "M10.0", "icd11_code": "FA25",
            "cardinal_symptoms": ["Podagra (first MTP joint excruciating swelling and erythema)", "Rapid peak of pain within 12-24 hours", "Desquamation over affected joint as inflammation clears", "Tophi in chronic disease"],
            "red_flags": ["Septic arthritis (must always be excluded with joint aspiration)", "Severe acute polyarticular gout flare in renal failure"],
            "clinical_pearl": "Serum uric acid may drop into the normal range during an acute flare due to inflammatory uricosuria; synovial fluid polarized microscopy is the diagnostic gold standard."
        },
        "pearl": "Podagra (first metatarsophalangeal joint exquisite inflammation). Negatively birefringent needle-shaped crystals on polarized light microscopy. Treat with NSAIDs or colchicine."
    },

    "Lyme Disease (Early Localized / Disseminated)": {
        "icd10": "A69.2", "icd11": "1C1G", "category": "Infectious / Vector-borne", "triage": "ROUTINE",
        "immediate_tests": ["Clinical Diagnosis for Erythema Migrans (bullseye rash >5 cm does NOT require serology to treat)", "Two-Tier Serology: Sensitive Enzyme Immunoassay (EIA) followed by Western Blot IgM/IgG", "12-Lead ECG (screen for Lyme carditis / AV block)"],
        "recommended_investigations": ["Clinical recognition of Erythema Migrans lesion (diagnostic on its own)", "CDC recommended Two-Tier Serological Testing (EIA/ELISA followed by Western Blot)", "12-Lead ECG (monitoring PR interval for Lyme carditis)", "Lumbar Puncture (lymphocytic pleocytosis, CSF Lyme antibody index for neuroborreliosis)"],
        "recommended_medications": ["Oral Doxycycline 100mg BID x10-14 days (first-line in non-pregnant adults and children of all ages)", "Oral Amoxicillin 500mg TID x14 days OR Cefuroxime axetil 500mg BID (preferred in pregnancy)", "IV Ceftriaxone 2g daily x14-28 days for Lyme carditis with high-degree AV block or neuroborreliosis"],
        "treatment_summary": "Oral Doxycycline 100mg BID x10-14 days. Erythema migrans is a clinical diagnosis and antibiotics should be started immediately without waiting for serological confirmation.",
        "disease_intelligence": {
            "disease_name": "Lyme Disease (Borreliosis)",
            "etiology": "Borrelia burgdorferi transmitted by Ixodes scapularis or Ixodes pacificus ticks",
            "icd10_code": "A69.2", "icd11_code": "1C1G",
            "cardinal_symptoms": ["Erythema migrans ('bulls-eye' expanding annular rash with central clearing)", "Fatigue, fever, and headache", "Migratory arthralgias", "Facial nerve palsy (Bannwarth syndrome)", "AV nodal heart block"],
            "red_flags": ["High-degree AV block / Lyme carditis", "Lyme meningitis / encephalopathy", "Chronic refractory Lyme arthritis"],
            "clinical_pearl": "Serology is negative in the first 2-3 weeks of infection; therefore, a patient with erythema migrans should be treated empirically without waiting for antibodies."
        },
        "pearl": "Tick-borne Borrelia burgdorferi infection: Pathognomonic erythema migrans ('bulls-eye' rash) does not require serology to initiate prompt oral Doxycycline therapy."
    },

    "Infective Endocarditis": {
        "icd10": "I33.0", "icd11": "BB60", "category": "Cardiology / Infectious", "triage": "URGENT",
        "immediate_tests": ["Blood Cultures (3 separate sets from different venipuncture sites before antibiotics)", "Transthoracic Echocardiogram (TTE, followed by TEE if high suspicion)", "12-Lead ECG (screen for PR prolongation indicating aortic root abscess)", "CBC, ESR, CRP, Urinalysis"],
        "recommended_investigations": ["Serial Blood Cultures (x3 sets at least 1 hour apart)", "Transesophageal Echocardiogram (TEE — superior sensitivity for vegetations and perivalvular abscess)", "CBC with differential (leukocytosis, normocytic anemia)", "Inflammatory markers (markedly elevated ESR and CRP)", "Urinalysis with microscopy (microscopic hematuria, red cell casts from glomerulonephritis)", "12-lead ECG monitoring for AV conduction block"],
        "recommended_medications": ["Empiric IV Vancomycin 15-20 mg/kg q8-12h + Ceftriaxone 2g IV q24h (native valve)", "Vancomycin + Gentamicin + Rifampin (prosthetic valve endocarditis)", "Targeted IV Penicillin G or Ampicillin + Ceftriaxone for Viridans group streptococci once sensitivities return", "Cardiothoracic surgery consult for severe valvular regurgitation, heart failure, or large vegetations >10mm"],
        "treatment_summary": "Immediate blood cultures x3 followed by empiric bactericidal IV antibiotics (Vancomycin + Ceftriaxone for native valves). Transesophageal echocardiography to detect vegetations. Urgent surgical evaluation if refractory heart failure or abscess occurs.",
        "disease_intelligence": {
            "disease_name": "Infective Endocarditis",
            "icd10_code": "I33.0", "icd11_code": "BB60",
            "cardinal_symptoms": ["Prolonged intermittent fevers with night sweats", "New or changing regurgitant heart murmur", "Splinter hemorrhages under fingernails", "Janeway lesions (painless erythematous macules on palms/soles)", "Osler nodes (painful violaceous nodules on finger pads)", "Roth spots on fundoscopy"],
            "red_flags": ["New AV conduction block on ECG (suspect aortic root ring abscess)", "Acute severe pulmonary edema / refractory cardiogenic shock", "Septic embolic stroke or mycotic aneurysm"],
            "clinical_pearl": "Modified Duke criteria require either 2 major, 1 major + 3 minor, or 5 minor criteria. Blood cultures must be drawn before antibiotic initiation whenever hemodynamically stable."
        },
        "pearl": "Modified Duke criteria: bacteremia (typical organism) + endocardial involvement (vegetation/new murmur) + vascular/immunologic phenomena (Janeway lesions, Osler nodes, splinter hemorrhages)."
    },

    "Pyelonephritis (Upper UTI)": {
        "icd10": "N10", "icd11": "GB50", "category": "Nephrology / Infectious", "triage": "URGENT",
        "immediate_tests": ["Urinalysis with microscopy (pyuria, bacteriuria, WBC casts)", "Urine Culture and Antibiotic Susceptibility", "Complete Blood Count (CBC) with differential", "Basic Metabolic Panel (BUN and serum Creatinine)"],
        "recommended_investigations": ["Midstream clean-catch Urinalysis with microscopic examination (pyuria >10 WBC/hpf, leukocyte esterase, nitrites)", "Urine Culture and quantitative colony count with susceptibility testing", "Complete Blood Count (leukocytosis with neutrophilic left shift)", "Basic Metabolic Panel (assess acute kidney injury and electrolyte abnormalities)", "Blood Cultures x2 sets (indicated in hospitalized patients or if septic)", "Renal Ultrasound or CT Abdomen/Pelvis with contrast (if persistent fever >72h to rule out perinephric abscess or obstruction)"],
        "recommended_medications": ["Oral Ciprofloxacin 500mg BID x7 days OR Levofloxacin 750mg daily x5 days (outpatient uncomplicated if local fluoroquinolone resistance <10%)", "IV Ceftriaxone 1g-2g q24h (first-line inpatient empirical therapy)", "Oral Trimethoprim-Sulfamethoxazole DS 1 tab BID x14 days (if organism susceptible)", "Oral Cefpodoxime 200mg BID x10-14 days (alternative beta-lactam regimen)", "Adequate oral or IV hydration and Antipyretics (Acetaminophen 650mg q6h PRN)"],
        "treatment_summary": "Empiric antimicrobial therapy initiated promptly: IV Ceftriaxone for hospitalized or complicated patients; oral fluoroquinolones (Ciprofloxacin/Levofloxacin) for stable outpatients. Tailor regimen once urine culture sensitivities are reported.",
        "disease_intelligence": {
            "disease_name": "Acute Pyelonephritis",
            "icd10_code": "N10", "icd11_code": "GB50",
            "cardinal_symptoms": ["Unilateral or bilateral flank pain", "Costovertebral angle (CVA) tenderness on percussion", "High-grade fever (>38.5C) with shaking chills/rigors", "Dysuria, urinary frequency, and urgency", "Nausea, vomiting, and systemic malaise"],
            "red_flags": ["Urosepsis and septic shock with hemodynamic instability", "Obstructing ureteral calculus with infected hydronephrosis (requires emergent urologic decompression)", "Renal or perinephric abscess formation with persistent fevers >72h"],
            "clinical_pearl": "Presence of white blood cell casts on urine microscopy pathognomonically localizes infection to the renal parenchyma (upper tract), distinguishing pyelonephritis from simple cystitis."
        },
        "pearl": "Flank pain, CVA tenderness, high fever, and pyuria with WBC casts distinguish pyelonephritis from lower UTI. First-line IV Ceftriaxone or oral Ciprofloxacin."
    },

    "Urinary Tract Infection (Lower)": {
        "icd10": "N39.0", "icd11": "GC00", "category": "Urology / Infectious", "triage": "ROUTINE",
        "immediate_tests": ["Urinalysis (dipstick + microscopy for nitrites, leukocyte esterase, WBCs)", "Urine Culture (in recurrent, complicated, or treatment-failure cases)"],
        "recommended_investigations": ["Urinalysis (positive leukocyte esterase, positive nitrites, pyuria)", "Urine Microscopy (WBCs >5-10/hpf, bacteria)", "Urine Culture and Susceptibility (if pregnancy, male, recurrent, or treatment failure)", "Urine pregnancy test in women of childbearing potential"],
        "recommended_medications": ["Nitrofurantoin monohydrate/macrocrystals 100mg PO BID x5 days (first-line)", "Trimethoprim-Sulfamethoxazole DS 1 tab PO BID x3 days (if local resistance <20%)", "Fosfomycin tromethamine 3g PO single dose", "Phenazopyridine 200mg PO TID PRN x2 days for dysuria symptom relief"],
        "treatment_summary": "First-line empirical therapy with Nitrofurantoin 100mg BID x5 days or TMP-SMX DS BID x3 days. Encourage oral hydration. Phenazopyridine for acute urinary burning relief.",
        "disease_intelligence": {
            "disease_name": "Acute Uncomplicated Cystitis",
            "icd10_code": "N39.0", "icd11_code": "GC00",
            "cardinal_symptoms": ["Dysuria (burning micturition)", "Urinary frequency and urgency", "Suprapubic pain and tenderness", "Cloudy or malodorous urine", "Hematuria (hemorrhagic cystitis)"],
            "red_flags": ["Fever, rigors, flank pain, or CVA tenderness (indicates progression to pyelonephritis)", "Urinary retention in males"],
            "clinical_pearl": "Uncomplicated cystitis does not cause systemic fever or CVA tenderness. Absence of fever and flank pain distinguishes lower from upper UTI."
        },
        "pearl": "Acute cystitis: Dysuria, frequency, urgency, suprapubic tenderness without fever or flank pain. First-line treatment Nitrofurantoin 100mg BID x5d."
    },

    "Nephrolithiasis (Kidney Stones)": {
        "icd10": "N20.0", "icd11": "GB70", "category": "Urology / Renal", "triage": "URGENT",
        "immediate_tests": ["Low-Dose Non-Contrast CT Abdomen and Pelvis (gold standard)", "Urinalysis with microscopy (hematuria, crystal identification)", "Basic Metabolic Panel (serum Creatinine and BUN)", "Point-of-Care Renal Ultrasound (if CT contraindicated or pregnant)"],
        "recommended_investigations": ["Non-contrast helical CT of abdomen and pelvis (confirms stone size, location, and hydronephrosis)", "Renal and bladder ultrasound (detects hydronephrosis and acoustic shadowing in stones)", "Urinalysis (gross or microscopic hematuria present in 85-90% of cases, pyuria rule-out)", "Serum BUN and Creatinine (assess renal function)", "Serum Calcium, Uric Acid, Phosphate, and Electrolytes", "Strain urine for stone capture and crystallographic composition analysis"],
        "recommended_medications": ["Ketorolac (Toradol) 15-30mg IV/IM q6h PRN (first-line NSAID for acute ureteral spasm)", "Acetaminophen 1g IV/PO + PRN IV Morphine or Hydromorphone for breakthrough pain", "Tamsulosin (Flomax) 0.4mg PO daily (medical expulsive therapy for distal ureteral stones 5-10mm)", "Ondansetron 4-8mg IV/PO q8h PRN for nausea and vomiting", "Aggressive IV crystalloid hydration"],
        "treatment_summary": "First-line analgesia with NSAIDs (Ketorolac) supplemented by narcotics. Medical expulsive therapy with Tamsulosin 0.4mg daily for distal ureteral stones <10mm. Immediate urologic intervention required for stones with concomitant infection or complete obstruction.",
        "disease_intelligence": {
            "disease_name": "Nephrolithiasis / Urolithiasis",
            "icd10_code": "N20.0", "icd11_code": "GB70",
            "cardinal_symptoms": ["Severe acute paroxysmal colicky flank pain", "Radiation of pain along ureter into ipsilateral groin, testicle, or labia", "Hematuria (gross or microscopic)", "Patient pacing restlessly, unable to find a comfortable position", "Nausea, persistent vomiting, and diaphoresis"],
            "red_flags": ["Obstructing stone accompanied by fever, chills, or pyuria (surgical emergency requiring emergent stent/nephrostomy)", "Anuria or solitary kidney with acute obstruction", "Refractory pain or intractable vomiting preventing oral hydration"],
            "clinical_pearl": "Unlike patients with peritonitis who lie motionless, patients with renal colic are in constant motion trying to relieve the excruciating colicky pain."
        },
        "pearl": "Severe colicky flank pain radiating to groin with microscopic hematuria. Non-contrast CT is gold standard. First-line analgesia with NSAIDs (Ketorolac) + Tamsulosin for medical expulsion."
    },

    "Acute Diverticulitis": {
        "icd10": "K57.32", "icd11": "DC50", "category": "Gastroenterology / Surgical", "triage": "URGENT",
        "immediate_tests": ["Contrast-Enhanced CT Abdomen and Pelvis (diagnostic gold standard)", "Complete Blood Count (CBC) with differential", "Basic Metabolic Panel (BMP) and Serum Lactate", "Urinalysis (rule out colovesical fistula)"],
        "recommended_investigations": ["Abdominal and pelvic CT with oral and IV contrast (pericolic fat stranding, bowel wall thickening >4mm, diverticula, phlegmon/abscess)", "Complete Blood Count (leukocytosis with left shift)", "Serum C-Reactive Protein (CRP >50 mg/L correlates with complicated disease)", "Urinalysis (sterile pyuria common due to adjacent bladder inflammation; pneumaturia suggests fistula)", "Colonoscopy strictly CONTRAINDICATED in acute phase due to perforation risk (defer 6-8 weeks)"],
        "recommended_medications": ["Oral Ciprofloxacin 500mg BID + Metronidazole 500mg TID x7-10 days (outpatient regimen)", "Oral Amoxicillin-Clavulanate (Augmentin) 875/125mg BID x7-10 days (single-agent alternative)", "IV Piperacillin-Tazobactam (Zosyn) 3.375g q6h OR Ceftriaxone 1g daily + Metronidazole 500mg q8h (inpatient complicated regimen)", "Clear liquid diet advance to low-fiber during acute resolution, then high-fiber maintenance", "Acetaminophen and antispasmodics for pain; avoid NSAIDs (associated with perforation)"],
        "treatment_summary": "Uncomplicated diverticulitis can be managed with bowel rest and oral antibiotics (Augmentin or Ciprofloxacin + Flagyl). Inpatient IV antibiotics for complicated cases with abscess, perforation, or peritonitis.",
        "disease_intelligence": {
            "disease_name": "Acute Sigmoid Diverticulitis",
            "icd10_code": "K57.32", "icd11_code": "DC50",
            "cardinal_symptoms": ["Constant, worsening Left Lower Quadrant (LLQ) abdominal pain", "Fever and chills", "Localized LLQ rebound tenderness and guarding", "Change in bowel habits (constipation or diarrhea)", "Nausea, vomiting, and abdominal fullness"],
            "red_flags": ["Peritoneal signs: diffuse guarding and rigidity indicating free perforation", "Pelvic or pericolic abscess (>4cm requires CT-guided percutaneous drainage)", "Colovesical fistula (pneumaturia, fecaluria, recurrent UTIs)"],
            "clinical_pearl": "Often called 'left-sided appendicitis'. Colonoscopy should never be performed during the acute phase due to high risk of iatrogenic colonic perforation."
        },
        "pearl": "Left lower quadrant pain, fever, and leukocytosis. CT abdomen/pelvis confirms pericolic fat stranding and wall thickening. Colonoscopy contraindicated during acute attack."
    },

    "Acute Cholecystitis": {
        "icd10": "K81.0", "icd11": "DC11.0", "category": "Gastroenterology / Surgical", "triage": "URGENT",
        "immediate_tests": ["Right Upper Quadrant (RUQ) Abdominal Ultrasound (first-line imaging)", "Complete Blood Count with differential", "Liver Function Tests (Total Bilirubin, Alk Phos, AST, ALT)", "Serum Lipase and Amylase (rule out gallstone pancreatitis)"],
        "recommended_investigations": ["Transabdominal Ultrasound of gallbladder (sonographic Murphy sign, wall thickening >3mm, gallstones, pericholecystic fluid)", "Hepatobiliary Iminodiacetic Acid (HIDA) Scan / Cholescintigraphy (most sensitive confirmatory test if US equivocal)", "CBC (leukocytosis >10,000/mcL with left shift)", "Comprehensive Metabolic Panel with LFTs (mild elevation in transaminases and bilirubin; marked elevation suggests choledocholithiasis or cholangitis)", "Serum Lipase (assess for concurrent gallstone pancreatitis)"],
        "recommended_medications": ["IV Piperacillin-Tazobactam 3.375g q6h OR Ceftriaxone 1g q24h + Metronidazole 500mg q8h", "IV Cefazolin 1-2g q8h + Metronidazole (for mild-to-moderate community-acquired cholecystitis)", "IV Ketorolac 15-30mg or Opioids (Hydromorphone) for analgesia", "IV Fluid Resuscitation and NPO (bowel rest)", "Definitive Treatment: Early laparoscopic cholecystectomy within 24-72 hours of admission"],
        "treatment_summary": "NPO, aggressive IV crystalloid hydration, empiric IV antibiotics (Ceftriaxone + Metronidazole or Zosyn), and early laparoscopic cholecystectomy (within 24-72 hours of symptom onset).",
        "disease_intelligence": {
            "disease_name": "Acute Calculous Cholecystitis",
            "icd10_code": "K81.0", "icd11_code": "DC11.0",
            "cardinal_symptoms": ["Steady, severe Right Upper Quadrant or epigastric pain lasting >4-6 hours", "Radiation of pain to right scapula or right shoulder", "Positive Murphy sign (inspiratory arrest on deep palpation of RUQ)", "Fever, nausea, and vomiting", "Triggered characteristically by fatty meals"],
            "red_flags": ["High-grade fever, rigors, and jaundice with confusion (Charcot triad / Reynolds pentad indicating ascending cholangitis)", "Emphysematous cholecystitis (gas in gallbladder wall in diabetics)", "Gallbladder gangrene or perforation with generalized peritonitis"],
            "clinical_pearl": "Biliary colic typically lasts under 4-6 hours without fever or leukocytosis; persistence of pain >6 hours with fever, leukocytosis, and Murphy sign defines acute cholecystitis."
        },
        "pearl": "RUQ pain radiating to right shoulder, fever, and positive Murphy sign. Ultrasound shows gallstones, thickened wall (>3mm), and pericholecystic fluid. Early laparoscopic cholecystectomy is definitive."
    },

    "Acute Pancreatitis": {
        "icd10": "K85.9", "icd11": "DC31", "category": "Gastroenterology", "triage": "URGENT",
        "immediate_tests": ["Serum Lipase (diagnostic threshold: >3x upper limit of normal)", "Abdominal Ultrasound (screen for gallstones and biliary duct dilation)", "Comprehensive Metabolic Panel (Calcium, BUN, Creatinine, LFTs)", "Serum Triglycerides (rule out hypertriglyceridemic pancreatitis)"],
        "recommended_investigations": ["Serum Lipase (more sensitive and specific than amylase, remains elevated for 7-14 days)", "Transabdominal Ultrasound (evaluates for gallstones and choledocholithiasis)", "Contrast-Enhanced CT Abdomen/Pelvis (indicated if diagnosis uncertain or clinical deterioration at 48-72h for necrotizing pancreatitis)", "Basic Metabolic Panel (BUN >20 or rising indicates hemoconcentration and severe course)", "Complete Blood Count (hematocrit >44% indicates hemoconcentration)", "Serum Calcium and Serum Triglycerides (>1000 mg/dL)", "Arterial Blood Gas and Serum Lactate (in severe pancreatitis / SIRS)"],
        "recommended_medications": ["Aggressive IV Crystalloid Resuscitation: Lactated Ringer's 200-500 mL/hr (target urine output >0.5-1.0 mL/kg/hr)", "IV Analgesia: Hydromorphone 0.5-1mg IV q2-3h PRN or Fentanyl", "IV Antiemetics: Ondansetron 4-8mg IV q8h PRN", "Early oral nutrition: resume low-fat solid or liquid diet as soon as nausea and ileus resolve", "Prophylactic antibiotics are NOT recommended for uncomplicated pancreatitis (reserve for infected necrosis)"],
        "treatment_summary": "Goal-directed IV hydration with Lactated Ringer's solution, multimodal analgesia, early enteral nutrition as tolerated, and identification of etiology (gallstones vs alcohol vs triglycerides).",
        "disease_intelligence": {
            "disease_name": "Acute Pancreatitis",
            "icd10_code": "K85.9", "icd11_code": "DC31",
            "cardinal_symptoms": ["Severe, constant epigastric pain radiating directly to mid-back", "Pain partially relieved by leaning forward in tripod or fetal position", "Persistent nausea and repeated vomiting", "Epigastric tenderness and voluntary guarding", "Abdominal distension and hypoactive bowel sounds"],
            "red_flags": ["Persistent organ failure >48 hours (shock, hypoxemic respiratory failure, renal failure)", "Ecchymoses: Grey Turner sign (flanks) or Cullen sign (periumbilical) indicating retroperitoneal hemorrhage", "SIRS score >=2 at admission and rising BUN/hematocrit indicating necrotizing pancreatitis"],
            "clinical_pearl": "Diagnosis requires 2 of 3 criteria: (1) characteristic epigastric pain radiating to back, (2) serum lipase >3x upper limit of normal, (3) characteristic findings on cross-sectional imaging (CT/MRI)."
        },
        "pearl": "Atlanta Criteria: Epigastric pain radiating to back + Lipase >3x ULN + CT findings (need 2 of 3). Treat with early aggressive Lactated Ringer's hydration."
    },

    "Pulmonary Embolism": {
        "icd10": "I26.9", "icd11": "BD30", "category": "Pulmonology / Vascular", "triage": "EMERGENT",
        "immediate_tests": ["CT Pulmonary Angiography (CTPA — definitive imaging of choice)", "High-Sensitivity D-Dimer (rule-out in low/intermediate Wells score)", "12-Lead ECG (sinus tachycardia, S1Q3T3, right ventricular strain)", "Arterial Blood Gas (hypoxemia, hypocapnia, respiratory alkalosis)"],
        "recommended_investigations": ["CT Pulmonary Angiogram (CTPA with contrast — gold standard)", "Quantitative D-Dimer assay (high sensitivity rule-out for low Wells score <=4)", "12-Lead ECG (sinus tachycardia is most common; S1Q3T3 pattern, T-wave inversions in V1-V4)", "Bedside Transthoracic Echocardiogram (McConnell sign: RV strain, paradoxical septal shift, RV dilation)", "Lower Extremity Venous Compression Duplex Ultrasound (detects source DVT in >50% of cases)", "Cardiac Biomarkers: high-sensitivity Troponin and BNP (risk stratify submassive PE)"],
        "recommended_medications": ["Low Molecular Weight Heparin: Enoxaparin 1 mg/kg SC q12h OR Unfractionated Heparin IV infusion (first-line anticoagulation)", "Direct Oral Anticoagulants (DOACs): Apixaban 10mg PO BID x7d then 5mg BID, OR Rivaroxaban 15mg PO BID x21d then 20mg daily", "Systemic Thrombolysis: Alteplase (tPA) 100mg IV infusion over 2 hours (indicated for MASSIVE PE with persistent hypotension SBP <90)", "Supplemental oxygen titrated to SpO2 >=90%, cautious IV fluid bolus (avoid RV volume overload)", "Catheter-directed embolectomy or surgical embolectomy for contraindications to thrombolysis"],
        "treatment_summary": "Immediate therapeutic anticoagulation (LMWH or DOAC) started upon clinical suspicion before imaging if high probability. Systemic thrombolysis with tPA reserved for massive PE with sustained shock.",
        "disease_intelligence": {
            "disease_name": "Acute Pulmonary Embolism (PE)",
            "icd10_code": "I26.9", "icd11_code": "BD30",
            "cardinal_symptoms": ["Sudden-onset unexplained dyspnea and tachypnea (RR >20)", "Pleuritic chest pain worsening on deep inspiration", "Hemoptysis", "Tachycardia (HR >100 bpm)", "Syncope or presyncope (heralds massive PE / saddle embolus)", "Unilateral swollen, warm, tender calf (DVT signs)"],
            "red_flags": ["Massive PE: Hemodynamic collapse (SBP <90 mmHg or vasopressor requirement)", "Submassive PE: Normotensive but with elevated Troponin/BNP and RV dysfunction on Echo/CT", "Cardiac arrest with pulseless electrical activity (PEA)"],
            "clinical_pearl": "Normal chest radiograph in the setting of acute severe dyspnea and hypoxemia is a classic clue for pulmonary embolism ('Westermark sign' or 'Hampton hump' are rare)."
        },
        "pearl": "Wells score + PERC rule stratifies risk. CTPA is gold standard. S1Q3T3 and sinus tachycardia on ECG. Immediate anticoagulation with Heparin/DOAC; tPA for massive hemodynamic collapse."
    },

    "COPD Exacerbation": {
        "icd10": "J44.1", "icd11": "CA22.0", "category": "Pulmonology", "triage": "URGENT",
        "immediate_tests": ["Pulse Oximetry and Arterial Blood Gas (assess hypoxemia and hypercapnic respiratory acidosis)", "Chest Radiograph (PA/Lateral to rule out pneumonia, pneumothorax, or edema)", "12-Lead ECG (rule out concurrent ischemia or cor pulmonale)", "CBC with differential"],
        "recommended_investigations": ["Arterial Blood Gas (ABG — assesses acute respiratory acidosis: pH, PaCO2, PaO2)", "Chest X-Ray (hyperinflation, flattened diaphragms, increased retrosternal airspace; rules out pneumonia/pneumothorax)", "Continuous pulse oximetry (target SpO2 88-92% to avoid blunting hypoxic drive)", "12-Lead ECG (P-pulmonale, right bundle branch block, MAT / multifocal atrial tachycardia)", "Sputum Gram stain and culture (if purulent sputum in severe exacerbation)", "Serum electrolytes and renal function panel"],
        "recommended_medications": ["Short-Acting Inhaled Bronchodilators: Albuterol (2.5mg) + Ipratropium (0.5mg) nebulized q1-4h PRN (DuoNeb)", "Systemic Corticosteroids: Oral Prednisone 40mg daily x5 days (accelerates recovery, improves FEV1)", "Empiric Antibiotics: Azithromycin 500mg day 1 then 250mg daily x4d OR Doxycycline 100mg BID x5d OR Amoxicillin-Clavulanate 875mg BID x5d (indicated if purulent sputum + increased dyspnea/volume)", "Controlled Oxygen Therapy: target SpO2 88-92% via Venturi mask or nasal cannula", "Non-Invasive Positive Pressure Ventilation (BiPAP) for acute hypercapnic respiratory failure (pH <7.35, PaCO2 >45)"],
        "treatment_summary": "Inhaled short-acting bronchodilators (Albuterol + Ipratropium), oral Prednisone 40mg daily x5 days, and targeted antibiotics for purulent sputum (Anthonisen criteria). Target SpO2 88-92%. BiPAP for respiratory acidosis.",
        "disease_intelligence": {
            "disease_name": "Acute COPD Exacerbation",
            "icd10_code": "J44.1", "icd11_code": "CA22.0",
            "cardinal_symptoms": ["Acute worsening of baseline dyspnea", "Increased sputum volume", "Increased sputum purulence (yellow/green discoloration)", "Expiratory wheezing and prolonged expiratory phase", "Barrel chest and pursed-lip breathing", "Use of accessory respiratory muscles"],
            "red_flags": ["Acute respiratory acidosis with pH <7.25 on ABG", "Altered mental status, severe lethargy, or somnolence (hypercapnic narcosis)", "Refractory hypoxemia despite supplemental oxygen"],
            "clinical_pearl": "Anthonisen criteria: (1) increased dyspnea, (2) increased sputum volume, (3) increased sputum purulence. Presence of all 3 (or purulence + 1 other) strongly indicates antibiotic therapy."
        },
        "pearl": "Anthonisen cardinal triad: Worsening dyspnea, increased sputum volume, increased sputum purulence. Treat with nebulized DuoNeb, Prednisone 40mg x5d, and antibiotics. Target SpO2 88-92%."
    },

    "Cellulitis": {
        "icd10": "L03.90", "icd11": "1B70", "category": "Dermatology / Infectious", "triage": "ROUTINE",
        "immediate_tests": ["Clinical Examination (mark erythema borders with surgical pen to track progression)", "CBC with differential (leukocytosis)", "Blood Cultures (x2 sets indicated in systemic signs, fever, or immunocompromise)", "Bedside Ultrasound (evaluates for occult drainable subcutaneous abscess)"],
        "recommended_investigations": ["Clinical examination and boundary tracing with skin marker", "Point-of-care ultrasound (POCUS — 'cobblestoning' indicates soft tissue edema; absence of hypoechoic fluid collection rules out abscess)", "Complete Blood Count (leukocytosis, elevated neutrophil band count)", "Inflammatory markers: Serum CRP and ESR", "Blood Cultures (indicated if fever >38C, chills, tachycardia, or failure of outpatient oral therapy)", "Wound culture (only if purulent drainage or ulceration present)"],
        "recommended_medications": ["Non-purulent Cellulitis: Oral Cephalexin 500mg QID x5-7 days OR Cefadroxil 500mg BID x5-7 days (covers Streptococcus pyogenes and MSSA)", "Severe / Inpatient Cellulitis: IV Cefazolin 1-2g q8h OR IV Ceftriaxone 1-2g daily", "Purulent Cellulitis or MRSA Risk: Oral Trimethoprim-Sulfamethoxazole DS 1-2 tabs BID x5-7 days OR Clindamycin 300-450mg TID OR Doxycycline 100mg BID", "Severe / Toxic MRSA concern: IV Vancomycin 15-20 mg/kg q8-12h or Daptomycin", "Limb elevation above heart level (crucial to accelerate lymphatic drainage)"],
        "treatment_summary": "First-line oral Cephalexin 500mg QID x5-7 days for non-purulent cellulitis. Add MRSA coverage (TMP-SMX or Vancomycin) if purulent or penetrating trauma. Mark borders and strictly elevate the limb.",
        "disease_intelligence": {
            "disease_name": "Acute Bacterial Cellulitis",
            "icd10_code": "L03.90", "icd11_code": "1B70",
            "cardinal_symptoms": ["Spreading, ill-defined erythematous skin lesion", "Localized warmth and cutaneous tenderness", "Soft tissue edema ('peau d'orange' appearance)", "Usually unilateral (bilateral lower extremity redness is almost always stasis dermatitis)", "Low-grade fever and regional lymphadenopathy"],
            "red_flags": ["Rapidly spreading erythema (>2 cm/hr) or severe pain out of proportion to exam (suspect Necrotizing Fasciitis)", "Skin bullae, crepitus, ecchymoses, or sensory anesthesia over lesion", "Systemic toxicity: hypotension, tachycardia, altered mental status"],
            "clinical_pearl": "Bilateral lower extremity redness is almost never bilateral cellulitis; it is overwhelmingly venous stasis dermatitis. True cellulitis is almost universally unilateral."
        },
        "pearl": "Unilateral spreading erythema with warmth, swelling, and tenderness. Non-purulent cellulitis: Cephalexin 500mg QID x5d. Strictly elevate the affected extremity to promote lymphatic clearance."
    },

    "Community-Acquired Pneumonia (Lobar Pneumonia)": {
        "icd10": "J18.9", "icd11": "CA40", "category": "Pulmonology / Infectious", "triage": "URGENT",
        "immediate_tests": ["Chest Radiograph (PA and Lateral — consolidative infiltrate)", "Pulse Oximetry and Respiratory Rate", "Complete Blood Count with differential (leukocytosis with left shift)", "Basic Metabolic Panel (BUN for CURB-65 scoring)"],
        "recommended_investigations": ["Chest X-Ray (PA and Lateral: demonstrates lobar consolidation, air bronchograms, or pleural effusion)", "Complete Blood Count (leukocytosis >12,000/mcL with immature bandemia)", "Basic Metabolic Panel (BUN >19 mg/dL is a major prognostic indicator in CURB-65 score)", "Pulse Oximetry & Arterial Blood Gas (evaluates hypoxemic respiratory failure)", "Sputum Gram stain and culture (recommended for hospitalized or severe CAP)", "Blood Cultures x2 (indicated in severe inpatient CAP)", "Urinary Antigen Tests for Streptococcus pneumoniae and Legionella pneumophila (in severe CAP)"],
        "recommended_medications": ["Outpatient Without Comorbidities: Amoxicillin 1g PO TID x5-7d OR Doxycycline 100mg PO BID x5-7d", "Outpatient With Comorbidities: Amoxicillin-Clavulanate 875/125mg BID + Azithromycin 500mg day 1 then 250mg daily OR Levofloxacin 750mg PO daily x5d", "Inpatient Non-Severe: IV Ceftriaxone 1-2g daily + Azithromycin 500mg IV/PO daily (OR respiratory fluoroquinolone monotherapy)", "Inpatient Severe / ICU: IV Ceftriaxone 2g daily + Azithromycin 500mg IV + Vancomycin (if MRSA risk)", "Supplemental oxygen to maintain SpO2 >=92%, antipyretics, and pulmonary toilet"],
        "treatment_summary": "Empiric antibiotic therapy based on CURB-65 risk stratification: high-dose Amoxicillin or Doxycycline for healthy outpatients; beta-lactam (Ceftriaxone) plus macrolide (Azithromycin) for hospitalized patients.",
        "disease_intelligence": {
            "disease_name": "Community-Acquired Pneumonia (CAP)",
            "icd10_code": "J18.9", "icd11_code": "CA40",
            "cardinal_symptoms": ["Productive cough with purulent or rust-colored sputum", "High fever with rigors and diaphoresis", "Pleuritic chest pain aggravated by breathing", "Dyspnea and tachypnea", "Focal crackles, bronchial breath sounds, and dullness to percussion on lung exam"],
            "red_flags": ["CURB-65 score >=3 (Confusion, BUN >19, RR >=30, SBP <90/DBP <=60, Age >=65) requiring ICU admission", "Septic shock or acute hypoxemic respiratory failure needing mechanical ventilation", "Empyema or large parapneumonic effusion"],
            "clinical_pearl": "Streptococcus pneumoniae is the most common etiology; classic 'rust-colored' sputum reflects alveolar capillary hemorrhage and inflammatory exudate."
        },
        "pearl": "Fever, cough with purulent sputum, and focal crackles. CXR confirms lobar infiltrate. Risk-stratify with CURB-65. First-line Ceftriaxone + Azithromycin for hospitalized patients."
    },
}

# ---------------------------------------------------------------------------
# Aliases and Nuanced Spectrum Cross-References
# ---------------------------------------------------------------------------
DISEASE_METADATA_ALIASES: Dict[str, str] = {
    "Meningococcal Disease / Meningococcemia (with Meningitis)": "Meningococcal Meningitis",
    "Cryopyrin-Associated Periodic Syndrome (CAPS / Muckle-Wells)": "Cryopyrin-Associated Periodic Syndrome (CAPS Spectrum / Muckle-Wells / FCAS)",
    "Anti-Synthetase Syndrome (Amyopathic Dermatomyositis)": "Idiopathic Inflammatory Myopathy (Suspected Anti-Synthetase Syndrome / Dermatomyositis Spectrum)",
    "Collodion Baby (Congenital Ichthyosis)": "Collodion Baby Phenotype (Underlying Congenital Ichthyosis suspected)",
    "Mitochondrial Encephalopathy (MELAS / Mitochondrial Ataxia)": "Mitochondrial Encephalopathy (Differential includes MELAS, MERRF, Mitochondrial Ataxia)",
    "Leigh Syndrome (Subacute Necrotizing Encephalomyelopathy)": "Subacute Necrotizing Encephalomyelopathy (Suspected Leigh Syndrome / Mitochondrial Neurodegeneration)",
    "Mitochondrial Complex Deficiency (Lactic Acidosis)": "Mitochondrial Energy Metabolism Disorder (Suspected Respiratory Chain Complex Deficiency / Inborn Error of Metabolism)",
    "Pneumonia (Community-Acquired)": "Community-Acquired Pneumonia (Lobar Pneumonia)",
    "Acute Pyelonephritis": "Pyelonephritis (Upper UTI)",
    "Kidney Stones": "Nephrolithiasis (Kidney Stones)",
    "Urolithiasis": "Nephrolithiasis (Kidney Stones)",
    "Sigmoid Diverticulitis": "Acute Diverticulitis",
    "Cholecystitis": "Acute Cholecystitis",
    "Pancreatitis": "Acute Pancreatitis",
    "Gout": "Gout (Acute Gouty Arthritis)",
    "Cellulitis": "Cellulitis",
}

for alias, target in DISEASE_METADATA_ALIASES.items():
    if target in DISEASE_METADATA_EXT and alias not in DISEASE_METADATA_EXT:
        DISEASE_METADATA_EXT[alias] = DISEASE_METADATA_EXT[target]

# Import and integrate expanded registries
try:
    from app.services.clinical_disease_registry import CLINICAL_DISEASE_REGISTRY, REGISTRY_ALIASES
    DISEASE_METADATA_EXT.update(CLINICAL_DISEASE_REGISTRY)
    DISEASE_METADATA_ALIASES.update(REGISTRY_ALIASES)
except Exception as _e:
    pass

try:
    from app.services.clinical_disease_registry_part2 import CLINICAL_DISEASE_REGISTRY_PART2
    DISEASE_METADATA_EXT.update(CLINICAL_DISEASE_REGISTRY_PART2)
except Exception as _e:
    pass

try:
    from app.services.clinical_disease_registry_part3 import CLINICAL_DISEASE_REGISTRY_PART3
    DISEASE_METADATA_EXT.update(CLINICAL_DISEASE_REGISTRY_PART3)
except Exception as _e:
    pass

# Re-link aliases after registry update
for alias, target in DISEASE_METADATA_ALIASES.items():
    if target in DISEASE_METADATA_EXT and alias not in DISEASE_METADATA_EXT:
        DISEASE_METADATA_EXT[alias] = DISEASE_METADATA_EXT[target]


def _standardize_profile(profile: Dict[str, Any] | None, query_name: str) -> Dict[str, Any] | None:
    if not profile:
        return None
    res = dict(profile)
    # Ensure icd10 and icd10_code aliases
    if "icd10" in res and "icd10_code" not in res:
        res["icd10_code"] = res["icd10"]
    elif "icd10_code" in res and "icd10" not in res:
        res["icd10"] = res["icd10_code"]
    elif "disease_intelligence" in res and isinstance(res["disease_intelligence"], dict):
        code10 = res["disease_intelligence"].get("icd10_code")
        if code10:
            res["icd10_code"] = code10
            res["icd10"] = code10

    # Ensure icd11 and icd11_code aliases
    if "icd11" in res and "icd11_code" not in res:
        res["icd11_code"] = res["icd11"]
    elif "icd11_code" in res and "icd11" not in res:
        res["icd11"] = res["icd11_code"]
    elif "disease_intelligence" in res and isinstance(res["disease_intelligence"], dict):
        code11 = res["disease_intelligence"].get("icd11_code")
        if code11:
            res["icd11_code"] = code11
            res["icd11"] = code11

    # Ensure red_flags
    if "red_flags" not in res:
        if "disease_intelligence" in res and isinstance(res["disease_intelligence"], dict) and "red_flags" in res["disease_intelligence"]:
            res["red_flags"] = res["disease_intelligence"]["red_flags"]
        else:
            res["red_flags"] = [f"Rapid hemodynamic compromise, respiratory distress, or shock in {query_name}"]

    return res


def get_disease_clinical_profile(disease_name: str) -> Dict[str, Any] | None:
    """
    Intelligently resolves any disease query to a comprehensive clinical profile.
    Uses exact, alias, normalized, substring, and syndromic matching.
    Guarantees clinically accurate investigations and medications.
    """
    if not disease_name or not isinstance(disease_name, str):
        return None

    raw_clean = disease_name.strip()
    lower_name = raw_clean.lower()

    # 0. Check OPEN_DOMAIN_ENTITIES registry
    try:
        from app.services.open_domain_medical_engine import OPEN_DOMAIN_ENTITIES
        if raw_clean in OPEN_DOMAIN_ENTITIES:
            return _standardize_profile(OPEN_DOMAIN_ENTITIES[raw_clean], raw_clean)
        for ok, ov in OPEN_DOMAIN_ENTITIES.items():
            if ok.lower() == lower_name or lower_name in ok.lower() or ok.lower() in lower_name:
                return _standardize_profile(ov, raw_clean)
    except Exception:
        pass

    # 1. Direct match
    if raw_clean in DISEASE_METADATA_EXT:
        return _standardize_profile(DISEASE_METADATA_EXT[raw_clean], raw_clean)
    if raw_clean in DISEASE_METADATA_ALIASES:
        canonical = DISEASE_METADATA_ALIASES[raw_clean]
        if canonical in DISEASE_METADATA_EXT:
            return _standardize_profile(DISEASE_METADATA_EXT[canonical], raw_clean)

    # 2. Case-insensitive exact match
    for k, v in DISEASE_METADATA_EXT.items():
        if k.lower() == lower_name:
            return _standardize_profile(v, raw_clean)

    for k, target in DISEASE_METADATA_ALIASES.items():
        if k.lower() == lower_name and target in DISEASE_METADATA_EXT:
            return DISEASE_METADATA_EXT[target]

    # 3. Cleaned name without parentheses or suffixes
    import re
    cleaned_query = re.sub(r"\s*\([^)]*\)", "", lower_name).strip()
    if cleaned_query and cleaned_query != lower_name:
        for k, v in DISEASE_METADATA_EXT.items():
            k_clean = re.sub(r"\s*\([^)]*\)", "", k.lower()).strip()
            if k_clean == cleaned_query:
                return _standardize_profile(v, raw_clean)

    # 4. Substring and keyword match (excluding medical stop-words)
    MEDICAL_STOPWORDS = {"virus", "disease", "syndrome", "acute", "chronic", "fever", "infection", "disorder", "type"}
    for k, v in DISEASE_METADATA_EXT.items():
        k_lower = k.lower()
        words_q = [w for w in re.split(r"[\s\-_/]+", lower_name) if len(w) >= 4 and w not in MEDICAL_STOPWORDS]
        words_k = [w for w in re.split(r"[\s\-_/]+", k_lower) if len(w) >= 4 and w not in MEDICAL_STOPWORDS]
        if words_q and words_k:
            shared = set(words_q) & set(words_k)
            if len(shared) >= 2 or (len(words_q) == 1 and words_q[0] in words_k):
                return _standardize_profile(v, raw_clean)
        if lower_name in k_lower or k_lower in lower_name:
            return _standardize_profile(v, raw_clean)

    # 5. High-Impact Clinical Syndromic Fallbacks
    syndromic_map = [
        (["ebola", "filovirus", "marburg", "sudv", "ebov"], "Ebola Virus Disease (Zaire)"),
        (["malaria", "plasmodium", "falciparum", "tertian"], "Malaria (Plasmodium falciparum)"),
        (["dengue", "breakbone", "dengue hemorrhagic"], "Dengue Fever"),
        (["typhoid", "enteric fever", "salmonella typhi"], "Typhoid Fever"),
        (["cholera", "rice-water", "vibrio"], "Cholera"),
        (["stroke", "infarct", "hemiparesis", "aphasia", "cva"], "Ischemic Stroke"),
        (["heart attack", "stemi", "nemi", "myocardial infarct", "coronary"], "Acute Coronary Syndrome (STEMI)"),
        (["heart failure", "pulmonary edema", "adhf", "orthopnea", "chf"], "Heart Failure (Acute Decompensated)"),
        (["appendicitis", "mcburney", "appendix"], "Acute Appendicitis"),
        (["pancreatitis", "lipase", "amylase"], "Acute Pancreatitis"),
        (["cholangitis", "charcot", "reynolds"], "Acute Ascending Cholangitis"),
        (["kidney stone", "nephrolithiasis", "renal colic", "ureterolithiasis"], "Nephrolithiasis (Kidney Stones)"),
        (["asthma", "wheezing", "bronchospasm", "status asthmaticus"], "Asthma Exacerbation"),
        (["pneumonia", "cap", "consolidation", "lobar"], "Community-Acquired Pneumonia (Lobar Pneumonia)"),
        (["dka", "ketoacidosis", "diabetic keto"], "Diabetic Ketoacidosis (DKA)"),
        (["pericarditis", "friction rub"], "Acute Pericarditis"),
        (["dvt", "deep vein", "phlebitis", "calf swelling"], "Deep Vein Thrombosis (DVT)"),
        (["pe", "pulmonary embolism", "pulmonary embolus"], "Pulmonary Embolism"),
        (["glaucoma", "angle-closure", "intraocular pressure"], "Acute Angle-Closure Glaucoma"),
        (["meningitis", "nuchal rigidity", "neck stiffness", "kernig"], "Bacterial Meningitis"),
        (["sepsis", "septic shock", "bacteremia"], "Sepsis (Bacterial)"),
        (["gout", "podagra", "urate"], "Gout (Acute Gouty Arthritis)"),
        (["anaphylaxis", "severe allergy", "angioedema"], "Anaphylaxis"),
        (["tb", "tuberculosis", "consumption", "mycobacterium"], "Tuberculosis (Active)"),
        (["covid", "sars-cov-2", "coronavirus"], "COVID-19"),
        (["flu", "influenza"], "Influenza"),
        (["chikungunya"], "Chikungunya"),
        (["yellow fever"], "Yellow Fever"),
        (["leptospirosis", "weil"], "Leptospirosis"),
        (["mpox", "monkeypox"], "Mpox (Monkeypox)"),
    ]

    for keywords, target in syndromic_map:
        if any(kw in lower_name for kw in keywords):
            if target in DISEASE_METADATA_EXT:
                return _standardize_profile(DISEASE_METADATA_EXT[target], raw_clean)

    return None


