"""DocAssistIQ — Discriminative "Next Best Test" Recommendation Engine.

When a patient's presentation narrows the differential diagnosis to top competing candidates,
this engine determines the single highest-yield diagnostic investigation or bedside maneuver
that decisively confirms Candidate #1 or rules out Candidate #2 (Maximum Information Gain).
"""

from typing import Dict, List, Any, Optional

DISCRIMINATIVE_PAIR_RULES: Dict[tuple, Dict[str, str]] = {
    # VHF & Tropical Pairs
    ("Bundibugyo Virus Disease (BVD)", "Severe Malaria / Cerebral Malaria"): {
        "test": "Stat Giemsa-stained Thick and Thin Blood Smears (Falciparum parasitemia) + Bundibugyo ebolavirus RT-PCR (BSL-4)",
        "rationale": "Directly differentiates high-density Plasmodium falciparum microvascular sequestration from filoviral viral hemorrhagic fever in a febrile traveler from DRC.",
        "urgency": "IMMEDIATE"
    },
    ("Bundibugyo Virus Disease (BVD)", "Malaria (Plasmodium falciparum)"): {
        "test": "Stat Thick and Thin Peripheral Blood Smears + Bundibugyo ebolavirus RT-PCR",
        "rationale": "Rapidly confirms or excludes intra-erythrocytic Plasmodium ring forms while evaluating filovirus viremia.",
        "urgency": "IMMEDIATE"
    },
    ("Bundibugyo Virus Disease (BVD)", "Ebola Virus Disease (Zaire)"): {
        "test": "Species-specific Orthoebolavirus RT-PCR (incorporating Bundibugyo-specific vs. Zaire-specific primers)",
        "rationale": "Critical therapeutic differentiation: Zaire monoclonals (Inmazeb, Ebanga) are completely ineffective against Bundibugyo virus.",
        "urgency": "IMMEDIATE"
    },
    ("Yellow Fever", "Hepatitis A"): {
        "test": "Serum Yellow Fever RT-PCR / IgM ELISA alongside Anti-HAV IgM Serology",
        "rationale": "Distinguishes toxic-phase flavivirus hepatorenal necrosis with coagulopathy from acute enteral picornavirus hepatitis.",
        "urgency": "IMMEDIATE"
    },
    ("Chikungunya", "Dengue Fever"): {
        "test": "Serum Dengue NS1 Antigen ELISA + Chikungunya RT-PCR with Serial Hematocrit",
        "rationale": "Identifies acute Dengue viremia and monitors for impending plasma leakage/thrombocytopenia vs. Chikungunya severe polyarthralgia.",
        "urgency": "URGENT"
    },
    ("Chikungunya", "Dengue Hemorrhagic Fever"): {
        "test": "Dengue NS1 Antigen / IgM ELISA and Serial Hematocrit/Platelet monitoring (q6h) vs Chikungunya RT-PCR",
        "rationale": "Differentiates debilitating post-arboviral arthralgia from life-threatening capillary leakage and severe thrombocytopenia.",
        "urgency": "IMMEDIATE"
    },

    # Neurological & Infectious Emergency Pairs
    ("Meningococcal Meningitis", "Bacterial Meningitis"): {
        "test": "Urgent Lumbar Puncture for CSF Gram Stain (Gram-negative diplococci) & Multiplex Meningitis PCR",
        "rationale": "Identifies Neisseria meningitidis with non-blanching purpura requiring immediate droplet isolation and close-contact chemoprophylaxis (Rifampin/Ciprofloxacin).",
        "urgency": "IMMEDIATE"
    },
    ("Meningococcal Disease / Meningococcemia (with Meningitis)", "Bacterial Meningitis"): {
        "test": "CSF Gram Stain and PCR + Paired Aerobic/Anaerobic Blood Cultures prior to IV Ceftriaxone",
        "rationale": "Differentiates invasive meningococcal disease with impending purpura fulminans from Streptococcus pneumoniae or Listeria meningitis.",
        "urgency": "IMMEDIATE"
    },
    ("Bacterial Meningitis", "Subarachnoid Hemorrhage"): {
        "test": "Non-contrast Head CT followed by Lumbar Puncture for CSF Opening Pressure, Cell Count (neutrophils vs. persistent RBCs across tubes 1-4), and Xanthochromia",
        "rationale": "Differentiates acute purulent bacterial infection of the subarachnoid space from aneurysmal rupture with hemorrhagic xanthochromia.",
        "urgency": "IMMEDIATE"
    },

    # Rare, Genetic, Metabolic & Rheumatologic Pairs
    ("Acute Intermittent Porphyria (AIP)", "Acute Appendicitis"): {
        "test": "Spot Urine Porphobilinogen (PBG) and ALA (light-protected sample) + Contrast-enhanced Abdominal CT",
        "rationale": "Conclusively identifies acute neurovisceral heme crisis (elevated PBG) and prevents unnecessary surgical laparotomy which can trigger fatal paralysis.",
        "urgency": "IMMEDIATE"
    },
    ("Insulin Autoimmune Syndrome (Hirata Disease)", "Preeclampsia with Severe Features"): {
        "test": "Serum Insulin Autoantibody (IAA) Titer with simultaneous Free/Total Insulin, C-peptide, and Urine Protein-to-Creatinine Ratio",
        "rationale": "Differentiates autoimmune postprandial hypoglycemia from gestational hypertensive end-organ disease.",
        "urgency": "URGENT"
    },
    ("Duchenne Muscular Dystrophy (DMD)", "Idiopathic Inflammatory Myopathy (Suspected Anti-Synthetase Syndrome / Dermatomyositis Spectrum)"): {
        "test": "Targeted DMD Gene MLPA Deletion/Duplication Testing vs. Extended Myositis-Specific Autoantibody Panel (anti-Jo-1, PL-7, PL-12, MDA5)",
        "rationale": "Differentiates an X-linked structural dystrophinopathy with calf pseudohypertrophy from an autoimmune idiopathic inflammatory myopathy with pulmonary involvement.",
        "urgency": "URGENT"
    },
    ("Gyrate Atrophy of the Choroid and Retina", "Retinitis Pigmentosa"): {
        "test": "Quantitative Plasma Amino Acid Chromatography (Plasma Ornithine Concentration) and OAT Gene Sequencing",
        "rationale": "Detects 10-20x hyperornithinemia pathognomonic for ornithine aminotransferase deficiency, which responds to dietary arginine restriction and pyridoxine.",
        "urgency": "ROUTINE"
    },
    ("Cryopyrin-Associated Periodic Syndrome (CAPS Spectrum / Muckle-Wells / FCAS)", "Bacterial Meningitis"): {
        "test": "Targeted NLRP3 (CIAS1) Gene Sequencing + Serum Amyloid A (SAA) with Lumbar Puncture CSF Cell Count/Gram Stain",
        "rationale": "Differentiates an inherited cryopyrin inflammasome autoinflammatory disorder from acute invasive bacterial neuroinfection.",
        "urgency": "IMMEDIATE"
    },
    ("Carnitine Palmitoyltransferase II (CPT II) Deficiency", "Hepatitis A"): {
        "test": "Tandem Mass Spectrometry (MS/MS) Plasma Acylcarnitine Profile (elevated C16, C18:1) & Urine Myoglobin Dipstick/Microscopy vs Anti-HAV IgM",
        "rationale": "Proves exercise-induced rhabdomyolytic myoglobinuria (heme positive without intact RBCs) and fatty acid oxidation defect vs hepatocellular hepatitis.",
        "urgency": "IMMEDIATE"
    },
    ("Hereditary Spastic Paraplegia (HSP)", "Serotonin Syndrome"): {
        "test": "Brain and Spinal Cord MRI (corticospinal tract evaluation) + Spastic Paraplegia NGS Gene Panel (SPG4, SPG3A, SPG7) vs Clinical Hunter Toxicity Criteria",
        "rationale": "Distinguishes chronic neurodegenerative upper motor neuron spasticity from acute drug-induced serotonergic neurotoxicity.",
        "urgency": "URGENT"
    },
    ("Mitochondrial Energy Metabolism Disorder (Suspected Respiratory Chain Complex Deficiency / Inborn Error of Metabolism)", "Gastroenteritis (Viral)"): {
        "test": "Venous/Arterial Blood Gas, Plasma Lactate & Pyruvate (L:P ratio), Urine Organic Acids, and Plasma Acylcarnitines",
        "rationale": "Detects severe high-anion-gap metabolic lactic acidosis and cellular oxidative phosphorylation defect during metabolic stress.",
        "urgency": "IMMEDIATE"
    },

    # Cardiovascular & Thoracic Emergencies
    ("Aortic Dissection", "Acute Myocardial Infarction (STEMI/NSTEMI)"): {
        "test": "STAT CT Angiography of Chest/Abdomen vs. Immediate 12-Lead ECG & High-Sensitivity Cardiac Troponin",
        "rationale": "Absolute clinical contraindication: Administering antiplatelets/anticoagulants for suspected MI in an undetected aortic dissection is fatal.",
        "urgency": "IMMEDIATE"
    },
    ("Acute Myocardial Infarction (STEMI/NSTEMI)", "Acute Pericarditis"): {
        "test": "12-Lead ECG (regional ST elevation with reciprocal depression vs diffuse concave ST elevation and PR depression) + High-Sensitivity Cardiac Troponin + Transthoracic Echocardiogram (TTE for regional wall motion abnormality)",
        "rationale": "Differentiates acute transmural coronary occlusion requiring emergent cath lab reperfusion from diffuse pericardial inflammation.",
        "urgency": "IMMEDIATE"
    },
    ("Pulmonary Embolism", "Acute Myocardial Infarction (STEMI/NSTEMI)"): {
        "test": "CT Pulmonary Angiography (CTPA) + High-Sensitivity Cardiac Troponin + 12-Lead ECG (RV strain pattern S1Q3T3 vs regional ST-T dynamics)",
        "rationale": "Differentiates massive/submassive pulmonary arterial mechanical obstruction from acute thrombotic coronary artery occlusion.",
        "urgency": "IMMEDIATE"
    },
    ("Pulmonary Embolism", "Pneumothorax (Tension Pneumothorax)"): {
        "test": "Point-of-Care Lung Ultrasound (POCUS: lung sliding and 'barcode sign' / lung point) + Upright Chest X-ray prior to CTPA",
        "rationale": "Excludes life-threatening tension pneumothorax requiring immediate needle decompression before pursuing CTPA.",
        "urgency": "IMMEDIATE"
    },
    ("Asthma Exacerbation", "Acute Decompensated Heart Failure (Cardiogenic Pulmonary Edema)"): {
        "test": "Serum NT-proBNP / BNP + Bedside Lung Ultrasound (diffuse B-lines 'wet lung' vs lung sliding with A-lines 'dry lung') + Chest X-ray",
        "rationale": "Distinguishes primary bronchospastic airway resistance from elevated left ventricular filling pressures and hydrostatic pulmonary alveolar transudation.",
        "urgency": "IMMEDIATE"
    },

    # Abdominal & Sepsis Emergencies
    ("Acute Pancreatitis", "Perforated Peptic Ulcer"): {
        "test": "Upright Chest X-ray / Non-contrast Abdominal CT (subdiaphragmatic free air / pneumoperitoneum) + Serum Lipase",
        "rationale": "Differentiates medical acute pancreatic autodigestion (Lipase >= 3x ULN) from a surgical visceral perforation requiring emergent laparotomy.",
        "urgency": "IMMEDIATE"
    },
    ("Septic Shock", "Cardiogenic Shock"): {
        "test": "Bedside Transthoracic Echocardiography (hyperdynamic vs severely reduced LV/RV contractility and IVC collapsibility) + Central Venous Oxygen Saturation (ScvO2) + Serial Lactate",
        "rationale": "Distinguishes low systemic vascular resistance distributive shock (requiring norepinephrine and aggressive crystalloid loading) from pump failure (where fluid boluses exacerbate lethal pulmonary edema).",
        "urgency": "IMMEDIATE"
    },
    ("Bacterial Meningitis", "Viral Meningoencephalitis (HSV-1)"): {
        "test": "Urgent Lumbar Puncture for CSF Multiplex PCR (HSV-1/2, VZV, Enterovirus) + CSF Gram Stain / Bacterial Culture + CSF Lactate & Glucose",
        "rationale": "Differentiates purulent bacterial infection requiring Ceftriaxone + Vancomycin + Dexamethasone from necrotizing temporal lobe HSV encephalitis requiring high-dose IV Acyclovir.",
        "urgency": "IMMEDIATE"
    },
}


