import asyncio
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tools.nmap_integration import (
    NmapResult,
    NmapScanner,
    ScanType,
    TimingTemplate,
)


@pytest.fixture
def scanner(monkeypatch):
    monkeypatch.setattr("tools.nmap_integration.shutil.which", lambda _: "/usr/bin/nmap")
    return NmapScanner("scanme.nmap.org", {"ports": "top-10"})


def test_validate_targets_rejects_injection(monkeypatch):
    monkeypatch.setattr("tools.nmap_integration.shutil.which", lambda _: "/usr/bin/nmap")
    with pytest.raises(ValueError):
        NmapScanner("example.com; rm -rf /", {})


def test_build_command_covers_multiple_options(scanner):
    scanner.options.update(
        {
            "scan_type": ScanType.CONNECT,
            "timing": TimingTemplate.AGGRESSIVE,
            "no_ping": True,
            "ports": "top-1000",
            "service_detection": True,
            "version_intensity": 5,
            "os_detection": True,
            "osscan_limit": True,
            "script_scan": ["http-title", "vulners"],
            "aggressive": True,
            "source_port": 53,
            "interface": "eth0",
            "max_retries": 2,
            "host_timeout": "30s",
            "scan_delay": "10ms",
            "max_rate": 100,
            "verbosity": 2,
            "debugging": 1,
            "additional_args": ["--reason"],
        }
    )

    cmd = scanner._build_command()

    assert cmd[0] == "/usr/bin/nmap"
    assert "-sT" in cmd
    assert "-T4" in cmd
    assert "--top-ports" in cmd and "1000" in cmd
    assert "-sV" in cmd and "--version-intensity" in cmd
    assert "-O" in cmd and "--osscan-limit" in cmd
    assert "--script" in cmd
    assert "-A" in cmd
    assert "-Pn" in cmd
    assert "scanme.nmap.org" in cmd


def test_parse_xml_output_extracts_host_port_and_scripts(scanner):
    xml = """
    <nmaprun>
      <host>
        <status state="up" />
        <address addr="1.2.3.4" addrtype="ipv4"/>
        <hostnames><hostname name="test.local" /></hostnames>
        <ports>
          <port protocol="tcp" portid="80">
            <state state="open"/>
            <service name="http" product="nginx" version="1.20"/>
            <script id="http-title" output="ok"/>
          </port>
        </ports>
      </host>
    </nmaprun>
    """
    hosts = scanner.parse_xml_output(xml)
    assert len(hosts) == 1
    h = hosts[0]
    assert h.ip == "1.2.3.4"
    assert h.hostname == "test.local"
    assert h.ports[0].service == "http"
    assert h.ports[0].scripts["http-title"] == "ok"


def test_fallback_parse_used_on_malformed_xml(scanner):
    bad_xml = '<host><address addr="2.2.2.2" addrtype="ipv4"/><status state="up"></host'
    hosts = scanner.parse_xml_output(bad_xml)
    assert isinstance(hosts, list)


@pytest.mark.asyncio
async def test_scan_handles_timeout(scanner, monkeypatch):
    async def fake_wait_for(*_args, **_kwargs):
        raise asyncio.TimeoutError()

    monkeypatch.setattr("tools.nmap_integration.asyncio.wait_for", fake_wait_for)
    result = await scanner.scan(timeout=1)
    assert result.success is False
    assert "timed out" in (result.error or "")


@pytest.mark.asyncio
async def test_scan_handles_nonzero_without_stdout(scanner, monkeypatch):
    class Loop:
        async def run_in_executor(self, *_args, **_kwargs):
            return SimpleNamespace(returncode=2, stdout="", stderr="boom")

    monkeypatch.setattr("tools.nmap_integration.asyncio.get_event_loop", lambda: Loop())

    async def passthrough(coro, timeout):
        return await coro

    monkeypatch.setattr("tools.nmap_integration.asyncio.wait_for", passthrough)

    result = await scanner.scan(timeout=1)
    assert result.success is False
    assert "nmap failed" in (result.error or "")


@pytest.mark.asyncio
async def test_scan_ports_and_result_to_dict(scanner, monkeypatch):
    fake_result = NmapResult(success=True, hosts=[], command="nmap", summary={"total_hosts": 0})

    async def _fake_scan():
        return fake_result

    scanner.scan = _fake_scan

    out = await scanner.scan_ports(ports="80,443", scan_type=ScanType.SYN)
    assert out["success"] is True
    assert out["summary"]["total_hosts"] == 0


def test_run_subprocess_executes(monkeypatch, scanner):
    monkeypatch.setattr(
        "tools.nmap_integration.subprocess.run",
        Mock(return_value=subprocess.CompletedProcess(args=["nmap"], returncode=0, stdout="ok", stderr="")),
    )
    cp = scanner._run_subprocess(["nmap"])
    assert cp.returncode == 0
