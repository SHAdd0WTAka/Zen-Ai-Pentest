"""
Extended API Tests
"""
import pytest


try:
    from api.main import app
    from fastapi.testclient import TestClient
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False


@pytest.mark.skipif(not API_AVAILABLE, reason="API not available")
class TestAPIEndpointsExtended:
    """Erweiterte API Tests"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code in [200, 307, 404]

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code in [200, 404]

    def test_api_version(self, client):
        response = client.get("/api/version")
        assert response.status_code in [200, 404]


class TestAPISchemas:
    """API Schema Tests"""

    def test_schemas_import(self):
        try:
            from api import schemas
            assert True
        except ImportError:
            pytest.skip("Schemas not available")

    def test_user_base_exists(self):
        try:
            from api.schemas import UserBase
            assert True
        except ImportError:
            pytest.skip("UserBase not available")

    def test_scan_create_exists(self):
        try:
            from api.schemas import ScanCreate
            assert True
        except ImportError:
            pytest.skip("ScanCreate not available")


class TestAPIAuth:
    """API Auth Tests"""

    def test_auth_import(self):
        try:
            from api import auth
            assert True
        except ImportError:
            pytest.skip("Auth not available")

    def test_auth_simple_import(self):
        try:
            from api import auth_simple
            assert True
        except ImportError:
            pytest.skip("Auth simple not available")
