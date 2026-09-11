from typing import Dict, Any
from app.models.consultation import Consultation
from app.schemas.note import ClinicalNoteResponse

class ExportService:
    @staticmethod
    def generate_fhir_document_reference(
        consultation: Consultation, note_data: ClinicalNoteResponse | None
    ) -> Dict[str, Any]:
        """
        Generates a simplified HL7 FHIR DocumentReference resource
        representing the finalized clinical note.
        """
        # Build the FHIR DocumentReference
        patient_ref = consultation.patient_session_id if consultation.patient_session_id else "unknown"
        
        # Build text representation of note
        note_text = ""
        if note_data:
            for section in note_data.sections:
                note_text += f"# {section.title}\n{section.content}\n\n"
        
        return {
            "resourceType": "DocumentReference",
            "status": "current",
            "type": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "11488-4",
                        "display": "Consultation note"
                    }
                ]
            },
            "subject": {
                "reference": f"Patient/{patient_ref}"
            },
            "date": consultation.created_at.isoformat() + "Z" if consultation.created_at else None,
            "author": [
                {
                    "reference": f"Practitioner/{consultation.doctor_id}"
                }
            ],
            "content": [
                {
                    "attachment": {
                        "contentType": "text/markdown",
                        "data": note_text.encode('utf-8').hex(), # Simplified hex encoding for mock
                        "title": "Clinical Consultation Note"
                    }
                }
            ]
        }

    @staticmethod
    def generate_markdown(
        consultation: Consultation, note_data: ClinicalNoteResponse | None
    ) -> str:
        """
        Generates a markdown version of the consultation for PDF printing.
        """
        md = f"# Clinical Consultation Note\n\n"
        md += f"**Date:** {consultation.created_at.isoformat() if consultation.created_at else 'N/A'}\n"
        md += f"**Consultation ID:** {consultation.id}\n"
        md += f"**Clinician ID:** {consultation.doctor_id}\n\n"
        md += "---\n\n"
        
        if note_data:
            for section in note_data.sections:
                md += f"## {section.title}\n{section.content}\n\n"
        else:
            md += "*No finalized note content available.*\n"
            
        return md

export_service = ExportService()
