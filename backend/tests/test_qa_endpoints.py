import urllib.request
import json

def query_ai(prompt):
    url = "http://127.0.0.1:8000/ai/ask"
    body = json.dumps({"query": prompt, "consultation_id": "a994e376-9e25-4759-922f-191c3b6710ea"}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        has_doc = "generated_document" in res and res["generated_document"] is not None
        doc_type = res["generated_document"]["document_type"] if has_doc else "none"
        ans = res.get("answer", "")
        first_line = ans.split("\n")[0] if ans else ""
        clean_first = first_line.encode("ascii", "replace").decode("ascii")
        print(f"QUERY: {prompt}")
        print(f"  First line: {clean_first}")
        print(f"  Has Document: {has_doc} (type: {doc_type})")
        print()

if __name__ == "__main__":
    query_ai("what is the patient profile and chronic conditions @a994e376")
    query_ai("what is the consultation timeline and audit history @a994e376")
    query_ai("generate referral letter to cardiology @a994e376")
    query_ai("generate lab order requisition @a994e376")
    query_ai("generate patient profile report @a994e376")
    query_ai("generate timeline certificate @a994e376")
