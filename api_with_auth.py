#!/usr/bin/env python3
"""API mit Authentifizierung nutzen"""

import os

import requests

BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_USER = os.environ.get("API_USERNAME", "admin")
API_PASS = os.environ.get("API_PASSWORD", "")

if not API_PASS:
    print("WARNING: Using default password. Set API_PASSWORD env var for production.")
    API_PASS = "admin"

# 1. LOGIN - Token holen
print("=" * 50)
print("1. LOGIN")
print("=" * 50)

login_resp = requests.post(f"{BASE}/auth/login", json={"username": API_USER, "password": API_PASS}, timeout=30)

token = login_resp.json()["access_token"]
print("Token erhalten!")
print(f"Token (gekürzt): {token[:50]}...")

# Header mit Auth
headers = {"Authorization": f"Bearer {token}"}

# 2. User Info
print("\n" + "=" * 50)
print("2. USER INFO")
print("=" * 50)

me_resp = requests.get(f"{BASE}/auth/me", headers=headers, timeout=30)
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
    timeout=30,
)
print(f"Status: {scan_resp.status_code}")
print(f"Response: {scan_resp.json()}")

print("\n" + "=" * 50)
print("AUTHENTIFIZIERUNG ERFOLGREICH!")
print("=" * 50)
