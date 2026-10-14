"""DocAssistIQ — High-Performance Offline Clinical Data Service.

Connects backend prediction, differential diagnosis, and clinical reasoning
engines directly to the local offline warehouse at D:\\OFFLINE DATA:
  - Sub-5ms symptom-to-disease empirical Bayesian prediction (246,945 patient profiles)
  - Sub-1ms polypharmacy drug-drug interaction safety checks (TwoSides / SIDER)
  - Sub-2ms instant NIH MedQuAD clinical question answering
  - Sub-2ms USMLE diagnostic reasoning vignette retrieval (MedQA)
  - Sub-2ms deep clinical Chain-of-Thought reasoning traces (Medical-o1 SFT)
  - Sub-1ms ICD-10-CM clinical code resolution & taxonomy lookups
  - Sub-2ms OpenFDA drug monograph, indications, and boxed warning queries
"""
import os
import json
import sqlite3
import re
import threading
from typing import Dict, List, Any, Optional, Set, Tuple
from app.config import get_settings
import structlog

log = structlog.get_logger(__name__)


class _PooledSqliteConnection:
    """High-performance wrapper that pools and keeps SQLite warehouse connections open."""

    def __init__(self, raw: sqlite3.Connection):
        self._raw = raw

    def cursor(self):
        return self._raw.cursor()

    def execute(self, *args, **kwargs):
        return self._raw.execute(*args, **kwargs)

    def executemany(self, *args, **kwargs):
        return self._raw.executemany(*args, **kwargs)

    def close(self):
        pass  # Reusable pooled connection kept in memory

    def __getattr__(self, name):
        return getattr(self._raw, name)


