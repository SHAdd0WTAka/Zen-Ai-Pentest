#!/usr/bin/env python3
"""
ECHTER Security Scan - Auf localhost/VM
"""
import socket
import subprocess
import sys
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

print("=" * 70)
print("ZEN AI PENTEST - ECHTER SCAN")
print("=" * 70)

# Ziel wählen
target = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
print(f"Ziel: {target}")
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# DNS Lookup
try:
    hostname = socket.gethostbyaddr(target)[0]
    print(f"\n[+] Hostname: {hostname}")
except:
    print(f"\n[+] Hostname: Konnte nicht aufgelöst werden")

# Echter Port Scan
print("\n[1] Port-Scan wird durchgeführt...")
print("-" * 70)

# Häufige Ports prüfen
common_ports = {
    21: "FTP",
    22: "SSH", 
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    135: "MSRPC",
    139: "NetBIOS",
    143: "IMAP",
    443: "HTTPS",
    445: "SMB",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    8080: "HTTP-Proxy",
    8443: "HTTPS-Alt"
}

open_ports = []

def check_port(port_info):
    port, service = port_info
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((target, port))
    sock.close()
    if result == 0:
        return (port, service, "open")
    return None

print("  Scanne Ports... (das kann 10-20 Sekunden dauern)")
with ThreadPoolExecutor(max_workers=50) as executor:
    futures = [executor.submit(check_port, (port, svc)) for port, svc in common_ports.items()]
    for future in as_completed(futures):
        result = future.result()
        if result:
            open_ports.append(result)
            print(f"  [OPEN] Port {result[0]}/{result[1]}")

if not open_ports:
    print("  [!] Keine offenen Ports gefunden (Firewall aktiv?)")
else:
    print(f"\n  Gefunden: {len(open_ports)} offene Ports")

# Service Detection (einfache Version)
print("\n[2] Service-Erkennung...")
print("-" * 70)

services = []
for port, svc_name, status in open_ports:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect((target, port))
        
        # Banner grabbing für einige Services
        if port in [22, 25, 80, 110, 143]:
            try:
                banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                if banner:
                    print(f"  Port {port}: {banner[:80]}")
                    services.append({"port": port, "service": svc_name, "banner": banner})
                else:
                    services.append({"port": port, "service": svc_name, "banner": "N/A"})
            except:
                services.append({"port": port, "service": svc_name, "banner": "N/A"})
        else:
            services.append({"port": port, "service": svc_name, "banner": "N/A"})
        sock.close()
    except Exception as e:
        services.append({"port": port, "service": svc_name, "banner": f"Error: {str(e)[:30]}"})

# Schwachstellen-Analyse (basierend auf gefundenen Services)
print("\n[3] Schwachstellen-Analyse...")
print("-" * 70)

findings = []

