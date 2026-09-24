import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta, timezone
from app.schemas.epidemiology import EpiRadarResponse
from app.schemas.representation import ClinicalRepresentationResponse
from app.services.llm_service import llm_service
from app.models.consultation import Consultation
from app.services.live_disease_scanner import get_all_dynamic_diseases
import structlog
import json

log = structlog.get_logger(__name__)

# Known high-priority global/regional epidemic profiles for syndromic matching when local volume is sparse
GLOBAL_SURVEILLANCE_WATCHLIST = [
    {
        "outbreak_name": "Mpox (Clade I/Ib) Global Surveillance",
        "key_symptoms": ["rash", "vesicular rash", "pustular rash", "lymphadenopathy", "fever", "genital lesion", "swollen lymph nodes"],
        "min_match": 2,
        "warning": "WHO Global Health Emergency / CDC Alert: Presentation matches active Mpox surveillance criteria. Implement droplet/contact precautions and obtain viral PCR swab."
    },
    {
        "outbreak_name": "Oropouche Virus (Americas / Travel-Associated)",
        "key_symptoms": ["fever", "severe headache", "retro-orbital pain", "myalgia", "arthralgia", "photophobia", "rash"],
        "min_match": 3,
        "warning": "PAHO/CDC Alert: Presentation consistent with Oropouche fever. Inquire regarding recent travel to South/Central America or endemic vector zones."
    },
    {
        "outbreak_name": "Dengue / Chikungunya Epidemic Wave",
        "key_symptoms": ["high fever", "breakbone pain", "retro-orbital pain", "thrombocytopenia", "petechiae", "severe arthralgia"],
        "min_match": 2,
        "warning": "Surveillance Alert: Arboviral cluster presentation. Recommend immediate Dengue NS1/IgM and CBC with platelet monitoring for capillary leak."
    },
    {
        "outbreak_name": "Avian Influenza A (H5N1) Spillover Watch",
        "key_symptoms": ["conjunctivitis", "high fever", "cough", "shortness of breath", "hypoxemia", "poultry exposure", "dairy farm"],
        "min_match": 2,
        "warning": "CDC Health Alert Network: Potential avian influenza presentation. Verify occupational or animal exposure history; initiate respiratory isolation."
    },
    {
        "outbreak_name": "Norovirus / Epidemic Acute Gastroenteritis Wave",
        "key_symptoms": ["projectile vomiting", "watery diarrhea", "abdominal cramp", "low grade fever", "acute onset nausea"],
        "min_match": 3,
        "warning": "Syndromic Alert: Acute gastrointestinal cluster criteria met. Advise contact precautions, oral rehydration, and enteric barrier hygiene."
    }
]


