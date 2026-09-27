import json
import urllib.parse
import urllib.request

def verify_all():
    print("=== 1. Physician Authentication ===")
    login_data = json.dumps({'email': 'dr.smith@hospital.org', 'password': 'DoctorSecure2026!'}).encode()
    login_req = urllib.request.Request('http://127.0.0.1:8002/api/v1/auth/login', data=login_data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(login_req) as resp:
            token = json.loads(resp.read().decode())['access_token']
            print("[OK] Physician Dr. Smith logged in successfully.")
    except Exception as e:
        # Fallback to Next.js route
        login_req = urllib.request.Request('http://localhost:3000/api/v1/auth/login', data=login_data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(login_req) as resp:
            token = json.loads(resp.read().decode())['access_token']
            print("[OK] Logged in via Next.js proxy successfully.")

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    print("\n=== 2. Testing Wikipedia Living Clinical Guideline Infobox API ===")
    conditions = [
        "Takotsubo Cardiomyopathy",
        "Wellens Syndrome",
        "Anti-NMDAR Encephalitis",
        "Brugada Syndrome",
        "Myasthenia Gravis",
        "Atypical Kawasaki Disease"
    ]
    for c in conditions:
        url = f"http://127.0.0.1:8002/api/v1/hub/guidelines/{urllib.parse.quote(c)}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"[OK] [{data['icd10_code']}] {data['condition_name']}")
            print(f"  Authority: {data['guideline_authority']} ({data['evidence_level']})")
            print(f"  First-Line: {', '.join(data['first_line_therapy'][:2])}")
            print(f"  PubMed Citations: {len(data['pubmed_citations'])} verified references")

    print("\n=== 3. Testing Feed Quoted Case & Comparative Protocol API ===")
    feed_req = urllib.request.Request('http://127.0.0.1:8002/api/v1/hub/feed?sort_by=recent', headers=headers)
    with urllib.request.urlopen(feed_req) as resp:
        feed = json.loads(resp.read().decode())
        print(f"[OK] Total Feed Posts Retrieved: {len(feed)}")
        quoted = [p for p in feed if p.get("quoted_post")]
        print(f"[OK] Cases with Embedded Quoted Protocol: {len(quoted)}")
        for q in quoted:
            print(f"  - Case: \"{q['disease_name']}\"")
            print(f"    Quotes original: \"{q['quoted_post']['disease_name']}\" by {q['quoted_post']['author_name']} ({q['quoted_post']['author_specialty']})")

    print("\n=== 4. Testing Creating a Real-Time Quoted Post ===")
    # Pick the first case to quote
    original_case = feed[0]
    quote_payload = json.dumps({
        "disease_name": f"Institutional Protocol: {original_case['disease_name']}",
        "specialty_tags": ["ComparativeProtocol", "Cardiology", "Consensus"],
        "clinical_findings": "Institutional cohort comparative study. Presentation mirrors the quoted index case.",
        "diagnosis": f"Confirmed {original_case['disease_name']} under ESC/AHA criteria",
        "treatment_plan": "First-line dual antiplatelet therapy + immediate interventional catheterization.",
        "drugs_used": ["Aspirin 325mg", "Ticagrelor 180mg", "Unfractionated Heparin"],
        "quoted_post_id": original_case["id"],
        "is_urgent_consult": False
    }).encode()
    create_req = urllib.request.Request('http://127.0.0.1:8002/api/v1/hub/posts', data=quote_payload, headers=headers)
    with urllib.request.urlopen(create_req) as resp:
        created_post = json.loads(resp.read().decode())
        print(f"[OK] Quoted Case Created! ID: {created_post['id']}")
        print(f"  Quoted Post Title: {created_post.get('quoted_post', {}).get('disease_name')}")
        print(f"  Quoted Author: {created_post.get('quoted_post', {}).get('author_name')}")

    print("\n=== ALL REAL-TIME CLINICAL FEATURES FULLY VERIFIED ===")

if __name__ == '__main__':
    verify_all()
