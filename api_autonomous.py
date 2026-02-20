#!/usr/bin/env python3
"""Autonomer Scan uber API"""

import time

import requests

BASE = "http://localhost:8000"

# Login
login = requests.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin"})
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("AUTONOMER SCAN UBER API")
print("=" * 60)

# Scan erstellen (autonom)
r = requests.post(
    f"{BASE}/api/v1/scans",
    headers=headers,
    json={"target": "scanme.nmap.org", "scan_type": "full", "modules": ["recon", "vuln_scan"]},
)

scan = r.json()
print("\nScan erstellt:")
print(f"  ID: {scan['id']}")
print(f"  Status: {scan['status']}")
print(f"  Target: {scan['target']}")
print(f"  Type: {scan['scan_type']}")

# Auf Ergebnisse warten
print("\nWarte auf Scan...")
for i in range(5):
    time.sleep(1)
    status = requests.get(f"{BASE}/api/v1/scans/{scan['id']}", headers=headers).json()
    print(f"  Status: {status['status']} | Progress: {status.get('progress', 0)}%")
    if status["status"] in ["completed", "failed"]:
        break

# Ergebnisse holen
results = requests.get(f"{BASE}/api/v1/scans/{scan['id']}/results", headers=headers).json()
print("\nErgebnisse:")
print(f"  Findings: {len(results.get('findings', []))}")

print("\n" + "=" * 60)
print("AUTONOMER SCAN COMPLETE")
print("=" * 60)
