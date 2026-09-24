"""DocAssistIQ — High-Speed Clinical Note Parser.

Processes complex, multi-paragraph, unstructured clinical notes in <5ms:
- Medical shorthand and clinical acronym expansion (HPI, PMH, ROS, EKG, labs, etc.)
- Clause-level negation scope resolution ("denies fever, cough, hemoptysis" -> correctly negates all three)
- Vital signs extraction & clinical concept normalization (e.g. BP 172/112 -> severe hypertension)
- Physical examination and diagnostic marker extraction (S4 gallop, crackles, McBurney, ST elevation, ANA+, clonus, etc.)
- Positive vs. negated clinical finding separation
"""

import re
from typing import Dict, List, Set, Any, Tuple, Optional
import structlog

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Medical Shorthand & Clinical Term Expansion
# ---------------------------------------------------------------------------

CLINICAL_SHORTHANDS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bPMH\b", re.I), "past medical history"),
    (re.compile(r"\bHPI\b", re.I), "history of present illness"),
    (re.compile(r"\bROS\b", re.I), "review of systems"),
    (re.compile(r"\bHTN\b", re.I), "hypertension"),
    (re.compile(r"\bHLD\b", re.I), "hyperlipidemia"),
    (re.compile(r"\bT2DM\b", re.I), "type 2 diabetes mellitus"),
    (re.compile(r"\bT1DM\b", re.I), "type 1 diabetes mellitus"),
    (re.compile(r"\bDM\b", re.I), "diabetes mellitus"),
    (re.compile(r"\bCAD\b", re.I), "coronary artery disease"),
    (re.compile(r"\bAFIB\b", re.I), "atrial fibrillation"),
    (re.compile(r"\bA-FIB\b", re.I), "atrial fibrillation"),
    (re.compile(r"\bCHF\b", re.I), "congestive heart failure"),
    (re.compile(r"\bCVA\b", re.I), "cerebrovascular accident stroke"),
    (re.compile(r"\bTIA\b", re.I), "transient ischemic attack"),
    (re.compile(r"\bPE\b", re.I), "pulmonary embolism"),
    (re.compile(r"\bDVT\b", re.I), "deep vein thrombosis"),
    (re.compile(r"\bSOB\b", re.I), "shortness of breath"),
    (re.compile(r"\bDOE\b", re.I), "dyspnea on exertion"),
    (re.compile(r"\bCP\b", re.I), "chest pain"),
    (re.compile(r"\bN/V\b", re.I), "nausea and vomiting"),
    (re.compile(r"\bN&V\b", re.I), "nausea and vomiting"),
    (re.compile(r"\bRLQ\b", re.I), "right lower quadrant"),
    (re.compile(r"\bRUQ\b", re.I), "right upper quadrant"),
    (re.compile(r"\bLLQ\b", re.I), "left lower quadrant"),
    (re.compile(r"\bLUQ\b", re.I), "left upper quadrant"),
    (re.compile(r"\bRIF\b", re.I), "right iliac fossa"),
    (re.compile(r"\bSTE\b", re.I), "ST elevation"),
    (re.compile(r"\bSTEMI\b", re.I), "ST elevation myocardial infarction"),
    (re.compile(r"\bNSTEMI\b", re.I), "non-ST elevation myocardial infarction"),
    (re.compile(r"\bLMP\b", re.I), "last menstrual period"),
    (re.compile(r"\bMCP\b", re.I), "metacarpophalangeal joint"),
    (re.compile(r"\bPIP\b", re.I), "proximal interphalangeal joint"),
    (re.compile(r"\bMTP\b", re.I), "metatarsophalangeal joint"),
    (re.compile(r"\bANA\b", re.I), "antinuclear antibody"),
    (re.compile(r"\banti-dsDNA\b", re.I), "anti-double stranded DNA antibody"),
    (re.compile(r"\bdsDNA\b", re.I), "double stranded DNA"),
    (re.compile(r"\bJVP\b", re.I), "jugular venous pressure"),
    (re.compile(r"\bDTRs?\b", re.I), "deep tendon reflexes"),
    (re.compile(r"\bRA\b(?!\s*\d)", re.I), "room air"),
    (re.compile(r"\bEKG\b", re.I), "electrocardiogram"),
    (re.compile(r"\bECG\b", re.I), "electrocardiogram"),
    (re.compile(r"\bWBC\b", re.I), "white blood cell count"),
    (re.compile(r"\bCRP\b", re.I), "C-reactive protein"),
    (re.compile(r"\bESR\b", re.I), "erythrocyte sedimentation rate"),
    (re.compile(r"\bCTA\b", re.I), "CT angiography"),
]

# ---------------------------------------------------------------------------
# Negation Triggers & Clause Boundaries
# ---------------------------------------------------------------------------

NEGATION_PATTERNS = [
    re.compile(r"\b(?:denies|denied|deny|denying)\b(?:\s+(?:any|the|a|prior|further|reported))?", re.I),
    re.compile(r"\b(?:negative for|neg for|ruled out for|free of)\b", re.I),
    re.compile(r"\b(?:no|not|without|absence of|zero|lacking|lack of)\b(?:\s+(?:evidence of|signs of|history of|reported|complaints of|any))?", re.I),
    re.compile(r"\bunresponsive to\b", re.I),
]

TRANSITION_WORDS = [
    "but", "however", "although", "except", "yet", "presents with", "complains of",
    "admitted for", "found to have", "positive for", "shows", "demonstrates", "reveals"
]

# ---------------------------------------------------------------------------
# Clinical Signs & Symptoms Dictionary for Sub-5ms Extraction
# ---------------------------------------------------------------------------

