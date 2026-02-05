#!/usr/bin/env python3
"""
Netzwerk-Scanner - Finde alle Geräte in deinem Netzwerk
Inklusive VMs, Router, Drucker, etc.
"""
import socket
import subprocess

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

print("=" * 70)
print("NETZWERK-SCANNER - GERÄTE FINDEN")
print("=" * 70)
print(f"Start: {datetime.now().strftime('%H:%M:%S')}")
print("=" * 70)

# Dein Netzwerk
network = "192.168.1"
start_ip = 1
end_ip = 254

print(f"\nScanne Netzwerk: {network}.0/24")
print(f"Bereich: {network}.{start_ip} - {network}.{end_ip}")
print("Das dauert ca. 30-60 Sekunden...\n")

found_hosts = []

def scan_host(ip_suffix):
    """Prüfe ob Host aktiv ist"""
    ip = f"{network}.{ip_suffix}"
    try:
        # Ping mit kurzem Timeout
        result = subprocess.run(
            ["ping", "-n", "1", "-w", "500", ip],
            capture_output=True,
            text=True,
            timeout=2
        )
        if "TTL=" in result.stdout or "bytes=" in result.stdout:
            # Host ist online, versuche Hostname zu bekommen
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except Exception:
                hostname = "Unknown"
            return (ip, hostname, True)
    except:
        pass
    return None

# Scan starten
print("[1] Suche nach aktiven Hosts...")
print("-" * 70)

with ThreadPoolExecutor(max_workers=50) as executor:
    futures = [executor.submit(scan_host, i) for i in range(start_ip, end_ip + 1)]
    
    completed = 0
    for future in as_completed(futures):
        completed += 1
        if completed % 50 == 0:
            print(f"  Fortschritt: {completed}/{end_ip-start_ip+1} IPs geprüft...")
        
        result = future.result()
        if result:
            ip, hostname, active = result
            found_hosts.append(result)
            print(f"  [ONLINE] {ip:<16} | {hostname}")

print("\n" + "=" * 70)
print("ERGEBNIS")
print("=" * 70)

if not found_hosts:
    print("\n[!] Keine aktiven Hosts gefunden!")
else:
    print(f"\nGefunden: {len(found_hosts)} aktive Geräte\n")
    
    # Sortieren
    found_hosts.sort(key=lambda x: [int(x) for x in x[0].split('.')])
    
    print(f"{'IP-Adresse':<16} | {'Hostname':<30} | {'Vermutung'}")
    print("-" * 70)
    
    for ip, hostname, _ in found_hosts:
        guess = ""
        last_octet = int(ip.split('.')[-1])
        
        # Vermutungen basierend auf IP/Hostname
        if last_octet == 1:
            guess = "Router/Gateway"
        elif "fritz" in hostname.lower():
            guess = "FritzBox"
        elif "vmware" in hostname.lower() or "virtual" in hostname.lower():
            guess = "VM (VMware)"
        elif "docker" in hostname.lower():
            guess = "Docker Container"
        elif hostname == "Unknown":
            if last_octet > 200:
                guess = "VM oder IoT-Gerät?"
            else:
                guess = "PC/Laptop/Smartphone"
        elif last_octet == 243:
            guess = "Dein PC (Windows)"
        else:
            guess = "PC/Server/VM"
        
        print(f"{ip:<16} | {hostname:<30} | {guess}")

# Häufige VM-IPs vorschlagen
print("\n" + "=" * 70)
print("MÖGLICHE VMs")
print("=" * 70)

vm_candidates = [h for h in found_hosts if 
    int(h[0].split('.')[-1]) > 100 and 
    h[0] not in ["192.168.1.1", "192.168.1.243"] and
    h[1] == "Unknown"]

if vm_candidates:
    print("\nDiese IPs könnten deine VMs sein:")
    for ip, hostname, _ in vm_candidates:
        print(f"  → {ip} (Hostname: {hostname})")
        print(f"    Teste: python real_scan.py {ip}")
else:
    print("\nKeine offensichtlichen VMs gefunden.")
    print("Tipps:")
    print("  1. Ist deine VM gerade gestartet?")
    print("  2. Netzwerk-Modus der VM prüfen (Bridged/NAT)")
    print("  3. In der VM: 'ipconfig' oder 'ifconfig' ausführen")

# Spezielle Empfehlungen
print("\n" + "=" * 70)
print("SCAN-EMPFEHLUNGEN")
print("=" * 70)

if len(found_hosts) > 2:
    interesting = [h for h in found_hosts if h[0] not in ["192.168.1.1", "192.168.1.243"]]
    if interesting:
        print("\nInteressante Ziele zum Scannen:")
        for ip, hostname, _ in interesting[:5]:
            print(f"  python real_scan.py {ip}")

print("\nEigenes Ziel scannen:")
print("  python real_scan.py <ip-adresse>")
print("\nBeispiele:")
print("  python real_scan.py 192.168.1.105  # Wahrscheinliche VM")
print("  python real_scan.py 192.168.1.50   # Anderes Gerät")

print("\n" + "=" * 70)
