"""Smoke tests for integration/bridge.py"""

from datetime import datetime

import pytest

from integration.bridge import (
    MetasploitRequest,
    NmapScanRequest,
    ScanRequest,
    ScanResult,
    SQLMapRequest,
    app,
    get_parser,
    health_check,
    parse_nmap_xml,
    parse_nuclei_json,
)


class TestPydanticModels:
    def test_scan_request(self):
        req = ScanRequest(target="example.com")
        assert req.target == "example.com"
        assert req.options == {}

    def test_nmap_scan_request(self):
        req = NmapScanRequest(target="10.0.0.1", scan_type="tcp_syn", scripts=["http-title"])
        assert req.scan_type == "tcp_syn"
        assert req.scripts == ["http-title"]

    def test_sqlmap_request(self):
        req = SQLMapRequest(target="http://example.com/page", url="http://example.com/page?id=1", level=3)
        assert req.level == 3
        assert req.risk == 1

    def test_metasploit_request(self):
        req = MetasploitRequest(module="exploit/multi/http/struts2_rest_xstream", rhosts="10.0.0.5", rport=8080)
        assert req.module.startswith("exploit/")
        assert req.rport == 8080

    def test_scan_result(self):
        result = ScanResult(
            scan_id="abc123",
            tool="nmap",
            target="example.com",
            status="running",
            start_time=datetime.now(),
        )
        assert result.status == "running"
        assert result.scan_id == "abc123"
        assert result.error is None


class TestFastAPIApp:
    def test_app_title(self):
        assert app.title == "Zen Pentest Integration Bridge"

    def test_health_check(self):
        import asyncio

        try:
            resp = asyncio.run(health_check())
            assert resp["status"] == "healthy"
            assert "docker_available" in resp
        except RuntimeError:
            pass

    def test_routes_exist(self):
        paths = [r.path for r in app.routes]
        assert "/api/v1/scan/nmap" in paths
        assert "/api/v1/scan/sqlmap" in paths
        assert "/api/v1/scan/metasploit" in paths
        assert "/health" in paths


class TestParsers:
    def test_get_parser_known(self):
        parser = get_parser("nmap")
        assert parser is parse_nmap_xml

    def test_get_parser_unknown(self):
        parser = get_parser("unknown_tool")
        assert parser is None

    def test_parse_nuclei_json_empty(self, tmp_path):
        f = tmp_path / "nuclei.json"
        f.write_text("")
        results = parse_nuclei_json(f)
        assert results == []

    def test_parse_nuclei_json_valid(self, tmp_path):
        f = tmp_path / "nuclei.json"
        f.write_text('{"info": {"name": "test"}}\n{"info": {"name": "test2"}}\n')
        results = parse_nuclei_json(f)
        assert len(results) == 2
