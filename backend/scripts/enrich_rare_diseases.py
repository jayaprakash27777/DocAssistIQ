import sqlite3
import json

db_path = r"D:\OFFLINE DATA\disease_catalog\master_disease_catalog.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# High-yield Orphanet / Medical Entity Clinical Manifestation Enrichment Map
CLINICAL_ENRICHMENTS = {
    "Fabry disease": [
        "acroparesthesia", "angiokeratoma", "hypohidrosis", "burning pain in hands and feet",
        "heat intolerance", "corneal verticillata", "proteinuria", "renal impairment"
    ],
    "Anderson-Fabry disease": [
        "acroparesthesia", "angiokeratoma", "hypohidrosis", "burning pain in hands and feet",
        "heat intolerance", "corneal verticillata", "proteinuria"
    ],
    "Idiopathic intracranial hypertension": [
        "papilledema", "pulsatile tinnitus", "transient visual obscurations", "headache",
        "pseudotumor cerebri", "elevated opening pressure", "visual disturbance"
    ],
    "Alport syndrome": [
        "sensorineural hearing loss", "microscopic hematuria", "proteinuria", "nephritis",
        "hearing loss", "kidney stones", "hematuria"
    ],
    "Behçet disease": [
        "oral ulcers", "genital ulcers", "uveitis", "hypopyon", "erythema nodosum",
        "pathergy", "retinal vasculitis", "mouth ulcers"
    ],
    "Behcet disease": [
        "oral ulcers", "genital ulcers", "uveitis", "hypopyon", "erythema nodosum",
        "pathergy", "retinal vasculitis", "mouth ulcers"
    ],
    "Carcinoid syndrome": [
        "carcinoid flush", "facial flushing", "secretory diarrhea", "diarrhea",
        "wheezing", "bronchospasm", "abdominal cramping", "tricuspid regurgitation"
    ],
    "Malignant carcinoid syndrome": [
        "carcinoid flush", "facial flushing", "secretory diarrhea", "diarrhea",
        "wheezing", "bronchospasm", "abdominal cramping"
    ],
    "Susac syndrome": [
        "encephalopathy", "branch retinal artery occlusion", "sensorineural hearing loss",
        "subacute confusion", "tinnitus", "hearing loss", "scotoma"
    ],
    "Neuromyelitis optica": [
        "optic neuritis", "longitudinally extensive transverse myelitis", "painful visual loss",
        "paraplegia", "sensory level", "urinary retention", "nmo", "aquaporin-4"
    ],
    "POEMS syndrome": [
        "polyneuropathy", "organomegaly", "endocrinopathy", "monoclonal protein",
        "skin changes", "peripheral edema", "hyperpigmentation", "papilledema"
    ],
    "Hereditary angioedema": [
        "angioedema", "laryngeal edema", "facial swelling", "abdominal pain",
        "c1 esterase inhibitor deficiency", "recurrent swelling without urticaria"
    ],
    "Gaucher disease type 1": [
        "splenomegaly", "hepatomegaly", "enlarged spleen", "thrombocytopenia",
        "anemia", "bone pain", "erlenmeyer flask deformity", "easy bruising"
    ],
    "MELAS": [
        "stroke-like cortical lesions", "exercise intolerance", "muscle weakness",
        "sensorineural hearing loss", "lactic acidosis", "seizures", "headache", "vomiting"
    ],
    "Mitochondrial encephalomyopathy, lactic acidosis, and stroke-like episodes": [
        "stroke-like cortical lesions", "exercise intolerance", "muscle weakness",
        "sensorineural hearing loss", "lactic acidosis", "seizures", "headache", "vomiting"
    ],
    "Paroxysmal nocturnal hemoglobinuria": [
        "hemoglobinuria", "cola-colored urine", "intravascular hemolysis",
        "venous thrombosis", "fatigue", "anemia", "thrombocytopenia", "abdominal pain"
    ],
    "Babesiosis": [
        "hemolytic anemia", "fever", "chills", "drenching sweats", "fatigue",
        "jaundice", "dark urine", "thrombocytopenia", "tick bite", "maltese cross"
    ],
    "Strongyloidiasis": [
        "larva currens", "eosinophilia", "watery diarrhea", "wheezing",
        "abdominal pain", "pulmonary infiltrates", "hyperinfection", "corticosteroid use"
    ],
    "Whipple disease": [
        "migratory arthralgias", "chronic diarrhea", "malabsorption", "weight loss",
        "abdominal pain", "lymphadenopathy", "tropheryma whipplei"
    ],
    "Eosinophilic esophagitis": [
        "dysphagia", "food impaction", "heartburn refractory to ppi", "chest pain",
        "esophageal rings", "esophageal furrows"
    ],
    "Achalasia": [
        "dysphagia to solids and liquids", "dysphagia", "regurgitation", "weight loss",
        "nocturnal cough", "chest pain", "birds beak sign"
    ],
    "Primary sclerosing cholangitis": [
        "pruritus", "itching", "fatigue", "jaundice", "elevated alkaline phosphatase",
        "inflammatory bowel disease", "ulcerative colitis", "beaded bile ducts"
    ],
}

count = 0
for target_name, hallmarks_to_add in CLINICAL_ENRICHMENTS.items():
    cur.execute("SELECT id, name, hallmarks_json, data_json FROM diseases WHERE name = ? OR name LIKE ?", (target_name, f"%{target_name}%"))
    rows = cur.fetchall()
    for row in rows:
        d_id = row[0]
        curr_hallmarks = json.loads(row[2]) if row[2] else []
        curr_data = json.loads(row[3]) if row[3] else {}
        
        # Merge hallmarks
        new_hallmarks = list(set([h.lower().strip() for h in curr_hallmarks] + [h.lower().strip() for h in hallmarks_to_add]))
        curr_cardinals = curr_data.get("cardinal_symptoms", [])
        new_cardinals = list(set([c.lower().strip() for c in curr_cardinals] + [h.lower().strip() for h in hallmarks_to_add]))
        curr_data["cardinal_symptoms"] = new_cardinals
        
        cur.execute("UPDATE diseases SET hallmarks_json = ?, data_json = ? WHERE id = ?", (json.dumps(new_hallmarks), json.dumps(curr_data), d_id))
        count += 1
        print(f"Enriched: {row[1]} -> {len(new_hallmarks)} hallmarks")

conn.commit()
conn.close()
print(f"Total diseases enriched with real clinical manifestations: {count}")