# Analyse basierend auf offenen Ports
for svc in services:
    port = svc["port"]
    service = svc["service"]
    banner = svc.get("banner", "")
    
    # SSH Analyse
    if port == 22:
        if "OpenSSH" in banner:
            if "7." in banner or "8.2" in banner or "8.3" in banner:
                findings.append({
                    "id": f"VULN-{port}-001",
                    "port": port,
                    "service": "SSH",
                    "name": "OpenSSH CVE-2020-15778",
                    "severity": "high",
                    "cvss": 7.8,
                    "description": f"OpenSSH Version in {banner} ist verwundbar für Command Injection via scp.",
                    "recommendation": "Aktualisiere OpenSSH auf Version 8.4p1 oder neuer",
                    "evidence": banner
                })
            else:
                findings.append({
                    "id": f"INFO-{port}-001",
                    "port": port,
                    "service": "SSH",
                    "name": "SSH Service Detected",
                    "severity": "info",
                    "cvss": 0.0,
                    "description": f"SSH Service läuft auf Port {port}: {banner}",
                    "recommendation": "Stelle sicher, dass nur Key-Authentifizierung erlaubt ist",
                    "evidence": banner
                })
        else:
            findings.append({
                "id": f"INFO-{port}-001",
                "port": port,
                "service": "SSH",
                "name": "SSH Service Detected",
                "severity": "info",
                "cvss": 0.0,
                "description": f"SSH Service erkannt auf Port {port}",
                "recommendation": "Prüfe die SSH-Konfiguration (PasswordAuthentication no)",
                "evidence": "Port 22 offen"
            })
    
    # HTTP/HTTPS Analyse
    elif port in [80, 443, 8080, 8443]:
        findings.append({
            "id": f"INFO-{port}-001",
            "port": port,
            "service": service,
            "name": f"{service} Service Detected",
            "severity": "info",
            "cvss": 0.0,
            "description": f"Web-Server erkannt auf Port {port}",
            "recommendation": "Überprüfe auf veraltete Software und CSP-Header",
            "evidence": f"Port {port} antwortet"
        })
    
    # RDP
    elif port == 3389:
        findings.append({
            "id": f"WARN-{port}-001",
            "port": port,
            "service": "RDP",
            "name": "Remote Desktop Protocol Exposed",
            "severity": "medium",
            "cvss": 5.3,
            "description": "RDP ist von außen erreichbar. Angriffsvektor für Brute-Force.",
            "recommendation": "Beschränke RDP-Zugriff via Firewall oder VPN",
            "evidence": "Port 3389 offen"
        })
    
    # SMB
    elif port == 445:
        findings.append({
            "id": f"CRIT-{port}-001",
            "port": port,
            "service": "SMB",
            "name": "SMB Service Exposed",
            "severity": "high",
            "cvss": 8.1,
            "description": "SMB (Windows File Sharing) ist erreichbar. Risiko für EternalBlue & Co.",
            "recommendation": "Deaktiviere SMBv1, beschränke Zugriff auf internes Netz",
            "evidence": "Port 445 offen"
        })
    
    # Datenbanken
    elif port in [3306, 5432]:
        findings.append({
            "id": f"CRIT-{port}-001",
            "port": port,
            "service": service,
            "name": f"{service} Database Exposed",
            "severity": "critical",
            "cvss": 9.1,
            "description": f"Datenbank-Server {service} ist direkt erreichbar. Hohes Datenleck-Risiko!",
            "recommendation": "SOFORT: Datenbank hinter Firewall schützen, Zugriff nur via localhost/VPN",
            "evidence": f"Port {port} offen"
        })
    
    # Telnet (unsicher!)
    elif port == 23:
        findings.append({
            "id": f"CRIT-{port}-001",
            "port": port,
            "service": "Telnet",
            "name": "Insecure Telnet Protocol",
            "severity": "critical",
            "cvss": 9.8,
            "description": "Telnet sendet Daten unverschlüsselt. Sofort deaktivieren!",
            "recommendation": "DEAKTIVIERE Telnet sofort. Nutze stattdessen SSH.",
            "evidence": "Port 23 offen"
        })

# Standard-Finding wenn nichts gefunden
if not findings:
    findings.append({
        "id": "INFO-000",
        "port": 0,
        "service": "System",
        "name": "Scan Completed - No Vulnerabilities Detected",
        "severity": "info",
        "cvss": 0.0,
        "description": f"Scan auf {target} abgeschlossen. Keine kritischen Schwachstellen erkannt.",
        "recommendation": "Führe regelmäßige Scans durch um die Sicherheit zu überwachen",
        "evidence": "Scan durchgeführt"
    })

# Ausgabe der Findings
severity_colors = {
    "critical": "\033[91m",  # Rot
    "high": "\033[93m",      # Gelb
    "medium": "\033[94m",    # Blau
    "low": "\033[92m",       # Grün
    "info": "\033[96m"       # Cyan
}
reset = "\033[0m"

print(f"\n  Gefunden: {len(findings)} Ergebnisse\n")

for i, f in enumerate(findings, 1):
    color = severity_colors.get(f["severity"].lower(), "")
    sev = f["severity"].upper()
    print(f"{i}. {color}[{sev}]{reset} {f['name']}")
    print(f"   Port: {f['port']}/{f['service']}")
    print(f"   CVSS: {f['cvss']}")
    print(f"   {f['description'][:100]}...")
    print()

# Zusammenfassung
severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
for f in findings:
    sev = f["severity"].lower()
    if sev in severity_counts:
        severity_counts[sev] += 1

