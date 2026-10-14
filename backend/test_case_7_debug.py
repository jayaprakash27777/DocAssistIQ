from app.services.realtime_prediction_service import realtime_prediction_service

text = "A 42-year-old woman develops fatigue, headache, confusion, and bruises over two days. Her temperature is 38.1°C, and she has scattered petechiae without active bleeding. Hemoglobin is 7.9 g/dL, platelets are 18,000/µL, creatinine is 1.7 mg/dL, LDH is markedly elevated, haptoglobin is undetectable, and the blood film contains fragmented red cells. PT and aPTT are near normal."
res = realtime_prediction_service.predict(text)
print("Primary:", res.get("top_candidates", [{}])[0].get("disease"))
print("Extracted findings:", res.get("extracted_findings", []))
print("Differentials:")
for d in res.get("top_candidates", [])[:10]:
    print(f"  {d.get('disease')} (prob: {d.get('post_test_probability')}, score: {d.get('score')})")
