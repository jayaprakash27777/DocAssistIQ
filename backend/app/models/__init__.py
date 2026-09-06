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

# ── Consultation (Phase 8, existing) ─────────────────────────
from app.models.consultation import Consultation  # noqa: F401

# ── Clinical ─────────────────────────────────────────────────
from app.models.clinical import ClinicalNote, ClinicalFinding  # noqa: F401

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

# ── Audit, Feedback, FileObject ───────────────────────────────
from app.models.audit import AuditLog, Feedback, FileObject  # noqa: F401

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
    "PatientSession",
    "ConsentRecord",
    # Consultation
    "Consultation",
    # Clinical
    "ClinicalNote",
    "ClinicalFinding",
    # Knowledge
    "Symptom",
    "Disease",
    "Investigation",
    "Medicine",
    "DiseaseSymptom",
    "DiseaseInvestigation",
    "DiseaseMedicine",
    # Audit
    "AuditLog",
    "Feedback",
    "FileObject",
]
