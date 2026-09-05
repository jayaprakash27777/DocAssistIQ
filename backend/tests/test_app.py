"""DocAssistIQ Backend — Tests for application health and readiness.

Phase 1: Tests cover:
  - Liveness (/health) — always 200 regardless of dependency state
  - Readiness (/ready) — probes DB, Redis, Storage; returns 503 on failure
  - Per-dependency failure isolation
  - Multi-dependency failure
  - Application configuration
  - CORS middleware presence
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


# ============================================================
# Helpers
# ============================================================

def _all_deps_healthy_mocks():
    """Return a context-manager stack that mocks all probes as successful."""
    return (
        patch("app.routers.system._probe_redis_sync", return_value={"status": "healthy"}),
        patch("app.routers.system._probe_storage_sync", return_value={"status": "healthy"}),
        patch("app.routers.system._probe_database_async", return_value={"status": "healthy"}),
    )


# ============================================================
# Liveness (/health)
# ============================================================

class TestLiveness:
    """Liveness endpoint must always return 200 regardless of dependency state."""

    def test_health_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_service_name(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.json()["service"] == "DocAssistIQ"

    def test_health_returns_healthy_status(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.json()["status"] == "healthy"

    def test_health_unaffected_by_db_failure(self, client: TestClient) -> None:
        """Liveness must not depend on the database."""
        with patch("app.routers.system._probe_database_async", side_effect=Exception("DB down")):
            response = client.get("/health")
        assert response.status_code == 200

    def test_health_wrong_method_returns_405(self, client: TestClient) -> None:
        response = client.post("/health")
        assert response.status_code == 405


# ============================================================
# Readiness (/ready) — all healthy
# ============================================================

class TestReadinessAllHealthy:
    """When all deps are up, /ready returns 200 with healthy status."""

    def test_ready_returns_200_when_all_healthy(self, client: TestClient) -> None:
        db_mock = patch("app.routers.system._probe_database_async", return_value={"status": "healthy"})
        redis_mock = patch("app.routers.system._probe_redis_sync", return_value={"status": "healthy"})
        storage_mock = patch("app.routers.system._probe_storage_sync", return_value={"status": "healthy"})
        with db_mock, redis_mock, storage_mock:
            response = client.get("/ready")
        assert response.status_code == 200

    def test_ready_overall_status_healthy(self, client: TestClient) -> None:
        db_mock = patch("app.routers.system._probe_database_async", return_value={"status": "healthy"})
        redis_mock = patch("app.routers.system._probe_redis_sync", return_value={"status": "healthy"})
        storage_mock = patch("app.routers.system._probe_storage_sync", return_value={"status": "healthy"})
        with db_mock, redis_mock, storage_mock:
            response = client.get("/ready")
        assert response.json()["status"] == "healthy"

    def test_ready_all_dependency_statuses_present(self, client: TestClient) -> None:
        db_mock = patch("app.routers.system._probe_database_async", return_value={"status": "healthy"})
        redis_mock = patch("app.routers.system._probe_redis_sync", return_value={"status": "healthy"})
        storage_mock = patch("app.routers.system._probe_storage_sync", return_value={"status": "healthy"})
        with db_mock, redis_mock, storage_mock:
            response = client.get("/ready")
        deps = response.json()["dependencies"]
        assert "database" in deps
        assert "redis" in deps
        assert "storage" in deps


# ============================================================
# Readiness — database failure
# ============================================================

class TestReadinessDatabaseFailure:
    """When DB is unreachable, /ready returns 503 with database unhealthy."""

    def test_ready_returns_503_on_db_failure(self, client: TestClient) -> None:
        db_mock = patch(
            "app.routers.system._probe_database_async",
            return_value={"status": "unhealthy", "error": "Connection refused"},
        )
        redis_mock = patch("app.routers.system._probe_redis_sync", return_value={"status": "healthy"})
        storage_mock = patch("app.routers.system._probe_storage_sync", return_value={"status": "healthy"})
        with db_mock, redis_mock, storage_mock:
            response = client.get("/ready")
        assert response.status_code == 503

    def test_ready_database_status_unhealthy(self, client: TestClient) -> None:
        db_mock = patch(
            "app.routers.system._probe_database_async",
            return_value={"status": "unhealthy", "error": "Connection refused"},
        )
        redis_mock = patch("app.routers.system._probe_redis_sync", return_value={"status": "healthy"})
        storage_mock = patch("app.routers.system._probe_storage_sync", return_value={"status": "healthy"})
        with db_mock, redis_mock, storage_mock:
            response = client.get("/ready")
        body = response.json()
        assert body["dependencies"]["database"]["status"] == "unhealthy"
        assert "error" in body["dependencies"]["database"]

    def test_ready_overall_status_degraded_on_db_failure(self, client: TestClient) -> None:
        db_mock = patch(
            "app.routers.system._probe_database_async",
            return_value={"status": "unhealthy", "error": "ECONNREFUSED"},
        )
        redis_mock = patch("app.routers.system._probe_redis_sync", return_value={"status": "healthy"})
        storage_mock = patch("app.routers.system._probe_storage_sync", return_value={"status": "healthy"})
        with db_mock, redis_mock, storage_mock:
            response = client.get("/ready")
        assert response.json()["status"] == "degraded"

    def test_liveness_still_200_when_db_down(self, client: TestClient) -> None:
        """Critical: liveness must stay 200 even when DB is down."""
        response = client.get("/health")
        assert response.status_code == 200


# ============================================================
# Readiness — Redis failure
# ============================================================

class TestReadinessRedisFailure:
    """When Redis is unreachable, /ready returns 503 with redis unhealthy."""

    def test_ready_returns_503_on_redis_failure(self, client: TestClient) -> None:
        db_mock = patch("app.routers.system._probe_database_async", return_value={"status": "healthy"})
        redis_mock = patch(
            "app.routers.system._probe_redis_sync",
            return_value={"status": "unhealthy", "error": "Connection refused"},
        )
        storage_mock = patch("app.routers.system._probe_storage_sync", return_value={"status": "healthy"})
        with db_mock, redis_mock, storage_mock:
            response = client.get("/ready")
        assert response.status_code == 503

    def test_ready_redis_status_unhealthy(self, client: TestClient) -> None:
        db_mock = patch("app.routers.system._probe_database_async", return_value={"status": "healthy"})
        redis_mock = patch(
            "app.routers.system._probe_redis_sync",
            return_value={"status": "unhealthy", "error": "NOAUTH"},
        )
        storage_mock = patch("app.routers.system._probe_storage_sync", return_value={"status": "healthy"})
        with db_mock, redis_mock, storage_mock:
            response = client.get("/ready")
        assert response.json()["dependencies"]["redis"]["status"] == "unhealthy"

    def test_ready_other_deps_still_reported_on_redis_failure(self, client: TestClient) -> None:
        """Other healthy deps must still be visible when Redis is down."""
        db_mock = patch("app.routers.system._probe_database_async", return_value={"status": "healthy"})
        redis_mock = patch(
            "app.routers.system._probe_redis_sync",
            return_value={"status": "unhealthy", "error": "timeout"},
        )
        storage_mock = patch("app.routers.system._probe_storage_sync", return_value={"status": "healthy"})
        with db_mock, redis_mock, storage_mock:
            response = client.get("/ready")
        deps = response.json()["dependencies"]
        assert deps["database"]["status"] == "healthy"
        assert deps["storage"]["status"] == "healthy"


# ============================================================
# Readiness — Storage failure
# ============================================================

class TestReadinessStorageFailure:
    """When MinIO/S3 is unreachable, /ready returns 503 with storage unhealthy."""

    def test_ready_returns_503_on_storage_failure(self, client: TestClient) -> None:
        db_mock = patch("app.routers.system._probe_database_async", return_value={"status": "healthy"})
        redis_mock = patch("app.routers.system._probe_redis_sync", return_value={"status": "healthy"})
        storage_mock = patch(
            "app.routers.system._probe_storage_sync",
            return_value={"status": "unhealthy", "error": "Object storage unreachable"},
        )
        with db_mock, redis_mock, storage_mock:
            response = client.get("/ready")
        assert response.status_code == 503

    def test_ready_storage_error_message_present(self, client: TestClient) -> None:
        db_mock = patch("app.routers.system._probe_database_async", return_value={"status": "healthy"})
        redis_mock = patch("app.routers.system._probe_redis_sync", return_value={"status": "healthy"})
        storage_mock = patch(
            "app.routers.system._probe_storage_sync",
            return_value={"status": "unhealthy", "error": "Bucket 'docassistiq' does not exist"},
        )
        with db_mock, redis_mock, storage_mock:
            response = client.get("/ready")
        assert "error" in response.json()["dependencies"]["storage"]


# ============================================================
# Readiness — Multiple dependency failures
# ============================================================

class TestReadinessMultipleFailures:
    """When multiple deps are down, all must appear as unhealthy."""

    def test_ready_returns_503_when_all_deps_down(self, client: TestClient) -> None:
        db_mock = patch(
            "app.routers.system._probe_database_async",
            return_value={"status": "unhealthy", "error": "ECONNREFUSED"},
        )
        redis_mock = patch(
            "app.routers.system._probe_redis_sync",
            return_value={"status": "unhealthy", "error": "ECONNREFUSED"},
        )
        storage_mock = patch(
            "app.routers.system._probe_storage_sync",
            return_value={"status": "unhealthy", "error": "ECONNREFUSED"},
        )
        with db_mock, redis_mock, storage_mock:
            response = client.get("/ready")
        assert response.status_code == 503

    def test_ready_all_deps_listed_when_multiple_down(self, client: TestClient) -> None:
        db_mock = patch(
            "app.routers.system._probe_database_async",
            return_value={"status": "unhealthy", "error": "DB down"},
        )
        redis_mock = patch(
            "app.routers.system._probe_redis_sync",
            return_value={"status": "unhealthy", "error": "Redis down"},
        )
        storage_mock = patch(
            "app.routers.system._probe_storage_sync",
            return_value={"status": "unhealthy", "error": "MinIO down"},
        )
        with db_mock, redis_mock, storage_mock:
            response = client.get("/ready")
        deps = response.json()["dependencies"]
        assert deps["database"]["status"] == "unhealthy"
        assert deps["redis"]["status"] == "unhealthy"
        assert deps["storage"]["status"] == "unhealthy"

    def test_ready_partial_failure_correct_statuses(self, client: TestClient) -> None:
        """DB down + Redis healthy + Storage down — mixed report."""
        db_mock = patch(
            "app.routers.system._probe_database_async",
            return_value={"status": "unhealthy", "error": "DB down"},
        )
        redis_mock = patch("app.routers.system._probe_redis_sync", return_value={"status": "healthy"})
        storage_mock = patch(
            "app.routers.system._probe_storage_sync",
            return_value={"status": "unhealthy", "error": "MinIO down"},
        )
        with db_mock, redis_mock, storage_mock:
            response = client.get("/ready")
        deps = response.json()["dependencies"]
        assert deps["database"]["status"] == "unhealthy"
        assert deps["redis"]["status"] == "healthy"
        assert deps["storage"]["status"] == "unhealthy"
        assert response.status_code == 503


# ============================================================
# Application configuration
# ============================================================

class TestAppConfiguration:
    def test_app_title(self) -> None:
        assert app.title == "DocAssistIQ"

    def test_app_version(self) -> None:
        assert app.version == "0.1.0"

    def test_docs_available_in_dev(self) -> None:
        assert app.docs_url is not None

    def test_cors_middleware_configured(self) -> None:
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes


class TestConfigSettings:
    def test_settings_load(self) -> None:
        from app.config import get_settings
        settings = get_settings()
        assert settings.app_name == "DocAssistIQ"

    def test_settings_cors_parsing(self) -> None:
        from app.config import get_settings
        origins = get_settings().cors_origins
        assert isinstance(origins, list)
        assert len(origins) >= 1

    def test_settings_is_development(self) -> None:
        from app.config import get_settings
        assert get_settings().is_development is True

    def test_settings_has_redis_url(self) -> None:
        from app.config import get_settings
        assert get_settings().redis_url.startswith("redis://")

    def test_settings_has_storage_config(self) -> None:
        from app.config import get_settings
        settings = get_settings()
        assert settings.object_storage_bucket == "docassistiq"

    def test_settings_has_celery_urls(self) -> None:
        from app.config import get_settings
        settings = get_settings()
        assert "redis://" in settings.celery_broker_url


class TestNegativePaths:
    def test_unknown_route_returns_404(self, client: TestClient) -> None:
        assert client.get("/nonexistent-route").status_code == 404

    def test_health_wrong_method_returns_405(self, client: TestClient) -> None:
        assert client.post("/health").status_code == 405

    def test_ready_wrong_method_returns_405(self, client: TestClient) -> None:
        assert client.post("/ready").status_code == 405
