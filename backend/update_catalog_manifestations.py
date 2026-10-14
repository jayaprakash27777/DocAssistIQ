import sqlite3
import json

db_path = r"D:\OFFLINE DATA\disease_catalog\master_disease_catalog.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# High-yield clinical manifestations for targeted conditions
CLINICAL_UPDATES = {
    "thrombotic-thrombocytopenic-purpura-54057": {
        "name": "Thrombotic thrombocytopenic purpura",
        "hallmarks": [
            "thrombotic thrombocytopenic purpura", "ttp", "schistocytes", "fragmented red cells",
            "microangiopathic hemolytic anemia", "severe thrombocytopenia", "thrombocytopenia",
            "fever", "confusion", "headache", "acute kidney injury", "renal impairment",
            "low adamts13", "petechiae", "purpura", "anemia", "elevated ldh", "low haptoglobin"
        ]
    },
    "immune-mediated-thrombotic-thrombocytopenic-purpura-93585": {
        "name": "Immune-mediated thrombotic thrombocytopenic purpura",
        "hallmarks": [
            "immune-mediated thrombotic thrombocytopenic purpura", "acquired ttp", "ttp",
            "schistocytes", "fragmented red cells", "microangiopathic hemolytic anemia",
            "severe thrombocytopenia", "thrombocytopenia", "fever", "confusion", "headache",
            "acute kidney injury", "renal impairment", "low adamts13", "petechiae", "purpura"
        ]
    },
    "expert-thrombotic-thrombocytopenic-purpura-ttp": {
        "name": "Thrombotic Thrombocytopenic Purpura (TTP)",
        "hallmarks": [
            "thrombotic thrombocytopenic purpura", "ttp", "schistocytes", "fragmented red cells",
            "microangiopathic hemolytic anemia", "severe thrombocytopenia", "thrombocytopenia",
            "fever", "confusion", "headache", "acute kidney injury", "renal impairment",
            "low adamts13", "petechiae", "purpura", "anemia", "elevated ldh", "low haptoglobin"
        ]
    },
    "expert-acute-cholecystitis": {
        "name": "Acute Cholecystitis",
        "hallmarks": [
            "acute cholecystitis", "cholecystitis", "gallstones", "gallbladder stones",
            "cholelithiasis", "biliary colic", "right upper quadrant pain", "ruq pain",
            "right-upper-quadrant pain", "murphy sign", "sonographic murphy sign",
            "gallbladder wall thickening", "postprandial pain", "fatty meals", "vomiting", "nausea"
        ]
    },
    "mplus-gallstones": {
        "name": "Gallstones",
        "hallmarks": [
            "gallstones", "cholelithiasis", "biliary colic", "right upper quadrant pain",
            "ruq pain", "right-upper-quadrant pain", "gallbladder stones", "nausea", "vomiting"
        ]
    },
    "whipple-disease-3452": {
        "name": "Whipple disease",
        "hallmarks": [
            "whipple disease", "tropheryma whipplei", "migratory polyarthritis", "migratory arthralgias",
            "migratory joint pain", "chronic diarrhea", "watery diarrhea", "weight loss",
            "abdominal pain", "malabsorption", "pas-positive macrophages", "enlarged villi",
            "pale small-bowel mucosa", "hypoalbuminemia"
        ]
    },
    "familial-mediterranean-fever-342": {
        "name": "Familial Mediterranean fever",
        "hallmarks": [
            "familial mediterranean fever", "fmf", "benign paroxysmal peritonitis", "benign recurrent polyserositis",
            "periodic fever syndrome", "recurrent episodes of fever", "severe abdominal pain", "pleuritic chest pain",
            "chest pain", "ankle swelling", "serositis", "peritonitis", "pleuritis", "eastern mediterranean descent",
            "recurrent fever attacks", "attacks lasting about two days", "persistent albumin", "aa amyloidosis"
        ]
    },
    "strongyloidiasis-76": {
        "name": "Strongyloidiasis",
        "hallmarks": [
            "strongyloidiasis", "strongyloides stercoralis", "larva currens", "rhabditiform larvae",
            "eosinophilia", "watery diarrhea", "wheezing", "cough", "abdominal distension",
            "hyperinfection", "corticosteroid immunosuppression", "corticosteroid use",
            "barefoot in soil", "gram-negative bacteremia"
        ]
    },
    "relapsing-polychondritis-728": {
        "name": "Relapsing polychondritis",
        "hallmarks": [
            "relapsing polychondritis", "auricular chondritis", "red ears", "ear pain",
            "ears red and hurt", "nasal chondritis", "tender nose", "nose tender",
            "saddle nose", "saddle nose deformity", "episcleritis", "costochondritis",
            "arthralgia", "painful joints", "macrocytic anemia", "steroid-responsive", "fever"
        ]
    },
    "hypokalemic-periodic-paralysis-681": {
        "name": "Hypokalemic periodic paralysis",
        "hallmarks": [
            "hypokalemic periodic paralysis", "periodic paralysis", "hypokalemia", "severe hypokalemia",
            "acute flaccid paralysis", "flaccid paralysis", "muscle weakness", "quadriparesis",
            "weakness both legs and arms", "u waves", "flat t waves", "distal renal tubular acidosis",
            "sjogren syndrome", "sicca syndrome", "xerostomia", "xerophthalmia", "pins and needles"
        ]
    },
    "amyloidosis-69": {
        "name": "Amyloidosis",
        "hallmarks": [
            "amyloidosis", "systemic amyloidosis", "macroglossia", "enlarged tongue",
            "periorbital purpura", "raccoon eyes", "apical sparing", "low qrs voltage",
            "cardiac amyloidosis", "unexplained proteinuria", "proteinuria", "monoclonal protein",
            "burning pain in feet", "acroparesthesia", "autonomic neuropathy", "edema"
        ]
    },
    "al-amyloidosis-85443": {
        "name": "AL amyloidosis",
        "hallmarks": [
            "al amyloidosis", "light-chain amyloidosis", "amyloidosis", "macroglossia", "enlarged tongue",
            "periorbital purpura", "raccoon eyes", "apical sparing", "low qrs voltage",
            "cardiac amyloidosis", "unexplained proteinuria", "proteinuria", "monoclonal protein",
            "burning pain in feet", "acroparesthesia", "autonomic neuropathy"
        ]
    },
    "hemolytic-uremic-syndrome-544458": {
        "name": "Hemolytic uremic syndrome",
        "hallmarks": [
            "hemolytic uremic syndrome", "stec-hus", "hus", "shiga toxin", "bloody diarrhea",
            "thrombocytopenia", "acute kidney injury", "microangiopathic hemolytic anemia",
            "schistocytes", "fragmented red cells", "pediatric renal failure", "pallor",
            "jaundice", "reduced urine output", "oliguria", "anemia"
        ]
    },
    "shiga-toxin-associated-hemolytic-uremic-syndrome-90038": {
        "name": "Shiga toxin-associated hemolytic uremic syndrome",
        "hallmarks": [
            "shiga toxin-associated hemolytic uremic syndrome", "stec-hus", "hus", "shiga toxin",
            "bloody diarrhea", "thrombocytopenia", "acute kidney injury", "microangiopathic hemolytic anemia",
            "schistocytes", "fragmented red cells", "pallor", "jaundice", "reduced urine output"
        ]
    },
    "sporadic-pheochromocytomasecreting-paraganglioma-276621": {
        "name": "Pheochromocytoma",
        "hallmarks": [
            "pheochromocytoma", "paroxysmal hypertension", "severe hypertension", "headache",
            "pounding headache", "paroxysmal headache", "palpitations", "sweating", "diaphoresis",
            "tremor", "tremulousness", "elevated metanephrines", "plasma metanephrines",
            "urinary metanephrines", "catecholamines", "panic attacks"
        ]
    },
    "pituitary-apoplexy-95613": {
        "name": "Pituitary apoplexy",
        "hallmarks": [
            "pituitary apoplexy", "sheehan syndrome", "postpartum hemorrhage", "postpartum bleeding",
            "bitemporal hemianopia", "bitemporal visual field loss", "peripheral visual field loss",
            "ophthalmoplegia", "double vision", "pituitary hemorrhage", "acute hypopituitarism",
            "adrenal crisis", "hypotension", "hyponatremia", "hypoglycemia", "headache", "vomiting"
        ]
    },
    "sheehan-syndrome-91355": {
        "name": "Sheehan syndrome",
        "hallmarks": [
            "sheehan syndrome", "pituitary apoplexy", "postpartum hemorrhage", "postpartum bleeding",
            "bitemporal hemianopia", "bitemporal visual field loss", "peripheral visual field loss",
            "ophthalmoplegia", "hypopituitarism", "hypotension", "hyponatremia", "hypoglycemia"
        ]
    },
    "mplus-cushings-syndrome": {
        "name": "Cushing's Syndrome",
        "hallmarks": [
            "cushing syndrome", "cushings syndrome", "exogenous cushing syndrome", "hypercortisolemia",
            "purple striae", "stretch marks", "broad purple stretch marks", "central obesity",
            "facial plethora", "moon facies", "easy bruising", "bruising", "proximal muscle weakness",
            "hirsutism", "irregular menses", "skin-lightening cream", "corticosteroid use", "hypertension"
        ]
    },
    "behçet-disease-117": {
        "name": "Behçet disease",
        "hallmarks": [
            "behcet disease", "behçet disease", "neuro-behcet", "oral ulcers", "mouth ulcers",
            "aphthous ulcers", "genital ulcers", "uveitis", "hypopyon", "pathergy test positive",
            "pathergy", "erythema nodosum", "intracranial arterial narrowing", "cerebral vasculitis"
        ]
    },
    "systemic-lupus-erythematosus-536": {
        "name": "Systemic lupus erythematosus",
        "hallmarks": [
            "systemic lupus erythematosus", "sle", "lupus", "malar rash", "facial rash",
            "sun-triggered rash", "sun-triggered facial rash", "oral ulcers", "mouth ulcers",
            "painless mouth ulcers", "morning stiffness", "joint pain", "ankle swelling",
            "frothy urine", "proteinuria", "thrombocytopenia", "anemia", "red-cell casts", "antinuclear antibody"
        ]
    },
    "erdheim-chester-disease-35687": {
        "name": "Erdheim-Chester disease",
        "hallmarks": [
            "erdheim-chester disease", "coated aorta", "circumferential soft-tissue cuff around the aorta",
            "hairy kidneys", "soft tissue surrounding both kidneys", "osteosclerosis", "sclerosis of the long bones",
            "patchy sclerosis", "bone pain", "polyuria", "large volumes of dilute urine", "polydipsia",
            "excessive thirst", "diabetes insipidus", "fatigue", "retroperitoneal fibrosis"
        ]
    },
    "x-linked-adrenoleukodystrophy-43": {
        "name": "X-linked adrenoleukodystrophy",
        "hallmarks": [
            "x-linked adrenoleukodystrophy", "adrenoleukodystrophy", "x-ald", "cerebral demyelination",
            "posterior cerebral white matter", "speech regression", "loss of speech", "ataxia",
            "worsening balance", "visual loss", "difficulty seeing", "hyperpigmentation",
            "palmar crease pigmentation", "adrenal insufficiency", "vomiting", "lethargy"
        ]
    },
    "ornithine-transcarbamylase-deficiency-664": {
        "name": "Ornithine transcarbamylase deficiency",
        "hallmarks": [
            "ornithine transcarbamylase deficiency", "otc deficiency", "urea cycle disorder",
            "hyperammonemia", "plasma ammonia", "respiratory alkalosis", "protein intolerance",
            "sleepy after a high-protein meal", "vomiting", "lethargy", "confusion", "rapid breathing"
        ]
    },
    "disorder-of-urea-cycle-metabolism-and-ammonia-detoxification-79167": {
        "name": "Disorder of urea cycle metabolism and ammonia detoxification",
        "hallmarks": [
            "disorder of urea cycle metabolism and ammonia detoxification", "urea cycle disorder",
            "ornithine transcarbamylase deficiency", "hyperammonemia", "plasma ammonia",
            "respiratory alkalosis", "protein intolerance", "sleepy after a high-protein meal", "vomiting", "lethargy", "confusion"
        ]
    },
    "neuromyelitis-optica-spectrum-disorder-71211": {
        "name": "Neuromyelitis optica spectrum disorder",
        "hallmarks": [
            "neuromyelitis optica spectrum disorder", "neuromyelitis optica", "nmosd", "devic disease",
            "optic neuritis", "painful visual loss", "longitudinally extensive transverse myelitis",
            "sensory level myelopathy", "area postrema syndrome", "severe hiccups", "urinary retention",
            "numbness", "unilateral weakness"
        ]
    },
    "neuromyelitis-optica-spectrum-disorder-with-anti-aqp4-antibodies-592850": {
        "name": "Neuromyelitis optica spectrum disorder with anti-AQP4 antibodies",
        "hallmarks": [
            "neuromyelitis optica spectrum disorder", "neuromyelitis optica", "nmosd", "devic disease",
            "optic neuritis", "painful visual loss", "longitudinally extensive transverse myelitis",
            "sensory level myelopathy", "area postrema syndrome", "severe hiccups", "urinary retention",
            "numbness", "unilateral weakness", "anti-aqp4"
        ]
    },
    "expert-leishmaniasis-visceral-kala-azar": {
        "name": "Leishmaniasis (Visceral / Kala-azar)",
        "hallmarks": [
            "visceral leishmaniasis", "kala-azar", "leishmaniasis", "splenomegaly", "splenic enlargement",
            "hepatomegaly", "liver enlargement", "pancytopenia", "intermittent fever", "pallor",
            "weight loss", "thrombocytopenia", "anemia", "loss of appetite"
        ]
    },
    "leishmaniasis-507": {
        "name": "Leishmaniasis",
        "hallmarks": [
            "visceral leishmaniasis", "kala-azar", "leishmaniasis", "splenomegaly", "splenic enlargement",
            "hepatomegaly", "liver enlargement", "pancytopenia", "intermittent fever", "pallor", "weight loss"
        ]
    },
    "icd10-b550-visceral-leishmaniasis-kala-azar-with-hepatosplenomegaly": {
        "name": "Visceral leishmaniasis (Kala-azar with hepatosplenomegaly)",
        "hallmarks": [
            "visceral leishmaniasis", "kala-azar", "leishmaniasis", "splenomegaly", "splenic enlargement",
            "hepatomegaly", "liver enlargement", "pancytopenia", "intermittent fever", "pallor", "weight loss"
        ]
    },
    "melioidosis-31202": {
        "name": "Melioidosis",
        "hallmarks": [
            "melioidosis", "burkholderia pseudomallei", "cavitary lung lesions", "pulmonary cavitation",
            "splenic lesions", "splenic abscess", "liver lesions", "hepatic abscess", "chronic plantar ulcer",
            "abscess", "persistent fever", "night sweats", "productive cough", "purulent sputum", "diabetes"
        ]
    },
    "expert-melioidosis-burkholderia-pseudomallei": {
        "name": "Melioidosis (Burkholderia pseudomallei)",
        "hallmarks": [
            "melioidosis", "burkholderia pseudomallei", "cavitary lung lesions", "pulmonary cavitation",
            "splenic lesions", "splenic abscess", "liver lesions", "hepatic abscess", "chronic plantar ulcer",
            "abscess", "persistent fever", "night sweats", "productive cough", "purulent sputum", "diabetes"
        ]
    },
    "acute-intermittent-porphyria-79276": {
        "name": "Acute intermittent porphyria",
        "hallmarks": [
            "acute intermittent porphyria", "aip", "porphyria", "crampy abdominal pain",
            "severe abdominal pain", "abdominal pain", "vomiting", "constipation", "hyponatremia",
            "proximal muscle weakness", "muscle weakness", "reduced reflexes", "hyporeflexia",
            "agitation", "confusion", "hypertension", "tachycardia", "porphobilinogen", "red-purple urine",
            "low-carbohydrate diet", "porphyria trigger low carbohydrate"
        ]
    },
    "expert-acute-intermittent-porphyria-aip": {
        "name": "Acute Intermittent Porphyria (AIP)",
        "hallmarks": [
            "acute intermittent porphyria", "aip", "porphyria", "crampy abdominal pain",
            "severe abdominal pain", "abdominal pain", "vomiting", "constipation", "hyponatremia",
            "proximal muscle weakness", "muscle weakness", "reduced reflexes", "hyporeflexia",
            "agitation", "confusion", "hypertension", "tachycardia", "porphobilinogen", "red-purple urine"
        ]
    },
    "histoplasmosis-390": {
        "name": "Histoplasmosis",
        "hallmarks": [
            "histoplasmosis", "disseminated histoplasmosis", "intracellular yeasts in macrophages",
            "intracellular yeasts", "micronodular infiltrates", "hepatosplenomegaly", "splenomegaly",
            "fever", "weight loss", "dyspnea", "progressive dyspnea", "pancytopenia", "ferritin",
            "hiv infection", "fungal infection"
        ]
    },
    "brucellosis-1304": {
        "name": "Brucellosis",
        "hallmarks": [
            "brucellosis", "malta fever", "undulant fever", "undulating fever", "dairy farmer",
            "unpasteurized dairy", "lumbar spondylodiscitis", "spondylodiscitis", "back pain",
            "lower back pain", "lumbar spine tenderness", "hepatosplenomegaly", "night sweats",
            "fatigue", "fever", "joint pain"
        ]
    },
    "igg4-related-disease-284264": {
        "name": "IgG4-related disease",
        "hallmarks": [
            "igg4-related disease", "igg4-rd", "autoimmune pancreatitis", "sausage-shaped pancreas",
            "elevated serum igg4", "igg4", "painless jaundice", "jaundice", "weight loss",
            "retroperitoneal lymphadenopathy", "diabetes", "halo of hypoattenuation"
        ]
    },
    "infective-endocarditis-570762": {
        "name": "Infective endocarditis",
        "hallmarks": [
            "infective endocarditis", "endocarditis", "bacterial endocarditis", "mitral valve prolapse",
            "regurgitant murmur", "systolic murmur", "splinter hemorrhages", "janeway lesions",
            "osler nodes", "streptococcus viridans", "dental cleaning", "night sweats", "fever",
            "malaise", "anorexia", "bacteremia"
        ]
    },
    "mplus-endocarditis": {
        "name": "Endocarditis",
        "hallmarks": [
            "infective endocarditis", "endocarditis", "bacterial endocarditis", "splinter hemorrhages",
            "janeway lesions", "streptococcus viridans", "dental cleaning", "regurgitant murmur"
        ]
    },
    "lambert-eaton-myasthenic-syndrome-43393": {
        "name": "Lambert-Eaton myasthenic syndrome",
        "hallmarks": [
            "lambert-eaton myasthenic syndrome", "lambert-eaton syndrome", "lems",
            "post-exercise facilitation", "lambert sign", "proximal leg weakness", "leg weakness",
            "hyporeflexia", "dry mouth", "erectile dysfunction", "hilar lung mass",
            "small cell lung cancer", "autonomic dysfunction"
        ]
    },
    "castleman-disease-160": {
        "name": "Castleman disease",
        "hallmarks": [
            "castleman disease", "multicentric castleman disease", "tafro syndrome", "hhv-8", "hhv8",
            "interleukin-6", "elevated il-6", "polyclonal hypergammaglobulinemia", "generalized lymphadenopathy",
            "lymphadenopathy", "hepatosplenomegaly", "massive hepatosplenomegaly", "fevers",
            "night sweats", "weight loss", "thrombocytopenia", "anemia"
        ]
    },
    "mplus-pneumocystis-infections": {
        "name": "Pneumocystis Infections",
        "hallmarks": [
            "pneumocystis pneumonia", "pneumocystis jirovecii pneumonia", "pcp", "pjp",
            "ground-glass opacities", "bilateral ground-glass opacities", "progressive exertional dyspnea",
            "exertional dyspnea", "dry cough", "dyspnea", "hypoxia", "elevated ldh", "hiv infection", "fever", "night sweats"
        ]
    },
    "icd10-b20-human-immunodeficiency-virus-hiv-with-pneumocystis-jirovecii-pneumonia": {
        "name": "Human immunodeficiency virus (HIV) with Pneumocystis jirovecii pneumonia",
        "hallmarks": [
            "pneumocystis pneumonia", "pneumocystis jirovecii pneumonia", "pcp", "pjp",
            "ground-glass opacities", "bilateral ground-glass opacities", "progressive exertional dyspnea",
            "exertional dyspnea", "dry cough", "dyspnea", "hypoxia", "elevated ldh", "hiv infection", "fever", "night sweats"
        ]
    }
}

