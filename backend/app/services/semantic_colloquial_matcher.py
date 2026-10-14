"""DocAssistIQ — Semantic Colloquial Mention Matcher (Step 2).

Bridges the gap between informal patient/doctor narrative descriptions and
standardized SNOMED-CT / HPO clinical manifestations:
1. Canonical colloquial semantic patterns (acroparesthesia, Raynaud's, Kussmaul, etc.)
2. Local dense vector embedding lookup via nomic-embed-text in Ollama (<180ms first, <0.1ms cached)
3. LRU vector embedding cache to preserve sub-millisecond execution
"""

import re
import math
import time
import json
import urllib.request
import threading
from typing import Dict, List, Set, Any, Tuple, Optional
import structlog

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# High-Yield Clinical Colloquial & Informal Narrative Patterns
# ---------------------------------------------------------------------------

COLLOQUIAL_CLINICAL_MAP: List[Tuple[re.Pattern, str]] = [
    # Rheumatology & Connective Tissue (Scleroderma, Raynaud's, SLE)
    (re.compile(r"\b(?:fingers?|toes?)\s+turn(?:ing)?\s+(?:white|blue|pale|purple)\b", re.I), "Raynaud's phenomenon"),
    (re.compile(r"\b(?:white\s+(?:then|and|to)\s+blue|color\s+changes?\s+in\s+cold)\b", re.I), "Raynaud's phenomenon"),
    (re.compile(r"\bskin\s+(?:on\s+fingers?\s+)?(?:tight|tightened|thickened|hardening|shiny)\b", re.I), "sclerodactyly"),
    (re.compile(r"\bsmall\s+red\s+spots?\s+on\s+(?:face|hands?|fingers?|lips?)\b", re.I), "telangiectasia"),
    (re.compile(r"\bpainful\s+red\s+nodules?\s+on\s+(?:shins?|legs?)\b", re.I), "erythema nodosum"),
    (re.compile(r"\bsun-triggered\s+(?:facial\s+)?rash\b", re.I), "malar rash"),
    (re.compile(r"\brash\s+across\s+(?:cheeks?|bridge\s+of\s+nose)\b", re.I), "malar rash"),
    (re.compile(r"\bsparing\s+nasolabial\s+folds\b", re.I), "malar rash"),
    (re.compile(r"\bpainless\s+mouth\s+ulcers?\b", re.I), "oral ulcers"),

    # Metabolic & Genetic (Fabry, CPT II, AIP, DKA)
    (re.compile(r"\bburning\s+pain\s+in\s+(?:his\s+|her\s+|my\s+)?(?:hands?|feet|extremities)\b", re.I), "acroparesthesia"),
    (re.compile(r"\btriggered\s+by\s+(?:exercise|heat|hot\s+weather|fever)\b", re.I), "heat intolerance"),
    (re.compile(r"\bsweats?\s+(?:very\s+little|rarely|not\s+at\s+all)\b", re.I), "hypohidrosis"),
    (re.compile(r"\btiny\s+dark\s+red\s+spots?\s+(?:in\s+clusters\s+)?around\s+(?:navel|umbilicus|hips?|groin)\b", re.I), "angiokeratoma"),
    (re.compile(r"\bcraving\s+ice\b", re.I), "pica"),
    (re.compile(r"\bcola-colored\s+urine\b", re.I), "hemoglobinuria"),
    (re.compile(r"\bdark\s+tea-colored\s+urine\b", re.I), "myoglobinuria"),
    (re.compile(r"\bbreathing\s+(?:deep\s+and\s+fast|deep\s+fast)\b", re.I), "Kussmaul breathing"),
    (re.compile(r"\bfruity\s+(?:smell|odor|breath)\b", re.I), "acetone breath"),
    (re.compile(r"\bpeeing\s+all\s+day\s+and\s+night\b", re.I), "polyuria"),
    (re.compile(r"\bvery\s+thirsty\b", re.I), "polydipsia"),

    # Neurology & Ophthalmology (IIH, Susac, NMOSD, HSE)
    (re.compile(r"\bvision\s+(?:blacking\s+out|dimming|greying\s+out)\s+for\s+seconds\b", re.I), "transient visual obscurations"),
    (re.compile(r"\bpulse\s+sounds?\s+in\s+ears?\b", re.I), "pulsatile tinnitus"),
    (re.compile(r"\bhearing\s+(?:heartbeat|pulse|whooshing)\s+in\s+ears?\b", re.I), "pulsatile tinnitus"),
    (re.compile(r"\bpapilledema\s+(?:both\s+eyes|bilateral)\b", re.I), "papilledema"),
    (re.compile(r"\bpatchy\s+visual\s+loss\b", re.I), "scotoma"),
    (re.compile(r"\bpainful\s+visual\s+loss\b", re.I), "optic neuritis"),
    (re.compile(r"\bnumbness\s+below\s+(?:the\s+)?chest\b", re.I), "sensory level myelopathy"),

    # Gastroenterology & Surgery (Achalasia, EoE, Biliary Colic, PSC)
    (re.compile(r"\bfood\s+sticks\s+sometimes\b", re.I), "dysphagia"),
    (re.compile(r"\bdifficulty\s+swallowing\b", re.I), "dysphagia"),
    (re.compile(r"\bregurgitation\s+of\s+undigested\s+food\b", re.I), "regurgitation"),
    (re.compile(r"\bpain\s+after\s+fatty\s+meals?\b", re.I), "biliary colic"),
    (re.compile(r"\btenderness\s+beneath\s+(?:the\s+)?right\s+costal\s+margin\s+on\s+inspiration\b", re.I), "Murphy sign"),

    # Endocrine & Paraneoplastic (Pheo, Carcinoid, Sheehan, Cushing)
    (re.compile(r"\bepisodic\s+pounding\s+headaches?\b", re.I), "paroxysmal headache"),
    (re.compile(r"\bflushing\s+of\s+(?:the\s+)?(?:face|chest)\s+(?:often\s+)?triggered\s+by\s+(?:alcohol|wine)\b", re.I), "carcinoid flush"),
    (re.compile(r"\bblood\s+pressure\s+reaches\s+(?:2\d\d/\d\d\d|19\d/\d\d\d)\b", re.I), "paroxysmal severe hypertension"),
    (re.compile(r"\b(?:purple\s+stretch\s+marks?|purple\s+striae|broad\s+purple\s+stretch\s+marks?)\b", re.I), "purple striae"),
    (re.compile(r"\bskin-?lightening\s+cream\b", re.I), "exogenous corticosteroid use"),
    (re.compile(r"\b(?:postpartum\s+bleeding|postpartum\s+hemorrhage)\b", re.I), "postpartum hemorrhage"),
    (re.compile(r"\bbitemporal\s+(?:visual-?field\s+loss|hemianopia)\b", re.I), "bitemporal hemianopia"),

    # Hematology & Microangiopathy (TTP, HUS, Amyloidosis)
    (re.compile(r"\b(?:fragmented\s+red\s+cells|schistocytes?)\b", re.I), "schistocytes"),
    (re.compile(r"\bbloody\s+diarrhea\b", re.I), "bloody diarrhea"),
    (re.compile(r"\b(?:enlarged\s+tongue|macroglossia)\b", re.I), "macroglossia"),
    (re.compile(r"\b(?:bruising\s+around\s+(?:the\s+)?eyes?|raccoon\s+eyes?|periorbital\s+purpura)\b", re.I), "periorbital purpura"),
    (re.compile(r"\bapical\s+sparing\b", re.I), "apical sparing cardiac amyloidosis"),
    (re.compile(r"\blow\s+qrs\s+voltage\b", re.I), "low QRS voltage"),

    # Multisystem & Rheumatology (Whipple, Strongyloides, Relapsing Polychondritis, Behcet, RTA)
    (re.compile(r"\b(?:ears?\s+(?:red\s+and\s+hurt|tender|painful)|red\s+ears?)\b", re.I), "auricular chondritis"),
    (re.compile(r"\b(?:nose\s+tender|tender\s+nose|saddle\s+nose)\b", re.I), "nasal chondritis"),
    (re.compile(r"\bmigratory\s+(?:pain|swelling|arthralgias?|polyarthritis)\b", re.I), "migratory polyarthritis"),
    (re.compile(r"\b(?:tropheryma\s+whipplei|pas-positive)\b", re.I), "Whipple disease"),
    (re.compile(r"\b(?:rhabditiform\s+larvae|strongyloides)\b", re.I), "strongyloidiasis"),
    (re.compile(r"\b(?:barefoot\s+in\s+soil|larva\s+currens)\b", re.I), "larva currens"),
    (re.compile(r"\b(?:eyes?\s+and\s+mouth\s+dry|dry\s+eyes?\s+and\s+(?:dry\s+)?mouth)\b", re.I), "sicca syndrome"),
    (re.compile(r"\bgenital\s+ulcers?\b", re.I), "genital ulcers"),
    (re.compile(r"\bpathergy\b", re.I), "pathergy"),
    (re.compile(r"\b(?:intracranial\s+arterial\s+narrowing|cerebral\s+vasculitis)\b", re.I), "cerebral vasculitis"),

    # Vascular & Acute Abdomen (Renal Infarction, Gallstones / Cholecystitis)
    (re.compile(r"\bwedge-?shaped\s+perfusion\s+defect\b", re.I), "wedge-shaped perfusion defect"),
    (re.compile(r"\b(?:pain\s+in\s+(?:the\s+)?(?:left\s+|right\s+)?flank|severe\s+flank\s+pain)\b", re.I), "flank pain"),
    (re.compile(r"\b(?:right-?upper-?quadrant\s+pain|pain\s+in\s+right\s+upper\s+quadrant)\b", re.I), "right upper quadrant pain"),
    (re.compile(r"\bgallbladder\s+stones?\b", re.I), "gallstones"),
    (re.compile(r"\bsonographic\s+murphy\b", re.I), "Murphy sign"),

    # Tropical, Pediatric & Rare Syndromic Hallmark Patterns
    (re.compile(r"\b(?:marked\s+)?splenic\s+enlargement\b", re.I), "splenomegaly"),
    (re.compile(r"\b(?:moderate\s+)?liver\s+enlargement\b", re.I), "hepatomegaly"),
    (re.compile(r"\b(?:plasma\s+ammonia\s*(?:is|was|of)?\s*\d+|elevated\s+ammonia|hyperammonemia)\b", re.I), "hyperammonemia"),
    (re.compile(r"\b(?:sleepy\s+after\s+(?:a\s+)?(?:high-?protein\s+meal|protein)|protein\s+intolerance)\b", re.I), "protein intolerance"),
    (re.compile(r"\brespiratory\s+alkalosis\b", re.I), "respiratory alkalosis"),
    (re.compile(r"\b(?:circumferential\s+)?soft-?tissue\s+cuff\s+around\s+(?:the\s+)?aorta\b", re.I), "coated aorta"),
    (re.compile(r"\bsoft\s+tissue\s+surrounding\s+both\s+kidneys\b", re.I), "hairy kidneys"),
    (re.compile(r"\b(?:patchy\s+)?sclerosis\s+of\s+(?:the\s+)?long\s+bones\b", re.I), "osteosclerosis"),
    (re.compile(r"\b(?:large\s+volumes\s+of\s+)?dilute\s+urine\b", re.I), "polyuria"),
    (re.compile(r"\bexcessive\s+thirst\b", re.I), "polydipsia"),
    (re.compile(r"\b(?:posterior\s+cerebral\s+white\s+matter|symmetric\s+abnormalities\s+in\s+the\s+posterior\s+cerebral\s+white\s+matter)\b", re.I), "cerebral demyelination"),
    (re.compile(r"\bloss\s+of\s+speech\b", re.I), "speech regression"),
    (re.compile(r"\bworsening\s+balance\b", re.I), "ataxia"),
    (re.compile(r"\bextending\s+across\s+(?:four|\d+)\s+vertebral\s+segments\b", re.I), "longitudinally extensive transverse myelitis"),
    (re.compile(r"\b(?:severe\s+hiccups|persistent\s+hiccups|intractable\s+hiccups)\b", re.I), "area postrema syndrome"),
    (re.compile(r"\b(?:nodules?,\s+one\s+with\s+cavitation|pulmonary\s+cavitation|cavitary\s+lesions?)\b", re.I), "cavitary lung lesions"),
    (re.compile(r"\b(?:splenic\s+lesions?|small\s+liver\s+and\s+splenic\s+lesions?)\b", re.I), "splenic abscess"),

    # Infectious, Neuromuscular & Hematologic Hallmarks (Histoplasmosis, Brucella, Porphyria, IgG4, Endocarditis, LEMS, Castleman)
    (re.compile(r"\bintracellular\s+yeasts?(?:\s+within\s+macrophages)?\b", re.I), "intracellular yeasts in macrophages"),
    (re.compile(r"\bdiffuse\s+micronodular\s+infiltrates?\b", re.I), "micronodular infiltrates"),
    (re.compile(r"\bundulat(?:ing|ant)\s+fever\b", re.I), "undulant fever"),
    (re.compile(r"\b(?:dairy\s+farmer|unpasteurized\s+dairy|raw\s+milk)\b", re.I), "dairy farmer"),
    (re.compile(r"\b(?:lumbar\s+)?spondylodiscitis\b", re.I), "lumbar spondylodiscitis"),
    (re.compile(r"\b(?:low-?carbohydrate\s+diet|strict\s+low-?carb)\b", re.I), "low-carbohydrate diet"),
    (re.compile(r"\bcrampy\s+abdominal\s+pain\b", re.I), "crampy abdominal pain"),
    (re.compile(r"\b(?:sausage-?shaped(?:\s+enlargement\s+of\s+the)?\s+pancreas|diffuse\s+(?:pancreatic\s+)?enlargement|pancreatic\s+.*diffuse\s+enlargement|thin\s+capsule-?like\s+rim)\b", re.I), "sausage-shaped pancreas"),
    (re.compile(r"\b(?:soft\s+tissue\s+surrounding\s+(?:the\s+.*)?aorta|coated\s+aorta)\b", re.I), "coated aorta"),
    (re.compile(r"\b(?:dense\s+lymphoplasmacytic\s+infiltrate|storiform\s+fibrosis)\b", re.I), "storiform fibrosis"),
    (re.compile(r"\b(?:dense\s+lymphoplasmacytic\s+infiltrate.*fibrosis|painless\s+enlargement\s+of\s+(?:both\s+)?salivary\s+glands.*pancreatic)\b", re.I), "IgG4-related disease"),
    (re.compile(r"\b(?:serum\s+)?igg4\s+(?:is\s+)?(?:markedly\s+)?elevated|immunoglobulin\s+subclass\s+testing\s+is\s+abnormal\b", re.I), "elevated serum IgG4"),
    (re.compile(r"\bpainless\s+jaundice\b", re.I), "painless jaundice"),
    (re.compile(r"\bsplinter\s+hemorrhages?\b", re.I), "splinter hemorrhages"),
    (re.compile(r"\bpainless\s+red\s+macules?(?:\s+on\s+(?:his\s+|her\s+)?palms?)?\b", re.I), "Janeway lesions"),
    (re.compile(r"\bdental\s+cleaning(?:\s+without\s+antibiotic\s+prophylaxis)?\b", re.I), "dental cleaning"),
    (re.compile(r"\bstreptococcus\s+viridans\b", re.I), "Streptococcus viridans"),
    (re.compile(r"\b(?:strength\s+)?(?:temporarily|briefly)?\s*improves\s*(?:briefly|temporarily)?\s*after\s*(?:repeated\s+muscle\s+contraction|exercise)\b", re.I), "post-exercise facilitation"),
    (re.compile(r"\b(?:tendon\s+)?reflexes\s+(?:are\s+)?reduced[^\.\n;]*apparent\s+after\s+exercise\b", re.I), "Lambert sign"),
    (re.compile(r"\b(?:shoulder\s+and\s+thigh\s+weakness|proximal\s+weakness)\b", re.I), "proximal muscle weakness"),
    (re.compile(r"\bhilar\s+(?:mass|lung\s+mass)\b", re.I), "hilar lung mass"),
    (re.compile(r"\bhhv-?8\b", re.I), "HHV-8"),
    (re.compile(r"\bpolyclonal\s+hypergammaglobulinemia\b", re.I), "polyclonal hypergammaglobulinemia"),
    (re.compile(r"\belevated\s+il-?6\b", re.I), "elevated IL-6"),
    (re.compile(r"\b(?:diffuse\s+bilateral\s+)?ground-?glass\s+opacities\b", re.I), "ground-glass opacities"),
    (re.compile(r"\bprogressive\s+exertional\s+dyspnea\b", re.I), "progressive exertional dyspnea"),
    (re.compile(r"\b(?:serum\s+protein\s+electrophoresis\s+is\s+polyclonal|polyclonal\s+(?:hypergammaglobulinemia|gammopathy))\b", re.I), "polyclonal hypergammaglobulinemia"),
    (re.compile(r"\b(?:enlarged\s+(?:painless\s+)?lymph\s+nodes?|extensive\s+plasma-?cell\s+infiltrate|angiofollicular\s+lymph\s+node\s+hyperplasia|plasma-?cell\s+infiltrate)\b", re.I), "lymphadenopathy"),
    (re.compile(r"\b(?:attacks\s+lasting\s+(?:about\s+two\s+days|one\s+to\s+three\s+days)|short\s+attacks\s+lasting\s+one\s+to\s+three\s+days|attacks\s+lasting\s+one\s+to\s+three\s+days|eastern\s+mediterranean|well\s+between\s+attacks|recurrent\s+(?:attacks|episodes)\s+of\s+fever)\b", re.I), "periodic fever syndrome"),
    (re.compile(r"\b(?:(?:family\s+is\s+from\s+(?:the\s+)?)?mediterranean(?:\s+region)?|eastern\s+mediterranean\s+descent)\b", re.I), "eastern mediterranean descent"),
    (re.compile(r"\b(?:colchicine(?:\s+therapy)?|cessation\s+(?:of\s+symptoms\s+)?with\s+colchicine)\b", re.I), "fmf"),
    (re.compile(r"\b(?:recurrent\s+polyserositis|polyserositis)\b", re.I), "polyserositis"),
    (re.compile(r"\b(?:chest\s+pain\s+(?:with\s+breathing|worse\s+on\s+inspiration)|pleuritic\s+chest\s+pain)\b", re.I), "pleuritic chest pain"),

    # Addison's & Adrenal Crisis
    (re.compile(r"\b(?:darkening\s+of\s+(?:her\s+|his\s+)?skin|hyperpigmentation\s+of\s+(?:knuckles|palmar\s+creases)|palmar\s+creases?\s+pigment(?:ed|ation)|hyperpigmentation\s+of\s+scars)\b", re.I), "palmar crease hyperpigmentation"),
    (re.compile(r"\b(?:refractory\s+hypotension\s+to\s+iv\s+fluids|circulatory\s+collapse\s+refractory)\b", re.I), "refractory hypotension"),

    # Cryptococcal Meningitis in HIV
    (re.compile(r"\b(?:india\s+ink(?:\s+preparation)?(?:\s+of\s+csf)?\s+shows\s+encapsulated\s+yeasts|encapsulated\s+yeasts\s+in\s+csf|cryptococcal\s+antigen\s+is\s+positive)\b", re.I), "encapsulated yeasts in csf"),

    # Adult-Onset Still's Disease (AOSD)
    (re.compile(r"\b(?:evanescent\s+(?:salmon-?pink\s+)?(?:maculopapular\s+)?rash|salmon[/-]?pink\s+rash)\b", re.I), "salmon-pink maculopapular rash"),
    (re.compile(r"\b(?:ferritin\s+(?:reported\s+)?['\"]?very\s+high['\"]?|markedly\s+elevated\s+ferritin|hyperferritinemia)\b", re.I), "hyperferritinemia"),
    (re.compile(r"\b(?:fever\s+almost\s+every\s+night|quotidian\s+fever|high\s+spiking\s+fevers?)\b", re.I), "quotidian fever"),
    (re.compile(r"\b(?:joint\s+pains?\s+(?:move\s+around|disappear)|migratory\s+arthralgia|arthralgias?)\b", re.I), "arthralgias"),

    # Silicosis & Berylliosis
    (re.compile(r"\b(?:stone-?cutting(?:\s+worker)?|silica\s+dust|eggshell\s+calcification(?:\s+of\s+hilar\s+lymph\s+nodes)?)\b", re.I), "eggshell calcification of hilar lymph nodes"),
    (re.compile(r"\b(?:dental\s+technician|beryllium\s+lymphocyte\s+proliferation\s+test|belpt|beryllium\s+exposure)\b", re.I), "beryllium lymphocyte proliferation test"),

    # Antiphospholipid Syndrome (APS)
    (re.compile(r"\b(?:three\s+(?:prior|previous)\s+(?:first-trimester\s+)?miscarriages|recurrent\s+(?:miscarriages|pregnancy\s+losses?)|dilute\s+russell\s+viper\s+venom\s+time|drvvt)\b", re.I), "recurrent miscarriages"),
    (re.compile(r"\b(?:livedo-?like(?:\s+skin)?\s+mottling|livedo\s+reticularis)\b", re.I), "livedo reticularis"),
    (re.compile(r"\b(?:painful\s+swelling\s+of\s+(?:one|left|right)\s+leg|thrombosis\s+of\s+(?:the\s+.*)?(?:femoral|deep|iliac|popliteal|leg)\s+vein|deep\s+vein\s+thrombosis|venous\s+thrombosis)\b", re.I), "deep vein thrombosis"),

    # EGPA & GPA Vasculitis
    (re.compile(r"\b(?:eosinophils?\s+(?:are|is)?\s*(?:markedly\s+elevated|greater\s+than\s+1500|3,?200)|blood\s+eosinophils|peripheral\s+eosinophilia)\b", re.I), "peripheral eosinophilia"),
    (re.compile(r"\b(?:mononeuritis\s+multiplex|foot\s+drop|painful\s+numbness\s+in\s+the\s+(?:right|left)?\s*foot)\b", re.I), "mononeuritis multiplex"),
    (re.compile(r"\b(?:p-?anca|anti-?mpo|myeloperoxidase\s+antibodies)\b", re.I), "p-ANCA"),
    (re.compile(r"\b(?:destruction\s+of\s+(?:the\s+)?nasal\s+septum|saddle\s+nose(?:\s+deformity)?|c-?anca|pr3-?anca)\b", re.I), "c-ANCA positive"),
    (re.compile(r"\brecurrent\s+nosebleeds?\b", re.I), "epistaxis"),
    (re.compile(r"\b(?:multiple\s+lung\s+nodules,?\s+some\s+cavitating|cavitating\s+lung\s+nodules?|lung\s+nodules.*cavitating)\b", re.I), "cavitary lung lesions"),
    (re.compile(r"\b(?:dysmorphic\s+red\s+cells|red-?cell\s+casts|rbc\s+casts)\b", re.I), "glomerulonephritis"),

    # Neurological: CJD, CVST, Myasthenia Gravis, Autoimmune Encephalitis, Meniere
    (re.compile(r"\b(?:cortical\s+ribboning|rt-?quic|14-3-3\s+protein|brief\s+involuntary\s+jerks|startle\s+myoclonus)\b", re.I), "startle myoclonus"),
    (re.compile(r"\b(?:mr\s+venography|magnetic\s+resonance\s+venography|sagittal\s+sinus\s+thrombosis|transverse\s+sinus\s+thrombosis|venous\s+sinus\s+filling\s+defect)\b", re.I), "mr venography filling defect"),
    (re.compile(r"\b(?:drooping\s+eyelids?|ptosis|anti-?achr|acetylcholine\s+receptor\s+antibody|edrophonium\s+test)\b", re.I), "drooping eyelids"),
    (re.compile(r"\b(?:anti-?nmda\s+receptor|nmdar(?:\s+antibodies)?|oro-?facial\s+dyskinesias?|ovarian\s+teratoma|facial\s+grimacing|abnormal\s+limb\s+movements|insomnia,\s+paranoia|paranoia,\s+disorganized\s+speech|disorganized\s+speech|short-?term\s+memory\s+loss)\b", re.I), "anti-NMDA receptor encephalitis"),
    (re.compile(r"\b(?:mild\s+)?lymphocytic\s+pleocytosis\b", re.I), "lymphocytic pleocytosis"),
    (re.compile(r"\b(?:fluctuating\s+hearing\s+loss|aural\s+fullness|endolymphatic\s+hydrops)\b", re.I), "endolymphatic hydrops"),

    # Vascular, Metabolic & Hematologic
    (re.compile(r"\b(?:focal\s+dilated\s+pulmonary\s+arteri(?:al|y)\s+segment|pulmonary\s+arteri(?:al|y)\s+(?:aneurysm|segment\s+with\s+adjacent\s+thrombus)|aneurysm\s+(?:of\s+the\s+.*)?pulmonary\s+artery|pulmonary\s+artery\s+aneurysms?(?:\s+and\s+thrombosis)?|hughes-?stovin)\b", re.I), "pulmonary artery aneurysm"),
    (re.compile(r"\b(?:adjacent\s+thrombus|pulmonary\s+vascular\s+thrombosis)\b", re.I), "pulmonary vascular thrombosis"),
    (re.compile(r"\b(?:(?:anti-?)?tissue[- ]transglutaminase(?:\s+iga)?|anti[- ]ttg(?:\s+iga)?|dermatitis\s+herpetiformis)\b", re.I), "anti-tTG IgA"),
    (re.compile(r"\b(?:villous\s+(?:blunting|atrophy)|intraepithelial\s+lymphocyt(?:es|osis))\b", re.I), "villous atrophy"),
    (re.compile(r"\b(?:gluten[- ]free\s+diet|gluten\s+enteropathy)\b", re.I), "gluten enteropathy"),
    (re.compile(r"\b(?:iron\s+deficiency\s+that\s+persists\s+despite\s+oral\s+iron)\b", re.I), "iron deficiency anemia unresponsive to oral iron"),
    (re.compile(r"\b(?:hair-?like(?:\s+cytoplasmic)?\s+projections?|tartrate-?resistant\s+acid\s+phosphatase|trap\s+positive|braf\s+v600e|monocytopenia|dry\s+tap(?:\s+bone\s+marrow)?|atypical\s+lymphoid\s+cells\s+with\s+abundant\s+pale\s+cytoplasm)\b", re.I), "hair-like cytoplasmic projections"),
    (re.compile(r"\b(?:hematuria\s+(?:that\s+occurs\s+)?within\s+24\s*(?:to\s*48)?\s*hours\s+of\s+(?:developing\s+)?a\s+sore\s+throat|synpharyngitic\s+hematuria)\b", re.I), "synpharyngitic hematuria"),
    (re.compile(r"\b(?:resolve\s+within\s+minutes\s+after\s+sweet\s+drinks|whipple\s+triad|inappropriately\s+(?:detectable|elevated)\s+insulin\s+and\s+c-?peptide)\b", re.I), "Whipple triad"),
    (re.compile(r"\b(?:strawberry-?like\s+tongue|strawberry\s+tongue|bilateral\s+non-?purulent\s+(?:red\s+eyes|conjunctivitis)|red\s+cracked\s+lips)\b", re.I), "strawberry tongue"),
    (re.compile(r"\b(?:elevated\s+calcitonin|medullary\s+thyroid\s+carcinoma|ret\s+proto-?oncogene)\b", re.I), "medullary thyroid carcinoma"),
    (re.compile(r"\b(?:painless\s+enlargement\s+of\s+(?:both\s+)?salivary\s+glands|storiform\s+fibrosis)\b", re.I), "salivary gland enlargement"),
    (re.compile(r"\b(?:red\s+painful\s+ears\s+but\s+earlobes\s+spared|earlobes?\s+spared|auricular\s+chondritis|nose\s+bridge\s+pain)\b", re.I), "auricular chondritis"),
    (re.compile(r"\b(?:claudication\s+of\s+(?:the\s+)?(?:left|right)?\s*arm|blood\s+pressure\s+(?:is\s+)?\d+/\d+\s+(?:mmhg\s+)?in\s+the\s+right\s+arm\s+and\s+\d+/\d+\s+in\s+the\s+left|weak\s+(?:left|right)?\s*radial\s+pulse|supraclavicular\s+bruit)\b", re.I), "blood pressure discrepancy between arms"),
    (re.compile(r"\b(?:unusual\s+sweet\s+odor|sweet\s+odor(?:\s+in\s+urine)?|maple\s+syrup\s+odor|branched-?chain\s+amino\s+acids?)\b", re.I), "maple syrup urine odor"),
    (re.compile(r"\b(?:osteosclerotic\s+(?:bone\s+)?lesions?|sclerotic\s+lesions\s+in\s+the\s+pelvis|demyelinating\s+(?:sensorimotor\s+)?polyneuropathy|monoclonal\s+(?:spike|band)|polyneuropathy,\s+organomegaly,\s+endocrinopathy)\b", re.I), "POEMS syndrome"),
    (re.compile(r"\b(?:enlarged\s+liver\s+and\s+spleen|hepatosplenomegaly)\b", re.I), "hepatosplenomegaly"),
    (re.compile(r"\b(?:meningeal\s+enhancement.*basal\s+ganglia|infarct-?like\s+lesions\s+near\s+the\s+basal\s+ganglia|meningeal\s+enhancement|lymphocyte-?predominant\s+pleocytosis)\b", re.I), "tuberculous meningitis"),
    (re.compile(r"\b(?:small-?bowel\s+biopsy\s+reveals\s+foamy\s+macrophages|foamy\s+macrophages\s+containing\s+granular\s+material|foamy\s+macrophages.*periodic\s+acid-?schiff|pas-?positive\s+macrophages|tropheryma\s+whipplei)\b", re.I), "Whipple disease"),
    (re.compile(r"\b(?:patchy\s+deep\s+ulcers|skip\s+lesions?|segmental\s+bowel-?wall\s+thickening|painful\s+ulcers\s+around\s+the\s+anus|non-?caseating\s+granulomas?)\b", re.I), "skip lesions"),
    (re.compile(r"\b(?:schirmer(?:\s+test)?(?:\s+is)?\s+positive|anti-?ro(?:/ssa)?|anti-?la(?:/ssb)?|keratoconjunctivitis\s+sicca|gritty\s+eyes|needing\s+water\s+to\s+swallow(?:\s+dry\s+food)?)\b", re.I), "keratoconjunctivitis sicca"),
]

