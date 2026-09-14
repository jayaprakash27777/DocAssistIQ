import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.early_warning import EarlyWarningResponse
from app.schemas.representation import ClinicalRepresentationResponse
from app.services.llm_service import llm_service
import structlog
import json
import re

log = structlog.get_logger(__name__)

class EarlyWarningService:
    def parse_vitals(self, vitals_list: list[str]) -> dict:
        parsed = {}
        vitals_text = " ".join(vitals_list).lower()
        
        # Regex extraction
        hr_match = re.search(r"(?:hr|heart rate|pulse)[^\d]*(\d{2,3})", vitals_text)
        if hr_match: parsed["hr"] = int(hr_match.group(1))
            
        rr_match = re.search(r"(?:rr|respiratory rate|respirations)[^\d]*(\d{1,2})", vitals_text)
        if rr_match: parsed["rr"] = int(rr_match.group(1))
            
        sys_match = re.search(r"(?:bp|blood pressure)[^\d]*(\d{2,3})/", vitals_text)
        if sys_match: parsed["sys_bp"] = int(sys_match.group(1))
            
        temp_match = re.search(r"(?:temp|temperature|t)[^\d]*(\d{2,3}\.?\d*)", vitals_text)
        if temp_match: 
            temp = float(temp_match.group(1))
            # Convert F to C if > 90
            parsed["temp"] = (temp - 32) * 5.0/9.0 if temp > 90 else temp
            
        spo2_match = re.search(r"(?:spo2|o2 sat|oxygen)[^\d]*(\d{2,3})", vitals_text)
        if spo2_match: parsed["spo2"] = int(spo2_match.group(1))
        
        # AVPU consciousness parsing
        if "unresponsive" in vitals_text: parsed["avpu"] = "U"
        elif "pain" in vitals_text and "response" in vitals_text: parsed["avpu"] = "P"
        elif "voice" in vitals_text or "verbal" in vitals_text: parsed["avpu"] = "V"
        elif "confused" in vitals_text: parsed["avpu"] = "C"
        else: parsed["avpu"] = "A" # Assume Alert if not specified
            
        return parsed

    def calculate_mews(self, v: dict) -> int:
        score = 0
        if "rr" in v:
            if v["rr"] <= 8 or v["rr"] >= 30: score += 3
            elif 21 <= v["rr"] <= 29: score += 2
            elif 9 <= v["rr"] <= 14: score += 1
        if "hr" in v:
            if v["hr"] <= 40 or v["hr"] >= 130: score += 3
            elif 111 <= v["hr"] <= 129: score += 2
            elif 41 <= v["hr"] <= 50 or 101 <= v["hr"] <= 110: score += 1
        if "sys_bp" in v:
            if v["sys_bp"] <= 70: score += 3
            elif 71 <= v["sys_bp"] <= 80: score += 2
            elif 81 <= v["sys_bp"] <= 100: score += 1
        if "temp" in v:
            if v["temp"] < 35: score += 2
            elif v["temp"] >= 38.5 or v["temp"] <= 35.9: score += 1
        return score

    def calculate_qsofa(self, v: dict) -> int:
        score = 0
        if "rr" in v and v["rr"] >= 22: score += 1
        if "sys_bp" in v and v["sys_bp"] <= 100: score += 1
        if v.get("avpu") in ["V", "P", "U", "C"]: score += 1
        return score
        
    def calculate_news2(self, v: dict) -> int:
        score = 0
        if "rr" in v:
            if v["rr"] <= 8 or v["rr"] >= 25: score += 3
            elif 21 <= v["rr"] <= 24: score += 2
            elif 9 <= v["rr"] <= 11: score += 1
        if "spo2" in v:
            if v["spo2"] <= 91: score += 3
            elif 92 <= v["spo2"] <= 93: score += 2
            elif 94 <= v["spo2"] <= 95: score += 1
        if "sys_bp" in v:
            if v["sys_bp"] <= 90 or v["sys_bp"] >= 220: score += 3
            elif 91 <= v["sys_bp"] <= 100: score += 2
            elif 101 <= v["sys_bp"] <= 110: score += 1
        if "hr" in v:
            if v["hr"] <= 40 or v["hr"] >= 131: score += 3
            elif 111 <= v["hr"] <= 130: score += 2
            elif 41 <= v["hr"] <= 50 or 91 <= v["hr"] <= 110: score += 1
        if "temp" in v:
            if v["temp"] <= 35.0: score += 3
            elif v["temp"] >= 39.1: score += 2
            elif 35.1 <= v["temp"] <= 36.0 or 38.1 <= v["temp"] <= 39.0: score += 1
        if v.get("avpu") in ["V", "P", "U", "C"]: score += 3
        return score

    def calculate_sirs(self, v: dict) -> int:
        score = 0
        if "temp" in v and (v["temp"] > 38.0 or v["temp"] < 36.0): score += 1
        if "hr" in v and v["hr"] > 90: score += 1
        if "rr" in v and v["rr"] > 20: score += 1
        # WBC normally required, but we use clinical proxy if unavailable
        return score

    async def evaluate_deterioration_risk(self, db: AsyncSession, consultation_id: uuid.UUID, representation: ClinicalRepresentationResponse) -> EarlyWarningResponse:
        vitals_list = [item.value for item in representation.vitals] if representation.vitals else []
        parsed_vitals = self.parse_vitals(vitals_list)
        
        mews = self.calculate_mews(parsed_vitals)
        qsofa = self.calculate_qsofa(parsed_vitals)
        news2 = self.calculate_news2(parsed_vitals)
        sirs = self.calculate_sirs(parsed_vitals)
        
        vitals = ", ".join(vitals_list) if vitals_list else "None reported"
        symptoms = ", ".join([item.value for item in representation.symptoms]) if representation.symptoms else "None reported"
        history = ", ".join([item.value for item in representation.history]) if representation.history else "None reported"
        
        system_prompt = f"""You are an elite Critical Care AI (Early Warning System).
Your task is to analyze the patient's clinical data and detect any early signs of severe clinical deterioration (e.g., Sepsis, Septic Shock, Cardiogenic Shock).

## Deterministic Scoring
I have already mathematically parsed the vitals and calculated the following clinical scores:
- NEWS2 (National Early Warning Score 2): {news2} (>= 5 is high risk, >= 7 is critical)
- MEWS (Modified Early Warning Score): {mews} (>= 4 is high risk)
- qSOFA (Quick SOFA): {qsofa} (>= 2 is high risk for sepsis)
- SIRS Criteria Met: {sirs}/4 (>= 2 is abnormal inflammatory response)

CRITICAL INSTRUCTIONS:
1. Output a probability percentage (0 to 100) of severe deterioration within the next 6-12 hours. Anchor this heavily on NEWS2 and SIRS!
2. If probability > 60% OR NEWS2 >= 5 OR MEWS >= 4 OR qSOFA >= 2 OR sirs >= 2, set `is_high_risk` to true.
3. Identify the `primary_warning_flag` (e.g., "Sepsis Risk", "Shock Risk", or "Stable").
4. List the exact `contributing_factors` from the patient's data.
5. Suggest `recommended_immediate_actions`.

Return ONLY valid JSON matching this schema:
{{
  "probability_percentage": int,
  "is_high_risk": bool,
  "primary_warning_flag": "string",
  "contributing_factors": ["string"],
  "recommended_immediate_actions": ["string"]
}}
"""

        user_prompt = f"Patient Context:\nVitals: {vitals}\nSymptoms: {symptoms}\nHistory: {history}\nParsed Vitals: {parsed_vitals}"

        try:
            response_json = await llm_service.generate_json(user_prompt, system=system_prompt)
            
            return EarlyWarningResponse(
                consultation_id=consultation_id,
                probability_percentage=response_json.get("probability_percentage", 0),
                is_high_risk=response_json.get("is_high_risk", False),
                primary_warning_flag=response_json.get("primary_warning_flag", "Stable"),
                contributing_factors=response_json.get("contributing_factors", []),
                recommended_immediate_actions=response_json.get("recommended_immediate_actions", []),
                mews_score=mews,
                qsofa_score=qsofa,
                news2_score=news2,
                sirs_score=sirs
            )
        except Exception as e:
            log.error("early_warning_evaluation_failed", error=str(e), consultation_id=str(consultation_id))
            return EarlyWarningResponse(
                consultation_id=consultation_id,
                probability_percentage=0,
                is_high_risk=False,
                primary_warning_flag="Error",
                contributing_factors=[],
                recommended_immediate_actions=[]
            )

early_warning_service = EarlyWarningService()
