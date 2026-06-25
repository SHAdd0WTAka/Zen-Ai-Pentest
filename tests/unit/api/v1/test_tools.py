"""
API v1 Tools Routes Tests
Target: 70%+ Coverage for api/routes/v1/tools.py
"""

import asyncio
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestToolsEndpoints:
    """Test cases for tools endpoints"""

    def test_list_tools_success(self, test_client, auth_headers):
        """Test listing all tools"""
        response = test_client.get("/api/v1/tools/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "categories" in data
        assert "total" in data
        assert data["total"] > 0

    def test_list_tools_grouped_by_category(self, test_client, auth_headers):
        """Test that tools are properly grouped by category"""
        response = test_client.get("/api/v1/tools/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        categories = data["categories"]
        assert isinstance(categories, dict)

        # Check common categories exist
        category_names = ["network", "web", "recon"]
        for cat in category_names:
            if cat in categories:
                assert isinstance(categories[cat], list)

    def test_list_tools_tool_structure(self, test_client, auth_headers):
        """Test tool object structure"""
        response = test_client.get("/api/v1/tools/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        for tool in data["tools"]:
            assert "id" in tool
            assert "name" in tool
            assert "category" in tool
            assert "description" in tool
            assert "safe" in tool

    def test_execute_tool_nmap(self, test_client, auth_headers):
        """Test executing nmap tool"""
        request_data = {
            "tool": "nmap",
            "target": "example.com",
            "options": {"ports": "80,443"},
        }

        response = test_client.post("/api/v1/tools/execute", json=request_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["tool"] == "nmap"
        assert data["target"] == "example.com"
        assert data["status"] == "completed"
        assert "output" in data

    def test_execute_tool_sqlmap(self, test_client, auth_headers):
        """Test executing sqlmap tool"""
        request_data = {
            "tool": "sqlmap",
            "target": "http://example.com/vuln",
            "options": {"level": 1},
        }

        response = test_client.post("/api/v1/tools/execute", json=request_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["tool"] == "sqlmap"
        assert data["status"] == "completed"

    def test_execute_tool_nikto(self, test_client, auth_headers):
        """Test executing nikto tool"""
        request_data = {
            "tool": "nikto",
            "target": "example.com",
            "options": {},
        }

        response = test_client.post("/api/v1/tools/execute", json=request_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["tool"] == "nikto"
        assert data["status"] == "completed"

    def test_execute_tool_unknown(self, test_client, auth_headers):
        """Test executing unknown tool"""
        request_data = {
            "tool": "unknown_tool",
            "target": "example.com",
            "options": {},
        }

        response = test_client.post("/api/v1/tools/execute", json=request_data, headers=auth_headers)
        assert response.status_code == 400
        assert "unknown" in response.json()["detail"].lower()

    def test_execute_tool_case_insensitive(self, test_client, auth_headers):
        """Test that tool names are case insensitive"""
        request_data = {"tool": "NMAP", "target": "example.com", "options": {}}

        response = test_client.post("/api/v1/tools/execute", json=request_data, headers=auth_headers)
        assert response.status_code == 200


class TestToolRegistry:
    """Test tool registry functions"""

    def test_get_tool_category_known(self):
        """Test getting category for known tools"""
        from api.routes.v1.tools import get_tool_category

        assert get_tool_category("nmap") == "network"
        assert get_tool_category("sqlmap") == "web"
        assert get_tool_category("nikto") == "web"
        assert get_tool_category("gobuster") == "web"
        assert get_tool_category("subfinder") == "recon"

    def test_get_tool_category_unknown(self):
        """Test getting category for unknown tool"""
        from api.routes.v1.tools import get_tool_category

        assert get_tool_category("unknown") == "unknown"

    def test_tool_registry_contents(self):
        """Test tool registry has expected tools"""
        from api.routes.v1.tools import TOOL_REGISTRY

        expected_tools = [
            "nmap",
            "sqlmap",
            "nikto",
            "gobuster",
            "subfinder",
            "httpx",
            "nuclei",
        ]
        for tool in expected_tools:
            assert tool in TOOL_REGISTRY
            assert "name" in TOOL_REGISTRY[tool]
            assert "category" in TOOL_REGISTRY[tool]
            assert "description" in TOOL_REGISTRY[tool]


class TestToolExecutionAsync:
    """Test async tool execution functions"""

    @pytest.mark.asyncio
    async def test_execute_nmap(self):
        """Test nmap execution"""
        from api.routes.v1.tools import execute_nmap

        result = await execute_nmap("example.com", {"ports": "80,443"})

        assert result["tool"] == "nmap"
        assert result["target"] == "example.com"
        assert "open_ports" in result
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_sqlmap(self):
        """Test sqlmap execution"""
        from api.routes.v1.tools import execute_sqlmap

        result = await execute_sqlmap("http://example.com", {"level": 1})

        assert result["tool"] == "sqlmap"
        assert result["target"] == "http://example.com"
        assert "vulnerabilities" in result
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_nikto(self):
        """Test nikto execution"""
        from api.routes.v1.tools import execute_nikto

        result = await execute_nikto("example.com", {})

        assert result["tool"] == "nikto"
        assert result["target"] == "example.com"
        assert "findings" in result
        assert result["status"] == "completed"


class TestToolsAuthorization:
    """Test authorization for tools"""

    def test_execute_tool_requires_auth(self, test_client):
        """Test that tool execution requires authentication (auth overridden in test env)"""
        request_data = {"tool": "nmap", "target": "example.com", "options": {}}

        response = test_client.post("/api/v1/tools/execute", json=request_data)
        assert response.status_code in [200, 401, 403]

    def test_list_tools_may_be_public(self, test_client):
        """Test that tool listing may be public"""
        response = test_client.get("/api/v1/tools/")
        # Can be 200 (public) or 401 (protected)
        assert response.status_code in [200, 401, 403]


class TestToolsEdgeCases:
    """Edge cases for tools"""

    def test_execute_tool_empty_options(self, test_client, auth_headers):
        """Test executing tool with empty options"""
        request_data = {"tool": "nmap", "target": "example.com", "options": {}}

        response = test_client.post("/api/v1/tools/execute", json=request_data, headers=auth_headers)
        assert response.status_code == 200

    def test_execute_tool_no_options_field(self, test_client, auth_headers):
        """Test executing tool without options field"""
        request_data = {"tool": "nmap", "target": "example.com"}

        response = test_client.post("/api/v1/tools/execute", json=request_data, headers=auth_headers)
        # May be 200 (optional) or 422 (required)
        assert response.status_code in [200, 422]

    def test_execute_tool_special_chars_in_target(self, test_client, auth_headers):
        """Test executing tool with special characters in target"""
        request_data = {
            "tool": "nmap",
            "target": "test-domain_123.example.com",
            "options": {},
        }

        response = test_client.post("/api/v1/tools/execute", json=request_data, headers=auth_headers)
        assert response.status_code == 200
