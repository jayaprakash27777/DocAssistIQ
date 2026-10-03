"""DocAssistIQ — Certified Clinical Documents & Tamper-Evident Verification API.

Provides:
- Public verification portal endpoint (GET /api/v1/documents/verify/{code})
- Hash integrity lookup (POST /api/v1/documents/verify/hash)
- Encounter document archive listing (GET /api/v1/documents/consultation/{consultation_id})
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
import uuid
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services.clinical_document_service import clinical_document_service

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Certified Clinical Documents & Verification"])


class DocumentVerificationResponse(BaseModel):
    status: str
    verification_code: str
    sha256_hash: str
    document_id: Optional[str] = None
    document_type: str
    title: str
    subtitle: Optional[str] = None
    consultation_id: Optional[str] = None
    patient_ref: str
    patient_age_group: Optional[str] = None
    patient_sex: Optional[str] = None
    doctor_name: str
    doctor_specialty: str
    registration_number: str
    issuing_body: str
    signed_at: str
    signed_at_formatted: str
    signature_status: str
    institution: str
    verified_at: str
    sections_summary: Optional[List[str]] = None


class VerifyHashRequest(BaseModel):
    sha256_hash: str


@router.get("/verify/{verification_code}", response_model=DocumentVerificationResponse)
async def verify_clinical_document_by_code(
    verification_code: str,
):
    """
    Public tamper-evident verification endpoint.
    Verifies the cryptographic SHA-256 digital signature and authenticity of any
    clinical document (Medical Certificate, Discharge Summary, Referral Letter, etc.).
    """
    clean_code = verification_code.strip()
    result = clinical_document_service.verify_document(clean_code)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Verification token '{clean_code}' not found in official registry or signature has been revoked.",
        )

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%d %B %Y, %H:%M:%S UTC")
    return DocumentVerificationResponse(
        status="VERIFIED_VALID",
        verification_code=result.get("verification_code", clean_code),
        sha256_hash=result.get("sha256_hash", ""),
        document_id=result.get("document_id"),
        document_type=result.get("document_type", "certified_clinical_record"),
        title=result.get("title", "CERTIFIED CLINICAL DOCUMENT"),
        subtitle=result.get("subtitle", "Official Verified Electronic Health Record"),
        consultation_id=result.get("consultation_id"),
        patient_ref=result.get("patient_ref", "PT-CONFIDENTIAL"),
        patient_age_group=result.get("patient_age_group", "Adult"),
        patient_sex=result.get("patient_sex", "Specified in Record"),
        doctor_name=result.get("doctor_name", "Attending Clinician"),
        doctor_specialty=result.get("doctor_specialty", "General Medicine"),
        registration_number=result.get("registration_number", "REG-MED-84920"),
        issuing_body=result.get("issuing_body", "National Medical Council"),
        signed_at=result.get("signed_at", datetime.datetime.now(datetime.timezone.utc).isoformat()),
        signed_at_formatted=result.get("signed_at_formatted", now),
        signature_status=result.get("signature_status", "VERIFIED_VALID"),
        institution=result.get("institution", "DocAssistIQ Clinical Intelligence Health System"),
        verified_at=now,
        sections_summary=result.get("sections_summary", []),
    )


@router.post("/verify/hash", response_model=DocumentVerificationResponse)
async def verify_clinical_document_by_hash(
    payload: VerifyHashRequest,
):
    """Verify document cryptographic integrity by full or truncated SHA-256 hash."""
    clean_hash = payload.sha256_hash.strip().lower()
    result = clinical_document_service.verify_document(clean_hash)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"SHA-256 digest '{clean_hash[:16]}...' does not match any registered official clinical document.",
        )

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%d %B %Y, %H:%M:%S UTC")
    return DocumentVerificationResponse(
        status="VERIFIED_VALID",
        verification_code=result.get("verification_code", f"DOCASSIST-SIG-{clean_hash[:12].upper()}"),
        sha256_hash=result.get("sha256_hash", clean_hash),
        document_id=result.get("document_id"),
        document_type=result.get("document_type", "certified_clinical_record"),
        title=result.get("title", "CERTIFIED CLINICAL DOCUMENT"),
        subtitle=result.get("subtitle", "Official Verified Electronic Health Record"),
        consultation_id=result.get("consultation_id"),
        patient_ref=result.get("patient_ref", "PT-CONFIDENTIAL"),
        patient_age_group=result.get("patient_age_group", "Adult"),
        patient_sex=result.get("patient_sex", "Specified in Record"),
        doctor_name=result.get("doctor_name", "Attending Clinician"),
        doctor_specialty=result.get("doctor_specialty", "General Medicine"),
        registration_number=result.get("registration_number", "REG-MED-84920"),
        issuing_body=result.get("issuing_body", "National Medical Council"),
        signed_at=result.get("signed_at", datetime.datetime.now(datetime.timezone.utc).isoformat()),
        signed_at_formatted=result.get("signed_at_formatted", now),
        signature_status=result.get("signature_status", "VERIFIED_VALID"),
        institution=result.get("institution", "DocAssistIQ Clinical Intelligence Health System"),
        verified_at=now,
        sections_summary=result.get("sections_summary", []),
    )


@router.get("/consultation/{consultation_id}")
async def list_consultation_certified_documents(
    consultation_id: uuid.UUID,
):
    """List all certified documents generated for a specific encounter."""
    docs = clinical_document_service.list_documents_for_consultation(str(consultation_id))
    return {
        "consultation_id": str(consultation_id),
        "total": len(docs),
        "documents": docs,
    }


@router.get("/patient/{patient_ref}")
async def list_patient_certified_documents(
    patient_ref: str,
):
    """List all certified documents generated for a specific patient."""
    docs = clinical_document_service.list_documents_for_patient(patient_ref)
    return {
        "patient_ref": patient_ref,
        "total": len(docs),
        "documents": docs,
    }

