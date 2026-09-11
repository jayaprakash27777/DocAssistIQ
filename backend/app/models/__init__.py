"""DocAssistIQ — ORM Models package.

All models must be imported here so that Alembic's autogenerate
and SQLAlchemy's metadata registry see every table definition.

Import order respects FK dependencies:
  1. Provenance (KnowledgeVersion, Source) — no other model FKs
  2. Tenant — no model FKs
  3. User (existing)
  4. RBAC (Role, Permission, joins) — depends on Tenant, User
  5. Doctor — depends on User, Tenant
  6. Patient (PatientSession, ConsentRecord) — depends on Tenant, Doctor, User
  7. Consultation (existing Phase 8) — depends on User
  8. Clinical (ClinicalNote, ClinicalFinding) — depends on Consultation, User
  9. Knowledge (Symptom, Disease, Investigation, Medicine, joins) — depends on Source, KnowledgeVersion
  10. Audit (AuditLog, Feedback, FileObject) — depends on User, Tenant, Consultation
"""

# ── Provenance (no upstream FKs to our models) ────────────────
from app.models.provenance import (  # noqa: F401
    KnowledgeVersion,
    Source,
    Article,
    Evidence,
)

# ── Tenant ────────────────────────────────────────────────────
from app.models.tenant import Tenant  # noqa: F401

# ── User (existing) ───────────────────────────────────────────
from app.models.user import User  # noqa: F401

# ── RBAC ──────────────────────────────────────────────────────
from app.models.rbac import (  # noqa: F401
    Role,
    Permission,
    RolePermission,
    UserRole,
)

# ── Doctor ────────────────────────────────────────────────────
from app.models.doctor import Doctor  # noqa: F401

# ── Patient ───────────────────────────────────────────────────
from app.models.patient import PatientSession, ConsentRecord  # noqa: F401
from app.models.patient_profile import PatientProfile  # noqa: F401

# ── Consultation ──────────────────────────────────────────────
from app.models.consultation import Consultation, ConsultationAudit  # noqa: F401

# ── Clinical ─────────────────────────────────────────────────
from app.models.clinical import ClinicalNote, ClinicalFinding, ManualIntake  # noqa: F401
from app.models.transcript import Transcript, TranscriptSegment  # noqa: F401

# ── Knowledge entities ────────────────────────────────────────
from app.models.knowledge import (  # noqa: F401
    Symptom,
    Disease,
    Investigation,
    Medicine,
    DiseaseSymptom,
    DiseaseInvestigation,
    DiseaseMedicine,
)

# 🎙️ Audit, Feedback, FileObject 🎙️
from app.models.audit import AuditLog, Feedback, FileObject  # noqa: F401
from app.models.feedback import ClinicianFeedback  # noqa: F401

# ── Dataset ───────────────────────────────────────────────────
from app.models.dataset import Dataset  # noqa: F401

# ── Evaluation ────────────────────────────────────────────────
from app.models.evaluation import EvaluationResult, EvaluationRun  # noqa: F401

# ── Experiments ───────────────────────────────────────────────
from app.models.experiment import MLExperiment  # noqa: F401

# ── Ingestion ─────────────────────────────────────────────────
from app.models.ingestion import IngestionJob  # noqa: F401

# ── Embeddings ────────────────────────────────────────────────
from app.models.embedding import EmbeddingRecord  # noqa: F401

# ── Social Hub (Phase 47) ─────────────────────────────────────
from app.models.social import DoctorPost, PostAttachment, PostLike, PostComment, PostBookmark  # noqa: F401

__all__ = [
    # Provenance
    "KnowledgeVersion",
    "Source",
    "Article",
    "Evidence",
    # Tenant
    "Tenant",
    # User
    "User",
    # RBAC
    "Role",
    "Permission",
    "RolePermission",
    "UserRole",
    # Doctor
    "Doctor",
    # Patient
    "PatientProfile",
    "PatientSession",
    "ConsentRecord",
    # Consultation
    "Consultation",
    "ConsultationAudit",
    # Clinical
    "ClinicalNote",
    "ClinicalFinding",
    "ManualIntake",
    "Transcript",
    "TranscriptSegment",
    # Knowledge
    "Symptom",
    "Disease",
    "Investigation",
    "Medicine",
    "DiseaseSymptom",
    "DiseaseInvestigation",
    "DiseaseMedicine",
    # Dataset
    "Dataset",
    # Audit
    "AuditLog",
    "Feedback",
    "FileObject",
    "ClinicianFeedback",
    # Ingestion
    "IngestionJob",
    # Evaluation
    "EvaluationRun",
    "EvaluationResult",
    # Experiments
    "MLExperiment",
    # Embeddings
    "EmbeddingRecord",
    # Social Hub
    "DoctorPost",
    "PostAttachment",
    "PostLike",
    "PostComment",
    "PostBookmark",
]
