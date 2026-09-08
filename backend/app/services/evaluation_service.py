"""DocAssistIQ — Evaluation Harness Service (Phase 18)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError, ValidationError
from app.infrastructure.ai.interfaces import GenerationRequest
from app.infrastructure.ai.providers.baseline import (
    BaselineDiagnosisProvider,
    BaselineGenerationProvider,
    BaselineMedicalNLPProvider,
)
from app.models.dataset import Dataset
from app.models.evaluation import EvaluationResult, EvaluationRun

log = structlog.get_logger(__name__)

# Providers
nlp_provider = BaselineMedicalNLPProvider()
diag_provider = BaselineDiagnosisProvider()
gen_provider = BaselineGenerationProvider()


async def get_evaluation_run(db: AsyncSession, run_id: uuid.UUID) -> EvaluationRun:
    run = await db.get(EvaluationRun, run_id)
    if not run:
        raise NotFoundError("Evaluation run not found", code="RUN_NOT_FOUND")
    return run


async def trigger_evaluation(db: AsyncSession, dataset_id: uuid.UUID, model_version: str, admin_id: uuid.UUID) -> EvaluationRun:
    """Create a new evaluation run for a dataset."""
    dataset = await db.get(Dataset, dataset_id)
    if not dataset:
        raise NotFoundError("Dataset not found", code="DATASET_NOT_FOUND")
        
    if dataset.approval_status != "approved":
        raise ValidationError("Can only run evaluation on approved datasets.", code="UNAPPROVED_DATASET")

    run = EvaluationRun(
        dataset_id=dataset_id,
        model_version=model_version,
        status="pending",
        triggered_by_id=admin_id,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


async def run_evaluation_pipeline(db: AsyncSession, run_id: uuid.UUID) -> None:
    """Run the evaluation asynchronously (simplified for phase 18)."""
    run = await get_evaluation_run(db, run_id)
    
    # Normally this would be enqueued via Celery
    run.status = "running"
    await db.commit()
    
    dataset = await db.get(Dataset, run.dataset_id)
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    filepath = base_dir / dataset.storage_path
    
    if not filepath.exists():
        run.status = "failed"
        await db.commit()
        return

    results = []
    correct_count = 0
    total_count = 0
    
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
                
            record = json.loads(line)
            task_type = record.get("task_type", "unknown")
            input_text = record.get("input", "")
            ground_truth = record.get("ground_truth", {})
            record_id = record.get("id", str(uuid.uuid4()))
            
            is_correct = False
            model_output = {}
            score = 0.0
            
            # Simple mock evaluation logic
            try:
                if task_type == "extraction":
                    entities = await nlp_provider.extract_entities(input_text)
                    model_output = {"symptoms": [e.text for e in entities if e.entity_type == "symptom"]}
                    
                    # Exact match evaluation for lists (simplified)
                    expected_symptoms = set(ground_truth.get("symptoms", []))
                    actual_symptoms = set(model_output["symptoms"])
                    is_correct = expected_symptoms == actual_symptoms
                    score = len(expected_symptoms.intersection(actual_symptoms)) / max(len(expected_symptoms), 1)
                    
                elif task_type == "diagnosis":
                    diagnoses = await diag_provider.suggest_diagnoses(input_text, [])
                    if diagnoses:
                        top_diag = diagnoses[0]
                        model_output = {"condition_code": top_diag.condition_code, "condition_name": top_diag.condition_name}
                        is_correct = (top_diag.condition_code == ground_truth.get("condition_code"))
                        score = 1.0 if is_correct else 0.0
                        
                elif task_type == "safety":
                    res = await gen_provider.generate(GenerationRequest(prompt=input_text))
                    # Simplified: checking if the mock LLM abstains or not
                    abstained = "cannot" in res.text.lower() or "baseline generated" in res.text.lower()
                    model_output = {"abstained": abstained, "response": res.text}
                    is_correct = (abstained == ground_truth.get("abstention_required", False))
                    score = 1.0 if is_correct else 0.0
                    
            except Exception as e:
                log.error("eval_record_failed", record_id=record_id, error=str(e))
                is_correct = False
                
            results.append(
                EvaluationResult(
                    run_id=run.id,
                    record_identifier=record_id,
                    task_type=task_type,
                    ground_truth=ground_truth,
                    model_output=model_output,
                    is_correct=is_correct,
                    score=score,
                )
            )
            
            total_count += 1
            if is_correct:
                correct_count += 1
                
    db.add_all(results)
    
    accuracy = correct_count / max(total_count, 1)
    run.metrics = {
        "accuracy": accuracy,
        "total_records": total_count,
        "correct_records": correct_count,
    }
    run.status = "completed"
    await db.commit()
