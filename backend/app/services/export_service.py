from typing import Dict, Any, List, Optional
from app.models.consultation import Consultation
from app.schemas.note import ClinicalNoteResponse
import io
import re
import uuid
import base64
from fpdf import FPDF


def _extract_vital_observations(vitals_text: str, patient_ref: str, encounter_ref: str, date_iso: str) -> List[Dict[str, Any]]:
    """
    Parses unstructured vitals string into standard HL7 FHIR R4 Observation resources with LOINC codes.
    """
    observations = []
    if not vitals_text or vitals_text.lower() == "not documented":
        return observations

    # 1. Blood Pressure: Systolic / Diastolic
    bp_match = re.search(r"\b(?:bp|blood pressure)[:\s]*(\d{2,3})/(\d{2,3})\b", vitals_text, re.IGNORECASE)
    if bp_match:
        sys_val = float(bp_match.group(1))
        dia_val = float(bp_match.group(2))
        bp_obs_id = f"obs-bp-{uuid.uuid4().hex[:8]}"
        observations.append({
            "fullUrl": f"urn:uuid:{bp_obs_id}",
            "resource": {
                "resourceType": "Observation",
                "id": bp_obs_id,
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs"
                    }]
                }],
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "85354-9",
                        "display": "Blood pressure panel with all children optional"
                    }],
                    "text": "Blood Pressure"
                },
                "subject": {"reference": f"urn:uuid:{patient_ref}"},
                "encounter": {"reference": f"urn:uuid:{encounter_ref}"},
                "effectiveDateTime": date_iso,
                "component": [
                    {
                        "code": {
                            "coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic blood pressure"}]
                        },
                        "valueQuantity": {"value": sys_val, "unit": "mmHg", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}
                    },
                    {
                        "code": {
                            "coding": [{"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic blood pressure"}]
                        },
                        "valueQuantity": {"value": dia_val, "unit": "mmHg", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}
                    }
                ]
            }
        })

    # 2. Heart Rate
    hr_match = re.search(r"\b(?:hr|heart rate|pulse)[:\s]*(\d{2,3})\b", vitals_text, re.IGNORECASE)
    if hr_match:
        hr_val = float(hr_match.group(1))
        hr_obs_id = f"obs-hr-{uuid.uuid4().hex[:8]}"
        observations.append({
            "fullUrl": f"urn:uuid:{hr_obs_id}",
            "resource": {
                "resourceType": "Observation",
                "id": hr_obs_id,
                "status": "final",
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]}],
                "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"}], "text": "Heart Rate"},
                "subject": {"reference": f"urn:uuid:{patient_ref}"},
                "encounter": {"reference": f"urn:uuid:{encounter_ref}"},
                "effectiveDateTime": date_iso,
                "valueQuantity": {"value": hr_val, "unit": "beats/minute", "system": "http://unitsofmeasure.org", "code": "/min"}
            }
        })

    # 3. Respiratory Rate
    rr_match = re.search(r"\b(?:rr|respiratory rate|resp rate)[:\s]*(\d{1,2})\b", vitals_text, re.IGNORECASE)
    if rr_match:
        rr_val = float(rr_match.group(1))
        rr_obs_id = f"obs-rr-{uuid.uuid4().hex[:8]}"
        observations.append({
            "fullUrl": f"urn:uuid:{rr_obs_id}",
            "resource": {
                "resourceType": "Observation",
                "id": rr_obs_id,
                "status": "final",
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]}],
                "code": {"coding": [{"system": "http://loinc.org", "code": "9279-1", "display": "Respiratory rate"}], "text": "Respiratory Rate"},
                "subject": {"reference": f"urn:uuid:{patient_ref}"},
                "encounter": {"reference": f"urn:uuid:{encounter_ref}"},
                "effectiveDateTime": date_iso,
                "valueQuantity": {"value": rr_val, "unit": "breaths/minute", "system": "http://unitsofmeasure.org", "code": "/min"}
            }
        })

    # 4. Body Temperature
    temp_match = re.search(r"\b(?:temp|temperature|t)[:\s]*(\d{2,3}(?:\.\d)?)\b", vitals_text, re.IGNORECASE)
    if temp_match:
        temp_val = float(temp_match.group(1))
        unit = "Cel" if temp_val < 50 else "[degF]"
        temp_obs_id = f"obs-temp-{uuid.uuid4().hex[:8]}"
        observations.append({
            "fullUrl": f"urn:uuid:{temp_obs_id}",
            "resource": {
                "resourceType": "Observation",
                "id": temp_obs_id,
                "status": "final",
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]}],
                "code": {"coding": [{"system": "http://loinc.org", "code": "8310-5", "display": "Body temperature"}], "text": "Body Temperature"},
                "subject": {"reference": f"urn:uuid:{patient_ref}"},
                "encounter": {"reference": f"urn:uuid:{encounter_ref}"},
                "effectiveDateTime": date_iso,
                "valueQuantity": {"value": temp_val, "unit": "degC" if unit == "Cel" else "degF", "system": "http://unitsofmeasure.org", "code": unit}
            }
        })

    # 5. Oxygen Saturation (SpO2)
    spo2_match = re.search(r"\b(?:spo2|o2 sat|oxygen sat(?:uration)?)[:\s]*(\d{2,3})\s*%?\b", vitals_text, re.IGNORECASE)
    if spo2_match:
        spo2_val = float(spo2_match.group(1))
        spo2_obs_id = f"obs-spo2-{uuid.uuid4().hex[:8]}"
        observations.append({
            "fullUrl": f"urn:uuid:{spo2_obs_id}",
            "resource": {
                "resourceType": "Observation",
                "id": spo2_obs_id,
                "status": "final",
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]}],
                "code": {"coding": [{"system": "http://loinc.org", "code": "2708-6", "display": "Oxygen saturation in Arterial blood"}], "text": "Oxygen Saturation (SpO2)"},
                "subject": {"reference": f"urn:uuid:{patient_ref}"},
                "encounter": {"reference": f"urn:uuid:{encounter_ref}"},
                "effectiveDateTime": date_iso,
                "valueQuantity": {"value": spo2_val, "unit": "%", "system": "http://unitsofmeasure.org", "code": "%"}
            }
        })

    return observations


