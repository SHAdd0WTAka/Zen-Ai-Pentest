"""Test API route imports"""

import pytest


class TestAPIRouteImports:
    """Test all API routes can be imported"""

    def test_auth_routes_import(self):
        from api.routes.auth import router

        assert router is not None

    def test_scans_routes_import(self):
        from api.routes.scans import router

        assert router is not None

    def test_agents_routes_import(self):
        from api.routes.agents import router

        assert router is not None

    def test_dashboard_routes_import(self):
        from api.routes.dashboard import router

        assert router is not None

    def test_evidence_routes_import(self):
        from api.routes.evidence import router

        assert router is not None

    def test_reports_routes_import(self):
        from api.routes.reports import router

        assert router is not None

    def test_orchestrator_routes_import(self):
        from api.routes.orchestrator import router

        assert router is not None

    def test_subdomain_routes_import(self):
        from api.routes.subdomain import router

        assert router is not None

    def test_findings_routes_import(self):
        from api.routes.findings import router

        assert router is not None

    def test_audit_routes_import(self):
        from api.routes.audit import router

        assert router is not None

    def test_analysis_routes_import(self):
        from api.routes.analysis import router

        assert router is not None

    def test_attack_path_routes_import(self):
        from api.routes.attack_path import router

        assert router is not None


class TestAPIMain:
    """Test API main module"""

    def test_app_import(self):
        from api.main import app

        assert app is not None

    def test_app_has_routes(self):
        from api.main import app

        assert len(app.routes) > 0


class TestAPIModels:
    """Test API schemas"""

    def test_schemas_import(self):
        from api.schemas import ScanCreate, ScanResponse, ToolExecuteRequest

        assert ScanCreate is not None
        assert ScanResponse is not None
        assert ToolExecuteRequest is not None
