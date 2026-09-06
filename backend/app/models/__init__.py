"""DocAssistIQ — ORM Models package.

All models must be imported here so that Alembic's autogenerate
and SQLAlchemy's metadata registry see every table definition.
"""

from app.models.consultation import Consultation  # noqa: F401
from app.models.user import User  # noqa: F401

__all__ = ["Consultation", "User"]
