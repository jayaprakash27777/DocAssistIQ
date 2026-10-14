import traceback
import sys
import os
import re

sys.path.insert(0, os.path.abspath("backend"))
from app.services.realtime_prediction_service import realtime_prediction_service

TEST_FILE = r"c:\Users\User\Downloads\DocAssistIQ_100_Symptom_to_Disease_Test_Cases.md"
with open(TEST_FILE, "r", encoding="utf-8") as f:
    text = f.read()

cases_raw = re.findall(r"###\s+Case\s+(\d+)\s*\n(.*?)(?=(?:###\s+Case\s+\d+)|\n##\s+|\Z)", text, re.DOTALL)
for num_str, content in cases_raw[55:100]:
    cid = int(num_str)
    content_clean = content.strip()
    text_to_test = re.sub(r"\[S\d+\]\s*$", "", content_clean).strip()
    try:
        res = realtime_prediction_service.predict(text_to_test)
        top = res.get("top_candidates", [])
        d_name = top[0].get("disease") if top else "None"
        lat = res.get("latency_ms")
        print(f"Case {cid} OK: {d_name} ({lat}ms)")
    except Exception as e:
        print(f"Case {cid} FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()
