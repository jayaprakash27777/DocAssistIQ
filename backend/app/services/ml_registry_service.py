"""DocAssistIQ ?" Model Registry Service (Phase 65).

Enforces the state machine for promoting ML models through safety gates.
"""

from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.ml_registry import RegisteredModel, ModelLifecycleState

# Define the strict sequence of promotion
PROMOTION_LIFECYCLE = [
    ModelLifecycleState.EXPERIMENTAL,
    ModelLifecycleState.EVALUATED,
    ModelLifecycleState.CANDIDATE,
    ModelLifecycleState.SAFETY_REVIEW,
    ModelLifecycleState.APPROVED,
    ModelLifecycleState.STAGING,
    ModelLifecycleState.PRODUCTION,
]


class MLRegistryService:
    def __init__(self, db: Session):
        self.db = db

    def register_model(self, model_name: str, version: str, base_model: str, **kwargs) -> RegisteredModel:
        """Registers a new model in EXPERIMENTAL state."""
        new_model = RegisteredModel(
            model_name=model_name,
            version=version,
            base_model=base_model,
            lifecycle_state=ModelLifecycleState.EXPERIMENTAL,
            **kwargs
        )
        self.db.add(new_model)
        self.db.commit()
        self.db.refresh(new_model)
        return new_model

    def promote_model(self, model_id: str, target_state: ModelLifecycleState) -> RegisteredModel:
        """Promotes a model strictly enforcing the lifecycle sequence."""
        model = self.db.query(RegisteredModel).filter(RegisteredModel.id == model_id).first()
        if not model:
            raise ValueError(f"Model with ID {model_id} not found.")

        current_state = model.lifecycle_state

        # Retirement can happen from any state
        if target_state == ModelLifecycleState.RETIRED:
            model.lifecycle_state = target_state
            self.db.commit()
            self.db.refresh(model)
            return model

        # Ensure strict forward progression
        if current_state not in PROMOTION_LIFECYCLE:
            raise ValueError(f"Model is in non-promotable state: {current_state}")

        current_idx = PROMOTION_LIFECYCLE.index(current_state)
        target_idx = PROMOTION_LIFECYCLE.index(target_state)

        # Disallow skipping gates
        if target_idx > current_idx + 1:
            raise ValueError(
                f"Safety Gate Violation: Cannot jump from {current_state} directly to {target_state}. "
                f"Must pass through {PROMOTION_LIFECYCLE[current_idx + 1]} first."
            )
            
        # Disallow backwards unless it's a rollback (handled separately)
        if target_idx < current_idx:
            raise ValueError("Use `rollback_model` to revert states, not `promote`.")

        # If deploying to STAGING or PRODUCTION, record the deployment date
        if target_state in (ModelLifecycleState.STAGING, ModelLifecycleState.PRODUCTION):
            model.deployment_date = datetime.utcnow()

        model.lifecycle_state = target_state
        self.db.commit()
        self.db.refresh(model)
        return model
