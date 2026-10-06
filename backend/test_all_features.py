import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import json
import time

consultation_id = '06d9f1de-0b8b-4bdd-bdf0-2345c8a7fa7b'

def test_query(label, payload):
    t0 = time.time()
    req = urllib.request.Request(
        'http://localhost:8000/api/v1/ai/ask',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            dt = (time.time() - t0) * 1000
            print(f"=== {label} ({dt:.1f}ms) ===")
            ans = data.get('answer', '')
            print(ans[:280] + ('...' if len(ans) > 280 else ''))
            print("Source Evidence:", data.get('source_evidence', 'N/A'))
            if data.get('generated_document'):
                doc = data['generated_document']
                print(f"DOCUMENT GENERATED:")
                print(f"  Title: {doc.get('title')}")
                print(f"  Type:  {doc.get('document_type')}")
                print(f"  Cert:  SHA-256 {doc.get('integrity_hash', '')[:24]}...")
                print(f"  Downloads: {data.get('download_urls')}")
            print("-" * 60)
            return data
    except Exception as e:
        print(f"=== {label} FAILED: {e} ===")
        print("-" * 60)
        return None

def test_download(label, url):
    try:
        req = urllib.request.Request(f"http://localhost:8000{url}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            print(f"DOWNLOAD OK: {label} -> {len(content)} bytes, Content-Type: {resp.headers.get('Content-Type')}")
    except Exception as e:
        print(f"DOWNLOAD FAILED: {label} -> {e}")

if __name__ == '__main__':
    print("1. Testing Health Ping...")
    with urllib.request.urlopen('http://localhost:8000/api/v1/ping') as r:
        print("Ping Status:", r.read().decode('utf-8'))
    print("=" * 60)

    print("\n2. Conversational Queries (Real-Time Executive Assistant):")
    test_query('Greeting', {'question': 'Hello'})
    test_query('Capabilities', {'question': 'What can you do?'})
    test_query('Identity', {'question': 'Who are you?'})

    print("\n3. Real-Time Disease Knowledge Base (225+ Conditions & Emergencies):")
    test_query('Dengue Symptoms', {'question': 'symptoms of dengue'})
    test_query('DKA Emergency Protocol', {'question': 'how to treat diabetic ketoacidosis'})
    test_query('Stroke Protocol', {'question': 'acute ischemic stroke protocol'})

    print("\n4. Evidence-Based Clinical Calculators:")
    test_query('BMI Calculator', {'question': 'calculate bmi height 175 weight 70'})
    test_query('MAP Calculator', {'question': 'calculate MAP blood pressure 130 85'})
    test_query('Normal Vitals Reference', {'question': 'normal vitals'})

    print("\n5. Grounded Consultation & Certified Document Generation:")
    # Asking about active patient demographics and findings
    test_query('Patient Age & Summary', {'consultation_id': consultation_id, 'question': 'what is the age of this patient?'})
    
    # Document generations
    res_op = test_query('Operative Note', {'consultation_id': consultation_id, 'question': 'generate operative note'})
    res_triage = test_query('Emergency Triage', {'consultation_id': consultation_id, 'question': 'generate emergency triage'})
    res_rad = test_query('Radiology Order', {'consultation_id': consultation_id, 'question': 'generate radiology order'})
    res_custom = test_query('Sports Clearance Certificate', {'consultation_id': consultation_id, 'question': 'generate sports clearance certificate'})

    print("\n6. Binary PDF and DOCX Downloads:")
    if res_op and res_op.get('download_urls'):
        urls = res_op['download_urls']
        if urls.get('pdf'):
            test_download('Operative Note PDF', urls['pdf'])
        if urls.get('docx'):
            test_download('Operative Note DOCX', urls['docx'])
    
    if res_custom and res_custom.get('download_urls'):
        urls = res_custom['download_urls']
        if urls.get('pdf'):
            test_download('Sports Clearance PDF', urls['pdf'])
