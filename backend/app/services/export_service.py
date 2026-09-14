from typing import Dict, Any
from app.models.consultation import Consultation
from app.schemas.note import ClinicalNoteResponse
import io
from fpdf import FPDF

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
        if note_data and hasattr(note_data, 'body'):
            for title, content in note_data.body.items():
                note_text += f"# {title}\n{content}\n\n"
        
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
        
        if note_data and hasattr(note_data, 'body'):
            for title, content in note_data.body.items():
                md += f"## {title}\n{content}\n\n"
        else:
            md += "*No finalized note content available.*\n"
            
        return md

    @staticmethod
    def generate_pdf(
        consultation: Consultation, note_data: ClinicalNoteResponse | None
    ) -> bytes:
        """
        Generates a physical PDF byte stream for the clinical record.
        Includes Phase 73 Immutability Hash in the footer.
        """
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)

        # Header
        pdf.set_font("Helvetica", style="B", size=16)
        pdf.cell(200, 10, text="DocAssistIQ - Finalized Clinical Note", align='C')
        pdf.ln(10)

        # Meta
        pdf.set_font("Helvetica", size=10)
        pdf.cell(200, 8, text=f"Consultation ID: {consultation.id}")
        pdf.cell(200, 8, text=f"Doctor ID: {consultation.doctor_id}")
        pdf.cell(200, 8, text=f"Date: {consultation.created_at.isoformat() if consultation.created_at else 'N/A'}")
        pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
        pdf.ln(10)

        # Content
        if note_data and hasattr(note_data, 'body'):
            for title, content in note_data.body.items():
                pdf.set_font("Helvetica", style="B", size=12)
                pdf.cell(200, 10, text=title.upper())
                pdf.set_font("Helvetica", size=10)
                # Handle multi-line content safely
                content_safe = str(content).encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 5, text=content_safe)
                pdf.ln(5)
        else:
            pdf.set_font("Helvetica", style="I", size=10)
            pdf.cell(200, 10, text="No finalized note content available.")

        # Footer with Immutable Hash
        pdf.ln(20)
        pdf.set_font("Helvetica", style="I", size=8)
        pdf.set_text_color(100, 100, 100)
        hash_val = getattr(consultation, 'immutable_hash', 'PENDING')
        pdf.cell(0, 10, text=f"Cryptographic Hash (SHA-256): {hash_val}", align='C')

        # Output bytes
        return bytes(pdf.output())

export_service = ExportService()
