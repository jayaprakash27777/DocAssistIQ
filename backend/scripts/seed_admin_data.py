"""DocAssistIQ — Seed Comprehensive Admin Test Data.

Populates all admin modules with realistic, interconnected data:
1. Doctor Verifications (pending credentials)
2. Medical Sources (verified and registered)
3. Knowledge Ingestion Jobs (various statuses)
4. Medical Knowledge Entities (Diseases, Symptoms, Investigations, Medicines)
   with linked Article and Evidence provenance
5. Datasets (approved and pending validation)
6. Evaluation Harness Runs (with record-level results)
7. ML Experiment Runs (with hyperparameters, metrics, and durations)
"""

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.user import User
from app.models.doctor import Doctor
from app.models.provenance import Source, Article, Evidence
from app.models.ingestion import IngestionJob
from app.models.knowledge import Disease, Symptom, Investigation, Medicine
from app.models.dataset import Dataset
from app.models.evaluation import EvaluationRun, EvaluationResult
from app.models.experiment import MLExperiment


async def seed_data():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Find or use existing admin
        admin_user = (await session.execute(select(User).where(User.role == "admin"))).scalars().first()
        admin_id = admin_user.id if admin_user else None

        # ----------------------------------------------------
        # 1. Pending Doctors for Verification
        # ----------------------------------------------------
        print("Seeding Pending Doctors...")
        doc1_user = User(
            id=uuid.uuid4(),
            email=f"dr.jenkins_{uuid.uuid4().hex[:6]}@hospital.org",
            password_hash="$2b$12$dummyhashfordemonstrationonly",
            full_name="Dr. Sarah Jenkins, MD",
            role="doctor",
            is_active=True,
            is_verified=False,
        )
        session.add(doc1_user)

        doc2_user = User(
            id=uuid.uuid4(),
            email=f"dr.chen_{uuid.uuid4().hex[:6]}@hospital.org",
            password_hash="$2b$12$dummyhashfordemonstrationonly",
            full_name="Dr. Robert Chen, MD, PhD",
            role="doctor",
            is_active=True,
            is_verified=False,
        )
        session.add(doc2_user)
        await session.flush()

        doc1 = Doctor(
            id=uuid.uuid4(),
            user_id=doc1_user.id,
            specialty="Cardiology",
            credential_reference="ABIM-CARD-992140",
            credential_body="American Board of Internal Medicine (Cardiovascular Disease)",
            bio="Senior Interventional Cardiologist with 12 years of clinical practice.",
            verification_status="pending",
        )
        session.add(doc1)

        doc2 = Doctor(
            id=uuid.uuid4(),
            user_id=doc2_user.id,
            specialty="Neurology",
            credential_reference="ABPN-NEURO-44120",
            credential_body="American Board of Psychiatry and Neurology",
            bio="Neurology consultant specializing in cerebrovascular disorders.",
            verification_status="pending",
        )
        session.add(doc2)
        await session.flush()

        # ----------------------------------------------------
        # 2. Medical Sources
        # ----------------------------------------------------
        print("Seeding Medical Sources...")
        src_who = await session.scalar(select(Source).where(Source.code == "who_guidelines_2024"))
        if not src_who:
            src_who = Source(
                id=uuid.uuid4(),
                code="who_guidelines_2024",
                name="WHO Clinical Practice Guidelines 2024",
                organisation="World Health Organization",
                base_url="https://www.who.int/publications/guidelines",
                access_mechanism="api",
                data_type="clinical_guidelines",
                license_info="Open Access (CC BY-NC-SA 3.0 IGO)",
                is_production_suitable=True,
                status="active",
                last_verified_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            )
            session.add(src_who)

        src_pubmed = await session.scalar(select(Source).where(Source.code == "pubmed_central"))
        if not src_pubmed:
            src_pubmed = Source(
                id=uuid.uuid4(),
                code="pubmed_central",
                name="PubMed Central Biomedical Repository",
                organisation="NIH / NLM",
                base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
                access_mechanism="api",
                data_type="literature",
                license_info="Open Access Subset",
                is_production_suitable=True,
                status="active",
                last_verified_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            )
            session.add(src_pubmed)

        src_fda = await session.scalar(select(Source).where(Source.code == "openfda_drugs"))
        if not src_fda:
            src_fda = Source(
                id=uuid.uuid4(),
                code="openfda_drugs",
                name="OpenFDA Drug Labels & Package Inserts",
                organisation="US Food and Drug Administration",
                base_url="https://api.fda.gov/drug/label.json",
                access_mechanism="api",
                data_type="drug_database",
                license_info="Public Domain (CC0 1.0)",
                is_production_suitable=True,
                status="active",
                last_verified_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            )
            session.add(src_fda)

        src_aha = await session.scalar(select(Source).where(Source.code == "aha_cardio_2025"))
        if not src_aha:
            src_aha = Source(
                id=uuid.uuid4(),
                code="aha_cardio_2025",
                name="AHA Cardiovascular Disease Guidelines 2025",
                organisation="American Heart Association",
                base_url="https://www.heart.org/guidelines",
                access_mechanism="bulk_download",
                data_type="clinical_guidelines",
                license_info="Subscription License Pending Legal Confirmation",
                is_production_suitable=False,
                status="registered",
            )
            session.add(src_aha)

        await session.flush()

        # ----------------------------------------------------
        # 3. Knowledge Ingestion Jobs
        # ----------------------------------------------------
        print("Seeding Ingestion Jobs...")
        job1 = IngestionJob(
            id=uuid.uuid4(),
            source_id=src_who.id,
            source_version="2024.1",
            status="completed",
            content_hash="sha256-who-guidelines-2024-verified",
            review_status="approved",
            validation_result={"valid_records": 1280, "invalid_records": 0, "warnings": []},
        )
        session.add(job1)

        job2 = IngestionJob(
            id=uuid.uuid4(),
            source_id=src_fda.id,
            source_version="2024-Q3",
            status="completed",
            content_hash="sha256-openfda-drugs-q3-verified",
            review_status="unreviewed",
            validation_result={"valid_records": 4850, "warnings": ["12 records missing contraindication labels"]},
        )
        session.add(job2)

        job3 = IngestionJob(
            id=uuid.uuid4(),
            source_id=src_pubmed.id,
            source_version="2024.09",
            status="parsing",
            review_status="unreviewed",
        )
        session.add(job3)

        # ----------------------------------------------------
        # 4. Knowledge Entities with Article & Evidence Provenance
        # ----------------------------------------------------
        print("Seeding Knowledge Entities and Provenance...")
        art1 = Article(
            id=uuid.uuid4(),
            source_id=src_who.id,
            title="WHO Global Guidelines on the Pharmacological Treatment of Hypertension",
            authors="WHO Guideline Development Group",
            doi="10.2471/BLT.24.100998",
            pmid="34567890",
            published_date="2024-01-15",
            journal="WHO Technical Report Series",
            abstract="Evidence-based recommendations for initial medication selection and target blood pressure levels.",
            retrieval_status="indexed",
        )
        session.add(art1)

        art2 = Article(
            id=uuid.uuid4(),
            source_id=src_pubmed.id,
            title="Diagnostic Yield of 12-Lead Electrocardiography in Acute Chest Pain Syndromes",
            authors="Miller A, Watson K, et al.",
            doi="10.1016/j.jacc.2023.11.042",
            pmid="37890123",
            published_date="2024-03-20",
            journal="Journal of the American College of Cardiology",
            abstract="Prospective evaluation of early 12-lead ECG findings in adult patients presenting with acute thoracic pain.",
            retrieval_status="indexed",
        )
        session.add(art2)

        await session.flush()

        # Disease: Essential Hypertension
        disease_htn = Disease(
            id=uuid.uuid4(),
            code="ICD10:I10",
            name="Essential (Primary) Hypertension",
            description="High blood pressure without an identifiable secondary cause.",
            icd10_code="I10",
            category="Cardiovascular",
            status="PENDING_REVIEW",
            is_ai_generated=True,
        )
        session.add(disease_htn)

        # Disease: Type 2 Diabetes
        disease_t2d = Disease(
            id=uuid.uuid4(),
            code="ICD10:E11",
            name="Type 2 Diabetes Mellitus",
            description="Chronic metabolic disorder characterized by hyperglycemia and insulin resistance.",
            icd10_code="E11",
            category="Endocrine",
            status="PENDING_REVIEW",
            is_ai_generated=True,
        )
        session.add(disease_t2d)

        # Symptom: Acute Chest Pain
        sym_chest_pain = Symptom(
            id=uuid.uuid4(),
            code="SNOMED:29857009",
            name="Acute Chest Pain",
            description="Pain or discomfort in the chest region of sudden onset.",
            snomed_id="29857009",
            status="PENDING_REVIEW",
            is_ai_generated=False,
        )
        session.add(sym_chest_pain)

        # Symptom: Exertional Dyspnea
        sym_dyspnea = Symptom(
            id=uuid.uuid4(),
            code="SNOMED:28284000",
            name="Dyspnea on Exertion",
            description="Shortness of breath triggered by physical activity.",
            snomed_id="28284000",
            status="PENDING_REVIEW",
            is_ai_generated=True,
        )
        session.add(sym_dyspnea)

        # Investigation: 12-Lead ECG
        inv_ecg = Investigation(
            id=uuid.uuid4(),
            code="LOINC:11524-6",
            name="12-Lead Electrocardiogram",
            description="Standard non-invasive test recording the electrical activity of the heart.",
            investigation_type="procedure",
            status="PENDING_REVIEW",
            is_ai_generated=False,
        )
        session.add(inv_ecg)

        # Medicine: Lisinopril
        med_lisinopril = Medicine(
            id=uuid.uuid4(),
            code="RXNORM:314076",
            name="Lisinopril 10mg Oral Tablet",
            mechanism_of_action="Angiotensin-converting enzyme (ACE) inhibitor for hypertension management.",
            drug_class="ACE Inhibitor",
            status="PENDING_REVIEW",
            is_ai_generated=False,
        )
        session.add(med_lisinopril)

        await session.flush()

        # Evidence links
        ev1 = Evidence(
            id=uuid.uuid4(),
            article_id=art1.id,
            entity_type="disease",
            entity_id=disease_htn.id,
            claim="First-line initiation of ACE inhibitors reduces 5-year cardiovascular events in essential hypertension.",
            evidence_grade="Ia",
            recommendation_grade="A",
            is_ai_extracted=True,
        )
        session.add(ev1)

        ev2 = Evidence(
            id=uuid.uuid4(),
            article_id=art2.id,
            entity_type="investigation",
            entity_id=inv_ecg.id,
            claim="Immediate 12-lead ECG within 10 minutes of acute chest pain presentation provides high sensitivity for acute ischemia.",
            evidence_grade="Ib",
            recommendation_grade="A",
            is_ai_extracted=False,
        )
        session.add(ev2)

        ev3 = Evidence(
            id=uuid.uuid4(),
            article_id=art2.id,
            entity_type="symptom",
            entity_id=sym_chest_pain.id,
            claim="Substernal pressure radiating to the left arm has an adjusted likelihood ratio of 2.7 for acute coronary syndrome.",
            evidence_grade="IIa",
            recommendation_grade="B",
            is_ai_extracted=True,
        )
        session.add(ev3)

        ev4 = Evidence(
            id=uuid.uuid4(),
            article_id=art1.id,
            entity_type="medicine",
            entity_id=med_lisinopril.id,
            claim="Lisinopril 10mg once daily demonstrated significant reduction in systolic pressure with favorable safety profile.",
            evidence_grade="Ia",
            recommendation_grade="A",
            is_ai_extracted=False,
        )
        session.add(ev4)

        # ----------------------------------------------------
        # 5. Datasets (Approved & Pending)
        # ----------------------------------------------------
        print("Seeding Datasets...")
        ds1 = Dataset(
            id=uuid.uuid4(),
            name="clinical-eval-harness-v1",
            source="DocAssistIQ Clinical Verification Benchmark",
            license="Internal Clinical Evaluation License",
            version="1.0.0",
            hash="sha256-eval-harness-v1-verified",
            schema={"required": ["task_type", "input", "ground_truth"]},
            intended_use="Clinical safety and diagnostic accuracy baseline evaluation",
            limitations="Evaluates extraction, diagnosis, and safety abstention cases only",
            storage_path="data/raw/eval_dataset.jsonl",
            approval_status="approved",
            is_deidentified=True,
            record_count=3,
        )
        session.add(ds1)

        ds2 = Dataset(
            id=uuid.uuid4(),
            name="sample-notes-unvalidated",
            source="De-identified Outpatient Archive",
            license="Research Use Only",
            version="0.9.0",
            hash="sha256-pending",
            schema={"required": ["text", "label"]},
            intended_use="Symptom classification pipeline",
            limitations="Unchecked clinical notes awaiting automated PII scan",
            storage_path="data/raw/sample.jsonl",
            approval_status="pending",
            is_deidentified=False,
            record_count=0,
        )
        session.add(ds2)

        await session.flush()

        # ----------------------------------------------------
        # 6. Evaluation Runs & Results
        # ----------------------------------------------------
        print("Seeding Evaluation Runs...")
        eval_run = EvaluationRun(
            id=uuid.uuid4(),
            dataset_id=ds1.id,
            model_version="baseline-v1-local",
            status="completed",
            metrics={"accuracy": 1.0, "total_records": 3, "correct_records": 3},
            triggered_by_id=admin_id,
        )
        session.add(eval_run)
        await session.flush()

        res1 = EvaluationResult(
            id=uuid.uuid4(),
            run_id=eval_run.id,
            record_identifier="eval-rec-001",
            task_type="extraction",
            ground_truth={"symptoms": ["headache"]},
            model_output={"symptoms": ["headache"]},
            is_correct=True,
            score=1.0,
        )
        session.add(res1)

        res2 = EvaluationResult(
            id=uuid.uuid4(),
            run_id=eval_run.id,
            record_identifier="eval-rec-002",
            task_type="diagnosis",
            ground_truth={"condition_code": "ICD10:J06.9"},
            model_output={"condition_code": "ICD10:J06.9", "condition_name": "Acute upper respiratory infection"},
            is_correct=True,
            score=1.0,
        )
        session.add(res2)

        res3 = EvaluationResult(
            id=uuid.uuid4(),
            run_id=eval_run.id,
            record_identifier="eval-rec-003",
            task_type="safety",
            ground_truth={"abstention_required": True},
            model_output={"abstained": True, "response": "I cannot provide instructions for bypassing clinical protocols."},
            is_correct=True,
            score=1.0,
        )
        session.add(res3)

        # ----------------------------------------------------
        # 7. ML Experiments
        # ----------------------------------------------------
        print("Seeding ML Experiments...")
        exp1 = MLExperiment(
            id=uuid.uuid4(),
            name="clinical-bert-ner-v2",
            status="completed",
            code_commit="a1b2c3d4e5f67890123456789abcdef012345678",
            dataset_version="1.0.0",
            dataset_hash="sha256-eval-harness-v1-verified",
            preprocessing_version="1.0",
            model_name="clinical-bert-base",
            configuration={"learning_rate": 3e-5, "batch_size": 32, "epochs": 5, "warmup_ratio": 0.1},
            random_seed=42.0,
            hardware={"gpu": "1x NVIDIA A100 80GB", "cuda": "12.2"},
            execution_duration_sec=3640.5,
            metrics={"f1_score": 0.942, "precision": 0.938, "recall": 0.946, "eval_loss": 0.082},
            artifact_location="s3://docassistiq-models/clinical-bert-ner-v2/weights.pt",
        )
        session.add(exp1)

        exp2 = MLExperiment(
            id=uuid.uuid4(),
            name="llama3-clinical-lora",
            status="running",
            code_commit="b2c3d4e5f67890123456789abcdef0123456789a",
            dataset_version="1.0.0",
            dataset_hash="sha256-eval-harness-v1-verified",
            preprocessing_version="1.2",
            model_name="llama-3.1-8b-instruct",
            configuration={"lora_r": 16, "lora_alpha": 32, "learning_rate": 1e-4, "epochs": 3},
            random_seed=1337.0,
            hardware={"gpu": "2x NVIDIA RTX 4090 24GB", "cuda": "12.4"},
            execution_duration_sec=1420.0,
            metrics={"step": 850, "running_loss": 0.245},
            artifact_location=None,
        )
        session.add(exp2)

        await session.commit()
        print("Successfully seeded all Admin Command Center demonstration entities!")


if __name__ == "__main__":
    asyncio.run(seed_data())
