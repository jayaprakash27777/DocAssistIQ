import sqlite3
import json

db_path = r"D:\OFFLINE DATA\disease_catalog\master_disease_catalog.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

UPDATES = {
    "adult-onset-still-disease-829": {
        "name": "Adult-onset Still disease",
        "hallmarks": [
            "adult-onset still disease", "aosd", "evanescent salmon-pink rash", "salmon-pink maculopapular rash",
            "high spiking fevers", "quotidian fever", "markedly elevated ferritin", "hyperferritinemia",
            "arthralgias", "sore throat", "neutrophilic leukocytosis", "splenomegaly", "yamaguchi criteria",
            "negative ana and rf"
        ]
    },
    "hughes-stovin-syndrome-228116": {
        "name": "Hughes-Stovin syndrome",
        "hallmarks": [
            "hughes-stovin syndrome", "pulmonary artery aneurysm", "deep vein thrombosis", "hemoptysis",
            "massive hemoptysis", "oral aphthae", "recurrent oral aphthae", "thrombophlebitis", "aneurysm",
            "pulmonary vascular thrombosis", "recurrent thrombosis"
        ]
    },
    "autoimmune-encephalitis-622014": {
        "name": "Autoimmune encephalitis",
        "hallmarks": [
            "autoimmune encephalitis", "anti-nmdar encephalitis", "anti-nmda receptor encephalitis",
            "ovarian teratoma", "oro-facial dyskinesias", "choreoathetosis", "seizures", "psychosis",
            "autonomic instability", "memory loss", "behavioral changes", "paranoia"
        ]
    },
    "sporadic-creutzfeldt-jakob-disease-204": {
        "name": "Sporadic Creutzfeldt-Jakob disease",
        "hallmarks": [
            "sporadic creutzfeldt-jakob disease", "creutzfeldt-jakob disease", "cjd", "prion disease",
            "rapidly progressive dementia", "myoclonus", "involuntary jerks", "startle myoclonus",
            "ataxia", "cortical ribboning", "14-3-3 protein", "rt-quic positive", "periodic sharp wave complexes",
            "dysarthria", "spongiform encephalopathy"
        ]
    },
    "takayasu-arteritis-3287": {
        "name": "Takayasu arteritis",
        "hallmarks": [
            "takayasu arteritis", "pulseless disease", "aortic arch syndrome", "blood pressure discrepancy between arms",
            "upper extremity claudication", "weak radial pulse", "absent radial pulses", "supraclavicular bruit",
            "carotidynia", "dizziness looking upward", "concentric aortic wall thickening", "large vessel vasculitis"
        ]
    },
    "expert-takayasu-arteritis-pulseless-disease": {
        "name": "Takayasu Arteritis (Pulseless Disease)",
        "hallmarks": [
            "takayasu arteritis", "pulseless disease", "absent radial pulses", "discrepancy in blood pressure between arms",
            "blood pressure discrepancy between arms", "upper extremity claudication", "weak radial pulse",
            "supraclavicular bruit", "aortic arch syndrome", "large vessel vasculitis"
        ]
    },
    "kawasaki-disease-2331": {
        "name": "Kawasaki disease",
        "hallmarks": [
            "kawasaki disease", "mucocutaneous lymph node syndrome", "strawberry tongue", "strawberry-like tongue",
            "bilateral conjunctival injection", "erythema of lips", "cracked lips", "cervical lymphadenopathy",
            "polymorphous rash", "coronary artery aneurysm", "induration of hands and feet", "desquamation",
            "fever lasting at least five days"
        ]
    },
    "antiphospholipid-syndrome-80": {
        "name": "Antiphospholipid syndrome",
        "hallmarks": [
            "antiphospholipid syndrome", "aps", "hughes syndrome", "recurrent miscarriages", "recurrent pregnancy loss",
            "deep vein thrombosis", "pulmonary embolism", "thrombocytopenia", "livedo reticularis", "prolonged aptt",
            "lupus anticoagulant", "anticardiolipin", "anti-beta2-glycoprotein", "drvvt abnormal"
        ]
    },
    "antiphospholipid-antibody-syndrome-80": {
        "name": "Antiphospholipid antibody syndrome",
        "hallmarks": [
            "antiphospholipid antibody syndrome", "antiphospholipid syndrome", "aps", "recurrent miscarriages",
            "deep vein thrombosis", "pulmonary embolism", "thrombocytopenia", "prolonged aptt", "lupus anticoagulant"
        ]
    },
    "eosinophilic-granulomatosis-with-polyangiitis-183": {
        "name": "Eosinophilic granulomatosis with polyangiitis",
        "hallmarks": [
            "eosinophilic granulomatosis with polyangiitis", "churg-strauss syndrome", "egpa", "asthma",
            "peripheral eosinophilia", "mononeuritis multiplex", "foot drop", "wrist drop", "pulmonary infiltrates",
            "palpable purpura", "p-anca", "mpo-anca", "allergic rhinosinusitis"
        ]
    },
    "granulomatosis-with-polyangiitis-900": {
        "name": "Granulomatosis with polyangiitis",
        "hallmarks": [
            "granulomatosis with polyangiitis", "gpa", "wegener granulomatosis", "saddle nose deformity",
            "destruction of nasal septum", "recurrent epistaxis", "sinusitis", "pulmonary nodules",
            "cavitary lung lesions", "hemoptysis", "glomerulonephritis", "c-anca", "pr3-anca", "c-anca positive"
        ]
    },
    "myasthenia-gravis-589": {
        "name": "Myasthenia gravis",
        "hallmarks": [
            "myasthenia gravis", "mg", "fluctuating weakness", "ptosis", "drooping eyelids", "diplopia",
            "dysphagia", "nasal speech", "fatigability worsening by evening", "anti-achr", "anti-musk",
            "edrophonium positive", "acetylcholine receptor antibody", "thymoma"
        ]
    },
    "maple-syrup-urine-disease-511": {
        "name": "Maple syrup urine disease",
        "hallmarks": [
            "maple syrup urine disease", "msud", "sweet odor in urine", "maple syrup urine odor",
            "branched-chain amino acids", "elevated leucine", "poor feeding", "lethargy", "vomiting",
            "encephalopathy in neonate", "ketoacidosis", "sweet smelling urine"
        ]
    },
    "multiple-endocrine-neoplasia-type-2-653": {
        "name": "Multiple endocrine neoplasia type 2",
        "hallmarks": [
            "multiple endocrine neoplasia type 2", "men2", "men 2a", "medullary thyroid carcinoma",
            "pheochromocytoma", "parathyroid hyperplasia", "hypercalcemia", "elevated calcitonin",
            "ret proto-oncogene", "palpitations", "sweating", "headache", "constipation"
        ]
    },
    "poems-syndrome-2905": {
        "name": "POEMS syndrome",
        "hallmarks": [
            "poems syndrome", "crow-fukase syndrome", "polyneuropathy", "organomegaly", "endocrinopathy",
            "monoclonal protein", "skin changes", "osteosclerotic bone lesions", "hyperpigmentation",
            "papilledema", "extravascular volume overload", "thrombocytosis", "elevated vegf", "lambda light chain"
        ]
    },
    "mplus-sjogrens-syndrome": {
        "name": "Sjogren's Syndrome",
        "hallmarks": [
            "sjogren's syndrome", "sjogren syndrome", "sicca syndrome", "keratoconjunctivitis sicca",
            "xerostomia", "dry eyes", "dry mouth", "parotid gland enlargement", "schirmer test positive",
            "anti-ro", "anti-la", "anti-ssa", "anti-ssb"
        ]
    },
    "cryptococcosis-1546": {
        "name": "Cryptococcosis",
        "hallmarks": [
            "cryptococcosis", "cryptococcal meningitis", "fungal meningitis", "cryptococcus neoformans",
            "india ink positive", "encapsulated yeasts in csf", "cryptococcal antigen", "cd4 <100 in hiv",
            "headache", "fever", "meningismus", "elevated opening pressure"
        ]
    },
    "icd10-b451-cerebral-cryptococcosis-cryptococcal-meningitis-in-hiv": {
        "name": "Cerebral cryptococcosis (Cryptococcal meningitis in HIV)",
        "hallmarks": [
            "cerebral cryptococcosis (cryptococcal meningitis in hiv)", "cryptococcal meningitis",
            "fungal meningitis", "india ink positive", "encapsulated yeasts in csf", "cryptococcal antigen",
            "cd4 <100 in hiv", "headache", "fever", "meningismus", "elevated opening pressure"
        ]
    }
}

