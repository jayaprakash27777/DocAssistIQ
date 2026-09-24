import urllib.request, json, time

BASE = "http://127.0.0.1:8000"

def run_test():
    print("=== 1. CLINICAL LOGIN ===")
    login_req = urllib.request.Request(
        f"{BASE}/api/v1/auth/login",
        data=json.dumps({"email": "dr.smith@hospital.org", "password": "DoctorSecure2026!"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(login_req) as resp:
        token = json.loads(resp.read().decode())["access_token"]
        print("Login Success! Clinician JWT authenticated.", flush=True)

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print("\n=== 2. CREATE CONSULTATION ===", flush=True)
    cons_req = urllib.request.Request(
        f"{BASE}/api/v1/consultations",
        data=json.dumps({
            "input_text": "58-year-old male with history of hypertension presents with 2 hours of substernal crushing chest pain radiating to the left jaw and diaphoresis. BP 155/95, HR 102."
        }).encode(),
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(cons_req) as resp:
        cons = json.loads(resp.read().decode())
        cons_id = cons["id"]
        print(f"Consultation Created! ID: {cons_id}", flush=True)

    print("\n=== 3. TEST SIMILAR CASES (PGVECTOR 768) ===", flush=True)
    sim_req = urllib.request.Request(
        f"{BASE}/api/v1/consultations/{cons_id}/similar-cases?limit=3",
        headers=headers,
        method="GET"
    )
    t0 = time.time()
    with urllib.request.urlopen(sim_req) as resp:
        sim_data = json.loads(resp.read().decode())
        cases = sim_data.get("cases", [])
        print(f"Similar Cases retrieved in {time.time()-t0:.2f}s! Found: {len(cases)} historical matches", flush=True)
        for i, c in enumerate(cases[:2], 1):
            print(f"  Match {i}: ID={c['id']}, Presentation={c['clinical_presentation_summary'][:80]}...", flush=True)

    print("\n=== 4. TEST DIFFERENTIAL DIAGNOSIS ===", flush=True)
    diff_req = urllib.request.Request(
        f"{BASE}/api/v1/consultations/{cons_id}/differential?symptoms=chest_pain,diaphoresis,radiating_pain",
        headers=headers,
        method="GET"
    )
    t0 = time.time()
    with urllib.request.urlopen(diff_req, timeout=30) as resp:
        diff_data = json.loads(resp.read().decode())
        cands = diff_data.get("top_candidates", [])
        print(f"Differential Diagnosis generated in {time.time()-t0:.2f}s! Top candidates: {len(cands)}", flush=True)
        for i, d in enumerate(cands[:3], 1):
            print(f"  {i}. {d.get('disease')} (Clinical Score: {d.get('score', 0.0):.2f})", flush=True)

    print("\n=== 5. TEST RAG CLINICAL RETRIEVAL ===", flush=True)
    rag_req = urllib.request.Request(
        f"{BASE}/api/v1/rag/query",
        data=json.dumps({
            "query": "Immediate pharmacological management of acute ST-elevation myocardial infarction STEMI aspirin heparin",
            "top_k": 3,
            "filters": {"only_approved": False}
        }).encode(),
        headers=headers,
        method="POST"
    )
    t0 = time.time()
    with urllib.request.urlopen(rag_req, timeout=180) as resp:
        rag_data = json.loads(resp.read().decode())
        print(f"RAG Retrieval completed in {time.time()-t0:.2f}s!", flush=True)
        print(f"  Model: {rag_data.get('model_used')}", flush=True)
        print(f"  Answer preview: {rag_data.get('answer', '')[:120]}...", flush=True)
        print(f"  Citations: {len(rag_data.get('citations', []))}", flush=True)

    print("\n=== 6. TEST POLYPHARMACY SIMULATION ===", flush=True)
    poly_req = urllib.request.Request(
        f"{BASE}/api/v1/consultations/{cons_id}/polypharmacy-simulate",
        data=json.dumps({
            "proposed_medications": ["Aspirin", "Clopidogrel", "Metoprolol", "Lisinopril"],
            "current_medications": ["Amlodipine"]
        }).encode(),
        headers=headers,
        method="POST"
    )
    t0 = time.time()
    with urllib.request.urlopen(poly_req, timeout=180) as resp:
        poly_data = json.loads(resp.read().decode())
        print(f"Polypharmacy Simulation in {time.time()-t0:.2f}s!", flush=True)
        print(f"  Is safe: {poly_data.get('is_safe')}", flush=True)
        print(f"  Interactions detected: {len(poly_data.get('interactions', []))}", flush=True)
        for item in poly_data.get('interactions', []):
            print(f"    - {item.get('severity')}: {', '.join(item.get('drugs_involved', []))} ({item.get('mechanism')})", flush=True)

    print("\n=== 7. TEST TEACHING-HOSPITAL SOAP+ NOTE GENERATION (LLAMA 3.1 8B) ===", flush=True)
    note_req = urllib.request.Request(
        f"{BASE}/api/v1/consultations/{cons_id}/notes/generate",
        data=json.dumps({
            "transcript_text": "Doctor: Hello Mr. Davis. Can you describe the chest pain? Patient: Yes doctor, it started 2 hours ago while I was resting. It feels like an elephant sitting on my chest, crushing pain, and it goes up to my left jaw. I am also sweating profusely and nauseous."
        }).encode(),
        headers=headers,
        method="POST"
    )
    t0 = time.time()
    with urllib.request.urlopen(note_req, timeout=180) as resp:
        note_data = json.loads(resp.read().decode())
        body = note_data.get("body", {})
        print(f"SOAP+ Note Generated in {time.time()-t0:.2f}s!")
        print(f"  Chief Complaint: {body.get('chief_complaint', {}).get('text')}")
        print(f"  HPI preview: {body.get('hpi', {}).get('text')[:100]}...")
        print(f"  Vitals: {body.get('vitals', {}).get('text')}")
        print(f"  Differential: {body.get('differential_diagnosis', {}).get('text')[:100]}...")
        print(f"  Safety Net: {body.get('safety_net', {}).get('text')[:100]}...")

    print("\n=== ALL CLINICAL AI SUITES OPERATIONAL AND VERIFIED ===")

if __name__ == "__main__":
    run_test()
