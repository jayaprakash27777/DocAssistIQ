"""DocAssistIQ — Comprehensive Multi-Specialty Expanded Disease Catalog.

Adds 80+ clinical-grade disease profiles covering:
- Cardiology & Vascular Emergencies (Tamponade, Pericarditis, AFib, PAD, Aortic Stenosis)
- Pulmonology (Tension Pneumothorax, Sarcoidosis, Bronchiectasis, IPF, Croup, Bronchiolitis)
- Gastroenterology & Surgery (Acute Cholecystitis, Acute Cholangitis, Celiac, IBS, C. diff, Boerhaave, SBO, Mesenteric Ischemia)
- Neurology & Ophthalmology (Giant Cell Arteritis, Bell's Palsy, Myasthenia Gravis, Parkinson's, MS, Cluster Headache, NPH, Trigeminal Neuralgia, ALS, BPPV, Meniere's, Glaucoma, Retinal Detachment, CRAO)
- Endocrinology (Pheochromocytoma, Cushing's, Addison's, Hyperparathyroidism, SIADH, Diabetes Insipidus, Hypoglycemia)
- Nephrology & Urology (Nephrotic Syndrome, Glomerulonephritis, BPH, Testicular Torsion, Fournier's)
- Rheumatology & Immunology (Pseudogout, Ankylosing Spondylitis, Psoriatic Arthritis, PMR, Sjogren's, Scleroderma, Dermatomyositis, Fibromyalgia, GPA)
- Hematology & Oncology (Iron Deficiency, B12 Deficiency, Hemolytic Anemia, Multiple Myeloma, ITP, TTP, DIC)
- Infectious & Pediatrics (Lyme Disease, Kawasaki Disease, Henoch-Schonlein Purpura, Epiglottitis, Peritonsillar Abscess, Mastoiditis, Necrotizing Fasciitis, Osteomyelitis)
- Critical Care & Toxicology (Anaphylaxis, NMS, Opioid Overdose, Carbon Monoxide Poisoning)
- Dermatology & Psychiatry (Psoriasis, Atopic Dermatitis, SJS/TEN, MDD, Bipolar Mania, Panic Disorder)
"""

from typing import Dict, Any