class DiscriminativeTestEngine:
    """
    Evaluates Candidate #1 and Candidate #2 and selects the maximum information-gain diagnostic order.
    """

    def recommend(
        self,
        candidate_1: Any,
        candidate_2: Optional[Any] = None,
        **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Generates the single best differentiating investigation between top candidates.
        Accepts dict or str for candidate_1 and candidate_2.
        """
        if not candidate_1:
            return None

        if isinstance(candidate_1, dict):
            d1 = candidate_1.get("disease", "")
            c1_dict = candidate_1
        else:
            d1 = str(candidate_1)
            c1_dict = {"disease": d1}

        if not candidate_2:
            tests = c1_dict.get("recommended_investigations") or c1_dict.get("immediate_tests") or []
            test_name = tests[0] if tests else "Comprehensive diagnostic confirmatory panel"
            return {
                "candidate_1": d1,
                "candidate_2": None,
                "differentiating_investigation": test_name,
                "clinical_rationale": f"Primary confirmatory diagnostic evaluation for {d1}.",
                "urgency": c1_dict.get("triage", "URGENT"),
            }

        if isinstance(candidate_2, dict):
            d2 = candidate_2.get("disease", "")
            c2_dict = candidate_2
        else:
            d2 = str(candidate_2)
            c2_dict = {"disease": d2}

        # 1. Check explicit rules (both (d1, d2) and (d2, d1))
        if (d1, d2) in DISCRIMINATIVE_PAIR_RULES:
            rule = DISCRIMINATIVE_PAIR_RULES[(d1, d2)]
            return {
                "candidate_1": d1,
                "candidate_2": d2,
                "differentiating_investigation": rule["test"],
                "clinical_rationale": rule["rationale"],
                "urgency": rule["urgency"],
            }
        elif (d2, d1) in DISCRIMINATIVE_PAIR_RULES:
            rule = DISCRIMINATIVE_PAIR_RULES[(d2, d1)]
            return {
                "candidate_1": d1,
                "candidate_2": d2,
                "differentiating_investigation": rule["test"],
                "clinical_rationale": rule["rationale"],
                "urgency": rule["urgency"],
            }

        # 2. Algorithmic Fallback: Select candidate 1's top specific test not shared by candidate 2
        tests_1 = c1_dict.get("recommended_investigations") or c1_dict.get("immediate_tests") or []
        tests_2 = set(c2_dict.get("recommended_investigations") or c2_dict.get("immediate_tests") or [])

        differentiating_test = None
        for t in tests_1:
            if t not in tests_2 and not any(w in t.lower() for w in ["complete blood count", "metabolic panel", "cbc", "cmp"]):
                differentiating_test = t
                break

        if not differentiating_test and tests_1:
            differentiating_test = tests_1[0]

        if not differentiating_test:
            differentiating_test = f"Targeted diagnostic panel and confirmatory imaging for {d1}"

        return {
            "candidate_1": d1,
            "candidate_2": d2,
            "differentiating_investigation": differentiating_test,
            "clinical_rationale": f"Decisively discriminates between primary suspicion ({d1}) and secondary differential ({d2}).",
            "urgency": "IMMEDIATE" if c1_dict.get("severity") in ("critical", "high") else "URGENT",
        }


discriminative_test_engine = DiscriminativeTestEngine()
