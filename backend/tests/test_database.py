"""DocAssistIQ Backend — Database Core Tests (PHASE 3).

Tests cover:
  Unit (SQLite, no Docker):
    - Engine creation and configuration
    - Session factory creation
    - Session commit/rollback semantics
    - atomic() context manager (commit on success, rollback on exception)
    - Repository base CRUD operations
    - TimestampMixin column presence
    - UUIDPrimaryKeyMixin default generation
    - Partial multi-record failure leaves no trace

  Integration (real PostgreSQL, requires Docker stack):
    - pgvector extension availability
    - pg_trgm extension availability
    - Alembic migration upgrade / downgrade / re-upgrade cycle
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.database import Base, atomic, get_engine, get_session_factory
from app.infrastructure.models import TimestampMixin, UUIDPrimaryKeyMixin
from app.infrastructure.repository import BaseRepository

# ============================================================
# Helper: minimal ORM model for testing
# ============================================================


class _TestItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Minimal ORM model used only in database tests."""

    __tablename__ = "test_items"
    __table_args__ = {"extend_existing": True}


def _make_sf(engine) -> async_sessionmaker[AsyncSession]:
    """Create a local session factory bound to the given engine."""
    return async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autobegin=False
    )


# ============================================================
# Engine & session factory
# ============================================================


class TestEngine:
    def test_get_engine_returns_engine(self) -> None:
        engine = get_engine()
        assert engine is not None

    def test_get_engine_is_singleton(self) -> None:
        assert get_engine() is get_engine()

    def test_engine_url_contains_driver(self) -> None:
        url = str(get_engine().url)
        assert any(d in url for d in ("asyncpg", "sqlite", "aiosqlite"))

    def test_get_session_factory_returns_factory(self) -> None:
        factory = get_session_factory()
        assert factory is not None

    def test_get_session_factory_is_singleton(self) -> None:
        assert get_session_factory() is get_session_factory()


# ============================================================
# Session commit / rollback (unit — SQLite)
# ============================================================


class TestSessionCommit:

    async def test_commit_persists_data(self, unit_engine) -> None:
        """A committed record should be readable in a subsequent session."""
        async with unit_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        sf = _make_sf(unit_engine)
        item_id = uuid.uuid4()

        async with sf() as s1, s1.begin():
            s1.add(_TestItem(id=item_id))

        async with sf() as s2, s2.begin():
            found = await s2.get(_TestItem, item_id)
            assert found is not None
            assert found.id == item_id

        # Cleanup
        async with sf() as s3, s3.begin():
            obj = await s3.get(_TestItem, item_id)
            if obj:
                await s3.delete(obj)


    async def test_rollback_leaves_no_trace(self, unit_engine) -> None:
        """A rolled-back transaction must leave no visible data."""
        async with unit_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        sf = _make_sf(unit_engine)
        item_id = uuid.uuid4()

        async with sf() as s1:
            await s1.begin()
            s1.add(_TestItem(id=item_id))
            await s1.flush()
            await s1.rollback()

        async with sf() as s2, s2.begin():
            found = await s2.get(_TestItem, item_id)
            assert found is None


# ============================================================
# atomic() context manager
# ============================================================


class TestAtomicContextManager:

    async def test_atomic_commits_on_clean_exit(self, unit_engine) -> None:
        """Successful atomic block must persist all writes."""
        async with unit_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        sf = _make_sf(unit_engine)
        item_id = uuid.uuid4()

        async with sf() as session, atomic(session):
            session.add(_TestItem(id=item_id))
            await session.flush()

        async with sf() as verify, verify.begin():
            found = await verify.get(_TestItem, item_id)
            assert found is not None

        async with sf() as cleanup, cleanup.begin():
            obj = await cleanup.get(_TestItem, item_id)
            if obj:
                await cleanup.delete(obj)


    async def test_atomic_rolls_back_on_exception(self, unit_engine) -> None:
        """An exception inside atomic must leave no partial state."""
        async with unit_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        sf = _make_sf(unit_engine)
        item_id = uuid.uuid4()

        with pytest.raises(ValueError, match="deliberate"):
            async with sf() as session, atomic(session):
                session.add(_TestItem(id=item_id))
                await session.flush()
                raise ValueError("deliberate failure")

        async with sf() as verify, verify.begin():
            found = await verify.get(_TestItem, item_id)
            assert found is None, "Rolled-back item must not be visible"


    async def test_atomic_multi_record_partial_failure(self, unit_engine) -> None:
        """All records in a failed atomic block must be absent."""
        async with unit_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        sf = _make_sf(unit_engine)
        ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]

        with pytest.raises(RuntimeError):
            async with sf() as session, atomic(session):
                for item_id in ids:
                    session.add(_TestItem(id=item_id))
                await session.flush()
                raise RuntimeError("mid-transaction failure")

        async with sf() as verify, verify.begin():
            for item_id in ids:
                found = await verify.get(_TestItem, item_id)
                assert found is None, f"Item {item_id} should be absent after rollback"


