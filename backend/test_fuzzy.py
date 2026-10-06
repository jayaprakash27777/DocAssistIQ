import sys
sys.stdout.reconfigure(encoding='utf-8')
from app.services.clinical_nlp_fuzzy_normalizer import normalize_clinical_query, fuzzy_intent_detect, extract_vitals_from_unstructured

test_cases = [
    'genrate opperative not',
    'radilogy ordr for chect ct',
    'calclate bmmi hight 175 weigt 70',
    'wat is patint aeg',
    'symptms of dengu',
    'how 2 treat dibetic ketoacidoss',
    'pt 58y male presnted to er with sever retrosternal ches pain radiatn to jaw, sob, profus diaphoresis. bp 85/55 hr 118 spo2 92%. ecg: st elevatn in lead II, III, aVF. troponn I positive.'
]

for t in test_cases:
    norm = normalize_clinical_query(t)
    intent = fuzzy_intent_detect(t)
    vitals = extract_vitals_from_unstructured(t)
    print(f"INPUT:  {t}")
    print(f"NORM:   {norm}")
    print(f"INTENT: {intent['intent']}, doc={intent['document_type']}, calc={intent['calculator_type']}, is_case={intent['is_unstructured_case']}")
    if vitals:
        print(f"VITALS: {vitals}")
    print("-" * 50)
