#!/usr/bin/env python3
"""Live Scan Demo - Mit Auth"""

import time

import requests

BASE = "http://localhost:8000"

# Login
login = requests.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin"})
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("LIVE SCAN DEMO")
print("=" * 60)

# 1. Scan starten
print("\n[1] Starte Scan auf scanme.nmap.org...")
scan = requests.post(
    f"{BASE}/api/v1/scans", headers=headers, json={"target": "scanme.nmap.org", "scan_type": "network", "modules": ["recon"]}
).json()

scan_id = scan["id"]
print(f"    Scan ID: {scan_id}")
print(f"    Status: {scan['status']}")

# 2. Status beobachten
print("\n[2] Warte auf Scan...")
for i in range(10):
    time.sleep(1)
    status = requests.get(f"{BASE}/api/v1/scans/{scan_id}", headers=headers).json()
    print(f"    Status: {status['status']} | Progress: {status.get('progress', 0)}%")
    if status["status"] in ["completed", "failed"]:
        break

# 3. Ergebnisse holen
print("\n[3] Hole Ergebnisse...")
results = requests.get(f"{BASE}/api/v1/scans/{scan_id}/results", headers=headers).json()
print(f"    Findings: {len(results.get('findings', []))}")

# 4. Alle Scans anzeigen
print("\n[4] Alle Scans:")
scans = requests.get(f"{BASE}/api/v1/scans", headers=headers).json()
for s in scans[-3:]:
    print(f"    - {s['target']}: {s['status']} ({s.get('findings_count', 0)} findings)")

print("\n" + "=" * 60)
print("SCAN DEMO ABGESCHLOSSEN!")
print("=" * 60)
