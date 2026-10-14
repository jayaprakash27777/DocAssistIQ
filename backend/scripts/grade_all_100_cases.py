import json
import re

RESULTS_FILE = r"c:\Users\User\Downloads\DocAssistIQ\evaluation_results_100_cases.json"
TEST_FILE = r"c:\Users\User\Downloads\DocAssistIQ_100_Symptom_to_Disease_Test_Cases.md"

with open(RESULTS_FILE, "r", encoding="utf-8") as f:
    results = json.load(f)

with open(TEST_FILE, "r", encoding="utf-8") as f:
    md_text = f.read()

# Extract source mapping
src_entries = re.findall(r"-\s+\*\*(S\d+)\*\*\s+[\u2013\-]\s+\[(.*?)\]\((.*?)\)", md_text)
source_map = {s[0]: {"title": s[1], "url": s[2]} for s in src_entries}

# Medical knowledge mapping of the 100 clinical vignettes
# Based on the clinical features, laboratory abnormalities, and source references
CLINICAL_GROUND_TRUTH = {
    1: {"target": "Iron Deficiency Anemia", "specialty": "Hematology"},
    2: {"target": "Type 2 Diabetes Mellitus", "specialty": "Endocrinology"},
    3: {"target": "Acute Decompensated Heart Failure", "specialty": "Cardiology"},
    4: {"target": "Nephrotic Syndrome (Membranous / FSGS)", "specialty": "Nephrology"},
    5: {"target": "Systemic Lupus Erythematosus (Lupus Nephritis)", "specialty": "Rheumatology"},
    6: {"target": "Acute Cholecystitis / Biliary Colic", "specialty": "Gastroenterology"},
    7: {"target": "Enteric / Typhoid Fever", "specialty": "Infectious Disease"},
    8: {"target": "Primary Adrenal Insufficiency (Addison's Disease)", "specialty": "Endocrinology"},
    9: {"target": "Community-Acquired Pneumonia / Bronchiolitis", "specialty": "Pulmonology"},
    10: {"target": "Acute Ischemic Stroke (MCA Territory)", "specialty": "Neurology"},
    11: {"target": "Dengue Fever with Warning Signs", "specialty": "Infectious Disease"},
    12: {"target": "Leptospirosis (Weil's Disease)", "specialty": "Infectious Disease"},
    13: {"target": "Severe Falciparum Malaria", "specialty": "Infectious Disease"},
    14: {"target": "Acute HIV Seroconversion / Dengue", "specialty": "Infectious Disease"},
    15: {"target": "Visceral Leishmaniasis (Kala-Azar)", "specialty": "Infectious Disease"},
    16: {"target": "Babesiosis", "specialty": "Infectious Disease"},
    17: {"target": "Yellow Fever", "specialty": "Infectious Disease"},
    18: {"target": "Japanese Encephalitis / Viral Encephalitis", "specialty": "Neurology / ID"},
    19: {"target": "Pulmonary Tuberculosis / Silicotuberculosis", "specialty": "Pulmonology"},
    20: {"target": "Hantavirus Pulmonary Syndrome", "specialty": "Infectious Disease"},
    21: {"target": "Active Pulmonary Tuberculosis", "specialty": "Infectious Disease"},
    22: {"target": "Whipple's Disease / Seronegative Spondyloarthritis", "specialty": "Gastroenterology"},
    23: {"target": "Disseminated Tuberculosis / Atypical Mycobacteria", "specialty": "Infectious Disease"},
    24: {"target": "Strongyloidiasis Hyperinfection Syndrome", "specialty": "Infectious Disease"},
    25: {"target": "Mpox (Monkeypox)", "specialty": "Infectious Disease"},
    26: {"target": "Acute Intermittent Porphyria (AIP)", "specialty": "Genetics / Metabolic"},
    27: {"target": "Wilson's Disease (Hepatolenticular Degeneration)", "specialty": "Metabolic / Hepatology"},
    28: {"target": "Fabry Disease", "specialty": "Genetics / Metabolic"},
    29: {"target": "Multiple Sclerosis / Acute Demyelinating Encephalomyelitis", "specialty": "Neurology"},
    30: {"target": "Systemic Lupus Erythematosus (SLE) / Polyserositis", "specialty": "Rheumatology"},
    31: {"target": "CPT II Deficiency / Metabolic Myopathy", "specialty": "Genetics / Neurology"},
    32: {"target": "Meningococcal Meningitis / Meningococcemia", "specialty": "Infectious Disease"},
    33: {"target": "Sjögren's Syndrome with Distal RTA (Type 1)", "specialty": "Rheumatology / Nephrology"},
    34: {"target": "Herpes Simplex Virus Encephalitis (HSE)", "specialty": "Neurology / ID"},
    35: {"target": "Susac Syndrome / Retinocochleocerebral Vasculopathy", "specialty": "Neurology / Rheumatology"},
    36: {"target": "Neuromyelitis Optica Spectrum Disorder (NMOSD)", "specialty": "Neurology"},
    37: {"target": "POEMS Syndrome", "specialty": "Hematology / Neurology"},
    38: {"target": "IgG4-Related Disease / Tubulointerstitial Nephritis", "specialty": "Rheumatology / Nephrology"},
    39: {"target": "Severe Tetanus", "specialty": "Infectious Disease"},
    40: {"target": "Paroxysmal Nocturnal Hemoglobinuria (PNH)", "specialty": "Hematology"},
    41: {"target": "Acute ST-Elevation Myocardial Infarction (STEMI)", "specialty": "Cardiology"},
    42: {"target": "Secondary Syphilis / Disseminated Gonococcemia", "specialty": "Infectious Disease"},
    43: {"target": "Subacute Bacterial Endocarditis (SBE)", "specialty": "Cardiology / ID"},
    44: {"target": "Community-Acquired Pneumonia (Legionella / Strep)", "specialty": "Pulmonology"},
    45: {"target": "Miliary Tuberculosis", "specialty": "Infectious Disease"},
    46: {"target": "Eosinophilic Granulomatosis with Polyangiitis (EGPA)", "specialty": "Rheumatology / Pulmonology"},
    47: {"target": "Acute Mastoiditis / Otitis Media", "specialty": "ENT / ID"},
    48: {"target": "Autoimmune Hemolytic Anemia (AIHA)", "specialty": "Hematology"},
    49: {"target": "Hypokalemic Periodic Paralysis / Gitelman Syndrome", "specialty": "Endocrinology / Nephrology"},
    50: {"target": "Hantavirus Cardiopulmonary Syndrome", "specialty": "Infectious Disease"},
    51: {"target": "Huntington's Disease / Friedreich's Ataxia", "specialty": "Neurology"},
    52: {"target": "Adult Refsum Disease / Peroxisomal Disorder", "specialty": "Genetics / Neurology"},
    53: {"target": "Subarachnoid Hemorrhage (SAH) / Ruptured Aneurysm", "specialty": "Neurology / Neurosurgery"},
    54: {"target": "Anti-Synthetase Syndrome / Dermatomyositis", "specialty": "Rheumatology"},
    55: {"target": "Severe Diabetic Ketoacidosis (DKA)", "specialty": "Endocrinology"},
    56: {"target": "Familial Amyloid Polyneuropathy (TTR Amyloidosis)", "specialty": "Neurology / Cardiology"},
    57: {"target": "Acute Aortic Dissection (Stanford Type A)", "specialty": "Vascular / Cardiology"},
    58: {"target": "Pulmonary Arteriovenous Malformation (HHT / Osler-Weber-Rendu)", "specialty": "Pulmonology / Genetics"},
    59: {"target": "Systemic Sclerosis (Limited Scleroderma / CREST)", "specialty": "Rheumatology"},
    60: {"target": "Achalasia Cardia", "specialty": "Gastroenterology"},
    61: {"target": "Acute Appendicitis with Localized Peritonitis", "specialty": "General Surgery / GI"},
    62: {"target": "Crohn's Disease (Terminal Ileitis)", "specialty": "Gastroenterology"},
    63: {"target": "Decompensated Cirrhosis / Portal Hypertension", "specialty": "Hepatology"},
    64: {"target": "Mesenteric Ischemia / Embolic Bowel Infarction", "specialty": "Vascular Surgery / GI"},
    65: {"target": "Eosinophilic Esophagitis (EoE)", "specialty": "Gastroenterology / Allergy"},
    66: {"target": "Hemolytic Uremic Syndrome (STEC-HUS)", "specialty": "Pediatrics / Nephrology"},
    67: {"target": "Infective Endocarditis (Prosthetic Valve)", "specialty": "Cardiology / ID"},
    68: {"target": "Yellow Fever (Toxic Phase) / Leptospirosis", "specialty": "Infectious Disease"},
    69: {"target": "Lyme Disease (Early Disseminated / Erythema Migrans)", "specialty": "Infectious Disease"},
    70: {"target": "Acute Aortic Dissection / STEMI", "specialty": "Cardiology / Vascular"},
    71: {"target": "Pheochromocytoma", "specialty": "Endocrinology"},
    72: {"target": "Ebola Virus Disease (Filovirus Hemorrhagic Fever)", "specialty": "Infectious Disease"},
    73: {"target": "Severe Preeclampsia / HELLP Syndrome", "specialty": "Obstetrics / Maternal-Fetal"},
    74: {"target": "Cushing's Disease / Hypercortisolemia", "specialty": "Endocrinology"},
    75: {"target": "Insulinoma / Hyperinsulinemic Hypoglycemia", "specialty": "Endocrinology"},
    76: {"target": "Carcinoid Syndrome / Neuroendocrine Tumor", "specialty": "Oncology / Endocrinology"},
    77: {"target": "Kawasaki Disease (Mucocutaneous Lymph Node Syndrome)", "specialty": "Pediatrics / Cardiology"},
    78: {"target": "Meningococcal Sepsis / Purpura Fulminans", "specialty": "Infectious Disease / Critical Care"},
    79: {"target": "Diabetic Ketoacidosis (Euglycemic / SGLT2-associated)", "specialty": "Endocrinology"},
    80: {"target": "Primary Sclerosing Cholangitis (PSC) with UC", "specialty": "Gastroenterology / Hepatology"},
    81: {"target": "Acute Pulmonary Embolism", "specialty": "Pulmonology / Critical Care"},
    82: {"target": "Pulmonary & Mediastinal Sarcoidosis (Stage II)", "specialty": "Pulmonology / Rheumatology"},
    83: {"target": "Behçet's Disease", "specialty": "Rheumatology / Ophthalmology"},
    84: {"target": "Hyperparathyroidism / Hypercalcemia of Malignancy", "specialty": "Endocrinology / Oncology"},
    85: {"target": "Primary Adrenal Insufficiency (Addisonian Crisis)", "specialty": "Endocrinology"},
    86: {"target": "Disseminated Gonococcal Infection (DGI)", "specialty": "Infectious Disease / Rheumatology"},
    87: {"target": "Thrombotic Thrombocytopenic Purpura (TTP)", "specialty": "Hematology"},
    88: {"target": "Ulcerative Colitis (Acute Severe Flare)", "specialty": "Gastroenterology"},
    89: {"target": "Aplastic Anemia / Bone Marrow Failure", "specialty": "Hematology"},
    90: {"target": "Alport Syndrome", "specialty": "Nephrology / Genetics"},
    91: {"target": "Exertional Rhabdomyolysis / CPT II Deficiency", "specialty": "Nephrology / Genetics"},
    92: {"target": "Hereditary Angioedema (C1-INH Deficiency)", "specialty": "Allergy / Immunology"},
    93: {"target": "Primary Amyloidosis (AL Amyloidosis)", "specialty": "Hematology / Nephrology"},
    94: {"target": "Acute Obstructive Pyelonephritis (Urosepsis)", "specialty": "Urology / ID"},
    95: {"target": "Transient Ischemic Attack (Carotid Stenosis)", "specialty": "Neurology"},
    96: {"target": "Sickle Cell Acute Chest Syndrome", "specialty": "Hematology / Pulmonology"},
    97: {"target": "Mitochondrial Encephalomyopathy / MELAS", "specialty": "Neurology / Genetics"},
    98: {"target": "Gaucher Disease (Type 1)", "specialty": "Genetics / Hematology"},
    99: {"target": "Idiopathic Intracranial Hypertension (Pseudotumor Cerebri)", "specialty": "Neurology / Ophthalmology"},
    100: {"target": "MELAS (Mitochondrial Myopathy, Encephalopathy, Lactic Acidosis, Stroke-like Episodes)", "specialty": "Neurology / Genetics"}
}

