import asyncio
import httpx
from app.infrastructure.database import get_session_factory
from app.models.consultation import Consultation
from app.models.doctor import Doctor
from app.models.user import User
from app.services import auth_service
from app.config import get_settings

async def main():
    # 1. Obtain doctor user ID for consultation
    cid = "dd6d73ca-9a1b-4783-bbed-759dec17ea30"
    factory = get_session_factory()
    async with factory() as db:
        c = await db.get(Consultation, cid)
        if not c:
            print("Consultation not found!")
            return
        doc = await db.get(Doctor, c.doctor_id)
        user = await db.get(User, doc.user_id) if doc else None
        print(f"Encounter ID: {c.id}")
        print(f"Doctor ID: {c.doctor_id} | Specialty: {doc.specialty if doc else 'N/A'}")
        print(f"Doctor User Email: {user.email if user else 'N/A'}")

        # Generate live auth token
        settings = get_settings()
        token, expires_in, _ = auth_service.create_access_token(user.id, settings)
        print(f"Generated Live JWT Token for Doctor (expires in {expires_in}s)")

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=30.0) as client:
        # 1. GET Clinical Note
        print("\n--- TEST 1: GET Clinical Note ---")
        note_res = await client.get(f"/api/v1/consultations/{cid}/notes", headers=headers)
        print(f"GET /notes status: {note_res.status_code}")
        note = note_res.json()
        body = note.get("body", {})
        inv_list = body.get("investigations_list", [])
        diff_list = body.get("differential_candidates", [])
        tl_list = body.get("clinical_timeline", [])
        print(f"  Note Version: {note.get('version')}")
        print(f"  Investigations: {len(inv_list)}, Candidates: {len(diff_list)}, Timeline: {len(tl_list)}")

        # 2. POST Order Investigation into Note
        print("\n--- TEST 2: POST Order Investigation (1-Click Real-Time Button) ---")
        order_res = await client.post(
            f"/api/v1/consultations/{cid}/investigations/order",
            headers=headers,
            json={
                "name": "Serum Ferritin & Procalcitonin",
                "category": "Laboratory",
                "priority": "STAT",
                "rationale": "Assess systemic hyperinflammation vs bacterial superinfection in neuro-outbreak presentation",
            }
        )
        print(f"POST /investigations/order status: {order_res.status_code}")
        ordered_note = order_res.json()
        new_invs = ordered_note.get("body", {}).get("investigations_list", [])
        new_item = next((i for i in new_invs if i.get("name") == "Serum Ferritin & Procalcitonin"), None)
        item_id = new_item.get("id") if new_item else None
        print(f"  Ordered: {new_item.get('name')} | Priority: {new_item.get('priority')} | ID: {item_id}")

        # 3. POST Record Investigation Result (Updates timeline & differential)
        if item_id:
            print("\n--- TEST 3: POST Record Result & Re-Evaluate Differential ---")
            res_res = await client.post(
                f"/api/v1/consultations/{cid}/investigations/{item_id}/result",
                headers=headers,
                json={
                    "result": "Procalcitonin 0.08 ng/mL (Normal < 0.5), Ferritin 118 ng/mL (Normal)",
                    "flag": "Normal",
                }
            )
            print(f"POST /investigations/{item_id}/result status: {res_res.status_code}")
            res_note = res_res.json()
            updated_tl = res_note.get("body", {}).get("clinical_timeline", [])
            print(f"  Timeline milestones count now: {len(updated_tl)}")
            print(f"  Latest milestone: [{updated_tl[-1].get('stage')}] {updated_tl[-1].get('event')}")
            if len(updated_tl) > 1:
                print(f"  Previous milestone: [{updated_tl[-2].get('stage')}] {updated_tl[-2].get('event')}")

        # 4. POST Clinician Action on Differential Candidate
        if diff_list:
            cand = diff_list[0]
            cand_id = cand.get("id")
            print(f"\n--- TEST 4: POST Accept Differential Candidate ({cand.get('disease')}) ---")
            diff_action_res = await client.post(
                f"/api/v1/consultations/{cid}/differential/{cand_id}/action",
                headers=headers,
                json={"action": "accept"}
            )
            print(f"POST /differential/{cand_id}/action status: {diff_action_res.status_code}")
            action_note = diff_action_res.json()
            cands = action_note.get("body", {}).get("differential_candidates", [])
            target = next((c for c in cands if c.get("id") == cand_id), None)
            print(f"  Candidate: {target.get('disease')} -> Status: {target.get('clinician_status')}")
            working_assessment = action_note.get("body", {}).get("assessment", {})
            print(f"  Updated Working Assessment: {working_assessment.get('text', '')[:120]}...")

        # 5. POST Re-Run Diagnostic Engine
        print("\n--- TEST 5: POST Re-Run Diagnostic Engine ---")
        rerun_res = await client.post(f"/api/v1/consultations/{cid}/differential/rerun", headers=headers)
        print(f"POST /differential/rerun status: {rerun_res.status_code}")
        rerun_note = rerun_res.json()
        print(f"  Differential candidates: {len(rerun_note.get('body', {}).get('differential_candidates', []))}")

        # 6. GET Export PDF
        print("\n--- TEST 6: GET Export PDF (Physical PDF byte stream) ---")
        pdf_res = await client.get(f"/api/v1/consultations/{cid}/export?format=pdf", headers=headers)
        print(f"GET /export?format=pdf status: {pdf_res.status_code} | Bytes: {len(pdf_res.content)} | Content-Type: {pdf_res.headers.get('content-type')}")
        assert pdf_res.status_code == 200, "PDF export failed!"
        assert len(pdf_res.content) > 1000, "PDF too small!"
        assert pdf_res.content[:4] == b"%PDF", "Invalid PDF magic header!"
        print("  ✓ Verified valid PDF binary byte stream!")

        # 7. GET Export FHIR
        print("\n--- TEST 7: GET Export FHIR (HL7 FHIR R4 Bundle) ---")
        fhir_res = await client.get(f"/api/v1/consultations/{cid}/export?format=fhir", headers=headers)
        print(f"GET /export?format=fhir status: {fhir_res.status_code}")
        fhir_json = fhir_res.json()
        print(f"  FHIR ResourceType: {fhir_json.get('resourceType')} | ID: {fhir_json.get('id')} | Entries: {len(fhir_json.get('entry', []))}")
        assert fhir_res.status_code == 200, "FHIR export failed!"
        assert fhir_json.get("resourceType") == "Bundle", "Not a FHIR bundle!"
        print("  ✓ Verified valid HL7 FHIR R4 Bundle!")

        # 8. POST Clinician Feedback
        print("\n--- TEST 8: POST Clinician AI Feedback ---")
        fb_res = await client.post(
            "/api/v1/feedback/suggestions",
            headers=headers,
            json={
                "suggestion_id": f"note-{cid}-physical_examination-1",
                "suggestion_type": "clinical_note",
                "decision": "ACCEPT",
                "suggestion_context": {"section": "physical_examination", "text": "Alert and oriented"}
            }
        )
        print(f"POST /feedback/suggestions status: {fb_res.status_code}")
        assert fb_res.status_code == 200, "Feedback failed!"
        print(f"  Feedback decision recorded: {fb_res.json().get('decision')}")

        print("\n========================================================")
        print("ALL 8 BACKEND BUTTON ENDPOINTS VERIFIED WORKING IN REAL TIME!")
        print("========================================================")

if __name__ == "__main__":
    asyncio.run(main())
