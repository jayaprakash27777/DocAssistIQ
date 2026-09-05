"""Tests for the DocAssistIQ FastAPI application.

Phase 0: Verify basic application setup and health endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


class TestHealth:
    """Tests for the health endpoint."""

    def test_health_returns_200(self, client: TestClient) -> None:
        """Health endpoint should return 200 with healthy status."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_correct_body(self, client: TestClient) -> None:
        """Health endpoint should return service name and healthy status."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "DocAssistIQ"


class TestAppConfiguration:
    """Tests for application configuration."""

    def test_app_title(self) -> None:
        """FastAPI app should have correct title."""
        assert app.title == "DocAssistIQ"

    def test_app_version(self) -> None:
        """FastAPI app should have a version string."""
        assert app.version == "0.1.0"

    def test_docs_available_in_dev(self) -> None:
        """Docs should be available in development mode."""
        assert app.docs_url is not None

    def test_cors_middleware_configured(self) -> None:
        """CORS middleware should be configured."""
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes


class TestConfigSettings:
    """Tests for Settings configuration."""

    def test_settings_load(self) -> None:
        """Settings should load without errors."""
        from app.config import get_settings

        settings = get_settings()
        assert settings.app_name == "DocAssistIQ"

    def test_settings_cors_parsing(self) -> None:
        """CORS origins should be parsed as a list."""
        from app.config import get_settings

        settings = get_settings()
        origins = settings.cors_origins
        assert isinstance(origins, list)
        assert len(origins) >= 1

    def test_settings_is_development(self) -> None:
        """Default environment should be development."""
        from app.config import get_settings

        settings = get_settings()
        assert settings.is_development is True


class TestNegativePaths:
    """Tests for error/failure conditions."""

    def test_unknown_route_returns_404(self, client: TestClient) -> None:
        """Requesting an unknown route should return 404."""
        response = client.get("/nonexistent-route")
        assert response.status_code == 404

    def test_health_wrong_method(self, client: TestClient) -> None:
        """POST to health endpoint should return 405."""
        response = client.post("/health")
        assert response.status_code == 405