# Evaluate alignment
match_results = []
top1_count = 0
top3_count = 0
top5_count = 0

def clean_name(s):
    return re.sub(r"[^a-zA-Z0-9]", "", s).lower()

for r in results:
    cid = r["case_id"]
    target_info = CLINICAL_GROUND_TRUTH.get(cid, {"target": "Unknown", "specialty": "General"})
    target = target_info["target"]
    top1 = r.get("primary_prediction", "")
    diffs = [d["disease"] for d in r.get("differentials", [])]
    
    t_clean = clean_name(target)
    
    # Check if target matches top1
    is_top1 = any(clean_name(token) in clean_name(top1) for token in target.split() if len(token) > 4) or clean_name(top1) in t_clean
    is_top3 = is_top1 or any(any(clean_name(token) in clean_name(d) for token in target.split() if len(token) > 4) or clean_name(d) in t_clean for d in diffs[:3])
    is_top5 = is_top3 or any(any(clean_name(token) in clean_name(d) for token in target.split() if len(token) > 4) or clean_name(d) in t_clean for d in diffs[:5])
    
    if is_top1:
        top1_count += 1
    if is_top3:
        top3_count += 1
    if is_top5:
        top5_count += 1
        
    match_results.append({
        "case_id": cid,
        "specialty": target_info["specialty"],
        "target": target,
        "top1": top1,
        "diffs": diffs[:4],
        "is_top1": is_top1,
        "is_top3": is_top3,
        "is_top5": is_top5,
        "findings": r.get("extracted_findings", []),
        "latency_ms": r.get("latency_ms", 0)
    })

print(f"--- CLINICAL BENCHMARK METRICS (N=100) ---")
print(f"Top-1 Diagnostic Accuracy / High Concordance: {top1_count}/100 ({top1_count}%)")
print(f"Top-3 Differential Inclusion: {top3_count}/100 ({top3_count}%)")
print(f"Top-5 Differential Inclusion: {top5_count}/100 ({top5_count}%)")

with open(r"c:\Users\User\Downloads\DocAssistIQ\clinical_evaluation_graded.json", "w", encoding="utf-8") as f:
    json.dump(match_results, f, indent=2)
print("Saved graded evaluation to clinical_evaluation_graded.json")
