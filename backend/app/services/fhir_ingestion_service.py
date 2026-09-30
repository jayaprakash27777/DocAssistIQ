"""DocAssistIQ — HL7 FHIR R4 Inbound Ingestion Service.

Parses hospital-grade HL7 FHIR R4 Bundles (from Epic, Oracle Cerner, MEDITECH,
and Ayushman Bharat Digital Mission ABHA), extracting:
- Patient demographics (gender, age calculated from birthDate, identifier)
- Conditions (ICD-10, SNOMED CT)
- Observations (Vitals & Labs with LOINC codes: BP, HR, SpO2, eGFR, Creatinine)
- MedicationStatements / MedicationRequests (RxNorm, dosages)
- AllergyIntolerances (substances and reaction severities)

Enforces strict de-identification (Rule 6) and validation.
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.patient_profile import PatientProfile
from app.models.doctor import Doctor
from app.services.clinical_nlp import scrub_phi

log = structlog.get_logger(__name__)

# Standard LOINC code mappings for clinical observations
LOINC_MAP = {
    # Blood pressure
    "85354-9": "Blood Pressure",
    "8480-6": "Systolic Blood Pressure",
    "8462-4": "Diastolic Blood Pressure",
    # Heart rate & pulse
    "8867-4": "Heart Rate",
    # Respiratory rate
    "9279-1": "Respiratory Rate",
    # Body temperature
    "8310-5": "Body Temperature",
    # Oxygen saturation
    "2708-6": "Oxygen Saturation",
    "59408-5": "Oxygen Saturation (SpO2)",
    # Key renal & metabolic labs
    "2160-0": "Serum Creatinine",
    "33914-3": "eGFR (Estimated GFR)",
    "48642-3": "eGFR (CKD-EPI)",
    "2345-7": "Glucose",
    "718-7": "Hemoglobin",
    "6690-2": "Leukocytes (WBC)",
    "777-3": "Platelets",
}


class FhirIngestionService:
    """Enterprise HL7 FHIR R4 Inbound Ingestion Engine."""

    @staticmethod
    def _calculate_age(birth_date_str: str) -> Optional[int]:
        """Calculates exact integer age from ISO birthDate string (YYYY-MM-DD)."""
        try:
            b_date = datetime.strptime(birth_date_str[:10], "%Y-%m-%d").date()
            today = date.today()
            age = today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
            return max(0, age)
        except Exception:
            return None

    @classmethod
    def parse_bundle(cls, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses an HL7 FHIR R4 Bundle and returns normalized clinical structures.
        """
        if not isinstance(bundle, dict):
            raise ValueError("Invalid FHIR payload: Expected JSON object")

        resource_type = bundle.get("resourceType")
        if resource_type != "Bundle":
            raise ValueError(f"Expected FHIR resourceType 'Bundle', received '{resource_type}'")

        entries = bundle.get("entry", [])
        if not isinstance(entries, list):
            raise ValueError("Invalid FHIR Bundle: 'entry' must be a list of resource objects")

        parsed_data: Dict[str, Any] = {
            "patient": {},
            "conditions": [],
            "observations": [],
            "medications": [],
            "allergies": [],
            "fhir_version": "R4",
            "total_resources_parsed": len(entries),
        }

        for entry in entries:
            resource = entry.get("resource") if isinstance(entry, dict) else None
            if not isinstance(resource, dict):
                continue

            res_type = resource.get("resourceType")

            # 1. Patient Demographics
            if res_type == "Patient":
                gender = resource.get("gender", "unknown").lower()
                biological_sex = "male" if gender == "male" else "female" if gender == "female" else "other"
                birth_date = resource.get("birthDate")
                calculated_age = cls._calculate_age(birth_date) if birth_date else None

                # Extract MRN or patient identifier
                identifiers = resource.get("identifier", [])
                patient_ref = None
                if identifiers and isinstance(identifiers, list):
                    patient_ref = identifiers[0].get("value")

                parsed_data["patient"] = {
                    "biological_sex": biological_sex,
                    "birth_date": birth_date,
                    "age": calculated_age,
                    "patient_ref": patient_ref,
                }

            # 2. Conditions (Diagnoses, Problem List)
            elif res_type == "Condition":
                code_obj = resource.get("code", {})
                codings = code_obj.get("coding", [])
                cond_name = code_obj.get("text")

                icd10_code = None
                snomed_code = None

                for c in codings:
                    sys_url = c.get("system", "").lower()
                    c_code = c.get("code")
                    c_display = c.get("display")

                    if not cond_name and c_display:
                        cond_name = c_display

                    if "icd-10" in sys_url or "icd10" in sys_url:
                        icd10_code = c_code
                    elif "snomed" in sys_url:
                        snomed_code = c_code

                status_obj = resource.get("clinicalStatus", {})
                status_codings = status_obj.get("coding", [])
                clinical_status = "active"
                if status_codings:
                    clinical_status = status_codings[0].get("code", "active")

                if cond_name:
                    clean_name, _ = scrub_phi(cond_name)
                    parsed_data["conditions"].append({
                        "name": clean_name.strip(),
                        "icd10": icd10_code,
                        "snomed": snomed_code,
                        "status": clinical_status,
                        "onset": resource.get("onsetDateTime"),
                    })

            # 3. Observations (Vitals & Labs)
            elif res_type == "Observation":
                code_obj = resource.get("code", {})
                codings = code_obj.get("coding", [])
                obs_name = code_obj.get("text")
                loinc_code = None

                for c in codings:
                    if "loinc" in c.get("system", "").lower():
                        loinc_code = c.get("code")
                        if not obs_name and loinc_code in LOINC_MAP:
                            obs_name = LOINC_MAP[loinc_code]
                        elif not obs_name and c.get("display"):
                            obs_name = c.get("display")

                # Handle multi-component observations (e.g., Blood Pressure panel)
                components = resource.get("component", [])
                if components:
                    comp_vals = {}
                    for comp in components:
                        c_codings = comp.get("code", {}).get("coding", [])
                        c_val_obj = comp.get("valueQuantity", {})
                        c_val = c_val_obj.get("value")
                        for cc in c_codings:
                            c_loinc = cc.get("code")
                            if c_loinc in LOINC_MAP:
                                comp_vals[LOINC_MAP[c_loinc]] = c_val
                    parsed_data["observations"].append({
                        "name": obs_name or "Panel Observation",
                        "loinc": loinc_code,
                        "components": comp_vals,
                        "effective_datetime": resource.get("effectiveDateTime"),
                    })
                else:
                    val_qty = resource.get("valueQuantity", {})
                    val_num = val_qty.get("value")
                    val_unit = val_qty.get("unit", "")
                    if val_num is not None:
                        parsed_data["observations"].append({
                            "name": obs_name or "Observation",
                            "loinc": loinc_code,
                            "value": val_num,
                            "unit": val_unit,
                            "effective_datetime": resource.get("effectiveDateTime"),
                        })

            # 4. MedicationStatements & MedicationRequests
            elif res_type in ("MedicationStatement", "MedicationRequest"):
                med_code_obj = resource.get("medicationCodeableConcept", {})
                codings = med_code_obj.get("coding", [])
                med_name = med_code_obj.get("text")
                rxnorm_code = None

                for c in codings:
                    sys_url = c.get("system", "").lower()
                    if "rxnorm" in sys_url:
                        rxnorm_code = c.get("code")
                    if not med_name and c.get("display"):
                        med_name = c.get("display")

                dosage_instructions = resource.get("dosageInstruction", [])
                dose_text = ""
                if dosage_instructions:
                    dose_text = dosage_instructions[0].get("text", "")

                if med_name:
                    clean_med, _ = scrub_phi(med_name)
                    parsed_data["medications"].append({
                        "name": clean_med.strip(),
                        "rxnorm": rxnorm_code,
                        "dosage": dose_text,
                        "status": resource.get("status", "active"),
                    })

            # 5. AllergyIntolerance
            elif res_type == "AllergyIntolerance":
                substance_obj = resource.get("code", {})
                substance_name = substance_obj.get("text")
                if not substance_name and substance_obj.get("coding"):
                    substance_name = substance_obj["coding"][0].get("display")

                if substance_name:
                    clean_substance, _ = scrub_phi(substance_name)
                    parsed_data["allergies"].append({
                        "substance": clean_substance.strip(),
                        "criticality": resource.get("criticality", "low"),
                        "clinical_status": resource.get("clinicalStatus", {}).get("coding", [{}])[0].get("code", "active"),
                    })

        return parsed_data

    @classmethod
    async def import_bundle(
        cls,
        db: AsyncSession,
        doctor: Doctor,
        bundle: Dict[str, Any],
        override_patient_ref: Optional[str] = None
    ) -> Tuple[PatientProfile, Dict[str, Any]]:
        """
        Parses and imports an HL7 FHIR R4 Bundle into an active PatientProfile in the database.
        """
        parsed = cls.parse_bundle(bundle)
        patient_info = parsed.get("patient", {})

        target_ref = override_patient_ref or patient_info.get("patient_ref") or f"FHIR-{uuid.uuid4().hex[:8].upper()}"

        # Check if profile already exists for this tenant
        stmt = select(PatientProfile).where(
            PatientProfile.tenant_id == doctor.tenant_id,
            PatientProfile.patient_ref == target_ref
        )
        existing = await db.scalar(stmt)

        # Assemble baseline conditions and medications
        conditions_list = [c["name"] for c in parsed.get("conditions", [])]
        medications_list = [m["name"] for m in parsed.get("medications", [])]
        allergies_list = [a["substance"] for a in parsed.get("allergies", [])]

        # Extract vitals and kidney labs
        vitals_dict: Dict[str, Any] = {}
        for obs in parsed.get("observations", []):
            if "components" in obs:
                for k, v in obs["components"].items():
                    vitals_dict[k] = v
            elif "name" in obs and "value" in obs:
                vitals_dict[obs["name"]] = f"{obs['value']} {obs.get('unit', '')}".strip()

        age_val = patient_info.get("age")
        age_group = "adult"
        if age_val is not None:
            if age_val < 18:
                age_group = "pediatric"
            elif age_val >= 65:
                age_group = "geriatric"

        bio_sex = patient_info.get("biological_sex", "unknown")

        baseline_data = {
            "source": "HL7_FHIR_R4_IMPORT",
            "imported_at": datetime.utcnow().isoformat(),
            "conditions": conditions_list,
            "current_medications": medications_list,
            "allergies": allergies_list,
            "vitals": vitals_dict,
            "fhir_conditions_detail": parsed.get("conditions", []),
            "fhir_medications_detail": parsed.get("medications", []),
            "fhir_observations_detail": parsed.get("observations", []),
        }

        if existing:
            # Merge into existing profile
            existing.biological_sex = bio_sex
            existing.age_group = age_group
            curr_baseline = existing.baseline_conditions or {}
            curr_baseline.update(baseline_data)
            existing.baseline_conditions = curr_baseline
            profile = existing
        else:
            profile = PatientProfile(
                tenant_id=doctor.tenant_id,
                patient_ref=target_ref,
                biological_sex=bio_sex,
                age_group=age_group,
                baseline_conditions=baseline_data,
            )
            db.add(profile)

        await db.commit()
        await db.refresh(profile)

        summary = {
            "patient_profile_id": str(profile.id),
            "patient_ref": profile.patient_ref,
            "biological_sex": profile.biological_sex,
            "age_group": profile.age_group,
            "conditions_imported": len(conditions_list),
            "medications_imported": len(medications_list),
            "observations_imported": len(parsed.get("observations", [])),
            "allergies_imported": len(allergies_list),
            "fhir_version": "R4",
            "status": "SUCCESS"
        }

        log.info("fhir_bundle_imported", **summary)
        return profile, summary


fhir_ingestion_service = FhirIngestionService()
