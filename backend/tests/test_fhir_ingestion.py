"""DocAssistIQ — Automated Verification Tests for HL7 FHIR R4 Inbound Ingestion.

Tests:
1. Valid FHIR R4 Bundle parsing (Patient, Conditions with ICD-10, Observations with LOINC,
   Medications with RxNorm, and Allergies).
2. Calculation of patient age from birthDate.
3. Multi-component observation parsing (e.g. systolic & diastolic blood pressure).
4. Error handling for non-bundle and malformed FHIR payloads.
"""

import pytest
from app.services.fhir_ingestion_service import fhir_ingestion_service, FhirIngestionService


@pytest.fixture
def sample_hospital_fhir_bundle():
    """Realistic hospital FHIR R4 Bundle containing EHR records."""
    return {
        "resourceType": "Bundle",
        "id": "bundle-ehr-example-001",
        "type": "collection",
        "entry": [
            {
                "fullUrl": "urn:uuid:patient-001",
                "resource": {
                    "resourceType": "Patient",
                    "id": "patient-001",
                    "identifier": [{"system": "urn:mrn", "value": "MRN-987654"}],
                    "gender": "female",
                    "birthDate": "1958-06-20"
                }
            },
            {
                "fullUrl": "urn:uuid:cond-001",
                "resource": {
                    "resourceType": "Condition",
                    "id": "cond-001",
                    "clinicalStatus": {
                        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
                    },
                    "code": {
                        "coding": [
                            {"system": "http://hl7.org/fhir/sid/icd-10", "code": "E11.9", "display": "Type 2 diabetes mellitus"},
                            {"system": "http://snomed.info/sct", "code": "44054006", "display": "Type 2 diabetes mellitus"}
                        ],
                        "text": "Type 2 diabetes mellitus"
                    },
                    "onsetDateTime": "2015-04-10"
                }
            },
            {
                "fullUrl": "urn:uuid:cond-002",
                "resource": {
                    "resourceType": "Condition",
                    "id": "cond-002",
                    "clinicalStatus": {
                        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
                    },
                    "code": {
                        "coding": [
                            {"system": "http://hl7.org/fhir/sid/icd-10", "code": "I10", "display": "Essential (primary) hypertension"}
                        ],
                        "text": "Essential Hypertension"
                    }
                }
            },
            {
                "fullUrl": "urn:uuid:obs-bp-001",
                "resource": {
                    "resourceType": "Observation",
                    "id": "obs-bp-001",
                    "status": "final",
                    "code": {
                        "coding": [{"system": "http://loinc.org", "code": "85354-9", "display": "Blood Pressure Panel"}],
                        "text": "Blood Pressure Panel"
                    },
                    "component": [
                        {
                            "code": {"coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic Blood Pressure"}]},
                            "valueQuantity": {"value": 138, "unit": "mmHg"}
                        },
                        {
                            "code": {"coding": [{"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic Blood Pressure"}]},
                            "valueQuantity": {"value": 84, "unit": "mmHg"}
                        }
                    ]
                }
            },
            {
                "fullUrl": "urn:uuid:obs-creatinine-001",
                "resource": {
                    "resourceType": "Observation",
                    "id": "obs-creatinine-001",
                    "status": "final",
                    "code": {
                        "coding": [{"system": "http://loinc.org", "code": "2160-0", "display": "Creatinine [Mass/volume] in Serum"}]
                    },
                    "valueQuantity": {"value": 1.85, "unit": "mg/dL"}
                }
            },
            {
                "fullUrl": "urn:uuid:obs-egfr-001",
                "resource": {
                    "resourceType": "Observation",
                    "id": "obs-egfr-001",
                    "status": "final",
                    "code": {
                        "coding": [{"system": "http://loinc.org", "code": "33914-3", "display": "eGFR"}]
                    },
                    "valueQuantity": {"value": 28.0, "unit": "mL/min"}
                }
            },
            {
                "fullUrl": "urn:uuid:med-001",
                "resource": {
                    "resourceType": "MedicationStatement",
                    "id": "med-001",
                    "status": "active",
                    "medicationCodeableConcept": {
                        "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "6809", "display": "Metformin 1000 MG Oral Tablet"}],
                        "text": "Metformin 1000mg"
                    },
                    "dosageInstruction": [{"text": "1000mg twice daily with meals"}]
                }
            },
            {
                "fullUrl": "urn:uuid:allergy-001",
                "resource": {
                    "resourceType": "AllergyIntolerance",
                    "id": "allergy-001",
                    "criticality": "high",
                    "code": {
                        "coding": [{"system": "http://snomed.info/sct", "code": "70618001", "display": "Penicillin"}],
                        "text": "Penicillin"
                    }
                }
            }
        ]
    }


def test_fhir_bundle_parsing_extracts_all_entities(sample_hospital_fhir_bundle):
    """Test that FHIR R4 bundle parser extracts patient, conditions, vitals, meds, and allergies."""
    parsed = fhir_ingestion_service.parse_bundle(sample_hospital_fhir_bundle)

    # Patient assertions
    assert parsed["patient"]["biological_sex"] == "female"
    assert parsed["patient"]["patient_ref"] == "MRN-987654"
    assert parsed["patient"]["age"] is not None
    assert parsed["patient"]["age"] >= 65  # Born 1958

    # Condition assertions
    assert len(parsed["conditions"]) == 2
    cond_names = [c["name"] for c in parsed["conditions"]]
    assert "Type 2 diabetes mellitus" in cond_names
    assert "Essential Hypertension" in cond_names
    # Check ICD-10 code extraction
    dm_cond = next(c for c in parsed["conditions"] if "diabetes" in c["name"].lower())
    assert dm_cond["icd10"] == "E11.9"

    # Observation assertions
    assert len(parsed["observations"]) == 3
    # Check multi-component blood pressure
    bp_obs = next(o for o in parsed["observations"] if "Blood Pressure" in o.get("name", ""))
    assert bp_obs["components"]["Systolic Blood Pressure"] == 138
    assert bp_obs["components"]["Diastolic Blood Pressure"] == 84

    # Check lab values
    creat_obs = next(o for o in parsed["observations"] if o.get("loinc") == "2160-0")
    assert creat_obs["value"] == 1.85
    assert creat_obs["unit"] == "mg/dL"

    egfr_obs = next(o for o in parsed["observations"] if o.get("loinc") == "33914-3")
    assert egfr_obs["value"] == 28.0

    # Medication assertions
    assert len(parsed["medications"]) == 1
    med = parsed["medications"][0]
    assert "Metformin" in med["name"]
    assert med["rxnorm"] == "6809"
    assert med["dosage"] == "1000mg twice daily with meals"

    # Allergy assertions
    assert len(parsed["allergies"]) == 1
    allergy = parsed["allergies"][0]
    assert allergy["substance"] == "Penicillin"
    assert allergy["criticality"] == "high"


def test_fhir_bundle_invalid_payload_raises_error():
    """Verify that malformed or non-bundle payloads raise informative ValueError."""
    with pytest.raises(ValueError, match="Expected FHIR resourceType 'Bundle'"):
        fhir_ingestion_service.parse_bundle({"resourceType": "Patient"})

    with pytest.raises(ValueError, match="Invalid FHIR payload"):
        fhir_ingestion_service.parse_bundle("not-a-dict")  # type: ignore