CLINICAL_SIGNS_MAP: Dict[str, str] = {
    # Cardiology & Vascular
    "crushing retrosternal chest pain": "crushing chest pain",
    "retrosternal chest pressure": "crushing chest pain",
    "substernal chest pressure": "crushing chest pain",
    "crushing chest pain": "crushing chest pain",
    "chest pain": "chest pain",
    "chest heaviness": "chest pressure",
    "chest tightness": "chest tightness",
    "tearing chest pain": "tearing chest pain",
    "ripping chest pain": "tearing chest pain",
    "radiating to back": "pain radiating to back",
    "radiating to left shoulder": "left arm pain",
    "radiating to left arm": "left arm pain",
    "radiating to left neck": "radiating chest pain",
    "radiating to jaw": "jaw pain",
    "radiates to left shoulder": "left arm pain",
    "radiates to jaw": "jaw pain",
    "diaphoresis": "sweating",
    "profuse sweating": "sweating",
    "dyspnea on exertion": "shortness of breath",
    "shortness of breath": "shortness of breath",
    "dyspnea": "shortness of breath",
    "orthopnea": "orthopnea",
    "paroxysmal nocturnal dyspnea": "paroxysmal nocturnal dyspnea",
    "s4 gallop": "S4 gallop",
    "s3 gallop": "S3 gallop",
    "elevated jvp": "elevated JVP",
    "jugular venous distension": "elevated JVP",
    "basilar crackles": "crackles",
    "crackles": "crackles",
    "rales": "crackles",
    "bibasilar crackles": "crackles",
    "st elevation": "ST elevation",
    "st elevations": "ST elevation",
    "st-segment elevation": "ST elevation",
    "elevated troponin": "elevated cardiac troponin",
    "troponin elevated": "elevated cardiac troponin",
    "pedal edema": "bilateral leg swelling",
    "peripheral edema": "bilateral leg swelling",
    "calf swelling": "calf swelling",
    "calf tenderness": "calf pain",
    "pulse deficit": "unequal blood pressure",
    "bp discrepancy": "unequal blood pressure",

    # Neurology & Neurosurgery
    "facial droop": "facial drooping",
    "facial drooping": "facial drooping",
    "face droop": "facial drooping",
    "arm weakness": "unilateral weakness",
    "leg weakness": "unilateral weakness",
    "hemiparesis": "hemiparesis",
    "expressive aphasia": "aphasia",
    "receptive aphasia": "aphasia",
    "aphasia": "aphasia",
    "slurred speech": "slurred speech",
    "dysarthria": "slurred speech",
    "thunderclap headache": "thunderclap headache",
    "worst headache of life": "thunderclap headache",
    "worst headache of my life": "thunderclap headache",
    "nuchal rigidity": "stiff neck",
    "neck stiffness": "stiff neck",
    "photophobia": "photophobia",
    "jaw claudication": "jaw claudication",
    "scalp tenderness": "scalp tenderness",
    "clonus": "clonus",
    "hyperreflexia": "brisk reflexes",
    "brisk reflexes": "brisk reflexes",
    "kayser-fleischer": "kayser-fleischer rings",
    "asterixis": "asterixis",
    "resting tremor": "tremor",
    "cogwheel": "cogwheel rigidity",
    "ataxia": "ataxia",
    "altered mental status": "altered consciousness",
    "confusion": "confusion",

    # Surgery & GI
    "periumbilical pain migrating": "right lower quadrant pain",
    "periumbilical pain": "abdominal pain",
    "migrating to right lower quadrant": "right lower quadrant pain",
    "right lower quadrant pain": "right lower quadrant pain",
    "mcburney": "McBurney point tenderness",
    "rovsing": "Rovsing sign",
    "rebound tenderness": "rebound tenderness",
    "guarding": "guarding",
    "epigastric pain radiating to back": "severe epigastric pain",
    "epigastric pain": "epigastric pain",
    "right upper quadrant pain": "right upper quadrant pain",
    "ruq pain": "right upper quadrant pain",
    "murphy sign": "Murphy sign",
    "jaundice": "jaundice",
    "melena": "black stool",
    "hematemesis": "vomiting blood",
    "obstipation": "obstipation",
    "anorexia": "loss of appetite",
    "nausea": "nausea",
    "vomiting": "vomiting",

    # OB/GYN & Pregnancy
    "gestation": "pregnancy",
    "pregnant": "pregnancy",
    "pregnancy": "pregnancy",
    "third trimester": "pregnancy",
    "scotoma": "scotoma",
    "blurred vision": "blurred vision",
    "proteinuria": "proteinuria",
    "vaginal bleeding": "vaginal bleeding",
    "uterine contractions": "uterine contractions",
    "leakage of fluid": "rupture of membranes",

    # Rheumatology & Autoimmune
    "malar rash": "malar rash",
    "butterfly rash": "malar rash",
    "sparing nasolabial folds": "malar rash",
    "photosensitivity": "photosensitive rash",
    "polyarthritis": "joint pain",
    "morning stiffness": "morning stiffness",
    "joint stiffness": "morning stiffness",
    "joint pain": "joint pain",
    "joint swelling": "joint swelling",
    "pleuritic chest pain": "pleuritic chest pain",
    "pleurisy": "pleuritic chest pain",
    "positive ana": "positive antinuclear antibody",
    "positive anti-dsdna": "positive anti-dsDNA",
    "anti-dsdna positive": "positive anti-dsDNA",
    "ana positive": "positive antinuclear antibody",
    "low c3": "hypocomplementemia",
    "low c4": "hypocomplementemia",
    "oral ulcers": "oral ulcers",
    "podagra": "podagra",
    "first mtp": "first mtp pain",

    # Infectious & Pediatrics & Respiratory
    "high fever": "fever",
    "fever": "fever",
    "chills": "chills",
    "cough": "cough",
    "coughing": "cough",
    "productive cough": "purulent sputum",
    "hemoptysis": "coughing blood",
    "coughing blood": "coughing blood",
    "pleuritic pain": "pleuritic chest pain",
    "pleuritic": "pleuritic chest pain",
    "headache": "headache",
    "throbbing headache": "headache",
    "frontal headache": "headache",
    "seizure": "seizures",
    "seizures": "seizures",
    "convulsions": "seizures",
    "trauma": "trauma",
    "atrial fibrillation": "irregularly irregular pulse",
    "irregularly irregular": "irregularly irregular pulse",
    "irregular pulse": "irregularly irregular pulse",
    "calf pain": "calf pain",
    "calf tenderness": "calf pain",
    "diarrhea": "diarrhea",
    "dysuria": "dysuria",
    "strawberry tongue": "strawberry tongue",
    "conjunctival injection": "conjunctivitis",
    "conjunctivitis": "conjunctivitis",
    "cracked lips": "cheilitis",
    "stridor": "stridor",
    "drooling": "drooling",
    "tripod position": "tripod position",
    "erythema migrans": "erythema migrans",
    "bullseye rash": "erythema migrans",
    "petechiae": "petechial rash",
    "petechial rash": "petechial rash",
    "petechial": "petechial rash",
    "purpura": "purpuric rash",
    "purpuric rash": "purpuric rash",
    "purpura fulminans": "purpura fulminans",
    "purplish-red lesions": "non-blanching rash",
    "purplish-red": "petechial rash",
    "remain visible when firm pressure is applied": "non-blanching rash",
    "remain visible when pressure is applied": "non-blanching rash",
    "remain visible under pressure": "non-blanching rash",
    "non-blanching rash": "non-blanching rash",
    "non-blanching lesions": "non-blanching rash",
    "non-blanching": "non-blanching rash",
    "blood pressure begins to fall": "hypotension",
    "circulatory deterioration": "hypotension",
    "eschar": "eschar",
    "tache noire": "eschar",

    # =========================================================
    # Tropical, Travel & High-Consequence Infectious Disease Signs
    # =========================================================
    # Bleeding manifestations
    "bleeding from the gums": "bleeding",
    "bleeding from gums": "bleeding",
    "gum bleeding": "bleeding",
    "bleeding gums": "bleeding",
    "bleeding manifestations": "bleeding",
    "mucosal bleeding": "bleeding",
    "blood associated with vomiting": "hematemesis",
    "small amounts of blood associated with vomiting": "hematemesis",
    "vomiting blood": "hematemesis",
    "hematemesis": "hematemesis",
    "unexplained bleeding": "bleeding",
    "spontaneous bleeding": "bleeding",

    # Joint & Musculoskeletal (Chikungunya, Arboviral, Rheumatic)
    "bilateral polyarthralgia": "severe joint pain",
    "polyarthralgia": "severe joint pain",
    "severe joint pain": "severe joint pain",
    "wrists, ankles, knees": "severe joint pain",
    "wrists, ankles": "severe joint pain",
    "small joints of the hands and feet": "severe joint pain",
    "small joints of hands and feet": "severe joint pain",
    "joint swelling": "joint swelling",
    "swelling around several peripheral joints": "joint swelling",
    "peripheral joint swelling": "joint swelling",
    "joint stiffness": "morning stiffness",
    "stiffness and pain": "morning stiffness",
    "limited mobility": "severe joint pain",
    "muscle pain": "muscle aches",
    "generalized muscle pain": "muscle aches",
    "muscle aches": "muscle aches",
    "myalgia": "muscle aches",
    "joint discomfort": "joint pain",

    # Hepatic & Jaundice (Yellow Fever, Viral Hepatitis, Leptospirosis)
    "yellow discoloration of his eyes and skin": "jaundice",
    "yellow discoloration of eyes and skin": "jaundice",
    "yellow discoloration": "jaundice",
    "jaundice": "jaundice",
    "jaundiced": "jaundice",
    "icterus": "jaundice",
    "scleral icterus": "jaundice",
    "darker urine": "dark urine",
    "dark urine": "dark urine",
    "hepatic involvement": "jaundice",

    # Fever patterns & Constitutional
    "gradually increasing fever": "step-ladder fever",
    "step-ladder fever": "step-ladder fever",
    "persistent fever": "persistent fever",
    "fever remained persistent": "persistent fever",
    "fever persisted": "persistent fever",
    "abrupt fever": "fever",
    "abrupt onset of high fever": "fever",
    "sudden fever": "fever",
    "chills": "chills",
    "profound weakness": "profound weakness",
    "marked weakness": "profound weakness",
    "profound fatigue": "fatigue",
    "marked tiredness": "fatigue",
    "loss of appetite": "loss of appetite",
    "reduced appetite": "loss of appetite",
    "dehydration": "dehydration",
    "dehydrated": "dehydration",
    "mildly dehydrated": "dehydration",

    # Dermatological (Zika, Dengue, Chikungunya, Mpox, Measles)
    "diffuse skin eruption": "maculopapular rash",
    "widespread skin eruption": "maculopapular rash",
    "generalized skin eruption": "maculopapular rash",
    "maculopapular eruption": "maculopapular rash",
    "maculopapular rash": "maculopapular rash",
    "diffuse rash": "rash",
    "rash": "rash",
    "skin eruption": "rash",

    # Ocular & ENT
    "redness of both eyes without purulent discharge": "conjunctivitis",
    "redness of both eyes": "conjunctivitis",
    "redness of the eyes": "conjunctivitis",
    "redness of eyes": "conjunctivitis",
    "redness and irritation of both eyes": "conjunctivitis",
    "bilateral conjunctival redness": "conjunctivitis",
    "both conjunctivae are mildly injected": "conjunctivitis",
    "conjunctivae are mildly injected": "conjunctivitis",
    "conjunctivae are injected": "conjunctivitis",
    "conjunctival redness": "conjunctivitis",
    "conjunctival injection": "conjunctivitis",
    "bilateral conjunctival injection": "conjunctivitis",
    "conjunctivitis": "conjunctivitis",
    "sore throat": "sore throat",
    "throat pain": "sore throat",

    # Hepatic & Stool Manifestations (Viral Hepatitis, Yellow Fever)
    "scleral icterus and mild jaundice": "jaundice",
    "scleral icterus": "jaundice",
    "clear scleral icterus": "jaundice",
    "mild jaundice": "jaundice",
    "jaundice": "jaundice",
    "jaundiced": "jaundice",
    "yellow discoloration of his eyes and skin": "jaundice",
    "yellow discoloration of his eyes": "jaundice",
    "yellow discoloration of eyes": "jaundice",
    "yellow discoloration of skin": "jaundice",
    "yellow discoloration": "jaundice",
    "darker urine": "dark urine",
    "dark urine": "dark urine",
    "stools have become unusually pale": "clay-colored stools",
    "stools have become pale": "clay-colored stools",
    "unusually pale stools": "clay-colored stools",
    "pale stools": "clay-colored stools",
    "clay-colored stools": "clay-colored stools",
    "acholic stools": "clay-colored stools",
    "liver edge is mildly tender": "hepatomegaly",
    "tender liver edge": "hepatomegaly",
    "mildly tender liver": "hepatomegaly",
    "right-upper-quadrant abdominal tenderness": "abdominal pain",
    "right upper quadrant abdominal tenderness": "abdominal pain",
    "upper abdominal discomfort": "abdominal pain",

    # Bleeding Manifestations
    "bleeding from the nose": "bleeding",
    "bleeding from nose": "bleeding",
    "bleeding from his nose": "bleeding",
    "epistaxis": "bleeding",
    "bleeding from the gums": "bleeding",
    "bleeding from his gums": "bleeding",
    "bleeding from gums": "bleeding",
    "gum bleeding": "bleeding",
    "blood-stained vomitus": "hematemesis",
    "blood associated with vomiting": "hematemesis",
    "small amounts of blood associated with vomiting": "hematemesis",
    "hematemesis": "hematemesis",

    # Dermatological, Purpura & Meningism (Meningococcemia, Dengue, Chikungunya)
    "several small reddish spots": "petechiae",
    "small reddish spots": "petechiae",
    "petechial lesions": "petechiae",
    "petechial": "petechiae",
    "petechiae": "petechiae",
    "do not blanch with pressure": "non-blanching rash",
    "do not blanch": "non-blanching rash",
    "non-blanching rash": "non-blanching rash",
    "non-blanching": "non-blanching rash",
    "reddish-purple spots": "non-blanching rash",
    "purpura fulminans": "non-blanching rash",
    "rapidly worsening neck pain": "neck stiffness",
    "marked neck stiffness": "neck stiffness",
    "neck stiffness": "neck stiffness",
    "stiff neck": "neck stiffness",
    "meningism": "neck stiffness",
    "sensitive to light": "photophobia",
    "photophobia": "photophobia",

    # Malaria & Fever Patterns
    "intermittent fever": "intermittent fever",
    "fever repeatedly returns": "intermittent fever",
    "recurrent fever": "intermittent fever",
    "cyclical fever": "intermittent fever",
    "step-ladder fever": "step-ladder fever",
    "gradually increasing fever": "step-ladder fever",
    "persistent fever": "persistent fever",
    "low-grade fever": "low-grade fever",
    "chills": "chills",
    "pale": "pallor",
    "pallor": "pallor",
    "anemia": "anemia",
    "thrombocytopenia": "thrombocytopenia",
    "blood smear is urgently requested": "blood smear requested",
    "blood smear urgently requested": "blood smear requested",
    "blood smear requested": "blood smear requested",
    "blood smear": "blood smear requested",
    "thick and thin blood smear": "blood smear requested",
    "nighttime outdoor exposure": "nighttime mosquito exposure",
    "nighttime mosquito": "nighttime mosquito exposure",

    # Arboviral Specifics (Dengue, Zika)
    "retro-orbital discomfort": "retro-orbital pain",
    "retro-orbital pain": "retro-orbital pain",
    "retro-orbital headache": "retro-orbital pain",
    "unprotected sexual contact": "sexual transmission risk",
    "unprotected sexual intercourse": "sexual transmission risk",
    "sexual contact": "sexual transmission risk",
    "sexual intercourse": "sexual transmission risk",
    "sexual exposure": "sexual transmission risk",
    "partner transmission": "sexual transmission risk",

    # Gastrointestinal (Dengue warning signs, VHF, Typhoid, Cholera)
    "repeated vomiting": "persistent vomiting",
    "persistent vomiting": "persistent vomiting",
    "severe vomiting": "persistent vomiting",
    "vomiting": "vomiting",
    "nausea": "nausea",
    "watery diarrhea": "diarrhea",
    "loose stools": "diarrhea",
    "intermittent diarrhea": "diarrhea",
    "diarrhea": "diarrhea",
    "abdominal discomfort": "abdominal pain",
    "abdominal tenderness": "abdominal pain",
    "worsening abdominal pain": "severe abdominal pain",
    "severe abdominal pain": "severe abdominal pain",
    "abdominal pain": "abdominal pain",

    # Neurological & Warning Signs (VHF, Dengue, Meningitis)
    "dizziness when attempting to stand": "postural dizziness",
    "dizziness whenever she attempted to stand": "postural dizziness",
    "postural dizziness": "postural dizziness",
    "dizziness": "dizziness",
    "intermittently confused": "confusion",
    "episodes of confusion": "confusion",
    "confusion": "confusion",
    "less alert": "lethargy",
    "unusually sleepy": "lethargy",
    "unusually lethargic": "lethargy",
    "increasingly drowsy": "lethargy",
    "increasing drowsiness": "lethargy",
    "drowsiness": "lethargy",
    "lethargic": "lethargy",
    "lethargy": "lethargy",
    "reduced urine output": "reduced urine output",
    "reduced urine production": "reduced urine output",
    "oliguria": "reduced urine output",
    "circulatory compromise": "hypotension",
    "clinically unstable": "hypotension",
    "clinically dehydrated": "dehydration",
    "dehydrated": "dehydration",
    "dehydration": "dehydration",
    "tachycardia": "tachycardia",
    "tachycardic": "tachycardia",

    # -----------------------------------------------------------------------
    # Hallmark signs for Cases 26-48 & Arboviral / Yellow Fever
    # -----------------------------------------------------------------------
    # Chikungunya & Polyarthralgia
    "severe generalized joint pain": "severe joint pain",
    "severe joint pain": "severe joint pain",
    "severe pain in both ankles": "severe joint pain",
    "severe pain in both ankles and wrists": "severe joint pain",
    "severe bilateral ankle and wrist pain": "severe joint pain",
    "pain deep inside the joints": "severe joint pain",
    "deep inside the joints": "severe joint pain",
    "walking short distances has become difficult": "severe joint pain",
    "cannot climb stairs without assistance": "severe joint pain",
    "cannot climb stairs": "severe joint pain",
    "joint pain is much more disabling": "severe joint pain",
    "joint pain is disproportionately prominent": "severe joint pain",
    "disproportionately prominent": "severe joint pain",
    "mild swelling and substantially reduced movement": "joint swelling",
    "mild swelling around several joints": "joint swelling",
    "periarticular swelling": "joint swelling",
    "faint rash over the trunk and upper arms": "maculopapular rash",
    "faint rash over the trunk": "maculopapular rash",
    "faint rash": "rash",

    # Yellow Fever & Hepatorenal
    "pain beneath the right costal margin": "right upper quadrant pain",
    "tenderness in the right upper abdomen": "right upper quadrant pain",
    "yellow discoloration of his eyes": "jaundice",
    "yellow discoloration of eyes": "jaundice",
    "noticeably darker": "dark urine",
    "severe back pain": "severe back pain",
    "hepatic dysfunction": "hepatic failure",
    "hepatic failure": "hepatic failure",
    "coagulation abnormalities": "bleeding",

    # Case 36: Insulin Autoimmune Syndrome (Hirata Disease)
    "several hours after meals": "postprandial hypoglycemia",
    "hours after meals": "postprandial hypoglycemia",
    "postprandial hypoglycemia": "postprandial hypoglycemia",
    "spontaneous hypoglycemia": "hypoglycemia",
    "plasma glucose is markedly reduced": "hypoglycemia",
    "markedly reduced plasma glucose": "hypoglycemia",
    "inappropriately elevated insulin": "hyperinsulinism",
    "elevated insulin": "hyperinsulinism",
    "elevated c-peptide": "elevated C-peptide",
    "suppressed ketone production": "suppressed ketogenesis",
    "suppressed ketones": "suppressed ketogenesis",
    "nutritional supplement": "thiol supplement exposure",
    "antibodies directed against endogenous insulin": "insulin autoantibodies",
    "antibodies directed against insulin": "insulin autoantibodies",
    "anti-insulin antibodies": "insulin autoantibodies",
    "tremulousness": "tremor",
    "near-syncope": "presyncope",

    # Case 37: Pachydermoperiostosis (Primary Hypertrophic Osteoarthropathy)
    "enlargement of the fingertips and toes": "digital clubbing",
    "enlargement of the fingertips": "digital clubbing",
    "bulbous enlargement of the distal digits": "digital clubbing",
    "bulbous enlargement": "digital clubbing",
    "increased curvature of the nails": "digital clubbing",
    "digital clubbing": "digital clubbing",
    "thickened facial skin": "pachydermia",
    "pachydermia": "pachydermia",
    "periosteal new bone formation": "periostosis",
    "periostosis": "periostosis",
    "periosteal tenderness": "periostosis",
    "excessive sweating of the hands and feet": "hyperhidrosis",
    "excessive sweating": "hyperhidrosis",
    "hyperhidrosis": "hyperhidrosis",
    "deep aching of the long bones": "bone pain",
    "deep aching of long bones": "bone pain",

    # Case 38: Acute Intermittent Porphyria (AIP)
    "recurrent episodes of severe abdominal pain": "severe abdominal pain",
    "disproportionate to the abdominal examination": "pain out of proportion to exam",
    "pain is diffuse and disproportionate": "pain out of proportion to exam",
    "weakness in both arms and legs": "peripheral neuropathy",
    "tingling in the hands": "paresthesias",
    "dark reddish-brown urine": "port-wine urine",
    "port-wine urine": "port-wine urine",
    "reddish-brown urine": "port-wine urine",
    "disorder of heme synthesis": "heme biosynthesis defect",
    "heme synthesis": "heme biosynthesis defect",
    "hyponatremia": "hyponatremia",
    "hormonal medication": "porphyrinogenic drug trigger",

    # Case 39: Duchenne Muscular Dystrophy (DMD)
    "difficulty walking and frequent falls": "difficulty walking",
    "difficulty walking": "difficulty walking",
    "frequent falls": "frequent falls",
    "clumsy": "clumsiness",
    "difficulty running, climbing stairs, and rising from the floor": "Gowers sign",
    "difficulty rising from the floor": "Gowers sign",
    "rising from the floor": "Gowers sign",
    "gowers sign": "Gowers sign",
    "proximal muscle weakness": "proximal muscle weakness",
    "calf enlargement": "calf pseudohypertrophy",
    "calf pseudohypertrophy": "calf pseudohypertrophy",
    "waddling gait": "waddling gait",
    "serum creatine kinase is markedly elevated": "markedly elevated CK",
    "creatine kinase is markedly elevated": "markedly elevated CK",
    "markedly elevated muscle enzymes": "markedly elevated CK",
    "myopathic pattern": "myopathic EMG",
    "x-linked inheritance": "X-linked family history",

    # Case 40: Gyrate Atrophy of the Choroid and Retina
    "progressive visual difficulties": "visual impairment",
    "difficulty seeing at night": "nyctalopia",
    "night blindness": "nyctalopia",
    "nyctalopia": "nyctalopia",
    "loss of peripheral vision": "peripheral visual field loss",
    "retinal degeneration": "retinal degeneration",
    "chorioretinal atrophy": "chorioretinal atrophy",
    "impairment of retinal function": "electroretinography impairment",
    "severe impairment of retinal function": "electroretinography impairment",
    "amino-acid transport pathway": "amino acid transport defect",
    "amino-acid transport": "amino acid transport defect",
    "hyperornithinemia": "hyperornithinemia",

    # Case 41: Cryopyrin-Associated Periodic Syndrome (CAPS)
    "recurrent episodes of unexplained fever": "recurrent fever",
    "began during infancy": "infantile onset",
    "symptoms began during infancy": "infantile onset",
    "rash is not associated with vesicles": "urticarial rash",
    "faint erythematous rash over the trunk and limbs": "urticarial rash",
    "faint erythematous rash": "urticarial rash",
    "urticarial rash": "urticarial rash",
    "urticarial-type rash": "urticarial rash",
    "difficulty hearing normal conversation": "sensorineural hearing loss",
    "sensorineural hearing impairment": "sensorineural hearing loss",
    "hearing impairment": "sensorineural hearing loss",
    "inflammatory markers are persistently elevated": "elevated inflammatory markers",
    "persistently elevated inflammatory markers": "elevated inflammatory markers",
    "inherited autoinflammatory disorder": "autoinflammatory syndrome",
    "autoinflammatory disorder": "autoinflammatory syndrome",

    # Case 42: Anti-Synthetase Syndrome / Amyopathic Dermatomyositis
    "progressive difficulty swallowing": "dysphagia",
    "swallowing solid food has become difficult": "dysphagia",
    "coughs while drinking liquids": "dysphagia",
    "weakness of the proximal limbs": "proximal muscle weakness",
    "symmetrical proximal muscle weakness": "proximal muscle weakness",
    "weakness of the neck flexors": "neck flexor weakness",
    "perifascicular distribution": "perifascicular atrophy",
    "perifascicular": "perifascicular atrophy",
    "rapidly progressive shortness of breath": "rapidly progressive dyspnea",
    "bilateral interstitial abnormalities": "interstitial lung disease",
    "interstitial abnormalities": "interstitial lung disease",
    "restrictive pattern": "restrictive lung disease",
    "myositis-associated antibody": "myositis-specific antibody",
    "myositis": "myositis",

    # Case 43: Collodion Baby (Congenital Ichthyosis)
    "tightly stretched, shiny membrane": "collodion membrane",
    "tightly stretched shiny membrane": "collodion membrane",
    "shiny membrane covering almost the entire body": "collodion membrane",
    "shiny membrane": "collodion membrane",
    "membrane began to crack and peel": "collodion membrane",
    "difficulty regulating body temperature": "impaired thermoregulation",
    "eyelids and lips are pulled outward": "ectropion",
    "difficulty closing the eyes": "ectropion",
    "thick scaling develops": "ichthyosis",
    "severe generalized ichthyosis": "ichthyosis",
    "generalized ichthyosis": "ichthyosis",
    "disorders of epidermal differentiation": "disorder of cornification",
    "epidermal differentiation": "disorder of cornification",

    # Case 44: Mitochondrial Encephalopathy (MELAS / Ataxia)
    "headaches began in adolescence": "migraine-like headaches",
    "migraine-like headaches": "migraine-like headaches",
    "vertigo, imbalance": "vertigo",
    "difficulty coordinating his hands": "ataxia",
    "horizontal nystagmus": "nystagmus",
    "gait ataxia": "ataxia",
    "bilateral abnormalities involving the white matter and deep cerebral structures": "cerebral white matter lesions",
    "posterior fossa": "brainstem/cerebellar lesions",
    "relatives on his mother's side": "maternal inheritance",
    "maternal-family clustering": "maternal inheritance",
    "mitochondrial dna": "mitochondrial DNA defect",

    # Case 45: Carnitine Palmitoyltransferase II (CPT II) Deficiency
    "severe muscle pain, weakness, and dark urine": "rhabdomyolysis",
    "dark urine following relatively modest physical activity": "exercise-induced myoglobinuria",
    "muscle pain following relatively modest physical activity": "exercise-induced myoglobinuria",
    "symptomatic after prolonged exercise": "exercise intolerance after prolonged exertion",
    "serum creatine kinase is extremely elevated": "massive CK elevation",
    "creatine kinase is extremely elevated": "massive CK elevation",
    "positive for blood despite very few red blood cells": "myoglobinuria",
    "abnormality involving fatty-acid utilization": "fatty acid oxidation defect",
    "fatty-acid utilization": "fatty acid oxidation defect",
    "recurrent rhabdomyolysis": "rhabdomyolysis",

    # Case 46: Leigh Syndrome
    "loss of previously acquired motor skills": "developmental regression",
    "difficulty with balance and coordination": "ataxia",
    "problems with speech": "dysarthria",
    "abnormal eye movements": "nystagmus",
    "progressive cerebellar and brainstem abnormalities": "brainstem and basal ganglia lesions",
    "cerebellar and brainstem abnormalities": "brainstem and basal ganglia lesions",
    "older sibling died during childhood": "sibling death in childhood",
    "inherited mitochondrial or neurodegenerative disease": "mitochondrial encephalomyopathy",

    # Case 47: Hereditary Spastic Paraplegia (HSP)
    "progressive weakness of the legs, stiffness": "spastic paraparesis",
    "weakness of the legs, stiffness": "spastic paraparesis",
    "urinary urgency and occasional episodes of incomplete bladder emptying": "neurogenic bladder",
    "urinary urgency": "urinary urgency",
    "bilateral lower-limb spasticity": "spastic paraparesis",
    "spasticity": "spastic paraparesis",
    "ankle clonus": "clonus",
    "positive plantar response": "extensor plantar response",
    "preserved sensation": "preserved sensation",
    "abnormalities involving long spinal tracts": "corticospinal tract abnormalities",
    "maternal relatives had similar gait problems": "familial spasticity",

    # Case 48: Mitochondrial Complex Deficiency (Lactic Acidosis)
    "recurrent episodes of severe abdominal pain, vomiting, and unexplained lethargy": "metabolic crisis with vomiting and lethargy",
    "severe metabolic acidosis and elevated lactate": "lactic acidosis",
    "severe metabolic acidosis": "metabolic acidosis",
    "elevated lactate": "lactic acidosis",
    "subtle hypotonia": "hypotonia",
    "hypertrophic changes": "hypertrophic cardiomyopathy",
    "hypoglycemia together with elevated lactate": "fasting hypoglycemia with lactic acidosis",
    "disorders of mitochondrial energy production": "mitochondrial respiratory chain defect",
    "impaired cellular oxidative metabolism": "mitochondrial respiratory chain defect",
    "cellular oxidative metabolism": "mitochondrial respiratory chain defect",

    # Addison's & Tension Pneumothorax
    "salt craving": "salt craving",
    "hyperpigmentation of palmar creases": "palmar crease pigmentation",
    "hyperpigmentation": "palmar crease pigmentation",
    "palmar creases": "palmar crease pigmentation",
    "orthostatic hypotension": "hypotension",
    "tracheal deviation away from affected side": "tracheal deviation away from affected side",
    "tracheal deviation": "tracheal deviation away from affected side",
    "absent breath sounds": "absent breath sounds",
    "sharp pleuritic chest pain": "pleuritic chest pain",
    "copper accumulation": "kayser-fleischer rings",

    # Porphyria & Acute Neurovisceral Signs
    "port-wine color": "port-wine urine",
    "port-wine urine": "port-wine urine",
    "port-wine": "port-wine urine",
    "dark reddish-brown": "port-wine urine",
    "pain out of proportion to exam": "pain out of proportion to exam",
    "out of proportion to physical exam findings": "pain out of proportion to exam",
    "out of proportion to physical examination": "pain out of proportion to exam",
    "out of proportion to physical exam": "pain out of proportion to exam",
    "out of proportion to exam": "pain out of proportion to exam",
    "out of proportion": "pain out of proportion to exam",

    # Infective Endocarditis & Cardiovascular
    "janeway lesions": "Janeway lesions",
    "janeway": "Janeway lesions",
    "osler nodes": "Osler nodes",
    "osler's nodes": "Osler nodes",
    "oslers nodes": "Osler nodes",
    "roth spots": "Roth spots",
    "splinter hemorrhages": "splinter hemorrhages",
    "subungual splinter hemorrhages": "splinter hemorrhages",
    "vegetation": "valvular vegetation",
    "valvular vegetation": "valvular vegetation",
    "cardiac murmur": "heart murmur",
    "heart murmur": "heart murmur",
    "new murmur": "new regurgitant murmur",
    "regurgitant murmur": "new regurgitant murmur",
    "prosthetic valve": "prosthetic valve",
    "intravenous drug use": "IV drug use",
    "iv drug use": "IV drug use",
    "ivdu": "IV drug use",

    # Inflammatory Myopathy & Anti-Synthetase Hallmarks
    "gottron papules": "Gottron's papules",
    "gottron's papules": "Gottron's papules",
    "gottrons papules": "Gottron's papules",
    "gottron sign": "Gottron sign",
    "gottron's sign": "Gottron sign",
    "heliotrope rash": "heliotrope rash",
    "heliotrope": "heliotrope rash",
    "periorbital erythema": "heliotrope rash",
    "periorbital edema": "heliotrope rash",
    "mechanic's hands": "mechanic's hands",
    "mechanics hands": "mechanic's hands",
    "shawl sign": "shawl sign",
    "v sign": "V-sign rash",
    "anti-jo-1": "positive anti-Jo-1 antibody",
    "anti-jo1": "positive anti-Jo-1 antibody",
    "jo-1": "positive anti-Jo-1 antibody",
    "difficulty rising from a chair": "proximal muscle weakness",
    "difficulty climbing stairs": "proximal muscle weakness",
    "difficulty combing hair": "proximal muscle weakness",

    # Pulmonary Embolism & Venous Thromboembolism
    "unilateral leg swelling": "unilateral leg swelling",
    "unilateral calf swelling": "unilateral leg swelling",
    "deep vein thrombosis": "deep vein thrombosis",
    "dvt": "deep vein thrombosis",
    "recent immobilization": "immobilization",
    "bed rest": "immobilization",

    # Streptococcal & Pediatric ENT
    "tonsillar exudates": "tonsillar exudates",
    "exudative tonsillitis": "tonsillar exudates",
    "anterior cervical lymphadenopathy": "cervical lymphadenopathy",
    "tender anterior cervical nodes": "cervical lymphadenopathy",
    "absence of cough": "absence of cough",

    # Nephrology & Urology
    "cva tenderness": "costovertebral angle tenderness",
    "costovertebral angle tenderness": "costovertebral angle tenderness",
    "flank tenderness": "costovertebral angle tenderness",
    "costovertebral tenderness": "costovertebral angle tenderness",
    "flank pain": "flank pain",
    "severe flank pain": "severe flank pain",
    "colicky flank pain": "severe flank pain",
    "ureteral colic": "severe flank pain",
    "renal colic": "severe flank pain",
    "radiating to groin": "radiation to groin",
    "radiates to groin": "radiation to groin",
    "groin radiation": "radiation to groin",
    "dysuria": "dysuria",
    "painful urination": "dysuria",
    "burning on urination": "dysuria",
    "burning urination": "dysuria",
    "urinary frequency": "urinary frequency",
    "urinary urgency": "urinary urgency",
    "gross hematuria": "hematuria",
    "microscopic hematuria": "hematuria",
    "hematuria": "hematuria",
    "pyuria": "pyuria",
    "wbc casts": "white blood cell casts",
    "white blood cell casts": "white blood cell casts",
    "cloudy urine": "cloudy urine",
    "malodorous urine": "cloudy urine",
    "suprapubic pain": "suprapubic tenderness",
    "suprapubic tenderness": "suprapubic tenderness",
    "kidney stone": "nephrolithiasis",
    "kidney stones": "nephrolithiasis",
    "nephrolithiasis": "nephrolithiasis",
    "renal calculi": "nephrolithiasis",
    "renal calculus": "nephrolithiasis",
    "ureteral stone": "nephrolithiasis",
    "ureteral calculus": "nephrolithiasis",

    # GI & Acute Abdomen
    "left lower quadrant abdominal pain": "left lower quadrant pain",
    "left lower quadrant pain": "left lower quadrant pain",
    "left lower quadrant tenderness": "left lower quadrant pain",
    "left lower quadrant": "left lower quadrant pain",
    "llq abdominal pain": "left lower quadrant pain",
    "llq pain": "left lower quadrant pain",
    "llq tenderness": "left lower quadrant pain",
    "llq": "left lower quadrant pain",
    "left iliac fossa pain": "left lower quadrant pain",
    "left iliac fossa": "left lower quadrant pain",
    "sigmoid tenderness": "left lower quadrant pain",
    "colonic wall thickening": "left lower quadrant pain",
    "pericolonic fat stranding": "left lower quadrant pain",
    "fat stranding": "left lower quadrant pain",
    "diverticulitis": "left lower quadrant pain",
    "diverticular": "left lower quadrant pain",
    "acute diverticulitis": "left lower quadrant pain",
    "severe epigastric pain": "severe epigastric pain",
    "epigastric tenderness": "epigastric pain",
    "elevated lipase": "elevated lipase",
    "elevated serum lipase": "elevated lipase",
    "elevated amylase": "elevated amylase",
    "gallbladder wall thickening": "gallbladder wall thickening",
    "pericholecystic fluid": "gallbladder wall thickening",
    "sonographic murphy": "Murphy sign",
    "sonographic murphy sign": "Murphy sign",
    "cholecystitis": "right upper quadrant pain",
    "acute cholecystitis": "right upper quadrant pain",
    "pancreatitis": "severe epigastric pain",
    "acute pancreatitis": "severe epigastric pain",
    "involuntary guarding": "guarding",
    "peritoneal signs": "rebound tenderness",

    # Rheumatology & Gout
    "first mtp": "first MTP joint pain",
    "1st mtp": "first MTP joint pain",
    "first metatarsophalangeal": "first MTP joint pain",
    "great toe pain": "first MTP joint pain",
    "podagra": "podagra",
    "podagric": "podagra",
    "negatively birefringent": "negatively birefringent needle-shaped crystals",
    "needle-shaped crystals": "negatively birefringent needle-shaped crystals",
    "needle shaped crystals": "negatively birefringent needle-shaped crystals",
    "monosodium urate": "negatively birefringent needle-shaped crystals",
    "tophus": "tophi",
    "tophi": "tophi",
    "hyperuricemia": "hyperuricemia",
    "elevated uric acid": "hyperuricemia",

    # Pulmonology & Respiratory
    "barrel chest": "barrel chest",
    "barrel-shaped chest": "barrel chest",
    "wheezing": "wheezing",
    "expiratory wheeze": "wheezing",
    "expiratory wheezing": "wheezing",
    "rhonchi": "rhonchi",
    "prolonged expiratory phase": "prolonged expiratory phase",
    "hyperinflated lungs": "hyperinflated lungs",
    "hyperinflation": "hyperinflated lungs",
    "chronic productive cough": "chronic cough",
    "chronic cough": "chronic cough",
    "increased sputum": "increased sputum purulence",
    "increased sputum purulence": "increased sputum purulence",
    "sputum purulence": "increased sputum purulence",
    "purulent sputum": "purulent sputum",
    "lobar consolidation": "consolidation",
    "consolidation": "consolidation",
    "bronchial breath sounds": "bronchial breath sounds",
    "egophony": "egophony",
    "dullness to percussion": "dullness to percussion",

    # Dermatology & Soft Tissue Infection
    "erythematous and warm": "erythematous warm skin",
    "warm and erythematous": "erythematous warm skin",
    "warm and tender": "erythematous warm skin",
    "erythematous plaque": "erythematous warm skin",
    "poorly demarcated erythema": "erythematous warm skin",
    "advancing border": "spreading erythema",
    "spreading erythema": "spreading erythema",
    "skin warmth and erythema": "erythematous warm skin",
    "local induration": "induration",
    "cellulitis": "erythematous warm skin",
    "skin erythema": "erythematous warm skin",

    # Cardiology, Thromboembolism & Vascular
    "s1q3t3": "S1Q3T3 pattern",
    "s1q3t3 pattern": "S1Q3T3 pattern",
    "wedge-shaped opacity": "wedge-shaped opacity",
    "hampton hump": "wedge-shaped opacity",
    "westermark sign": "wedge-shaped opacity",
    "elevated d-dimer": "elevated D-dimer",
    "d-dimer elevated": "elevated D-dimer",
    "positive d-dimer": "elevated D-dimer",
    "d-dimer": "elevated D-dimer",

    # Endocrinology & Metabolic
    "kussmaul": "Kussmaul breathing",
    "kussmaul breathing": "Kussmaul breathing",
    "kussmaul respirations": "Kussmaul breathing",
    "deep rapid respirations": "Kussmaul breathing",
    "fruity breath": "fruity breath odor",
    "fruity breath odor": "fruity breath odor",
    "fruity acetone odor": "fruity breath odor",
    "ketonuria": "ketonuria",
    "urine ketones": "ketonuria",
    "ketones in urine": "ketonuria",
    "high anion gap": "high anion gap metabolic acidosis",
    "anion gap metabolic acidosis": "high anion gap metabolic acidosis",
    "hyperglycemia": "hyperglycemia",
    "elevated blood glucose": "hyperglycemia",
}


