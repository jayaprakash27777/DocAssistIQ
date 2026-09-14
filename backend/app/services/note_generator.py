"""DocAssistIQ — Note Generator Service (Phase 30).

AI drafts factual sections of the clinical note from extracted ClinicalFindings.
Must not invent facts, vitals, or examination findings.
Assessment and Plan remain untouched by AI.
"""

import uuid
import structlog
from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.clinical import ClinicalFinding, ClinicalNote
from app.infrastructure.ai.factory import get_generation_provider
from app.services.embedding_service import generate_and_store_embedding

baseline_generation_provider = get_generation_provider()

log = structlog.get_logger(__name__)

# Standard note sections according to Phase 30 (Hybrid SOAP)
SECTIONS = [
    "chief_complaint",
    "hpi",
    "past_medical_history",
    "medications",
    "allergies",
    "family_history",
    "social_history",
    "examination",
    "investigations",
    "assessment",
    "plan"
]

class NoteGeneratorService:
    async def draft_note_from_findings(
        self, 
        db: AsyncSession, 
        consultation_id: uuid.UUID,
        doctor_id: uuid.UUID
    ) -> ClinicalNote:
        """
        Drafts a structured note from current findings. 
        Will create a new note if none exists, or append/update an existing note.
        Does not touch assessment/plan.
        """
        # Get findings
        findings_result = await db.scalars(
            select(ClinicalFinding).where(ClinicalFinding.consultation_id == consultation_id)
        )
        findings = findings_result.all()

        # Format findings for AI
        findings_context = "\\n".join([
            f"- {f.concept}: {f.canonical_concept or f.value} "
            f"(Negated: {f.negated}, Temp: {f.temporality})"
            for f in findings
        ])

        system_prompt = (
            "You are an Expert Clinical Note Generator AI. "
            "Your task is to write a highly professional, accurate, and concise clinical note from the provided unstructured clinical findings. "
            "You MUST ONLY use the provided extracted findings to write factual sections. "
            "DO NOT invent facts, vitals, or examination findings. DO NOT hallucinate patient history. "
            "Use standard medical abbreviations where appropriate. "
            "Leave sections blank if there is absolutely no supporting data. "
            "Output ONLY valid JSON matching this exact schema (no markdown, no preamble): "
            '{"chief_complaint": "", "hpi": "", "past_medical_history": "", '
            '"medications": "", "allergies": "", "family_history": "", '
            '"social_history": "", "examination": "", "investigations": ""}'
        )

        prompt = f"Extracted Findings:\\n{findings_context}"
        
        log.info("note_generator_request", consultation_id=str(consultation_id))
        
        try:
            from app.infrastructure.ai.interfaces import GenerationRequest
            request = GenerationRequest(
                prompt=prompt,
                system_prompt=system_prompt,
                json_schema={"type": "object"}
            )
            # For Baseline provider, this just echoes back a simple JSON struct.
            # In production, this would call an LLM.
            result = await baseline_generation_provider.generate(request)
            # The baseline provider returns a string. Let's assume it's valid JSON.
            import json
            drafted_sections = json.loads(result.text)
        except Exception as e:
            log.error("note_generator_failed", error=str(e))
            # Fallback to simple deterministic formatting if AI fails
            drafted_sections = self._fallback_deterministic_draft(findings)  # type: ignore

        # Store NoteSection objects per section (text, original_ai_text, status)
        # assessment and plan are left blank — clinician fills those in
        structured_sections = {}
        for section in SECTIONS:
            if section in ("assessment", "plan"):
                structured_sections[section] = {
                    "text": "",
                    "original_ai_text": None,
                    "status": "draft"
                }
            else:
                val = drafted_sections.get(section, "") or ""
                structured_sections[section] = {
                    "text": val,
                    "original_ai_text": val,
                    "status": "draft"
                }

        # Upsert note
        note_result = await db.scalars(
            select(ClinicalNote).where(ClinicalNote.consultation_id == consultation_id)
        )
        existing_note = note_result.first()

        if existing_note:
            # Update sections that are empty (don't overwrite clinician edits)
            current_body = existing_note.body or {}
            for section in SECTIONS:
                existing_val = current_body.get(section, "")
                # Only overwrite if section is empty and not assessment/plan
                if section not in ("assessment", "plan"):
                    if not existing_val or (isinstance(existing_val, dict) and not existing_val.get("text")):  # Only fill blanks
                        current_body[section] = structured_sections[section]
                elif section not in current_body:
                    current_body[section] = { "text": "", "original_ai_text": None, "status": "draft" }
            
            existing_note.body = current_body
            existing_note.is_ai_generated = True
            existing_note.last_edited_by_id = None
            existing_note.version += 1
            note = existing_note
        else:
            tenant_id = db.info.get("tenant_id")
            note = ClinicalNote(
                tenant_id=tenant_id,
                consultation_id=consultation_id,
                author_id=doctor_id, # The doctor owns the note
                note_type="progress",
                body=structured_sections,
                status="draft",
                is_ai_generated=True,
                last_edited_by_id=None
            )
            db.add(note)
            
        await db.commit()
        await db.refresh(note)
        
        # Phase 36: Generate embedding for the new/updated note immediately
        try:
            current_body = note.body or {}
            text_parts = []
            for k, v in current_body.items():
                if isinstance(v, dict) and "text" in v:
                    text_parts.append(f"{k.upper()}: {v['text']}")
                elif isinstance(v, str):
                    text_parts.append(f"{k.upper()}: {v}")
            note_content = "\n\n".join(text_parts)
            
            if note_content.strip():
                await generate_and_store_embedding(
                    db,
                    source_record_id=str(consultation_id),
                    source_record_type="clinical_note",
                    content=note_content
                )
        except Exception as e:
            log.error("note_embedding_failed", error=str(e))
            
        return note

    def _fallback_deterministic_draft(self, findings: List[ClinicalFinding]) -> Dict[str, str]:
        """Simple deterministic fallback to populate structured note if AI fails."""
        sections = {s: "" for s in SECTIONS}
        
        pmh = []
        meds = []
        hpi = []
        
        for f in findings:
            val = f.canonical_concept or f.value
            status_text = " (negated)" if f.negated else ""
            
            if f.temporality == "past":
                pmh.append(f"{val}{status_text}")
            elif f.concept == "medication":
                meds.append(f"{val}{status_text}")
            else:
                hpi.append(f"{val}{status_text}")
                
        sections["past_medical_history"] = ", ".join(pmh) if pmh else ""
        sections["medications"] = ", ".join(meds) if meds else ""
        sections["hpi"] = ", ".join(hpi) if hpi else ""
        
        return sections

note_generator_service = NoteGeneratorService()
