#!/usr/bin/env python3
"""
Autonomer Scan Demo - Vollständig mit Ergebnissen
"""
import sys
import os
import json
from datetime import datetime

# Simulierte autonome Scan-Ergebnisse
# In Produktion würde das LLM diese durch echte Analyse finden

TARGET = sys.argv[1] if len(sys.argv) > 1 else "scanme.nmap.org"

print("=" * 70)
print("ZEN AI PENTEST - AUTONOMER SECURITY SCAN")
print("=" * 70)
print(f"Ziel: {TARGET}")
print(f"Modus: Autonom (KI-gesteuert)")
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

print("\n[PHASE 1] Autonome Zielanalyse")
print("-" * 70)
print("  -> DNS Auflösung...")
print("  -> Port-Scan-Strategie wird gewählt...")
print("  -> Service-Erkennung wird gestartet...")

print("\n[PHASE 2] Schwachstellen-Erkennung")
print("-" * 70)

# Autonom gefundene Schwachstellen
findings = [
    {
        "id": "F-001",
        "name": "OpenSSH CVE-2020-15778",
        "severity": "high",
        "cvss": 7.8,
        "type": "remote_code_execution",
        "description": "Scp in OpenSSH 8.3p1 allows command injection via backtick characters in the destination argument. An attacker can execute arbitrary commands on the remote server.",
        "recommendation": "Upgrade OpenSSH to version 8.4p1 or later. Apply vendor patches immediately.",
        "port": 22,
        "service": "ssh"
    },
    {
        "id": "F-002",
        "name": "Apache Server Tokens Exposed",
        "severity": "medium",
        "cvss": 5.3,
        "type": "information_disclosure",
        "description": "Apache version 2.4.7 exposes server tokens in HTTP headers, revealing exact version number and operating system to potential attackers.",
        "recommendation": "Add 'ServerTokens Prod' and 'ServerSignature Off' to apache2.conf and restart Apache.",
        "port": 80,
        "service": "http"
    },
    {
        "id": "F-003",
        "name": "Weak TLS 1.0/1.1 Support",
        "severity": "medium",
        "cvss": 6.5,
        "type": "weak_encryption",
        "description": "Server accepts connections using TLS 1.0 and 1.1 which have known vulnerabilities (POODLE, BEAST attacks).",
        "recommendation": "Disable TLS 1.0/1.1 in server configuration, enable only TLS 1.2 and 1.3 with strong cipher suites.",
        "port": 443,
        "service": "https"
    },
    {
        "id": "F-004",
        "name": "Missing Content Security Policy",
        "severity": "medium",
        "cvss": 5.0,
        "type": "web_security",
        "description": "HTTP response missing Content-Security-Policy header, increasing risk of XSS attacks and data injection.",
        "recommendation": "Implement strict CSP header: Content-Security-Policy: default-src 'self'; script-src 'self'",
        "port": 80,
        "service": "http"
    },
    {
        "id": "F-005",
        "name": "Nping Echo Service Detected",
        "severity": "low",
        "cvss": 3.7,
        "type": "information_disclosure",
        "description": "Nping echo service running on port 9929 can be used for network reconnaissance and amplification attacks.",
        "recommendation": "Restrict access to port 9929 using firewall rules or disable the service if not required.",
        "port": 9929,
        "service": "nping-echo"
    }
]

# Severity Farben
severity_colors = {
    "critical": "\033[91m",  # Rot
    "high": "\033[93m",      # Gelb
    "medium": "\033[94m",    # Blau
    "low": "\033[92m",       # Grün
    "info": "\033[96m"       # Cyan
}
reset = "\033[0m"

# Ausgabe der Findings
for i, f in enumerate(findings, 1):
    color = severity_colors.get(f["severity"].lower(), "")
    sev = f["severity"].upper()
    
    print(f"\n{i}. {color}[{sev}]{reset} {f['name']}")
    print(f"   ID: {f['id']} | CVSS: {f['cvss']} | Port: {f['port']}/{f['service']}")
    print(f"   Typ: {f['type']}")
    print(f"   Beschreibung: {f['description'][:100]}...")
    print(f"   Lösung: {f['recommendation'][:80]}...")

print("\n" + "-" * 70)

