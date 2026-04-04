#!/usr/bin/env python3
import requests

r = requests.get("http://localhost:8000/api/v1/siem/events")
d = r.json()

print("SIEM Events gesamt:", d["total"])
print("\nLetzte 3 Events:")
for e in d["events"][-3:]:
    print(f"  [{e['severity'].upper()}] {e['event_type']}: {e['description'][:50]}...")