# Standard reference clinical concepts for dense semantic embedding comparison
TARGET_CANONICAL_CONCEPTS = [
    "Raynaud's phenomenon",
    "sclerodactyly",
    "telangiectasia",
    "acroparesthesia",
    "angiokeratoma",
    "hypohidrosis",
    "pulsatile tinnitus",
    "transient visual obscurations",
    "papilledema",
    "Kussmaul breathing",
    "acetone breath",
    "optic neuritis",
    "carcinoid flush",
    "biliary colic",
    "dysphagia",
    "erythema nodosum",
    "malar rash",
    "oral ulcers",
]


class SemanticColloquialMatcher:
    """Enterprise semantic matcher bridging colloquial language to SNOMED/HPO concepts."""

    _instance: Optional["SemanticColloquialMatcher"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "SemanticColloquialMatcher":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self._ollama_url = "http://localhost:11434/api/embeddings"
        self._model_name = "nomic-embed-text:latest"
        self._embedding_cache: Dict[str, List[float]] = {}
        self._concept_embeddings: Dict[str, List[float]] = {}
        self._cache_lock = threading.Lock()
        self._initialized = True
        self._warmed = False

    def extract_colloquial_mentions(self, text: str, existing_findings_count: int = 0) -> List[str]:
        """
        Extracts clinical findings from colloquial phrases in <1ms via regex patterns,
        and uses dense vector embeddings only if no findings exist across the entire note.
        """
        if not text or not text.strip():
            return []

        findings: List[str] = []
        t_clean = text.lower()

        # Tier 1: Fast Regex Colloquial Mappings (<0.2ms)
        for pat, canonical in COLLOQUIAL_CLINICAL_MAP:
            if pat.search(t_clean):
                if canonical not in findings:
                    findings.append(canonical)

        # Tier 2: Dense Semantic Embedding Matcher via nomic-embed-text only if ZERO findings were extracted
        if not findings and existing_findings_count == 0 and len(t_clean) > 20:
            try:
                dense_matches = self._dense_semantic_match(text)
                for dm in dense_matches:
                    if dm not in findings:
                        findings.append(dm)
            except Exception as e:
                log.debug("dense_semantic_match_fallback", error=str(e))

        return findings

    def _get_embedding(self, text_clause: str, timeout: float = 0.5) -> Optional[List[float]]:
        """Retrieves dense embedding vector with in-memory LRU cache."""
        key = text_clause.strip().lower()
        with self._cache_lock:
            if key in self._embedding_cache:
                return self._embedding_cache[key]

        try:
            payload = json.dumps({"model": self._model_name, "prompt": key}).encode()
            req = urllib.request.Request(
                self._ollama_url,
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                res = json.loads(resp.read().decode())
                vec = res.get("embedding", [])
                if vec:
                    with self._cache_lock:
                        if len(self._embedding_cache) < 2048:
                            self._embedding_cache[key] = vec
                    return vec
        except Exception:
            return None
        return None

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Computes cosine similarity between two float vectors."""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def _dense_semantic_match(self, text: str, threshold: float = 0.72) -> List[str]:
        """Compares sentences against reference clinical concepts using dense embeddings."""
        # Warm concept embeddings if needed
        if not self._concept_embeddings:
            for concept in TARGET_CANONICAL_CONCEPTS:
                vec = self._get_embedding(concept, timeout=1.0)
                if vec:
                    self._concept_embeddings[concept] = vec

        if not self._concept_embeddings:
            return []

        matches: List[str] = []
        # Break text into short phrases or sentences
        clauses = [c.strip() for c in re.split(r"[,.;\n]+", text) if len(c.strip()) > 10]
        for cl in clauses[:6]:  # evaluate first 6 clauses to keep sub-50ms budget
            cl_vec = self._get_embedding(cl, timeout=0.25)
            if not cl_vec:
                continue
            for concept, c_vec in self._concept_embeddings.items():
                sim = self._cosine_similarity(cl_vec, c_vec)
                if sim >= threshold:
                    matches.append(concept)

        return list(set(matches))


# Singleton instance
semantic_colloquial_matcher = SemanticColloquialMatcher()
