import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinical import ClinicalFinding, ManualIntake
from app.schemas.representation import (
    ClinicalRepresentationResponse,
    PatientContext,
    Provenance,
    RepresentationItem,
)

async def build_clinical_representation(db: AsyncSession, consultation_id: uuid.UUID) -> ClinicalRepresentationResponse:
    # 1. Fetch Manual Intake
    intake_res = await db.execute(select(ManualIntake).where(ManualIntake.consultation_id == consultation_id))
    intake = intake_res.scalar_one_or_none()
    
    # 2. Fetch Clinical Findings
    findings_res = await db.execute(select(ClinicalFinding).where(ClinicalFinding.consultation_id == consultation_id))
    findings = findings_res.scalars().all()
    
    # Initialize output structure
    rep = ClinicalRepresentationResponse(  # type: ignore
        consultation_id=consultation_id,
        generated_at=datetime.now(timezone.utc),
        patient_context=PatientContext()
    )
    
    def add_item(target_list: List[RepresentationItem], value: str, concept: str | None, status: str | None, provenance: Provenance):
        if not value:
            return
        value = value.strip()
        if not value:
            return
            
        for item in target_list:
            if item.value.lower() == value.lower():
                # Avoid duplicate provenances from same source ID
                if not any(p.source_id == provenance.source_id for p in item.provenances):
                    item.provenances.append(provenance)
                return
                
        target_list.append(RepresentationItem(
            value=value,
            concept=concept,
            status=status,
            provenances=[provenance]
        ))

    # 3. Process Manual Intake
    if intake:
        prov = Provenance(
            source_type="manual_intake",
            source_id=str(intake.id),
            timestamp=intake.updated_at or intake.created_at,
            author_id=str(intake.doctor_id)
        )
        
        if intake.chief_complaint:
            add_item(rep.symptoms, intake.chief_complaint, "chief_complaint", "confirmed", prov)
        if intake.symptoms:
            for s in intake.symptoms.split(","):
                add_item(rep.symptoms, s, "symptom", "confirmed", prov)
        if intake.duration:
            add_item(rep.duration, intake.duration, "duration", "confirmed", prov)
        if intake.severity:
            add_item(rep.severity, intake.severity, "severity", "confirmed", prov)
        if intake.negations:
            for n in intake.negations.split(","):
                add_item(rep.negations, n, "negation", "negated", prov)
        if intake.past_medical_history:
            for h in intake.past_medical_history.split(","):
                add_item(rep.history, h, "history", "confirmed", prov)
        if intake.medications:
            for m in intake.medications.split(","):
                add_item(rep.medications, m, "medication", "confirmed", prov)
        if intake.allergies:
            for a in intake.allergies.split(","):
                add_item(rep.allergies, a, "allergy", "confirmed", prov)
        if intake.vitals:
            add_item(rep.vitals, intake.vitals, "vitals", "confirmed", prov)
        if intake.previous_investigations:
            add_item(rep.investigations, intake.previous_investigations, "investigation", "confirmed", prov)

    # 4. Process Clinical Findings
    for f in findings:
        prov = Provenance(
            source_type="clinical_finding",
            source_id=str(f.id),
            timestamp=f.updated_at or f.created_at,
            author_id=None
        )
        
        val = f.canonical_concept or f.value
        concept = f.concept or f.finding_type
        status = "negated" if f.negated else f.status
        
        if f.negated:
            add_item(rep.negations, val, concept, status, prov)  # type: ignore
        elif f.finding_type == "symptom" or concept == "symptom" or concept == "CONDITION" or f.finding_type == "diagnosis":
            add_item(rep.symptoms, val, concept, status, prov)  # type: ignore
        elif f.finding_type == "measurement" or concept == "vitals" or concept == "VITALS":
            add_item(rep.vitals, val, concept, status, prov)  # type: ignore
        elif concept == "medication" or concept == "MEDICATION":
            add_item(rep.medications, val, concept, status, prov)  # type: ignore
        elif concept == "allergy" or concept == "ALLERGY":
            add_item(rep.allergies, val, concept, status, prov)  # type: ignore
        elif concept in ("travel_history", "travel", "TRAVEL_HISTORY", "GEOGRAPHIC_EXPOSURE"):
            add_item(rep.travel_history, val, concept, status, prov)  # type: ignore
        elif f.temporality == "past" or concept == "history":
            add_item(rep.history, val, concept, status, prov)  # type: ignore
        else:
            add_item(rep.report_findings, val, concept, status, prov)  # type: ignore

    return rep