print("-" * 70)
print("\n[4] ZUSAMMENFASSUNG")
print("-" * 70)
print(f"  Ziel: {target}")
print(f"  Offene Ports: {len(open_ports)}")
print(f"  Ergebnisse: {len(findings)}")
print()
print(f"  Kritisch: {severity_counts['critical']}")
print(f"  Hoch:     {severity_counts['high']}")
print(f"  Mittel:   {severity_counts['medium']}")
print(f"  Niedrig:  {severity_counts['low']}")
print(f"  Info:     {severity_counts['info']}")

# Risiko-Score
risk_score = sum([
    severity_counts["critical"] * 10,
    severity_counts["high"] * 7,
    severity_counts["medium"] * 4,
    severity_counts["low"] * 1
])
risk_level = "Kritisch" if risk_score > 50 else "Hoch" if risk_score > 30 else "Mittel" if risk_score > 10 else "Niedrig"
print(f"\n  Risiko-Score: {risk_score}/100 ({risk_level})")

# Report speichern
print("\n[5] Report wird gespeichert...")
import os
os.makedirs('logs', exist_ok=True)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
report_data = {
    "scan_info": {
        "target": target,
        "timestamp": datetime.now().isoformat(),
        "scan_type": "real_port_scan",
        "open_ports": len(open_ports),
        "findings_count": len(findings)
    },
    "summary": severity_counts,
    "risk_score": risk_score,
    "risk_level": risk_level,
    "open_ports": [{"port": p[0], "service": p[1]} for p in open_ports],
    "findings": findings
}

json_file = f'logs/real_scan_{target.replace(".", "_")}_{timestamp}.json'
with open(json_file, 'w') as f:
    json.dump(report_data, f, indent=2)

print(f"  JSON Report: {json_file}")

# Markdown Report
md_file = f'logs/real_scan_{target.replace(".", "_")}_{timestamp}.md'
with open(md_file, 'w') as f:
    f.write(f"# Security Scan Report: {target}\n\n")
    f.write(f"**Scan Type:** Real Port Scan\n")
    f.write(f"**Date:** {datetime.now().isoformat()}\n")
    f.write(f"**Risk Score:** {risk_score}/100 ({risk_level})\n\n")
    
    f.write("## Summary\n\n")
    f.write(f"- **Open Ports:** {len(open_ports)}\n")
    f.write(f"- **Findings:** {len(findings)}\n\n")
    
    f.write("| Severity | Count |\n")
    f.write("|----------|-------|\n")
    for sev, count in severity_counts.items():
        if count > 0:
            f.write(f"| {sev.capitalize()} | {count} |\n")
    
    f.write(f"\n## Open Ports\n\n")
    for p in open_ports:
        f.write(f"- Port {p[0]}/{p[1]}\n")
    
    f.write(f"\n## Findings ({len(findings)} total)\n\n")
    for f_item in findings:
        f.write(f"### {f_item['id']}: {f_item['name']}\n\n")
        f.write(f"- **Severity:** {f_item['severity'].upper()} (CVSS: {f_item['cvss']})\n")
        f.write(f"- **Port:** {f_item['port']}/{f_item['service']}\n")
        f.write(f"- **Description:** {f_item['description']}\n")
        f.write(f"- **Recommendation:** {f_item['recommendation']}\n")
        f.write(f"- **Evidence:** `{f_item['evidence']}`\n\n")

print(f"  Markdown Report: {md_file}")

# SIEM Event
print("\n[6] SIEM Event wird gesendet...")
try:
    import requests
    r = requests.post('http://localhost:8000/api/v1/siem/events',
        json={
            "severity": "info" if risk_score < 30 else "high",
            "event_type": "real_scan_completed",
            "source": "real_scanner",
            "target": target,
            "description": f"Real scan on {target} found {len(findings)} issues (Risk: {risk_level})"
        }, timeout=5)
    if r.status_code == 200:
        print(f"  SIEM Event: Gesendet ✓")
except Exception as e:
    print(f"  SIEM Event: API nicht erreichbar ({str(e)[:30]})")

print("\n" + "=" * 70)
print("SCAN ABGESCHLOSSEN!")
print("=" * 70)
print(f"\nEmpfohlene Aktionen:")
if severity_counts['critical'] > 0:
    print(f"  ⚠️  SOFORT HANDELN: {severity_counts['critical']} kritische Schwachstellen!")
if severity_counts['high'] > 0:
    print(f"  ⚠️  Priorisiere: {severity_counts['high']} hohe Risiken")
print(f"  → Reports findest du in: logs/")
print("=" * 70)
