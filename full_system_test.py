#!/usr/bin/env python3
"""
ZEN AI PENTEST - KOMPLETTE SYSTEM-TEST
Testet alle Komponenten auf dem Rechner
"""

import subprocess
import sys
import os
import json

from datetime import datetime

print("=" * 70)
print("ZEN AI PENTEST - VOLLSTÄNDIGER SYSTEM-TEST")
print("=" * 70)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

test_results = {}

# Test 1: Module Import Test
print("\n[TEST 1] Module Importe")
print("-" * 70)
try:
    from modules.report_gen import ReportGenerator  # noqa: F401
    from modules.recon import ReconModule  # noqa: F401
    from modules.vuln_scanner import VulnScannerModule  # noqa: F401
    from modules.exploit_assist import ExploitAssistModule  # noqa: F401
    from modules.report_export import ReportExporter  # noqa: F401
    from autonomous.agent_loop import AutonomousAgentLoop  # noqa: F401

    print("  [OK] Alle Module erfolgreich importiert")
    test_results["module_imports"] = "PASS"
except Exception as e:
    print(f"  [FAIL] Fehler: {e}")
    test_results["module_imports"] = "FAIL"

# Test 2: Autonomer Scan (Demo)
print("\n[TEST 2] Autonomer Scan")
print("-" * 70)
try:
    result = subprocess.run(
        [sys.executable, "autonomous_demo_final.py", "192.168.1.1"], capture_output=True, text=True, timeout=30
    )
    if "AUTONOMER SCAN ABGESCHLOSSEN" in result.stdout:
        print("  [OK] Autonomer Scan erfolgreich")
        test_results["autonomous_scan"] = "PASS"
    else:
        print("  [FAIL] Autonomer Scan fehlgeschlagen")
        test_results["autonomous_scan"] = "FAIL"
except Exception as e:
    print(f"  [FAIL] Fehler: {e}")
    test_results["autonomous_scan"] = "FAIL"

# Test 3: API Health Check
print("\n[TEST 3] API Server")
print("-" * 70)
try:
    import requests

    r = requests.get("http://localhost:8000/health", timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"  [OK] API läuft (Version: {data.get('version', 'unknown')})")
        test_results["api_health"] = "PASS"
    else:
        print("  [FAIL] API nicht erreichbar")
        test_results["api_health"] = "FAIL"
except Exception as e:
    print(f"  ✗ API nicht erreichbar: {e}")
    test_results["api_health"] = "FAIL"

# Test 4: SIEM Funktionalität
print("\n[TEST 4] Mock-SIEM")
print("-" * 70)
try:
    import requests

    # Event senden
    r = requests.post(
        "http://localhost:8000/api/v1/siem/events",
        json={
            "severity": "info",
            "event_type": "system_test",
            "source": "test_suite",
            "target": "localhost",
            "description": "Full system test",
        },
        timeout=5,
    )
    if r.status_code == 200:
        # Events abrufen
        r2 = requests.get("http://localhost:8000/api/v1/siem/events", timeout=5)
        events = r2.json()
        print(f"  [OK] SIEM funktioniert ({events.get('total', 0)} Events gespeichert)")
        test_results["siem"] = "PASS"
    else:
        print("  [FAIL] SIEM Fehler")
        test_results["siem"] = "FAIL"
except Exception as e:
    print(f"  ✗ SIEM nicht erreichbar: {e}")
    test_results["siem"] = "FAIL"

# Test 5: Authentifizierung
print("\n[TEST 5] API Auth")
print("-" * 70)
try:
    import requests

    r = requests.post("http://localhost:8000/auth/login", json={"username": "admin", "password": "admin"}, timeout=5)
    if r.status_code == 200 and "access_token" in r.json():
        print("  [OK] Login funktioniert")
        test_results["auth"] = "PASS"
    else:
        print("  [FAIL] Login fehlgeschlagen")
        test_results["auth"] = "FAIL"
except Exception as e:
    print(f"  ✗ Auth Fehler: {e}")
    test_results["auth"] = "FAIL"

# Test 6: Reports generieren
print("\n[TEST 6] Report-Generierung")
print("-" * 70)
try:
    # Prüfe ob Reports existieren
    import os

    log_files = os.listdir("logs")
    json_reports = [f for f in log_files if f.endswith(".json")]
    md_reports = [f for f in log_files if f.endswith(".md")]

    if len(json_reports) > 0 and len(md_reports) > 0:
        print(f"  [OK] Reports vorhanden ({len(json_reports)} JSON, {len(md_reports)} MD)")
        test_results["reports"] = "PASS"
    else:
        print("  [FAIL] Keine Reports gefunden")
        test_results["reports"] = "FAIL"
except Exception as e:
    print(f"  ✗ Report-Fehler: {e}")
    test_results["reports"] = "FAIL"

# Test 7: Echter Port-Scan
print("\n[TEST 7] Echter Port-Scan")
print("-" * 70)
try:
    result = subprocess.run([sys.executable, "real_scan.py", "127.0.0.1"], capture_output=True, text=True, timeout=60)
    if "SCAN ABGESCHLOSSEN" in result.stdout:
        print("  [OK] Port-Scan erfolgreich")
        test_results["port_scan"] = "PASS"
    else:
        print("  [FAIL] Port-Scan fehlgeschlagen")
        test_results["port_scan"] = "FAIL"
except Exception as e:
    print(f"  ✗ Port-Scan Fehler: {e}")
    test_results["port_scan"] = "FAIL"

# Zusammenfassung
print("\n" + "=" * 70)
print("TEST-ZUSAMMENFASSUNG")
print("=" * 70)

passed = sum(1 for v in test_results.values() if v == "PASS")
total = len(test_results)

for test, status in test_results.items():
    symbol = "[OK]" if status == "PASS" else "[FAIL]"
    color = "PASS" if status == "PASS" else "FAIL"
    print(f"  {symbol} {test:<25} {status}")

print("-" * 70)
print(f"Ergebnis: {passed}/{total} Tests bestanden")

if passed == total:
    print("\n*** ALLE TESTS BESTANDEN! System ist voll funktionsfaehig! ***")
elif passed >= total * 0.7:
    print("\n*** Meiste Tests bestanden. Kleine Probleme vorhanden. ***")
else:
    print("\n*** Viele Tests fehlgeschlagen. System braucht Aufmerksamkeit. ***")

print("=" * 70)

# Save test report
report = {
    "timestamp": datetime.now().isoformat(),
    "results": test_results,
    "summary": {"passed": passed, "total": total, "percentage": round(passed / total * 100, 1)},
}

with open("logs/system_test_report.json", "w") as f:
    json.dump(report, f, indent=2)

print("\nReport gespeichert: logs/system_test_report.json")
