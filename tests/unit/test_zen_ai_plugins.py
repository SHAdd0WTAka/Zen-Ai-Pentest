"""
Comprehensive unit tests for zen_ai_pentest built-in tool plugins.

Covers:
    - nmap_plugin
    - nuclei_plugin
    - sqlmap_plugin
    - subfinder_plugin
    - trivy_plugin
"""

import builtins
import io
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import pytest

from zen_ai_pentest.plugin_manager import BaseTool, ToolCategory, ToolRiskLevel
from zen_ai_pentest.plugins import (
    NmapPlugin,
    NucleiPlugin,
    SQLMapPlugin,
    SubfinderPlugin,
    TrivyPlugin,
    get_builtin_plugin,
    list_builtin_plugins,
)

# =============================================================================
# Helpers / Fixtures
# =============================================================================


class _FakeFileHandle:
    """Tiny fake file handle for ``json.load`` / iteration.

    ``read()`` returns the full content on the first call and an empty value
    afterwards so that incremental XML parsers know when EOF is reached.
    """

    def __init__(self, content: str):
        self._content = content
        self._lines = content.splitlines(keepends=True)
        self._consumed = False

    def read(self, *_args, **_kwargs):
        if self._consumed:
            return "" if isinstance(self._content, str) else b""
        self._consumed = True
        return self._content

    def __iter__(self):
        return iter(self._lines)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def fake_files(monkeypatch):
    """Fixture providing an in-memory file system for plugin output paths."""
    _files = {}

    original_exists = Path.exists

    def _exists(self):
        return str(self) in _files

    def _open(path, mode="r", *args, **kwargs):
        key = str(path) if not isinstance(path, str) else path
        if key not in _files:
            raise FileNotFoundError(2, "No such file or directory", key)
        content = _files[key]
        if isinstance(content, bytes):
            if "b" not in mode:
                content = content.decode()
        else:
            if "b" in mode:
                content = content.encode()
        return _FakeFileHandle(content)

    monkeypatch.setattr(Path, "exists", _exists)
    monkeypatch.setattr(builtins, "open", _open)
    monkeypatch.setattr(io, "open", _open)

    return _files


# =============================================================================
# Shared metadata tests
# =============================================================================


@pytest.mark.parametrize(
    "plugin_cls, expected_name, category, risk_level",
    [
        (NmapPlugin, "nmap", ToolCategory.NETWORK_SCANNING, ToolRiskLevel.MEDIUM),
        (NucleiPlugin, "nuclei", ToolCategory.VULNERABILITY_SCANNER, ToolRiskLevel.MEDIUM),
        (SQLMapPlugin, "sqlmap", ToolCategory.WEB_APPLICATION, ToolRiskLevel.HIGH),
        (SubfinderPlugin, "subfinder", ToolCategory.RECONNAISSANCE, ToolRiskLevel.LOW),
        (TrivyPlugin, "trivy", ToolCategory.CONTAINER_SECURITY, ToolRiskLevel.LOW),
    ],
)
def test_plugin_metadata(plugin_cls, expected_name, category, risk_level):
    inst = plugin_cls()
    assert isinstance(inst, BaseTool)
    md = inst.metadata
    assert md.name == expected_name
    assert md.category == category
    assert md.risk_level == risk_level
    assert md.description
    assert md.author
    assert isinstance(md.tags, list)
    assert isinstance(md.supported_platforms, list)
    assert isinstance(md.output_formats, list)
    assert md.max_execution_time > 0
    assert md.max_memory_mb > 0


def test_metadata_to_dict_roundtrip():
    md = NmapPlugin.METADATA
    d = md.to_dict()
    restored = NmapPlugin.METADATA.__class__.from_dict(d)
    assert restored.name == md.name
    assert restored.version == md.version


def _build_nmap_xml():
    """Return a well-formed nmap XML string for tests."""
    root = ET.Element("nmaprun")
    host = ET.SubElement(root, "host")
    status = ET.SubElement(host, "status")
    status.set("state", "up")
    address = ET.SubElement(host, "address")
    address.set("addr", "192.168.1.1")
    address.set("addrtype", "ipv4")
    hostnames = ET.SubElement(host, "hostnames")
    hostname = ET.SubElement(hostnames, "hostname")
    hostname.set("name", "router")
    hostname.set("type", "PTR")
    ports = ET.SubElement(host, "ports")
    for portid, svc_name in [("22", "ssh"), ("23", "telnet")]:
        port = ET.SubElement(ports, "port")
        port.set("protocol", "tcp")
        port.set("portid", portid)
        state = ET.SubElement(port, "state")
        state.set("state", "open")
        service = ET.SubElement(port, "service")
        service.set("name", svc_name)
        if svc_name == "ssh":
            service.set("product", "OpenSSH")
            service.set("version", "8.2")
    os_elem = ET.SubElement(host, "os")
    osmatch = ET.SubElement(os_elem, "osmatch")
    osmatch.set("name", "Linux 5.4")
    osmatch.set("accuracy", "98")
    runstats = ET.SubElement(root, "runstats")
    finished = ET.SubElement(runstats, "finished")
    finished.set("elapsed", "12.34")
    finished.set("summary", "Done")
    return ET.tostring(root, encoding="unicode")


