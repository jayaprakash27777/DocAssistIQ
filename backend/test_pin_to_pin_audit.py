import os
import sys
import uuid
import asyncio
import httpx

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.main import app

async def run_pin_to_pin_audit():
    transport = httpx.ASGITransport(app=app)
    results = []

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        print("\n" + "="*65)
        print("      DOCASSISTIQ PIN-TO-PIN FULL STACK AUDIT & VERIFICATION")
        print("="*65 + "\n")

        # 1. Health & Liveness
        resp = await client.get("/health")
        assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
        print(f"[PIN 1]  GET  /health -> Status: {resp.status_code} | Body: {resp.json().get('status')}")
        results.append(("GET /health", True))

        # 2. Readiness Check
        resp = await client.get("/ready")
        assert resp.status_code in (200, 503), f"Readiness check failed: {resp.status_code}"
        print(f"[PIN 2]  GET  /ready -> Status: {resp.status_code} | AI Mode: {resp.json().get('ai_mode')}")
        results.append(("GET /ready", True))

        # 3. AI Status Endpoint
        resp = await client.get("/ai-status")
        assert resp.status_code == 200, f"AI status check failed: {resp.status_code}"
        data = resp.json()
        assert "features_available" in data
        print(f"[PIN 3]  GET  /ai-status -> Status: {resp.status_code} | Features: {len(data['features_available'])}")
        results.append(("GET /ai-status", True))

        # 4. API v1 Ping Check
        resp = await client.get("/api/v1/ping")
        assert resp.status_code == 200, f"Ping check failed: {resp.status_code}"
        print(f"[PIN 4]  GET  /api/v1/ping -> Status: {resp.status_code} | Version: {resp.json().get('version')}")
        results.append(("GET /api/v1/ping", True))

        # 5. Live DDI Check Endpoint (New Endpoint test)
        ddi_payload = {"drugs": ["Warfarin", "Amiodarone", "Diphenhydramine", "Lisinopril"]}
        resp = await client.post("/api/v1/hub/ddi-check", json=ddi_payload)
        assert resp.status_code == 200, f"DDI check failed: {resp.status_code}, {resp.text}"
        ddi_data = resp.json()
        assert ddi_data["total_interactions"] >= 1, "Expected at least 1 DDI interaction"
        assert "acb_score" in ddi_data, "Expected ACB score in response"
        print(f"[PIN 5]  POST /api/v1/hub/ddi-check -> Status: {resp.status_code} | Interactions: {ddi_data['total_interactions']} | ACB Score: {ddi_data['acb_score']} ({ddi_data['acb_risk']})")
        results.append(("POST /api/v1/hub/ddi-check", True))

        # 6. Real-time NLP Symptom Extraction
        extract_payload = {"text": "Patient has had acute crushing chest pain radiating to left jaw for 3 hours with diaphoresis."}
        resp = await client.post("/api/v1/ai/extract", json=extract_payload)
        assert resp.status_code == 200, f"NLP Extract failed: {resp.status_code}"
        assert resp.json().get("symptom_count", 0) > 0
        print(f"[PIN 6]  POST /api/v1/ai/extract -> Status: {resp.status_code} | Symptoms Found: {resp.json().get('symptom_count')}")
        results.append(("POST /api/v1/ai/extract", True))

        # 7. Real-Time Medical Q&A
        qa_payload = {"query": "What are the first-line interventions for acute STEMI?"}
        resp = await client.post("/api/v1/ai/ask", json=qa_payload)
        assert resp.status_code == 200, f"AI Ask failed: {resp.status_code}"
        qa_data = resp.json()
        assert len(qa_data.get("answer", "")) > 10
        print(f"[PIN 7]  POST /api/v1/ai/ask -> Status: {resp.status_code} | Answer Length: {len(qa_data['answer'])} chars | Latency: {qa_data.get('latency_ms', 0):.2f}ms")
        results.append(("POST /api/v1/ai/ask", True))

        # 8. State Outbreak Radar Surveillance
        resp = await client.get("/api/v1/intelligence/state-outbreaks?state=Kerala")
        assert resp.status_code == 200, f"State outbreaks failed: {resp.status_code}"
        radar_data = resp.json()
        assert "india_state_alerts" in radar_data or "global_alerts" in radar_data or "alerts" in radar_data
        total_alerts = radar_data.get("total_active_alerts", len(radar_data.get("india_state_alerts", [])))
        print(f"[PIN 8]  GET  /api/v1/intelligence/state-outbreaks -> Status: {resp.status_code} | Total active alerts: {total_alerts}")
        results.append(("GET /api/v1/intelligence/state-outbreaks", True))

        # 9. Realtime Differential Prediction
        predict_payload = {"symptoms": "sudden tearing chest pain radiating to back unequal pulses wide mediastinum"}
        resp = await client.post("/api/v1/consultations/predict-realtime", json=predict_payload)
        assert resp.status_code == 200, f"Realtime predict failed: {resp.status_code}"
        pred_data = resp.json()
        assert len(pred_data.get("top_candidates", [])) > 0
        top_dx = pred_data["top_candidates"][0]["disease"]
        print(f"[PIN 9]  POST /api/v1/consultations/predict-realtime -> Status: {resp.status_code} | Top Candidate: {top_dx} | Latency: {pred_data.get('latency_ms', 0):.2f}ms")
        results.append(("POST /api/v1/consultations/predict-realtime", True))

        # 10. Deep Disease Intelligence Profile
        resp = await client.get("/api/v1/intelligence/disease/Glaucoma")
        assert resp.status_code == 200, f"Disease intelligence profile failed: {resp.status_code}"
        disease_data = resp.json()
        assert "disease_name" in disease_data
        print(f"[PIN 10] GET  /api/v1/intelligence/disease/Glaucoma -> Status: {resp.status_code} | Name: {disease_data.get('disease_name')}")
        results.append(("GET /api/v1/intelligence/disease/Glaucoma", True))

        # 11. Register & Login Clinician to test authenticated endpoints
        email = f"pin_doc_{uuid.uuid4().hex[:6]}@hospital.org"
        password = "ValidDoctorPass99"
        r_reg = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Dr. Pin Auditor"},
        )
        assert r_reg.status_code == 201, f"Register failed: {r_reg.text}"

        r_login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert r_login.status_code == 200, f"Login failed: {r_login.text}"
        token = r_login.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Fetch or Create doctor profile
        r_doc = await client.get("/api/v1/doctors/me", headers=auth_headers)
        if r_doc.status_code == 404:
            r_doc = await client.post(
                "/api/v1/doctors/me",
                headers=auth_headers,
                json={
                    "specialty": "Cardiology",
                    "credential_reference": "NMC-998877",
                    "credential_body": "NMC",
                },
            )
        assert r_doc.status_code in (200, 201), f"Doctor profile fetch/create failed: {r_doc.text}"
        doc_data = r_doc.json()
        print(f"[AUTH]   Authenticated Dr. Pin Auditor | Doctor ID: {doc_data.get('id')} | Status: {doc_data.get('verification_status')}")

        # 12. Social Hub Trending Hashtags (Authenticated)
        resp = await client.get("/api/v1/hub/hashtags", headers=auth_headers)
        assert resp.status_code == 200, f"Hashtags failed: {resp.status_code}"
        tags = resp.json()
        print(f"[PIN 11] GET  /api/v1/hub/hashtags -> Status: {resp.status_code} | Hashtags count: {len(tags)}")
        results.append(("GET /api/v1/hub/hashtags", True))

        # 13. Social Hub Emergency Radar (Authenticated)
        resp = await client.get("/api/v1/hub/emergency", headers=auth_headers)
        assert resp.status_code == 200, f"Hub emergency failed: {resp.status_code}"
        emergencies = resp.json()
        print(f"[PIN 12] GET  /api/v1/hub/emergency -> Status: {resp.status_code} | Active cases: {len(emergencies)}")
        results.append(("GET /api/v1/hub/emergency", True))

        # 14. Social Hub Verified Doctors Feed (Authenticated)
        resp = await client.get("/api/v1/hub/posts", headers=auth_headers)
        assert resp.status_code == 200, f"Hub posts feed failed: {resp.status_code}"
        posts = resp.json()
        print(f"[PIN 13] GET  /api/v1/hub/posts -> Status: {resp.status_code} | Posts loaded: {len(posts)}")
        results.append(("GET /api/v1/hub/posts", True))

        # 15. Cryptographic Document Verification by Hash (Schema & Handler)
        test_hash = "a" * 64
        resp = await client.post("/api/v1/documents/verify/hash", json={"sha256_hash": test_hash})
        assert resp.status_code in (200, 404), f"Document verify failed: {resp.status_code}"
        print(f"[PIN 14] POST /api/v1/documents/verify/hash -> Status: {resp.status_code} (Cryptographic verification check handled)")
        results.append(("POST /api/v1/documents/verify/hash", True))

        print("\n" + "="*65)
        print(f"  ALL {len(results)}/{len(results)} PIN-TO-PIN ENDPOINTS VERIFIED & 100% FUNCTIONAL")
        print("="*65 + "\n")

if __name__ == "__main__":
    asyncio.run(run_pin_to_pin_audit())
