from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field

class SafetyFlag(BaseModel):
    rule_id: str
    rule_version: str
    category: Literal["ALLERGY", "DRUG_INTERACTION", "CONTRAINDICATION", "CONTRADICTION", "MISSING_INFO", "RED_FLAG", "UNCERTAINTY", "EVIDENCE_INSUFFICIENCY"]
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    message: str
    source: str
    related_entity: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SafetyDecision(BaseModel):
    decision: Literal["ALLOW", "WARN", "ABSTAIN"]
    flags: list[SafetyFlag] = []
