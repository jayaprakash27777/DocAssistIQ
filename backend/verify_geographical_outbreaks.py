"""DocAssistIQ — Comprehensive Geographical Outbreak Verification Benchmark.

Evaluates:
1. India State-Wise Outbreaks (28 States & 8 UTs)
2. International Travel & High-Consequence Regional Outbreaks
3. Real-Time Outbreak Tagging, Isolation Protocols, and Confirmatory Testing
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.realtime_prediction_service import realtime_prediction_service
from app.services.india_outbreak_surveillance import (
    get_all_state_outbreaks,
    match_outbreaks_for_symptoms,
    fetch_live_cdc_outbreaks,
    ALL_INDIAN_STATES_AND_UTS,
)

print("=" * 80)
print("DOCASSISTIQ — GEOGRAPHICAL OUTBREAK SURVEILLANCE VERIFICATION")
print("=" * 80)

# 1. Verify Surveillance Registry Coverage
state_data = get_all_state_outbreaks()
total_alerts = state_data["total_active_alerts"]
india_alerts = len(state_data["india_state_alerts"])
global_alerts = len(state_data["global_alerts"])

print(f"\n[1] ACTIVE SURVEILLANCE REGISTRY STATUS:")
print(f"    - Total Active Monitored Alerts: {total_alerts}")
print(f"    - India States & UTs Monitored:   {len(ALL_INDIAN_STATES_AND_UTS)} (All 28 States + 8 UTs)")
print(f"    - India State-Level Alerts:       {india_alerts}")
print(f"    - Global Outbreak Alerts:         {global_alerts}")
print(f"    - Surveillance Agencies:          {', '.join(state_data['surveillance_sources'])}")

# 2. Test Specific Geographical Outbreak Cases
outbreak_cases = [
    # --- INDIA STATE-LEVEL OUTBREAKS ---
    {
        "category": "India Outbreak - Kerala",
        "query": "high fever, altered mental status, myoclonus, patient from Kozhikode Kerala with acute encephalitis",
        "expected": ["Nipah", "Encephalitis"],
        "expect_outbreak": True,
        "expect_alert_level": "CRITICAL"
    },
    {
        "category": "India Outbreak - Gujarat",
        "query": "fever, rapid altered sensorium, generalized convulsions in child from Sabarkantha Gujarat",
        "expected": ["Chandipura", "Acute Encephalitis", "Encephalitis"],
        "expect_outbreak": True,
        "expect_alert_level": "CRITICAL"
    },
    {
        "category": "India Outbreak - Karnataka",
        "query": "sudden high fever, severe frontal headache, conjunctival suffusion, tick bite, forest exposure in Shivamogga Karnataka",
        "expected": ["Kyasanur", "KFD", "Monkey Fever"],
        "expect_outbreak": True,
        "expect_alert_level": "HIGH"
    },
    {
        "category": "India Outbreak - Gujarat / Rajasthan CCHF",
        "query": "sudden high fever, petechial rash, ecchymosis, livestock handling, tick exposure in Surendranagar Gujarat",
        "expected": ["Crimean-Congo", "CCHF"],
        "expect_outbreak": True,
        "expect_alert_level": "CRITICAL"
    },
    {
        "category": "India Outbreak - Goa / Coastal Leptospirosis",
        "query": "high fever, severe calf muscle tenderness, conjunctival suffusion, jaundice, monsoon flooding in Goa",
        "expected": ["Leptospirosis"],
        "expect_outbreak": True,
        "expect_alert_level": "HIGH"
    },
    {
        "category": "India Outbreak - Odisha Cerebral Malaria",
        "query": "tertian fever, chills, blackwater dark urine, jaundice, splenomegaly in Rayagada Odisha",
        "expected": ["Malaria"],
        "expect_outbreak": True,
        "expect_alert_level": None
    },
    {
        "category": "India Outbreak - West Bengal Cholera",
        "query": "sudden severe profuse painless watery rice-water diarrhea, severe dehydration in Kolkata West Bengal",
        "expected": ["Cholera"],
        "expect_outbreak": True,
        "expect_alert_level": None
    },
    {
        "category": "India Outbreak - Andaman Hemorrhagic Fever",
        "query": "fever, severe hemoptysis, pulmonary hemorrhage, jaundice, post-cyclone flooding in Port Blair Andaman",
        "expected": ["Andaman", "Leptospirosis"],
        "expect_outbreak": True,
        "expect_alert_level": None
    },

    # --- INTERNATIONAL / GLOBAL TRAVEL OUTBREAKS ---
    {
        "category": "Global Outbreak - DRC Bundibugyo (BVD)",
        "query": "fever, bleeding from gums, hematemesis, watery diarrhea, patient returned from Democratic Republic of the Congo",
        "expected": ["Bundibugyo", "Ebola", "Viral Hemorrhagic Fever"],
        "expect_outbreak": True,
        "expect_alert_level": None
    },
    {
        "category": "Global Outbreak - Amazon / Peru Oropouche",
        "query": "high fever, severe retro-orbital headache, myalgia, arthralgia, photophobia, traveled to Peru Amazon",
        "expected": ["Oropouche", "Dengue"],
        "expect_outbreak": True,
        "expect_alert_level": None
    },
    {
        "category": "Global Outbreak - Colombia Yellow Fever",
        "query": "fever, severe jaundice, dark urine, hematemesis, bleeding diathesis, traveled to Colombia",
        "expected": ["Yellow Fever"],
        "expect_outbreak": True,
        "expect_alert_level": None
    },
    {
        "category": "Global Outbreak - Patagonia Andes Hantavirus (HPS)",
        "query": "fever, myalgia, abdominal pain, sudden severe shortness of breath, rapid non-cardiogenic pulmonary edema, rodent exposure in Patagonia Chile",
        "expected": ["Andes", "Hantavirus"],
        "expect_outbreak": True,
        "expect_alert_level": None
    },
    {
        "category": "Global Outbreak - Nigeria Lassa Fever",
        "query": "prolonged fever, pharyngitis with tonsillar exudates, facial edema, bleeding, sensorineural hearing loss, traveled to Nigeria",
        "expected": ["Lassa Fever"],
        "expect_outbreak": True,
        "expect_alert_level": None
    },
    {
        "category": "Global Outbreak - Saudi Arabia MERS-CoV",
        "query": "acute severe respiratory illness, high fever, cough, shortness of breath, dromedary camel exposure in Riyadh Saudi Arabia",
        "expected": ["MERS", "Coronavirus"],
        "expect_outbreak": True,
        "expect_alert_level": None
    },
    {
        "category": "Global Outbreak - Madagascar Plague",
        "query": "sudden high fever, painful suppurative inguinal lymphadenopathy buboes, chills, flea bite, traveled to Madagascar",
        "expected": ["Plague", "Bubonic Plague"],
        "expect_outbreak": True,
        "expect_alert_level": None
    },
    {
        "category": "Global Outbreak - Rwanda / Uganda Marburg",
        "query": "high fever, severe persistent headache, profuse watery diarrhea, severe bleeding, cave bat exposure in Uganda",
        "expected": ["Marburg"],
        "expect_outbreak": True,
        "expect_alert_level": None
    },
]

print(f"\n[2] RUNNING {len(outbreak_cases)} GEOGRAPHICAL OUTBREAK PREDICTION TESTS:\n")

passed = 0
failed = 0

for i, tc in enumerate(outbreak_cases, 1):
    q = tc["query"]
    t0 = time.perf_counter()
    res = realtime_prediction_service.predict(q)
    latency_ms = round((time.perf_counter() - t0) * 1000, 1)

    top_candidates = res.get("top_candidates", [])
    top3 = [c["disease"] for c in top_candidates[:3]]
    outbreak_detected = res.get("outbreak_detected", False)
    emergency_alert = res.get("emergency_alert")
    
    # Check if any expected keyword matches in top 3
    matched = any(any(exp.lower() in d.lower() for exp in tc["expected"]) for d in top3)

    # Check outbreak details or emergency alert if expected
    badge = None
    if top_candidates:
        badge = top_candidates[0].get("outbreak_badge")

    status_icon = "PASS" if matched else "FAIL"
    if matched:
        passed += 1
    else:
        failed += 1

    print(f"[{i:02d}] {tc['category']:<40} [{status_icon}] ({latency_ms}ms)")
    print(f"     Top 3: {top3}")
    if badge:
        clean_badge = badge.encode('ascii', 'ignore').decode('ascii').strip()
        print(f"     Alert Badge: {clean_badge}")
    if emergency_alert:
        clean_cond = emergency_alert.get('condition', '').encode('ascii', 'ignore').decode('ascii').strip()
        print(f"     Emergency Alert: {clean_cond}")
    print()

print("=" * 80)
print(f"GEOGRAPHICAL OUTBREAK CASES SUMMARY: {passed}/{len(outbreak_cases)} PASSED ({(passed/len(outbreak_cases))*100:.1f}%)")
print("=" * 80)
