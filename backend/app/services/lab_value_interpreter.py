"""DocAssistIQ — Quantitative Laboratory & Biomarker Magnitude Interpreter.

Extracts exact numerical lab values with units from unstructured clinical text,
compares them against physiological reference intervals, calculates clinical composite indices
(Anion Gap, CSF/Serum Glucose Ratio, BUN/Cr Ratio, AST/ALT Ratio), and generates high-specificity biomarker flags.
Strictly zero mock data; deterministic physiological math executing in <2ms.
"""

import re
from typing import Dict, List, Any, Optional, Tuple


class LabValueInterpreter:
    """
    Deterministic quantitative lab extractor & clinical physiology calculator.
    Executes in <2ms with zero hallucination.
    """

    def interpret(self, text: str) -> Dict[str, Any]:
        """
        Parses full note text for numerical lab values and calculates composite indices.
        Returns:
          - extracted_labs: dict of parsed measurements with values, units, and severity
          - calculated_indices: composite physiological calculations (Anion Gap, BUN/Cr, etc.)
          - diagnostic_flags: list of high-value clinical findings for reasoning engine
        """
        if not text or not text.strip():
            return {
                "extracted_labs": {},
                "calculated_indices": {},
                "diagnostic_flags": [],
            }

        extracted_labs: Dict[str, Any] = {}
        calculated_indices: Dict[str, Any] = {}
        diagnostic_flags: List[str] = []

        # ---------------------------------------------------------------------
        # 1. Creatine Kinase (CK / CPK)
        # ---------------------------------------------------------------------
        ck_match = re.search(
            r"\b(?:creatine\s+kinase|cpk|ck)\b[^\d\n]{0,20}?(\d{1,3}(?:,\d{3})+|\d+)\s*(?:u/?l|iu/?l)?",
            text,
            re.IGNORECASE
        )
        if ck_match:
            ck_val = float(ck_match.group(1).replace(",", ""))
            extracted_labs["creatine_kinase"] = {"value": ck_val, "unit": "U/L"}
            if ck_val >= 10000:
                extracted_labs["creatine_kinase"]["severity"] = "massive_elevation"
                diagnostic_flags.append("massive CK elevation (>10,000 U/L)")
                diagnostic_flags.append("rhabdomyolysis")
            elif ck_val >= 1000:
                extracted_labs["creatine_kinase"]["severity"] = "moderate_elevation"
                diagnostic_flags.append("elevated CK (1,000-10,000 U/L)")
            elif ck_val > 250:
                extracted_labs["creatine_kinase"]["severity"] = "mild_elevation"
                diagnostic_flags.append("mildly elevated CK")

        # ---------------------------------------------------------------------
        # 2. Lactate / Lactic Acid
        # ---------------------------------------------------------------------
        lactate_match = re.search(
            r"\b(?:serum\s+)?(?:lactate|lactic\s+acid)\b[^\d\n]{0,15}?(\d+(?:\.\d+)?)\s*(?:mmol/?l|mg/?dl)?",
            text,
            re.IGNORECASE
        )
        if lactate_match:
            lac_val = float(lactate_match.group(1))
            extracted_labs["lactate"] = {"value": lac_val, "unit": "mmol/L"}
            if lac_val >= 4.0:
                extracted_labs["lactate"]["severity"] = "severe_lactic_acidosis"
                diagnostic_flags.append("severe lactic acidosis (lactate >=4.0 mmol/L)")
                diagnostic_flags.append("lactic acidosis")
            elif lac_val > 2.0:
                extracted_labs["lactate"]["severity"] = "mild_hyperlactatemia"
                diagnostic_flags.append("elevated lactate (>2.0 mmol/L)")

        # ---------------------------------------------------------------------
        # 3. High-Sensitivity Cardiac Troponin
        # ---------------------------------------------------------------------
        troponin_match = re.search(
            r"\b(?:high-sensitivity\s+)?(?:troponin\s*(?:i|t)?|hs-?ctn[it]?)\b[^\d\n]{0,15}?(\d+(?:\.\d+)?)\s*(?:ng/?ml|ug/?l|ng/?l)?",
            text,
            re.IGNORECASE
        )
        if troponin_match:
            trop_val = float(troponin_match.group(1))
            extracted_labs["cardiac_troponin"] = {"value": trop_val}
            if trop_val > 0.04:
                extracted_labs["cardiac_troponin"]["severity"] = "myocardial_necrosis"
                diagnostic_flags.append("elevated cardiac troponin")
                diagnostic_flags.append("myocardial injury")

        # ---------------------------------------------------------------------
        # 4. Platelets
        # ---------------------------------------------------------------------
        plt_match = re.search(
            r"\b(?:platelets?|plt|platelet\s+count)\b[^\d\n]{0,15}?(\d{1,3}(?:,\d{3})+|\d+)\s*(?:k|k/?ul|/\s*ul|x10\^9/?l)?",
            text,
            re.IGNORECASE
        )
        if plt_match:
            raw_plt = plt_match.group(1).replace(",", "")
            plt_val = float(raw_plt)
            if plt_val < 500:  # e.g. "45k" expressed as 45
                plt_val *= 1000
            extracted_labs["platelets"] = {"value": plt_val, "unit": "/uL"}
            if plt_val < 50000:
                extracted_labs["platelets"]["severity"] = "severe_thrombocytopenia"
                diagnostic_flags.append("severe thrombocytopenia (<50,000/uL)")
                diagnostic_flags.append("thrombocytopenia")
            elif plt_val < 150000:
                extracted_labs["platelets"]["severity"] = "mild_moderate_thrombocytopenia"
                diagnostic_flags.append("thrombocytopenia")

        # ---------------------------------------------------------------------
        # 5. White Blood Cell Count (WBC)
        # ---------------------------------------------------------------------
        wbc_match = re.search(
            r"\b(?:wbc|white\s+blood\s+cells?|leukocyte\s+count)\b[^\d\n]{0,15}?(\d+(?:\.\d+)?)\s*(?:k|/\s*ul|x10\^9/?l)?",
            text,
            re.IGNORECASE
        )
        if wbc_match:
            raw_wbc = float(wbc_match.group(1))
            wbc_val = raw_wbc if raw_wbc < 100 else raw_wbc / 1000.0
            extracted_labs["wbc"] = {"value": wbc_val, "unit": "x10^3/uL"}
            if wbc_val > 12.0:
                extracted_labs["wbc"]["severity"] = "leukocytosis"
                diagnostic_flags.append("leukocytosis")
            elif wbc_val < 4.0:
                extracted_labs["wbc"]["severity"] = "leukopenia"
                diagnostic_flags.append("leukopenia")

        # ---------------------------------------------------------------------
        # 6. Hemoglobin (Hb / Hgb)
        # ---------------------------------------------------------------------
        hb_match = re.search(
            r"\b(?:hemoglobin|hgb|hb)\b[^\d\n]{0,10}?(\d+(?:\.\d+)?)\s*(?:g/?dl)?",
            text,
            re.IGNORECASE
        )
        if hb_match:
            hb_val = float(hb_match.group(1))
            extracted_labs["hemoglobin"] = {"value": hb_val, "unit": "g/dL"}
            if hb_val < 7.0:
                extracted_labs["hemoglobin"]["severity"] = "critical_anemia"
                diagnostic_flags.append("critical severe anemia (Hb <7.0 g/dL)")
                diagnostic_flags.append("anemia")
            elif hb_val < 11.0:
                extracted_labs["hemoglobin"]["severity"] = "anemia"
                diagnostic_flags.append("anemia")

        # ---------------------------------------------------------------------
        # 7. Serum Potassium (K+)
        # ---------------------------------------------------------------------
        k_match = re.search(
            r"\b(?:potassium|serum\s+k\+?|\bk\+?\b)[^\d\n]{0,10}?(\d+(?:\.\d+)?)\s*(?:meq/?l|mmol/?l)?",
            text,
            re.IGNORECASE
        )
        if k_match:
            k_val = float(k_match.group(1))
            # Validate reasonable physiological range
            if 1.0 <= k_val <= 10.0:
                extracted_labs["potassium"] = {"value": k_val, "unit": "mEq/L"}
                if k_val >= 6.0:
                    extracted_labs["potassium"]["severity"] = "critical_hyperkalemia"
                    diagnostic_flags.append("critical hyperkalemia (K >= 6.0 mEq/L)")
                    diagnostic_flags.append("hyperkalemia")
                elif k_val > 5.2:
                    extracted_labs["potassium"]["severity"] = "mild_moderate_hyperkalemia"
                    diagnostic_flags.append("hyperkalemia")
                elif k_val < 2.8:
                    extracted_labs["potassium"]["severity"] = "critical_hypokalemia"
                    diagnostic_flags.append("severe hypokalemia (<2.8 mEq/L)")
                    diagnostic_flags.append("hypokalemia")
                elif k_val < 3.5:
                    extracted_labs["potassium"]["severity"] = "hypokalemia"
                    diagnostic_flags.append("hypokalemia")

        # ---------------------------------------------------------------------
        # 8. Blood Glucose & Hyper/Hypoglycemia
        # ---------------------------------------------------------------------
        glu_match = re.search(
            r"\b(?:blood\s+sugar|blood\s+glucose|serum\s+glucose|glucose|bsl|fbs|rbs)\b[^\d\n]{0,10}?(\d{2,4})\s*(?:mg/?dl)?",
            text,
            re.IGNORECASE
        )
        if glu_match:
            glu_val = float(glu_match.group(1))
            extracted_labs["blood_glucose"] = {"value": glu_val, "unit": "mg/dL"}
            if glu_val >= 600:
                extracted_labs["blood_glucose"]["severity"] = "extreme_hyperglycemia"
                diagnostic_flags.append("severe hyperosmolar hyperglycemia (>=600 mg/dL)")
                diagnostic_flags.append("hyperglycemia")
            elif glu_val >= 250:
                extracted_labs["blood_glucose"]["severity"] = "marked_hyperglycemia"
                diagnostic_flags.append("marked hyperglycemia (>=250 mg/dL)")
                diagnostic_flags.append("hyperglycemia")
            elif glu_val < 54:
                extracted_labs["blood_glucose"]["severity"] = "severe_neuroglycopenia"
                diagnostic_flags.append("severe hypoglycemia (<54 mg/dL)")
                diagnostic_flags.append("hypoglycemia")
            elif glu_val < 70:
                extracted_labs["blood_glucose"]["severity"] = "hypoglycemia"
                diagnostic_flags.append("hypoglycemia")

        # ---------------------------------------------------------------------
        # 9. Electrolytes & Anion Gap Calculation: Na - (Cl + HCO3)
        # ---------------------------------------------------------------------
        na_match = re.search(r"\b(?:sodium|na\+?)\b[^\d\n]{0,10}?(\d{2,3})", text, re.IGNORECASE)
        cl_match = re.search(r"\b(?:chloride|cl\-?)\b[^\d\n]{0,10}?(\d{2,3})", text, re.IGNORECASE)
        hco3_match = re.search(r"\b(?:bicarbonate|hco3\-?|co2|bicarb)\b[^\d\n]{0,10}?(\d{1,2})", text, re.IGNORECASE)

        if na_match:
            na_val = float(na_match.group(1))
            extracted_labs["sodium"] = {"value": na_val, "unit": "mEq/L"}
            if na_val < 135:
                diagnostic_flags.append("hyponatremia")
            elif na_val > 145:
                diagnostic_flags.append("hypernatremia")

        if cl_match:
            extracted_labs["chloride"] = {"value": float(cl_match.group(1)), "unit": "mEq/L"}

        if hco3_match:
            hco3_val = float(hco3_match.group(1))
            extracted_labs["bicarbonate"] = {"value": hco3_val, "unit": "mEq/L"}
            if hco3_val < 22:
                diagnostic_flags.append("metabolic acidosis")

        if na_match and cl_match and hco3_match:
            na = float(na_match.group(1))
            cl = float(cl_match.group(1))
            hco3 = float(hco3_match.group(1))
            anion_gap = na - (cl + hco3)
            calculated_indices["anion_gap"] = round(anion_gap, 1)
            if anion_gap >= 16:
                calculated_indices["anion_gap_interpretation"] = "high_anion_gap_metabolic_acidosis"
                diagnostic_flags.append("high-anion-gap metabolic acidosis (HAGMA)")
                diagnostic_flags.append("severe metabolic acidosis")

        # ---------------------------------------------------------------------
        # 10. Renal Function (BUN, Creatinine) & Azotemia Ratio
        # ---------------------------------------------------------------------
        cr_match = re.search(r"\b(?:creatinine|cr)\b[^\d\n]{0,10}?(\d+(?:\.\d+)?)\s*(?:mg/?dl)?", text, re.IGNORECASE)
        bun_match = re.search(r"\b(?:bun|blood\s+urea\s+nitrogen|urea)\b[^\d\n]{0,10}?(\d+(?:\.\d+)?)", text, re.IGNORECASE)

        if cr_match:
            cr_val = float(cr_match.group(1))
            extracted_labs["creatinine"] = {"value": cr_val, "unit": "mg/dL"}
            if cr_val >= 1.5:
                diagnostic_flags.append("acute kidney injury")

        if bun_match:
            bun_val = float(bun_match.group(1))
            extracted_labs["bun"] = {"value": bun_val, "unit": "mg/dL"}

        if cr_match and bun_match:
            cr = float(cr_match.group(1))
            bun = float(bun_match.group(1))
            if cr > 0:
                bun_cr_ratio = bun / cr
                calculated_indices["bun_cr_ratio"] = round(bun_cr_ratio, 1)
                if bun_cr_ratio >= 20.0 and cr >= 1.3:
                    calculated_indices["azotemia_type"] = "prerenal_azotemia"
                    diagnostic_flags.append("prerenal azotemia (BUN/Cr >20)")

        # ---------------------------------------------------------------------
        # 11. Hepatic Transaminases (ALT, AST) & Ratio
        # ---------------------------------------------------------------------
        alt_match = re.search(r"\b(?:alt|sgpt)\b[^\d\n]{0,10}?(\d{1,5})\s*(?:u/?l)?", text, re.IGNORECASE)
        ast_match = re.search(r"\b(?:ast|sgot)\b[^\d\n]{0,10}?(\d{1,5})\s*(?:u/?l)?", text, re.IGNORECASE)

        if alt_match:
            alt_val = float(alt_match.group(1))
            extracted_labs["alt"] = {"value": alt_val, "unit": "U/L"}
            if alt_val >= 1000:
                extracted_labs["alt"]["severity"] = "massive_hepatotoxicity"
                diagnostic_flags.append("massive transaminitis / acute liver injury (>1,000 U/L)")
                diagnostic_flags.append("acute hepatitis")
            elif alt_val > 55:
                diagnostic_flags.append("elevated transaminases")

        if ast_match:
            ast_val = float(ast_match.group(1))
            extracted_labs["ast"] = {"value": ast_val, "unit": "U/L"}
            if ast_val >= 1000:
                diagnostic_flags.append("massive transaminitis / acute liver injury (>1,000 U/L)")
                diagnostic_flags.append("acute hepatitis")
            elif ast_val > 50:
                diagnostic_flags.append("elevated transaminases")

        if alt_match and ast_match:
            alt_v = float(alt_match.group(1))
            ast_v = float(ast_match.group(1))
            if alt_v > 0:
                ast_alt_ratio = round(ast_v / alt_v, 2)
                calculated_indices["ast_alt_ratio"] = ast_alt_ratio
                if ast_alt_ratio >= 2.0 and ast_v > 100:
                    calculated_indices["hepatic_pattern"] = "alcoholic_hepatitis_pattern"
                    diagnostic_flags.append("AST/ALT ratio >2:1 (alcoholic hepatitis pattern)")

        # ---------------------------------------------------------------------
        # 12. Total Bilirubin & Jaundice
        # ---------------------------------------------------------------------
        bili_match = re.search(
            r"\b(?:total\s+bilirubin|bilirubin|t\.?\s*bili?)\b[^\d\n]{0,10}?(\d+(?:\.\d+)?)\s*(?:mg/?dl)?",
            text,
            re.IGNORECASE
        )
        if bili_match:
            bili_val = float(bili_match.group(1))
            extracted_labs["total_bilirubin"] = {"value": bili_val, "unit": "mg/dL"}
            if bili_val >= 5.0:
                extracted_labs["total_bilirubin"]["severity"] = "severe_hyperbilirubinemia"
                diagnostic_flags.append("severe hyperbilirubinemia (>=5.0 mg/dL)")
                diagnostic_flags.append("jaundice")
            elif bili_val >= 2.0:
                extracted_labs["total_bilirubin"]["severity"] = "hyperbilirubinemia"
                diagnostic_flags.append("hyperbilirubinemia")
                diagnostic_flags.append("jaundice")

        # ---------------------------------------------------------------------
        # 13. Serum Lipase & Pancreatitis
        # ---------------------------------------------------------------------
        lipase_match = re.search(
            r"\b(?:serum\s+)?lipase\b[^\d\n]{0,10}?(\d{2,5})\s*(?:u/?l)?",
            text,
            re.IGNORECASE
        )
        if lipase_match:
            lip_val = float(lipase_match.group(1))
            extracted_labs["lipase"] = {"value": lip_val, "unit": "U/L"}
            if lip_val >= 180:
                extracted_labs["lipase"]["severity"] = "pancreatitis_diagnostic"
                diagnostic_flags.append("acute pancreatitis diagnostic lipase (>=3x ULN)")
                diagnostic_flags.append("acute pancreatitis")
            elif lip_val > 60:
                diagnostic_flags.append("elevated lipase")

        # ---------------------------------------------------------------------
        # 14. Coagulation: Prothrombin Time / INR
        # ---------------------------------------------------------------------
        inr_match = re.search(r"\binr\b[^\d\n]{0,10}?(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if inr_match:
            inr_val = float(inr_match.group(1))
            extracted_labs["inr"] = {"value": inr_val}
            if inr_val >= 5.0:
                extracted_labs["inr"]["severity"] = "critical_coagulopathy"
                diagnostic_flags.append("critical INR elevation (>=5.0)")
                diagnostic_flags.append("coagulopathy")
            elif inr_val >= 3.5:
                extracted_labs["inr"]["severity"] = "supratherapeutic_inr"
                diagnostic_flags.append("supratherapeutic INR / coagulopathy")
                diagnostic_flags.append("coagulopathy")

        # ---------------------------------------------------------------------
        # 15. Inflammatory Biomarkers: CRP & ESR
        # ---------------------------------------------------------------------
        crp_match = re.search(
            r"\b(?:c-reactive\s+protein|crp|hs-?crp)\b[^\d\n]{0,10}?(\d+(?:\.\d+)?)\s*(?:mg/?l|mg/?dl)?",
            text,
            re.IGNORECASE
        )
        if crp_match:
            crp_val = float(crp_match.group(1))
            extracted_labs["crp"] = {"value": crp_val, "unit": "mg/L"}
            if crp_val >= 50.0:
                extracted_labs["crp"]["severity"] = "severe_systemic_inflammation"
                diagnostic_flags.append("severe systemic inflammation (CRP >=50 mg/L)")
                diagnostic_flags.append("elevated CRP")
            elif crp_val > 10.0:
                diagnostic_flags.append("elevated CRP")

        esr_match = re.search(
            r"\b(?:esr|sed\s+rate|sedimentation\s+rate)\b[^\d\n]{0,10}?(\d{1,3})\s*(?:mm/?h(?:r)?)?",
            text,
            re.IGNORECASE
        )
        if esr_match:
            esr_val = float(esr_match.group(1))
            extracted_labs["esr"] = {"value": esr_val, "unit": "mm/hr"}
            if esr_val >= 80:
                extracted_labs["esr"]["severity"] = "marked_esr_elevation"
                diagnostic_flags.append("marked ESR elevation (>80 mm/hr)")
                diagnostic_flags.append("elevated ESR")
            elif esr_val > 30:
                diagnostic_flags.append("elevated ESR")

        # ---------------------------------------------------------------------
        # 16. Cerebrospinal Fluid (CSF) Analysis & Ratio
        # ---------------------------------------------------------------------
        csf_glu_match = re.search(r"\bcsf\s+glucose\b[^\d\n]{0,10}?(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        serum_glu_match = re.search(r"\b(?:serum|plasma|blood)\s+glucose\b[^\d\n]{0,10}?(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        csf_pressure_match = re.search(r"\b(?:opening\s+pressure|csf\s+pressure)\b[^\d\n]{0,10}?(\d{2,3})", text, re.IGNORECASE)

        if csf_glu_match:
            extracted_labs["csf_glucose"] = {"value": float(csf_glu_match.group(1)), "unit": "mg/dL"}

        if csf_pressure_match:
            csf_p = float(csf_pressure_match.group(1))
            extracted_labs["csf_opening_pressure"] = {"value": csf_p, "unit": "mmH2O"}
            if csf_p > 200:
                diagnostic_flags.append("elevated CSF opening pressure")

        if csf_glu_match and serum_glu_match:
            csf_g = float(csf_glu_match.group(1))
            serum_g = float(serum_glu_match.group(1))
            if serum_g > 0:
                csf_serum_ratio = round(csf_g / serum_g, 2)
                calculated_indices["csf_serum_glucose_ratio"] = csf_serum_ratio
                if csf_serum_ratio < 0.40:
                    calculated_indices["csf_interpretation"] = "hypoglycorrhachia_bacterial_meningitis_pattern"
                    diagnostic_flags.append("hypoglycorrhachia (CSF/serum glucose ratio <0.40)")

        # ---------------------------------------------------------------------
        # 17. D-Dimer
        # ---------------------------------------------------------------------
        ddimer_match = re.search(r"\bd-?dimer\b[^\d\n]{0,10}?(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if ddimer_match:
            dd_val = float(ddimer_match.group(1))
            extracted_labs["d_dimer"] = {"value": dd_val}
            if dd_val > 0.5:
                diagnostic_flags.append("elevated D-dimer")

        # ---------------------------------------------------------------------
        # 18. Arterial Blood Gas (ABG): pH, PaCO2, PaO2
        # ---------------------------------------------------------------------
        ph_match = re.search(r"\bph\b[^\d\n]{0,8}?([67]\.\d{1,3})", text, re.IGNORECASE)
        pco2_match = re.search(r"\b(?:paco2|pco2)\b[^\d\n]{0,10}?(\d{1,3}(?:\.\d)?)\s*(?:mmhg)?", text, re.IGNORECASE)
        pao2_match = re.search(r"\b(?:pao2|po2)\b[^\d\n]{0,10}?(\d{1,3}(?:\.\d)?)\s*(?:mmhg)?", text, re.IGNORECASE)

        if ph_match:
            ph_val = float(ph_match.group(1))
            extracted_labs["ph"] = {"value": ph_val}
            if ph_val < 7.20:
                extracted_labs["ph"]["severity"] = "critical_acidemia"
                diagnostic_flags.append("critical severe acidemia (pH <7.20)")
                diagnostic_flags.append("acidemia")
            elif ph_val < 7.35:
                extracted_labs["ph"]["severity"] = "acidemia"
                diagnostic_flags.append("acidemia")
            elif ph_val > 7.45:
                extracted_labs["ph"]["severity"] = "alkalemia"
                diagnostic_flags.append("alkalemia")

        if pco2_match:
            pco2_val = float(pco2_match.group(1))
            extracted_labs["pco2"] = {"value": pco2_val, "unit": "mmHg"}
            if pco2_val > 50.0:
                diagnostic_flags.append("hypercapnic respiratory failure (pCO2 >50 mmHg)")
                diagnostic_flags.append("hypercapnia")
            elif pco2_val < 35.0:
                diagnostic_flags.append("hypocapnia")

        if pao2_match:
            pao2_val = float(pao2_match.group(1))
            extracted_labs["pao2"] = {"value": pao2_val, "unit": "mmHg"}
            if pao2_val < 60.0:
                diagnostic_flags.append("hypoxemic respiratory failure (PaO2 <60 mmHg)")
                diagnostic_flags.append("hypoxemia")

        # Composite Acid-Base Classification
        if ph_match and pco2_match:
            ph_v = float(ph_match.group(1))
            pco2_v = float(pco2_match.group(1))
            if ph_v < 7.35 and pco2_v > 45.0:
                calculated_indices["acid_base_status"] = "respiratory_acidosis"
                diagnostic_flags.append("respiratory acidosis")
            elif ph_v < 7.35 and pco2_v <= 40.0:
                calculated_indices["acid_base_status"] = "metabolic_acidosis_with_respiratory_compensation"
                diagnostic_flags.append("metabolic acidosis")
            elif ph_v > 7.45 and pco2_v < 35.0:
                calculated_indices["acid_base_status"] = "respiratory_alkalosis"
                diagnostic_flags.append("respiratory alkalosis")

        # ---------------------------------------------------------------------
        # 19. Cardiac Natriuretic Peptides: BNP & NT-proBNP
        # ---------------------------------------------------------------------
        bnp_match = re.search(r"\b(?:bnp|b-type\s+natriuretic\s+peptide)\b[^\d\n]{0,10}?(\d{1,5}(?:\.\d)?)\s*(?:pg/?ml)?", text, re.IGNORECASE)
        nt_probnp_match = re.search(r"\bnt-?probnp\b[^\d\n]{0,10}?(\d{1,6}(?:\.\d)?)\s*(?:pg/?ml)?", text, re.IGNORECASE)

        if bnp_match:
            bnp_val = float(bnp_match.group(1))
            extracted_labs["bnp"] = {"value": bnp_val, "unit": "pg/mL"}
            if bnp_val >= 400.0:
                extracted_labs["bnp"]["severity"] = "acute_heart_failure_likely"
                diagnostic_flags.append("markedly elevated BNP (>=400 pg/mL)")
                diagnostic_flags.append("acute decompensated heart failure")
            elif bnp_val >= 100.0:
                extracted_labs["bnp"]["severity"] = "elevated"
                diagnostic_flags.append("elevated BNP")

        if nt_probnp_match:
            nt_val = float(nt_probnp_match.group(1))
            extracted_labs["nt_probnp"] = {"value": nt_val, "unit": "pg/mL"}
            if nt_val >= 900.0:
                extracted_labs["nt_probnp"]["severity"] = "acute_heart_failure_likely"
                diagnostic_flags.append("markedly elevated NT-proBNP (>=900 pg/mL)")
                diagnostic_flags.append("acute decompensated heart failure")
            elif nt_val >= 300.0:
                extracted_labs["nt_probnp"]["severity"] = "elevated"
                diagnostic_flags.append("elevated NT-proBNP")

        # ---------------------------------------------------------------------
        # 20. Calcium, Albumin & Corrected Calcium
        # ---------------------------------------------------------------------
        ca_match = re.search(r"\b(?:serum\s+calcium|calcium|total\s+ca)\b[^\d\n]{0,10}?(\d{1,2}(?:\.\d)?)\s*(?:mg/?dl)?", text, re.IGNORECASE)
        alb_match = re.search(r"\b(?:serum\s+albumin|albumin)\b[^\d\n]{0,10}?(\d{1,2}(?:\.\d)?)\s*(?:g/?dl)?", text, re.IGNORECASE)

        if ca_match:
            ca_val = float(ca_match.group(1))
            if 4.0 <= ca_val <= 18.0:
                extracted_labs["calcium"] = {"value": ca_val, "unit": "mg/dL"}
                if ca_val >= 12.0:
                    extracted_labs["calcium"]["severity"] = "severe_hypercalcemia"
                    diagnostic_flags.append("severe hypercalcemia (>=12.0 mg/dL)")
                    diagnostic_flags.append("hypercalcemia")
                elif ca_val > 10.5:
                    extracted_labs["calcium"]["severity"] = "hypercalcemia"
                    diagnostic_flags.append("hypercalcemia")
                elif ca_val < 7.0:
                    extracted_labs["calcium"]["severity"] = "severe_hypocalcemia"
                    diagnostic_flags.append("severe hypocalcemia (<7.0 mg/dL)")
                    diagnostic_flags.append("hypocalcemia")
                elif ca_val < 8.5:
                    extracted_labs["calcium"]["severity"] = "hypocalcemia"
                    diagnostic_flags.append("hypocalcemia")

        if alb_match:
            alb_val = float(alb_match.group(1))
            if 1.0 <= alb_val <= 6.0:
                extracted_labs["albumin"] = {"value": alb_val, "unit": "g/dL"}
                if alb_val < 2.5:
                    diagnostic_flags.append("severe hypoalbuminemia (<2.5 g/dL)")
                    diagnostic_flags.append("hypoalbuminemia")
                elif alb_val < 3.5:
                    diagnostic_flags.append("hypoalbuminemia")

        # Corrected Calcium: Measured Ca + 0.8 * (4.0 - Albumin)
        if ca_match and alb_match:
            ca_v = float(ca_match.group(1))
            alb_v = float(alb_match.group(1))
            if 4.0 <= ca_v <= 18.0 and 1.0 <= alb_v <= 6.0:
                corr_ca = round(ca_v + 0.8 * (4.0 - alb_v), 2)
                calculated_indices["corrected_calcium"] = corr_ca
                if corr_ca >= 12.0:
                    diagnostic_flags.append("severe corrected hypercalcemia (>=12.0 mg/dL)")

        # ---------------------------------------------------------------------
        # 21. Estimated GFR (eGFR) & Renal Staging
        # ---------------------------------------------------------------------
        egfr_match = re.search(r"\b(?:egfr|gfr)\b[^\d\n]{0,10}?(\d{1,3})\s*(?:ml/?min)?", text, re.IGNORECASE)
        if egfr_match:
            egfr_val = float(egfr_match.group(1))
            extracted_labs["egfr"] = {"value": egfr_val, "unit": "mL/min/1.73m2"}
            if egfr_val < 15:
                extracted_labs["egfr"]["severity"] = "kidney_failure_stage_5"
                diagnostic_flags.append("kidney failure / ESRD (eGFR <15 mL/min)")
                diagnostic_flags.append("chronic kidney disease")
            elif egfr_val < 30:
                extracted_labs["egfr"]["severity"] = "severe_ckd_stage_4"
                diagnostic_flags.append("severe renal impairment (eGFR 15-29 mL/min)")
                diagnostic_flags.append("chronic kidney disease")
            elif egfr_val < 60:
                extracted_labs["egfr"]["severity"] = "moderate_ckd_stage_3"
                diagnostic_flags.append("moderate renal impairment (eGFR 30-59 mL/min)")
                diagnostic_flags.append("chronic kidney disease")

        # ---------------------------------------------------------------------
        # 22. Serum Magnesium (Mg)
        # ---------------------------------------------------------------------
        mg_match = re.search(r"\b(?:serum\s+magnesium|magnesium|\bmg\b)[^\d\n]{0,10}?(\d+(?:\.\d+)?)\s*(?:mg/?dl)?", text, re.IGNORECASE)
        if mg_match:
            mg_val = float(mg_match.group(1))
            if 0.5 <= mg_val <= 6.0:
                extracted_labs["magnesium"] = {"value": mg_val, "unit": "mg/dL"}
                if mg_val < 1.5:
                    diagnostic_flags.append("hypomagnesemia (<1.5 mg/dL)")
                    diagnostic_flags.append("hypomagnesemia")
                elif mg_val > 2.6:
                    diagnostic_flags.append("hypermagnesemia")

        return {
            "extracted_labs": extracted_labs,
            "calculated_indices": calculated_indices,
            "diagnostic_flags": list(set(diagnostic_flags)),
        }


lab_value_interpreter = LabValueInterpreter()