# =============================================================================
# Nmap plugin
# =============================================================================


class TestNmapPlugin:
    @pytest.fixture
    def plugin(self):
        return NmapPlugin()

    def test_validate_input_accepts_ip(self, plugin):
        assert plugin.validate_input("192.168.1.1", {}) is True

    def test_validate_input_accepts_cidr(self, plugin):
        assert plugin.validate_input("10.0.0.0/24", {}) is True

    def test_validate_input_accepts_hostname(self, plugin):
        assert plugin.validate_input("example.com", {}) is True

    def test_validate_input_rejects_empty(self, plugin):
        assert plugin.validate_input("", {}) is False

    def test_validate_input_rejects_invalid_ports(self, plugin):
        assert plugin.validate_input("1.2.3.4", {"ports": "abc"}) is False

    def test_validate_input_accepts_valid_ports(self, plugin):
        assert plugin.validate_input("1.2.3.4", {"ports": "80,443,8080-8090"}) is True

    def test_validate_input_ports_non_string(self, plugin):
        # Non-string ports skip the regex validation branch.
        assert plugin.validate_input("1.2.3.4", {"ports": [80, 443]}) is True

    def test_validate_input_warns_bad_target(self, plugin, caplog):
        with caplog.at_level("WARNING"):
            assert plugin.validate_input("not a target", {}) is True
        assert "may be invalid" in caplog.text

    def test_build_command_default(self, plugin):
        cmd = plugin.build_command("192.168.1.1", {})
        assert cmd[:2] == ["nmap", "-sS"]
        assert "-sV" in cmd
        assert "-p-" in cmd
        assert "-T4" in cmd
        assert cmd[-1] == "192.168.1.1"

    def test_build_command_all_scan_types(self, plugin):
        for st, flag in [
            ("syn", "-sS"),
            ("connect", "-sT"),
            ("udp", "-sU"),
            ("ack", "-sA"),
            ("window", "-sW"),
            ("maimon", "-sM"),
            ("fin", "-sF"),
            ("null", "-sN"),
            ("xmas", "-sX"),
        ]:
            cmd = plugin.build_command("1.1.1.1", {"scan_type": st})
            assert flag in cmd

    def test_build_command_options(self, plugin):
        cmd = plugin.build_command(
            "1.1.1.1",
            {
                "scan_type": "udp",
                "service_detection": False,
                "os_detection": True,
                "script_scan": True,
                "scripts": "vuln",
                "ports": "22,80",
                "timing": "T3",
                "output_format": "grepable",
                "verbose": True,
                "reason": True,
            },
        )
        assert "-sU" in cmd
        assert "-sV" not in cmd
        assert "-O" in cmd
        assert "--script" in cmd and "vuln" in cmd
        assert "-p" in cmd and "22,80" in cmd
        assert "-T3" in cmd
        assert "-oG" in cmd
        assert "-v" in cmd
        assert "--reason" in cmd

    def test_build_command_xml_output(self, plugin):
        cmd = plugin.build_command("1.1.1.1", {"output_format": "xml"})
        assert "-oX" in cmd and "/output/nmap_output.xml" in cmd

    def test_build_command_output_format_json(self, plugin):
        cmd = plugin.build_command("1.1.1.1", {"output_format": "json"})
        assert "-oX" not in cmd
        assert "-oG" not in cmd

    def test_parse_output_text(self, plugin):
        # Avoid the plugin's service-string/service-dict mismatch by providing
        # host + OS lines only.  Port parsing is covered directly below.
        stdout = "Nmap scan report for 192.168.1.1\nOS details: Linux 5.4\n"
        result = plugin.parse_output(stdout, "")
        assert result["hosts"][0]["host"] == "192.168.1.1"
        assert result["hosts"][0]["os"] == "Linux 5.4"
        assert any(f["type"] == "os_detection" for f in result["findings"])

    def test_parse_text_output_ports(self, plugin):
        stdout = "Nmap scan report for 192.168.1.1\n22/tcp open  ssh   OpenSSH 8.2\n23/tcp open  telnet\n80/tcp closed http\n"
        hosts = plugin._parse_text_output(stdout)
        assert hosts[0]["host"] == "192.168.1.1"
        assert len(hosts[0]["ports"]) == 3
        port22 = next(p for p in hosts[0]["ports"] if p["port"] == "22")
        assert port22["service"] == "ssh"
        assert port22["version"] == "OpenSSH 8.2"

    def test_parse_text_output_multiple_hosts(self, plugin):
        stdout = "Nmap scan report for 192.168.1.1\nNmap scan report for 192.168.1.2\n"
        hosts = plugin._parse_text_output(stdout)
        assert len(hosts) == 2
        assert hosts[0]["host"] == "192.168.1.1"
        assert hosts[1]["host"] == "192.168.1.2"

    def test_parse_output_xml_updates_scan_stats(self, plugin, fake_files):
        # parse_output calls _parse_xml_output and then overwrites hosts with
        # text parsing, so we verify the XML-derived scan_stats are preserved.
        fake_files["/output/nmap_output.xml"] = _build_nmap_xml()
        result = plugin.parse_output("", "")
        assert result["scan_stats"]["elapsed"] == "12.34"

    def test_parse_xml_output_missing_finished(self, plugin, fake_files):
        root = ET.Element("nmaprun")
        host = ET.SubElement(root, "host")
        status = ET.SubElement(host, "status")
        status.set("state", "up")
        # runstats present but no <finished>
        ET.SubElement(root, "runstats")
        fake_files["/output/nmap_output.xml"] = ET.tostring(root, encoding="unicode")
        parsed = plugin._parse_xml_output("/output/nmap_output.xml")
        assert parsed["scan_stats"] == {}

    def test_parse_output_xml_malformed(self, plugin, fake_files, caplog):
        fake_files["/output/nmap_output.xml"] = "not-valid-xml"
        with caplog.at_level("WARNING"):
            result = plugin.parse_output("", "")
        assert "Failed to parse XML" in caplog.text or "XML parsing error" in caplog.text
        assert result["hosts"] == []
        assert result["findings"] == []

    def test_parse_output_xml_raises(self, plugin, monkeypatch, caplog):
        def _raise(*_args, **_kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(plugin, "_parse_xml_output", _raise)
        with caplog.at_level("WARNING"):
            result = plugin.parse_output("", "")
        assert "Failed to parse XML" in caplog.text
        assert result["hosts"] == []

    def test_parse_xml_output(self, plugin, fake_files):
        fake_files["/output/nmap_output.xml"] = _build_nmap_xml()
        parsed = plugin._parse_xml_output("/output/nmap_output.xml")
        host = parsed["hosts"][0]
        assert host["status"] == "up"
        assert host["addresses"][0]["addr"] == "192.168.1.1"
        assert len(host["ports"]) == 2
        assert host["ports"][0]["service"]["name"] == "ssh"
        assert host["os"][0]["name"] == "Linux 5.4"

    def test_parse_host_element_minimal(self, plugin, fake_files):
        root = ET.Element("nmaprun")
        host = ET.SubElement(root, "host")
        # No status, no addresses, no hostnames, ports without state/service
        ports = ET.SubElement(host, "ports")
        port = ET.SubElement(ports, "port")
        port.set("protocol", "tcp")
        port.set("portid", "80")
        parsed = plugin._parse_host_element(host)
        assert parsed["status"] == "unknown"
        assert parsed["addresses"] == []
        assert parsed["hostnames"] == []
        assert parsed["ports"][0]["state"] == "unknown"
        assert parsed["ports"][0]["service"] == {}

    def test_parse_output_xml_fallback_to_stdlib(self, plugin, fake_files, monkeypatch):
        """Cover the ImportError fallback branch in _parse_xml_output."""
        root = ET.Element("nmaprun")
        host = ET.SubElement(root, "host")
        status = ET.SubElement(host, "status")
        status.set("state", "up")
        address = ET.SubElement(host, "address")
        address.set("addr", "10.0.0.1")
        address.set("addrtype", "ipv4")
        fake_files["/output/nmap_output.xml"] = ET.tostring(root, encoding="unicode")
        monkeypatch.setitem(sys.modules, "defusedxml", None)
        parsed = plugin._parse_xml_output("/output/nmap_output.xml")
        assert parsed["hosts"][0]["addresses"][0]["addr"] == "10.0.0.1"

    def test_extract_findings_severity(self, plugin):
        hosts = [
            {
                "addresses": [{"addr": "1.1.1.1"}],
                "ports": [
                    {"state": "open", "portid": "23", "protocol": "tcp", "service": {"name": "telnet"}},
                    {"state": "open", "portid": "25", "protocol": "tcp", "service": {"name": "smtp"}},
                    {"state": "open", "portid": "22", "protocol": "tcp", "service": {"name": "ssh"}},
                ],
                "os": ["Linux"],
            }
        ]
        findings = plugin._extract_findings(hosts)
        severities = {f["port"]: f["severity"] for f in findings if f["type"] == "open_port"}
        assert severities["23"] == "high"
        assert severities["25"] == "medium"
        assert severities["22"] == "info"

    def test_extract_findings_no_os(self, plugin):
        hosts = [{"addresses": [{"addr": "1.1.1.1"}], "ports": [], "os": None}]
        findings = plugin._extract_findings(hosts)
        assert findings == []


# =============================================================================
# Nuclei plugin
# =============================================================================


class TestNucleiPlugin:
    @pytest.fixture
    def plugin(self):
        return NucleiPlugin()

    def test_validate_input_accepts_url(self, plugin):
        assert plugin.validate_input("https://example.com", {}) is True

    def test_validate_input_accepts_ip(self, plugin):
        assert plugin.validate_input("192.168.1.1", {}) is True

    def test_validate_input_accepts_cidr(self, plugin):
        assert plugin.validate_input("192.168.1.0/24", {}) is True

    def test_validate_input_rejects_empty(self, plugin):
        assert plugin.validate_input("", {}) is False

    def test_validate_input_warns_file_path(self, plugin, caplog):
        with caplog.at_level("WARNING"):
            assert plugin.validate_input("bad-target", {}) is True
        assert "may be invalid" in caplog.text

    def test_validate_input_file_path_no_warning(self, plugin, caplog):
        with caplog.at_level("WARNING"):
            assert plugin.validate_input("/tmp/targets.txt", {}) is True
        assert "may be invalid" not in caplog.text

    def test_validate_input_template_warning(self, plugin, caplog):
        with caplog.at_level("WARNING"):
            assert plugin.validate_input("http://x.com", {"templates": ["bad.tpl"]}) is True
        assert "Template format may be invalid" in caplog.text

    def test_validate_input_valid_template(self, plugin, caplog):
        with caplog.at_level("WARNING"):
            assert plugin.validate_input("http://x.com", {"templates": ["cves.yaml"]}) is True
        assert "Template format" not in caplog.text

    def test_build_command_default(self, plugin):
        cmd = plugin.build_command("https://example.com", {})
        assert cmd[0] == "nuclei"
        assert "-u" in cmd and "https://example.com" in cmd
        assert "/root/nuclei-templates/" in cmd
        assert "-silent" in cmd
        assert "-nc" in cmd
        assert "-json" in cmd

    def test_build_command_full_options(self, plugin):
        cmd = plugin.build_command(
            "http://target",
            {
                "templates": ["cves.yaml", "exposures.yaml"],
                "severity": "high,critical",
                "tags": "cisco",
                "exclude_tags": "dos",
                "author": "pdteam",
                "rate_limit": 100,
                "bulk_size": 25,
                "concurrency": 50,
                "timeout": 10,
                "retries": 3,
                "output_format": "sarif",
                "silent": False,
                "no_color": False,
                "update_templates": True,
                "validate": True,
                "debug": True,
                "verbose": True,
                "headers": ["X-Auth: 1", "X-Token: 2"],
                "proxy": "http://proxy:8080",
                "follow_redirects": True,
                "max_redirects": 5,
                "interactsh_server": "interact.sh",
            },
        )
        assert cmd.count("-t") == 2
        assert "-s" in cmd and "high,critical" in cmd
        assert "-tags" in cmd and "cisco" in cmd
        assert "-etags" in cmd and "dos" in cmd
        assert "-author" in cmd and "pdteam" in cmd
        assert "-rl" in cmd and "100" in cmd
        assert "-bs" in cmd and "25" in cmd
        assert "-c" in cmd and "50" in cmd
        assert "-timeout" in cmd and "10" in cmd
        assert "-retries" in cmd and "3" in cmd
        assert "-sarif" in cmd
        assert "-o" in cmd and "/output/nuclei_results.json" in cmd
        assert "-ut" in cmd
        assert "-validate" in cmd
        assert "-debug" in cmd
        assert "-v" in cmd
        assert "-fr" in cmd
        assert "-mr" in cmd and "5" in cmd
        assert "-iserver" in cmd and "interact.sh" in cmd
        assert cmd.count("-H") == 2
        assert "-proxy" in cmd and "http://proxy:8080" in cmd
        assert "-silent" not in cmd
        assert "-nc" not in cmd

    def test_parse_output_json(self, plugin, fake_files):
        lines = [
            json.dumps(
                {
                    "template-id": "CVE-2023-TEST",
                    "info": {
                        "name": "Test High",
                        "severity": "high",
                        "description": "A bug",
                        "reference": ["https://ref"],
                        "tags": ["cve"],
                    },
                    "host": "http://example.com",
                    "matched-at": "http://example.com/x",
                    "matcher-name": "word",
                    "extracted-results": ["secret"],
                    "curl-command": "curl http://example.com/x",
                }
            ),
            json.dumps(
                {
                    "template-id": "INFO-1",
                    "info": {"name": "Info Thing", "severity": "info"},
                    "host": "http://ex.com",
                }
            ),
        ]
        fake_files["/output/nuclei_results.json"] = "\n".join(lines)
        stdout = "[INF] 150 templates loaded\n[INF] 10 hosts scanned\n[INF] 2 vulnerabilities found"
        result = plugin.parse_output(stdout, "")
        assert len(result["vulnerabilities"]) == 2
        assert result["statistics"]["templates_loaded"] == 150
        assert result["statistics"]["hosts_scanned"] == 10
        assert result["statistics"]["vulnerabilities_found"] == 2
        findings = result["findings"]
        assert findings[0]["severity"] == "high"
        assert findings[0]["severity_score"] == 3
        assert findings[1]["severity"] == "info"

    def test_validate_input_templates_string(self, plugin):
        assert plugin.validate_input("http://x.com", {"templates": "custom.yaml"}) is True

    def test_build_command_templates_string_and_markdown(self, plugin):
        cmd = plugin.build_command("http://x.com", {"templates": "custom.yaml", "output_format": "markdown"})
        assert cmd.count("-t") == 1
        assert "custom.yaml" in cmd
        assert "-markdown" in cmd

    def test_build_command_output_format_text(self, plugin):
        cmd = plugin.build_command("http://x.com", {"output_format": "text"})
        assert "-json" not in cmd
        assert "-markdown" not in cmd
        assert "-sarif" not in cmd

    def test_parse_output_json_malformed_line(self, plugin, fake_files):
        fake_files["/output/nuclei_results.json"] = "not-json\n"
        result = plugin.parse_output("", "")
        assert result["vulnerabilities"] == []

    def test_parse_output_missing_file(self, plugin):
        result = plugin.parse_output("", "")
        assert result["vulnerabilities"] == []
        assert result["findings"] == []

    def test_parse_output_json_with_blank_lines(self, plugin, fake_files):
        fake_files["/output/nuclei_results.json"] = "\n{}\n\n{}\n"
        result = plugin.parse_output("", "")
        assert len(result["vulnerabilities"]) == 2

    def test_parse_output_file_open_error(self, plugin, fake_files, monkeypatch, caplog):
        fake_files["/output/nuclei_results.json"] = "irrelevant"
        original_fake_open = builtins.open

        def _raising_open(path, mode="r", *args, **kwargs):
            key = str(path) if not isinstance(path, str) else path
            if key == "/output/nuclei_results.json":
                raise PermissionError("denied")
            return original_fake_open(path, mode, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", _raising_open)
        monkeypatch.setattr(io, "open", _raising_open)
        with caplog.at_level("WARNING"):
            result = plugin.parse_output("", "")
        assert "Failed to parse JSON" in caplog.text
        assert result["vulnerabilities"] == []

    def test_parse_statistics_regex(self, plugin):
        stats = plugin._parse_statistics("[INF] 7 templates loaded\n[INF] 3 hosts scanned\n[INF] 11 vulnerabilities found")
        assert stats == {"templates_loaded": 7, "hosts_scanned": 3, "vulnerabilities_found": 11}


# =============================================================================
# SQLMap plugin
# =============================================================================


class TestSQLMapPlugin:
    @pytest.fixture
    def plugin(self):
        return SQLMapPlugin()

    def test_validate_input_accepts_url(self, plugin):
        assert plugin.validate_input("https://example.com/page.php?id=1", {}) is True

    def test_validate_input_rejects_invalid_url(self, plugin):
        assert plugin.validate_input("not-a-url", {}) is False

    def test_validate_input_rejects_empty(self, plugin):
        assert plugin.validate_input("", {}) is False

    def test_validate_input_warns_no_injection_point(self, plugin, caplog):
        with caplog.at_level("WARNING"):
            assert plugin.validate_input("https://example.com/page", {}) is True
        assert "injection point" in caplog.text

    def test_validate_input_query_param_no_warning(self, plugin, caplog):
        with caplog.at_level("WARNING"):
            assert plugin.validate_input("https://example.com/page?id=1", {}) is True
        assert "injection point" not in caplog.text

    def test_validate_input_with_data_no_warning(self, plugin, caplog):
        with caplog.at_level("WARNING"):
            assert plugin.validate_input("https://example.com/page", {"data": "id=1"}) is True
        assert "injection point" not in caplog.text

    def test_validate_input_warns_high_risk(self, plugin, caplog):
        with caplog.at_level("WARNING"):
            assert plugin.validate_input("https://x/?id=1", {"risk": 5}) is True
        assert "High risk" in caplog.text

    def test_validate_input_warns_high_level(self, plugin, caplog):
        with caplog.at_level("WARNING"):
            assert plugin.validate_input("https://x/?id=1", {"level": 5}) is True
        assert "High detection level" in caplog.text

    def test_build_command_default(self, plugin):
        cmd = plugin.build_command("https://x/?id=1", {})
        assert cmd[:2] == ["sqlmap", "-u"]
        assert "https://x/?id=1" in cmd
        assert "--risk" in cmd and "1" in cmd
        assert "--level" in cmd and "1" in cmd
        assert "--batch" in cmd
        assert "--random-agent" in cmd
        assert "--threads" in cmd and "1" in cmd
        assert "--timeout" in cmd and "30" in cmd

    def test_build_command_full_options(self, plugin):
        cmd = plugin.build_command(
            "https://x/?id=1",
            {
                "data": "user=1",
                "cookie": "session=abc",
                "headers": ["X-Token: 1"],
                "user_agent": "Mozilla/5.0",
                "risk": 2,
                "level": 3,
                "dbs": True,
                "tables": True,
                "columns": True,
                "dump": True,
                "dump_all": True,
                "db": "mysql",
                "table": "users",
                "column": "pass",
                "technique": "BEUSTQ",
                "threads": 10,
                "timeout": 60,
                "batch": False,
                "flush_session": True,
                "random_agent": False,
                "tamper": "base64encode",
                "verbose": True,
            },
        )
        assert "--data" in cmd and "user=1" in cmd
        assert "--cookie" in cmd and "session=abc" in cmd
        assert "--header" in cmd and "X-Token: 1" in cmd
        assert "--user-agent" in cmd and "Mozilla/5.0" in cmd
        assert "--dbs" in cmd
        assert "--tables" in cmd
        assert "--columns" in cmd
        assert "--dump" in cmd
        assert "--dump-all" in cmd
        assert "-D" in cmd and "mysql" in cmd
        assert "-T" in cmd and "users" in cmd
        assert "-C" in cmd and "pass" in cmd
        assert "--technique" in cmd and "BEUSTQ" in cmd
        assert "--threads" in cmd and "10" in cmd
        assert "--timeout" in cmd and "60" in cmd
        assert "--flush-session" in cmd
        assert "--tamper" in cmd and "base64encode" in cmd
        assert "-v" in cmd
        # batch is False so no --batch from option, but default output format json adds --batch
        assert cmd.count("--batch") == 1

    def test_parse_output_with_log(self, plugin, fake_files):
        log = {
            "data": [
                {
                    "value": [
                        {
                            "parameter": "id",
                            "type": "boolean-based blind",
                            "title": "MySQL >= 5.0",
                            "payload": "1 AND 1=1",
                        }
                    ]
                }
            ]
        }
        fake_files["/output/log"] = json.dumps(log)
        stdout = (
            "the target is vulnerable\n"
            "the back-end DBMS is MySQL\n"
            "the back-end DBMS operating system is Linux\n"
            "available databases [2]:\n"
            "[*] users\n"
            "Database: users\n"
            "[1] accounts\n"
        )
        result = plugin.parse_output(stdout, "")
        assert result["vulnerable"] is True
        assert result["dbms"] == "MySQL"
        assert result["os"] == "Linux"
        assert "users" in result["databases"]
        assert "accounts" in result["tables"].get("users", [])
        findings = result["findings"]
        assert any(f["type"] == "sql_injection" for f in findings)
        assert any(f["type"] == "database_exposure" for f in findings)
        assert any(f["type"] == "table_exposure" for f in findings)

    def test_parse_output_without_log(self, plugin):
        stdout = "no vulnerability here\n"
        result = plugin.parse_output(stdout, "")
        assert result["vulnerable"] is False
        assert result["findings"] == []

    def test_parse_output_invalid_log(self, plugin, fake_files, caplog):
        fake_files["/output/log"] = "not-json"
        with caplog.at_level("WARNING"):
            result = plugin.parse_output("", "")
        assert "Failed to parse log" in caplog.text
        assert result["findings"] == []

    def test_build_command_non_json_output_format(self, plugin):
        cmd = plugin.build_command("https://x/?id=1", {"output_format": "text"})
        assert "--output-dir" not in cmd
        assert "--batch" in cmd

    def test_parse_stdout_duplicate_db_and_table_lines(self, plugin):
        # Database: users without preceding [*] users -> triggers line 264
        # Duplicate [*] users and [1] accounts -> covers false branches on 254 and 269
        stdout = "Database: users\n[*] users\n[*] users\n[1] accounts\n[1] accounts\n"
        result = plugin._parse_stdout(stdout)
        assert result["databases"] == ["users"]
        assert result["tables"] == {"users": ["accounts"]}


# =============================================================================
# Subfinder plugin
# =============================================================================


class TestSubfinderPlugin:
    @pytest.fixture
    def plugin(self):
        return SubfinderPlugin()

    def test_validate_input_accepts_domain(self, plugin):
        assert plugin.validate_input("example.com", {}) is True

    def test_validate_input_rejects_empty(self, plugin):
        assert plugin.validate_input("", {}) is False

    def test_validate_input_warns_bad_domain(self, plugin, caplog):
        with caplog.at_level("WARNING"):
            assert plugin.validate_input("not a domain", {}) is True
        assert "Domain format may be invalid" in caplog.text

    def test_build_command_default(self, plugin):
        cmd = plugin.build_command("example.com", {})
        assert cmd[:2] == ["subfinder", "-d"]
        assert "example.com" in cmd
        assert "-json" in cmd
        assert "-o" in cmd and "/output/subfinder_results.txt" in cmd
        assert "-silent" in cmd

    def test_build_command_full_options(self, plugin):
        cmd = plugin.build_command(
            "example.com",
            {
                "output_format": "csv",
                "all": True,
                "recursive": True,
                "threads": 50,
                "timeout": 30,
                "rate_limit": 100,
                "max_time": 120,
                "exclude_sources": "archiveis",
                "sources": "crtsh",
                "resolver": "1.1.1.1",
                "resolver_list": "/tmp/r.txt",
                "proxy": "socks5://p:1080",
                "silent": False,
                "verbose": True,
                "statistics": True,
            },
        )
        assert "-csv" in cmd
        assert "-all" in cmd
        assert "-recursive" in cmd
        assert "-t" in cmd and "50" in cmd
        assert "-timeout" in cmd and "30" in cmd
        assert "-rl" in cmd and "100" in cmd
        assert "-max-time" in cmd and "120" in cmd
        assert "-es" in cmd and "archiveis" in cmd
        assert "-s" in cmd and "crtsh" in cmd
        assert "-r" in cmd and "1.1.1.1" in cmd
        assert "-rL" in cmd and "/tmp/r.txt" in cmd
        assert "-proxy" in cmd and "socks5://p:1080" in cmd
        assert "-v" in cmd
        assert "-stats" in cmd
        assert "-silent" not in cmd

    def test_build_command_output_format_text(self, plugin):
        cmd = plugin.build_command("example.com", {"output_format": "text"})
        assert "-json" not in cmd
        assert "-csv" not in cmd

    def test_parse_output_json_list(self, plugin, fake_files):
        fake_files["/output/subfinder_results.txt"] = json.dumps(["www.example.com", "api.example.com", "db.example.com"])
        result = plugin.parse_output("", "")
        assert result["count"] == 3
        assert "api.example.com" in result["subdomains"]
        findings = result["findings"]
        by_sub = {f["subdomain"]: f for f in findings}
        assert by_sub["api.example.com"]["type"] == "api_endpoint"
        assert by_sub["db.example.com"]["type"] == "database"
        assert by_sub["db.example.com"]["severity"] == "high"

    def test_parse_output_json_dict(self, plugin, fake_files):
        fake_files["/output/subfinder_results.txt"] = json.dumps({"subdomains": ["a.example.com"], "count": 1})
        result = plugin.parse_output("", "")
        assert "a.example.com" in result["subdomains"]

    def test_parse_output_text_fallback(self, plugin):
        stdout = "[INFO] starting\nwww.example.com\napi.example.com\n"
        stderr = "archiveis: 5\ncrtsh: 10\n"
        result = plugin.parse_output(stdout, stderr)
        assert sorted(result["subdomains"]) == sorted(["www.example.com", "api.example.com"])
        assert result["sources"] == {"archiveis": 5, "crtsh": 10}

    def test_parse_output_invalid_json_file(self, plugin, fake_files):
        fake_files["/output/subfinder_results.txt"] = "www.example.com\napi.example.com\n"
        result = plugin.parse_output("", "")
        assert sorted(result["subdomains"]) == sorted(["www.example.com", "api.example.com"])

    def test_parse_output_json_primitive(self, plugin, fake_files):
        # JSON that decodes to a primitive (neither list nor dict) falls through.
        fake_files["/output/subfinder_results.txt"] = json.dumps("ignored")
        result = plugin.parse_output("", "")
        assert result["subdomains"] == []

    def test_parse_output_empty_file(self, plugin, fake_files):
        fake_files["/output/subfinder_results.txt"] = ""
        result = plugin.parse_output("", "")
        assert result["subdomains"] == []

    def test_parse_statistics_empty(self, plugin):
        assert plugin._parse_statistics("") == {}

    def test_parse_output_file_open_error(self, plugin, fake_files, monkeypatch, caplog):
        fake_files["/output/subfinder_results.txt"] = "irrelevant"

        original_fake_open = builtins.open

        def _raising_open(path, mode="r", *args, **kwargs):
            key = str(path) if not isinstance(path, str) else path
            if key == "/output/subfinder_results.txt":
                raise PermissionError("denied")
            return original_fake_open(path, mode, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", _raising_open)
        monkeypatch.setattr(io, "open", _raising_open)
        with caplog.at_level("WARNING"):
            result = plugin.parse_output("", "")
        assert "Failed to parse output file" in caplog.text
        assert result["subdomains"] == []


# =============================================================================
# Trivy plugin
# =============================================================================


class TestTrivyPlugin:
    @pytest.fixture
    def plugin(self):
        return TrivyPlugin()

    def test_validate_input_image(self, plugin):
        assert plugin.validate_input("alpine:latest", {"scan_type": "image"}) is True

    def test_validate_input_image_warns_bad_format(self, plugin, caplog):
        with caplog.at_level("WARNING"):
            assert plugin.validate_input("bad image:ref", {"scan_type": "image"}) is True
        assert "may be invalid" in caplog.text

    def test_validate_input_fs_missing_path(self, plugin, tmp_path, caplog):
        missing = tmp_path / "missing"
        with caplog.at_level("ERROR"):
            assert plugin.validate_input(str(missing), {"scan_type": "fs"}) is False
        assert "does not exist" in caplog.text

    def test_validate_input_fs_existing_path(self, plugin, tmp_path):
        existing = tmp_path / "exists"
        existing.mkdir()
        assert plugin.validate_input(str(existing), {"scan_type": "fs"}) is True

    def test_validate_input_repo(self, plugin):
        assert plugin.validate_input("https://github.com/foo/bar", {"scan_type": "repo"}) is True

    def test_validate_input_repo_warns(self, plugin, caplog):
        with caplog.at_level("WARNING"):
            assert plugin.validate_input("foo/bar", {"scan_type": "repo"}) is True
        assert "may be invalid" in caplog.text

    def test_build_command_default(self, plugin):
        cmd = plugin.build_command("alpine:latest", {})
        assert cmd[:2] == ["trivy", "image"]
        assert "alpine:latest" in cmd
        assert "--format" in cmd and "json" in cmd
        assert "--output" in cmd and "/output/trivy_results.json" in cmd
        assert "--scanners" in cmd and "vuln,config,secret" in cmd
        assert "--quiet" in cmd

    def test_build_command_full_options(self, plugin):
        cmd = plugin.build_command(
            "myimage:tag",
            {
                "scan_type": "fs",
                "output_format": "sarif",
                "severity": "HIGH,CRITICAL",
                "vuln_types": "os,library",
                "scanners": ["vuln", "secret"],
                "skip_update": True,
                "offline": True,
                "ignore_unfixed": True,
                "exit_code": 1,
                "timeout": "10m",
                "cache_dir": "/tmp/trivycache",
                "quiet": False,
                "debug": True,
                "skip_files": ["/skip1", "/skip2"],
                "skip_dirs": ["/dir1"],
            },
        )
        assert cmd[1] == "fs"
        assert "--format" in cmd and "sarif" in cmd
        assert "--severity" in cmd and "HIGH,CRITICAL" in cmd
        assert "--vuln-type" in cmd and "os,library" in cmd
        assert "--scanners" in cmd and "vuln,secret" in cmd
        assert "--skip-update" in cmd
        assert "--offline-scan" in cmd
        assert "--ignore-unfixed" in cmd
        assert "--exit-code" in cmd and "1" in cmd
        assert "--timeout" in cmd and "10m" in cmd
        assert "--cache-dir" in cmd and "/tmp/trivycache" in cmd
        assert "--debug" in cmd
        assert "--skip-files" in cmd and "/skip1" in cmd and "/skip2" in cmd
        assert "--skip-dirs" in cmd and "/dir1" in cmd
        assert "--quiet" not in cmd

    def test_build_command_scanners_string(self, plugin):
        cmd = plugin.build_command("img:tag", {"scanners": "vuln"})
        assert "--scanners" in cmd and "vuln" in cmd

    def test_parse_output_json(self, plugin, fake_files):
        data = {
            "Results": [
                {
                    "Target": "alpine:latest",
                    "Class": "os-pkgs",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2023-HIGH",
                            "PkgName": "curl",
                            "InstalledVersion": "7.88",
                            "FixedVersion": "7.89",
                            "Severity": "HIGH",
                            "Title": "Buffer overflow",
                            "Description": "bad",
                            "References": ["https://ref"],
                            "CVSS": {"V3": {"Score": 7.5}},
                            "PrimaryURL": "https://primary",
                        }
                    ],
                    "Misconfigurations": [
                        {
                            "ID": "KSV001",
                            "Title": "Privileged container",
                            "Description": "Should not be privileged",
                            "Severity": "MEDIUM",
                            "Message": "msg",
                            "Resolution": "res",
                            "References": ["ref"],
                        }
                    ],
                    "Secrets": [
                        {
                            "RuleID": "aws-key",
                            "Category": "AWS",
                            "Severity": "CRITICAL",
                            "Title": "AWS Access Key",
                            "Match": "AKIAIOSFODNN7EXAMPLE",
                        }
                    ],
                }
            ]
        }
        fake_files["/output/trivy_results.json"] = json.dumps(data)
        result = plugin.parse_output("", "")
        assert len(result["vulnerabilities"]) == 1
        assert len(result["misconfigurations"]) == 1
        assert len(result["secrets"]) == 1
        assert result["summary"]["total_vulnerabilities"] == 1
        assert result["summary"]["severity_counts"]["HIGH"] == 1
        findings = result["findings"]
        severities = [f["severity"] for f in findings]
        assert severities == ["critical", "high", "medium"]
        vuln_finding = next(f for f in findings if f["type"] == "container_vulnerability")
        assert vuln_finding["cvss_score"] == 7.5
        assert vuln_finding["vulnerability_id"] == "CVE-2023-HIGH"

    def test_parse_output_missing_file(self, plugin):
        result = plugin.parse_output("", "")
        assert result["findings"] == []

    def test_validate_input_empty(self, plugin):
        assert plugin.validate_input("", {}) is False

    def test_parse_output_invalid_json(self, plugin, fake_files, caplog):
        fake_files["/output/trivy_results.json"] = "not-json"
        with caplog.at_level("WARNING"):
            result = plugin.parse_output("", "")
        assert "Failed to parse JSON" in caplog.text
        assert result["findings"] == []

    def test_extract_cvss_score(self, plugin):
        assert plugin._extract_cvss_score({}) is None
        assert plugin._extract_cvss_score({"V3": {"Score": 9.8}}) == 9.8
        assert plugin._extract_cvss_score({"V2": {"Score": 5.0}}) == 5.0
        assert plugin._extract_cvss_score({"V3": {"Score": None}}) is None


# =============================================================================
# Plugin package helpers
# =============================================================================


def test_get_builtin_plugin():
    assert get_builtin_plugin("nmap") is NmapPlugin
    assert get_builtin_plugin("not-a-plugin") is None


def test_list_builtin_plugins():
    plugins = list_builtin_plugins()
    assert isinstance(plugins, list)
    assert set(plugins) == {"nmap", "nuclei", "sqlmap", "subfinder", "trivy"}