# Update or insert
for d_id, data in CLINICAL_UPDATES.items():
    cur.execute("SELECT id, hallmarks_json, data_json FROM diseases WHERE id = ?", (d_id,))
    row = cur.fetchone()
    if row:
        curr_h = json.loads(row[1]) if row[1] else []
        curr_d = json.loads(row[2]) if row[2] else {}
        merged_h = list(set([h.lower().strip() for h in curr_h] + [h.lower().strip() for h in data["hallmarks"]]))
        curr_d["cardinal_symptoms"] = merged_h
        cur.execute("UPDATE diseases SET hallmarks_json = ?, data_json = ? WHERE id = ?", (json.dumps(merged_h), json.dumps(curr_d), d_id))
        print(f"Updated {d_id} ({data['name']}) -> {len(merged_h)} hallmarks")
    else:
        # Check if exists by name
        cur.execute("SELECT id, hallmarks_json, data_json FROM diseases WHERE name LIKE ?", (f"%{data['name']}%",))
        rows = cur.fetchall()
        for r in rows:
            curr_h = json.loads(r[1]) if r[1] else []
            curr_d = json.loads(r[2]) if r[2] else {}
            merged_h = list(set([h.lower().strip() for h in curr_h] + [h.lower().strip() for h in data["hallmarks"]]))
            curr_d["cardinal_symptoms"] = merged_h
            cur.execute("UPDATE diseases SET hallmarks_json = ?, data_json = ? WHERE id = ?", (json.dumps(merged_h), json.dumps(curr_d), r[0]))
            print(f"Updated by name {r[0]} ({data['name']}) -> {len(merged_h)} hallmarks")

