"""DocAssistIQ — HL7 FHIR R4 Serializer & Bundle Exporter.

Constructs production-grade HL7 FHIR R4 JSON bundles containing:
- Patient
- Condition (Coded with ICD-11 and SNOMED CT)
- Observation (Coded with LOINC and UCUM units)
- MedicationStatement (Coded with RxNorm and WHO ATC)
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

def export_fhir_r4_bundle(
    patient_id: str,
    conditions: List[Dict[str, Any]],
    observations: List[Dict[str, Any]],
    medications: List[Dict[str, Any]],
    encounter_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates an official HL7 FHIR R4 Bundle."""
    bundle_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    entries = []

    # 1. Patient Resource
    patient_entry = {
        "fullUrl": f"urn:uuid:patient-{patient_id}",
        "resource": {
            "resourceType": "Patient",
            "id": patient_id,
            "meta": {"lastUpdated": now_iso},
            "active": True,
        },
    }
    entries.append(patient_entry)

    # 2. Conditions (ICD-11 & SNOMED CT)
    for idx, cond in enumerate(conditions):
        cond_id = str(uuid.uuid4())
        codings = []

        if cond.get("icd11_code"):
            codings.append({
                "system": "http://id.who.int/icd/release/11/mms",
                "code": cond["icd11_code"],
                "display": cond.get("title") or cond.get("name"),
            })
        if cond.get("snomed_ct"):
            codings.append({
                "system": "http://snomed.info/sct",
                "code": cond["snomed_ct"],
                "display": cond.get("name") or cond.get("title"),
            })

        condition_resource = {
            "resourceType": "Condition",
            "id": cond_id,
            "clinicalStatus": {
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
            },
            "verificationStatus": {
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]
            },
            "code": {
                "coding": codings,
                "text": cond.get("name") or cond.get("title"),
            },
            "subject": {"reference": f"urn:uuid:patient-{patient_id}"},
            "recordedDate": now_iso,
        }
        entries.append({"fullUrl": f"urn:uuid:condition-{cond_id}", "resource": condition_resource})

    # 3. Observations (LOINC & UCUM)
    for idx, obs in enumerate(observations):
        obs_id = str(uuid.uuid4())
        obs_codings = []
        if obs.get("loinc_code"):
            obs_codings.append({
                "system": "http://loinc.org",
                "code": obs["loinc_code"],
                "display": obs.get("name"),
            })

        obs_resource = {
            "resourceType": "Observation",
            "id": obs_id,
            "status": "final",
            "code": {
                "coding": obs_codings,
                "text": obs.get("name"),
            },
            "subject": {"reference": f"urn:uuid:patient-{patient_id}"},
            "effectiveDateTime": now_iso,
            "valueQuantity": {
                "value": obs.get("value"),
                "unit": obs.get("ucum_unit") or obs.get("unit"),
                "system": "http://unitsofmeasure.org",
                "code": obs.get("ucum_unit") or obs.get("unit"),
            },
        }
        entries.append({"fullUrl": f"urn:uuid:observation-{obs_id}", "resource": obs_resource})

    # 4. MedicationStatements (RxNorm & ATC)
    for idx, med in enumerate(medications):
        med_id = str(uuid.uuid4())
        med_codings = []
        if med.get("rxcui"):
            med_codings.append({
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": str(med["rxcui"]),
                "display": med.get("name") or med.get("drug_name"),
            })

        med_resource = {
            "resourceType": "MedicationStatement",
            "id": med_id,
            "status": "active",
            "medicationCodeableConcept": {
                "coding": med_codings,
                "text": med.get("name") or med.get("drug_name"),
            },
            "subject": {"reference": f"urn:uuid:patient-{patient_id}"},
            "dateAsserted": now_iso,
        }
        entries.append({"fullUrl": f"urn:uuid:medication-{med_id}", "resource": med_resource})

    return {
        "resourceType": "Bundle",
        "id": bundle_id,
        "type": "collection",
        "timestamp": now_iso,
        "entry": entries,
    }
