"""DocAssistIQ — Comprehensive Clinical Disease Registry (Universal Coverage).

Provides evidence-based diagnostic investigations, guideline-directed medications,
and clinical intelligence profiles for universal disease entities across all medical
specialties. Aligned with WHO, CDC, IDSA, ACC/AHA, ATS, KDIGO, and GINA standards.
"""

from typing import Dict, Any

CLINICAL_DISEASE_REGISTRY: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # 1. HIGH-CONSEQUENCE INFECTIOUS & TROPICAL PATHOGENS
    # =========================================================================
    "Sudan Ebolavirus Disease": {
        "icd10": "A98.4", "icd11": "1D60.2", "category": "Viral Hemorrhagic Fever — Orthoebolavirus", "triage": "EMERGENT",
        "immediate_tests": [
            "Sudan Ebolavirus RT-PCR (Whole Blood — BSL-4 facility)",
            "Complete Blood Count with differential (marked lymphopenia, severe thrombocytopenia)",
            "Coagulation Panel (PT/INR, aPTT, D-Dimer, Fibrinogen for DIC evaluation)",
            "Comprehensive Metabolic Panel (AST >> ALT, BUN, Creatinine, Electrolytes)",
            "Malaria RDT and Thick/Thin Blood Film (co-endemic rule out)"
        ],
        "recommended_investigations": [
            "Sudan ebolavirus RT-PCR (BSL-4 reference laboratory confirmation)",
            "Serial Complete Blood Count with Platelets (daily monitoring for hemorrhage risk)",
            "Comprehensive Metabolic Panel (daily renal failure and hypokalemia surveillance)",
            "Coagulation Studies (PT/INR, aPTT, D-Dimer, Fibrinogen)",
            "Blood Cultures x2 sets (aerobic + anaerobic to exclude secondary bacteremia)",
            "Venous Blood Gas and Serum Lactate (shock and tissue hypoperfusion marker)",
            "Malaria Rapid Diagnostic Test and Microscopy"
        ],
        "recommended_medications": [
            "Aggressive IV Fluid Resuscitation (Balanced crystalloids / Ringer's Lactate titrated to urine output >=0.5-1.0 mL/kg/h)",
            "IV Potassium and Magnesium chloride replacement (cardiac dysrhythmia prevention)",
            "Empiric IV Ceftriaxone 2g daily (prevent bacterial translocation across compromised gut)",
            "IV Ondansetron 4-8mg q8h PRN for severe vomiting",
            "Therapeutic Alert: Zaire monoclonal antibodies (Inmazeb, Ebanga) are INEFFECTIVE against Sudan virus; supportive ICU care is lifesaving"
        ],
        "first_line_treatment": "Immediate high-level isolation (BSL-4 barrier precautions) and aggressive volume-targeted fluid resuscitation with balanced crystalloids.",
        "treatment_summary": "Strict Level 4 barrier isolation and immediate public health reporting. Survival hinges on early, aggressive IV fluid/electrolyte replacement and intensive organ support.",
        "disease_intelligence": {
            "disease_name": "Sudan Ebolavirus Disease (SUDV)",
            "etiology": "Sudan ebolavirus (genus Orthoebolavirus, family Filoviridae)",
            "icd10_code": "A98.4", "icd11_code": "1D60.2",
            "transmission": "Direct contact with blood, body fluids, or organs of infected individuals or contaminated surfaces.",
            "incubation_period": "2 to 21 days (mean 6 to 12 days)",
            "cardinal_symptoms": ["Acute high fever (>38.5°C)", "Profound weakness/prostration", "Severe watery diarrhea", "Persistent vomiting", "Mucosal bleeding / petechiae"],
            "red_flags": ["Hypotension / circulatory shock", "Oliguria / anuria (acute tubular necrosis)", "Overt hemorrhage (hematemesis, melena)", "Encephalopathy / coma"],
            "pathophysiology": "Systemic viral replication in dendritic cells and macrophages triggers massive cytokine release (TNF-alpha, IL-6), extensive endothelial injury, microvascular leakage, DIC, and multi-organ failure.",
            "clinical_pearl": "Unlike Zaire EBOV, there is currently no FDA-approved monoclonal antibody or licensed vaccine for Sudan virus; optimized supportive critical care dramatically reduces mortality from 70% to <35%."
        },
        "pearl": "Filovirus causing periodic Ugandan outbreaks. Inmazeb is ineffective. Aggressive early IV fluid resuscitation and electrolyte correction are the mainstays of survival."
    },

    "Lassa Fever": {
        "icd10": "A96.2", "icd11": "1D62", "category": "Viral Hemorrhagic Fever — Arenavirus", "triage": "EMERGENT",
        "immediate_tests": [
            "Lassa Virus RT-PCR (Blood — BSL-4 / Reference Laboratory)",
            "Complete Blood Count (leukopenia, thrombocytopenia)",
            "Comprehensive Metabolic Panel (AST elevated >3x ALT indicates severe hepatic necrosis)",
            "Coagulation Profile (PT/INR, aPTT, Fibrinogen)",
            "Malaria RDT and Blood Film (mandatory exclusion in West Africa)"
        ],
        "recommended_investigations": [
            "Lassa Virus RT-PCR (definitive acute diagnostic test)",
            "Lassa virus IgM/IgG ELISA (detectable after day 7)",
            "Serial AST/ALT transaminases (AST >150 IU/L correlates directly with mortality)",
            "Serum Creatinine, BUN, and Urinalysis (proteinuria is frequent and prognostic)",
            "Coagulation Profile and D-Dimer (monitoring DIC)",
            "Blood cultures and Malaria microscopy"
        ],
        "recommended_medications": [
            "IV Ribavirin: Loading dose 33 mg/kg (max 2g) IV, then 16 mg/kg (max 1g) q6h for 4 days, then 8 mg/kg (max 500mg) q8h for 6 days (most effective within first 6 days of illness)",
            "IV Balanced Crystalloids (Ringer's Lactate titrated to maintain organ perfusion)",
            "Paracetamol 500-1000mg q6h PRN (avoid NSAIDs due to platelet dysfunction and hemorrhage risk)",
            "Empiric IV Ceftriaxone 2g daily for secondary bacterial infection coverage"
        ],
        "first_line_treatment": "IV Ribavirin initiated within the first 6 days of illness combined with aggressive supportive care in barrier isolation.",
        "treatment_summary": "Early administration of IV Ribavirin significantly reduces mortality. Strict droplet/contact isolation. Avoid NSAIDs and IM injections.",
        "disease_intelligence": {
            "disease_name": "Lassa Fever",
            "etiology": "Lassa mammarenavirus (family Arenaviridae)",
            "icd10_code": "A96.2", "icd11_code": "1D62",
            "transmission": "Zoonotic reservoir is Mastomys natalensis (multimammate rat); exposure to rat excreta or human-to-human body fluid contact.",
            "incubation_period": "6 to 21 days (mean 10 days)",
            "cardinal_symptoms": ["Insidious fever and malaise", "Retro-sternal chest pain", "Severe pharyngitis with white tonsillar exudates", "Facial and neck edema", "Proteinuria"],
            "red_flags": ["Overt mucosal hemorrhage", "Encephalopathy / seizures", "Hypotensive shock", "AST >150 IU/L", "Third trimester pregnancy (80% fetal/maternal mortality)"],
            "pathophysiology": "Endothelial dysfunction without massive cytopathology leads to capillary leak, selective platelet dysfunction, pleural/pericardial effusions, and terminal hypovolemic shock.",
            "clinical_pearl": "Sensorineural hearing loss occurs in 25-30% of convalescent patients (unilateral or bilateral) and is permanent in half of cases."
        },
        "pearl": "Endemic in West Africa (Nigeria, Sierra Leone). Mastomys rat vector. Pharyngitis, retrosternal pain, facial edema. IV Ribavirin is effective when started early. Sensorineural deafness is a common sequela."
    },

    "Crimean-Congo Hemorrhagic Fever": {
        "icd10": "A98.0", "icd11": "1D63", "category": "Viral Hemorrhagic Fever — Nairovirus", "triage": "EMERGENT",
        "immediate_tests": [
            "CCHF Virus RT-PCR (Blood — BSL-4/high-containment facility)",
            "Complete Blood Count (profound early thrombocytopenia, leukopenia)",
            "Coagulation Profile (PT/INR, aPTT, Fibrinogen, D-Dimer — rapid progression to DIC)",
            "Comprehensive Metabolic Panel (marked AST/ALT and CPK elevation)",
            "Malaria RDT and Blood Film (if travel to endemic overlap areas)"
        ],
        "recommended_investigations": [
            "CCHF Virus RT-PCR (positive during first 7-10 days of viremia)",
            "CCHF IgM/IgG ELISA (detectable after day 5-7)",
            "Serial Platelet Count and Fibrinogen (surveillance for severe DIC)",
            "Liver function tests and Creatine Kinase (CPK elevation reflects rhabdomyolysis)",
            "Blood Cultures and inflammatory markers"
        ],
        "recommended_medications": [
            "Oral / IV Ribavirin: 30 mg/kg initial dose, then 15 mg/kg q6h x4 days, then 7.5 mg/kg q8h x6 days (WHO guideline for suspected/confirmed CCHF)",
            "Fresh Frozen Plasma (FFP), Platelet transfusions, and Cryoprecipitate for active coagulopathy",
            "Judicious IV crystalloid fluid management (avoid aggressive over-resuscitation in capillary leak)",
            "Analgesia with Paracetamol; strict contraindication to Aspirin and NSAIDs"
        ],
        "first_line_treatment": "Strict barrier isolation, Ribavirin therapy, and aggressive replacement of platelets and coagulation factors for DIC.",
        "treatment_summary": "High risk of nosocomial transmission via blood/body fluids. Early Ribavirin and platelet/FFP transfusion protocol.",
        "disease_intelligence": {
            "disease_name": "Crimean-Congo Hemorrhagic Fever (CCHF)",
            "etiology": "Crimean-Congo hemorrhagic fever virus (Orthonairovirus / Nairoviridae)",
            "icd10_code": "A98.0", "icd11_code": "1D63",
            "transmission": "Bite of Hyalomma ticks or direct contact with blood/tissues of infected viremic livestock (slaughterhouse workers, shepherds) or nosocomial exposure.",
            "incubation_period": "1 to 3 days (tick bite, max 9 days); 5 to 6 days (blood contact, max 13 days)",
            "cardinal_symptoms": ["Sudden high fever and severe headache", "Intense back and abdominal pain", "Photophobia and neck stiffness", "Prominent petechial rash on soft palate and skin", "Uncontrolled bleeding from multiple puncture sites"],
            "red_flags": ["Severe thrombocytopenia (<20,000/mcL)", "Massive gastrointestinal or pulmonary hemorrhage", "AST/ALT >1000 IU/L", "Hepatorenal failure"],
            "pathophysiology": "Infection of endothelial cells and hepatocytes causes vascular damage, intense inflammatory response, severe consumption coagulopathy (DIC), and circulatory collapse.",
            "clinical_pearl": "Highest risk among livestock handlers and slaughterhouse workers in the Balkans, Middle East, Central Asia, and Mediterranean. Petechial enanthem on the uvula/palate is an early diagnostic clue."
        },
        "pearl": "Hyalomma tick or livestock blood exposure. Sudden fever, severe myalgia, rapid onset of petechiae and massive hemorrhage. Ribavirin + aggressive blood product support."
    },

    "Rift Valley Fever": {
        "icd10": "A92.4", "icd11": "1D23", "category": "Tropical Arboviral / Hemorrhagic", "triage": "URGENT",
        "immediate_tests": [
            "Rift Valley Fever RT-PCR (Blood — acute phase days 1-5)",
            "RVF IgM and IgG ELISA",
            "Complete Blood Count (leukopenia, thrombocytopenia)",
            "Liver Function Tests (AST/ALT markedly elevated)",
            "Dilated Fundus Examination (for macular retinitis)"
        ],
        "recommended_investigations": [
            "RVF Virus RT-PCR (blood/tissue)",
            "RVF IgM/IgG Serology (ELISA)",
            "Serial Complete Blood Count and Liver Enzymes",
            "Coagulation Profile (PT/INR, aPTT, Fibrinogen)",
            "Ophthalmology Dilated Funduscopy (screens for retinal hemorrhage / macular infarction)",
            "Lumbar Puncture with CSF analysis (if meningoencephalitis suspected)"
        ],
        "recommended_medications": [
            "Supportive Care: IV balanced crystalloids and hemodynamic monitoring",
            "Antipyresis: Paracetamol 500-1000mg q6h PRN (avoid NSAIDs/Aspirin due to hemorrhagic risk)",
            "Ophthalmic Referral: Urgent retina specialist evaluation for vision-threatening macular lesions",
            "Anticonvulsants (Levetiracetam / Lorazepam) if late meningoencephalitis manifests"
        ],
        "first_line_treatment": "Supportive fluid and hemodynamic management; early ophthalmic screening; strict vector and contact precautions.",
        "treatment_summary": "Most cases are mild; 1-2% develop hemorrhagic fever, encephalitis, or macular retinitis causing permanent visual impairment.",
        "disease_intelligence": {
            "disease_name": "Rift Valley Fever (RVF)",
            "etiology": "Rift Valley fever phlebovirus (family Phenuiviridae)",
            "icd10_code": "A92.4", "icd11_code": "1D23",
            "transmission": "Mosquito bites (Aedes and Culex spp.) or contact with blood, body fluids, or aborted fetuses of infected livestock.",
            "incubation_period": "2 to 6 days",
            "cardinal_symptoms": ["Biphasic fever and intense retro-orbital headache", "Severe generalized myalgia", "Loss of central vision (retinitis)", "Epigastric discomfort and vomiting"],
            "red_flags": ["Jaundice and bleeding diathesis (hemorrhagic form, 50% CFR)", "Meningoencephalitis (confusion, hallucinations, coma 1-4 weeks later)", "Macular whitening/infarction (retinitis)"],
            "pathophysiology": "Hepatic tropism with extensive hepatocellular necrosis; microvascular thrombosis in retinal and cerebral vessels.",
            "clinical_pearl": "Veterinarians, farmers, and slaughterhouse workers following heavy seasonal rainfall (mosquito booms). Retinal vasculitis affecting the macula occurs in 10% and can cause permanent blindness."
        },
        "pearl": "Phlebovirus linked to livestock exposure and heavy rains. Biphasic fever, retinitis with permanent visual loss, and potential hemorrhagic fever or late encephalitis."
    },

    "Malaria (Plasmodium vivax)": {
        "icd10": "B51.9", "icd11": "1F41", "category": "Parasitic / Tropical Infectious", "triage": "URGENT",
        "immediate_tests": [
            "Thick and Thin Blood Smears with Giemsa Stain (trophozoites, Schüffner dots, enlarged RBCs)",
            "Malaria Rapid Diagnostic Test (RDT with pan-LDH / aldolase target)",
            "G6PD Quantitative Enzyme Assay (mandatory before prescribing Primaquine/Tafenoquine)",
            "Complete Blood Count (normocytic anemia, thrombocytopenia)",
            "Basic Metabolic Panel and Total Bilirubin (unconjugated hyperbilirubinemia)"
        ],
        "recommended_investigations": [
            "Giemsa-stained Thick and Thin Blood Films (serial q12h if initially negative)",
            "Malaria PCR (species identification: confirms P. vivax vs P. falciparum co-infection)",
            "Quantitative G6PD Enzymatic Assay (specifies enzyme activity level prior to 8-aminoquinoline therapy)",
            "Complete Blood Count with Platelets and Reticulocyte count",
            "Serum Electrolytes, Creatinine, BUN, and Total/Direct Bilirubin"
        ],
        "recommended_medications": [
            "Blood-Stage Schizontocidal: Chloroquine phosphate (600 mg base initial, 300 mg at 6h, 24h, 48h) in chloroquine-sensitive areas OR Artemether-Lumefantrine (80/480mg BID x3d with fatty meal) in resistant zones",
            "Anti-Relapse Hypnozoitocidal (Normal G6PD): Primaquine phosphate 30 mg base PO daily for 14 days with food OR Tafenoquine 300 mg single dose PO with food",
            "Intermediate G6PD Deficiency: Primaquine 45 mg base PO once weekly for 8 weeks under close clinical observation",
            "Antipyresis: Paracetamol 500-1000 mg q6h PRN for paroxysms"
        ],
        "first_line_treatment": "Artemether-Lumefantrine or Chloroquine for acute erythrocytic stage PLUS Primaquine for 14 days (or single-dose Tafenoquine) for radical cure of dormant liver hypnozoites after G6PD testing.",
        "treatment_summary": "Radical cure requires killing blood parasites AND dormant liver hypnozoites. Always perform quantitative G6PD assay before Primaquine or Tafenoquine to prevent massive acute intravascular hemolysis.",
        "disease_intelligence": {
            "disease_name": "Vivax Malaria (Benign Tertian Malaria)",
            "etiology": "Plasmodium vivax (protozoan parasite transmitted by female Anopheles mosquitoes)",
            "icd10_code": "B51.9", "icd11_code": "1F41",
            "transmission": "Bite of infected female Anopheles mosquitoes; blood transfusion, congenital.",
            "incubation_period": "12 to 18 days (delayed relapses up to 9-12 months via dormant hypnozoites)",
            "cardinal_symptoms": ["Tertian fever paroxysms (cold stage/rigors -> hot fever spike -> diaphoresis every 48 hours)", "Severe headache and fatigue", "Splenomegaly", "Pallor and jaundice"],
            "red_flags": ["Severe acute anemia (Hb <7 g/dL)", "Spontaneous splenic rupture (sudden LUQ pain, hypotension)", "Dark brown/black urine (hemoglobinuria / G6PD hemolysis)"],
            "pathophysiology": "P. vivax invades young reticulocytes via Duffy antigen receptor (DARC). Dormant liver stages (hypnozoites) remain latent in hepatocytes and cause periodic relapses months after primary infection.",
            "clinical_pearl": "People lacking the Duffy blood group (Fy(a-b-)), widespread in West Africa, are largely resistant to P. vivax infection. Spontaneous splenic rupture is an acute surgical emergency unique to vivax malaria."
        },
        "pearl": "Tertian 48h fever cycle, enlarged RBCs with Schüffner dots on blood smear. Radical cure requires G6PD testing followed by Primaquine/Tafenoquine to destroy liver hypnozoites."
    },

    "Cholera": {
        "icd10": "A00.9", "icd11": "1A00", "category": "Enteric Bacterial Infection", "triage": "EMERGENT",
        "immediate_tests": [
            "Stool Darkfield Microscopy / Hanging Drop (rapid detection of darting motility)",
            "Cholera Rapid Diagnostic Test (Crystal VC dipstick on liquid stool)",
            "Serum Electrolytes, BUN, and Creatinine (severe hypokalemia, metabolic acidosis, prerenal AKI)",
            "Arterial / Venous Blood Gas (evaluating severe base-deficit metabolic acidosis)",
            "Point-of-care Blood Glucose (hypoglycemia screening, especially in pediatric patients)"
        ],
        "recommended_investigations": [
            "Stool Culture on Thiosulfate-Citrate-Bile Salts-Sucrose (TCBS) agar (yellow sucrose-fermenting colonies)",
            "Vibrio cholerae O1/O139 Serotyping and Antimicrobial Susceptibility Testing",
            "Serial Serum Electrolytes (Sodium, Potassium, Bicarbonate) and Creatinine",
            "Venous Blood Gas (monitoring resolution of metabolic acidosis)",
            "Stool PCR for cholera toxin (ctxA) gene confirmation"
        ],
        "recommended_medications": [
            "IV Rehydration (WHO Protocol for Severe Dehydration): IV Ringer's Lactate 100 mL/kg (30 mL/kg in first 30 min, 70 mL/kg over 2.5 hours in adults)",
            "Oral Rehydration Salts (ORS): Low-osmolarity WHO ORS solution given continuously once patient can drink",
            "First-Line Antibiotic (Adults): Doxycycline 300 mg PO single dose (reduces volume and duration of diarrhea)",
            "Alternative Antibiotics: Azithromycin 1g PO single dose (preferred in pregnant women and children) OR Ciprofloxacin 1g PO single dose",
            "Zinc Supplementation (Pediatric): 20 mg elemental zinc PO daily for 10-14 days (10 mg if <6 months)"
        ],
        "first_line_treatment": "Aggressive and immediate IV rehydration with Ringer's Lactate followed by WHO low-osmolarity Oral Rehydration Salts and single-dose Doxycycline or Azithromycin.",
        "treatment_summary": "Death occurs from hypovolemic shock within hours without rehydration. Fluid replacement is the single life-saving intervention; antibiotics shorten illness duration.",
        "disease_intelligence": {
            "disease_name": "Cholera",
            "etiology": "Vibrio cholerae serogroups O1 (biotypes Classical and El Tor) and O139",
            "icd10_code": "A00.9", "icd11_code": "1A00",
            "transmission": "Fecal-oral contamination of drinking water or food; common in conflict, humanitarian crises, and inadequate sanitation infrastructure.",
            "incubation_period": "2 hours to 5 days (mean 1-2 days)",
            "cardinal_symptoms": ["Painless profuse watery diarrhea ('rice-water stool')", "Effortless vomiting", "Rapid severe dehydration (sunken eyes, loss of skin turgor, washerwoman hands)", "Intense muscle cramps in calves and abdomen (hypokalemia)"],
            "red_flags": ["Hypovolemic circulatory shock (unpalpable radial pulse, SBP <80)", "Anuria / acute tubular necrosis", "Severe metabolic acidosis (Kussmaul breathing)", "Hypoglycemic coma in children"],
            "pathophysiology": "Cholera toxin (CTX, an AB5 enterotoxin) binds GM1 ganglioside on enterocytes, activates adenylate cyclase, elevates intracellular cAMP, and drives massive active secretion of chloride and water into the intestinal lumen (up to 1L/hour).",
            "clinical_pearl": "Stool has a characteristic sweet, fishy odor and looks like cloudy rice-wash water. Antibiotics are an adjunct; mortality drops from >50% to <1% with timely fluid resuscitation alone."
        },
        "pearl": "Profuse painless 'rice-water' diarrhea causing rapid fatal hypovolemic shock. Immediate Ringer's Lactate IV + WHO ORS + single-dose Doxycycline or Azithromycin."
    },

    "Mpox (Monkeypox)": {
        "icd10": "B04", "icd11": "1E71", "category": "Zoonotic Orthopoxvirus", "triage": "URGENT",
        "immediate_tests": [
            "Mpox Virus DNA RT-PCR (Swab of lesion exudate, crust, or roof — dry sterile swab)",
            "Orthopoxvirus PCR (Confirmatory clade distinction: Clade I vs Clade IIb)",
            "Complete Blood Count with differential",
            "Comprehensive Metabolic Panel",
            "Sexual Health Screening: Syphilis serology (RPR/VDRL), HIV 4th gen Ag/Ab, GC/CT NAAT"
        ],
        "recommended_investigations": [
            "Lesion fluid/crust DNA PCR (swab vigorous rub of open lesion or vesicle roof)",
            "Viral clade genomic sequencing (distinguishes Clade I endemic/severe from Clade IIb global epidemic)",
            "Syphilis Treponemal/Non-Treponemal serology (frequent clinical mimic and co-infection)",
            "Pharyngeal and rectal swabs for Mpox and bacterial STI NAAT",
            "Slit-lamp examination by ophthalmology if periorbital or ocular lesions present"
        ],
        "recommended_medications": [
            "Antiviral Therapy (Severe / High-Risk / Immunocompromised / Ocular): Tecovirimat (TPOXX) 600 mg PO q12h with a full fatty meal for 14 days (or IV 200 mg q12h)",
            "Secondary Antiviral (Refractory): Cidofovir 5 mg/kg IV weekly with oral probenecid and saline hydration",
            "Topical Ophthalmic: Trifluridine 1% eye drops (under ophthalmology supervision if ocular involvement)",
            "Pain Management: Oral NSAIDs/Paracetamol; topical lidocaine or sitz baths for excruciating anorectal proctitis lesions",
            "Post-Exposure Prophylaxis: JYNNEOS (Modified Vaccinia Ankara) vaccine administered within 4-14 days of exposure"
        ],
        "first_line_treatment": "Lesion barrier isolation, symptomatic pain control (especially proctitis), and oral Tecovirimat (TPOXX) for patients with severe disease, extensive mucosal involvement, or immunosuppression.",
        "treatment_summary": "Contact and droplet precautions until all scabs have fallen off and fresh skin forms. Screen for concurrent STIs including HIV and Syphilis.",
        "disease_intelligence": {
            "disease_name": "Mpox (Monkeypox)",
            "etiology": "Monkeypox virus (genus Orthopoxvirus, family Poxviridae; Clade I and Clade II)",
            "icd10_code": "B04", "icd11_code": "1E71",
            "transmission": "Close, personal, skin-to-skin contact with infectious lesions or mucosal secretions; sexual contact; respiratory droplets; contact with contaminated fomites (bedding, towels).",
            "incubation_period": "3 to 17 days (mean 7 to 10 days)",
            "cardinal_symptoms": ["Deep-seated, well-circumscribed, umbilicated pustular lesions", "Marked lymphadenopathy (cervical, axillary, and prominent inguinal/femoral)", "Fever, chills, and myalgia prodrome", "Severe anorectal pain / proctitis", "Pharyngitis and odynophagia"],
            "red_flags": ["Confluent necrotic lesions in advanced HIV (CD4 <200/mcL — severe Clade IIb mortality)", "Corneal ulceration / keratitis (risk of blindness)", "Encephalitis / respiratory compromise from airway lesions"],
            "pathophysiology": "Entry through skin breaks or mucous membranes, initial replication in lymphoid tissue, primary viremia, secondary replication in liver/spleen, followed by secondary viremia and cutaneous eruption.",
            "clinical_pearl": "Prominent painful lymphadenopathy (submandibular, cervical, inguinal) distinctly differentiates Mpox from Smallpox and Varicella (Chickenpox)."
        },
        "pearl": "Orthopoxvirus with painful umbilicated pustules and marked lymphadenopathy. PCR of lesion roof is diagnostic. Tecovirimat (TPOXX) for severe disease or immunosuppressed patients."
    },

    "Leptospirosis": {
        "icd10": "A27.9", "icd11": "1D02", "category": "Zoonotic Spirochetal Infection", "triage": "URGENT",
        "immediate_tests": [
            "Leptospira DNA PCR (Blood/Serum during days 1-7; Urine after day 7)",
            "Complete Blood Count (neutrophilic leukocytosis, thrombocytopenia)",
            "Comprehensive Metabolic Panel (marked indirect/direct bilirubin elevation with modest AST/ALT elevation; elevated BUN/Creatinine)",
            "Creatine Kinase (CPK markedly elevated in leptospiral myositis)",
            "Urinalysis (proteinuria, microscopic hematuria, granular casts)"
        ],
        "recommended_investigations": [
            "Leptospira PCR (blood in week 1; urine in weeks 2-4)",
            "Microscopic Agglutination Test (MAT — reference standard serology with 4-fold titer rise)",
            "Leptospira IgM ELISA (screening test, positive from day 5-7)",
            "Liver Function Tests and Renal Function (hallmark is hyperbilirubinemia with disproportionately mild transaminitis)",
            "Chest X-Ray (diffuse alveolar infiltrates indicating severe pulmonary hemorrhage syndrome)",
            "12-lead ECG (atrial fibrillation, prolonged PR, non-specific ST-T changes)"
        ],
        "recommended_medications": [
            "Severe Inpatient / Weil's Disease: IV Penicillin G 1.5 million units IV q6h x7d OR IV Ceftriaxone 1-2g IV daily x7d",
            "Mild / Outpatient: Doxycycline 100 mg PO BID for 7 days OR Amoxicillin 500 mg PO TID for 7 days",
            "Hemodialysis: Early renal replacement therapy for oliguric acute kidney injury",
            "Critical Pulmonary Care: Mechanical ventilation with lung-protective low tidal volume for pulmonary hemorrhage syndrome"
        ],
        "first_line_treatment": "IV Ceftriaxone 1-2g daily or IV Penicillin G for severe/hospitalized cases; oral Doxycycline 100mg BID for mild outpatient disease; aggressive supportive renal and ventilatory care.",
        "treatment_summary": "Biphasic illness: bacteremic phase then immune phase. Severe Weil's disease (jaundice, AKI, hemorrhage) has high mortality and requires ICU management.",
        "disease_intelligence": {
            "disease_name": "Leptospirosis (Weil Disease)",
            "etiology": "Pathogenic spirochetes of the genus Leptospira (predominantly Leptospira interrogans)",
            "icd10_code": "A27.9", "icd11_code": "1D02",
            "transmission": "Contact of abraded skin or mucous membranes with water, soil, or mud contaminated with urine of infected animal reservoirs (especially rodents and livestock) during floods or water sports.",
            "incubation_period": "2 to 30 days (mean 7 to 12 days)",
            "cardinal_symptoms": ["Bilateral conjunctival suffusion without purulent discharge (pathognomonic hallmark)", "Severe calf and paraspinal muscle tenderness (extreme CPK elevation)", "Sudden high fever with chills and rigors", "Orange-tinted deep jaundice", "Oliguric renal failure"],
            "red_flags": ["Severe Pulmonary Hemorrhagic Syndrome (SPHS — rapid fatal hemoptysis)", "Acute Kidney Injury with anuria", "Hypotensive shock and cardiac dysrhythmias", "Altered mental status / meningism"],
            "pathophysiology": "Systemic vasculitis caused by spirochetal dissemination injuring capillary endothelial cells throughout the lung, liver, kidneys, and skeletal muscle.",
            "clinical_pearl": "Bilateral conjunctival suffusion (dilated scleral vessels without inflammatory exudate) combined with intense calf pain upon palpation points strongly to leptospirosis over malaria or dengue."
        },
        "pearl": "Flood water or rat urine contact. Classic conjunctival suffusion, severe calf tenderness, jaundice + renal failure (Weil's triad). IV Ceftriaxone or Penicillin G."
    },

    "Tuberculosis (Active)": {
        "icd10": "A15.0", "icd11": "1B10.0", "category": "Mycobacterial Infection", "triage": "URGENT",
        "immediate_tests": [
            "Sputum GeneXpert MTB/RIF Ultra NAAT (detects M. tuberculosis DNA & Rifampicin resistance in <2 hours)",
            "Acid-Fast Bacilli (AFB) Sputum Smear Microscopy (Ziehl-Neelsen or auramine fluorescent stain x3 consecutive samples)",
            "Chest Radiograph (PA view: apical/posterior upper lobe infiltrates, cavitation, or pleural effusion)",
            "HIV 4th Generation Ag/Ab Serology (mandatory co-testing)",
            "Complete Blood Count, Liver Function Tests, Serum Creatinine (baseline pre-treatment organ function)"
        ],
        "recommended_investigations": [
            "GeneXpert MTB/RIF Ultra on sputum (or BAL/pleural fluid)",
            "Mycobacterial Growth Indicator Tube (MGIT) liquid culture & solid Lowenstein-Jensen culture",
            "Phenotypic and genotypic Line Probe Assay (LPA) for second-line drug resistance (Isoniazid, Fluoroquinolones)",
            "Chest CT scan (high-resolution: demonstrates tree-in-bud pattern, cavitation, lymphadenopathy)",
            "Baseline Liver Panel (ALT, AST, Total Bilirubin) and Uric acid, Visual acuity / Ishihara color test (for Ethambutol)"
        ],
        "recommended_medications": [
            "Standard 4-Drug Intensive Phase (First 2 Months): Isoniazid (INH) 300 mg PO daily + Rifampin (RIF) 600 mg PO daily + Pyrazinamide (PZA) 1500-2000 mg PO daily + Ethambutol (EMB) 1200-1600 mg PO daily",
            "Continuation Phase (Months 3 to 6): Isoniazid 300 mg PO daily + Rifampin 600 mg PO daily",
            "Adjunctive Neuro-Protection: Pyridoxine (Vitamin B6) 25-50 mg PO daily (prevents INH peripheral neuropathy)",
            "MDR-TB Regimen (if Rifampin-resistant): Bedaquiline, Pretomanid, Linezolid +/- Moxifloxacin (BPaL/BPaLM regimen under specialist care)"
        ],
        "first_line_treatment": "Directly Observed Therapy (DOT) with 4-drug RIPE regimen (Rifampin, Isoniazid, Pyrazinamide, Ethambutol) for 2 months, followed by Rifampin + Isoniazid for 4 months, plus Pyridoxine.",
        "treatment_summary": "Airborne infection isolation (negative-pressure room, N95 respirators) until 3 consecutive negative AFB smears and clinical improvement on therapy. Baseline and serial monitoring of hepatic transaminases.",
        "disease_intelligence": {
            "disease_name": "Active Pulmonary Tuberculosis (TB)",
            "etiology": "Mycobacterium tuberculosis (acid-fast, slow-growing obligate aerobe)",
            "icd10_code": "A15.0", "icd11_code": "1B10.0",
            "transmission": "Inhalation of airborne droplet nuclei (<5 microns) generated by coughing, sneezing, or singing of infectious pulmonary/laryngeal TB patients.",
            "incubation_period": "2 to 12 weeks to tuberculin skin test conversion; active disease may emerge months to decades later",
            "cardinal_symptoms": ["Chronic productive cough lasting >3 weeks", "Hemoptysis (blood-streaked sputum to frank hemorrhage)", "Drenching night sweats", "Unintentional weight loss and anorexia", "Low-grade afternoon fever"],
            "red_flags": ["Massive hemoptysis (>200-400 mL/24h — risk of asphyxiation)", "Miliary TB (widespread hematogenous dissemination, ARDS)", "Tuberculous meningitis (headache, cranial nerve palsies, altered mental status)"],
            "pathophysiology": "Inhaled bacilli engulfed by alveolar macrophages; formation of caseating granulomas (Ghon focus) with surrounding multinucleated Langhans giant cells. Cavitation results when caseous centers liquefy and discharge bacilli into airways.",
            "clinical_pearl": "Rifampin causes harmless orange-red discoloration of body fluids (urine, sweat, tears, contact lenses). Pyrazinamide is the most hepatotoxic; Ethambutol causes dose-dependent optic neuritis (red-green color blindness)."
        },
        "pearl": "Chronic cough >3 weeks, night sweats, weight loss, upper lobe cavitation on CXR. Sputum GeneXpert MTB/RIF is first-line rapid test. 4-drug RIPE regimen + Pyridoxine."
    },

    "COVID-19": {
        "icd10": "U07.1", "icd11": "RA01", "category": "Respiratory Viral Pandemic Infection", "triage": "URGENT",
        "immediate_tests": [
            "SARS-CoV-2 RT-PCR or High-Sensitivity Rapid Antigen Test (Nasopharyngeal swab)",
            "Continuous Pulse Oximetry (screens for 'silent hypoxemia')",
            "Complete Blood Count (lymphopenia is hallmark)",
            "Inflammatory Biomarkers: CRP, Ferritin, D-Dimer, Procalcitonin",
            "Chest Radiograph or CT Chest (bilateral peripheral ground-glass opacities)"
        ],
        "recommended_investigations": [
            "SARS-CoV-2 RT-PCR (nasopharyngeal or saliva)",
            "Chest X-Ray / CT Chest (bilateral subpleural ground-glass opacification and consolidation)",
            "D-Dimer, Fibrinogen, PT/INR (screening for micro- and macro-vascular thromboembolism)",
            "High-sensitivity Troponin and BNP/NT-proBNP (surveillance for viral myocarditis and myocardial injury)",
            "Multiplex Respiratory PCR Panel (influenza A/B and RSV co-detection)"
        ],
        "recommended_medications": [
            "Outpatient Mild-to-Moderate at Risk: Nirmatrelvir/Ritonavir (Paxlovid) 300/100 mg PO BID for 5 days (initiated within 5 days of symptom onset) OR Remdesivir 200mg IV day 1 then 100mg IV days 2-3",
            "Hospitalized Requiring Oxygen: Dexamethasone 6 mg PO/IV daily for up to 10 days + IV Remdesivir 200 mg day 1 then 100 mg daily x5d",
            "Severe ICU / Rapid Deterioration: Add IL-6 receptor antagonist (Tocilizumab 8 mg/kg IV single dose) or JAK inhibitor (Baricitinib 4 mg PO daily)",
            "Thromboprophylaxis: Standard prophylactic-dose Low Molecular Weight Heparin (Enoxaparin 40 mg SC daily) for all hospitalized patients"
        ],
        "first_line_treatment": "Oxygen therapy to maintain SpO2 >=92-96%; oral Paxlovid for high-risk outpatients within 5 days; Dexamethasone 6mg daily + Remdesivir for hospitalized hypoxemic patients.",
        "treatment_summary": "Prone positioning improves oxygenation in hypoxemic patients. Dexamethasone is beneficial ONLY in patients requiring supplemental oxygen; prophylactic anticoagulation is mandatory in inpatients.",
        "disease_intelligence": {
            "disease_name": "COVID-19 (Coronavirus Disease 2019)",
            "etiology": "Severe Acute Respiratory Syndrome Coronavirus 2 (SARS-CoV-2 / Coronaviridae)",
            "icd10_code": "U07.1", "icd11_code": "RA01",
            "transmission": "Inhalation of respiratory droplets and aerosols; higher transmission risk in enclosed, poorly ventilated indoor spaces.",
            "incubation_period": "2 to 14 days (mean 3 to 5 days for newer subvariants)",
            "cardinal_symptoms": ["Fever or chills", "Dry cough and dyspnea", "Sudden anosmia (loss of smell) and ageusia (loss of taste)", "Fatigue and body aches", "Sore throat and nasal congestion"],
            "red_flags": ["'Silent / Happy Hypoxemia' (SpO2 <90% without marked respiratory distress)", "Acute Respiratory Distress Syndrome (ARDS)", "Cytokine release syndrome (exponentially rising CRP/Ferritin/D-Dimer)", "Pulmonary embolism / arterial thrombosis"],
            "pathophysiology": "Spike glycoprotein binds cell-surface ACE2 receptor aided by TMPRSS2 protease; endothelial damage, complement activation, and microvascular thrombosis (immunothrombosis) trigger alveolar damage and ARDS.",
            "clinical_pearl": "Paxlovid has extensive drug-drug interactions via strong CYP3A4 inhibition by Ritonavir (contraindicated or requires dose withholding of statins, anticoagulants, antiarrhythmics, calcineurin inhibitors)."
        },
        "pearl": "Respiratory viral illness hallmarked by anosmia, fever, and hypoxemia. Bilateral ground-glass infiltrates. Paxlovid for outpatients at risk; Dexamethasone + Remdesivir for patients requiring supplemental oxygen."
    },

    "Influenza": {
        "icd10": "J10.1", "icd11": "1E30", "category": "Respiratory Viral Infection", "triage": "URGENT",
        "immediate_tests": [
            "Multiplex Rapid Molecular NAAT / PCR for Influenza A and B (Nasopharyngeal swab — far superior to rapid antigen)",
            "Pulse Oximetry (evaluating hypoxemia and viral pneumonia)",
            "Complete Blood Count (leukopenia or normal WBC; marked leukocytosis suggests secondary bacterial pneumonia)",
            "Chest Radiograph (PA view if hypoxemic, tachypneic, or severe crackles present)"
        ],
        "recommended_investigations": [
            "Multiplex RT-PCR for Influenza A, Influenza B, RSV, and SARS-CoV-2",
            "Chest X-Ray (evaluates primary influenza pneumonitis vs secondary bacterial consolidation)",
            "Sputum Gram stain and culture (if secondary bacterial pneumonia suspected — S. aureus, S. pneumoniae)",
            "Basic Metabolic Panel and Blood Gas (if severe respiratory distress)"
        ],
        "recommended_medications": [
            "First-Line Neuraminidase Inhibitor: Oseltamivir (Tamiflu) 75 mg PO BID for 5 days (ideal within 48h of onset; still beneficial later in hospitalized/high-risk patients)",
            "Cap-Dependent Endonuclease Inhibitor: Baloxavir marboxil (Xofluza) 40 mg single dose PO (80 mg if >=80 kg)",
            "Inhaled Alternative: Zanamivir 10 mg (two 5mg inhalations) BID for 5 days (avoid in asthma/COPD due to bronchospasm risk)",
            "Antipyretics: Paracetamol 650-1000 mg q6h PRN (Strict contraindication to Aspirin in children/adolescents due to Reye Syndrome)"
        ],
        "first_line_treatment": "Oral Oseltamivir 75mg BID for 5 days (or single-dose Baloxavir) started as early as possible, plus antipyretics, hydration, and droplet isolation.",
        "treatment_summary": "Most effective within 48 hours of onset. Prescribe to all hospitalized patients, severe disease, or outpatients at high risk of complications regardless of illness duration.",
        "disease_intelligence": {
            "disease_name": "Influenza (Seasonal Flu)",
            "etiology": "Influenza virus types A and B (family Orthomyxoviridae)",
            "icd10_code": "J10.1", "icd11_code": "1E30",
            "transmission": "Inhalation of infectious droplets generated by coughing or sneezing; direct contact with contaminated surfaces.",
            "incubation_period": "1 to 4 days (mean 2 days)",
            "cardinal_symptoms": ["Abrupt onset of high fever and severe rigors", "Prominent myalgias and backache", "Severe frontal/retro-orbital headache", "Non-productive dry cough and sore throat", "Profound exhaustion and malaise"],
            "red_flags": ["Secondary bacterial pneumonia (recurrent fever and purulent sputum after initial improvement)", "Severe viral pneumonia and ARDS", "Myocarditis / pericarditis", "Reye syndrome (in children given Aspirin)"],
            "pathophysiology": "Viral hemagglutinin binds sialic acid receptors on ciliated respiratory epithelium, enters cells, and causes epithelial necrosis, desquamation, and massive systemic interferon-alpha release driving severe myalgias.",
            "clinical_pearl": "Biphasic fever curve ('improvement followed by sudden high fever and purulent sputum') is a classic harbinger of post-influenza secondary bacterial pneumonia, often caused by MRSA or Streptococcus pneumoniae."
        },
        "pearl": "Abrupt onset of fever, severe myalgia, headache, and dry cough. Oseltamivir within 48h. Never give Aspirin to pediatric patients (Reye syndrome). Watch for secondary Staph aureus pneumonia."
    },

    "African Trypanosomiasis (Sleeping Sickness)": {
        "icd10": "B56.9", "icd11": "1F42", "category": "Parasitic / Tropical Neglected", "triage": "URGENT",
        "immediate_tests": [
            "Giemsa-stained Thick and Thin Blood Films (detection of extracellular trypomastigotes)",
            "Lymph Node Aspirate Microscopy (cervical node fluid — Winterbottom sign)",
            "Card Agglutination Test for Trypanosomiasis (CATT for T. b. gambiense screening)",
            "Lumbar Puncture with CSF Analysis (CSF white cell count and trypanosome search — staging determines therapy)"
        ],
        "recommended_investigations": [
            "Blood and lymph node aspirate microscopy (wet mount and Giemsa smear)",
            "Mini-anion exchange centrifugation technique (mAECT) on blood",
            "CSF examination for staging: CSF WBC count (>5 cells/mcL indicates Stage 2 meningoencephalitic disease) and presence of trypanosomes",
            "Complete Blood Count (anemia, thrombocytopenia) and Serum IgM (markedly elevated)"
        ],
        "recommended_medications": [
            "T. b. gambiense (Stage 1 & Non-Severe Stage 2): Fexinidazole 1800 mg PO daily with food for 4 days, then 1200 mg PO daily for 6 days (WHO first-line all-oral treatment)",
            "T. b. gambiense (Severe Stage 2, CSF WBC >100): Nifurtimox-Eflornithine Combination Therapy (NECT) — IV Eflornithine 400 mg/kg/day in 2 infusions for 7 days + oral Nifurtimox 15 mg/kg/day in 3 divided doses for 10 days",
            "T. b. rhodesiense (Stage 1 Hemolymphatic): Suramin 20 mg/kg (max 1g) IV on days 1, 3, 7, 14, 21",
            "T. b. rhodesiense (Stage 2 Neurological): Melarsoprol 2.2 mg/kg IV daily for 10 days (co-prescribe Prednisolone to reduce reactive encephalopathy)"
        ],
        "first_line_treatment": "Oral Fexinidazole for T. b. gambiense (NECT for severe Stage 2); Suramin for Stage 1 rhodesiense and Melarsoprol for Stage 2 rhodesiense under expert guidance.",
        "treatment_summary": "Staging via lumbar puncture is mandatory. Stage 1 is hemolymphatic; Stage 2 involves the CNS. Fexinidazole has revolutionized gambiense therapy as an all-oral regimen.",
        "disease_intelligence": {
            "disease_name": "Human African Trypanosomiasis (HAT)",
            "etiology": "Trypanosoma brucei gambiense (West/Central Africa) and Trypanosoma brucei rhodesiense (East/Southern Africa)",
            "icd10_code": "B56.9", "icd11_code": "1F42",
            "transmission": "Bite of infected tsetse flies (genus Glossina) in sub-Saharan Africa.",
            "incubation_period": "Gambiense: months to years; Rhodesiense: 1 to 3 weeks (rapidly progressive)",
            "cardinal_symptoms": ["Chancre at bite site", "Posterior cervical lymphadenopathy (Winterbottom sign)", "Irregular undulating fever and pruritus", "Disrupted sleep architecture (daytime somnolence, nocturnal insomnia)", "Progressive tremors, ataxia, and mental deterioration"],
            "red_flags": ["Severe meningoencephalopathy with coma", "Melarsoprol-induced encephalopathic syndrome (10% incidence, 50% fatal)", "Acute cardiac failure in T. b. rhodesiense"],
            "pathophysiology": "Parasite undergoes variable surface glycoprotein (VSG) antigenic variation to evade humoral immunity; eventually crosses the blood-brain barrier into the central nervous system causing severe meningoencephalitis.",
            "clinical_pearl": "Winterbottom sign (painless, rubbery enlargement of posterior cervical lymph nodes) is a classic physical exam finding of early gambiense sleeping sickness."
        },
        "pearl": "Tsetse fly transmission. Winterbottom sign (cervical adenopathy), sleep-wake reversal, ataxia. LP mandatory for CNS staging. Oral Fexinidazole is first-line for gambiense."
    },

    "Brucellosis": {
        "icd10": "A23.9", "icd11": "1B90", "category": "Zoonotic Bacterial Infection", "triage": "URGENT",
        "immediate_tests": [
            "Serum Standard Tube Agglutination Test (SAT / Wright test — titer >=1:160)",
            "Brucella IgM/IgG ELISA",
            "Blood Cultures in BACTEC (alert lab: incubate for >=21 days due to slow growth)",
            "Complete Blood Count (leukopenia with relative lymphocytosis)",
            "Spine MRI / Pelvic Radiograph (evaluating brucellar spondylodiscitis or sacroiliitis)"
        ],
        "recommended_investigations": [
            "Standard Agglutination Test (SAT) with 2-mercaptoethanol (2-ME) to measure IgG",
            "Brucella PCR and automated blood/bone marrow culture (bone marrow culture has highest sensitivity ~90%)",
            "Liver Function Tests (mild transaminitis, granulomatous hepatitis)",
            "MRI of Lumbar Spine and Sacroiliac Joints (detects spondylodiscitis with epidural abscess)",
            "Echocardiogram (mandatory rule-out of Brucella aortic endocarditis in persistent fever)"
        ],
        "recommended_medications": [
            "Standard Regimen (Uncomplicated): Doxycycline 100 mg PO BID for 6 weeks PLUS Rifampin 600-900 mg PO daily for 6 weeks",
            "Alternative Superior Regimen: Doxycycline 100 mg PO BID for 6 weeks PLUS Gentamicin 5 mg/kg IV/IM daily for first 7-14 days",
            "Complicated (Spondylodiscitis / Neurobrucellosis / Endocarditis): Doxycycline 100 mg BID + Rifampin 600-900 mg daily + Ceftriaxone 2g IV daily (minimum 12 weeks duration)",
            "Pregnancy and Children <8 years: Cotrimoxazole (TMP-SMX) 160/800 mg BID + Rifampin 600 mg daily for 6 weeks"
        ],
        "first_line_treatment": "Oral Doxycycline 100mg BID for 6 weeks combined with either Rifampin for 6 weeks or Gentamicin for the first 14 days.",
        "treatment_summary": "Monotherapy is strictly contraindicated due to high relapse rates (>30%). Prolonged dual/triple antibiotic therapy is essential. Watch for spondylodiscitis and endocarditis.",
        "disease_intelligence": {
            "disease_name": "Brucellosis (Undulant / Malta Fever)",
            "etiology": "Brucella species (B. melitensis [goats/sheep - most virulent], B. abortus [cattle], B. suis [swine])",
            "icd10_code": "A23.9", "icd11_code": "1B90",
            "transmission": "Ingestion of unpasteurized milk, cheese, or dairy products; direct contact with infected animal tissues (veterinarians, abattoir workers); laboratory aerosolization.",
            "incubation_period": "1 to 4 weeks (can extend up to several months)",
            "cardinal_symptoms": ["Undulant fever (rising in evening, falling by morning)", "Profuse, foul-smelling, moldy-scented night sweats", "Severe arthralgias and lumbar back pain (sacroiliitis/spondylodiscitis)", "Hepatosplenomegaly and lymphadenopathy", "Chronic fatigue and depression"],
            "red_flags": ["Brucella endocarditis (leading cause of mortality — aortic valve vegetation requiring urgent surgery)", "Neurobrucellosis (meningoencephalitis, cranial neuropathies)", "Epidural or psoas abscess complicating spondylodiscitis"],
            "pathophysiology": "Facultative intracellular survival inside macrophages; inhibits phagosome-lysosome fusion, seeds reticuloendothelial organs (liver, spleen, bone marrow), forming non-caseating granulomas.",
            "clinical_pearl": "History of consuming unpasteurized goat cheese in the Mediterranean, Middle East, or Latin America combined with undulant fever and back pain is the classic presentation. High lab-acquired infection risk."
        },
        "pearl": "Unpasteurized dairy exposure. Undulant fever, foul sweats, sacroiliitis, spondylodiscitis. Never treat with monotherapy: Doxycycline + Rifampin or Gentamicin for >=6 weeks."
    },

    "Bubonic Plague": {
        "icd10": "A20.0", "icd11": "1B91.0", "category": "Zoonotic High-Consequence Bacterial Infection", "triage": "EMERGENT",
        "immediate_tests": [
            "Bubo Aspirate Microscopy with Gram and Wayson / Giemsa Staining (bipolar 'safety-pin' staining coccobacilli)",
            "Yersinia pestis F1 Antigen Rapid Diagnostic Test",
            "Yersinia pestis Blood Cultures x2 sets (notify lab for BSL-3 precautions)",
            "Complete Blood Count with differential (marked leukocytosis with prominent left shift)",
            "Coagulation Profile and D-Dimer (screening for purpuric disseminated intravascular coagulation)"
        ],
        "recommended_investigations": [
            "Bubo aspirate and blood culture on sheep blood agar and MacConkey",
            "Yersinia pestis PCR targeting caf1 and pla genes",
            "Serum F1 antibody titer testing (paired acute and convalescent serology)",
            "Chest X-Ray (PA view: mandatory screening for secondary pneumonic plague spread)",
            "Lumbar Puncture (if plague meningitis is suspected)"
        ],
        "recommended_medications": [
            "First-Line Aminoglycoside: Gentamicin 5 mg/kg IV daily (or 1.7 mg/kg IV q8h) for 10-14 days OR Streptomycin 1g IM q12h",
            "Alternative Antibiotics: Doxycycline 100 mg IV/PO BID for 10-14 days OR Ciprofloxacin 400 mg IV q12h (or 500-750 mg PO BID)",
            "Plague Meningitis: Chloramphenicol 25 mg/kg IV q6h (crosses blood-brain barrier)",
            "Post-Exposure Prophylaxis: Doxycycline 100 mg PO BID or Ciprofloxacin 500 mg PO BID for 7 days"
        ],
        "first_line_treatment": "Immediate IV Gentamicin or Streptomycin initiated upon suspicion without waiting for laboratory confirmation, combined with droplet isolation if pulmonary symptoms emerge.",
        "treatment_summary": "Highly virulent pathogen. Treatment within 24 hours of symptom onset reduces mortality from 60% to <10%. Droplet precautions if pneumonic spread suspected.",
        "disease_intelligence": {
            "disease_name": "Bubonic Plague",
            "etiology": "Yersinia pestis (Gram-negative, facultative intracellular coccobacillus / Enterobacteriaceae)",
            "icd10_code": "A20.0", "icd11_code": "1B91.0",
            "transmission": "Bite of infected rodent fleas (Xenopsylla cheopis); direct contact with tissues/fluids of infected animals (prairie dogs, ground squirrels in US Southwest; Madagascar).",
            "incubation_period": "2 to 8 days (mean 2 to 4 days)",
            "cardinal_symptoms": ["Sudden onset of high fever and prostrating rigors", "Extremely painful, tender, swollen lymph node ('bubo') typically in groin, axilla, or neck", "Erythema and warmth overlying the bubo without fluctuance", "Tachycardia and hypotension"],
            "red_flags": ["Septicemic plague with DIC ('Black Death' acral gangrene of fingers and nose)", "Secondary pneumonic plague (cough, hemoptysis — highly contagious via droplets)", "Plague meningitis"],
            "pathophysiology": "Injected by flea; engulfed by macrophages where it produces anti-phagocytic F1 capsular antigen and Yops (Yersinia outer proteins) injected via Type III secretion system, causing massive hemorrhagic necrosis of regional lymph nodes.",
            "clinical_pearl": "Bipolar 'safety-pin' staining on Wayson or Giemsa stain of bubo aspirate is virtually diagnostic. Do not incise and drain buboes (risk of bacteremia and aerosolization)."
        },
        "pearl": "Flea bite or rodent exposure in endemic areas (US Southwest, Madagascar). Extremely painful bubo + high fever. Bipolar 'safety-pin' staining. IV Gentamicin is lifesaving."
    },

    "Pneumonic Plague": {
        "icd10": "A20.2", "icd11": "1B91.2", "category": "Airborne High-Consequence Bacterial Infection", "triage": "EMERGENT",
        "immediate_tests": [
            "Sputum / Tracheal Aspirate Gram and Wayson Stain (bipolar 'safety pin' bacilli)",
            "Yersinia pestis Sputum and Blood PCR",
            "Blood Cultures x2 sets (BSL-3 notification)",
            "Chest Radiograph (rapidly expanding bilateral bronchopneumonic consolidation, cavities, pleural effusion)",
            "Arterial Blood Gas (severe hypoxemic respiratory failure)"
        ],
        "recommended_investigations": [
            "Sputum and blood culture for Y. pestis",
            "Yersinia pestis PCR and F1 antigen detection",
            "Serial CXR (assessing progression of alveolar consolidation)",
            "Coagulation panel (PT/INR, PTT, Fibrinogen, D-Dimer for severe DIC)"
        ],
        "recommended_medications": [
            "First-Line Bactericidal: Gentamicin 5 mg/kg IV daily (or 1.7 mg/kg q8h) for 10-14 days OR Streptomycin 1g IM q12h",
            "Alternative First-Line: Levofloxacin 750 mg IV daily OR Ciprofloxacin 400 mg IV q12h",
            "Severe Shock / Second Agent: Doxycycline 100 mg IV q12h combined with Gentamicin",
            "Close Contact Post-Exposure Prophylaxis: Doxycycline 100 mg PO BID or Ciprofloxacin 500 mg PO BID for 7 days"
        ],
        "first_line_treatment": "Immediate IV Gentamicin or Fluoroquinolone within 24 hours of symptom onset in strict airborne and droplet isolation.",
        "treatment_summary": "100% fatal without treatment within 24 hours. Primary pneumonic plague is aerosol-transmitted person-to-person. Universal PPE and prophylaxis of all close contacts.",
        "disease_intelligence": {
            "disease_name": "Pneumonic Plague (Primary / Secondary)",
            "etiology": "Yersinia pestis",
            "icd10_code": "A20.2", "icd11_code": "1B91.2",
            "transmission": "Inhalation of infectious respiratory droplets from human or animal (cats) with pneumonic plague; or hematogenous spread from bubonic plague.",
            "incubation_period": "1 to 3 days (exceptionally rapid)",
            "cardinal_symptoms": ["Sudden high fever and intense chills", "Severe dyspnea and tachypnea", "Chest pain and productive cough", "Watery sputum rapidly becoming blood-stained and bright red ('raspberry syrup' sputum)", "Cardiovascular collapse"],
            "red_flags": ["Refractory cyanosis and acute respiratory failure", "Diffuse pulmonary hemorrhage", "Septic shock with peripheral gangrene", "Coma within 24-48 hours"],
            "pathophysiology": "Rapid alveolar destruction, intra-alveolar hemorrhage, and massive bacterial proliferation without early neutrophil influx due to Type III secretion effector paralysis.",
            "clinical_pearl": "Pneumonic plague is the only form of plague that spreads person-to-person through the air. Any delay in initiating antimicrobial therapy beyond 24 hours from onset carries near-certain mortality."
        },
        "pearl": "Aerosol-spread, 100% fatal without treatment in 24 hours. 'Raspberry syrup' bloody sputum, rapid respiratory collapse. Immediate IV Gentamicin + strict droplet/airborne isolation."
    },

    "Acute HIV Infection (Primary)": {
        "icd10": "B20", "icd11": "1C62.0", "category": "Viral Retroviral Infection", "triage": "URGENT",
        "immediate_tests": [
            "HIV-1/2 Antigen/Antibody 4th Generation Immunoassay (detects p24 antigen and antibodies)",
            "HIV-1 Viral Load (Quantitative RNA PCR — essential because antibody tests may be negative in early eclipse/window phase)",
            "Complete Blood Count with differential (lymphopenia early, followed by atypical lymphocytosis)",
            "Comprehensive Metabolic Panel and Liver Function Tests (transaminitis)",
            "Baseline STI Screening: Syphilis RPR/VDRL, Hepatitis B surface antigen, Hepatitis C antibody, Gonorrhea/Chlamydia NAAT"
        ],
        "recommended_investigations": [
            "Plasma HIV-1 RNA Quantitative Real-Time PCR (typically >100,000 to >1,000,000 copies/mL)",
            "4th Generation HIV-1/2 Ag/Ab Combo Immunoassay",
            "CD4+ T-lymphocyte count and CD4/CD8 ratio (transient profound CD4 drop during peak viremia)",
            "Baseline HIV-1 Genotypic Antiretroviral Resistance Testing (Pol gene: reverse transcriptase, protease, integrase)",
            "HLA-B*5701 testing (if Abacavir-containing regimen considered)"
        ],
        "recommended_medications": [
            "Immediate Antiretroviral Therapy (ART — Same-Day Start): Bictegravir 50mg / Emtricitabine 200mg / Tenofovir Alafenamide 25mg (Biktarvy) 1 tablet PO daily with or without food",
            "Alternative First-Line ART: Dolutegravir 50mg PO daily PLUS Emtricitabine/Tenofovir Disoproxil Fumarate (or TAF) 1 tablet daily",
            "Protease Inhibitor Regimen (if integrase resistance suspected): Darunavir 800mg + Ritonavir 100mg (or Cobicistat 150mg) + FTC/TAF daily",
            "Partner Notification: Immediate evaluation of sexual contacts for Post-Exposure Prophylaxis (PEP) or Pre-Exposure Prophylaxis (PrEP)"
        ],
        "first_line_treatment": "Immediate 'Same-Day' initiation of triple-agent Antiretroviral Therapy (INSTI-based: Bictegravir/FTC/TAF or Dolutegravir + FTC/TAF) upon clinical and virological confirmation.",
        "treatment_summary": "Diagnosis requires viral load RNA testing because 4th generation antibody tests may be non-reactive in the first 10-14 days. Immediate ART limits viral reservoir seeding and preserves immune function.",
        "disease_intelligence": {
            "disease_name": "Acute HIV Infection (Primary Seroconversion Syndrome)",
            "etiology": "Human Immunodeficiency Virus type 1 (HIV-1 / Retroviridae)",
            "icd10_code": "B20", "icd11_code": "1C62.0",
            "transmission": "Unprotected sexual intercourse (receptive anal/vaginal), shared contaminated injection needles, vertical maternal-fetal transmission, contaminated blood transfusion.",
            "incubation_period": "10 days to 4 weeks (mean 2 to 3 weeks)",
            "cardinal_symptoms": ["Acute mononucleosis-like illness (fever, fatigue, pharyngitis)", "Generalized non-tender lymphadenopathy", "Erythematous maculopapular rash (face, trunk, and occasionally palms/soles)", "Painful mucocutaneous oral or genital ulcers", "Myalgias, arthralgias, and aseptic meningitis headache"],
            "red_flags": ["Severe opportunistic infections during transient CD4 nadir (Pneumocystis pneumonia, esophageal candidiasis)", "Acute neurological deficits (meningoencephalitis, Guillain-Barré-like neuropathy)", "Extreme viral transmission risk (viral load >10^6 copies/mL makes patient extremely contagious)"],
            "pathophysiology": "Rapid mucosal entry, infection of CD4+ CCR5+ memory T-cells in gut-associated lymphoid tissue (GALT), massive viremic burst, destruction of GALT memory pool, followed by CD8 cytotoxic immune response.",
            "clinical_pearl": "High fever, sore throat, and a non-pruritic maculopapular rash with painful shallow aphthous-like ulcers on the palate or genitals 2-4 weeks after unprotected sex is classical for acute HIV. An antibody-only rapid test will be FALSE-NEGATIVE; order HIV RNA viral load."
        },
        "pearl": "Mononucleosis-like syndrome with maculopapular rash and painful oral/genital ulcers. Antibody test may be negative; viral load RNA is massively positive. Start Biktarvy on day of diagnosis."
    },

    "Melioidosis (Burkholderia pseudomallei)": {
        "icd10": "A24.4", "icd11": "1B92", "category": "Tropical Bacterial / Environmental", "triage": "EMERGENT",
        "immediate_tests": [
            "Blood Cultures x2 sets (notify lab: alert for Burkholderia pseudomallei — potential lab hazard)",
            "Sputum / Pus / Abscess Aspirate Gram Stain and Culture (Gram-negative bacilli with safety-pin bipolar staining)",
            "Chest Radiograph (PA/Lateral: upper lobe cavitary infiltrates resembling tuberculosis)",
            "Abdominal Ultrasound / CT (detects pathognomonic 'honeycomb' splenic and hepatic micro-abscesses)",
            "Complete Blood Count and Metabolic Panel (diabetic ketoacidosis screening — diabetes is #1 risk factor)"
        ],
        "recommended_investigations": [
            "Culture of blood, sputum, urine, and abscess aspirates on selective Ashdown's medium",
            "Burkholderia pseudomallei specific PCR and Indirect Hemagglutination Assay (IHA)",
            "Contrast-Enhanced CT Abdomen and Pelvis (surveillance for multi-organ abscesses in spleen, liver, prostate)",
            "Prostate Ultrasound or MRI (prostatic abscesses are frequent in infected males in endemic zones)"
        ],
        "recommended_medications": [
            "Intensive Phase (Minimum 14 Days IV; 4-8 weeks if deep abscesses/neuromelioidosis): IV Ceftazidime 2g (50 mg/kg) q8h OR IV Meropenem 1g (25 mg/kg) q8h (preferred for septic shock)",
            "Adjunctive Folic Acid Antagonist: Add Trimethoprim-Sulfamethoxazole (TMP-SMX) 160/800 mg (or 240/1200 mg if >60kg) PO q12h + Folic acid 5mg daily",
            "Eradication Phase (3 to 6 Months Oral): Trimethoprim-Sulfamethoxazole 160/800 mg PO BID (prevents relapses)",
            "Alternative Eradication: Amoxicillin-Clavulanate (Augmentin) 875/125 mg PO TID (if TMP-SMX contraindicated/intolerant)"
        ],
        "first_line_treatment": "IV Ceftazidime 2g q8h (or Meropenem 1g q8h in septic shock) for at least 14 days, followed by oral TMP-SMX for 3 to 6 months to prevent relapse.",
        "treatment_summary": "'The Great Mimicker'. High mortality if treated with standard empiric CAP antibiotics. Requires dual-phase treatment (intravenous intensive phase followed by prolonged oral eradication).",
        "disease_intelligence": {
            "disease_name": "Melioidosis (Whitmore Disease)",
            "etiology": "Burkholderia pseudomallei (Gram-negative saprophytic environmental bacterium)",
            "icd10_code": "A24.4", "icd11_code": "1B92",
            "transmission": "Percutaneous inoculation through skin abrasions, inhalation of aerosolized dust/water during heavy storms/typhoons, or ingestion of contaminated soil or surface water (Southeast Asia, Northern Australia).",
            "incubation_period": "1 to 21 days (can remain latent for decades before activating during immunosuppression)",
            "cardinal_symptoms": ["Acute pneumonia with high fever and productive cough", "Disseminated multi-organ abscesses (spleen, liver, skin, prostate)", "Severe sepsis / septic shock with rapid deterioration", "Localized painful skin ulcer or suppurative parotitis (pediatric)"],
            "red_flags": ["Septic shock with multi-organ failure (>40% mortality)", "Neuromelioidosis (brainstem encephalitis, peripheral motor weakness)", "Multiple 'honeycomb' splenic abscesses requiring drainage"],
            "pathophysiology": "Intracellular pathogen capable of surviving inside phagocytic and non-phagocytic cells, inducing multinucleated giant cell formation, actin-based motility, and extensive pyogenic granuloma destruction.",
            "clinical_pearl": "Type 2 Diabetes Mellitus is the single biggest risk factor (present in >50% of patients). Splenic abscesses with a 'honeycomb' appearance on CT in a traveler from Thailand or Australia are virtually diagnostic."
        },
        "pearl": "Soil/water exposure in Southeast Asia or Northern Australia; strongly associated with diabetes. Multi-organ micro-abscesses ('honeycomb' spleen). IV Ceftazidime or Meropenem -> oral TMP-SMX for 3-6 months."
    },

    "Nipah Virus Disease": {
        "icd10": "A98.8", "icd11": "1D65", "category": "Zoonotic Henipavirus / BSL-4", "triage": "EMERGENT",
        "immediate_tests": [
            "Nipah Virus RT-PCR (Throat/nasal swabs, urine, blood, and CSF — BSL-4 containment)",
            "Lumbar Puncture with CSF Analysis (lymphocytic pleocytosis, elevated protein, normal glucose)",
            "Brain MRI (Multiple small discrete focal T2/FLAIR hyperintense subcortical white matter lesions)",
            "Chest Radiograph (acute respiratory distress syndrome / bilateral alveolar infiltrates)",
            "Complete Blood Count (thrombocytopenia, leukopenia)"
        ],
        "recommended_investigations": [
            "Nipah RT-PCR on multiple specimens (blood, CSF, throat swab, urine)",
            "Nipah IgM and IgG ELISA (positive after day 5-7)",
            "Brain MRI with and without gadolinium contrast (essential for detecting microvascular encephalitis lesions and brainstem involvement)",
            "Continuous EEG (monitoring subclinical seizure activity and periodic generalized complexes)"
        ],
        "recommended_medications": [
            "Supportive Critical Care: Intensive airway management, mechanical ventilation, and hemodynamic support",
            "Monoclonal Antibody (Compassionate Use): m102.4 human monoclonal antibody (broad-spectrum henipavirus neutralizing antibody)",
            "Experimental Antivirals: Remdesivir (demonstrated efficacy in non-human primate models) or oral Ribavirin",
            "Anticonvulsants: IV Levetiracetam or Fosphenytoin for acute seizures",
            "Strict Infection Control: Level 4 barrier nursing; high-efficiency respiratory protection (N95/PAPR)"
        ],
        "first_line_treatment": "Immediate high-containment isolation, aggressive airway protection and intensive neuro-critical care; experimental m102.4 monoclonal antibody if accessible.",
        "treatment_summary": "Extremely lethal zoonotic pathogen (40-75% CFR). Presentation combines acute encephalitic coma with severe respiratory distress. Human-to-human transmission via droplets and secretions is documented.",
        "disease_intelligence": {
            "disease_name": "Nipah Virus Encephalitis",
            "etiology": "Nipah virus (genus Henipavirus, family Paramyxoviridae)",
            "icd10_code": "A98.8", "icd11_code": "1D65",
            "transmission": "Consumption of raw date palm sap contaminated with fruit bat (Pteropus) saliva/urine; contact with infected pigs (Malaysia outbreak); person-to-person spread via droplets/secretions (Bangladesh, India).",
            "incubation_period": "4 to 14 days (can extend up to 45 days)",
            "cardinal_symptoms": ["Acute fever and headache progressing rapidly to dizziness and disorientation", "Rapidly deteriorating mental status into coma within 24-48 hours", "Severe brainstem signs: myoclonus, areflexia, doll's eye loss, autonomic instability", "Severe respiratory distress / atypical pneumonia"],
            "red_flags": ["Rapid coma within 24-48 hours of onset", "Segmental myoclonus (characteristic involuntary jerking)", "Hypotension and labile tachycardia", "Relapsing / late-onset encephalitis months after initial recovery"],
            "pathophysiology": "Endothelial cell infection via ephrin-B2 and ephrin-B3 receptors leads to widespread syncytia formation, systemic vasculitis, micro-infarctions, and extensive parenchymal brain and lung necrosis.",
            "clinical_pearl": "History of drinking raw date palm sap in Bangladesh or Kerala, India, followed by acute encephalitis with segmental myoclonus is classic. Late-onset or relapsing encephalitis can occur months to years after recovery."
        },
        "pearl": "Henipavirus from Pteropus fruit bats or raw date palm sap. High CFR (40-75%). Rapid encephalitic coma with segmental myoclonus and respiratory failure. Strict isolation and neuro-critical ICU care."
    },

    "Sepsis (Bacterial)": {
        "icd10": "A41.9", "icd11": "1G40", "category": "Systemic Critical Care / Infectious", "triage": "EMERGENT",
        "immediate_tests": [
            "Venous / Arterial Blood Gas with Stat Serum Lactate (lactate >2 mmol/L indicates tissue hypoperfusion)",
            "Blood Cultures x2 sets (aerobic and anaerobic from separate venipuncture sites PRIOR to antibiotics)",
            "Complete Blood Count with differential (leukocytosis >12,000 or leukopenia <4,000 or >10% immature bands)",
            "Comprehensive Metabolic Panel (Creatinine, BUN, Bilirubin, Electrolytes — calculates SOFA score)",
            "Coagulation Profile (PT/INR, aPTT, Platelets — evaluates sepsis-induced coagulopathy)",
            "Targeted Source Cultures: Urinalysis & culture, Sputum culture, Wound/fluid aspirates"
        ],
        "recommended_investigations": [
            "Serial Serum Lactate (repeat within 2-4 hours to monitor clearance >=20% reduction)",
            "Procalcitonin (PCT) and C-Reactive Protein (bacterial etiology and antibiotic de-escalation)",
            "Chest Radiograph or CT Imaging of suspected source (abdomen, pelvis, spine)",
            "Point-of-Care Echocardiography (POCUS: IVC collapsibility, cardiac contractility, fluid responsiveness)"
        ],
        "recommended_medications": [
            "Hour-1 Bundle Empiric Broad-Spectrum Antibiotics (Administer within 1 hour): IV Piperacillin-Tazobactam 4.5g q6h (or Cefepime 2g q8h) PLUS IV Vancomycin 25-30 mg/kg loading dose (for MRSA coverage)",
            "IV Fluid Resuscitation: 30 mL/kg of balanced crystalloids (Ringer's Lactate / Plasmalyte) within first 3 hours for hypotension (MAP <65) or lactate >=4 mmol/L",
            "First-Line Vasopressor (Septic Shock): Norepinephrine infusion titrated to target Mean Arterial Pressure (MAP) >=65 mmHg",
            "Second-Line Vasopressor: Add Vasopressin 0.03 units/min if MAP remains refractory to Norepinephrine",
            "Refractory Septic Shock: IV Hydrocortisone 200 mg/day (50mg IV q6h) if vasopressor requirements escalating"
        ],
        "first_line_treatment": "Surviving Sepsis Hour-1 Bundle: Measure lactate, obtain blood cultures, administer empiric broad-spectrum antibiotics within 60 minutes, and infuse 30 mL/kg balanced crystalloids for hypotension/hyperlactatemia.",
        "treatment_summary": "Life-threatening organ dysfunction caused by a dysregulated host response to infection (SOFA score increase >=2). Every 1-hour delay in antibiotics increases mortality by 7-8%.",
        "disease_intelligence": {
            "disease_name": "Sepsis & Septic Shock",
            "etiology": "Gram-negative bacteria (E. coli, Klebsiella, Pseudomonas), Gram-positive bacteria (S. aureus, S. pneumoniae, Enterococcus), or fungal/polymicrobial pathogens.",
            "icd10_code": "A41.9", "icd11_code": "1G40",
            "transmission": "Infection arising from pulmonary, urinary, intra-abdominal, soft tissue, or intravascular catheter sources.",
            "incubation_period": "Variable depending on primary source infection",
            "cardinal_symptoms": ["Fever (>38.3°C) or hypothermia (<36.0°C — carries worse prognosis)", "Tachycardia (HR >90 bpm) and Tachypnea (RR >20 bpm)", "Altered mental status / acute confusion", "Oliguria and delayed capillary refill (>3 seconds)", "Mottled skin and clammy extremities"],
            "red_flags": ["Septic Shock: Persistent hypotension requiring vasopressors to maintain MAP >=65 and lactate >2 mmol/L despite fluid resuscitation (40-50% mortality)", "Disseminated Intravascular Coagulation (DIC)", "Acute Respiratory Distress Syndrome (ARDS)"],
            "pathophysiology": "Systemic release of pathogen-associated molecular patterns (PAMPs) activates toll-like receptors, unleashing an uncontrolled storm of pro-inflammatory cytokines, endothelial glycocalyx disruption, capillary leak, widespread microvascular thrombosis, mitochondrial dysfunction, and multi-organ failure.",
            "clinical_pearl": "Hypothermia (<36°C) in sepsis indicates severe immunosuppression or exhausted metabolic reserve and carries a higher mortality than high fever. Target MAP >=65 mmHg with Norepinephrine."
        },
        "pearl": "Hour-1 bundle: Blood cultures x2, broad-spectrum IV antibiotics within 60 min, 30 mL/kg Ringer's Lactate, repeat lactate. First-line vasopressor is Norepinephrine (MAP target >=65)."
    },

    "Measles": {
        "icd10": "B05.9", "icd11": "1F03", "category": "Airborne Viral Exanthem", "triage": "URGENT",
        "immediate_tests": [
            "Measles Virus RT-PCR (Throat swab, nasopharyngeal swab, or urine)",
            "Measles Specific IgM Antibody Capture ELISA (positive from day 3 of rash)",
            "Oral Cavity Examination (detection of Koplik spots on buccal mucosa opposite molars)",
            "Complete Blood Count (leukopenia, lymphopenia, thrombocytopenia)",
            "Pulse Oximetry and Chest Radiograph (screens for giant cell pneumonitis or secondary bacterial pneumonia)"
        ],
        "recommended_investigations": [
            "Measles RT-PCR (most sensitive within first 3 days of rash)",
            "Serum Measles IgM and IgG (paired serology showing 4-fold IgG rise)",
            "Chest X-Ray (bilateral interstitial pneumonitis vs focal consolidation)",
            "Microbiology sputum culture if bacterial superinfection suspected"
        ],
        "recommended_medications": [
            "WHO-Mandated Vitamin A Therapy: Age >=12 months: 200,000 IU PO daily for 2 days; Age 6-11 months: 100,000 IU PO daily x2d; Age <6 months: 50,000 IU PO daily x2d (halves measles mortality and prevents blindness)",
            "Antipyresis and Hydration: Paracetamol 10-15 mg/kg q6h PRN (avoid Aspirin in children)",
            "Secondary Bacterial Antibiotics: Amoxicillin-Clavulanate or Ceftriaxone for secondary otitis media or pneumonia",
            "Post-Exposure Prophylaxis: MMR vaccine within 72 hours OR Intravenous/Intramuscular Immune Globulin (IG) within 6 days for high-risk contacts (infants, pregnant women, immunocompromised)"
        ],
        "first_line_treatment": "Immediate airborne isolation (negative pressure room), high-dose Vitamin A oral supplementation for 2 consecutive days, supportive hydration, and urgent public health notification.",
        "treatment_summary": "One of the most contagious human pathogens known (R0 12-18). Measles causes profound temporary immune amnesia lasting 2-3 years, predisposing to secondary fatal infections.",
        "disease_intelligence": {
            "disease_name": "Measles (Rubeola)",
            "etiology": "Measles morbillivirus (genus Morbillivirus, family Paramyxoviridae)",
            "icd10_code": "B05.9", "icd11_code": "1F03",
            "transmission": "Airborne aerosol transmission; virus remains suspended and infectious in ambient air for up to 2 hours after infected person leaves room.",
            "incubation_period": "10 to 14 days (rash typically appears on day 14)",
            "cardinal_symptoms": ["Classic 3 C's prodrome: Cough, Coryza (runny nose), and Conjunctivitis (with photophobia)", "High fever spiking to >40°C", "Koplik spots: tiny bluish-white spots with red halos on buccal mucosa (pathognomonic, day 2-3)", "Confluent erythematous maculopapular rash starting at hairline/behind ears and spreading downward (cephalocaudal)"],
            "red_flags": ["Severe pneumonia (Hecht giant cell pneumonia or bacterial superinfection — leading cause of death)", "Acute post-measles encephalitis (1 in 1,000 cases, day 2-7 post-rash)", "Subacute Sclerosing Panencephalitis (SSPE — fatal neurodegeneration 7-10 years later)"],
            "pathophysiology": "Infection of alveolar macrophages/dendritic cells via CD150 (SLAM) receptor, dissemination to regional lymph nodes, viremia, and massive infection of CD150+ lymphocytes leading to depletion of memory B and T cells ('immune amnesia').",
            "clinical_pearl": "Koplik spots ('grains of salt on a red velvet background') appear on the inner cheek 1-2 days before the skin rash and disappear as the rash blooms. Vitamin A administration is mandatory in all acute cases."
        },
        "pearl": "Classic 3 C's: Cough, Coryza, Conjunctivitis + Koplik spots. Descending maculopapular rash. Airborne isolation. High-dose oral Vitamin A x 2 days reduces mortality by 50%."
    },

    "Schistosomiasis (Katayama Fever)": {
        "icd10": "B65.9", "icd11": "1F80", "category": "Parasitic / Helminthic Infection", "triage": "URGENT",
        "immediate_tests": [
            "Complete Blood Count with differential (profound peripheral eosinophilia >1,500-3,000/mcL)",
            "Serum Schistosoma Antibody Serology (ELISA — IgG against soluble egg antigen or adult worm)",
            "Urine Filtration Microscopy (detection of Schistosoma haematobium eggs with terminal spine — collect at noon)",
            "Stool Microscopy via Kato-Katz technique (S. mansoni [lateral spine] and S. japonicum eggs)",
            "Liver Function Tests and Abdominal Ultrasound (periportal fibrosis, hepatosplenomegaly)"
        ],
        "recommended_investigations": [
            "Schistosoma Serology (ELISA / Western Blot — may take 6-12 weeks to seroconvert)",
            "Serial Stool Kato-Katz and Urine Microscopy (may be negative in early Katayama fever before egg deposition)",
            "Serum Eosinophil Count and Total IgE (dramatically elevated in acute toxemic Katayama syndrome)",
            "Abdominal Ultrasound (evaluates Symmers pipe-stem periportal fibrosis, splenomegaly, portal hypertension)",
            "Bladder Ultrasound or Cystoscopy (evaluates bladder wall thickening, calcifications, hydronephrosis in S. haematobium)"
        ],
        "recommended_medications": [
            "Acute Katayama Fever Phase: Prednisolone 0.5-1.0 mg/kg/day PO for 3-5 days (suppresses life-threatening immune complex allergic reaction) FOLLOWED BY Praziquantel after acute phase subsides",
            "Definitive Antihelminthic: Praziquantel 40 mg/kg PO in 2 divided doses (or 60 mg/kg in 3 divided doses for S. japonicum) with food",
            "Second Praziquantel Course: Repeat same dose 4 to 6 weeks later (Praziquantel only kills adult worms, not maturing schistosomula)",
            "Antihistamines: Cetirizine 10 mg PO daily for swimmer's itch cercarial dermatitis"
        ],
        "first_line_treatment": "Oral Praziquantel 40-60 mg/kg in divided doses with food, repeated 4-6 weeks later; co-administer corticosteroids in acute Katayama fever to prevent worsening immune-mediated reaction.",
        "treatment_summary": "Freshwater snail intermediate host. Katayama fever is an acute hypersensitivity reaction to migrating schistosomula. Chronic infection causes bladder cancer (S. haematobium) or portal hypertension (S. mansoni).",
        "disease_intelligence": {
            "disease_name": "Schistosomiasis (Bilharzia / Katayama Fever)",
            "etiology": "Schistosoma haematobium (urogenital), Schistosoma mansoni (intestinal/hepatic), Schistosoma japonicum",
            "icd10_code": "B65.9", "icd11_code": "1F80",
            "transmission": "Penetration of intact skin by free-swimming cercariae released by freshwater snails (Biomphalaria, Bulinus) during swimming, bathing, or wading in endemic fresh water (Lake Malawi, Nile River).",
            "incubation_period": "Cercarial dermatitis within 24h; Katayama fever 2 to 8 weeks; chronic disease years later",
            "cardinal_symptoms": ["Swimmer's itch (transient pruritic papular rash at water contact site)", "Katayama fever: acute high fever, rigors, dry cough, urticaria, hepatosplenomegaly, and extreme eosinophilia", "Terminal painless hematuria (S. haematobium)", "Bloody diarrhea and abdominal cramping (S. mansoni)"],
            "red_flags": ["Cor pulmonale / pulmonary hypertension from egg embolization", "Bleeding esophageal varices secondary to periportal (Symmers) hepatic fibrosis", "Squamous cell carcinoma of the bladder (chronic S. haematobium)"],
            "pathophysiology": "Cercariae penetrate skin, transform into schistosomula, migrate via lungs to portal/vesical venous plexus, mature into adult worm pairs. Deposited eggs secrete antigens, provoking intense granulomatous cell-mediated Th2 inflammation and extensive tissue fibrosis.",
            "clinical_pearl": "Praziquantel is ineffective against developing juvenile schistosomula; giving it during acute Katayama fever can trigger severe allergic exacerbations. Treat Katayama with steroids first, then Praziquantel, and repeat Praziquantel 4-6 weeks later."
        },
        "pearl": "Freshwater swimming history (e.g., Lake Malawi). High fever + massive eosinophilia + urticaria = Katayama fever. Praziquantel (repeat in 4-6 weeks) + steroids for acute phase."
    },

    # =========================================================================
    # 2. EMERGENCY CARDIOLOGY & CRITICAL CARE
    # =========================================================================
    "Acute Coronary Syndrome (STEMI)": {
        "icd10": "I21.3", "icd11": "BA41.0", "category": "Emergency Cardiology / Acute Ischemia", "triage": "EMERGENT",
        "immediate_tests": [
            "12-Lead Electrocardiogram (STAT within 10 minutes: ST elevation >=1mm in >=2 contiguous leads or new LBBB)",
            "High-Sensitivity Cardiac Troponin (hs-cTnI or hs-cTnT STAT at 0h and 1h/2h)",
            "Portable Chest X-Ray (rule out aortic dissection and evaluate pulmonary edema)",
            "Basic Metabolic Panel and Serum Potassium/Magnesium",
            "Complete Blood Count and Coagulation Profile (PT/INR, aPTT)"
        ],
        "recommended_investigations": [
            "Emergency Coronary Angiography (Gold Standard for culprit vessel identification and primary PCI)",
            "Serial High-Sensitivity Troponin I/T assays",
            "Echocardiogram (transthoracic: regional wall motion abnormalities, LVEF, mechanical complications)",
            "Lipid Panel (baseline LDL-C for statin titration)",
            "Continuous 12-lead telemetry monitoring (ventricular tachycardia / VF surveillance)"
        ],
        "recommended_medications": [
            "Immediate Dual Antiplatelet Therapy (DAPT): Aspirin 324 mg chewable PO STAT + Ticagrelor 180 mg PO loading dose (or Prasugrel 60 mg PO loading dose)",
            "Parenteral Anticoagulation: Unfractionated Heparin 60-70 units/kg IV bolus (max 4000-5000 units), then 12 units/kg/h (titrated to aPTT 50-70s)",
            "Sublingual Nitroglycerin: 0.4 mg SL q5min up to 3 doses (Hold if SBP <90, HR <50, or right ventricular infarction / PDE5 inhibitor use)",
            "High-Intensity Statin: Atorvastatin 80 mg PO daily (started immediately regardless of baseline LDL)",
            "Beta-Blocker: Metoprolol tartrate 25-50 mg PO q6-12h (start within 24h if hemodynamically stable without acute heart failure)"
        ],
        "first_line_treatment": "Immediate Primary Percutaneous Coronary Intervention (PCI) with door-to-balloon time <90 minutes; or IV Thrombolytic therapy (Tenecteplase) within 30 minutes if PCI transfer >120 minutes.",
        "treatment_summary": "Activate Cardiac Catheterization Lab immediately. Administer chewable Aspirin, P2Y12 inhibitor loading dose, Heparin anticoagulation, and high-intensity Atorvastatin.",
        "disease_intelligence": {
            "disease_name": "ST-Elevation Myocardial Infarction (STEMI)",
            "etiology": "Acute rupture or erosion of vulnerable atherosclerotic plaque triggering occlusive platelet-rich coronary thrombosis.",
            "icd10_code": "I21.3", "icd11_code": "BA41.0",
            "cardinal_symptoms": ["Crushing retrosternal chest pain/pressure lasting >20 minutes", "Radiation to left arm, neck, jaw, or shoulder", "Profound diaphoresis and nausea", "Dyspnea and sense of impending doom", "ST-segment elevations on 12-lead ECG"],
            "red_flags": ["Cardiogenic shock (hypotension SBP <90, oliguria, cold extremities)", "Ventricular fibrillation / pulseless VT (primary cause of pre-hospital death)", "Mechanical complications: acute mitral regurgitation (papillary muscle rupture), ventricular septal defect, free wall rupture"],
            "pathophysiology": "Complete acute occlusion of an epicardial coronary artery leads to transmural myocardial ischemia, progressive myocardial necrosis beginning from the subendocardium outward, and loss of contractility.",
            "clinical_pearl": "In inferior STEMI (leads II, III, aVF), always obtain right-sided ECG leads (V4R) to screen for Right Ventricular Infarction. Nitroglycerin and morphine are strictly contraindicated in RV infarction due to catastrophic preload reduction."
        },
        "pearl": "Door-to-balloon <90 min for primary PCI. Chewable Aspirin 324mg + Ticagrelor 180mg + Heparin + Atorvastatin 80mg. Strictly avoid Nitrates if right ventricular involvement or PDE5 inhibitor."
    },

    "Heart Failure (Acute Decompensated)": {
        "icd10": "I50.9", "icd11": "BD11", "category": "Emergency Cardiology / Hemodynamics", "triage": "EMERGENT",
        "immediate_tests": [
            "B-type Natriuretic Peptide (BNP >400 pg/mL or NT-proBNP >900-1800 pg/mL strongly supports ADHF)",
            "12-Lead Electrocardiogram (ischemia, arrhythmia, left ventricular hypertrophy)",
            "Portable Chest Radiograph (cardiomegaly, bilateral alveolar pulmonary edema, Kerley B lines, pleural effusions)",
            "Basic Metabolic Panel (Serum Creatinine, BUN, Sodium, Potassium)",
            "Point-of-Care Cardiac Ultrasound (POCUS: multiple lung B-lines, decreased ejection fraction, dilated non-collapsing IVC)"
        ],
        "recommended_investigations": [
            "Serum NT-proBNP / BNP (diagnostic and prognostic biomarker)",
            "Transthoracic Echocardiogram (evaluates LVEF, diastolic dysfunction, valve pathology, pulmonary pressures)",
            "High-Sensitivity Cardiac Troponin (excludes acute myocardial infarction as precipitant)",
            "Arterial / Venous Blood Gas (assessing respiratory acidosis or severe hypoxemia in pulmonary edema)",
            "Complete Blood Count and Thyroid Function Tests (TSH excludes high-output failure)"
        ],
        "recommended_medications": [
            "First-Line IV Loop Diuretic: IV Furosemide (Lasix) 40-80 mg IV bolus (or 1.0-2.5 times patient's home oral daily dose in IV mg)",
            "Vasodilator (in Hypertensive Acute Pulmonary Edema): IV Nitroglycerin infusion 10-20 mcg/min titrated rapidly up to 200 mcg/min (reduces preload and afterload)",
            "Non-Invasive Positive Pressure Ventilation (NIV): CPAP 5-10 cmH2O or BiPAP (rapidly unloads respiratory muscles and clears alveolar fluid)",
            "Guideline-Directed Medical Therapy (GDMT) Continuation: Maintain SGLT2 inhibitor (Dapagliflozin/Empagliflozin 10mg daily) and continue stable beta-blocker/ARNI unless cardiogenic shock",
            "Inotropes (ONLY in Cardiogenic Shock / Low-Output): IV Milrinone or Dobutamine infusion"
        ],
        "first_line_treatment": "IV Loop Diuretics (Furosemide) + IV Vasodilators (Nitroglycerin for hypertensive pulmonary edema) + CPAP/BiPAP respiratory support.",
        "treatment_summary": "Classify hemodynamic profile: 'Warm & Wet' (most common — diuretics + vasodilators), 'Cold & Wet' (inotropes + diuretics), 'Cold & Dry' (cautious volume). Avoid starting high-dose beta-blockers in acute decompensation.",
        "disease_intelligence": {
            "disease_name": "Acute Decompensated Heart Failure (ADHF)",
            "etiology": "Ischemic cardiomyopathy, uncontrolled hypertension, valvular disease, non-adherence, medication triggers (NSAIDs), or arrhythmias (atrial fibrillation).",
            "icd10_code": "I50.9", "icd11_code": "BD11",
            "cardinal_symptoms": ["Severe progressive dyspnea and orthopnea (requiring multiple pillows)", "Paroxysmal nocturnal dyspnea (PND)", "Bilateral lower extremity pitting edema and abdominal ascites", "Audible S3 gallop and jugular venous distention (JVD >8 cm)", "Bilateral basilar pulmonary crackles"],
            "red_flags": ["Flash Pulmonary Edema (rapid catastrophic alveolar flooding, severe hypoxemia)", "Cardiogenic Shock (hypotension, cold extremities, confusion, oliguria)", "Cardiorenal syndrome (rapidly worsening creatinine despite worsening fluid overload)"],
            "pathophysiology": "Elevated left ventricular end-diastolic pressure transmits backward into the pulmonary venous and capillary bed, overcoming oncotic pressure and causing fluid extravasation into lung interstitium and alveoli.",
            "clinical_pearl": "In severe hypertensive acute pulmonary edema, high-dose IV Nitroglycerin (50-200 mcg/min) plus BiPAP is more effective and acts faster than diuretics alone by aggressively reducing afterload and preload."
        },
        "pearl": "Orthopnea, JVD, S3 gallop, bilateral B-lines. IV Furosemide (1-2.5x home dose) + IV Nitroglycerin for hypertensive edema + BiPAP. Never start new beta-blockers during acute decompensation."
    },

    "Atrial Fibrillation (Rapid Ventricular Response)": {
        "icd10": "I48.0", "icd11": "BC81.3", "category": "Emergency Cardiology / Arrhythmia", "triage": "URGENT",
        "immediate_tests": [
            "12-Lead Electrocardiogram (irregularly irregular rhythm, absent P-waves, fibrillatory waves, ventricular rate >110-160 bpm)",
            "Continuous Cardiac Telemetry and Blood Pressure Monitoring",
            "Serum Electrolytes (Potassium >=4.0 mEq/L, Magnesium >=2.0 mg/dL target)",
            "High-Sensitivity Cardiac Troponin (evaluates myocardial demand ischemia)",
            "Point-of-Care Echocardiogram (evaluates left ventricular function and pericardial effusion)"
        ],
        "recommended_investigations": [
            "12-lead ECG (confirms rhythm and excludes pre-excitation / Wolff-Parkinson-White delta waves)",
            "Serum Electrolytes, BUN, and Creatinine (essential for antiarrhythmic and DOAC dosing)",
            "Thyroid-Stimulating Hormone (TSH: hyperthyroidism is a key reversible trigger)",
            "Transthoracic / Transesophageal Echocardiogram (TTE/TEE: rules out left atrial appendage thrombus prior to cardioversion)",
            "CHA2DS2-VASc and HAS-BLED stroke/bleeding risk score calculations"
        ],
        "recommended_medications": [
            "First-Line Rate Control (Beta-Blocker): IV Metoprolol 2.5-5 mg slow IV push q5min (up to 3 doses) OR IV Diltiazem 0.25 mg/kg (approx 15-20 mg) IV over 2 minutes",
            "Maintenance Infusion: Diltiazem IV infusion 5-15 mg/h (titrate to HR <100-110 bpm) or switch to oral Metoprolol succinate",
            "Rate Control in Reduced LVEF (HFrEF): IV Digoxin 0.25-0.5 mg IV or IV Amiodarone 150 mg over 10 min (avoid Diltiazem/Verapamil in HFrEF)",
            "Oral Anticoagulation (CHA2DS2-VASc >=2 in men, >=3 in women): Apixaban 5 mg PO BID (or Rivaroxaban 20 mg PO daily)",
            "Urgent Synchronized Cardioversion (Hemodynamically Unstable): Synchronized DC shock 120-200 J biphasic under procedural sedation"
        ],
        "first_line_treatment": "Immediate synchronized electrical cardioversion if hemodynamically unstable (hypotension, angina, pulmonary edema); IV Metoprolol or Diltiazem for rate control if stable.",
        "treatment_summary": "Assess stability first. If stable, target resting ventricular rate <110 bpm with IV beta-blocker or calcium channel blocker. Calculate CHA2DS2-VASc and initiate stroke prevention anticoagulation.",
        "disease_intelligence": {
            "disease_name": "Atrial Fibrillation with RVR",
            "etiology": "Hypertensive heart disease, coronary artery disease, valvular heart disease, alcohol binge ('holiday heart'), hyperthyroidism, pulmonary embolism, infection.",
            "icd10_code": "I48.0", "icd11_code": "BC81.3",
            "cardinal_symptoms": ["Rapid fluttering palpitations and pounding chest sensation", "Lightheadedness, presyncope, and dizziness", "Shortness of breath and fatigue on minimal exertion", "Irregularly irregular peripheral pulse on palpation"],
            "red_flags": ["Hemodynamic instability: SBP <90, altered mental status, acute pulmonary edema, ongoing myocardial ischemia (requires immediate electrical cardioversion)", "Wolff-Parkinson-White syndrome with AF (AV-nodal blockers contraindicated: can cause VF)"],
            "pathophysiology": "Multiple re-entrant wavelets and rapid focal firing (commonly from pulmonary vein sleeves) cause chaotic atrial depolarization (350-600 bpm); the AV node conducts variably, producing an irregularly irregular ventricular response.",
            "clinical_pearl": "Never administer Diltiazem, Verapamil, Beta-blockers, or Digoxin in pre-excited Atrial Fibrillation (WPW with wide irregular QRS). Blocking the AV node accelerates conduction down the accessory pathway into fatal Ventricular Fibrillation."
        },
        "pearl": "Irregularly irregular rhythm without P-waves. If unstable: Synchronized cardioversion 120-200J. If stable: IV Metoprolol or Diltiazem. Calculate CHA2DS2-VASc for Apixaban. Beware WPW."
    },

    "Cardiac Tamponade": {
        "icd10": "I31.9", "icd11": "BB21", "category": "Emergency Cardiology / Hemodynamics", "triage": "EMERGENT",
        "immediate_tests": [
            "Point-of-Care Ultrasound / Echocardiography (STAT: pericardial effusion with right ventricular diastolic collapse & IVC plethoric non-collapsing)",
            "Pulsus Paradoxus measurement (>10 mmHg systolic drop during normal inspiration)",
            "12-Lead Electrocardiogram (low QRS voltage, sinus tachycardia, electrical alternans)",
            "Portable Chest Radiograph ('water-bottle' enlarged globular cardiac silhouette)",
            "Basic Metabolic Panel, Troponin, and Coagulation Panel"
        ],
        "recommended_investigations": [
            "Transthoracic Echocardiogram (confirms RV diastolic collapse, late RA systolic collapse, exaggerated respiratory mitral/tricuspid inflow variation >25%)",
            "Diagnostic & Therapeutic Pericardiocentesis with fluid analysis (cell count, cytology, AFB, bacterial culture)",
            "CT Chest with contrast (identifies aortic dissection, malignant lymphadenopathy, hemopericardium)",
            "Autoimmune and Inflammatory markers (ANA, ESR, CRP)"
        ],
        "recommended_medications": [
            "Emergent Procedural: Subxiphoid Pericardiocentesis under ultrasound guidance (or surgical pericardial window)",
            "Intravascular Volume Expansion: IV Normal Saline 500-1000 mL bolus (temporizing bridge to increase intracardiac pressures while preparing pericardiocentesis)",
            "Vasopressors (if refractory): Norepinephrine infusion to maintain perfusion pressure",
            "Strict Contraindication: Avoid vasodilators and diuretics; avoid positive pressure mechanical ventilation if possible (drops venous return)"
        ],
        "first_line_treatment": "Emergency Ultrasound-Guided Pericardiocentesis or surgical pericardial window; temporary IV fluid bolus to augment preload.",
        "treatment_summary": "Life-threatening mechanical compression of the heart by pericardial fluid. Beck's triad (hypotension, JVD, muffled heart sounds). Do not give diuretics.",
        "disease_intelligence": {
            "disease_name": "Cardiac Tamponade",
            "etiology": "Malignancy (lung, breast, lymphoma), viral pericarditis, trauma, post-cardiac surgery / catheter perforation, uremia, aortic dissection type A.",
            "icd10_code": "I31.9", "icd11_code": "BB21",
            "cardinal_symptoms": ["Severe dyspnea, orthopnea, and tachypnea", "Beck's Triad: Hypotension, Jugular Venous Distension, Muffled Heart Sounds", "Pulsus paradoxus (>10-12 mmHg drop in SBP on inspiration)", "Electrical alternans and sinus tachycardia on ECG"],
            "red_flags": ["PEA (Pulseless Electrical Activity) cardiac arrest", "Hypotensive circulatory collapse", "Aortic dissection type A with hemopericardium (pericardiocentesis contraindicated: requires immediate emergency sternotomy)"],
            "pathophysiology": "Pericardial fluid under high pressure equalizes diastolic pressures across all cardiac chambers, preventing ventricular filling, dramatically reducing stroke volume, and causing cardiogenic shock.",
            "clinical_pearl": "Electrical alternans (beat-to-beat alternating QRS amplitude) on ECG reflects the heart swinging back and forth within a massive fluid-filled pericardial sac. It is pathognomonic for large pericardial effusion with tamponade."
        },
        "pearl": "Beck's Triad (hypotension, JVD, muffled sounds) + Pulsus paradoxus + electrical alternans. Bedside echo shows RV collapse. Emergent subxiphoid pericardiocentesis is lifesaving."
    },

    # =========================================================================
    # 3. EMERGENCY GASTROENTEROLOGY & SURGICAL ABDOMEN
    # =========================================================================
    "Acute Appendicitis": {
        "icd10": "K35.80", "icd11": "DB10", "category": "Emergency Surgery / Abdomen", "triage": "EMERGENT",
        "immediate_tests": [
            "Contrast-Enhanced CT Abdomen and Pelvis (Gold Standard in adults: dilated appendix >6mm, wall thickening, periappendiceal fat stranding, appendicolith)",
            "Abdominal Ultrasound (first-line in children and pregnant women: non-compressible blind-ended tubular structure >6mm)",
            "Complete Blood Count with differential (neutrophilic leukocytosis with left shift)",
            "Serum C-Reactive Protein (CRP)",
            "Serum Urine Pregnancy Test (hCG — mandatory in all reproductive-age females to exclude ectopic pregnancy)"
        ],
        "recommended_investigations": [
            "Abdominal CT with IV contrast (sensitivity/specificity >95%)",
            "Urinalysis (excludes nephrolithiasis and UTI; mild pyuria may occur from ureteral proximity)",
            "Basic Metabolic Panel and Coagulation Profile (pre-operative surgical clearance)",
            "Serial abdominal examinations and Alvarado / AIR score calculation"
        ],
        "recommended_medications": [
            "Pre-Operative IV Antibiotics: IV Ceftriaxone 2g daily PLUS IV Metronidazole 500mg q8h (OR single-agent IV Piperacillin-Tazobactam 3.375g q6h)",
            "Alternative in Penicillin Allergy: IV Ciprofloxacin 400mg q12h + IV Metronidazole 500mg q8h",
            "Multimodal Analgesia: IV Acetaminophen 1000mg q6h + IV Hydromorphone/Morphine titrated for acute pain (does NOT mask exam)",
            "IV Crystalloid Fluid Resuscitation: Normal Saline or Ringer's Lactate at 150-200 mL/h NPO"
        ],
        "first_line_treatment": "Urgent Laparoscopic Appendectomy combined with pre-operative broad-spectrum IV antibiotics (Ceftriaxone + Metronidazole).",
        "treatment_summary": "Keep patient strictly NPO, administer IV fluids, initiate IV antibiotics, and obtain immediate surgical consultation for appendectomy. Adequate analgesia does not obscure physical diagnosis.",
        "disease_intelligence": {
            "disease_name": "Acute Appendicitis",
            "etiology": "Luminal obstruction of the vermiform appendix by a fecalith (appendicolith), lymphoid hyperplasia, foreign body, or carcinoid tumor.",
            "icd10_code": "K35.80", "icd11_code": "DB10",
            "cardinal_symptoms": ["Periumbilical dull visceral pain migrating within 12-24 hours to sharp somatic Right Lower Quadrant pain (McBurney's point)", "Anorexia ('hamburger sign': refusal of favorite food)", "Nausea and low-grade fever after pain onset", "Peritoneal signs: localized guarding, rebound tenderness, Rovsing sign, Psoas sign, Obturator sign"],
            "red_flags": ["Appendiceal Perforation: Sudden temporary pain relief followed by diffuse peritonitis, high-grade fever (>38.5°C), and septic shock", "Appendiceal abscess / phlegmon (palpable RLQ mass)", "Pylephlebitis (infectious suppurative portal vein thrombosis)"],
            "pathophysiology": "Obstruction traps mucosal secretions, ballooning intraluminal pressure, compromising venous then arterial blood flow, causing transmural ischemia, bacterial invasion by enteric flora, gangrene, and perforation.",
            "clinical_pearl": "Chronology is critical: pain almost always precedes nausea and vomiting. If vomiting occurs before pain, reconsider appendicitis (gastroenteritis or bowel obstruction is more likely)."
        },
        "pearl": "Periumbilical pain migrating to McBurney's point, anorexia, guarding. CT with contrast confirms. Pre-op IV Ceftriaxone + Metronidazole -> Laparoscopic Appendectomy."
    },

    "Acute Pancreatitis": {
        "icd10": "K85.90", "icd11": "DC31", "category": "Gastroenterology / Emergency Medicine", "triage": "URGENT",
        "immediate_tests": [
            "Serum Lipase (diagnostic hallmark: elevated >=3 times upper limit of normal)",
            "Serum Amylase (elevated, but less sensitive and specific than lipase)",
            "Abdominal Ultrasound (STAT: screens for gallstones, common bile duct dilation, and choledocholithiasis)",
            "Comprehensive Metabolic Panel (Calcium, BUN, Creatinine, Liver Function Tests, AST/ALT >150 suggests gallstone etiology)",
            "Triglyceride Level (hypertriglyceridemia >1000 mg/dL as etiology)"
        ],
        "recommended_investigations": [
            "Contrast-Enhanced CT Abdomen (indicated at 48-72 hours if necrosis, severe pancreatitis, or clinical deterioration suspected; early CT can underestimate necrosis)",
            "Serial Hematocrit and BUN (BUN elevation >20 mg/dL and rising hematocrit reflect inadequate fluid resuscitation and predict mortality)",
            "BISAP score calculation (BUN >25, Impaired mental status, SIRS, Age >60, Pleural effusion)",
            "MRCP / ERCP (MRCP for non-invasive biliary duct imaging; urgent ERCP within 24h if acute cholangitis or persistent biliary obstruction present)"
        ],
        "recommended_medications": [
            "Goal-Directed IV Fluid Resuscitation: IV Ringer's Lactate 200-250 mL/h (or 20 mL/kg bolus then 3 mL/kg/h) adjusted to urine output >=0.5 mL/kg/h and falling BUN/Hct",
            "Multimodal Analgesia: IV Hydromorphone 0.5-1 mg q3h PRN or IV Fentanyl (effective control of severe visceral pain)",
            "Early Enteral Nutrition: Low-fat oral diet or oral fluids as soon as tolerated (reduces gut barrier translocation and infections compared to TPN/NPO)",
            "Prophylactic Antibiotics: NOT recommended in uncomplicated or sterile acute pancreatitis (only if infected pancreatic necrosis confirmed)"
        ],
        "first_line_treatment": "Aggressive, early goal-directed IV fluid resuscitation with Ringer's Lactate, multimodal analgesia, and early oral re-feeding as tolerated.",
        "treatment_summary": "Diagnosis requires 2 of 3: epigastric abdominal pain, lipase >=3x ULN, characteristic CT/MRI/ultrasound findings. Ringer's Lactate is superior to Normal Saline.",
        "disease_intelligence": {
            "disease_name": "Acute Pancreatitis",
            "etiology": "Gallstones (40-50%), Alcohol abuse (30-35%), Hypertriglyceridemia (>1000 mg/dL), Medications (Azathioprine, Didanosine), ERCP, Hypercalcemia, Trauma.",
            "icd10_code": "K85.90", "icd11_code": "DC31",
            "cardinal_symptoms": ["Severe, constant, boring epigastric pain radiating directly to the back", "Pain partially relieved by leaning forward / sitting in fetal position", "Persistent nausea and vomiting without pain relief", "Epigastric tenderness and abdominal distension with hypoactive bowel sounds"],
            "red_flags": ["Necrotizing pancreatitis with infected necrosis (fever, sepsis day 7-14)", "Cullen's sign (periumbilical ecchymosis) or Grey Turner's sign (flank ecchymosis) indicating retroperitoneal hemorrhage", "Organ failure >48 hours (Persistent shock, AKI, ARDS = Severe Pancreatitis)"],
            "pathophysiology": "Premature intracellular activation of trypsinogen within pancreatic acinar cells causes auto-digestion of pancreatic parenchyma, recruitment of neutrophils, microvascular thrombosis, and systemic release of inflammatory mediators.",
            "clinical_pearl": "Serum ALT >150 IU/L in the setting of acute pancreatitis has a >95% positive predictive value for a gallstone etiology, mandating urgent biliary ultrasound."
        },
        "pearl": "Boring epigastric pain radiating to back, lipase >=3x ULN. Goal-directed Ringer's Lactate IV + analgesia. Early oral feeding. Prophylactic antibiotics NOT indicated for sterile pancreatitis."
    },

    "Acute Ascending Cholangitis": {
        "icd10": "K83.09", "icd11": "DC11.0", "category": "Emergency Hepatobiliary / Sepsis", "triage": "EMERGENT",
        "immediate_tests": [
            "Right Upper Quadrant Abdominal Ultrasound (dilated common bile duct >6-8mm, choledocholithiasis)",
            "Complete Blood Count with differential (marked leukocytosis with prominent toxic granulation)",
            "Liver Function Tests (cholestatic pattern: marked Total/Direct Bilirubin and Alkaline Phosphatase elevation)",
            "Blood Cultures x2 sets (aerobic and anaerobic STAT prior to antibiotics)",
            "Serum Lactate and Renal Panel (assessing septic shock and acute renal dysfunction)"
        ],
        "recommended_investigations": [
            "Emergency Endoscopic Retrograde Cholangiopancreatography (ERCP — diagnostic and definitive therapeutic biliary decompression)",
            "Abdominal CT with IV contrast or MRCP (identifies level and etiology of biliary obstruction)",
            "Coagulation Profile (PT/INR, PTT — prolonged due to vitamin K malabsorption and sepsis)",
            "Serial Serum Bilirubin and Inflammatory Markers"
        ],
        "recommended_medications": [
            "Immediate Broad-Spectrum IV Antibiotics: IV Piperacillin-Tazobactam 4.5g q6h (or IV Ceftriaxone 2g daily PLUS IV Metronidazole 500mg q8h)",
            "Alternative in Severe Beta-Lactam Allergy: IV Ciprofloxacin 400mg q12h + IV Metronidazole 500mg q8h (or Meropenem 1g q8h)",
            "IV Fluid Resuscitation: Balanced crystalloids (Ringer's Lactate) titrated to urine output and blood pressure",
            "Emergency Biliary Decompression: Emergent ERCP with biliary sphincterotomy and stent placement (or percutaneous transhepatic drainage)"
        ],
        "first_line_treatment": "Immediate broad-spectrum parenteral antibiotics (Piperacillin-Tazobactam) + Emergency Biliary Decompression via ERCP within 12-24 hours.",
        "treatment_summary": "Surgical/endoscopic emergency. Charcot's triad (fever, RUQ pain, jaundice) or Reynolds' pentad (+ hypotension, confusion = 50% mortality without urgent drainage).",
        "disease_intelligence": {
            "disease_name": "Acute Ascending Cholangitis",
            "etiology": "Biliary tract outflow obstruction (choledocholithiasis 70%, biliary stricture, cholangiocarcinoma, stent occlusion) with superimposed ascending bacterial infection (E. coli, Klebsiella, Enterobacter, Enterococcus).",
            "icd10_code": "K83.09", "icd11_code": "DC11.0",
            "cardinal_symptoms": ["Charcot's Triad: High fever with chills/rigors, Right upper quadrant abdominal pain, and Jaundice", "Reynolds' Pentad: Charcot's triad PLUS Hypotension (shock) and Altered mental status / lethargy", "Dark tea-colored urine and pale acholic stools", "RUQ guarding and hepatomegaly"],
            "red_flags": ["Reynolds' Pentad (presence indicates suppurative toxic cholangitis with >50% mortality without emergent drainage)", "Septic shock requiring vasopressor support", "Acute renal failure and coagulopathy"],
            "pathophysiology": "Complete or partial obstruction raises intrabiliary pressure above 20 cmH2O; tight junctions between hepatocytes and biliary canaliculi disrupt, allowing bacteria to translocate into hepatic circulation causing bacteremia and overwhelming septic shock.",
            "clinical_pearl": "Antibiotics alone will NOT cure suppurative acute cholangitis without physical decompression of the obstructed biliary tree. ERCP biliary drainage is definitive."
        },
        "pearl": "Charcot's triad (Fever, RUQ pain, Jaundice) or Reynolds' pentad (+ Shock, Confusion). Emergency IV Piperacillin-Tazobactam + urgent ERCP biliary decompression."
    },

    "Bowel Obstruction": {
        "icd10": "K56.60", "icd11": "DC50", "category": "Emergency Surgery / Abdomen", "triage": "EMERGENT",
        "immediate_tests": [
            "CT Abdomen and Pelvis with IV and Oral Contrast (dilated bowel loops >3cm SBO, transition point, air-fluid levels, closed-loop obstruction)",
            "Acute Abdominal Series Radiographs (dilated small bowel loops, string-of-pearls sign, lack of colonic gas)",
            "Serum Lactate and Arterial Blood Gas (elevated lactate warns of bowel strangulation / ischemia)",
            "Complete Blood Count (leukocytosis suggests strangulation or perforation)",
            "Basic Metabolic Panel (hypochloremic hypokalemic metabolic alkalosis from proximal vomiting)"
        ],
        "recommended_investigations": [
            "Contrast-Enhanced CT Abdomen/Pelvis (identifies transition point, closed-loop 'whirl sign', mesenteric edema, ischemia)",
            "Serial abdominal examinations every 2-4 hours",
            "Serum Electrolytes, BUN, and Creatinine (monitoring prerenal dehydration)",
            "Water-soluble contrast (Gastrografin) challenge (both diagnostic and therapeutic in adhesive SBO)"
        ],
        "recommended_medications": [
            "Gastrointestinal Decompression: Nasogastric (NG) tube to continuous low-intermittent suction (relieves vomiting and aspirates fluid/air)",
            "Aggressive IV Fluid Replacement: IV Ringer's Lactate or Normal Saline 150-250 mL/h (replaces massive third-space and nasogastric losses)",
            "Electrolyte Correction: IV Potassium Chloride replacement (hypokalemia worsens paralytic ileus)",
            "Antiemetics: IV Ondansetron 4-8mg q8h PRN",
            "Broad-Spectrum Antibiotics (if strangulation/perforation suspected): IV Ceftriaxone 2g + IV Metronidazole 500mg"
        ],
        "first_line_treatment": "Nasogastric tube decompression, aggressive IV fluid resuscitation, bowel rest (NPO), and emergent surgical laparotomy if strangulation, closed-loop, or peritonitis present.",
        "treatment_summary": "Adhesions from prior surgery are #1 cause of SBO; neoplasms are #1 cause of LBO. Monitor for strangulation (fever, tachycardia, localized peritonitis, elevated lactate).",
        "disease_intelligence": {
            "disease_name": "Small / Large Bowel Obstruction (SBO / LBO)",
            "etiology": "Post-surgical intra-abdominal adhesions (60-70% SBO), incarcerated hernias, colorectal malignancy, volvulus (sigmoid/cecal), strictures.",
            "icd10_code": "K56.60", "icd11_code": "DC50",
            "cardinal_symptoms": ["Colicky crampy abdominal pain coming in paroxysms", "Profuse bilious or feculent vomiting", "Marked abdominal distension", "Absolute obstipation (failure to pass both flatus and feces)", "Hyperactive high-pitched 'tinkling' rushes early, becoming absent later"],
            "red_flags": ["Strangulated Obstruction: Continuous unremitting pain out of proportion, localized peritonitis, tachycardia, fever, elevated lactate", "Closed-Loop Obstruction (cecal/sigmoid volvulus — rapid gangrene risk)", "Free air on imaging (pneumoperitoneum indicating bowel perforation)"],
            "pathophysiology": "Proximal accumulation of fluid, gas, and swallowed air leads to bowel wall distension, intramural venous congestion, third-space fluid sequestration, hypovolemia, arterial compromise, transmural necrosis, and bacterial translocation.",
            "clinical_pearl": "Sudden progression from intermittent colicky pain to constant severe pain, accompanied by tachycardia and localized guarding, heralds bowel strangulation and demands immediate surgical intervention."
        },
        "pearl": "Colicky pain, bilious vomiting, distension, obstipation. CT shows transition point. NG tube decompression + IV fluids. Constant pain and elevated lactate indicate strangulation -> emergent surgery."
    },

    # =========================================================================
    # 4. EMERGENCY ENDOCRINOLOGY & METABOLIC
    # =========================================================================
    "Diabetic Ketoacidosis (DKA)": {
        "icd10": "E10.10", "icd11": "5A10.0", "category": "Emergency Endocrinology / Metabolic", "triage": "EMERGENT",
        "immediate_tests": [
            "Point-of-Care Blood Glucose (typically >250 mg/dL to 600 mg/dL)",
            "Serum or Point-of-Care Beta-Hydroxybutyrate (BHB >3.0 mmol/L confirms ketoacidosis)",
            "Arterial or Venous Blood Gas (pH <7.30, Bicarbonate <18 mEq/L, calculates anion gap)",
            "Basic Metabolic Panel (Serum Potassium, Sodium, Chloride, Bicarbonate, BUN, Creatinine)",
            "Urinalysis (4+ glucosuria, 3-4+ ketonuria)"
        ],
        "recommended_investigations": [
            "Anion Gap Calculation (Na - [Cl + HCO3] >12-16 mEq/L: high anion gap metabolic acidosis)",
            "Serial Serum Potassium and Venous Blood Gas every 1-2 hours",
            "Corrected Sodium Calculation: Measured Na + 1.6 * ([Glucose - 100] / 100)",
            "12-Lead Electrocardiogram (surveillance for peaked T waves of hyperkalemia or U waves of hypokalemia)",
            "Precipitant Workup: Chest X-ray, Blood/Urine cultures, Troponin (infection and MI are leading triggers)"
        ],
        "recommended_medications": [
            "First-Line Fluid Resuscitation: IV Normal Saline (0.9% NaCl) 1000-1500 mL/h during first hour (15-20 mL/kg/h); switch to 0.45% NaCl once corrected sodium normal/high",
            "IV Potassium Replacement: Add 20-30 mEq KCl per liter of IV fluid once K+ <5.2 mEq/L (HOLD insulin if K+ <3.3 mEq/L until potassium corrected)",
            "Continuous IV Regular Insulin: 0.1 units/kg IV bolus followed by 0.1 units/kg/h continuous infusion (target glucose drop 50-75 mg/dL/h)",
            "Dextrose Addition: Add 5% Dextrose to IV fluids (D5W 0.45% NaCl) once blood glucose drops <200 mg/dL while continuing insulin to clear ketoacidosis",
            "Bicarbonate (Restricted): ONLY indicated if arterial pH <6.9 (100 mmol Sodium Bicarbonate in sterile water over 2 hours)"
        ],
        "first_line_treatment": "Aggressive IV Normal Saline resuscitation + IV Potassium replacement once K+ <5.2 + continuous regular insulin infusion at 0.1 units/kg/h; add Dextrose when glucose <200 mg/dL.",
        "treatment_summary": "Resolve the ketoacidosis, not just hyperglycemia. Never stop insulin until anion gap is closed and bicarbonate is >=18 mEq/L. Always verify potassium before initiating insulin.",
        "disease_intelligence": {
            "disease_name": "Diabetic Ketoacidosis (DKA)",
            "etiology": "Absolute or severe relative insulin deficiency combined with counter-regulatory hormone excess (glucagon, catecholamines, cortisol, GH); triggered by infection, non-adherence, new-onset T1D, acute MI, or SGLT2 inhibitors (euglycemic DKA).",
            "icd10_code": "E10.10", "icd11_code": "5A10.0",
            "cardinal_symptoms": ["Polyuria, polydipsia, and rapid weight loss", "Nausea, intractable vomiting, and diffuse abdominal pain", "Kussmaul breathing (rapid, deep respirations blowing off CO2)", "Fruity / acetone breath odor", "Signs of severe dehydration (hypotension, tachycardia, dry mucous membranes)"],
            "red_flags": ["Severe Hypokalemia (K+ <3.3 mEq/L: insulin drives K+ intracellularly, causing fatal cardiac arrest if not pre-treated with potassium)", "Cerebral Edema (headache, bradycardia, lethargy — major pediatric mortality risk, avoid rapid osmolality drops)", "Severe refractory acidosis (pH <6.9)"],
            "pathophysiology": "Insulin deficiency prevents cellular glucose uptake and disinhibits hormone-sensitive lipase in adipose tissue; massive free fatty acid flux to the liver undergoes beta-oxidation into ketone bodies (acetoacetate and beta-hydroxybutyrate), creating severe high anion gap metabolic acidosis and osmotic diuresis.",
            "clinical_pearl": "Never administer insulin if serum potassium is <3.3 mEq/L. Giving insulin in severe hypokalemia drives potassium into cells, triggering fatal cardiac arrhythmias or respiratory arrest. Resuscitate potassium first."
        },
        "pearl": "High anion gap acidosis (pH <7.3, HCO3 <18) + ketones + glucose >250. Normal Saline 1L/h + check K+. If K+ <3.3, give potassium BEFORE insulin. Add Dextrose when glucose <200."
    },

    "Adrenal Insufficiency (Addisonian Crisis)": {
        "icd10": "E27.2", "icd11": "5A71", "category": "Emergency Endocrinology / Shock", "triage": "EMERGENT",
        "immediate_tests": [
            "Stat Serum Cortisol and ACTH (draw blood immediately, but DO NOT delay treatment for results)",
            "Comprehensive Metabolic Panel (hallmark: severe Hyponatremia + Hyperkalemia + Hypoglycemia)",
            "Point-of-Care Blood Glucose (treat acute hypoglycemia immediately with IV dextrose)",
            "Basic Metabolic Panel with BUN and Creatinine (prerenal azotemia)",
            "12-Lead Electrocardiogram (tall peaked T waves, prolonged PR of hyperkalemia)"
        ],
        "recommended_investigations": [
            "Baseline serum Cortisol (<5 mcg/dL strongly supports adrenal crisis; >18 mcg/dL excludes)",
            "Plasma ACTH (markedly elevated in primary adrenal insufficiency; low/normal in secondary)",
            "Cosyntropin (ACTH) Stimulation Test (perform after patient is stabilized on Dexamethasone if diagnosis unconfirmed)",
            "Anti-21-Hydroxylase Antibodies (confirms autoimmune Addison disease)",
            "CT Adrenal Glands (evaluates adrenal hemorrhage, calcifications from TB, or metastases)"
        ],
        "recommended_medications": [
            "Immediate Glucocorticoid: IV Hydrocortisone 100 mg IV STAT bolus, followed by 50-100 mg IV q6h (or continuous infusion 200 mg/24h)",
            "Alternative if ACTH test planned: IV Dexamethasone 4 mg IV bolus (does not cross-react with cortisol immunoassay)",
            "Aggressive Volume Resuscitation: IV Normal Saline (0.9% NaCl) with 5% Dextrose (D5NS) 1000 mL bolus, then 200-300 mL/h (corrects hyponatremia and hypoglycemia)",
            "Mineralocorticoid (Maintenance phase): Fludrocortisone 0.1 mg PO daily (NOT needed acutely because high-dose Hydrocortisone provides saturated mineralocorticoid activity)"
        ],
        "first_line_treatment": "Immediate IV Hydrocortisone 100mg bolus + rapid IV 0.9% Normal Saline with 5% Dextrose (D5NS) resuscitation. Never delay steroid administration for laboratory confirmation.",
        "treatment_summary": "Vasopressor-resistant shock in a patient with hyponatremia and hyperkalemia. Sudden withdrawal of chronic steroids or severe stress in known Addison's patient.",
        "disease_intelligence": {
            "disease_name": "Acute Adrenal Crisis (Addisonian Crisis)",
            "etiology": "Acute decompensation of primary adrenal insufficiency (Addison's) or sudden cessation of chronic exogenous glucocorticoids, triggered by major infection, trauma, surgery, or bilateral adrenal hemorrhage (Waterhouse-Friderichsen).",
            "icd10_code": "E27.2", "icd11_code": "5A71",
            "cardinal_symptoms": ["Refractory hypotensive shock unresponsive to IV fluids and vasopressors", "Severe nausea, persistent vomiting, and acute abdominal pain mimicking surgical abdomen", "Profound weakness, fatigue, and lethargy progressing to delirium", "Hyperpigmentation of palmar creases, buccal mucosa, and surgical scars (primary Addison's)", "Hypoglycemia"],
            "red_flags": ["Vasopressor-refractory distributive/hypovolemic shock", "Severe hyperkalemic cardiac dysrhythmias", "Coma from neuroglycopenia"],
            "pathophysiology": "Complete lack of cortisol causes loss of vascular smooth muscle tone and adrenergic receptor down-regulation; lack of aldosterone causes renal sodium wasting, potassium retention, hypovolemia, and circulatory collapse.",
            "clinical_pearl": "Unexplained shock refractory to fluids and Norepinephrine, especially in a patient with hyponatremia (low Na) and hyperkalemia (high K), is an adrenal crisis until proven otherwise. Administer 100mg IV Hydrocortisone immediately."
        },
        "pearl": "Refractory shock + low Na + high K + hypoglycemia. Immediate IV Hydrocortisone 100mg + IV D5 Normal Saline. Never delay steroids for diagnostic cortisol results."
    },

    # =========================================================================
    # 5. EMERGENCY NEUROLOGY
    # =========================================================================
    "Ischemic Stroke": {
        "icd10": "I63.9", "icd11": "8B11", "category": "Emergency Neurology / Vascular", "triage": "EMERGENT",
        "immediate_tests": [
            "Non-Contrast CT Head (STAT within 20 minutes of arrival: excludes intracranial hemorrhage and evaluates early ischemic changes / ASPECTS score)",
            "Point-of-Care Blood Glucose (STAT: rule out hypoglycemia as stroke mimic)",
            "CT Angiography (CTA) Head and Neck (STAT: detects Large Vessel Occlusion [LVO] in ICA, MCA M1/M2, basilar artery eligible for thrombectomy)",
            "CT Perfusion (CTP) / MRI Diffusion-Weighted Imaging (evaluates ischemic core vs salvageable penumbra)",
            "Complete Blood Count with Platelets and Coagulation Profile (PT/INR, aPTT)"
        ],
        "recommended_investigations": [
            "NIH Stroke Scale (NIHSS) score calculation",
            "Continuous telemetry monitoring (detection of paroxysmal atrial fibrillation)",
            "Transthoracic Echocardiogram with bubble study (patent foramen ovale and left atrial clot)",
            "Carotid Duplex Ultrasound (evaluates carotid artery stenosis >=70%)",
            "Lipid Panel (fasting LDL) and Hemoglobin A1c"
        ],
        "recommended_medications": [
            "Intravenous Thrombolysis (Onset <4.5 hours and no contraindications): IV Tenecteplase 0.25 mg/kg single bolus (max 25 mg) OR IV Alteplase (tPA) 0.9 mg/kg (max 90 mg; 10% bolus, 90% over 60 min)",
            "Mechanical Thrombectomy (LVO in anterior circulation up to 24 hours based on mismatch imaging): Endovascular stent-retriever/aspiration",
            "Blood Pressure Management: If eligible for tPA/TNK, lower BP to SBP <185 and DBP <110 using IV Labetalol 10-20mg or IV Nicardipine infusion; if not eligible, allow permissive hypertension up to 220/120 mmHg",
            "Antiplatelet Therapy: Aspirin 160-325 mg PO started at 24-48 hours post-thrombolysis (or immediately if tPA not given); add Clopidogrel 75mg for 21 days in minor stroke (NIHSS <=3)",
            "High-Intensity Statin: Atorvastatin 80 mg PO daily started prior to discharge"
        ],
        "first_line_treatment": "IV Tenecteplase/Alteplase within 4.5 hours of last known normal + Endovascular Mechanical Thrombectomy for Large Vessel Occlusion up to 24 hours.",
        "treatment_summary": "'Time is Brain' (1.9 million neurons lost per minute). Non-contrast head CT immediately. Target door-to-needle time <45-60 minutes.",
        "disease_intelligence": {
            "disease_name": "Acute Ischemic Stroke",
            "etiology": "Large artery atherosclerosis (carotid/vertebral stenosis), cardioembolism (atrial fibrillation 30%), small vessel lacunar occlusion, or cryptogenic / arterial dissection.",
            "icd10_code": "I63.9", "icd11_code": "8B11",
            "cardinal_symptoms": ["Sudden unilateral facial droop", "Sudden unilateral arm or leg weakness / hemiparesis", "Sudden expressive or receptive aphasia / dysarthria", "Sudden visual field defect / gaze deviation toward lesion side", "Sudden ataxia, vertigo, and loss of balance"],
            "red_flags": ["Hemorrhagic transformation of ischemic infarct (sudden neurological deterioration, rising BP, headache)", "Malignant MCA syndrome (massive hemispheric edema with midline shift, requiring decompressive craniectomy)", "Basilar artery occlusion ('locked-in' syndrome, quadriplegia, coma)"],
            "pathophysiology": "Occlusion of an intracranial artery causes immediate loss of blood supply to brain parenchyma; the ischemic core dies within minutes, surrounded by an ischemic penumbra that remains salvageable if reperfusion occurs rapidly.",
            "clinical_pearl": "Never administer rapid blood pressure lowering drugs in acute ischemic stroke unless SBP >220/120 mmHg (or >185/110 if receiving tPA). Permissive hypertension is vital to maintain collateral perfusion to the salvageable penumbra."
        },
        "pearl": "FAST: Face, Arm, Speech, Time. Non-contrast CT STAT to rule out bleed. IV Tenecteplase <4.5h + Endovascular Thrombectomy for LVO <24h. Permissive hypertension (target <185/110 for tPA, <220/120 otherwise)."
    }
}

