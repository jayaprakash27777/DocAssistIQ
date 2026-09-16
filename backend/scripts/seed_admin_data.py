import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.user import User
from app.models.doctor import Doctor
from app.models.ingestion import IngestionJob
from app.models.provenance import Source
from app.models.dataset import Dataset
from app.models.evaluation import EvaluationRun
from app.models.experiment import MLExperiment
from app.config import get_settings

async def seed_data():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Create a dummy user for the doctor if not exists
        dummy_user_id = uuid.uuid4()
        user = User(
            id=dummy_user_id,
            email=f"dr.smith_{dummy_user_id.hex[:6]}@example.com",
            hashed_password="mock",
            full_name="Dr. John Smith",
            role="doctor"
        )
        session.add(user)
        
        # 1. Doctor Verifications
        doc1 = Doctor(
            id=uuid.uuid4(),
            user_id=dummy_user_id,
            specialty="Cardiology",
            credential_reference="BOARD-CERT-12345",
            credential_body="American Board of Cardiology Certification...",
            verification_status="pending",
            created_at=datetime.now(timezone.utc)
        )
        session.add(doc1)
        
        # 2. Medical Sources
        src1 = Source(
            id=uuid.uuid4(),
            name="AHA Guidelines 2024",
            url="https://www.heart.org/guidelines",
            status="active"
        )
        session.add(src1)
        
        # 3. Knowledge Ingestion Jobs
        job1 = IngestionJob(
            id=uuid.uuid4(),
            source_id=src1.id,
            status="running",
            documents_processed=45,
            error_message=""
        )
        session.add(job1)
        
        # 4. Datasets
        ds1 = Dataset(
            id=uuid.uuid4(),
            name="clinical-notes-cardio-v1",
            source="MIMIC-IV (Filtered)",
            license="PhysioNet",
            version="1.0.0",
            hash="sha256-abc123def456",
            schema={"required": ["text", "label"]},
            intended_use="Symptom Extraction",
            limitations="ICU Patients only",
            storage_path="data/raw/cardio.jsonl",
            approval_status="approved",
            is_deidentified=True,
            record_count=15000
        )
        session.add(ds1)
        
        # 5. Evaluation Harness
        eval1 = EvaluationRun(
            id=uuid.uuid4(),
            dataset_id=ds1.id,
            model_version="baseline-v1-local",
            status="completed",
            metrics={"accuracy": 0.94, "total_records": 15000, "correct_records": 14100},
            triggered_by_id=uuid.uuid4() # dummy admin id
        )
        session.add(eval1)
        
        # 6. ML Experiments
        exp1 = MLExperiment(
            id=uuid.uuid4(),
            name="bert-finetune-cardio",
            status="completed",
            code_commit="abcdef1234567890abcdef1234567890abcdef12",
            dataset_version="1.0.0",
            dataset_hash="sha256-abc123def456",
            preprocessing_version="1.0",
            model_name="clinical-bert-base",
            configuration={"learning_rate": 2e-5, "batch_size": 32, "epochs": 3},
            random_seed=42,
            hardware={"gpu": "1x A100 80GB"},
            execution_duration_sec=7200.5,
            metrics={"loss": 0.12, "f1_score": 0.95},
            artifact_location="s3://docassistiq-models/bert-finetune-cardio/weights"
        )
        session.add(exp1)

        await session.commit()
        print("Successfully seeded admin dashboard mock data!")

if __name__ == "__main__":
    asyncio.run(seed_data())