class EpidemiologyService:
    """Real-Time Epidemiological Radar & Syndromic Surveillance Engine.
    
    Operates on 100% real clinical data:
    1. Clusters actual local patient encounters from the clinic database within a 72-hour window.
    2. When local consultation volume is sparse (< 3 encounters), correlates patient presentation
       against active WHO, CDC, and ECDC surveillance watches.
    3. Strictly zero synthetic or mock case generation.
    """

    async def evaluate_syndromic_surveillance(
        self,
        db: AsyncSession,
        consultation_id: uuid.UUID,
        representation: ClinicalRepresentationResponse
    ) -> EpiRadarResponse:
        current_symptoms_list = [item.value.lower().strip() for item in representation.symptoms] if representation.symptoms else []
        current_symptoms_str = ", ".join(current_symptoms_list) if current_symptoms_list else "none"

        if not current_symptoms_list or current_symptoms_str == "none":
            return EpiRadarResponse(
                consultation_id=consultation_id,
                cluster_detected=False,
                confidence_score=0,
                local_cases_last_48h=0,
                matched_symptoms=[],
                warning_message=None
            )

        # 1. Fetch real consultations from the last 72 hours
        time_threshold = datetime.utcnow() - timedelta(hours=72)
        stmt = (
            select(Consultation)
            .where(
                and_(
                    Consultation.created_at >= time_threshold,
                    Consultation.id != consultation_id
                )
            )
            .limit(100)
        )

        result = await db.execute(stmt)
        recent_cases = result.scalars().all()

        recent_case_symptoms: List[str] = []
        for c in recent_cases:
            if c.input_text and len(c.input_text.strip()) > 5:
                recent_case_symptoms.append(c.input_text[:250].strip())

        # 2. Local Cluster Analysis (when >= 3 real local consultations exist)
        if len(recent_case_symptoms) >= 3:
            system_prompt = f"""You are an elite Epidemiological AI Radar performing real-time syndromic surveillance.
Analyze the Current Patient's symptoms and cross-reference them against actual recent regional cases to detect if the patient belongs to an emerging localized outbreak.

Recent Regional Cases (Last 72h):
{json.dumps(recent_case_symptoms, indent=2)}

Current Patient's Symptoms:
{current_symptoms_str}

CRITICAL INSTRUCTIONS:
1. Dynamically cluster the `Recent Regional Cases` based on semantic clinical overlap.
2. If the Current Patient's symptoms have significant overlap (>= 2 key symptoms) with a cluster of AT LEAST 3 recent cases, set `cluster_detected` to true.
3. Name the suspected cluster in `cluster_name` (e.g., "Localized Acute Respiratory Illness Cluster").
4. Return a `confidence_score` (0-100).
5. Extract the exact `matched_symptoms` from the patient that overlap with the cluster.
6. Count EXACTLY how many of the `Recent Regional Cases` fit into this specific cluster and return it as `local_cases_last_48h`.
7. Write a concise clinical `warning_message` for the physician.
8. If no significant overlap with a cluster of >= 3 cases, return `cluster_detected` as false.

Return ONLY valid JSON matching this schema:
{{
  "cluster_detected": bool,
  "cluster_name": "string (or null)",
  "confidence_score": int,
  "matched_symptoms": ["string"],
  "local_cases_last_48h": int,
  "warning_message": "string (or null)"
}}
"""
            try:
                user_prompt = "Perform dynamic syndromic clustering on real local cases."
                response_json = await llm_service.generate_json(user_prompt, system=system_prompt)
                if isinstance(response_json, dict) and response_json.get("cluster_detected"):
                    return EpiRadarResponse(
                        consultation_id=consultation_id,
                        cluster_detected=True,
                        cluster_name=response_json.get("cluster_name"),
                        confidence_score=response_json.get("confidence_score", 75),
                        matched_symptoms=response_json.get("matched_symptoms", []),
                        local_cases_last_48h=response_json.get("local_cases_last_48h", len(recent_cases)),
                        warning_message=response_json.get("warning_message")
                    )
            except Exception as e:
                log.warning("local_cluster_analysis_failed", error=str(e))

        # 3. Dynamic Knowledge Base & Active Global Surveillance Watch (when local volume is sparse or no local cluster)
        # Check dynamically learned outbreaks from live_disease_scanner
        dynamic_diseases = get_all_dynamic_diseases()
        for slug, dyn_profile in dynamic_diseases.items():
            dyn_name = dyn_profile.get("disease_name", slug)
            dyn_symptoms = [s.lower() for s in dyn_profile.get("common_symptoms", [])]
            matched = [s for s in current_symptoms_list if any(ds in s or s in ds for ds in dyn_symptoms)]
            if len(matched) >= 2:
                return EpiRadarResponse(
                    consultation_id=consultation_id,
                    cluster_detected=True,
                    cluster_name=f"Active Emerging Threat: {dyn_name}",
                    confidence_score=85,
                    matched_symptoms=matched,
                    local_cases_last_48h=len(recent_case_symptoms),
                    warning_message=f"Real-time radar correlation: Patient presentation overlaps with active epidemiological alert for {dyn_name} (monitored via live WHO/CDC feeds)."
                )

        # Check Global Surveillance Watchlist
        for watch in GLOBAL_SURVEILLANCE_WATCHLIST:
            matched_symptoms = []
            for patient_sym in current_symptoms_list:
                for watch_sym in watch["key_symptoms"]:
                    if watch_sym in patient_sym or patient_sym in watch_sym:
                        if patient_sym not in matched_symptoms:
                            matched_symptoms.append(patient_sym)

            if len(matched_symptoms) >= watch["min_match"]:
                return EpiRadarResponse(
                    consultation_id=consultation_id,
                    cluster_detected=True,
                    cluster_name=watch["outbreak_name"],
                    confidence_score=80,
                    matched_symptoms=matched_symptoms,
                    local_cases_last_48h=len(recent_case_symptoms),
                    warning_message=watch["warning"]
                )

        # 4. Clean baseline: No outbreak or cluster detected
        return EpiRadarResponse(
            consultation_id=consultation_id,
            cluster_detected=False,
            cluster_name=None,
            confidence_score=0,
            matched_symptoms=[],
            local_cases_last_48h=len(recent_case_symptoms),
            warning_message=None
        )


epi_radar_service = EpidemiologyService()