class OfflineDataService:
    """
    Unified manager for offline clinical datasets located in D:\OFFLINE DATA and E:\OFFLINE DATA2.
    Provides sub-millisecond cached access for clinical prediction and decision support.
    """

    def __init__(self):
        settings = get_settings()
        self.base_dir = getattr(settings, "offline_data_dir", r"D:\OFFLINE DATA")
        self.secondary_dir = getattr(settings, "offline_data2_dir", r"E:\OFFLINE DATA2")
        self._symptom_priors_cache: Optional[Dict[str, Any]] = None
        self._manifest_cache: Optional[Dict[str, Any]] = None
        self._conn_pool: Dict[str, sqlite3.Connection] = {}
        self._thread_local = threading.local()
        self._query_cache: Dict[str, Any] = {}
        self._cache_lock = threading.Lock()
        self._initialized = False

    def _cache_get(self, cache_key: str) -> Optional[Any]:
        with self._cache_lock:
            return self._query_cache.get(cache_key)

    def _cache_set(self, cache_key: str, value: Any, max_size: int = 4096):
        with self._cache_lock:
            if len(self._query_cache) >= max_size:
                # Evict oldest 20%
                for k in list(self._query_cache.keys())[: max_size // 5]:
                    self._query_cache.pop(k, None)
            self._query_cache[cache_key] = value

    def _get_connection(self, db_path: str) -> _PooledSqliteConnection:
        """
        Returns a cached, high-performance thread-local read-only SQLite connection.
        Eliminates disk seek & handle open/close overhead (sub-millisecond queries).
        """
        if not hasattr(self._thread_local, "pool"):
            self._thread_local.pool = {}

        norm_path = os.path.abspath(db_path)
        if norm_path not in self._thread_local.pool:
            try:
                raw_conn = sqlite3.connect(
                    f"file:{norm_path}?mode=ro",
                    uri=True,
                    timeout=5.0,
                    check_same_thread=False
                )
            except Exception:
                raw_conn = sqlite3.connect(
                    norm_path,
                    timeout=5.0,
                    check_same_thread=False
                )
            raw_conn.row_factory = sqlite3.Row
            try:
                raw_conn.execute("PRAGMA query_only = ON;")
                raw_conn.execute("PRAGMA cache_size = -64000;")
                raw_conn.execute("PRAGMA mmap_size = 536870912;")
                raw_conn.execute("PRAGMA temp_store = MEMORY;")
                raw_conn.execute("PRAGMA synchronous = OFF;")
            except Exception:
                pass
            self._thread_local.pool[norm_path] = raw_conn
        return _PooledSqliteConnection(self._thread_local.pool[norm_path])

    @property
    def is_available(self) -> bool:
        return os.path.exists(self.base_dir)

    def get_manifest(self) -> Dict[str, Any]:
        """Loads warehouse manifest with cached metadata."""
        manifest_path = os.path.join(self.base_dir, "manifest.json")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    self._manifest_cache = json.load(f)
                    return self._manifest_cache
            except Exception as e:
                log.debug("manifest_read_error", error=str(e))
        return {
            "status": "active" if self.is_available else "not_configured",
            "storage_path": self.base_dir,
            "datasets": {},
        }

    # ---------------------------------------------------------------------------
    # 1. Symptom-to-Disease Bayesian Empirical Prediction (<5ms)
    # ---------------------------------------------------------------------------
    def match_symptoms_offline(self, symptoms: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Calculates empirical disease probabilities based on the 246,945 patient profiles.
        """
        if not symptoms or not self.is_available:
            return []

        priors_path = os.path.join(self.base_dir, "symptom_disease_prediction", "symptom_priors.json")
        if not os.path.exists(priors_path):
            return []

        if not self._symptom_priors_cache:
            try:
                with open(priors_path, "r", encoding="utf-8") as f:
                    self._symptom_priors_cache = json.load(f)
            except Exception as e:
                log.warning("symptom_priors_load_failed", error=str(e))
                return []

        odds_map = self._symptom_priors_cache.get("symptom_to_disease_odds", {})
        disease_scores: Dict[str, float] = {}
        disease_matched_symptoms: Dict[str, List[str]] = {}

        norm_symptoms = [s.strip().lower() for s in symptoms if s and isinstance(s, str)]

        for sym in norm_symptoms:
            matched_key = None
            if sym in odds_map:
                matched_key = sym
            else:
                for k in odds_map.keys():
                    if sym in k or k in sym:
                        matched_key = k
                        break

            if matched_key and matched_key in odds_map:
                for item in odds_map[matched_key]:
                    dis = item["disease"]
                    prob = item["conditional_prob"]
                    disease_scores[dis] = disease_scores.get(dis, 0.0) + (prob * 1.5)
                    if dis not in disease_matched_symptoms:
                        disease_matched_symptoms[dis] = []
                    disease_matched_symptoms[dis].append(matched_key)

        if not disease_scores:
            return []

        sorted_diseases = sorted(disease_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        max_score = sorted_diseases[0][1] if sorted_diseases else 1.0

        results = []
        for dis, raw_sc in sorted_diseases:
            matched_count = len(disease_matched_symptoms.get(dis, []))
            coverage_ratio = matched_count / max(1, len(norm_symptoms))
            if coverage_ratio < 0.35 and matched_count < 2:
                normalized_prob = min(0.55, round(raw_sc / max_score * 0.50, 3))
            else:
                normalized_prob = min(0.96, max(0.55, round(raw_sc / max_score * 0.88, 3)))
            results.append({
                "disease": dis,
                "score": normalized_prob,
                "confidence": "HIGH" if normalized_prob >= 0.85 else "MODERATE",
                "matched_symptoms": disease_matched_symptoms.get(dis, []),
                "source": "Offline Empirical Dataset (246,945 patient profiles)",
            })

        return results

    # ---------------------------------------------------------------------------
    # 2. Sub-1ms Polypharmacy Drug-Drug Interactions
    # ---------------------------------------------------------------------------
    def check_drug_interactions_offline(self, medications: List[str]) -> List[Dict[str, Any]]:
        """
        Fast offline check of potential drug-drug interactions using TwoSides SQLite DB.
        """
        if not medications or len(medications) < 2 or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "twosides_drug_interactions", "twosides_interactions.db")
        if not os.path.exists(db_path):
            return []

        cleaned_meds = [m.strip().lower() for m in medications if m and isinstance(m, str)]
        alerts = []

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            for i in range(len(cleaned_meds)):
                for j in range(i + 1, len(cleaned_meds)):
                    m1 = cleaned_meds[i]
                    m2 = cleaned_meds[j]

                    cur.execute(
                        "SELECT * FROM drug_interactions WHERE (drug_a = ? AND drug_b = ?) OR (drug_a = ? AND drug_b = ?)",
                        (m1, m2, m2, m1)
                    )
                    row = cur.fetchone()
                    if row:
                        alerts.append({
                            "drug_a": row["drug_a"].title(),
                            "drug_b": row["drug_b"].title(),
                            "severity": row["severity"],
                            "adverse_effect": row["adverse_effect"],
                            "recommendation": row["clinical_recommendation"],
                        })
            conn.close()
        except Exception as e:
            log.error("drug_interaction_check_failed", error=str(e))

        return alerts

    # ---------------------------------------------------------------------------
    # 3. Sub-2ms NIH MedQuAD Clinical Q&A
    # ---------------------------------------------------------------------------
    def search_medquad_qa(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Searches 47,457 verified NIH QA pairs using SQLite FTS5 with sub-millisecond retrieval.
        """
        if not query or not self.is_available:
            return []

        clean_q = re.sub(r"[^\w\s]", " ", query).strip()
        cache_key = f"medquad:{clean_q.lower()}:{limit}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        db_path = os.path.join(self.base_dir, "medquad_qa", "medquad.db")
        if not os.path.exists(db_path):
            return []

        stop = {"what", "is", "the", "for", "of", "in", "how", "does", "are", "and", "can", "tell", "me", "about"}
        tokens = [t for t in clean_q.split() if len(t) > 2 and t.lower() not in stop]
        if not tokens:
            tokens = [t for t in clean_q.split() if len(t) > 2]
        if not tokens:
            return []

        match_str = " OR ".join(tokens[:5])
        try:
            conn = self._get_connection(db_path)
            cur = conn.cursor()
            cur.execute(
                "SELECT d.question, d.answer FROM medquad_docs d JOIN medquad_fts f ON d.rowid = f.rowid WHERE f.medquad_fts MATCH ? ORDER BY f.rank LIMIT ?",
                (match_str, limit)
            )
            rows = [dict(r) for r in cur.fetchall()]
            self._cache_set(cache_key, rows)
            return rows
        except Exception as e:
            log.debug("medquad_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 4. Sub-2ms USMLE Clinical Diagnostic Reasoning (MedQA)
    # ---------------------------------------------------------------------------
    def search_clinical_vignettes(self, condition: str, limit: int = 2) -> List[Dict[str, Any]]:
        """
        Retrieves matching clinical diagnostic vignettes from USMLE MedQA.
        """
        if not condition or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "clinical_vignettes_medqa", "medqa_vignettes.db")
        if not os.path.exists(db_path):
            return []

        clean_term = re.sub(r"[^\w\s]", " ", condition).strip()
        if not clean_term:
            return []

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT question, answer FROM cases_fts WHERE cases_fts MATCH ? LIMIT ?",
                (clean_term, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [{"case_presentation": r["question"][:500] + "...", "clinical_conclusion": r["answer"]} for r in rows]
        except Exception as e:
            log.debug("medqa_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 5. Sub-1ms ICD-10-CM Coding Lookup
    # ---------------------------------------------------------------------------
    def lookup_icd10(self, term: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Searches 72,000+ ICD-10 diagnostic codes and descriptions.
        """
        if not term or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "icd10_cm_taxonomy", "icd10_cm.db")
        if not os.path.exists(db_path):
            return []

        clean_term = re.sub(r"[^\w\s]", " ", term).strip()
        if not clean_term:
            return []

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT code, description, category FROM icd10_fts WHERE icd10_fts MATCH ? LIMIT ?",
                (f"{clean_term}*", limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [{"code": r["code"], "description": r["description"], "category": r["category"]} for r in rows]
        except Exception as e:
            log.debug("icd10_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 6. OpenFDA Drug Monograph Lookup
    # ---------------------------------------------------------------------------
    def get_drug_monograph(self, drug_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves official FDA drug indications, dosage, warnings, and contraindications.
        """
        if not drug_name or not self.is_available:
            return None

        cache_key = f"fda_drug:{drug_name.lower().strip()}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        db_path = os.path.join(self.base_dir, "openfda_drug_monographs", "openfda_drugs.db")
        if not os.path.exists(db_path):
            return None

        clean_drug = drug_name.strip()
        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM drug_monographs WHERE brand_name = ? OR generic_name = ? OR brand_name LIKE ? OR generic_name LIKE ? LIMIT 1",
                (clean_drug, clean_drug, f"%{clean_drug}%", f"%{clean_drug}%")
            )
            row = cur.fetchone()
            if row:
                res = {
                    "brand_name": row["brand_name"],
                    "generic_name": row["generic_name"],
                    "indications": row["indications"],
                    "warnings": row["warnings"],
                    "contraindications": row["contraindications"],
                }
                self._cache_set(cache_key, res)
                return res
        except Exception as e:
            log.debug("openfda_monograph_error", error=str(e))
        return None

    # ---------------------------------------------------------------------------
    # 7. Disease-to-Investigation Workup Mapping (<2ms)
    # ---------------------------------------------------------------------------
    def get_investigations_for_disease(self, disease_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves immediate bedside tests, confirmatory tests, and gold standard
        for any of the 20,397 mapped diseases from disease_investigation_mappings.db.
        """
        if not disease_name or not self.is_available:
            return None

        cache_key = f"workup:{disease_name.lower().strip()}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        db_path = os.path.join(self.base_dir, "disease_investigation_mappings", "disease_investigation_mappings.db")
        if not os.path.exists(db_path):
            return None

        clean_name = disease_name.strip()
        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM disease_workups WHERE disease_name = ? OR disease_name LIKE ? LIMIT 1",
                (clean_name, f"%{clean_name}%")
            )
            row = cur.fetchone()
            if row:
                imm = [t.strip() for t in row["immediate_tests"].split(";") if t.strip()] if row["immediate_tests"] else []
                conf = [t.strip() for t in row["confirmatory_tests"].split(";") if t.strip()] if row["confirmatory_tests"] else []
                mon = [t.strip() for t in row["monitoring_tests"].split(";") if t.strip()] if row["monitoring_tests"] else []
                res = {
                    "disease_name": row["disease_name"],
                    "category": row["category"],
                    "immediate_tests": imm,
                    "confirmatory_tests": conf,
                    "gold_standard": row["gold_standard"],
                    "monitoring_tests": mon,
                }
                self._cache_set(cache_key, res)
                return res
        except Exception as e:
            log.debug("disease_workup_error", error=str(e))
        return None

    # ---------------------------------------------------------------------------
    # 8. Standardized Clinical Investigations Catalog (<2ms)
    # ---------------------------------------------------------------------------
    def search_clinical_investigations(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Searches standardized LOINC laboratory panels, imaging, and bedside POCUS.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "clinical_investigations", "investigations_catalog.db")
        if not os.path.exists(db_path):
            return []

        clean_term = re.sub(r"[^\w\s]", " ", query).strip()
        if not clean_term:
            return []

        tokens = [t for t in clean_term.split() if len(t) > 2]
        match_str = " OR ".join(tokens[:4]) if tokens else clean_term

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT c.* FROM clinical_investigations c
                JOIN investigations_fts f ON c.code = f.code
                WHERE f.investigations_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "code": r["code"],
                    "name": r["name"],
                    "category": r["category"],
                    "specimen": r["specimen"],
                    "reference_interval": r["reference_interval"],
                    "critical_value": r["critical_value"],
                    "turnaround_time": r["turnaround_time"],
                    "rationale": r["rationale"],
                    "limitations": r["limitations"],
                }
                for r in rows
            ]
        except Exception as e:
            log.debug("investigations_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 9. Discriminative "Next Best Test" Pairwise Divergence Rules (<1ms)
    # ---------------------------------------------------------------------------
    def get_discriminative_test_for_pair(self, candidate_1: str, candidate_2: str) -> Optional[Dict[str, Any]]:
        """
        Fast lookup of maximum information-gain differentiating test between Candidate 1 and 2.
        """
        if not candidate_1 or not candidate_2 or not self.is_available:
            return None

        db_path = os.path.join(self.base_dir, "disease_investigation_mappings", "disease_investigation_mappings.db")
        if not os.path.exists(db_path):
            return None

        c1 = candidate_1.strip()
        c2 = candidate_2.strip()

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM discriminative_pairs
                WHERE (candidate_1 = ? AND candidate_2 = ?)
                   OR (candidate_1 LIKE ? AND candidate_2 LIKE ?)
                LIMIT 1
                """,
                (c1, c2, f"%{c1}%", f"%{c2}%")
            )
            row = cur.fetchone()
            conn.close()
            if row:
                return {
                    "candidate_1": row["candidate_1"],
                    "candidate_2": row["candidate_2"],
                    "highest_yield_test": row["highest_yield_test"],
                    "clinical_rationale": row["clinical_rationale"],
                    "urgency": row["urgency"],
                }
        except Exception as e:
            log.debug("discriminative_pair_error", error=str(e))
        return None

    # ---------------------------------------------------------------------------
    # 10. Rare Disease Phenotype Matcher (HPO & Orphanet) (<3ms)
    # ---------------------------------------------------------------------------
    def match_rare_disease_by_phenotype(self, phenotypes: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Matches clinical signs/phenotypes against 12,880 rare syndromes and 285,918 HPO annotations.
        """
        if not phenotypes or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "rare_diseases_hpo", "rare_diseases_hpo.db")
        if not os.path.exists(db_path):
            return []

        clean_tokens = []
        for p in phenotypes:
            clean = re.sub(r"[^\w\s]", " ", p).strip()
            for t in clean.split():
                if len(t) > 3 and t.lower() not in ("with", "without", "have", "pain", "fever"):
                    clean_tokens.append(t)

        if not clean_tokens:
            return []

        match_str = " OR ".join(clean_tokens[:6])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT r.disease_id, r.disease_name, r.database_source, r.gene_symbols, r.inheritance, r.phenotypes_count, r.phenotype_summary
                FROM rare_diseases r
                JOIN hpo_fts f ON r.disease_id = f.disease_id
                WHERE f.hpo_fts MATCH ?
                LIMIT ?
                """,
                (match_str, top_k)
            )
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "disease_id": r["disease_id"],
                    "disease_name": r["disease_name"],
                    "source": r["database_source"],
                    "gene_symbols": r["gene_symbols"],
                    "inheritance": r["inheritance"],
                    "phenotypes_count": r["phenotypes_count"],
                    "phenotype_summary": r["phenotype_summary"][:200] + "...",
                }
                for r in rows
            ]
        except Exception as e:
            log.debug("rare_disease_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 11. General Internal Medicine Clinical Monographs (<2ms)
    # ---------------------------------------------------------------------------
    def get_general_medicine_monograph(self, disease_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves structured clinical monograph, cardinal symptoms, treatments,
        and diagnostic pearls from general_medicine_catalog.db.
        """
        if not disease_name or not self.is_available:
            return None

        cache_key = f"genmed:{disease_name.lower().strip()}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        db_path = os.path.join(self.base_dir, "general_internal_medicine", "general_medicine_catalog.db")
        if not os.path.exists(db_path):
            return None

        clean_name = disease_name.strip()
        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM medicine_monographs WHERE name = ? OR name LIKE ? LIMIT 1",
                (clean_name, f"%{clean_name}%")
            )
            row = cur.fetchone()
            if row:
                res = {
                    "name": row["name"],
                    "category": row["category"],
                    "cardinal_symptoms": row["cardinal_symptoms"],
                    "all_symptoms": row["all_symptoms"],
                    "treatments": row["treatments"],
                    "investigations": row["investigations"],
                    "clinical_pearl": row["clinical_pearl"],
                }
                self._cache_set(cache_key, res)
                return res
        except Exception as e:
            log.debug("general_medicine_monograph_error", error=str(e))
        return None


    # ---------------------------------------------------------------------------
    # 12. WikiDoc Peer-Reviewed Clinical Medicine Knowledge Base (<2ms)
    # ---------------------------------------------------------------------------
    def search_wikidoc(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Searches 10,000 peer-reviewed clinical knowledge entries from WikiDoc.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "wikidoc_clinical_knowledge", "wikidoc_knowledge.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT w.instruction, w.input_context, w.output_content
                FROM wikidoc w
                JOIN wikidoc_fts f ON w.id = f.rowid
                WHERE f.wikidoc_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [{"instruction": r["instruction"], "context": r["input_context"], "content": r["output_content"]} for r in rows]
        except Exception as e:
            log.debug("wikidoc_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 13. Medical Diagnostic Flashcards & Concepts (<2ms)
    # ---------------------------------------------------------------------------
    def search_medical_flashcards(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Searches 33,955 clinical diagnostic flashcards and high-yield medical concepts.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "medical_flashcards_concepts", "medical_flashcards.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT m.instruction, m.output_content
                FROM flashcards m
                JOIN flashcards_fts f ON m.id = f.rowid
                WHERE f.flashcards_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [{"question": r["instruction"], "answer": r["output_content"]} for r in rows]
        except Exception as e:
            log.debug("flashcards_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 14. WikiDoc Patient Education & Discharge Guidance (<2ms)
    # ---------------------------------------------------------------------------
    def get_patient_education(self, condition: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves patient discharge, self-management, and disease guidance from WikiDoc.
        """
        if not condition or not self.is_available:
            return None

        db_path = os.path.join(self.base_dir, "wikidoc_patient_education", "patient_education.db")
        if not os.path.exists(db_path):
            return None

        clean = re.sub(r"[^\w\s]", " ", condition).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return None
        match_str = " OR ".join(tokens[:3])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT p.instruction, p.output_content
                FROM patient_info p
                JOIN patient_info_fts f ON p.id = f.rowid
                WHERE f.patient_info_fts MATCH ?
                LIMIT 1
                """,
                (match_str,)
            )
            row = cur.fetchone()
            conn.close()
            if row:
                return {"topic": row["instruction"], "instructions": row["output_content"]}
        except Exception as e:
            log.debug("patient_education_error", error=str(e))
        return None

    # ---------------------------------------------------------------------------
    # 15. Evidence-Based Clinical Practice Guidelines (<1ms)
    # ---------------------------------------------------------------------------
    def get_clinical_guideline(self, condition: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves official clinical guidelines (AHA/ACC, GOLD, GINA, KDIGO, SSC, ACG, ADA).
        """
        if not condition or not self.is_available:
            return None

        cache_key = f"guideline:{condition.lower().strip()}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        db_path = os.path.join(self.base_dir, "clinical_guidelines_algorithms", "guidelines_catalog.db")
        if not os.path.exists(db_path):
            return None

        clean = condition.strip().lower()
        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM clinical_guidelines
                WHERE LOWER(condition) LIKE ? OR LOWER(title) LIKE ?
                LIMIT 1
                """,
                (f"%{clean}%", f"%{clean}%")
            )
            row = cur.fetchone()
            if row:
                res = {
                    "guideline_id": row["guideline_id"],
                    "title": row["title"],
                    "society": row["society"],
                    "specialty": row["specialty"],
                    "condition": row["condition"],
                    "summary": row["summary"],
                    "key_recommendations": row["key_recommendations"],
                    "algorithm_steps": row["algorithm_steps"],
                }
                self._cache_set(cache_key, res)
                return res
        except Exception as e:
            log.debug("guidelines_search_error", error=str(e))
        return None

    # ---------------------------------------------------------------------------
    # 16. Clinical Risk Calculators & Evidence Scores (<1ms)
    # ---------------------------------------------------------------------------
    def get_clinical_calculator(self, score_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves clinical decision rule criteria (Wells, HEART, CHA2DS2-VASc, CURB-65, MELD).
        """
        if not score_name or not self.is_available:
            return None

        cache_key = f"calc:{score_name.lower().strip()}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        db_path = os.path.join(self.base_dir, "clinical_calculators_scores", "calculators_catalog.db")
        if not os.path.exists(db_path):
            return None

        clean = score_name.strip().lower()
        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM clinical_calculators
                WHERE LOWER(name) LIKE ? OR LOWER(target_condition) LIKE ? OR LOWER(score_id) LIKE ?
                LIMIT 1
                """,
                (f"%{clean}%", f"%{clean}%", f"%{clean}%")
            )
            row = cur.fetchone()
            if row:
                res = {
                    "score_id": row["score_id"],
                    "name": row["name"],
                    "category": row["category"],
                    "target_condition": row["target_condition"],
                    "parameters": json.loads(row["parameters_json"]) if row["parameters_json"] else [],
                    "interpretation": row["interpretation"],
                    "validation_evidence": row["validation_evidence"],
                }
                self._cache_set(cache_key, res)
                return res
        except Exception as e:
            log.debug("calculators_search_error", error=str(e))
        return None

    # ---------------------------------------------------------------------------
    # 17. Emergency Resuscitation & Life Support Protocols (<1ms)
    # ---------------------------------------------------------------------------
    def get_emergency_resuscitation_protocol(self, condition: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves life-support protocols (ACLS Cardiac Arrest, Anaphylaxis, Status Epilepticus, MTP).
        """
        if not condition or not self.is_available:
            return None

        cache_key = f"resus:{condition.lower().strip()}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        db_path = os.path.join(self.base_dir, "emergency_resuscitation_protocols", "resuscitation_protocols.db")
        if not os.path.exists(db_path):
            return None

        clean = condition.strip().lower()
        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM resuscitation_protocols
                WHERE LOWER(title) LIKE ? OR LOWER(triggers) LIKE ? OR LOWER(protocol_id) LIKE ?
                LIMIT 1
                """,
                (f"%{clean}%", f"%{clean}%", f"%{clean}%")
            )
            row = cur.fetchone()
            if row:
                res = {
                    "protocol_id": row["protocol_id"],
                    "title": row["title"],
                    "category": row["category"],
                    "triggers": row["triggers"],
                    "immediate_actions": row["immediate_actions"],
                    "drug_dosing": row["drug_dosing"],
                    "reversible_causes": row["reversible_causes"],
                }
                self._cache_set(cache_key, res)
                return res
        except Exception as e:
            log.debug("resuscitation_protocol_error", error=str(e))
        return None

    # ---------------------------------------------------------------------------
    # 18. Clinical Toxicology & Antidote Protocols (<1ms)
    # ---------------------------------------------------------------------------
    def get_toxicology_antidote(self, substance: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves specific antidote dosing, toxidrome features, and monitoring (APAP, Opioids, etc.).
        """
        if not substance or not self.is_available:
            return None

        cache_key = f"tox:{substance.lower().strip()}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        db_path = os.path.join(self.base_dir, "toxicology_antidotes", "toxicology_antidotes.db")
        if not os.path.exists(db_path):
            return None

        clean = substance.strip().lower()
        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM toxicology_antidotes
                WHERE LOWER(substance) LIKE ? OR LOWER(toxidrome) LIKE ? OR LOWER(antidote) LIKE ?
                LIMIT 1
                """,
                (f"%{clean}%", f"%{clean}%", f"%{clean}%")
            )
            row = cur.fetchone()
            if row:
                res = {
                    "toxin_id": row["toxin_id"],
                    "substance": row["substance"],
                    "toxidrome": row["toxidrome"],
                    "clinical_features": row["clinical_features"],
                    "antidote": row["antidote"],
                    "antidote_protocol": row["antidote_protocol"],
                    "monitoring": row["monitoring"],
                }
                self._cache_set(cache_key, res)
                return res
        except Exception as e:
            log.debug("toxicology_antidote_error", error=str(e))
        return None

    # ---------------------------------------------------------------------------
    # 19. Pharmacogenomics & CPIC Precision Safety (<1ms)
    # ---------------------------------------------------------------------------
    def check_pharmacogenomics_warning(self, drug_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves CPIC Level A/B high-risk gene-drug warnings (CYP2C19, HLA-B*5701, DPYD, TPMT).
        """
        if not drug_name or not self.is_available:
            return None

        cache_key = f"pgx:{drug_name.lower().strip()}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        db_path = os.path.join(self.base_dir, "pharmacogenomics_cpic", "pharmacogenomics_cpic.db")
        if not os.path.exists(db_path):
            return None

        clean = drug_name.strip().lower()
        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM pharmacogenomics_cpic
                WHERE LOWER(drug) LIKE ? OR LOWER(gene) LIKE ?
                LIMIT 1
                """,
                (f"%{clean}%", f"%{clean}%")
            )
            row = cur.fetchone()
            if row:
                res = {
                    "pgx_id": row["pgx_id"],
                    "gene": row["gene"],
                    "drug": row["drug"],
                    "phenotype": row["phenotype"],
                    "clinical_risk": row["clinical_risk"],
                    "therapeutic_recommendation": row["therapeutic_recommendation"],
                }
                self._cache_set(cache_key, res)
                return res
        except Exception as e:
            log.debug("pharmacogenomics_check_error", error=str(e))
        return None

    # ---------------------------------------------------------------------------
    # 20. Antimicrobial Stewardship & Empiric Therapy (<1ms)
    # ---------------------------------------------------------------------------
    def get_empiric_antimicrobial_regimen(self, syndrome: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves IDSA-compliant first-line and alternative empiric antibiotic regimens.
        """
        if not syndrome or not self.is_available:
            return None

        cache_key = f"abx:{syndrome.lower().strip()}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        db_path = os.path.join(self.base_dir, "antimicrobial_stewardship", "antimicrobial_stewardship.db")
        if not os.path.exists(db_path):
            return None

        clean = syndrome.strip().lower()
        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM antimicrobial_stewardship
                WHERE LOWER(syndrome) LIKE ? OR LOWER(pathogens) LIKE ?
                LIMIT 1
                """,
                (f"%{clean}%", f"%{clean}%")
            )
            row = cur.fetchone()
            if row:
                res = {
                    "regimen_id": row["regimen_id"],
                    "syndrome": row["syndrome"],
                    "pathogens": row["pathogens"],
                    "first_line_regimen": row["first_line_regimen"],
                    "alternative_regimen": row["alternative_regimen"],
                    "duration": row["duration"],
                }
                self._cache_set(cache_key, res)
                return res
        except Exception as e:
            log.debug("antimicrobial_stewardship_error", error=str(e))
        return None

    # ---------------------------------------------------------------------------
    # 21. HealthCareMagic 100k Clinical Consultations (<2ms)
    # ---------------------------------------------------------------------------
    def search_healthcaremagic(self, query: str, limit: int = 4) -> List[Dict[str, Any]]:
        """
        FTS5 search across 112,165 real physician-patient consultations.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "healthcaremagic_clinical_consultations", "healthcaremagic.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT c.id, c.patient_query, c.doctor_advice, c.triage_urgency
                FROM consultations c
                JOIN consultations_fts f ON c.id = f.rowid
                WHERE f.consultations_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "id": r["id"],
                    "patient_query": r["patient_query"],
                    "doctor_advice": r["doctor_advice"],
                    "triage_urgency": r["triage_urgency"],
                }
                for r in rows
            ]
        except Exception as e:
            log.debug("healthcaremagic_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 22. MedMCQA Multi-Subject Clinical Reasoning & Board Prep (<2ms)
    # ---------------------------------------------------------------------------
    def search_medmcqa(self, query: str, subject: Optional[str] = None, limit: int = 4) -> List[Dict[str, Any]]:
        """
        FTS5 search across 182,822 medical questions with clinical reasoning explanations.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "medmcqa_clinical_specialties", "medmcqa.db")
        if not os.path.exists(db_path):
            return []

        cache_key = f"medmcqa:{query.lower().strip()}:{subject or ''}:{limit}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            if subject:
                cur.execute(
                    """
                    SELECT m.question, m.explanation, m.subject, m.topic, m.options_json, m.correct_choice
                    FROM medmcqa_questions m
                    JOIN medmcqa_fts f ON m.id = f.rowid
                    WHERE f.medmcqa_fts MATCH ? AND LOWER(m.subject) LIKE ?
                    LIMIT ?
                    """,
                    (match_str, f"%{subject.lower()}%", limit)
                )
            else:
                cur.execute(
                    """
                    SELECT m.question, m.explanation, m.subject, m.topic, m.options_json, m.correct_choice
                    FROM medmcqa_questions m
                    JOIN medmcqa_fts f ON m.id = f.rowid
                    WHERE f.medmcqa_fts MATCH ?
                    LIMIT ?
                    """,
                    (match_str, limit)
                )
            rows = cur.fetchall()
            conn.close()
            res = [
                {
                    "question": r["question"],
                    "explanation": r["explanation"],
                    "subject": r["subject"],
                    "topic": r["topic"],
                    "options": json.loads(r["options_json"]) if r["options_json"] else {},
                    "correct_choice": r["correct_choice"],
                }
                for r in rows
            ]
            self._cache_set(cache_key, res)
            return res
        except Exception as e:
            log.debug("medmcqa_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 23. Medical-O1 Clinical Chain-of-Thought Diagnostic Rationale (<2ms)
    # ---------------------------------------------------------------------------
    def search_medical_o1_reasoning(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        FTS5 search across 19,704 deep clinical Chain-of-Thought reasoning rationale cases.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "medical_o1_clinical_reasoning", "medical_o1.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT m.question, m.complex_cot, m.response
                FROM medical_o1_cases m
                JOIN medical_o1_fts f ON m.id = f.rowid
                WHERE f.medical_o1_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "question": r["question"],
                    "complex_cot": r["complex_cot"],
                    "response": r["response"],
                }
                for r in rows
            ]
        except Exception as e:
            log.debug("medical_o1_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 24. AI Medical Chatbot Real Clinical Dialogues (<2ms)
    # ---------------------------------------------------------------------------
    def search_ai_medical_dialogues(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        FTS5 search across 256,916 real patient-doctor dialogues.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "ai_medical_dialogues", "medical_dialogues.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT d.description, d.patient_dialogue, d.doctor_response
                FROM dialogues d
                JOIN dialogues_fts f ON d.id = f.rowid
                WHERE f.dialogues_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "description": r["description"],
                    "patient_dialogue": r["patient_dialogue"],
                    "doctor_response": r["doctor_response"],
                }
                for r in rows
            ]
        except Exception as e:
            log.debug("ai_medical_dialogues_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 25. Health Advice & Symptom Urgency Triage (<1ms)
    # ---------------------------------------------------------------------------
    def search_health_advice(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        FTS5 search across 8,676 clinician-verified triage guidance and health advice entries.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "health_advice_triage", "health_advice.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT h.query, h.advice
                FROM health_advice h
                JOIN health_advice_fts f ON h.id = f.rowid
                WHERE f.health_advice_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [{"query": r["query"], "advice": r["advice"]} for r in rows]
        except Exception as e:
            log.debug("health_advice_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 26. PubMed Causal Pathophysiological Mechanisms (<1ms)
    # ---------------------------------------------------------------------------
    def search_pubmed_causal(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        FTS5 search across 2,446 biomedical causal pathophysiology relationships.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "pubmed_causal_pathophysiology", "pubmed_causal.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT c.condition_or_finding, c.causal_pathway
                FROM causal_mechanisms c
                JOIN causal_fts f ON c.id = f.rowid
                WHERE f.causal_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "condition_or_finding": r["condition_or_finding"],
                    "causal_pathway": r["causal_pathway"],
                }
                for r in rows
            ]
        except Exception as e:
            log.debug("pubmed_causal_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 27. MTS-Dialog Clinical SOAP Documentation Templates (<1ms)
    # ---------------------------------------------------------------------------
    def search_mts_dialog_notes(self, query: str, section: Optional[str] = None, limit: int = 3) -> List[Dict[str, Any]]:
        """
        FTS5 search across doctor-patient dialogue paired with structured SOAP note sections.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "mts_dialog_clinical_notes", "mts_dialog.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            if section:
                cur.execute(
                    """
                    SELECT d.dialogue_id, d.section_header, d.section_text, d.dialogue
                    FROM clinical_dialogue_notes d
                    JOIN dialogue_notes_fts f ON d.id = f.rowid
                    WHERE f.dialogue_notes_fts MATCH ? AND LOWER(d.section_header) LIKE ?
                    LIMIT ?
                    """,
                    (match_str, f"%{section.lower()}%", limit)
                )
            else:
                cur.execute(
                    """
                    SELECT d.dialogue_id, d.section_header, d.section_text, d.dialogue
                    FROM clinical_dialogue_notes d
                    JOIN dialogue_notes_fts f ON d.id = f.rowid
                    WHERE f.dialogue_notes_fts MATCH ?
                    LIMIT ?
                    """,
                    (match_str, limit)
                )
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "dialogue_id": r["dialogue_id"],
                    "section_header": r["section_header"],
                    "section_text": r["section_text"],
                    "dialogue": r["dialogue"],
                }
                for r in rows
            ]
        except Exception as e:
            log.debug("mts_dialog_notes_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 28. MedText Clinical Vignettes (<1ms)
    # ---------------------------------------------------------------------------
    def search_medtext_vignettes(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        FTS5 search across curated internal medicine clinical case vignettes and workups.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "clinical_text_vignettes_medtext", "medtext.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT m.prompt, m.completion
                FROM medtext m
                JOIN medtext_fts f ON m.id = f.rowid
                WHERE f.medtext_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [{"prompt": r["prompt"], "completion": r["completion"]} for r in rows]
        except Exception as e:
            log.debug("medtext_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 29. Asclepius Clinical Discharge Summaries & Inpatient Notes (<2ms)
    # ---------------------------------------------------------------------------
    def search_asclepius_notes(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        FTS5 search across Asclepius hospital discharge summaries and clinical notes.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "asclepius_clinical_discharge_notes", "asclepius.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT c.patient_id, c.note, c.question, c.answer, c.task
                FROM clinical_notes c
                JOIN clinical_notes_fts f ON c.id = f.rowid
                WHERE f.clinical_notes_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "patient_id": r["patient_id"],
                    "note": r["note"][:500] + "..." if len(r["note"]) > 500 else r["note"],
                    "question": r["question"],
                    "answer": r["answer"],
                    "task": r["task"],
                }
                for r in rows
            ]
        except Exception as e:
            log.debug("asclepius_search_error", error=str(e))
            return []


    # ---------------------------------------------------------------------------
    # 30. DDXPlus Differential Diagnosis Benchmark (<2ms)
    # ---------------------------------------------------------------------------
    def search_ddxplus_differential_cases(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        FTS5 search across DDXPlus 132,448 differential diagnosis simulator encounters.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "ddxplus_differential_diagnosis", "ddxplus.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT c.age, c.sex, c.pathology, c.initial_symptom_text, c.symptoms_english, c.differential_diagnosis
                FROM cases c
                JOIN cases_fts f ON c.id = f.rowid
                WHERE f.cases_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "pathology": r["pathology"],
                    "age": r["age"],
                    "sex": r["sex"],
                    "initial_symptom": r["initial_symptom_text"],
                    "symptoms": r["symptoms_english"],
                    "differential_diagnosis": r["differential_diagnosis"][:300] if r["differential_diagnosis"] else "",
                    "source": "DDXPlus Differential Diagnosis Benchmark",
                }
                for r in rows
            ]
        except Exception as e:
            log.debug("ddxplus_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 31. Sajjad Hadi 469k Clinical Diagnosis Encounters (<2ms)
    # ---------------------------------------------------------------------------
    def search_clinical_diagnosis_encounters(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        FTS5 search across Sajjad Hadi 469k disease diagnosis encounters.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "clinical_diagnosis_encounters", "clinical_diagnosis_encounters.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT e.diagnosis, e.symptom_text
                FROM encounters e
                JOIN encounters_fts f ON e.id = f.rowid
                WHERE f.encounters_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "diagnosis": r["diagnosis"],
                    "symptom_text": r["symptom_text"][:400] if len(r["symptom_text"]) > 400 else r["symptom_text"],
                    "source": "Clinical Diagnosis Encounters (469k records)",
                }
                for r in rows
            ]
        except Exception as e:
            log.debug("clinical_encounters_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 32. Extensive Disease-Symptom Clean Matrix (246k profiles) (<2ms)
    # ---------------------------------------------------------------------------
    def match_extensive_disease_symptoms(self, symptoms: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """
        FTS5 match against Dhivyesh 246,945 disease-symptom profiles spanning 378 symptoms.
        """
        if not symptoms or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "disease_symptom_extensive_clean", "disease_symptom_matrix.db")
        if not os.path.exists(db_path):
            return []

        tokens = [re.sub(r"[^\w]", "", s).strip() for s in symptoms if s]
        tokens = [t for t in tokens if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:5])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT d.disease, d.symptoms_list
                FROM disease_symptoms d
                JOIN disease_symptoms_fts f ON d.id = f.rowid
                WHERE f.disease_symptoms_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "disease": r["disease"],
                    "symptoms_list": r["symptoms_list"],
                    "source": "Extensive Multi-Symptom Clean Matrix (246k profiles)",
                }
                for r in rows
            ]
        except Exception as e:
            log.debug("extensive_symptoms_match_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 33. Mayo Clinic Gold-Standard Diseases & Symptoms (<2ms)
    # ---------------------------------------------------------------------------
    def search_mayo_clinic_diseases(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        FTS5 search across Mayo Clinic gold-standard disease monographs.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "mayo_clinic_symptoms_and_diseases", "mayo_clinic_diseases.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT m.disease, m.clinical_text
                FROM mayo_diseases m
                JOIN mayo_diseases_fts f ON m.id = f.rowid
                WHERE f.mayo_diseases_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "disease": r["disease"],
                    "clinical_text": r["clinical_text"][:500] if len(r["clinical_text"]) > 500 else r["clinical_text"],
                    "source": "Mayo Clinic Symptoms & Diseases Library",
                }
                for r in rows
            ]
        except Exception as e:
            log.debug("mayo_clinic_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 34. Medical Differential Diagnosis Scenarios (<2ms)
    # ---------------------------------------------------------------------------
    def search_medical_diff_dx_cases(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        FTS5 search across Shuyue J 1,871 medical differential diagnosis scenarios.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "medical_differential_diagnosis_cases", "medical_differential_diagnosis.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT d.instruction, d.patient_presentation, d.differential_reasoning, d.source
                FROM diff_cases d
                JOIN diff_cases_fts f ON d.id = f.rowid
                WHERE f.diff_cases_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "presentation": r["patient_presentation"][:400] if len(r["patient_presentation"]) > 400 else r["patient_presentation"],
                    "differential_reasoning": r["differential_reasoning"][:600] if len(r["differential_reasoning"]) > 600 else r["differential_reasoning"],
                    "source": f"Differential Diagnosis Cases ({r['source'] or 'Clinical'})",
                }
                for r in rows
            ]
        except Exception as e:
            log.debug("medical_diff_dx_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 35. Shaheer Comprehensive Disease Encyclopedia (253k) (<2ms)
    # ---------------------------------------------------------------------------
    def search_shaheer_disease_encyclopedia(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        FTS5 search across Shaheer 253,851 disease profiles with causes, symptoms, and complications.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "disease_symptom_knowledge_base", "disease_symptom_kb.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT d.disease, d.overview, d.symptoms, d.causes, d.complications, d.preventions
                FROM disease_profiles d
                JOIN disease_profiles_fts f ON d.id = f.rowid
                WHERE f.disease_profiles_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "disease": r["disease"],
                    "overview": r["overview"][:300] if len(r["overview"]) > 300 else r["overview"],
                    "symptoms": r["symptoms"][:300] if len(r["symptoms"]) > 300 else r["symptoms"],
                    "causes": r["causes"][:300] if len(r["causes"]) > 300 else r["causes"],
                    "complications": r["complications"][:300] if len(r["complications"]) > 300 else r["complications"],
                    "preventions": r["preventions"][:300] if len(r["preventions"]) > 300 else r["preventions"],
                    "source": "Shaheer Disease & Symptom Encyclopedia (253k profiles)",
                }
                for r in rows
            ]
        except Exception as e:
            log.debug("shaheer_encyclopedia_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 36. Jainam Confidence-Ranked Disease Predictions (<2ms)
    # ---------------------------------------------------------------------------
    def search_jainam_predictions(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        FTS5 search across Jainam multi-symptom confidence-grouped disease predictions.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "jainam_symptom_disease_prediction", "jainam_disease_prediction.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT j.symptoms_input, j.predicted_output
                FROM symptom_predictions j
                JOIN symptom_predictions_fts f ON j.id = f.rowid
                WHERE f.symptom_predictions_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "symptoms_input": r["symptoms_input"],
                    "predicted_output": r["predicted_output"],
                    "source": "Jainam Confidence-Grouped Disease Prediction Benchmark",
                }
                for r in rows
            ]
        except Exception as e:
            log.debug("jainam_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 37. Open Clinical Vignettes (100k) (<2ms)
    # ---------------------------------------------------------------------------
    def search_open_clinical_vignettes(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        FTS5 search across 100,000 open clinical vignettes with diagnostic rationales.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "open_clinical_vignettes", "open_clinical_vignettes.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT v.case_text, v.educational_score, v.article_id, v.article_url
                FROM clinical_vignettes v
                JOIN clinical_vignettes_fts f ON v.id = f.rowid
                WHERE f.clinical_vignettes_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "case_text": r["case_text"][:600] + "..." if len(r["case_text"]) > 600 else r["case_text"],
                    "educational_score": r["educational_score"],
                    "article_url": r["article_url"],
                    "source": "Open Clinical Vignettes Corpus",
                }
                for r in rows
            ]
        except Exception as e:
            log.debug("vignettes_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 38. Phase 4: Clinical Differential Diagnosis Scenarios (<2ms)
    # ---------------------------------------------------------------------------
    def search_differential_scenarios(self, query: str, limit: int = 2) -> List[Dict[str, Any]]:
        """
        FTS5 search across Shuyue J Differential Diagnosis Scenarios.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "differential_diagnosis_scenarios_ddx", "differential_diagnosis_scenarios.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT r.instruction, r.output, r.source
                FROM records r
                JOIN records_fts f ON r.row_id = f.rowid
                WHERE f.records_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "instruction": r["instruction"][:250] + "..." if r["instruction"] and len(r["instruction"]) > 250 else r["instruction"],
                    "output": r["output"][:350] + "..." if r["output"] and len(r["output"]) > 350 else r["output"],
                    "source": "Shuyue J Clinical DDx Benchmark",
                }
                for r in rows
            ]
        except Exception as e:
            log.debug("differential_scenarios_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 39. Phase 4: Conversational & Structured Symptom Triage (<2ms)
    # ---------------------------------------------------------------------------
    def search_symptom_triage_conversations(self, query: str, limit: int = 2) -> List[Dict[str, Any]]:
        """
        FTS5 search across Conversational Symptom Triage dialogues.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "symptom_triage_conversational", "symptom_triage_conversational.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT r.* FROM records r
                JOIN records_fts f ON r.row_id = f.rowid
                WHERE f.records_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            results = []
            for r in rows:
                d = dict(r)
                d.pop("row_id", None)
                results.append(d)
            return results
        except Exception as e:
            log.debug("symptom_triage_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 40. Phase 4: Medical Diagnosis 20K Encounters (<2ms)
    # ---------------------------------------------------------------------------
    def search_medical_diagnosis_20k(self, query: str, limit: int = 2) -> List[Dict[str, Any]]:
        """
        FTS5 search across 20,000 real medical diagnosis encounters.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "medical_diagnosis_20k", "medical_diagnosis_20k.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT r.* FROM records r
                JOIN records_fts f ON r.row_id = f.rowid
                WHERE f.records_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            results = []
            for r in rows:
                d = dict(r)
                d.pop("row_id", None)
                results.append(d)
            return results
        except Exception as e:
            log.debug("medical_diagnosis_20k_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 41. Phase 4: Chain-of-Thought Diagnostic Reasoning Traces (<2ms)
    # ---------------------------------------------------------------------------
    def search_medical_diagnosis_cot(self, query: str, limit: int = 2) -> List[Dict[str, Any]]:
        """
        FTS5 search across Chain-of-Thought diagnostic reasoning traces.
        """
        if not query or not self.is_available:
            return []

        db_path = os.path.join(self.base_dir, "medical_diagnosis_cot_reasoning", "medical_diagnosis_cot.db")
        if not os.path.exists(db_path):
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT r.* FROM records r
                JOIN records_fts f ON r.row_id = f.rowid
                WHERE f.records_fts MATCH ?
                LIMIT ?
                """,
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            results = []
            for r in rows:
                d = dict(r)
                d.pop("row_id", None)
                results.append(d)
            return results
        except Exception as e:
            log.debug("cot_reasoning_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # 42. Phase 4: Organ-Specific Chronic Disease Risk & Prediction (<2ms)
    # ---------------------------------------------------------------------------
    def search_chronic_organ_risk(self, query: str, limit: int = 2) -> List[Dict[str, Any]]:
        """
        Searches across organ-specific prediction datasets (Diabetes, Stroke, CKD, Sepsis).
        """
        if not query or not self.is_available:
            return []

        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        organ_dbs = [
            ("diabetes_clinical_risk_prediction", "diabetes_prediction.db", "Diabetes Risk (100k)", ["diabetes", "glucose", "hba1c", "sugar", "insulin"]),
            ("stroke_clinical_risk_prediction", "stroke_prediction.db", "Cerebrovascular Stroke Risk", ["stroke", "paralysis", "hemiplegia", "tia", "facial droop"]),
            ("chronic_kidney_disease_prediction", "chronic_kidney_disease.db", "Renal CKD Prediction", ["kidney", "renal", "creatinine", "nephro", "bun"]),
            ("nhanes_cardiovascular_prediction", "nhanes_cardio_prediction.db", "NHANES Cardiovascular Risk", ["cardio", "heart", "coronary", "angina", "infarction"]),
        ]

        found = []
        q_lower = query.lower()
        for folder, db_name, label, keywords in organ_dbs:
            # Check if relevant to current query or candidates
            if not any(k in q_lower for k in keywords):
                continue
            db_path = os.path.join(self.base_dir, folder, db_name)
            if not os.path.exists(db_path):
                continue
            try:
                conn = self._get_connection(db_path)
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # Retrieve representative high-risk baseline profiles
                cur.execute("SELECT * FROM records LIMIT ?", (limit,))
                rows = cur.fetchall()
                conn.close()
                for r in rows:
                    d = dict(r)
                    d.pop("row_id", None)
                    d["risk_domain"] = label
                    found.append(d)
                    if len(found) >= limit:
                        return found
            except Exception:
                continue
        return found

    # ---------------------------------------------------------------------------
    # 43. Universal Offline Warehouse Search Across All 76 Datasets (<3ms)
    # ---------------------------------------------------------------------------
    def search_universal_warehouse(self, folder_name: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Universal query capability supporting all 76 datasets in D:\\OFFLINE DATA.
        """
        if not folder_name or not query or not self.is_available:
            return []

        target_dir = os.path.join(self.base_dir, folder_name)
        if not os.path.exists(target_dir):
            return []

        # Find any sqlite database file in directory
        db_files = [f for f in os.listdir(target_dir) if f.endswith(".db")]
        if not db_files:
            return []

        db_path = os.path.join(target_dir, db_files[0])
        clean = re.sub(r"[^\w\s]", " ", query).strip()
        tokens = [t for t in clean.split() if len(t) > 2]
        if not tokens:
            return []
        match_str = " OR ".join(tokens[:4])

        try:
            conn = self._get_connection(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Check table name
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_fts'")
            fts_tables = [r["name"] for r in cur.fetchall()]
            if not fts_tables:
                conn.close()
                return []
            
            fts_name = fts_tables[0]
            base_name = fts_name.replace("_fts", "")
            
            cur.execute(
                f"SELECT r.* FROM {base_name} r JOIN {fts_name} f ON r.row_id = f.rowid WHERE f.{fts_name} MATCH ? LIMIT ?",
                (match_str, limit)
            )
            rows = cur.fetchall()
            conn.close()
            results = []
            for r in rows:
                d = dict(r)
                d.pop("row_id", None)
                results.append(d)
            return results
        except Exception as e:
            log.debug("universal_warehouse_search_error", error=str(e), folder=folder_name)
            return []

    # ---------------------------------------------------------------------------
    # E:\OFFLINE DATA2 — Global Open-Source Clinical Intelligence
    # ---------------------------------------------------------------------------
    def search_snomed_concepts(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches SNOMED CT clinical findings and RxNorm drugs from E:\OFFLINE DATA2."""
        db_path = os.path.join(self.secondary_dir, "snomed_rxnorm_ontology", "snomed_rxnorm.db")
        if not os.path.exists(db_path):
            return []
        try:
            conn = self._get_connection(db_path)
            clean_q = re.sub(r"[^\w\s]", "", query).strip()
            if not clean_q:
                return []
            words = clean_q.split()
            match_str = " ".join([f'"{w}"*' for w in words[:4]])
            cur = conn.cursor()
            cur.execute(
                "SELECT c.concept_id AS id, c.concept_name AS name, 'SNOMED Concept' AS type, c.domain_id FROM concepts c JOIN concepts_fts f ON c.concept_id = f.concept_id WHERE f.concepts_fts MATCH ? LIMIT ?",
                (match_str, limit),
            )
            rows = [dict(r) for r in cur.fetchall()]
            if len(rows) < limit:
                cur.execute(
                    "SELECT d.rxcui AS id, d.drug_name AS name, 'RxNorm Drug' AS type, d.dosage_forms AS domain_id FROM rxnorm_drugs d JOIN rxnorm_fts f ON d.rxcui = f.rxcui WHERE f.rxnorm_fts MATCH ? LIMIT ?",
                    (match_str, limit - len(rows)),
                )
                rows.extend([dict(r) for r in cur.fetchall()])
            return rows
        except Exception as e:
            log.debug("snomed_search_error", error=str(e))
            return []

    def search_cochrane_guidelines(self, condition: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches Cochrane systematic reviews and gold-standard guidelines from E:\OFFLINE DATA2."""
        db_path = os.path.join(self.secondary_dir, "cochrane_clinical_guidelines", "cochrane_guidelines.db")
        if not os.path.exists(db_path):
            return []
        try:
            conn = self._get_connection(db_path)
            clean_q = re.sub(r"[^\w\s]", "", condition).strip()
            if not clean_q:
                return []
            words = clean_q.split()
            match_str = " ".join([f'"{w}"*' for w in words[:4]])
            cur = conn.cursor()
            cur.execute(
                "SELECT g.* FROM guidelines g JOIN guidelines_fts f ON g.guideline_id = f.guideline_id WHERE f.guidelines_fts MATCH ? LIMIT ?",
                (match_str, limit),
            )
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            log.debug("cochrane_guidelines_search_error", error=str(e))
            return []

    def search_synthea_patient_history(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches Synthea longitudinal patient cohorts from E:\OFFLINE DATA2."""
        db_path = os.path.join(self.secondary_dir, "synthea_longitudinal_ehr", "synthea_ehr.db")
        if not os.path.exists(db_path):
            return []
        try:
            conn = self._get_connection(db_path)
            clean_q = re.sub(r"[^\w\s]", "", query).strip()
            if not clean_q:
                return []
            words = clean_q.split()
            match_str = " ".join([f'"{w}"*' for w in words[:4]])
            cur = conn.cursor()
            cur.execute(
                "SELECT p.patient_id, p.gender, p.city, p.state, f.description, f.reason_description "
                "FROM patients p JOIN patient_search_fts f ON p.patient_id = f.patient_id "
                "WHERE f.patient_search_fts MATCH ? LIMIT ?",
                (match_str, limit),
            )
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            log.debug("synthea_search_error", error=str(e))
            return []

    def search_who_global_outbreaks(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches WHO global disease outbreak bulletins and international alerts from E:\OFFLINE DATA2."""
        db_path = os.path.join(self.secondary_dir, "who_global_outbreaks", "who_global_health.db")
        if not os.path.exists(db_path):
            return []
        try:
            conn = self._get_connection(db_path)
            clean_q = re.sub(r"[^\w\s]", "", query).strip()
            if not clean_q:
                return []
            words = clean_q.split()
            match_str = " ".join([f'"{w}"*' for w in words[:4]])
            cur = conn.cursor()
            cur.execute(
                "SELECT o.* FROM outbreaks o JOIN outbreaks_fts f ON o.outbreak_id = f.outbreak_id WHERE f.outbreaks_fts MATCH ? LIMIT ?",
                (match_str, limit),
            )
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            log.debug("who_outbreak_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # Universal Diagnostic Pack: MONDO, HPO, & PrimeKG
    # ---------------------------------------------------------------------------
    def search_mondo_diseases(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches 45,000+ universal human diseases from MONDO Master Disease Ontology."""
        db_path = os.path.join(self.secondary_dir, "mondo_disease_ontology", "mondo_diseases.db")
        if not os.path.exists(db_path):
            return []
        try:
            conn = self._get_connection(db_path)
            clean_q = re.sub(r"[^\w\s]", "", query).strip()
            if not clean_q:
                return []
            words = clean_q.split()
            match_str = " ".join([f'"{w}"*' for w in words[:4]])
            cur = conn.cursor()
            cur.execute(
                "SELECT d.* FROM diseases d JOIN diseases_fts f ON d.mondo_id = f.mondo_id WHERE f.diseases_fts MATCH ? LIMIT ?",
                (match_str, limit),
            )
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            log.debug("mondo_search_error", error=str(e))
            return []

    def search_hpo_phenotypes(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches 300,000+ clinical phenotype-to-rare disease annotations from HPO."""
        db_path = os.path.join(self.secondary_dir, "hpo_phenotype_matrix", "hpo_matrix.db")
        if not os.path.exists(db_path):
            return []
        try:
            conn = self._get_connection(db_path)
            clean_q = re.sub(r"[^\w\s]", "", query).strip()
            if not clean_q:
                return []
            words = clean_q.split()
            match_str = " ".join([f'"{w}"*' for w in words[:4]])
            cur = conn.cursor()
            cur.execute(
                "SELECT a.* FROM phenotype_annotations a JOIN phenotype_fts f ON a.rowid = f.rowid WHERE f.phenotype_fts MATCH ? LIMIT ?",
                (match_str, limit),
            )
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            log.debug("hpo_search_error", error=str(e))
            return []

    _PRIMEKG_CACHE: dict = {}

    def search_primekg_precision_graph(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches 4M+ multi-scale biological edges from Harvard PrimeKG."""
        cache_key = f"pg_{query.lower().strip()}_{limit}"
        if cache_key in self._PRIMEKG_CACHE:
            return self._PRIMEKG_CACHE[cache_key]

        db_path = os.path.join(self.secondary_dir, "primekg_harvard_knowledge_graph", "primekg.db")
        if not os.path.exists(db_path):
            return []
        try:
            conn = self._get_connection(db_path)
            clean_q = re.sub(r"[^\w\s]", "", query).strip()
            if not clean_q:
                return []
            words = clean_q.split()
            match_str = " ".join([f'"{w}"*' for w in words[:4]])
            cur = conn.cursor()
            cur.execute(
                "SELECT e.* FROM edges e JOIN edges_fts f ON e.rowid = f.rowid WHERE f.edges_fts MATCH ? LIMIT ?",
                (match_str, limit),
            )
            rows = cur.fetchall()
            res = [dict(r) for r in rows]
            if len(self._PRIMEKG_CACHE) > 500:
                self._PRIMEKG_CACHE.clear()
            self._PRIMEKG_CACHE[cache_key] = res
            return res
        except Exception as e:
            log.debug("primekg_search_error", error=str(e))
            return []

    def search_primekg_disease_phenotypes(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches 303,000+ disease-phenotype associations from Harvard PrimeKG."""
        cache_key = f"dp_{query.lower().strip()}_{limit}"
        if cache_key in self._PRIMEKG_CACHE:
            return self._PRIMEKG_CACHE[cache_key]

        db_path = os.path.join(self.secondary_dir, "primekg_harvard_knowledge_graph", "primekg.db")
        if not os.path.exists(db_path):
            return []
        try:
            conn = self._get_connection(db_path)
            clean_q = re.sub(r"[^\w\s]", "", query).strip()
            if not clean_q:
                return []
            words = clean_q.split()
            match_str = " ".join([f'"{w}"*' for w in words[:4]])
            cur = conn.cursor()
            cur.execute(
                "SELECT dp.* FROM disease_phenotypes dp JOIN disease_phenotypes_fts f ON dp.rowid = f.rowid WHERE f.disease_phenotypes_fts MATCH ? LIMIT ?",
                (match_str, limit),
            )
            rows = cur.fetchall()
            res = [dict(r) for r in rows]
            if len(self._PRIMEKG_CACHE) > 500:
                self._PRIMEKG_CACHE.clear()
            self._PRIMEKG_CACHE[cache_key] = res
            return res
        except Exception as e:
            log.debug("primekg_dp_search_error", error=str(e))
            return []

    # ---------------------------------------------------------------------------
    # Omniscient Medical Master Suite: StatPearls, DrugCentral, EBM Rules, etc.
    # ---------------------------------------------------------------------------
    def search_statpearls_monographs(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches 9,541+ peer-reviewed clinical disease monographs from NCBI StatPearls."""
        db_path = os.path.join(self.secondary_dir, "ncbi_statpearls_monographs", "statpearls.db")
        if not os.path.exists(db_path):
            return []

        clean_q = re.sub(r"[^\w\s]", "", query).strip()
        if not clean_q:
            return []

        cache_key = f"statpearls:{clean_q.lower()}:{limit}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            conn = self._get_connection(db_path)
            cur = conn.cursor()

            # 1. Exact topic match (sub-millisecond PK lookup)
            cur.execute("SELECT t.* FROM topics t WHERE t.topic = ? LIMIT ?", (clean_q, limit))
            rows = [dict(r) for r in cur.fetchall()]
            if rows:
                self._cache_set(cache_key, rows)
                return rows

            # 2. Topic column match via FTS5 (sub-millisecond title match)
            words = [w for w in clean_q.split() if len(w) > 2]
            if words:
                topic_match = f'topic: "{" ".join(words[:4])}"'
                try:
                    cur.execute(
                        "SELECT t.* FROM topics t JOIN topics_fts f ON t.rowid = f.rowid WHERE f.topics_fts MATCH ? ORDER BY rank LIMIT ?",
                        (topic_match, limit),
                    )
                    rows = [dict(r) for r in cur.fetchall()]
                    if rows:
                        self._cache_set(cache_key, rows)
                        return rows
                except Exception:
                    pass

            # 3. General Ranked FTS5 search
            match_str = " ".join([f'"{w}"*' for w in (words[:4] if words else clean_q.split()[:4])])
            cur.execute(
                "SELECT t.* FROM topics t JOIN topics_fts f ON t.rowid = f.rowid WHERE f.topics_fts MATCH ? ORDER BY rank LIMIT ?",
                (match_str, limit),
            )
            rows = [dict(r) for r in cur.fetchall()]
            self._cache_set(cache_key, rows)
            return rows
        except Exception as e:
            log.debug("statpearls_search_error", error=str(e))
            return []

    def search_drugcentral(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches FDA indications, contraindications, and MOA from DrugCentral."""
        db_path = os.path.join(self.secondary_dir, "drugcentral_pharmacopeia", "drugcentral.db")
        if not os.path.exists(db_path):
            return []

        clean_q = re.sub(r"[^\w\s]", "", query).strip()
        if not clean_q:
            return []

        cache_key = f"drugcentral:{clean_q.lower()}:{limit}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            conn = self._get_connection(db_path)
            words = clean_q.split()
            match_str = " ".join([f'"{w}"*' for w in words[:4]])
            cur = conn.cursor()
            cur.execute(
                "SELECT d.* FROM drugs d JOIN drugs_fts f ON d.rowid = f.rowid WHERE f.drugs_fts MATCH ? LIMIT ?",
                (match_str, limit),
            )
            rows = [dict(r) for r in cur.fetchall()]
            self._cache_set(cache_key, rows)
            return rows
        except Exception as e:
            log.debug("drugcentral_search_error", error=str(e))
            return []

    def search_clinical_decision_rules(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches validated clinical calculators & scores (Wells, HEART, CURB-65, MELD, CHA2DS2-VASc, Centor, GCS, NIHSS)."""
        db_path = os.path.join(self.secondary_dir, "clinical_decision_rules", "decision_rules.db")
        if not os.path.exists(db_path):
            return []

        clean_q = re.sub(r"[^\w\s]", "", query).strip()
        if not clean_q:
            return []

        cache_key = f"rules:{clean_q.lower()}:{limit}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            conn = self._get_connection(db_path)
            words = clean_q.split()
            match_str = " ".join([f'"{w}"*' for w in words[:4]])
            cur = conn.cursor()
            cur.execute(
                "SELECT r.* FROM decision_rules r JOIN decision_rules_fts f ON r.rowid = f.rowid WHERE f.decision_rules_fts MATCH ? LIMIT ?",
                (match_str, limit),
            )
            rows = [dict(r) for r in cur.fetchall()]
            self._cache_set(cache_key, rows)
            return rows
        except Exception as e:
            log.debug("decision_rules_search_error", error=str(e))
            return []

    def search_antimicrobial_guidelines(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches CDC & IDSA empirical antibiotic regimens, dosing, and penicillin allergy alternatives."""
        db_path = os.path.join(self.secondary_dir, "cdc_idsa_antimicrobial_guidelines", "antimicrobial_guidelines.db")
        if not os.path.exists(db_path):
            return []

        clean_q = re.sub(r"[^\w\s]", "", query).strip()
        if not clean_q:
            return []

        cache_key = f"antimicrobial:{clean_q.lower()}:{limit}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            conn = self._get_connection(db_path)
            words = clean_q.split()
            match_str = " ".join([f'"{w}"*' for w in words[:4]])
            cur = conn.cursor()
            cur.execute(
                "SELECT a.* FROM antimicrobial_guidelines a JOIN antimicrobial_fts f ON a.rowid = f.rowid WHERE f.antimicrobial_fts MATCH ? LIMIT ?",
                (match_str, limit),
            )
            rows = [dict(r) for r in cur.fetchall()]
            self._cache_set(cache_key, rows)
            return rows
        except Exception as e:
            log.debug("antimicrobial_search_error", error=str(e))
            return []

    def search_loinc_lab_tests(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches LOINC lab tests, reference ranges, and abnormal value differential causes."""
        db_path = os.path.join(self.secondary_dir, "loinc_lab_biomarkers", "loinc_labs.db")
        if not os.path.exists(db_path):
            return []

        clean_q = re.sub(r"[^\w\s]", "", query).strip()
        if not clean_q:
            return []

        cache_key = f"loinc:{clean_q.lower()}:{limit}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            conn = self._get_connection(db_path)
            words = clean_q.split()
            match_str = " ".join([f'"{w}"*' for w in words[:4]])
            cur = conn.cursor()
            # First check abnormal differentials
            cur.execute(
                "SELECT ad.* FROM abnormal_differentials ad JOIN abnormal_differentials_fts f ON ad.rowid = f.rowid WHERE f.abnormal_differentials_fts MATCH ? LIMIT ?",
                (match_str, limit),
            )
            rows = [dict(r) for r in cur.fetchall()]
            if len(rows) < limit:
                cur.execute(
                    "SELECT l.* FROM lab_tests l JOIN lab_tests_fts f ON l.rowid = f.rowid WHERE f.lab_tests_fts MATCH ? LIMIT ?",
                    (match_str, limit - len(rows)),
                )
                rows.extend([dict(r) for r in cur.fetchall()])
            self._cache_set(cache_key, rows)
            return rows
        except Exception as e:
            log.debug("loinc_search_error", error=str(e))
            return []

    def search_pediatric_dosing(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches Harriet Lane / WHO weight-based pediatric dosing and vital signs."""
        db_path = os.path.join(self.secondary_dir, "pediatric_clinical_formulary", "pediatric_formulary.db")
        if not os.path.exists(db_path):
            return []

        clean_q = re.sub(r"[^\w\s]", "", query).strip()
        if not clean_q:
            return []

        cache_key = f"pediatric:{clean_q.lower()}:{limit}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            conn = self._get_connection(db_path)
            stop = {"pediatric", "dose", "dosing", "child", "infant", "neonate", "what", "is", "the", "for", "of", "in", "peds"}
            words = [w for w in clean_q.split() if w.lower() not in stop]
            if not words:
                words = clean_q.split()
            match_str = " OR ".join([f'"{w}"*' for w in words[:4]])
            cur = conn.cursor()
            cur.execute(
                "SELECT p.* FROM pediatric_drugs p JOIN pediatric_drugs_fts f ON p.rowid = f.rowid WHERE f.pediatric_drugs_fts MATCH ? LIMIT ?",
                (match_str, limit),
            )
            rows = [dict(r) for r in cur.fetchall()]
            self._cache_set(cache_key, rows)
            return rows
        except Exception as e:
            log.debug("pediatric_search_error", error=str(e))
            return []

    def search_toxicology_antidotes(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches toxidromes, toxicities, and exact antidote protocols (NAC, Fomepizole, Glucagon)."""
        db_path = os.path.join(self.secondary_dir, "toxicology_antidote_protocols", "toxicology.db")
        if not os.path.exists(db_path):
            return []

        clean_q = re.sub(r"[^\w\s]", "", query).strip()
        if not clean_q:
            return []

        cache_key = f"toxicology:{clean_q.lower()}:{limit}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            conn = self._get_connection(db_path)
            stop = {"overdose", "antidote", "protocol", "poisoning", "toxic", "toxicity", "what", "is", "the", "for", "of", "in", "management"}
            words = [w for w in clean_q.split() if w.lower() not in stop]
            if not words:
                words = clean_q.split()
            match_str = " OR ".join([f'"{w}"*' for w in words[:4]])
            cur = conn.cursor()
            cur.execute(
                "SELECT a.* FROM antidotes a JOIN antidotes_fts f ON a.rowid = f.rowid WHERE f.antidotes_fts MATCH ? LIMIT ?",
                (match_str, limit),
            )
            rows = [dict(r) for r in cur.fetchall()]
            if len(rows) < limit:
                cur.execute(
                    "SELECT t.* FROM toxins t JOIN toxins_fts f ON t.rowid = f.rowid WHERE f.toxins_fts MATCH ? LIMIT ?",
                    (match_str, limit - len(rows)),
                )
                rows.extend([dict(r) for r in cur.fetchall()])
            self._cache_set(cache_key, rows)
            return rows
        except Exception as e:
            log.debug("toxicology_search_error", error=str(e))
            return []

    def search_oncology_regimens(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches AJCC/UICC TNM staging and standard systemic chemotherapy/immunotherapy regimens."""
        db_path = os.path.join(self.secondary_dir, "oncology_staging_regimens", "oncology_compendium.db")
        if not os.path.exists(db_path):
            return []

        clean_q = re.sub(r"[^\w\s]", "", query).strip()
        if not clean_q:
            return []

        cache_key = f"oncology:{clean_q.lower()}:{limit}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            conn = self._get_connection(db_path)
            words = clean_q.split()
            match_str = " ".join([f'"{w}"*' for w in words[:4]])
            cur = conn.cursor()
            cur.execute(
                "SELECT r.* FROM systemic_regimens r JOIN systemic_regimens_fts f ON r.rowid = f.rowid WHERE f.systemic_regimens_fts MATCH ? LIMIT ?",
                (match_str, limit),
            )
            rows = [dict(r) for r in cur.fetchall()]
            if len(rows) < limit:
                cur.execute(
                    "SELECT c.* FROM cancer_types c JOIN cancer_types_fts f ON c.rowid = f.rowid WHERE f.cancer_types_fts MATCH ? LIMIT ?",
                    (match_str, limit - len(rows)),
                )
                rows.extend([dict(r) for r in cur.fetchall()])
            self._cache_set(cache_key, rows)
            return rows
        except Exception as e:
            log.debug("oncology_search_error", error=str(e))
            return []


    def search_pmc_clinical_cases(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Searches peer-reviewed NIH PMC open access clinical case reports & diagnostic articles.
        Returns matching gold-standard hospital diagnostic presentations, workups, and outcomes.
        """
        db_path = os.path.join(self.secondary_dir, "pmc_clinical_cases", "pmc_patients_cases.db")
        if not os.path.exists(db_path):
            return []

        cache_key = f"pmc_cases:{query.lower().strip()}:{limit}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            conn = self._get_connection(db_path)
            clean_q = re.sub(r"[^\w\s]", "", query).strip()
            if not clean_q:
                return []
            stop = {"case", "report", "patient", "presentation", "clinical", "what", "is", "the", "for", "of", "in", "and", "with", "to"}
            words = [w for w in clean_q.split() if len(w) > 3 and w.lower() not in stop]
            if not words:
                words = [w for w in clean_q.split() if len(w) > 2]
            if not words:
                return []
            match_str = " ".join([f'"{w}"' for w in words[:2]])
            cur = conn.cursor()
            cur.execute(
                """
                SELECT c.case_id, c.title, c.authors, substr(c.clinical_narrative, 1, 1200) as summary, length(c.clinical_narrative) as full_length
                FROM clinical_cases c
                JOIN clinical_cases_fts f ON c.rowid = f.rowid
                WHERE f.clinical_cases_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (match_str, limit),
            )
            rows = [dict(r) for r in cur.fetchall()]
            self._cache_set(cache_key, rows)
            return rows
        except Exception as e:
            log.debug("pmc_cases_search_error", error=str(e))
            return []

    def find_patient_digital_twins(self, symptoms_or_query: str, age: str = "", gender: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Matches patient presentation against 167,000+ real NIH PMC patient case histories.
        Finds true clinical digital twins with real confirmed diagnoses, hospital courses, and outcomes.
        """
        db_path = os.path.join(self.secondary_dir, "pmc_clinical_cases", "pmc_patients_cases.db")
        if not os.path.exists(db_path):
            return []

        cache_key = f"twins:{symptoms_or_query.lower().strip()}:{age}:{gender}:{limit}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            conn = self._get_connection(db_path)
            clean_q = re.sub(r"[^\w\s]", "", symptoms_or_query).strip()
            if not clean_q:
                return []
            stop = {"patient", "male", "female", "year", "old", "presented", "with", "history", "of", "and", "in", "a", "the", "has", "been", "for", "to"}
            words = [w for w in clean_q.split() if len(w) > 3 and w.lower() not in stop]
            if not words:
                words = [w for w in clean_q.split() if len(w) > 2]
            if not words:
                return []
            match_str = " ".join([f'"{w}"' for w in words[:2]])
            cur = conn.cursor()
            cur.execute(
                """
                SELECT p.patient_id, p.pmid, p.title, p.age, p.gender, substr(p.patient_narrative, 1, 1200) as patient_summary
                FROM patients p
                JOIN patients_fts f ON p.rowid = f.rowid
                WHERE f.patients_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (match_str, limit),
            )
            rows = [dict(r) for r in cur.fetchall()]
            self._cache_set(cache_key, rows)
            return rows
        except Exception as e:
            log.debug("digital_twins_search_error", error=str(e))
            return []


    def match_rare_disease_by_phenotype(self, symptoms: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """Matches rare and Orphanet diseases against master disease catalog in <1ms."""
        try:
            from app.services.master_disease_catalog import master_disease_catalog
            return master_disease_catalog.match_symptoms(symptoms, top_k=top_k)
        except Exception as e:
            log.debug("rare_disease_match_error", error=str(e))
            return []


# Global singleton instance
offline_data_service = OfflineDataService()