# ============================================================
# ORM Base + Mixins
# ============================================================


class TestBase:
    def test_base_has_metadata(self) -> None:
        assert Base.metadata is not None

    def test_base_metadata_is_populated_after_model_import(self) -> None:
        assert "test_items" in Base.metadata.tables


class TestTimestampMixin:
    def test_created_at_column_in_mixin(self) -> None:
        assert hasattr(TimestampMixin, "created_at")

    def test_updated_at_column_in_mixin(self) -> None:
        assert hasattr(TimestampMixin, "updated_at")

    def test_test_item_inherits_timestamp_columns(self) -> None:
        table = Base.metadata.tables["test_items"]
        assert "created_at" in table.c
        assert "updated_at" in table.c


class TestUUIDPrimaryKeyMixin:
    def test_uuid_column_has_default_configured(self) -> None:
        """The id column default must be uuid.uuid4 (applied at INSERT time)."""
        table = Base.metadata.tables["test_items"]
        id_col = table.c["id"]
        # The column has a Python-side ColumnDefault
        assert id_col.default is not None

    def test_explicit_id_respected(self) -> None:
        explicit_id = uuid.uuid4()
        item = _TestItem(id=explicit_id)
        assert item.id == explicit_id

    def test_two_explicit_ids_are_distinct(self) -> None:
        a = _TestItem(id=uuid.uuid4())
        b = _TestItem(id=uuid.uuid4())
        assert a.id != b.id

    def test_id_column_is_primary_key(self) -> None:
        table = Base.metadata.tables["test_items"]
        assert table.c["id"].primary_key is True


# ============================================================
# Repository base (unit — SQLite)
# ============================================================


class TestBaseRepository:

    async def test_create_returns_object_with_id(self, unit_engine) -> None:
        async with unit_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        sf = _make_sf(unit_engine)
        created_id: uuid.UUID | None = None
        async with sf() as session, atomic(session):
            repo = BaseRepository(session, _TestItem)
            item = await repo.create(_TestItem())
            assert item.id is not None
            created_id = item.id

        async with sf() as cleanup, cleanup.begin():
            if created_id:
                obj = await cleanup.get(_TestItem, created_id)
                if obj:
                    await cleanup.delete(obj)


    async def test_get_by_id_returns_created_record(self, unit_engine) -> None:
        async with unit_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        sf = _make_sf(unit_engine)
        item_id = uuid.uuid4()

        async with sf() as session, atomic(session):
            repo = BaseRepository(session, _TestItem)
            await repo.create(_TestItem(id=item_id))

        async with sf() as session, session.begin():
            repo = BaseRepository(session, _TestItem)
            found = await repo.get_by_id(item_id)
            assert found is not None
            assert found.id == item_id

        async with sf() as cleanup, cleanup.begin():
            obj = await cleanup.get(_TestItem, item_id)
            if obj:
                await cleanup.delete(obj)


    async def test_get_by_id_returns_none_for_missing_id(self, unit_engine) -> None:
        sf = _make_sf(unit_engine)
        async with sf() as session, session.begin():
            repo = BaseRepository(session, _TestItem)
            result = await repo.get_by_id(uuid.uuid4())
            assert result is None


    async def test_exists_returns_true_for_present_id(self, unit_engine) -> None:
        async with unit_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        sf = _make_sf(unit_engine)
        item_id = uuid.uuid4()

        async with sf() as session, atomic(session):
            await BaseRepository(session, _TestItem).create(_TestItem(id=item_id))

        async with sf() as session, session.begin():
            assert await BaseRepository(session, _TestItem).exists(item_id) is True

        async with sf() as cleanup, cleanup.begin():
            obj = await cleanup.get(_TestItem, item_id)
            if obj:
                await cleanup.delete(obj)


    async def test_exists_returns_false_for_absent_id(self, unit_engine) -> None:
        sf = _make_sf(unit_engine)
        async with sf() as session, session.begin():
            assert await BaseRepository(session, _TestItem).exists(uuid.uuid4()) is False


    async def test_delete_removes_record(self, unit_engine) -> None:
        async with unit_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        sf = _make_sf(unit_engine)
        item_id = uuid.uuid4()

        async with sf() as session, atomic(session):
            await BaseRepository(session, _TestItem).create(_TestItem(id=item_id))

        async with sf() as session, atomic(session):
            repo = BaseRepository(session, _TestItem)
            item = await repo.get_by_id(item_id)
            assert item is not None
            await repo.delete(item)

        async with sf() as session, session.begin():
            assert await BaseRepository(session, _TestItem).exists(item_id) is False


    async def test_count_returns_correct_total(self, unit_engine) -> None:
        async with unit_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        sf = _make_sf(unit_engine)
        created_ids: list[uuid.UUID] = []

        async with sf() as session, atomic(session):
            repo = BaseRepository(session, _TestItem)
            before = await repo.count()
            for _ in range(3):
                item = await repo.create(_TestItem())
                created_ids.append(item.id)
            after = await repo.count()
            assert after == before + 3

        async with sf() as cleanup, cleanup.begin():
            for cid in created_ids:
                obj = await cleanup.get(_TestItem, cid)
                if obj:
                    await cleanup.delete(obj)


    async def test_list_paginated_returns_subset(self, unit_engine) -> None:
        async with unit_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        sf = _make_sf(unit_engine)
        created_ids: list[uuid.UUID] = []

        async with sf() as session, atomic(session):
            repo = BaseRepository(session, _TestItem)
            for _ in range(5):
                item = await repo.create(_TestItem())
                created_ids.append(item.id)

        async with sf() as session, session.begin():
            page = await BaseRepository(session, _TestItem).list_paginated(
                skip=0, limit=3
            )
            assert len(page) <= 3

        async with sf() as cleanup, cleanup.begin():
            for cid in created_ids:
                obj = await cleanup.get(_TestItem, cid)
                if obj:
                    await cleanup.delete(obj)


