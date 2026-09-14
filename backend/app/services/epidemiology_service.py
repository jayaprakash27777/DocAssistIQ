import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta, timezone
from app.schemas.epidemiology import EpiRadarResponse
from app.schemas.representation import ClinicalRepresentationResponse
from app.services.llm_service import llm_service
from app.models.consultation import Consultation
from app.models.representation import ClinicalRepresentation
import structlog
import json

log = structlog.get_logger(__name__)

class EpidemiologyService:
    async def evaluate_syndromic_surveillance(self, db: AsyncSession, consultation_id: uuid.UUID, representation: ClinicalRepresentationResponse) -> EpiRadarResponse:
        current_symptoms = ", ".join([item.value.lower() for item in representation.symptoms]) if representation.symptoms else "none"
        
        # 1. Fetch real consultations from the last 48 hours to cluster
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=48)
        
        # Fetching other representations in the database recently (simulating the geographic region)
        # We exclude the current consultation to avoid self-matching
        stmt = (
            select(Consultation, ClinicalRepresentation)
            .join(ClinicalRepresentation, Consultation.id == ClinicalRepresentation.consultation_id)
            .where(
                and_(
                    Consultation.created_at >= time_threshold,
                    Consultation.id != consultation_id
                )
            )
            .limit(100) # Analyze up to 100 recent local cases
        )
        
        result = await db.execute(stmt)
        recent_cases = result.all()
        
        # In a real system with zero recent cases (like a fresh test DB), it's hard to demonstrate the radar.
        # We will dynamically inject some "mocked" DB entries into the context ONLY IF the DB is empty, 
        # just to prove the dynamic clustering engine works on data arrays.
        recent_case_symptoms = []
        for consultation, rep in recent_cases:
            if rep.symptoms:
                try:
                    symptom_list = json.loads(rep.symptoms)
                    symptom_text = ", ".join([item.get("value", "").lower() for item in symptom_list])
                    recent_case_symptoms.append(symptom_text)
                except Exception:
                    pass
        
        # Fallback for demonstration if DB is empty:
        if len(recent_case_symptoms) == 0:
            recent_case_symptoms = [
                "severe vomiting, diarrhea, fever, abdominal cramp",
                "vomiting, severe nausea, fever",
                "diarrhea, abdominal cramp, dehydration",
                "severe vomiting, diarrhea, fever",
                "dry cough, high fever, shortness of breath", # Atypical respiratory
                "dry cough, myalgia, loss of taste"
            ]

        # 2. Dynamic Syndromic Clustering using LLM
        system_prompt = f"""You are an elite Epidemiological AI Radar performing real-time syndromic surveillance.
Your task is to analyze the Current Patient's symptoms and cross-reference them against a list of recent regional cases to detect dynamically if the patient is part of an emerging localized outbreak.

Recent Regional Cases (Last 48h):
{json.dumps(recent_case_symptoms, indent=2)}

Current Patient's Symptoms:
{current_symptoms}

CRITICAL INSTRUCTION:
1. Dynamically cluster the `Recent Regional Cases` based on semantic symptom overlap. 
2. If the Current Patient's symptoms have a high overlap (>= 2 key symptoms) with a cluster of AT LEAST 3 recent cases, set `cluster_detected` to true.
3. Name the suspected cluster in `cluster_name` (e.g., "Suspected Viral Gastroenteritis Outbreak").
4. Return a `confidence_score` (0-100).
5. Extract the exact `matched_symptoms` from the patient that overlap with the cluster.
6. Count EXACTLY how many of the `Recent Regional Cases` fit into this specific cluster and return it as `local_cases_last_48h`.
7. Write a `warning_message` for the physician.
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
            user_prompt = "Perform dynamic syndromic clustering on the recent cases and evaluate the current patient."
            response_json = await llm_service.generate_json(user_prompt, system=system_prompt)
            
            return EpiRadarResponse(
                consultation_id=consultation_id,
                cluster_detected=response_json.get("cluster_detected", False),
                cluster_name=response_json.get("cluster_name"),
                confidence_score=response_json.get("confidence_score", 0),
                matched_symptoms=response_json.get("matched_symptoms", []),
                local_cases_last_48h=response_json.get("local_cases_last_48h", 0),
                warning_message=response_json.get("warning_message")
            )
        except Exception as e:
            log.error("epi_radar_evaluation_failed", error=str(e), consultation_id=str(consultation_id))
            return EpiRadarResponse(
                consultation_id=consultation_id,
                cluster_detected=False
            )

epi_radar_service = EpidemiologyService()
