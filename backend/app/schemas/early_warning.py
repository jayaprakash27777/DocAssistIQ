from pydantic import BaseModel
from typing import List
import uuid

class EarlyWarningResponse(BaseModel):
    consultation_id: uuid.UUID
    probability_percentage: int
    is_high_risk: bool
    primary_warning_flag: str  # e.g. "Sepsis Risk", "Cardiogenic Shock Risk"
    contributing_factors: List[str]
    recommended_immediate_actions: List[str]
    mews_score: int = 0
    qsofa_score: int = 0
    news2_score: int = 0
    sirs_score: int = 0
