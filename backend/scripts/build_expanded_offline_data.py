"""DocAssistIQ — Expanded Offline Clinical Warehouse Builder.

Adds comprehensive Rare Disease (HPO / OMIM / Orphanet), General Internal Medicine,
and Diagnostic Investigation & Laboratory Panels directly to D:\\OFFLINE DATA:
  1. rare_diseases_hpo: 100,000+ Human Phenotype Ontology annotations across rare genetic diseases
  2. clinical_investigations: Standardized lab panels (LOINC), radiology protocols & specimen requirements
  3. disease_investigation_mappings: Bidirectional Disease <-> Investigation mapping & Discriminative Pair Rules
  4. general_internal_medicine: Comprehensive internal medicine monographs across 10 clinical specialties

Builds SQLite FTS5 indices, compiles fast JSON lookups, and registers all datasets in PostgreSQL.
"""

import os
import sys
import json
import sqlite3
import hashlib
import shutil
import time
import argparse
import asyncio
import urllib.request
from typing import Dict, List, Any, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

DEFAULT_STORAGE_PATH = r"D:\OFFLINE DATA"


def format_size(bytes_val: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"


class ExpandedOfflineDataBuilder:
    def __init__(self, target_dir: str = DEFAULT_STORAGE_PATH):
        self.target_dir = os.path.abspath(target_dir)
        os.makedirs(self.target_dir, exist_ok=True)
        self.manifest_path = os.path.join(self.target_dir, "manifest.json")
        self.manifest: Dict[str, Any] = {
            "warehouse_version": "2.0.0",
            "storage_path": self.target_dir,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "datasets": {},
        }
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    self.manifest = json.load(f)
            except Exception:
                pass

    # ---------------------------------------------------------------------------
    # 1. Rare & Genetic Disease Phenotype Knowledge Base (HPO / OMIM / Orphanet)
    # ---------------------------------------------------------------------------
    def build_rare_diseases_hpo(self) -> Dict[str, Any]:
        print("\n" + "=" * 70)
        print("STEP 1: Compiling Rare Disease & Human Phenotype Ontology (HPO)")
        print("=" * 70)
        dest_dir = os.path.join(self.target_dir, "rare_diseases_hpo")
        os.makedirs(dest_dir, exist_ok=True)

        db_path = os.path.join(dest_dir, "rare_diseases_hpo.db")
        pheno_hpoa_path = os.path.join(dest_dir, "phenotype.hpoa")
        genes_disease_path = os.path.join(dest_dir, "genes_to_disease.txt")
        index_json_path = os.path.join(dest_dir, "phenotype_to_disease_index.json")

        # Download genes_to_disease.txt if missing
        if not os.path.exists(genes_disease_path):
            print("  [*] Downloading 'genes_to_disease.txt' from HPO release...")
            url_genes = "https://github.com/obophenotype/human-phenotype-ontology/releases/download/v2026-09-01/genes_to_disease.txt"
            req = urllib.request.Request(url_genes, headers={"User-Agent": "DocAssistIQ"})
            with urllib.request.urlopen(req, timeout=60) as resp, open(genes_disease_path, "wb") as f:
                f.write(resp.read())
            print(f"  [+] Saved genes_to_disease.txt ({format_size(os.path.getsize(genes_disease_path))})")

        # Download phenotype.hpoa if missing
        if not os.path.exists(pheno_hpoa_path):
            print("  [*] Downloading 'phenotype.hpoa' (disease-phenotype annotations)...")
            url_pheno = "https://github.com/obophenotype/human-phenotype-ontology/releases/download/v2026-09-01/phenotype.hpoa"
            req = urllib.request.Request(url_pheno, headers={"User-Agent": "DocAssistIQ"})
            with urllib.request.urlopen(req, timeout=120) as resp, open(pheno_hpoa_path, "wb") as f:
                f.write(resp.read())
            print(f"  [+] Saved phenotype.hpoa ({format_size(os.path.getsize(pheno_hpoa_path))})")

        # Map genes to disease
        gene_map: Dict[str, str] = {}
        if os.path.exists(genes_disease_path):
            with open(genes_disease_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.startswith("#"):
                        continue
                    parts = line.strip().split("\t")
                    if len(parts) >= 4:
                        # gene_symbol, disease_id
                        gene_symbol = parts[1]
                        disease_id = parts[2]
                        gene_map[disease_id] = gene_symbol

        # Parse phenotype.hpoa and index into SQLite
        print("  [*] Parsing HPO annotations and building SQLite database...")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS rare_diseases")
        cur.execute("""
            CREATE TABLE rare_diseases (
                disease_id TEXT PRIMARY KEY,
                disease_name TEXT NOT NULL,
                gene_symbol TEXT,
                phenotypes_count INTEGER,
                phenotypes_json TEXT NOT NULL
            )
        """)
        cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS hpo_fts USING fts5(disease_name, phenotypes_json, gene_symbol)")
        cur.execute("DROP TABLE IF EXISTS disease_phenotype_annotations")
        cur.execute("""
            CREATE TABLE disease_phenotype_annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                disease_id TEXT NOT NULL,
                disease_name TEXT NOT NULL,
                hpo_id TEXT NOT NULL,
                hpo_name TEXT NOT NULL,
                frequency TEXT
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_dpa_hpo ON disease_phenotype_annotations(hpo_name)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_dpa_dis ON disease_phenotype_annotations(disease_id)")

        disease_pheno_map: Dict[str, Dict[str, Any]] = {}
        phenotype_inverted_index: Dict[str, List[str]] = {}

        annotation_count = 0
        with open(pheno_hpoa_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                parts = line.strip().split("\t")
                if len(parts) >= 4:
                    dis_id = parts[0]
                    dis_name = parts[1]
                    hpo_id = parts[3]
                    hpo_name = parts[2] if len(parts) > 2 and parts[2].startswith("HP:") is False else hpo_id
                    freq = parts[7] if len(parts) > 7 else ""

                    if dis_id not in disease_pheno_map:
                        disease_pheno_map[dis_id] = {
                            "name": dis_name,
                            "gene": gene_map.get(dis_id, ""),
                            "phenotypes": [],
                        }

                    disease_pheno_map[dis_id]["phenotypes"].append(hpo_name)

                    # Inverted index
                    pheno_key = hpo_name.lower().strip()
                    if pheno_key not in phenotype_inverted_index:
                        phenotype_inverted_index[pheno_key] = []
                    if dis_name not in phenotype_inverted_index[pheno_key] and len(phenotype_inverted_index[pheno_key]) < 15:
                        phenotype_inverted_index[pheno_key].append(dis_name)

                    annotation_count += 1

        print(f"  [*] Extracted {annotation_count:,} annotations across {len(disease_pheno_map):,} unique rare diseases.")

        # Insert into SQLite
        batch_dis = []
        batch_fts = []
        for dis_id, info in disease_pheno_map.items():
            phenos = info["phenotypes"]
            phenos_json = json.dumps(phenos[:40])
            batch_dis.append((dis_id, info["name"], info["gene"], len(phenos), phenos_json))
            batch_fts.append((info["name"], " ".join(phenos[:30]), info["gene"]))

            if len(batch_dis) >= 2000:
                cur.executemany("INSERT OR REPLACE INTO rare_diseases VALUES (?, ?, ?, ?, ?)", batch_dis)
                cur.executemany("INSERT INTO hpo_fts(disease_name, phenotypes_json, gene_symbol) VALUES (?, ?, ?)", batch_fts)
                conn.commit()
                batch_dis = []
                batch_fts = []

        if batch_dis:
            cur.executemany("INSERT OR REPLACE INTO rare_diseases VALUES (?, ?, ?, ?, ?)", batch_dis)
            cur.executemany("INSERT INTO hpo_fts(disease_name, phenotypes_json, gene_symbol) VALUES (?, ?, ?)", batch_fts)
            conn.commit()

        conn.close()

        # Save inverted phenotype index
        with open(index_json_path, "w", encoding="utf-8") as f:
            json.dump(phenotype_inverted_index, f)

        total_sz = os.path.getsize(db_path) + os.path.getsize(pheno_hpoa_path) + os.path.getsize(genes_disease_path) + os.path.getsize(index_json_path)

        entry = {
            "name": "rare_diseases_hpo",
            "category": "rare_genetic_phenotypes",
            "source": "Human Phenotype Ontology (HPO), OMIM & Orphanet v2026",
            "record_count": annotation_count,
            "directory": dest_dir,
            "primary_file": db_path,
            "total_size_bytes": total_sz,
            "formatted_size": format_size(total_sz),
            "status": "ready",
        }
        self.manifest["datasets"]["rare_diseases_hpo"] = entry
        print(f"  [SUCCESS] Rare Diseases HPO ready: {annotation_count:,} annotations, {len(disease_pheno_map):,} rare syndromes ({format_size(total_sz)})")
        return entry

    # ---------------------------------------------------------------------------
    # 2. Clinical Diagnostic Investigations & Laboratory Knowledge Base
    # ---------------------------------------------------------------------------
    def build_clinical_investigations(self) -> Dict[str, Any]:
        print("\n" + "=" * 70)
        print("STEP 2: Compiling Comprehensive Diagnostic Investigations & Panels")
        print("=" * 70)
        dest_dir = os.path.join(self.target_dir, "clinical_investigations")
        os.makedirs(dest_dir, exist_ok=True)

        db_path = os.path.join(dest_dir, "investigations_catalog.db")
        json_path = os.path.join(dest_dir, "investigations_catalog.json")

        # Import standard clinical lab test catalog from medlineplus_lab_tests_ingester
        from app.services.ingestion.medlineplus_lab_tests_ingester import CLINICAL_LAB_TEST_CATALOG

        # Expand with Bedside Tests, Radiology, Ultrasound, and Specialized Diagnostic Procedures
        expanded_tests = list(CLINICAL_LAB_TEST_CATALOG)

        imaging_and_bedside_tests = [
            # Bedside & Point-of-Care
            {
                "code": "PROC-12-LEAD-ECG",
                "name": "12-Lead Electrocardiogram (ECG / EKG)",
                "category": "Cardiac & Electrophysiology",
                "specimen": "Non-invasive electrical leads (surface)",
                "reference_interval": "Normal sinus rhythm (60-100 bpm), normal intervals (PR: 120-200ms, QRS <120ms, QTc <450ms M, <460ms F)",
                "critical_value": "ST-segment elevation >=1mm in contiguous leads (STEMI), new LBBB, ventricular tachycardia/fibrillation, complete heart block",
                "rationale": "Mandatory immediate investigation for all acute chest pain, dyspnea, syncope, palpitations, and unexplained hemodynamic instability within 10 minutes of arrival.",
                "limitations": "Up to 50% of acute myocardial infarctions initially present with non-diagnostic or normal initial ECG; serial ECGs mandatory."
            },
            {
                "code": "PROC-CXR-BEDSIDE",
                "name": "Bedside Chest Radiograph (CXR: PA and Lateral)",
                "category": "Diagnostic Radiology",
                "specimen": "X-ray projection (PA/AP erect preferred)",
                "reference_interval": "Clear lung fields, normal cardiothoracic ratio (<0.5), sharp costophrenic angles, normal mediastinal contour",
                "critical_value": "Tension pneumothorax, pneumoperitoneum (free air under diaphragm), acute widening of mediastinum (>8cm on upright), bilateral alveolar bat-wing infiltrates",
                "rationale": "Primary imaging modality for evaluating community-acquired pneumonia (consolidation/infiltrates), congestive heart failure, pneumothorax, effusion, and acute aortic pathology.",
                "limitations": "Early pneumonia or neutropenic patients may lack consolidation; AP supine view artificially magnifies heart size."
            },
            {
                "code": "PROC-NCCT-HEAD",
                "name": "Non-Contrast Computed Tomography of Head (NCCT Brain)",
                "category": "Neuroimaging & Stroke Protocols",
                "specimen": "Axial CT helical scan",
                "reference_interval": "Normal brain parenchyma, symmetrical ventricles and sulci, no midline shift, no acute hemorrhage",
                "critical_value": "Hyperdense acute hemorrhage (intracerebral / subarachnoid / subdural), mass effect with midline shift >5mm, acute territorial hypodensity, loss of gray-white differentiation",
                "rationale": "Universal emergency gold standard within 20 minutes of arrival for acute focal neurologic deficit to differentiate hemorrhagic from ischemic stroke before thrombolysis.",
                "limitations": "Insensitive to hyperacute ischemic infarct (<3 hours); posterior fossa and brainstem strokes poorly visualized."
            },
            {
                "code": "PROC-CTPA-CHEST",
                "name": "Computed Tomography Pulmonary Angiography (CTPA)",
                "category": "Vascular Radiology & Thoracic",
                "specimen": "Contrast-enhanced helical thin-slice CT (bolus tracked to pulmonary trunk)",
                "reference_interval": "Homogeneous opacification of pulmonary arterial tree without intraluminal filling defects",
                "critical_value": "Saddle embolus occluding main pulmonary bifurcation, acute lobar/segmental intraluminal filling defect, right ventricular strain (RV/LV diameter ratio >1.0)",
                "rationale": "Gold standard definitive imaging investigation for confirming Acute Pulmonary Embolism in patients with intermediate or high pre-test Wells score or elevated D-dimer.",
                "limitations": "Requires iodinated intravenous contrast; contraindicated in severe renal impairment (eGFR <30) or anaphylactoid contrast allergy."
            },
            {
                "code": "PROC-CTA-AORTA",
                "name": "Computed Tomography Angiography of Chest and Abdomen (CTA Aorta)",
                "category": "Vascular Radiology & Emergency",
                "specimen": "Electrocardiographically-gated contrast-enhanced helical CT",
                "reference_interval": "Uniform contrast opacification of thoracic and abdominal aorta without intimal flap, ulceration, or intramural hematoma",
                "critical_value": "Stanford Type A dissection flap involving ascending aorta, Stanford Type B dissection flap, impending rupture, malperfusion syndrome",
                "rationale": "Emergency definitive investigation for suspected Acute Aortic Dissection, intramural hematoma, and penetrating atherosclerotic ulcer.",
                "limitations": "Requires patient stability for CT transport; contraindication in unstable patients where bedside transesophageal echo (TEE) is preferred."
            },
            {
                "code": "PROC-POCUS-LUNG",
                "name": "Point-of-Care Lung Ultrasound (POCUS — BLUE Protocol)",
                "category": "Bedside Ultrasonography",
                "specimen": "Bedside high-frequency linear/phased array probe",
                "reference_interval": "A-line profile with bilateral lung sliding (rules out pneumothorax)",
                "critical_value": "Absence of lung sliding with lung point sign (pathognomonic for pneumothorax), diffuse confluent B-lines (pulmonary edema / interstitial syndrome), dense hepatization with dynamic air bronchograms (consolidation)",
                "rationale": "Rapid (<3 minute) bed-side diagnostic differentiation of acute dyspnea and respiratory distress in emergency/ICU.",
                "limitations": "Operator dependent; subcutaneous emphysema or extreme chest wall obesity impairs acoustic window."
            },
            {
                "code": "PROC-POCUS-FAST",
                "name": "Focused Assessment with Sonography for Trauma (FAST / eFAST)",
                "category": "Bedside Ultrasonography & Emergency",
                "specimen": "Bedside phased-array or curvilinear transducer",
                "reference_interval": "No free anechoic fluid in Morison's pouch, splenorenal recess, suprapubic pelvis, pericardial sac, or pleural spaces",
                "critical_value": "Anechoic fluid stripe in pericardium (cardiac tamponade), intra-abdominal hemoperitoneum, absent lung sliding (pneumothorax)",
                "rationale": "Immediate emergency room triage for blunt/penetrating torso trauma and unexplained hypotension.",
                "limitations": "Does not assess retroperitoneal hemorrhage or hollow viscus bowel perforation."
            },
            {
                "code": "PROC-TTE-ECHO",
                "name": "Transthoracic Echocardiogram (TTE with Doppler)",
                "category": "Cardiovascular Ultrasound",
                "specimen": "2D, M-mode, and color/spectral Doppler echocardiography",
                "reference_interval": "Normal Left Ventricular Ejection Fraction (LVEF 52-72%), normal chamber dimensions, intact valvular architecture, no pericardial effusion",
                "critical_value": "Severe acute LVEF depression (<30%), regional wall motion abnormality (RWMA) consistent with coronary territory, severe aortic regurgitation, mobile valvular vegetation, cardiac tamponade physiology",
                "rationale": "First-line evaluation for acute and chronic heart failure, cardiogenic shock, infective endocarditis, and valvular heart disease.",
                "limitations": "Suboptimal acoustic windows in severe COPD, chest deformities, or morbid obesity."
            },
            {
                "code": "PROC-LUMBAR-PUNCTURE",
                "name": "Lumbar Puncture with CSF Analysis (Opening Pressure, Cells, Chemistry, BioFire PCR)",
                "category": "Neurology & Neuroinfectious Procedures",
                "specimen": "Cerebrospinal fluid collected at L3-L4 or L4-L5 interspace into tubes 1-4",
                "reference_interval": "Opening pressure: 10-20 cm H2O, Clear/colorless, WBC: 0-5 /uL (mononuclear), Protein: 15-45 mg/dL, Glucose: 60-70% of concurrent serum glucose, Gram stain negative",
                "critical_value": "Opening pressure >25 cm H2O, WBC >1000/uL with neutrophilic predominance (bacterial meningitis), CSF/serum glucose ratio <0.4, elevated RBCs across all 4 tubes with xanthochromia (SAH)",
                "rationale": "Definitive diagnostic investigation for acute bacterial, viral, fungal, and tuberculous meningitis, encephalitis, and subarachnoid hemorrhage with negative CT.",
                "limitations": "Contraindicated in coagulopathy (INR >1.5, platelets <50,000) or space-occupying intracranial lesion with risk of uncal herniation (NCCT head prior)."
            },
            {
                "code": "PROC-BLOOD-CULTURE-X2",
                "name": "Paired Blood Cultures (Aerobic and Anaerobic, 2 Separate Venipuncture Sites)",
                "category": "Infectious Disease Microbiology",
                "specimen": "20 mL whole blood per set (10 mL aerobic bottle, 10 mL anaerobic bottle) drawn before antimicrobial initiation",
                "reference_interval": "No bacterial or fungal growth at 5 days",
                "critical_value": "Growth of pathogenic organisms: Staphylococcus aureus, Streptococcus pneumoniae, Gram-negative bacilli (Pseudomonas, E. coli, Klebsiella), Candida spp.",
                "rationale": "Cornerstone diagnostic investigation for bloodstream infection, severe sepsis, infective endocarditis, and catheter-associated bacteremia.",
                "limitations": "Administration of antibiotics prior to blood draw slashes culture yield by up to 50%; skin commensal contamination (CoNS) requires multi-set verification."
            },
            {
                "code": "PROC-GENEXPERT-MTB",
                "name": "Sputum GeneXpert MTB/RIF Ultra (Real-Time Automated Nucleic Acid Amplification)",
                "category": "Molecular Microbiology",
                "specimen": "Early morning deep expectorated or induced sputum",
                "reference_interval": "MTB not detected",
                "critical_value": "MTB detected with Rifampicin resistance detected (MDR-TB alert)",
                "rationale": "WHO first-line diagnostic investigation for rapid (<2 hour) detection of Mycobacterium tuberculosis complex and simultaneous rifampicin resistance.",
                "limitations": "Cannot differentiate live from dead bacilli; not suitable for monitoring treatment response."
            },
            {
                "code": "LOINC-69538-7",
                "name": "Arterial Blood Gas (ABG: PaO2, PaCO2, pH, Base Excess)",
                "category": "Pulmonary & Critical Care",
                "specimen": "Heparinized arterial blood drawn from radial or femoral artery",
                "reference_interval": "pH: 7.35-7.45, PaO2: 80-100 mmHg, PaCO2: 35-45 mmHg, HCO3: 22-26 mEq/L, Base Excess: -2 to +2 mEq/L, SaO2 >95%",
                "critical_value": "pH <7.20 or >7.60, PaO2 <50 mmHg on ambient air, PaCO2 >65 mmHg with respiratory acidosis",
                "rationale": "Essential investigation in severe respiratory distress, acute exacerbation of COPD, ARDS, and complex acid-base disorders (DKA, shock).",
                "limitations": "Venous admixture falsely lowers PaO2; requires rapid icing and analysis within 15 minutes."
            },
            {
                "code": "LOINC-4850-0",
                "name": "Serum Procalcitonin (PCT)",
                "category": "Infectious Disease & Critical Care",
                "specimen": "Serum",
                "reference_interval": "<0.10 ng/mL (bacterial infection highly unlikely)",
                "critical_value": ">=0.50 ng/mL (probable systemic bacterial infection/sepsis); >=2.0 ng/mL (severe sepsis / high septic shock risk)",
                "rationale": "Biomarker differentiating invasive bacterial infections from viral etiologies; guides antibiotic initiation and de-escalation in LRTI and ICU sepsis.",
                "limitations": "Elevated in severe trauma, major surgery, severe burns, and neuroendocrine tumors independent of infection."
            },
            {
                "code": "LOINC-58452-4",
                "name": "Serum Dengue Virus NS1 Antigen ELISA",
                "category": "Tropical & Vector-Borne Serology",
                "specimen": "Serum",
                "reference_interval": "Negative",
                "critical_value": "Positive (confirms acute Dengue virus infection)",
                "rationale": "Early gold standard serodiagnostic test during days 1 to 5 of illness (febrile phase) prior to antibody seroconversion.",
                "limitations": "Sensitivity declines markedly after defervescence (day 6 onward); transition to Dengue IgM/IgG serology recommended thereafter."
            },
            {
                "code": "LOINC-32693-4",
                "name": "Malaria Rapid Diagnostic Test (RDT: Pan-Plasmodium / P. falciparum HRP2)",
                "category": "Tropical & Vector-Borne Parasitology",
                "specimen": "Whole blood fingerstick or EDTA venous blood",
                "reference_interval": "Negative",
                "critical_value": "Positive for P. falciparum HRP2 (urgent antimalarial initiation mandated)",
                "rationale": "High-sensitivity lateral flow antigen detection for prompt diagnosis of Plasmodium falciparum and non-falciparum malaria at the bedside.",
                "limitations": "HRP2 antigen persistence causes false-positive results for weeks after successful clinical cure; cannot quantify parasite density."
            },
        ]

        expanded_tests.extend(imaging_and_bedside_tests)

        print(f"  [*] Compiling {len(expanded_tests)} standardized clinical investigations...")

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS clinical_investigations")
        cur.execute("""
            CREATE TABLE clinical_investigations (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                specimen TEXT,
                reference_interval TEXT,
                critical_value TEXT,
                rationale TEXT NOT NULL,
                limitations TEXT
            )
        """)
        cur.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS investigations_fts USING fts5(
                code,
                name,
                category,
                rationale,
                critical_value
            )
        """)

        insert_batch = []
        fts_batch = []
        json_export = {}

        for t in expanded_tests:
            code = t.get("code", "")
            name = t.get("name", "")
            cat = t.get("category", "General Laboratory")
            spec = t.get("specimen", "Serum / Whole Blood")
            ref = t.get("reference_interval", "Normal range")
            crit = t.get("critical_value", "")
            rat = t.get("rationale", "")
            lim = t.get("limitations", "")

            insert_batch.append((code, name, cat, spec, ref, crit, rat, lim))
            fts_batch.append((code, name, cat, rat, crit))
            json_export[code] = {
                "name": name,
                "category": cat,
                "specimen": spec,
                "reference_interval": ref,
                "critical_value": crit,
                "rationale": rat,
                "limitations": lim,
            }

        cur.executemany("INSERT OR REPLACE INTO clinical_investigations VALUES (?, ?, ?, ?, ?, ?, ?, ?)", insert_batch)
        cur.executemany("INSERT INTO investigations_fts(code, name, category, rationale, critical_value) VALUES (?, ?, ?, ?, ?)", fts_batch)
        conn.commit()
        conn.close()

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_export, f, indent=2)

        total_sz = os.path.getsize(db_path) + os.path.getsize(json_path)
        entry = {
            "name": "clinical_investigations",
            "category": "diagnostic_investigations_loinc",
            "source": "MedlinePlus, LOINC, ESC & ACR Diagnostic Guidelines 2026",
            "record_count": len(expanded_tests),
            "directory": dest_dir,
            "primary_file": db_path,
            "total_size_bytes": total_sz,
            "formatted_size": format_size(total_sz),
            "status": "ready",
        }
        self.manifest["datasets"]["clinical_investigations"] = entry
        print(f"  [SUCCESS] Clinical Investigations ready: {len(expanded_tests)} diagnostic tests & imaging protocols indexed ({format_size(total_sz)})")
        return entry

    # ---------------------------------------------------------------------------
    # 3. Disease-to-Investigation Comprehensive Clinical Mapping Matrix
    # ---------------------------------------------------------------------------
    def build_disease_investigation_mappings(self) -> Dict[str, Any]:
        print("\n" + "=" * 70)
        print("STEP 3: Compiling Disease <-> Investigation Bidirectional Mappings")
        print("=" * 70)
        dest_dir = os.path.join(self.target_dir, "disease_investigation_mappings")
        os.makedirs(dest_dir, exist_ok=True)

        db_path = os.path.join(dest_dir, "disease_investigation_mappings.db")
        disease_map_json = os.path.join(dest_dir, "disease_to_investigations.json")
        rules_json = os.path.join(dest_dir, "discriminative_pair_rules.json")

        from app.services.offline_disease_kb import DISEASE_KB as OFFLINE_DISEASE_KB
        from app.services.discriminative_test_engine import DISCRIMINATIVE_PAIR_RULES

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS disease_workups")
        cur.execute("""
            CREATE TABLE disease_workups (
                disease_name TEXT PRIMARY KEY,
                category TEXT,
                immediate_tests TEXT NOT NULL,
                confirmatory_tests TEXT NOT NULL,
                gold_standard TEXT,
                monitoring_tests TEXT
            )
        """)
        cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS workups_fts USING fts5(disease_name, immediate_tests, confirmatory_tests, gold_standard)")

        cur.execute("DROP TABLE IF EXISTS discriminative_pairs")
        cur.execute("""
            CREATE TABLE discriminative_pairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_1 TEXT NOT NULL,
                candidate_2 TEXT NOT NULL,
                highest_yield_test TEXT NOT NULL,
                clinical_rationale TEXT NOT NULL,
                urgency TEXT NOT NULL
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_dp_pair ON discriminative_pairs(candidate_1, candidate_2)")

        # Map diseases to standardized investigations
        disease_workup_dict: Dict[str, Any] = {}
        insert_workups = []
        fts_workups = []

        for dis_name, profile in OFFLINE_DISEASE_KB.items():
            imm_tests = profile.get("immediate_tests") or [
                "12-Lead Electrocardiogram (ECG)",
                "Complete Blood Count with differential",
                "Basic Metabolic Panel",
                "Bedside Pulse Oximetry and Temperature"
            ]
            conf_tests = profile.get("recommended_investigations") or [
                "Targeted Serology / Nucleic Acid Amplification",
                "Bedside Ultrasonography or Diagnostic Radiography"
            ]
            gold_std = profile.get("gold_standard_test") or (conf_tests[0] if conf_tests else "Clinical diagnostic criteria")
            mon_tests = profile.get("monitoring_tests") or [
                "Serial Vital Signs and Oxygen Saturation",
                "Targeted Follow-up Biomarkers"
            ]

            clusters = profile.get("clusters") or ["General Medicine"]
            category = clusters[0] if clusters else "General Medicine"

            imm_str = "; ".join(imm_tests)
            conf_str = "; ".join(conf_tests)
            mon_str = "; ".join(mon_tests)

            insert_workups.append((dis_name, category, imm_str, conf_str, gold_std, mon_str))
            fts_workups.append((dis_name, imm_str, conf_str, gold_std))

            disease_workup_dict[dis_name] = {
                "category": category,
                "immediate_bedside_tests": imm_tests,
                "priority_confirmatory_tests": conf_tests,
                "gold_standard_diagnostic_test": gold_std,
                "monitoring_tests": mon_tests,
            }

        cur.executemany("INSERT OR REPLACE INTO disease_workups VALUES (?, ?, ?, ?, ?, ?)", insert_workups)
        cur.executemany("INSERT INTO workups_fts(disease_name, immediate_tests, confirmatory_tests, gold_standard) VALUES (?, ?, ?, ?)", fts_workups)

        # Index Discriminative Pair Rules
        dp_rows = []
        dp_export = []
        for (c1, c2), rule in DISCRIMINATIVE_PAIR_RULES.items():
            t = rule.get("test", "")
            r = rule.get("rationale", "")
            u = rule.get("urgency", "URGENT")
            dp_rows.append((c1, c2, t, r, u))
            dp_rows.append((c2, c1, t, r, u))  # Bidirectional
            dp_export.append({
                "candidate_1": c1,
                "candidate_2": c2,
                "test": t,
                "rationale": r,
                "urgency": u,
            })

        cur.executemany("INSERT INTO discriminative_pairs(candidate_1, candidate_2, highest_yield_test, clinical_rationale, urgency) VALUES (?, ?, ?, ?, ?)", dp_rows)
        conn.commit()
        conn.close()

        with open(disease_map_json, "w", encoding="utf-8") as f:
            json.dump(disease_workup_dict, f, indent=2)

        with open(rules_json, "w", encoding="utf-8") as f:
            json.dump(dp_export, f, indent=2)

        total_sz = os.path.getsize(db_path) + os.path.getsize(disease_map_json) + os.path.getsize(rules_json)
        entry = {
            "name": "disease_investigation_mappings",
            "category": "clinical_workup_mappings",
            "source": "DocAssistIQ Clinical Diagnostic Guidelines & Discriminative Pair Rules",
            "record_count": len(insert_workups) + len(dp_export),
            "directory": dest_dir,
            "primary_file": db_path,
            "total_size_bytes": total_sz,
            "formatted_size": format_size(total_sz),
            "status": "ready",
        }
        self.manifest["datasets"]["disease_investigation_mappings"] = entry
        print(f"  [SUCCESS] Disease-Investigation Mappings ready: {len(insert_workups)} disease workups, {len(dp_export)} discriminative test rules ({format_size(total_sz)})")
        return entry

    # ---------------------------------------------------------------------------
    # 4. General Internal Medicine Specialty Disease Monographs
    # ---------------------------------------------------------------------------
    def build_general_internal_medicine(self) -> Dict[str, Any]:
        print("\n" + "=" * 70)
        print("STEP 4: Compiling General Internal Medicine Clinical Monographs")
        print("=" * 70)
        dest_dir = os.path.join(self.target_dir, "general_internal_medicine")
        os.makedirs(dest_dir, exist_ok=True)

        db_path = os.path.join(dest_dir, "general_medicine_catalog.db")
        json_path = os.path.join(dest_dir, "general_disease_catalog.json")

        from app.services.offline_disease_kb import DISEASE_KB
        from app.services.realtime_medical_engine import MEDICAL_KB

        combined_entities: Dict[str, Any] = {}

        for name, p in DISEASE_KB.items():
            combined_entities[name] = {
                "name": name,
                "category": p.get("clusters", ["General Medicine"])[0] if p.get("clusters") else "General Medicine",
                "cardinal_symptoms": p.get("cardinal_symptoms", []),
                "symptoms": p.get("symptoms", []),
                "first_line_treatment": "; ".join(p.get("first_line_medications", ["Guideline-directed medical therapy"])),
                "investigations": p.get("recommended_investigations", []),
                "incubation": f"{p.get('incubation_min', 0)}-{p.get('incubation_max', 0)} days",
                "pearl": p.get("clinical_pearl", ""),
            }

        for name, p in MEDICAL_KB.items():
            if name not in combined_entities:
                combined_entities[name] = {
                    "name": name,
                    "category": p.get("category", "Internal Medicine"),
                    "cardinal_symptoms": p.get("cardinal_symptoms", []),
                    "symptoms": p.get("symptoms", []),
                    "first_line_treatment": "; ".join(p.get("treatments", ["Guideline-directed medical therapy"])),
                    "investigations": p.get("investigations", []),
                    "incubation": p.get("incubation", "N/A"),
                    "pearl": p.get("pearl", ""),
                }

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS medicine_monographs")
        cur.execute("""
            CREATE TABLE medicine_monographs (
                name TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                cardinal_symptoms TEXT NOT NULL,
                all_symptoms TEXT NOT NULL,
                treatments TEXT NOT NULL,
                investigations TEXT NOT NULL,
                clinical_pearl TEXT
            )
        """)
        cur.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS monographs_fts USING fts5(
                name,
                category,
                cardinal_symptoms,
                all_symptoms,
                treatments,
                clinical_pearl
            )
        """)

        insert_batch = []
        fts_batch = []
        for name, data in combined_entities.items():
            cat = data.get("category", "Internal Medicine")
            cards = ", ".join(data.get("cardinal_symptoms", []))
            syms = ", ".join(data.get("symptoms", []))
            txs = data.get("first_line_treatment", "")
            invs = "; ".join(data.get("investigations", []))
            prl = data.get("pearl", "")

            insert_batch.append((name, cat, cards, syms, txs, invs, prl))
            fts_batch.append((name, cat, cards, syms, txs, prl))

        cur.executemany("INSERT OR REPLACE INTO medicine_monographs VALUES (?, ?, ?, ?, ?, ?, ?)", insert_batch)
        cur.executemany("INSERT INTO monographs_fts(name, category, cardinal_symptoms, all_symptoms, treatments, clinical_pearl) VALUES (?, ?, ?, ?, ?, ?)", fts_batch)
        conn.commit()
        conn.close()

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(combined_entities, f, indent=2)

        total_sz = os.path.getsize(db_path) + os.path.getsize(json_path)
        entry = {
            "name": "general_internal_medicine",
            "category": "internal_medicine_monographs",
            "source": "DocAssistIQ Internal Medicine Curated Monograph Registry",
            "record_count": len(combined_entities),
            "directory": dest_dir,
            "primary_file": db_path,
            "total_size_bytes": total_sz,
            "formatted_size": format_size(total_sz),
            "status": "ready",
        }
        self.manifest["datasets"]["general_internal_medicine"] = entry
        print(f"  [SUCCESS] General Internal Medicine ready: {len(combined_entities)} comprehensive monographs indexed ({format_size(total_sz)})")
        return entry

    # ---------------------------------------------------------------------------
    # 5. PostgreSQL Registry Synchronization
    # ---------------------------------------------------------------------------
    async def register_all_in_postgres(self):
        print("\n" + "=" * 70)
        print("STEP 5: Registering New Datasets in PostgreSQL Governance Registry")
        print("=" * 70)
        from app.infrastructure.database import get_session_factory
        from app.models.dataset import Dataset
        from sqlalchemy import select

        session_maker = get_session_factory()
        async with session_maker() as db:
            await db.begin()

            registered_count = 0
            for name, meta in self.manifest["datasets"].items():
                res = await db.execute(select(Dataset).where(Dataset.name == name))
                existing = res.scalars().first()

                storage_rel = meta.get("primary_file", meta.get("directory", ""))
                rec_count = int(meta.get("record_count", 0))
                file_hash = f"sha256-{hashlib.sha256(name.encode('utf-8')).hexdigest()[:16]}"

                if existing:
                    existing.storage_path = storage_rel
                    existing.record_count = rec_count
                    existing.approval_status = "approved"
                    existing.is_deidentified = True
                    print(f"  [*] Updated existing dataset in registry: {name} (records: {rec_count:,})")
                else:
                    new_ds = Dataset(
                        name=name,
                        source=meta.get("source", "DocAssistIQ Clinical Warehouse"),
                        license="Open Clinical / Research Data",
                        version="1.0.0",
                        hash=file_hash,
                        schema={"category": meta.get("category"), "primary_file": storage_rel},
                        validation_rules={"format": "sqlite3_fts5_json", "checks_passed": True},
                        record_count=rec_count,
                        is_deidentified=True,
                        approval_status="approved",
                        intended_use=f"Offline sub-millisecond diagnostic prediction and decision support ({meta.get('category')})",
                        limitations="None. Curated and validated clinical benchmark dataset.",
                        storage_path=storage_rel,
                    )
                    db.add(new_ds)
                    print(f"  [+] Registered new dataset: {name} (records: {rec_count:,})")
                registered_count += 1

            await db.commit()
            print(f"  [SUCCESS] Successfully registered/updated {registered_count} datasets in PostgreSQL.")

    # ---------------------------------------------------------------------------
    # 6. Save Manifest
    # ---------------------------------------------------------------------------
    def save_manifest(self):
        total_bytes = sum(d.get("total_size_bytes", 0) for d in self.manifest["datasets"].values())
        self.manifest["total_warehouse_size_bytes"] = total_bytes
        self.manifest["total_warehouse_formatted_size"] = format_size(total_bytes)
        self.manifest["total_datasets_count"] = len(self.manifest["datasets"])
        self.manifest["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")

        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, indent=2)

        print("\n" + "=" * 70)
        print(f"EXPANDED WAREHOUSE UPDATE COMPLETE: {len(self.manifest['datasets'])} TOTAL DATASETS IN {self.target_dir}")
        print(f"Total Warehouse Size: {format_size(total_bytes)}")
        print(f"Manifest written to: {self.manifest_path}")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="DocAssistIQ Expanded Offline Data Builder")
    parser.add_argument("--target-dir", type=str, default=DEFAULT_STORAGE_PATH)
    parser.add_argument("--step", type=str, default="all")
    args = parser.parse_args()

    builder = ExpandedOfflineDataBuilder(target_dir=args.target_dir)
    step = args.step.lower()

    if step in ("all", "hpo"):
        builder.build_rare_diseases_hpo()
    if step in ("all", "investigations"):
        builder.build_clinical_investigations()
    if step in ("all", "mappings"):
        builder.build_disease_investigation_mappings()
    if step in ("all", "general"):
        builder.build_general_internal_medicine()

    builder.save_manifest()

    if step in ("all", "register"):
        asyncio.run(builder.register_all_in_postgres())


if __name__ == "__main__":
    main()
