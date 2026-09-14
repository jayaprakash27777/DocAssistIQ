"""DocAssistIQ — User ORM Model.

Represents a registered clinician or administrator. All authentication
state lives here. Clinical role assignment lives here for Phase 5 RBAC.

Security notes:
  - ``password_hash`` is never serialised in Pydantic response schemas.
  - ``email`` is stored as-is but looked up via ``lower(email)`` index
    (case-insensitive uniqueness without forcing lowercase storage).
  - ``role`` defaults to ``'doctor'``. Only admins can elevate roles
    (enforced in the service layer, not the model).
"""


from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Registered user of the DocAssistIQ platform."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320),  # RFC 5321 maximum
        nullable=False,
        index=True,
        comment="User email address (case-insensitive unique via lower() index)",
    )

    password_hash: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="bcrypt password hash (never serialised in API responses)",
    )

    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Clinician full name as displayed in the UI",
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="doctor",
        comment="Role: 'doctor' | 'admin'",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="False = account suspended; login is rejected",
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="True once email verification is complete (future phase)",
    )

    @property
    def permissions(self) -> list[str]:
        from app.authorization import PERMISSION_MATRIX
        perms = PERMISSION_MATRIX.get(self.role, set())
        return list(perms)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"
