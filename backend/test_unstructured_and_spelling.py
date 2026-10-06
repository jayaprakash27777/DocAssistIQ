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
            print(ans[:320] + ('...' if len(ans) > 320 else ''))
            print("Source Evidence:", data.get('source_evidence', 'N/A'))
            if data.get('generated_document'):
                doc = data['generated_document']
                print(f"DOCUMENT GENERATED:")
                print(f"  Title: {doc.get('title')}")
                print(f"  Type:  {doc.get('document_type')}")
                print(f"  Cert:  SHA-256 {doc.get('integrity_hash', '')[:24]}...")
                print(f"  PDF URL:  {doc.get('pdf_download_url')}")
                print(f"  DOCX URL: {doc.get('docx_download_url')}")
            print("-" * 65)
            return data
    except Exception as e:
        print(f"=== {label} FAILED: {e} ===")
        print("-" * 65)
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
    print("=" * 65)
    print("DOCASSISTIQ 'GOD-LEVEL' SPELLING MISTAKES & UNSTRUCTURED TEXT TEST")
    print("=" * 65)

    print("\n1. SEVERE SPELLING MISTAKES & TYPOS IN MEDICAL QUESTIONS:")
    # Typhoid / Dengue / DKA / Stroke with misspellings
    test_query('Typo: Dengue Symptoms ("symptms of dengu")', {'question': 'symptms of dengu'})
    test_query('Typo: DKA Treatment ("how 2 treat dibetic ketoacidoss")', {'question': 'how 2 treat dibetic ketoacidoss'})
    test_query('Typo: Stroke Protocol ("strok treatmnt")', {'question': 'strok treatmnt'})

    print("\n2. SEVERE SPELLING MISTAKES IN CLINICAL CALCULATORS:")
    test_query('Typo: BMI ("calclate bmmi hight 175 weigt 70")', {'question': 'calclate bmmi hight 175 weigt 70'})
    test_query('Typo: MAP ("calclat map blod presure 130 85")', {'question': 'calclat map blod presure 130 85'})

    print("\n3. SEVERE SPELLING MISTAKES IN CLINICAL DOCUMENT DIRECTIVES:")
    res_op = test_query('Typo: Operative Note ("genrate opperative not")', {'consultation_id': consultation_id, 'question': 'genrate opperative not'})
    res_rad = test_query('Typo: Radiology Order ("radilogy ordr for chect ct")', {'consultation_id': consultation_id, 'question': 'radilogy ordr for chect ct'})
    res_triage = test_query('Typo: Emergency Triage ("emergenc triag sumary")', {'consultation_id': consultation_id, 'question': 'emergenc triag sumary'})

    print("\n4. AUTOMATIC ENCOUNTER LINKING (Generating document without @consultation_id):")
    res_auto = test_query('Auto-Encounter Link ("generate sports clearance certificate")', {'question': 'generate sports clearance certificate'})

    print("\n5. TYPO IN PATIENT DEMOGRAPHICS QUERY:")
    test_query('Typo: Patient Age ("wat is patint aeg")', {'consultation_id': consultation_id, 'question': 'wat is patint aeg'})

    print("\n6. MESSY UNSTRUCTURED CLINICAL CASE PRESENTATION WITH TYPOS:")
    unstructured_case = (
        "pt 58y male presnted to er with sever retrosternal ches pain radiatn to jaw and left arm, "
        "sob, profus diaphoresis, nausia. bp 85/55 hr 118 spo2 92%. ecg: st elevatn in lead II, III, aVF. "
        "troponn I positive. what is primary diagnsis and urget mangement?"
    )
    test_query('Unstructured STEMI Case', {'question': unstructured_case})

    print("\n7. BINARY DOWNLOADS VERIFICATION:")
    if res_op and res_op.get('download_urls'):
        urls = res_op['download_urls']
        if urls.get('pdf'):
            test_download('Operative Note PDF', urls['pdf'])
        if urls.get('docx'):
            test_download('Operative Note DOCX', urls['docx'])
    elif res_op and res_op.get('generated_document'):
        doc = res_op['generated_document']
        if doc.get('pdf_download_url'):
            test_download('Operative Note PDF', doc['pdf_download_url'])
