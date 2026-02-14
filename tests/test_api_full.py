"""
Vollständige API Tests
"""
import pytest
from fastapi.testclient import TestClient


class TestHealth:
    """Health Check Tests"""
    
    def test_health_endpoint(self, client: TestClient):
        """Health Check sollte 200 zurückgeben"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
    
    def test_health_shows_services(self, client: TestClient):
        """Health Check sollte Services zeigen"""
        response = client.get("/health")
        data = response.json()
        assert "services" in data


class TestAuth:
    """Authentication Tests"""
    
    def test_login_success(self, client: TestClient):
        """Login mit gültigen Credentials"""
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_failure(self, client: TestClient):
        """Login mit falschen Credentials"""
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_protected_endpoint_without_auth(self, client: TestClient):
        """Geschützte Endpunkte ohne Auth sollten 401 geben"""
        response = client.get("/auth/me")
        assert response.status_code == 401
    
    def test_protected_endpoint_with_auth(self, client: TestClient, auth_headers):
        """Geschützte Endpunkte mit Auth sollten funktionieren"""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "username" in data


class TestAPIInfo:
    """API Info Tests"""
    
    def test_api_info(self, client: TestClient):
        """API Info Endpoint"""
        response = client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data


class TestTools:
    """Tools API Tests"""
    
    def test_list_tools(self, client: TestClient, auth_headers):
        """Tools Liste abrufen"""
        response = client.get("/tools", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
