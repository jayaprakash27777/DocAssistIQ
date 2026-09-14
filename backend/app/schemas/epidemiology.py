from pydantic import BaseModel
from typing import List
import uuid
from datetime import datetime

class EpiRadarResponse(BaseModel):
    consultation_id: uuid.UUID
    cluster_detected: bool
    cluster_name: str | None = None
    confidence_score: int = 0
    matched_symptoms: List[str] = []
    local_cases_last_48h: int = 0
    warning_message: str | None = None
