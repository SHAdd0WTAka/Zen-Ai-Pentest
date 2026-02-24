#!/usr/bin/env python3
"""Test Mock SIEM functionality"""

import requests

BASE = "http://localhost:8000/api/v1"

print("=" * 60)
print("MOCK SIEM TEST")
print("=" * 60)

# 1. Verbindungen checken
r = requests.get(f"{BASE}/siem/connections")
connections = r.json()
print(f"\n[1] Aktive Verbindungen: {connections['count']}")
for c in connections["connections"]:
    print(f"    - {c['name']} ({c['type']}): {c['status']}")

# 2. Test-Events senden
print("\n[2] Sende Test-Events...")
test_events = [
    {
        "severity": "critical",
        "event_type": "sql_injection",
        "source": "192.168.1.100",
        "target": "webapp.example.com",
        "description": "SQL Injection in login form",
    },
    {
        "severity": "high",
        "event_type": "xss",
        "source": "10.0.0.50",
        "target": "api.example.com",
        "description": "Reflected XSS in search",
    },
    {
        "severity": "medium",
        "event_type": "brute_force",
        "source": "172.16.0.25",
        "target": "ssh.example.com",
        "description": "Failed SSH logins",
    },
]

for event in test_events:
    r = requests.post(f"{BASE}/siem/events", json=event)
    result = r.json()
    print(
        f"    {event['severity'].upper()}: {event['event_type']} - {result['message']}"
    )

# 3. Events abrufen
r = requests.get(f"{BASE}/siem/events")
events_data = r.json()
print(f"\n[3] Gespeicherte Events: {events_data['total']}")
print("\nLetzte Events:")
print(f"{'Time':<20} {'Severity':<10} {'Type':<20} {'Description'}")
print("-" * 70)

for event in reversed(events_data["events"][-5:]):
    ts = event.get("timestamp", "N/A")[:19] if "timestamp" in event else "N/A"
    sev = event.get("severity", "unknown")
    evt_type = event.get("event_type", "unknown")[:18]
    desc = event.get("description", "")[:30]
    print(f"{ts:<20} {sev:<10} {evt_type:<20} {desc}")

# 4. Cleanup
print("\n[4] Cleanup...")
r = requests.delete(f"{BASE}/siem/events")
print(f"    {r.json()['message']}")

print("\n" + "=" * 60)
print("MOCK SIEM TEST ERFOLGREICH!")
print("=" * 60)
