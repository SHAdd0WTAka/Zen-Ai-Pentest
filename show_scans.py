#!/usr/bin/env python3
import requests

BASE = "http://localhost:8000"

# Login
login = requests.post(
    f"{BASE}/auth/login", json={"username": "admin", "password": "admin"}
)
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Alle Scans
scans = requests.get(f"{BASE}/api/v1/scans", headers=headers).json()

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