class ExportService:
    @staticmethod
    def generate_fhir_document_reference(
        consultation: Consultation, note_data: ClinicalNoteResponse | None
    ) -> Dict[str, Any]:
        """
        Generates a compliant HL7 FHIR R4 DocumentReference resource
        representing the finalized clinical note with RFC 4648 Base64 attachment encoding.
        """
        patient_ref = str(consultation.patient_session_id) if consultation.patient_session_id else "unknown"
        
        # Build text representation of note cleanly
        note_text = ""
        if note_data and hasattr(note_data, 'body') and isinstance(note_data.body, dict):
            for sec_key, sec_content in note_data.body.items():
                if sec_key.startswith("_"):
                    continue
                clean_title = sec_key.replace("_", " ").title()
                sec_text = sec_content.get("text", "") if isinstance(sec_content, dict) else str(sec_content)
                if sec_text and sec_text.strip():
                    note_text += f"# {clean_title}\n{sec_text.strip()}\n\n"
        elif consultation.input_text:
            note_text = f"# Clinical Intake Note\n{consultation.input_text}\n"

        b64_data = base64.b64encode(note_text.encode('utf-8')).decode('ascii')
        
        return {
            "resourceType": "DocumentReference",
            "id": f"docref-{consultation.id}",
            "status": "current",
            "docStatus": "final",
            "type": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "11488-4",
                        "display": "Consultation note"
                    }
                ],
                "text": "Consultation note"
            },
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category",
                            "code": "clinical-note",
                            "display": "Clinical Note"
                        }
                    ]
                }
            ],
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
                        "data": b64_data,
                        "title": "Clinical Consultation Note",
                        "size": len(note_text.encode('utf-8'))
                    }
                }
            ]
        }

    @staticmethod
    def generate_fhir_bundle(
        consultation: Consultation,
        note_data: ClinicalNoteResponse | None,
        findings: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generates a complete, ONC/CMS US Core compliant HL7 FHIR R4 Document Bundle with
        Composition, Patient, Practitioner, Encounter, DocumentReference, Condition,
        Observation (LOINC vitals), and MedicationStatement entries.
        """
        patient_ref = str(consultation.patient_session_id) if consultation.patient_session_id else str(uuid.uuid4())
        doctor_ref = str(consultation.doctor_id) if consultation.doctor_id else str(uuid.uuid4())
        encounter_ref = str(consultation.id)
        composition_id = f"comp-{consultation.id}"
        date_iso = (consultation.created_at.isoformat() + "Z") if consultation.created_at else "2026-01-01T00:00:00Z"

        # Build sections with LOINC mapping
        loinc_map = {
            "chief_complaint": ("10154-3", "Chief complaint"),
            "hpi": ("10164-2", "History of present illness"),
            "vitals": ("8716-3", "Vital signs"),
            "review_of_systems": ("10187-3", "Review of systems"),
            "past_medical_history": ("11348-0", "History of past illness"),
            "medications": ("10160-0", "History of medication use"),
            "allergies": ("48765-2", "Allergies and adverse reactions"),
            "physical_examination": ("29545-1", "Physical findings"),
            "investigations": ("30954-2", "Relevant diagnostic tests/laboratory data"),
            "differential_diagnosis": ("51848-0", "Evaluation + Plan note"),
            "assessment": ("51848-0", "Assessment"),
            "plan": ("18776-5", "Plan of care"),
            "follow_up_plan": ("51847-2", "Follow-up instructions"),
            "safety_net": ("51847-2", "Safety net & precautions"),
        }

        sections = []
        full_note_text = ""
        vitals_text = ""

        if note_data and hasattr(note_data, 'body') and isinstance(note_data.body, dict):
            for sec_key, sec_content in note_data.body.items():
                if sec_key.startswith("_"):
                    continue
                loinc_info = loinc_map.get(sec_key, ("11488-4", sec_key.replace("_", " ").title()))
                clean_title = sec_key.replace("_", " ").title()
                
                sec_text = sec_content.get("text", "") if isinstance(sec_content, dict) else str(sec_content)
                if not sec_text or not sec_text.strip():
                    continue

                if sec_key == "vitals":
                    vitals_text = sec_text

                full_note_text += f"## {clean_title}\n{sec_text.strip()}\n\n"
                sections.append({
                    "title": clean_title,
                    "code": {
                        "coding": [{
                            "system": "http://loinc.org",
                            "code": loinc_info[0],
                            "display": loinc_info[1]
                        }]
                    },
                    "text": {
                        "status": "generated",
                        "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\"><p>{sec_text.strip()}</p></div>"
                    }
                })
        else:
            full_note_text = consultation.input_text or "No clinical note documented."
            sections.append({
                "title": "Clinical Narrative",
                "code": {"coding": [{"system": "http://loinc.org", "code": "11488-4", "display": "Consultation note"}]},
                "text": {"status": "generated", "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\"><p>{full_note_text}</p></div>"}
            })

        b64_data = base64.b64encode(full_note_text.encode('utf-8')).decode('ascii')

        # 1. Composition
        composition_entry = {
            "fullUrl": f"urn:uuid:{composition_id}",
            "resource": {
                "resourceType": "Composition",
                "id": composition_id,
                "status": "final",
                "type": {
                    "coding": [{"system": "http://loinc.org", "code": "11488-4", "display": "Consultation note"}]
                },
                "subject": {"reference": f"urn:uuid:{patient_ref}"},
                "encounter": {"reference": f"urn:uuid:{encounter_ref}"},
                "date": date_iso,
                "author": [{"reference": f"urn:uuid:{doctor_ref}"}],
                "title": "Clinical Consultation Encounter Note",
                "section": sections
            }
        }

        # 2. Patient
        patient_entry = {
            "fullUrl": f"urn:uuid:{patient_ref}",
            "resource": {
                "resourceType": "Patient",
                "id": patient_ref,
                "active": True
            }
        }

        # 3. Practitioner
        practitioner_entry = {
            "fullUrl": f"urn:uuid:{doctor_ref}",
            "resource": {
                "resourceType": "Practitioner",
                "id": doctor_ref,
                "active": True
            }
        }

        # 4. Encounter
        encounter_entry = {
            "fullUrl": f"urn:uuid:{encounter_ref}",
            "resource": {
                "resourceType": "Encounter",
                "id": encounter_ref,
                "status": "finished",
                "class": {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "code": "AMB",
                    "display": "ambulatory"
                },
                "subject": {"reference": f"urn:uuid:{patient_ref}"}
            }
        }

        # 5. DocumentReference
        docref_entry = {
            "fullUrl": f"urn:uuid:docref-{consultation.id}",
            "resource": {
                "resourceType": "DocumentReference",
                "id": f"docref-{consultation.id}",
                "status": "current",
                "docStatus": "final",
                "type": {
                    "coding": [{"system": "http://loinc.org", "code": "11488-4", "display": "Consultation note"}]
                },
                "subject": {"reference": f"urn:uuid:{patient_ref}"},
                "date": date_iso,
                "author": [{"reference": f"urn:uuid:{doctor_ref}"}],
                "content": [{
                    "attachment": {
                        "contentType": "text/markdown",
                        "data": b64_data,
                        "title": "Clinical Consultation Note"
                    }
                }]
            }
        }

        entries = [
            composition_entry,
            patient_entry,
            practitioner_entry,
            encounter_entry,
            docref_entry
        ]

        # 6. Structured Observations from Vitals
        vital_obs = _extract_vital_observations(vitals_text, patient_ref, encounter_ref, date_iso)
        entries.extend(vital_obs)

        # 7. Discrete Conditions and Medications from Findings
        if findings:
            for f in findings:
                f_type = getattr(f, "finding_type", "")
                f_concept = getattr(f, "concept", "")
                f_text = getattr(f, "finding_text", "") or getattr(f, "value", "") or ""
                f_canonical = getattr(f, "canonical_concept", None) or f_text
                f_id = getattr(f, "id", uuid.uuid4())
                is_confirmed = getattr(f, "is_clinician_confirmed", False)

                # Condition resource
                if f_type in ("diagnosis", "symptom") or f_concept in ("CONDITION", "SYMPTOM"):
                    cond_id = f"cond-{f_id}"
                    entries.append({
                        "fullUrl": f"urn:uuid:{cond_id}",
                        "resource": {
                            "resourceType": "Condition",
                            "id": str(cond_id),
                            "clinicalStatus": {
                                "coding": [{
                                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                    "code": "active",
                                    "display": "Active"
                                }]
                            },
                            "verificationStatus": {
                                "coding": [{
                                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                                    "code": "confirmed" if is_confirmed else "provisional",
                                    "display": "Confirmed" if is_confirmed else "Provisional"
                                }]
                            },
                            "category": [{
                                "coding": [{
                                    "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                                    "code": "encounter-diagnosis",
                                    "display": "Encounter Diagnosis"
                                }]
                            }],
                            "code": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "display": f_canonical
                                }],
                                "text": f_text
                            },
                            "subject": {"reference": f"urn:uuid:{patient_ref}"},
                            "encounter": {"reference": f"urn:uuid:{encounter_ref}"}
                        }
                    })

                # MedicationStatement resource
                elif f_concept == "MEDICATION" or f_type == "medication":
                    med_id = f"med-{f_id}"
                    entries.append({
                        "fullUrl": f"urn:uuid:{med_id}",
                        "resource": {
                            "resourceType": "MedicationStatement",
                            "id": str(med_id),
                            "status": "active",
                            "medicationCodeableConcept": {
                                "coding": [{
                                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                    "display": f_canonical
                                }],
                                "text": f_text
                            },
                            "subject": {"reference": f"urn:uuid:{patient_ref}"}
                        }
                    })

        return {
            "resourceType": "Bundle",
            "id": f"bundle-{consultation.id}",
            "type": "document",
            "timestamp": date_iso,
            "entry": entries
        }

    @staticmethod
    def generate_markdown(
        consultation: Consultation, note_data: ClinicalNoteResponse | None
    ) -> str:
        """
        Generates a markdown version of the consultation for PDF printing.
        """
        md = "# Clinical Consultation Note\n\n"
        md += f"**Date:** {consultation.created_at.isoformat() if consultation.created_at else 'N/A'}\n"
        md += f"**Consultation ID:** {consultation.id}\n"
        md += f"**Clinician ID:** {consultation.doctor_id}\n\n"
        md += "---\n\n"
        
        if note_data and hasattr(note_data, 'body') and isinstance(note_data.body, dict):
            for sec_key, sec_content in note_data.body.items():
                if sec_key.startswith("_"):
                    continue
                clean_title = sec_key.replace("_", " ").title()
                sec_text = sec_content.get("text", "") if isinstance(sec_content, dict) else str(sec_content)
                if sec_text and sec_text.strip():
                    md += f"## {clean_title}\n{sec_text.strip()}\n\n"
        else:
            md += "*No finalized note content available.*\n"
            
        return md

    @staticmethod
    def generate_pdf(
        consultation: Consultation, note_data: ClinicalNoteResponse | None
    ) -> bytes:
        """
        Generates a physical PDF byte stream for the clinical record.
        Includes hospital header layout and cryptographic integrity hash in footer.
        """
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Header - Professional Hospital Style
        pdf.set_font("Helvetica", style="B", size=15)
        pdf.set_text_color(24, 43, 73)  # Clinical deep navy
        pdf.cell(0, 10, text="DOCASSISTIQ CLINICAL CONSULTATION RECORD", align='C', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        # Subtitle
        pdf.set_font("Helvetica", size=9)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 5, text="Ambulatory Electronic Health Record Summary", align='C', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Meta Box
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(226, 232, 240)
        pdf.rect(10, pdf.get_y(), 190, 22, style="FD")
        pdf.set_xy(12, pdf.get_y() + 2)

        pdf.set_font("Helvetica", style="B", size=9)
        pdf.set_text_color(51, 65, 85)
        created_str = consultation.created_at.strftime("%d %B %Y, %H:%M UTC") if consultation.created_at else "N/A"
        pdf.cell(90, 5, text=f"Consultation ID: {consultation.id}")
        pdf.cell(90, 5, text=f"Date: {created_str}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(12)
        pdf.cell(90, 5, text=f"Attending Clinician ID: {consultation.doctor_id}")
        pat_session = getattr(consultation, 'patient_session_id', None) or 'N/A'
        pdf.cell(90, 5, text=f"Patient Session ID: {pat_session}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(12)

        # Content Sections
        has_content = False
        if note_data and hasattr(note_data, 'body') and isinstance(note_data.body, dict):
            for sec_key, sec_content in note_data.body.items():
                if sec_key.startswith("_"):
                    continue
                clean_title = sec_key.replace("_", " ").upper()
                sec_text = sec_content.get("text", "") if isinstance(sec_content, dict) else str(sec_content)
                if not sec_text or not sec_text.strip():
                    continue

                has_content = True
                pdf.set_font("Helvetica", style="B", size=10)
                pdf.set_text_color(30, 58, 138)  # Primary blue
                pdf.cell(0, 7, text=clean_title, new_x="LMARGIN", new_y="NEXT")

                pdf.set_font("Helvetica", size=9)
                pdf.set_text_color(31, 41, 55)
                # Clean latin-1 encoding for FPDF
                content_safe = sec_text.strip().encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 5, text=content_safe)
                pdf.ln(3)

        if not has_content:
            pdf.set_font("Helvetica", style="I", size=10)
            pdf.set_text_color(150, 150, 150)
            fallback_text = consultation.input_text or "No finalized clinical narrative documented."
            pdf.multi_cell(0, 5, text=fallback_text.encode('latin-1', 'replace').decode('latin-1'))
            pdf.ln(5)

        # Footer with Cryptographic Tamper-Evident Hash
        pdf.ln(6)
        pdf.set_draw_color(203, 213, 225)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)

        pdf.set_font("Helvetica", style="I", size=8)
        pdf.set_text_color(100, 116, 139)
        hash_val = getattr(consultation, 'immutable_hash', None) or 'PENDING_FINALIZATION'
        pdf.cell(0, 4, text=f"Cryptographic Tamper-Evident Hash (SHA-256): {hash_val}", align='C', new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 4, text="DocAssistIQ Clinical AI Platform - Confidential Medical Record", align='C')

        # Output bytes
        return bytes(pdf.output())


export_service = ExportService()

