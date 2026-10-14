import asyncio
import sys
import time

sys.path.append("backend")

from app.services.universal_clinical_engine import (
    _extract_calc_answer,
    _extract_clinical_entity,
    _normalize_query,
    _detect_intents,
    _extract_keywords,
    _format_god_level_answer,
)
from app.services.offline_data_service import offline_data_service
from app.services.realtime_medical_engine import _find_kb_match

async def profile_query(query):
    t_start = time.time()
    def mark(label):
        nonlocal t_start
        now = time.time()
        print(f"[{label}]: {(now - t_start)*1000:.2f}ms")
        t_start = now

    mark("start")
    clean_entity = _extract_clinical_entity(query)
    norm_q = _normalize_query(clean_entity) if clean_entity else _normalize_query(query)
    intents = _detect_intents(query)
    keywords = _extract_keywords(clean_entity or norm_q or query)
    mark("normalize")

    # 1. Rules
    rule_hits = offline_data_service.search_clinical_decision_rules(norm_q, limit=1)
    mark("rules")

    # 2. Medical KB
    kb_result = _find_kb_match(clean_entity) or _find_kb_match(norm_q) or _find_kb_match(query)
    mark("medical_kb")
    print("kb_result found:", bool(kb_result))

    # 3. StatPearls
    sp_hits = offline_data_service.search_statpearls_monographs(clean_entity or norm_q, limit=1)
    mark("statpearls")

    # 4. MedQuAD
    mq_hits = offline_data_service.search_medquad_qa(clean_entity or norm_q, limit=2)
    mark("medquad")

    # 5. Warehouse
    wh_hits = offline_data_service.search_universal_warehouse("lavita_medical_qa_benchmarks", clean_entity, limit=2)
    mark("warehouse_lavita")

    wh_trials = offline_data_service.search_universal_warehouse("pubmed_clinical_trials_full", clean_entity, limit=2)
    mark("warehouse_trials")

asyncio.run(profile_query("What is the first-line treatment for acute pulmonary embolism?"))
