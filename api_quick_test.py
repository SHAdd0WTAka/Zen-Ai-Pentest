#!/usr/bin/env python3
"""Schnell-Test der API Funktionen"""
import requests

BASE = 'http://localhost:8000/api/v1'

print("=" * 50)
print("API QUICK TEST")
print("=" * 50)

# 1. Health Check
print("\n[1] Health Check...")
r = requests.get(f"{BASE}/health")
data = r.json()
print(f"    Status: {data['status']}")
print(f"    Version: {data['version']}")

# 2. Stats
print("\n[2] Stats Overview...")
try:
    r = requests.get(f"{BASE}/stats/overview")
    print(f"    Stats: {r.json()}")
except:
    print("    Stats nicht verfügbar")

# 3. SIEM Events
print("\n[3] SIEM Events senden...")
r = requests.post(f"{BASE}/siem/events", json={
    "severity": "info",
    "event_type": "swagger_test",
    "source": "browser",
    "target": "localhost",
    "description": "User testing API via Swagger UI"
})
print(f"    Result: {r.json()['message']}")

# 4. Supported SIEMs
print("\n[4] Unterstützte SIEMs...")
r = requests.get(f"{BASE}/siem/supported")
data = r.json()
if 'siems' in data:
    for s in data['siems'][:3]:
        print(f"    - {s.get('name', 'Unknown')}")

print("\n" + "=" * 50)
print("API FUNKTIONIERT!")
print("=" * 50)
print("\nNächste Schritte:")
print("1. Öffne http://localhost:8000/docs im Browser")
print("2. Klicke auf 'Try it out' bei POST /scans")
print("3. Führe einen echten Scan durch!")
