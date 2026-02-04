#!/usr/bin/env python3
import requests

BASE = 'http://localhost:8000/api/v1'

# Events abrufen
r = requests.get(f'{BASE}/siem/events')
data = r.json()

print("=" * 60)
print("MOCK SIEM - AKTUELLE EVENTS")
print("=" * 60)
print(f"\nGesamte Events: {data['total']}\n")

print(f"{'Time':<20} {'Severity':<10} {'Type':<18} {'Description'}")
print("-" * 70)

for e in reversed(data['events'][-5:]):
    ts = e.get('timestamp', 'N/A')[:16]
    sev = e.get('severity', 'unknown')
    evt = e.get('event_type', 'unknown')[:17]
    desc = e.get('description', '')[:35]
    print(f"{ts:<20} {sev:<10} {evt:<18} {desc}")

print("\n" + "=" * 60)
print("NEUESTES EVENT:")
print("=" * 60)
if data['events']:
    latest = data['events'][-1]
    print(f"Severity:   {latest['severity'].upper()}")
    print(f"Type:       {latest['event_type']}")
    print(f"Source:     {latest['source']}")
    print(f"Target:     {latest['target']}")
    print(f"Description: {latest['description']}")
    print(f"Timestamp:  {latest['timestamp']}")
