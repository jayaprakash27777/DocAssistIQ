"""DocAssistIQ — Dataset Validation and Governance Service (Phase 17).

Enforces strict quality controls and mandatory de-identification
for any dataset intended for ML pipelines.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ValidationError, NotFoundError
from app.models.dataset import Dataset

log = structlog.get_logger(__name__)

# Basic PII heuristics (fail closed)
# In production, use presidio or MedicalNLPProvider
PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),  # Email
    re.compile(r"\b\d{10}\b"),  # Simple phone
    re.compile(r"\b(mr|mrs|ms|dr)\.?\s+[a-z]+\b", re.IGNORECASE),  # Names
]


class DatasetValidationResult:
    def __init__(self):
        self.is_valid = True
        self.errors: list[str] = []
        self.record_count = 0
        self.malformed_count = 0
        self.missing_values_count = 0
        self.duplicates_count = 0
        self.pii_detected = False
        self.label_conflicts = 0
        self.leakage_detected = False

    def fail(self, reason: str):
        self.is_valid = False
        self.errors.append(reason)


async def register_dataset(db: AsyncSession, payload: dict) -> Dataset:
    """Registers a new dataset in a pending state."""
    
    # Check if name + version exists
    existing = await db.execute(
        select(Dataset).where(Dataset.name == payload["name"], Dataset.version == payload["version"])
    )
    if existing.scalar_one_or_none():
        raise ValidationError(f"Dataset {payload['name']} v{payload['version']} already exists.", code="DATASET_EXISTS")
        
    ds = Dataset(
        name=payload["name"],
        source=payload["source"],
        license=payload["license"],
        version=payload["version"],
        hash=payload.get("hash", "pending"),
        schema=payload.get("schema", {}),
        intended_use=payload["intended_use"],
        limitations=payload["limitations"],
        storage_path=payload["storage_path"],
        approval_status="pending",
        is_deidentified=False,
    )
    db.add(ds)
    await db.commit()
    await db.refresh(ds)
    return ds


async def get_dataset(db: AsyncSession, dataset_id: uuid.UUID) -> Dataset:
    ds = await db.get(Dataset, dataset_id)
    if not ds:
        raise NotFoundError("Dataset not found", code="DATASET_NOT_FOUND")
    return ds


def validate_dataset_file(filepath: Path, required_keys: list[str]) -> DatasetValidationResult:
    """
    Executable validation. Reads a JSONL file and validates for Phase 17 rules.
    """
    result = DatasetValidationResult()
    
    if not filepath.exists():
        result.fail(f"File not found: {filepath}")
        return result

    seen_hashes = set()
    label_map: dict[str, str] = {}

    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            result.record_count += 1
            
            # 1. Malformed Records
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                result.malformed_count += 1
                result.fail(f"Line {line_num}: Malformed JSON")
                continue
                
            # 2. Missing Values
            for key in required_keys:
                if key not in record or record[key] is None or record[key] == "":
                    result.missing_values_count += 1
                    result.fail(f"Line {line_num}: Missing required key '{key}'")
                    break

            # 3. Duplicates
            # We hash the entire JSON string (sorted keys) to find exact duplicates
            record_hash = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
            if record_hash in seen_hashes:
                result.duplicates_count += 1
                result.fail(f"Line {line_num}: Exact duplicate found")
            else:
                seen_hashes.add(record_hash)

            # 4. PII Detection (Fail Closed)
            # Scan all string values
            for val in record.values():
                if isinstance(val, str):
                    for pattern in PII_PATTERNS:
                        if pattern.search(val):
                            result.pii_detected = True
                            result.fail(f"Line {line_num}: PII detected. Failing closed.")
                            break
                if result.pii_detected:
                    break

            # 5. Label Conflicts
            # If the schema implies a text -> label mapping (e.g. classification)
            if "text" in record and "label" in record:
                text = record["text"]
                label = record["label"]
                if text in label_map and label_map[text] != label:
                    result.label_conflicts += 1
                    result.fail(f"Line {line_num}: Label conflict for text. Was {label_map[text]}, now {label}.")
                else:
                    label_map[text] = label
                    
            # 6. Leakage
            # In a real system, we would query the Evaluation sets. 
            # For this baseline, we check for a specific test string.
            if "text" in record and "EVAL_SET_ONLY" in record["text"]:
                result.leakage_detected = True
                result.fail(f"Line {line_num}: Data leakage detected (text present in holdout evaluation set).")

    if result.malformed_count > 0 or result.missing_values_count > 0 or result.duplicates_count > 0 or result.label_conflicts > 0 or result.pii_detected or result.leakage_detected:
        result.is_valid = False

    return result


async def run_dataset_validation(db: AsyncSession, dataset_id: uuid.UUID) -> dict[str, Any]:
    """Runs the validation pipeline and updates the dataset record."""
    ds = await get_dataset(db, dataset_id)
    
    # Path is relative to the DocAssistIQ project root
    # e.g. data/raw/sample.jsonl
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    filepath = base_dir / ds.storage_path
    
    schema = ds.schema
    required_keys = schema.get("required", [])
    
    log.info("starting_dataset_validation", dataset_id=str(ds.id), path=str(filepath))
    
    # Execute validation
    result = validate_dataset_file(filepath, required_keys)
    
    ds.record_count = result.record_count
    
    if result.is_valid and not result.pii_detected:
        ds.is_deidentified = True
        log.info("dataset_validation_passed", dataset_id=str(ds.id))
    else:
        ds.is_deidentified = False
        ds.approval_status = "rejected"
        log.warning("dataset_validation_failed", dataset_id=str(ds.id), errors=result.errors[:5])

    await db.commit()
    
    return {
        "is_valid": result.is_valid,
        "record_count": result.record_count,
        "malformed": result.malformed_count,
        "missing_values": result.missing_values_count,
        "duplicates": result.duplicates_count,
        "pii_detected": result.pii_detected,
        "label_conflicts": result.label_conflicts,
        "leakage_detected": result.leakage_detected,
        "errors": result.errors[:10], # Truncate for response
    }


async def approve_dataset(db: AsyncSession, dataset_id: uuid.UUID) -> Dataset:
    """Approve a dataset for ML use."""
    ds = await get_dataset(db, dataset_id)
    
    if not ds.is_deidentified:
        raise ValidationError("Cannot approve a dataset that is not de-identified and validated.", code="SAFETY_VIOLATION")
        
    ds.approval_status = "approved"
    await db.commit()
    return ds
