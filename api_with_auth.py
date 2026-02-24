#!/usr/bin/env python3
"""API mit Authentifizierung nutzen"""

import requests

BASE = "http://localhost:8000"

# 1. LOGIN - Token holen
print("=" * 50)
print("1. LOGIN")
print("=" * 50)

login_resp = requests.post(
    f"{BASE}/auth/login", json={"username": "admin", "password": "admin"}
)

token = login_resp.json()["access_token"]
print("Token erhalten!")
print(f"Token (gekürzt): {token[:50]}...")

# Header mit Auth
headers = {"Authorization": f"Bearer {token}"}

# 2. User Info
print("\n" + "=" * 50)
print("2. USER INFO")
print("=" * 50)

me_resp = requests.get(f"{BASE}/auth/me", headers=headers)
print(f"User: {me_resp.json()}")

# 3. Geschützte Endpunkte nutzen
print("\n" + "=" * 50)
print("3. SCAN ERSTELLEN (mit Auth)")
print("=" * 50)

scan_resp = requests.post(
    f"{BASE}/api/v1/scans",
    headers=headers,
    json={
        "target": "scanme.nmap.org",
        "scan_type": "network",
        "modules": ["recon", "vuln_scan"],
    },
)
print(f"Status: {scan_resp.status_code}")
print(f"Response: {scan_resp.json()}")

print("\n" + "=" * 50)
print("AUTHENTIFIZIERUNG ERFOLGREICH!")
print("=" * 50)
