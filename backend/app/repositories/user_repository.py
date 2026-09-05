"""DocAssistIQ — User Repository.

Extends BaseRepository with email-specific lookup methods.
All queries use ``lower(email)`` to match the case-insensitive
unique index defined in migration 0002.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repository import BaseRepository
from app.models.user import User


class UserRepository(BaseRepository[User]):
    """Data-access layer for the ``users`` table."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        """Return a user by email (case-insensitive), or ``None``."""
        result = await self._session.execute(
            select(User).where(func.lower(User.email) == email.lower())
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Return ``True`` if any user has this email (case-insensitive)."""
        result = await self._session.execute(
            select(func.count()).where(func.lower(User.email) == email.lower())
        )
        return (result.scalar() or 0) > 0
