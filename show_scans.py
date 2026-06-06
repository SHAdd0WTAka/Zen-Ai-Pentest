#!/usr/bin/env python3
import os

import requests

BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_USER = os.environ.get("API_USERNAME", "admin")
API_PASS = os.environ.get("API_PASSWORD", "")

if not API_PASS:
    print("WARNING: Using default password. Set API_PASSWORD env var for production.")
    API_PASS = "admin"

login = requests.post(f"{BASE}/auth/login", json={"username": API_USER, "password": API_PASS}, timeout=30)
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Alle Scans
scans = requests.get(f"{BASE}/api/v1/scans", headers=headers, timeout=30).json()

print("=" * 60)
print("DEINE SCANS")
print("=" * 60)

for s in scans[-5:]:
    print(f"\nID: {s['id']}")
    print(f"Target: {s['target']}")
    print(f"Type: {s['scan_type']}")
    print(f"Status: {s['status']}")
    print(f"Progress: {s.get('progress', 0)}%")
    print(f"Findings: {s.get('findings_count', 0)}")
    print(f"Erstellt: {s['created_at'][:19]}")
    print("-" * 60)
