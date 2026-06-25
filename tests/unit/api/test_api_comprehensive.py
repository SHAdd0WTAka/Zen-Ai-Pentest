"""Comprehensive API tests"""

import pytest


class TestAPIRoutesComprehensive:
    """Comprehensive API route tests"""

    def test_auth_routes_exist(self):
        from api.routes.auth import router

        assert router is not None
        assert len(router.routes) > 0

    def test_scans_routes_exist(self):
        from api.routes.scans import router

        assert router is not None
        assert len(router.routes) > 0

    def test_agents_routes_exist(self):
        from api.routes.agents import router

        assert router is not None
        assert len(router.routes) > 0

    def test_dashboard_routes_exist(self):
        from api.routes.dashboard import router

        assert router is not None
        assert len(router.routes) > 0

    def test_evidence_routes_exist(self):
        from api.routes.evidence import router

        assert router is not None
        assert len(router.routes) > 0

    def test_reports_routes_exist(self):
        from api.routes.reports import router

        assert router is not None
        assert len(router.routes) > 0

    def test_orchestrator_routes_exist(self):
        from api.routes.orchestrator import router

        assert router is not None
        assert len(router.routes) > 0

    def test_subdomain_routes_exist(self):
        from api.routes.subdomain import router

        assert router is not None
        assert len(router.routes) > 0

    def test_findings_routes_exist(self):
        from api.routes.findings import router

        assert router is not None
        assert len(router.routes) > 0

    def test_audit_routes_exist(self):
        from api.routes.audit import router

        assert router is not None
        assert len(router.routes) > 0

    def test_analysis_routes_exist(self):
        from api.routes.analysis import router

        assert router is not None
        assert len(router.routes) > 0

    def test_attack_path_routes_exist(self):
        from api.routes.attack_path import router

        assert router is not None
        assert len(router.routes) > 0


class TestAPIMainComprehensive:
    """Comprehensive API main tests"""

    def test_app_exists(self):
        from api.main import app

        assert app is not None

    def test_app_has_routes(self):
        from api.main import app

        assert len(app.routes) > 10

    def test_app_has_title(self):
        from api.main import app

        assert app.title is not None


class TestAPISchemasComprehensive:
    """Comprehensive API schema tests"""

    def test_scan_create_schema(self):
        from api.schemas import ScanCreate

        assert ScanCreate is not None

    def test_scan_response_schema(self):
        from api.schemas import ScanResponse

        assert ScanResponse is not None

    def test_tool_execute_request_schema(self):
        from api.schemas import ToolExecuteRequest

        assert ToolExecuteRequest is not None

    def test_finding_response_schema(self):
        from api.schemas import FindingResponse

        assert FindingResponse is not None