# Now ensure Renal Infarction exists!
cur.execute("SELECT id FROM diseases WHERE id = 'expert-renal-infarction-n280'")
if not cur.fetchone():
    renal_hallmarks = [
        "renal infarction", "acute renal infarction", "wedge-shaped perfusion defect",
        "wedge shaped perfusion defect", "renal thromboembolism", "atrial fibrillation",
        "flank pain", "severe flank pain", "left flank pain", "microscopic hematuria",
        "hematuria", "elevated ldh", "absence of hydronephrosis", "irregularly irregular pulse"
    ]
    renal_data = {
        "cardinal_symptoms": renal_hallmarks,
        "immediate_tests": ["Contrast-enhanced CT abdomen/pelvis", "ECG", "Echocardiogram", "Serum LDH"],
        "recommended_medications": ["Anticoagulation (Heparin/DOAC)", "Analgesia"],
        "pearl": "Suspect acute renal infarction in patients with atrial fibrillation presenting with sudden severe flank pain, microscopic hematuria, and elevated LDH without urinary calculi."
    }
    cur.execute(
        """
        INSERT INTO diseases (id, name, icd10, icd11, orphacode, category, severity, triage, synonyms_json, hallmarks_json, data_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "expert-renal-infarction-n280",
            "Renal Infarction",
            "N28.0",
            "GB90",
            "ORPHA:0",
            "Vascular / Nephrology",
            "critical",
            "EMERGENT",
            json.dumps(["acute renal infarction", "infarction of kidney", "renal thromboembolism"]),
            json.dumps(renal_hallmarks),
            json.dumps(renal_data)
        )
    )
    print("Inserted expert-renal-infarction-n280 into catalog!")

# Also add ASCII Behcet disease alias
cur.execute("SELECT id FROM diseases WHERE id = 'behcet-disease-ascii-117'")
if not cur.fetchone():
    behcet_hallmarks = [
        "behcet disease", "behçet disease", "neuro-behcet", "oral ulcers", "mouth ulcers",
        "aphthous ulcers", "genital ulcers", "uveitis", "hypopyon", "pathergy test positive",
        "pathergy", "erythema nodosum", "intracranial arterial narrowing", "cerebral vasculitis"
    ]
    behcet_data = {
        "cardinal_symptoms": behcet_hallmarks,
        "immediate_tests": ["Pathergy test", "Brain MRI/MRA", "Slit-lamp examination", "HLA-B51"],
        "recommended_medications": ["Colchicine", "Systemic corticosteroids", "Immunosuppressants"],
        "pearl": "Behçet disease is a systemic vasculitis characterized by recurrent painful oral aphthae, genital ulcers, uveitis, and neurovascular involvement."
    }
    cur.execute(
        """
        INSERT INTO diseases (id, name, icd10, icd11, orphacode, category, severity, triage, synonyms_json, hallmarks_json, data_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "behcet-disease-ascii-117",
            "Behçet Disease",
            "M35.2",
            "4A44.0",
            "ORPHA:117",
            "Rheumatology / Ophthalmology",
            "high",
            "URGENT",
            json.dumps(["behcet disease", "behcets syndrome", "silk road disease"]),
            json.dumps(behcet_hallmarks),
            json.dumps(behcet_data)
        )
    )
    print("Inserted behcet-disease-ascii-117 into catalog!")

conn.commit()
conn.close()
print("Finished clinical updates to master_disease_catalog.db!")