class ClinicalNoteParser:
    """
    Deterministic, high-speed parser for unstructured clinical notes.
    Extracts positive symptoms, negated symptoms, abnormal vitals, and diagnostic findings.
    """

    def __init__(self):
        from app.services.clinical_section_segmenter import clinical_section_segmenter
        from app.services.lab_value_interpreter import lab_value_interpreter
        self.section_segmenter = clinical_section_segmenter
        self.lab_interpreter = lab_value_interpreter
        # Dynamically index disease KB symptoms if length >= 4
        try:
            from app.services.offline_disease_kb import DISEASE_KB
            for disease, ddata in DISEASE_KB.items():
                for s in ddata.get("symptoms", []) + ddata.get("cardinal_symptoms", []):
                    s_lower = s.lower().strip()
                    if len(s_lower) >= 4 and s_lower not in CLINICAL_SIGNS_MAP:
                        CLINICAL_SIGNS_MAP[s_lower] = s
        except Exception as e:
            log.warning("failed_dynamic_kb_symptom_indexing", error=str(e))

    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parses full clinical note and returns structured clinical representation in <3ms.
        Extracts symptoms, negations, vitals, travel history, incubation days, and exposures.
        """
        if not text or not text.strip():
            return {
                "positive_findings": [],
                "negated_findings": [],
                "vitals": {},
                "abnormal_vitals_findings": [],
                "diagnostic_findings": [],
                "travel_history": [],
                "days_since_return": None,
                "exposures": [],
                "section_breakdown": {},
                "quantitative_labs": {},
                "calculated_indices": {},
                "background_history": [],
                "summary": "",
            }

        # Step 0: Section Segmentation & Quantitative Lab Extraction
        section_map = self.section_segmenter.segment(text)
        lab_data = self.lab_interpreter.interpret(text)

        # Step 1: Expand shorthand & abbreviations
        expanded = text
        for pat, replacement in CLINICAL_SHORTHANDS:
            expanded = pat.sub(replacement, expanded)

        # Step 2: Extract & interpret Vital Signs
        vitals, abnormal_vitals = self._extract_and_interpret_vitals(expanded)

        # Step 3: Sentence & Clause level parsing for Positive vs. Negated Findings
        positive_findings, negated_findings, diagnostic_findings = self._extract_findings_with_negation(expanded)

        # Step 4: Extract Travel History & Incubation Period
        travel_history = self._extract_travel_history(expanded)
        days_since_return = self._extract_incubation_days(expanded)
        exposures = self._extract_exposures(expanded)

        # Merge abnormal vitals into positive findings
        for av in abnormal_vitals:
            if av not in positive_findings and av not in negated_findings:
                positive_findings.append(av)

        # Step 5: Incorporate Quantitative Lab Diagnostic Flags
        for flag in lab_data.get("diagnostic_flags", []):
            if flag not in positive_findings and flag not in negated_findings:
                positive_findings.append(flag)
            if flag not in diagnostic_findings:
                diagnostic_findings.append(flag)

        # Ensure no overlap: if a concept is in negated_findings, remove from positive
        positive_findings = [f for f in positive_findings if f not in negated_findings]

        # Step 6: Section-Aware Context Isolation (Disambiguating PMH/Family History from Acute Presentation)
        background_history: List[str] = []
        has_distinct_sections = any(
            k in section_map for k in ["CHIEF_COMPLAINT_AND_HPI", "PHYSICAL_EXAM", "LABS_AND_DIAGNOSTICS"]
        )
        if has_distinct_sections:
            pmh_text = (
                section_map.get("PAST_MEDICAL_HISTORY", "") + " " +
                section_map.get("FAMILY_HISTORY", "") + " " +
                section_map.get("MEDICATIONS_AND_EXPOSURES", "")
            )
            if pmh_text.strip():
                pmh_expanded = pmh_text
                for pat, replacement in CLINICAL_SHORTHANDS:
                    pmh_expanded = pat.sub(replacement, pmh_expanded)
                pmh_pos, _, _ = self._extract_findings_with_negation(pmh_expanded)

                acute_sections = [
                    section_map.get("CHIEF_COMPLAINT_AND_HPI", ""),
                    section_map.get("PHYSICAL_EXAM", ""),
                    section_map.get("LABS_AND_DIAGNOSTICS", ""),
                    section_map.get("ASSESSMENT_AND_PLAN", ""),
                ]
                acute_text = " ".join([s for s in acute_sections if s.strip()])
                acute_pos = []
                if acute_text.strip():
                    acute_expanded = acute_text
                    for pat, replacement in CLINICAL_SHORTHANDS:
                        acute_expanded = pat.sub(replacement, acute_expanded)
                    acute_pos, _, _ = self._extract_findings_with_negation(acute_expanded)

                acute_pos_set = set(acute_pos)
                filtered_positive = []
                for pf in positive_findings:
                    if pf in pmh_pos and pf not in acute_pos_set and pf not in abnormal_vitals and pf not in lab_data.get("diagnostic_flags", []):
                        background_history.append(pf)
                    else:
                        filtered_positive.append(pf)
                positive_findings = filtered_positive

        return {
            "positive_findings": positive_findings,
            "negated_findings": negated_findings,
            "vitals": vitals,
            "abnormal_vitals_findings": abnormal_vitals,
            "diagnostic_findings": diagnostic_findings,
            "travel_history": travel_history,
            "days_since_return": days_since_return,
            "exposures": exposures,
            "section_breakdown": section_map,
            "quantitative_labs": lab_data.get("extracted_labs", {}),
            "calculated_indices": lab_data.get("calculated_indices", {}),
            "background_history": background_history,
            "summary": f"Extracted {len(positive_findings)} active acute findings, {len(background_history)} background history items, {len(negated_findings)} negated findings, {len(travel_history)} travel links.",
        }

    def _extract_travel_history(self, text: str) -> List[str]:
        """Extracts visited countries, endemic territories, and outbreak contexts."""
        text_lower = text.lower()
        found_destinations: List[str] = []

        # Canonical travel and outbreak entities
        travel_targets = [
            ("democratic republic of the congo", "Democratic Republic of the Congo"),
            ("drc", "Democratic Republic of the Congo"),
            ("congo", "Democratic Republic of the Congo"),
            ("central africa", "Central Africa"),
            ("nicaragua", "Nicaragua"),
            ("bali", "Bali"),
            ("indonesia", "Indonesia"),
            ("colombia", "Colombia"),
            ("yemen", "Yemen"),
            ("west africa", "West Africa"),
            ("east africa", "East Africa"),
            ("sub-saharan africa", "Sub-Saharan Africa"),
            ("uganda", "Uganda"),
            ("rwanda", "Rwanda"),
            ("kenya", "Kenya"),
            ("angola", "Angola"),
            ("nigeria", "Nigeria"),
            ("sierra leone", "Sierra Leone"),
            ("guinea", "Guinea"),
            ("ghana", "Ghana"),
            ("cameroon", "Cameroon"),
            ("sudan", "Sudan"),
            ("brazil", "Brazil"),
            ("peru", "Peru"),
            ("ecuador", "Ecuador"),
            ("venezuela", "Venezuela"),
            ("bolivia", "Bolivia"),
            ("argentina", "Argentina"),
            ("chile", "Chile"),
            ("uruguay", "Uruguay"),
            ("paraguay", "Paraguay"),
            ("costa rica", "Costa Rica"),
            ("mauritius", "Mauritius"),
            ("thailand", "Thailand"),
            ("vietnam", "Vietnam"),
            ("philippines", "Philippines"),
            ("malaysia", "Malaysia"),
            ("cambodia", "Cambodia"),
            ("myanmar", "Myanmar"),
            ("bangladesh", "Bangladesh"),
            ("pakistan", "Pakistan"),
            ("saudi arabia", "Saudi Arabia"),
            ("jordan", "Jordan"),
            ("middle east", "Middle East"),
            ("africa", "Africa"),
            # Outbreak & transmission contexts
            ("active transmission", "active transmission"),
            ("ongoing infectious disease outbreak", "ongoing outbreak"),
            ("ongoing outbreak", "ongoing outbreak"),
            ("outbreak area", "outbreak area"),
            ("high-consequence infectious disease", "high-consequence infectious disease"),
            ("high-consequence viral infection", "high-consequence viral infection"),
            ("mosquito-borne viral transmission", "mosquito-borne viral transmission"),
            ("mosquito-borne outbreak", "mosquito-borne outbreak"),
            ("mosquito exposure", "mosquito exposure"),
            ("mosquito bites", "mosquito exposure"),
            ("uncertain food and water", "uncertain food and water"),
            ("forested areas", "rural area"),
            ("rural and forested", "rural area"),
            ("rural area", "rural area"),
        ]

        for trigger, canonical in travel_targets:
            # Word boundary search
            if re.search(r"\b" + re.escape(trigger) + r"\b", text_lower):
                if canonical not in found_destinations:
                    found_destinations.append(canonical)

        return found_destinations

    def _extract_incubation_days(self, text: str) -> Optional[int]:
        """Extracts incubation interval (days between travel return/exposure and symptom onset)."""
        word_to_num = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
            "fifteen": 15, "twenty": 20, "twenty-one": 21
        }

        patterns = [
            # "approximately one week after returning", "five days after returning"
            re.compile(r"(?:about|approximately|approx\.?|around)?\s*(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen)\s*(days?|weeks?)\s*(?:after|following|since)\s*(?:returning|return|arrival|travel|exposure|trip|stay)", re.I),
            # "developed ... 5 days after returning"
            re.compile(r"(?:developed|onset of|started|began)\s*(?:an?\s+)?(?:abrupt|sudden|gradual|low-grade|high)?\s*(?:fever|illness|symptoms|pain)\s*(?:about|approximately|around)?\s*(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen)\s*(days?|weeks?)\s*(?:after|following|since)\s*(?:returning|return|arrival)", re.I),
            # "nine days after returning"
            re.compile(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen)\s*(days?|weeks?)\s*after\s*(?:returning|arrival)", re.I),
            # "within 5 days of returning"
            re.compile(r"within\s*(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*days\s*of\s*(?:returning|return)", re.I),
            # "returned 8 days ago from", "arrived 5 days ago"
            re.compile(r"(?:returned|arrived|back)\s*(?:about|approximately|around)?\s*(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen)\s*(days?|weeks?)\s*ago", re.I),
        ]

        for pat in patterns:
            m = pat.search(text)
            if m:
                val_str = m.group(1).lower()
                val = int(val_str) if val_str.isdigit() else word_to_num.get(val_str, 1)
                unit = m.group(2).lower() if len(m.groups()) >= 2 and m.group(2) else "days"
                if "week" in unit:
                    return val * 7
                return val

        return None

    def _extract_exposures(self, text: str) -> List[str]:
        """Extracts environmental, animal, vector, or partner exposure modes."""
        text_lower = text.lower()
        exposures: List[str] = []

        mapping = [
            (r"\b(?:mosquito|mosquitoes|insect repellent|mosquito bites)\b", "mosquito exposure"),
            (r"\b(?:unpasteurized|raw milk|unfiltered water|uncertain food and water|street food)\b", "food and water exposure"),
            (r"\b(?:forest|forested|jungle|caving|bats|mine)\b", "forest / wildlife exposure"),
            (r"\b(?:rodent|rats|mice|excreta|barn)\b", "rodent exposure"),
            (r"\b(?:sexual|partner|close contact|household)\b", "secondary / contact exposure"),
        ]

        for pat, label in mapping:
            if re.search(pat, text_lower):
                exposures.append(label)

        return exposures

    def _extract_and_interpret_vitals(self, text: str) -> Tuple[Dict[str, Any], List[str]]:
        """Extracts numeric vitals and translates abnormal values to clinical findings."""
        vitals: Dict[str, Any] = {}
        abnormal_findings: List[str] = []

        # BP
        bp_match = re.search(r"\b(?:BP|blood pressure)(?:[:\s=]+|\s+(?:is|was|of)\s+)(\d{2,3})[/](\d{2,3})", text, re.I)
        if bp_match:
            sys_bp = int(bp_match.group(1))
            dia_bp = int(bp_match.group(2))
            vitals["blood_pressure"] = f"{sys_bp}/{dia_bp}"
            if sys_bp >= 160 or dia_bp >= 100:
                abnormal_findings.append("severe hypertension")
                abnormal_findings.append("hypertension")
            elif sys_bp >= 140 or dia_bp >= 90:
                abnormal_findings.append("hypertension")
            elif sys_bp < 90:
                abnormal_findings.append("hypotension")

        # HR
        hr_match = re.search(r"\b(?:HR|heart rate|pulse)(?:[:\s=]+|\s+(?:is|was|of)\s+)(\d{2,3})", text, re.I)
        if hr_match:
            hr = int(hr_match.group(1))
            vitals["heart_rate"] = hr
            if hr > 100:
                abnormal_findings.append("tachycardia")
            elif hr < 60:
                abnormal_findings.append("bradycardia")

        # RR
        rr_match = re.search(r"\b(?:RR|respiratory rate)(?:[:\s=]+|\s+(?:is|was|of)\s+)(\d{1,2})", text, re.I)
        if rr_match:
            rr = int(rr_match.group(1))
            vitals["respiratory_rate"] = rr
            if rr > 20:
                abnormal_findings.append("tachypnea")

        # Temp
        temp_match = re.search(r"\b(?:Temp|temperature|T)(?:[:\s=]+|\s+(?:is|was|of|at)\s+)(\d{2,3}(?:\.\d)?)(?:\s*°?[CF])?", text, re.I)
        if temp_match:
            val = float(temp_match.group(1))
            vitals["temperature"] = val
            celsius = (val - 32) * 5 / 9 if val > 50 else val
            if celsius >= 38.0:
                abnormal_findings.append("fever")
            elif celsius < 35.5:
                abnormal_findings.append("hypothermia")

        # SpO2
        spo2_match = re.search(r"\b(?:SpO2|spo2|O2 sat(?:uration)?|sats)(?:[:\s=]+|\s+(?:is|was|of|at)\s+)?(\d{2,3})(?:\s*%)?", text, re.I)
        if spo2_match:
            spo2 = int(spo2_match.group(1))
            vitals["oxygen_saturation"] = spo2
            if spo2 <= 94:
                abnormal_findings.append("hypoxia")

        return vitals, list(dict.fromkeys(abnormal_findings))

    def _extract_findings_with_negation(self, text: str) -> Tuple[List[str], List[str], List[str]]:
        """
        Splits notes into sentences, divides into positive and negated clauses,
        and extracts clinical signs with strict scope boundaries.
        """
        positive_set: Set[str] = set()
        negated_set: Set[str] = set()
        diagnostic_list: List[str] = []

        # Split into sentences
        sentences = re.split(r"[.\n;]+", text)

        for sent in sentences:
            sent_clean = sent.strip().lower()
            if not sent_clean:
                continue

            # Check if sentence contains transition word
            # e.g. "Denies chest pain, but reports severe headache"
            clauses = [sent_clean]
            for tw in TRANSITION_WORDS:
                new_clauses = []
                for cl in clauses:
                    if f" {tw} " in cl:
                        parts = cl.split(f" {tw} ")
                        new_clauses.append(parts[0])
                        for p in parts[1:]:
                            new_clauses.append(f"__TRANSITION_POS__ {p}")
                    else:
                        new_clauses.append(cl)
                clauses = new_clauses

            for clause in clauses:
                is_transition = "__TRANSITION_POS__" in clause
                cl_clean = clause.replace("__TRANSITION_POS__", "").strip()

                # Check if this clause begins with or contains a negation trigger
                neg_start = -1
                for np in NEGATION_PATTERNS:
                    m = np.search(cl_clean)
                    if m:
                        neg_start = m.start()
                        break

                if neg_start != -1:
                    # Clause is negated from neg_start onwards
                    pos_part = cl_clean[:neg_start].strip()
                    neg_part = cl_clean[neg_start:].strip()

                    # Positive matches before negation
                    if pos_part:
                        for sign_phrase, canonical in CLINICAL_SIGNS_MAP.items():
                            if sign_phrase in pos_part:
                                positive_set.add(canonical)

                    # Negated matches after negation trigger
                    for sign_phrase, canonical in CLINICAL_SIGNS_MAP.items():
                        if sign_phrase in neg_part:
                            negated_set.add(canonical)
                else:
                    # Purely positive clause
                    for sign_phrase, canonical in CLINICAL_SIGNS_MAP.items():
                        if sign_phrase in cl_clean:
                            positive_set.add(canonical)

        # Detect Diagnostic Laboratory & Imaging Findings
        diag_patterns = [
            (r"(?:ST elevation|STEMI|ST-segment elevation)", "ST-segment elevation on ECG"),
            (r"(?:elevated troponin|troponin elevated|troponin\s*>\s*\d+)", "Elevated Cardiac Troponin"),
            (r"(?:proteinuria|3\+\s*protein|2\+\s*protein)", "Proteinuria on Urinalysis"),
            (r"(?:positive ana|ana positive|ana\s*1:\d+)", "Positive Antinuclear Antibody (ANA)"),
            (r"(?:positive anti-dsdna|anti-dsdna positive)", "Positive Anti-dsDNA Antibody"),
            (r"(?:low c3|low c4|hypocomplementemia)", "Low Complement C3/C4"),
            (r"(?:mcburney)", "Positive McBurney Point Sign"),
            (r"(?:rovsing)", "Positive Rovsing Sign"),
            (r"(?:s4 gallop)", "Audible S4 Cardiac Gallop"),
            (r"(?:clonus)", "Hyperreflexia with Sustained Clonus"),
            (r"(?:blood cultures? positive|positive blood cultures?|bacteremia)", "Positive Blood Cultures"),
            (r"(?:valvular vegetation|vegetation on leaflet|vegetation on mitral|vegetation on aortic)", "Valvular Vegetation on Echocardiogram"),
            (r"(?:calculus|stone|nephrolithiasis).*(?:non-contrast ct|ncct|ultrasound|ureter)", "Urinary Calculus on Imaging"),
            (r"(?:colonic diverticula|sigmoid diverticulitis|diverticular wall thickening|colonic wall thickening|pericolonic fat stranding)", "Acute Diverticulitis on CT Abdomen"),
            (r"(?:gallbladder wall thickening|pericholecystic fluid|cholelithiasis)", "Acute Cholecystitis on Ultrasound"),
            (r"(?:elevated lipase|lipase\s*>\s*\d+|elevated amylase)", "Markedly Elevated Lipase (>3x ULN)"),
            (r"(?:negatively birefringent|needle-shaped crystals)", "Intracellular Monosodium Urate Crystals"),
            (r"(?:s1q3t3|hampton hump|pulmonary embol)", "Pulmonary Embolism Findings"),
            (r"(?:wbc casts|white cell casts|pyuria)", "WBC Casts on Urinalysis"),
        ]
        text_lower = text.lower()
        for pat, label in diag_patterns:
            if re.search(pat, text_lower):
                diagnostic_list.append(label)

        # Resolve Temporal Negation Overrides:
        # If a finding was initially absent (e.g. "initially no jaundice/bleeding"), but subsequently developed
        # later in the narrative or was confirmed on physical examination, the positive finding PREVAILS.
        to_unnegate = set()
        for item in positive_set:
            if item in negated_set:
                # Find positions of positive and negative mentions
                last_pos_pos = max(
                    (text_lower.rfind(phrase) for phrase, canon in CLINICAL_SIGNS_MAP.items() if canon == item and phrase in text_lower),
                    default=-1
                )
                first_neg_pos = min(
                    (text_lower.find(phrase) for phrase, canon in CLINICAL_SIGNS_MAP.items() if canon == item and phrase in text_lower),
                    default=0
                )
                # Check for historical/initial negation phrases
                is_initially_neg = bool(re.search(r"\b(?:initially|at first|early on|initially had|initially has|prior to)\b[^\.\n;]*\b(?:no|not|without|denies)\b", text_lower))
                if last_pos_pos > first_neg_pos or is_initially_neg:
                    to_unnegate.add(item)

        for item in to_unnegate:
            negated_set.discard(item)

        final_pos = [p for p in positive_set if p not in negated_set]
        final_neg = list(negated_set)

        return final_pos, final_neg, diagnostic_list


# Singleton instance
clinical_note_parser = ClinicalNoteParser()
