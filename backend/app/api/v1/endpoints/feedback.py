from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.dependencies import get_db, get_current_doctor_profile
from app.models.doctor import Doctor
from app.models.feedback import ClinicianFeedback
from app.schemas.feedback import ClinicianFeedbackCreate, ClinicianFeedbackResponse

log = structlog.get_logger(__name__)

router = APIRouter()

@router.post("/suggestions", response_model=ClinicianFeedbackResponse)
async def submit_feedback(
    feedback_in: ClinicianFeedbackCreate,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor_profile)
):
    """
    Records a clinician's feedback (Accept, Modify, Reject) on an AI suggestion.
    """
    feedback = ClinicianFeedback(
        suggestion_id=feedback_in.suggestion_id,
        suggestion_type=feedback_in.suggestion_type,
        doctor_id=doctor.id,
        decision=feedback_in.decision,
        reason=feedback_in.reason,
        suggestion_context=feedback_in.suggestion_context,
        modified_context=feedback_in.modified_context,
        model_version=feedback_in.model_version,
        knowledge_version=feedback_in.knowledge_version
    )
    
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    
    log.info(
        "clinician_feedback_recorded", 
        doctor_id=str(doctor.id), 
        suggestion_id=feedback.suggestion_id, 
        decision=feedback.decision
    )
    
    return feedback