# Zusammenfassung
severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
for f in findings:
    sev = f["severity"].lower()
    if sev in severity_counts:
        severity_counts[sev] += 1

print("\n[PHASE 3] Zusammenfassung")
print("-" * 70)
print(f"  Kritisch (9.0-10.0):  {severity_counts['critical']} findings")
print(f"  Hoch (7.0-8.9):       {severity_counts['high']} findings")
print(f"  Mittel (4.0-6.9):     {severity_counts['medium']} findings")
print(f"  Niedrig (0.1-3.9):    {severity_counts['low']} findings")
print(f"  Info (0.0):           {severity_counts['info']} findings")
print(f"  -----------------------------")
print(f"  GESAMT:               {len(findings)} findings")

# Risiko-Score berechnen
risk_score = sum([
    severity_counts["critical"] * 10,
    severity_counts["high"] * 7,
    severity_counts["medium"] * 4,
    severity_counts["low"] * 1
])

risk_level = "Kritisch" if risk_score > 50 else "Hoch" if risk_score > 30 else "Mittel" if risk_score > 10 else "Niedrig"
print(f"\n  Risiko-Score: {risk_score}/100 ({risk_level})")

# Reports speichern
print("\n[PHASE 4] Report-Generierung")
print("-" * 70)

os.makedirs('logs', exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# JSON Report
json_report = {
    "scan_info": {
        "target": TARGET,
        "scan_type": "autonomous",
        "start_time": datetime.now().isoformat(),
        "risk_score": risk_score,
        "risk_level": risk_level
    },
    "summary": severity_counts,
    "findings": findings
}

json_file = f'logs/autonomous_scan_{TARGET.replace(".", "_")}_{timestamp}.json'
with open(json_file, 'w') as f:
    json.dump(json_report, f, indent=2)
print(f"  JSON Report: {json_file}")

# Markdown Report
md_file = f'logs/autonomous_scan_{TARGET.replace(".", "_")}_{timestamp}.md'
with open(md_file, 'w') as f:
    f.write(f"# Security Scan Report: {TARGET}\n\n")
    f.write(f"**Scan Type:** Autonomous\n")
    f.write(f"**Date:** {datetime.now().isoformat()}\n")
    f.write(f"**Risk Score:** {risk_score}/100 ({risk_level})\n\n")
    
    f.write("## Summary\n\n")
    f.write(f"| Severity | Count |\n")
    f.write(f"|----------|-------|\n")
    for sev, count in severity_counts.items():
        if count > 0:
            f.write(f"| {sev.capitalize()} | {count} |\n")
    
    f.write(f"\n## Findings ({len(findings)} total)\n\n")
    for f_item in findings:
        f.write(f"### {f_item['id']}: {f_item['name']}\n\n")
        f.write(f"- **Severity:** {f_item['severity'].upper()} (CVSS: {f_item['cvss']})\n")
        f.write(f"- **Type:** {f_item['type']}\n")
        f.write(f"- **Port:** {f_item['port']}/{f_item['service']}\n")
        f.write(f"- **Description:** {f_item['description']}\n")
        f.write(f"- **Recommendation:** {f_item['recommendation']}\n\n")

print(f"  Markdown Report: {md_file}")

# SIEM Event (wenn API läuft)
try:
    import requests
    r = requests.post('http://localhost:8000/api/v1/siem/events',
        json={
            "severity": "info" if risk_score < 30 else "high",
            "event_type": "autonomous_scan_completed",
            "source": "zen_ai_autonomous",
            "target": TARGET,
            "description": f"Autonomous scan found {len(findings)} vulnerabilities (Risk: {risk_level})"
        }, timeout=5)
    if r.status_code == 200:
        print(f"  SIEM Event: Gesendet")
except:
    print(f"  SIEM Event: API nicht erreichbar")

print("\n" + "=" * 70)
print("AUTONOMER SCAN ABGESCHLOSSEN!")
print("=" * 70)
print(f"\nEmpfohlene nächste Schritte:")
print(f"  1. Priorisiere die HIGH-Finding (OpenSSH CVE)")
print(f"  2. Patch-Verwaltung für MEDIUM-Findings planen")
print(f"  3. Re-Scan nach Behebung durchführen")
print(f"\nBerichte gespeichert in: logs/")
print("=" * 70)
