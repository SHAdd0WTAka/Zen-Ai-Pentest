#!/usr/bin/env python3
"""Komplette Demo aller Funktionen"""
import requests

BASE = 'http://localhost:8000/api/v1'

print("=" * 60)
print("MOCK-SIEM DEMO")
print("=" * 60)

# 1. Verbindungen zeigen
r = requests.get(f'{BASE}/siem/connections')
conns = r.json()
print(f"\n[1] Aktive SIEM-Verbindungen: {conns['count']}")
for c in conns['connections'][:3]:
    print(f"    - {c['name']} ({c['type']}): {c['status']}")

# 2. Security Events senden
print("\n[2] Sende Security Events...")
events = [
    {'severity': 'critical', 'event_type': 'sql_injection', 'source': '192.168.1.100', 'target': 'webapp.com', 'description': 'SQL Injection detected'},
    {'severity': 'high', 'event_type': 'xss', 'source': '10.0.0.50', 'target': 'api.com', 'description': 'XSS in search'},
    {'severity': 'medium', 'event_type': 'brute_force', 'source': '172.16.0.25', 'target': 'ssh.com', 'description': 'SSH brute force'},
]
for e in events:
    r = requests.post(f'{BASE}/siem/events', json=e)
    print(f"    {e['severity'].upper():<8} {e['event_type']:<15} -> {r.json()['message']}")

# 3. Events anzeigen
r = requests.get(f'{BASE}/siem/events')
data = r.json()
print(f"\n[3] Gespeicherte Events: {data['total']}")
print(f"\n{'Time':<20} {'Severity':<10} {'Type':<15} {'Description'}")
print("-" * 70)
for e in data['events']:
    ts = e.get('timestamp', 'N/A')[:19]
    print(f"{ts:<20} {e['severity']:<10} {e['event_type']:<15} {e['description'][:30]}")

print("\n" + "=" * 60)
print("MOCK-SIEM DEMO ABGESCHLOSSEN")
print("=" * 60)
