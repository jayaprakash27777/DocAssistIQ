import uuid
import asyncio
import httpx
from app.main import app
from app.infrastructure.database import get_session_factory
from sqlalchemy import text

async def run_linkage_verification():
    uid = uuid.uuid4().hex[:6]
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Register and login a doctor
        reg_payload = {
            "email": f"link_tester_{uid}@hospital.org",
            "password": "Password123!",
            "full_name": f"Dr. Link Tester {uid}",
            "role": "doctor"
        }
        await client.post("/api/v1/auth/register", json=reg_payload)
        r_login = await client.post("/api/v1/auth/login", json={"email": reg_payload["email"], "password": reg_payload["password"]})
        assert r_login.status_code == 200, f"Login failed: {r_login.text}"
        token = r_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create a Patient Profile
        patient_ref_code = f"PT-VERIFY-{uid.upper()}"
        p_res = await client.post(
            "/api/v1/patients/",
            headers=headers,
            json={
                "patient_ref": patient_ref_code,
                "age_group": "45-54",
                "biological_sex": "Female",
                "baseline_conditions": {"chronic_conditions": ["Type 2 Diabetes", "Hypertension"], "allergies": ["Penicillin"]}
            }
        )
        assert p_res.status_code in (200, 201), f"Create patient failed: {p_res.text}"
        patient_data = p_res.json()
        patient_id = patient_data["id"]
        print(f"[TEST 1] Created Patient Profile: {patient_data['patient_ref']} (ID: {patient_id})")

        # 2. Create a Consultation linked to this patient_id
        c_res = await client.post(
            "/api/v1/consultations",
            headers=headers,
            json={
                "patient_id": patient_id,
                "input_text": f"Patient {patient_ref_code} presents with 3-day history of productive cough, fever of 38.6C, and pleuritic chest discomfort."
            }
        )
        assert c_res.status_code == 201, f"Create consultation failed: {c_res.text}"
        consultation = c_res.json()
        print(f"[TEST 2] Created Consultation: ID={consultation['id']}")
        print(f"         Linked patient_id: {consultation.get('patient_id')}")
        print(f"         Linked patient_ref: {consultation.get('patient_ref')}")
        print(f"         Linked patient_demographics: {consultation.get('patient_demographics')}")
        assert str(consultation.get("patient_id")) == str(patient_id), "patient_id mismatch!"
        assert consultation.get("patient_ref") == patient_ref_code, "patient_ref mismatch!"

        # 3. Verify List Consultations includes patient linkage
        list_res = await client.get("/api/v1/consultations", headers=headers)
        assert list_res.status_code == 200, f"List consultations failed: {list_res.text}"
        items = list_res.json()
        if isinstance(items, dict) and "items" in items:
            items = items["items"]
        matching = [item for item in items if str(item.get("id")) == str(consultation["id"])]
        assert len(matching) == 1, "Created consultation not found in list!"
        print(f"[TEST 3] Verified in List Consultations: patient_ref={matching[0].get('patient_ref')}")

        # 4. Verify Patient Profile includes the session and consultation_id
        p_get = await client.get(f"/api/v1/patients/{patient_id}", headers=headers)
        assert p_get.status_code == 200, f"Get patient profile failed: {p_get.text}"
        p_details = p_get.json()
        assert len(p_details["sessions"]) >= 1, "Patient sessions empty!"
        session = p_details["sessions"][0]
        print(f"[TEST 4] Verified in Patient Profile: sessions count={len(p_details['sessions'])}")
        print(f"         Session ID: {session['id']}")
        print(f"         Session consultation_id: {session.get('consultation_id')}")
        assert str(session.get("consultation_id")) == str(consultation["id"]), "Session consultation_id mismatch!"

        print("\n" + "="*60)
        print("  PATIENT MANAGEMENT <-> CONSULTATION LINKAGE 100% VERIFIED")
        print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(run_linkage_verification())