for did, info in UPDATES.items():
    cur.execute("SELECT id, hallmarks_json FROM diseases WHERE id = ?", (did,))
    row = cur.fetchone()
    if row:
        existing_h = json.loads(row[1]) if row[1] else []
        merged_h = list(dict.fromkeys(info["hallmarks"] + existing_h))
        cur.execute("UPDATE diseases SET hallmarks_json = ? WHERE id = ?", (json.dumps(merged_h), did))
        print(f"Updated {did} ({info['name']}) -> {len(merged_h)} hallmarks")

NEW_DISEASES = [
    {
        "id": "expert-addisons-disease-e271",
        "name": "Addison's Disease (Primary Adrenal Insufficiency)",
        "icd10": "E27.1",
        "icd11": "5A71.0",
        "orphacode": "ORPHA:85414",
        "category": "Endocrinology",
        "severity": "critical",
        "triage": "URGENT",
        "synonyms": ["addison's disease", "addison disease", "primary adrenal insufficiency", "chronic adrenocortical insufficiency"],
        "hallmarks": [
            "addison's disease", "addison disease", "primary adrenal insufficiency", "hyperpigmentation",
            "palmar crease hyperpigmentation", "mucosal hyperpigmentation", "knuckle hyperpigmentation",
            "fatigue", "weakness", "weight loss", "hyponatremia", "hyperkalemia", "hypotension",
            "postural hypotension", "salt craving", "elevated acth", "low cortisol", "skin darkening"
        ],
        "data": {
            "cardinal_symptoms": ["hyperpigmentation", "fatigue", "hyponatremia", "hyperkalemia", "hypotension"],
            "immediate_tests": ["Serum Cortisol (8 AM)", "Plasma ACTH", "Basic Metabolic Panel (Na, K)", "ACTH Stimulation Test"],
            "recommended_medications": ["Oral Hydrocortisone", "Fludrocortisone", "Stress-dose steroids counseling"],
            "pearl": "Primary adrenal insufficiency presents with hyperpigmentation (due to elevated ACTH/POMC), hyponatremia, and hyperkalemia."
        }
    },
    {
        "id": "expert-silicosis-j628",
        "name": "Silicosis",
        "icd10": "J62.8",
        "icd11": "CA60",
        "orphacode": "ORPHA:3197",
        "category": "Pulmonology / Occupational",
        "severity": "high",
        "triage": "ROUTINE",
        "synonyms": ["silicosis", "pneumoconiosis due to silica", "silicotuberculosis", "grinder's disease"],
        "hallmarks": [
            "silicosis", "silica dust exposure", "stone-cutting worker", "sandblasting", "quarry worker",
            "eggshell calcification of hilar lymph nodes", "upper lobe rounded nodules", "progressive exertional dyspnea",
            "restrictive lung disease", "dry cough", "pulmonary fibrosis"
        ],
        "data": {
            "cardinal_symptoms": ["stone-cutting worker", "eggshell calcification of hilar lymph nodes", "progressive exertional dyspnea", "upper lobe nodules"],
            "immediate_tests": ["High-Resolution Chest CT (HRCT)", "Pulmonary Function Tests (PFTs)", "Tuberculin Skin Test / IGRA"],
            "recommended_medications": ["Cessation of silica exposure", "Supplemental oxygen if hypoxemic", "Pulmonary rehabilitation"],
            "pearl": "Silicosis classically causes eggshell calcification of hilar lymph nodes and multiple small upper-lobe nodules with increased tuberculosis risk."
        }
    },
    {
        "id": "expert-berylliosis-j632",
        "name": "Chronic Beryllium Disease (Berylliosis)",
        "icd10": "J63.2",
        "icd11": "CA61",
        "orphacode": "ORPHA:3198",
        "category": "Pulmonology / Occupational",
        "severity": "high",
        "triage": "ROUTINE",
        "synonyms": ["chronic beryllium disease", "berylliosis", "beryllium disease", "cbd"],
        "hallmarks": [
            "chronic beryllium disease", "berylliosis", "beryllium exposure", "dental technician", "aerospace worker",
            "bilateral hilar lymphadenopathy", "non-caseating granulomas", "beryllium lymphocyte proliferation test",
            "belpt", "progressive dyspnea", "dry cough", "fatigue", "night sweats"
        ],
        "data": {
            "cardinal_symptoms": ["beryllium lymphocyte proliferation test", "dental technician", "bilateral hilar lymphadenopathy", "non-caseating granulomas"],
            "immediate_tests": ["Beryllium Lymphocyte Proliferation Test (BeLPT)", "High-Resolution Chest CT", "Bronchoscopy with BAL"],
            "recommended_medications": ["Systemic corticosteroids (Prednisone)", "Immunosuppressants (Methotrexate) if refractory"],
            "pearl": "Chronic Beryllium Disease mimics sarcoidosis with non-caseating granulomas, diagnosed by abnormal BeLPT in dental/aerospace workers."
        }
    },
    {
        "id": "expert-cvst-i676",
        "name": "Cerebral Venous Sinus Thrombosis (CVST)",
        "icd10": "I67.6",
        "icd11": "8B13",
        "orphacode": "ORPHA:85415",
        "category": "Neurology / Vascular",
        "severity": "critical",
        "triage": "EMERGENT",
        "synonyms": ["cerebral venous sinus thrombosis", "cvst", "cerebral venous thrombosis", "dural sinus thrombosis"],
        "hallmarks": [
            "cerebral venous sinus thrombosis", "cvst", "venous sinus thrombosis", "sagittal sinus thrombosis",
            "transverse sinus thrombosis", "mr venography filling defect", "headache", "papilledema",
            "transient visual obscurations", "pulsatile tinnitus", "elevated d-dimer", "hypercoagulable state"
        ],
        "data": {
            "cardinal_symptoms": ["headache", "mr venography filling defect", "papilledema", "pulsatile tinnitus", "elevated d-dimer"],
            "immediate_tests": ["MR Venography (MRV)", "Contrast-enhanced Brain MRI", "Coagulation Profile & D-Dimer"],
            "recommended_medications": ["Therapeutic Anticoagulation (LMWH or unfractionated heparin)", "Endovascular thrombectomy if refractory"],
            "pearl": "CVST is diagnosed via MR Venography demonstrating absence of flow / 'empty delta sign' in dural sinuses."
        }
    },
    {
        "id": "expert-iga-nephropathy-n028",
        "name": "IgA Nephropathy (Berger Disease)",
        "icd10": "N02.8",
        "icd11": "GB40",
        "orphacode": "ORPHA:85416",
        "category": "Nephrology",
        "severity": "high",
        "triage": "URGENT",
        "synonyms": ["iga nephropathy", "berger's disease", "berger disease", "synpharyngitic glomerulonephritis"],
        "hallmarks": [
            "iga nephropathy", "berger's disease", "berger disease", "synpharyngitic hematuria",
            "gross hematuria with sore throat", "episodic macroscopic hematuria", "mesangial iga deposition",
            "rbc casts", "proteinuria", "microscopic hematuria", "recurrent hematuria"
        ],
        "data": {
            "cardinal_symptoms": ["synpharyngitic hematuria", "gross hematuria with sore throat", "rbc casts", "proteinuria"],
            "immediate_tests": ["Renal Biopsy (Immunofluorescence for mesangial IgA)", "Urinalysis with Microscopy", "Serum Creatinine"],
            "recommended_medications": ["ACE inhibitors / ARBs (optimized blood pressure control)", "SGLT2 inhibitors", "Systemic corticosteroids if high risk"],
            "pearl": "IgA nephropathy classically presents with gross hematuria concurrent with or within 24-48 hours of upper respiratory infection ('synpharyngitic')."
        }
    },
    {
        "id": "expert-hairy-cell-leukemia-c914",
        "name": "Hairy Cell Leukemia",
        "icd10": "C91.4",
        "icd11": "2A60.2",
        "orphacode": "ORPHA:85417",
        "category": "Hematology / Oncology",
        "severity": "high",
        "triage": "URGENT",
        "synonyms": ["hairy cell leukemia", "hcl", "leukemic reticuloendotheliosis"],
        "hallmarks": [
            "hairy cell leukemia", "hcl", "hair-like cytoplasmic projections", "trap positive",
            "tartrate-resistant acid phosphatase", "braf v600e mutation", "massive splenomegaly without lymphadenopathy",
            "pancytopenia", "monocytopenia", "dry tap bone marrow", "splenomegaly"
        ],
        "data": {
            "cardinal_symptoms": ["hair-like cytoplasmic projections", "trap positive", "braf v600e mutation", "massive splenomegaly without lymphadenopathy", "monocytopenia"],
            "immediate_tests": ["Peripheral Blood Flow Cytometry (CD11c, CD25, CD103)", "Bone Marrow Biopsy with TRAP stain", "BRAF V600E Mutation Testing"],
            "recommended_medications": ["Purine nucleoside analogs (Cladribine or Pentostatin)", "BRAF inhibitors (Vemurafenib) if relapsed"],
            "pearl": "Hairy cell leukemia presents with massive splenomegaly, pancytopenia with profound monocytopenia, TRAP-positive hair-like lymphoid cells, and BRAF V600E mutation."
        }
    },
    {
        "id": "expert-celiac-disease-k900",
        "name": "Celiac Disease (Gluten Enteropathy)",
        "icd10": "K90.0",
        "icd11": "DA96.0",
        "orphacode": "ORPHA:85418",
        "category": "Gastroenterology",
        "severity": "moderate",
        "triage": "ROUTINE",
        "synonyms": ["celiac disease", "celiac sprue", "gluten enteropathy", "nontropical sprue", "coeliac disease"],
        "hallmarks": [
            "celiac disease", "celiac sprue", "gluten enteropathy", "anti-ttg iga", "anti-tissue transglutaminase",
            "anti-endomysial antibodies", "villous atrophy", "intraepithelial lymphocytosis", "dermatitis herpetiformis",
            "chronic diarrhea", "malabsorption", "iron deficiency anemia unresponsive to oral iron", "bloating", "steatorrhea"
        ],
        "data": {
            "cardinal_symptoms": ["anti-ttg iga", "anti-tissue transglutaminase", "dermatitis herpetiformis", "villous atrophy", "chronic diarrhea"],
            "immediate_tests": ["Serum IgA Anti-Tissue Transglutaminase (anti-tTG IgA)", "Total Serum IgA", "Esophagogastroduodenoscopy (EGD) with Duodenal Biopsies"],
            "recommended_medications": ["Strict lifelong gluten-free diet", "Nutritional supplementation (Iron, Vitamin D, Calcium, Folate)"],
            "pearl": "Celiac disease is confirmed by elevated anti-tTG IgA serology and duodenal biopsy showing villous blunting and intraepithelial lymphocytosis."
        }
    },
    {
        "id": "expert-insulinoma-d137",
        "name": "Insulinoma",
        "icd10": "D13.7",
        "icd11": "2F35.0",
        "orphacode": "ORPHA:85419",
        "category": "Endocrinology / Oncology",
        "severity": "high",
        "triage": "URGENT",
        "synonyms": ["insulinoma", "pancreatic neuroendocrine tumor", "islet cell tumor", "endogenous hyperinsulinism"],
        "hallmarks": [
            "insulinoma", "pancreatic neuroendocrine tumor", "whipple triad", "fasting hypoglycemia",
            "symptoms relieved by glucose", "inappropriately elevated insulin", "inappropriately elevated c-peptide",
            "negative sulfonylurea screen", "confusion", "diaphoresis", "tremor", "weight gain"
        ],
        "data": {
            "cardinal_symptoms": ["whipple triad", "inappropriately elevated insulin", "inappropriately elevated c-peptide", "negative sulfonylurea screen", "fasting hypoglycemia"],
            "immediate_tests": ["Supervised 72-hour Fasting Test", "Paired Serum Glucose, Insulin, C-Peptide, Proinsulin", "Endoscopic Ultrasound (EUS) of Pancreas"],
            "recommended_medications": ["Diazoxide / Octreotide for medical stabilization", "Surgical enucleation / partial pancreatectomy"],
            "pearl": "Insulinoma causes neuroglycopenic symptoms satisfying Whipple's triad with inappropriately detectable insulin and C-peptide during hypoglycemia."
        }
    },
    {
        "id": "expert-adrenal-crisis-e272",
        "name": "Acute Adrenal Crisis",
        "icd10": "E27.2",
        "icd11": "5A71.2",
        "orphacode": "ORPHA:85420",
        "category": "Endocrinology",
        "severity": "critical",
        "triage": "EMERGENT",
        "synonyms": ["acute adrenal crisis", "addisonian crisis", "acute adrenocortical insufficiency"],
        "hallmarks": [
            "acute adrenal crisis", "addisonian crisis", "refractory hypotension", "circulatory collapse refractory to fluids",
            "profound weakness", "confusion", "fever", "hyperpigmentation", "hyponatremia", "hyperkalemia",
            "hypoglycemia", "adrenal insufficiency", "severe abdominal pain", "vomiting"
        ],
        "data": {
            "cardinal_symptoms": ["refractory hypotension", "circulatory collapse refractory to fluids", "hyperpigmentation", "hyponatremia", "hyperkalemia"],
            "immediate_tests": ["STAT IV Hydrocortisone (100 mg bolus)", "Basic Metabolic Panel (Na, K, Glucose)", "Serum Cortisol & ACTH (do not delay treatment)"],
            "recommended_medications": ["IV Hydrocortisone 100mg bolus q8h", "Aggressive IV 0.9% Normal Saline with 5% Dextrose resuscitation"],
            "pearl": "Acute adrenal crisis is a life-threatening endocrine emergency presenting with circulatory shock refractory to volume and inotropes, requiring immediate IV hydrocortisone."
        }
    }
]

for d in NEW_DISEASES:
    cur.execute("SELECT id FROM diseases WHERE id = ?", (d["id"],))
    if not cur.fetchone():
        cur.execute(
            """
            INSERT INTO diseases (id, name, icd10, icd11, orphacode, category, severity, triage, synonyms_json, hallmarks_json, data_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                d["id"],
                d["name"],
                d["icd10"],
                d["icd11"],
                d["orphacode"],
                d["category"],
                d["severity"],
                d["triage"],
                json.dumps(d["synonyms"]),
                json.dumps(d["hallmarks"]),
                json.dumps(d["data"])
            )
        )
        print(f"Inserted new master catalog disease: {d['name']} ({d['id']})")

conn.commit()
conn.close()
print("Finished clinical master catalog enrichment!")