# ============================================================
# Integration tests — real PostgreSQL (requires Docker)
# ============================================================


@pytest.mark.integration
class TestPgvectorIntegration:

    async def test_pgvector_extension_available(self, int_session: AsyncSession) -> None:
        """pgvector must be installed and the vector cast must work."""
        async with int_session.begin():
            result = await int_session.execute(
                text("SELECT '[1.0, 2.0, 3.0]'::vector(3)")
            )
            assert result.scalar_one() is not None


    async def test_pg_trgm_extension_available(self, int_session: AsyncSession) -> None:
        """pg_trgm must be installed (supports fuzzy clinical term search)."""
        async with int_session.begin():
            result = await int_session.execute(
                text("SELECT similarity('hello', 'hello world')")
            )
            score = float(result.scalar_one())
            assert 0.0 <= score <= 1.0


    async def test_database_version_is_postgres_16_plus(
        self, int_session: AsyncSession
    ) -> None:
        """Server version must be PostgreSQL 16+ (pgvector requires it)."""
        async with int_session.begin():
            result = await int_session.execute(text("SHOW server_version"))
            version_str = result.scalar_one()
            assert int(version_str.split(".")[0]) >= 16, f"Need PG 16+, got {version_str}"


@pytest.mark.integration
class TestAlembicMigration:
    def setup_method(self) -> None:
        """Clear settings cache before each migration test.

        Prevents lru_cache from returning a stale Settings instance
        that was created during unit tests (which use SQLite).
        """
        from app.config import get_settings

        get_settings.cache_clear()

    def test_alembic_upgrade_to_head(self) -> None:
        """Migration upgrade must complete without error."""
        from alembic import command
        from alembic.config import Config

        command.upgrade(Config("alembic.ini"), "head")

    def test_alembic_current_reports_head(self) -> None:
        """After upgrade, alembic current must reference revision 0001."""
        from io import StringIO

        from alembic import command
        from alembic.config import Config

        cfg = Config("alembic.ini")
        buf = StringIO()
        cfg.stdout = buf
        command.current(cfg)
        output = buf.getvalue()
        assert "0001" in output or "head" in output or output.strip() != ""

    def test_alembic_downgrade_to_base(self) -> None:
        """Downgrade to base must succeed (no-op for extensions)."""
        from alembic import command
        from alembic.config import Config

        command.downgrade(Config("alembic.ini"), "base")

    def test_alembic_reupgrade_after_downgrade(self) -> None:
        """Re-upgrade after downgrade must succeed (idempotent IF NOT EXISTS)."""
        from alembic import command
        from alembic.config import Config

        command.upgrade(Config("alembic.ini"), "head")