# Aliases to map common alternative terminology to canonical registry entries
REGISTRY_ALIASES: Dict[str, str] = {
    "Sudan Virus": "Sudan Ebolavirus Disease",
    "Sudan Ebola": "Sudan Ebolavirus Disease",
    "Lassa": "Lassa Fever",
    "CCHF": "Crimean-Congo Hemorrhagic Fever",
    "Crimean-Congo": "Crimean-Congo Hemorrhagic Fever",
    "RVF": "Rift Valley Fever",
    "Rift Valley": "Rift Valley Fever",
    "Plasmodium vivax": "Malaria (Plasmodium vivax)",
    "Vivax Malaria": "Malaria (Plasmodium vivax)",
    "Vibrio cholerae": "Cholera",
    "Monkeypox": "Mpox (Monkeypox)",
    "Monkey Pox": "Mpox (Monkeypox)",
    "Mpox": "Mpox (Monkeypox)",
    "Weil's Disease": "Leptospirosis",
    "Weil Disease": "Leptospirosis",
    "TB": "Tuberculosis (Active)",
    "Pulmonary Tuberculosis": "Tuberculosis (Active)",
    "SARS-CoV-2": "COVID-19",
    "Covid": "COVID-19",
    "Flu": "Influenza",
    "Seasonal Flu": "Influenza",
    "Sleeping Sickness": "African Trypanosomiasis (Sleeping Sickness)",
    "African Sleeping Sickness": "African Trypanosomiasis (Sleeping Sickness)",
    "Malta Fever": "Brucellosis",
    "Undulant Fever": "Brucellosis",
    "Plague": "Bubonic Plague",
    "Black Death": "Bubonic Plague",
    "Primary HIV": "Acute HIV Infection (Primary)",
    "Acute HIV": "Acute HIV Infection (Primary)",
    "Whitmore Disease": "Melioidosis (Burkholderia pseudomallei)",
    "Nipah": "Nipah Virus Disease",
    "Nipah Virus": "Nipah Virus Disease",
    "Septic Shock": "Sepsis (Bacterial)",
    "Severe Sepsis": "Sepsis (Bacterial)",
    "Rubeola": "Measles",
    "Bilharzia": "Schistosomiasis (Katayama Fever)",
    "Katayama Fever": "Schistosomiasis (Katayama Fever)",
    "STEMI": "Acute Coronary Syndrome (STEMI)",
    "Acute MI": "Acute Coronary Syndrome (STEMI)",
    "Heart Attack": "Acute Coronary Syndrome (STEMI)",
    "Myocardial Infarction": "Acute Coronary Syndrome (STEMI)",
    "ADHF": "Heart Failure (Acute Decompensated)",
    "Congestive Heart Failure": "Heart Failure (Acute Decompensated)",
    "Pulmonary Edema": "Heart Failure (Acute Decompensated)",
    "Atrial Fibrillation": "Atrial Fibrillation (Rapid Ventricular Response)",
    "AFib": "Atrial Fibrillation (Rapid Ventricular Response)",
    "AFib with RVR": "Atrial Fibrillation (Rapid Ventricular Response)",
    "Tamponade": "Cardiac Tamponade",
    "Pericardial Tamponade": "Cardiac Tamponade",
    "Appendicitis": "Acute Appendicitis",
    "Pancreatitis": "Acute Pancreatitis",
    "Ascending Cholangitis": "Acute Ascending Cholangitis",
    "Cholangitis": "Acute Ascending Cholangitis",
    "Small Bowel Obstruction": "Bowel Obstruction",
    "SBO": "Bowel Obstruction",
    "DKA": "Diabetic Ketoacidosis (DKA)",
    "Addisonian Crisis": "Adrenal Insufficiency (Addisonian Crisis)",
    "Adrenal Crisis": "Adrenal Insufficiency (Addisonian Crisis)",
    "Stroke": "Ischemic Stroke",
    "Acute Stroke": "Ischemic Stroke",
    "CVA": "Ischemic Stroke",
}
