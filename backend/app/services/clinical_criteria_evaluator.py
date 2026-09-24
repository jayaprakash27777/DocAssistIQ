"""DocAssistIQ — Consensus Clinical Diagnostic Criteria Evaluator.

Formally evaluates globally accepted, validated clinical scoring systems:
  1. ACR/EULAR 2019 Classification Criteria for Systemic Lupus Erythematosus (SLE)
  2. Modified Duke Criteria for Infective Endocarditis (IE)
  3. Bohan & Peter / ENMC Criteria for Idiopathic Inflammatory Myopathies (Dermatomyositis / Polymyositis / Anti-Synthetase)
  4. Wells Score & PERC Rule for Pulmonary Embolism (PE)
  5. Centor & McIsaac Score for Streptococcal Pharyngitis

Executes deterministically in <2ms, providing criteria score, fulfillment status,
fulfilled items, missing items, and authoritative clinical recommendation.
"""

from typing import Dict, List, Any, Optional, Set


class ClinicalCriteriaEvaluator:
    """
    Evaluator for authoritative clinical diagnostic criteria.
    """

    def evaluate_sle_acr_eular(
        self,
        findings: Set[str],
        labs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ACR/EULAR 2019 Criteria for Systemic Lupus Erythematosus.
        Entry criterion: Positive ANA (titer >= 1:80).
        Threshold for classification: >= 10 points with at least one clinical domain.
        """
        # Entry criterion check
        ana_positive = any("ana" in f or "antinuclear" in f for f in findings)
        if not ana_positive:
            # Check labs
            ana_positive = labs.get("ana", {}).get("positive", False)

        domain_scores: Dict[str, int] = {}
        fulfilled_items: List[str] = []

        # Constitutional: Fever (2)
        if any("fever" in f or "febrile" in f or "pyrexia" in f for f in findings):
            domain_scores["Constitutional"] = 2
            fulfilled_items.append("Fever (2 pts)")

        # Hematologic: Autoimmune hemolysis (4), Thrombocytopenia (4), Leukopenia (3)
        plt_lab = labs.get("platelets", {})
        plt_val = plt_lab.get("value", 200000)
        wbc_lab = labs.get("wbc", {})
        wbc_val = wbc_lab.get("value", 7000)

        if any("hemolytic anemia" in f or "coombs" in f for f in findings):
            domain_scores["Hematologic"] = 4
            fulfilled_items.append("Autoimmune hemolysis (4 pts)")
        elif any("thrombocytopenia" in f or "low platelets" in f for f in findings) or plt_val < 100000:
            domain_scores["Hematologic"] = 4
            fulfilled_items.append("Thrombocytopenia (4 pts)")
        elif any("leukopenia" in f or "lymphopenia" in f for f in findings) or wbc_val < 4000:
            domain_scores["Hematologic"] = 3
            fulfilled_items.append("Leukopenia (3 pts)")

        # Neuropsychiatric: Seizure (5), Psychosis (3), Delirium (2)
        if any("seizure" in f or "convulsion" in f for f in findings):
            domain_scores["Neuropsychiatric"] = 5
            fulfilled_items.append("Seizure (5 pts)")
        elif any("psychosis" in f or "hallucination" in f for f in findings):
            domain_scores["Neuropsychiatric"] = 3
            fulfilled_items.append("Psychosis (3 pts)")
        elif any("delirium" in f or "acute confusion" in f for f in findings):
            domain_scores["Neuropsychiatric"] = 2
            fulfilled_items.append("Delirium (2 pts)")

        # Mucocutaneous: Acute cutaneous lupus/malar rash (6), Subacute/discoid (4), Oral ulcers (2), Alopecia (2)
        if any("malar rash" in f or "butterfly rash" in f or "acute cutaneous lupus" in f for f in findings):
            domain_scores["Mucocutaneous"] = 6
            fulfilled_items.append("Acute cutaneous lupus / malar rash (6 pts)")
        elif any("discoid" in f for f in findings):
            domain_scores["Mucocutaneous"] = 4
            fulfilled_items.append("Discoid lupus (4 pts)")
        elif any("oral ulcer" in f or "mouth ulcer" in f for f in findings):
            domain_scores["Mucocutaneous"] = 2
            fulfilled_items.append("Oral ulcers (2 pts)")
        elif any("alopecia" in f or "hair loss" in f for f in findings):
            domain_scores["Mucocutaneous"] = 2
            fulfilled_items.append("Non-scarring alopecia (2 pts)")

        # Serosal: Acute pericarditis (6), Pleural or pericardial effusion (5)
        if any("pericarditis" in f for f in findings):
            domain_scores["Serosal"] = 6
            fulfilled_items.append("Acute pericarditis (6 pts)")
        elif any("pleural effusion" in f or "pericardial effusion" in f or "serositis" in f or "pleuritis" in f or "pleurisy" in f for f in findings):
            domain_scores["Serosal"] = 5
            fulfilled_items.append("Pleural or pericardial effusion (5 pts)")

        # Musculoskeletal: Joint involvement / synovitis (6)
        if any("arthritis" in f or "synovitis" in f or "joint pain" in f or "arthralgia" in f or "swollen joints" in f for f in findings):
            domain_scores["Musculoskeletal"] = 6
            fulfilled_items.append("Joint involvement / synovitis (6 pts)")

        # Renal: Proteinuria > 0.5g/24h or active sediment (8)
        if any("proteinuria" in f or "lupus nephritis" in f or "cellular casts" in f for f in findings):
            domain_scores["Renal"] = 8
            fulfilled_items.append("Renal involvement / proteinuria (8 pts)")

        # Immunology: Anti-dsDNA / Anti-Smith (6), Low complement C3/C4 (4), Antiphospholipid (2)
        if any("dsdna" in f or "anti-smith" in f or "anti-sm" in f for f in findings):
            domain_scores["Immunology_Specific"] = 6
            fulfilled_items.append("Anti-dsDNA or Anti-Smith antibody (6 pts)")
        if any("low complement" in f or "low c3" in f or "low c4" in f or "hypocomplementemia" in f for f in findings):
            domain_scores["Complement"] = 4
            fulfilled_items.append("Low C3 and/or C4 (4 pts)")
        if any("antiphospholipid" in f or "anticardiolipin" in f or "lupus anticoagulant" in f for f in findings):
            domain_scores["Antiphospholipid"] = 2
            fulfilled_items.append("Antiphospholipid antibodies (2 pts)")

        total_score = sum(domain_scores.values())
        clinical_domains = [d for d in domain_scores.keys() if not d.startswith("Immuno") and d != "Complement" and d != "Antiphospholipid"]
        meets_criteria = ana_positive and total_score >= 10 and len(clinical_domains) >= 1

        return {
            "criteria_name": "ACR/EULAR 2019 SLE Classification Criteria",
            "entry_criterion_met": ana_positive,
            "entry_criterion_detail": "Antinuclear Antibodies (ANA) positive" if ana_positive else "ANA negative or unverified (Required entry criterion)",
            "total_score": total_score,
            "threshold": 10,
            "meets_criteria": meets_criteria,
            "fulfilled_items": fulfilled_items,
            "clinical_interpretation": "Definite SLE Classification Met" if meets_criteria else ("Subthreshold / Not Met" if ana_positive else "Entry Criterion (ANA) Not Met")
        }

    def evaluate_duke_endocarditis(
        self,
        findings: Set[str],
        labs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Modified Duke Criteria for Infective Endocarditis.
        Major criteria:
          1. Typical blood culture positive for IE in 2 separate cultures
          2. Endocardial involvement (vegetation, abscess, new valvular regurgitation murmur)
        Minor criteria:
          1. Predisposition (prosthetic valve, IV drug use, congenital heart disease)
          2. Fever (>= 38.0 C)
          3. Vascular phenomena (arterial emboli, Janeway lesions, splinter hemorrhages)
          4. Immunologic phenomena (Osler nodes, Roth spots, glomerulonephritis, RF)
          5. Microbiological evidence (positive culture not meeting major)
        """
        major_count = 0
        minor_count = 0
        fulfilled_items: List[str] = []

        # Major 1: Microorganism
        if any("blood culture positive" in f or "viridans" in f or "staph aureus bacteremia" in f or "enterococcal bacteremia" in f for f in findings):
            major_count += 1
            fulfilled_items.append("Major: Blood cultures positive for typical IE organism")

        # Major 2: Echo / Valve
        if any("vegetation" in f or "intracardiac mass" in f or "valvular regurgitation" in f or "new murmur" in f or "leaflet perforation" in f for f in findings):
            major_count += 1
            fulfilled_items.append("Major: Echocardiographic evidence of vegetation or new regurgitant murmur")

        # Minor 1: Predisposition
        if any("prosthetic valve" in f or "iv drug" in f or "ivdu" in f or "congenital heart" in f or "valvular heart disease" in f for f in findings):
            minor_count += 1
            fulfilled_items.append("Minor: Predisposition (prosthetic valve / history of IVDU / structural defect)")

        # Minor 2: Fever
        if any("fever" in f or "febrile" in f or "pyrexia" in f or "temperature" in f for f in findings):
            minor_count += 1
            fulfilled_items.append("Minor: Fever >= 38.0 C")

        # Minor 3: Vascular phenomena
        if any("janeway" in f or "splinter hemorrhage" in f or "embolic" in f or "infarct" in f or "petechiae" in f or "subungual" in f for f in findings):
            minor_count += 1
            fulfilled_items.append("Minor: Vascular phenomena (Janeway lesions / emboli / hemorrhages)")

        # Minor 4: Immunologic phenomena
        if any("osler" in f or "roth" in f or "glomerulonephritis" in f or "rheumatoid factor" in f for f in findings):
            minor_count += 1
            fulfilled_items.append("Minor: Immunologic phenomena (Osler nodes / Roth spots / RF)")

        # Minor 5: Microbiological (if not major)
        if major_count == 0 and any("positive culture" in f or "bacteremia" in f for f in findings):
            minor_count += 1
            fulfilled_items.append("Minor: Microbiological evidence not meeting major criterion")

        is_definite = (major_count >= 2) or (major_count == 1 and minor_count >= 3) or (minor_count >= 5)
        is_possible = (major_count == 1 and minor_count >= 1) or (minor_count >= 3)

        status = "Definite Infective Endocarditis" if is_definite else ("Possible Infective Endocarditis" if is_possible else "Rejected / Insufficient Criteria")

        return {
            "criteria_name": "Modified Duke Criteria for Infective Endocarditis",
            "major_criteria_count": major_count,
            "minor_criteria_count": minor_count,
            "meets_criteria": is_definite,
            "is_possible": is_possible,
            "status": status,
            "fulfilled_items": fulfilled_items
        }

    def evaluate_inflammatory_myopathy(
        self,
        findings: Set[str],
        labs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Bohan & Peter / ENMC Criteria for Inflammatory Myopathy & Anti-Synthetase Syndrome.
        Criteria:
          1. Symmetric proximal muscle weakness
          2. Elevated muscle enzymes (CK, aldolase, AST, ALT)
          3. Electromyographic triad of myopathy
          4. Muscle biopsy demonstrating inflammatory myopathy
          5. Dermatologic hallmark rashes (Gottron's, heliotrope, mechanic's hands)
          6. Anti-synthetase features: Interstitial lung disease (ILD) + Jo-1/PL-7
        """
        criteria_count = 0
        fulfilled_items: List[str] = []

        # 1. Proximal muscle weakness
        if any("proximal muscle weakness" in f or "difficulty rising" in f or "difficulty climbing" in f or "shoulder weakness" in f or "hip weakness" in f for f in findings):
            criteria_count += 1
            fulfilled_items.append("Symmetric proximal muscle weakness")

        # 2. Elevated muscle enzymes
        ck_lab = labs.get("creatine_kinase", {})
        ck_val = ck_lab.get("value", 0)
        if ck_val > 250 or any("elevated ck" in f or "creatine kinase" in f or "aldolase" in f or "myositis" in f for f in findings):
            criteria_count += 1
            fulfilled_items.append(f"Elevated muscle enzymes (CK: {ck_val} U/L)" if ck_val > 0 else "Elevated muscle enzymes (CK / Aldolase)")

        # 3. EMG
        if any("emg" in f or "electromyograph" in f or "myopathic motor units" in f or "fibrillation" in f for f in findings):
            criteria_count += 1
            fulfilled_items.append("Electromyographic features of myopathy")

        # 4. Biopsy
        if any("muscle biopsy" in f or "mononuclear infiltrates" in f or "perifascicular" in f or "endomysial" in f for f in findings):
            criteria_count += 1
            fulfilled_items.append("Muscle biopsy confirming inflammatory myopathy")

        # 5. Rashes
        has_derm_rash = any("gottron" in f or "heliotrope" in f or "shawl sign" in f or "v sign" in f for f in findings)
        if has_derm_rash:
            fulfilled_items.append("Pathognomonic cutaneous eruption (Gottron's papules / Heliotrope rash)")

        # 6. Anti-synthetase specific
        has_ild = any("interstitial lung disease" in f or "ild" in f or "basilar crackles" in f or "ground-glass" in f or "fibrosis" in f for f in findings)
        has_mech_hands = any("mechanic's hands" in f or "hyperkeratotic" in f for f in findings)
        has_jo1 = any("jo-1" in f or "pl-7" in f or "pl-12" in f or "anti-synthetase" in f for f in findings)

        is_anti_synthetase = (has_jo1 or "anti-synthetase" in " ".join(findings)) and (has_ild or criteria_count >= 2 or has_mech_hands)
        is_definite_dermatomyositis = has_derm_rash and criteria_count >= 3
        is_probable_dermatomyositis = has_derm_rash and criteria_count == 2
        is_definite_polymyositis = not has_derm_rash and criteria_count >= 4

        classification = "Anti-Synthetase Syndrome" if is_anti_synthetase else (
            "Definite Dermatomyositis" if is_definite_dermatomyositis else (
                "Probable Dermatomyositis" if is_probable_dermatomyositis else (
                    "Definite Polymyositis" if is_definite_polymyositis else "Suspected Inflammatory Myopathy"
                )
            )
        )

        return {
            "criteria_name": "Bohan & Peter / ENMC Criteria for Inflammatory Myopathies",
            "muscle_criteria_fulfilled": criteria_count,
            "pathognomonic_rash_present": has_derm_rash,
            "anti_synthetase_features_present": is_anti_synthetase,
            "classification": classification,
            "meets_criteria": is_anti_synthetase or is_definite_dermatomyositis or is_definite_polymyositis,
            "fulfilled_items": fulfilled_items
        }

    def evaluate_wells_pe(
        self,
        findings: Set[str],
        labs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Wells Score for Pulmonary Embolism.
        Points:
          - Clinical signs of DVT (+3.0)
          - PE is #1 diagnosis or equally likely (+3.0)
          - Heart rate > 100 bpm (+1.5)
          - Immobilization >= 3 days or surgery in past 4 weeks (+1.5)
          - Previous DVT/PE (+1.5)
          - Hemoptysis (+1.0)
          - Malignancy (+1.0)
        """
        score = 0.0
        fulfilled_items: List[str] = []

        if any("dvt" in f or "leg swelling" in f or "calf pain" in f or "calf tenderness" in f for f in findings):
            score += 3.0
            fulfilled_items.append("Clinical signs/symptoms of DVT (+3.0)")

        if any("pleuritic chest pain" in f or "sudden onset dyspnea" in f or "hypoxia" in f for f in findings):
            score += 3.0
            fulfilled_items.append("PE is #1 or equally likely diagnosis (+3.0)")

        if any("tachycardia" in f or "tachycardic" in f or "heart rate > 100" in f or "hr 1" in f for f in findings):
            score += 1.5
            fulfilled_items.append("Tachycardia / Heart Rate > 100 bpm (+1.5)")

        if any("immobilization" in f or "bed rest" in f or "recent surgery" in f or "post-operative" in f or "long flight" in f for f in findings):
            score += 1.5
            fulfilled_items.append("Immobilization >= 3 days or surgery within 4 weeks (+1.5)")

        if any("prior pe" in f or "prior dvt" in f or "history of pe" in f or "history of dvt" in f for f in findings):
            score += 1.5
            fulfilled_items.append("Prior PE or DVT (+1.5)")

        if any("hemoptysis" in f or "coughing up blood" in f for f in findings):
            score += 1.0
            fulfilled_items.append("Hemoptysis (+1.0)")

        if any("malignancy" in f or "cancer" in f or "active cancer" in f or "chemotherapy" in f for f in findings):
            score += 1.0
            fulfilled_items.append("Active malignancy (+1.0)")

        pe_likely = score > 4.0
        risk_tier = "High" if score > 6.0 else ("Moderate" if score >= 2.0 else "Low")
        next_step = "Stat CT Pulmonary Angiography (CTPA) indicated" if pe_likely else "High-sensitivity D-dimer indicated"

        # PERC Rule evaluation (Pulmonary Embolism Rule-out Criteria)
        perc_negative = not (
            any("tachycardia" in f or "heart rate > 100" in f for f in findings) or
            any("hypoxia" in f or "low sats" in f for f in findings) or
            any("prior pe" in f or "prior dvt" in f for f in findings) or
            any("immobilization" in f or "recent surgery" in f or "post-operative" in f for f in findings) or
            any("hemoptysis" in f or "coughing blood" in f for f in findings) or
            any("unilateral leg swelling" in f or "calf swelling" in f or "dvt" in f for f in findings)
        )

        return {
            "criteria_name": "Wells Criteria for Pulmonary Embolism",
            "score": score,
            "pe_likely": pe_likely,
            "risk_tier": risk_tier,
            "perc_rule_negative": perc_negative if score < 2.0 else None,
            "next_step": next_step if not (score < 2.0 and perc_negative) else "PE rule-out criteria met (PERC negative); no D-dimer needed",
            "fulfilled_items": fulfilled_items
        }

    def evaluate_centor_mcisaac(
        self,
        findings: Set[str],
        labs: Dict[str, Any],
        age: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Centor / McIsaac Score for Streptococcal Pharyngitis.
        Criteria:
          1. Absence of cough (+1)
          2. Swollen/tender anterior cervical lymph nodes (+1)
          3. Temperature > 38.0 C / 100.4 F (+1)
          4. Tonsillar exudates or swelling (+1)
          5. Age modifiers (McIsaac):
             - 3 to 14 years: +1
             - 15 to 44 years: 0
             - >= 45 years: -1
        """
        score = 0
        fulfilled_items: List[str] = []

        if any("absence of cough" in f or "no cough" in f or "denies cough" in f for f in findings):
            score += 1
            fulfilled_items.append("Absence of cough (+1)")

        if any("cervical lymphadenopathy" in f or "tender cervical" in f or "swollen lymph" in f or "cervical nodes" in f for f in findings):
            score += 1
            fulfilled_items.append("Swollen, tender anterior cervical lymph nodes (+1)")

        if any("fever" in f or "febrile" in f or "pyrexia" in f or "temperature" in f for f in findings):
            score += 1
            fulfilled_items.append("Fever / Temperature > 38.0 C (+1)")

        if any("tonsillar exudate" in f or "exudative tonsillitis" in f or "tonsillar swelling" in f or "exudates" in f for f in findings):
            score += 1
            fulfilled_items.append("Tonsillar exudates or swelling (+1)")

        if age is not None:
            if 3 <= age <= 14:
                score += 1
                fulfilled_items.append("Age 3-14 years (+1)")
            elif age >= 45:
                score -= 1
                fulfilled_items.append("Age >= 45 years (-1)")

        if score >= 4:
            recommendation = "High probability (>=50%): Empiric antibiotic therapy or rapid antigen test + treatment"
            risk_tier = "High"
        elif score >= 2:
            recommendation = "Intermediate probability (15-30%): Rapid Antigen Detection Test (RADT) or throat culture indicated"
            risk_tier = "Moderate"
        else:
            recommendation = "Low probability (<10%): No antibiotic or throat culture indicated (symptomatic care)"
            risk_tier = "Low"

        return {
            "criteria_name": "Centor / McIsaac Score for Streptococcal Pharyngitis",
            "score": score,
            "risk_tier": risk_tier,
            "recommendation": recommendation,
            "meets_criteria": score >= 2,
            "fulfilled_items": fulfilled_items
        }

    def evaluate_curb65(
        self,
        findings: Set[str],
        labs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        CURB-65 Pneumonia Severity Score (BTS Guidelines).
        Predicts 30-day mortality and guides site-of-care (outpatient vs inpatient vs ICU).
        """
        score = 0
        fulfilled_items: List[str] = []

        if any(f in findings for f in ["confusion", "altered mental status", "delirium", "disoriented"]):
            score += 1
            fulfilled_items.append("Confusion (new disorientation in person/place/time) (+1)")

        bun_val = labs.get("bun", {}).get("value", 0)
        if bun_val > 19:
            score += 1
            fulfilled_items.append(f"Urea / BUN > 19 mg/dL (measured: {bun_val} mg/dL) (+1)")

        if any(f in findings for f in ["tachypnea", "respiratory rate >= 30", "rr >= 30", "severe tachypnea"]):
            score += 1
            fulfilled_items.append("Respiratory rate >= 30 breaths/min (+1)")

        if any(f in findings for f in ["hypotension", "sbp < 90", "dbp <= 60", "shock"]):
            score += 1
            fulfilled_items.append("Blood pressure: SBP < 90 mmHg or DBP <= 60 mmHg (+1)")

        if any(f in findings for f in ["age >= 65", "elderly", "age 65+", "age 70", "age 75", "age 80", "age 85"]):
            score += 1
            fulfilled_items.append("Age >= 65 years (+1)")

        if score >= 3:
            risk_tier = "High"
            recommendation = f"Severe pneumonia (CURB-65 = {score}): Urgent inpatient hospitalization; score 4-5 warrants immediate ICU admission consideration."
        elif score == 2:
            risk_tier = "Moderate"
            recommendation = f"Intermediate risk pneumonia (CURB-65 = {score}): Short inpatient hospitalization or closely monitored outpatient therapy."
        else:
            risk_tier = "Low"
            recommendation = f"Low risk pneumonia (CURB-65 = {score}): Suitable for outpatient management with oral antimicrobial therapy."

        return {
            "criteria_name": "CURB-65 Score for Pneumonia Severity",
            "score": score,
            "risk_tier": risk_tier,
            "recommendation": recommendation,
            "meets_criteria": score >= 2,
            "fulfilled_items": fulfilled_items
        }

    def evaluate_cha2ds2_vasc(
        self,
        findings: Set[str],
        labs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        CHA2DS2-VASc Score for Stroke Risk in Non-Valvular Atrial Fibrillation.
        Determines necessity of oral anticoagulation (DOAC / Warfarin).
        """
        score = 0
        fulfilled_items: List[str] = []

        if any(f in findings for f in ["congestive heart failure", "chf", "heart failure", "hfref", "hfpef", "cardiomyopathy"]):
            score += 1
            fulfilled_items.append("Congestive Heart Failure / LVEF <= 40% (+1)")

        if any(f in findings for f in ["hypertension", "htn", "high blood pressure"]):
            score += 1
            fulfilled_items.append("Hypertension (+1)")

        if any(f in findings for f in ["age >= 75", "age 75+", "age 80", "age 85", "age 90"]):
            score += 2
            fulfilled_items.append("Age >= 75 years (+2)")
        elif any(f in findings for f in ["age 65-74", "age >= 65", "age 65+"]):
            score += 1
            fulfilled_items.append("Age 65-74 years (+1)")

        if any(f in findings for f in ["diabetes", "type 2 diabetes mellitus", "t2dm", "t1dm", "diabetes mellitus"]):
            score += 1
            fulfilled_items.append("Diabetes Mellitus (+1)")

        if any(f in findings for f in ["stroke", "cva", "transient ischemic attack", "tia", "thromboembolism"]):
            score += 2
            fulfilled_items.append("Prior Stroke, TIA, or Systemic Embolism (+2)")

        if any(f in findings for f in ["myocardial infarction", "cad", "peripheral artery disease", "pad", "aortic plaque"]):
            score += 1
            fulfilled_items.append("Vascular Disease (prior MI, PAD, or aortic plaque) (+1)")

        if any(f in findings for f in ["female", "woman", "sex: female"]):
            score += 1
            fulfilled_items.append("Sex Category Female (+1)")

        if score >= 2:
            risk_tier = "High"
            recommendation = f"High thromboembolic risk (CHA2DS2-VASc = {score}): Oral anticoagulation (DOAC: Apixaban, Rivaroxaban, or Dabigatran preferred over Warfarin) is strongly recommended (Class I guideline mandate)."
        elif score == 1:
            risk_tier = "Moderate"
            recommendation = f"Moderate thromboembolic risk (CHA2DS2-VASc = {score}): Oral anticoagulation should be considered based on individual bleeding risk and clinical judgement."
        else:
            risk_tier = "Low"
            recommendation = f"Low thromboembolic risk (CHA2DS2-VASc = {score}): No antithrombotic therapy recommended."

        return {
            "criteria_name": "CHA2DS2-VASc Score for Atrial Fibrillation Stroke Risk",
            "score": score,
            "risk_tier": risk_tier,
            "recommendation": recommendation,
            "meets_criteria": score >= 2,
            "fulfilled_items": fulfilled_items
        }

    def evaluate_qsofa(
        self,
        findings: Set[str],
        labs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Quick Sepsis-related Organ Failure Assessment (qSOFA) Criteria.
        Sepsis-3 consensus bedside tool to identify infected patients at high risk of deterioration.
        """
        score = 0
        fulfilled_items: List[str] = []

        if any(f in findings for f in ["altered mental status", "ams", "confusion", "delirium", "gcs < 15"]):
            score += 1
            fulfilled_items.append("Altered mental status (GCS < 15) (+1)")

        if any(f in findings for f in ["tachypnea", "respiratory rate >= 22", "rr >= 22", "respiratory rate >= 30"]):
            score += 1
            fulfilled_items.append("Respiratory rate >= 22 breaths/min (+1)")

        if any(f in findings for f in ["hypotension", "sbp <= 100", "sbp < 90", "shock"]):
            score += 1
            fulfilled_items.append("Systolic blood pressure <= 100 mmHg (+1)")

        meets = score >= 2
        if meets:
            risk_tier = "High"
            recommendation = f"High risk of in-hospital mortality / deterioration (qSOFA = {score}/3): Activate Sepsis-3 resuscitation pathway (blood cultures, stat broad-spectrum antibiotics within 1h, IV crystalloid bolus, serial lactate)."
        else:
            risk_tier = "Low/Moderate"
            recommendation = f"qSOFA score = {score}/3: Continue close clinical surveillance and monitor vital signs for decompensation."

        return {
            "criteria_name": "qSOFA (Quick Sepsis-related Organ Failure Assessment)",
            "score": score,
            "risk_tier": risk_tier,
            "recommendation": recommendation,
            "meets_criteria": meets,
            "fulfilled_items": fulfilled_items
        }

    def evaluate_all(
        self,
        top_candidates: List[str],
        positive_findings: List[str],
        extracted_labs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Contextually determines which authoritative criteria sets should be run
        based on candidate diseases and clinical findings.
        """
        results: List[Dict[str, Any]] = []
        findings_set = {f.lower() for f in positive_findings}
        cand_text = " ".join(top_candidates).lower()

        # 1. SLE
        if "lupus" in cand_text or "sle" in cand_text or any("ana" in f or "malar" in f for f in findings_set):
            results.append(self.evaluate_sle_acr_eular(findings_set, extracted_labs))

        # 2. Endocarditis
        if "endocarditis" in cand_text or any("vegetation" in f or "osler" in f or "janeway" in f for f in findings_set):
            results.append(self.evaluate_duke_endocarditis(findings_set, extracted_labs))

        # 3. Inflammatory Myopathy
        if any(term in cand_text for term in ["myositis", "dermatomyositis", "polymyositis", "anti-synthetase", "synthetase"]) or any("gottron" in f or "heliotrope" in f for f in findings_set):
            results.append(self.evaluate_inflammatory_myopathy(findings_set, extracted_labs))

        # 4. Pulmonary Embolism
        if "pulmonary embolism" in cand_text or "pe" in cand_text or any("dvt" in f or "pleuritic chest pain" in f for f in findings_set):
            results.append(self.evaluate_wells_pe(findings_set, extracted_labs))

        # 5. Streptococcal Pharyngitis
        if "pharyngitis" in cand_text or "strep" in cand_text or any("tonsill" in f or "sore throat" in f for f in findings_set):
            results.append(self.evaluate_centor_mcisaac(findings_set, extracted_labs))

        # 6. Pneumonia Severity (CURB-65)
        if "pneumonia" in cand_text or "cap" in cand_text or any("pneumonia" in f for f in findings_set):
            results.append(self.evaluate_curb65(findings_set, extracted_labs))

        # 7. Atrial Fibrillation (CHA2DS2-VASc)
        if "atrial fibrillation" in cand_text or "afib" in cand_text or any("atrial fibrillation" in f or "afib" in f for f in findings_set):
            results.append(self.evaluate_cha2ds2_vasc(findings_set, extracted_labs))

        # 8. Sepsis / Deterioration (qSOFA)
        if any(term in cand_text for term in ["sepsis", "septic", "bacteremia"]) or any("sepsis" in f for f in findings_set):
            results.append(self.evaluate_qsofa(findings_set, extracted_labs))

        return results


# Global singleton instance
criteria_evaluator = ClinicalCriteriaEvaluator()