EXPANDED_DISEASE_CATALOG: Dict[str, Dict[str, Any]] = {
    # -----------------------------------------------------------------------
    # NEUROLOGY & OPHTHALMOLOGY
    # -----------------------------------------------------------------------
    "Giant Cell Arteritis (Temporal Arteritis)": {
        "symptoms": [
            "jaw claudication", "temporal headache", "scalp tenderness", "headache",
            "vision loss", "amaurosis fugax", "diplopia", "blurred vision", "fever",
            "fatigue", "weight loss", "polymyalgia rheumatica symptoms", "elevated esr", "prominent temporal artery"
        ],
        "cardinal_symptoms": ["jaw claudication", "temporal headache", "scalp tenderness", "vision loss"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["headache_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
        "prevalence": "moderate",
        "_investigations": [
            "Erythrocyte sedimentation rate (ESR >50 mm/hr, often >100) and C-reactive protein (CRP)",
            "Temporal artery ultrasound (hypoechoic 'halo' sign)",
            "Temporal artery biopsy (gold standard: transmural inflammation, giant cells, lamina elastica disruption)",
            "Complete blood count (normocytic normochromic anemia, thrombocytosis)",
        ],
        "_treatment_summary": "Immediate high-dose systemic corticosteroids (Prednisone 60mg oral daily or IV Methylprednisolone 1g daily if visual symptoms) before biopsy. Tocilizumab (IL-6 receptor antagonist).",
    },
    "Bell's Palsy (Idiopathic Facial Palsy)": {
        "symptoms": [
            "facial weakness", "facial drooping", "inability to close eye", "loss of nasolabial fold",
            "inability to wrinkle forehead", "hyperacusis", "ear pain", "loss of taste anterior tongue",
            "dry eyes", "drooling", "unilateral facial droop"
        ],
        "cardinal_symptoms": ["facial drooping", "inability to close eye", "inability to wrinkle forehead"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_syndrome"],
        "incubation_min": 0, "incubation_max": 2,
        "severity": "moderate",
        "prevalence": "common",
        "_investigations": [
            "Clinical diagnosis (LMN facial nerve palsy involves the forehead, distinguishing from UMN stroke)",
            "Lyme disease serology (in endemic areas)",
            "Herpes zoster examination (exclude Ramsay Hunt syndrome / zoster oticus)",
            "MRI brain/internal auditory canal (if atypical, bilateral, or not improving by 3-4 months)",
        ],
        "_treatment_summary": "Oral Prednisolone (50-60mg daily for 7-10 days, ideally started within 72 hours of onset). Artificial tears and eye lubrication/taping at night to prevent exposure keratopathy. Add Valacyclovir for severe palsy.",
    },
    "Myasthenia Gravis": {
        "symptoms": [
            "ptosis", "drooping eyelid", "diplopia", "double vision", "fatigable weakness",
            "muscle weakness worse with activity", "weakness improves with rest",
            "dysphagia", "difficulty chewing", "dysarthria", "nasal voice",
            "facial weakness", "shortness of breath", "myasthenic crisis"
        ],
        "cardinal_symptoms": ["ptosis", "diplopia", "fatigable weakness", "weakness improves with rest"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
        "prevalence": "moderate",
        "_investigations": [
            "Serum anti-acetylcholine receptor (AChR) antibodies (85% positive in generalized MG)",
            "Serum anti-muscle-specific tyrosine kinase (MuSK) antibodies",
            "Repetitive nerve stimulation (RNS) and single-fiber electromyography (SFEMG - most sensitive test)",
            "Ice pack test at bedside (improvement of ptosis by ≥2mm after 2 minutes of ice application)",
            "Chest CT with IV contrast (screen for thymoma or thymic hyperplasia)",
        ],
        "_treatment_summary": "Pyridostigmine (oral acetylcholinesterase inhibitor 60mg 3-5 times daily). Immunosuppression (corticosteroids, azathioprine). Thymectomy (for thymoma or generalized AChR-positive MG). IVIG or plasmapheresis for myasthenic crisis.",
    },
    "Parkinson's Disease": {
        "symptoms": [
            "resting tremor", "pill-rolling tremor", "cogwheel rigidity", "bradykinesia",
            "slowness of movement", "shuffling gait", "festinating gait", "postural instability",
            "masked facies", "monotone voice", "micrographia", "anosmia", "rem sleep behavior disorder"
        ],
        "cardinal_symptoms": ["resting tremor", "cogwheel rigidity", "bradykinesia", "shuffling gait"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "moderate",
        "prevalence": "common",
        "_investigations": [
            "Clinical diagnosis (UK Parkinson's Disease Society Brain Bank criteria: bradykinesia + rigidity or resting tremor)",
            "Levodopa challenge test (positive response supports idiopathic Parkinson's)",
            "DaTscan (I-123 ioflupane SPECT demonstrating loss of dopamine transporters in striatum)",
            "MRI brain (to exclude secondary parkinsonism, normal pressure hydrocephalus, or vascular causes)",
        ],
        "_treatment_summary": "Levodopa/Carbidopa (gold standard). Dopamine agonists (pramipexole, ropinirole). MAO-B inhibitors (rasagiline, selegiline). COMT inhibitors (entacapone). Deep Brain Stimulation (DBS) for refractory motor fluctuations.",
    },
    "Multiple Sclerosis (Relapsing-Remitting)": {
        "symptoms": [
            "optic neuritis", "monocular vision loss", "eye pain with movement", "paresthesias",
            "numbness", "tingling", "lhermitte sign", "electric shock sensation down spine",
            "muscle weakness", "spasticity", "ataxia", "fatigue", "urinary urgency", "internuclear ophthalmoplegia"
        ],
        "cardinal_symptoms": ["optic neuritis", "lhermitte sign", "paresthesias", "internuclear ophthalmoplegia"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
        "prevalence": "moderate",
        "_investigations": [
            "MRI brain and cervical/thoracic spine with gadolinium (periventricular Dawson fingers, corpus callosum lesions, dissemination in space and time by McDonald criteria)",
            "Lumbar puncture (CSF-specific oligoclonal bands and elevated IgG index)",
            "Visual evoked potentials (delayed P100 latency confirming demyelination)",
        ],
        "_treatment_summary": "Acute relapse: IV Methylprednisolone 1g daily for 3-5 days. Disease-modifying therapy (DMT): Ocrelizumab, Natalizumab, Fingolimod, Dimethyl fumarate, or Interferon-beta.",
    },
    "Acute Angle-Closure Glaucoma": {
        "symptoms": [
            "severe eye pain", "unilateral eye pain", "headache", "blurred vision", "halos around lights",
            "colored halos", "fixed mid-dilated pupil", "cloudy cornea", "steamy cornea", "nausea",
            "vomiting", "rock-hard eye on palpation", "red eye", "conjunctival injection"
        ],
        "cardinal_symptoms": ["halos around lights", "severe eye pain", "fixed mid-dilated pupil", "cloudy cornea"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["ocular_emergency"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
        "prevalence": "moderate",
        "_investigations": [
            "Tonometry (markedly elevated intraocular pressure >30-40 mmHg, often >50 mmHg)",
            "Gonioscopy (visualization of closed iridocorneal angle)",
            "Slit lamp examination (shallow anterior chamber, conjunctival ciliary flush, corneal edema)",
        ],
        "_treatment_summary": "EMERGENT OPHTHALMOLOGY CONSULT. Topical Timolol 0.5%, Apraclonidine 1%, Pilocarpine 2%. IV Acetazolamide 500mg. IV Mannitol if refractory. Definitive therapy: Bilateral laser peripheral iridotomy (LPI).",
    },
    "Retinal Detachment": {
        "symptoms": [
            "flashes of light", "photopsia", "sudden increase in floaters", "dark curtain falling over vision",
            "shadow in visual field", "peripheral visual field loss", "painless vision loss", "blurry vision"
        ],
        "cardinal_symptoms": ["flashes of light", "floaters", "dark curtain falling over vision"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["ocular_emergency"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
        "prevalence": "moderate",
        "_investigations": [
            "Dilated funduscopic examination with indirect ophthalmoscope (elevation of retina, retinal tear)",
            "Ocular B-scan ultrasonography (demonstrating detached retinal membrane)",
        ],
        "_treatment_summary": "EMERGENT OPHTHALMOLOGY SURGERY. Pneumatic retinopexy, scleral buckle, or pars plana vitrectomy with laser photocoagulation / cryopexy to prevent macular detachment.",
    },

    # -----------------------------------------------------------------------
    # CARDIOLOGY & VASCULAR
    # -----------------------------------------------------------------------
    "Cardiac Tamponade": {
        "symptoms": [
            "hypotension", "muffled heart sounds", "jugular venous distension", "beck triad",
            "pulsus paradoxus", "tachycardia", "dyspnea", "tachypnea", "chest fullness",
            "syncope", "diaphoresis", "cardiomegaly"
        ],
        "cardinal_symptoms": ["hypotension", "muffled heart sounds", "jugular venous distension", "pulsus paradoxus"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["cardiovascular_shock"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
        "prevalence": "rare",
        "_investigations": [
            "Transthoracic echocardiography (gold standard: right ventricular diastolic collapse, right atrial systolic collapse, large pericardial effusion with swinging heart)",
            "12-Lead ECG (electrical alternans, low-voltage QRS complexes, sinus tachycardia)",
            "Chest X-ray ('water bottle' cardiac silhouette)",
        ],
        "_treatment_summary": "LIFE-THREATENING EMERGENCY: Emergent ultrasound-guided pericardiocentesis or surgical subxiphoid pericardial window. IV fluid bolus (volume loading preserves preload). Avoid positive pressure ventilation.",
    },
    "Acute Pericarditis": {
        "symptoms": [
            "sharp chest pain", "retrosternal chest pain", "pleuritic chest pain",
            "chest pain relieved by sitting forward", "chest pain worse lying flat",
            "pericardial friction rub", "fever", "malaise", "dyspnea", "tachycardia"
        ],
        "cardinal_symptoms": ["chest pain relieved by sitting forward", "pericardial friction rub", "sharp chest pain"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["cardiac_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "moderate",
        "prevalence": "common",
        "_investigations": [
            "12-Lead ECG (pathognomonic diffuse upward concave ST-segment elevations and PR-segment depressions with reciprocal ST depression in aVR and V1)",
            "High-sensitivity troponin (elevated if myopericarditis present)",
            "Transthoracic echocardiography (assess for pericardial effusion / tamponade)",
            "Inflammatory markers (serum CRP and ESR elevated)",
        ],
        "_treatment_summary": "High-dose oral NSAIDs (Ibuprofen 600-800mg TDS or Aspirin) plus Colchicine (0.5mg BD for 3 months to prevent recurrences). Exercise restriction until symptoms and CRP normalize.",
    },
    "Atrial Fibrillation (Rapid Ventricular Response)": {
        "symptoms": [
            "palpitations", "irregular heartbeat", "irregularly irregular pulse",
            "fatigue", "shortness of breath", "dizziness", "lightheadedness", "chest pain", "reduced exercise tolerance"
        ],
        "cardinal_symptoms": ["irregularly irregular pulse", "palpitations", "irregular heartbeat"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["cardiac_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
        "prevalence": "common",
        "_investigations": [
            "12-Lead ECG (absence of distinct P waves, disorganized fibrillatory baseline waves, irregularly irregular QRS intervals)",
            "Transthoracic echocardiography (assess left atrial enlargement, valvular disease, LVEF)",
            "Thyroid-stimulating hormone (TSH - rule out hyperthyroidism)",
            "Serum electrolytes, renal and liver function",
        ],
        "_treatment_summary": "Hemodynamically unstable: Emergent synchronized DC cardioversion. Hemodynamically stable: Rate control (Beta-blockers e.g. Metoprolol/Bisoprolol, or non-DHP CCB e.g. Diltiazem). Stroke risk assessment via CHA2DS2-VASc score and anticoagulation (DOACs: Apixaban, Rivaroxaban).",
    },

    # -----------------------------------------------------------------------
    # PULMONOLOGY
    # -----------------------------------------------------------------------
    "Tension Pneumothorax": {
        "symptoms": [
            "sudden pleuritic chest pain", "severe shortness of breath", "tracheal deviation away from affected side",
            "absent breath sounds", "hyperresonance to percussion", "hypotension", "tachycardia",
            "jugular venous distension", "cyanosis", "respiratory distress"
        ],
        "cardinal_symptoms": ["tracheal deviation away from affected side", "absent breath sounds", "sudden pleuritic chest pain", "hypotension"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["respiratory_distress", "cardiovascular_shock"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
        "prevalence": "moderate",
        "_investigations": [
            "CLINICAL DIAGNOSIS ONLY: Do NOT delay treatment for chest radiography in unstable patients!",
            "Point-of-care ultrasound (POCUS: absence of lung sliding, barcode sign on M-mode)",
            "Chest X-ray (after decompression: contralateral tracheal/mediastinal shift, depression of hemidiaphragm)",
        ],
        "_treatment_summary": "IMMEDIATE EMERGENCY NEEDLE DECOMPRESSION: 14-16G catheter in 2nd intercostal space mid-clavicular line or 4th/5th intercostal space anterior axillary line, immediately followed by tube thoracostomy (chest drain insertion).",
    },
    "Sarcoidosis": {
        "symptoms": [
            "dry cough", "shortness of breath", "dyspnea", "fatigue", "bilateral hilar lymphadenopathy",
            "erythema nodosum", "painful red skin nodules", "anterior uveitis", "joint pain", "hypercalcemia"
        ],
        "cardinal_symptoms": ["bilateral hilar lymphadenopathy", "erythema nodosum", "dry cough"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["autoimmune_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "moderate",
        "prevalence": "moderate",
        "_investigations": [
            "Chest Radiograph / High-resolution CT chest (bilateral symmetrical hilar lymphadenopathy, perilymphatic nodules)",
            "Bronchoscopy with endobronchial ultrasound (EBUS-TBNA) / transbronchial lung biopsy (non-caseating granulomas, negative for AFB/fungi)",
            "Serum ACE (angiotensin-converting enzyme) level and serum calcium / 24-hour urine calcium",
            "Ophthalmology slit-lamp exam and baseline ECG",
        ],
        "_treatment_summary": "Asymptomatic stage 1 disease: observation. Symptomatic pulmonary, cardiac, ocular, or neurologic involvement: Oral Prednisone (0.5mg/kg/day, tapered over 6-12 months). Second-line: Methotrexate or Infliximab.",
    },
    "Croup (Laryngotracheobronchitis)": {
        "symptoms": [
            "barking cough", "seal-like cough", "inspiratory stridor", "hoarseness",
            "fever", "runny nose", "worse at night", "intercostal retractions", "agitation worsens stridor"
        ],
        "cardinal_symptoms": ["barking cough", "inspiratory stridor", "hoarseness"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["pediatric_respiratory"],
        "incubation_min": 1, "incubation_max": 3,
        "severity": "moderate",
        "prevalence": "common",
        "_investigations": [
            "Clinical diagnosis (Westley Croup Score evaluates stridor, retractions, air entry, cyanosis, consciousness)",
            "AP neck soft tissue radiograph (classic 'steeple sign' from subglottic narrowing; do not perform if causes distress)",
            "Pulse oximetry",
        ],
        "_treatment_summary": "Single dose oral Dexamethasone 0.15–0.60 mg/kg for all severities. Moderate-to-severe (stridor at rest): Nebulized racemic epinephrine (or L-epinephrine 1:1000 5mL) with 2–4 hours observation.",
    },

    # -----------------------------------------------------------------------
    # GASTROENTEROLOGY & SURGICAL EMERGENCIES
    # -----------------------------------------------------------------------
    "Acute Cholecystitis": {
        "symptoms": [
            "right upper quadrant pain", "biliary colic", "pain radiating to right shoulder",
            "murphy sign positive", "fever", "nausea", "vomiting", "leukocytosis",
            "pain after fatty meal", "anorexia"
        ],
        "cardinal_symptoms": ["right upper quadrant pain", "murphy sign positive", "fever", "pain radiating to right shoulder"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["acute_abdomen"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
        "prevalence": "common",
        "_investigations": [
            "Right Upper Quadrant Abdominal Ultrasound (first-line: gallstones, gallbladder wall thickening >4mm, pericholecystic fluid, sonographic Murphy's sign)",
            "Complete Blood Count (leukocytosis with left shift)",
            "Liver function tests (mild elevation in AST, ALT, bilirubin; marked elevation suggests choledocholithiasis/cholangitis)",
            "HIDA scan (cholescintigraphy - most sensitive test if ultrasound inconclusive)",
        ],
        "_treatment_summary": "NPO, IV fluid resuscitation, IV antibiotics (Ceftriaxone + Metronidazole, or Ampicillin/Sulbactam). Early laparoscopic cholecystectomy within 72 hours of admission (Tokyo Guidelines 2018).",
    },
    "Acute Ascending Cholangitis": {
        "symptoms": [
            "charcot triad", "reynolds pentad", "right upper quadrant pain", "jaundice", "high fever",
            "rigors", "hypotension", "septic shock", "confusion", "altered mental status", "pruritus"
        ],
        "cardinal_symptoms": ["charcot triad", "reynolds pentad", "jaundice", "right upper quadrant pain", "high fever"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["acute_abdomen", "hepatic_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
        "prevalence": "moderate",
        "_investigations": [
            "Blood cultures x2 (bacteremia common: E. coli, Klebsiella, Enterococcus)",
            "Liver function tests (direct hyperbilirubinemia, markedly elevated alkaline phosphatase and GGT)",
            "Abdominal ultrasound / CT abdomen with contrast (biliary ductal dilation, common bile duct stones)",
            "MRCP (magnetic resonance cholangiopancreatography) or emergency ERCP",
        ],
        "_treatment_summary": "LIFE-THREATENING BILIARY SEPSIS: IV fluid resuscitation, emergent broad-spectrum IV antibiotics (Piperacillin-Tazobactam or Meropenem). Urgent biliary decompression via ERCP sphincterotomy/stenting or percutaneous transhepatic drainage.",
    },
    "Celiac Disease (Gluten-Sensitive Enteropathy)": {
        "symptoms": [
            "chronic diarrhea", "steatorrhea", "foul-smelling stool", "abdominal bloating",
            "flatulence", "weight loss", "fatigue", "dermatitis herpetiformis",
            "iron deficiency anemia", "osteopenia", "failure to thrive"
        ],
        "cardinal_symptoms": ["chronic diarrhea", "dermatitis herpetiformis", "abdominal bloating", "steatorrhea"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["gastrointestinal_fever"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "moderate",
        "prevalence": "common",
        "_investigations": [
            "Serum IgA tissue transglutaminase (tTG-IgA) antibodies (first-line test, must be on gluten-containing diet)",
            "Total serum IgA level (to exclude IgA deficiency; check IgG-DGP or IgG-tTG if IgA deficient)",
            "Upper endoscopy with duodenal biopsies (Marsh criteria: villous atrophy, crypt hyperplasia, intraepithelial lymphocytosis)",
            "HLA-DQ2 and HLA-DQ8 genotyping (high negative predictive value)",
        ],
        "_treatment_summary": "Strict lifelong gluten-free diet (avoid wheat, barley, rye). Nutritional replacement for iron, folate, vitamin D, calcium, and B12. DEXA scan to assess bone mineral density.",
    },
    "Boerhaave Syndrome (Spontaneous Esophageal Rupture)": {
        "symptoms": [
            "violent vomiting history", "severe chest pain", "retrosternal pain", "epigastric pain",
            "subcutaneous emphysema", "hamman sign", "crunching sound over precordium", "fever",
            "dyspnea", "tachycardia", "cyanosis", "pleural effusion", "shock"
        ],
        "cardinal_symptoms": ["hamman sign", "subcutaneous emphysema", "severe chest pain", "violent vomiting history"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["acute_abdomen", "cardiac_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
        "prevalence": "rare",
        "_investigations": [
            "CT chest and abdomen with oral water-soluble contrast (Gastrografin, NOT barium) demonstrating esophageal tear and mediastinal fluid/air",
            "Chest radiography (pneumomediastinum, subcutaneous emphysema in neck, left hydropneumothorax)",
            "Pleural fluid analysis (pH <6.0, elevated salivary amylase)",
        ],
        "_treatment_summary": "SURGICAL EMERGENCY: NPO, IV fluid resuscitation, broad-spectrum IV antibiotics and antifungals. Emergent surgical primary repair and mediastinal/pleural debridement within 24 hours (mortality doubles after 24h).",
    },

    # -----------------------------------------------------------------------
    # ENDOCRINOLOGY
    # -----------------------------------------------------------------------
    "Pheochromocytoma": {
        "symptoms": [
            "episodic severe headache", "profuse diaphoresis", "paroxysmal sweating",
            "tachycardia", "palpitations", "severe paroxysmal hypertension",
            "tremor", "pallor", "anxiety", "panic sensation", "orthostatic hypotension"
        ],
        "cardinal_symptoms": ["episodic severe headache", "profuse diaphoresis", "tachycardia", "severe paroxysmal hypertension"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["endocrine_crisis"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
        "prevalence": "rare",
        "_investigations": [
            "Plasma free metanephrines (high sensitivity, excellent screening test)",
            "24-Hour urinary fractionated metanephrines and catecholamines",
            "CT abdomen with adrenal protocol or MRI abdomen (without gadolinium)",
            "123I-MIBG scintigraphy or 68Ga-DOTATATE PET/CT for localization of extra-adrenal paragangliomas",
        ],
        "_treatment_summary": "Alpha-blockade FIRST (Phenoxybenzamine 10mg BD or Doxazosin for 10-14 days), followed by beta-blockade ONLY AFTER adequate alpha-blockade to avoid unopposed alpha-mediated hypertensive crisis. High-sodium diet, then laparoscopic adrenalectomy.",
    },
    "Cushing's Syndrome": {
        "symptoms": [
            "moon facies", "facial plethora", "buffalo hump", "dorsocervical fat pad",
            "central obesity", "purple abdominal striae", "easy bruising", "proximal muscle weakness",
            "hypertension", "hyperglycemia", "osteoporosis", "hirsutism", "menstrual irregularity"
        ],
        "cardinal_symptoms": ["purple abdominal striae", "moon facies", "buffalo hump", "proximal muscle weakness"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["endocrine_crisis"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "moderate",
        "prevalence": "moderate",
        "_investigations": [
            "24-Hour urinary free cortisol (UFC) x2",
            "Late-night salivary cortisol x2",
            "Low-dose dexamethasone suppression test (1mg overnight, morning cortisol fails to suppress <1.8 mcg/dL)",
            "Plasma ACTH level (ACTH-dependent vs. ACTH-independent)",
            "Pituitary MRI with gadolinium (Cushing's disease) or Adrenal CT (adrenal adenoma/carcinoma)",
        ],
        "_treatment_summary": "Surgical resection of underlying cause (transsphenoidal adenomectomy for pituitary Cushing's, unilateral laparoscopic adrenalectomy for adrenal adenoma). Medical therapy (Ketoconazole, Metyrapone, Osilodrostat) if awaiting surgery.",
    },
    "Addison's Disease (Primary Adrenal Insufficiency)": {
        "symptoms": [
            "chronic fatigue", "hyperpigmentation", "palmar crease pigmentation", "mucosal hyperpigmentation",
            "orthostatic hypotension", "salt craving", "weight loss", "anorexia", "nausea",
            "vomiting", "abdominal pain", "hypoglycemia", "hyponatremia", "hyperkalemia"
        ],
        "cardinal_symptoms": ["hyperpigmentation", "salt craving", "orthostatic hypotension", "hyperkalemia"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["endocrine_crisis"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
        "prevalence": "moderate",
        "_investigations": [
            "8 AM Serum Cortisol (<3 mcg/dL strongly suggestive) and simultaneous plasma ACTH (elevated in primary)",
            "Short Synacthen (Cosyntropin) stimulation test (250 mcg IV/IM; failure of cortisol to rise >18 mcg/dL at 30/60 min)",
            "Serum Electrolytes (hyponatremia with hyperkalemia, elevated BUN/creatinine)",
            "Serum 21-hydroxylase autoantibodies (confirms autoimmune adrenalitis)",
            "CT adrenals (enlarged in infectious/TB/hemorrhage, atrophic in autoimmune)",
        ],
        "_treatment_summary": "Lifelong dual hormone replacement: Hydrocortisone (15-25mg daily in divided doses) PLUS Fludrocortisone (0.05-0.1mg daily). Patient must carry steroid card/bracelet and double doses during illness (sick-day rules). IV hydrocortisone 100mg stat for crisis.",
    },

    # -----------------------------------------------------------------------
    # NEPHROLOGY & UROLOGY
    # -----------------------------------------------------------------------
    "Nephrotic Syndrome": {
        "symptoms": [
            "generalized edema", "anasarca", "periorbital edema", "pitting edema",
            "frothy urine", "foamy urine", "weight gain", "fatigue",
            "loss of appetite", "hyperlipidemia", "hypercoagulability", "flank pain if renal vein thrombosis"
        ],
        "cardinal_symptoms": ["frothy urine", "generalized edema", "periorbital edema"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["renal_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
        "prevalence": "common",
        "_investigations": [
            "Urine protein-to-creatinine ratio (UPCR) or 24-hour urine protein (>3.5g/24 hours/1.73 m2)",
            "Serum albumin (<3.0 g/dL, often <2.5 g/dL)",
            "Fasting lipid panel (hypercholesterolemia and hypertriglyceridemia)",
            "Serum PLA2R antibodies (primary membranous nephropathy)",
            "Renal biopsy (definitive histologic diagnosis: minimal change disease, FSGS, membranous)",
        ],
        "_treatment_summary": "Sodium restriction (<2g/day), Loop diuretics (Furosemide with Bumetanide). ACE inhibitors or ARBs for proteinuria reduction. High-dose Corticosteroids (Prednisone 1mg/kg/day, especially for MCD). Prophylactic anticoagulation if serum albumin <2.0 g/dL.",
    },
    "Testicular Torsion": {
        "symptoms": [
            "sudden severe testicular pain", "unilateral scrotal pain", "high-riding testicle",
            "horizontal lie of testicle", "absent cremasteric reflex", "scrotal swelling",
            "scrotal erythema", "nausea", "vomiting", "abdominal pain", "negative prehn sign"
        ],
        "cardinal_symptoms": ["absent cremasteric reflex", "high-riding testicle", "sudden severe testicular pain"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["renal_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
        "prevalence": "moderate",
        "_investigations": [
            "EMERGENT SURGICAL EVALUATION: Clinical diagnosis, surgical exploration should NOT be delayed for imaging!",
            "Color Doppler scrotal ultrasound (absence of testicular blood flow, whirlpool sign of twisted spermatic cord)",
            "Urinalysis (usually normal, excludes epididymitis)",
        ],
        "_treatment_summary": "TIME-CRITICAL SURGICAL EMERGENCY: Viability window <6 hours. Emergent surgical scrotal exploration, manual/surgical detorsion, and bilateral orchiopexy (bell-clapper deformity is bilateral).",
    },

    # -----------------------------------------------------------------------
    # RHEUMATOLOGY & AUTOIMMUNE
    # -----------------------------------------------------------------------
    "Ankylosing Spondylitis": {
        "symptoms": [
            "inflammatory back pain", "chronic low back pain", "morning stiffness >30 minutes",
            "back pain improves with exercise", "back pain worse with rest", "buttock pain",
            "sacroiliac joint pain", "enthesitis", "achilles tendonitis", "anterior uveitis", "bamboo spine"
        ],
        "cardinal_symptoms": ["inflammatory back pain", "morning stiffness >30 minutes", "back pain improves with exercise"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["autoimmune_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "moderate",
        "prevalence": "common",
        "_investigations": [
            "Pelvic Radiograph (sacroiliitis: sclerosis, joint erosion, ankylosis) and Spine Radiograph ('bamboo spine', syndesmophytes)",
            "MRI of sacroiliac joints (STIR sequences show bone marrow edema in active non-radiographic axial SpA)",
            "HLA-B27 genetic testing (>90% positive in white patients)",
            "ESR and CRP (elevated in 50-70% of active patients)",
        ],
        "_treatment_summary": "First-line: Continuous oral NSAIDs (Naproxen, Celecoxib) combined with dedicated spinal physical therapy. Refractory disease: Biologic DMARDs (TNF inhibitors: Adalimumab, Infliximab, Etanercept, or IL-17 inhibitors: Secukinumab).",
    },
    "Sjogren's Syndrome": {
        "symptoms": [
            "keratoconjunctivitis sicca", "dry eyes", "gritty eyes", "xerostomia", "dry mouth",
            "difficulty swallowing dry food", "bilateral parotid swelling", "dental caries",
            "joint pain", "arthralgia", "profound fatigue", "raynaud phenomenon"
        ],
        "cardinal_symptoms": ["dry eyes", "dry mouth", "bilateral parotid swelling"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["autoimmune_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "moderate",
        "prevalence": "common",
        "_investigations": [
            "Serum anti-SSA (Ro) and anti-SSB (La) autoantibodies",
            "Schirmer's test (filter paper strip wetting ≤5mm in 5 minutes confirms dry eyes)",
            "Rose Bengal or Lissamine Green ocular surface staining",
            "Minor salivary gland (lip) biopsy (focal lymphocytic sialadenitis with focus score ≥1 per 4 mm2)",
        ],
        "_treatment_summary": "Symptomatic lubrication: Preservative-free artificial tears, ocular lubricants, oral saliva substitutes. Secretagogues: Pilocarpine (5mg TDS) or Cevimeline. Hydroxychloroquine for systemic arthralgias and fatigue.",
    },

    # -----------------------------------------------------------------------
    # PEDIATRICS & INFECTIOUS
    # -----------------------------------------------------------------------
    "Kawasaki Disease": {
        "symptoms": [
            "high fever >5 days", "bilateral conjunctival injection", "non-purulent conjunctivitis",
            "strawberry tongue", "erythema of lips", "cracked lips", "cervical lymphadenopathy",
            "polymorphous rash", "erythema of palms and soles", "edema of hands and feet",
            "periungual desquamation", "irritability", "coronary artery aneurysm risk"
        ],
        "cardinal_symptoms": ["high fever >5 days", "strawberry tongue", "bilateral conjunctival injection", "periungual desquamation"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["rash_fever", "lymphadenopathy_fever"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
        "prevalence": "moderate",
        "_investigations": [
            "Transthoracic Echocardiography (mandatory at diagnosis, 2 weeks, and 6-8 weeks to detect coronary artery dilation/aneurysm)",
            "Complete blood count (normocytic anemia, leukocytosis with left shift, marked thrombocytosis >500k in 2nd week)",
            "Serum inflammatory markers (ESR >40 mm/hr, CRP >30 mg/L)",
            "Liver function tests (hypoalbuminemia, elevated transaminases) and sterile pyuria on urinalysis",
        ],
        "_treatment_summary": "EARLY TREATMENT WITHIN 10 DAYS PREVENTS CORONARY ANEURYSMS: High-dose Intravenous Immunoglobulin (IVIG 2g/kg as single 12-hour infusion) PLUS high-dose Aspirin (30-50 mg/kg/day until afebrile for 48h, then low-dose 3-5 mg/kg/day antiplatelet for 6-8 weeks).",
    },
    "Henoch-Schonlein Purpura (IgA Vasculitis)": {
        "symptoms": [
            "palpable purpura", "petechiae on lower extremities", "buttock purpura",
            "colicky abdominal pain", "arthralgia", "joint pain of knees and ankles",
            "hematuria", "blood in urine", "proteinuria", "recent upper respiratory infection"
        ],
        "cardinal_symptoms": ["palpable purpura", "colicky abdominal pain", "arthralgia", "hematuria"],
        "hemorrhagic": True,
        "geographic_zones": ["Global"],
        "clusters": ["rash_fever", "renal_syndrome", "acute_abdomen"],
        "incubation_min": 7, "incubation_max": 21,
        "severity": "high",
        "prevalence": "common",
        "_investigations": [
            "Clinical diagnosis (EULAR/PRINTO/PRES criteria: palpable purpura without thrombocytopenia + abdominal pain, IgA on biopsy, arthralgia, or renal involvement)",
            "Urinalysis and UPCR (screen for microscopic hematuria and proteinuria; monitor weekly for 2 months)",
            "Platelet count and coagulation profile (normal platelets rule out ITP/thrombocytopenic purpura)",
            "Skin punch biopsy with direct immunofluorescence (leukocytoclastic vasculitis with IgA immune complexes)",
        ],
        "_treatment_summary": "Supportive care (hydration, rest, analgesia). Systemic corticosteroids (oral Prednisone 1-2 mg/kg/day for 2 weeks) for severe abdominal pain or glomerulonephritis. Routine monitoring of BP and urinalysis for 6 months.",
    },
    "Acute Epiglottitis": {
        "symptoms": [
            "severe sore throat", "odynophagia", "drooling", "difficulty swallowing",
            "tripod position", "leaning forward", "inspiratory stridor", "muffled voice",
            "hot potato voice", "high fever", "toxic appearance", "respiratory distress"
        ],
        "cardinal_symptoms": ["drooling", "tripod position", "inspiratory stridor", "hot potato voice"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["respiratory_distress"],
        "incubation_min": 1, "incubation_max": 3,
        "severity": "critical",
        "prevalence": "rare",
        "_investigations": [
            "DO NOT AGITATE THE PATIENT: Do NOT perform oral exam or tongue depression without emergency airway equipment ready!",
            "Fiberoptic laryngoscopy in controlled OR setting (cherry-red, swollen epiglottis)",
            "Lateral soft-tissue neck radiograph (classic 'thumbprint sign' representing enlarged epiglottis; only if stable)",
            "Blood cultures after airway is secured",
        ],
        "_treatment_summary": "CRITICAL AIRWAY EMERGENCY: Immediate endotracheal intubation in operating room by most experienced clinician. IV Ceftriaxone (2g daily) PLUS IV Vancomycin (MRSA coverage). IV Dexamethasone to reduce airway edema.",
    },
    "Lyme Disease (Early Localized / Disseminated)": {
        "symptoms": [
            "erythema migrans", "bullseye rash", "expanding target rash", "tick bite history",
            "fever", "fatigue", "headache", "myalgia", "neck stiffness", "facial palsy",
            "bell palsy", "av block", "migratory arthritis"
        ],
        "cardinal_symptoms": ["erythema migrans", "bullseye rash", "tick bite history"],
        "hemorrhagic": False,
        "geographic_zones": ["Global", "North America", "Europe"],
        "clusters": ["rash_fever", "zoonotic"],
        "incubation_min": 3, "incubation_max": 30,
        "severity": "moderate",
        "prevalence": "common",
        "_investigations": [
            "Clinical diagnosis: Erythema migrans rash (≥5 cm expanding with central clearing) in an endemic area is diagnostic without serology!",
            "Two-tiered serologic testing (ELISA screen followed by confirmatory Western Blot IgM and IgG if symptoms >30 days)",
            "ECG (screen for Lyme carditis / AV nodal conduction block)",
        ],
        "_treatment_summary": "Oral Doxycycline 100mg BD for 10-14 days (first-line for adults and children). Alternatives: Amoxicillin 500mg TDS or Cefuroxime axetil (for pregnant women). IV Ceftriaxone 2g daily for neurologic (meningitis) or cardiac involvement.",
    },

    # -----------------------------------------------------------------------
    # TOXICOLOGY & ALLERGIC EMERGENCIES
    # -----------------------------------------------------------------------
    "Anaphylaxis": {
        "symptoms": [
            "urticaria", "hives", "angioedema", "facial swelling", "lip swelling", "tongue swelling",
            "stridor", "wheezing", "shortness of breath", "hypotension", "dizziness",
            "syncope", "diarrhea", "vomiting", "sense of impending doom"
        ],
        "cardinal_symptoms": ["angioedema", "stridor", "urticaria", "hypotension"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["cardiovascular_shock", "respiratory_distress"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
        "prevalence": "common",
        "_investigations": [
            "CLINICAL DIAGNOSIS: Treatment must not be delayed for any lab or test!",
            "Serum total tryptase (drawn 1-2 hours post-reaction to confirm mast cell activation)",
            "Continuous pulse oximetry, non-invasive BP, and 12-lead ECG monitoring",
        ],
        "_treatment_summary": "IMMEDIATE FIRST-LINE: Intramuscular Epinephrine 0.3–0.5mg (1:1000) in anterolateral mid-thigh, repeated every 5–15 minutes PRN. Aggressive IV crystalloids (1–2L bolus). Supplemental oxygen. Secondary: IV H1/H2 antihistamines and Methylprednisolone.",
    },
    "Neuroleptic Malignant Syndrome (NMS)": {
        "symptoms": [
            "lead-pipe rigidity", "severe muscle rigidity", "hyperthermia", "high fever",
            "autonomic instability", "tachycardia", "labile blood pressure", "diaphoresis",
            "altered mental status", "stupor", "coma", "antipsychotic history"
        ],
        "cardinal_symptoms": ["lead-pipe rigidity", "hyperthermia", "autonomic instability", "altered mental status"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["endocrine_crisis"],
        "incubation_min": 1, "incubation_max": 14,
        "severity": "critical",
        "prevalence": "rare",
        "_investigations": [
            "Serum Creatine Kinase (CK - markedly elevated, often >10,000 U/L)",
            "Comprehensive Metabolic Panel (hyperkalemia, acute kidney injury secondary to rhabdomyolysis)",
            "Urine myoglobin and urinalysis (positive blood on dipstick without RBCs confirms myoglobinuria)",
            "Complete blood count (leukocytosis)",
        ],
        "_treatment_summary": "IMMEDIATE DISCONTINUATION OF ALL NEUROLEPTIC AGENTS. Aggressive cooling and IV hydration to prevent renal failure. Dopamine agonists: Bromocriptine (2.5mg oral TDS) or Amantadine. Muscle relaxant: Dantrolene (1-2.5 mg/kg IV).",
    },
    "Acute Ischemic Stroke (CVA)": {
        "symptoms": [
            "facial drooping", "facial droop", "unilateral weakness", "arm weakness", "leg weakness",
            "hemiparesis", "aphasia", "expressive aphasia", "slurred speech", "dysarthria",
            "ataxia", "severe hypertension", "hypertension", "irregularly irregular pulse",
            "visual field cut", "hemisensory loss"
        ],
        "cardinal_symptoms": ["facial drooping", "unilateral weakness", "aphasia", "hemiparesis"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
        "prevalence": "common",
        "_investigations": [
            "STAT Non-contrast Head CT (rule out intracranial hemorrhage immediately)",
            "CT Angiography (CTA) of Head and Neck (screen for large vessel occlusion / LVO)",
            "Fingerstick blood glucose (rule out hypoglycemia mimic)",
            "12-Lead ECG (screen for atrial fibrillation)",
            "NIH Stroke Scale (NIHSS) standardized score calculation",
        ],
        "_treatment_summary": "Activate Code Stroke. IV Thrombolysis (Alteplase/Tenecteplase) within 4.5 hours of last known well if eligible. Emergency Mechanical Thrombectomy for anterior circulation LVO up to 24 hours. Permissive hypertension unless thrombolytic candidate.",
    },
    "Preeclampsia with Severe Features": {
        "symptoms": [
            "severe hypertension", "hypertension", "proteinuria", "headache", "blurred vision",
            "scotoma", "right upper quadrant pain", "epigastric pain", "pregnancy",
            "brisk reflexes", "clonus", "bilateral leg swelling", "edema", "shortness of breath", "thrombocytopenia"
        ],
        "cardinal_symptoms": ["severe hypertension", "proteinuria", "headache", "blurred vision", "pregnancy", "right upper quadrant pain"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["obstetric_syndrome", "headache_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
        "prevalence": "common",
        "_investigations": [
            "Serial blood pressure monitoring (q15m until stabilized)",
            "Urinalysis / Urine protein-to-creatinine ratio (or 24-hr urine protein >300 mg)",
            "Complete blood count (platelet count <100,000/microL)",
            "Comprehensive metabolic panel (AST/ALT >2x ULN, serum creatinine >1.1 mg/dL)",
            "Serum uric acid and LDH",
            "Continuous electronic fetal heart rate monitoring",
        ],
        "_treatment_summary": "Immediate IV Magnesium Sulfate (4–6g loading over 20 min, then 1–2g/hr continuous) for seizure prophylaxis. Acute antihypertensive therapy: IV Labetalol (20–80mg) or IV Hydralazine (5–10mg) to maintain SBP <160 and DBP <110. Plan urgent obstetric delivery.",
    },
    "Systemic Lupus Erythematosus (SLE)": {
        "symptoms": [
            "malar rash", "photosensitive rash", "joint pain", "joint swelling", "morning stiffness",
            "pleuritic chest pain", "fatigue", "fever", "oral ulcers", "hair loss",
            "proteinuria", "positive antinuclear antibody", "positive anti-dsDNA", "hypocomplementemia", "Raynaud phenomenon"
        ],
        "cardinal_symptoms": ["malar rash", "photosensitive rash", "joint pain", "positive antinuclear antibody", "positive anti-dsDNA", "hypocomplementemia"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["autoimmune_syndrome", "rash_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
        "prevalence": "moderate",
        "_investigations": [
            "Antinuclear antibodies (ANA by immunofluorescence - >98% sensitivity)",
            "Anti-double-stranded DNA (anti-dsDNA) antibodies (highly specific, correlates with lupus nephritis)",
            "Anti-Smith (anti-Sm) antibodies (pathognomonic specificity)",
            "Serum complement levels (C3, C4 - consumed during active flares)",
            "Urinalysis with urine microscopy (casts, hematuria, proteinuria)",
            "Complete Blood Count (leukopenia, lymphopenia, hemolytic anemia, thrombocytopenia)",
        ],
        "_treatment_summary": "Hydroxychloroquine (200–400mg daily) for all patients to reduce mortality and flares. Systemic corticosteroids for acute disease flares. Immunosuppressants (Mycophenolate mofetil, cyclophosphamide, or belimumab) for organ-threatening nephritis.",
    },
    "Acute Heart Failure (Cardiogenic Pulmonary Edema)": {
        "symptoms": [
            "shortness of breath", "dyspnea", "orthopnea", "paroxysmal nocturnal dyspnea", "crackles",
            "S3 gallop", "S4 gallop", "elevated JVP", "bilateral leg swelling", "hypoxia",
            "tachycardia", "severe hypertension", "fatigue"
        ],
        "cardinal_symptoms": ["orthopnea", "paroxysmal nocturnal dyspnea", "crackles", "elevated JVP", "bilateral leg swelling"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["respiratory_syndrome", "cardiovascular_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
        "prevalence": "common",
        "_investigations": [
            "B-type Natriuretic Peptide (BNP >100 pg/mL or NT-proBNP >300 pg/mL)",
            "Transthoracic Echocardiogram (TTE - ejection fraction, diastolic function, valve pathology)",
            "Chest X-ray (cardiomegaly, cephalization, Kerley B lines, pleural effusions)",
            "12-Lead ECG (acute ischemia, arrhythmia, LVH)",
            "High-sensitivity cardiac troponin, basic metabolic panel, serum electrolytes",
        ],
        "_treatment_summary": "IV loop diuretics (Furosemide 40–80mg IV bolus). Non-invasive positive pressure ventilation (BiPAP/CPAP) for respiratory failure and pulmonary edema. IV vasodilators (Nitroglycerin infusion) if SBP >120 mmHg. Position patient upright.",
    },
    "Acute Pancreatitis": {
        "symptoms": [
            "severe epigastric pain", "epigastric pain", "pain radiating to back", "nausea", "vomiting",
            "tachycardia", "abdominal distension", "fever", "guarding", "jaundice"
        ],
        "cardinal_symptoms": ["severe epigastric pain", "pain radiating to back", "nausea", "vomiting"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["abdominal_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
        "prevalence": "common",
        "_investigations": [
            "Serum Lipase (elevated >3x upper limit of normal, gold standard diagnostic enzyme)",
            "Serum Amylase",
            "Abdominal Ultrasound (screen for gallstones, biliary sludge, CBD dilatation)",
            "Contrast-enhanced CT Abdomen and Pelvis (after 48–72 hours to evaluate necrosis and peripancreatic fluid collections)",
            "Comprehensive Metabolic Panel, calcium, triglycerides, CBC, liver enzymes",
        ],
        "_treatment_summary": "Aggressive goal-directed IV fluid resuscitation (Lactated Ringer's 200–500 mL/hr guided by hemodynamics and urine output). Multimodal IV analgesia. Early oral feeding as tolerated once pain improves. Urgent ERCP within 24h for gallstone pancreatitis with cholangitis.",
    },
    "Septic Shock / Severe Sepsis": {
        "symptoms": [
            "hypotension", "fever", "hypothermia", "tachycardia", "tachypnea",
            "altered consciousness", "confusion", "reduced urine output", "shortness of breath", "chills", "leukocytosis"
        ],
        "cardinal_symptoms": ["hypotension", "fever", "tachycardia", "altered consciousness", "reduced urine output"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["septic_syndrome", "infectious_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
        "prevalence": "common",
        "_investigations": [
            "Serum Lactate (stat measurement and repeat q2–4h to assess clearance)",
            "Blood cultures x2 (drawn before initiating antimicrobials)",
            "Source identification: Urinalysis/culture, CXR, sputum culture, skin/soft tissue assessment",
            "Complete blood count with differential, PT/INR, PTT, Comprehensive Metabolic Panel",
            "Arterial Blood Gas (ABG) for acid-base status and oxygenation",
        ],
        "_treatment_summary": "Surviving Sepsis Campaign Hour-1 Bundle: 30 mL/kg IV crystalloid fluid resuscitation for hypotension or lactate ≥4. Broad-spectrum empiric IV antibiotics within 1 hour. Vasopressors (Norepinephrine first-line) to target MAP ≥65 mmHg if hypotension persists.",
    },
    "Community-Acquired Pneumonia (Lobar Pneumonia)": {
        "symptoms": [
            "fever", "chills", "cough", "purulent sputum", "pleuritic chest pain",
            "shortness of breath", "crackles", "tachypnea", "tachycardia", "hypoxia", "fatigue"
        ],
        "cardinal_symptoms": ["fever", "cough", "purulent sputum", "crackles", "pleuritic chest pain"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["respiratory_syndrome", "infectious_syndrome"],
        "incubation_min": 1, "incubation_max": 14,
        "severity": "moderate",
        "prevalence": "common",
        "_investigations": [
            "Chest Radiograph (CXR - demonstrates lobar consolidation, air bronchograms, or alveolar infiltrates)",
            "Complete Blood Count (leukocytosis >12,000/microL with left shift)",
            "Sputum Gram stain and culture (if hospitalized or severe)",
            "Blood cultures x2 (for severe/ICU-admitted pneumonia)",
            "Pulse oximetry, serum CRP, and serum Procalcitonin",
        ],
        "_treatment_summary": "Empiric antimicrobial therapy: Outpatient without comorbidities: Amoxicillin or Doxycycline. Inpatient non-ICU: IV Ceftriaxone + Azithromycin or respiratory fluoroquinolone (Levofloxacin). Supplemental oxygen to maintain SpO2 94–98%.",
    },

    # -----------------------------------------------------------------------
    # RARE, METABOLIC, GENETIC & RHEUMATOLOGIC COMPLEX DISORDERS (CASES 36-48)
    # -----------------------------------------------------------------------
    "Insulin Autoimmune Syndrome (Hirata Disease)": {
        "symptoms": [
            "hypoglycemia", "postprandial hypoglycemia", "neuroglycopenia", "fatigue",
            "confusion", "sweating", "tremor", "blurred vision", "presyncope", "hyperinsulinism",
            "elevated C-peptide", "suppressed ketogenesis", "thiol supplement exposure",
            "insulin autoantibodies", "loss of consciousness"
        ],
        "cardinal_symptoms": ["hypoglycemia", "postprandial hypoglycemia", "hyperinsulinism", "insulin autoantibodies"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["endocrine_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
        "prevalence": "rare",
        "_investigations": [
            "Serum Insulin Autoantibody (IAA) titer (markedly elevated polyclonal IgG)",
            "72-hour supervised fast or prolonged oral glucose tolerance test (OGTT showing paradoxical postprandial hypoglycemia)",
            "Concurrent serum glucose, insulin (>100 microU/mL), and C-peptide levels during hypoglycemia",
            "Serum sulfonylurea screen (negative)",
            "Pancreatic MRI / Endoscopic Ultrasound (EUS to definitively rule out insulinoma)",
            "HLA class II typing (DRB1*04:06 strongly associated)",
        ],
        "_treatment_summary": "Discontinuation of offending sulfhydryl/thiol-containing medications/supplements (alpha-lipoic acid, glutathione). Frequent small low-carbohydrate meals with alpha-glucosidase inhibitors (Acarbose). Systemic corticosteroids or plasmapheresis / Rituximab for refractory cases.",
    },
    "Pachydermoperiostosis (Primary Hypertrophic Osteoarthropathy)": {
        "symptoms": [
            "digital clubbing", "pachydermia", "periostosis", "hyperhidrosis", "bone pain",
            "joint swelling", "joint pain", "knee and ankle pain", "elevated inflammatory markers",
            "autosomal dominant inheritance", "fatigue"
        ],
        "cardinal_symptoms": ["digital clubbing", "pachydermia", "periostosis"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["skeletal_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "moderate",
        "prevalence": "rare",
        "_investigations": [
            "Skeletal survey / Plain radiographs of long bones (symmetric periosteal hyperostosis / new bone formation sparing epiphyses)",
            "Chest CT / Echocardiography (exclude secondary pulmonary or cyanotic cardiac causes of clubbing)",
            "Genetic testing for HPGD and SLCO2A1 mutations (prostaglandin metabolism pathway)",
            "Urinary prostaglandin E2 (PGE2) and PGE-metabolite (PGE-M) levels (elevated)",
            "Serum inflammatory markers (ESR/CRP) and autoimmune panel (negative)",
        ],
        "_treatment_summary": "Non-steroidal anti-inflammatory drugs (NSAIDs) for chronic arthralgia/bone pain. Prostaglandin synthesis inhibitors or selective COX-2 inhibitors. Corticosteroids or Pamidronate/Zoledronic acid (bisphosphonates) for refractory bone pain. Plastic surgery for facial pachydermia.",
    },
    "Acute Intermittent Porphyria (AIP)": {
        "symptoms": [
            "severe abdominal pain", "pain out of proportion to exam", "port-wine urine", "dark urine",
            "peripheral neuropathy", "paresthesias", "weakness", "tachycardia", "anxiety",
            "hyponatremia", "confusion", "heme biosynthesis defect", "porphyrinogenic drug trigger",
            "nausea", "vomiting", "constipation"
        ],
        "cardinal_symptoms": ["severe abdominal pain", "pain out of proportion to exam", "port-wine urine", "heme biosynthesis defect"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["metabolic_syndrome", "neurological_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
        "prevalence": "rare",
        "_investigations": [
            "Urinary porphobilinogen (PBG) and delta-aminolevulinic acid (ALA) quantitative measurement (light-protected sample; markedly elevated during acute attacks)",
            "Erythrocyte hydroxymethylbilane synthase (HMBS / PBG deaminase) enzyme activity",
            "HMBS gene sequence analysis (identifies pathogenic mutation)",
            "Serum electrolytes (hyponatremia secondary to SIADH or GI loss)",
            "Abdominal CT (typically negative, confirming non-surgical acute abdomen)",
        ],
        "_treatment_summary": "Immediate IV Hemin (Panhematin 3–4 mg/kg daily for 4 days) to repress hepatic ALA synthase. IV 10% Dextrose infusion (glucose loading suppresses ALAS1). Stop all porphyrinogenic medications (barbiturates, sulfonamides, progesterone). IV analgesia (opioids) and antiemetics.",
    },
    "Duchenne Muscular Dystrophy (DMD)": {
        "symptoms": [
            "difficulty walking", "frequent falls", "clumsiness", "Gowers sign", "proximal muscle weakness",
            "calf pseudohypertrophy", "waddling gait", "markedly elevated CK", "myopathic EMG",
            "X-linked family history", "subclinical cardiomyopathy"
        ],
        "cardinal_symptoms": ["proximal muscle weakness", "calf pseudohypertrophy", "Gowers sign", "markedly elevated CK"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["neuromuscular_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
        "prevalence": "rare",
        "_investigations": [
            "Serum Creatine Kinase (CK - markedly elevated, typically 10 to 100 times normal limit, >10,000 U/L)",
            "Genetic multiplex ligation-dependent probe amplification (MLPA) or Next-Gen sequencing of the DMD gene (dystrophin deletion/duplication)",
            "Electromyography (EMG - demonstrates classic myopathic pattern with short-duration, low-amplitude polyphasic potentials)",
            "Muscle biopsy (dystrophin immunostaining and Western blot showing absent or near-absent dystrophin)",
            "Echocardiogram and cardiac MRI (screen for dilated cardiomyopathy and fibrosis)",
        ],
        "_treatment_summary": "Systemic corticosteroids (Prednisone 0.75 mg/kg/day or Deflazacort 0.9 mg/kg/day) to prolong ambulation and cardiopulmonary function. Exon-skipping antisense oligonucleotides (Eteplirsen, Golodirsen) or gene therapy (Delandistrogene moxeparvovec) where indicated. Multidisciplinary physical therapy and pulmonary surveillance.",
    },
    "Gyrate Atrophy of the Choroid and Retina": {
        "symptoms": [
            "nyctalopia", "difficulty seeing at night", "peripheral visual field loss", "visual impairment",
            "retinal degeneration", "chorioretinal atrophy", "amino acid transport defect", "hyperornithinemia",
            "muscle weakness", "reduced reflexes", "electroretinography impairment"
        ],
        "cardinal_symptoms": ["nyctalopia", "peripheral visual field loss", "retinal degeneration", "amino acid transport defect"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["ophthalmic_syndrome", "metabolic_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "moderate",
        "prevalence": "rare",
        "_investigations": [
            "Plasma and urinary amino acid chromatography (demonstrating marked 10–20-fold elevation of plasma ornithine: hyperornithinemia)",
            "Full-field Electroretinography (ERG - markedly diminished to non-recordable scotopic and photopic responses)",
            "Dilated funduscopic examination (characteristic sharply demarcated, scalloped circular areas of chorioretinal atrophy in mid-periphery)",
            "OAT gene molecular genetic testing (ornithine aminotransferase deficiency)",
            "Visual field testing (Humphrey visual field showing progressive peripheral constriction / tunnel vision)",
        ],
        "_treatment_summary": "Strict dietary arginine restriction (low-protein diet to lower toxic ornithine levels). Trial of high-dose Pyridoxine (Vitamin B6 300–500 mg/day) for B6-responsive OAT mutations. Creatine supplementation (to replenish cerebral/muscle creatine depleted by hyperornithinemia).",
    },
    "Cryopyrin-Associated Periodic Syndrome (CAPS Spectrum / Muckle-Wells / FCAS)": {
        "symptoms": [
            "recurrent fever", "infantile onset", "urticarial rash", "chronic joint pain", "joint swelling",
            "sensorineural hearing loss", "elevated inflammatory markers", "autoinflammatory syndrome",
            "NLRP3 mutation", "fatigue", "irritability"
        ],
        "cardinal_symptoms": ["recurrent fever", "urticarial rash", "sensorineural hearing loss", "autoinflammatory syndrome"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["autoinflammatory_syndrome", "febrile_illness"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
        "prevalence": "rare",
        "_investigations": [
            "NLRP3 (CIAS1) molecular genetic sequencing (heterozygous gain-of-function mutation causing hyperactive cryopyrin inflammasome)",
            "Serum inflammatory markers (markedly elevated ESR, CRP, and Serum Amyloid A [SAA] during and between attacks)",
            "Pure tone audiometry (demonstrates progressive bilateral high-frequency sensorineural hearing loss)",
            "Skin biopsy of rash (perivascular neutrophilic infiltrate without true leukocytoclastic vasculitis)",
            "Renal function and urinalysis (monitor for secondary AA amyloidosis)",
        ],
        "_treatment_summary": "Targeted Interleukin-1 (IL-1) blockade: Anakinra (recombinant IL-1 receptor antagonist daily), Canakinumab (fully human anti-IL-1beta monoclonal antibody q8w), or Rilonacept (IL-1 trap). Dramatic symptom resolution and prevention of hearing loss and amyloidosis.",
    },
    "Idiopathic Inflammatory Myopathy (Suspected Anti-Synthetase Syndrome / Dermatomyositis Spectrum)": {
        "symptoms": [
            "dysphagia", "proximal muscle weakness", "neck flexor weakness", "perifascicular atrophy",
            "interstitial lung disease", "rapidly progressive dyspnea", "restrictive lung disease",
            "elevated CK", "myositis-specific antibody", "myopathic EMG", "cough"
        ],
        "cardinal_symptoms": ["perifascicular atrophy", "interstitial lung disease", "proximal muscle weakness", "myositis-specific antibody"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["rheumatologic_syndrome", "pulmonary_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
        "prevalence": "rare",
        "_investigations": [
            "High-Resolution Computed Tomography (HRCT) of chest (bilateral ground-glass opacities, subpleural consolidation, traction bronchiectasis / NSIP or OP pattern)",
            "Extended Myositis Autoantibody Panel (anti-Jo-1 [histidyl-tRNA synthetase], anti-PL-7, anti-PL-12, anti-MDA5)",
            "Muscle biopsy (pathognomonic perifascicular muscle fiber atrophy and perivascular/perimysial inflammation)",
            "Pulmonary Function Tests (PFTs - reduced FVC and severely decreased DLCO with restrictive physiology)",
            "Serum Creatine Kinase (CK) and Aldolase (mild-to-moderately elevated)",
        ],
        "_treatment_summary": "High-dose systemic corticosteroids (oral Prednisone 1 mg/kg/day or IV pulse Methylprednisolone). Early combination with steroid-sparing immunosuppressants: Mycophenolate Mofetil, Tacrolimus, or Cyclophosphamide for rapidly progressive ILD. IVIG or Rituximab for refractory pulmonary disease.",
    },
    "Collodion Baby Phenotype (Underlying Congenital Ichthyosis suspected)": {
        "symptoms": [
            "collodion membrane", "shiny membrane covering body at birth", "cracking and peeling of skin",
            "ectropion", "eclabium", "impaired thermoregulation", "recurrent dehydration",
            "ichthyosis", "disorder of cornification"
        ],
        "cardinal_symptoms": ["collodion membrane", "ectropion", "ichthyosis", "disorder of cornification"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["dermatological_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
        "prevalence": "rare",
        "_investigations": [
            "Clinical dermatological examination (parchment-like taut membrane, bilateral ectropion, eclabium, hypoplasia of nasal/auricular cartilage)",
            "Serum electrolytes, BUN, creatinine (vigorous monitoring for hypernatremic dehydration from trans-epidermal water loss)",
            "Targeted gene panel sequencing for congenital ichthyosis (TGM1, ALOXE3, ALOX12B, ABCA12, CYP4F22)",
            "Bacterial and fungal skin swabs (frequent monitoring for cutaneous superinfections and sepsis)",
        ],
        "_treatment_summary": "Neonatal Intensive Care Unit (NICU) admission with high-humidity humidified incubator (≥70-80%). Liberal application of sterile petrolatum/bland emollients (avoid keratolytics due to systemic absorption). Gentle ophthalmologic lubrication for ectropion. Strict fluid and electrolyte balance management.",
    },
    "Mitochondrial Encephalopathy (Differential includes MELAS, MERRF, Mitochondrial Ataxia)": {
        "symptoms": [
            "migraine-like headaches", "vertigo", "ataxia", "nystagmus", "brainstem/cerebellar lesions",
            "cerebral white matter lesions", "maternal inheritance", "mitochondrial DNA defect",
            "vomiting", "dysarthria", "inability to walk"
        ],
        "cardinal_symptoms": ["migraine-like headaches", "ataxia", "brainstem/cerebellar lesions", "maternal inheritance", "mitochondrial DNA defect"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_syndrome", "metabolic_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
        "prevalence": "rare",
        "_investigations": [
            "Brain MRI with MR Spectroscopy (MRS - cortical/subcortical infarct-like lesions crossing vascular territories, inverted lactate doublet peak at 1.3 ppm)",
            "Mitochondrial DNA (mtDNA) point mutation analysis in blood, saliva, or urinary epithelial cells (e.g. m.3243A>G in MT-TL1)",
            "Plasma and CSF lactate and pyruvate levels (elevated resting lactate or exaggerated increase after exercise)",
            "Audiometry and retinal exam (screen for sensorineural hearing loss and pigmentary retinopathy)",
            "Muscle biopsy (modified Gomori trichrome stain demonstrating ragged-red fibers [RRF] and COX-negative fibers)",
        ],
        "_treatment_summary": "IV L-Arginine (0.5 g/kg during acute stroke-like attacks to promote nitric oxide vasodilation and tissue perfusion). Maintenance oral L-Arginine or L-Citrulline. Mitochondrial cocktail (Coenzyme Q10, L-Carnitine, Riboflavin, Thiamine). Avoid mitochondrial toxins (valproate, metformin, statins).",
    },
    "Carnitine Palmitoyltransferase II (CPT II) Deficiency": {
        "symptoms": [
            "rhabdomyolysis", "exercise-induced myoglobinuria", "dark urine",
            "exercise intolerance after prolonged exertion", "muscle weakness", "massive CK elevation",
            "myoglobinuria", "fatty acid oxidation defect", "acute kidney injury", "maternal family history"
        ],
        "cardinal_symptoms": ["rhabdomyolysis", "exercise-induced myoglobinuria", "massive CK elevation", "fatty acid oxidation defect"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["metabolic_syndrome", "neuromuscular_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
        "prevalence": "rare",
        "_investigations": [
            "Serum Creatine Kinase (CK - dramatically elevated during attacks, often >50,000–100,000 U/L)",
            "Urinalysis (strongly dipstick positive for heme/blood with absence of intact erythrocytes on microscopy: myoglobinuria)",
            "Acylcarnitine profile via tandem mass spectrometry (MS/MS - elevated long-chain acylcarnitines: C16, C18:1, and C18:2 with high [C16+C18:1]/C2 ratio)",
            "Molecular genetic testing of CPT2 gene (common p.Ser113Leu mutation in adult myopathic form)",
            "Serum electrolytes, BUN, creatinine (monitor for acute kidney injury / pigment nephropathy)",
        ],
        "_treatment_summary": "Vigorous IV crystalloid hydration (saline with sodium bicarbonate to alkalize urine and prevent acute tubular necrosis from myoglobin casts). High-carbohydrate, low-fat diet. Medium-chain triglyceride (MCT) oil supplementation (bypasses CPT shuttle). Avoid prolonged fasting, extreme exertion, and cold exposure.",
    },
    "Subacute Necrotizing Encephalomyelopathy (Suspected Leigh Syndrome / Mitochondrial Neurodegeneration)": {
        "symptoms": [
            "developmental regression", "loss of motor skills", "ataxia", "tremor", "nystagmus",
            "dysarthria", "brainstem and basal ganglia lesions", "sibling death in childhood",
            "mitochondrial encephalomyopathy", "reduced reflexes", "hypotonia"
        ],
        "cardinal_symptoms": ["developmental regression", "ataxia", "brainstem and basal ganglia lesions", "mitochondrial encephalomyopathy"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_syndrome", "metabolic_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
        "prevalence": "rare",
        "_investigations": [
            "Brain MRI (pathognomonic bilateral, symmetric T2/FLAIR hyperintensities in basal ganglia [putamen, globus pallidus], substantia nigra, brainstem, and dentate nuclei)",
            "Targeted nuclear and mitochondrial whole-exome sequencing (mutations in SURF1, MT-ATP6, NDUFV1, PDHA1)",
            "Serum and CSF lactate and pyruvate (consistently elevated lactate:pyruvate ratio)",
            "MR Spectroscopy (MRS - elevated lactate peak in basal ganglia lesions)",
            "Echocardiography (screen for hypertrophic cardiomyopathy)",
        ],
        "_treatment_summary": "Thiamine (vitamin B1 100–300 mg/day) and Biotin supplementation. Coenzyme Q10, L-Carnitine, and Alpha-lipoic acid. High-fat ketogenic diet (specifically in pyruvate dehydrogenase complex [PDHc] deficiency). Aggressive management of infections to avoid metabolic decompensation.",
    },
    "Hereditary Spastic Paraplegia (HSP)": {
        "symptoms": [
            "spastic paraparesis", "progressive weakness of the legs", "stiffness of the legs",
            "lower-limb spasticity", "clonus", "extensor plantar response", "neurogenic bladder",
            "urinary urgency", "preserved sensation", "corticospinal tract abnormalities", "familial spasticity"
        ],
        "cardinal_symptoms": ["spastic paraparesis", "lower-limb spasticity", "clonus", "corticospinal tract abnormalities"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "moderate",
        "prevalence": "rare",
        "_investigations": [
            "Spinal cord and Brain MRI (corticospinal tract hyperintensity, spinal cord atrophy, excludes MS plaques and compressive myelopathy)",
            "Next-Generation Sequencing (NGS) spastic paraplegia multigene panel (SPG4 [spastin], SPG3A [atlastin], SPG7 [paraplegin], SPG11)",
            "Electromyography and nerve conduction studies (NCS - confirms pure upper motor neuron pathology with preserved motor units)",
            "Urodynamic studies (detrusor hyperreflexia / neurogenic bladder)",
            "Serum vitamin B12, folate, copper, HTLV-1/2, and very long chain fatty acids (rule out secondary metabolic myelopathies)",
        ],
        "_treatment_summary": "Oral antispasmodics: Baclofen, Tizanidine, or Dantrolene. Intrathecal Baclofen pump for severe lower-limb spasticity. Anticholinergic therapy (Oxybutynin, Mirabegron) for neurogenic bladder urgency. Regular physical therapy and ankle-foot orthoses (AFOs).",
    },
    "Mitochondrial Energy Metabolism Disorder (Suspected Respiratory Chain Complex Deficiency / Inborn Error of Metabolism)": {
        "symptoms": [
            "metabolic crisis with vomiting and lethargy", "severe metabolic acidosis", "lactic acidosis",
            "fasting hypoglycemia with lactic acidosis", "hypotonia", "hypertrophic cardiomyopathy",
            "developmental delay", "mitochondrial respiratory chain defect", "impaired cellular oxidative metabolism",
            "abdominal pain", "vomiting"
        ],
        "cardinal_symptoms": ["severe metabolic acidosis", "lactic acidosis", "mitochondrial respiratory chain defect"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["metabolic_syndrome", "neurological_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
        "prevalence": "rare",
        "_investigations": [
            "Blood gas, plasma lactate and pyruvate (severe high-anion-gap metabolic acidosis with elevated lactate >5 mmol/L and L:P ratio >20)",
            "Mitochondrial respiratory chain enzyme activity analysis (complex I, II, III, IV spectrophotometric assay on muscle/fibroblasts)",
            "Whole exome / mitochondrial genome sequencing (identifies nuclear or mtDNA respiratory chain complex subunit mutations)",
            "Plasma acylcarnitines and urine organic acids (elevated lactic, pyruvic, and dicarboxylic acids)",
            "Echocardiogram (hypertrophic cardiomyopathy screening)",
        ],
        "_treatment_summary": "Acute emergency stabilization: IV Dextrose 10% with electrolytes to stop catabolism; cautious bicarbonate for profound acidosis (pH <7.1). Cofactor supplementation: Coenzyme Q10 (10–30 mg/kg/day), Riboflavin (vitamin B2), Thiamine, L-Carnitine. Frequent feeds with avoidance of fasting.",
    },
}

# Alias mappings for short/legacy names pointing to primary nuanced entities
EXPANDED_DISEASE_CATALOG["Cryopyrin-Associated Periodic Syndrome (CAPS / Muckle-Wells)"] = EXPANDED_DISEASE_CATALOG["Cryopyrin-Associated Periodic Syndrome (CAPS Spectrum / Muckle-Wells / FCAS)"]
EXPANDED_DISEASE_CATALOG["Anti-Synthetase Syndrome (Amyopathic Dermatomyositis)"] = EXPANDED_DISEASE_CATALOG["Idiopathic Inflammatory Myopathy (Suspected Anti-Synthetase Syndrome / Dermatomyositis Spectrum)"]
EXPANDED_DISEASE_CATALOG["Collodion Baby (Congenital Ichthyosis)"] = EXPANDED_DISEASE_CATALOG["Collodion Baby Phenotype (Underlying Congenital Ichthyosis suspected)"]
EXPANDED_DISEASE_CATALOG["Mitochondrial Encephalopathy (MELAS / Mitochondrial Ataxia)"] = EXPANDED_DISEASE_CATALOG["Mitochondrial Encephalopathy (Differential includes MELAS, MERRF, Mitochondrial Ataxia)"]
EXPANDED_DISEASE_CATALOG["Leigh Syndrome (Subacute Necrotizing Encephalomyelopathy)"] = EXPANDED_DISEASE_CATALOG["Subacute Necrotizing Encephalomyelopathy (Suspected Leigh Syndrome / Mitochondrial Neurodegeneration)"]
EXPANDED_DISEASE_CATALOG["Mitochondrial Complex Deficiency (Lactic Acidosis)"] = EXPANDED_DISEASE_CATALOG["Mitochondrial Energy Metabolism Disorder (Suspected Respiratory Chain Complex Deficiency / Inborn Error of Metabolism)"]

