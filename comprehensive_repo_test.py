#!/usr/bin/env python3
"""
ZEN AI PENTEST - KOMPREHENSIVER REPO-TEST
Testet ALLE Komponenten des gesamten Repositories
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Test-Konfiguration
REPO_PATH = Path(__file__).parent
TEST_RESULTS = {}


def log_test(name, status, details=""):
    """Log test result"""
    symbol = "[OK]" if status else "[FAIL]"
    TEST_RESULTS[name] = {"status": status, "details": details}
    print(f"  {symbol} {name:<40} {details}")


def test_file_structure():
    """Test 1: Repository Struktur"""
    print("\n[TEST 1] Repository Struktur")
    print("-" * 70)

    required_dirs = ["api", "autonomous", "backends", "core", "modules", "utils", "logs", "demos", "tests"]

    for dir_name in required_dirs:
        path = REPO_PATH / dir_name
        exists = path.exists() and path.is_dir()
        log_test(f"Dir: {dir_name}/", exists, "exists" if exists else "missing")

    required_files = ["zen_ai_pentest.py", "config.json", "requirements.txt", "README.md", "setup.py"]

    for file_name in required_files:
        path = REPO_PATH / file_name
        exists = path.exists() and path.is_file()
        log_test(f"File: {file_name}", exists, "exists" if exists else "missing")


def test_python_modules():
    """Test 2: Alle Python Module importierbar"""
    print("\n[TEST 2] Python Module Imports")
    print("-" * 70)

    modules_to_test = [
        ("modules.report_gen", "ReportGenerator"),
        ("modules.recon", "ReconModule"),
        ("modules.vuln_scanner", "VulnScannerModule"),
        ("modules.exploit_assist", "ExploitAssistModule"),
        ("modules.report_export", "ReportExporter"),
        ("modules.siem_integration", None),
        ("backends.duckduckgo", "DuckDuckGoBackend"),
        ("backends.openrouter", "OpenRouterBackend"),
        ("core.orchestrator", "ZenOrchestrator"),
        ("autonomous.agent_loop", "AutonomousAgentLoop"),
        ("autonomous.agent", "AutonomousAgent"),
        ("utils.helpers", "banner"),
        ("utils.stealth", "StealthManager"),
    ]

    for module_path, class_name in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name or ""])
            if class_name:
                getattr(module, class_name)
            log_test(f"Import: {module_path}", True)
        except Exception as e:
            log_test(f"Import: {module_path}", False, str(e)[:30])


def test_autonomous_functionality():
    """Test 3: Autonome Funktionen"""
    print("\n[TEST 3] Autonome Funktionen")
    print("-" * 70)

    # Test autonomous workflow
    try:
        sys.path.insert(0, str(REPO_PATH))
        from autonomous.agent_loop import AutonomousAgentLoop
        from core.orchestrator import ZenOrchestrator

        orch = ZenOrchestrator()
        loop = AutonomousAgentLoop(orchestrator=orch)
        log_test("AgentLoop init", True)

        # Test state machine
        assert loop.state in ["IDLE", "PLANNING", "EXECUTING"]
        log_test("State machine", True, f"state={loop.state}")

    except Exception as e:
        log_test("Autonomous init", False, str(e)[:30])

    # Run actual autonomous scan
    try:
        result = subprocess.run(
            [sys.executable, "autonomous_demo_final.py", "127.0.0.1"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=REPO_PATH,
        )
        success = "AUTONOMER SCAN ABGESCHLOSSEN" in result.stdout
        log_test("Autonomous Scan", success)
    except Exception as e:
        log_test("Autonomous Scan", False, str(e)[:30])


def test_api_endpoints():
    """Test 4: Alle API Endpunkte"""
    print("\n[TEST 4] API Endpunkte")
    print("-" * 70)

    import requests

    base_url = "http://localhost:8000"

    # Health checks
    endpoints = [
        ("GET", "/health", "Health Check"),
        ("GET", "/api/v1/health", "API Health"),
        ("GET", "/api/v1/health/ready", "Readiness"),
        ("GET", "/api/v1/siem/supported", "SIEM List"),
        ("GET", "/api/v1/siem/connections", "SIEM Connections"),
        ("GET", "/api/v1/scans", "List Scans"),
        ("GET", "/api/v1/findings", "List Findings"),
        ("GET", "/api/v1/findings/stats", "Finding Stats"),
    ]

    for method, endpoint, name in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            if method == "GET":
                r = requests.get(url, timeout=5)
            else:
                r = requests.post(url, json={}, timeout=5)

            status_ok = r.status_code in [200, 401, 422]  # Auth errors are OK for structure
            log_test(f"API: {name}", status_ok, f"HTTP {r.status_code}")
        except Exception:
            log_test(f"API: {name}", False, "not reachable")

    # Test Auth
    try:
        r = requests.post(f"{base_url}/auth/login", json={"username": "admin", "password": "admin"}, timeout=5)
        has_token = "access_token" in r.json() if r.status_code == 200 else False
        log_test("API: Auth/Login", has_token)
    except Exception:
        log_test("API: Auth/Login", False)


def test_siem_integration():
    """Test 5: SIEM Integration komplett"""
    print("\n[TEST 5] SIEM Integration")
    print("-" * 70)

    import requests

    base_url = "http://localhost:8000/api/v1"

    # 1. Connect Mock SIEM
    try:
        r = requests.post(
            f"{base_url}/siem/connect",
            json={"name": "Test SIEM", "type": "mock", "url": "mock://test", "api_key": "test", "is_mock": True},
            timeout=5,
        )
        log_test("SIEM Connect", r.status_code == 200)
    except Exception:
        log_test("SIEM Connect", False)

    # 2. Send Events
    events_sent = 0
    for severity in ["critical", "high", "medium", "low", "info"]:
        try:
            r = requests.post(
                f"{base_url}/siem/events",
                json={
                    "severity": severity,
                    "event_type": "test_event",
                    "source": "comprehensive_test",
                    "target": "localhost",
                    "description": f"Test event {severity}",
                },
                timeout=5,
            )
            if r.status_code == 200:
                events_sent += 1
        except Exception:
            pass

    log_test("SIEM Send Events", events_sent >= 3, f"{events_sent}/5 sent")

    # 3. Retrieve Events
    try:
        r = requests.get(f"{base_url}/siem/events", timeout=5)
        event_count = r.json().get("total", 0) if r.status_code == 200 else 0
        log_test("SIEM Get Events", event_count > 0, f"{event_count} events")
    except Exception:
        log_test("SIEM Get Events", False)


def test_report_generation():
    """Test 6: Report-Generierung"""
    print("\n[TEST 6] Report-Generierung")
    print("-" * 70)

    sys.path.insert(0, str(REPO_PATH))

    try:
        from modules.report_export import ReportExporter
        from modules.report_gen import ReportGenerator

        # Test ReportGenerator
        gen = ReportGenerator()
        log_test("ReportGenerator init", True)

        # Test ReportExporter
        _ = ReportExporter()
        log_test("ReportExporter init", True)

        # Test async methods exist
        assert hasattr(gen, "generate_executive_summary")
        assert hasattr(gen, "generate_technical_report")
        assert hasattr(gen, "export_json")
        log_test("Report methods", True)

    except Exception as exc:
        log_test("Report generation", False, str(exc)[:30])

    # Check generated reports
    try:
        logs_dir = REPO_PATH / "logs"
        json_files = list(logs_dir.glob("*.json"))
        md_files = list(logs_dir.glob("*.md"))

        total_reports = len(json_files) + len(md_files)
        log_test("Generated Reports", total_reports > 0, f"{len(json_files)} JSON, {len(md_files)} MD")
    except Exception:
        log_test("Generated Reports", False)


def test_cli_tools():
    """Test 7: CLI Tools"""
    print("\n[TEST 7] CLI Tools")
    print("-" * 70)

    tools = [
        ("real_scan.py", ["127.0.0.1"], 60),
        ("autonomous_demo_final.py", ["scanme.nmap.org"], 30),
        ("test_mock_siem.py", [], 10),
    ]

    for script, args, timeout in tools:
        try:
            cmd = [sys.executable, script] + args
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=REPO_PATH)
            success = result.returncode == 0 or "ABGESCHLOSSEN" in result.stdout
            log_test(f"CLI: {script}", success)
        except Exception as e:
            log_test(f"CLI: {script}", False, str(e)[:20])


def test_backend_functionality():
    """Test 8: LLM Backends"""
    print("\n[TEST 8] LLM Backends")
    print("-" * 70)

    sys.path.insert(0, str(REPO_PATH))

    try:
        from backends.duckduckgo import DuckDuckGoBackend
        from core.orchestrator import ZenOrchestrator

        orch = ZenOrchestrator()
        log_test("Orchestrator init", True)

        ddg = DuckDuckGoBackend()
        orch.add_backend(ddg)
        log_test("DuckDuckGo Backend", True)

        backend_count = len(orch.backends)
        log_test("Backend registration", backend_count > 0, f"{backend_count} backends")

        caps = orch.get_capabilities()
        log_test("Capabilities check", len(caps) > 0, f"{len(caps)} caps")

    except Exception as e:
        log_test("Backend functionality", False, str(e)[:30])


def test_configuration():
    """Test 9: Konfiguration"""
    print("\n[TEST 9] Konfiguration")
    print("-" * 70)

    # Check config.json
    config_path = REPO_PATH / "config.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
            log_test("Config file", True, "valid JSON")

            # Check required sections
            has_backends = "backends" in config
            has_stealth = "stealth" in config
            log_test("Config: backends", has_backends)
            log_test("Config: stealth", has_stealth)

        except json.JSONDecodeError:
            log_test("Config file", False, "invalid JSON")
    else:
        log_test("Config file", False, "not found")


def test_dependencies():
    """Test 10: Abhängigkeiten"""
    print("\n[TEST 10] Abhängigkeiten")
    print("-" * 70)

    required_packages = ["fastapi", "uvicorn", "requests", "pydantic", "python-multipart", "jinja2", "aiofiles"]

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            log_test(f"Package: {package}", True)
        except ImportError:
            log_test(f"Package: {package}", False, "not installed")


def main():
    """Haupttest-Funktion"""
    print("=" * 70)
    print("ZEN AI PENTEST - KOMPREHENSIVER REPO-TEST")
    print("Testet das gesamte Repository auf Funktionsfähigkeit")
    print("=" * 70)
    print(f"Repository: {REPO_PATH}")
    print(f"Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Alle Tests ausführen
    test_file_structure()
    test_python_modules()
    test_autonomous_functionality()
    test_api_endpoints()
    test_siem_integration()
    test_report_generation()
    test_cli_tools()
    test_backend_functionality()
    test_configuration()
    test_dependencies()

    # Zusammenfassung
    print("\n" + "=" * 70)
    print("GESAMT-ERGEBNIS")
    print("=" * 70)

    total = len(TEST_RESULTS)
    passed = sum(1 for r in TEST_RESULTS.values() if r["status"])
    failed = total - passed

    print(f"\nGesamt: {total} Tests")
    print(f"Erfolgreich: {passed}")
    print(f"Fehlgeschlagen: {failed}")
    print(f"Erfolgsrate: {passed / total * 100:.1f}%")

    # Detaillierte Fehler
    if failed > 0:
        print("\nFehlgeschlagene Tests:")
        for name, result in TEST_RESULTS.items():
            if not result["status"]:
                print(f"  - {name}: {result.get('details', 'FAIL')}")

    print("\n" + "=" * 70)
    if passed == total:
        print("*** ALLE TESTS BESTANDEN! Repo ist voll funktionsfaehig! ***")
    elif passed >= total * 0.8:
        print("*** MEISTE TESTS BESTANDEN - System einsatzbereit ***")
    else:
        print("*** WARNUNG: Einige Tests fehlgeschlagen ***")
    print("=" * 70)

    # Speichern
    report = {
        "timestamp": datetime.now().isoformat(),
        "repository": str(REPO_PATH),
        "summary": {"total": total, "passed": passed, "failed": failed, "success_rate": round(passed / total * 100, 1)},
        "results": TEST_RESULTS,
    }

    logs_dir = REPO_PATH / "logs"
    logs_dir.mkdir(exist_ok=True)

    with open(logs_dir / "comprehensive_test_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("\nReport gespeichert: logs/comprehensive_test_report.json")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
