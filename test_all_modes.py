#!/usr/bin/env python3
"""
Testet ALLE 3 Modi auf einmal
"""

import subprocess
import sys


def test_standalone():
    """Test 1: Standalone Mode (kein API nötig)"""
    print("\n" + "=" * 60)
    print("TEST 1: STANDALONE MODE (ohne API)")
    print("=" * 60)

    result = subprocess.run(
        [
            sys.executable,
            "standalone_scan.py",
            "--target",
            "localhost",
            "--scan-type",
            "quick",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if "completed" in result.stdout or "completed" in result.stderr:
        print("[OK] Standalone: Reports erstellt")
        return True
    else:
        print("[FAIL] Standalone: FEHLER")
        return False


def test_localhost_api():
    """Test 2: Localhost API"""
    print("\n" + "=" * 60)
    print("TEST 2: LOCALHOST API (Port 8000)")
    print("=" * 60)

    try:
        import requests

        r = requests.get("http://localhost:8000/health", timeout=5)
        if r.status_code == 200:
            print(f"[OK] API läuft: {r.json()['status']}")
            print(f"   Version: {r.json()['version']}")

            # SIEM Test
            r = requests.post(
                "http://localhost:8000/api/v1/siem/events",
                json={
                    "severity": "info",
                    "event_type": "test",
                    "source": "localhost",
                    "target": "test",
                    "description": "Localhost test event",
                },
                timeout=5,
            )
            print(f"[OK] SIEM Event: {r.json()['message']}")
            return True
    except Exception as e:
        print(f"[FAIL] API nicht erreichbar: {e}")
        print("   Starte zuerst: python -m api.main")
        return False


def main():
    print("=" * 60)
    print("ZEN AI PENTEST - KOMPLETT TEST")
    print("=" * 60)

    results = []

    # Test 1: Standalone
    results.append(("Standalone", test_standalone()))

    # Test 2: Localhost API
    results.append(("Localhost API", test_localhost_api()))

    # Summary
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)

    for name, ok in results:
        status = "[OK]" if ok else "[FAIL]"
        print(f"{name:<20} {status}")

    all_ok = all(r[1] for r in results)

    print("\n" + "=" * 60)
    if all_ok:
        print("ALLE TESTS ERFOLGREICH!")
        print("\nDu hast 2 Möglichkeiten:")
        print("   1. Standalone: python standalone_scan.py --target <host>")
        print("   2. Mit API:    http://localhost:8000/docs")
    else:
        print("EINIGE TESTS FEHLGESCHLAGEN")
    print("=" * 60)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
